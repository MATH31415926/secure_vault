"""
Secure Vault - Hash Utilities
Provides hashing functions for file deduplication and integrity verification.
"""

from pathlib import Path
from typing import Iterator

from nacl.hash import blake2b
from nacl.encoding import RawEncoder

# Block size for file reading (1 MB)
READ_BLOCK_SIZE = 1024 * 1024


def compute_block_hash(data: bytes) -> str:
    """
    Compute hash of a data block for deduplication.
    
    Args:
        data: Data block to hash
    
    Returns:
        Hex-encoded BLAKE2b hash
    """
    return blake2b(data, digest_size=32, encoder=RawEncoder).hex()


def compute_file_hash(file_path: Path) -> str:
    """
    Compute hash of an entire file.
    
    Args:
        file_path: Path to the file
    
    Returns:
        Hex-encoded BLAKE2b hash
    """
    # Use incremental hashing for large files
    from nacl.bindings import (
        crypto_generichash_blake2b_init,
        crypto_generichash_blake2b_update,
        crypto_generichash_blake2b_final
    )
    
    state = crypto_generichash_blake2b_init(digest_size=32)
    
    with open(file_path, "rb") as f:
        while chunk := f.read(READ_BLOCK_SIZE):
            crypto_generichash_blake2b_update(state, chunk)
    
    return crypto_generichash_blake2b_final(state).hex()


def iter_file_blocks(file_path: Path, block_size: int = READ_BLOCK_SIZE) -> Iterator[bytes]:
    """
    Iterate over file in blocks.
    
    Args:
        file_path: Path to the file
        block_size: Size of each block
    
    Yields:
        Data blocks
    """
    with open(file_path, "rb") as f:
        while chunk := f.read(block_size):
            yield chunk


def count_file_blocks(file_path: Path, block_size: int = READ_BLOCK_SIZE) -> int:
    """
    Count the number of blocks in a file.
    
    Args:
        file_path: Path to the file
        block_size: Size of each block
    
    Returns:
        Number of blocks
    """
    file_size = file_path.stat().st_size
    return (file_size + block_size - 1) // block_size


def get_file_size(file_path: Path) -> int:
    """
    Get file size in bytes.
    
    Args:
        file_path: Path to the file
    
    Returns:
        File size in bytes
    """
    return file_path.stat().st_size


def format_size(size_bytes: int) -> str:
    """
    Format byte size to human-readable string.
    
    Args:
        size_bytes: Size in bytes
    
    Returns:
        Human-readable size string (e.g., "1.5 GB")
    """
    if size_bytes < 0:
        return "-"
    
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024:
            if unit == "B":
                return f"{size_bytes} {unit}"
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    
    return f"{size_bytes:.2f} PB"
