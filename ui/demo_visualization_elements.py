# -*- coding: utf-8 -*-
"""
ui.demo_visualization_elements

可視化要素のデモアプリケーションです。
このモジュールは、セーリング分析用の可視化要素を実演します。
"""

import streamlit as st
import os
import sys
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
from pathlib import Path

# プロジェクトのルートディレクトリをPYTHONPATHに追加
root_dir = Path(__file__).parent.parent.absolute()
sys.path.append(str(root_dir))

# 可視化要素モジュールのインポート
from sailing_data_processor.reporting.elements.visualizations.base_chart import BaseChartElement
from sailing_data_processor.reporting.elements.visualizations.sailing_charts import (
    WindRoseElement, CoursePerformanceElement, TackingAngleElement, StrategyPointMapElement
)
from sailing_data_processor.reporting.elements.visualizations.statistical_charts import (
    TimeSeriesElement, BoxPlotElement, HeatMapElement, CorrelationElement
)
from sailing_data_processor.reporting.elements.visualizations.map_elements import (
    TrackMapElement, HeatMapLayerElement, StrategyPointLayerElement, WindFieldElement
)
from sailing_data_processor.reporting.elements.visualizations.timeline_elements import (
    EventTimelineElement, ParameterTimelineElement, SegmentComparisonElement, DataViewerElement
)

# UIコンポーネント
from ui.components.reporting.visualization_editor import VisualizationEditor
from ui.components.reporting.chart_options_panel import ChartOptionsPanel
from ui.components.reporting.data_selection_panel import DataSelectionPanel


def generate_sample_data():
    """サンプルデータを生成"""
    
    # 現在時刻をベースに時系列データを生成
    base_time = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
    times = [base_time + timedelta(minutes=10*i) for i in range(20)]
    time_strings = [t.strftime("%Y-%m-%dT%H:%M:%S") for t in times]
    
    # 風向と風速のサンプルデータ
    wind_directions = [45, 48, 50, 52, 55, 58, 60, 62, 60, 58, 55, 52, 50, 48, 45, 42, 40, 38, 35, 32]
    wind_speeds = [4.5, 4.8, 5.0, 5.2, 5.5, 5.8, 6.0, 6.2, 6.0, 5.8, 5.5, 5.2, 5.0, 4.8, 4.5, 4.2, 4.0, 3.8, 3.5, 3.2]
    
    # 船速と角度のサンプルデータ
    boat_speeds = [3.5, 3.8, 4.0, 4.2, 4.5, 4.8, 5.0, 5.2, 5.0, 4.8, 4.5, 4.2, 4.0, 3.8, 3.5, 3.2, 3.0, 2.8, 2.5, 2.2]
    boat_directions = [40, 43, 45, 47, 50, 53, 55, 57, 55, 53, 50, 47, 45, 43, 40, 37, 35, 33, 30, 27]
    
    # VMGのサンプルデータ
    vmg_values = [2.5, 2.7, 2.8, 3.0, 3.2, 3.4, 3.5, 3.6, 3.5, 3.4, 3.2, 3.0, 2.8, 2.7, 2.5, 2.3, 2.1, 2.0, 1.8, 1.6]
    
    # ヒール角のサンプルデータ
    heel_angles = [10, 12, 15, 18, 20, 22, 25, 28, 25, 22, 20, 18, 15, 12, 10, 8, 5, 3, 0, 0]
    
    # 位置データ（東京湾の架空の座標）
    base_lat = 35.6500
    base_lng = 139.7700
    lats = [base_lat + 0.001*i for i in range(20)]
    lngs = [base_lng + 0.001*i for i in range(20)]
    
    # 時系列データセット
    time_series_data = []
    for i in range(20):
        time_series_data.append({
            "timestamp": time_strings[i],
            "latitude": lats[i],
            "longitude": lngs[i],
            "speed": boat_speeds[i],
            "direction": boat_directions[i],
            "wind_speed": wind_speeds[i],
            "wind_direction": wind_directions[i],
            "vmg": vmg_values[i],
            "heel": heel_angles[i]
        })
    
    # 戦略ポイントデータ
    strategy_points = {
        "track": [
            {"latitude": lats[0], "longitude": lngs[0], "speed": boat_speeds[0], "direction": boat_directions[0]},
            {"latitude": lats[2], "longitude": lngs[2], "speed": boat_speeds[2], "direction": boat_directions[2]},
            {"latitude": lats[4], "longitude": lngs[4], "speed": boat_speeds[4], "direction": boat_directions[4]},
            {"latitude": lats[6], "longitude": lngs[6], "speed": boat_speeds[6], "direction": boat_directions[6]},
            {"latitude": lats[8], "longitude": lngs[8], "speed": boat_speeds[8], "direction": boat_directions[8]},
            {"latitude": lats[10], "longitude": lngs[10], "speed": boat_speeds[10], "direction": boat_directions[10]},
            {"latitude": lats[12], "longitude": lngs[12], "speed": boat_speeds[12], "direction": boat_directions[12]},
            {"latitude": lats[14], "longitude": lngs[14], "speed": boat_speeds[14], "direction": boat_directions[14]},
            {"latitude": lats[16], "longitude": lngs[16], "speed": boat_speeds[16], "direction": boat_directions[16]},
            {"latitude": lats[18], "longitude": lngs[18], "speed": boat_speeds[18], "direction": boat_directions[18]}
        ],
        "points": [
            {"latitude": lats[1], "longitude": lngs[1], "name": "タック1", "type": "tack", "description": "風向変化に対応したタック", "time": "09:10"},
            {"latitude": lats[4], "longitude": lngs[4], "name": "風向変化1", "type": "wind_shift", "description": "北東からの風が強まる", "time": "09:40"},
            {"latitude": lats[7], "longitude": lngs[7], "name": "マーク1", "type": "mark_rounding", "description": "風上マーク回航", "time": "10:10"},
            {"latitude": lats[10], "longitude": lngs[10], "name": "ジャイブ1", "type": "gybe", "description": "風下への転針", "time": "10:40"},
            {"latitude": lats[13], "longitude": lngs[13], "name": "風向変化2", "type": "wind_shift", "description": "風が弱まる傾向", "time": "11:10"},
            {"latitude": lats[16], "longitude": lngs[16], "name": "タック2", "type": "tack", "description": "フィニッシュに向けたタック", "time": "11:40"}
        ]
    }
    
    # 風配図データ
    wind_rose_data = []
    for i in range(0, 360, 30):
        # 各方向に風のデータを生成（風速は方向によって変える）
        frequency = 5 + 5 * np.sin(np.radians(i))
        wind_rose_data.append({
            "direction": i,
            "value": frequency
        })
    
    # コースパフォーマンスデータ
    course_performance_data = {
        "angles": list(range(0, 360, 10)),
        "actual": [0] * 36,  # 36方位（10度間隔）
        "target": [0] * 36,
        "vmg": [0] * 36
    }
    
    # 角度ごとにパフォーマンスデータを設定
    for i, angle in enumerate(course_performance_data["angles"]):
        # 実際の速度（風下で速い）
        course_performance_data["actual"][i] = 2 + 3 * np.sin(np.radians(angle + 180))
        # ターゲット速度（少し高め）
        course_performance_data["target"][i] = 2.5 + 3.5 * np.sin(np.radians(angle + 180))
        # VMG（風上風下方向で高い）
        course_performance_data["vmg"][i] = 1 + 2.5 * (np.sin(np.radians(angle)) ** 2)
    
    # タッキングアングル分析データ
    tacking_angles = []
    # 正規分布に近い形で生成（90度周辺に集中）
    for i in range(100):
        angle = np.random.normal(90, 10)  # 平均90度、標準偏差10度
        if 60 <= angle <= 120:  # 60～120度の範囲に制限
            tacking_angles.append({"tacking_angle": angle})
    
    # ヒートマップデータ（時間×パラメータの分布）
    heatmap_data = []
    for hour in range(9, 12):
        for minute in range(0, 60, 30):
            time_label = f"{hour:02d}:{minute:02d}"
            for param in ["speed", "wind_speed", "vmg"]:
                if param == "speed":
                    value = 2.5 + (hour - 9) * 0.7 + (minute / 60) * 0.5
                elif param == "wind_speed":
                    value = 3.5 + (hour - 9) * 0.5 + (minute / 60) * 0.3
                else:  # vmg
                    value = 1.8 + (hour - 9) * 0.5 + (minute / 60) * 0.2
                
                heatmap_data.append({
                    "x": time_label,
                    "y": param,
                    "value": value
                })
    
    # 相関分析データを時系列データから抽出
    correlation_data = []
    for item in time_series_data:
        correlation_data.append({
            "speed": item["speed"],
            "wind_speed": item["wind_speed"],
            "vmg": item["vmg"],
            "heel": item["heel"],
            "wind_angle": item["wind_direction"]
        })
    
    # イベントタイムライン
    event_timeline = []
    for point in strategy_points["points"]:
        event_time = base_time + timedelta(minutes=int(point["time"].split(":")[0]) * 60 + int(point["time"].split(":")[1]) - 9 * 60)
        event_timeline.append({
            "timestamp": event_time.strftime("%Y-%m-%dT%H:%M:%S"),
            "event": point["name"],
            "type": point["type"],
            "description": point["description"]
        })
    
    # パラメータタイムライン（時系列データと同じ）
    parameter_timeline = time_series_data
    
    # セグメント比較データ
    segment_comparison = [
        {"segment": "風上1", "session": "Session1", "value": 85},
        {"segment": "風上2", "session": "Session1", "value": 88},
        {"segment": "風下1", "session": "Session1", "value": 92},
        {"segment": "風下2", "session": "Session1", "value": 90},
        {"segment": "風上3", "session": "Session1", "value": 86},
        {"segment": "風上4", "session": "Session1", "value": 82},
        {"segment": "風上1", "session": "Session2", "value": 80},
        {"segment": "風上2", "session": "Session2", "value": 84},
        {"segment": "風下1", "session": "Session2", "value": 89},
        {"segment": "風下2", "session": "Session2", "value": 87},
        {"segment": "風上3", "session": "Session2", "value": 83},
        {"segment": "風上4", "session": "Session2", "value": 79}
    ]
    
    # 風場データ
    wind_field_data = {
        "wind_field": {
            "lat_min": base_lat - 0.01,
            "lat_max": base_lat + 0.03,
            "lon_min": base_lng - 0.01,
            "lon_max": base_lng + 0.03,
            "nx": 5,
            "ny": 5,
            "u-wind": [
                [1.0, 1.2, 1.4, 1.6, 1.8],
                [1.1, 1.3, 1.5, 1.7, 1.9],
                [1.2, 1.4, 1.6, 1.8, 2.0],
                [1.3, 1.5, 1.7, 1.9, 2.1],
                [1.4, 1.6, 1.8, 2.0, 2.2]
            ],
            "v-wind": [
                [0.5, 0.6, 0.7, 0.8, 0.9],
                [0.6, 0.7, 0.8, 0.9, 1.0],
                [0.7, 0.8, 0.9, 1.0, 1.1],
                [0.8, 0.9, 1.0, 1.1, 1.2],
                [0.9, 1.0, 1.1, 1.2, 1.3]
            ]
        }
    }
    
    # すべてのデータセットを辞書にまとめる
    sample_data = {
        "time_series": time_series_data,
        "strategy_points": strategy_points,
        "wind_rose": wind_rose_data,
        "course_performance": course_performance_data,
        "tacking_angles": tacking_angles,
        "heatmap_data": heatmap_data,
        "correlation_data": correlation_data,
        "event_timeline": event_timeline,
        "parameter_timeline": parameter_timeline,
        "segment_comparison": segment_comparison,
        "wind_field": wind_field_data
    }
    
    return sample_data


def create_visualization_element(element_type):
    """指定された要素タイプに基づいて可視化要素を作成"""
    
    element_classes = {
        "WindRoseElement": WindRoseElement,
        "CoursePerformanceElement": CoursePerformanceElement,
        "TackingAngleElement": TackingAngleElement,
        "StrategyPointMapElement": StrategyPointMapElement,
        "TimeSeriesElement": TimeSeriesElement,
        "BoxPlotElement": BoxPlotElement,
        "HeatMapElement": HeatMapElement,
        "CorrelationElement": CorrelationElement,
        "TrackMapElement": TrackMapElement,
        "HeatMapLayerElement": HeatMapLayerElement,
        "StrategyPointLayerElement": StrategyPointLayerElement,
        "WindFieldElement": WindFieldElement,
        "EventTimelineElement": EventTimelineElement,
        "ParameterTimelineElement": ParameterTimelineElement,
        "SegmentComparisonElement": SegmentComparisonElement,
        "DataViewerElement": DataViewerElement
    }
    
    # 要素タイプに基づいてデフォルトプロパティを設定
    default_properties = {
        "WindRoseElement": {
            "title": "風配図",
            "data_source": "wind_rose"
        },
        "CoursePerformanceElement": {
            "title": "コースパフォーマンス",
            "data_source": "course_performance"
        },
        "TackingAngleElement": {
            "title": "タッキングアングル分析",
            "data_source": "tacking_angles"
        },
        "StrategyPointMapElement": {
            "title": "戦略ポイントマップ",
            "data_source": "strategy_points"
        },
        "TimeSeriesElement": {
            "title": "時系列分析",
            "data_source": "time_series",
            "time_key": "timestamp",
            "value_keys": ["speed", "wind_speed", "vmg"]
        },
        "BoxPlotElement": {
            "title": "ボックスプロット",
            "data_source": "segment_comparison",
            "group_key": "segment",
            "value_key": "value"
        },
        "HeatMapElement": {
            "title": "ヒートマップ",
            "data_source": "heatmap_data",
            "x_key": "x",
            "y_key": "y",
            "value_key": "value"
        },
        "CorrelationElement": {
            "title": "相関分析",
            "data_source": "correlation_data",
            "x_param": "wind_speed",
            "y_param": "speed"
        },
        "TrackMapElement": {
            "title": "航路追跡マップ",
            "data_source": "time_series"
        },
        "HeatMapLayerElement": {
            "title": "ヒートマップレイヤー",
            "data_source": "time_series",
            "heat_value_key": "speed"
        },
        "StrategyPointLayerElement": {
            "title": "戦略ポイントレイヤー",
            "data_source": "strategy_points"
        },
        "WindFieldElement": {
            "title": "風場の可視化",
            "data_source": "wind_field"
        },
        "EventTimelineElement": {
            "title": "イベントタイムライン",
            "data_source": "event_timeline",
            "time_key": "timestamp",
            "event_key": "event"
        },
        "ParameterTimelineElement": {
            "title": "パラメータタイムライン",
            "data_source": "parameter_timeline",
            "time_key": "timestamp",
            "parameters": ["speed", "wind_speed", "vmg", "heel"]
        },
        "SegmentComparisonElement": {
            "title": "セグメント比較",
            "data_source": "segment_comparison",
            "segment_key": "segment",
            "session_key": "session",
            "value_key": "value"
        },
        "DataViewerElement": {
            "title": "データビューア",
            "data_source": "time_series",
            "time_key": "timestamp"
        }
    }
    
    # 要素クラスを取得
    element_class = element_classes.get(element_type)
    if element_class is None:
        st.error(f"未知の要素タイプ: {element_type}")
        return None
    
    # デフォルトプロパティを取得
    props = default_properties.get(element_type, {})
    
    # 要素を作成して返す
    return element_class(**props)


def main():
    st.set_page_config(
        page_title="可視化要素デモ",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("セーリング戦略分析 可視化要素デモ")
    
    # サイドバー
    with st.sidebar:
        st.header("可視化要素デモについて")
        st.markdown("""
        このデモアプリケーションは、セーリング戦略分析のための可視化要素を
        試すためのインターフェースを提供します。

        ### 主な機能

        - 各種可視化要素の表示
        - パラメータのカスタマイズ
        - リアルタイムプレビュー

        ### 要素のカテゴリ

        1. **セーリング特化型**: 風配図、コースパフォーマンス、タッキングアングル分析など
        2. **統計分析**: 時系列分析、ボックスプロット、ヒートマップ、相関分析など
        3. **地図要素**: 航路追跡マップ、ヒートマップレイヤー、戦略ポイントレイヤーなど
        4. **タイムライン**: イベントタイムライン、パラメータタイムライン、セグメント比較など
        """)
        
        # 要素タイプの選択
        st.header("要素の選択")
        
        # カテゴリ別に選択オプションを提供
        visualization_category = st.selectbox(
            "可視化カテゴリ",
            options=["セーリング特化型", "統計分析", "地図要素", "タイムライン"]
        )
        
        # カテゴリに応じた要素タイプのオプション
        category_elements = {
            "セーリング特化型": [
                "WindRoseElement", "CoursePerformanceElement", 
                "TackingAngleElement", "StrategyPointMapElement"
            ],
            "統計分析": [
                "TimeSeriesElement", "BoxPlotElement", 
                "HeatMapElement", "CorrelationElement"
            ],
            "地図要素": [
                "TrackMapElement", "HeatMapLayerElement", 
                "StrategyPointLayerElement", "WindFieldElement"
            ],
            "タイムライン": [
                "EventTimelineElement", "ParameterTimelineElement", 
                "SegmentComparisonElement", "DataViewerElement"
            ]
        }
        
        # 選択されたカテゴリの要素を表示名に変換
        element_display_names = {
            "WindRoseElement": "風配図",
            "CoursePerformanceElement": "コースパフォーマンス",
            "TackingAngleElement": "タッキングアングル分析",
            "StrategyPointMapElement": "戦略ポイントマップ",
            "TimeSeriesElement": "時系列分析",
            "BoxPlotElement": "ボックスプロット",
            "HeatMapElement": "ヒートマップ",
            "CorrelationElement": "相関分析",
            "TrackMapElement": "航路追跡マップ",
            "HeatMapLayerElement": "ヒートマップレイヤー",
            "StrategyPointLayerElement": "戦略ポイントレイヤー",
            "WindFieldElement": "風場の可視化",
            "EventTimelineElement": "イベントタイムライン",
            "ParameterTimelineElement": "パラメータタイムライン",
            "SegmentComparisonElement": "セグメント比較",
            "DataViewerElement": "データビューア"
        }
        
        # 選択されたカテゴリの要素タイプのオプションを表示
        element_options = category_elements.get(visualization_category, [])
        element_option_names = [element_display_names.get(elem, elem) for elem in element_options]
        
        selected_element_name = st.selectbox(
            "要素タイプ",
            options=element_option_names,
            format_func=lambda x: x
        )
        
        # 表示名から要素タイプに変換
        reverse_names = {v: k for k, v in element_display_names.items()}
        selected_element_type = reverse_names.get(selected_element_name)
        
        if st.button("この要素を表示"):
            # セッション状態に選択された要素タイプを保存
            st.session_state.selected_element_type = selected_element_type
    
    # メインコンテンツ
    if not hasattr(st.session_state, "sample_data"):
        # サンプルデータを生成
        st.session_state.sample_data = generate_sample_data()
    
    if not hasattr(st.session_state, "selected_element_type"):
        # デフォルトの要素タイプを設定
        st.session_state.selected_element_type = "WindRoseElement"
    
    # 選択された要素タイプに基づいて要素を作成
    element = create_visualization_element(st.session_state.selected_element_type)
    
    if element:
        # 要素のタイトルを表示
        st.subheader(f"要素タイプ: {element_display_names.get(st.session_state.selected_element_type, st.session_state.selected_element_type)}")
        
        # タブを作成
        tab1, tab2, tab3 = st.tabs(["プレビュー", "オプション設定", "データソース"])
        
        with tab1:
            # 要素のプレビュー
            st.subheader("プレビュー")
            html_content = element.render(st.session_state.sample_data)
            st.components.v1.html(html_content, height=600, scrolling=True)
            
            # HTMLソースの表示（デバッグ用）
            with st.expander("HTMLソース", expanded=False):
                st.code(html_content, language="html")
        
        with tab2:
            # オプションパネル
            def on_option_change(key, value):
                if key.startswith("style_"):
                    # スタイルプロパティの場合
                    style_key = key.replace("style_", "")
                    element.set_style(style_key, value)
                else:
                    # 通常のプロパティの場合
                    element.set_property(key, value)
            
            options_panel = ChartOptionsPanel(on_option_change=on_option_change)
            options_panel.render(element)
        
        with tab3:
            # データ選択パネル
            def on_data_selection(source_name, data):
                element.data_source = source_name
                if source_name not in st.session_state.sample_data:
                    # 新しいデータソースの場合、sample_dataに追加
                    st.session_state.sample_data[source_name] = data
                st.success(f"データソース '{source_name}' を選択しました")
            
            data_panel = DataSelectionPanel(on_data_selection=on_data_selection)
            data_panel.render(st.session_state.sample_data)
    else:
        st.error("要素の作成に失敗しました。")


if __name__ == "__main__":
    main()
