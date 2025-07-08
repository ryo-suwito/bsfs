#!/usr/bin/env python3
"""
BSFS File Backup Demo - Demonstrates how to backup and restore native Linux files

This example shows how to:
1. Backup files from the filesystem to BSFS
2. Restore files from BSFS to the filesystem
3. Handle different file types (text, binary, directories)
4. Maintain file metadata and structure
5. Create incremental backups
"""

import os
import uuid
import json
import tempfile
import shutil
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

import bsfs


class FileBackupSystem:
    """A file backup system built on top of BSFS"""
    
    def __init__(self, blob_path: str, master_key: bytes):
        self.blob_path = blob_path
        self.master_key = master_key
        self.fs = bsfs.BSFS(blob_path, master_key)
        
        # Special UUID for storing backup index
        self.index_id = uuid.UUID('00000000-0000-0000-0000-000000000002')
        
        # Load or create backup index
        self.index = self._load_index()
    
    def _load_index(self) -> Dict[str, Any]:
        """Load the backup index from BSFS"""
        try:
            index_data = self.fs.read_file(self.index_id)
            return json.loads(index_data.decode())
        except bsfs.BSFSFileNotFoundError:
            # Create new index
            return {
                'backups': {},
                'files': {},
                'created_at': datetime.now().isoformat()
            }
    
    def _save_index(self):
        """Save the backup index to BSFS"""
        index_data = json.dumps(self.index, indent=2).encode()
        self.fs.write_file(self.index_id, index_data)
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def backup_file(self, file_path: Path, backup_name: str = None) -> str:
        """Backup a single file to BSFS"""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if backup_name is None:
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Calculate file hash for deduplication
        file_hash = self._calculate_file_hash(file_path)
        
        # Check if file already exists (deduplication)
        existing_file_id = None
        for file_id, file_info in self.index['files'].items():
            if file_info['hash'] == file_hash:
                existing_file_id = file_id
                print(f"🔄 File already exists (deduplicated): {file_path}")
                break
        
        # Store file content if not already stored
        if existing_file_id is None:
            file_id = str(uuid.uuid4())
            file_content = file_path.read_bytes()
            file_uuid = uuid.UUID(file_id)
            self.fs.write_file(file_uuid, file_content)
            
            # Store file metadata
            self.index['files'][file_id] = {
                'hash': file_hash,
                'size': len(file_content),
                'stored_at': datetime.now().isoformat()
            }
            
            print(f"📁 Stored file content: {file_path} ({len(file_content):,} bytes)")
        else:
            file_id = existing_file_id
        
        # Create backup entry
        backup_id = str(uuid.uuid4())
        stat = file_path.stat()
        
        backup_entry = {
            'id': backup_id,
            'name': backup_name,
            'original_path': str(file_path.absolute()),
            'filename': file_path.name,
            'file_id': file_id,
            'size': stat.st_size,
            'hash': file_hash,
            'mode': stat.st_mode,
            'created_at': datetime.now().isoformat(),
            'file_mtime': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'file_ctime': datetime.fromtimestamp(stat.st_ctime).isoformat(),
        }
        
        # Add to backup index
        if backup_name not in self.index['backups']:
            self.index['backups'][backup_name] = []
        
        self.index['backups'][backup_name].append(backup_entry)
        self._save_index()
        
        print(f"✅ Backed up: {file_path} -> {backup_name}")
        return backup_id
    
    def backup_directory(self, dir_path: Path, backup_name: str = None) -> List[str]:
        """Backup an entire directory to BSFS"""
        if not dir_path.exists() or not dir_path.is_dir():
            raise NotADirectoryError(f"Directory not found: {dir_path}")
        
        if backup_name is None:
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        backup_ids = []
        
        # Walk through directory
        for root, dirs, files in os.walk(dir_path):
            root_path = Path(root)
            
            # Backup all files
            for file in files:
                file_path = root_path / file
                try:
                    backup_id = self.backup_file(file_path, backup_name)
                    backup_ids.append(backup_id)
                except Exception as e:
                    print(f"⚠️ Failed to backup {file_path}: {e}")
        
        print(f"✅ Backed up directory: {dir_path} -> {backup_name} ({len(backup_ids)} files)")
        return backup_ids
    
    def restore_file(self, backup_id: str, restore_path: Path) -> bool:
        """Restore a file from backup"""
        # Find backup entry
        backup_entry = None
        for backup_name, entries in self.index['backups'].items():
            for entry in entries:
                if entry['id'] == backup_id:
                    backup_entry = entry
                    break
            if backup_entry:
                break
        
        if not backup_entry:
            print(f"❌ Backup not found: {backup_id}")
            return False
        
        # Get file content
        file_id = backup_entry['file_id']
        try:
            file_uuid = uuid.UUID(file_id)
            file_content = self.fs.read_file(file_uuid)
        except bsfs.BSFSFileNotFoundError:
            print(f"❌ File content not found: {file_id}")
            return False
        
        # Write to restore path
        restore_path.parent.mkdir(parents=True, exist_ok=True)
        restore_path.write_bytes(file_content)
        
        # Restore file permissions
        os.chmod(restore_path, backup_entry['mode'])
        
        print(f"✅ Restored: {backup_entry['original_path']} -> {restore_path}")
        return True
    
    def restore_backup(self, backup_name: str, restore_dir: Path) -> int:
        """Restore an entire backup"""
        if backup_name not in self.index['backups']:
            print(f"❌ Backup not found: {backup_name}")
            return 0
        
        restore_dir.mkdir(parents=True, exist_ok=True)
        restored_count = 0
        
        for entry in self.index['backups'][backup_name]:
            # Determine restore path
            original_path = Path(entry['original_path'])
            restore_path = restore_dir / original_path.name
            
            if self.restore_file(entry['id'], restore_path):
                restored_count += 1
        
        print(f"✅ Restored backup '{backup_name}': {restored_count} files")
        return restored_count
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """List all backups"""
        backups = []
        for backup_name, entries in self.index['backups'].items():
            total_size = sum(entry['size'] for entry in entries)
            backups.append({
                'name': backup_name,
                'files': len(entries),
                'total_size': total_size,
                'created_at': min(entry['created_at'] for entry in entries)
            })
        return backups
    
    def list_files_in_backup(self, backup_name: str) -> List[Dict[str, Any]]:
        """List files in a specific backup"""
        if backup_name not in self.index['backups']:
            return []
        
        return self.index['backups'][backup_name]
    
    def delete_backup(self, backup_name: str) -> bool:
        """Delete a backup (but keep file content for deduplication)"""
        if backup_name not in self.index['backups']:
            return False
        
        file_count = len(self.index['backups'][backup_name])
        del self.index['backups'][backup_name]
        self._save_index()
        
        print(f"✅ Deleted backup: {backup_name} ({file_count} files)")
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get backup statistics"""
        total_backups = len(self.index['backups'])
        total_files = sum(len(entries) for entries in self.index['backups'].values())
        unique_files = len(self.index['files'])
        
        total_size = sum(file_info['size'] for file_info in self.index['files'].values())
        
        storage_info = self.fs.get_storage_info()
        
        return {
            'total_backups': total_backups,
            'total_files': total_files,
            'unique_files': unique_files,
            'total_size': total_size,
            'deduplication_ratio': (total_files / unique_files) if unique_files > 0 else 0,
            'storage_info': storage_info
        }
    
    def close(self):
        """Close the BSFS connection"""
        self.fs.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def create_sample_files(temp_dir: Path) -> Path:
    """Create sample files for backup demonstration"""
    sample_dir = temp_dir / "sample_files"
    sample_dir.mkdir()
    
    # Create text files
    (sample_dir / "config.txt").write_text("""
# Sample Configuration File
server_host = localhost
server_port = 8080
database_url = postgresql://user:pass@localhost/db
debug = true
""")
    
    (sample_dir / "README.md").write_text("""
# Sample Project
This is a sample project for demonstrating BSFS backup functionality.

## Features
- File backup and restore
- Directory backup
- Deduplication
- Metadata preservation
""")
    
    # Create JSON file
    (sample_dir / "data.json").write_text(json.dumps({
        "users": [
            {"id": 1, "name": "Alice", "email": "alice@example.com"},
            {"id": 2, "name": "Bob", "email": "bob@example.com"}
        ],
        "settings": {
            "theme": "dark",
            "notifications": True
        }
    }, indent=2))
    
    # Create binary file (simulated)
    (sample_dir / "binary_data.bin").write_bytes(b'\x89PNG\r\n\x1a\n' + b'\x00' * 1000)
    
    # Create subdirectory
    sub_dir = sample_dir / "logs"
    sub_dir.mkdir()
    (sub_dir / "app.log").write_text("2024-01-01 10:00:00 INFO Application started\n")
    (sub_dir / "error.log").write_text("2024-01-01 10:30:00 ERROR Connection failed\n")
    
    return sample_dir


def demo_file_backup():
    """Demonstrate file backup and restore operations"""
    print("🚀 BSFS File Backup Demo")
    print("=" * 50)
    
    # Create temporary directories
    temp_dir = Path(tempfile.mkdtemp())
    blob_path = temp_dir / "backup.blob"
    restore_dir = temp_dir / "restored"
    
    # Create sample files
    sample_dir = create_sample_files(temp_dir)
    
    master_key = bsfs.generate_master_key()
    
    try:
        with FileBackupSystem(str(blob_path), master_key) as backup_system:
            # Backup individual files
            print("\n📁 Backing up individual files...")
            
            config_file = sample_dir / "config.txt"
            readme_file = sample_dir / "README.md"
            
            backup_system.backup_file(config_file, "config_backup")
            backup_system.backup_file(readme_file, "config_backup")
            
            # Backup entire directory
            print("\n📂 Backing up entire directory...")
            backup_system.backup_directory(sample_dir, "full_backup")
            
            # Test deduplication - backup same file again
            print("\n🔄 Testing deduplication...")
            backup_system.backup_file(config_file, "duplicate_test")
            
            # List backups
            print("\n📋 Listing backups...")
            backups = backup_system.list_backups()
            for backup in backups:
                print(f"  📦 {backup['name']}:")
                print(f"     Files: {backup['files']}")
                print(f"     Size: {backup['total_size']:,} bytes")
                print(f"     Created: {backup['created_at']}")
            
            # Show files in backup
            print("\n📄 Files in 'full_backup':")
            files_in_backup = backup_system.list_files_in_backup("full_backup")
            for file_entry in files_in_backup:
                print(f"  📄 {file_entry['filename']} ({file_entry['size']:,} bytes)")
                print(f"     Original: {file_entry['original_path']}")
                print(f"     Hash: {file_entry['hash'][:16]}...")
            
            # Restore individual file
            print("\n🔄 Restoring individual file...")
            restore_file_path = restore_dir / "restored_config.txt"
            
            # Find the backup entry for config.txt
            config_backup_id = None
            for entry in backup_system.list_files_in_backup("config_backup"):
                if entry['filename'] == 'config.txt':
                    config_backup_id = entry['id']
                    break
            
            if config_backup_id:
                backup_system.restore_file(config_backup_id, restore_file_path)
                print(f"     Restored content preview:")
                content = restore_file_path.read_text()
                print(f"     {content[:100]}...")
            
            # Restore entire backup
            print("\n🔄 Restoring entire backup...")
            full_restore_dir = restore_dir / "full_restore"
            restored_count = backup_system.restore_backup("full_backup", full_restore_dir)
            print(f"     Restored {restored_count} files to {full_restore_dir}")
            
            # List restored files
            print("\n📋 Restored files:")
            for restored_file in full_restore_dir.iterdir():
                if restored_file.is_file():
                    print(f"  📄 {restored_file.name} ({restored_file.stat().st_size:,} bytes)")
            
            # Show statistics
            print("\n📊 Backup statistics...")
            stats = backup_system.get_stats()
            print(f"Total backups: {stats['total_backups']}")
            print(f"Total files: {stats['total_files']}")
            print(f"Unique files: {stats['unique_files']}")
            print(f"Total size: {stats['total_size']:,} bytes")
            print(f"Deduplication ratio: {stats['deduplication_ratio']:.2f}x")
            print(f"Storage utilization: {stats['storage_info']['storage_utilization']:.1f}%")
            
            # Delete a backup
            print("\n🗑️ Deleting backup...")
            backup_system.delete_backup("duplicate_test")
            
            # Final stats
            print("\n📊 Final statistics...")
            final_stats = backup_system.get_stats()
            print(f"Remaining backups: {final_stats['total_backups']}")
            print(f"Remaining files: {final_stats['total_files']}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
        print("\n🧹 Cleanup completed")


if __name__ == "__main__":
    demo_file_backup()