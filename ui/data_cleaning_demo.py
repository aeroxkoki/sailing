# -*- coding: utf-8 -*-
"""
ui.data_cleaning_demo

データクリーニングのデモページ
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any
import os
import sys

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ui.components.forms.import_wizard import ImportWizard
from ui.components.forms.data_cleaning import DataCleaning
from sailing_data_processor.data_model.container import GPSDataContainer

# ページ設定
st.set_page_config(
    page_title="データクリーニング - セーリング戦略分析システム",
    page_icon="🚢",
    layout="wide",
)

# タイトル
st.title("データクリーニングツール")
st.write("GPS位置データの検証と修正を行うためのツール")


def on_import_complete(container):
    """インポート完了時のコールバック"""
    st.session_state["imported_data"] = container
    st.session_state["show_cleaning"] = True
    st.session_state["view"] = "cleaning"


def on_data_cleaned(container):
    """データ修正完了時のコールバック"""
    st.session_state["cleaned_data"] = container
    st.session_state["show_analysis"] = True
    st.session_state["cleaning_complete"] = True


# セッション状態の初期化
if "imported_data" not in st.session_state:
    st.session_state["imported_data"] = None
if "cleaned_data" not in st.session_state:
    st.session_state["cleaned_data"] = None
if "show_cleaning" not in st.session_state:
    st.session_state["show_cleaning"] = False
if "show_analysis" not in st.session_state:
    st.session_state["show_analysis"] = False
if "cleaning_complete" not in st.session_state:
    st.session_state["cleaning_complete"] = False
if "view" not in st.session_state:
    st.session_state["view"] = "import"


# ナビゲーション
st.sidebar.header("ナビゲーション")
view_options = []

# 常に表示
view_options.append("データインポート")

# データがインポートされた場合
if st.session_state["show_cleaning"]:
    view_options.append("データクリーニング")

# クリーニングが完了した場合
if st.session_state["show_analysis"]:
    view_options.append("データ分析")

# 選択された表示を取得
selected_view = st.sidebar.radio("表示:", view_options)

# 選択された表示に応じて状態を変更
if selected_view == "データインポート":
    st.session_state["view"] = "import"
elif selected_view == "データクリーニング":
    st.session_state["view"] = "cleaning"
elif selected_view == "データ分析":
    st.session_state["view"] = "analysis"


# 表示の切り替え
if st.session_state["view"] == "import":
    # インポートウィザードの利用
    st.header("データインポート")
    st.write("GPSデータを読み込むには、以下のインポートウィザードを使用してください。")
    
    wizard = ImportWizard(
        key="main_import_wizard",
        on_import_complete=on_import_complete
    )
    wizard.render()

elif st.session_state["view"] == "cleaning":
    # データクリーニングの表示
    st.header("データクリーニング")
    st.write("インポートされたデータを検証し、問題を修正します。")
    
    # データクリーニングコンポーネントの利用
    cleaner = DataCleaning(
        key="main_data_cleaning",
        on_data_cleaned=on_data_cleaned
    )
    cleaner.render(st.session_state["imported_data"])

elif st.session_state["view"] == "analysis":
    # データ分析の表示
    st.header("データ分析")
    st.write("修正されたデータを分析します。")
    
    container = st.session_state["cleaned_data"]
    
    if container is not None:
        # データの概要
        st.subheader("データの概要")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**データポイント数:** {len(container.data):,}")
            time_range = container.get_time_range()
            st.write(f"**期間:** {time_range['duration_seconds'] / 60:.1f} 分")
        
        with col2:
            st.write(f"**開始時刻:** {time_range['start']}")
            st.write(f"**終了時刻:** {time_range['end']}")
        
        # データの可視化
        st.subheader("位置データ")
        map_data = container.data[["latitude", "longitude"]].copy()
        st.map(map_data)
        
        # データテーブル
        st.subheader("データテーブル")
        st.dataframe(container.data)
    else:
        st.warning("データが見つかりません。データクリーニングを完了してください。")


# サイドバー情報
st.sidebar.header("情報")
st.sidebar.write("""
このページでは、GPSデータの検証と修正を行うことができます。

ステップ:
1. データインポート - GPSデータファイルを読み込み
2. データクリーニング - データの検証と問題の修正
3. データ分析 - 修正後のデータを確認・分析

データクリーニングでできること:
- 欠損値の検出と修正
- 異常値の検出と修正
- 重複タイムスタンプの検出と修正
- 空間的・時間的整合性のチェックと修正
""")

# フッター
st.sidebar.markdown("---")
st.sidebar.write("セーリング戦略分析システム - データクリーニングデモ")
