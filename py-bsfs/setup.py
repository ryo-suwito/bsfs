#!/usr/bin/env python3
"""
Setup script for BSFS Python wrapper
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text() if (this_directory / "README.md").exists() else ""

setup(
    name="bsfs",
    version="0.1.0",
    author="BSFS Team",
    author_email="dev@bsfs.org",
    description="Python wrapper for BSFS (Block Storage File System)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/bsfs/bsfs-python",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: System :: Filesystems",
        "Topic :: Security :: Cryptography",
        "Topic :: Database :: Database Engines/Servers",
    ],
    python_requires=">=3.8",
    install_requires=[
        # No external dependencies - uses only stdlib
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov",
            "black",
            "flake8",
            "mypy",
        ],
        "test": [
            "pytest>=6.0",
            "pytest-cov",
        ],
    },
    entry_points={
        "console_scripts": [
            "bsfs-cli=bsfs.cli:main",
        ],
    },
    package_data={
        "bsfs": ["*.so", "*.dylib", "*.dll"],  # Include shared libraries if bundled
    },
    include_package_data=True,
    zip_safe=False,
)