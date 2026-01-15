"""
Secure Vault - File Utilities
Helpers for file naming and path handling.
"""

from typing import Set
from pathlib import Path


def get_unique_filename(name: str, existing_names: Set[str]) -> str:
    """
    Get a unique filename by appending (N) if collision occurs.
    Windows-style collision resolution: file.txt -> file (2).txt -> file (3).txt
    
    Args:
        name: Desired filename (e.g., "file.txt")
        existing_names: Set of names already in the destination
        
    Returns:
        Unique filename
    """
    if name not in existing_names:
        return name
    
    path_obj = Path(name)
    stem = path_obj.stem
    suffix = path_obj.suffix
    
    counter = 1
    while True:
        new_name = f"{stem} ({counter}){suffix}"
        if new_name not in existing_names:
            return new_name
        counter += 1
