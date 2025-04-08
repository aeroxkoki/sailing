#!/usr/bin/env python3
"""
ファイルのエンコーディングを修正するスクリプト
Shift_JISなどで保存されたファイルをUTF-8に変換します。
"""

import sys
import os

def convert_file_encoding(input_file, output_file, input_encoding='shift_jis', output_encoding='utf-8'):
    """
    ファイルのエンコーディングを変換する
    
    Parameters:
    -----------
    input_file : str
        入力ファイルのパス
    output_file : str
        出力ファイルのパス
    input_encoding : str
        入力ファイルのエンコーディング
    output_encoding : str
        出力ファイルのエンコーディング
    """
    try:
        # 入力ファイルを読み込み
        with open(input_file, 'rb') as f:
            content = f.read()
        
        # バイナリデータからnullバイトを除去
        content = content.replace(b'\x00', b'')
        
        # 入力エンコーディングでデコード
        try:
            text = content.decode(input_encoding, errors='replace')
        except UnicodeDecodeError:
            # 第一のエンコーディングで失敗した場合、代替を試す
            fallback_encodings = ['euc-jp', 'cp932', 'iso-2022-jp', 'utf-16', 'latin1']
            for enc in fallback_encodings:
                try:
                    text = content.decode(enc, errors='replace')
                    print(f"成功: {enc}エンコーディングでデコードできました")
                    break
                except UnicodeDecodeError:
                    continue
            else:
                # すべてのエンコーディングが失敗した場合
                text = content.decode('latin1', errors='replace')
                print("警告: 最終手段としてlatin1でデコードしました")
        
        # 出力エンコーディングでエンコード
        with open(output_file, 'w', encoding=output_encoding) as f:
            f.write(text)
        
        print(f"変換成功: {input_file} → {output_file}")
        return True
    
    except Exception as e:
        print(f"エラー: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用法: python fix_encoding.py <input_file> [output_file] [input_encoding] [output_encoding]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    # 出力ファイル名が指定されていない場合は入力ファイル名に_utf8を追加
    output_file = sys.argv[2] if len(sys.argv) > 2 else input_file + ".utf8"
    
    # エンコーディングが指定されていない場合はデフォルト値を使用
    input_encoding = sys.argv[3] if len(sys.argv) > 3 else 'shift_jis'
    output_encoding = sys.argv[4] if len(sys.argv) > 4 else 'utf-8'
    
    success = convert_file_encoding(input_file, output_file, input_encoding, output_encoding)
    sys.exit(0 if success else 1)
