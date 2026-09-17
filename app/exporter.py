from pathlib import Path


def save_tracks(tracks, filename):
    filename = Path(filename)

    with filename.open(
        "w",
        encoding="utf-8",
        newline="\n",
    ) as file:
        if tracks:
            file.write("\n".join(tracks))
            file.write("\n")
