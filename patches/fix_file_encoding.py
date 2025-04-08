#!/usr/bin/env python3
"""
文字化けしたファイルのエンコーディングを修正するためのスクリプト
"""

import os
import sys
import logging

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# プロジェクトルートとファイルパス
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
file_path = os.path.join(project_root, 'sailing_data_processor', 'strategy', 'strategy_detector_with_propagation.py')

def read_file_binary(path):
    """ファイルをバイナリモードで読み込む"""
    try:
        with open(path, 'rb') as file:
            return file.read()
    except Exception as e:
        logger.error(f"ファイルの読み込みに失敗しました: {e}")
        return None

def write_file_binary(path, content):
    """ファイルをバイナリモードで書き込む"""
    try:
        with open(path, 'wb') as file:
            file.write(content)
        logger.info(f"ファイルを更新しました: {path}")
        return True
    except Exception as e:
        logger.error(f"ファイル書き込みエラー: {e}")
        return False

def fix_encoding(content):
    """エンコーディングの問題を修正"""
    # nullバイトを削除
    content = content.replace(b'\x00', b'')
    
    # 特定の文字化けパターンを修正
    # ここには必要に応じて他の置換パターンを追加できます
    
    return content

def apply_encoding_fix():
    """エンコーディング修正を適用する"""
    logger.info(f"ファイルを処理中: {file_path}")
    
    # ファイルを読み込む
    content = read_file_binary(file_path)
    if content is None:
        return False
    
    # エンコーディングを修正
    fixed_content = fix_encoding(content)
    
    # 変更がなければ終了
    if fixed_content == content:
        logger.warning("変更はありませんでした")
        return False
    
    # 更新したファイルを書き込む
    return write_file_binary(file_path, fixed_content)

if __name__ == "__main__":
    if apply_encoding_fix():
        logger.info("エンコーディング修正に成功しました")
        sys.exit(0)
    else:
        logger.error("エンコーディング修正に失敗しました")
        sys.exit(1)
