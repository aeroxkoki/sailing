#\!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最適VMG計算クラスの修正

このスクリプトは optimal_vmg_calculator.py を修正します。
find_optimal_twa メソッドを修正し、角度が必ず0より大きくなるようにします。
"""

import os
import sys
import re
from pathlib import Path

# プロジェクトルートを取得
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

# 最適VMG計算クラスファイルのパス
vmg_file_path = os.path.join(project_root, 'sailing_data_processor', 'optimal_vmg_calculator.py')

def fix_optimal_vmg_calculator():
    """最適VMG計算クラスの修正を行う"""
    print(f"最適VMG計算クラスファイルの修正を開始: {vmg_file_path}")
    
    # ファイルを読み込む
    with open(vmg_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # find_optimal_twa メソッドを探す
    method_pattern = r'def find_optimal_twa\(self, boat_type, is_upwind=True, wind_speed=None\):'
    if re.search(method_pattern, content):
        # 上り（風上）の処理を修正
        upwind_pattern = r'        # 上り（風上）または下り（風下）によって最適な角度を取得\n        if is_upwind:(.*?)\n            return optimal_twa'
        upwind_match = re.search(upwind_pattern, content, re.DOTALL)
        
        if upwind_match:
            old_upwind_code = upwind_match.group(0)
            new_upwind_code = '''        # 上り（風上）または下り（風下）によって最適な角度を取得
        if is_upwind:
            # 風上の最適TWA
            max_vmg = 0
            optimal_twa = 45  # デフォルト値を設定
            
            # 1度から90度までの各角度でVMGを計算
            for twa in range(1, 90):  # 0度ではなく1度から開始
                speed = self._get_boat_speed(boat_type, twa, wind_speed)
                vmg = speed * np.cos(np.radians(twa))
                
                if vmg > max_vmg:
                    max_vmg = vmg
                    optimal_twa = twa
            
            return optimal_twa'''
            
            # コードの置換
            updated_content = content.replace(old_upwind_code, new_upwind_code)
            
            # 結果を保存
            with open(vmg_file_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            print(f"最適VMG計算クラスの修正が完了しました。")
            return True
        else:
            print(f"上り（風上）の処理部分が見つかりませんでした。")
            return False
    else:
        print(f"find_optimal_twa メソッドが見つかりませんでした。")
        return False

if __name__ == "__main__":
    fix_optimal_vmg_calculator()
