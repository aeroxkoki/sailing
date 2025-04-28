#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
セーリング戦略分析システムのすべてのPythonファイルのエンコーディングを修正する
"""

import os
import sys
import codecs
import glob

def fix_file_encoding(file_path, output_path=None, input_encoding='utf-8', output_encoding='utf-8'):
    """
    ファイルのエンコーディングを修正して保存
    
    Parameters:
    -----------
    file_path : str
        元のファイルのパス
    output_path : str, optional
        出力ファイルのパス。Noneの場合は上書き
    input_encoding : str, optional
        入力ファイルのエンコーディング推定値
    output_encoding : str, optional
        出力ファイルのエンコーディング
    """
    if output_path is None:
        output_path = file_path
    
    # 複数のエンコーディングを試す
    encodings_to_try = ['utf-8', 'utf-8-sig', 'shift-jis', 'euc-jp', 'iso-2022-jp', 'cp932']
    
    # 指定されたエンコーディングを先に試す
    if input_encoding in encodings_to_try:
        encodings_to_try.remove(input_encoding)
    encodings_to_try.insert(0, input_encoding)
    
    content = None
    successful_encoding = None
    
    # 各エンコーディングを試す
    for encoding in encodings_to_try:
        try:
            with codecs.open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            successful_encoding = encoding
            print(f"ファイルを {encoding} として正常に読み込みました: {file_path}")
            break
        except UnicodeDecodeError:
            pass
        except Exception as e:
            print(f"ファイル {file_path} の処理中にエラー: {e}")
    
    if content is None:
        print(f"どのエンコーディングでもファイルを読み込めませんでした: {file_path}")
        return False
    
    # UTF-8エンコーディング宣言を追加（まだない場合）
    if not content.startswith('# -*- coding: utf-8 -*-'):
        if content.startswith('#!'):
            # シバン行がある場合はその後に追加
            lines = content.split('\n')
            lines.insert(1, '# -*- coding: utf-8 -*-')
            content = '\n'.join(lines)
        else:
            # シバン行がない場合は先頭に追加
            content = '# -*- coding: utf-8 -*-\n' + content
    
    # 修正したコンテンツを書き込む
    try:
        with codecs.open(output_path, 'w', encoding=output_encoding) as f:
            f.write(content)
        print(f"ファイルを {output_encoding} として保存しました: {output_path}")
        return True
    except Exception as e:
        print(f"ファイル保存中にエラーが発生しました: {e}")
        return False

def find_problematic_files(root_dir):
    """
    問題のあるファイルをすべて見つける
    
    Parameters:
    -----------
    root_dir : str
        検索を開始するルートディレクトリ
    """
    problematic_files = []
    
    # 問題のあることがわかっているディレクトリからPythonファイルを検索
    problem_dirs = [
        'sailing_data_processor/reporting',
        'sailing_data_processor/validation',
    ]
    
    # 全てのPythonファイルを収集
    for dir_path in problem_dirs:
        full_dir_path = os.path.join(root_dir, dir_path)
        if os.path.exists(full_dir_path):
            for py_file in glob.glob(f"{full_dir_path}/**/*.py", recursive=True):
                problematic_files.append(py_file)
    
    return problematic_files

def process_files(file_list):
    """
    ファイルリストを処理する
    
    Parameters:
    -----------
    file_list : list
        処理対象のファイルパスのリスト
    """
    success_count = 0
    total_count = len(file_list)
    
    for file_path in file_list:
        # バックアップを作成
        backup_path = file_path + '.bak'
        
        try:
            with open(file_path, 'rb') as src_file:
                content = src_file.read()
                with open(backup_path, 'wb') as dst_file:
                    dst_file.write(content)
        except Exception as e:
            print(f"バックアップ作成中にエラー ({file_path}): {e}")
            continue
        
        # エンコーディングを修正
        success = fix_file_encoding(file_path)
        
        if success:
            success_count += 1
        else:
            # 失敗した場合はバックアップから復元
            try:
                with open(backup_path, 'rb') as src_file:
                    content = src_file.read()
                    with open(file_path, 'wb') as dst_file:
                        dst_file.write(content)
                print(f"元のファイルを復元しました: {file_path}")
            except Exception as e:
                print(f"復元中にエラー ({file_path}): {e}")
    
    print(f"\n処理結果: {success_count}/{total_count} ファイルを修正しました")

if __name__ == "__main__":
    # プロジェクトルートディレクトリ
    root_dir = '/Users/koki_air/Documents/GitHub/sailing-strategy-analyzer'
    
    print("問題のあるファイルを検索中...")
    problematic_files = find_problematic_files(root_dir)
    
    print(f"{len(problematic_files)}個の問題ファイルが見つかりました。")
    
    if problematic_files:
        print("\n処理を開始します...")
        process_files(problematic_files)
