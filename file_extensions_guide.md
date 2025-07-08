# C/C++ File Extensions Explained

Understanding the different file types in C/C++ development and the compilation process.

## 🔤 **Source Code Files**

### **.c files** - C Source Code
- **What**: Human-readable C programming language source code
- **Contains**: Functions, variables, logic written in C
- **Example**: `bsfs.c`, `main.c`, `utils.c`

```c
// example.c
#include <stdio.h>

int add(int a, int b) {
    return a + b;
}

int main() {
    printf("Result: %d\n", add(5, 3));
    return 0;
}
```

### **.h files** - Header Files
- **What**: Contains declarations, function prototypes, constants, macros
- **Purpose**: Shared between multiple `.c` files to avoid code duplication
- **Example**: `bsfs.h`, `stdio.h`, `stdlib.h`

```c
// math_utils.h
#ifndef MATH_UTILS_H
#define MATH_UTILS_H

// Function declarations
int add(int a, int b);
int multiply(int a, int b);

// Constants
#define PI 3.14159
#define MAX_SIZE 1024

#endif
```

## ⚙️ **Compiled/Binary Files**

### **.o files** - Object Files
- **What**: Compiled machine code from individual `.c` files
- **Contains**: Binary machine instructions, but not yet linked
- **Purpose**: Intermediate step in compilation process
- **Platform**: Specific to CPU architecture (x86, ARM, etc.)

```bash
# Compilation process
gcc -c bsfs.c        # Creates bsfs.o (object file)
gcc -c main.c        # Creates main.o (object file)
```

**What's inside a .o file:**
- Machine code instructions
- Symbol table (function/variable names)
- Relocation information
- Not executable by itself (missing dependencies)

### **.a files** - Static Libraries (Archives)
- **What**: Collection of `.o` files bundled together
- **Contains**: Multiple object files in one archive
- **Purpose**: Reusable code library that gets embedded into final program
- **Platform**: Linux/Unix (Windows uses `.lib`)

```bash
# Create static library
ar rcs libbsfs.a bsfs.o utils.o crypto.o

# Use static library
gcc main.o -L. -lbsfs -o myprogram
```

**Characteristics:**
- ✅ Self-contained (no external dependencies at runtime)
- ❌ Larger executable size (code is copied into each program)
- ✅ Faster program startup
- ❌ Updates require recompiling all programs

### **.so files** - Shared Libraries (Shared Objects)
- **What**: Dynamic libraries loaded at runtime
- **Contains**: Compiled code that multiple programs can share
- **Purpose**: Reduce memory usage and enable code updates
- **Platform**: Linux/Unix (Windows uses `.dll`, macOS uses `.dylib`)

```bash
# Create shared library
gcc -shared -fPIC -o libbsfs.so bsfs.o utils.o crypto.o

# Use shared library
gcc main.o -L. -lbsfs -o myprogram
```

**Characteristics:**
- ✅ Smaller executable size
- ✅ Memory shared between programs
- ✅ Can update library without recompiling programs
- ❌ Requires library to be present at runtime
- ❌ Slightly slower startup (dynamic linking)

## 🔄 **Compilation Process Flow**

```
Source Code → Object Files → Executable/Library

.c files  →  .o files  →  executable
.h files  ↗             ↘  .a files (static)
                        ↘  .so files (shared)
```

### **Step-by-Step Example:**

```bash
# 1. Compile source files to object files
gcc -c -fPIC bsfs.c        # → bsfs.o
gcc -c -fPIC utils.c       # → utils.o
gcc -c main.c              # → main.o

# 2a. Create static library
ar rcs libbsfs.a bsfs.o utils.o    # → libbsfs.a

# 2b. Create shared library  
gcc -shared -o libbsfs.so bsfs.o utils.o    # → libbsfs.so

# 3a. Link with static library
gcc main.o -L. -lbsfs -o myprogram_static

# 3b. Link with shared library
gcc main.o -L. -lbsfs -o myprogram_dynamic
```

## 📊 **File Type Comparison**

| File Type | Purpose | Human Readable | Executable | Platform Specific |
|-----------|---------|----------------|------------|-------------------|
| `.c`      | Source code | ✅ Yes | ❌ No | ❌ No |
| `.h`      | Headers | ✅ Yes | ❌ No | ❌ No |
| `.o`      | Object code | ❌ No | ❌ No | ✅ Yes |
| `.a`      | Static library | ❌ No | ❌ No | ✅ Yes |
| `.so`     | Shared library | ❌ No | ✅ Loadable | ✅ Yes |

## 🛠️ **Practical Examples**

### **BSFS Project Structure:**

```
bsfs/
├── bsfs.h           # Header file with declarations
├── bsfs.c           # Source code implementation
├── test_bsfs.c      # Test program source
├── Makefile         # Build instructions
│
├── bsfs.o           # Compiled object file (after: gcc -c bsfs.c)
├── test_bsfs.o      # Test object file (after: gcc -c test_bsfs.c)
│
├── libbsfs.a        # Static library (after: ar rcs libbsfs.a bsfs.o)
├── libbsfs.so       # Shared library (after: gcc -shared -o libbsfs.so bsfs.o)
│
└── test_bsfs        # Final executable (after linking)
```

### **Using the Files:**

```bash
# Method 1: Compile everything together
gcc bsfs.c test_bsfs.c -lssl -lcrypto -luuid -o test_bsfs

# Method 2: Use object files
gcc -c bsfs.c                    # → bsfs.o
gcc -c test_bsfs.c               # → test_bsfs.o
gcc bsfs.o test_bsfs.o -lssl -lcrypto -luuid -o test_bsfs

# Method 3: Use static library
ar rcs libbsfs.a bsfs.o          # → libbsfs.a
gcc test_bsfs.o -L. -lbsfs -lssl -lcrypto -luuid -o test_bsfs

# Method 4: Use shared library
gcc -shared -fPIC -o libbsfs.so bsfs.o -lssl -lcrypto -luuid
gcc test_bsfs.o -L. -lbsfs -o test_bsfs
```

## 🌍 **Platform Differences**

| Platform | Shared Library | Static Library | Object File |
|----------|----------------|----------------|-------------|
| Linux    | `.so`          | `.a`           | `.o`        |
| macOS    | `.dylib`       | `.a`           | `.o`        |
| Windows  | `.dll`         | `.lib`         | `.obj`      |

## 🔍 **Inspecting Files**

### **View file information:**
```bash
# Check file type
file bsfs.o          # → bsfs.o: ELF 64-bit LSB relocatable, x86-64
file libbsfs.so      # → libbsfs.so: ELF 64-bit LSB shared object

# List symbols in object/library files
nm bsfs.o            # Show symbols in object file
nm -D libbsfs.so     # Show dynamic symbols in shared library

# Check library dependencies
ldd myprogram        # Show shared library dependencies
objdump -p libbsfs.so # Detailed library information

# View library contents
ar -t libbsfs.a      # List files in static library
```

### **Size comparison:**
```bash
# Compare file sizes
ls -lh bsfs.c        # Source: ~15KB (human readable)
ls -lh bsfs.o        # Object: ~25KB (compiled machine code)
ls -lh libbsfs.a     # Static: ~30KB (with archive metadata)
ls -lh libbsfs.so    # Shared: ~28KB (optimized for sharing)
```

## 💡 **When to Use Each**

### **Source Files (.c/.h):**
- Development and debugging
- Code sharing and version control
- Cross-platform compatibility

### **Object Files (.o):**
- Incremental compilation (only recompile changed files)
- Temporary step in build process
- Rarely used directly

### **Static Libraries (.a):**
- ✅ When you want self-contained executables
- ✅ When performance is critical (no runtime linking)
- ✅ When deploying to systems without library dependencies
- ❌ When you need to save disk space
- ❌ When you want to update libraries independently

### **Shared Libraries (.so):**
- ✅ When multiple programs use the same code
- ✅ When you want smaller executables
- ✅ When you need to update libraries without recompiling programs
- ✅ System libraries (like libc, OpenSSL)
- ❌ When you want completely portable executables

## 🎯 **In the BSFS Context**

For the **BSFS Python wrapper**, we specifically need:

1. **`libbsfs.so`** - Shared library that Python can load with `ctypes`
2. **`bsfs.h`** - Header file to understand the C function signatures
3. **`bsfs.c`** - Source code for reference and compilation

The Python wrapper uses `ctypes.CDLL()` to load the `.so` file and call C functions directly from Python!

```python
# This is what happens in the Python wrapper:
self._lib = ctypes.CDLL('libbsfs.so')  # Load the .so file
result = self._lib.bsfs_write_file(...)  # Call C function
```
