#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ファイル編集ヘルパースクリプト
GUIエディタを起動せず、テキストファイルを直接編集するためのユーティリティ

使用方法:
python3 edit_helper.py <file_path> [<line_number>]
"""

import sys
import os
import tempfile
import subprocess
import shutil

def edit_file_safe(file_path, line_number=None):
    """
    ファイルを安全に編集（GUIエディタを起動せず）
    
    Parameters:
    -----------
    file_path : str
        編集するファイルのパス
    line_number : int, optional
        編集を開始する行番号
    """
    try:
        # ファイルの存在確認
        if not os.path.exists(file_path):
            print(f"エラー: ファイル '{file_path}' が見つかりません。")
            return False
            
        # 一時ファイルの作成
        with tempfile.NamedTemporaryFile(suffix='.tmp', mode='w', delete=False) as temp:
            temp_path = temp.name
            
            # 元のファイルの内容をコピー
            with open(file_path, 'r') as src:
                content = src.read()
                temp.write(content)
        
        # エディタを使って一時ファイルを編集
        editor = os.environ.get('EDITOR', 'nano')  # 環境変数EDITORを使用、デフォルトはnano
        cmd = [editor, temp_path]
        
        # 行番号が指定されていれば、エディタによって適切なオプションを追加
        if line_number is not None:
            if editor == 'nano':
                cmd = [editor, f"+{line_number}", temp_path]
            elif editor == 'vim' or editor == 'vi':
                cmd = [editor, f"+{line_number}", temp_path]
            # その他のエディタにも対応可能
        
        print(f"エディタ {editor} を使用してファイルを編集しています...")
        subprocess.call(cmd)
        
        # 編集済みの一時ファイルの内容を元のファイルに書き戻す
        shutil.copy2(temp_path, file_path)
        os.unlink(temp_path)  # 一時ファイルを削除
        
        print(f"ファイル '{file_path}' の編集が完了しました。")
        return True
        
    except Exception as e:
        print(f"エラー: ファイル編集中に問題が発生しました: {e}")
        return False

def main():
    # コマンドライン引数のチェック
    if len(sys.argv) < 2:
        print("使用方法: python3 edit_helper.py <file_path> [<line_number>]")
        return
    
    file_path = sys.argv[1]
    line_number = int(sys.argv[2]) if len(sys.argv) > 2 else None
    
    edit_file_safe(file_path, line_number)

if __name__ == "__main__":
    main()
