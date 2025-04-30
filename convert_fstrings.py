#\!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
f-stringをformat()方式に変換するスクリプト
"""

import os
import re
import sys

def convert_fstrings_in_file(file_path):
    """ファイル内のf-stringをformat()方式に変換する"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # f-stringを検出するパターン
        pattern = r'f([\'"])((?:\\.|[^\\\1])*?)\1'
        
        def replace_fstring(match):
            quote = match.group(1)
            string_content = match.group(2)
            
            # 波括弧内の式を検出
            expr_pattern = r'{([^{}]*)}'
            exprs = re.findall(expr_pattern, string_content)
            
            if exprs:
                # 式を置き換える
                template = re.sub(expr_pattern, '{}', string_content)
                # format()を使用する形式に変換
                args = ', '.join(exprs)
                return f'{quote}{template}{quote}.format({args})'
            else:
                # 式がない場合はf-接頭辞を削除
                return f'{quote}{string_content}{quote}'
        
        # 変換実行
        new_content = re.sub(pattern, replace_fstring, content)
        
        # 変更があれば保存
        if new_content \!= content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True
        
        return False
    
    except Exception as e:
        print(f"エラー: {file_path} - {str(e)}")
        return False

def main():
    """メイン関数"""
    # プロジェクトのルートディレクトリ
    project_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 問題のあるファイルリストを読み込む
    problem_file_path = os.path.join(project_dir, 'problematic_files.txt')
    
    try:
        with open(problem_file_path, 'r') as f:
            problem_files = [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(f"エラー: {problem_file_path} を読み込めませんでした - {str(e)}")
        return 1
    
    print(f"{len(problem_files)}個の問題ファイルを処理します...")
    
    # 各ファイルを処理
    converted_count = 0
    for rel_path in problem_files:
        # 先頭の/を削除
        if rel_path.startswith('/'):
            rel_path = rel_path[1:]
        
        file_path = os.path.join(project_dir, rel_path)
        
        if os.path.isfile(file_path):
            if convert_fstrings_in_file(file_path):
                converted_count += 1
                print(f"変換完了: {rel_path}")
        else:
            print(f"スキップ: {rel_path} - ファイルが存在しません")
    
    print(f"\n処理完了: {converted_count}/{len(problem_files)}個のファイルを変換しました")
    return 0

if __name__ == "__main__":
    sys.exit(main())
