#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
カッコの不一致を見つけるスクリプト

このスクリプトは、Pythonファイル内で括弧（{}[]()）の数が一致しているかチェックします。
閉じられていない括弧があるファイルを検出します。
"""

import os
import sys
import tokenize
import io
from pathlib import Path

def check_brackets_balance(file_path):
    """
    ファイル内の括弧のバランスをチェック
    
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
            content = f.read()
            
        # 括弧の数をカウント
        brackets = {'(': 0, ')': 0, '{': 0, '}': 0, '[': 0, ']': 0}
        line_counts = {}
        
        for i, line in enumerate(content.splitlines(), 1):
            for char in line:
                if char in brackets:
                    brackets[char] += 1
                    if char in ['(', '{', '[']:
                        if i not in line_counts:
                            line_counts[i] = {}
                        if char not in line_counts[i]:
                            line_counts[i][char] = 0
                        line_counts[i][char] += 1
        
        # 括弧のペアをチェック
        issues = []
        if brackets['('] != brackets[')']:
            issues.append(f"丸括弧の不一致: ( = {brackets['(']}, ) = {brackets[')']} (差: {brackets['('] - brackets[')']})")
        if brackets['{'] != brackets['}']:
            issues.append(f"波括弧の不一致: {{ = {brackets['{']}, }} = {brackets['}']} (差: {brackets['{'] - brackets['}']})") 
        if brackets['['] != brackets[']']:
            issues.append(f"角括弧の不一致: [ = {brackets['[']}, ] = {brackets[']']} (差: {brackets['['] - brackets[']']})")
        
        # 問題がある行と括弧の種類を特定
        problematic_lines = {}
        if issues:
            for line_num, chars in line_counts.items():
                if any(char in chars for char in ['(', '{', '[']):
                    problematic_lines[line_num] = chars
        
        return (len(issues) == 0, issues, problematic_lines)
    except UnicodeDecodeError:
        return (False, ["ファイルのエンコーディングに問題があります"], {})
    except Exception as e:
        return (False, [f"その他のエラー: {str(e)}"], {})

def scan_directory(root_dir, ext='.py'):
    """
    ディレクトリ内のファイルをスキャン
    
    Parameters
    ----------
    root_dir : str
        スキャンするディレクトリのパス
    ext : str, optional
        チェックするファイルの拡張子
        
    Returns
    -------
    dict
        {ファイルパス: (エラーメッセージ, 問題のある行)} の形式
    """
    error_files = {}
    
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith(ext):
                file_path = os.path.join(root, file)
                
                # 括弧のバランスをチェック
                success, issues, problematic_lines = check_brackets_balance(file_path)
                
                if not success:
                    error_files[file_path] = (issues, problematic_lines)
    
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
    
    target_dir_rel = os.path.relpath(target_dir, current_dir)
    print(f"スキャン対象ディレクトリ: {target_dir_rel}")
    print("括弧バランスのチェックを開始します...")
    
    # ディレクトリをスキャン
    error_files = scan_directory(target_dir)
    
    if error_files:
        print(f"\n括弧の不一致が見つかりました ({len(error_files)} ファイル):")
        for file_path, (issues, problematic_lines) in error_files.items():
            rel_path = os.path.relpath(file_path, current_dir)
            print(f"\n- {rel_path}")
            for issue in issues:
                print(f"  {issue}")
            
            if problematic_lines:
                print("  問題のある可能性がある行:")
                for line_num, chars in sorted(problematic_lines.items()):
                    char_info = ", ".join([f"{char}: {count}" for char, count in chars.items()])
                    print(f"  - 行 {line_num}: {char_info}")
    else:
        print("\n全てのファイルの括弧はバランスが取れています。")
    
    return 0 if not error_files else 1

if __name__ == "__main__":
    sys.exit(main())
