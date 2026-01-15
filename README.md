# BSFS - Block Storage File System

A C implementation of the BSFS specification providing encrypted block-addressable storage with cryptographic isolation.

## Features

- **Binary-only formats** - No JSON dependencies, all data structures are raw bytes
- **AES-256-CBC encryption** for Block Allocation Tables (BAT)
- **Random block allocation** for security through cryptographic confusion
- **Atomic file updates** using copy-on-write semantics
- **HKDF key derivation** for tenant/partition isolation
- **Configurable block sizes** (default 2MB)
- **Multi-tenant support** with cryptographic isolation

## Architecture

```
Tenant Storage (blob file)
├── Partition 0
│   ├── BAT (encrypted)
│   └── Blocks 0-1023 (raw bytes)
├── Partition 1
│   ├── BAT (encrypted)
│   └── Blocks 0-1023 (raw bytes)
└── ...
```

## Build Requirements

```bash
# Ubuntu/Debian
sudo apt-get install libssl-dev uuid-dev

# Build
make all

# Run tests
make test

# Install system-wide
sudo make install
```

## Usage Example

```c
#include "bsfs.h"

int main() {
    // Initialize tenant with master key
    uint8_t master_key[32] = {/* your key */};
    bsfs_tenant_t tenant;
    
    if (bsfs_tenant_init(&tenant, "tenant.blob", master_key) != 0) {
        return -1;
    }
    
    // Write file
    uuid_t file_id;
    uuid_generate(file_id);
    const char *data = "Hello, BSFS!";
    
    if (bsfs_write_file(&tenant, file_id, (uint8_t*)data, strlen(data)) != 0) {
        return -1;
    }
    
    // Read file
    uint8_t *read_data;
    size_t read_size;
    
    if (bsfs_read_file(&tenant, file_id, &read_data, &read_size) != 0) {
        return -1;
    }
    
    printf("Read: %.*s\n", (int)read_size, read_data);
    free(read_data);
    
    // Cleanup
    bsfs_tenant_cleanup(&tenant);
    return 0;
}
```

## Security Properties

- **Encrypted metadata**: BAT contains file-to-block mappings, encrypted per partition
- **Random allocation**: Blocks assigned randomly to prevent temporal correlation
- **Tenant isolation**: Each tenant has separate blob file and key derivation
- **Atomic updates**: BAT update is commit point, ensuring consistency

## API Reference

### Core Functions

- `bsfs_tenant_init()` - Initialize tenant with master key
- `bsfs_tenant_cleanup()` - Cleanup tenant resources
- `bsfs_write_file()` - Write file with atomic updates
- `bsfs_read_file()` - Read file by UUID
- `bsfs_delete_file()` - Delete file and free blocks

### Configuration

- `BSFS_BLOCK_SIZE_DEFAULT` - Default block size (2MB)
- `BSFS_BLOCKS_PER_PARTITION` - Max blocks per partition (1024)
- `BSFS_MAX_FILE_BLOCKS` - Max blocks per file (256)

## Current Limitations

- Single partition implementation (easily extendable)
- 64 files per partition maximum
- 2GB maximum file size (512MB with current settings)
- No built-in compression or deduplication
- No file listing/enumeration API
- No multi-threading support
- No streaming I/O for large files

## Files

- `bsfs.h` - Header with API and data structures
- `bsfs.c` - Core implementation
- `test_bsfs.c` - Comprehensive test suite
- `Makefile` - Build configuration
- `README.md` - This documentation

## Implementation Notes

- Uses OpenSSL for encryption and key derivation
- BAT structures allocated dynamically to avoid stack overflow
- File size stored in BAT for exact reconstruction
- Copy-on-write semantics ensure atomic updates
- Random block insertion maintains security properties

## Testing

The test suite covers:
- Basic file operations (create, read, update, delete)
- Large file handling (multi-block files)
- Multiple file management
- Atomic update verification
- Error handling

All tests pass successfully with the current implementation.

## Development Roadmap

### High Priority
- **[Completed] Multi-partition support** - Extend beyond single partition for larger storage
- **[Completed] Error recovery** - BAT corruption detection and recovery mechanisms (SHA256 checksums)
- **[Completed] Python wrapper** - ctypes-based bindings for easy Python integration

### Medium Priority
- **Increased file limits** - Expand from 64 to 1024+ files per partition
- **Configurable block sizes** - Support 64MB, 128MB block options
- **File enumeration API** - List files in tenant/partition
- **Background garbage collection** - Optimize freed block management
- **Streaming I/O** - Support for large file operations without full memory load
- **Multi-threading** - Thread-safe operations with proper locking
- **Performance benchmarks** - Comprehensive performance testing suite
- **Node.js bindings** - Native module for web applications

### Low Priority
- **File metadata** - Creation/modification timestamps
- **Compression support** - LZ4/zstd integration for space efficiency
- **Deduplication** - Block-level deduplication for storage optimization
- **File versioning** - Snapshot capabilities for data history

### Future Possibilities
- **Distributed storage** - Multi-node BSFS clusters
- **Encryption at rest** - Block-level encryption in addition to BAT
- **Replication** - Cross-node data redundancy
- **Web interface** - REST API for file operations
- **FUSE integration** - Mount BSFS as filesystem
- **Backup/restore** - Efficient tenant backup mechanisms

## Python Wrapper Roadmap

### Phase 1: Basic ctypes wrapper
```python
import ctypes
from ctypes import c_char_p, c_uint8, c_size_t, POINTER

class BSFS:
    def __init__(self, blob_path: str, master_key: bytes):
        # Load shared library and wrap functions
        pass
    
    def write_file(self, file_id: str, data: bytes) -> bool:
        # Wrapper for bsfs_write_file
        pass
    
    def read_file(self, file_id: str) -> bytes:
        # Wrapper for bsfs_read_file
        pass
```

### Phase 2: Pythonic interface
- UUID object integration
- Context managers for resource cleanup
- Exception handling instead of error codes
- Async I/O support

### Phase 3: Advanced features
- File-like object interface
- Integration with pathlib
- Streaming support for large files
- Connection pooling for multi-tenant apps

This roadmap provides a clear path for extending BSFS from a solid C foundation to a comprehensive storage solution with modern language bindings.