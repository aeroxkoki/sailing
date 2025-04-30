#\!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
f-stringをformat()方式に変換するスクリプト

このスクリプトは、指定されたPythonファイル内のf-stringを従来の.format()方式に変換します。
特にPython 3.6未満との互換性を確保するために使用します。
"""

import os
import re
import sys

def convert_f_strings(file_path):
    """
    ファイル内のf-stringを従来の.format()方式に変換する
    
    Parameters
    ----------
    file_path : str
        変換するPythonファイルのパス
    
    Returns
    -------
    int
        変換されたf-stringの数
    """
    try:
        # ファイルを読み込み
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            content = file.read()
        
        # 変換前の内容を保存
        original_content = content
        
        # 簡易的なf-stringパターン（完全ではありませんが基本的なケースを処理）
        f_string_pattern = r'f(["\'])(.*?)\1'
        
        # 置換回数をカウント
        count = 0
        
        # 基本的なf-string変換関数
        def convert_match(match):
            nonlocal count
            quote_char = match.group(1)
            string_content = match.group(2)
            
            # 括弧内の式を抽出
            format_parts = []
            format_vars = []
            
            # 正規表現でf-string内の式を検出
            expr_pattern = r'{([^{}]*)}'
            for expr_match in re.finditer(expr_pattern, string_content):
                expr = expr_match.group(1)
                format_vars.append(expr)
                
            # f-stringを.format()に変換
            if format_vars:
                count += 1
                # 括弧をエスケープして文字列テンプレートを作成
                template = re.sub(r'{([^{}]*)}', '{}', string_content)
                # エスケープされた括弧を復元
                template = template.replace('{{', '{').replace('}}', '}')
                # .format()を使用した文字列を構築
                format_args = ', '.join(format_vars)
                return f'{quote_char}{template}{quote_char}.format({format_args})'
            
            # f-stringが式を含まない場合はそのまま返す（f-prefixを削除）
            return f'{quote_char}{string_content}{quote_char}'
        
        # f-stringを変換
        converted_content = re.sub(f_string_pattern, convert_match, content)
        
        # 変更があった場合のみファイルに書き込み
        if converted_content \!= original_content:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(converted_content)
            
            return count
        
        return 0
    
    except Exception as e:
        print(f"エラー（{file_path}）: {str(e)}")
        return 0

def process_files_from_list(file_list_path, base_dir='.'):
    """
    ファイルリストからPythonファイルのf-stringを変換する
    
    Parameters
    ----------
    file_list_path : str
        ファイルリストのパス
    base_dir : str, optional
        ベースディレクトリ, by default '.'
    
    Returns
    -------
    tuple
        (処理ファイル数, 変換f-string数)
    """
    # ファイルリストを読み込み
    with open(file_list_path, 'r') as file:
        file_paths = [line.strip() for line in file if line.strip()]
    
    processed = 0
    converted = 0
    
    # 各ファイルを処理
    for rel_path in file_paths:
        # パスの正規化
        if rel_path.startswith('/'):
            rel_path = rel_path[1:]
        
        file_path = os.path.join(base_dir, rel_path)
        
        if os.path.isfile(file_path) and file_path.endswith('.py'):
            # f-stringを変換
            count = convert_f_strings(file_path)
            processed += 1
            converted += count
            
            if count > 0:
                print(f"変換: {file_path} - {count}個のf-stringを変換")
        else:
            print(f"スキップ: {file_path} - ファイルが存在しないかPythonファイルではありません")
    
    return processed, converted

def main():
    """
    メイン関数
    """
    # プロジェクトルートディレクトリ
    project_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 処理するファイルリスト
    if len(sys.argv) > 1:
        file_list_path = sys.argv[1]
    else:
        file_list_path = 'problematic_files.txt'
    
    if not os.path.isfile(file_list_path):
        print(f"エラー: ファイル {file_list_path} が見つかりません")
        return 1
    
    print(f"ファイルリスト {file_list_path} からf-stringを変換します...")
    
    # ファイルを処理
    processed, converted = process_files_from_list(file_list_path, project_dir)
    
    # 結果を表示
    print("\n変換結果:")
    print(f"  処理ファイル数: {processed}")
    print(f"  変換f-string数: {converted}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
