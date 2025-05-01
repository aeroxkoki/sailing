#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix duplicate content in Python files

This script removes duplicate sections in Python files that may occur
due to concatenation errors or other issues

Usage: python3 fix_duplicates.py [file_path]
"""

import sys
import os
from pathlib import Path

def remove_duplicates(file_path):
    """Remove duplicate lines from a file"""
    try:
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split into lines
        lines = content.split('\n')
        
        # Remove exact duplicates while preserving order
        seen = set()
        unique_lines = []
        for line in lines:
            if line not in seen:
                seen.add(line)
                unique_lines.append(line)
        
        # Join lines back together
        new_content = '\n'.join(unique_lines)
        
        # Save the file if changes were made
        if new_content != content:
            print(f"Fixing duplicate content in {file_path}")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True
        else:
            print(f"No duplicate content found in {file_path}")
            return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Main entry point"""
    if len(sys.argv) != 2:
        print("Usage: python3 fix_duplicates.py <file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        sys.exit(1)
    
    if remove_duplicates(file_path):
        print("Successfully fixed duplicate content")
    else:
        print("No changes were made to the file")

if __name__ == "__main__":
    main()
