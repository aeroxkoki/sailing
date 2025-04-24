#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
strategy_detector_with_propagation.pyの_normalize_to_timestampメソッドを修正するパッチスクリプト
"""

import os
import re
import sys
import logging

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# プロジェクトルートとファイルパス
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
file_path = os.path.join(project_root, 'sailing_data_processor', 'strategy', 'strategy_detector_with_propagation.py')
patch_path = os.path.join(project_root, 'patches', 'normalize_to_timestamp_fixed.py')

def read_file(path):
    """ファイルを読み込む"""
    try:
        with open(path, 'r', encoding='utf-8') as file:
            return file.read()
    except UnicodeDecodeError:
        # UTF-8でデコードできない場合はバイナリモードで読み込む
        with open(path, 'rb') as file:
            content = file.read()
            # ここでは修正できないのでそのまま返す
            return content.decode('utf-8', errors='ignore')

def replace_normalize_to_timestamp(content):
    """_normalize_to_timestamp メソッドを修正したバージョンに置き換える"""
    # 修正済みメソッドを読み込む
    with open(patch_path, 'r', encoding='utf-8') as patch_file:
        patch_content = patch_file.read()
        # 関数定義部分だけを抽出
        match = re.search(r'def _normalize_to_timestamp.*?(?=def|\Z)', patch_content, re.DOTALL)
        if match:
            new_method = match.group(0)
        else:
            logger.error("パッチファイルから_normalize_to_timestampメソッドを抽出できませんでした")
            return content

    # 元のファイル内の_normalize_to_timestampメソッドを特定する
    pattern = r'def _normalize_to_timestamp.*?(?=def|\Z)'
    match = re.search(pattern, content, re.DOTALL)
    
    if match:
        # 修正を適用
        logger.info("_normalize_to_timestampメソッドを修正済みバージョンに置き換えます")
        return content.replace(match.group(0), new_method)
    else:
        logger.error("元のファイル内で_normalize_to_timestampメソッドが見つかりませんでした")
        return content

def write_file(path, content):
    """ファイルに書き込む"""
    try:
        with open(path, 'w', encoding='utf-8') as file:
            file.write(content)
        logger.info(f"ファイルを更新しました: {path}")
        return True
    except Exception as e:
        logger.error(f"ファイル書き込みエラー: {e}")
        return False

def apply_patch():
    """パッチを適用する"""
    logger.info(f"ファイルを処理中: {file_path}")
    
    # ファイルを読み込む
    content = read_file(file_path)
    if not content:
        logger.error("ファイルの読み込みに失敗しました")
        return False
    
    # _normalize_to_timestampメソッドを置き換える
    patched_content = replace_normalize_to_timestamp(content)
    
    # 変更がなければ終了
    if patched_content == content:
        logger.warning("変更はありませんでした")
        return False
    
    # 更新したファイルを書き込む
    return write_file(file_path, patched_content)

if __name__ == "__main__":
    if apply_patch():
        logger.info("パッチの適用に成功しました")
        sys.exit(0)
    else:
        logger.error("パッチの適用に失敗しました")
        sys.exit(1)
