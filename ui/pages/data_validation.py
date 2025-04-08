"""
ui.pages.data_validation

データ検証と修正のページコンポーネント
"""

import streamlit as st
from typing import Dict, List, Any, Optional, Callable, Union
import pandas as pd
import numpy as np
from datetime import datetime

from sailing_data_processor.data_model.container import GPSDataContainer
from sailing_data_processor.validation.data_validator import DataValidator
from sailing_data_processor.validation.visualization import ValidationVisualizer
from sailing_data_processor.validation.quality_metrics import QualityMetricsCalculator
from sailing_data_processor.validation.correction import InteractiveCorrectionInterface

from ui.components.forms.data_cleaning_basic import DataCleaningBasic
from ui.components.visualizations.validation_dashboard_base import ValidationDashboardBase


def data_validation_page():
    """
    データ検証と修正ページを表示
    """
    st.title("データ検証と修正")
    
    # セッション状態の初期化
    if "data_container" not in st.session_state:
        st.session_state.data_container = None
    
    if "validator" not in st.session_state:
        st.session_state.validator = DataValidator()
    
    # データがセッションにあるか確認
    container = st.session_state.get("data_container")
    
    if container is None:
        st.info("データが読み込まれていません。まずデータをインポートしてください。")
        return
    
    # タブの設定
    tab1, tab2 = st.tabs(["基本検証・修正", "詳細検証ダッシュボード"])
    
    with tab1:
        # 基本的なデータクリーニングコンポーネントを表示
        cleaner = DataCleaningBasic(key="validation_basic")
        cleaner.render(container)
    
    with tab2:
        # 詳細なデータ検証ダッシュボードを表示
        validator = st.session_state.validator
        
        def on_correction(data):
            # 修正が適用されたときのコールバック
            if "container" in data:
                st.session_state.data_container = data["container"]
                st.success("データが正常に修正されました。")
                st.experimental_rerun()
        
        dashboard = ValidationDashboardBase(
            key="validation_dashboard",
            container=container,
            validator=validator,
            on_correction=on_correction
        )
        
        dashboard.render()


def load_sample_data() -> GPSDataContainer:
    """
    テスト用のサンプルデータを生成
    
    Returns
    -------
    GPSDataContainer
        サンプルデータコンテナ
    """
    # タイムスタンプを生成
    base_time = datetime.now()
    timestamps = [base_time + pd.Timedelta(seconds=i) for i in range(100)]
    
    # 緯度経度を生成
    latitudes = np.linspace(35.6, 35.7, 100) + np.random.normal(0, 0.001, 100)
    longitudes = np.linspace(139.7, 139.8, 100) + np.random.normal(0, 0.001, 100)
    
    # 速度と方向を生成
    speeds = np.abs(np.sin(np.linspace(0, 10, 100)) * 10)
    directions = np.linspace(0, 360, 100) % 360
    
    # いくつかの異常値を追加
    latitudes[20] = np.nan  # 欠損値
    longitudes[30] = np.nan  # 欠損値
    latitudes[40] = 35.9  # 範囲外の値
    speeds[50] = 100  # 異常な速度
    timestamps[60] = timestamps[59]  # 重複タイムスタンプ
    timestamps[70] = timestamps[69] - pd.Timedelta(seconds=1)  # 時間逆行
    
    # データフレームを作成
    data = pd.DataFrame({
        "timestamp": timestamps,
        "latitude": latitudes,
        "longitude": longitudes,
        "speed": speeds,
        "direction": directions,
        "distance": np.cumsum(np.random.uniform(0, 10, 100))
    })
    
    # GPSデータコンテナを作成
    container = GPSDataContainer(data, {
        "name": "サンプルデータ",
        "description": "テスト用のサンプルデータセット",
        "created_at": datetime.now().isoformat()
    })
    
    return container


# 単体テスト用
if __name__ == "__main__":
    # サンプルデータをロード
    container = load_sample_data()
    
    # セッション状態にデータを設定
    st.session_state.data_container = container
    
    # 検証器を初期化
    validator = DataValidator()
    validator.validate(container)
    st.session_state.validator = validator
    
    # ページを表示
    data_validation_page()
