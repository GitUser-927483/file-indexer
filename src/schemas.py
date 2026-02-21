import json
from typing import Any, Dict, List


INDEX_SCHEMA: Dict[str, Any] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "FileIndexResult",
    "type": "object",
    "required": ["files", "summary"],
    "properties": {
        "files": {
            "type": "array",
            "items": {
                "type": "object",
                "required": [
                    "name",
                    "path",
                    "size",
                    "modified_time",
                    "created_time",
                    "is_hidden",
                    "is_readonly",
                    "is_system",
                    "is_archive",
                ],
                "properties": {
                    "name": {"type": "string"},
                    "path": {"type": "string"},
                    "size": {"type": "integer"},
                    "modified_time": {"type": "string", "format": "date-time"},
                    "created_time": {"type": "string", "format": "date-time"},
                    "is_hidden": {"type": "boolean"},
                    "is_readonly": {"type": "boolean"},
                    "is_system": {"type": "boolean"},
                    "is_archive": {"type": "boolean"},
                },
            },
        },
        "summary": {
            "type": "object",
            "required": ["total_files", "total_size", "indexed_paths", "timestamp"],
            "properties": {
                "total_files": {"type": "integer"},
                "total_size": {"type": "integer"},
                "indexed_paths": {"type": "array", "items": {"type": "string"}},
                "timestamp": {"type": "string", "format": "date-time"},
            },
        },
    },
}


def validate_index_result(data: Dict[str, Any]) -> bool:
    try:
        json.validate(data, INDEX_SCHEMA)
        return True
    except Exception:
        return False


def get_schema_json() -> str:
    return json.dumps(INDEX_SCHEMA, indent=2)
