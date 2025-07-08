"""
BSFS Python Package

A Pythonic wrapper for the BSFS (Block Storage File System) C library,
providing encrypted block-addressable storage with cryptographic isolation.
"""

from .bsfs import (
    BSFS,
    BSFSError,
    BSFSInitError,
    BSFSFileNotFoundError,
    BSFSStorageFullError,
    BSFSCorruptionError,
    create_storage,
    generate_master_key,
)

__version__ = "0.1.0"
__author__ = "BSFS Team"
__email__ = "dev@bsfs.org"

__all__ = [
    "BSFS",
    "BSFSError",
    "BSFSInitError", 
    "BSFSFileNotFoundError",
    "BSFSStorageFullError",
    "BSFSCorruptionError",
    "create_storage",
    "generate_master_key",
]