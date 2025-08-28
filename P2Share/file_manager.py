#!/usr/bin/env python3
"""
File Manager Module
Handles shared file management using only Python built-in libraries.
"""

import os
import json
import hashlib
from pathlib import Path

class FileManager:
    def __init__(self, config_dir=None):
        # Use user's home directory for config
        if config_dir is None:
            config_dir = Path.home() / '.p2p_file_share'
        
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        self.shared_files_db = self.config_dir / 'shared_files.json'
        self.downloads_dir = self.config_dir / 'downloads'
        self.downloads_dir.mkdir(exist_ok=True)
        
        self.shared_files = self._load_shared_files()
    
    def _load_shared_files(self):
        """Load shared files database"""
        if self.shared_files_db.exists():
            try:
                with open(self.shared_files_db, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {}
    
    def _save_shared_files(self):
        """Save shared files database"""
        try:
            with open(self.shared_files_db, 'w', encoding='utf-8') as f:
                json.dump(self.shared_files, f, indent=2)
            return True
        except IOError:
            return False
    
    def add_shared_file(self, file_path):
        """Add a file to the shared files list"""
        if not os.path.exists(file_path):
            return False
        
        filename = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        file_hash = self._calculate_file_hash(file_path)
        
        if not file_hash:
            return False
        
        # Check if file already exists
        if filename in self.shared_files:
            # Update if it's a different file
            if self.shared_files[filename]['hash'] != file_hash:
                self.shared_files[filename] = {
                    'path': file_path,
                    'size': file_size,
                    'hash': file_hash,
                    'added_time': self._get_current_time()
                }
        else:
            self.shared_files[filename] = {
                'path': file_path,
                'size': file_size,
                'hash': file_hash,
                'added_time': self._get_current_time()
            }
        
        return self._save_shared_files()
    
    def remove_shared_file(self, filename):
        """Remove a file from the shared files list"""
        if filename in self.shared_files:
            del self.shared_files[filename]
            return self._save_shared_files()
        return False
    
    def get_shared_files(self):
        """Get list of shared file names"""
        # Clean up non-existent files
        files_to_remove = []
        for filename, file_info in self.shared_files.items():
            if not os.path.exists(file_info['path']):
                files_to_remove.append(filename)
        
        for filename in files_to_remove:
            del self.shared_files[filename]
        
        if files_to_remove:
            self._save_shared_files()
        
        return list(self.shared_files.keys())
    
    def get_file_path(self, filename):
        """Get the full path of a shared file"""
        if filename in self.shared_files:
            return self.shared_files[filename]['path']
        return None
    
    def get_file_info(self, filename):
        """Get detailed information about a shared file"""
        if filename in self.shared_files:
            file_info = self.shared_files[filename].copy()
            if os.path.exists(file_info['path']):
                # Update size in case file was modified
                current_size = os.path.getsize(file_info['path'])
                if current_size != file_info['size']:
                    file_info['size'] = current_size
                    file_info['hash'] = self._calculate_file_hash(file_info['path'])
                    # Update in database
                    self.shared_files[filename].update({
                        'size': current_size,
                        'hash': file_info['hash']
                    })
                    self._save_shared_files()
                
                return file_info
        return None
    
    def get_downloads_directory(self):
        """Get the downloads directory path"""
        return str(self.downloads_dir)
    
    def is_file_shared(self, filename):
        """Check if a file is currently shared"""
        return filename in self.shared_files
    
    def get_shared_files_summary(self):
        """Get summary of all shared files"""
        summary = {
            'total_files': len(self.shared_files),
            'total_size': 0,
            'files': []
        }
        
        for filename, file_info in self.shared_files.items():
            if os.path.exists(file_info['path']):
                summary['total_size'] += file_info['size']
                summary['files'].append({
                    'name': filename,
                    'size': file_info['size'],
                    'hash': file_info['hash'],
                    'path': file_info['path']
                })
        
        return summary
    
    def validate_shared_files(self):
        """Validate all shared files and remove invalid ones"""
        invalid_files = []
        
        for filename, file_info in self.shared_files.items():
            file_path = file_info['path']
            
            # Check if file exists
            if not os.path.exists(file_path):
                invalid_files.append(filename)
                continue
            
            # Check if file hash matches (optional integrity check)
            if file_info.get('hash'):
                current_hash = self._calculate_file_hash(file_path)
                if current_hash != file_info['hash']:
                    # File was modified, update hash
                    file_info['hash'] = current_hash
                    file_info['size'] = os.path.getsize(file_path)
        
        # Remove invalid files
        for filename in invalid_files:
            del self.shared_files[filename]
        
        if invalid_files:
            self._save_shared_files()
        
        return invalid_files
    
    def _calculate_file_hash(self, file_path):
        """Calculate SHA-256 hash of a file"""
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, 'rb') as f:
                # Read file in chunks to handle large files
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except (IOError, OSError):
            return None
    
    def _get_current_time(self):
        """Get current timestamp"""
        import time
        return int(time.time())
    
    def export_shared_files_list(self, output_file=None):
        """Export shared files list to JSON file"""
        if output_file is None:
            output_file = self.config_dir / 'shared_files_export.json'
        
        try:
            summary = self.get_shared_files_summary()
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2)
            return True
        except IOError:
            return False
    
    def import_shared_files_list(self, input_file):
        """Import shared files from JSON file"""
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if 'files' in data:
                imported_count = 0
                for file_info in data['files']:
                    if 'path' in file_info and os.path.exists(file_info['path']):
                        if self.add_shared_file(file_info['path']):
                            imported_count += 1
                return imported_count
        except (IOError, json.JSONDecodeError):
            pass
        
        return 0
    
    def get_file_by_hash(self, file_hash):
        """Find a shared file by its hash"""
        for filename, file_info in self.shared_files.items():
            if file_info.get('hash') == file_hash:
                return filename, file_info
        return None, None
    
    def cleanup_downloads(self, max_age_days=30):
        """Clean up old downloaded files"""
        import time
        
        current_time = time.time()
        max_age_seconds = max_age_days * 24 * 60 * 60
        
        cleaned_files = []
        
        try:
            for file_path in self.downloads_dir.iterdir():
                if file_path.is_file():
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > max_age_seconds:
                        try:
                            file_path.unlink()
                            cleaned_files.append(str(file_path))
                        except OSError:
                            pass
        except OSError:
            pass
        
        return cleaned_files