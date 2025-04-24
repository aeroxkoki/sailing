# -*- coding: utf-8 -*-
#\!/usr/bin/env python3
"""
すべてのPythonファイルからnullバイトを削除する
"""

import os
import sys

def remove_null_bytes(file_path):
    """ファイルからnullバイトを削除する"""
    print(f"処理中: {file_path}")
    try:
        # バイナリモードで読み込み
        with open(file_path, 'rb') as f:
            content = f.read()
        
        # nullバイトを削除
        new_content = content.replace(b'\x00', b'')
        
        # サイズが変わったか確認
        if len(content) \!= len(new_content):
            print(f"  修正: {file_path} ({len(content)} -> {len(new_content)} bytes)")
            
            # バイナリモードで書き込み
            with open(file_path, 'wb') as f:
                f.write(new_content)
            return True
        else:
            print(f"  変更なし: {file_path}")
            return False
    except Exception as e:
        print(f"  エラー: {file_path} - {str(e)}")
        return False

def process_directory(directory):
    """ディレクトリ内のPythonファイルを処理する"""
    fixed = []
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                if remove_null_bytes(file_path):
                    fixed.append(file_path)
    
    return fixed

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用法: python3 fix_nulls.py <directory>")
        sys.exit(1)
    
    directory = sys.argv[1]
    fixed_files = process_directory(directory)
    
    print(f"\n修正されたファイル数: {len(fixed_files)}")
    if fixed_files:
        print("以下のファイルが修正されました:")
        for file in fixed_files:
            print(f"  - {file}")
