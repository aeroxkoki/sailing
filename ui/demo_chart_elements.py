"""
セーリング分析システム用チャート要素のデモアプリケーション

基本チャート要素とセーリング特化型グラフを表示するデモアプリケーションです。
このアプリケーションは、開発段階でのテストと検証を目的としています。

以下のグラフタイプを確認できます：
1. 基本グラフ：折れ線グラフ、散布図、棒グラフ、円グラフ
2. セーリング特化型グラフ：風配図、ポーラーダイアグラム、タッキングアングル分析
"""

import os
import sys
import json
import random
import numpy as np
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

# モジュールのインポートパスを設定
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

# セーリング分析モジュールをインポート
# 基本グラフ要素
from sailing_data_processor.reporting.elements.visualizations.basic_charts import (
    LineChartElement, ScatterChartElement, BarChartElement, PieChartElement
)

# セーリング特化型グラフ要素
from sailing_data_processor.reporting.elements.visualizations.sailing_charts import (
    WindRoseElement, PolarDiagramElement, TackingAngleElement, CoursePerformanceElement
)

# レポートテンプレートモデル
from sailing_data_processor.reporting.templates.template_model import ElementType, ElementModel

# 新しく作成したコンポーネント
from ui.components.reporting.chart_properties_panel import render_chart_properties_panel
from ui.components.reporting.chart_preview import render_chart_preview, _generate_sample_data

# サンプルデータ生成関数はchart_preview.pyで定義したものを使用

def main():
    """メイン関数"""
    st.set_page_config(
        page_title="セーリング分析チャートデモ",
        page_icon="⛵",
        layout="wide"
    )
    
    st.title("セーリング分析チャートデモ")
    st.markdown("""
    このデモアプリケーションでは、セーリング分析に特化したチャート要素を編集・プレビューできます。
    左側のサイドバーでチャートタイプを選択し、各種パラメータを調整して結果を確認できます。
    """)
    
    # セッション状態の初期化
    if 'chart_type' not in st.session_state:
        st.session_state.chart_type = 'line'
    
    if 'properties' not in st.session_state:
        st.session_state.properties = {}
    
    # チャートタイプの選択
    with st.sidebar:
        st.header("チャートタイプ")
        
        # 大分類の選択
        chart_category = st.radio(
            "グラフカテゴリ",
            ["基本グラフ", "セーリング特化型グラフ"],
            key="chart_category"
        )
        
        # 選択された大分類に基づいてチャートタイプの選択肢を設定
        if chart_category == "基本グラフ":
            chart_types = {
                "折れ線グラフ": "line",
                "散布図": "scatter",
                "棒グラフ": "bar",
                "円グラフ": "pie"
            }
        else:  # セーリング特化型グラフ
            chart_types = {
                "風配図": "windrose",
                "ポーラーダイアグラム": "polar",
                "タッキングアングル分析": "tacking",
                "コースパフォーマンス": "course_performance"
            }
        
        # チャートタイプの選択
        selected_chart_name = st.selectbox(
            "チャートタイプ",
            list(chart_types.keys()),
            key="selected_chart_name"
        )
        
        # 選択されたチャートタイプのコードを取得
        chart_type = chart_types[selected_chart_name]
        
        # チャートタイプが変更された場合、デフォルトのプロパティを設定
        if chart_type != st.session_state.chart_type:
            st.session_state.chart_type = chart_type
            # デフォルトのプロパティを設定
            st.session_state.properties = {
                "chart_type": chart_type,
                "title": f"{selected_chart_name}のサンプル",
                "renderer": "plotly" if chart_type in ["polar", "windrose"] else "chartjs"
            }
    
    # プロパティの変更を処理する関数
    def handle_property_change(new_properties):
        st.session_state.properties.update(new_properties)
        st.rerun()
    
    # プロパティパネルを表示
    with st.sidebar:
        render_chart_properties_panel(
            chart_type=st.session_state.chart_type,
            on_property_change=handle_property_change,
            available_data_sources=[]
        )
    
    # メイン画面：チャートプレビュー
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # チャートプレビューの表示
        sample_data = _generate_sample_data(st.session_state.properties)
        render_chart_preview(
            st.session_state.properties,
            sample_data=sample_data,
            width="100%",
            height="600px"
        )
    
    with col2:
        # 現在のプロパティ情報
        st.subheader("現在のプロパティ")
        st.json(st.session_state.properties)
        
        # サンプルデータプレビュー
        with st.expander("サンプルデータプレビュー", expanded=False):
            st.json(sample_data[:5] if isinstance(sample_data, list) else sample_data)
    
    # 追加情報
    st.markdown("""
    ### 使用方法
    1. 左側のサイドバーからグラフカテゴリとチャートタイプを選択します
    2. プロパティパネルで各種設定を変更します
    3. メイン画面でプレビューが更新されます
    
    ### データについて
    このデモではサンプルデータを自動生成しています。実際の使用では、セッションデータからチャートを生成します。
    """)

if __name__ == "__main__":
    main()
