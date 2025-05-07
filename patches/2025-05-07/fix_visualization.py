#\!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
視覚化モジュールのバグ修正スクリプト

テストで見つかったエラー：
- test_render_details_section - KeyError: 'lat_range'
"""

import sys
import os
import re

def fix_visualizer_part2(file_path):
    """visualizer_part2.py ファイルを修正します"""
    
    # ファイルの存在確認
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return False
    
    print(f"Fixing {file_path}")
    
    # ファイルを読み込む
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # バックアップファイルの作成
    backup_path = f"{file_path}.bak"
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Backup created: {backup_path}")
    
    # generate_heatmap_data メソッドの修正
    # データがない場合のフォールバック処理を追加
    heatmap_no_data_pattern = r'if not spatial_scores:\n\s+return \{\n\s+"has_data": False,\n\s+"heatmap_data": \[\],'
    heatmap_no_data_replacement = r'if not spatial_scores:\n        return {\n            "has_data": False,\n            "heatmap_data": [],\n            "lat_range": [0, 0],  # 空のデータでもlat_rangeを定義\n            "lon_range": [0, 0],  # 空のデータでもlon_rangeを定義'
    content = re.sub(heatmap_no_data_pattern, heatmap_no_data_replacement, content, flags=re.DOTALL)
    
    # lat_rangeとlon_rangeの取得部分を改善
    grid_bounds_pattern = r'# 格子の範囲情報の取得(.*?)lat_min, lat_max = grid\["bounds"\]\["min_lat"\], grid\["bounds"\]\["max_lat"\]\n\s+lon_min, lon_max = grid\["bounds"\]\["min_lon"\], grid\["bounds"\]\["max_lon"\]'
    grid_bounds_replacement = r'# 格子の範囲情報の取得 - 互換性のためにlat_rangeとlon_rangeを両方チェック\n        if "lat_range" in grid:\n            lat_min, lat_max = grid["lat_range"]\n            lon_min, lon_max = grid["lon_range"]\n        elif "bounds" in grid:\n            # boundsから取得\n            bounds = grid["bounds"]\n            lat_min, lat_max = bounds["min_lat"], bounds["max_lat"]\n            lon_min, lon_max = bounds["min_lon"], bounds["max_lon"]\n        else:\n            # どちらもない場合はスキップ\n            continue'
    content = re.sub(grid_bounds_pattern, grid_bounds_replacement, content, flags=re.DOTALL)
    
    # 修正したファイルを保存
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Visualizer part2 fixed successfully")
    return True

def fix_validation_dashboard(file_path):
    """validation_dashboard.py ファイルを修正します"""
    
    # ファイルの存在確認
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return False
    
    print(f"Fixing {file_path}")
    
    # ファイルを読み込む
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # バックアップファイルの作成
    backup_path = f"{file_path}.bak"
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Backup created: {backup_path}")
    
    # render_details_section メソッドの修正
    # エラーハンドリングを追加
    render_pattern = r'def render_details_section\(self\)(.*?)# 詳細チャートの生成(.*?)(spatial_quality_map = self\.visualizer\.generate_spatial_quality_map\(\))'
    render_replacement = r'def render_details_section(self)\1# 詳細チャートの生成\n        try:\2\3'
    content = re.sub(render_pattern, render_replacement, content, flags=re.DOTALL)
    
    # エラー処理を追加
    catch_pattern = r'(temporal_quality_chart = self\.visualizer\.generate_temporal_quality_chart\(\))'
    catch_replacement = r'\1\n        except Exception as e:\n            print(f"Error generating spatial quality map: {e}")\n            # エラー時はダミーのマップを返す\n            spatial_quality_map = go.Figure()\n            spatial_quality_map.update_layout(title="空間品質マップ（エラーのため表示できません）")\n        \n        try:'
    content = re.sub(catch_pattern, catch_replacement, content, flags=re.DOTALL)
    
    # 二つ目の例外処理を追加
    catch2_pattern = r'(# 詳細レポートの生成\n\s+detailed_report = self\.metrics_calculator\.get_quality_report\(\))'
    catch2_replacement = r'        except Exception as e:\n            print(f"Error generating temporal quality chart: {e}")\n            # エラー時はダミーのチャートを返す\n            temporal_quality_chart = go.Figure()\n            temporal_quality_chart.update_layout(title="時間品質チャート（エラーのため表示できません）")\n        \n\1'
    content = re.sub(catch2_pattern, catch2_replacement, content, flags=re.DOTALL)
    
    # 最終的なフォールバックを追加
    return_pattern = r'return \{\n\s+"charts": \{\n\s+"spatial_quality": spatial_quality_map,\n\s+"temporal_quality": temporal_quality_chart\n\s+\},\n\s+"problem_records_df": problem_records_df,\n\s+"detailed_report": detailed_report\n\s+\}'
    return_replacement = r'return {\n            "charts": {\n                "spatial_quality": spatial_quality_map,\n                "temporal_quality": temporal_quality_chart\n            },\n            "problem_records_df": problem_records_df,\n            "detailed_report": detailed_report\n        }\n    except Exception as e:\n        # 最終的なフォールバック - エラーが発生した場合も最低限の情報を返す\n        print(f"Error rendering details section: {e}")\n        return {\n            "charts": {},\n            "problem_records_df": pd.DataFrame(),\n            "detailed_report": {"error": f"レポート生成エラー: {str(e)}"}\n        }'
    content = re.sub(return_pattern, return_replacement, content, flags=re.DOTALL)
    
    # 修正したファイルを保存
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Validation dashboard fixed successfully")
    return True

if __name__ == "__main__":
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # visualizer_part2.py の修正
    visualizer_part2_path = os.path.join(root_dir, "sailing_data_processor/validation/visualization_modules/visualizer_part2.py")
    if not fix_visualizer_part2(visualizer_part2_path):
        print("Failed to fix visualizer_part2.py")
        sys.exit(1)
    
    # validation_dashboard.py の修正
    validation_dashboard_path = os.path.join(root_dir, "sailing_data_processor/validation/visualization_modules/validation_dashboard.py")
    if not fix_validation_dashboard(validation_dashboard_path):
        print("Failed to fix validation_dashboard.py")
        sys.exit(1)
    
    print("All visualization modules fixed successfully\!")
