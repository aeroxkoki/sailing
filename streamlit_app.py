"""
セーリング戦略分析システム - Streamlit Cloudエントリーポイント (シンプル版)

このファイルはStreamlit Cloudでのデプロイ用の簡易バージョンです。
初期デプロイ成功のためにシンプルな実装を提供します。
"""

import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import folium
from streamlit_folium import folium_static
import datetime

# ページ設定
st.set_page_config(
    page_title="セーリング戦略分析システム",
    page_icon="🌊",
    layout="wide",
)

# ヘッダー
st.title("セーリング戦略分析システム - 風向風速可視化デモ")
st.markdown("---")

# 基本レイアウト
col1, col2 = st.columns([7, 3])

with col1:
    st.subheader("マップビュー")
    
    # シンプルなマップの表示
    center = [35.45, 139.65]  # 東京湾付近
    m = folium.Map(
        location=center,
        zoom_start=12,
        tiles='CartoDB positron'
    )
    
    # シンプルな軌跡データ
    points = []
    radius = 0.02
    for i in range(0, 360, 10):
        angle = np.radians(i)
        lat = center[0] + radius * np.cos(angle)
        lon = center[1] + radius * np.sin(angle)
        points.append([lat, lon])
    
    # 軌跡描画
    folium.PolyLine(
        points,
        color='#FF5722',
        weight=3,
        opacity=0.7
    ).add_to(m)
    
    # マップ表示
    folium_static(m, width=800, height=500)
    
    # シンプルなタイムライン
    st.subheader("タイムライン")
    st.slider("時間", 0, 100, 50)

with col2:
    st.subheader("データパネル")
    
    # サンプルデータ
    df = pd.DataFrame({
        '時間': [f"12:{i:02d}:00" for i in range(0, 30, 5)],
        '速度 (kt)': [5.2, 6.4, 7.1, 6.8, 5.9, 6.2],
        '方位角 (°)': [128, 132, 127, 135, 140, 138]
    })
    
    st.dataframe(df)
    
    # シンプルなチャート
    st.subheader("速度データ")
    
    fig, ax = plt.subplots()
    ax.plot(range(len(df)), df['速度 (kt)'], marker='o')
    ax.set_ylabel('速度 (kt)')
    ax.set_xticks(range(len(df)))
    ax.set_xticklabels(df['時間'], rotation=45)
    ax.grid(True, alpha=0.3)
    
    # グラフ表示
    st.pyplot(fig)
    
    st.subheader("情報")
    st.info("""
    このデモはセーリング戦略分析システムの風向風速可視化の機能を示すシンプル版です。
    完全版は近日公開予定です。
    """)

# フッター
st.markdown("---")
st.caption("セーリング戦略分析システム © 2024")
