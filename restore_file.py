#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
バックアップからファイルを復元するスクリプト
"""
import os
import sys
import shutil

def restore_file(backup_path):
    """バックアップからファイルを復元"""
    if not backup_path.endswith('.bak'):
        print(f"Error: {backup_path} はバックアップファイルではありません")
        return False
    
    original_path = backup_path[:-4]  # .bakを除去
    
    if not os.path.exists(backup_path):
        print(f"Error: バックアップファイル {backup_path} が見つかりません")
        return False
    
    try:
        shutil.copy2(backup_path, original_path)
        print(f"ファイルを復元しました: {original_path}")
        return True
    except Exception as e:
        print(f"復元中にエラーが発生しました: {str(e)}")
        return False

def main():
    """メイン関数"""
    # コマンドライン引数からバックアップファイルのパスを取得
    if len(sys.argv) < 2:
        print("使用法: python restore_file.py <backup_file_path> [backup_file_path2 ...]")
        return
    
    success_count = 0
    for backup_path in sys.argv[1:]:
        if restore_file(backup_path):
            success_count += 1
    
    print(f"\n{len(sys.argv) - 1} ファイル中 {success_count} ファイルの復元に成功しました")

if __name__ == "__main__":
    main()
