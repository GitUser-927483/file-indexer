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


def save_with_duplicate_check(index_result: IndexResult, base_name: str, indent: int = 2) -> Dict[str, str]:
    """
    Save files with duplicate protection and return file paths.
    Returns dictionary with file paths.
    """
    output_dir = "file_indexer/output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Get current timestamp for unique filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create base filenames
    base_filename = os.path.join(output_dir, base_name)
    
    # Add timestamp to avoid duplicates
    index_filepath = f"{base_filename}_{timestamp}.json"
    structure_filepath = f"{base_filename}_structure_{timestamp}.json"
    
    # Check if files exist (should not with timestamp, but just in case)
    if os.path.exists(index_filepath) or os.path.exists(structure_filepath):
        raise FileExistsError("Generated file names already exist. This should not happen with timestamp.")
    
    # Save both files (without creating directory, it already exists)
    with open(index_filepath, "w", encoding="utf-8") as f:
        f.write(to_json(index_result, indent=indent))
    
    with open(structure_filepath, "w", encoding="utf-8") as f:
        f.write(json.dumps(build_directory_structure(index_result), indent=indent))
    
    return {
        "index_file": index_filepath,
        "structure_file": structure_filepath
    }
