"""
ui.components.reporting.chart_preview

チャート要素のプレビューを表示するコンポーネントを提供するモジュールです。
"""

import streamlit as st
from typing import Dict, List, Any, Optional, Union
import json
from contextlib import contextmanager

from sailing_data_processor.reporting.templates.template_model import (
    ElementType, ElementModel, Element
)
from sailing_data_processor.reporting.elements.visualizations.base_chart import BaseChartElement
from sailing_data_processor.reporting.elements.visualizations.basic_charts import (
    LineChartElement, ScatterChartElement, BarChartElement, PieChartElement
)
from sailing_data_processor.reporting.elements.visualizations.sailing_charts import (
    WindRoseElement, PolarDiagramElement, TackingAngleElement, CoursePerformanceElement
)


def render_chart_preview(
    element_properties: Dict[str, Any],
    sample_data: Optional[Dict[str, Any]] = None,
    width: str = "100%",
    height: str = "500px"
) -> None:
    """
    チャート要素のプレビューを表示

    Parameters
    ----------
    element_properties : Dict[str, Any]
        チャート要素のプロパティ
    sample_data : Optional[Dict[str, Any]], optional
        サンプルデータ, by default None
    width : str, optional
        プレビューの幅, by default "100%"
    height : str, optional
        プレビューの高さ, by default "500px"
    """
    # サンプルデータがない場合はダミーデータを生成
    if sample_data is None:
        sample_data = _generate_sample_data(element_properties)
    
    # プレビューコンテナの作成
    with st.container():
        st.subheader("チャートプレビュー")
        
        # スタイル設定
        preview_style = f"width: {width}; height: {height}; border: 1px solid #ddd; padding: 10px; border-radius: 5px;"
        st.markdown(f'<div style="{preview_style}">', unsafe_allow_html=True)
        
        # チャートタイプの取得
        chart_type = element_properties.get("chart_type", "")
        
        # チャートタイプに応じたチャート要素を作成
        chart_element = _create_chart_element(chart_type, element_properties)
        
        if chart_element:
            # データソース名を取得
            data_source_name = element_properties.get("data_source", "data")
            
            # コンテキストの作成
            context = {data_source_name: sample_data}
            
            # レンダリング結果を取得
            try:
                html_output = chart_element.render(context)
                # HTMLの出力
                st.components.v1.html(html_output, height=int(height.replace("px", "")))
            except Exception as e:
                st.error(f"チャートのレンダリングエラー: {str(e)}")
                st.code(json.dumps(element_properties, indent=2, ensure_ascii=False))
        else:
            st.info(f"サポートされていないチャートタイプ: {chart_type}")
        
        st.markdown('</div>', unsafe_allow_html=True)


def _create_chart_element(chart_type: str, properties: Dict[str, Any]) -> Optional[BaseChartElement]:
    """
    チャートタイプに応じたチャート要素を作成

    Parameters
    ----------
    chart_type : str
        チャートタイプ
    properties : Dict[str, Any]
        チャート要素のプロパティ

    Returns
    -------
    Optional[BaseChartElement]
        作成されたチャート要素、サポートされていないタイプの場合はNone
    """
    # デフォルトのElementModelを作成
    model = ElementModel(
        element_id=properties.get("element_id", "preview_chart"),
        element_type=ElementType.CHART,
        properties=properties,
        styles=properties.get("styles", {}),
        conditions=properties.get("conditions", [])
    )
    
    # 基本チャートタイプ
    if chart_type == "line":
        return LineChartElement(model)
    elif chart_type == "scatter":
        return ScatterChartElement(model)
    elif chart_type == "bar":
        return BarChartElement(model)
    elif chart_type == "pie":
        return PieChartElement(model)
    
    # セーリング特化型チャート
    elif chart_type == "windrose":
        return WindRoseElement(model)
    elif chart_type == "polar":
        return PolarDiagramElement(model)
    elif chart_type == "tacking":
        return TackingAngleElement(model)
    elif chart_type == "course_performance":
        return CoursePerformanceElement(model)
    
    # サポートされていないタイプ
    return None


def _generate_sample_data(properties: Dict[str, Any]) -> Dict[str, Any]:
    """
    チャートタイプに応じたサンプルデータを生成

    Parameters
    ----------
    properties : Dict[str, Any]
        チャート要素のプロパティ

    Returns
    -------
    Dict[str, Any]
        生成されたサンプルデータ
    """
    chart_type = properties.get("chart_type", "")
    
    # 基本チャートタイプのサンプルデータ
    if chart_type == "line":
        return _generate_line_chart_sample(properties)
    elif chart_type == "scatter":
        return _generate_scatter_chart_sample(properties)
    elif chart_type == "bar":
        return _generate_bar_chart_sample(properties)
    elif chart_type == "pie":
        return _generate_pie_chart_sample(properties)
    
    # セーリング特化型チャートのサンプルデータ
    elif chart_type == "windrose":
        return _generate_windrose_sample(properties)
    elif chart_type == "polar":
        return _generate_polar_diagram_sample(properties)
    elif chart_type == "tacking":
        return _generate_tacking_angle_sample(properties)
    elif chart_type == "course_performance":
        return _generate_course_performance_sample(properties)
    
    # サポートされていないタイプの場合は空のデータを返す
    return {}


def _generate_line_chart_sample(properties: Dict[str, Any]) -> Dict[str, Any]:
    """
    折れ線グラフのサンプルデータを生成

    Parameters
    ----------
    properties : Dict[str, Any]
        チャート要素のプロパティ

    Returns
    -------
    Dict[str, Any]
        生成されたサンプルデータ
    """
    import numpy as np
    from datetime import datetime, timedelta
    
    # フィールド名を取得
    x_field = properties.get("x_field", "x")
    y_field = properties.get("y_field", "y")
    series_field = properties.get("series_field", "")
    
    # 基本データの生成
    n_points = 20
    x_values = list(range(n_points))
    
    # 時系列データの場合
    if x_field.lower() in ["date", "time", "timestamp", "datetime"]:
        base_date = datetime.now() - timedelta(days=n_points)
        x_values = [(base_date + timedelta(days=i)).isoformat() for i in range(n_points)]
    
    data = []
    
    if series_field:
        # 複数系列のデータを生成
        series_names = ["A", "B", "C"]
        for series in series_names:
            # 系列ごとに異なる波形を生成
            if series == "A":
                y_values = [5 + i * 0.5 + np.sin(i * 0.5) * 3 for i in range(n_points)]
            elif series == "B":
                y_values = [10 + i * 0.3 + np.cos(i * 0.5) * 2 for i in range(n_points)]
            else:
                y_values = [7 + i * 0.4 + np.sin(i * 0.3) * 4 for i in range(n_points)]
            
            for i in range(n_points):
                data.append({
                    x_field: x_values[i],
                    y_field: y_values[i],
                    series_field: series
                })
    else:
        # 単一系列のデータを生成
        y_values = [10 + i * 0.5 + np.sin(i * 0.5) * 5 for i in range(n_points)]
        for i in range(n_points):
            data.append({
                x_field: x_values[i],
                y_field: y_values[i]
            })
    
    return data


def _generate_scatter_chart_sample(properties: Dict[str, Any]) -> Dict[str, Any]:
    """
    散布図のサンプルデータを生成

    Parameters
    ----------
    properties : Dict[str, Any]
        チャート要素のプロパティ

    Returns
    -------
    Dict[str, Any]
        生成されたサンプルデータ
    """
    import numpy as np
    
    # フィールド名を取得
    x_field = properties.get("x_field", "x")
    y_field = properties.get("y_field", "y")
    series_field = properties.get("series_field", "")
    
    # 基本データの生成
    n_points = 30
    data = []
    
    if series_field:
        # 複数系列のデータを生成
        series_names = ["グループA", "グループB", "グループC"]
        
        for series in series_names:
            # 系列ごとに中心位置をずらす
            if series == "グループA":
                center_x, center_y = 5, 5
                cov = [[3, 1], [1, 2]]
            elif series == "グループB":
                center_x, center_y = 10, 15
                cov = [[2, -0.5], [-0.5, 3]]
            else:
                center_x, center_y = 15, 8
                cov = [[4, 0], [0, 1]]
            
            # 分布に従ってランダムな点を生成
            points = np.random.multivariate_normal([center_x, center_y], cov, n_points)
            
            for i in range(n_points):
                data.append({
                    x_field: float(points[i, 0]),
                    y_field: float(points[i, 1]),
                    series_field: series
                })
    else:
        # 単一系列のデータを生成
        x_values = np.random.normal(10, 3, n_points)
        # 線形関係にノイズを加える
        y_values = x_values * 0.8 + np.random.normal(0, 2, n_points) + 5
        
        for i in range(n_points):
            data.append({
                x_field: float(x_values[i]),
                y_field: float(y_values[i])
            })
    
    return data


def _generate_bar_chart_sample(properties: Dict[str, Any]) -> Dict[str, Any]:
    """
    棒グラフのサンプルデータを生成

    Parameters
    ----------
    properties : Dict[str, Any]
        チャート要素のプロパティ

    Returns
    -------
    Dict[str, Any]
        生成されたサンプルデータ
    """
    import numpy as np
    
    # フィールド名を取得
    label_field = properties.get("label_field", "label")
    value_field = properties.get("value_field", "value")
    series_field = properties.get("series_field", "")
    
    # カテゴリとそれに対応する値を生成
    categories = ["A", "B", "C", "D", "E", "F"]
    data = []
    
    if series_field:
        # 複数系列のデータを生成
        series_names = ["2023年", "2024年", "2025年"]
        
        for series in series_names:
            # 系列ごとに異なる値を設定
            for category in categories:
                data.append({
                    label_field: category,
                    value_field: np.random.randint(10, 100),
                    series_field: series
                })
    else:
        # 単一系列のデータを生成
        for category in categories:
            data.append({
                label_field: category,
                value_field: np.random.randint(10, 100)
            })
    
    return data


def _generate_pie_chart_sample(properties: Dict[str, Any]) -> Dict[str, Any]:
    """
    円グラフのサンプルデータを生成

    Parameters
    ----------
    properties : Dict[str, Any]
        チャート要素のプロパティ

    Returns
    -------
    Dict[str, Any]
        生成されたサンプルデータ
    """
    import numpy as np
    
    # フィールド名を取得
    label_field = properties.get("label_field", "label")
    value_field = properties.get("value_field", "value")
    
    # カテゴリとそれに対応する値を生成
    categories = ["サブシステムA", "サブシステムB", "サブシステムC", "サブシステムD", "その他"]
    
    # 値の合計が100になるようにデータを生成
    values = np.random.randint(5, 30, len(categories))
    total = np.sum(values)
    scaled_values = [int(v * 100 / total) for v in values]
    
    # 合計が100になるよう調整
    remainder = 100 - sum(scaled_values)
    scaled_values[0] += remainder
    
    data = []
    for i, category in enumerate(categories):
        data.append({
            label_field: category,
            value_field: scaled_values[i]
        })
    
    return data


def _generate_windrose_sample(properties: Dict[str, Any]) -> Dict[str, Any]:
    """
    風配図のサンプルデータを生成

    Parameters
    ----------
    properties : Dict[str, Any]
        チャート要素のプロパティ

    Returns
    -------
    Dict[str, Any]
        生成されたサンプルデータ
    """
    import numpy as np
    from datetime import datetime, timedelta
    
    # フィールド名を取得
    direction_key = properties.get("direction_key", "direction")
    value_key = properties.get("value_key", "speed")
    time_key = properties.get("time_key", "timestamp")
    
    # サンプルデータの生成
    n_points = 500
    
    # 方位分布はノーマル分布と一様分布の組み合わせ
    direction_primary = np.random.normal(45, 15, int(n_points * 0.6))  # 主要風向
    direction_secondary = np.random.normal(225, 20, int(n_points * 0.3))  # 二次風向
    direction_random = np.random.uniform(0, 360, n_points - len(direction_primary) - len(direction_secondary))  # ランダム成分
    
    directions = np.concatenate([direction_primary, direction_secondary, direction_random])
    directions = directions % 360  # 0-360の範囲に正規化
    
    # 風速はガンマ分布
    speeds = np.random.gamma(2, 2, n_points)
    
    # 時間は過去数日間
    base_time = datetime.now() - timedelta(days=7)
    times = [base_time + timedelta(minutes=np.random.randint(0, 7*24*60)) for _ in range(n_points)]
    times_iso = [t.isoformat() for t in times]
    
    # データの組み立て
    data = []
    for i in range(n_points):
        data.append({
            direction_key: float(directions[i]),
            value_key: float(speeds[i]),
            time_key: times_iso[i]
        })
    
    return data


def _generate_polar_diagram_sample(properties: Dict[str, Any]) -> Dict[str, Any]:
    """
    ポーラーダイアグラムのサンプルデータを生成

    Parameters
    ----------
    properties : Dict[str, Any]
        チャート要素のプロパティ

    Returns
    -------
    Dict[str, Any]
        生成されたサンプルデータ
    """
    import numpy as np
    
    # 風速リストを取得
    wind_speeds = properties.get("wind_speeds", [5, 10, 15, 20])
    
    # ボートの速度特性を表現する関数
    def calc_boat_speed(wind_speed, angle_deg):
        # 0-180度の範囲に正規化（対称性を利用）
        norm_angle = abs(angle_deg % 360)
        if norm_angle > 180:
            norm_angle = 360 - norm_angle
        
        # ボートの特性を模擬（単純な数式モデル）
        if 0 <= norm_angle < 30:  # 風上不能領域
            factor = norm_angle / 30.0
            return wind_speed * 0.4 * factor
        elif 30 <= norm_angle < 60:  # 風上クローズホールド
            factor = (norm_angle - 30) / 30.0
            return wind_speed * (0.4 + factor * 0.3)
        elif 60 <= norm_angle < 100:  # ビーム～リーチ
            factor = (norm_angle - 60) / 40.0
            base = wind_speed * 0.7
            peak = wind_speed * 0.9
            return base + (peak - base) * factor
        elif 100 <= norm_angle < 150:  # ブロードリーチ
            factor = (norm_angle - 100) / 50.0
            return wind_speed * (0.9 - factor * 0.1)
        else:  # ランニング
            factor = (norm_angle - 150) / 30.0
            return wind_speed * (0.8 - factor * 0.2)
    
    # VMGを計算
    def calc_vmg(speed, angle_deg):
        angle_rad = np.radians(angle_deg)
        return speed * np.cos(angle_rad)
    
    # 0-360度を5度刻みで
    angles = list(range(0, 360, 5))
    
    # 結果を格納
    result = {
        "target": {},
        "actual": {},
        "vmg": {}
    }
    
    for wind in wind_speeds:
        wind_key = f"wind_{wind}"
        result["target"][wind_key] = {}
        result["actual"][wind_key] = {}
        
        # 各角度でのボート速度を計算
        for angle in angles:
            # ターゲット速度（理想値）
            target_speed = calc_boat_speed(wind, angle)
            result["target"][wind_key][f"{angle}°"] = target_speed
            
            # 実測速度（ランダムな変動を加える）
            variation = np.random.uniform(0.8, 1.1)
            actual_speed = target_speed * variation
            result["actual"][wind_key][f"{angle}°"] = actual_speed
    
    # VMGの最適値を計算
    result["vmg"] = {}
    for wind in wind_speeds:
        wind_key = f"wind_{wind}"
        result["vmg"][wind_key] = {
            "upwind": {},
            "downwind": {}
        }
        
        # 上り・下りの全角度でVMGを計算
        upwind_angles = list(range(30, 90, 5))
        downwind_angles = list(range(120, 180, 5))
        
        upwind_vmgs = []
        for angle in upwind_angles:
            target_speed = result["target"][wind_key][f"{angle}°"]
            vmg = calc_vmg(target_speed, angle)
            upwind_vmgs.append((angle, vmg, target_speed))
        
        downwind_vmgs = []
        for angle in downwind_angles:
            target_speed = result["target"][wind_key][f"{angle}°"]
            vmg = -calc_vmg(target_speed, angle)  # 下りは逆向き
            downwind_vmgs.append((angle, vmg, target_speed))
        
        # 最適VMGを選択
        best_upwind = max(upwind_vmgs, key=lambda x: x[1])
        best_downwind = max(downwind_vmgs, key=lambda x: x[1])
        
        # 結果を保存
        result["vmg"][wind_key]["upwind"] = {
            "angle": best_upwind[0],
            "vmg": best_upwind[1],
            "speed": best_upwind[2]
        }
        
        result["vmg"][wind_key]["downwind"] = {
            "angle": best_downwind[0],
            "vmg": best_downwind[1],
            "speed": best_downwind[2]
        }
    
    return result


def _generate_tacking_angle_sample(properties: Dict[str, Any]) -> Dict[str, Any]:
    """
    タッキングアングル分析のサンプルデータを生成

    Parameters
    ----------
    properties : Dict[str, Any]
        チャート要素のプロパティ

    Returns
    -------
    Dict[str, Any]
        生成されたサンプルデータ
    """
    import numpy as np
    
    # フィールド名を取得
    angle_key = properties.get("angle_key", "tacking_angle")
    
    # 角度範囲を取得
    min_angle = properties.get("min_angle", 70)
    max_angle = properties.get("max_angle", 140)
    optimal_min = properties.get("optimal_min", 85)
    optimal_max = properties.get("optimal_max", 95)
    
    # サンプルデータの生成
    n_points = 100
    
    # 最適範囲に集中するような分布を生成
    optimal_center = (optimal_min + optimal_max) / 2
    optimal_std = (optimal_max - optimal_min) / 3
    
    # 70%は最適範囲周辺、30%は広い範囲でランダム
    optimal_angles = np.random.normal(optimal_center, optimal_std, int(n_points * 0.7))
    random_angles = np.random.uniform(min_angle, max_angle, n_points - len(optimal_angles))
    
    angles = np.concatenate([optimal_angles, random_angles])
    angles = np.clip(angles, min_angle, max_angle)  # 範囲内に収める
    
    # データの組み立て（リスト形式とDict形式の両方に対応）
    data_list = list(angles)
    
    data_dict = []
    for angle in angles:
        data_dict.append({
            angle_key: float(angle)
        })
    
    # properties内のデータ形式に基づいて返す
    if properties.get("data_format", "dict") == "list":
        return data_list
    else:
        return data_dict


def _generate_course_performance_sample(properties: Dict[str, Any]) -> Dict[str, Any]:
    """
    コースパフォーマンスグラフのサンプルデータを生成

    Parameters
    ----------
    properties : Dict[str, Any]
        チャート要素のプロパティ

    Returns
    -------
    Dict[str, Any]
        生成されたサンプルデータ
    """
    import numpy as np
    
    # フィールド名を取得
    label_field = properties.get("label_field", "angle")
    value_field = properties.get("value_field", "speed")
    series_field = properties.get("series_field", "type")
    
    # 角度分割数を取得
    angle_divisions = properties.get("angle_divisions", 36)
    
    # 角度リストを生成
    angles = np.linspace(0, 360, angle_divisions, endpoint=False)
    
    # ボートの速度特性を表現する関数
    def calc_boat_speed(angle_deg, is_target=True):
        # 0-180度の範囲に正規化（対称性を利用）
        norm_angle = abs(angle_deg % 360)
        if norm_angle > 180:
            norm_angle = 360 - norm_angle
        
        # 基本的な速度プロファイル
        if norm_angle < 45:
            speed = 4 + norm_angle * 0.05
        elif norm_angle < 90:
            speed = 6 + (norm_angle - 45) * 0.02
        elif norm_angle < 135:
            speed = 7 - (norm_angle - 90) * 0.01
        else:
            speed = 6.5 - (norm_angle - 135) * 0.02
        
        # 実測値の場合はばらつきを加える
        if not is_target:
            speed *= np.random.uniform(0.85, 1.1)
        
        return speed
    
    # VMGを計算
    def calc_vmg(speed, angle_deg):
        angle_rad = np.radians(angle_deg)
        return speed * np.cos(angle_rad)
    
    # データを生成
    actual_data = []
    target_data = []
    vmg_data = []
    
    for angle in angles:
        target_speed = calc_boat_speed(angle, True)
        actual_speed = calc_boat_speed(angle, False)
        vmg_value = calc_vmg(actual_speed, angle)
        
        actual_data.append({
            label_field: float(angle),
            value_field: float(actual_speed),
            series_field: "実績"
        })
        
        target_data.append({
            label_field: float(angle),
            value_field: float(target_speed),
            series_field: "ターゲット"
        })
        
        # VMGは上り下りの場合のみ意味があるので、フィルタリング
        if 0 <= angle < 90 or 270 <= angle < 360:
            vmg_data.append({
                label_field: float(angle),
                value_field: abs(float(vmg_value)),
                series_field: "VMG"
            })
    
    # すべてのデータを結合
    data = actual_data + target_data + vmg_data
    
    return data


@contextmanager
def chart_preview_container(title: str = "チャートプレビュー", width: str = "100%", height: str = "500px"):
    """
    チャートプレビュー用のコンテナを提供するコンテキストマネージャ

    Parameters
    ----------
    title : str, optional
        コンテナのタイトル, by default "チャートプレビュー"
    width : str, optional
        コンテナの幅, by default "100%"
    height : str, optional
        コンテナの高さ, by default "500px"
    """
    st.subheader(title)
    
    # スタイル設定
    preview_style = f"width: {width}; height: {height}; border: 1px solid #ddd; padding: 10px; border-radius: 5px;"
    st.markdown(f'<div style="{preview_style}">', unsafe_allow_html=True)
    
    # コンテキストを提供
    yield
    
    # コンテナを閉じる
    st.markdown('</div>', unsafe_allow_html=True)
