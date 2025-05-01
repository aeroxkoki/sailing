#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Manual fixes for problematic Python files

This script implements targeted fixes for specific syntax errors in problematic files.
It uses regular expressions to find and replace problematic patterns.

Usage: python3 manual_fix.py
"""

import os
import re
import ast
import sys
from pathlib import Path

# List of problematic files
PROBLEM_FILES = [
    "sailing_data_processor/reporting/exporters/image_exporter.py",
    "sailing_data_processor/reporting/exporters/image_exporter_parts/utils.py",
    "sailing_data_processor/reporting/exporters/image_exporter_parts/chart_generators.py",
    "sailing_data_processor/reporting/templates/template_manager.py",
    "sailing_data_processor/reporting/templates/standard_templates.py"
]

def backup_file(file_path):
    """Create a backup of a file before modifying it"""
    backup_dir = Path("./manual_backups")
    backup_dir.mkdir(exist_ok=True)
    
    rel_path = Path(file_path).name
    backup_path = backup_dir / f"{rel_path}.bak"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as src:
            content = src.read()
        
        with open(backup_path, 'w', encoding='utf-8') as dst:
            dst.write(content)
        
        print(f"Created backup: {backup_path}")
        return True
    except Exception as e:
        print(f"Error creating backup: {e}")
        return False

def fix_file(file_path):
    """Apply specific fixes to a file"""
    try:
        # Create backup
        if not backup_file(file_path):
            return False
        
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Apply fixes
        fixed_content = content
        
        # Fix invalid escape sequences
        fixed_content = re.sub(r'\\\\!(?!=)', '!', fixed_content)
        
        # Fix another common issue - doubled backslash plus !
        fixed_content = re.sub(r'style \\!= "default"', 'style != "default"', fixed_content)
        fixed_content = re.sub(r'\\!= fmt_value', '!= fmt_value', fixed_content)
        
        # Remove duplicate code blocks
        lines = fixed_content.split('\n')
        unique_lines = []
        seen_blocks = set()
        
        i = 0
        while i < len(lines):
            current_line = lines[i].strip()
            
            # Skip empty lines
            if not current_line:
                unique_lines.append(lines[i])
                i += 1
                continue
            
            # Use a sliding window to detect duplicated blocks
            if i + 5 < len(lines):  # Need at least 5 lines to detect a block
                block = '\n'.join(line.strip() for line in lines[i:i+5])
                if block in seen_blocks:
                    # Skip this duplicated block
                    j = i + 5
                    while j < len(lines) and lines[j].strip() and lines[j].strip() in [line.strip() for line in lines[i:i+5]]:
                        j += 1
                    i = j
                    continue
                
                seen_blocks.add(block)
            
            unique_lines.append(lines[i])
            i += 1
        
        fixed_content = '\n'.join(unique_lines)
        
        # Write fixed content back to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        
        return True
    except Exception as e:
        print(f"Error fixing {file_path}: {e}")
        return False

def check_syntax(file_path):
    """Check if a Python file has valid syntax"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        ast.parse(content)
        return True
    except SyntaxError as e:
        print(f"Syntax error in {file_path} at line {e.lineno}, column {e.offset}: {e.msg}")
        return False
    except Exception as e:
        print(f"Error checking syntax of {file_path}: {e}")
        return False

def main():
    """Main entry point"""
    print("Starting manual fixes...")
    
    fixed_count = 0
    for file_path in PROBLEM_FILES:
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            continue
        
        print(f"\nProcessing: {file_path}")
        
        # Check syntax before fixing
        print("Checking syntax before fixing...")
        syntax_ok_before = check_syntax(file_path)
        if syntax_ok_before:
            print("✅ Syntax is already valid")
            continue
        
        # Apply fixes
        if fix_file(file_path):
            print(f"✅ Applied fixes to {file_path}")
            
            # Check syntax after fixing
            print("Checking syntax after fixing...")
            syntax_ok_after = check_syntax(file_path)
            
            if syntax_ok_after:
                print("✅ Syntax is now valid")
                fixed_count += 1
            else:
                print("❌ Syntax is still invalid")
        else:
            print(f"❌ Failed to fix {file_path}")
    
    print(f"\nFixed {fixed_count}/{len(PROBLEM_FILES)} files!")

if __name__ == "__main__":
    main()
