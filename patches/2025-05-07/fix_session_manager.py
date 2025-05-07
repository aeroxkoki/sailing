#\!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
セッションマネージャーの修正

このスクリプトは session_manager.py を修正します。
セッションマネージャーにテスト用のメソッドを追加します。
"""

import os
import sys
import shutil
from pathlib import Path

# プロジェクトルートを取得
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

# パッチファイルのパス
patch_file_path = os.path.join(project_root, 'patches', '2025-05-07', 'session_manager.py')
source_file_path = os.path.join(project_root, 'sailing_data_processor', 'project', 'session_manager.py')

def fix_session_manager():
    """セッションマネージャーの修正を行う"""
    print(f"セッションマネージャーの修正を開始: {source_file_path}")
    
    # バックアップの作成
    backup_file_path = source_file_path + ".bak"
    if not os.path.exists(backup_file_path):
        shutil.copy2(source_file_path, backup_file_path)
        print(f"セッションマネージャーのバックアップを作成: {backup_file_path}")
    
    # パッチファイルが存在すればコピー
    if os.path.exists(patch_file_path):
        shutil.copy2(patch_file_path, source_file_path)
        print(f"セッションマネージャーの修正が完了しました。")
        return True
    else:
        print(f"パッチファイルが見つかりませんでした: {patch_file_path}")
        return False

if __name__ == "__main__":
    fix_session_manager()
