import sys
from typing import List

from cli import parse_args
from src.indexer import index_directory
from src.output import create_index_result, save_to_file, to_json


def main() -> None:
    args = parse_args()

    root_path = args.path
    output_path = args.output
    sort_by = args.sort

    files: List = []
    indexed_paths: List[str] = []

    if root_path in ("*", "all"):
        from src.indexer import get_windows_drives
        indexed_paths = get_windows_drives()
    else:
        indexed_paths = [root_path]

    for file_metadata in index_directory(root_path):
        files.append(file_metadata)

    result = create_index_result(files, indexed_paths)

    if output_path:
        from src.output import sort_files
        sorted_files = sort_files(result.files, sort_by)
        from src.models import IndexResult
        result = IndexResult(files=sorted_files, summary=result.summary)
        save_to_file(result, output_path)
        print(f"Index saved to: {output_path}")
    else:
        json_output = to_json(result, sort_by=sort_by)
        print(json_output)


if __name__ == "__main__":
    main()
