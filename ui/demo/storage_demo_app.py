# -*- coding: utf-8 -*-
"""
ストレージソリューションデモアプリケーション

セーリング戦略分析システム向けのストレージソリューション機能確認用Streamlitアプリケーション。
このファイルは `streamlit run storage_demo_app.py` コマンドで直接実行できます。
"""

import streamlit as st
from sailing_data_processor.storage.storage_demo import StorageDemoApp

# ページ設定
st.set_page_config(
    page_title="セーリング戦略分析システム - ストレージデモ",
    page_icon="⛵",
    layout="wide",
    initial_sidebar_state="expanded",
)

# カスタムCSSの追加
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
    }
    .stButton>button {
        width: 100%;
    }
    div[data-testid="stSidebarUserContent"] {
        padding-top: 1rem;
    }
    .css-1544g2n.e1fqkh3o4 {
        padding-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# デモアプリケーションの実行
demo_app = StorageDemoApp()
demo_app.run()
