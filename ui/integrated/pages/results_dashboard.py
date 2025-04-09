"""
ui.integrated.pages.results_dashboard

セーリング戦略分析システムの分析結果ダッシュボードページです。
分析結果の概要表示、重要指標のKPIカード表示、主要な分析カテゴリーへのナビゲーションリンクを提供します。
"""

import streamlit as st
import pandas as pd
import numpy as np
import os
import sys
import json
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

# ダッシュボードコンポーネントのインポート
from ui.integrated.components.dashboard.widget_manager import WidgetManager
from ui.integrated.components.dashboard.widgets.wind_summary_widget import WindSummaryWidget
from ui.integrated.components.dashboard.widgets.strategy_points_widget import StrategyPointsWidget
from ui.integrated.components.dashboard.widgets.performance_widget import PerformanceWidget
from ui.integrated.components.dashboard.widgets.data_quality_widget import DataQualityWidget

def render_page():
    """
    分析結果ダッシュボードページをレンダリングする関数
    """
    st.title('分析結果ダッシュボード')
    
    # セッション状態の初期化
    if 'selected_dashboard_session' not in st.session_state:
        st.session_state.selected_dashboard_session = None
    
    # サイドバーのセッション選択
    with st.sidebar:
        st.subheader("セッション選択")
        # 実際にはプロジェクト管理システムからセッションを取得する
        # サンプルとしてダミーデータを使用
        sessions = ["2025/03/27 レース練習", "2025/03/25 風向変化トレーニング", "2025/03/20 スピードテスト"]
        selected_session = st.selectbox("分析するセッションを選択", sessions)
        
        if selected_session != st.session_state.selected_dashboard_session:
            st.session_state.selected_dashboard_session = selected_session
            # ここで実際のセッションデータをロードする処理を追加
            # st.experimental_rerun()
    
    # 選択されたセッションに関する情報を表示
    if st.session_state.selected_dashboard_session:
        st.markdown(f"## セッション: {st.session_state.selected_dashboard_session}")
        
        # セッション基本情報（ダミーデータ）
        session_info = {
            "日付": "2025/03/27",
            "場所": "江の島",
            "コース": "トライアングル",
            "風向平均": "南西 (225°)",
            "風速平均": "12 kt",
            "走行距離": "8.5 km",
            "所要時間": "1時間25分",
            "解析状態": "完了"
        }
        
        # 基本情報カード
        with st.container():
            st.subheader("セッション基本情報")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("日付", session_info["日付"])
                st.metric("場所", session_info["場所"])
            
            with col2:
                st.metric("風向平均", session_info["風向平均"])
                st.metric("風速平均", session_info["風速平均"])
            
            with col3:
                st.metric("走行距離", session_info["走行距離"])
                st.metric("所要時間", session_info["所要時間"])
            
            with col4:
                st.metric("コース", session_info["コース"])
                st.metric("解析状態", session_info["解析状態"])
        
        # 主要KPIと要約情報
        with st.container():
            st.subheader("主要パフォーマンス指標")
            
            # レイアウト: 3カラム
            kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
            
            # サンプルデータ（実際の実装では分析結果から取得）
            performance_metrics = {
                "平均VMG (風上)": "3.8 kt",
                "平均VMG (風下)": "4.5 kt",
                "ヒール角平均": "18°",
                "タック回数": "12",
                "平均タック所要時間": "8.2 秒",
                "風上効率": "87%",
                "風下効率": "92%",
                "風向変化対応速度": "85%"
            }
            
            with kpi_col1:
                st.metric("平均VMG (風上)", performance_metrics["平均VMG (風上)"], delta="+0.2 kt")
                st.metric("風上効率", performance_metrics["風上効率"], delta="+3%")
                st.metric("タック回数", performance_metrics["タック回数"])
            
            with kpi_col2:
                st.metric("平均VMG (風下)", performance_metrics["平均VMG (風下)"], delta="-0.1 kt")
                st.metric("風下効率", performance_metrics["風下効率"], delta="+1%")
                st.metric("平均タック所要時間", performance_metrics["平均タック所要時間"], delta="-0.4 秒")
            
            with kpi_col3:
                st.metric("ヒール角平均", performance_metrics["ヒール角平均"])
                st.metric("風向変化対応速度", performance_metrics["風向変化対応速度"], delta="+5%")
                
                # グラフへのクイックリンク
                if st.button("詳細パフォーマンスグラフ", use_container_width=True):
                    # 実際の実装ではパフォーマンスグラフページへリダイレクト
                    st.info("詳細パフォーマンスグラフページへのリンクは開発中です")
        
        # ダッシュボードウィジェット
        st.subheader("詳細分析")
        
        # ウィジェット管理システムを使用
        widget_manager = WidgetManager()
        
        # サンプルデータの生成（本来はセッションから読み込む）
        def generate_sample_data():
            """サンプルデータを生成"""
            # 時系列データ
            start_time = datetime.now() - timedelta(hours=2)
            times = [start_time + timedelta(minutes=i) for i in range(120)]
            
            # 風向風速データ
            wind_data = pd.DataFrame({
                'timestamp': times,
                'wind_direction': (np.cumsum(np.random.normal(0, 2, len(times))) % 40 + 200),
                'wind_speed': np.random.normal(12, 1.5, len(times)) + np.sin(np.linspace(0, 6, len(times)))
            })
            
            # 戦略ポイントデータ
            strategy_points = {
                'total': 15,
                'types': {
                    'タック': 8,
                    '風向シフト': 4,
                    'レイライン': 2,
                    'その他': 1
                },
                'importance': {
                    '最高': 3,
                    '高': 5,
                    '中': 4,
                    '低': 3
                },
                'quality': {
                    '最適': 6,
                    '適切': 4,
                    '改善必要': 3,
                    '不適切': 2
                }
            }
            
            # パフォーマンスデータ
            speed_data = pd.DataFrame({
                'timestamp': times,
                'boat_speed': np.random.normal(6, 1, len(times)) + np.sin(np.linspace(0, 8, len(times))),
                'vmg': np.random.normal(4, 1.2, len(times)) + np.sin(np.linspace(0, 6, len(times))) * 0.8,
                'heel_angle': np.random.normal(18, 3, len(times)) + np.sin(np.linspace(0, 10, len(times))) * 2
            })
            
            # データ品質情報
            data_quality = {
                'gps_quality': 98,
                'data_completeness': 95,
                'issues': {
                    'total': 3,
                    'fixed': 2,
                    'types': {
                        'GPS信号低下': 1,
                        'センサー一時的エラー': 1,
                        '欠損データ': 1
                    }
                },
                'coverage': {
                    'gps': 100,
                    'wind': 98,
                    'heel': 95,
                    'course': 100
                }
            }
            
            return {
                'wind_data': wind_data,
                'strategy_points': strategy_points,
                'speed_data': speed_data,
                'data_quality': data_quality
            }
        
        # サンプルデータを生成
        sample_data = generate_sample_data()
        
        # ウィジェットの表示（2行2列のグリッド）
        col1, col2 = st.columns(2)
        
        with col1:
            # 風向風速サマリーウィジェット
            wind_widget = WindSummaryWidget()
            wind_widget.render(sample_data['wind_data'])
        
        with col2:
            # 戦略ポイントサマリーウィジェット
            strategy_widget = StrategyPointsWidget()
            strategy_widget.render(sample_data['strategy_points'])
        
        col3, col4 = st.columns(2)
        
        with col3:
            # パフォーマンス指標ウィジェット
            performance_widget = PerformanceWidget()
            performance_widget.render(sample_data['speed_data'])
        
        with col4:
            # データ品質ウィジェット
            quality_widget = DataQualityWidget()
            quality_widget.render(sample_data['data_quality'])
        
        # 分析ナビゲーションリンク
        st.subheader("詳細分析へのリンク")
        
        # 3カラムでリンクボタンを表示
        link_col1, link_col2, link_col3 = st.columns(3)
        
        with link_col1:
            if st.button("🧭 航跡マップ表示", use_container_width=True):
                # 実際の実装では実装済みのマップビューページへリダイレクト
                st.switch_page("ui/integrated/pages/map_view.py")
        
        with link_col2:
            if st.button("📊 統計グラフ表示", use_container_width=True):
                # 実際の実装では統計チャートページへリダイレクト
                # st.switch_page("ui/integrated/pages/chart_view.py")
                st.info("統計グラフページへのリンクは開発中です")
        
        with link_col3:
            if st.button("⏱️ タイムライン表示", use_container_width=True):
                # 実際の実装ではタイムラインページへリダイレクト
                # st.switch_page("ui/integrated/pages/timeline_view.py")
                st.info("タイムラインページへのリンクは開発中です")
        
        # レポート生成とエクスポートオプション
        st.subheader("レポートとエクスポート")
        
        export_col1, export_col2, export_col3 = st.columns(3)
        
        with export_col1:
            if st.button("📝 分析レポート生成", use_container_width=True):
                st.info("レポート生成機能は開発中です")
        
        with export_col2:
            if st.button("💾 データエクスポート", use_container_width=True):
                st.info("データエクスポート機能は開発中です")
        
        with export_col3:
            if st.button("🔄 比較分析", use_container_width=True):
                st.info("比較分析機能は開発中です")
        
        # フッター情報
        st.divider()
        st.caption("© 2025 セーリング戦略分析システム")
    
    else:
        # セッションが選択されていない場合
        st.info("分析するセッションを左側のサイドバーから選択してください。")

if __name__ == "__main__":
    render_page()
