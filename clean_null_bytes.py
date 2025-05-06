#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NULL バイト除去スクリプト

テストファイル内の NULL バイト（\0）を検出して除去するスクリプト。
これらの NULL バイトがあると Python の処理時にエラーが発生します。
"""

import os
import argparse
from pathlib import Path
import re


def clean_file(file_path):
    """
    ファイルからヌル文字（NULL バイト）を除去する
    
    Parameters
    ----------
    file_path : str
        処理するファイルのパス
    
    Returns
    -------
    bool
        ヌル文字が見つかり、除去された場合は True、そうでなければ False
    """
    print(f"Processing file: {file_path}")
    
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
        return True
    
    return False


def process_directory(directory, pattern=None):
    """
    指定されたディレクトリ内のすべての Python ファイルを処理
    
    Parameters
    ----------
    directory : str
        処理するディレクトリのパス
    pattern : str, optional
        ファイル名のパターン（正規表現）
    
    Returns
    -------
    int
        処理されたファイルの数
    """
    directory_path = Path(directory)
    processed_files = 0
    cleaned_files = 0
    
    # パターンが指定されていれば、正規表現コンパイル
    if pattern:
        pattern_re = re.compile(pattern)
    
    # ディレクトリ内のすべてのPythonファイルを再帰的に処理
    for file_path in directory_path.glob('**/*.py'):
        # パターンが指定されていて、ファイル名がパターンにマッチしない場合はスキップ
        if pattern and not pattern_re.search(str(file_path)):
            continue
        
        processed_files += 1
        if clean_file(file_path):
            cleaned_files += 1
    
    print(f"Processed {processed_files} files, cleaned {cleaned_files} files")
    return processed_files


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Clean NULL bytes from Python files')
    parser.add_argument('directory', help='Directory to process')
    parser.add_argument('--pattern', help='Filename pattern (regex)')
    
    args = parser.parse_args()
    
    process_directory(args.directory, args.pattern)
