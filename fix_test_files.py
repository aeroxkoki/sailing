#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
テストファイル修正スクリプト

テストファイルを再エンコードして、隠れた NULL バイトなどの問題を解決する
"""

import os
from pathlib import Path

def fix_test_files():
    """
    テストファイルを再エンコードして修正
    """
    # プロジェクトのルートディレクトリ
    root_dir = Path(__file__).parent
    test_dir = root_dir / "tests"
    
    # 問題のあるファイルを特定
    problem_files = [
        test_dir / "test_project" / "test_import_integration.py",
        test_dir / "test_project" / "test_project_storage.py"
    ]
    
    fixed_files = 0
    
    for file_path in problem_files:
        if not file_path.exists():
            print(f"File does not exist: {file_path}")
            continue
        
        print(f"Fixing file: {file_path}")
        
        try:
            # テキストとして読み込み（エラーが出る可能性があるが、できる限り読み込む）
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # NULL バイトの除去
            content = content.replace(b'\x00', b'')
            
            # UTF-8として正しくデコード
            text = content.decode('utf-8', errors='replace')
            
            # 新しいファイルとして書き込み
            backup_path = file_path.with_suffix('.py.bak')
            os.rename(file_path, backup_path)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(text)
            
            print(f"Fixed {file_path}")
            fixed_files += 1
            
        except Exception as e:
            print(f"Error fixing {file_path}: {e}")
    
    print(f"Fixed {fixed_files} files")

if __name__ == "__main__":
    fix_test_files()
