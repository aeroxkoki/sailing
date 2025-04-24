# -*- coding: utf-8 -*-
"""
ui.integrated.pages.dashboard

セーリング戦略分析システムのメインダッシュボードページ
"""

import streamlit as st
import pandas as pd
import numpy as np
import time
import os
import sys
from datetime import datetime

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

# ウィジェット管理システムのインポート
from ui.integrated.components.dashboard.widget_manager import WidgetManager

def render_page():
    """ダッシュボードページをレンダリングする関数"""
    
    st.title('分析ダッシュボード')
    
    # セッション状態の初期化
    if 'dashboard_initialized' not in st.session_state:
        st.session_state.dashboard_initialized = True
        st.session_state.selected_session = None
        st.session_state.dashboard_widgets = []
        st.session_state.dashboard_layout = "default"
    
    # セッション選択
    with st.sidebar:
        st.subheader("セッション選択")
        # 実際にはプロジェクト管理システムからセッションを取得する
        # サンプルとしてダミーデータを使用
        sessions = ["2025/03/27 レース練習", "2025/03/25 風向変化トレーニング", "2025/03/20 スピードテスト"]
        selected_session = st.selectbox("分析するセッションを選択", sessions)
        
        if selected_session != st.session_state.selected_session:
            st.session_state.selected_session = selected_session
            # セッションが変更されたら関連データを読み込む処理をここに追加
            st.experimental_rerun()
    
    # ダッシュボードレイアウト選択
    with st.sidebar:
        st.subheader("ダッシュボード設定")
        dashboard_layout = st.selectbox(
            "レイアウト", 
            ["デフォルト", "風向分析フォーカス", "パフォーマンスフォーカス", "比較分析", "カスタム"],
            key="dashboard_layout_select"
        )
        
        if dashboard_layout.lower().replace(" ", "_") != st.session_state.dashboard_layout:
            st.session_state.dashboard_layout = dashboard_layout.lower().replace(" ", "_")
            # レイアウトが変更されたらウィジェットを再構成
            # 実際の実装では、WidgetManagerを使用して適切なウィジェットセットを読み込む
            st.experimental_rerun()
    
    # WidgetManagerのインスタンス化
    widget_manager = WidgetManager()
    
    # 現在のセッション情報を表示するヘッダーエリア
    if st.session_state.selected_session:
        col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
        with col1:
            st.subheader(f"セッション: {st.session_state.selected_session}")
        with col2:
            st.metric("風速平均", "12.3 kt", "1.2 kt")
        with col3:
            st.metric("最高速度", "7.5 kt", "0.5 kt")
        with col4:
            st.metric("風向変化", "15°右", delta_color="normal")
        with col5:
            st.metric("データ品質", "92%", "2%")
    
    # タブを使用して異なる分析ビューを提供
    tab1, tab2, tab3, tab4 = st.tabs(["概要", "風向分析", "パフォーマンス", "戦略ポイント"])
    
    with tab1:
        # 概要タブのウィジェット
        st.subheader("セッション概要")
        
        # 基本情報カード
        with st.container():
            cols = st.columns(3)
            with cols[0]:
                st.markdown("### 基本情報")
                st.markdown("**日時**: 2025年3月27日 13:00-15:30")
                st.markdown("**場所**: 江の島沖")
                st.markdown("**艇種**: 470級")
                st.markdown("**風況**: 南西 8-15kt")
            
            with cols[1]:
                st.markdown("### セッション統計")
                st.markdown("**総距離**: 15.2 km")
                st.markdown("**総時間**: 2時間30分")
                st.markdown("**タック回数**: 24回")
                st.markdown("**ジャイブ回数**: 12回")
            
            with cols[2]:
                st.markdown("### データ品質")
                st.markdown("**完全性**: 98%")
                st.markdown("**精度**: 高")
                st.markdown("**異常値**: 2%")
                st.markdown("**サンプリングレート**: 1Hz")
        
        # KPI指標
        st.subheader("主要パフォーマンス指標")
        kpi_cols = st.columns(4)
        
        with kpi_cols[0]:
            st.metric(label="平均VMG (風上)", value="3.2 kt", delta="0.3 kt")
        with kpi_cols[1]:
            st.metric(label="平均VMG (風下)", value="4.5 kt", delta="-0.1 kt")
        with kpi_cols[2]:
            st.metric(label="タック効率", value="92%", delta="2%")
        with kpi_cols[3]:
            st.metric(label="風向変化対応", value="85%", delta="-5%")
        
        # マップサマリー
        st.subheader("セッションマップ")
        st.info("マップビューはこのダッシュボードの簡易版です。詳細な分析には「マップビュー」ページをご利用ください。")
        map_placeholder = st.empty()
        # ここで簡易版のマップを表示する（実際の実装では folium や他のマップライブラリを使用）
        map_placeholder.image("https://via.placeholder.com/800x400?text=セッションマップ", use_column_width=True)
    
    with tab2:
        # 風向分析タブ
        st.subheader("風向風速分析")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 風向変化")
            # 風向の時系列チャート
            chart_data = pd.DataFrame(
                np.sin(np.linspace(0, 10, 100)) * 30 + 180,
                columns=['風向 (度)']
            )
            st.line_chart(chart_data)
            
        with col2:
            st.markdown("### 風速変化")
            # 風速の時系列チャート
            wind_speed_data = pd.DataFrame(
                np.abs(np.sin(np.linspace(0, 10, 100)) * 5 + 10),
                columns=['風速 (kt)']
            )
            st.line_chart(wind_speed_data)
        
        # 風向シフト検出結果
        st.markdown("### 検出された風向シフト")
        shift_data = {
            "時間": ["13:15", "13:42", "14:10", "14:35", "15:05"],
            "シフト量": ["右 15°", "左 12°", "右 8°", "右 20°", "左 10°"],
            "シフト速度": ["緩やか", "急激", "緩やか", "緩やか", "急激"],
            "対応状況": ["良好", "遅延", "良好", "見逃し", "良好"]
        }
        st.dataframe(pd.DataFrame(shift_data))
        
        # 極座標図（風配図）
        st.markdown("### 風配図")
        st.info("極座標グラフは開発中です。完全版では風向と風速の分布を極座標で表示します。")
        
    with tab3:
        # パフォーマンスタブ
        st.subheader("パフォーマンス分析")
        
        # 速度分布
        st.markdown("### 速度分布")
        hist_data = np.random.normal(5, 1, 100)  # ダミーデータ
        hist_df = pd.DataFrame(hist_data, columns=["艇速 (kt)"])
        st.bar_chart(hist_df.value_counts(bins=10, sort=False))
        
        # VMGパフォーマンス
        st.markdown("### VMGパフォーマンス")
        
        vmg_cols = st.columns(2)
        with vmg_cols[0]:
            st.markdown("#### 風上VMG")
            vmg_upwind = pd.DataFrame(
                np.random.normal(3.2, 0.5, 50),
                columns=['VMG (kt)']
            )
            st.line_chart(vmg_upwind)
            
        with vmg_cols[1]:
            st.markdown("#### 風下VMG")
            vmg_downwind = pd.DataFrame(
                np.random.normal(4.5, 0.6, 50),
                columns=['VMG (kt)']
            )
            st.line_chart(vmg_downwind)
            
        # タック/ジャイブ分析
        st.markdown("### タック/ジャイブ分析")
        maneuver_data = {
            "種類": ["タック", "タック", "ジャイブ", "タック", "ジャイブ"],
            "時間": ["13:20", "13:55", "14:15", "14:40", "15:10"],
            "所要時間": ["8秒", "7秒", "10秒", "9秒", "8秒"],
            "速度損失": ["0.8kt", "0.5kt", "1.2kt", "0.7kt", "0.9kt"],
            "評価": ["良好", "優秀", "改善必要", "良好", "良好"]
        }
        st.dataframe(pd.DataFrame(maneuver_data))
    
    with tab4:
        # 戦略ポイントタブ
        st.subheader("戦略ポイント分析")
        
        # 戦略ポイント概要
        st.markdown("### 重要な戦略ポイント")
        strategy_data = {
            "時間": ["13:10", "13:38", "14:05", "14:32", "15:00"],
            "タイプ": ["風向シフト対応", "レイライン接近", "風向シフト対応", "障害物回避", "コース変更"],
            "判断": ["シフト前にタック", "レイラインでタック", "様子見", "早めの回避行動", "風上へのコース変更"],
            "結果": ["レグ短縮", "オーバースタンド", "不利なレイヤー", "ロス最小化", "有利なレイヤー獲得"],
            "評価": ["最適", "改善必要", "不適切", "適切", "最適"]
        }
        st.dataframe(pd.DataFrame(strategy_data))
        
        # 意思決定の効果
        st.markdown("### 意思決定の効果")
        decision_cols = st.columns(2)
        
        with decision_cols[0]:
            st.markdown("#### 風向変化への対応速度")
            response_data = pd.DataFrame(
                np.random.normal(85, 10, 10),
                columns=['対応速度 (%)']
            )
            st.bar_chart(response_data)
            
        with decision_cols[1]:
            st.markdown("#### 戦略効果")
            effect_data = {
                "戦略": ["早めのタック", "レイヤー選択", "周囲艇観察", "風予測に基づく展開"],
                "効果 (推定利得)": ["+45秒", "+30秒", "+15秒", "+60秒"]
            }
            st.dataframe(pd.DataFrame(effect_data))
        
        # 改善提案
        st.markdown("### 改善提案")
        with st.container():
            st.info("分析に基づく改善提案:")
            st.markdown("""
            1. **風向シフトの予測と対応**：右シフトパターンをより早く察知し、事前対応することで約30秒の利得が期待できます。
            2. **タック実行の判断**：オーバースタンドが2回観測されました。レイライン接近時の判断を改善してください。
            3. **風下での艇速**：風下走行時の艇速が理想値を10%下回っています。セールトリムの調整を検討してください。
            """)

    # ダッシュボードのカスタマイズオプション
    with st.sidebar:
        st.subheader("ダッシュボードカスタマイズ")
        
        # 編集モード切り替え
        edit_mode = st.session_state.get('dashboard_edit_mode', False)
        edit_mode_toggle = st.toggle("編集モード", value=edit_mode)
        
        if edit_mode_toggle != edit_mode:
            st.session_state.dashboard_edit_mode = edit_mode_toggle
            # 編集モードが変更されたらページを再読み込み
            st.experimental_rerun()
        
        # 編集モードの場合、ウィジェット管理機能を表示
        if edit_mode_toggle:
            st.markdown("---")
            st.subheader("ウィジェット管理")
            with st.expander("ウィジェットの追加", expanded=True):
                widget_category = st.selectbox(
                    "カテゴリ",
                    ["風向分析", "パフォーマンス", "戦略", "コース", "データ品質"]
                )
                
                if widget_category == "風向分析":
                    widget_options = ["風向時系列", "風速時系列", "極座標風配図", "シフト検出"]
                elif widget_category == "パフォーマンス":
                    widget_options = ["速度分布", "VMG分析", "タック効率", "ポーラー比較"]
                elif widget_category == "戦略":
                    widget_options = ["戦略ポイント", "意思決定評価", "改善提案", "レース分析"]
                elif widget_category == "コース":
                    widget_options = ["コースマップ", "軌跡分析", "レグパフォーマンス"]
                else:  # データ品質
                    widget_options = ["品質概要", "異常値分析", "データ完全性", "修正提案"]
                    
                widget_to_add = st.selectbox("追加するウィジェット", widget_options)
                
                # ウィジェットの位置とサイズの設定
                col1, col2 = st.columns(2)
                with col1:
                    widget_pos_row = st.number_input("行位置", min_value=0, max_value=2, value=0, step=1)
                    widget_width = st.number_input("幅", min_value=1, max_value=3, value=1, step=1)
                
                with col2:
                    widget_pos_col = st.number_input("列位置", min_value=0, max_value=2, value=0, step=1)
                    widget_height = st.number_input("高さ", min_value=1, max_value=3, value=1, step=1)
                
                if st.button("ウィジェットを追加", use_container_width=True):
                    # 実際の実装ではウィジェットマネージャーを使用して追加
                    widget_type_map = {
                        "風向時系列": "WindSummaryWidget",
                        "風速時系列": "WindSummaryWidget",
                        "極座標風配図": "WindSummaryWidget",
                        "シフト検出": "WindSummaryWidget",
                        "速度分布": "PerformanceWidget",
                        "VMG分析": "PerformanceWidget",
                        "タック効率": "PerformanceWidget",
                        "ポーラー比較": "PerformanceWidget",
                        "戦略ポイント": "StrategyPointsWidget",
                        "意思決定評価": "StrategyPointsWidget",
                        "改善提案": "StrategyPointsWidget",
                        "レース分析": "StrategyPointsWidget",
                        "品質概要": "DataQualityWidget",
                        "異常値分析": "DataQualityWidget",
                        "データ完全性": "DataQualityWidget",
                        "修正提案": "DataQualityWidget"
                    }
                    
                    widget_class = widget_type_map.get(widget_to_add, "WindSummaryWidget")
                    
                    # ウィジェット作成とレイアウト追加のロジック（実際にはWidgetManagerのメソッド呼び出し）
                    st.success(f"{widget_to_add}ウィジェットを追加しました（{widget_pos_row}, {widget_pos_col}）。")
                    
            with st.expander("レイアウト管理"):
                layout_name = st.text_input("レイアウト名", "マイレイアウト")
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("レイアウトを保存", use_container_width=True):
                        # 実際の実装ではウィジェットマネージャーを使用して保存
                        st.success(f"レイアウト「{layout_name}」を保存しました。")
                
                with col2:
                    if st.button("レイアウトをリセット", use_container_width=True):
                        # 確認ダイアログは実装の制約上省略
                        st.warning("現在のレイアウトをデフォルトに戻します。")
        
        # 編集モードでなくても表示するオプション
        st.markdown("---")
        with st.expander("表示オプション"):
            st.checkbox("自動更新", value=False)
            st.slider("更新間隔 (秒)", min_value=5, max_value=60, value=30, step=5)
            st.radio("データ表示期間", ["全期間", "最新30分", "最新1時間", "カスタム"])
            st.select_slider("詳細レベル", options=["低", "中", "高"], value="中")
                
    # アクションバー：便利なショートカットとデータインサイト
    st.markdown("### インサイトとアクション")
    
    insight_col1, insight_col2 = st.columns(2)
    with insight_col1:
        st.info("**主要インサイト**: 風上走行時のVMGが前回セッションより5%向上しています。タック効率の改善が主な要因です。")
    
    with insight_col2:
        st.warning("**注意点**: 14:30頃の右シフトへの対応が遅れました。風向変化の予測と早期対応の練習が推奨されます。")
    
    # ページ下部の操作ボタン
    st.markdown("---")
    action_cols = st.columns(4)
    
    with action_cols[0]:
        if st.button("📊 レポート生成", use_container_width=True):
            st.session_state.show_report_dialog = True
            
    with action_cols[1]:
        if st.button("💾 分析結果のエクスポート", use_container_width=True):
            # 実際の実装ではエクスポートページへの遷移
            st.session_state.page = "data_export"
            st.info("エクスポートページへ移動します...")
            
    with action_cols[2]:
        if st.button("🔍 比較分析", use_container_width=True):
            # 実際の実装では比較分析ページへの遷移
            st.session_state.page = "statistical_view"
            st.info("比較分析ページへ移動します...")
            
    with action_cols[3]:
        if st.button("🗺️ 詳細マップビュー", use_container_width=True):
            # 実際の実装ではマップビューページへの遷移
            st.session_state.page = "map_view"
            st.info("マップビューページへ移動します...")
    
    # レポート生成ダイアログ（モーダル代わり）
    if 'show_report_dialog' in st.session_state and st.session_state.show_report_dialog:
        with st.container():
            st.subheader("レポート生成")
            st.markdown("セッション分析レポートを生成します。希望する形式を選択してください。")
            
            report_format = st.selectbox(
                "レポート形式",
                ["PDF", "HTML", "Markdown"]
            )
            
            report_template = st.selectbox(
                "テンプレート",
                ["標準分析レポート", "簡易サマリー", "詳細技術レポート", "コーチング用"]
            )
            
            include_sections = st.multiselect(
                "含めるセクション",
                ["基本情報", "風向分析", "パフォーマンス指標", "戦略ポイント分析", "マップビュー", "改善提案"],
                default=["基本情報", "風向分析", "パフォーマンス指標", "戦略ポイント分析"]
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("キャンセル"):
                    st.session_state.show_report_dialog = False
                    st.experimental_rerun()
            with col2:
                if st.button("レポート生成"):
                    # 実際の実装ではレポート生成ロジックを呼び出す
                    st.success(f"{report_format}形式のレポートを生成しています...")
                    # プログレスバーで生成状況を表示
                    progress_bar = st.progress(0)
                    for i in range(100):
                        # 実際の処理ではなく、単純な遅延を模擬
                        time.sleep(0.01)
                        progress_bar.progress(i + 1)
                    
                    st.session_state.show_report_dialog = False
                    st.success(f"{report_format}形式のレポートが生成されました。")

if __name__ == "__main__":
    render_page()
