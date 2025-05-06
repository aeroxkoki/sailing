#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
テストファイル用 NULL バイト除去スクリプト

テストファイル内の NULL バイト（\0）を検出して除去するスクリプト。
エラー発生ファイルである test_import_integration.py と test_project_storage.py に特化。
"""

import os
from pathlib import Path

def clean_test_files():
    """
    指定したテストファイルからNULLバイトを除去
    """
    # プロジェクトのルートディレクトリ
    root_dir = Path(__file__).parent
    
    # 問題のあるファイルのパス
    test_files = [
        root_dir / "tests" / "test_project" / "test_import_integration.py",
        root_dir / "tests" / "test_project" / "test_project_storage.py"
    ]
    
    cleaned_files = 0
    
    for file_path in test_files:
        print(f"Cleaning file: {file_path}")
        
        if not file_path.exists():
            print(f"File does not exist: {file_path}")
            continue
        
        # バイナリモードでファイルを読み込み
        with open(file_path, 'rb') as f:
            content = f.read()
        
        # NULL バイトを検出
        if b'\x00' in content:
            print(f"NULL bytes found in {file_path}")
            
            # NULL バイトを除去
            cleaned_content = content.replace(b'\x00', b'')
            
            # ファイルを上書き
            with open(file_path, 'wb') as f:
                f.write(cleaned_content)
            
            print(f"Cleaned {file_path}")
            cleaned_files += 1
        else:
            print(f"No NULL bytes found in {file_path}")
    
    print(f"Cleaned {cleaned_files} files")

if __name__ == "__main__":
    clean_test_files()
