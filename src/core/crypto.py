"""
Secure Vault - Cryptographic Operations
Implements all encryption, decryption, and key management using libsodium (PyNaCl).
"""

import secrets
from typing import Tuple

from nacl.pwhash import argon2id
from nacl.secret import SecretBox
from nacl.utils import random as nacl_random
from nacl.hash import blake2b
from nacl.encoding import RawEncoder


# Constants
MASTER_KEY_SIZE = 32  # 256 bits
SALT_SIZE = 16  # 128 bits for Argon2id
NONCE_SIZE = 24  # 192 bits for XSalsa20-Poly1305
BLOCK_SIZE = 4 * 1024 * 1024  # 4 MB blocks (optimized for large files)


class CryptoError(Exception):
    """Exception raised for cryptographic operation failures."""
    pass


def generate_master_key() -> bytes:
    """
    Generate a new random master key.
    
    Returns:
        32-byte random master key
    """
    return nacl_random(MASTER_KEY_SIZE)


def generate_salt() -> bytes:
    """
    Generate a random salt for key derivation or encryption.
    
    Returns:
        Random salt bytes
    """
    return nacl_random(SALT_SIZE)


def derive_key_from_pin(pin: str, salt: bytes) -> bytes:
    """
    Derive a key from PIN using Argon2id.
    
    Args:
        pin: User's PIN code
        salt: Salt for key derivation
    
    Returns:
        32-byte derived key
    """
    # Argon2id parameters (secure defaults)
    return argon2id.kdf(
        size=MASTER_KEY_SIZE,
        password=pin.encode("utf-8"),
        salt=salt,
        opslimit=argon2id.OPSLIMIT_MODERATE,
        memlimit=argon2id.MEMLIMIT_MODERATE
    )


def encrypt_master_key(master_key: bytes, pin: str) -> Tuple[bytes, bytes, bytes]:
    """
    Encrypt the master key with a PIN-derived key.
    
    Args:
        master_key: The master key to encrypt
        pin: User's PIN code
    
    Returns:
        Tuple of (encrypted_key, salt, nonce)
    """
    salt = generate_salt()
    derived_key = derive_key_from_pin(pin, salt)
    
    box = SecretBox(derived_key)
    nonce = nacl_random(NONCE_SIZE)
    encrypted = box.encrypt(master_key, nonce)
    
    # SecretBox.encrypt returns nonce + ciphertext, extract just ciphertext
    ciphertext = encrypted.ciphertext
    
    return ciphertext, salt, nonce


def decrypt_master_key(
    encrypted_key: bytes,
    pin: str,
    salt: bytes,
    nonce: bytes
) -> bytes:
    """
    Decrypt the master key with a PIN-derived key.
    
    Args:
        encrypted_key: The encrypted master key
        pin: User's PIN code
        salt: Salt used during encryption
        nonce: Nonce used during encryption
    
    Returns:
        Decrypted master key
    
    Raises:
        CryptoError: If decryption fails (wrong PIN)
    """
    try:
        derived_key = derive_key_from_pin(pin, salt)
        box = SecretBox(derived_key)
        return box.decrypt(encrypted_key, nonce)
    except Exception as e:
        raise CryptoError("Failed to decrypt master key. Invalid PIN.") from e


def compute_key_hash(key: bytes) -> str:
    """
    Compute a hash of the key for verification.
    
    Args:
        key: The key to hash
    
    Returns:
        Hex-encoded hash string
    """
    return blake2b(key, digest_size=32, encoder=RawEncoder).hex()


def verify_key_hash(key: bytes, expected_hash: str) -> bool:
    """
    Verify a key against its expected hash.
    
    Args:
        key: The key to verify
        expected_hash: Expected hex-encoded hash
    
    Returns:
        True if hash matches, False otherwise
    """
    return compute_key_hash(key) == expected_hash


def derive_file_key(master_key: bytes, salt: bytes) -> bytes:
    """
    Derive a file-specific encryption key from the master key.
    
    Args:
        master_key: The master key
        salt: Unique salt for this file/block
    
    Returns:
        32-byte derived key for file encryption
    """
    # Use BLAKE2b for key derivation from master key
    return blake2b(
        master_key + salt,
        digest_size=MASTER_KEY_SIZE,
        encoder=RawEncoder
    )


def encrypt_block(data: bytes, key: bytes) -> Tuple[bytes, bytes]:
    """
    Encrypt a data block.
    
    Args:
        data: Data to encrypt
        key: Encryption key
    
    Returns:
        Tuple of (encrypted_data, nonce)
    """
    box = SecretBox(key)
    nonce = nacl_random(NONCE_SIZE)
    encrypted = box.encrypt(data, nonce)
    return encrypted.ciphertext, nonce


def decrypt_block(encrypted_data: bytes, key: bytes, nonce: bytes) -> bytes:
    """
    Decrypt a data block.
    
    Args:
        encrypted_data: Encrypted data
        key: Decryption key
        nonce: Nonce used during encryption
    
    Returns:
        Decrypted data
    
    Raises:
        CryptoError: If decryption fails
    """
    try:
        box = SecretBox(key)
        return box.decrypt(encrypted_data, nonce)
    except Exception as e:
        raise CryptoError("Failed to decrypt block") from e


def encrypt_metadata(data: str, key: bytes) -> Tuple[bytes, bytes]:
    """
    Encrypt metadata (filenames, comments, etc.).
    
    Args:
        data: String data to encrypt
        key: Encryption key
    
    Returns:
        Tuple of (encrypted_data, nonce)
    """
    return encrypt_block(data.encode("utf-8"), key)


def decrypt_metadata(encrypted_data: bytes, key: bytes, nonce: bytes) -> str:
    """
    Decrypt metadata.
    
    Args:
        encrypted_data: Encrypted metadata
        key: Decryption key
        nonce: Nonce used during encryption
    
    Returns:
        Decrypted string
    """
    decrypted = decrypt_block(encrypted_data, key, nonce)
    return decrypted.decode("utf-8")


def generate_random_password(length: int = 32) -> str:
    """
    Generate a random password for 7z encryption.
    
    Args:
        length: Password length
    
    Returns:
        Random password string
    """
    # Use URL-safe characters for compatibility
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
    return "".join(secrets.choice(alphabet) for _ in range(length))
