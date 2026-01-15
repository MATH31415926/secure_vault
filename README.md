# Secure Vault

A cross-platform encrypted file storage application with block-level deduplication.

## Security Architecture

### Encryption
- **Algorithm**: XSalsa20-Poly1305 (via libsodium/PyNaCl)
- **Key Size**: 256-bit master key
- **Block Size**: 4 MB per encrypted block
- **Per-Block Key Derivation**: Each block uses a unique random salt, and the actual encryption key is derived using `BLAKE2b(master_key + salt)`. This ensures that even blocks encrypted with the same master key have completely different ciphertext, preventing pattern analysis attacks.
- **Metadata**: File names and comments are encrypted with the master key

### Key Management
- **PIN Protection**: Master key is encrypted using Argon2id-derived key from user PIN
- **Key Derivation**: Argon2id with MODERATE cost parameters
- **Verification**: BLAKE2b hash (32 bytes) stored for master key verification
- **Per-Block Keys**: Each block uses a unique salt with BLAKE2b key derivation

### Storage
- **Deduplication**: Content-addressed storage using BLAKE2b file hashing
- **Lazy Loading**: Directory contents loaded on-demand for billion-file scale
- **Database**: Per-repository SQLite with encrypted metadata

## Requirements

```
Python >= 3.10
PyQt6
PyNaCl
```

## Installation

```bash
git clone <repository>
cd secure_vault
pip install -r requirements.txt
python main.py
```

## Usage

### Initial Setup
1. Launch application → Set PIN (minimum 4 digits)
2. Configure master key:
   - **Random**: Auto-generate 256-bit key (recommended)
   - **Manual**: Enter 64-character hex string
3. Create repository → Select folder and capacity limit

### Daily Use
1. Enter PIN to decrypt master key
2. Select repository
3. Drag & drop files to import (encrypted automatically)
4. Right-click to export, rename, delete, or add comments

### Features
- **Import**: Drag files/folders → Split into 4MB blocks → Encrypt → Deduplicate
- **Export**: Select files → Decrypt blocks → Reconstruct original files
- **Multi-repo**: Each repository has independent database and block storage

## File Structure

```
repository/
├── .vault/
│   ├── database.db      # Encrypted file metadata
│   ├── blocks/          # Encrypted 4MB data blocks
│   │   ├── 00/          # Hash-based subdirectories
│   │   ├── 01/
│   │   └── ...
│   └── config.json      # Repository configuration
```

## License

MIT
