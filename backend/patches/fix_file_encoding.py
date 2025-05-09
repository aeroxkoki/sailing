#\!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
エンコーディング問題を修正するスクリプト
"""

import os
import sys
import logging
import glob
import chardet

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def detect_encoding(file_path):
    """ファイルのエンコーディングを検出"""
    with open(file_path, 'rb') as f:
        raw_data = f.read()
        result = chardet.detect(raw_data)
        return result['encoding'], raw_data

def fix_file_encoding(file_path, target_encoding='utf-8'):
    """ファイルのエンコーディングを修正"""
    try:
        detected_encoding, content = detect_encoding(file_path)
        
        # 変換が必要かどうか確認
        if detected_encoding and detected_encoding.lower() \!= target_encoding.lower():
            logger.info(f"エンコーディングを変換: {file_path} ({detected_encoding} -> {target_encoding})")
            
            # デコードとエンコード
            decoded_content = content.decode(detected_encoding, errors='replace')
            encoded_content = decoded_content.encode(target_encoding)
            
            # 新しいエンコーディングで保存
            with open(file_path, 'wb') as f:
                f.write(encoded_content)
            
            return True
        elif not detected_encoding:
            logger.warning(f"エンコーディングを検出できませんでした: {file_path}")
            return False
        else:
            logger.info(f"エンコーディング変換不要: {file_path} ({detected_encoding})")
            return True
    except Exception as e:
        logger.error(f"ファイル処理エラー: {file_path}, {str(e)}")
        return False

def apply_encoding_fixes():
    """プロジェクト内の文字化けファイルを修正"""
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
    logger.info(f"プロジェクトルート: {project_root}")
    
    # 修正が必要なファイルのパターン
    patterns = [
        os.path.join(project_root, 'backend/app/services/strategy_detection_service.py'),
        os.path.join(project_root, 'sailing_data_processor/strategy/*.py'),
        os.path.join(project_root, 'backend/app/**/*.py')
    ]
    
    fixed_count = 0
    error_count = 0
    
    # 各パターンに対して処理
    for pattern in patterns:
        for file_path in glob.glob(pattern, recursive=True):
            if os.path.isfile(file_path):
                if fix_file_encoding(file_path):
                    fixed_count += 1
                else:
                    error_count += 1
    
    logger.info(f"処理結果: {fixed_count}ファイル修正, {error_count}ファイルエラー")
    return error_count == 0

if __name__ == "__main__":
    if apply_encoding_fixes():
        logger.info("エンコーディング修正が成功しました")
        sys.exit(0)
    else:
        logger.warning("一部のエンコーディング修正に失敗しました")
        sys.exit(1)
