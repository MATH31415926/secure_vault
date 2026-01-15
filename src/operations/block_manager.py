"""
Secure Vault - Block Manager
Handles encrypted block storage with deduplication.
Blocks are stored in repository/.vault/blocks/
"""

import shutil
import uuid
from pathlib import Path
from typing import Tuple, Optional, List

from src.core.crypto import (
    derive_file_key, encrypt_block, decrypt_block, generate_salt
)
from src.core.hash_utils import compute_block_hash
from src.database.models import Block
from src.database.database import get_repository_database


class BlockManager:
    """Manages encrypted block storage."""
    
    def __init__(self, repository_path: str, master_key: bytes):
        """
        Initialize block manager.
        
        Args:
            repository_path: Path to the repository
            master_key: Master encryption key
        """
        self.repository_path = Path(repository_path)
        self.master_key = master_key
        
        # Get blocks directory from repository database
        repo_db = get_repository_database(repository_path)
        self.blocks_dir = repo_db.blocks_path
        
        # Ensure blocks directory exists
        self.blocks_dir.mkdir(parents=True, exist_ok=True)
    
    def prepare_block(self, data: bytes) -> dict:
        """
        Prepare a block for storage (hashing, encryption, path generation).
        This method is CPU and IO intensive but does NOT touch the database.
        It is safe to run in a thread pool.
        
        Args:
            data: Raw block data
            
        Returns:
            Dictionary with block metadata and prepared data
        """
        # Hashing (CPU)
        block_hash = compute_block_hash(data)
        
        # Salt and key derivation (CPU)
        salt = generate_salt()
        file_key = derive_file_key(self.master_key, salt)
        
        # Encryption (CPU)
        encrypted_data, nonce = encrypt_block(data, file_key)
        
        # Path generation
        relative_path = self._generate_block_path()
        
        # Return all needed data for storage
        return {
            "hash": block_hash,
            "relative_path": relative_path,
            "size": len(encrypted_data),
            "salt": salt,
            "nonce": nonce,
            "encrypted_data": encrypted_data,
            "original_size": len(data)
        }

    def store_prepared_block(self, prepared: dict) -> Tuple[Block, bool]:
        """
        Store a previously prepared block into the database and disk.
        
        Args:
            prepared: Dictionary from prepare_block
            
        Returns:
            Tuple of (Block object, is_new_block)
        """
        # Check for existing block with same hash (Deduplication)
        # This must be done here (sequential) to avoid race conditions in DB
        existing_block = Block.get_by_hash(prepared["hash"], str(self.repository_path))
        if existing_block:
            existing_block.increment_reference(str(self.repository_path))
            return existing_block, False
        
        # Determine target directory
        target_dir = self.blocks_dir
            
        # Write encrypted block to disk (IO)
        full_path = target_dir / prepared["relative_path"]
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(full_path, "wb") as f:
            f.write(prepared["encrypted_data"])
        
            
        # Create block record in database (DB)
        block = Block.create(
            block_hash=prepared["hash"],
            relative_path=prepared["relative_path"],
            size=prepared["size"],
            salt=prepared["salt"],
            nonce=prepared["nonce"],
            repo_path=str(self.repository_path)
        )
        
        
        return block, True

    def store_block(self, data: bytes) -> Tuple[Block, bool]:
        """Legacy synchronous storage."""
        prepared = self.prepare_block(data)
        return self.store_prepared_block(prepared)
    
    def retrieve_block_data(self, block: Block) -> bytes:
        """
        Read and decrypt a block's data. 
        Safe to run in a thread pool (CPU and IO intensive).
        """
        full_path = self.blocks_dir / block.relative_path
        
        if not full_path.exists():
            raise FileNotFoundError(f"Block file not found: {block.relative_path}")
        
        with open(full_path, "rb") as f:
            encrypted_data = f.read()
        
        # Derive key and decrypt
        file_key = derive_file_key(self.master_key, block.salt)
        return decrypt_block(encrypted_data, file_key, block.nonce)

    def retrieve_block(self, block: Block) -> bytes:
        """Legacy synchronous retrieval."""
        return self.retrieve_block_data(block)
    
    def delete_block_file(self, block: Block) -> bool:
        """
        Only remove the block file from disk.
        Does NOT touch the database.
        
        Args:
            block: Block to delete
            
        Returns:
            True if block file was deleted
        """
        full_path = self.blocks_dir / block.relative_path
        if full_path.exists():
            full_path.unlink()
            return True
        return False

    def delete_block(self, block: Block) -> bool:
        """
        Delete a block (decrement reference, remove if zero).
        
        Args:
            block: Block to delete
        
        Returns:
            True if block file was deleted
        """
        should_delete = block.decrement_reference(str(self.repository_path))
        
        if should_delete:
            self.delete_block_file(block)
            
            # Remove from database
            block.delete(str(self.repository_path))
            return True
        
        return False
    
    def block_exists(self, block: Block) -> bool:
        """
        Check if a block file exists on disk.
        
        Args:
            block: Block to check
        
        Returns:
            True if block file exists
        """
        full_path = self.blocks_dir / block.relative_path
        return full_path.exists()
    
    def _generate_block_path(self) -> str:
        """
        Generate a unique relative path for a new block.
        
        Uses UUID-based paths with directory sharding for performance.
        
        Returns:
            Relative path like "ab/cd/abcd1234-5678-......"
        """
        block_id = uuid.uuid4().hex
        # Shard by first 4 characters (2 levels of directories)
        return f"{block_id[:2]}/{block_id[2:4]}/{block_id}"
    
    def get_block_size(self, block: Block) -> int:
        """
        Get the size of a block file.
        
        Args:
            block: Block to check
        
        Returns:
            File size in bytes, or 0 if not found
        """
        full_path = self.blocks_dir / block.relative_path
        if full_path.exists():
            return full_path.stat().st_size
        return 0
    
    def rollback_temp_blocks(self) -> None:
        """Legacy placeholder for rollback."""
        pass
