"""
Command-line interface for BSFS
"""

import argparse
import sys
import uuid
import json
from pathlib import Path
from typing import Optional

from .bsfs import BSFS, generate_master_key, BSFSError


def create_parser():
    """Create command-line argument parser"""
    parser = argparse.ArgumentParser(
        description="BSFS Command Line Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Initialize new storage
  bsfs-cli init storage.blob --key-file master.key
  
  # Write a file
  bsfs-cli write storage.blob --key-file master.key --file-id $(uuidgen) --data "Hello World"
  
  # Read a file
  bsfs-cli read storage.blob --key-file master.key --file-id <uuid>
  
  # List storage info
  bsfs-cli info storage.blob --key-file master.key
  
  # Delete a file
  bsfs-cli delete storage.blob --key-file master.key --file-id <uuid>
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize new BSFS storage")
    init_parser.add_argument("blob_path", help="Path to blob storage file")
    init_parser.add_argument("--key-file", required=True, help="Path to master key file")
    init_parser.add_argument("--generate-key", action="store_true", help="Generate new master key")
    
    # Write command
    write_parser = subparsers.add_parser("write", help="Write file to storage")
    write_parser.add_argument("blob_path", help="Path to blob storage file")
    write_parser.add_argument("--key-file", required=True, help="Path to master key file")
    write_parser.add_argument("--file-id", help="File UUID (generates if not provided)")
    write_parser.add_argument("--data", help="Data to write (use --input-file for files)")
    write_parser.add_argument("--input-file", help="Read data from file")
    
    # Read command
    read_parser = subparsers.add_parser("read", help="Read file from storage")
    read_parser.add_argument("blob_path", help="Path to blob storage file")
    read_parser.add_argument("--key-file", required=True, help="Path to master key file")
    read_parser.add_argument("--file-id", required=True, help="File UUID")
    read_parser.add_argument("--output-file", help="Write data to file (stdout if not provided)")
    
    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete file from storage")
    delete_parser.add_argument("blob_path", help="Path to blob storage file")
    delete_parser.add_argument("--key-file", required=True, help="Path to master key file")
    delete_parser.add_argument("--file-id", required=True, help="File UUID")
    
    # Info command
    info_parser = subparsers.add_parser("info", help="Show storage information")
    info_parser.add_argument("blob_path", help="Path to blob storage file")
    info_parser.add_argument("--key-file", required=True, help="Path to master key file")
    info_parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    return parser


def load_key(key_file: Path) -> bytes:
    """Load master key from file"""
    if not key_file.exists():
        raise FileNotFoundError(f"Key file not found: {key_file}")
    
    key_data = key_file.read_bytes()
    if len(key_data) != 32:
        raise ValueError(f"Key file must contain exactly 32 bytes, got {len(key_data)}")
    
    return key_data


def save_key(key_file: Path, key: bytes):
    """Save master key to file"""
    key_file.write_bytes(key)
    key_file.chmod(0o600)  # Restrict permissions


def cmd_init(args):
    """Initialize new BSFS storage"""
    key_file = Path(args.key_file)
    blob_path = Path(args.blob_path)
    
    # Generate or load key
    if args.generate_key:
        if key_file.exists():
            print(f"Error: Key file {key_file} already exists")
            return 1
        
        master_key = generate_master_key()
        save_key(key_file, master_key)
        print(f"Generated new master key: {key_file}")
    else:
        try:
            master_key = load_key(key_file)
        except (FileNotFoundError, ValueError) as e:
            print(f"Error: {e}")
            return 1
    
    # Initialize BSFS
    try:
        with BSFS(blob_path, master_key) as fs:
            info = fs.get_storage_info()
            print(f"Initialized BSFS storage: {blob_path}")
            print(f"Block size: {info['block_size']:,} bytes")
            print(f"Total capacity: {info['total_capacity']:,} bytes")
    except BSFSError as e:
        print(f"Error: {e}")
        return 1
    
    return 0


def cmd_info(args):
    """Show storage information"""
    try:
        master_key = load_key(Path(args.key_file))
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}")
        return 1
    
    try:
        with BSFS(args.blob_path, master_key) as fs:
            info = fs.get_storage_info()
            
            if args.json:
                print(json.dumps(info, indent=2))
            else:
                print(f"BSFS Storage Information")
                print(f"========================")
                print(f"Blob file: {info['blob_path']}")
                print(f"Partitions: {info['partition_count']}")
                print(f"Files: {info['file_count']}")
                print(f"Block size: {info['block_size']:,} bytes")
                print(f"Total blocks: {info['total_blocks']:,}")
                print(f"Used blocks: {info['used_blocks']:,}")
                print(f"Free blocks: {info['free_blocks']:,}")
                print(f"Storage utilization: {info['storage_utilization']:.1f}%")
                print(f"Total capacity: {info['total_capacity']:,} bytes")
                print(f"Used capacity: {info['used_capacity']:,} bytes")
                print(f"Free capacity: {info['free_capacity']:,} bytes")
    except BSFSError as e:
        print(f"Error: {e}")
        return 1
    
    return 0


def main():
    """Main CLI entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Dispatch to command handlers
    commands = {
        "init": cmd_init,
        "info": cmd_info,
    }
    
    if args.command not in commands:
        print(f"Command '{args.command}' not implemented yet")
        return 1
    
    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())