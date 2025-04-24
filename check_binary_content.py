#!/usr/bin/env python3
"""
バイナリコンテンツを確認するスクリプト
NULL バイトや非 UTF-8 文字を検出します
"""

import os
import sys

def check_file(filepath):
    """
    ファイルのバイナリ内容を調査し、問題を報告します
    """
    print(f"ファイル調査: {filepath}")
    
    # ファイルが存在するか確認
    if not os.path.exists(filepath):
        print(f"  エラー: ファイルが存在しません")
        return False
        
    try:
        # バイナリモードで読み込み
        with open(filepath, 'rb') as f:
            content = f.read()
            
        file_size = len(content)
        print(f"  ファイルサイズ: {file_size} バイト")
        
        # NULL バイトを検出
        null_count = content.count(b'\x00')
        if null_count > 0:
            print(f"  警告: {null_count} NULLバイト検出")
            # 最初の数箇所を表示
            positions = [i for i in range(len(content)) if content[i:i+1] == b'\x00']
            print(f"  最初の10箇所: {positions[:10]}")
        
        # UTF-8 でデコード可能か確認
        try:
            text = content.decode('utf-8')
            print("  UTF-8としてデコード: 成功")
        except UnicodeDecodeError as e:
            print(f"  UTF-8としてデコード: 失敗 ({e})")
            # 問題の箇所周辺のバイトを表示
            error_pos = e.start
            print(f"  問題の周辺バイト: {content[max(0, error_pos-10):error_pos+10]}")
            
        # バイナリダンプ (最初の100バイト)
        if file_size > 0:
            print("  先頭100バイト:")
            hex_dump = ' '.join([f'{b:02x}' for b in content[:100]])
            print(f"  {hex_dump}")
            
        return True
    except Exception as e:
        print(f"  エラー: {str(e)}")
        return False

def main():
    """
    メイン関数
    """
    if len(sys.argv) < 2:
        print("使用方法: python3 check_binary_content.py <ファイルパス>")
        return
        
    filepath = sys.argv[1]
    check_file(filepath)

if __name__ == "__main__":
    main()
