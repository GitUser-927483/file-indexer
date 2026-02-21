import argparse
from typing import List, Optional


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="File indexer - Index files and generate metadata JSON",
        epilog="""
Examples:
  python main.py --path "C:\\Users"
  python main.py --path "*" --output full_index.json
  python main.py --path "C:\\Users" --sort size
  python main.py --path "D:\\Documents" --output index.json --sort name
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--path",
        type=str,
        default=".",
        help="Directory to index, or '*' for all drives (default: '.')",
    )

    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output JSON file path (optional, prints to stdout if not specified)",
    )

    parser.add_argument(
        "--sort",
        type=str,
        choices=["name", "path", "size", "modified_time", "created_time"],
        default="path",
        help="Sort results by field (default: path)",
    )

    return parser


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    parser = create_parser()
    return parser.parse_args(args)
