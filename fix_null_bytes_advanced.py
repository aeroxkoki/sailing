#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
拡張版 NULL バイト除去スクリプト

ファイル内の不正な文字を検出し、それらを置換するスクリプト。
正しいUTF-8エンコーディングで再保存します。
"""

import os
import argparse
from pathlib import Path
import re
import binascii
import codecs

def show_file_details(file_path):
    """
    ファイルの詳細情報を表示する
    
    Parameters
    ----------
    file_path : str
        処理するファイルのパス
    """
    print(f"\nFile details for: {file_path}")
    
    # バイナリモードでファイルを読み込み
    with open(file_path, 'rb') as f:
        content = f.read()
    
    # ファイルサイズと最初の100バイトのHEX表示
    print(f"File size: {len(content)} bytes")
    print(f"First 100 bytes (hex): {content[:100].hex()}")
    
    # NULL バイトがあるか確認
    null_count = content.count(b'\x00')
    if null_count > 0:
        null_positions = [i for i, byte in enumerate(content) if byte == 0]
        print(f"NULL bytes found: {null_count} at positions: {null_positions[:10]}{'...' if len(null_positions) > 10 else ''}")
    else:
        print("No NULL bytes found")
    
    # デコードエラーの発生場所を特定
    try:
        content.decode('utf-8')
        print("File is valid UTF-8")
    except UnicodeDecodeError as e:
        print(f"UTF-8 decode error: {e}")
        
        # エラー位置の周辺のバイトを表示
        error_start = max(0, e.start - 10)
        error_end = min(len(content), e.end + 10)
        error_bytes = content[error_start:error_end]
        print(f"Bytes around error (hex): {error_bytes.hex()}")
        
        # エラー位置のバイトを詳細表示
        error_exact = content[e.start:e.end]
        print(f"Error bytes (hex): {error_exact.hex()}")
        print(f"Error bytes (decimal): {list(error_exact)}")

def clean_file(file_path, make_backup=True):
    """
    ファイルから不正なバイトを除去して、UTF-8で再保存する
    
    Parameters
    ----------
    file_path : str
        処理するファイルのパス
    make_backup : bool
        バックアップを作成するかどうか
    
    Returns
    -------
    bool
        ファイルが修正された場合はTrue、そうでなければFalse
    """
    print(f"Processing file: {file_path}")
    
    # バックアップ作成
    if make_backup:
        backup_path = f"{file_path}.bak"
        with open(file_path, 'rb') as src, open(backup_path, 'wb') as dst:
            dst.write(src.read())
        print(f"Backup created: {backup_path}")
    
    # バイナリモードでファイルを読み込み
    with open(file_path, 'rb') as f:
        content = f.read()
    
    # 不正なバイトを検出
    has_null_bytes = b'\x00' in content
    
    try:
        # UTF-8でデコード（エラーがないか確認）
        content.decode('utf-8')
        is_valid_utf8 = True
    except UnicodeDecodeError:
        is_valid_utf8 = False
    
    if not has_null_bytes and is_valid_utf8:
        print(f"File is clean: {file_path}")
        return False
    
    # 変更があった場合のみ処理
    modified = False
    
    # NULL バイトを除去
    if has_null_bytes:
        content = content.replace(b'\x00', b'')
        modified = True
        print(f"NULL bytes removed from {file_path}")
    
    # エンコードの問題を修正（可能な限り）
    if not is_valid_utf8:
        try:
            # errors='replace'で不正なシーケンスを置換文字に置き換え
            decoded = content.decode('utf-8', errors='replace')
            content = decoded.encode('utf-8')
            modified = True
            print(f"Invalid UTF-8 sequences replaced in {file_path}")
        except Exception as e:
            print(f"Error during encoding fix: {e}")
    
    if modified:
        # ファイルを上書き
        with open(file_path, 'wb') as f:
            f.write(content)
        
        print(f"Cleaned {file_path}")
        return True
    
    return False

def process_directory(directory, pattern=None, cleanup=True, details=False, test_only=False):
    """
    指定されたディレクトリ内のPythonファイルを処理
    
    Parameters
    ----------
    directory : str
        処理するディレクトリのパス
    pattern : str, optional
        ファイル名のパターン（正規表現）
    cleanup : bool
        ファイルをクリーンアップするかどうか
    details : bool
        詳細情報を表示するかどうか
    test_only : bool
        テスト用ファイルのみを処理するかどうか
    
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
    
    # 処理対象のファイル拡張子
    file_pattern = '**/*.py' if not test_only else '**/test_*.py'
    
    # ディレクトリ内のすべてのPythonファイルを再帰的に処理
    for file_path in directory_path.glob(file_pattern):
        # パターンが指定されていて、ファイル名がパターンにマッチしない場合はスキップ
        if pattern and not pattern_re.search(str(file_path)):
            continue
        
        processed_files += 1
        
        if details:
            show_file_details(file_path)
        
        if cleanup:
            if clean_file(file_path):
                cleaned_files += 1
    
    print(f"Processed {processed_files} files, cleaned {cleaned_files} files")
    return processed_files

def process_specific_files(file_paths, cleanup=True, details=True):
    """
    指定されたファイルを処理
    
    Parameters
    ----------
    file_paths : list
        処理するファイルのパスのリスト
    cleanup : bool
        ファイルをクリーンアップするかどうか
    details : bool
        詳細情報を表示するかどうか
    
    Returns
    -------
    int
        処理されたファイルの数
    """
    processed_files = 0
    cleaned_files = 0
    
    for file_path in file_paths:
        path = Path(file_path)
        if not path.exists():
            print(f"File does not exist: {path}")
            continue
        
        processed_files += 1
        
        if details:
            show_file_details(path)
        
        if cleanup:
            if clean_file(path):
                cleaned_files += 1
    
    print(f"Processed {processed_files} files, cleaned {cleaned_files} files")
    return processed_files

def main():
    parser = argparse.ArgumentParser(description='Clean NULL bytes and invalid UTF-8 sequences from Python files')
    parser.add_argument('--directory', help='Directory to process')
    parser.add_argument('--file', action='append', help='Specific file to process (can be used multiple times)')
    parser.add_argument('--pattern', help='Filename pattern (regex)')
    parser.add_argument('--details', action='store_true', help='Show detailed file information')
    parser.add_argument('--no-cleanup', action='store_true', help='Do not modify files, just show information')
    parser.add_argument('--test-only', action='store_true', help='Process only test_*.py files')
    parser.add_argument('--test-project', action='store_true', help='Process only test_project directory')
    
    args = parser.parse_args()
    
    # デフォルトの処理: 問題のテストファイルを処理
    if not args.directory and not args.file and not args.test_project:
        # プロジェクトのルートディレクトリ
        root_dir = Path(__file__).parent
        
        # 問題のあるファイルのパス
        problem_files = [
            root_dir / "tests" / "test_project" / "test_import_integration.py",
            root_dir / "tests" / "test_project" / "test_project_storage.py"
        ]
        
        return process_specific_files(
            problem_files, 
            cleanup=not args.no_cleanup, 
            details=args.details
        )
    
    # test_project ディレクトリの処理
    if args.test_project:
        root_dir = Path(__file__).parent
        test_project_dir = root_dir / "tests" / "test_project"
        
        return process_directory(
            test_project_dir,
            pattern=args.pattern,
            cleanup=not args.no_cleanup,
            details=args.details
        )
    
    # 指定されたディレクトリの処理
    if args.directory:
        return process_directory(
            args.directory,
            pattern=args.pattern,
            cleanup=not args.no_cleanup,
            details=args.details,
            test_only=args.test_only
        )
    
    # 指定されたファイルの処理
    if args.file:
        return process_specific_files(
            args.file,
            cleanup=not args.no_cleanup,
            details=args.details
        )

if __name__ == "__main__":
    main()
