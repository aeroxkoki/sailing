#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
テスト用CSVファイルのタイムスタンプ形式を修正するスクリプト
テスト環境によってはタイムスタンプ形式が認識されないことがあるため、
ISO 8601形式(YYYY-MM-DDTHH:MM:SS)に統一します。
"""

import os
import sys
import logging
import csv
import io
from datetime import datetime

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# プロジェクトルート
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# 修正対象のCSVファイルのパス
TARGET_CSV_FILES = [
    os.path.join(project_root, 'test_data', 'sample.csv'),
    os.path.join(project_root, 'test_data', 'sample_gps.csv'),
    os.path.join(project_root, 'test_data', 'sample_different_columns.csv'),
]

def read_csv_file(file_path):
    """CSVファイルを読み込む"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
        return rows
    except Exception as e:
        logger.error(f"CSVファイルの読み込みに失敗しました: {file_path} - {e}")
        return None

def write_csv_file(file_path, rows):
    """CSVファイルを書き込む"""
    try:
        with open(file_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(rows)
        logger.info(f"CSVファイルを更新しました: {file_path}")
        return True
    except Exception as e:
        logger.error(f"CSVファイル書き込みエラー: {file_path} - {e}")
        return False

def fix_timestamps(rows):
    """タイムスタンプ形式を修正"""
    if not rows or len(rows) < 2:
        return rows
    
    # ヘッダー行
    header = rows[0]
    
    # タイムスタンプカラムのインデックスを探す
    timestamp_idx = -1
    for i, column_name in enumerate(header):
        if 'time' in column_name.lower() or 'date' in column_name.lower():
            timestamp_idx = i
            break
    
    if timestamp_idx == -1:
        logger.warning("タイムスタンプカラムが見つかりませんでした")
        return rows
    
    # タイムスタンプを標準形式に変換
    for i in range(1, len(rows)):
        row = rows[i]
        if len(row) > timestamp_idx:
            timestamp_str = row[timestamp_idx]
            try:
                # 空の値の場合はスキップ
                if not timestamp_str.strip():
                    continue
                
                # 様々な形式を試行
                formats = [
                    '%Y-%m-%d %H:%M:%S',
                    '%Y/%m/%d %H:%M:%S',
                    '%d-%m-%Y %H:%M:%S',
                    '%d/%m/%Y %H:%M:%S',
                    '%m-%d-%Y %H:%M:%S',
                    '%m/%d/%Y %H:%M:%S',
                    '%Y-%m-%dT%H:%M:%S',
                    '%Y/%m/%dT%H:%M:%S',
                ]
                
                dt = None
                for fmt in formats:
                    try:
                        dt = datetime.strptime(timestamp_str, fmt)
                        break
                    except ValueError:
                        continue
                
                if dt:
                    # ISO 8601形式に変換
                    row[timestamp_idx] = dt.strftime('%Y-%m-%dT%H:%M:%S')
            except Exception as e:
                logger.warning(f"タイムスタンプの変換に失敗しました: {timestamp_str} - {e}")
    
    return rows

def fix_csv_timestamps(file_path):
    """CSVファイルのタイムスタンプを修正"""
    logger.info(f"ファイルを処理中: {file_path}")
    
    # ファイルが存在するか確認
    if not os.path.exists(file_path):
        logger.warning(f"ファイルが存在しません: {file_path}")
        return False
    
    # CSVを読み込む
    rows = read_csv_file(file_path)
    if rows is None:
        return False
    
    # タイムスタンプを修正
    fixed_rows = fix_timestamps(rows)
    
    # バックアップを作成
    backup_path = file_path + '.bak'
    with open(backup_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    logger.info(f"バックアップを作成しました: {backup_path}")
    
    # 更新したCSVを書き込む
    return write_csv_file(file_path, fixed_rows)

def apply_csv_fixes():
    """すべてのCSVファイルのタイムスタンプ形式を修正"""
    success_count = 0
    fail_count = 0
    
    for file_path in TARGET_CSV_FILES:
        if fix_csv_timestamps(file_path):
            success_count += 1
        else:
            fail_count += 1
    
    logger.info(f"処理完了: {success_count}ファイル修正, {fail_count}ファイル失敗")
    return fail_count == 0

if __name__ == "__main__":
    if apply_csv_fixes():
        logger.info("CSVタイムスタンプ修正に成功しました")
        sys.exit(0)
    else:
        logger.error("CSVタイムスタンプ修正に失敗しました")
        sys.exit(1)
