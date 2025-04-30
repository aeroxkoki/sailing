#!/usr/bin/env python3

import os
import re
import sys

def check_f_string_syntax(file_path):
    """
    ファイル内のf-string構文をチェックします。
    """
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
        
    # f-stringの検出
    f_string_pattern = r'f[\"\'].*?[\"\']'
    f_strings = re.findall(f_string_pattern, content, re.DOTALL)
    
    # 問題のあるf-stringを特定
    issues = []
    for f_string in f_strings:
        # 単一の中括弧が外側にある場合
        if '}' in f_string and not '{' in f_string:
            issues.append(f_string)
        # 中括弧内に引用符がない場合
        elif re.search(r'{[^\'\"{}]*}', f_string):
            issues.append(f_string)
    
    return issues

def find_python_files(directory):
    """
    指定されたディレクトリ内の.pyファイルを再帰的に検索します。
    """
    python_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    return python_files

def main():
    # プロジェクトディレクトリ
    project_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Pythonファイルのリストを取得
    python_files = find_python_files(os.path.join(project_dir, 'sailing_data_processor'))
    
    # 各ファイルをチェック
    for file_path in python_files:
        issues = check_f_string_syntax(file_path)
        if issues:
            print(f"\n問題のあるファイル: {file_path}")
            for i, issue in enumerate(issues):
                print(f"  問題 {i+1}: {issue}")

if __name__ == "__main__":
    main()
