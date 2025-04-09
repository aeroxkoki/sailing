"""
ui.integrated.components.visualization.comparison_tool

セッション間の比較分析のためのツール
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Any, Optional, Tuple
import os
import sys
from datetime import datetime, timedelta

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..')))

class ComparisonTool:
    """複数のセッションを比較するためのツール"""
    
    def __init__(self):
        """比較ツールを初期化"""
        # セッション状態の初期化
        if 'comparison_tool_initialized' not in st.session_state:
            st.session_state.comparison_tool_initialized = True
            st.session_state.comparison_sessions = []
            st.session_state.comparison_metrics = []
            st.session_state.comparison_time_alignment = "start"
            st.session_state.comparison_data_cache = {}
        
        # 比較可能なメトリクスのリスト
        self.available_metrics = [
            {"id": "speed", "name": "速度", "unit": "kt", "description": "艇速"},
            {"id": "vmg", "name": "VMG", "unit": "kt", "description": "Velocity Made Good (対風速度)"},
            {"id": "wind_dir", "name": "風向", "unit": "度", "description": "風向角度"},
            {"id": "wind_speed", "name": "風速", "unit": "kt", "description": "風速"},
            {"id": "course", "name": "進路", "unit": "度", "description": "対地進路"},
            {"id": "heel", "name": "ヒール角", "unit": "度", "description": "艇のヒール（傾き）角度"},
            {"id": "tack_efficiency", "name": "タック効率", "unit": "%", "description": "タック操作の効率性"},
            {"id": "vmg_efficiency", "name": "VMG効率", "unit": "%", "description": "最適VMGに対する効率"}
        ]
    
    def render_session_selector(self, sessions: List[str], current_session: str) -> None:
        """比較するセッションの選択UIを表示
        
        Args:
            sessions: 利用可能なセッションのリスト
            current_session: 現在選択されているメインセッション
        """
        st.subheader("比較セッションの選択")
        
        # 現在のセッションは除外
        available_sessions = [s for s in sessions if s != current_session]
        
        if not available_sessions:
            st.info("比較可能なセッションがありません。他のセッションを追加してください。")
            return
        
        # 比較するセッションの選択
        selected_sessions = st.multiselect(
            "比較するセッションを選択",
            available_sessions,
            default=st.session_state.comparison_sessions
        )
        
        if selected_sessions != st.session_state.comparison_sessions:
            st.session_state.comparison_sessions = selected_sessions
            # セッションが変更されたら関連データをリセット
            st.session_state.comparison_data_cache = {}
            st.experimental_rerun()
    
    def render_metric_selector(self) -> None:
        """比較するメトリクスの選択UIを表示"""
        st.subheader("比較メトリクスの選択")
        
        # メトリクスの選択
        metrics_options = [(m["id"], f"{m['name']} ({m['unit']})") for m in self.available_metrics]
        
        selected_metrics = st.multiselect(
            "比較するメトリクスを選択",
            options=[m[0] for m in metrics_options],
            default=st.session_state.comparison_metrics,
            format_func=lambda x: next((name for id, name in metrics_options if id == x), x)
        )
        
        if selected_metrics != st.session_state.comparison_metrics:
            st.session_state.comparison_metrics = selected_metrics
            st.experimental_rerun()
    
    def render_time_alignment_options(self) -> None:
        """時間軸の調整オプションUIを表示"""
        st.subheader("時間軸の調整")
        
        alignment_options = {
            "start": "開始時刻で揃える",
            "end": "終了時刻で揃える",
            "duration": "所要時間に正規化",
            "gps": "GPSポイントで揃える"
        }
        
        selected_alignment = st.radio(
            "時間軸の調整方法",
            options=list(alignment_options.keys()),
            format_func=lambda x: alignment_options[x],
            index=list(alignment_options.keys()).index(st.session_state.comparison_time_alignment)
        )
        
        if selected_alignment != st.session_state.comparison_time_alignment:
            st.session_state.comparison_time_alignment = selected_alignment
            st.experimental_rerun()
        
        # GPSポイントで揃える場合は、追加オプションを表示
        if selected_alignment == "gps":
            st.info("GPSポイントで揃える場合、マップ上で基準となるポイントを選択する必要があります。")
            
            if st.button("マップでポイントを選択"):
                st.session_state.show_map_point_selector = True
    
    def render_comparison_summary(self, 
                                  current_session: str, 
                                  comparison_sessions: List[str]) -> None:
        """セッション比較の概要を表示
        
        Args:
            current_session: 現在のメインセッション
            comparison_sessions: 比較するセッションのリスト
        """
        if not comparison_sessions:
            return
        
        st.subheader("セッション比較概要")
        
        # サンプルの概要データを生成（実際の実装では、セッションから実際のデータを取得）
        summary_data = []
        
        # 現在のセッションのデータ
        current_data = {
            "セッション": current_session,
            "日付": "2025/03/27",
            "所要時間": "2時間30分",
            "風向": "210°±15°",
            "風速": "12.3 kt",
            "平均速度": "6.2 kt",
            "タック回数": 24,
            "VMG効率": "92%"
        }
        summary_data.append(current_data)
        
        # 比較セッションのデータ
        for session in comparison_sessions:
            # セッションごとに少し異なるダミーデータを生成
            session_seed = hash(session) % 1000
            np.random.seed(session_seed)
            
            session_data = {
                "セッション": session,
                "日付": f"2025/{3-(session_seed%3)}/{20+(session_seed%7)}",
                "所要時間": f"{2-(session_seed%2)}時間{30+(session_seed%30)}分",
                "風向": f"{200+(session_seed%40)}°±{10+(session_seed%10)}°",
                "風速": f"{11.5+(session_seed%10)/10:.1f} kt",
                "平均速度": f"{5.8+(session_seed%8)/10:.1f} kt",
                "タック回数": 20+(session_seed%10),
                "VMG効率": f"{85+(session_seed%15)}%"
            }
            summary_data.append(session_data)
        
        # 概要テーブルの表示
        st.dataframe(pd.DataFrame(summary_data), use_container_width=True)
    
    def render_metric_comparison(self, 
                                current_session: str, 
                                comparison_sessions: List[str],
                                metrics: List[str]) -> None:
        """選択されたメトリクスの比較グラフを表示
        
        Args:
            current_session: 現在のメインセッション
            comparison_sessions: 比較するセッションのリスト
            metrics: 比較するメトリクスのリスト
        """
        if not comparison_sessions or not metrics:
            return
        
        st.subheader("メトリクス比較")
        
        for metric_id in metrics:
            # メトリクス情報を取得
            metric_info = next((m for m in self.available_metrics if m["id"] == metric_id), None)
            
            if not metric_info:
                continue
            
            metric_name = metric_info["name"]
            metric_unit = metric_info["unit"]
            
            st.markdown(f"### {metric_name}の比較")
            
            # 時系列データの生成（実際の実装では、セッションから実際のデータを取得）
            time_range = pd.date_range(start="2025-03-27 13:00:00", periods=100, freq="1min")
            
            # 異なるメトリクスに応じたデータパターンを生成
            if metric_id == "speed":
                # 速度データの生成
                base_data = self._generate_speed_sample(time_range)
            elif metric_id == "vmg":
                # VMGデータの生成
                base_data = self._generate_vmg_sample(time_range)
            elif metric_id == "wind_dir":
                # 風向データの生成
                base_data = self._generate_wind_dir_sample(time_range)
            elif metric_id == "wind_speed":
                # 風速データの生成
                base_data = self._generate_wind_speed_sample(time_range)
            else:
                # その他のメトリクスは単純なサイン波で模擬
                base_data = pd.DataFrame({
                    '時間': time_range,
                    f'{metric_name} ({metric_unit})': np.sin(np.linspace(0, 6*np.pi, 100)) * 5 + 10
                })
            
            # 現在のセッションのデータ
            base_data['セッション'] = current_session
            
            # 時間軸の調整
            if st.session_state.comparison_time_alignment == "end":
                # 終了時刻で揃える場合は、時間を反転
                time_shift = timedelta(minutes=0)
            elif st.session_state.comparison_time_alignment == "duration":
                # 所要時間に正規化する場合は、0-100%のスケールに変換
                # 実際の実装では、各セッションの実際の所要時間に基づいて正規化
                base_data['時間'] = np.linspace(0, 100, len(time_range))
            else:  # "start" または "gps"
                # 開始時刻で揃えるか、GPSポイントで揃える場合は調整なし
                time_shift = timedelta(minutes=0)
            
            # 比較セッションのデータを生成
            all_data = [base_data]
            
            for session in comparison_sessions:
                # セッションごとに少し異なるデータを生成
                session_seed = hash(session) % 1000
                np.random.seed(session_seed)
                
                if metric_id == "speed":
                    session_data = self._generate_speed_sample(time_range, session_seed)
                elif metric_id == "vmg":
                    session_data = self._generate_vmg_sample(time_range, session_seed)
                elif metric_id == "wind_dir":
                    session_data = self._generate_wind_dir_sample(time_range, session_seed)
                elif metric_id == "wind_speed":
                    session_data = self._generate_wind_speed_sample(time_range, session_seed)
                else:
                    # 他のメトリクスは基本のパターンに少し変動を加える
                    session_data = pd.DataFrame({
                        '時間': time_range,
                        f'{metric_name} ({metric_unit})': (np.sin(np.linspace(0, 6*np.pi, 100) + session_seed * 0.01) * 5 + 10) * (0.9 + session_seed * 0.0002)
                    })
                
                session_data['セッション'] = session
                all_data.append(session_data)
            
            # すべてのデータを結合
            combined_data = pd.concat(all_data, ignore_index=True)
            
            # 時系列グラフの作成
            if st.session_state.comparison_time_alignment == "duration":
                # 所要時間正規化の場合はX軸を進捗率（%）で表示
                fig = px.line(
                    combined_data,
                    x='時間',
                    y=f'{metric_name} ({metric_unit})',
                    color='セッション',
                    title=f'{metric_name}の時間変化比較'
                )
                
                # X軸のラベル変更
                fig.update_layout(
                    xaxis_title='進捗 (%)',
                    yaxis_title=f'{metric_name} ({metric_unit})',
                    legend_title='セッション',
                    template='plotly_white'
                )
            else:
                # 通常の時間軸表示
                fig = px.line(
                    combined_data,
                    x='時間',
                    y=f'{metric_name} ({metric_unit})',
                    color='セッション',
                    title=f'{metric_name}の時間変化比較'
                )
                
                # レイアウトの調整
                fig.update_layout(
                    xaxis_title='時間',
                    yaxis_title=f'{metric_name} ({metric_unit})',
                    legend_title='セッション',
                    template='plotly_white'
                )
            
            # グラフの表示
            st.plotly_chart(fig, use_container_width=True)
            
            # 分布比較（ヒストグラム）
            st.markdown(f"#### {metric_name}の分布比較")
            
            # ヒストグラムの作成
            fig_hist = px.histogram(
                combined_data, 
                x=f'{metric_name} ({metric_unit})', 
                color='セッション',
                barmode='overlay',
                opacity=0.7,
                histnorm='percent',
                title=f'{metric_name}の分布比較'
            )
            
            # レイアウトの調整
            fig_hist.update_layout(
                xaxis_title=f'{metric_name} ({metric_unit})',
                yaxis_title='割合 (%)',
                legend_title='セッション',
                template='plotly_white'
            )
            
            st.plotly_chart(fig_hist, use_container_width=True)
            
            # 統計情報の表示
            st.markdown(f"#### {metric_name}の統計比較")
            
            # 各セッションの統計情報を計算
            stats_data = []
            for session_name in [current_session] + comparison_sessions:
                session_data = combined_data[combined_data['セッション'] == session_name][f'{metric_name} ({metric_unit})']
                
                stats_data.append({
                    'セッション': session_name,
                    '平均値': session_data.mean().round(2),
                    '最大値': session_data.max().round(2),
                    '最小値': session_data.min().round(2),
                    '標準偏差': session_data.std().round(2),
                    '中央値': session_data.median().round(2)
                })
            
            # 統計テーブルの表示
            st.dataframe(pd.DataFrame(stats_data), use_container_width=True)
            
            # セッション間の差分
            if len(comparison_sessions) > 0:
                st.markdown(f"#### {current_session} と他セッションとの差分")
                
                # 差分データの計算
                diff_data = {}
                base_values = combined_data[combined_data['セッション'] == current_session][f'{metric_name} ({metric_unit})'].values
                
                for session in comparison_sessions:
                    session_values = combined_data[combined_data['セッション'] == session][f'{metric_name} ({metric_unit})'].values
                    
                    # 各セッションの長さを合わせる
                    min_length = min(len(base_values), len(session_values))
                    
                    if min_length > 0:
                        diff = base_values[:min_length] - session_values[:min_length]
                        diff_df = pd.DataFrame({
                            '時間': time_range[:min_length],
                            f'差分 ({metric_unit})': diff,
                            'セッション比較': f'{current_session} - {session}'
                        })
                        
                        if 'time' in diff_data:
                            diff_data[session] = diff_df
                        else:
                            diff_data[session] = diff_df
                
                if diff_data:
                    # 差分の時系列グラフ
                    all_diff_data = pd.concat(diff_data.values(), ignore_index=True)
                    
                    fig_diff = px.line(
                        all_diff_data,
                        x='時間',
                        y=f'差分 ({metric_unit})',
                        color='セッション比較',
                        title=f'{metric_name}の差分'
                    )
                    
                    # レイアウトの調整
                    fig_diff.update_layout(
                        xaxis_title='時間',
                        yaxis_title=f'差分 ({metric_unit})',
                        legend_title='比較',
                        template='plotly_white'
                    )
                    
                    # ゼロ線の追加
                    fig_diff.add_hline(y=0, line_width=1, line_dash="dash", line_color="gray")
                    
                    st.plotly_chart(fig_diff, use_container_width=True)
            
            st.markdown("---")
    
    def render_map_comparison(self, 
                             current_session: str, 
                             comparison_sessions: List[str]) -> None:
        """GPSトラックの比較マップを表示
        
        Args:
            current_session: 現在のメインセッション
            comparison_sessions: 比較するセッションのリスト
        """
        if not comparison_sessions:
            return
        
        st.subheader("トラック比較")
        
        # MVPでは、マップ表示は実装せず、説明と将来の機能としてプレースホルダーを表示
        st.info("GPSトラック比較機能は完全実装ではプロジェクトのマップビューとの統合が必要です。MVPでは、サンプル画像で表現します。")
        
        # サンプルマップ画像
        st.image("https://via.placeholder.com/800x400?text=GPS+Track+Comparison", use_container_width=True)
        
        # 将来実装される機能の説明
        st.markdown("""
        完全実装では、以下の機能が提供される予定です：
        
        - 複数セッションのGPSトラックを同じマップ上に重ねて表示
        - 各トラックの色分けと透明度調整
        - 特定のポイント（マーク回航点など）での詳細比較
        - トラックの差分ヒートマップ（コース選択の違いを視覚化）
        - トラック間の距離分析
        """)
    
    def render_performance_polar_comparison(self, 
                                           current_session: str, 
                                           comparison_sessions: List[str]) -> None:
        """パフォーマンスポーラーの比較を表示
        
        Args:
            current_session: 現在のメインセッション
            comparison_sessions: 比較するセッションのリスト
        """
        if not comparison_sessions:
            return
        
        st.subheader("パフォーマンスポーラー比較")
        
        # 極座標データの生成（実際の実装では、セッションから実際のデータを取得）
        
        # 風向角度のデータポイント（0-360度）
        angles = np.linspace(0, 360, 72)
        
        # 現在のセッションのポーラーデータ生成
        np.random.seed(42)
        
        # 風向に応じた速度モデリング
        # 風上（0度付近）と風下（180度付近）で遅く、横風（90度、270度付近）で速い
        base_speed = 5.0
        angle_factor = 2.5 * np.sin(np.deg2rad(angles) * 2) + 0.5
        
        # 速度データ
        speeds = base_speed + angle_factor + np.random.normal(0, 0.2, len(angles))
        
        # 極座標プロット
        fig = go.Figure()
        
        # 現在のセッションのデータを追加
        fig.add_trace(go.Scatterpolar(
            r=speeds,
            theta=angles,
            mode='lines',
            name=current_session,
            line=dict(width=3)
        ))
        
        # 比較セッションのデータを追加
        for session in comparison_sessions:
            # セッションごとに少し異なるポーラーデータを生成
            session_seed = hash(session) % 1000
            np.random.seed(session_seed)
            
            # 基準から少し変えたデータ
            session_base = base_speed * (0.9 + session_seed * 0.0003)
            session_factor = angle_factor * (0.95 + session_seed * 0.0002)
            session_speeds = session_base + session_factor + np.random.normal(0, 0.2, len(angles))
            
            # プロットに追加
            fig.add_trace(go.Scatterpolar(
                r=session_speeds,
                theta=angles,
                mode='lines',
                name=session,
                line=dict(width=2)
            ))
        
        # レイアウトの設定
        fig.update_layout(
            title='パフォーマンスポーラー比較',
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 10]
                )
            ),
            showlegend=True,
            template='plotly_white'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _generate_speed_sample(self, time_range, seed=42):
        """速度サンプルデータの生成
        
        Args:
            time_range: 時間軸のデータ
            seed: 乱数シード
        
        Returns:
            pd.DataFrame: 生成されたデータフレーム
        """
        np.random.seed(seed)
        
        # トレンド成分（徐々に上昇して後半で下降）
        trend = np.concatenate([
            np.linspace(5.5, 7.0, 60),  # 上昇トレンド
            np.linspace(7.0, 6.0, 40)   # 下降トレンド
        ])
        
        # サイクル成分（風上/風下の繰り返し）
        cycles = np.sin(np.linspace(0, 4*np.pi, 100)) * 1.2
        
        # ノイズ成分
        noise = np.random.normal(0, 0.3, 100)
        
        # 速度データの生成
        speed_data = trend + cycles + noise
        
        # データフレーム作成
        return pd.DataFrame({
            '時間': time_range,
            '速度 (kt)': speed_data
        })
    
    def _generate_vmg_sample(self, time_range, seed=42):
        """VMGサンプルデータの生成
        
        Args:
            time_range: 時間軸のデータ
            seed: 乱数シード
        
        Returns:
            pd.DataFrame: 生成されたデータフレーム
        """
        np.random.seed(seed)
        
        # 風上と風下を交互に走るようなパターンを模倣
        stages = [
            {'start': 0, 'end': 20, 'type': '風上', 'base_vmg': 3.2},
            {'start': 20, 'end': 40, 'type': '風下', 'base_vmg': 4.5},
            {'start': 40, 'end': 60, 'type': '風上', 'base_vmg': 3.4},
            {'start': 60, 'end': 80, 'type': '風下', 'base_vmg': 4.7},
            {'start': 80, 'end': 100, 'type': '風上', 'base_vmg': 3.3}
        ]
        
        # VMGデータの生成
        vmg_values = []
        
        for stage in stages:
            length = stage['end'] - stage['start']
            # 各レグ内でパフォーマンスが向上するトレンド
            trend = np.linspace(stage['base_vmg']-0.2, stage['base_vmg']+0.3, length)
            
            # ノイズを追加
            np.random.seed(seed + stage['start'])
            noise = np.random.normal(0, 0.2, length)
            
            # タックやジャイブでの一時的な落ち込み
            if length > 10:
                indices = np.random.choice(range(3, length-3), 2, replace=False)
                for idx in indices:
                    noise[idx-2:idx+3] -= np.array([0.4, 0.8, 1.2, 0.8, 0.4])
            
            stage_vmg = trend + noise
            vmg_values.extend(stage_vmg)
        
        # データフレーム作成
        return pd.DataFrame({
            '時間': time_range,
            'VMG (kt)': vmg_values
        })
    
    def _generate_wind_dir_sample(self, time_range, seed=42):
        """風向サンプルデータの生成
        
        Args:
            time_range: 時間軸のデータ
            seed: 乱数シード
        
        Returns:
            pd.DataFrame: 生成されたデータフレーム
        """
        np.random.seed(seed)
        
        # 風向データを生成（徐々に変化する傾向と短期的な変動を含む）
        # 基本的な傾向 - 時間とともに右に振れる
        trend = np.linspace(180, 220, 100)
        
        # 短期的な変動
        oscillations = np.cumsum(np.random.normal(0, 1, 100))  # ランダムウォークで変動を模倣
        oscillations = oscillations * 3 / np.max(np.abs(oscillations))  # 変動幅を調整
        
        # 風向データ
        wind_dir_data = (trend + oscillations) % 360
        
        # データフレーム作成
        return pd.DataFrame({
            '時間': time_range,
            '風向 (度)': wind_dir_data
        })
    
    def _generate_wind_speed_sample(self, time_range, seed=42):
        """風速サンプルデータの生成
        
        Args:
            time_range: 時間軸のデータ
            seed: 乱数シード
        
        Returns:
            pd.DataFrame: 生成されたデータフレーム
        """
        np.random.seed(seed)
        
        # 風速データを生成
        base_wind_speed = 12.0
        wind_speed_trend = np.concatenate([
            np.linspace(base_wind_speed, base_wind_speed + 3, 40),  # 徐々に強くなる
            np.linspace(base_wind_speed + 3, base_wind_speed - 1, 60)  # 徐々に弱くなる
        ])
        
        wind_speed_oscillations = np.sin(np.linspace(0, 5*np.pi, 100)) * 1.2  # 周期的な変動
        wind_speed_noise = np.random.normal(0, 0.5, 100)  # ランダムな変動
        
        wind_speed_data = wind_speed_trend + wind_speed_oscillations + wind_speed_noise
        wind_speed_data = np.maximum(wind_speed_data, 0)  # 負の風速を除外
        
        # データフレーム作成
        return pd.DataFrame({
            '時間': time_range,
            '風速 (kt)': wind_speed_data
        })
