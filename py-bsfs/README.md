# BSFS Python Wrapper

A Pythonic interface to the BSFS (Block Storage File System) C library, providing encrypted block-addressable storage with cryptographic isolation.

## Features

- **High-level Pythonic API** - Clean, intuitive interface for Python developers
- **Type safety** - Full type hints and runtime type checking
- **Memory management** - Automatic cleanup of C-allocated memory
- **Context managers** - Proper resource management with `with` statements
- **Exception handling** - Meaningful Python exceptions instead of error codes
- **UUID support** - Native Python UUID objects for file identification
- **Command-line interface** - Full-featured CLI for storage operations
- **Comprehensive testing** - Complete test suite with pytest

## Installation

### Prerequisites

First, you need to build the BSFS C library:

```bash
# Install C dependencies
sudo apt-get install libssl-dev uuid-dev build-essential

# Build the C library
git clone https://github.com/your-org/bsfs.git
cd bsfs
make libbsfs.so
```

### Install Python Package

```bash
# Install from source
pip install .

# Install in development mode
pip install -e ".[dev]"

# Or install from PyPI (when published)
pip install bsfs
```

## Quick Start

### Basic Usage

```python
from bsfs import BSFS, generate_master_key
import uuid

# Generate a master key (store this securely!)
master_key = generate_master_key()

# Initialize BSFS storage
with BSFS('storage.blob', master_key) as fs:
    # Write a file
    file_id = uuid.uuid4()
    fs.write_file(file_id, b'Hello, BSFS!')
    
    # Read it back
    data = fs.read_file(file_id)
    print(data.decode())  # "Hello, BSFS!"
    
    # Check if file exists
    if fs.file_exists(file_id):
        print("File exists!")
    
    # Get storage info
    info = fs.get_storage_info()
    print(f"Storage utilization: {info['storage_utilization']:.1f}%")
    
    # Delete file
    fs.delete_file(file_id)
```

### Working with Binary Data

```python
import json
from bsfs import BSFS

# Store structured data
data = {"name": "Alice", "age": 30, "city": "San Francisco"}
json_bytes = json.dumps(data).encode()

with BSFS('data.blob', master_key) as fs:
    file_id = uuid.uuid4()
    fs.write_file(file_id, json_bytes)
    
    # Read back and parse
    stored_bytes = fs.read_file(file_id)
    restored_data = json.loads(stored_bytes.decode())
    print(restored_data)  # {'name': 'Alice', 'age': 30, 'city': 'San Francisco'}
```

### Handling Large Files

```python
from pathlib import Path

# Store a large file
large_file = Path("document.pdf")
file_content = large_file.read_bytes()

with BSFS('documents.blob', master_key) as fs:
    file_id = uuid.uuid4()
    fs.write_file(file_id, file_content)
    
    # Read back and save
    restored_content = fs.read_file(file_id)
    Path("restored_document.pdf").write_bytes(restored_content)
```

## Command Line Interface

The package includes a full-featured CLI for interacting with BSFS storage:

### Initialize Storage

```bash
# Generate new master key and initialize storage
bsfs-cli init storage.blob --key-file master.key --generate-key

# Use existing key
bsfs-cli init storage.blob --key-file existing.key
```

### File Operations

```bash
# Write text data
bsfs-cli write storage.blob --key-file master.key --data "Hello World"

# Write file content
bsfs-cli write storage.blob --key-file master.key --input-file document.txt

# Read file (prints to stdout)
bsfs-cli read storage.blob --key-file master.key --file-id <uuid>

# Save to file
bsfs-cli read storage.blob --key-file master.key --file-id <uuid> --output-file output.txt

# Delete file
bsfs-cli delete storage.blob --key-file master.key --file-id <uuid>
```

### Storage Information

```bash
# Human-readable format
bsfs-cli info storage.blob --key-file master.key

# JSON format
bsfs-cli info storage.blob --key-file master.key --json
```

## API Reference

### Core Classes

#### BSFS

Main class for interacting with BSFS storage.

```python
class BSFS:
    def __init__(self, blob_path: Union[str, Path], master_key: bytes, 
                 library_path: Optional[str] = None)
    
    def write_file(self, file_id: uuid.UUID, data: bytes) -> None
    def read_file(self, file_id: uuid.UUID) -> bytes
    def delete_file(self, file_id: uuid.UUID) -> None
    def file_exists(self, file_id: uuid.UUID) -> bool
    def get_storage_info(self) -> dict
    def close(self) -> None
```

**Parameters:**
- `blob_path`: Path to the blob storage file
- `master_key`: 32-byte master encryption key
- `library_path`: Optional path to BSFS shared library

**Context Manager:**
```python
with BSFS(blob_path, master_key) as fs:
    # Operations here
    pass  # Automatically cleaned up
```

### Exception Classes

```python
class BSFSError(Exception):
    """Base exception for BSFS operations"""

class BSFSInitError(BSFSError):
    """Raised when BSFS initialization fails"""

class BSFSFileNotFoundError(BSFSError):
    """Raised when a file is not found"""

class BSFSStorageFullError(BSFSError):
    """Raised when storage is full"""

class BSFSCorruptionError(BSFSError):
    """Raised when data corruption is detected"""
```

### Utility Functions

```python
def generate_master_key() -> bytes:
    """Generate a random 32-byte master key"""

def create_storage(blob_path: Union[str, Path], master_key: bytes) -> BSFS:
    """Create a new BSFS storage instance"""
```

## Error Handling

The wrapper provides meaningful Python exceptions:

```python
from bsfs import BSFS, BSFSFileNotFoundError, BSFSStorageFullError

try:
    with BSFS('storage.blob', master_key) as fs:
        # Try to read non-existent file
        data = fs.read_file(uuid.uuid4())
except BSFSFileNotFoundError:
    print("File not found")
except BSFSStorageFullError:
    print("Storage is full")
except BSFSError as e:
    print(f"BSFS error: {e}")
```

## Advanced Usage

### Custom Library Path

If the BSFS shared library is not in the standard location:

```python
from bsfs import BSFS

# Specify custom library path
fs = BSFS('storage.blob', master_key, library_path='/custom/path/libbsfs.so')
```

### Storage Information

```python
with BSFS('storage.blob', master_key) as fs:
    info = fs.get_storage_info()
    
    print(f"Files: {info['file_count']}")
    print(f"Used: {info['used_capacity']:,} bytes")
    print(f"Free: {info['free_capacity']:,} bytes") 
    print(f"Utilization: {info['storage_utilization']:.1f}%")
```

### Batch Operations

```python
# Store multiple files efficiently
files_to_store = [
    (uuid.uuid4(), b"File 1 content"),
    (uuid.uuid4(), b"File 2 content"),
    (uuid.uuid4(), b"File 3 content"),
]

with BSFS('batch.blob', master_key) as fs:
    for file_id, data in files_to_store:
        fs.write_file(file_id, data)
    
    # Read them all back
    for file_id, original_data in files_to_store:
        stored_data = fs.read_file(file_id)
        assert stored_data == original_data
```

## Development

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=bsfs --cov-report=html
```

### Code Quality

```bash
# Format code
black bsfs/ tests/
isort bsfs/ tests/

# Lint code
flake8 bsfs/ tests/
mypy bsfs/
```

### Building

```bash
# Build C library first
make build-c

# Build Python package
python setup.py sdist bdist_wheel
```

## Security Considerations

### Master Key Management

- **Generate secure keys**: Use `generate_master_key()` or a secure random source
- **Store safely**: Keep master keys in secure key management systems
- **Never hardcode**: Don't embed keys in source code
- **Rotate regularly**: Implement key rotation procedures

```python
# Good: Generate and store securely
master_key = generate_master_key()
secure_storage.store_key("bsfs_master", master_key)

# Bad: Hardcoded key
master_key = b"this_is_not_secure_at_all_12345"  # Don't do this!
```

### File Access Patterns

BSFS provides cryptographic isolation, but consider:
- File IDs are not encrypted (use meaningful UUIDs)
- Access patterns may leak information
- Consider application-level access controls

## Performance Tips

### Batch Operations

```python
# Efficient: Single context manager
with BSFS('storage.blob', master_key) as fs:
    for file_id, data in many_files:
        fs.write_file(file_id, data)

# Inefficient: Multiple initializations
for file_id, data in many_files:
    with BSFS('storage.blob', master_key) as fs:  # Reopens each time
        fs.write_file(file_id, data)
```

### Memory Usage

- Files are loaded entirely into memory
- For very large files, consider chunking at application level
- Monitor memory usage with large datasets

### Storage Efficiency

- Current limit: 64 files per partition, 256 blocks per file
- Default block size: 2MB
- Plan storage layout for your use case

## Limitations

### Current Limitations

- **Single partition**: Only first partition is used (easily extendable)
- **File limits**: 64 files per partition maximum
- **File size**: 512MB maximum per file (with default 2MB blocks)
- **No enumeration**: Cannot list files (use external index)
- **No streaming**: Files loaded entirely into memory
- **No compression**: Raw storage without compression

### Planned Improvements

- Multi-partition support for larger storage
- Increased file limits (1024+ files per partition)
- File enumeration API
- Streaming I/O for large files
- Background garbage collection
- Performance optimizations

## Examples

### Document Storage System

```python
import uuid
import json
from datetime import datetime
from bsfs import BSFS, generate_master_key

class DocumentStore:
    def __init__(self, storage_path, master_key):
        self.fs = BSFS(storage_path, master_key)
        self.index = {}  # file_id -> metadata
    
    def store_document(self, content: bytes, metadata: dict = None):
        file_id = uuid.uuid4()
        
        # Add timestamp
        if metadata is None:
            metadata = {}
        metadata['created'] = datetime.now().isoformat()
        metadata['size'] = len(content)
        
        # Store content
        self.fs.write_file(file_id, content)
        
        # Update index
        self.index[str(file_id)] = metadata
        
        return file_id
    
    def get_document(self, file_id: uuid.UUID):
        content = self.fs.read_file(file_id)
        metadata = self.index.get(str(file_id), {})
        return content, metadata
    
    def delete_document(self, file_id: uuid.UUID):
        self.fs.delete_file(file_id)
        self.index.pop(str(file_id), None)
    
    def list_documents(self):
        return self.index
    
    def close(self):
        self.fs.close()

# Usage
master_key = generate_master_key()
store = DocumentStore('documents.blob', master_key)

try:
    # Store a document
    doc_id = store.store_document(
        b"Important document content",
        {"title": "Meeting Notes", "author": "Alice"}
    )
    
    # Retrieve it
    content, metadata = store.get_document(doc_id)
    print(f"Document: {metadata['title']} by {metadata['author']}")
    
    # List all documents
    for file_id, meta in store.list_documents().items():
        print(f"{file_id}: {meta['title']} ({meta['size']} bytes)")

finally:
    store.close()
```

### Configuration Manager

```python
import json
from bsfs import BSFS

class ConfigManager:
    def __init__(self, storage_path, master_key):
        self.fs = BSFS(storage_path, master_key)
        self.config_id = uuid.UUID('12345678-1234-5678-9abc-123456789abc')
    
    def save_config(self, config: dict):
        config_json = json.dumps(config, indent=2)
        self.fs.write_file(self.config_id, config_json.encode())
    
    def load_config(self) -> dict:
        try:
            config_bytes = self.fs.read_file(self.config_id)
            return json.loads(config_bytes.decode())
        except BSFSFileNotFoundError:
            return {}
    
    def update_config(self, updates: dict):
        config = self.load_config()
        config.update(updates)
        self.save_config(config)

# Usage
config_mgr = ConfigManager('config.blob', master_key)

# Save configuration
config_mgr.save_config({
    "database_url": "postgresql://localhost/myapp",
    "debug": True,
    "cache_size": 1000
})

# Load and update
config = config_mgr.load_config()
config_mgr.update_config({"debug": False})
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

- GitHub Issues: Report bugs and request features
- Documentation: Check the docs/ directory
- Examples: See the examples/ directory

## Changelog

### v0.1.0 (Initial Release)

- Complete Python wrapper for BSFS C library
- Context manager support
- Comprehensive error handling
- Command-line interface
- Full test suite
- Type hints throughout
- Documentation and examples