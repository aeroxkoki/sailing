# -*- coding: utf-8 -*-
#\!/usr/bin/env python3
import os
import glob

def fix_file_encoding(file_path):
    """ファイルの文字エンコーディングを修正"""
    try:
        # まず UTF-8 として読み込みを試みる
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            # UTF-8 として正常に読めたら処理不要
            print(f"OK: {file_path}")
            return False
        except UnicodeDecodeError:
            pass  # エラーが発生したら次のステップへ
        
        # バイナリとして読み込んでヌルバイトを削除
        with open(file_path, 'rb') as f:
            content = f.read()
        
        # ヌルバイトとその他の無効なバイトを削除
        content_fixed = content.replace(b'\x00', b'')
        
        # 元のファイルをバックアップ
        backup_path = file_path + '.bak'
        os.rename(file_path, backup_path)
        
        # 修正したコンテンツを UTF-8 で書き込み
        with open(file_path, 'wb') as f:
            f.write(content_fixed)
        
        print(f"修正: {file_path}")
        return True
    except Exception as e:
        print(f"エラー ({file_path}): {e}")
        return False

def main():
    # 対象ディレクトリ
    base_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(base_dir, 'backend')
    
    # 全Pythonファイルを処理
    fixed_count = 0
    total_count = 0
    
    for root, _, files in os.walk(backend_dir):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                total_count += 1
                if fix_file_encoding(file_path):
                    fixed_count += 1
    
    print(f"処理完了: {fixed_count}/{total_count} ファイルを修正しました")

if __name__ == "__main__":
    main()
