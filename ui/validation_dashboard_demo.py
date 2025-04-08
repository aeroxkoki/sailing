"""
Streamlit検証ダッシュボードデモ

このスクリプトは、検証ダッシュボードとデータクリーニングUIの
デモを提供するStreamlitアプリケーションです。

使用方法:
    streamlit run ui/validation_dashboard_demo.py

注意:
    このプログラムはデモ用で、実際の運用環境では専用のUIを使用してください。
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import os
import sys

# 親ディレクトリをインポートパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sailing_data_processor.data_model.container import GPSDataContainer
from sailing_data_processor.validation.data_validator import DataValidator
from sailing_data_processor.validation.quality_metrics import QualityMetricsCalculator
from sailing_data_processor.validation.visualization import ValidationVisualizer
from ui.components.visualizations.validation_dashboard_base import ValidationDashboardBase
from ui.components.forms.data_cleaning_basic import DataCleaningBasic

# アプリケーションのタイトル
st.set_page_config(
    page_title="検証ダッシュボードデモ",
    page_icon="🧭",
    layout="wide",
)

@st.cache_data
def create_sample_data():
    """サンプルデータの作成 (キャッシュ対応)"""
    # 正常なデータをベースに作成
    data = pd.DataFrame({
        'timestamp': [datetime(2025, 1, 1, 12, 0, i) for i in range(30)],
        'latitude': [35.0 + i * 0.001 for i in range(30)],
        'longitude': [135.0 + i * 0.001 for i in range(30)],
        'speed': [5.0 + i * 0.2 for i in range(30)],
        'course': [45.0 + i * 1.0 for i in range(30)],
        'boat_id': ['demo_boat'] * 30
    })
    
    # いくつかの問題を作成
    # 欠損値
    data.loc[2, 'latitude'] = None
    data.loc[5, 'speed'] = None
    data.loc[10, 'course'] = None
    
    # 範囲外の値
    data.loc[8, 'speed'] = 100.0  # 異常な速度
    data.loc[12, 'course'] = 500.0  # 異常な角度
    
    # 重複タイムスタンプ
    data.loc[15, 'timestamp'] = data.loc[14, 'timestamp']
    data.loc[16, 'timestamp'] = data.loc[14, 'timestamp']
    
    # 時間逆行
    data.loc[20, 'timestamp'] = data.loc[19, 'timestamp'] - timedelta(seconds=30)
    
    # 空間的異常（急激な位置の変化）
    data.loc[25, 'latitude'] = 36.0
    
    # GPSDataContainerの作成
    container = GPSDataContainer()
    container.data = data
    container.metadata = {
        'boat_id': 'demo_boat',
        'data_source': 'streamlit_demo',
        'created_at': datetime.now().isoformat()
    }
    
    return container

def main():
    st.title("セーリングデータ検証ダッシュボード")
    
    # サイドバーにアプリの説明と操作方法を表示
    with st.sidebar:
        st.header("アプリケーション情報")
        st.write("""
        このデモアプリは、セーリングデータの検証・クリーニング機能を示しています。
        
        以下の機能を試すことができます：
        - データ品質メトリクスの計算と表示
        - 問題の可視化と分析
        - インタラクティブなデータクリーニング
        """)
        
        st.header("デモモード")
        demo_modes = [
            "自動検証ダッシュボード",
            "データクリーニングUI",
            "両方を表示"
        ]
        selected_mode = st.selectbox("表示するデモを選択", demo_modes)
        
        st.header("サンプルデータ")
        if st.button("新しいサンプルデータを生成"):
            # キャッシュを無効化して新しいデータを生成
            st.cache_data.clear()
            st.rerun()
    
    # サンプルデータの作成とバリデーション
    container = create_sample_data()
    validator = DataValidator()
    validator.validate(container)
    
    # 選択されたモードに応じてUIを表示
    if selected_mode == "自動検証ダッシュボード" or selected_mode == "両方を表示":
        st.header("検証ダッシュボード")
        st.write("データの品質メトリクスと問題の可視化")
        
        # 検証ダッシュボードを表示
        dashboard = ValidationDashboardBase(container, validator)
        dashboard.render()
    
    if selected_mode == "データクリーニングUI" or selected_mode == "両方を表示":
        st.header("データクリーニングUI")
        st.write("検出された問題の修正インターフェース")
        
        # データクリーニングUIを表示
        cleaning_ui = DataCleaningBasic(container, validator)
        cleaning_ui.render()
        
        # 修正後のコンテナを取得（修正が適用された場合）
        updated_container = cleaning_ui.get_container()
        if updated_container != container:
            st.success("データが修正されました！品質スコアが向上しています。")

if __name__ == "__main__":
    main()
