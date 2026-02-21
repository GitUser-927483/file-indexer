import json
import os
import shutil
from datetime import datetime
from typing import List, Dict, Any

from src.models import FileMetadata, IndexResult, IndexSummary


def create_index_result(files: List[FileMetadata], indexed_paths: List[str]) -> IndexResult:
    total_size = sum(f.size for f in files)
    summary = IndexSummary(
        total_files=len(files),
        total_size=total_size,
        indexed_paths=indexed_paths,
        timestamp=datetime.now(),
    )
    return IndexResult(files=files, summary=summary)


def sort_files(files: List[FileMetadata], sort_by: str = "path") -> List[FileMetadata]:
    valid_sort_keys = {"name", "path", "size", "modified_time", "created_time"}
    if sort_by not in valid_sort_keys:
        sort_by = "path"
    return sorted(files, key=lambda f: getattr(f, sort_by, f.path))


def to_json(index_result: IndexResult, indent: int = 2, sort_by: str = "path") -> str:
    files = sort_files(index_result.files, sort_by)
    result = IndexResult(files=files, summary=index_result.summary)
    return json.dumps(result.to_dict(), indent=indent)


def save_to_file(index_result: IndexResult, filepath: str, indent: int = 2) -> None:
    json_str = to_json(index_result, indent=indent)
    
    # Check if file exists and warn user
    if os.path.exists(filepath):
        raise FileExistsError(f"File already exists: {filepath}")
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(json_str)


def build_directory_structure(index_result: IndexResult) -> Dict[str, Any]:
    """Build directory tree structure from index result."""
    directory_tree = {}
    for file in index_result.files:
        parts = file.path.split(os.sep)
        current_level = directory_tree
        
        for part in parts:
            if part not in current_level:
                current_level[part] = {}
            current_level = current_level[part]
    
    return directory_tree


def directory_tree_to_tree_format(tree: Dict[str, Any], prefix: str = "", is_last: bool = True, is_root: bool = True) -> List[str]:
    """Convert directory tree dictionary to tree format string."""
    lines = []
    
    if is_root:
        # Root level - show as the base path
        items = sorted(tree.items(), key=lambda x: (not bool(x[1]), x[0]))
        for i, (name, subtree) in enumerate(items):
            is_last_item = (i == len(items) - 1)
            if i == 0:
                lines.append(f"/{name}")
            
            if isinstance(subtree, dict) and subtree:
                # This is a directory
                new_prefix = "│ " if not is_last_item else "  "
                lines.extend(directory_tree_to_tree_format(subtree, new_prefix, is_last_item, is_root=False))
            else:
                # This is a file
                connector = "└── " if is_last_item else "├── "
                lines.append(f"{prefix}{connector}{name}")
    
    return lines


def build_tree_format(index_result: IndexResult) -> str:
    """Build tree format string from index result."""
    # Get unique root paths
    root_paths = set()
    for file in index_result.files:
        # Get the root drive or first directory
        parts = file.path.split(os.sep)
        if parts:
            root_paths.add(parts[0] if parts[0] else parts[1] if len(parts) > 1 else "")
    
    lines = []
    sorted_roots = sorted(root_paths)
    
    for i, root in enumerate(sorted_roots):
        is_last_root = (i == len(sorted_roots) - 1)
        root_connector = "└── " if is_last_root else "├── "
        
        if root:
            lines.append(f"{root_connector}{root}")
            
            # Build subtree for this root
            subtree = {}
            for file in index_result.files:
                parts = file.path.split(os.sep)
                if parts and parts[0] == root:
                    # Build the rest of the path
                    current = subtree
                    for part in parts[1:]:
                        if part not in current:
                            current[part] = {}
                        current = current[part]
            
            # Convert subtree to tree format
            if subtree:
                new_prefix = "    " if is_last_root else "│   "
                subtree_lines = directory_tree_to_tree_format_simple(subtree, new_prefix, is_last_root)
                lines.extend(subtree_lines)
    
    if not lines:
        return "(empty)"
    
    return "\n".join(lines)


def directory_tree_to_tree_format_simple(tree: Dict[str, Any], prefix: str = "", is_last: bool = True) -> List[str]:
    """Convert directory tree dictionary to tree format string (simplified)."""
    lines = []
    
    # Sort: directories first, then files
    items = sorted(tree.items(), key=lambda x: (not bool(x[1]), x[0].lower()))
    
    for i, (name, subtree) in enumerate(items):
        is_last_item = (i == len(items) - 1)
        
        if isinstance(subtree, dict) and subtree:
            # Directory
            connector = "└── " if is_last_item else "├── "
            lines.append(f"{prefix}{connector}/{name}")
            
            # Continuation prefix for children
            new_prefix = prefix + ("    " if is_last_item else "│   ")
            lines.extend(directory_tree_to_tree_format_simple(subtree, new_prefix, is_last_item))
        else:
            # File
            connector = "└── " if is_last_item else "├── "
            lines.append(f"{prefix}{connector}{name}")
    
    return lines


def save_directory_structure(index_result: IndexResult, filepath: str, indent: int = 2) -> None:
    """Save directory structure showing all directories and branches."""
    
    # Build directory tree
    directory_tree = build_directory_structure(index_result)
    
    # Convert to JSON
    json_str = json.dumps(directory_tree, indent=indent)
    
    # Check if file exists and warn user
    if os.path.exists(filepath):
        raise FileExistsError(f"File already exists: {filepath}")
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(json_str)


def get_file_saver():
    """Return a function that saves files with duplicate protection."""
    
    def saver(index_result: IndexResult, base_name: str, indent: int = 2) -> Dict[str, str]:
        return save_with_duplicate_check(index_result, base_name, indent)
    
    return saver


def save_with_duplicate_check(index_result: IndexResult, base_name: str, indent: int = 2, output_dir: str = None) -> Dict[str, str]:
    """
    Save files with DUPLICATE CHECK only - no auto-rename.
    Returns dictionary with file paths.
    Raises FileExistsError if file already exists.
    """
    # Use default output directory or custom
    if output_dir is None:
        output_dir = "file_indexer/output"
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Create base filenames WITHOUT timestamp
    base_filename = os.path.join(output_dir, base_name)
    index_filepath = f"{base_filename}.json"
    structure_filepath = f"{base_filename}_structure.txt"
    
    # Check if files already exist - if so, raise error to alert user
    if os.path.exists(index_filepath):
        raise FileExistsError(f"A file named '{base_name}.json' already exists in {output_dir}")
    if os.path.exists(structure_filepath):
        raise FileExistsError(f"A file named '{base_name}_structure.txt' already exists in {output_dir}")
    
    # Save index file (JSON)
    with open(index_filepath, "w", encoding="utf-8") as f:
        f.write(to_json(index_result, indent=indent))
    
    # Save directory structure in tree format (.txt)
    tree_content = build_tree_format(index_result)
    with open(structure_filepath, "w", encoding="utf-8") as f:
        f.write(tree_content)
    
    return {
        "index_file": index_filepath,
        "structure_file": structure_filepath
    }
