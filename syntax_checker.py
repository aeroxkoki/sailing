#!/usr/bin/env python3
import ast
import os
import sys

def check_file_syntax(file_path):
    """ファイルの構文をチェックする"""
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    try:
        ast.parse(content)
        return None  # エラーなし
    except SyntaxError as e:
        return {
            'file': file_path,
            'line': e.lineno,
            'column': e.offset,
            'error': str(e)
        }

def check_directory(directory, file_list=None):
    """ディレクトリ内のPythonファイルの構文をチェックする"""
    errors = []
    
    if file_list:
        # ファイルリストが指定されている場合
        for rel_path in file_list:
            file_path = os.path.join(directory, rel_path.lstrip('/'))
            if os.path.isfile(file_path) and file_path.endswith('.py'):
                error = check_file_syntax(file_path)
                if error:
                    errors.append(error)
    else:
        # ディレクトリ内のすべてのPythonファイルをチェック
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    error = check_file_syntax(file_path)
                    if error:
                        errors.append(error)
    
    return errors

if __name__ == '__main__':
    if len(sys.argv) > 1:
        # ファイルリストが指定されている場合
        repo_dir = os.path.dirname(os.path.abspath(__file__))
        with open(sys.argv[1], 'r') as f:
            file_list = [line.strip() for line in f if line.strip()]
        errors = check_directory(repo_dir, file_list)
    else:
        # ディレクトリ内のすべてのPythonファイルをチェック
        repo_dir = os.path.dirname(os.path.abspath(__file__))
        errors = check_directory(repo_dir)
    
    if errors:
        print(f"{len(errors)}個のファイルに構文エラーがあります:")
        for error in errors:
            print(f"\n{error['file']}")
            print(f"  行 {error['line']}, 列 {error['column']}: {error['error']}")
        sys.exit(1)
    else:
        print("すべてのPythonファイルの構文は正常です。")
        sys.exit(0)
