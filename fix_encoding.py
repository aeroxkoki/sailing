#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
strategy_detector_with_propagation.py ファイルのエンコーディングを修正する
"""

import os
import sys
import codecs

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
            print(f"ファイルを {encoding} として正常に読み込みました")
            break
        except UnicodeDecodeError:
            print(f"{encoding} でデコードできませんでした")
    
    if content is None:
        print("どのエンコーディングでもファイルを読み込めませんでした")
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

if __name__ == "__main__":
    # ファイルパスを設定
    target_file = '/Users/koki_air/Documents/GitHub/sailing-strategy-analyzer/sailing_data_processor/strategy/strategy_detector_with_propagation.py'
    backup_file = target_file + '.bak'
    
    # 元のファイルをバックアップ
    try:
        with open(target_file, 'rb') as src_file:
            content = src_file.read()
            with open(backup_file, 'wb') as dst_file:
                dst_file.write(content)
        print(f"バックアップファイルを作成しました: {backup_file}")
    except Exception as e:
        print(f"バックアップ作成中にエラーが発生しました: {e}")
        sys.exit(1)
    
    # エンコーディングを修正
    success = fix_file_encoding(target_file)
    
    if success:
        print("エンコーディングの修正が完了しました")
    else:
        print("エンコーディングの修正に失敗しました")
        # 失敗した場合はバックアップから復元
        try:
            with open(backup_file, 'rb') as src_file:
                content = src_file.read()
                with open(target_file, 'wb') as dst_file:
                    dst_file.write(content)
            print("元のファイルを復元しました")
        except Exception as e:
            print(f"復元中にエラーが発生しました: {e}")
