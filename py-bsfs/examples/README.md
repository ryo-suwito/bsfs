# BSFS Python Examples

This directory contains comprehensive examples demonstrating how to use the BSFS Python wrapper for various real-world tasks.

## Examples Overview

### 1. JSON CRUD Demo (`json_crud_demo.py`)
**What it does:** Demonstrates how to use BSFS as a JSON document store with full CRUD (Create, Read, Update, Delete) operations.

**Features:**
- Document collections (like databases)
- Query operations with filters
- Document indexing and metadata
- Collection management

**Usage:**
```bash
python json_crud_demo.py
```

**Example output:**
```
✅ Created document abc123 in collection 'users'
✅ Updated document abc123  
🔍 Found 2 developers
📊 Total documents: 5
```

### 2. File Backup Demo (`file_backup_demo.py`)
**What it does:** Shows how to backup and restore native Linux files using BSFS as encrypted storage.

**Features:**
- Backup individual files or entire directories
- File deduplication (same content stored once)
- Metadata preservation (permissions, timestamps)
- Incremental backups
- Selective restore

**Usage:**
```bash
python file_backup_demo.py
```

**Example output:**
```
📁 Stored file content: /tmp/config.txt (245 bytes)
✅ Backed up: /tmp/config.txt -> backup_20241201_143022
🔄 File already exists (deduplicated): /tmp/config.txt
✅ Restored backup 'full_backup': 6 files
```

### 3. Performance Test (`performance_test.py`)
**What it does:** Comprehensive performance testing of BSFS operations.

**Features:**
- Small file performance (1KB-10KB)
- Large file performance (1MB-10MB)
- Concurrent operations testing
- Storage efficiency analysis
- Throughput measurements

**Usage:**
```bash
python performance_test.py
```

**Example output:**
```
🚀 Write throughput: 15.23 MB/s
🚀 Read throughput: 28.45 MB/s
🧵 8 threads: 234.5 ops/s
📊 All data integrity tests passed ✅
```

### 4. Run All Examples (`run_all_examples.py`)
**What it does:** Runs all examples in sequence for a complete demonstration.

**Usage:**
```bash
python run_all_examples.py
```

## Quick Start Guide

### Basic BSFS Usage

```python
import bsfs
import uuid

# Generate a master key
master_key = bsfs.generate_master_key()

# Create/open BSFS storage
with bsfs.BSFS('storage.blob', master_key) as fs:
    # Write a file
    file_id = uuid.uuid4()
    fs.write_file(file_id, b'Hello, BSFS!')
    
    # Read the file
    data = fs.read_file(file_id)
    print(data.decode())  # "Hello, BSFS!"
    
    # Delete the file
    fs.delete_file(file_id)
```

### CLI Usage

```bash
# Initialize new storage
bsfs-cli init storage.blob --key-file master.key --generate-key

# Show storage info
bsfs-cli info storage.blob --key-file master.key

# Write and read files (more CLI commands coming soon)
```

## Common Use Cases

### 1. Encrypted Document Storage
Perfect for storing sensitive documents, configuration files, or personal data with strong encryption.

### 2. Application Data Storage
Use as a backend for applications that need secure, block-level storage with UUID-based file identification.

### 3. Backup and Archival
Create encrypted backups of important files with deduplication and metadata preservation.

### 4. Development and Testing
Use in development environments where you need isolated, encrypted storage that can be easily created and destroyed.

## Example Data

The examples create various types of sample data:

- **JSON documents:** User profiles, product catalogs, orders
- **Text files:** Configuration files, documentation, logs
- **Binary data:** Simulated images, compiled binaries
- **Directory structures:** Nested folders with mixed content

## Performance Characteristics

Based on the performance tests:

- **Small files (1-10KB):** ~1000+ ops/second
- **Large files (1-10MB):** ~20-50 MB/s throughput
- **Concurrent operations:** Scales well with multiple threads
- **Storage efficiency:** Strong data integrity, effective deduplication

## Security Features

All examples demonstrate:

- **AES-256-CBC encryption** for all stored data
- **Cryptographic isolation** between different storage instances
- **Secure key derivation** using HKDF
- **Random block allocation** for additional security

## Tips for Real-World Usage

1. **Key Management:** Always store master keys securely, separate from blob files
2. **Error Handling:** Wrap operations in try-catch blocks for production use
3. **Backup Strategy:** Consider backing up both blob files and master keys
4. **Performance:** For high-throughput scenarios, consider connection pooling
5. **Security:** Use secure random generation for master keys in production

## Troubleshooting

### Common Issues

1. **"Library not found"** - Make sure `libbsfs.so` is in the package directory
2. **"Permission denied"** - Check file permissions on blob files
3. **"Invalid key"** - Ensure master key is exactly 32 bytes
4. **"File not found"** - Check that UUID exists before reading

### Debug Mode

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Next Steps

After running these examples, you might want to:

1. **Integrate with your application** - Use the patterns shown in your own code
2. **Extend functionality** - Add your own features like compression or caching
3. **Scale up** - Test with larger datasets and more concurrent operations
4. **Contribute** - Help improve BSFS by reporting issues or contributing code

## Links

- [BSFS C Library Documentation](../README.md)
- [Python Package Documentation](../bsfs/)
- [CLI Reference](../bsfs/cli.py)
- [Performance Benchmarks](performance_test.py)