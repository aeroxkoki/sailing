"""
セーリング戦略分析システム - インポートテスト

モジュールのインポートが正しく行われるかテストします。
"""

print("インポートテストを開始...")

try:
    import streamlit as st
    print("streamlit のインポート成功")
except ImportError as e:
    print(f"streamlit のインポート失敗: {e}")

try:
    import folium
    print("folium のインポート成功")
except ImportError as e:
    print(f"folium のインポート失敗: {e}")

try:
    import numpy as np
    print("numpy のインポート成功")
except ImportError as e:
    print(f"numpy のインポート失敗: {e}")

try:
    # まずファイルの存在を確認
    import os
    top_bar_path = os.path.join('ui', 'components', 'navigation', 'top_bar.py')
    print(f"top_bar ファイルの存在: {os.path.exists(top_bar_path)}")
    
    # インポート試行
    from ui.components.navigation.top_bar import apply_top_bar_style
    print("top_bar モジュールのインポート成功")
except ImportError as e:
    print(f"top_bar モジュールのインポート失敗: {e}")

try:
    from sailing_data_processor.utilities.wind_field_generator import generate_sample_wind_field
    print("wind_field_generator モジュールのインポート成功")
except ImportError as e:
    print(f"wind_field_generator モジュールのインポート失敗: {e}")

print("インポートテスト完了")
