# -*- coding: utf-8 -*-
#\!/usr/bin/env python3
"""
nullバイト（\0）を含むPythonファイルを修正するスクリプト。
"""

import os
import sys

def fix_file(file_path):
    """ファイル内のnullバイトを削除します"""
    try:
        with open(file_path, 'rb') as f:
            content = f.read()
        
        # nullバイトが含まれているか確認
        if b'\x00' in content:
            # nullバイトを削除
            new_content = content.replace(b'\x00', b'')
            
            # 新しい内容を書き出し
            with open(file_path, 'wb') as f:
                f.write(new_content)
            
            return True
        
        return False
    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")
        return False

def scan_directory(directory):
    """ディレクトリ内のPythonファイルをスキャンし修正します"""
    fixed_files = []
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                if fix_file(file_path):
                    fixed_files.append(file_path)
    
    return fixed_files

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 fix_null_bytes.py <directory>")
        sys.exit(1)
    
    directory = sys.argv[1]
    if not os.path.isdir(directory):
        print(f"Error: {directory} is not a directory")
        sys.exit(1)
    
    fixed_files = scan_directory(directory)
    
    if fixed_files:
        print(f"Fixed {len(fixed_files)} files:")
        for file in fixed_files:
            print(f"  - {file}")
    else:
        print("No files needed fixing.")
