"""Large file splitting for Telegram's 2GB upload limit."""
from __future__ import annotations

import logging
import math
from pathlib import Path

logger = logging.getLogger(__name__)

TELEGRAM_MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2GB
DEFAULT_CHUNK_SIZE = 1900 * 1024 * 1024  # ~1.9GB to stay safely under limit


def needs_splitting(file_path: Path, max_size: int = TELEGRAM_MAX_FILE_SIZE) -> bool:
    """Check if file exceeds Telegram's size limit."""
    return file_path.stat().st_size > max_size


def calculate_chunks(file_size: int, chunk_size: int = DEFAULT_CHUNK_SIZE) -> list[tuple[int, int]]:
    """Calculate byte ranges for each chunk. Returns list of (start, end) tuples."""
    chunks = []
    offset = 0
    while offset < file_size:
        end = min(offset + chunk_size, file_size)
        chunks.append((offset, end))
        offset = end
    return chunks


async def split_file(
    file_path: Path,
    output_dir: Path,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> list[Path]:
    """Split a large file into chunks under the size limit.

    Returns list of chunk file paths in order.
    """
    file_size = file_path.stat().st_size
    if file_size <= TELEGRAM_MAX_FILE_SIZE:
        logger.info("File %s (%d bytes) is within limit, no split needed", file_path.name, file_size)
        return [file_path]

    output_dir.mkdir(parents=True, exist_ok=True)
    chunks = calculate_chunks(file_size, chunk_size)
    logger.info("Splitting %s (%d bytes) into %d chunks", file_path.name, file_size, len(chunks))

    chunk_paths = []
    for index, (start, end) in enumerate(chunks):
        chunk_name = f"{file_path.stem}.part{index + 1:03d}{file_path.suffix}"
        chunk_path = output_dir / chunk_name
        chunk_paths.append(chunk_path)

        # Stream copy in chunks to avoid loading entire file into memory
        bytes_written = 0
        chunk_bytes = end - start
        with file_path.open("rb") as src, chunk_path.open("wb") as dst:
            src.seek(start)
            remaining = chunk_bytes
            buffer_size = 1024 * 1024  # 1MB buffer
            while remaining > 0:
                read_size = min(buffer_size, remaining)
                data = src.read(read_size)
                if not data:
                    break
                dst.write(data)
                remaining -= len(data)
                bytes_written += len(data)

        logger.info(
            "Created chunk %d/%d: %s (%d bytes)",
            index + 1, len(chunks), chunk_path.name, bytes_written,
        )

    return chunk_paths


def get_chunk_name(original_name: str, part: int, total: int) -> str:
    """Generate a descriptive name for a file chunk."""
    stem = Path(original_name).stem
    suffix = Path(original_name).suffix
    return f"{stem} (part {part} of {total}){suffix}"


def cleanup_chunks(chunk_paths: list[Path]) -> None:
    """Remove temporary chunk files after upload."""
    for path in chunk_paths:
        try:
            path.unlink(missing_ok=True)
        except Exception as exc:
            logger.warning("Failed to cleanup chunk %s: %s", path, exc)