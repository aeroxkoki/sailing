"""
風推定モジュールページ

このモジュールは風向風速の推定と表示を行うためのStreamlitページを提供します。
GPSデータから風の状況を推定し、その結果を視覚化します。
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import folium
from folium.plugins import HeatMap
from streamlit_folium import folium_static
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Any, Optional

from sailing_data_processor.analysis.analysis_parameters import ParametersManager, ParameterNamespace
from sailing_data_processor.analysis.integrated_wind_estimator import IntegratedWindEstimator
from sailing_data_processor.analysis.analysis_cache import AnalysisCache
from ui.components.workflow_components import parameter_adjustment_panel
from ui.integrated.controllers.workflow_controller import IntegratedWorkflowController


# ロガーの設定
logger = logging.getLogger(__name__)


def display_wind_rose(wind_data: Dict[str, Any]) -> None:
    """
    風配図の表示
    
    Parameters:
    -----------
    wind_data : Dict[str, Any]
        風データ（方向と風速を含む）
    """
    # 風データの検証
    if not wind_data or "wind" not in wind_data:
        st.warning("有効な風データがありません。")
        return
    
    wind_info = wind_data.get("wind", {})
    direction = wind_info.get("direction")
    speed = wind_info.get("speed")
    
    if direction is None or speed is None:
        st.warning("風向または風速のデータがありません。")
        return
    
    # 風配図の作成
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    
    # 方位角（0度が北、時計回りに増加）
    theta = np.radians(90 - direction)  # matplotlib極座標は0度が東、反時計回りなので変換
    
    # 矢印の長さは風速に比例
    r = speed
    
    # 風向きの矢印を描画（風は「風が吹いてくる方向」を示す）
    ax.annotate("", xy=(theta, r), xytext=(theta, 0),
                arrowprops=dict(facecolor='red', width=2, headwidth=10))
    
    # 風速を表示
    ax.text(theta, r/2, f"{speed:.1f} knots", 
            ha='center', va='center', fontsize=12,
            bbox=dict(facecolor='white', alpha=0.7))
    
    # 方位の設定
    ax.set_theta_zero_location("N")  # 0度を北に設定
    ax.set_theta_direction(-1)  # 時計回りに角度が増加
    
    # 目盛りの設定
    ax.set_thetagrids([0, 45, 90, 135, 180, 225, 270, 315], 
                       ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'])
    
    max_r = max(10, speed * 1.2)  # 最大風速の1.2倍かつ最低10ノットを確保
    ax.set_rticks([max_r/4, max_r/2, 3*max_r/4, max_r])
    ax.set_rlim(0, max_r)
    
    ax.set_title("風向風速", fontsize=16)
    ax.grid(True)
    
    # プロットの表示
    st.pyplot(fig)


def display_wind_time_series(time_series_data: List[Dict[str, Any]]) -> None:
    """
    風の時系列データを表示
    
    Parameters:
    -----------
    time_series_data : List[Dict[str, Any]]
        時系列の風データ
    """
    if not time_series_data:
        st.warning("時系列風データがありません。")
        return
    
    # データの抽出
    timestamps = []
    directions = []
    speeds = []
    
    for data_point in time_series_data:
        if "timestamp" in data_point and "direction" in data_point and "speed" in data_point:
            timestamps.append(data_point["timestamp"])
            directions.append(data_point["direction"])
            speeds.append(data_point["speed"])
    
    if not timestamps:
        st.warning("時系列データが不足しています。")
        return
    
    # DataFrameの作成
    df = pd.DataFrame({
        "timestamp": timestamps,
        "direction": directions,
        "speed": speeds
    })
    
    # Plotlyでインタラクティブなグラフを作成
    fig = go.Figure()
    
    # 風速のグラフ
    fig.add_trace(go.Scatter(
        x=df["timestamp"],
        y=df["speed"],
        mode='lines+markers',
        name='風速 (ノット)',
        line=dict(color='blue', width=2),
        hovertemplate='時刻: %{x}<br>風速: %{y:.1f} ノット<extra></extra>'
    ))
    
    # 風向のグラフ（別の軸）
    fig.add_trace(go.Scatter(
        x=df["timestamp"],
        y=df["direction"],
        mode='lines+markers',
        name='風向 (度)',
        line=dict(color='red', width=2, dash='dot'),
        hovertemplate='時刻: %{x}<br>風向: %{y:.1f}°<extra></extra>',
        yaxis='y2'
    ))
    
    # レイアウトの設定
    fig.update_layout(
        title='風の時系列変化',
        xaxis=dict(title='時刻'),
        yaxis=dict(
            title='風速 (ノット)',
            titlefont=dict(color='blue'),
            tickfont=dict(color='blue')
        ),
        yaxis2=dict(
            title='風向 (度)',
            titlefont=dict(color='red'),
            tickfont=dict(color='red'),
            anchor='x',
            overlaying='y',
            side='right',
            range=[0, 360]
        ),
        hovermode='x unified',
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        )
    )
    
    # グラフの表示
    st.plotly_chart(fig, use_container_width=True)


def display_wind_map(df: pd.DataFrame, wind_data: Dict[str, Any]) -> None:
    """
    GPSトラックと風向を地図上に表示
    
    Parameters:
    -----------
    df : pd.DataFrame
        GPSデータを含むデータフレーム
    wind_data : Dict[str, Any]
        風データ
    """
    if df is None or df.empty:
        st.warning("GPSデータがありません。")
        return
    
    # 中心位置の計算
    center_lat = df["latitude"].mean()
    center_lon = df["longitude"].mean()
    
    # 地図の作成
    m = folium.Map(location=[center_lat, center_lon], zoom_start=15)
    
    # GPSトラックの描画
    track_coords = [[row["latitude"], row["longitude"]] for _, row in df.iterrows()]
    folium.PolyLine(
        track_coords,
        color="blue",
        weight=3,
        opacity=0.7,
        tooltip="航路"
    ).add_to(m)
    
    # 開始点と終了点のマーカー
    folium.Marker(
        [df["latitude"].iloc[0], df["longitude"].iloc[0]],
        popup="開始",
        icon=folium.Icon(color="green", icon="play")
    ).add_to(m)
    
    folium.Marker(
        [df["latitude"].iloc[-1], df["longitude"].iloc[-1]],
        popup="終了",
        icon=folium.Icon(color="red", icon="stop")
    ).add_to(m)
    
    # 風向を表示
    if wind_data and "wind" in wind_data:
        wind_info = wind_data["wind"]
        wind_direction = wind_info.get("direction")
        wind_speed = wind_info.get("speed")
        
        if wind_direction is not None and wind_speed is not None:
            # 風向矢印のアイコンを作成
            wind_icon_html = f"""
            <div style="
                width: 60px;
                height: 60px;
                position: relative;
                background-color: rgba(255, 255, 255, 0.7);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
            ">
                <div style="
                    transform: rotate({wind_direction}deg);
                    font-size: 30px;
                    color: red;
                ">↑</div>
                <div style="
                    position: absolute;
                    bottom: 0;
                    font-size: 10px;
                    font-weight: bold;
                ">{wind_speed:.1f}kn</div>
            </div>
            """
            
            # 風向アイコンを地図に追加
            folium.Marker(
                [center_lat, center_lon],
                popup=f"風向: {wind_direction}°, 風速: {wind_speed}ノット",
                icon=folium.DivIcon(html=wind_icon_html)
            ).add_to(m)
    
    # 地図の表示
    folium_static(m)


def display_maneuvers(maneuvers: List[Dict[str, Any]], df: pd.DataFrame) -> None:
    """
    検出されたマニューバーの表示
    
    Parameters:
    -----------
    maneuvers : List[Dict[str, Any]]
        検出されたマニューバーのリスト
    df : pd.DataFrame
        GPSデータを含むデータフレーム
    """
    if not maneuvers:
        st.info("マニューバーは検出されませんでした。")
        return
    
    st.subheader(f"検出されたマニューバー ({len(maneuvers)}件)")
    
    # マニューバーデータをDataFrameに変換
    maneuver_df = pd.DataFrame(maneuvers)
    
    # 不要な列の削除
    display_columns = [
        "maneuver_type", "start_time", "end_time", "duration_seconds", 
        "start_heading", "end_heading", "heading_change", 
        "start_speed", "min_speed", "end_speed", "speed_loss_percentage"
    ]
    
    # 表示用の列名マッピング
    column_labels = {
        "maneuver_type": "タイプ",
        "start_time": "開始時間",
        "end_time": "終了時間",
        "duration_seconds": "所要時間(秒)",
        "start_heading": "開始進路",
        "end_heading": "終了進路",
        "heading_change": "進路変化",
        "start_speed": "開始速度",
        "min_speed": "最低速度",
        "end_speed": "終了速度",
        "speed_loss_percentage": "速度損失(%)"
    }
    
    # 存在する列のみ選択
    display_columns = [col for col in display_columns if col in maneuver_df.columns]
    
    # 表示用にデータフレームを整形
    display_df = maneuver_df[display_columns].copy()
    
    # 列名の日本語化
    display_df.columns = [column_labels.get(col, col) for col in display_df.columns]
    
    # 時間列のフォーマット
    if "開始時間" in display_df.columns and pd.api.types.is_datetime64_any_dtype(display_df["開始時間"]):
        display_df["開始時間"] = display_df["開始時間"].dt.strftime("%H:%M:%S")
    
    if "終了時間" in display_df.columns and pd.api.types.is_datetime64_any_dtype(display_df["終了時間"]):
        display_df["終了時間"] = display_df["終了時間"].dt.strftime("%H:%M:%S")
    
    # パーセント表示の整形
    if "速度損失(%)" in display_df.columns:
        display_df["速度損失(%)"] = display_df["速度損失(%)"].apply(lambda x: f"{x*100:.1f}" if pd.notnull(x) else "-")
    
    # 角度表示の整形
    for col in ["開始進路", "終了進路", "進路変化"]:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(lambda x: f"{x:.1f}°" if pd.notnull(x) else "-")
    
    # 速度表示の整形
    for col in ["開始速度", "最低速度", "終了速度"]:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(lambda x: f"{x:.1f}kn" if pd.notnull(x) else "-")
    
    # タイプの翻訳
    type_mapping = {
        "tack": "タック",
        "gybe": "ジャイブ",
        "unknown": "不明"
    }
    
    if "タイプ" in display_df.columns:
        display_df["タイプ"] = display_df["タイプ"].map(lambda x: type_mapping.get(x, x))
    
    # 時間の書式整形
    if "所要時間(秒)" in display_df.columns:
        display_df["所要時間(秒)"] = display_df["所要時間(秒)"].apply(lambda x: f"{x:.1f}" if pd.notnull(x) else "-")
    
    # データフレームの表示
    st.dataframe(display_df.head(10))
    
    # 全データの表示（展開可能）
    if len(display_df) > 10:
        with st.expander("すべてのマニューバーを表示", expanded=False):
            st.dataframe(display_df)
    
    # マニューバー地点を地図上に表示
    if "latitude" in maneuver_df.columns and "longitude" in maneuver_df.columns:
        st.subheader("マニューバーマップ")
        
        # 中心位置の計算
        center_lat = df["latitude"].mean() if not df.empty else maneuver_df["latitude"].mean()
        center_lon = df["longitude"].mean() if not df.empty else maneuver_df["longitude"].mean()
        
        # 地図の作成
        m = folium.Map(location=[center_lat, center_lon], zoom_start=15)
        
        # トラックの描画（データフレームがある場合）
        if not df.empty and "latitude" in df.columns and "longitude" in df.columns:
            track_coords = [[row["latitude"], row["longitude"]] for _, row in df.iterrows()]
            folium.PolyLine(
                track_coords,
                color="blue",
                weight=2,
                opacity=0.5,
                tooltip="航路"
            ).add_to(m)
        
        # マニューバーポイントの追加
        for _, row in maneuver_df.iterrows():
            if pd.notnull(row.get("latitude")) and pd.notnull(row.get("longitude")):
                # マニューバータイプに応じたアイコン色
                icon_color = "green" if row.get("maneuver_type") == "tack" else "orange"
                icon_name = "random" if row.get("maneuver_type") == "tack" else "refresh"
                
                # ポップアップテキストの作成
                popup_text = f"タイプ: {type_mapping.get(row.get('maneuver_type'), '不明')}<br>"
                if "start_time" in row and pd.notnull(row["start_time"]):
                    popup_text += f"時間: {row['start_time'].strftime('%H:%M:%S') if isinstance(row['start_time'], pd.Timestamp) else row['start_time']}<br>"
                if "duration_seconds" in row and pd.notnull(row["duration_seconds"]):
                    popup_text += f"所要時間: {row['duration_seconds']:.1f}秒<br>"
                if "heading_change" in row and pd.notnull(row["heading_change"]):
                    popup_text += f"進路変化: {row['heading_change']:.1f}°<br>"
                if "speed_loss_percentage" in row and pd.notnull(row["speed_loss_percentage"]):
                    popup_text += f"速度損失: {row['speed_loss_percentage']*100:.1f}%"
                
                # マーカー追加
                folium.Marker(
                    [row["latitude"], row["longitude"]],
                    popup=folium.Popup(popup_text, max_width=200),
                    icon=folium.Icon(color=icon_color, icon=icon_name)
                ).add_to(m)
        
        # 地図の表示
        folium_static(m)


def estimate_wind_from_df(df: pd.DataFrame, params_manager: ParametersManager) -> Dict[str, Any]:
    """
    データフレームから風を推定
    
    Parameters:
    -----------
    df : pd.DataFrame
        GPSデータを含むデータフレーム
    params_manager : ParametersManager
        パラメータ管理オブジェクト
        
    Returns:
    --------
    Dict[str, Any]
        風推定結果
    """
    # 必須カラムの確認
    required_cols = ["timestamp", "latitude", "longitude", "course", "speed"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        return {
            "error": f"データに必須カラムがありません: {', '.join(missing_cols)}",
            "wind": {
                "direction": None,
                "speed": None,
                "confidence": 0
            }
        }
    
    try:
        # 風推定モジュールのインスタンス化
        cache = AnalysisCache()
        estimator = IntegratedWindEstimator(params_manager, cache)
        
        # 風の推定
        result = estimator.estimate_wind(df)
        
        return result
    except Exception as e:
        logger.exception(f"風推定中にエラーが発生しました: {str(e)}")
        return {
            "error": f"風推定エラー: {str(e)}",
            "wind": {
                "direction": None,
                "speed": None,
                "confidence": 0
            }
        }


def wind_estimation_page() -> None:
    """
    風推定ページのメインエントリーポイント
    """
    st.title("風向風速推定")
    
    # セッションデータの取得
    session_data = st.session_state.get('session_data', {})
    
    # 選択されたセッションの情報表示
    current_session = session_data.get('current_session')
    
    if current_session and 'current_session_df' in session_data:
        st.subheader(f"セッション: {current_session.get('name', '名称未設定')}")
        
        # パラメータマネージャーの取得または作成
        params_manager = session_data.get('params_manager')
        if params_manager is None:
            params_manager = ParametersManager()
            session_data['params_manager'] = params_manager
        
        # データフレームの取得
        df = session_data['current_session_df']
        
        if df is None or df.empty:
            st.warning("データが選択されていないか、空です。")
            return
        
        # パラメータ調整と風推定
        with st.expander("風推定パラメータ", expanded=False):
            st.write("風向風速を推定するためのパラメータを調整できます。")
            
            # パラメータ調整パネル
            wind_params = parameter_adjustment_panel(
                params_manager, 
                ParameterNamespace.WIND_ESTIMATION
            )
        
        # 風推定実行ボタン
        col1, col2 = st.columns([1, 1])
        
        with col1:
            estimate_button = st.button("風向風速を推定", key="estimate_wind", use_container_width=True)
        
        with col2:
            # ワークフローから結果を取得するオプション
            if 'workflow_controller' in st.session_state:
                workflow_button = st.button(
                    "ワークフローから結果を取得", 
                    key="get_from_workflow",
                    use_container_width=True
                )
            else:
                workflow_button = False
                st.info("ワークフローの結果を使用するには、最初にワークフローページで分析を実行してください。")
        
        # 風推定結果のキャッシュ
        if 'wind_result' not in st.session_state:
            st.session_state.wind_result = None
        
        # 風推定の実行
        if estimate_button:
            with st.spinner("風向風速を推定中..."):
                wind_result = estimate_wind_from_df(df, params_manager)
                st.session_state.wind_result = wind_result
                
                # 成功メッセージまたはエラーメッセージ
                if "error" in wind_result:
                    st.error(wind_result["error"])
                else:
                    wind_info = wind_result.get("wind", {})
                    st.success(
                        f"風向風速の推定が完了しました。"
                        f"風向: {wind_info.get('direction', 0):.1f}°, "
                        f"風速: {wind_info.get('speed', 0):.1f}ノット, "
                        f"信頼度: {wind_info.get('confidence', 0):.2f}"
                    )
        
        # ワークフローからの結果取得
        elif workflow_button:
            if 'workflow_controller' in st.session_state:
                workflow_controller = st.session_state.workflow_controller
                
                # 結果の取得
                results = workflow_controller.get_results()
                
                if "wind_result" in results:
                    st.session_state.wind_result = results["wind_result"]
                    
                    # 成功メッセージ
                    wind_info = results["wind_result"].get("wind", {})
                    st.success(
                        f"ワークフローから風向風速を取得しました。"
                        f"風向: {wind_info.get('direction', 0):.1f}°, "
                        f"風速: {wind_info.get('speed', 0):.1f}ノット, "
                        f"信頼度: {wind_info.get('confidence', 0):.2f}"
                    )
                else:
                    st.warning("ワークフローに風推定結果が見つかりません。ワークフローを実行してください。")
        
        # 結果の表示
        wind_result = st.session_state.wind_result
        
        if wind_result:
            # 結果を複数のセクションに分けて表示
            tabs = st.tabs(["風の概要", "風配図", "マニューバー", "地図", "時系列データ"])
            
            # 風の概要タブ
            with tabs[0]:
                wind_info = wind_result.get("wind", {})
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        "風向",
                        f"{wind_info.get('direction', 0):.1f}°"
                    )
                
                with col2:
                    st.metric(
                        "風速",
                        f"{wind_info.get('speed', 0):.1f}ノット"
                    )
                
                with col3:
                    st.metric(
                        "信頼度",
                        f"{wind_info.get('confidence', 0):.2f}"
                    )
                
                # 推定方法と詳細情報
                st.write(f"推定方法: {wind_info.get('method', '不明')}")
                
                if "details" in wind_info:
                    with st.expander("詳細情報", expanded=False):
                        st.json(wind_info["details"])
            
            # 風配図タブ
            with tabs[1]:
                display_wind_rose(wind_result)
            
            # マニューバータブ
            with tabs[2]:
                # 検出されたマニューバーの表示
                maneuvers = wind_result.get("detected_maneuvers", [])
                display_maneuvers(maneuvers, df)
            
            # 地図タブ
            with tabs[3]:
                display_wind_map(df, wind_result)
            
            # 時系列データタブ
            with tabs[4]:
                time_series = wind_result.get("time_series", [])
                display_wind_time_series(time_series)
        
        else:
            # 風推定の説明
            st.info("""
            「風向風速を推定」ボタンをクリックして、GPSデータから風向と風速を推定します。
            
            このモジュールでは、艇の航跡データから以下の方法で風を推定します：
            
            1. **マニューバー検出**: タックやジャイブを検出し、風向を推定します
            2. **VMG分析**: 風上・風下の走行パターンからVMG（Velocity Made Good）を分析し、最大VMGとなる角度から風向を推定します
            3. **極座標データ**: 艇種の極座標データがある場合、実際の速度との比較から風向風速を推定します
            
            複数の方法を組み合わせることで、より正確な風向風速の推定が可能になります。
            """)
    
    else:
        st.info("風向風速を推定するには、まずプロジェクトからセッションを選択してください。")


if __name__ == "__main__":
    wind_estimation_page()
