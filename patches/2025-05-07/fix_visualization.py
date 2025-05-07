#\!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
マップ表示クラスの修正

このスクリプトは map_display.py を修正します。
create_map メソッドを修正し、zoom_start 属性をマップオブジェクトに設定します。
"""

import os
import sys
import re
from pathlib import Path

# プロジェクトルートを取得
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

# マップ表示クラスファイルのパス
map_file_path = os.path.join(project_root, 'visualization', 'map_display.py')

def fix_map_display():
    """マップ表示クラスの修正を行う"""
    print(f"マップ表示クラスファイルの修正を開始: {map_file_path}")
    
    # ファイルを読み込む
    with open(map_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # create_map メソッドの修正
    old_code = r'''        # 地図オブジェクトの作成
        # 引数の型を保証する（タプルでも受け取れるようにしつつ、内部ではリスト形式に統一）
        map_center = list(center) if isinstance(center, (list, tuple)) else center
        self.map_object = folium.Map(
            location=map_center,
            zoom_start=zoom_start,
            tiles=tile
        )
        
        # スケールバーの追加
        plugins.MousePosition().add_to(self.map_object)'''
    
    new_code = r'''        # 地図オブジェクトの作成
        # 引数の型を保証する（タプルでも受け取れるようにしつつ、内部ではリスト形式に統一）
        map_center = list(center) if isinstance(center, (list, tuple)) else center
        self.map_object = folium.Map(
            location=map_center,
            zoom_start=zoom_start,
            tiles=tile
        )
        
        # zoom_startプロパティを設定（テスト用）
        self.map_object.zoom_start = zoom_start
        
        # スケールバーの追加
        plugins.MousePosition().add_to(self.map_object)'''
    
    # コードの置換
    if old_code in content:
        updated_content = content.replace(old_code, new_code)
        
        # 結果を保存
        with open(map_file_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print(f"マップ表示クラスの修正が完了しました。")
        return True
    else:
        print(f"修正すべきコード部分が見つかりませんでした。")
        return False

if __name__ == "__main__":
    fix_map_display()
