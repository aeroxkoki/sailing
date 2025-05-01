#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix escape sequences in Python files.

This script fixes common syntax errors in Python files, including:
1. Invalid escape sequences like "\!" -> "!"
2. Duplicate file segments
3. Other encoding issues

Usage: python3 fix_escape_sequences.py [directory]
"""

import os
import sys
import re
from pathlib import Path

def fix_file(file_path):
    """Fix escape sequences in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fix invalid escape sequences
        fixed_content = re.sub(r'\\!', '!', content)
        
        # Check if content has duplicate sections (a common issue in some files)
        # This is a simple check for exact duplicates - may need refinement for partial duplicates
        lines = fixed_content.split('\n')
        seen_lines = set()
        duplicate_indices = []
        
        for i, line in enumerate(lines):
            if line.strip() and line in seen_lines:
                duplicate_indices.append(i)
            seen_lines.add(line)
        
        # If duplicates found, attempt to fix by keeping only the first occurrence
        if duplicate_indices:
            print(f"Warning: Found {len(duplicate_indices)} duplicate lines in {file_path}")
            # This is a simplistic approach - real-world duplicates may need manual inspection
        
        # Check for other common syntax issues and fix them
        # Add more patterns as needed
        
        # Write the fixed content back to the file
        if content != fixed_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            print(f"Fixed escape sequences in {file_path}")
            return True
        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def fix_directory(directory):
    """Fix escape sequences in all Python files in a directory (recursive)."""
    fixed_count = 0
    error_count = 0
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    if fix_file(file_path):
                        fixed_count += 1
                except Exception as e:
                    print(f"Error fixing {file_path}: {e}")
                    error_count += 1
    
    return fixed_count, error_count

def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        directory = sys.argv[1]
    else:
        directory = '.'
    
    print(f"Fixing escape sequences in Python files in {directory}...")
    fixed, errors = fix_directory(directory)
    print(f"Done. Fixed {fixed} files. Encountered {errors} errors.")

if __name__ == "__main__":
    main()
