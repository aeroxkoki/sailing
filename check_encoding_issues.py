#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import traceback
import binascii

# NULL文字を含むファイルを検出する関数
def detect_null_bytes(file_path, max_output=1000):
    try:
        with open(file_path, 'rb') as f:
            content = f.read()
            if b'\x00' in content:
                null_positions = [i for i, b in enumerate(content) if b == 0]
                hex_view = binascii.hexlify(content[:max_output]).decode('ascii')
                formatted_hex = ' '.join(hex_view[i:i+2] for i in range(0, len(hex_view), 2))
                return True, f"ファイル {file_path} にNULLバイト({len(null_positions)}個)が含まれています。位置: {null_positions[:10]}... 先頭部分の16進数表示: {formatted_hex[:100]}..."
        return False, ""
    except Exception as e:
        return False, f"ファイル {file_path} の読み込み中にエラーが発生しました: {e}"

# UTF-8でデコードできないファイルを検出する関数
def detect_encoding_issues(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            f.read()
        return False, ""
    except UnicodeDecodeError as e:
        # バイナリとして読み込んで問題のあるバイトを表示
        with open(file_path, 'rb') as f:
            content = f.read(100)  # 最初の100バイトだけ表示
            hex_view = binascii.hexlify(content).decode('ascii')
            formatted_hex = ' '.join(hex_view[i:i+2] for i in range(0, len(hex_view), 2))
            
            return True, f"ファイル {file_path} はUTF-8としてデコードできません: {e}, 先頭バイト: {formatted_hex}"
    except Exception as e:
        return False, f"ファイル {file_path} の読み込み中にエラーが発生しました: {e}"

# 指定されたディレクトリ配下のPythonファイルをチェック
def check_directory(directory_path, extensions=None, verbose=True):
    if extensions is None:
        extensions = ['.py']
    
    null_byte_files = []
    encoding_issue_files = []
    
    # プログレス表示用変数
    total_files = 0
    processed_files = 0
    
    # ファイル数をカウント
    for root, _, files in os.walk(directory_path):
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                total_files += 1
    
    print(f"検査対象ファイル数: {total_files}")
    
    # ファイルをチェック
    for root, _, files in os.walk(directory_path):
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                file_path = os.path.join(root, file)
                processed_files += 1
                
                # 進捗を表示
                if verbose and processed_files % 50 == 0:
                    print(f"進捗: {processed_files}/{total_files} ファイル処理済み")
                
                # NULLバイトチェック
                has_null, null_message = detect_null_bytes(file_path)
                if has_null:
                    null_byte_files.append((file_path, null_message))
                    if verbose:
                        print(f"NULL: {file_path}")
                
                # エンコーディングチェック
                has_issue, issue_message = detect_encoding_issues(file_path)
                if has_issue:
                    encoding_issue_files.append((file_path, issue_message))
                    if verbose:
                        print(f"ENC: {file_path}")
    
    return null_byte_files, encoding_issue_files

# メイン処理
def main():
    target_dir = "."  # カレントディレクトリ
    if len(sys.argv) > 1:
        target_dir = sys.argv[1]
    
    print(f"ディレクトリ {target_dir} のPythonファイルをチェックします...")
    
    try:
        null_files, encoding_files = check_directory(target_dir)
        
        # 結果表示
        print("\n===== NULLバイトを含むファイル =====")
        if null_files:
            for file_path, message in null_files:
                print(message)
            print(f"NULLバイトを含むファイル数: {len(null_files)}")
        else:
            print("NULLバイトを含むファイルはありませんでした")
        
        print("\n===== エンコーディング問題があるファイル =====")
        if encoding_files:
            for file_path, message in encoding_files:
                print(message)
            print(f"エンコーディング問題があるファイル数: {len(encoding_files)}")
        else:
            print("エンコーディング問題があるファイルはありませんでした")
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
