from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass
class FileMetadata:
    name: str
    path: str
    size: int
    modified_time: datetime
    created_time: datetime
    is_hidden: bool
    is_readonly: bool
    is_system: bool
    is_archive: bool

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "path": self.path,
            "size": self.size,
            "modified_time": self.modified_time.isoformat(),
            "created_time": self.created_time.isoformat(),
            "is_hidden": self.is_hidden,
            "is_readonly": self.is_readonly,
            "is_system": self.is_system,
            "is_archive": self.is_archive,
        }


@dataclass
class IndexResult:
    files: List[FileMetadata]
    summary: "IndexSummary"

    def to_dict(self) -> dict:
        return {
            "files": [f.to_dict() for f in self.files],
            "summary": self.summary.to_dict(),
        }


@dataclass
class IndexSummary:
    total_files: int
    total_size: int
    indexed_paths: List[str]
    timestamp: datetime

    def to_dict(self) -> dict:
        return {
            "total_files": self.total_files,
            "total_size": self.total_size,
            "indexed_paths": self.indexed_paths,
            "timestamp": self.timestamp.isoformat(),
        }
