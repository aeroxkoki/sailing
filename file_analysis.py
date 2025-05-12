#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

base_path = os.path.dirname(os.path.abspath(__file__))
reporting_path = os.path.join(base_path, "sailing_data_processor/reporting")

py_files = []
for root, dirs, files in os.walk(reporting_path):
    for file in files:
        if file.endswith(".py"):
            full_path = os.path.join(root, file)
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    lines = len(f.readlines())
                    py_files.append((full_path, lines))
            except Exception as e:
                py_files.append((full_path, f"Error: {str(e)}"))

# Sort by line count in descending order
py_files.sort(key=lambda x: x[1] if isinstance(x[1], int) else 0, reverse=True)

# Print files with more than 500 lines
print("Files with more than 500 lines:")
large_files = [f for f in py_files if isinstance(f[1], int) and f[1] > 500]
for file_path, line_count in large_files:
    rel_path = os.path.relpath(file_path, base_path)
    print(f"{rel_path}: {line_count} lines")

# Print top 10 files by size
print("\nTop 10 files by size:")
for i, (file_path, line_count) in enumerate(py_files[:10]):
    rel_path = os.path.relpath(file_path, base_path)
    print(f"{rel_path}: {line_count} lines")
