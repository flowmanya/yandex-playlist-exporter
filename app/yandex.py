import html
import re
import time
from urllib.parse import unquote, urlparse

import requests

from .config import (
    API_HOST,
    MAX_RETRIES,
    MUSIC_HOSTS,
    REQUEST_TIMEOUT,
    RETRY_DELAY,
    USER_AGENT,
)


class YandexMusicError(RuntimeError):
    pass


def create_session():
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": USER_AGENT,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
        }
    )
    return session


def request_json(session, url, params=None):
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = session.get(
                url,
                params=params,
                timeout=REQUEST_TIMEOUT,
            )

            if response.ok:
                try:
                    return response.json()
                except ValueError as exc:
                    raise YandexMusicError(
                        "Сервер вернул некорректный JSON."
                    ) from exc

            if response.status_code in (429, 500, 502, 503, 504):
                last_error = YandexMusicError(
                    f"HTTP {response.status_code}"
                )
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY * attempt)
                    continue

            raise YandexMusicError(
                f"HTTP {response.status_code}"
            )

        except requests.RequestException as exc:
            last_error = exc
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY * attempt)

    raise YandexMusicError(
        "Не удалось получить данные от Яндекс Музыки."
    ) from last_error


def _is_music_url(value):
    try:
        host = (urlparse(value).hostname or "").lower()
    except ValueError:
        return False

    return host in MUSIC_HOSTS


def _iframe_playlist_url(value):
    value = html.unescape(value)

    for href in re.findall(
        r'href\s*=\s*["\']([^"\']+)["\']',
        value,
        re.IGNORECASE,
    ):
        href = html.unescape(href).strip()
        if _is_music_url(href) and "/playlists/" in href:
            return href

    return None


def normalize_playlist_url(value):
    value = html.unescape(value.strip())

    if not value:
        raise YandexMusicError("Ссылка на плейлист не указана.")

    if "<iframe" in value.lower():
        url = _iframe_playlist_url(value)
        if url:
            return url

        raise YandexMusicError(
            "В iframe не найдена обычная ссылка на плейлист."
        )

    if _is_music_url(value) and "/playlists/" in value:
        return value

    match = re.search(
        r'https?://music\.yandex\.[^/\s"<>]+/playlists/[^\s"<>]+',
        value,
        re.IGNORECASE,
    )
    if match:
        return match.group(0)

    raise YandexMusicError(
        "Не удалось найти ссылку на публичный плейлист."
    )


def playlist_id_from_url(url):
    path = unquote(urlparse(url).path)

    match = re.search(
        r"/playlists/([^/?#]+)",
        path,
        re.IGNORECASE,
    )
    if not match:
        raise YandexMusicError(
            "Не удалось определить идентификатор плейлиста."
        )

    return match.group(1)


def _playlist_from_response(data):
    if not isinstance(data, dict):
        return None

    result = data.get("result")

    if isinstance(result, dict):
        playlist = result.get("playlist")
        if isinstance(playlist, dict):
            return playlist

        if "tracks" in result:
            return result

    playlist = data.get("playlist")
    if isinstance(playlist, dict):
        return playlist

    return None


def _track_items(data):
    playlist = _playlist_from_response(data)
    if not playlist:
        return []

    tracks = playlist.get("tracks")
    return tracks if isinstance(tracks, list) else []


def _track_count(data):
    playlist = _playlist_from_response(data)
    if not playlist:
        return None

    for key in ("trackCount", "tracksCount", "totalTracks"):
        value = playlist.get(key)
        if isinstance(value, int):
            return value

    return None


def _format_track(item):
    if not isinstance(item, dict):
        return None

    track = item.get("track")
    if not isinstance(track, dict):
        track = item

    title = track.get("title")
    if not title:
        return None

    artists = track.get("artists", [])
    names = []

    if isinstance(artists, list):
        for artist in artists:
            if isinstance(artist, dict) and artist.get("name"):
                names.append(str(artist["name"]).strip())

    title = str(title).replace("\r", " ").replace("\n", " ").strip()

    if names:
        return f"{', '.join(names)} - {title}"

    return title


def _extract_tracks(data):
    result = []

    for item in _track_items(data):
        line = _format_track(item)
        if line:
            result.append(line)

    return result


def fetch_playlist(value, session=None, progress=None):
    session = session or create_session()

    url = normalize_playlist_url(value)
    playlist_id = playlist_id_from_url(url)

    data = request_json(
        session,
        f"{API_HOST}/playlist/{playlist_id}",
        params={"richTracks": "true"},
    )

    items = _track_items(data)
    total = _track_count(data)

    if total is not None and len(items) < total:
        raise YandexMusicError(
            f"API вернул только {len(items)} из {total} треков. "
            "Публичный ответ не содержит полной коллекции."
        )

    tracks = _extract_tracks(data)

    if progress:
        progress(len(tracks), total or len(tracks))

    return tracks
