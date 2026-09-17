from pathlib import Path


APP_NAME = "Yandex Music Exporter"
OUTPUT_FILE = Path("tracks.txt")

REQUEST_TIMEOUT = 20
MAX_RETRIES = 4
RETRY_DELAY = 1.5

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/140.0 Safari/537.36"
)

API_HOST = "https://api.music.yandex.ru"

MUSIC_HOSTS = {
    "music.yandex.ru",
    "music.yandex.com",
    "music.yandex.kz",
    "music.yandex.by",
    "music.yandex.uz",
    "music.yandex.az",
    "music.yandex.am",
    "music.yandex.ge",
    "music.yandex.md",
    "music.yandex.tj",
    "music.yandex.tm",
    "music.yandex.kg",
}
