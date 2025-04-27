#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
構文エラーを検出するスクリプト
"""

import os
import sys
import traceback

def check_syntax(file_path: str):
    """
    ファイルの構文エラーをチェック
    
    Parameters
    ----------
    file_path : str
        チェックするファイルのパス
    
    Returns
    -------
    tuple
        (エラーがあるかどうか, エラーメッセージ)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        # コンパイルする（シンタックスエラーをチェック）
        compile(source, file_path, 'exec')
        return (False, "OK")
    except SyntaxError as e:
        return (True, f"Line {e.lineno}, column {e.offset}: {e.msg}")
    except UnicodeDecodeError as e:
        return (True, f"Unicode decode error: {e}")
    except Exception as e:
        return (True, f"Error: {str(e)}")

def scan_directory(dir_path: str, extension: str = '.py'):
    """
    ディレクトリ内のすべてのPythonファイルをスキャン
    
    Parameters
    ----------
    dir_path : str
        スキャンするディレクトリのパス
    extension : str, optional
        チェックするファイルの拡張子, by default '.py'
    
    Returns
    -------
    dict
        {ファイルパス: エラーメッセージ} の辞書
    """
    results = {}
    
    for root, _, files in os.walk(dir_path):
        for file in files:
            if file.endswith(extension):
                file_path = os.path.join(root, file)
                try:
                    has_error, message = check_syntax(file_path)
                    if has_error:
                        results[file_path] = message
                except Exception as e:
                    results[file_path] = f"Error checking syntax: {str(e)}"
    
    return results

def check_single_file(file_path: str):
    """
    単一ファイルの構文チェック
    
    Parameters
    ----------
    file_path : str
        チェックするファイルのパス
    """
    print(f"Checking {file_path}...")
    try:
        has_error, message = check_syntax(file_path)
        if has_error:
            print(f"Error: {message}")
            return 1
        else:
            print("No syntax errors found!")
            return 0
    except Exception as e:
        print(f"Exception during check: {str(e)}")
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    # コマンドライン引数からディレクトリまたはファイルを取得
    if len(sys.argv) > 1:
        target = sys.argv[1]
    else:
        target = '.'
    
    # ファイルかディレクトリかを判断
    if os.path.isfile(target):
        sys.exit(check_single_file(target))
    
    # ディレクトリの場合
    print(f"Scanning {target} for syntax errors...")
    errors = scan_directory(target)
    
    # 結果表示
    if errors:
        print(f"\nFound {len(errors)} files with syntax errors:")
        for file_path, message in errors.items():
            print(f"\n{file_path}:")
            print(f"  {message}")
        sys.exit(1)
    else:
        print("No syntax errors found!")
        sys.exit(0)
