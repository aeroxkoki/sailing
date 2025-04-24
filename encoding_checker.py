#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
エンコーディング宣言のチェックと追加を行うスクリプト

このスクリプトはリポジトリ内のすべてのPythonファイルをスキャンし、
エンコーディング宣言（# -*- coding: utf-8 -*-）がないファイルを探し、
必要に応じて追加します。
"""

import os
import sys
import glob

def check_encoding_declaration(file_path):
    """
    ファイルにエンコーディング宣言があるかチェックする
    
    Parameters:
    -----------
    file_path : str
        チェックするファイルのパス
        
    Returns:
    --------
    bool
        エンコーディング宣言がある場合はTrue、ない場合はFalse
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()
            second_line = f.readline().strip() if first_line else ""
            
            # 1行目または2行目にエンコーディング宣言があるかチェック
            return "# -*- coding: utf-8 -*-" in first_line or "# -*- coding: utf-8 -*-" in second_line
    except UnicodeDecodeError:
        print(f"Warning: Cannot decode file as UTF-8: {file_path}")
        return False
    except Exception as e:
        print(f"Error checking file {file_path}: {e}")
        return False

def add_encoding_declaration(file_path):
    """
    ファイルにエンコーディング宣言を追加する
    
    Parameters:
    -----------
    file_path : str
        エンコーディング宣言を追加するファイルのパス
        
    Returns:
    --------
    bool
        追加に成功した場合はTrue、それ以外はFalse
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        lines = content.splitlines()
        if not lines:
            # 空のファイルの場合は宣言を追加して終了
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("# -*- coding: utf-8 -*-\n")
            return True
            
        first_line = lines[0]
        
        if first_line.startswith("#!"):
            # Shebang行がある場合は2行目に追加
            lines.insert(1, "# -*- coding: utf-8 -*-")
        else:
            # Shebang行がない場合は1行目に追加
            lines.insert(0, "# -*- coding: utf-8 -*-")
            
        # ファイルを上書き
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))
            
        return True
    except Exception as e:
        print(f"Error adding encoding declaration to {file_path}: {e}")
        return False

def scan_repository(base_path):
    """
    リポジトリ内のすべてのPythonファイルをスキャンし、エンコーディング宣言をチェック・追加する
    
    Parameters:
    -----------
    base_path : str
        リポジトリのベースパス
    """
    # 避けるべきディレクトリパターン
    exclude_dirs = [
        "venv", 
        "__pycache__", 
        ".git", 
        "node_modules",
        "backend/venv",
        "backend/test_venv"
    ]
    
    # 結果カウンタ
    total_files = 0
    missing_encoding = 0
    added_encoding = 0
    
    # すべてのPythonファイルを検索
    for root, dirs, files in os.walk(base_path):
        # 除外ディレクトリをスキップ
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                total_files += 1
                
                if not check_encoding_declaration(file_path):
                    missing_encoding += 1
                    print(f"Missing encoding declaration: {file_path}")
                    
                    # エンコーディング宣言を追加
                    if add_encoding_declaration(file_path):
                        added_encoding += 1
                        print(f"  Added encoding declaration")
    
    # 結果を出力
    print(f"\nスキャン結果:")
    print(f"合計Pythonファイル数: {total_files}")
    print(f"エンコーディング宣言がないファイル: {missing_encoding}")
    print(f"エンコーディング宣言を追加したファイル: {added_encoding}")

if __name__ == "__main__":
    # コマンドライン引数からベースパスを取得、指定がなければカレントディレクトリを使用
    base_path = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    print(f"Scanning repository: {base_path}")
    
    scan_repository(base_path)
