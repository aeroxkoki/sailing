#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
エンコーディング問題を修正するスクリプト
NULLバイトや不正なUnicode文字を含むファイルを修正します。
"""

import os
import sys
import glob
import re
import shutil
from pathlib import Path

def fix_file(filepath, backup=True):
    """
    ファイルの問題を修正します
    """
    try:
        # バックアップの作成
        if backup:
            backup_path = f"{filepath}.bak"
            shutil.copy2(filepath, backup_path)
            print(f"バックアップ作成: {backup_path}")
        
        # バイナリモードで読み込み
        with open(filepath, 'rb') as f:
            content = f.read()
        
        # NULL bytes を削除
        if b'\x00' in content:
            original_size = len(content)
            content = content.replace(b'\x00', b'')
            null_removed = original_size - len(content)
            print(f"  - NULLバイト削除: {null_removed}バイト")
        
        # 文字エンコーディング問題の修正
        try:
            # UTF-8でデコードを試みる
            text = content.decode('utf-8')
        except UnicodeDecodeError:
            # デコードできない場合は、エラーを無視してデコード
            text = content.decode('utf-8', errors='replace')
            print(f"  - 不正な文字を置換しました")
        
        # 修正したテキストを書き戻す
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(text)
        
        print(f"ファイル修正完了: {filepath}")
        return True
    
    except Exception as e:
        print(f"エラー - {filepath}: {str(e)}")
        return False

def main():
    """
    メイン関数
    """
    # 修正するファイルのリスト
    problem_files = [
        "ui/components/reporting/timeline/playback_panel.py",
        "ui/components/sharing/team_panel.py",
        "ui/components/session/__init__.py",
        "ui/components/session/session_detail.py",
        "ui/components/session/session_list.py",
        "tests/test_import_wizard.py",
        "backend/app/services/wind_estimation_service.py",
        "backend/app/services/strategy_detection_service.py",
        "sailing_data_processor/reporting/elements/map/wind_field.py",
        "sailing_data_processor/reporting/elements/map/course_elements.py",
        "sailing_data_processor/reporting/elements/map/track_map.py",
        "sailing_data_processor/reporting/elements/map/layer_manager.py",
        "sailing_data_processor/reporting/elements/timeline/__init__.py",
        "sailing_data_processor/reporting/interaction/view_synchronizer.py",
        "sailing_data_processor/reporting/interaction/__init__.py",
        "sailing_data_processor/session/__init__.py",
        "scripts/benchmark_wind_estimation.py",
    ]
    
    # sailing_data_processor/reporting/elements/ 以下の他のファイルもチェック
    additional_files = glob.glob("sailing_data_processor/reporting/elements/**/*.py", recursive=True)
    for file in additional_files:
        if file not in problem_files:
            problem_files.append(file)
    
    print(f"{len(problem_files)} ファイルを修正します...")
    
    success_count = 0
    for filepath in problem_files:
        if os.path.exists(filepath):
            print(f"修正中: {filepath}")
            if fix_file(filepath):
                success_count += 1
        else:
            print(f"ファイルが見つかりません: {filepath}")
    
    print("\n修正結果:")
    print(f"- 対象ファイル数: {len(problem_files)}")
    print(f"- 修正成功: {success_count}")
    print(f"- 修正失敗: {len(problem_files) - success_count}")

if __name__ == "__main__":
    main()
