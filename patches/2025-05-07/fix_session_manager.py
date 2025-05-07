#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix script for the SessionManager class

This script fixes issues in the SessionManager class implementation
to make it compatible with the expected test behavior.
"""

import shutil
import os
from pathlib import Path

def backup_file(filepath):
    """Create a backup of the file"""
    backup_path = filepath.with_suffix(filepath.suffix + '.bak')
    shutil.copy2(filepath, backup_path)
    print(f"Backup created: {backup_path}")

def fix_session_manager():
    """Fix the SessionManager class implementation"""
    # Define file paths
    project_root = Path(__file__).parents[2]
    session_manager_path = project_root / "sailing_data_processor" / "project" / "session_manager.py"
    patch_session_manager_path = project_root / "patches" / "2025-05-07" / "session_manager.py"
    
    # Create the patch file if it doesn't exist
    if not patch_session_manager_path.exists():
        print(f"Patch file not found: {patch_session_manager_path}")
        return False
    
    # Backup original files
    backup_file(session_manager_path)
    
    # Replace the files with the fixed versions
    try:
        shutil.copy2(patch_session_manager_path, session_manager_path)
        print(f"Successfully updated: {session_manager_path}")
        return True
    except Exception as e:
        print(f"Error updating session_manager.py: {e}")
        return False

if __name__ == "__main__":
    success = fix_session_manager()
    if success:
        print("Fix completed successfully!")
    else:
        print("Fix failed. Please check the error messages above.")
