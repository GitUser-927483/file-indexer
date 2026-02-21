import os
import ctypes
from datetime import datetime
from typing import Optional

from .models import FileMetadata


FILE_ATTRIBUTE_HIDDEN = 0x2
FILE_ATTRIBUTE_READONLY = 0x1
FILE_ATTRIBUTE_SYSTEM = 0x4
FILE_ATTRIBUTE_ARCHIVE = 0x20

GetFileAttributesExW = ctypes.windll.kernel32.GetFileAttributesExW
GetFileAttributesExW.argtypes = [ctypes.c_wchar_p, ctypes.c_int, ctypes.c_void_p]
GetFileAttributesExW.restype = ctypes.c_bool


class WIN32_FILE_ATTRIBUTE_DATA(ctypes.Structure):
    _fields_ = [
        ("dwFileAttributes", ctypes.c_ulong),
        ("ftCreationTime", ctypes.c_ulonglong),
        ("ftLastAccessTime", ctypes.c_ulonglong),
        ("ftLastWriteTime", ctypes.c_ulonglong),
        ("nFileSizeHigh", ctypes.c_ulong),
        ("nFileSizeLow", ctypes.c_ulong),
    ]


def extract_metadata(file_path: str) -> Optional[FileMetadata]:
    try:
        stat_result = os.stat(file_path)
    except (OSError, PermissionError):
        return None

    name = os.path.basename(file_path)
    size = stat_result.st_size
    modified_time = datetime.fromtimestamp(stat_result.st_mtime)
    created_time = datetime.fromtimestamp(stat_result.st_ctime)

    is_hidden = False
    is_readonly = False
    is_system = False
    is_archive = False

    try:
        attr_data = WIN32_FILE_ATTRIBUTE_DATA()
        if GetFileAttributesExW(file_path, 0, ctypes.byref(attr_data)):
            attrs = attr_data.dwFileAttributes
            is_hidden = bool(attrs & FILE_ATTRIBUTE_HIDDEN)
            is_readonly = bool(attrs & FILE_ATTRIBUTE_READONLY)
            is_system = bool(attrs & FILE_ATTRIBUTE_SYSTEM)
            is_archive = bool(attrs & FILE_ATTRIBUTE_ARCHIVE)
    except Exception:
        pass

    return FileMetadata(
        name=name,
        path=file_path,
        size=size,
        modified_time=modified_time,
        created_time=created_time,
        is_hidden=is_hidden,
        is_readonly=is_readonly,
        is_system=is_system,
        is_archive=is_archive,
    )


def extract_metadata_safe(file_path: str) -> Optional[FileMetadata]:
    try:
        return extract_metadata(file_path)
    except Exception:
        return None
