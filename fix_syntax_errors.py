#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
セーリング戦略分析システム - 構文エラー修正スクリプト

このスクリプトは指定されたディレクトリ内のPythonファイルの構文エラーを修正します。
特に辞書定義の閉じ括弧の欠落などの一般的な問題を修正します。
"""

import os
import sys
import re
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

def find_unbalanced_dicts(file_path):
    """
    ファイル内の辞書定義で閉じ括弧が欠けている箇所を検出する
    
    Parameters
    ----------
    file_path : str
        チェックするPythonファイルのパス
    
    Returns
    -------
    list
        問題のある箇所のリスト (開始行, 終了行, インデントレベル)
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    issues = []
    dict_stack = []  # (開始行, インデントレベル)
    
    for i, line in enumerate(lines):
        stripped = line.rstrip()
        indent = len(line) - len(line.lstrip())
        
        # 辞書の開始を検出
        if re.search(r'[=:]\s*{', stripped) and not stripped.rstrip().endswith('}'):
            dict_stack.append((i, indent))
        
        # 辞書の終了を検出
        elif '}' in stripped:
            if dict_stack:
                dict_stack.pop()
        
        # インデントが戻った場合、辞書が閉じられていない可能性がある
        elif dict_stack and indent <= dict_stack[-1][1] and not stripped.endswith('\\'):
            start_line, start_indent = dict_stack.pop()
            issues.append((start_line, i-1, start_indent))
    
    # スタックに残った開始括弧は閉じられていない可能性がある
    for start_line, indent in dict_stack:
        issues.append((start_line, len(lines)-1, indent))
    
    return issues

def fix_unbalanced_dicts(file_path):
    """
    ファイル内の閉じられていない辞書定義を修正する
    
    Parameters
    ----------
    file_path : str
        修正するPythonファイルのパス
    
    Returns
    -------
    int
        修正された問題の数
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    issues = find_unbalanced_dicts(file_path)
    
    if not issues:
        return 0
    
    # 逆順に修正していく（行番号への影響を避けるため）
    modified_lines = lines.copy()
    fixes_count = 0
    
    for start_line, end_line, indent in sorted(issues, reverse=True):
        # 終了行の次の行に閉じ括弧を追加
        indent_str = ' ' * indent
        closing_line = f"{indent_str}}}\n"
        
        # 挿入位置の調整（コメント行やインデントの変化を考慮）
        insert_line = end_line + 1
        
        # 閉じ括弧の挿入
        modified_lines.insert(insert_line, closing_line)
        fixes_count += 1
    
    # 修正内容を書き込み
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(modified_lines)
    
    return fixes_count

def find_and_fix_syntax_errors(directory, extensions=['.py'], dry_run=False):
    """
    ディレクトリ内の構文エラーのあるファイルを見つけて修正する
    
    Parameters
    ----------
    directory : str
        検索するディレクトリのパス
    extensions : list
        チェックするファイル拡張子のリスト
    dry_run : bool
        True の場合は変更を適用せず、問題箇所を報告するのみ
    
    Returns
    -------
    dict
        処理結果の統計情報
    """
    stats = {
        'checked': 0,
        'with_errors': 0,
        'fixed': 0,
        'fixes_applied': 0
    }
    
    error_files = []
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                file_path = os.path.join(root, file)
                stats['checked'] += 1
                
                # 構文エラーチェック
                error_msg, line_num = check_file_syntax(file_path)
                if error_msg:
                    stats['with_errors'] += 1
                    error_files.append({
                        'path': file_path,
                        'error': error_msg,
                        'line': line_num,
                        'fixed': False
                    })
                    
                    # 修正を試みる
                    if not dry_run:
                        fixes = fix_unbalanced_dicts(file_path)
                        if fixes > 0:
                            stats['fixes_applied'] += fixes
                            error_files[-1]['fixed'] = True
                            stats['fixed'] += 1
    
    return stats, error_files

def main():
    """メイン関数"""
    # コマンドライン引数の解析
    dry_run = False
    directory = None
    
    for arg in sys.argv[1:]:
        if arg == '--dry-run':
            dry_run = True
        elif not arg.startswith('-'):
            directory = arg
    
    if not directory:
        directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sailing_data_processor')
    
    print(f"ディレクトリ {directory} の構文エラーを検索中...")
    if dry_run:
        print("ドライラン: 実際の修正は行いません")
    
    stats, error_files = find_and_fix_syntax_errors(directory, dry_run=dry_run)
    
    print(f"\n処理結果:")
    print(f"  チェック済みファイル: {stats['checked']}")
    print(f"  エラーのあるファイル: {stats['with_errors']}")
    
    if not dry_run:
        print(f"  修正したファイル: {stats['fixed']}")
        print(f"  適用した修正: {stats['fixes_applied']}")
    
    if error_files:
        print(f"\n問題が見つかったファイル:")
        
        for file_info in error_files:
            status = "修正済み" if file_info.get('fixed') else "未修正"
            print(f"  {file_info['path']} ({status})")
            print(f"    エラー: {file_info['error']}")
            if file_info['line']:
                print(f"    行番号: {file_info['line']}")
        
        if dry_run or stats['with_errors'] > stats['fixed']:
            print("\n一部のファイルが修正されていません。手動で修正してください。")
            return 1
        else:
            print("\nすべてのファイルが修正されました。")
            return 0
    else:
        print("\n構文エラーのあるファイルは見つかりませんでした。")
        return 0

if __name__ == "__main__":
    sys.exit(main())
