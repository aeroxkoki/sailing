"""
ui.demo_timeline

イベントタイムラインとパラメータタイムラインのデモアプリケーションです。
セーリングデータの時系列分析を行うUIコンポーネントの動作を確認できます。
"""

import streamlit as st
import numpy as np
import pandas as pd
import json
from datetime import datetime, timedelta
import uuid
import os
import sys
import math

# パスの追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sailing_data_processor.reporting.elements.timeline.event_timeline import EventTimeline
from sailing_data_processor.reporting.elements.timeline.parameter_timeline import ParameterTimeline
from ui.components.reporting.timeline.timeline_properties_panel import timeline_properties_panel


def main():
    """
    メイン関数
    """
    st.set_page_config(
        page_title="タイムラインデモ",
        page_icon="⏱️",
        layout="wide"
    )
    
    st.title("タイムラインデモ")
    st.markdown("""
    セーリングデータのタイムライン表示コンポーネントのデモです。
    以下の要素を試せます:
    
    - イベントタイムライン: タック、ジャイブなどのイベントを時間軸上に表示
    - パラメータタイムライン: 速度、風速、風向などのデータを時間軸上にグラフ表示
    - タイムラインの連携: 複数のタイムラインを連動させる
    """)
    
    # サンプルデータを生成
    sample_data = generate_sample_data()
    
    # タブを作成
    tabs = st.tabs(["イベントタイムライン", "パラメータタイムライン", "連携表示"])
    
    # イベントタイムラインタブ
    with tabs[0]:
        render_event_timeline_demo(sample_data)
    
    # パラメータタイムラインタブ
    with tabs[1]:
        render_parameter_timeline_demo(sample_data)
    
    # 連携表示タブ
    with tabs[2]:
        render_combined_timeline_demo(sample_data)
    
    st.markdown("---")
    st.markdown("### サンプルデータ")
    
    with st.expander("サンプルデータの内容"):
        st.dataframe(pd.DataFrame(sample_data))


def generate_sample_data() -> dict:
    """
    サンプルデータを生成
    
    Returns
    -------
    dict
        サンプルデータ
    """
    # データポイント数
    n_points = 200
    
    # 基準時刻 (2023/04/01 13:00:00)
    base_time = datetime(2023, 4, 1, 13, 0, 0)
    
    # 時間データ (5秒間隔)
    timestamps = [base_time + timedelta(seconds=i*5) for i in range(n_points)]
    timestamps_str = [ts.isoformat() for ts in timestamps]
    
    # 速度データ (基本速度 + 波形変動 + ランダムノイズ)
    base_speed = 4.0  # 基本速度 (kt)
    speed_variation = np.sin(np.linspace(0, 4*np.pi, n_points)) * 1.5  # 波形変動
    speed_noise = np.random.normal(0, 0.3, n_points)  # ランダムノイズ
    speed = base_speed + speed_variation + speed_noise
    speed = np.clip(speed, 0, 10)  # 0～10ktの範囲に制限
    
    # 風速データ
    base_wind_speed = 12.0  # 基本風速 (kt)
    wind_speed_variation = np.sin(np.linspace(0, 2*np.pi, n_points)) * 2.0
    wind_speed_noise = np.random.normal(0, 0.5, n_points)
    wind_speed = base_wind_speed + wind_speed_variation + wind_speed_noise
    wind_speed = np.clip(wind_speed, 5, 20)  # 5～20ktの範囲に制限
    
    # 風向データ
    base_wind_dir = 45.0  # 基本風向 (°)
    wind_dir_variation = np.sin(np.linspace(0, 3*np.pi, n_points)) * 15.0
    wind_dir_noise = np.random.normal(0, 3.0, n_points)
    wind_direction = (base_wind_dir + wind_dir_variation + wind_dir_noise) % 360
    
    # 艇首方位データ
    # タックごとに約180度変化するようにする
    heading_base = np.zeros(n_points)
    tack_points = [0, 40, 85, 130, 170]  # タックするポイント
    current_heading = 320.0
    
    for i in range(len(tack_points)-1):
        start_idx = tack_points[i]
        end_idx = tack_points[i+1]
        heading_base[start_idx:end_idx] = current_heading
        current_heading = (current_heading + 180) % 360  # 約180度変化
    
    heading_noise = np.random.normal(0, 2.0, n_points)
    heading = (heading_base + heading_noise) % 360
    
    # ヒール角データ
    heel_base = np.abs(np.sin(np.linspace(0, 6*np.pi, n_points))) * 15.0
    heel_noise = np.random.normal(0, 1.0, n_points)
    heel = heel_base + heel_noise
    heel = np.clip(heel, 0, 30)  # 0～30度の範囲に制限
    
    # VMG (Velocity Made Good)
    # 風上/風下方向の速度成分
    wind_angle = np.abs((wind_direction - heading) % 360)
    wind_angle = np.minimum(wind_angle, 360 - wind_angle)  # 0～180度に正規化
    vmg = speed * np.cos(np.radians(wind_angle))
    
    # イベントデータを生成 (タック、ジャイブ、マーク回航)
    is_tack = np.zeros(n_points, dtype=bool)
    is_jibe = np.zeros(n_points, dtype=bool)
    is_mark_rounding = np.zeros(n_points, dtype=bool)
    
    # タックポイントを設定
    for point in tack_points[1:]:
        is_tack[point] = True
    
    # ジャイブポイントを設定
    jibe_points = [20, 60, 100, 150]
    for point in jibe_points:
        is_jibe[point] = True
    
    # マーク回航ポイントを設定
    mark_points = [30, 120, 180]
    for point in mark_points:
        is_mark_rounding[point] = True
    
    # スタート/フィニッシュポイント
    is_start = np.zeros(n_points, dtype=bool)
    is_finish = np.zeros(n_points, dtype=bool)
    is_start[0] = True
    is_finish[n_points-1] = True
    
    # データを辞書に集約
    data = {
        "timestamp": timestamps_str,
        "speed": speed.tolist(),
        "wind_speed": wind_speed.tolist(),
        "wind_direction": wind_direction.tolist(),
        "heading": heading.tolist(),
        "heel": heel.tolist(),
        "vmg": vmg.tolist(),
        "is_tack": is_tack.tolist(),
        "is_jibe": is_jibe.tolist(),
        "is_mark_rounding": is_mark_rounding.tolist(),
        "is_start": is_start.tolist(),
        "is_finish": is_finish.tolist()
    }
    
    return data


def render_event_timeline_demo(data: dict):
    """
    イベントタイムラインのデモ表示
    
    Parameters
    ----------
    data : dict
        サンプルデータ
    """
    st.header("イベントタイムライン")
    
    # イベントタイムラインを作成
    event_timeline = create_event_timeline(data)
    
    # 2カラムレイアウト
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # イベントタイムラインのHTMLを表示
        st.subheader("タイムライン表示")
        html = event_timeline.render({"data": data})
        st.components.v1.html(html, height=event_timeline.get_property("timeline_height", 150) + 100)
    
    with col2:
        # プロパティを表示
        st.subheader("プロパティ")
        
        # プロパティの変更ハンドラを定義
        def handle_property_change(changes):
            # 変更されたプロパティを適用
            for key, value in changes.items():
                event_timeline.set_property(key, value)
            
            # 再描画が必要なことを示す
            st.session_state.event_timeline_updated = True
        
        # プロパティパネルを表示
        timeline_properties_panel(event_timeline, handle_property_change, "event_timeline")
        
        # 変更があった場合、再描画ボタンを表示
        if st.session_state.get("event_timeline_updated", False):
            if st.button("変更を適用して再描画", key="redraw_event_timeline"):
                st.session_state.event_timeline_updated = False
                st.experimental_rerun()


def render_parameter_timeline_demo(data: dict):
    """
    パラメータタイムラインのデモ表示
    
    Parameters
    ----------
    data : dict
        サンプルデータ
    """
    st.header("パラメータタイムライン")
    
    # パラメータタイムラインを作成
    param_timeline = create_parameter_timeline(data)
    
    # 2カラムレイアウト
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # パラメータタイムラインのHTMLを表示
        st.subheader("タイムライン表示")
        html = param_timeline.render({"data": data})
        st.components.v1.html(html, height=param_timeline.get_property("timeline_height", 300) + 200)
    
    with col2:
        # プロパティを表示
        st.subheader("プロパティ")
        
        # プロパティの変更ハンドラを定義
        def handle_property_change(changes):
            # 変更されたプロパティを適用
            for key, value in changes.items():
                param_timeline.set_property(key, value)
            
            # 再描画が必要なことを示す
            st.session_state.param_timeline_updated = True
        
        # プロパティパネルを表示
        timeline_properties_panel(param_timeline, handle_property_change, "param_timeline")
        
        # 変更があった場合、再描画ボタンを表示
        if st.session_state.get("param_timeline_updated", False):
            if st.button("変更を適用して再描画", key="redraw_param_timeline"):
                st.session_state.param_timeline_updated = False
                st.experimental_rerun()


def render_combined_timeline_demo(data: dict):
    """
    イベントタイムラインとパラメータタイムラインの連携表示
    
    Parameters
    ----------
    data : dict
        サンプルデータ
    """
    st.header("タイムライン連携表示")
    
    # タイムラインを作成
    event_timeline = create_event_timeline(data)
    param_timeline = create_parameter_timeline(data)
    
    # サイズを調整
    event_timeline.set_property("timeline_height", 120)
    param_timeline.set_property("timeline_height", 250)
    
    # 連携用のJavaScriptを生成
    js_link = f"""
    <script>
        document.addEventListener('timelineEventSelect', function(e) {{
            // イベント選択時の処理
            console.log('Event selected:', e.detail);
            
            // イベントの時間を取得
            var eventTime = new Date(e.detail.event.timestamp);
            
            // パラメータタイムラインのChart.jsインスタンスを取得
            var paramChart = window['{param_timeline.element_id}_chart'];
            if (paramChart) {{
                // イベント周辺時間の範囲を表示
                var min = new Date(eventTime.getTime() - 60000);  // 1分前
                var max = new Date(eventTime.getTime() + 60000);  // 1分後
                
                paramChart.scales.x.options.min = min;
                paramChart.scales.x.options.max = max;
                paramChart.update();
            }}
        }});
    </script>
    """
    
    # イベントタイムライン表示
    st.subheader("イベントタイムライン")
    event_html = event_timeline.render({"data": data})
    st.components.v1.html(event_html, height=event_timeline.get_property("timeline_height", 120) + 50)
    
    # パラメータタイムライン表示
    st.subheader("パラメータタイムライン")
    param_html = param_timeline.render({"data": data})
    st.components.v1.html(param_html + js_link, height=param_timeline.get_property("timeline_height", 250) + 200)
    
    st.info("""
    **連携動作の説明**: 
    
    上のイベントタイムラインで任意のイベント（タック・ジャイブなど）をクリックすると、
    下のパラメータタイムラインが該当イベント前後の時間（±1分）にズームします。
    
    これにより、特定のイベント周辺のパラメータ変化を詳細に確認できます。
    """)


def create_event_timeline(data: dict) -> EventTimeline:
    """
    イベントタイムラインを作成
    
    Parameters
    ----------
    data : dict
        サンプルデータ
        
    Returns
    -------
    EventTimeline
        作成されたイベントタイムライン
    """
    # タイムラインを作成
    timeline = EventTimeline(name="セーリングイベント")
    
    # データソースを設定
    timeline.set_property("data_source", "data")
    
    # イベントタイプとフィールドの対応を設定
    timeline.set_property("event_type_fields", {
        "tack": "is_tack",
        "jibe": "is_jibe",
        "mark_rounding": "is_mark_rounding",
        "start": "is_start",
        "finish": "is_finish"
    })
    
    # ポップアップ表示の詳細フィールドを設定
    timeline.set_property("detail_fields", [
        "speed", "wind_speed", "wind_direction", "heading"
    ])
    
    return timeline


def create_parameter_timeline(data: dict) -> ParameterTimeline:
    """
    パラメータタイムラインを作成
    
    Parameters
    ----------
    data : dict
        サンプルデータ
        
    Returns
    -------
    ParameterTimeline
        作成されたパラメータタイムライン
    """
    # タイムラインを作成
    timeline = ParameterTimeline(name="セーリングパラメータ")
    
    # データソースを設定
    timeline.set_property("data_source", "data")
    
    # 表示するパラメータを設定
    timeline.set_property("show_speed", True)
    timeline.set_property("show_wind_speed", True)
    timeline.set_property("show_wind_direction", True)
    timeline.set_property("show_heading", False)
    timeline.set_property("show_heel", False)
    timeline.set_property("show_vmg", False)
    
    # 表示設定を設定
    timeline.set_property("show_statistics", True)
    timeline.set_property("show_trends", True)
    timeline.set_property("line_style", "spline")
    
    return timeline


if __name__ == "__main__":
    main()
