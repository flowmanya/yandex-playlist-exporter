from .config import OUTPUT_FILE
from .exporter import save_tracks
from .yandex import YandexMusicError, create_session, fetch_playlist


def run_cli(value):
    print("Получение плейлиста...")

    try:
        tracks = fetch_playlist(
            value,
            session=create_session(),
            progress=lambda current, total: print(
                f"\rПолучено: {current}/{total}",
                end="",
                flush=True,
            ),
        )
        print()

        print(f"Найдено треков: {len(tracks)}")
        print("Сохранение в tracks.txt...")

        save_tracks(tracks, OUTPUT_FILE)

    except YandexMusicError as exc:
        print(f"\nОшибка: {exc}")
        return 1

    except OSError as exc:
        print(f"\nОшибка записи файла: {exc}")
        return 1

    print("Готово!")
    return 0
