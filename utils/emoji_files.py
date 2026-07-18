import io
import re
import zipfile
from dataclasses import dataclass
from pathlib import PurePosixPath

SUPPORTED_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".avif",
}
MAX_FILE_SIZE_MB = 10


@dataclass
class EmojiFile:
    path: str
    filename: str
    data: bytes
    category_from_folder: str


def normalize_emoji_name(
    filename: str,
    prefix: str = "",
) -> str:
    stem = PurePosixPath(filename).stem.lower()
    stem = re.sub(r"[^a-z0-9_+-]+", "_", stem)
    stem = re.sub(r"_+", "_", stem).strip("_")

    prefix = re.sub(
        r"[^a-zA-Z0-9_+-]+",
        "_",
        prefix.strip(),
    ).strip("_").lower()

    name = f"{prefix}_{stem}" if prefix and stem else prefix or stem
    return name[:100]


def read_zip(uploaded_file) -> list[EmojiFile]:
    content = uploaded_file.getvalue()
    emojis = []

    try:
        archive = zipfile.ZipFile(io.BytesIO(content))
    except zipfile.BadZipFile as exc:
        raise ValueError("ZIPファイルを開けませんでした。") from exc

    for info in archive.infolist():
        if info.is_dir():
            continue

        path = PurePosixPath(info.filename)

        if path.name.startswith(".") or "__MACOSX" in path.parts:
            continue

        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        if info.file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
            continue

        category = path.parts[-2] if len(path.parts) >= 2 else ""

        emojis.append(
            EmojiFile(
                path=info.filename,
                filename=path.name,
                data=archive.read(info),
                category_from_folder=category,
            )
        )

    return emojis


def parse_aliases(value: str) -> list[str]:
    return [
        item.strip()
        for item in re.split(r"[,、\s]+", value)
        if item.strip()
    ]
