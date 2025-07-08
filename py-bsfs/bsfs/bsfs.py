#!/usr/bin/env python3
"""
BSFS Python Wrapper - A Pythonic interface to the BSFS C library

This module provides a high-level Python interface to the BSFS (Block Storage File System)
C library, featuring encrypted block-addressable storage with cryptographic isolation.

Example usage:
    from bsfs import BSFS
    import uuid
    
    # Initialize with master key
    master_key = b'your-32-byte-master-key-here!'
    
    with BSFS('storage.blob', master_key) as fs:
        # Write a file
        file_id = uuid.uuid4()
        fs.write_file(file_id, b'Hello, BSFS!')
        
        # Read it back
        data = fs.read_file(file_id)
        print(data.decode())  # "Hello, BSFS!"
        
        # Delete file
        fs.delete_file(file_id)
"""

import ctypes
import os
import uuid
import sys
from ctypes import (
    Structure, c_char_p, c_uint8, c_uint16, c_uint32, c_uint64,
    c_int, c_size_t, c_void_p, POINTER, byref, create_string_buffer,
    cast, string_at
)
from pathlib import Path
from typing import Union, Optional
import logging

# Set up logging
logger = logging.getLogger(__name__)

class BSFSError(Exception):
    """Base exception for BSFS operations"""
    pass

class BSFSInitError(BSFSError):
    """Raised when BSFS initialization fails"""
    pass

class BSFSFileNotFoundError(BSFSError):
    """Raised when a file is not found"""
    pass

class BSFSStorageFullError(BSFSError):
    """Raised when storage is full"""
    pass

class BSFSCorruptionError(BSFSError):
    """Raised when data corruption is detected"""
    pass

# C structure definitions matching bsfs.h
class BSFSBlockRef(Structure):
    _fields_ = [
        ('partition_id', c_uint8),
        ('block_id', c_uint16)
    ]
    _pack_ = 1

class BSFSFileEntry(Structure):
    _fields_ = [
        ('file_id', c_uint8 * 16),  # UUID
        ('file_size', c_uint32),
        ('block_count', c_uint16),
        ('blocks', BSFSBlockRef * 256)  # BSFS_MAX_FILE_BLOCKS
    ]
    _pack_ = 1

class BSFSBATHeader(Structure):
    _fields_ = [
        ('magic', c_uint32),
        ('version', c_uint32),
        ('block_size', c_uint32),
        ('file_count', c_uint32),
        ('free_block_count', c_uint32),
        ('timestamp', c_uint64),
        ('partition_id', c_uint8),
        ('reserved', c_uint8 * 7)
    ]
    _pack_ = 1

class BSFSBAT(Structure):
    _fields_ = [
        ('header', BSFSBATHeader),
        ('files', BSFSFileEntry * 64),
        ('free_blocks', c_uint16 * 1024),  # BSFS_BLOCKS_PER_PARTITION
        ('padding', c_uint8 * 1024)
    ]
    _pack_ = 1

class BSFSPartition(Structure):
    _fields_ = [
        ('partition_id', c_uint8),
        ('blob_file', c_void_p),  # FILE*
        ('partition_offset', c_uint64),
        ('block_size', c_uint32),
        ('encryption_key', c_uint8 * 32),  # BSFS_AES_KEY_SIZE
        ('bat', POINTER(BSFSBAT)),
        ('bat_dirty', c_int)
    ]

class BSFSTenant(Structure):
    _fields_ = [
        ('blob_path', c_char_p),
        ('blob_file', c_void_p),  # FILE*
        ('master_key', c_uint8 * 32),  # BSFS_AES_KEY_SIZE
        ('partitions', BSFSPartition * 256),  # BSFS_MAX_PARTITIONS
        ('partition_count', c_int)
    ]

class BSFSLibrary:
    """Low-level wrapper for the BSFS C library"""
    
    def __init__(self, library_path: Optional[str] = None):
        self._lib = self._load_library(library_path)
        self._setup_function_signatures()
    
    def _load_library(self, library_path: Optional[str]) -> ctypes.CDLL:
        """Load the BSFS shared library"""
        if library_path:
            lib_path = Path(library_path)
        else:
            # Try to find the library in package directory first
            package_dir = Path(__file__).parent
            possible_paths = [
                package_dir / 'libbsfs.so',
                package_dir / 'libbsfs.dylib',
                package_dir / 'bsfs.dll',
                'libbsfs.so',
                './libbsfs.so',
                '/usr/local/lib/libbsfs.so',
                '/usr/lib/libbsfs.so',
                'libbsfs.dylib',  # macOS
                './libbsfs.dylib',
                'bsfs.dll'  # Windows
            ]
            
            lib_path = None
            for path in possible_paths:
                if Path(path).exists():
                    lib_path = Path(path)
                    break
            
            if not lib_path:
                raise BSFSInitError(
                    f"Could not find BSFS library. Tried: {possible_paths}. "
                    "Please compile the library first with 'make libbsfs.so' or "
                    "specify the library path explicitly."
                )
        
        try:
            return ctypes.CDLL(str(lib_path))
        except OSError as e:
            raise BSFSInitError(f"Failed to load BSFS library from {lib_path}: {e}")
    
    def _setup_function_signatures(self):
        """Setup function signatures for type safety"""
        # bsfs_tenant_init
        self._lib.bsfs_tenant_init.argtypes = [
            POINTER(BSFSTenant), c_char_p, POINTER(c_uint8)
        ]
        self._lib.bsfs_tenant_init.restype = c_int
        
        # bsfs_tenant_cleanup
        self._lib.bsfs_tenant_cleanup.argtypes = [POINTER(BSFSTenant)]
        self._lib.bsfs_tenant_cleanup.restype = None
        
        # bsfs_write_file
        self._lib.bsfs_write_file.argtypes = [
            POINTER(BSFSTenant), POINTER(c_uint8), POINTER(c_uint8), c_size_t
        ]
        self._lib.bsfs_write_file.restype = c_int
        
        # bsfs_read_file
        self._lib.bsfs_read_file.argtypes = [
            POINTER(BSFSTenant), POINTER(c_uint8), POINTER(POINTER(c_uint8)), POINTER(c_size_t)
        ]
        self._lib.bsfs_read_file.restype = c_int
        
        # bsfs_delete_file
        self._lib.bsfs_delete_file.argtypes = [
            POINTER(BSFSTenant), POINTER(c_uint8)
        ]
        self._lib.bsfs_delete_file.restype = c_int
        
        # libc free (for memory allocated by C library)
        try:
            self._lib.free.argtypes = [c_void_p]
            self._lib.free.restype = None
        except AttributeError:
            # Try to get free from libc
            import platform
            if platform.system() == 'Windows':
                libc = ctypes.CDLL('msvcrt.dll')
            else:
                libc = ctypes.CDLL(None)
            self._free = libc.free
            self._free.argtypes = [c_void_p]
            self._free.restype = None
        else:
            self._free = self._lib.free

class BSFS:
    """High-level Pythonic interface to BSFS"""
    
    def __init__(self, blob_path: Union[str, Path], master_key: bytes, 
                 library_path: Optional[str] = None):
        """
        Initialize BSFS instance
        
        Args:
            blob_path: Path to the blob storage file
            master_key: 32-byte master encryption key
            library_path: Optional path to BSFS shared library
            
        Raises:
            BSFSInitError: If initialization fails
            ValueError: If master_key is not 32 bytes
        """
        if len(master_key) != 32:
            raise ValueError("Master key must be exactly 32 bytes")
        
        self.blob_path = Path(blob_path)
        self.master_key = master_key
        self._lib = BSFSLibrary(library_path)
        self._tenant = BSFSTenant()
        self._initialized = False
        
        # Convert master key to C array
        key_array = (c_uint8 * 32)()
        for i, byte in enumerate(master_key):
            key_array[i] = byte
        
        # Initialize tenant
        blob_path_bytes = str(self.blob_path).encode('utf-8')
        result = self._lib._lib.bsfs_tenant_init(
            byref(self._tenant), 
            blob_path_bytes, 
            key_array
        )
        
        if result != 0:
            raise BSFSInitError(f"Failed to initialize BSFS tenant: error code {result}")
        
        self._initialized = True
        logger.info(f"BSFS initialized with blob file: {self.blob_path}")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
    
    def close(self):
        """Cleanup BSFS resources"""
        if self._initialized:
            self._lib._lib.bsfs_tenant_cleanup(byref(self._tenant))
            self._initialized = False
            logger.info("BSFS resources cleaned up")
    
    def __del__(self):
        """Destructor"""
        self.close()
    
    def _uuid_to_c_array(self, file_id: uuid.UUID) -> ctypes.Array:
        """Convert Python UUID to C uint8 array"""
        uuid_bytes = file_id.bytes
        uuid_array = (c_uint8 * 16)()
        for i, byte in enumerate(uuid_bytes):
            uuid_array[i] = byte
        return uuid_array
    
    def _check_initialized(self):
        """Check if BSFS is initialized"""
        if not self._initialized:
            raise BSFSError("BSFS instance has been closed")
    
    def write_file(self, file_id: uuid.UUID, data: bytes) -> None:
        """
        Write a file to BSFS storage
        
        Args:
            file_id: UUID identifying the file
            data: File content as bytes
            
        Raises:
            BSFSError: If write operation fails
            BSFSStorageFullError: If storage is full
        """
        self._check_initialized()
        
        if not isinstance(file_id, uuid.UUID):
            raise TypeError("file_id must be a UUID object")
        
        if not isinstance(data, bytes):
            raise TypeError("data must be bytes")
        
        if len(data) == 0:
            raise ValueError("Cannot write empty file")
        
        uuid_array = self._uuid_to_c_array(file_id)
        data_ptr = cast(data, POINTER(c_uint8))
        
        result = self._lib._lib.bsfs_write_file(
            byref(self._tenant),
            uuid_array,
            data_ptr,
            len(data)
        )
        
        if result != 0:
            if result == -1:
                raise BSFSStorageFullError("Storage is full or file too large")
            else:
                raise BSFSError(f"Failed to write file: error code {result}")
        
        logger.debug(f"Successfully wrote file {file_id} ({len(data)} bytes)")
    
    def read_file(self, file_id: uuid.UUID) -> bytes:
        """
        Read a file from BSFS storage
        
        Args:
            file_id: UUID identifying the file
            
        Returns:
            File content as bytes
            
        Raises:
            BSFSFileNotFoundError: If file doesn't exist
            BSFSCorruptionError: If file data is corrupted
        """
        self._check_initialized()
        
        if not isinstance(file_id, uuid.UUID):
            raise TypeError("file_id must be a UUID object")
        
        uuid_array = self._uuid_to_c_array(file_id)
        data_ptr = POINTER(c_uint8)()
        size = c_size_t()
        
        result = self._lib._lib.bsfs_read_file(
            byref(self._tenant),
            uuid_array,
            byref(data_ptr),
            byref(size)
        )
        
        if result != 0:
            if result == -1:
                raise BSFSFileNotFoundError(f"File {file_id} not found")
            else:
                raise BSFSCorruptionError(f"Failed to read file: error code {result}")
        
        try:
            # Copy data from C memory to Python bytes
            data_bytes = string_at(data_ptr, size.value)
            return data_bytes
        finally:
            # Free C-allocated memory
            if data_ptr:
                self._lib._free(cast(data_ptr, c_void_p))
        
        logger.debug(f"Successfully read file {file_id} ({size.value} bytes)")
    
    def delete_file(self, file_id: uuid.UUID) -> None:
        """
        Delete a file from BSFS storage
        
        Args:
            file_id: UUID identifying the file
            
        Raises:
            BSFSFileNotFoundError: If file doesn't exist
        """
        self._check_initialized()
        
        if not isinstance(file_id, uuid.UUID):
            raise TypeError("file_id must be a UUID object")
        
        uuid_array = self._uuid_to_c_array(file_id)
        
        result = self._lib._lib.bsfs_delete_file(
            byref(self._tenant),
            uuid_array
        )
        
        if result != 0:
            if result == -1:
                raise BSFSFileNotFoundError(f"File {file_id} not found")
            else:
                raise BSFSError(f"Failed to delete file: error code {result}")
        
        logger.debug(f"Successfully deleted file {file_id}")
    
    def file_exists(self, file_id: uuid.UUID) -> bool:
        """
        Check if a file exists in BSFS storage
        
        Args:
            file_id: UUID identifying the file
            
        Returns:
            True if file exists, False otherwise
        """
        try:
            # Try to read the file - if it succeeds, file exists
            data = self.read_file(file_id)
            return True
        except BSFSFileNotFoundError:
            return False
    
    def get_storage_info(self) -> dict:
        """
        Get storage information
        
        Returns:
            Dictionary with storage statistics
        """
        self._check_initialized()
        
        # Access the BAT through the partition
        if self._tenant.partition_count > 0:
            partition = self._tenant.partitions[0]
            if partition.bat:
                bat = partition.bat.contents
                header = bat.header
                
                total_blocks = 1024  # BSFS_BLOCKS_PER_PARTITION
                used_blocks = total_blocks - header.free_block_count
                
                return {
                    'blob_path': str(self.blob_path),
                    'partition_count': self._tenant.partition_count,
                    'file_count': header.file_count,
                    'block_size': header.block_size,
                    'total_blocks': total_blocks,
                    'used_blocks': used_blocks,
                    'free_blocks': header.free_block_count,
                    'storage_utilization': (used_blocks / total_blocks) * 100,
                    'total_capacity': total_blocks * header.block_size,
                    'used_capacity': used_blocks * header.block_size,
                    'free_capacity': header.free_block_count * header.block_size
                }
        
        return {
            'blob_path': str(self.blob_path),
            'partition_count': 0,
            'error': 'No partitions initialized'
        }

# Convenience functions for common operations
def create_storage(blob_path: Union[str, Path], master_key: bytes) -> BSFS:
    """
    Create a new BSFS storage instance
    
    Args:
        blob_path: Path to the blob storage file
        master_key: 32-byte master encryption key
        
    Returns:
        BSFS instance
    """
    return BSFS(blob_path, master_key)

def generate_master_key() -> bytes:
    """
    Generate a random 32-byte master key
    
    Returns:
        32 bytes of random data suitable for use as master key
    """
    import secrets
    return secrets.token_bytes(32)

# Example usage and testing
if __name__ == "__main__":
    import tempfile
    import shutil
    
    def test_bsfs():
        """Basic test of BSFS functionality"""
        # Create temporary directory for testing
        test_dir = Path(tempfile.mkdtemp())
        blob_path = test_dir / "test.blob"
        
        try:
            # Generate master key
            master_key = generate_master_key()
            print(f"Generated master key: {master_key.hex()}")
            
            # Initialize BSFS
            with BSFS(blob_path, master_key) as fs:
                print(f"Initialized BSFS with blob: {blob_path}")
                
                # Test file operations
                file_id = uuid.uuid4()
                test_data = b"Hello, BSFS from Python!"
                
                print(f"Writing file {file_id}")
                fs.write_file(file_id, test_data)
                
                print(f"Reading file {file_id}")
                read_data = fs.read_file(file_id)
                assert read_data == test_data, "Data mismatch!"
                print(f"Read data: {read_data.decode()}")
                
                print(f"Checking if file exists: {fs.file_exists(file_id)}")
                
                # Get storage info
                info = fs.get_storage_info()
                print(f"Storage info: {info}")
                
                print(f"Deleting file {file_id}")
                fs.delete_file(file_id)
                
                print(f"Checking if file exists after deletion: {fs.file_exists(file_id)}")
            
            print("All tests passed!")
            
        except Exception as e:
            print(f"Test failed: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Cleanup
            shutil.rmtree(test_dir, ignore_errors=True)
    
    test_bsfs()
