import os
import ctypes
import logging
from typing import Iterator, List, Optional

from .metadata import extract_metadata_safe
from .models import FileMetadata

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_windows_drives() -> List[str]:
    drives = []
    bitmask = ctypes.windll.kernel32.GetLogicalDrives()
    for i in range(26):
        if bitmask & (1 << i):
            drive_letter = chr(65 + i)
            drives.append(f"{drive_letter}:\\")
    return drives


def _walk_error_handler(error: OSError) -> None:
    logger.debug(f"Skipping inaccessible path: {error.filename}")


def index_directory(root_path: str) -> Iterator[FileMetadata]:
    if root_path in ("*", "all"):
        root_paths = get_windows_drives()
    else:
        root_paths = [root_path]

    for root in root_paths:
        if not os.path.exists(root):
            logger.warning(f"Path does not exist: {root}")
            continue

        for dirpath, dirnames, filenames in os.walk(root, onerror=_walk_error_handler):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                try:
                    metadata = extract_metadata_safe(file_path)
                    if metadata is not None:
                        yield metadata
                except (OSError, PermissionError) as e:
                    logger.debug(f"Cannot access file: {file_path} - {e}")
                    continue


def index_directories(paths: List[str]) -> Iterator[FileMetadata]:
    for path in paths:
        yield from index_directory(path)
