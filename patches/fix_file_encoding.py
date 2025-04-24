#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文字化けしたファイルのエンコーディングを修正するためのスクリプト
"""

import os
import sys
import logging
import glob

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# プロジェクトルート
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# 修正が必要なファイルパスリスト
PROBLEMATIC_FILES = [
    # テストログから特定された問題ファイル
    os.path.join(project_root, 'sailing_data_processor', 'reporting', 'elements', 'map', 'course_elements.py'),
    os.path.join(project_root, 'sailing_data_processor', 'reporting', 'elements', 'map', 'layer_manager.py'),
    os.path.join(project_root, 'sailing_data_processor', 'reporting', 'elements', 'map', 'layers', 'data_connector.py'),
    os.path.join(project_root, 'sailing_data_processor', 'reporting', 'elements', 'timeline', 'event_timeline.py'),
    os.path.join(project_root, 'sailing_data_processor', 'reporting', 'elements', 'timeline', 'parameter_timeline.py'),
    os.path.join(project_root, 'sailing_data_processor', 'reporting', 'elements', 'timeline', 'playback_control.py'),
    os.path.join(project_root, 'sailing_data_processor', 'reporting', 'elements', 'visualizations', 'basic_charts.py'),
    os.path.join(project_root, 'sailing_data_processor', 'reporting', 'elements', 'visualizations', 'sailing_charts.py'),
    os.path.join(project_root, 'sailing_data_processor', 'validation', 'visualization_improvements.py'),
    os.path.join(project_root, 'sailing_data_processor', 'strategy', 'strategy_detector_with_propagation.py'),
]

def read_file_binary(path):
    """ファイルをバイナリモードで読み込む"""
    try:
        with open(path, 'rb') as file:
            return file.read()
    except Exception as e:
        logger.error(f"ファイルの読み込みに失敗しました: {path} - {e}")
        return None

def write_file_binary(path, content):
    """ファイルをバイナリモードで書き込む"""
    try:
        with open(path, 'wb') as file:
            file.write(content)
        logger.info(f"ファイルを更新しました: {path}")
        return True
    except Exception as e:
        logger.error(f"ファイル書き込みエラー: {path} - {e}")
        return False

def fix_encoding(content):
    """エンコーディングの問題を修正"""
    # nullバイトを削除
    content = content.replace(b'\x00', b'')
    
    # 特定の文字化けパターンを修正
    # ここには必要に応じて他の置換パターンを追加できます
    
    return content

def fix_file(file_path):
    """単一ファイルのエンコーディングを修正"""
    logger.info(f"ファイルを処理中: {file_path}")
    
    # ファイルが存在するか確認
    if not os.path.exists(file_path):
        logger.warning(f"ファイルが存在しません: {file_path}")
        return False
    
    # ファイルを読み込む
    content = read_file_binary(file_path)
    if content is None:
        return False
    
    # エンコーディングを修正
    fixed_content = fix_encoding(content)
    
    # 変更がなければ終了
    if fixed_content == content:
        logger.info(f"変更はありませんでした: {file_path}")
        return True  # 変更なしでも成功とみなす
    
    # バックアップを作成
    backup_path = file_path + '.bak'
    write_file_binary(backup_path, content)
    
    # 更新したファイルを書き込む
    return write_file_binary(file_path, fixed_content)

def apply_encoding_fixes():
    """すべての問題ファイルのエンコーディングを修正"""
    success_count = 0
    fail_count = 0
    
    for file_path in PROBLEMATIC_FILES:
        if fix_file(file_path):
            success_count += 1
        else:
            fail_count += 1
    
    # ディレクトリを再帰的に探索して追加のnullバイトを含むファイルを検出して修正
    python_files = glob.glob(os.path.join(project_root, 'sailing_data_processor', '**', '*.py'), recursive=True)
    
    for file_path in python_files:
        if file_path in PROBLEMATIC_FILES:
            continue  # 既に処理済み
            
        content = read_file_binary(file_path)
        if content and b'\x00' in content:
            logger.warning(f"追加のnullバイトを含むファイルを検出: {file_path}")
            if fix_file(file_path):
                success_count += 1
            else:
                fail_count += 1
    
    logger.info(f"処理完了: {success_count}ファイル修正, {fail_count}ファイル失敗")
    return fail_count == 0

if __name__ == "__main__":
    if apply_encoding_fixes():
        logger.info("エンコーディング修正に成功しました")
        sys.exit(0)
    else:
        logger.error("エンコーディング修正に失敗しました")
        sys.exit(1)
