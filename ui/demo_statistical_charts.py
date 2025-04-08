"""
ui.demo_statistical_charts

統計分析グラフのデモアプリケーションです。
時系列分析、ボックスプロット、ヒートマップ、相関分析の各グラフタイプの
機能をデモンストレーションします。
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta
import json
import os

from sailing_data_processor.reporting.elements.visualizations.statistical_charts import (
    TimeSeriesElement, BoxPlotElement, HeatMapElement, CorrelationElement
)
from ui.components.reporting.statistical_properties_panel import StatisticalPropertiesPanel
from ui.components.reporting.data_preview import DataPreviewComponent


def load_sample_data():
    """
    サンプルデータを生成または読み込む
    
    Returns
    -------
    Dict[str, Any]
        データコンテキスト
    """
    # コンテキストを初期化
    context = {}
    
    # 時系列データを生成
    def generate_time_series(n=100, freq='1min'):
        now = datetime.now()
        times = [now - timedelta(minutes=i) for i in range(n)]
        times.reverse()
        
        data = pd.DataFrame({
            'timestamp': times,
            'speed': np.random.normal(8, 2, n) + np.sin(np.linspace(0, 6, n)),
            'direction': np.cumsum(np.random.normal(0, 5, n)) % 360,
            'wind_speed': np.random.normal(12, 3, n) + np.sin(np.linspace(0, 4, n)),
            'wind_direction': (np.random.normal(270, 10, n) + np.sin(np.linspace(0, 8, n)) * 20) % 360,
            'temperature': np.random.normal(22, 3, n) + np.sin(np.linspace(0, 2, n)) * 3,
            'vmg': np.random.normal(6, 1.5, n) + np.sin(np.linspace(0, 5, n))
        })
        
        return data
    
    # ボックスプロットデータを生成
    def generate_box_plot_data(n_groups=5, n_points=30):
        groups = ['A', 'B', 'C', 'D', 'E'][:n_groups]
        data = []
        
        for group in groups:
            # 各グループに異なる分布を持たせる
            if group == 'A':
                values = np.random.normal(10, 2, n_points)
            elif group == 'B':
                values = np.random.normal(8, 1.5, n_points)
            elif group == 'C':
                values = np.random.normal(12, 3, n_points)
            elif group == 'D':
                values = np.random.normal(9, 2.5, n_points)
            else:
                values = np.random.normal(11, 2, n_points)
            
            # 外れ値を追加
            outliers = np.random.normal(20, 5, int(n_points * 0.1))
            values = np.append(values, outliers)
            
            for value in values:
                data.append({
                    'group': group,
                    'value': value,
                    'category': np.random.choice(['X', 'Y', 'Z'])
                })
        
        return pd.DataFrame(data)
    
    # ヒートマップデータを生成
    def generate_heat_map_data(n_x=10, n_y=8):
        data = []
        x_labels = [f"X{i+1}" for i in range(n_x)]
        y_labels = [f"Y{i+1}" for i in range(n_y)]
        
        # 座標形式のデータを生成
        for x_idx, x in enumerate(x_labels):
            for y_idx, y in enumerate(y_labels):
                # 中心に近いほど高い値を持つパターン
                center_x = n_x / 2
                center_y = n_y / 2
                distance = np.sqrt((x_idx - center_x)**2 + (y_idx - center_y)**2)
                value = np.exp(-distance / 3) * 10 + np.random.normal(0, 0.5)
                
                data.append({
                    'x': x,
                    'y': y,
                    'value': value,
                    'category': 'heat'
                })
        
        # マトリックス形式のデータも作成
        matrix = np.zeros((n_y, n_x))
        for item in data:
            x_idx = x_labels.index(item['x'])
            y_idx = y_labels.index(item['y'])
            matrix[y_idx, x_idx] = item['value']
        
        return pd.DataFrame(data), matrix, x_labels, y_labels
    
    # 相関データを生成
    def generate_correlation_data(n=100):
        # 基本的な関係を持つ変数を生成
        x = np.random.normal(10, 2, n)
        
        # 線形関係
        y_linear = 2 * x + 5 + np.random.normal(0, 3, n)
        
        # 非線形関係
        y_nonlinear = x**2 / 10 + np.random.normal(0, 5, n)
        
        # 弱い相関
        y_weak = 0.5 * x + np.random.normal(0, 8, n)
        
        # データフレームを作成
        data = pd.DataFrame({
            'x': x,
            'y_linear': y_linear,
            'y_nonlinear': y_nonlinear,
            'y_weak': y_weak,
            'category': np.random.choice(['A', 'B', 'C'], size=n)
        })
        
        return data
    
    # データを生成してコンテキストに追加
    context['time_series_data'] = generate_time_series()
    context['box_plot_data'] = generate_box_plot_data()
    
    heat_map_data, heat_matrix, x_labels, y_labels = generate_heat_map_data()
    context['heat_map_data'] = heat_map_data
    context['heat_matrix'] = {
        'data': heat_matrix.tolist(),
        'x_labels': x_labels,
        'y_labels': y_labels
    }
    
    context['correlation_data'] = generate_correlation_data()
    
    return context


def render_chart_demo(chart_element, properties, data_context):
    """
    チャートデモを描画
    
    Parameters
    ----------
    chart_element : BaseChartElement
        チャート要素
    properties : Dict[str, Any]
        プロパティ値
    data_context : Dict[str, Any]
        データコンテキスト
    """
    # プロパティを設定
    for key, value in properties.items():
        setattr(chart_element, key, value)
    
    # チャートデータとオプションを取得
    chart_data = chart_element.get_chart_data(data_context)
    chart_options = chart_element.get_chart_options()
    
    # JSONとして表示
    st.write("### チャートデータ")
    st.json(json.dumps(chart_data, default=str)[:1000] + "...")
    
    st.write("### チャートオプション")
    st.json(json.dumps(chart_options, default=str)[:1000] + "...")
    
    # HTML描画用のコードを生成
    libraries = chart_element.get_chart_libraries()
    initialization_code = chart_element.get_chart_initialization_code("config")
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Chart Demo</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        
        <!-- 必要なライブラリを読み込み -->
        {' '.join([f'<script src="{lib}"></script>' for lib in libraries])}
    </head>
    <body>
        <div style="width: 100%; max-width: 800px; margin: 0 auto;">
            <canvas id="{chart_element.chart_id}" width="800" height="400"></canvas>
        </div>
        
        <script>
            var config = {json.dumps(chart_data, default=str)};
            config.options = {json.dumps(chart_options, default=str)};
            
            {initialization_code}
        </script>
    </body>
    </html>
    """
    
    # HTMLをファイルに保存
    temp_html_file = "temp_chart_demo.html"
    with open(temp_html_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    # iframeとして表示
    st.write("### プレビュー")
    st.write("※注: 実際のHTML描画が可能な環境では以下にチャートが表示されます")
    
    if os.path.isfile(temp_html_file):
        with open(temp_html_file, "r", encoding="utf-8") as f:
            html_code = f.read()
            st.code(html_code, language="html")
    
    # Plotlyでの代替表示（一部のグラフタイプのみ）
    st.write("### 代替プレビュー (Plotly)")
    
    try:
        if isinstance(chart_element, TimeSeriesElement):
            # 時系列グラフの代替プレビュー
            data_source = properties.get("data_source", "time_series_data")
            df = data_context.get(data_source)
            if df is not None and isinstance(df, pd.DataFrame):
                time_key = properties.get("time_key", "timestamp")
                value_keys = properties.get("value_keys", df.select_dtypes(include=[np.number]).columns[:3].tolist())
                
                fig = px.line(df, x=time_key, y=value_keys, title=properties.get("title", "時系列分析"))
                st.plotly_chart(fig, use_container_width=True)
        
        elif isinstance(chart_element, BoxPlotElement):
            # ボックスプロットの代替プレビュー
            data_source = properties.get("data_source", "box_plot_data")
            df = data_context.get(data_source)
            if df is not None and isinstance(df, pd.DataFrame):
                group_key = properties.get("group_key", "group")
                value_key = properties.get("value_key", "value")
                
                fig = px.box(df, x=group_key, y=value_key, title=properties.get("title", "ボックスプロット"))
                st.plotly_chart(fig, use_container_width=True)
        
        elif isinstance(chart_element, HeatMapElement):
            # ヒートマップの代替プレビュー
            data_source = properties.get("data_source", "heat_map_data")
            if "heat_matrix" in data_context:
                matrix_data = data_context["heat_matrix"]
                matrix = np.array(matrix_data["data"])
                x_labels = matrix_data["x_labels"]
                y_labels = matrix_data["y_labels"]
                
                fig = px.imshow(matrix, 
                               x=x_labels, 
                               y=y_labels, 
                               color_continuous_scale="Viridis", 
                               title=properties.get("title", "ヒートマップ"))
                st.plotly_chart(fig, use_container_width=True)
        
        elif isinstance(chart_element, CorrelationElement):
            # 相関グラフの代替プレビュー
            data_source = properties.get("data_source", "correlation_data")
            df = data_context.get(data_source)
            if df is not None and isinstance(df, pd.DataFrame):
                x_param = properties.get("x_param", "x")
                y_param = properties.get("y_param", "y_linear")
                
                fig = px.scatter(df, x=x_param, y=y_param, 
                                trendline="ols" if properties.get("show_trendline", True) else None,
                                title=properties.get("title", "相関分析"))
                st.plotly_chart(fig, use_container_width=True)
    
    except Exception as e:
        st.error(f"プレビュー生成エラー: {str(e)}")


def main():
    """
    メイン関数
    """
    st.set_page_config(
        page_title="統計分析グラフデモ",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("統計分析グラフデモ")
    st.write("時系列分析、ボックスプロット、ヒートマップ、相関分析の各グラフタイプをデモンストレーションします。")
    
    # サンプルデータを読み込み
    data_context = load_sample_data()
    
    # データプレビューコンポーネント
    data_preview = DataPreviewComponent()
    
    # プロパティパネル
    properties_panel = StatisticalPropertiesPanel()
    
    # グラフタイプを選択
    graph_type = st.sidebar.selectbox(
        "グラフタイプ",
        options=["time_series", "box_plot", "heat_map", "correlation"],
        format_func=lambda x: {
            "time_series": "時系列分析",
            "box_plot": "ボックスプロット",
            "heat_map": "ヒートマップ",
            "correlation": "相関分析"
        }.get(x, x)
    )
    
    # データソースの選択
    data_source = st.sidebar.selectbox(
        "データソース",
        options=list(data_context.keys()),
        format_func=lambda x: {
            "time_series_data": "時系列データ",
            "box_plot_data": "分布データ",
            "heat_map_data": "ヒートマップデータ（座標形式）",
            "heat_matrix": "ヒートマップデータ（マトリックス形式）",
            "correlation_data": "相関データ"
        }.get(x, x)
    )
    
    # 選択されたデータソースのプレビュー
    st.sidebar.subheader("データプレビュー")
    with st.sidebar.expander("データプレビュー", expanded=False):
        data_preview.render(data_context[data_source], "選択データ")
    
    # デフォルトのプロパティを設定
    default_properties = {
        "data_source": data_source
    }
    
    if graph_type == "time_series":
        default_properties.update({
            "time_key": "timestamp",
            "value_keys": ["speed", "wind_speed"],
            "title": "セーリングデータ時系列分析",
            "x_axis_title": "時間",
            "y_axis_title": "スピード (ノット)",
            "moving_average": True,
            "moving_average_window": 5
        })
        chart_element = TimeSeriesElement(element_type="chart", **default_properties)
    
    elif graph_type == "box_plot":
        default_properties.update({
            "group_key": "group",
            "value_key": "value",
            "title": "グループ別データ分布",
            "x_axis_title": "グループ",
            "y_axis_title": "値",
            "begin_at_zero": False
        })
        chart_element = BoxPlotElement(element_type="chart", **default_properties)
    
    elif graph_type == "heat_map":
        if data_source == "heat_matrix":
            default_properties.update({
                "x_labels": data_context["heat_matrix"]["x_labels"],
                "y_labels": data_context["heat_matrix"]["y_labels"],
                "title": "ヒートマップ (マトリックス形式)",
                "x_axis_title": "X軸",
                "y_axis_title": "Y軸",
                "cell_width": 40,
                "cell_height": 40
            })
        else:
            default_properties.update({
                "x_key": "x",
                "y_key": "y",
                "value_key": "value",
                "title": "ヒートマップ (座標形式)",
                "x_axis_title": "X軸",
                "y_axis_title": "Y軸",
                "cell_width": 40,
                "cell_height": 40
            })
        chart_element = HeatMapElement(element_type="chart", **default_properties)
    
    elif graph_type == "correlation":
        default_properties.update({
            "x_param": "x",
            "y_param": "y_linear",
            "title": "変数間の相関分析",
            "x_axis_title": "X値",
            "y_axis_title": "Y値",
            "show_trendline": True,
            "regression_type": "linear"
        })
        chart_element = CorrelationElement(element_type="chart", **default_properties)
    
    # 2カラムレイアウト
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("プロパティ設定")
        properties = properties_panel.render(graph_type, default_properties, data_context)
    
    with col2:
        st.subheader("チャートプレビュー")
        render_chart_demo(chart_element, properties, data_context)


if __name__ == "__main__":
    main()
