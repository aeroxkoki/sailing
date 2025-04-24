# -*- coding: utf-8 -*-
"""
ui.components.analysis.wind_shift_panel モジュール

風向シフト分析のためのパネルUIコンポーネントを提供します。
検出設定、検出結果、予測、パターン分析、可視化のタブで構成されます。
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Union, Any
import os
import sys
import logging

# 上位ディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

# アプリケーションモジュールのインポート
from sailing_data_processor.analysis.wind_shift_detector import WindShiftDetector
from sailing_data_processor.analysis.wind_pattern_analyzer import WindPatternAnalyzer
from sailing_data_processor.analysis.ml_models.shift_predictor import WindShiftPredictor
from sailing_data_processor.visualization.shift_visualization import ShiftVisualizer

# 共通コンポーネントのインポート
from ui.components.common.card import card
from ui.components.common.tooltip import tooltip
from ui.components.common.alert import info_alert, success_alert, warning_alert, error_alert

# ロギング設定
logger = logging.getLogger(__name__)

def wind_shift_analysis_panel(detector: Optional[WindShiftDetector] = None, 
                            predictor: Optional[WindShiftPredictor] = None, 
                            data_manager: Any = None,
                            on_change: Optional[callable] = None, 
                            key_prefix: str = ""):
    """
    風向シフト分析パネルを表示
    
    Parameters
    ----------
    detector : WindShiftDetector, optional
        風向シフト検出器, by default None
        Noneの場合は新規作成
    predictor : WindShiftPredictor, optional
        風向シフト予測モデル, by default None
    data_manager : Any, optional
        データ管理オブジェクト, by default None
    on_change : callable, optional
        変更時のコールバック, by default None
    key_prefix : str, optional
        キー接頭辞, by default ""
        
    Returns
    -------
    dict
        コンポーネント状態
    """
    st.markdown("### 風向シフト分析")
    
    # 検出器と予測器の初期化
    if detector is None:
        detector = WindShiftDetector()
    
    # 表示用の視覚化モジュール初期化
    visualizer = ShiftVisualizer()
    
    # パターン分析器の初期化
    pattern_analyzer = WindPatternAnalyzer()
    
    # 状態変数をセッションに保存
    if f"{key_prefix}_shifts" not in st.session_state:
        st.session_state[f"{key_prefix}_shifts"] = []
    
    if f"{key_prefix}_analysis_results" not in st.session_state:
        st.session_state[f"{key_prefix}_analysis_results"] = {}
    
    if f"{key_prefix}_forecast_results" not in st.session_state:
        st.session_state[f"{key_prefix}_forecast_results"] = {}
        
    changes = {}
    
    # タブレイアウト
    tabs = st.tabs(["検出設定", "検出結果", "予測", "パターン分析", "可視化"])
    
    # 検出設定タブ
    with tabs[0]:
        _detection_settings_tab(detector, data_manager, changes, key_prefix)
    
    # 検出結果タブ
    with tabs[1]:
        _detection_results_tab(detector, data_manager, visualizer, changes, key_prefix)
    
    # 予測タブ
    with tabs[2]:
        _prediction_tab(predictor, detector, data_manager, visualizer, changes, key_prefix)
    
    # パターン分析タブ
    with tabs[3]:
        _pattern_analysis_tab(pattern_analyzer, data_manager, visualizer, changes, key_prefix)
    
    # 可視化タブ
    with tabs[4]:
        _visualization_tab(visualizer, data_manager, changes, key_prefix)
    
    # コールバックの呼び出し
    if changes and on_change:
        on_change(changes)
    
    return changes

def _detection_settings_tab(detector: WindShiftDetector, 
                          data_manager: Any, 
                          changes: Dict, 
                          key_prefix: str):
    """検出設定タブの内容"""
    with st.container():
        st.subheader("風向シフト検出設定")
        
        # 検出方法
        col1, col2 = st.columns(2)
        
        with col1:
            detection_method = st.selectbox(
                "検出アルゴリズム",
                options=["statistical", "signal_processing", "machine_learning", "adaptive"],
                format_func=lambda x: {
                    "statistical": "統計的手法",
                    "signal_processing": "信号処理",
                    "machine_learning": "機械学習",
                    "adaptive": "適応型（自動選択）"
                }.get(x, x),
                index=["statistical", "signal_processing", "machine_learning", "adaptive"].index(
                    detector.method
                ),
                key=f"{key_prefix}_detection_method",
                help="風向シフトの検出に使用するアルゴリズム"
            )
            
            if detection_method != detector.method:
                detector.method = detection_method
                detector._init_detector()
                changes["detection_method"] = detection_method
            
            # 感度設定
            sensitivity = st.slider(
                "検出感度",
                min_value=0.1,
                max_value=1.0,
                value=detector.sensitivity,
                step=0.05,
                format="%.2f",
                key=f"{key_prefix}_sensitivity",
                help="シフト検出の感度（高いほど小さなシフトも検出）"
            )
            
            if sensitivity != detector.sensitivity:
                detector.sensitivity = sensitivity
                detector._adjust_thresholds_by_sensitivity()
                changes["sensitivity"] = sensitivity
        
        with col2:
            # 最小シフト角度
            min_shift_angle = st.slider(
                "最小シフト角度 (度)",
                min_value=3.0,
                max_value=20.0,
                value=detector.params.get("min_shift_angle", 5.0),
                step=0.5,
                key=f"{key_prefix}_min_shift_angle",
                help="検出するシフトの最小角度"
            )
            
            if min_shift_angle != detector.params.get("min_shift_angle"):
                detector.params["min_shift_angle"] = min_shift_angle
                changes["min_shift_angle"] = min_shift_angle
            
            # 信頼度閾値
            confidence_threshold = st.slider(
                "信頼度閾値",
                min_value=0.3,
                max_value=0.9,
                value=detector.params.get("confidence_threshold", 0.6),
                step=0.05,
                format="%.2f",
                key=f"{key_prefix}_confidence_threshold",
                help="シフトとして検出する最小信頼度"
            )
            
            if confidence_threshold != detector.params.get("confidence_threshold"):
                detector.params["confidence_threshold"] = confidence_threshold
                changes["confidence_threshold"] = confidence_threshold
        
        # 詳細パラメータを展開可能なセクション
        with st.expander("詳細パラメータ", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                # ノイズフィルタタイプ
                noise_filter = st.selectbox(
                    "ノイズフィルタ",
                    options=["kalman", "median", "gaussian", "savgol"],
                    format_func=lambda x: {
                        "kalman": "カルマンフィルタ",
                        "median": "メディアンフィルタ",
                        "gaussian": "ガウシアンフィルタ",
                        "savgol": "Savitzky-Golayフィルタ"
                    }.get(x, x),
                    index=["kalman", "median", "gaussian", "savgol"].index(
                        detector.params.get("noise_filter", "kalman")
                    ),
                    key=f"{key_prefix}_noise_filter"
                )
                
                if noise_filter != detector.params.get("noise_filter"):
                    detector.params["noise_filter"] = noise_filter
                    changes["noise_filter"] = noise_filter
                
                # トレンド検出オプション
                trend_detection = st.checkbox(
                    "トレンド変化を検出",
                    value=detector.params.get("trend_detection", True),
                    key=f"{key_prefix}_trend_detection"
                )
                
                if trend_detection != detector.params.get("trend_detection"):
                    detector.params["trend_detection"] = trend_detection
                    changes["trend_detection"] = trend_detection
            
            with col2:
                # 位置情報の活用
                use_location = st.checkbox(
                    "位置情報を活用",
                    value=detector.params.get("use_location_context", False),
                    key=f"{key_prefix}_use_location",
                    help="位置情報を使用してシフトの地理的文脈を分析"
                )
                
                if use_location != detector.params.get("use_location_context"):
                    detector.params["use_location_context"] = use_location
                    changes["use_location_context"] = use_location
                
                # 分析ウィンドウサイズ（自動/手動）
                auto_window = detector.window_size is None
                is_auto_window = st.checkbox(
                    "分析ウィンドウサイズを自動調整",
                    value=auto_window,
                    key=f"{key_prefix}_auto_window"
                )
                
                if not is_auto_window:
                    window_size = st.slider(
                        "分析ウィンドウサイズ (秒)",
                        min_value=30,
                        max_value=300,
                        value=detector.window_size if detector.window_size is not None else 120,
                        step=30,
                        key=f"{key_prefix}_window_size"
                    )
                    
                    if window_size != detector.window_size:
                        detector.window_size = window_size
                        changes["window_size"] = window_size
                elif detector.window_size is not None:
                    detector.window_size = None
                    changes["window_size"] = None
        
        # 実行ボタン
        col1, col2 = st.columns(2)
        with col1:
            if st.button("シフト検出実行", key=f"{key_prefix}_detect_button", type="primary"):
                # 検出処理の実行
                if data_manager and hasattr(data_manager, "get_wind_data"):
                    with st.spinner("風向シフトを検出中..."):
                        try:
                            wind_data = data_manager.get_wind_data()
                            
                            if wind_data is not None and not wind_data.empty:
                                track_data = None
                                if hasattr(data_manager, "get_track_data"):
                                    track_data = data_manager.get_track_data()
                                
                                # コース情報（利用可能な場合）
                                course_info = None
                                if hasattr(data_manager, "get_course_info"):
                                    course_info = data_manager.get_course_info()
                                
                                shifts = detector.detect_shifts(wind_data, track_data, course_info)
                                
                                if shifts:
                                    # シフトごとに重要度評価を追加
                                    for shift in shifts:
                                        shift['significance'] = detector.evaluate_shift_significance(shift)
                                    
                                    # 重要度でソート
                                    shifts.sort(key=lambda s: s.get('significance', 0), reverse=True)
                                    
                                    st.session_state[f"{key_prefix}_shifts"] = shifts
                                    changes["shifts"] = shifts
                                    
                                    # シフト数によるメッセージ
                                    st.success(f"合計 {len(shifts)} 件のシフトを検出しました。「検出結果」タブで詳細を確認できます。")
                                else:
                                    st.warning("シフトは検出されませんでした。検出感度を上げるか、他の検出方法を試してください。")
                            else:
                                st.error("風データが空または利用できません。")
                        except Exception as e:
                            st.error(f"シフト検出中にエラーが発生しました: {str(e)}")
                            logger.exception("シフト検出中にエラー:")
                else:
                    st.error("データが利用できません。データをロードしてください。")
        
        with col2:
            if st.button("設定をリセット", key=f"{key_prefix}_reset_button"):
                # 設定のリセット
                detector.__init__()
                
                # セッション状態のクリア
                for key in list(st.session_state.keys()):
                    if key.startswith(f"{key_prefix}_"):
                        del st.session_state[key]
                
                # 変更を記録
                changes["reset"] = True
                
                st.experimental_rerun()

def _detection_results_tab(detector: WindShiftDetector, 
                         data_manager: Any, 
                         visualizer: ShiftVisualizer, 
                         changes: Dict, 
                         key_prefix: str):
    """検出結果タブの内容"""
    with st.container():
        st.subheader("検出されたシフト")
        
        shifts = st.session_state.get(f"{key_prefix}_shifts", [])
        
        if not shifts:
            st.info("シフトはまだ検出されていません。「検出設定」タブでシフト検出を実行してください。")
            return
        
        # シフトタイプでフィルタリングオプション
        shift_types = list(set(s.get('shift_type', 'UNKNOWN') for s in shifts))
        
        col1, col2 = st.columns(2)
        
        with col1:
            selected_types = st.multiselect(
                "シフトタイプでフィルタ",
                options=shift_types,
                default=shift_types,
                format_func=lambda x: {
                    "PERSISTENT": "持続的シフト",
                    "TREND": "トレンド変化",
                    "OSCILLATION": "振動",
                    "PHASE": "位相変化",
                    "UNKNOWN": "未分類"
                }.get(x, x),
                key=f"{key_prefix}_filter_types"
            )
        
        with col2:
            # 信頼度でフィルタリング
            min_confidence = st.slider(
                "最小信頼度",
                min_value=0.0,
                max_value=1.0,
                value=0.3,
                step=0.05,
                format="%.2f",
                key=f"{key_prefix}_min_confidence"
            )
        
        # フィルタリングの適用
        filtered_shifts = [
            s for s in shifts
            if s.get('shift_type', 'UNKNOWN') in selected_types
            and s.get('confidence', 0) >= min_confidence
        ]
        
        # 時間順にソート
        filtered_shifts.sort(key=lambda s: s['timestamp'])
        
        # シフト数の表示
        st.write(f"表示: {len(filtered_shifts)} / {len(shifts)} 件のシフト")
        
        # データテーブル表示
        if filtered_shifts:
            # データフレームに変換
            shift_data = []
            for i, shift in enumerate(filtered_shifts, 1):
                # タイムスタンプをフォーマット
                timestamp_str = shift['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                
                # シフト方向
                direction = "右" if shift.get('direction_change', 0) > 0 else "左"
                
                # シフトタイプの日本語表示
                shift_type_ja = {
                    "PERSISTENT": "持続的シフト",
                    "TREND": "トレンド変化",
                    "OSCILLATION": "振動",
                    "PHASE": "位相変化",
                    "UNKNOWN": "未分類"
                }.get(shift.get('shift_type', 'UNKNOWN'), shift.get('shift_type', '不明'))
                
                # データの整形
                shift_data.append({
                    "#": i,
                    "時刻": timestamp_str,
                    "タイプ": shift_type_ja,
                    "前の風向": f"{shift.get('before_direction', 0):.1f}°",
                    "後の風向": f"{shift.get('after_direction', 0):.1f}°",
                    "変化量": f"{abs(shift.get('direction_change', 0)):.1f}°{direction}",
                    "信頼度": f"{shift.get('confidence', 0):.2f}",
                    "重要度": f"{shift.get('significance', 0):.2f}"
                })
            
            df = pd.DataFrame(shift_data)
            st.dataframe(df, use_container_width=True)
            
            # 時系列グラフ
            if data_manager and hasattr(data_manager, "get_wind_data"):
                st.subheader("シフトの時系列表示")
                
                wind_data = data_manager.get_wind_data()
                if wind_data is not None and not wind_data.empty:
                    col1, col2 = st.columns([1, 3])
                    
                    with col1:
                        # グラフのオプション
                        start_time = wind_data['timestamp'].min()
                        end_time = wind_data['timestamp'].max()
                        
                        # 表示期間の選択
                        st.write("表示期間")
                        start_select = st.date_input(
                            "開始日",
                            value=start_time.date(),
                            min_value=start_time.date(),
                            max_value=end_time.date(),
                            key=f"{key_prefix}_graph_start_date"
                        )
                        
                        start_time_h = st.slider(
                            "開始時刻",
                            min_value=0,
                            max_value=23,
                            value=start_time.hour,
                            step=1,
                            format="%d時",
                            key=f"{key_prefix}_graph_start_hour"
                        )
                        
                        end_select = st.date_input(
                            "終了日",
                            value=end_time.date(),
                            min_value=start_time.date(),
                            max_value=end_time.date(),
                            key=f"{key_prefix}_graph_end_date"
                        )
                        
                        end_time_h = st.slider(
                            "終了時刻",
                            min_value=0,
                            max_value=23,
                            value=min(end_time.hour + 1, 23),
                            step=1,
                            format="%d時",
                            key=f"{key_prefix}_graph_end_hour"
                        )
                        
                        # 日付と時間の組み合わせ
                        from datetime import datetime
                        display_start = datetime.combine(start_select, datetime.min.time().replace(hour=start_time_h))
                        display_end = datetime.combine(end_select, datetime.min.time().replace(hour=end_time_h, minute=59, second=59))
                        
                        # 期間でデータをフィルタリング
                        filtered_wind_data = wind_data[
                            (wind_data['timestamp'] >= display_start) &
                            (wind_data['timestamp'] <= display_end)
                        ]
                        
                        filtered_time_shifts = [
                            s for s in filtered_shifts
                            if display_start <= s['timestamp'] <= display_end
                        ]
                    
                    with col2:
                        if not filtered_wind_data.empty:
                            # グラフの生成
                            try:
                                fig = visualizer.plot_wind_direction_timeline(
                                    filtered_wind_data,
                                    filtered_time_shifts,
                                    title="風向の時系列と検出されたシフト"
                                )
                                st.pyplot(fig)
                            except Exception as e:
                                st.error(f"グラフ作成中にエラーが発生しました: {str(e)}")
                                logger.exception("グラフ作成中にエラー:")
                        else:
                            st.warning("選択された期間にデータがありません。")
            
            # シフト詳細情報
            st.subheader("シフト詳細情報")
            shift_index = st.selectbox(
                "詳細表示するシフトを選択",
                options=range(len(filtered_shifts)),
                format_func=lambda i: f"シフト #{i+1}: {filtered_shifts[i]['timestamp'].strftime('%Y-%m-%d %H:%M:%S')} - {abs(filtered_shifts[i].get('direction_change', 0)):.1f}°",
                key=f"{key_prefix}_shift_detail_select"
            )
            
            if shift_index is not None:
                selected_shift = filtered_shifts[shift_index]
                
                # シフト詳細情報のカード表示
                with st.container():
                    cols = st.columns([1, 1, 1])
                    
                    with cols[0]:
                        st.markdown(f"**発生時刻**: {selected_shift['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
                        st.markdown(f"**シフトタイプ**: {shift_type_ja}")
                        
                        # 位置情報（存在する場合）
                        if 'position' in selected_shift and selected_shift['position'][0] is not None:
                            lat, lon = selected_shift['position']
                            st.markdown(f"**位置**: 緯度 {lat:.6f}, 経度 {lon:.6f}")
                    
                    with cols[1]:
                        st.markdown(f"**シフト前の風向**: {selected_shift.get('before_direction', 0):.1f}°")
                        st.markdown(f"**シフト後の風向**: {selected_shift.get('after_direction', 0):.1f}°")
                        st.markdown(f"**変化量**: {abs(selected_shift.get('direction_change', 0)):.1f}°{direction}")
                    
                    with cols[2]:
                        st.markdown(f"**信頼度**: {selected_shift.get('confidence', 0):.2f}")
                        st.markdown(f"**重要度**: {selected_shift.get('significance', 0):.2f}")
                        
                        # 風速情報（存在する場合）
                        if 'before_speed' in selected_shift and 'after_speed' in selected_shift:
                            before_speed = selected_shift.get('before_speed')
                            after_speed = selected_shift.get('after_speed')
                            
                            if before_speed is not None and after_speed is not None:
                                st.markdown(f"**風速変化**: {before_speed:.1f} → {after_speed:.1f} ノット")
                
                # 近接シフトの表示
                if len(filtered_shifts) > 1:
                    st.subheader("近接するシフト")
                    
                    # 現在のシフトの時刻
                    current_time = selected_shift['timestamp']
                    
                    # 近接するシフトをリストアップ（時間差が10分以内）
                    nearby_shifts = [
                        (i, s, abs((s['timestamp'] - current_time).total_seconds()))
                        for i, s in enumerate(filtered_shifts)
                        if s != selected_shift and abs((s['timestamp'] - current_time).total_seconds()) <= 600
                    ]
                    
                    # 時間差でソート
                    nearby_shifts.sort(key=lambda x: x[2])
                    
                    if nearby_shifts:
                        nearby_data = []
                        for i, shift, seconds in nearby_shifts[:5]:  # 最大5件まで表示
                            # 時間差を分単位に変換
                            minutes = seconds / 60
                            
                            # シフト方向
                            direction = "右" if shift.get('direction_change', 0) > 0 else "左"
                            
                            # シフトタイプの日本語表示
                            shift_type_ja = {
                                "PERSISTENT": "持続的シフト",
                                "TREND": "トレンド変化",
                                "OSCILLATION": "振動",
                                "PHASE": "位相変化",
                                "UNKNOWN": "未分類"
                            }.get(shift.get('shift_type', 'UNKNOWN'), shift.get('shift_type', '不明'))
                            
                            # 相対時間（「前」または「後」）
                            relative_time = "前" if shift['timestamp'] < current_time else "後"
                            
                            nearby_data.append({
                                "シフト #": i + 1,
                                "時刻": shift['timestamp'].strftime('%H:%M:%S'),
                                "相対時間": f"{minutes:.1f}分{relative_time}",
                                "タイプ": shift_type_ja,
                                "変化量": f"{abs(shift.get('direction_change', 0)):.1f}°{direction}",
                                "信頼度": f"{shift.get('confidence', 0):.2f}"
                            })
                        
                        df_nearby = pd.DataFrame(nearby_data)
                        st.dataframe(df_nearby, use_container_width=True)
                    else:
                        st.info("近接するシフトはありません。")
        else:
            st.warning("フィルタ条件に一致するシフトはありません。")

def _prediction_tab(predictor: Optional[WindShiftPredictor], 
                  detector: WindShiftDetector, 
                  data_manager: Any, 
                  visualizer: ShiftVisualizer, 
                  changes: Dict, 
                  key_prefix: str):
    """予測タブの内容"""
    with st.container():
        st.subheader("風向シフト予測")
        
        # 検出したシフトの取得
        shifts = st.session_state.get(f"{key_prefix}_shifts", [])
        
        # 予測器がなければ作成するオプション
        if predictor is None:
            st.info("風向シフト予測モデルが初期化されていません。新しいモデルを作成するか、既存モデルをロードできます。")
            
            col1, col2 = st.columns(2)
            with col1:
                model_type = st.selectbox(
                    "モデルタイプ",
                    options=["arima", "prophet", "lstm", "ensemble"],
                    format_func=lambda x: {
                        "arima": "ARIMA (時系列統計)",
                        "prophet": "Prophet (Facebook)",
                        "lstm": "LSTM (ディープラーニング)",
                        "ensemble": "アンサンブル (複合モデル)"
                    }.get(x, x),
                    index=3,  # ensemble がデフォルト
                    key=f"{key_prefix}_model_type"
                )
            
            with col2:
                horizon = st.slider(
                    "予測時間 (分)",
                    min_value=10,
                    max_value=60,
                    value=30,
                    step=5,
                    key=f"{key_prefix}_prediction_horizon"
                )
            
            # モデル作成ボタン
            if st.button("予測モデルを作成", key=f"{key_prefix}_create_model", type="primary"):
                with st.spinner("予測モデルを作成中..."):
                    try:
                        predictor = WindShiftPredictor(
                            model_type=model_type,
                            prediction_horizon=horizon
                        )
                        
                        # セッションに保存
                        st.session_state[f"{key_prefix}_predictor"] = predictor
                        changes["predictor_created"] = True
                        
                        st.success(f"{model_type.upper()} モデルが正常に作成されました。")
                        
                        # 再描画
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"モデル作成中にエラーが発生しました: {str(e)}")
                        logger.exception("モデル作成中にエラー:")
            
            # 既存モデルがなければここで終了
            if predictor is None:
                st.warning("モデルが作成されていないため、予測機能は利用できません。")
                return
            
            # セッションからリロードの場合
            predictor = st.session_state.get(f"{key_prefix}_predictor")
            if predictor is None:
                return
        
        # 以下はモデルが存在する場合の処理
        
        # モデル情報の表示
        with st.expander("予測モデル情報", expanded=False):
            model_params = predictor.get_model_params()
            
            st.markdown(f"**モデルタイプ**: {model_params['model_type']}")
            st.markdown(f"**予測時間**: {model_params['prediction_horizon']}分")
            
            if predictor.is_trained:
                st.markdown(f"**最終更新**: {predictor.last_update.strftime('%Y-%m-%d %H:%M:%S')}" if predictor.last_update else "未更新")
                
                # パフォーマンス指標（存在する場合）
                if predictor.performance_metrics:
                    st.subheader("モデル性能指標")
                    for metric_name, metric_value in predictor.performance_metrics.items():
                        if isinstance(metric_value, dict):
                            st.markdown(f"**{metric_name}**:")
                            for k, v in metric_value.items():
                                st.markdown(f"- {k}: {v}")
                        else:
                            st.markdown(f"**{metric_name}**: {metric_value}")
            else:
                st.warning("モデルはまだ学習されていません。")
        
        # 訓練と予測のセクション
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("モデルの学習")
            
            if data_manager and hasattr(data_manager, "get_wind_data"):
                # 訓練データのスライダー
                if predictor.is_trained:
                    st.info("モデルは既に学習済みです。再学習することもできます。")
                
                # 学習ウィンドウ
                training_window = st.slider(
                    "学習ウィンドウ (分)",
                    min_value=60,
                    max_value=480,
                    value=predictor.params.get("training_window", 180),
                    step=30,
                    key=f"{key_prefix}_training_window"
                )
                
                if training_window != predictor.params.get("training_window"):
                    predictor.params["training_window"] = training_window
                    changes["training_window"] = training_window
                
                # 検証比率
                validation_ratio = st.slider(
                    "検証データ比率",
                    min_value=0.1,
                    max_value=0.4,
                    value=0.2,
                    step=0.05,
                    format="%.2f",
                    key=f"{key_prefix}_validation_ratio"
                )
                
                # 学習ボタン
                if st.button("モデルを学習", key=f"{key_prefix}_train_model", type="primary"):
                    wind_data = data_manager.get_wind_data()
                    
                    if wind_data is not None and not wind_data.empty:
                        with st.spinner("モデルを学習中..."):
                            try:
                                # 学習の実行
                                training_result = predictor.train(wind_data, validation_ratio)
                                
                                if training_result.get('status') == 'success':
                                    st.success("モデルの学習が完了しました。")
                                    changes["model_trained"] = True
                                    
                                    # メトリクスの表示
                                    if 'metrics' in training_result:
                                        metrics = training_result['metrics']
                                        st.write("学習結果:")
                                        
                                        if 'validation' in metrics:
                                            val_metrics = metrics['validation']
                                            st.metric("検証MAE", f"{val_metrics.get('mae', 0):.2f}度")
                                else:
                                    st.warning(f"モデルの学習は完了しましたが、一部の問題がありました: {training_result.get('message', '')}")
                            except Exception as e:
                                st.error(f"モデル学習中にエラーが発生しました: {str(e)}")
                                logger.exception("モデル学習中にエラー:")
                    else:
                        st.error("風データが空または利用できません。")
            else:
                st.error("データが利用できません。データをロードしてください。")
        
        with col2:
            st.subheader("風向予測")
            
            if not predictor.is_trained:
                st.warning("モデルが学習されていないため、予測を実行できません。まず左側でモデルを学習してください。")
            else:
                # 予測ホライズン
                horizon = st.slider(
                    "予測時間 (分)",
                    min_value=5,
                    max_value=60,
                    value=predictor.prediction_horizon,
                    step=5,
                    key=f"{key_prefix}_forecast_horizon"
                )
                
                # 予測ボタン
                if st.button("風向を予測", key=f"{key_prefix}_predict", type="primary"):
                    if data_manager and hasattr(data_manager, "get_wind_data"):
                        wind_data = data_manager.get_wind_data()
                        
                        if wind_data is not None and not wind_data.empty:
                            with st.spinner("予測を実行中..."):
                                try:
                                    # 最新のデータだけを使用（過去24時間）
                                    latest_time = wind_data['timestamp'].max()
                                    start_time = latest_time - timedelta(hours=24)
                                    recent_data = wind_data[wind_data['timestamp'] >= start_time]
                                    
                                    # 予測の実行
                                    forecast = predictor.predict(recent_data, horizon)
                                    
                                    if not forecast.empty:
                                        # 予測結果をセッションに保存
                                        st.session_state[f"{key_prefix}_forecast_results"] = forecast
                                        changes["forecast"] = forecast
                                        
                                        # 予測結果の表示
                                        st.success("予測が完了しました。")
                                        
                                        # 結果テーブル
                                        forecast_table = []
                                        for i, (_, row) in enumerate(forecast.iterrows()):
                                            forecast_table.append({
                                                "時刻": row['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                                                "予測風向": f"{row['predicted_direction']:.1f}°",
                                                "信頼度": f"{row['confidence']:.2f}",
                                                "シフトポイント": "はい" if row.get('shift_point', False) else "いいえ"
                                            })
                                        
                                        df_forecast = pd.DataFrame(forecast_table)
                                        st.dataframe(df_forecast, use_container_width=True)
                                        
                                        # シフトポイントの抽出
                                        shift_points = forecast[forecast['shift_point'] == True]
                                        
                                        if not shift_points.empty:
                                            st.subheader("予測されるシフトポイント")
                                            
                                            for _, point in shift_points.iterrows():
                                                with st.container():
                                                    cols = st.columns([2, 1])
                                                    
                                                    with cols[0]:
                                                        # シフトの方向
                                                        direction = "右" if point.get('shift_magnitude', 0) > 0 else "左"
                                                        magnitude = abs(point.get('shift_magnitude', 0))
                                                        
                                                        st.markdown(f"**時刻**: {point['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
                                                        st.markdown(f"**予測シフト**: {magnitude:.1f}°{direction} (信頼度: {point['confidence']:.2f})")
                                                    
                                                    with cols[1]:
                                                        # 現在時刻からの経過時間
                                                        now = datetime.now()
                                                        time_diff = (point['timestamp'] - now).total_seconds() / 60
                                                        
                                                        if time_diff > 0:
                                                            st.markdown(f"**予測時間**: 約 {time_diff:.0f}分後")
                                                        else:
                                                            st.markdown("**予測時間**: 過去の時点")
                                        else:
                                            st.info("予測期間内にシフトポイントは検出されませんでした。")
                                    else:
                                        st.warning("予測結果が空です。")
                                except Exception as e:
                                    st.error(f"予測中にエラーが発生しました: {str(e)}")
                                    logger.exception("予測中にエラー:")
                        else:
                            st.error("風データが空または利用できません。")
                    else:
                        st.error("データが利用できません。データをロードしてください。")
        
        # 予測結果のグラフ表示
        forecast_results = st.session_state.get(f"{key_prefix}_forecast_results")
        if forecast_results is not None and not forecast_results.empty:
            st.subheader("予測グラフ")
            
            with st.spinner("グラフを生成中..."):
                try:
                    # 最新の風データを取得
                    if data_manager and hasattr(data_manager, "get_wind_data"):
                        wind_data = data_manager.get_wind_data()
                        
                        if wind_data is not None and not wind_data.empty:
                            # 最新の24時間分のデータだけを使用
                            latest_time = wind_data['timestamp'].max()
                            start_time = latest_time - timedelta(hours=24)
                            recent_data = wind_data[wind_data['timestamp'] >= start_time].copy()
                            
                            # 予測データを結合
                            combined_data = recent_data.copy()
                            
                            # 予測ポイントをシフトとして整形
                            forecast_shifts = []
                            for _, row in forecast_results[forecast_results['shift_point'] == True].iterrows():
                                forecast_shifts.append({
                                    'timestamp': row['timestamp'],
                                    'before_direction': row['predicted_direction'] - row.get('shift_magnitude', 0) / 2,
                                    'after_direction': row['predicted_direction'] + row.get('shift_magnitude', 0) / 2,
                                    'direction_change': row.get('shift_magnitude', 0),
                                    'confidence': row['confidence'],
                                    'shift_type': 'FORECAST',
                                    'significance': row['confidence']
                                })
                            
                            # 実際のシフトとの比較
                            shifts = st.session_state.get(f"{key_prefix}_shifts", [])
                            
                            # 過去と予測を1つのグラフに表示
                            fig = visualizer.plot_wind_direction_timeline(
                                combined_data,
                                shifts + forecast_shifts,
                                title="過去の風向と将来予測"
                            )
                            st.pyplot(fig)
                except Exception as e:
                    st.error(f"予測グラフ作成中にエラーが発生しました: {str(e)}")
                    logger.exception("予測グラフ作成中にエラー:")

def _pattern_analysis_tab(pattern_analyzer: WindPatternAnalyzer, 
                        data_manager: Any, 
                        visualizer: ShiftVisualizer, 
                        changes: Dict, 
                        key_prefix: str):
    """パターン分析タブの内容"""
    with st.container():
        st.subheader("風向パターン分析")
        
        # 検出したシフトの取得
        shifts = st.session_state.get(f"{key_prefix}_shifts", [])
        
        # 分析オプション
        col1, col2 = st.columns(2)
        
        with col1:
            min_data_points = st.slider(
                "最小データポイント数",
                min_value=10,
                max_value=100,
                value=pattern_analyzer.min_data_points,
                step=10,
                key=f"{key_prefix}_min_data_points"
            )
            
            if min_data_points != pattern_analyzer.min_data_points:
                pattern_analyzer.min_data_points = min_data_points
                changes["min_data_points"] = min_data_points
        
        with col2:
            max_pattern_period = st.slider(
                "最大パターン周期 (分)",
                min_value=30,
                max_value=240,
                value=pattern_analyzer.max_pattern_period,
                step=30,
                key=f"{key_prefix}_max_pattern_period"
            )
            
            if max_pattern_period != pattern_analyzer.max_pattern_period:
                pattern_analyzer.max_pattern_period = max_pattern_period
                changes["max_pattern_period"] = max_pattern_period
        
        # 詳細オプション
        with st.expander("詳細オプション", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                min_period = st.slider(
                    "最小周期 (分)",
                    min_value=5,
                    max_value=30,
                    value=pattern_analyzer.params.get("min_period", 10),
                    step=5,
                    key=f"{key_prefix}_min_period"
                )
                
                if min_period != pattern_analyzer.params.get("min_period"):
                    pattern_analyzer.params["min_period"] = min_period
                    changes["min_period"] = min_period
                
                confidence_threshold = st.slider(
                    "信頼度閾値",
                    min_value=0.3,
                    max_value=0.9,
                    value=pattern_analyzer.params.get("confidence_threshold", 0.6),
                    step=0.05,
                    format="%.2f",
                    key=f"{key_prefix}_pattern_confidence_threshold"
                )
                
                if confidence_threshold != pattern_analyzer.params.get("confidence_threshold"):
                    pattern_analyzer.params["confidence_threshold"] = confidence_threshold
                    changes["pattern_confidence_threshold"] = confidence_threshold
            
            with col2:
                use_geo = st.checkbox(
                    "地理的分析を有効化",
                    value=pattern_analyzer.params.get("geographical_analysis", False),
                    key=f"{key_prefix}_geographical_analysis"
                )
                
                if use_geo != pattern_analyzer.params.get("geographical_analysis"):
                    pattern_analyzer.params["geographical_analysis"] = use_geo
                    changes["geographical_analysis"] = use_geo
                
                use_clustering = st.checkbox(
                    "クラスタリングを使用",
                    value=pattern_analyzer.params.get("use_clustering", True),
                    key=f"{key_prefix}_use_clustering",
                    help="地理的分析でクラスタリングアルゴリズムを使用"
                )
                
                if use_clustering != pattern_analyzer.params.get("use_clustering"):
                    pattern_analyzer.params["use_clustering"] = use_clustering
                    changes["use_clustering"] = use_clustering
                
                smooth_window = st.slider(
                    "平滑化ウィンドウサイズ",
                    min_value=1,
                    max_value=15,
                    value=pattern_analyzer.params.get("smooth_window", 5),
                    step=2,
                    key=f"{key_prefix}_smooth_window"
                )
                
                if smooth_window != pattern_analyzer.params.get("smooth_window"):
                    pattern_analyzer.params["smooth_window"] = smooth_window
                    changes["smooth_window"] = smooth_window
        
        # 分析実行ボタン
        if st.button("パターン分析を実行", key=f"{key_prefix}_analyze_button", type="primary"):
            if data_manager and hasattr(data_manager, "get_wind_data"):
                wind_data = data_manager.get_wind_data()
                
                if wind_data is not None and not wind_data.empty:
                    with st.spinner("風向パターンを分析中..."):
                        try:
                            # 位置データの取得（利用可能な場合）
                            location_data = None
                            if use_geo and hasattr(data_manager, "get_track_data"):
                                location_data = data_manager.get_track_data()
                            
                            # パターン分析の実行
                            analysis_results = pattern_analyzer.analyze_patterns(wind_data, location_data)
                            
                            if analysis_results:
                                # 分析結果をセッションに保存
                                st.session_state[f"{key_prefix}_analysis_results"] = analysis_results
                                changes["analysis_results"] = analysis_results
                                
                                # 結果表示
                                st.success("パターン分析が完了しました。")
                                
                                # パターンタイプの表示
                                aggregate = analysis_results.get("aggregate", {})
                                pattern_type = aggregate.get("pattern_type", "unknown")
                                
                                pattern_ja = {
                                    "periodic": "周期的",
                                    "trending": "トレンド",
                                    "oscillating": "振動",
                                    "complex": "複合",
                                    "trend_with_oscillations": "トレンド+振動",
                                    "stable": "安定",
                                    "mixed": "混合",
                                    "unknown": "不明"
                                }.get(pattern_type, pattern_type)
                                
                                # 主要な特性表示
                                st.subheader("パターン特性")
                                
                                metrics = st.columns(3)
                                
                                with metrics[0]:
                                    st.metric(
                                        "パターンタイプ",
                                        pattern_ja
                                    )
                                
                                with metrics[1]:
                                    st.metric(
                                        "風の安定性",
                                        f"{aggregate.get('stability', 0) * 100:.1f}%"
                                    )
                                
                                with metrics[2]:
                                    st.metric(
                                        "予測可能性",
                                        f"{aggregate.get('predictability', 0) * 100:.1f}%"
                                    )
                            else:
                                st.warning("パターン分析を実行できませんでした。データが不十分な可能性があります。")
                        except Exception as e:
                            st.error(f"パターン分析中にエラーが発生しました: {str(e)}")
                            logger.exception("パターン分析中にエラー:")
                else:
                    st.error("風データが空または利用できません。")
            else:
                st.error("データが利用できません。データをロードしてください。")
        
        # 分析結果の表示
        analysis_results = st.session_state.get(f"{key_prefix}_analysis_results")
        
        if analysis_results:
            # タブで分析結果を表示
            result_tabs = st.tabs(["概要", "周期性", "トレンド", "振動", "地理的パターン", "推奨事項"])
            
            # 概要タブ
            with result_tabs[0]:
                aggregate = analysis_results.get("aggregate", {})
                
                # キーとなる洞察
                if "key_insights" in aggregate and aggregate["key_insights"]:
                    st.subheader("主要な洞察")
                    
                    for insight in aggregate["key_insights"]:
                        st.markdown(f"- {insight}")
                
                # 総合ダッシュボード
                st.subheader("分析ダッシュボード")
                
                if data_manager and hasattr(data_manager, "get_wind_data"):
                    wind_data = data_manager.get_wind_data()
                    
                    if wind_data is not None and not wind_data.empty:
                        try:
                            # ダッシュボードの表示
                            fig = visualizer.plot_shift_analysis_dashboard(
                                wind_data,
                                shifts,
                                analysis_results
                            )
                            st.pyplot(fig)
                        except Exception as e:
                            st.error(f"ダッシュボード作成中にエラーが発生しました: {str(e)}")
                            logger.exception("ダッシュボード作成中にエラー:")
                    else:
                        st.warning("風データが利用できないため、ダッシュボードを表示できません。")
            
            # 周期性タブ
            with result_tabs[1]:
                periodicity = analysis_results.get("periodicity", {})
                
                if periodicity.get("has_periodicity", False):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric(
                            "主要周期",
                            f"{periodicity.get('main_period_minutes', 0):.1f}分"
                        )
                        
                        st.metric(
                            "パターン強度",
                            f"{periodicity.get('pattern_strength', 0) * 100:.1f}%"
                        )
                    
                    with col2:
                        # 追加のピーク
                        additional_peaks = periodicity.get("additional_peaks", [])
                        if additional_peaks:
                            st.subheader("副次的な周期")
                            
                            for i, peak in enumerate(additional_peaks, 1):
                                st.markdown(f"- 周期 {peak.get('period_minutes', 0):.1f}分 (強度: {peak.get('strength', 0) * 100:.1f}%)")
                    
                    # 周期パターンの可視化
                    direction_pattern = periodicity.get("direction_pattern", [])
                    if direction_pattern:
                        st.subheader("周期的パターン")
                        
                        # 周期パターンの可視化
                        fig, ax = plt.subplots(figsize=(10, 4))
                        
                        # パターン内の位置（0-1）
                        positions = np.linspace(0, 1, len(direction_pattern))
                        period_mins = periodicity.get("main_period_minutes", 0)
                        
                        # X軸のラベル（分単位）
                        x_ticks = np.linspace(0, period_mins, 6)
                        x_tick_pos = np.linspace(0, 1, 6)
                        
                        # パターンのプロット
                        ax.plot(positions, direction_pattern, 'b-', linewidth=2)
                        
                        # シフトポイント
                        shift_points = periodicity.get("shift_points", [])
                        if shift_points:
                            for pos, direction in shift_points:
                                color = 'red' if direction == "clockwise" else 'green'
                                ax.axvline(x=pos, color=color, linestyle='--', alpha=0.7)
                        
                        # グラフの装飾
                        ax.set_xlabel(f'周期内の位置 (分, 全体{period_mins:.1f}分)')
                        ax.set_ylabel('風向 (度)')
                        ax.set_title('周期的な風向パターン')
                        ax.set_xticks(x_tick_pos)
                        ax.set_xticklabels([f'{x:.1f}' for x in x_ticks])
                        ax.grid(True, linestyle='--', alpha=0.7)
                        
                        st.pyplot(fig)
                    
                    # 予測
                    st.subheader("周期に基づく予測")
                    
                    # 現在時刻に基づく予測
                    forecast = pattern_analyzer.get_period_forecast()
                    
                    if forecast and forecast["status"] == "success":
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.metric(
                                "現在の予測風向",
                                f"{forecast.get('predicted_direction', 0):.1f}°"
                            )
                            
                            st.metric(
                                "信頼度",
                                f"{forecast.get('confidence', 0) * 100:.1f}%"
                            )
                        
                        with col2:
                            next_shift = forecast.get("next_shift_time")
                            if next_shift:
                                time_to_shift = (next_shift - datetime.now()).total_seconds() / 60
                                direction = forecast.get("shift_direction", "unknown")
                                direction_ja = "右" if direction == "clockwise" else "左"
                                
                                st.metric(
                                    "次のシフト予測",
                                    f"{time_to_shift:.1f}分後 ({direction_ja}シフト)"
                                )
                            
                            cycle_position = forecast.get("cycle_position", 0)
                            st.metric(
                                "周期内の位置",
                                f"{cycle_position * 100:.1f}%"
                            )
                    else:
                        st.warning("周期に基づく予測ができませんでした。")
                else:
                    st.info("周期的なパターンは検出されませんでした。")
            
            # トレンドタブ
            with result_tabs[2]:
                trend = analysis_results.get("trend", {})
                
                if trend.get("has_trend", False):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        trend_rate = trend.get("direction_trend_rate", 0)
                        direction = "右回り" if trend_rate > 0 else "左回り"
                        
                        st.metric(
                            "変化率",
                            f"{abs(trend_rate):.3f}°/分 {direction}"
                        )
                        
                        st.metric(
                            "トレンド強度",
                            f"{trend.get('trend_strength', 0) * 100:.1f}%"
                        )
                    
                    with col2:
                        total_change = trend.get("total_direction_change", 0)
                        st.metric(
                            "全体の変化量",
                            f"{abs(total_change):.1f}°"
                        )
                        
                        # 相関係数
                        if "sin_r_squared" in trend and "cos_r_squared" in trend:
                            avg_r2 = (trend["sin_r_squared"] + trend["cos_r_squared"]) / 2
                            st.metric(
                                "決定係数 (R²)",
                                f"{avg_r2:.3f}"
                            )
                    
                    # 予測
                    st.subheader("トレンドに基づく予測")
                    
                    # 現在時刻からの予測
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        horizon = st.slider(
                            "予測時間 (分)",
                            min_value=10,
                            max_value=60,
                            value=30,
                            step=10,
                            key=f"{key_prefix}_trend_horizon"
                        )
                    
                    with col2:
                        if st.button("トレンド予測を表示", key=f"{key_prefix}_trend_forecast"):
                            forecast = pattern_analyzer.get_trend_forecast(
                                horizon_minutes=horizon
                            )
                            
                            if forecast and forecast["status"] == "success":
                                st.metric(
                                    f"{horizon}分後の予測風向",
                                    f"{forecast.get('predicted_direction', 0):.1f}°"
                                )
                                
                                st.metric(
                                    "予測信頼度",
                                    f"{forecast.get('confidence', 0) * 100:.1f}%"
                                )
                            else:
                                st.warning("トレンド予測ができませんでした。")
                else:
                    st.info("持続的なトレンドは検出されませんでした。")
            
            # 振動タブ
            with result_tabs[3]:
                oscillations = analysis_results.get("oscillations", {})
                
                if oscillations.get("has_oscillations", False):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric(
                            "振動振幅",
                            f"±{oscillations.get('oscillation_amplitude', 0):.1f}°"
                        )
                        
                        # 方向の標準偏差
                        if "direction_std" in oscillations:
                            st.metric(
                                "風向の標準偏差",
                                f"{oscillations.get('direction_std', 0):.1f}°"
                            )
                    
                    with col2:
                        freq = oscillations.get("oscillation_frequency", 0)
                        if freq > 0:
                            period_sec = 60 / freq
                            st.metric(
                                "振動周期",
                                f"{period_sec:.1f}秒"
                            )
                        
                        # 符号変化回数
                        st.metric(
                            "符号変化回数",
                            f"{oscillations.get('sign_changes', 0)}"
                        )
                    
                    # 振動の特性
                    st.info(
                        "振動は風向の短期的な変動を示しています。"
                        "この場合、平均的な風向に合わせたコース戦略を取り、短期的な変動に過剰反応しないことが推奨されます。"
                    )
                else:
                    st.info("顕著な振動パターンは検出されませんでした。")
            
            # 地理的パターンタブ
            with result_tabs[4]:
                geographical = analysis_results.get("geographical", {})
                
                if geographical:
                    # 地理的クラスタ
                    region_clusters = geographical.get("region_clusters", [])
                    if region_clusters:
                        st.subheader("地域クラスタ分析")
                        
                        # クラスタ情報をテーブルで表示
                        cluster_data = []
                        for i, cluster in enumerate(region_clusters, 1):
                            cluster_data.append({
                                "クラスタID": i,
                                "中心緯度": f"{cluster.get('center_latitude', 0):.6f}",
                                "中心経度": f"{cluster.get('center_longitude', 0):.6f}",
                                "半径 (m)": f"{cluster.get('radius_meters', 0):.1f}",
                                "ポイント数": cluster.get("point_count", 0),
                                "平均風向": f"{cluster.get('mean_direction', 0):.1f}°",
                                "風向標準偏差": f"{cluster.get('direction_std', 0):.1f}°",
                                "安定性": f"{cluster.get('stability', 0) * 100:.1f}%",
                                "パターン": cluster.get("pattern", "unknown")
                            })
                        
                        df_clusters = pd.DataFrame(cluster_data)
                        st.dataframe(df_clusters, use_container_width=True)
                        
                        # 地理的分布の可視化
                        if data_manager and hasattr(data_manager, "get_track_data"):
                            track_data = data_manager.get_track_data()
                            
                            if track_data is not None and not track_data.empty:
                                try:
                                    # ヒートマップの表示
                                    fig = visualizer.plot_shift_heatmap(
                                        track_data,
                                        shifts,
                                        title="風向シフトの地理的分布"
                                    )
                                    st.pyplot(fig)
                                except Exception as e:
                                    st.error(f"ヒートマップ作成中にエラーが発生しました: {str(e)}")
                                    logger.exception("ヒートマップ作成中にエラー:")
                    else:
                        # グリッド分析
                        grid_analysis = geographical.get("grid_analysis", [])
                        if grid_analysis:
                            st.subheader("グリッド分析")
                            
                            # グリッド情報をテーブルで表示
                            grid_data = []
                            for i, cell in enumerate(grid_analysis, 1):
                                grid_data.append({
                                    "セルID": i,
                                    "中心緯度": f"{cell.get('center_latitude', 0):.6f}",
                                    "中心経度": f"{cell.get('center_longitude', 0):.6f}",
                                    "ポイント数": cell.get("point_count", 0),
                                    "平均風向": f"{cell.get('mean_direction', 0):.1f}°",
                                    "風向標準偏差": f"{cell.get('direction_std', 0):.1f}°",
                                    "信頼度": f"{cell.get('confidence', 0) * 100:.1f}%"
                                })
                            
                            df_grid = pd.DataFrame(grid_data)
                            st.dataframe(df_grid, use_container_width=True)
                        else:
                            st.info("地理的パターン分析データがありません。")
                else:
                    st.info("地理的パターン分析は実行されていないか、利用可能な位置データがありません。")
            
            # 推奨事項タブ
            with result_tabs[5]:
                recommendations = analysis_results.get("recommendations", {})
                
                if "strategy_recommendations" in recommendations and recommendations["strategy_recommendations"]:
                    st.subheader("戦略的推奨事項")
                    
                    for i, rec in enumerate(recommendations["strategy_recommendations"], 1):
                        st.markdown(f"{i}. {rec}")
                    
                    # 戦略的洞察の取得
                    insights = pattern_analyzer.get_strategic_insights()
                    
                    if insights and insights["status"] == "success":
                        st.subheader("風パターンの特性")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.metric(
                                "風の安定性",
                                f"{insights.get('stability', 0) * 100:.1f}%"
                            )
                        
                        with col2:
                            st.metric(
                                "予測可能性",
                                f"{insights.get('predictability', 0) * 100:.1f}%"
                            )
                        
                        # レースへの示唆
                        st.subheader("レース戦略への示唆")
                        
                        pattern_type = insights.get("pattern_type", "unknown")
                        pattern_ja = {
                            "periodic": "周期的",
                            "trending": "トレンド",
                            "oscillating": "振動",
                            "complex": "複合",
                            "trend_with_oscillations": "トレンド+振動",
                            "stable": "安定",
                            "mixed": "混合"
                        }.get(pattern_type, "不明")
                        
                        if pattern_type == "periodic":
                            st.info(
                                f"**{pattern_ja}パターン**: 一定の周期で風向が変化します。"
                                "周期を予測して先回りした戦略を立てることが有効です。"
                            )
                        elif pattern_type == "trending":
                            st.info(
                                f"**{pattern_ja}パターン**: 持続的に一定方向へ風向が変化しています。"
                                "シフトの方向に有利なコースを選ぶと効果的です。"
                            )
                        elif pattern_type == "oscillating":
                            st.info(
                                f"**{pattern_ja}パターン**: 風向が短期的に振動しています。"
                                "平均的な風向に合わせた安定した戦略が効果的です。"
                            )
                        elif pattern_type == "complex" or pattern_type == "trend_with_oscillations":
                            st.info(
                                f"**{pattern_ja}パターン**: 複数のパターンが組み合わさっています。"
                                "適応的な戦略と常に風の変化に注意を払うことが重要です。"
                            )
                        elif pattern_type == "stable":
                            st.info(
                                f"**{pattern_ja}パターン**: 風向は比較的安定しています。"
                                "一貫したコース戦略が有効でしょう。"
                            )
                        else:
                            st.info(
                                f"**{pattern_ja}パターン**: 明確なパターンは見られません。"
                                "柔軟な対応と風の変化への注意が必要です。"
                            )
                else:
                    st.info("戦略的推奨事項は生成されていません。")

def _visualization_tab(visualizer: ShiftVisualizer, 
                     data_manager: Any, 
                     changes: Dict, 
                     key_prefix: str):
    """可視化タブの内容"""
    with st.container():
        st.subheader("風向シフトの可視化")
        
        # 検出したシフトの取得
        shifts = st.session_state.get(f"{key_prefix}_shifts", [])
        analysis_results = st.session_state.get(f"{key_prefix}_analysis_results", {})
        
        if not shifts:
            st.info("シフトはまだ検出されていません。「検出設定」タブでシフト検出を実行してください。")
            return
        
        # 可視化タイプの選択
        viz_type = st.radio(
            "可視化タイプ",
            options=["時系列グラフ", "風配図", "総合ダッシュボード", "地理的分布"],
            horizontal=True,
            key=f"{key_prefix}_viz_type"
        )
        
        # 可視化設定
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.subheader("表示設定")
            
            # 表示テーマ
            theme = st.selectbox(
                "表示テーマ",
                options=["default", "dark", "minimal"],
                format_func=lambda x: {
                    "default": "標準",
                    "dark": "ダーク",
                    "minimal": "ミニマル"
                }.get(x, x),
                key=f"{key_prefix}_viz_theme"
            )
            
            # 設定を反映
            if theme != visualizer.theme:
                visualizer.theme = theme
                visualizer._set_theme(theme)
                changes["viz_theme"] = theme
            
            # 図のサイズ設定
            fig_width = st.slider(
                "図の幅",
                min_value=6,
                max_value=15,
                value=visualizer.figure_size[0],
                step=1,
                key=f"{key_prefix}_fig_width"
            )
            
            fig_height = st.slider(
                "図の高さ",
                min_value=4,
                max_value=10,
                value=visualizer.figure_size[1],
                step=1,
                key=f"{key_prefix}_fig_height"
            )
            
            if (fig_width, fig_height) != visualizer.figure_size:
                visualizer.figure_size = (fig_width, fig_height)
                changes["fig_size"] = (fig_width, fig_height)
            
            # 解像度設定
            dpi = st.slider(
                "解像度 (DPI)",
                min_value=72,
                max_value=300,
                value=visualizer.dpi,
                step=36,
                key=f"{key_prefix}_fig_dpi"
            )
            
            if dpi != visualizer.dpi:
                visualizer.dpi = dpi
                changes["fig_dpi"] = dpi
            
            # フィルタリングオプション
            if viz_type != "風配図":  # 風配図以外ではフィルタが利用可能
                st.subheader("シフトフィルタ")
                
                # シフトタイプでフィルタリング
                shift_types = list(set(s.get('shift_type', 'UNKNOWN') for s in shifts))
                
                selected_types = st.multiselect(
                    "シフトタイプ",
                    options=shift_types,
                    default=shift_types,
                    format_func=lambda x: {
                        "PERSISTENT": "持続的シフト",
                        "TREND": "トレンド変化",
                        "OSCILLATION": "振動",
                        "PHASE": "位相変化",
                        "UNKNOWN": "未分類"
                    }.get(x, x),
                    key=f"{key_prefix}_viz_filter_types"
                )
                
                # 信頼度でフィルタリング
                min_confidence = st.slider(
                    "最小信頼度",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.3,
                    step=0.05,
                    format="%.2f",
                    key=f"{key_prefix}_viz_min_confidence"
                )
                
                # フィルタリングの適用
                filtered_shifts = [
                    s for s in shifts
                    if s.get('shift_type', 'UNKNOWN') in selected_types
                    and s.get('confidence', 0) >= min_confidence
                ]
            else:
                # 風配図では全シフトを使用
                filtered_shifts = shifts
            
            # エクスポートボタン
            if st.button("画像をエクスポート", key=f"{key_prefix}_export_image"):
                # エクスポート用のフラグをセット（下部で処理）
                st.session_state[f"{key_prefix}_export_viz"] = True
        
        with col2:
            # データの取得
            if data_manager and hasattr(data_manager, "get_wind_data"):
                wind_data = data_manager.get_wind_data()
                
                if wind_data is not None and not wind_data.empty:
                    # 可視化タイプに応じた表示
                    st.subheader("可視化結果")
                    
                    try:
                        if viz_type == "時系列グラフ":
                            fig = visualizer.plot_wind_direction_timeline(
                                wind_data,
                                filtered_shifts,
                                title="風向の時系列と検出されたシフト"
                            )
                            st.pyplot(fig)
                            
                            # エクスポート
                            if st.session_state.get(f"{key_prefix}_export_viz", False):
                                # Base64エンコードされた画像の取得
                                img_str = visualizer.get_base64_image(fig)
                                
                                # ダウンロードリンクの作成
                                st.markdown("### 画像ダウンロード")
                                st.markdown(f"[時系列グラフをダウンロード]({img_str})", unsafe_allow_html=True)
                                
                                # フラグをリセット
                                st.session_state[f"{key_prefix}_export_viz"] = False
                            
                        elif viz_type == "風配図":
                            fig = visualizer.plot_wind_rose_with_shifts(
                                wind_data,
                                filtered_shifts,
                                title="風配図とシフトパターン"
                            )
                            st.pyplot(fig)
                            
                            # エクスポート
                            if st.session_state.get(f"{key_prefix}_export_viz", False):
                                # Base64エンコードされた画像の取得
                                img_str = visualizer.get_base64_image(fig)
                                
                                # ダウンロードリンクの作成
                                st.markdown("### 画像ダウンロード")
                                st.markdown(f"[風配図をダウンロード]({img_str})", unsafe_allow_html=True)
                                
                                # フラグをリセット
                                st.session_state[f"{key_prefix}_export_viz"] = False
                            
                        elif viz_type == "総合ダッシュボード":
                            if analysis_results:
                                fig = visualizer.plot_shift_analysis_dashboard(
                                    wind_data,
                                    filtered_shifts,
                                    analysis_results
                                )
                                st.pyplot(fig)
                                
                                # エクスポート
                                if st.session_state.get(f"{key_prefix}_export_viz", False):
                                    # Base64エンコードされた画像の取得
                                    img_str = visualizer.get_base64_image(fig)
                                    
                                    # ダウンロードリンクの作成
                                    st.markdown("### 画像ダウンロード")
                                    st.markdown(f"[ダッシュボードをダウンロード]({img_str})", unsafe_allow_html=True)
                                    
                                    # フラグをリセット
                                    st.session_state[f"{key_prefix}_export_viz"] = False
                            else:
                                st.warning("パターン分析結果がないため、ダッシュボードを表示できません。「パターン分析」タブで分析を実行してください。")
                                
                        elif viz_type == "地理的分布":
                            # 位置データの取得
                            if hasattr(data_manager, "get_track_data"):
                                track_data = data_manager.get_track_data()
                                
                                if track_data is not None and not track_data.empty:
                                    fig = visualizer.plot_shift_heatmap(
                                        track_data,
                                        filtered_shifts,
                                        title="風向シフトの地理的分布"
                                    )
                                    st.pyplot(fig)
                                    
                                    # エクスポート
                                    if st.session_state.get(f"{key_prefix}_export_viz", False):
                                        # Base64エンコードされた画像の取得
                                        img_str = visualizer.get_base64_image(fig)
                                        
                                        # ダウンロードリンクの作成
                                        st.markdown("### 画像ダウンロード")
                                        st.markdown(f"[地理的分布をダウンロード]({img_str})", unsafe_allow_html=True)
                                        
                                        # フラグをリセット
                                        st.session_state[f"{key_prefix}_export_viz"] = False
                                else:
                                    st.warning("位置データが利用できないため、地理的分布を表示できません。")
                            else:
                                st.warning("位置データが利用できないため、地理的分布を表示できません。")
                    except Exception as e:
                        st.error(f"可視化中にエラーが発生しました: {str(e)}")
                        logger.exception("可視化中にエラー:")
                else:
                    st.error("風データが空または利用できません。")
            else:
                st.error("データが利用できません。データをロードしてください。")
