#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Clean and fix corrupted files in the sailing-strategy-analyzer project.

This script fixes files with NULL bytes and corrupted UTF-8 encoding.
"""

import os
import sys
from pathlib import Path
import logging
import shutil

# Setup logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("clean_fix")

def fix_file(file_path, backup=True):
    """
    Fix encoding issues in a file
    
    Args:
        file_path: Path to the file to fix
        backup: Whether to create a backup of the original file
    
    Returns:
        bool: True if the file was fixed, False otherwise
    """
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return False
        
        # Create backup
        if backup:
            backup_path = f"{file_path}.bak"
            shutil.copy2(file_path, backup_path)
            logger.info(f"Created backup: {backup_path}")
        
        # Read file in binary mode
        with open(file_path, 'rb') as f:
            content = f.read()
        
        # Remove NULL bytes
        has_null = b'\x00' in content
        if has_null:
            logger.info(f"Found NULL bytes in {file_path}")
            content = content.replace(b'\x00', b'')
        
        # Check if file is valid UTF-8
        try:
            content.decode('utf-8')
            is_valid_utf8 = True
        except UnicodeDecodeError:
            logger.warning(f"File has invalid UTF-8 encoding: {file_path}")
            is_valid_utf8 = False
        
        # Write back clean content
        if has_null or not is_valid_utf8:
            try:
                # If not valid UTF-8, try to fix by decoding with 'replace'
                if not is_valid_utf8:
                    decoded = content.decode('utf-8', errors='replace')
                    content = decoded.encode('utf-8')
                
                with open(file_path, 'wb') as f:
                    f.write(content)
                logger.info(f"Fixed file: {file_path}")
                return True
            except Exception as e:
                logger.error(f"Error writing fixed content to {file_path}: {e}")
                return False
        else:
            logger.info(f"File is already clean: {file_path}")
            return True
    
    except Exception as e:
        logger.error(f"Error fixing file {file_path}: {e}")
        return False

def main():
    # Project root directory (assuming this script is in the project root)
    project_root = Path(__file__).parent
    
    # Critical test files to fix
    test_files = [
        project_root / "tests" / "test_project" / "test_import_integration.py",
        project_root / "tests" / "test_project" / "test_project_storage.py"
    ]
    
    # Core files that might need fixing
    core_files = [
        project_root / "sailing_data_processor" / "project" / "import_integration.py",
        project_root / "sailing_data_processor" / "project" / "project_storage.py",
        project_root / "sailing_data_processor" / "project" / "project_model.py"
    ]
    
    # Fix test files
    logger.info("Fixing test files...")
    for file_path in test_files:
        fix_file(file_path)
    
    # Fix core files
    logger.info("Fixing core files...")
    for file_path in core_files:
        fix_file(file_path)
    
    logger.info("Done fixing files")

if __name__ == "__main__":
    main()
