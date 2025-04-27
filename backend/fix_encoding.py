#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Renderデプロイ時のfix_encoding.py
sailing_data_processorパッケージをPythonパスに追加し、エンコーディング問題を修正するスクリプト
"""

import os
import sys
import logging
import glob
import site

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# プロジェクトのルートディレクトリ（このスクリプトの親の親ディレクトリ）
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
logger.info(f"プロジェクトルート: {PROJECT_ROOT}")

# sailing_data_processorパッケージへのパスをPythonパスに追加
PACKAGE_PATH = os.path.join(PROJECT_ROOT)
logger.info(f"パッケージパス: {PACKAGE_PATH}")

# site-packagesディレクトリを取得
site_packages = site.getsitepackages()[0]
logger.info(f"Site-packages: {site_packages}")

# シンボリックリンクを作成
try:
    sailing_data_processor_path = os.path.join(PROJECT_ROOT, 'sailing_data_processor')
    link_path = os.path.join(site_packages, 'sailing_data_processor')
    
    # 既存のリンクやディレクトリがあれば削除
    if os.path.exists(link_path):
        logger.info(f"既存のリンクまたはディレクトリを削除: {link_path}")
        if os.path.islink(link_path):
            os.unlink(link_path)
        else:
            import shutil
            shutil.rmtree(link_path)
    
    # シンボリックリンクを作成
    os.symlink(sailing_data_processor_path, link_path, target_is_directory=True)
    logger.info(f"シンボリックリンクを作成: {sailing_data_processor_path} -> {link_path}")
except Exception as e:
    logger.error(f"シンボリックリンク作成エラー: {e}")
    # エラーが発生してもスクリプトは続行

# sailing_data_processorパッケージが正しくインポートできるか確認
try:
    sys.path.insert(0, PROJECT_ROOT)
    import sailing_data_processor
    logger.info(f"sailing_data_processorパッケージをインポートしました: {sailing_data_processor.__file__}")
except ImportError as e:
    logger.error(f"sailing_data_processorのインポートに失敗: {e}")
    sys.exit(1)

# 文字化け修正が必要なファイルのエンコーディングを修正
from patches.fix_file_encoding import apply_encoding_fixes
if apply_encoding_fixes():
    logger.info("エンコーディング修正が成功しました")
else:
    logger.warning("一部のエンコーディング修正に失敗しました")

# エラーなしで終了
sys.exit(0)
