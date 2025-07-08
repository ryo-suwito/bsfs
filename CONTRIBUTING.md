# Contributing to BSFS

## Development Setup

### Prerequisites
```bash
# Ubuntu/Debian
sudo apt-get install build-essential libssl-dev uuid-dev valgrind

# Build and test
make clean && make test

# Python development
pip install -e py-bsfs/
```

### Repository Structure
```
bsfs/
├── bsfs.h              # Core API header
├── bsfs.c              # Core implementation
├── test_bsfs.c         # Test suite
├── Makefile            # Build configuration
├── README.md           # Main documentation
├── GUIDES.md           # Developer commands
├── ROADMAP.md          # HTTP API roadmap
└── py-bsfs/            # Python wrapper
    ├── bsfs/           # Package source
    ├── examples/       # Usage examples
    └── setup.py        # Python packaging
```

## Git Workflow

### Initial Setup
```bash
# Clone and build
git clone <repository-url>
cd bsfs
make clean && make test

# Set up Python wrapper
pip install -e py-bsfs/
```

### Development Workflow
```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes
vim bsfs.c

# Test changes
make clean && make test
valgrind --leak-check=full ./test_bsfs

# Test Python wrapper
cd py-bsfs && python examples/run_all_examples.py

# Commit changes
git add .
git commit -m "Add your feature description

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# Push and create PR
git push origin feature/your-feature-name
```

## Testing Requirements

### C Library Tests
- All `make test` must pass
- No valgrind errors or leaks
- Test large files (>1MB)
- Test multiple files (>10)
- Test error conditions

### Python Wrapper Tests
- All examples must run successfully
- Package must install with `pip install -e .`
- CLI must work: `bsfs-cli --help`
- Performance tests should pass

## Code Standards

### C Code
- Follow existing style in `bsfs.c`
- Use `uint8_t`, `uint16_t`, etc. for fixed-width types
- Check all malloc/free pairs
- Handle all error conditions
- Document complex algorithms

### Python Code
- Follow PEP 8 style guidelines
- Use type hints where possible
- Include docstrings for public functions
- Handle exceptions properly
- Use context managers for resources

## Pull Request Process

1. **Create descriptive PR title and description**
2. **Include test results** (make test output)
3. **Reference any issues** being fixed
4. **Update documentation** if API changes
5. **Ensure CI passes** (when available)

## Issue Reporting

### Bug Reports
Include:
- Operating system and version
- Compiler version (`gcc --version`)
- Steps to reproduce
- Expected vs actual behavior
- Relevant log output

### Feature Requests
Include:
- Use case description
- Proposed API design
- Implementation considerations
- Performance implications

## Release Process

### Version Numbering
- `v0.x.y` - Alpha releases
- `v1.x.y` - Stable releases
- `vX.Y.Z` - Major.Minor.Patch

### Release Checklist
- [ ] All tests pass
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version bumped in relevant files
- [ ] Git tag created
- [ ] Python package uploaded to PyPI

## Security

### Reporting Vulnerabilities
Email security issues privately rather than opening public issues.

### Security Considerations
- All data encrypted with AES-256-CBC
- Keys derived with HKDF-SHA256
- Random block allocation
- Memory cleared after use
- No information leakage in error messages

## Performance Guidelines

### C Library
- Minimize memory allocations
- Use stack allocation for small objects
- Batch operations when possible
- Profile with `gprof` for optimizations

### Python Wrapper
- Minimize Python/C boundary crossings
- Use bytes objects efficiently
- Consider async operations for I/O
- Profile with `cProfile` for bottlenecks

## Documentation

### Code Documentation
- Comment complex algorithms
- Explain security considerations
- Document API contracts
- Include usage examples

### User Documentation
- Keep README.md current
- Update examples with new features
- Maintain accurate API reference
- Include troubleshooting guides

Thank you for contributing to BSFS!