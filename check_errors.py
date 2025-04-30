#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
簡単なソースコード構文チェックスクリプト
"""

import os
import sys
import ast

def check_syntax(file_path):
    """ファイルの構文をチェックする"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    try:
        ast.parse(content)
        return None
    except SyntaxError as e:
        return f"行 {e.lineno}, 列 {e.offset}: {e.msg}"
    except Exception as e:
        return f"予期せぬエラー: {str(e)}"

def main():
    """メイン関数"""
    if len(sys.argv) < 2:
        print("使用法: python check_errors.py <ファイルパス>")
        return 1
    
    file_path = sys.argv[1]
    
    if not os.path.exists(file_path):
        print(f"エラー: ファイル '{file_path}' が見つかりません")
        return 1
    
    error = check_syntax(file_path)
    
    if error:
        print(f"構文エラーが見つかりました: {error}")
        return 1
    else:
        print(f"ファイル '{file_path}' は構文的に正しいです")
        return 0

if __name__ == "__main__":
    sys.exit(main())
