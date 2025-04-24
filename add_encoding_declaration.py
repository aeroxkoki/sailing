#!/usr/bin/env python3
"""
Pythonファイルにエンコーディング宣言を追加するスクリプト
"""

import os
import sys
import re
import glob

def add_encoding_declaration(file_path):
    """
    ファイルが既にエンコーディング宣言を持っていない場合、追加します
    """
    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    
    # 既にエンコーディング宣言があるかチェック
    if re.search(r'coding[:=]\s*([-\w.]+)', content):
        print(f"✓ {file_path} には既にエンコーディング宣言があります")
        return False
    
    # シバン行があるかチェック
    has_shebang = content.startswith('#!')
    
    # ファイルの先頭に適切な宣言を追加
    if has_shebang:
        lines = content.split('\n')
        new_content = lines[0] + '\n# -*- coding: utf-8 -*-\n' + '\n'.join(lines[1:])
    else:
        new_content = '# -*- coding: utf-8 -*-\n' + content
    
    # 変更をファイルに書き込み
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"+ {file_path} にエンコーディング宣言を追加しました")
    return True

def process_directory(directory_path, pattern="*.py"):
    """
    指定されたディレクトリ内のPythonファイルを処理します
    """
    modified_count = 0
    skipped_count = 0
    
    # 指定されたパターンに一致するファイルを取得
    file_paths = glob.glob(os.path.join(directory_path, '**', pattern), recursive=True)
    
    print(f"{len(file_paths)}個のPythonファイルを処理します...")
    
    for file_path in file_paths:
        try:
            if add_encoding_declaration(file_path):
                modified_count += 1
            else:
                skipped_count += 1
        except Exception as e:
            print(f"! {file_path} の処理中にエラーが発生しました: {e}")
    
    print(f"\n処理結果:")
    print(f"- 処理されたファイル数: {len(file_paths)}")
    print(f"- 修正されたファイル: {modified_count}")
    print(f"- スキップされたファイル: {skipped_count}")

def main():
    """
    メイン関数
    """
    # コマンドライン引数からディレクトリを取得
    if len(sys.argv) > 1:
        directory_path = sys.argv[1]
    else:
        # デフォルトはtestsディレクトリ
        directory_path = "tests"
    
    print(f"ディレクトリ '{directory_path}' のPythonファイルにエンコーディング宣言を追加します")
    
    # ディレクトリを処理
    process_directory(directory_path)

if __name__ == "__main__":
    main()
