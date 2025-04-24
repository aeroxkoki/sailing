#!/usr/bin/env python3
"""
ファイルのエンコーディングに関する問題を検出するスクリプト
特に、NULLバイトや不正なUnicode文字を含むファイルを特定します。
"""

import os
import sys
import glob
from pathlib import Path

def check_file(filepath):
    """
    ファイルをチェックして問題を報告します
    """
    try:
        with open(filepath, 'rb') as f:
            content = f.read()
            
        # NULL bytes check
        null_count = content.count(b'\x00')
        
        # Try to decode as UTF-8 and check for errors
        decode_error = False
        try:
            content.decode('utf-8')
        except UnicodeDecodeError:
            decode_error = True
        
        if null_count > 0 or decode_error:
            print(f"問題ファイル: {filepath}")
            if null_count > 0:
                print(f"  - NULL bytes: {null_count}")
            if decode_error:
                print("  - UTF-8デコードエラー")
            return True
    except Exception as e:
        print(f"エラー - {filepath}: {str(e)}")
        return True
    
    return False

def main():
    """
    メイン関数
    """
    # Check Python files recursively
    python_files = glob.glob("**/*.py", recursive=True)
    
    print(f"{len(python_files)} Pythonファイルを検査中...")
    
    problem_files = []
    for filepath in python_files:
        if check_file(filepath):
            problem_files.append(filepath)
    
    print("\n検査結果:")
    print(f"- 合計ファイル数: {len(python_files)}")
    print(f"- 問題ファイル数: {len(problem_files)}")
    
    if problem_files:
        print("\n問題ファイル一覧:")
        for f in problem_files:
            print(f"- {f}")
    else:
        print("\n問題は見つかりませんでした")

if __name__ == "__main__":
    main()
