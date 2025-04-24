#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
バイナリ形式でファイルを読み込み、エンコーディングの問題を修正するスクリプト
"""
import os
import sys
import traceback

def fix_file(filepath):
    """ファイルのエンコーディングを修正"""
    try:
        print(f"処理中: {filepath}")
        
        # バックアップを作成
        backup_path = f"{filepath}.bak2"
        with open(filepath, 'rb') as src, open(backup_path, 'wb') as dst:
            dst.write(src.read())
        
        # ファイルを読み込み
        with open(filepath, 'rb') as f:
            content = f.read()
        
        # NULL バイトの削除
        if b'\x00' in content:
            content = content.replace(b'\x00', b'')
            print(f"  - NULLバイトを削除しました")
        
        # エンコーディングを修正
        try:
            # UTF-8でデコード
            text = content.decode('utf-8')
        except UnicodeDecodeError:
            # 問題がある場合は置換モードでデコード
            text = content.decode('utf-8', errors='replace')
            print(f"  - 不正な文字を置換しました")
        
        # 修正したファイルを保存
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(text)
        
        print(f"ファイル修正完了: {filepath}")
        return True
    except Exception as e:
        print(f"エラー: {filepath} - {str(e)}")
        traceback.print_exc()
        return False

def main():
    """メインルーチン"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 処理するファイルのリスト
    problem_files = [
        os.path.join(script_dir, "sailing_data_processor/reporting/elements/map/course_elements.py"),
        os.path.join(script_dir, "sailing_data_processor/reporting/elements/map/layers/data_connector.py"),
        os.path.join(script_dir, "sailing_data_processor/reporting/elements/map/track_map.py"),
        os.path.join(script_dir, "sailing_data_processor/reporting/elements/timeline/__init__.py"),
        os.path.join(script_dir, "sailing_data_processor/reporting/elements/timeline/event_timeline.py"),
        os.path.join(script_dir, "sailing_data_processor/reporting/elements/timeline/parameter_timeline.py"),
        os.path.join(script_dir, "sailing_data_processor/reporting/elements/timeline/playback_control.py"),
        os.path.join(script_dir, "sailing_data_processor/reporting/elements/visualizations/basic_charts.py"),
        os.path.join(script_dir, "sailing_data_processor/reporting/elements/visualizations/sailing_charts.py"),
    ]
    
    # 全モジュールの初期化ファイル
    init_files = [
        os.path.join(script_dir, "sailing_data_processor/reporting/__init__.py"),
        os.path.join(script_dir, "sailing_data_processor/reporting/elements/__init__.py"),
        os.path.join(script_dir, "sailing_data_processor/reporting/elements/map/__init__.py"),
        os.path.join(script_dir, "sailing_data_processor/reporting/elements/map/layers/__init__.py"),
        os.path.join(script_dir, "sailing_data_processor/reporting/elements/visualizations/__init__.py"),
        os.path.join(script_dir, "sailing_data_processor/reporting/templates/__init__.py"),
    ]
    
    # すべてのファイルを処理リストに追加
    all_files = problem_files + init_files
    
    print(f"{len(all_files)}個のファイルを処理します...")
    success_count = 0
    
    for filepath in all_files:
        if os.path.exists(filepath):
            if fix_file(filepath):
                success_count += 1
        else:
            print(f"ファイルが見つかりません: {filepath}")
    
    print(f"\n処理結果:")
    print(f"- 対象ファイル数: {len(all_files)}")
    print(f"- 成功: {success_count}")
    print(f"- 失敗: {len(all_files) - success_count}")

if __name__ == "__main__":
    main()
