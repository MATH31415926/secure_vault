"""
Secure Vault - Database Management
SQLite database connection and management with per-repository support.
"""

import os
import sqlite3
from pathlib import Path
from typing import Optional, List, Tuple
from contextlib import contextmanager

from src.core.config import get_config


class RepositoryDatabase:
    """SQLite database manager for a single repository."""
    
    VAULT_DIR = ".vault"
    DB_NAME = "vault.db"
    BLOCKS_DIR = "blocks"
    
    def __init__(self, repo_path: str):
        self._repo_path = Path(repo_path)
        self._vault_path = self._repo_path / self.VAULT_DIR
        self._db_path = self._vault_path / self.DB_NAME
        self._blocks_path = self._vault_path / self.BLOCKS_DIR
        self._connection: Optional[sqlite3.Connection] = None
        self._transaction_depth = 0
    
    @property
    def blocks_path(self) -> Path:
        """Get the blocks storage path."""
        return self._blocks_path
    
    def init_directory(self) -> None:
        """Initialize repository directory structure."""
        self._vault_path.mkdir(parents=True, exist_ok=True)
        self._blocks_path.mkdir(exist_ok=True)
    
    def connect(self) -> None:
        """Establish database connection."""
        # Ensure drive exists on Windows before trying to mkdir
        if os.name == 'nt':
            drive = os.path.splitdrive(str(self._repo_path))[0]
            if drive and not Path(drive + "\\").exists():
                raise FileNotFoundError(f"无法访问驱动器 '{drive}'，请检查是否已连接。")

        # Ensure directory exists
        self._vault_path.mkdir(parents=True, exist_ok=True)
        
        self._connection = sqlite3.connect(
            str(self._db_path),
            check_same_thread=False
        )
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._init_schema()
    
    def close(self) -> None:
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
    
    @contextmanager
    def transaction(self):
        """Context manager for database transactions with nesting support."""
        conn = self._connection
        if conn is None:
            yield
            return
            
        self._transaction_depth += 1
        try:
            yield
            if self._transaction_depth == 1:
                if self._connection and self._connection == conn:
                    self._connection.commit()
        except Exception:
            if self._transaction_depth == 1:
                if self._connection and self._connection == conn:
                    try:
                        self._connection.rollback()
                    except sqlite3.ProgrammingError:
                        pass # Connection already closed
            raise
        finally:
            self._transaction_depth -= 1
    
    def execute(
        self,
        query: str,
        params: Tuple = ()
    ) -> sqlite3.Cursor:
        """Execute a single query."""
        return self._connection.execute(query, params)
    
    def executemany(
        self,
        query: str,
        params_list: List[Tuple]
    ) -> sqlite3.Cursor:
        """Execute a query with multiple parameter sets."""
        return self._connection.executemany(query, params_list)
    
    def fetchone(
        self,
        query: str,
        params: Tuple = ()
    ) -> Optional[sqlite3.Row]:
        """Execute query and fetch one result."""
        cursor = self.execute(query, params)
        return cursor.fetchone()
    
    def fetchall(
        self,
        query: str,
        params: Tuple = ()
    ) -> List[sqlite3.Row]:
        """Execute query and fetch all results."""
        cursor = self.execute(query, params)
        return cursor.fetchall()
    
    def _init_schema(self) -> None:
        """Initialize database schema for repository-specific data."""
        schema = """
        -- Virtual file structure (encrypted metadata)
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parent_id INTEGER REFERENCES files(id) ON DELETE CASCADE,
            name_encrypted BLOB NOT NULL,
            name_nonce BLOB NOT NULL,
            is_directory INTEGER DEFAULT 0,
            size INTEGER DEFAULT 0,
            comment_encrypted BLOB,
            comment_nonce BLOB,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Block storage with deduplication
        CREATE TABLE IF NOT EXISTS blocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hash TEXT NOT NULL UNIQUE,
            relative_path TEXT NOT NULL,
            size INTEGER NOT NULL,
            salt BLOB NOT NULL,
            nonce BLOB NOT NULL,
            reference_count INTEGER DEFAULT 1
        );
        
        -- File-to-block mapping
        CREATE TABLE IF NOT EXISTS file_blocks (
            file_id INTEGER NOT NULL REFERENCES files(id) ON DELETE CASCADE,
            block_id INTEGER NOT NULL REFERENCES blocks(id),
            block_order INTEGER NOT NULL,
            PRIMARY KEY (file_id, block_order)
        );

        -- Operations for crash recovery and resumable tasks
        CREATE TABLE IF NOT EXISTS operations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL, -- 'import', 'export'
            status TEXT NOT NULL, -- 'pending', 'processing', 'cancelling', 'completed', 'failed'
            source_paths TEXT NOT NULL, -- JSON list of paths
            target_path TEXT, -- JSON path or dir ID
            parent_id INTEGER, -- For imports
            total_size INTEGER DEFAULT 0,
            processed_size INTEGER DEFAULT 0,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Indexes for performance
        CREATE INDEX IF NOT EXISTS idx_files_parent ON files(parent_id);
        CREATE INDEX IF NOT EXISTS idx_blocks_hash ON blocks(hash);
        CREATE INDEX IF NOT EXISTS idx_file_blocks_file ON file_blocks(file_id);
        """
        self._connection.executescript(schema)
        self._connection.commit()


class GlobalDatabase:
    """SQLite database for global app data (repositories list)."""
    
    def __init__(self):
        self._connection: Optional[sqlite3.Connection] = None
        self._db_path = get_config().database_path
    
    def connect(self) -> None:
        """Establish database connection."""
        self._connection = sqlite3.connect(
            str(self._db_path),
            check_same_thread=False
        )
        self._connection.row_factory = sqlite3.Row
        self._init_schema()
    
    def close(self) -> None:
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
    
    def execute(
        self,
        query: str,
        params: Tuple = ()
    ) -> sqlite3.Cursor:
        """Execute a single query."""
        return self._connection.execute(query, params)
    
    def fetchone(
        self,
        query: str,
        params: Tuple = ()
    ) -> Optional[sqlite3.Row]:
        """Execute query and fetch one result."""
        cursor = self.execute(query, params)
        return cursor.fetchone()
    
    def fetchall(
        self,
        query: str,
        params: Tuple = ()
    ) -> List[sqlite3.Row]:
        """Execute query and fetch all results."""
        cursor = self.execute(query, params)
        return cursor.fetchall()
    
    def _init_schema(self) -> None:
        """Initialize database schema for global data."""
        schema = """
        -- Repositories table (metadata only)
        CREATE TABLE IF NOT EXISTS repositories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            path TEXT NOT NULL UNIQUE,
            max_capacity INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        self._connection.executescript(schema)
        self._connection.commit()


# Global database instance (for repository list)
_global_db: Optional[GlobalDatabase] = None

# Current repository database
_repo_db: Optional[RepositoryDatabase] = None
_current_repo_path: Optional[str] = None


def get_global_database() -> GlobalDatabase:
    """Get the global database instance."""
    global _global_db
    if _global_db is None:
        _global_db = GlobalDatabase()
        _global_db.connect()
    return _global_db


def get_repository_database(repo_path: str = None) -> Optional[RepositoryDatabase]:
    """Get the repository database for the given path."""
    global _repo_db, _current_repo_path
    
    if repo_path is None:
        return _repo_db
        
    # Normalize path for reliable comparison
    try:
        norm_path = str(Path(repo_path).resolve())
    except Exception:
        norm_path = repo_path
    
    # CASE 1: Already have the correct database and it's connected
    if _current_repo_path == norm_path and _repo_db is not None:
        if _repo_db._connection is not None:
            return _repo_db
        else:
            # Reconnect if died
            _repo_db.connect()
            return _repo_db
    
    # CASE 2: Switching to a different repository or first-time connection
    # We do NOT update the globals until we know the connection works
    new_db = RepositoryDatabase(repo_path)
    new_db.connect() # This might raise FileNotFoundError if drive/path is invalid
    
    # If we got here, connection succeeded. Now it is safe to update globals.
    if _repo_db is not None:
        _repo_db.close()
    
    _repo_db = new_db
    _current_repo_path = norm_path
    
    return _repo_db


def close_repository_database() -> None:
    """Close the current repository database."""
    global _repo_db, _current_repo_path
    if _repo_db is not None:
        try:
            _repo_db.close()
        except Exception:
            pass
        _repo_db = None
        _current_repo_path = None


def close_all_databases() -> None:
    """Close all database connections."""
    global _global_db
    close_repository_database()
    if _global_db is not None:
        _global_db.close()
        _global_db = None


# Legacy compatibility - deprecated, use get_global_database or get_repository_database
def get_database():
    """Legacy function - returns global database."""
    return get_global_database()


def close_database():
    """Legacy function - closes all databases."""
    close_all_databases()
