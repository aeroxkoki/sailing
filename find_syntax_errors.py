#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
セーリング戦略分析システム - 構文エラー検出スクリプト

このスクリプトは指定されたディレクトリ内のPythonファイルの構文エラーを検出します。
特に辞書定義の閉じ括弧の欠落などの一般的な問題に焦点を当てています。
"""

import os
import sys
import tokenize
import io
import ast

def check_file_syntax(file_path):
    """
    ファイルの構文エラーを検出する
    
    Parameters
    ----------
    file_path : str
        チェックするPythonファイルのパス
    
    Returns
    -------
    tuple
        (エラーメッセージ, 行番号) または正常な場合は (None, None)
    """
    try:
        with open(file_path, 'rb') as f:
            content = f.read()
        
        # ファイルをデコードして構文エラーをチェック
        decoded_content = content.decode('utf-8')
        ast.parse(decoded_content)
        return None, None
    except SyntaxError as e:
        return str(e), e.lineno
    except UnicodeDecodeError:
        return "ファイルのデコードエラー", 0
    except Exception as e:
        return f"予期せぬエラー: {str(e)}", 0

def check_dict_brackets(file_path):
    """
    ファイル内の辞書定義で閉じ括弧が欠けている可能性のある箇所を検出する
    
    Parameters
    ----------
    file_path : str
        チェックするPythonファイルのパス
    
    Returns
    -------
    list
        問題のある箇所の行番号とコンテキストのリスト
    """
    issues = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        bracket_stack = []
        for i, line in enumerate(lines):
            # 辞書の始まりを検出
            if '= {' in line or ': {' in line:
                if '}' not in line:  # 同じ行に閉じ括弧がない場合
                    bracket_stack.append((i+1, line.strip()))
            
            # 閉じ括弧がある行
            if '}' in line:
                if bracket_stack:
                    bracket_stack.pop()
        
        # スタックに残った開始括弧は閉じられていない可能性がある
        for line_num, context in bracket_stack:
            issues.append((line_num, context))
        
        return issues
    except Exception as e:
        print(f"ファイル {file_path} の解析中にエラーが発生: {e}")
        return []

def find_syntax_errors(directory, extensions=['.py']):
    """
    ディレクトリ内の構文エラーのあるファイルを見つける
    
    Parameters
    ----------
    directory : str
        検索するディレクトリのパス
    extensions : list
        チェックするファイル拡張子のリスト
    
    Returns
    -------
    list
        問題のあるファイルとその詳細情報のリスト
    """
    error_files = []
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                file_path = os.path.join(root, file)
                
                # 構文エラーチェック
                error_msg, line_num = check_file_syntax(file_path)
                if error_msg:
                    error_files.append({
                        'path': file_path,
                        'error': error_msg,
                        'line': line_num,
                        'dict_issues': []
                    })
                    continue
                
                # 辞書の括弧の問題をチェック
                dict_issues = check_dict_brackets(file_path)
                if dict_issues:
                    error_files.append({
                        'path': file_path,
                        'error': '辞書の閉じ括弧が欠けている可能性',
                        'line': None,
                        'dict_issues': dict_issues
                    })
    
    return error_files

def main():
    """メイン関数"""
    if len(sys.argv) > 1:
        directory = sys.argv[1]
    else:
        directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sailing_data_processor')
    
    print(f"ディレクトリ {directory} の構文エラーを検索中...")
    
    error_files = find_syntax_errors(directory)
    
    if error_files:
        print(f"\n{len(error_files)} 個のファイルに構文エラーが見つかりました:")
        
        for file_info in error_files:
            print(f"\n[問題] {file_info['path']}")
            print(f"  エラー: {file_info['error']}")
            
            if file_info['line']:
                print(f"  行番号: {file_info['line']}")
            
            for line_num, context in file_info['dict_issues']:
                print(f"  辞書開始 (行 {line_num}): {context}")
        
        print("\nこれらのファイルを修正してからテストを再実行してください。")
        return 1
    else:
        print("構文エラーのあるファイルは見つかりませんでした。")
        return 0

if __name__ == "__main__":
    sys.exit(main())
