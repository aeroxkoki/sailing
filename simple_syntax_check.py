#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
シンプルな構文チェックスクリプト
"""

import os
import sys
import ast

def check_syntax(file_path):
    """ファイルの構文をチェックする"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        ast.parse(content)
        return None
    except SyntaxError as e:
        return f"行 {e.lineno}: {e.msg}"
    except Exception as e:
        return f"エラー: {str(e)}"

def main():
    """メイン関数"""
    # 特定のディレクトリを優先的にチェック
    target_dirs = [
        'sailing_data_processor/validation',
        'sailing_data_processor/reporting/elements'
    ]
    
    root_dir = os.path.dirname(os.path.abspath(__file__))
    
    for target_dir in target_dirs:
        full_path = os.path.join(root_dir, target_dir)
        print(f"\nディレクトリ {target_dir} をチェック中...")
        
        if not os.path.exists(full_path):
            print(f"  ディレクトリが見つかりません: {full_path}")
            continue
        
        for root, _, files in os.walk(full_path):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    error = check_syntax(file_path)
                    
                    if error:
                        rel_path = os.path.relpath(file_path, root_dir)
                        print(f"  [エラー] {rel_path}")
                        print(f"    {error}")
                    else:
                        rel_path = os.path.relpath(file_path, root_dir)
                        print(f"  [OK] {rel_path}")

if __name__ == "__main__":
    main()
