#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
デバッグスクリプト: Pythonファイルの構文エラーを検出

このスクリプトは、sailing_data_processorディレクトリ内の全てのPythonファイルを
構文エラーがないかチェックします。
"""

import os
import sys
import ast
import traceback
from pathlib import Path

def check_syntax(file_path):
    """
    Pythonファイルの構文エラーをチェック
    
    Parameters
    ----------
    file_path : str
        チェックするファイルのパス
        
    Returns
    -------
    tuple
        (成功したか, エラーメッセージ)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        # 構文解析を試行
        ast.parse(source, filename=file_path)
        return True, None
    except SyntaxError as e:
        return False, f"構文エラー: {str(e)}"
    except Exception as e:
        return False, f"その他のエラー: {str(e)}"

def scan_directory(root_dir):
    """
    ディレクトリ内の全Pythonファイルをスキャン
    
    Parameters
    ----------
    root_dir : str
        スキャンするディレクトリのパス
        
    Returns
    -------
    dict
        {ファイルパス: エラーメッセージ} の形式
    """
    error_files = {}
    
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                
                # 構文チェック
                success, error_msg = check_syntax(file_path)
                
                if not success:
                    error_files[file_path] = error_msg
    
    return error_files

def main():
    """
    メイン関数
    """
    # カレントディレクトリを取得
    current_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"スクリプト実行ディレクトリ: {current_dir}")
    
    # スキャンするディレクトリ
    target_dir = os.path.join(current_dir, 'sailing_data_processor')
    if not os.path.exists(target_dir):
        print(f"エラー: ディレクトリが存在しません: {target_dir}")
        return 1
    
    print(f"スキャン対象ディレクトリ: {target_dir}")
    print("構文チェックを開始します...")
    
    # ディレクトリをスキャン
    error_files = scan_directory(target_dir)
    
    if error_files:
        print(f"\n構文エラーが見つかりました ({len(error_files)} ファイル):")
        for file_path, error_msg in error_files.items():
            rel_path = os.path.relpath(file_path, current_dir)
            print(f"\n- {rel_path}")
            print(f"  {error_msg}")
    else:
        print("\n全てのファイルは構文的に正しいです。")
    
    # 特定のファイルを詳細にチェック
    problem_files = [
        'sailing_data_processor/validation/correction.py',
        'sailing_data_processor/validation/visualization.py',
        'sailing_data_processor/validation/quality_metrics.py',
        'sailing_data_processor/validation/quality_metrics_improvements.py',
        'sailing_data_processor/validation/quality_metrics_integration.py',
        'sailing_data_processor/validation/data_cleaner.py'
    ]
    
    print("\n指定したファイルの詳細チェック:")
    for rel_path in problem_files:
        file_path = os.path.join(current_dir, rel_path)
        
        if not os.path.exists(file_path):
            print(f"- {rel_path}: ファイルが存在しません")
            continue
            
        success, error_msg = check_syntax(file_path)
        
        if success:
            print(f"- {rel_path}: OK")
        else:
            print(f"- {rel_path}: NG - {error_msg}")
    
    return 0 if not error_files else 1

if __name__ == "__main__":
    sys.exit(main())
