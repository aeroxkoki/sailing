#!/usr/bin/env python3

import os
import sys

def remove_null_bytes(file_path):
    with open(file_path, 'rb') as f:
        content = f.read()
    
    new_content = content.replace(b'\x00', b'')
    
    if len(content) != len(new_content):
        print(f"修正: {file_path}")
        with open(file_path, 'wb') as f:
            f.write(new_content)
        return True
    return False

def scan_directory(directory):
    fixed_files = []
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                if remove_null_bytes(file_path):
                    fixed_files.append(file_path)
    
    return fixed_files

if __name__ == "__main__":
    directory = "backend"
    if len(sys.argv) > 1:
        directory = sys.argv[1]
    
    fixed_files = scan_directory(directory)
    print(f"修正されたファイル数: {len(fixed_files)}")
