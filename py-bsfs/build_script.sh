#!/bin/bash
# build_and_install.sh - Complete build and installation script for BSFS Python wrapper

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running on supported OS
check_os() {
    log_info "Checking operating system..."
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
        PACKAGE_MANAGER="apt"
        if command -v yum &> /dev/null; then
            PACKAGE_MANAGER="yum"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        PACKAGE_MANAGER="brew"
    else
        log_error "Unsupported operating system: $OSTYPE"
        exit 1
    fi
    
    log_success "Detected OS: $OS with package manager: $PACKAGE_MANAGER"
}

# Install system dependencies
install_dependencies() {
    log_info "Installing system dependencies..."
    
    case $PACKAGE_MANAGER in
        "apt")
            sudo apt-get update
            sudo apt-get install -y build-essential libssl-dev uuid-dev pkg-config
            ;;
        "yum")
            sudo yum install -y gcc openssl-devel libuuid-devel pkgconfig
            ;;
        "brew")
            brew install openssl ossp-uuid pkg-config
            ;;
        *)
            log_error "Unknown package manager: $PACKAGE_MANAGER"
            exit 1
            ;;
    esac
    
    log_success "System dependencies installed"
}

# Check for Python
check_python() {
    log_info "Checking Python installation..."
    
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed. Please install Python 3.8 or later."
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    log_success "Python $PYTHON_VERSION found"
    
    # Check if version is 3.8+
    if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
        log_success "Python version is compatible"
    else
        log_error "Python 3.8 or later is required. Found: $PYTHON_VERSION"
        exit 1
    fi
}

# Install pip dependencies
install_pip_dependencies() {
    log_info "Installing Python dependencies..."
    
    # Upgrade pip
    python3 -m pip install --upgrade pip
    
    # Install build dependencies
    python3 -m pip install setuptools wheel
    
    log_success "Python dependencies installed"
}

# Build C library
build_c_library() {
    log_info "Building BSFS C library..."
    
    if [ ! -f "Makefile" ]; then
        log_error "Makefile not found. Are you in the BSFS project root?"
        exit 1
    fi
    
    # Clean previous builds
    make clean 2>/dev/null || true
    
    # Build shared library
    make libbsfs.so
    
    if [ ! -f "libbsfs.so" ] && [ ! -f "libbsfs.dylib" ]; then
        log_error "Failed to build shared library"
        exit 1
    fi
    
    log_success "C library built successfully"
}

# Create Python package structure
setup_python_package() {
    log_info "Setting up Python package structure..."
    
    # Create package directory if it doesn't exist
    mkdir -p bsfs
    
    # Copy shared library to package directory
    if [ -f "libbsfs.so" ]; then
        cp libbsfs.so bsfs/
    elif [ -f "libbsfs.dylib" ]; then
        cp libbsfs.dylib bsfs/
    fi
    
    log_success "Python package structure ready"
}

# Install Python package
install_python_package() {
    log_info "Installing BSFS Python package..."
    
    # Install in development mode
    python3 -m pip install -e ".[dev]"
    
    log_success "Python package installed"
}

# Run tests
run_tests() {
    log_info "Running tests..."
    
    if command -v pytest &> /dev/null; then
        python3 -m pytest tests/ -v
        log_success "All tests passed"
    else
        log_warning "pytest not available, running basic test"
        python3 -c "
import bsfs
import uuid
import tempfile
import os

# Basic functionality test
with tempfile.NamedTemporaryFile(delete=False) as f:
    blob_path = f.name

try:
    master_key = bsfs.generate_master_key()
    with bsfs.BSFS(blob_path, master_key) as fs:
        file_id = uuid.uuid4()
        test_data = b'Hello, BSFS!'
        
        fs.write_file(file_id, test_data)
        read_data = fs.read_file(file_id)
        
        assert read_data == test_data, 'Data mismatch'
        
        fs.delete_file(file_id)
        assert not fs.file_exists(file_id), 'File should be deleted'
        
    print('Basic functionality test passed!')
finally:
    os.unlink(blob_path)
"
        log_success "Basic test passed"
    fi
}

# Create demo
create_demo() {
    log_info "Creating demo..."
    
    cat > demo.py << 'EOF'
#!/usr/bin/env python3
"""
BSFS Python Wrapper Demo

This script demonstrates the basic functionality of the BSFS Python wrapper.
"""

import uuid
import tempfile
import os
from pathlib import Path

# Import BSFS
try:
    from bsfs import BSFS, generate_master_key
except ImportError as e:
    print(f"Error: Failed to import BSFS: {e}")
    print("Make sure the package is installed: pip install -e .")
    exit(1)

def main():
    print("🚀 BSFS Python Wrapper Demo")
    print("=" * 40)
    
    # Create temporary blob file
    temp_dir = Path(tempfile.mkdtemp())
    blob_path = temp_dir / "demo.blob"
    
    try:
        # Generate master key
        print("🔑 Generating master key...")
        master_key = generate_master_key()
        print(f"   Key: {master_key.hex()[:16]}... (32 bytes)")
        
        # Initialize BSFS
        print(f"🗃️  Initializing BSFS storage: {blob_path}")
        with BSFS(blob_path, master_key) as fs:
            # Store some files
            print("📝 Writing files...")
            
            files = [
                (uuid.uuid4(), b"Hello, BSFS! This is file #1"),
                (uuid.uuid4(), b"Python wrapper is working great!"),
                (uuid.uuid4(), b"Encrypted storage with UUIDs"),
            ]
            
            for i, (file_id, data) in enumerate(files, 1):
                fs.write_file(file_id, data)
                print(f"   File {i}: {file_id} ({len(data)} bytes)")
            
            # Read files back
            print("📖 Reading files...")
            for i, (file_id, original_data) in enumerate(files, 1):
                read_data = fs.read_file(file_id)
                assert read_data == original_data
                print(f"   File {i}: {read_data.decode()}")
            
            # Show storage info
            print("📊 Storage information:")
            info = fs.get_storage_info()
            print(f"   Files: {info['file_count']}")
            print(f"   Used blocks: {info['used_blocks']}")
            print(f"   Free blocks: {info['free_blocks']}")
            print(f"   Utilization: {info['storage_utilization']:.1f}%")
            
            # Test file existence
            print("🔍 Testing file operations...")
            test_file_id = files[0][0]
            print(f"   File exists: {fs.file_exists(test_file_id)}")
            
            # Delete a file
            fs.delete_file(test_file_id)
            print(f"   After deletion: {fs.file_exists(test_file_id)}")
            
            # Final storage info
            info = fs.get_storage_info()
            print(f"   Files after deletion: {info['file_count']}")
        
        print("✅ Demo completed successfully!")
        print(f"📁 Blob file created: {blob_path} ({blob_path.stat().st_size} bytes)")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        # Cleanup
        if blob_path.exists():
            blob_path.unlink()
        temp_dir.rmdir()
        print("🧹 Cleanup completed")
    
    return 0

if __name__ == "__main__":
    exit(main())
EOF
    
    chmod +x demo.py
    log_success "Demo script created: demo.py"
}

# Print usage information
print_usage() {
    cat << EOF
📚 BSFS Python Wrapper - Build Complete!

Quick Start:
-----------

1. Run the demo:
   python3 demo.py

2. Use the CLI:
   # Initialize storage
   python3 -m bsfs.cli init storage.blob --key-file master.key --generate-key
   
   # Write a file
   python3 -m bsfs.cli write storage.blob --key-file master.key --data "Hello!"
   
   # Show storage info
   python3 -m bsfs.cli info storage.blob --key-file master.key

3. Use in Python code:
   from bsfs import BSFS, generate_master_key
   import uuid
   
   master_key = generate_master_key()
   with BSFS('storage.blob', master_key) as fs:
       file_id = uuid.uuid4()
       fs.write_file(file_id, b'Hello, BSFS!')
       data = fs.read_file(file_id)

Development:
-----------
- Run tests: pytest tests/ -v
- Format code: black bsfs/ tests/
- Lint code: flake8 bsfs/ tests/

Documentation:
-------------
- See README.md for detailed usage
- Check examples/ directory for more examples
- API documentation in docstrings

EOF
}

# Main installation function
main() {
    echo "🔧 BSFS Python Wrapper - Build and Install Script"
    echo "================================================="
    
    check_os
    check_python
    install_dependencies
    install_pip_dependencies
    build_c_library
    setup_python_package
    install_python_package
    run_tests
    create_demo
    
    echo ""
    log_success "🎉 Installation completed successfully!"
    echo ""
    print_usage
}

# Handle command line arguments
case "${1:-}" in
    "deps")
        log_info "Installing dependencies only..."
        check_os
        install_dependencies
        ;;
    "c-lib")
        log_info "Building C library only..."
        build_c_library
        ;;
    "python")
        log_info "Installing Python package only..."
        check_python
        install_pip_dependencies
        setup_python_package
        install_python_package
        ;;
    "test")
        log_info "Running tests only..."
        run_tests
        ;;
    "demo")
        log_info "Creating demo only..."
        create_demo
        ;;
    "clean")
        log_info "Cleaning build artifacts..."
        make clean 2>/dev/null || true
        rm -rf build/ dist/ *.egg-info/ bsfs/*.so bsfs/*.dylib
        python3 -m pip uninstall -y bsfs 2>/dev/null || true
        log_success "Cleanup completed"
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  (no args)  - Full build and install"
        echo "  deps       - Install system dependencies only"
        echo "  c-lib      - Build C library only"
        echo "  python     - Install Python package only"
        echo "  test       - Run tests only"
        echo "  demo       - Create demo script only"
        echo "  clean      - Clean build artifacts"
        echo "  help       - Show this help"
        ;;
    "")
        main
        ;;
    *)
        log_error "Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac
