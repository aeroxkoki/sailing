#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verify syntax of Python files

This script verifies that Python files have valid syntax.
"""

import ast
import sys
from pathlib import Path

# List of files to check
FILES_TO_CHECK = [
    "sailing_data_processor/reporting/exporters/image_exporter.py",
    "sailing_data_processor/reporting/exporters/image_exporter_parts/utils.py",
    "sailing_data_processor/reporting/exporters/image_exporter_parts/chart_generators.py",
    "sailing_data_processor/reporting/templates/template_manager.py",
    "sailing_data_processor/reporting/templates/standard_templates.py"
]

def check_file_syntax(file_path):
    """Check if a file has valid Python syntax"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        ast.parse(content)
        print(f"✅ {file_path}: Valid syntax")
        return True
    except SyntaxError as e:
        print(f"❌ {file_path}: Syntax error at line {e.lineno}, column {e.offset}")
        print(f"   {e.text}")
        print(f"   {' ' * (e.offset - 1)}^")
        print(f"   {e.msg}")
        return False
    except Exception as e:
        print(f"❌ {file_path}: Error: {e}")
        return False

def main():
    """Main function"""
    success = True
    
    for file_path in FILES_TO_CHECK:
        if not check_file_syntax(file_path):
            success = False
    
    if success:
        print("\nAll files have valid syntax! 🎉")
        return 0
    else:
        print("\nSome files have syntax errors. 😢")
        return 1

if __name__ == "__main__":
    sys.exit(main())
