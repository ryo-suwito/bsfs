#!/bin/bash
# Quick setup script for BSFS Python wrapper

set -e

echo "🚀 Setting up BSFS Python wrapper..."

# Build shared library if needed
if [ ! -f "libbsfs.so" ]; then
    echo "📦 Building shared library..."
    make shared
fi

# Copy to py-bsfs directory
echo "📁 Copying shared library to py-bsfs/"
cp libbsfs.so py-bsfs/

# Test the Python wrapper
echo "🧪 Testing Python wrapper..."
cd py-bsfs
python3 -c "
import sys
sys.path.append('.')
from bsfs_python_wrapper import BSFS, generate_master_key
import uuid
import tempfile
import os

# Use absolute library path
lib_path = os.path.abspath('./libbsfs.so')
print(f'Using library: {lib_path}')

with tempfile.NamedTemporaryFile(delete=False) as f:
    blob_path = f.name

try:
    master_key = generate_master_key()
    with BSFS(blob_path, master_key, library_path=lib_path) as fs:
        file_id = uuid.uuid4()
        test_data = b'Hello, BSFS Python wrapper!'
        
        fs.write_file(file_id, test_data)
        read_data = fs.read_file(file_id)
        
        assert read_data == test_data
        print('✅ Python wrapper working correctly!')
        print(f'📄 Stored and retrieved: {read_data.decode()}')
        
        info = fs.get_storage_info()
        print(f'📊 Storage info: {info[\"file_count\"]} files, {info[\"used_blocks\"]} blocks used')
        
finally:
    os.unlink(blob_path)
"

echo ""
echo "🎉 BSFS Python wrapper setup complete!"
echo ""
echo "Quick usage example:"
echo "  cd py-bsfs"
echo "  python3 bsfs_python_wrapper.py  # Run built-in test"
echo ""
echo "In your Python code:"
echo "  from bsfs_python_wrapper import BSFS, generate_master_key"
echo "  master_key = generate_master_key()"
echo "  with BSFS('storage.blob', master_key, library_path='./libbsfs.so') as fs:"
echo "      # Use fs.write_file(), fs.read_file(), etc."