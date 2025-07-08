# BSFS Developer Guide

## Quick Start Commands

### Prerequisites
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install build-essential libssl-dev uuid-dev

# CentOS/RHEL
sudo yum install gcc openssl-devel libuuid-devel

# macOS
brew install openssl ossp-uuid
```

### Basic Build Commands
```bash
# Clean and build everything
make clean && make all

# Run tests
make test

# Build only the library
make libbsfs.a

# Build only the test program
make test_bsfs

# Install system-wide (requires sudo)
sudo make install

# Show available targets
make help
```

### Development Workflow
```bash
# 1. Make changes to source code
vim bsfs.c

# 2. Recompile and test
make clean && make test

# 3. Run specific test
./test_bsfs

# 4. Debug with gdb
gdb ./test_bsfs
(gdb) run
(gdb) bt
(gdb) quit

# 5. Check for memory leaks
valgrind --leak-check=full ./test_bsfs
```

## Compilation Options

### Debug Build
```bash
# Enable debug symbols and disable optimization
make clean
CFLAGS="-g -O0 -DDEBUG" make all

# Or edit Makefile temporarily:
# CFLAGS = -Wall -Wextra -std=c99 -g -O0 -DDEBUG
```

### Release Build
```bash
# Optimized build for production
make clean
CFLAGS="-O3 -DNDEBUG -march=native" make all
```

### Static Analysis
```bash
# Using clang static analyzer
scan-build make clean
scan-build make all

# Using cppcheck
cppcheck --enable=all --std=c99 *.c *.h
```

## Testing Commands

### Run All Tests
```bash
# Standard test run
make test

# Verbose test output
./test_bsfs

# Test with different configurations
BSFS_BLOCK_SIZE=4194304 ./test_bsfs  # 4MB blocks
```

### Individual Test Functions
```bash
# Run specific test (modify test_bsfs.c)
gcc -DTEST_BASIC_ONLY -g -O0 -o test_basic test_bsfs.c bsfs.c -lssl -lcrypto -luuid
./test_basic
```

### Performance Testing
```bash
# Time the tests
time ./test_bsfs

# Profile with gprof
gcc -pg -o test_profile test_bsfs.c bsfs.c -lssl -lcrypto -luuid
./test_profile
gprof test_profile gmon.out > profile.txt
```

### Memory Testing
```bash
# Check for memory leaks (should show 0 errors)
valgrind --leak-check=full --show-leak-kinds=all ./test_bsfs

# Check for memory errors
valgrind --tool=memcheck --track-origins=yes ./test_bsfs

# Address sanitizer (compile with -fsanitize=address)
gcc -fsanitize=address -g -O0 -o test_asan test_bsfs.c bsfs.c -lssl -lcrypto -luuid
./test_asan

# Note: Fixed alignment issues with OpenSSL by using temporary buffers
# in encrypt/decrypt functions to avoid packed struct alignment problems
```

## File Operations

### Inspect Generated Files
```bash
# List blob files
ls -la *.blob

# Check blob file size
du -h *.blob

# Hexdump blob file structure
hexdump -C test_tenant.blob | head -20

# Remove test files
rm -f *.blob
```

### Backup and Restore
```bash
# Backup a tenant blob
cp tenant_001.blob backup_001.blob

# Restore from backup
cp backup_001.blob tenant_001.blob

# Verify blob integrity (basic check)
file tenant_001.blob
```

## Debugging Commands

### GDB Debugging
```bash
# Start debugging
gdb ./test_bsfs

# Common GDB commands
(gdb) break main
(gdb) break bsfs_write_file
(gdb) run
(gdb) step
(gdb) next
(gdb) print variable_name
(gdb) info locals
(gdb) backtrace
(gdb) continue
(gdb) quit
```

### Core Dump Analysis
```bash
# Enable core dumps
ulimit -c unlimited

# Run program that crashes
./test_bsfs

# Analyze core dump
gdb ./test_bsfs core

# In GDB:
(gdb) bt
(gdb) info registers
(gdb) disassemble
```

### Logging and Debugging
```bash
# Add debug prints (modify source)
#ifdef DEBUG
printf("DEBUG: %s:%d - %s\n", __FILE__, __LINE__, __func__);
#endif

# Compile with debug enabled
gcc -DDEBUG -g -O0 -o test_debug test_bsfs.c bsfs.c -lssl -lcrypto -luuid
```

## Library Usage Examples

### Simple Program
```bash
# Create simple_example.c
cat > simple_example.c << 'EOF'
#include "bsfs.h"
#include <stdio.h>

int main() {
    uint8_t key[32] = {0};
    bsfs_tenant_t tenant;
    
    if (bsfs_tenant_init(&tenant, "example.blob", key) != 0) {
        printf("Failed to init tenant\n");
        return 1;
    }
    
    printf("BSFS initialized successfully\n");
    bsfs_tenant_cleanup(&tenant);
    return 0;
}
EOF

# Compile and run
gcc -o simple_example simple_example.c bsfs.c -lssl -lcrypto -luuid
./simple_example
```

### Linking Against Library
```bash
# Create shared library
gcc -shared -fPIC -o libbsfs.so bsfs.c -lssl -lcrypto -luuid

# Link program against shared library
gcc -o myprogram myprogram.c -L. -lbsfs -lssl -lcrypto -luuid

# Run with library path
LD_LIBRARY_PATH=. ./myprogram
```

## Performance Optimization

### Compiler Optimizations
```bash
# Maximum optimization
gcc -O3 -march=native -flto -o bsfs_optimized bsfs.c test_bsfs.c -lssl -lcrypto -luuid

# Profile-guided optimization
gcc -fprofile-generate -o bsfs_profile bsfs.c test_bsfs.c -lssl -lcrypto -luuid
./bsfs_profile
gcc -fprofile-use -O3 -o bsfs_pgo bsfs.c test_bsfs.c -lssl -lcrypto -luuid
```

### Benchmarking
```bash
# Simple benchmark
cat > benchmark.c << 'EOF'
#include "bsfs.h"
#include <time.h>

int main() {
    clock_t start = clock();
    // Your BSFS operations here
    clock_t end = clock();
    double cpu_time = ((double)(end - start)) / CLOCKS_PER_SEC;
    printf("Time: %f seconds\n", cpu_time);
    return 0;
}
EOF

gcc -O3 -o benchmark benchmark.c bsfs.c -lssl -lcrypto -luuid
./benchmark
```

## Configuration Options

### Compile-Time Configuration
```bash
# Modify bsfs.h constants
#define BSFS_BLOCK_SIZE_DEFAULT (4 * 1024 * 1024)  // 4MB blocks
#define BSFS_BLOCKS_PER_PARTITION 2048             // More blocks
#define BSFS_MAX_FILE_BLOCKS 512                   // Larger files

# Recompile
make clean && make all
```

### Runtime Configuration
```bash
# Set environment variables
export BSFS_DEFAULT_BLOCK_SIZE=4194304
export BSFS_MAX_PARTITIONS=512
./test_bsfs
```

## Troubleshooting

### Common Issues

#### OpenSSL Linking Problems
```bash
# Check OpenSSL installation
pkg-config --modversion openssl
pkg-config --libs openssl

# Explicit linking
gcc -o test test.c bsfs.c -I/usr/include/openssl -L/usr/lib/x86_64-linux-gnu -lssl -lcrypto -luuid
```

#### UUID Library Issues
```bash
# Check UUID library
find /usr -name "uuid.h" 2>/dev/null
pkg-config --libs uuid

# Alternative UUID library
sudo apt-get install uuid-dev
```

#### Permission Issues
```bash
# Check file permissions
ls -la *.blob

# Fix permissions
chmod 644 *.blob
```

### Debug Information
```bash
# Check library dependencies
ldd ./test_bsfs

# Check symbols
nm -D ./test_bsfs | grep bsfs

# Check file format
file ./test_bsfs
```

## Development Tips

### Code Style
```bash
# Format code with clang-format
clang-format -i *.c *.h

# Check style
clang-format --dry-run *.c *.h
```

### Documentation
```bash
# Generate documentation with doxygen
doxygen -g
doxygen Doxyfile
```

### Version Control
```bash
# Initialize git repository
git init
git add *.c *.h Makefile README.md
git commit -m "Initial BSFS implementation"

# Create development branch
git checkout -b feature/multi-partition
```

## Continuous Integration

### GitHub Actions Example
```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Install dependencies
      run: sudo apt-get install libssl-dev uuid-dev
    - name: Build
      run: make all
    - name: Test
      run: make test
    - name: Memory check
      run: valgrind --error-exitcode=1 --leak-check=full ./test_bsfs
```

### Docker Development
```dockerfile
# Dockerfile.dev
FROM ubuntu:20.04
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    uuid-dev \
    valgrind \
    gdb
WORKDIR /app
COPY . .
RUN make all
CMD ["make", "test"]
```

```bash
# Build and run
docker build -f Dockerfile.dev -t bsfs-dev .
docker run --rm bsfs-dev
```

## Production Deployment

### System Installation
```bash
# Install system-wide
sudo make install

# Verify installation
pkg-config --modversion bsfs
```

### Service Configuration
```bash
# Create systemd service
sudo tee /etc/systemd/system/bsfs.service << 'EOF'
[Unit]
Description=BSFS Storage Service
After=network.target

[Service]
Type=simple
User=bsfs
Group=bsfs
WorkingDirectory=/var/lib/bsfs
ExecStart=/usr/local/bin/bsfs-server
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Enable and start
sudo systemctl enable bsfs
sudo systemctl start bsfs
```

This guide provides all the essential commands and workflows for developing, testing, debugging, and deploying BSFS. Keep it handy for quick reference during development!