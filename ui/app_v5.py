"""
ui.app_v5

セーリング戦略分析システムの最新バージョンのアプリケーション
"""

import streamlit as st
import pandas as pd
import numpy as np
import os
import sys
from streamlit_folium import folium_static
import folium

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# UI ページのインポート
from ui.pages.basic_project_management import render_page as render_project_management
from ui.pages.data_validation import render_page as render_data_validation

# ページ設定
st.set_page_config(
    page_title="セーリング戦略分析システム",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# アプリケーションのタイトル
st.title('セーリング戦略分析システム')

# ページ選択
page = st.sidebar.selectbox(
    'ナビゲーション',
    ['プロジェクト管理', 'マップビュー', 'データ管理', 'データ検証', 'パフォーマンス分析']
)

# 選択したページの表示
if page == 'プロジェクト管理':
    render_project_management()
elif page == 'データ検証':
    render_data_validation()
elif page == 'マップビュー':
    st.info("マップビュー機能は開発中です。")
    # マップの例を表示
    m = folium.Map(location=[35.45, 139.65], zoom_start=12)
    folium_static(m, width=800, height=600)
elif page == 'データ管理':
    st.info("データ管理機能は開発中です。")
elif page == 'パフォーマンス分析':
    st.info("パフォーマンス分析機能は開発中です。")

# フッター
st.sidebar.markdown('---')
st.sidebar.info('セーリング戦略分析システム v1.0')
