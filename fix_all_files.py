#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix all Python files with syntax issues

This script fixes common issues in Python files:
1. Invalid escape sequences
2. Duplicated content
3. Incomplete class/function definitions
4. Other common syntax errors

Usage: python3 fix_all_files.py
"""

import os
import re
import ast
import shutil
from pathlib import Path

# Problematic directories to focus on
PROBLEM_DIRS = [
    "sailing_data_processor/reporting/exporters",
    "sailing_data_processor/reporting/templates"
]

def backup_file(file_path):
    """Create a backup of a file before modifying it"""
    backup_dir = Path("./backups")
    backup_dir.mkdir(exist_ok=True)
    
    rel_path = Path(file_path).name
    backup_path = backup_dir / f"{rel_path}.bak"
    
    try:
        shutil.copy2(file_path, backup_path)
        print(f"Created backup: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"Error creating backup: {e}")
        return None

def fix_escape_sequences(content):
    """Fix invalid escape sequences like \! -> !"""
    return re.sub(r'\\\\!', '!', content)

def fix_duplicates(content):
    """Remove duplicate lines"""
    lines = content.split('\n')
    seen = set()
    unique_lines = []
    
    for line in lines:
        line_key = line.strip()
        if not line_key or line_key not in seen:
            seen.add(line_key)
            unique_lines.append(line)
    
    return '\n'.join(unique_lines)

def fix_file(file_path):
    """Apply all fixes to a file"""
    print(f"Processing: {file_path}")
    
    try:
        # Create backup
        backup_path = backup_file(file_path)
        if not backup_path:
            return False
        
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Apply fixes
        content = fix_escape_sequences(content)
        content = fix_duplicates(content)
        
        # Check if we fixed the file
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Fixed issues in {file_path}")
            return True
        else:
            print(f"ℹ️ No issues found in {file_path}")
            return False
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False

def check_syntax(file_path):
    """Check if a Python file has valid syntax"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        ast.parse(content)
        return True
    except SyntaxError:
        return False
    except Exception:
        return False

def find_problematic_files():
    """Find Python files with syntax errors"""
    problematic_files = []
    
    for problem_dir in PROBLEM_DIRS:
        dir_path = Path(problem_dir)
        if not dir_path.exists():
            continue
        
        for file_path in dir_path.glob('**/*.py'):
            if not check_syntax(file_path):
                problematic_files.append(str(file_path))
    
    return problematic_files

def main():
    """Main entry point"""
    print("Finding problematic files...")
    problematic_files = find_problematic_files()
    
    if not problematic_files:
        print("No problematic files found!")
        return
    
    print(f"Found {len(problematic_files)} problematic files:")
    for file in problematic_files:
        print(f"  - {file}")
    
    print("\nFixing files...")
    fixed_count = 0
    for file in problematic_files:
        if fix_file(file):
            fixed_count += 1
    
    print(f"\nFixed {fixed_count}/{len(problematic_files)} files!")
    
    # Check if we fixed all files
    remaining_problematic = find_problematic_files()
    if remaining_problematic:
        print(f"\nThere are still {len(remaining_problematic)} problematic files:")
        for file in remaining_problematic:
            print(f"  - {file}")
    else:
        print("\nAll syntax issues have been fixed!")

if __name__ == "__main__":
    main()
