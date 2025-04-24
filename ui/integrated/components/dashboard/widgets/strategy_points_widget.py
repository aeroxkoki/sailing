# -*- coding: utf-8 -*-
"""
ui.integrated.components.dashboard.widgets.strategy_points_widget

戦略ポイントデータのサマリーを表示するダッシュボードウィジェット
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

class StrategyPointsWidget:
    """戦略ポイントサマリーウィジェット"""
    
    def __init__(self):
        """初期化"""
        self.title = "戦略ポイントサマリー"
    
    def render(self, strategy_points):
        """
        戦略ポイントサマリーウィジェットの描画
        
        Parameters
        ----------
        strategy_points : dict
            戦略ポイントのデータ
            {
                'total': 合計数,
                'types': {'タイプ名': 数, ...},
                'importance': {'重要度': 数, ...},
                'quality': {'品質': 数, ...}
            }
        """
        # カードのスタイル設定
        with st.container():
            st.write(f"### {self.title}")
            
            # 基本情報の表示
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("検出数", strategy_points['total'])
            
            with col2:
                # 重要度の高いポイント数
                high_importance = strategy_points['importance'].get('最高', 0) + strategy_points['importance'].get('高', 0)
                st.metric("重要ポイント数", high_importance)
            
            with col3:
                # 判断不適切なポイント数
                suboptimal_decisions = strategy_points['quality'].get('改善必要', 0) + strategy_points['quality'].get('不適切', 0)
                st.metric("要改善ポイント", suboptimal_decisions)
            
            # 戦略ポイントタイプの円グラフ
            self._render_type_breakdown(strategy_points['types'])
            
            # 戦略ポイントの重要度と判断品質のヒートマップ
            self._render_importance_quality_matrix(strategy_points)
    
    def _render_type_breakdown(self, type_data):
        """
        戦略ポイントタイプの内訳を円グラフで表示
        
        Parameters
        ----------
        type_data : dict
            戦略ポイントタイプごとの数
            {'タイプ名': 数, ...}
        """
        # データ変換
        df = pd.DataFrame({
            'type': list(type_data.keys()),
            'count': list(type_data.values())
        })
        
        # 戦略ポイントタイプのカラーマップ
        color_map = {
            'タック': 'green',
            '風向シフト': 'blue',
            'レイライン': 'purple',
            'ジャイブ': 'orange',
            'その他': 'gray'
        }
        
        # 円グラフの作成
        fig = px.pie(
            df, 
            values='count', 
            names='type',
            color='type',
            color_discrete_map=color_map,
            title="戦略ポイントタイプ"
        )
        
        # レイアウト設定
        fig.update_layout(
            height=240,
            margin=dict(l=10, r=10, t=40, b=10),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5
            )
        )
        
        # プロットの表示
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    def _render_importance_quality_matrix(self, strategy_points):
        """
        重要度と判断品質のマトリックスをヒートマップで表示
        
        Parameters
        ----------
        strategy_points : dict
            戦略ポイントのデータ
        """
        # 重要度と判断品質のデータを組み合わせてマトリックスを作成
        # 実際の実装では、戦略ポイントの詳細データからこのマトリックスを生成
        
        # サンプルマトリックスデータ（実際の実装では計算）
        importance_levels = ['最高', '高', '中', '低']
        quality_levels = ['最適', '適切', '改善必要', '不適切']
        
        # マトリックスの初期化
        matrix = np.zeros((len(importance_levels), len(quality_levels)))
        
        # サンプルデータの作成（実際の実装では実データから計算）
        # この例ではランダムに割り当てるが、重要度が高いほど最適な判断が多くなるようにバイアス
        for i, imp in enumerate(importance_levels):
            for j, qual in enumerate(quality_levels):
                # 実際の実装では、戦略ポイントごとの重要度と判断品質から計算
                # ここではサンプル値として固定値を設定
                if imp == '最高' and qual == '最適':
                    matrix[i, j] = 2
                elif imp == '高' and qual == '最適':
                    matrix[i, j] = 3
                elif imp == '中' and qual == '適切':
                    matrix[i, j] = 2
                elif imp == '低' and qual == '適切':
                    matrix[i, j] = 2
                elif imp == '最高' and qual == '改善必要':
                    matrix[i, j] = 1
                elif imp == '高' and qual == '不適切':
                    matrix[i, j] = 1
                elif imp == '中' and qual == '改善必要':
                    matrix[i, j] = 2
                elif imp == '低' and qual == '不適切':
                    matrix[i, j] = 1
                elif imp == '最高' and qual == '不適切':
                    matrix[i, j] = 1
                else:
                    matrix[i, j] = 0
        
        # ヒートマップの作成
        fig = go.Figure(data=go.Heatmap(
            z=matrix,
            x=quality_levels,
            y=importance_levels,
            colorscale='Viridis',
            hoverongaps=False,
            text=matrix.astype(int).astype(str),
            texttemplate="%{text}",
            showscale=False
        ))
        
        # レイアウト設定
        fig.update_layout(
            title="重要度と判断品質のマトリックス",
            height=240,
            margin=dict(l=10, r=10, t=40, b=10),
            xaxis=dict(title="判断品質"),
            yaxis=dict(title="重要度")
        )
        
        # プロットの表示
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        # 分析インサイト
        with st.expander("分析インサイト", expanded=False):
            # 戦略ポイントの分析結果
            high_impact_points = strategy_points['importance'].get('最高', 0) + strategy_points['importance'].get('高', 0)
            optimal_decisions = strategy_points['quality'].get('最適', 0) + strategy_points['quality'].get('適切', 0)
            
            optimal_ratio = optimal_decisions / strategy_points['total'] * 100 if strategy_points['total'] > 0 else 0
            
            st.markdown(f"**戦略判断の分析:**")
            st.markdown(f"- 重要な戦略ポイント: {high_impact_points}箇所 (全体の{high_impact_points/strategy_points['total']*100:.1f}%)")
            st.markdown(f"- 最適な判断の割合: {optimal_ratio:.1f}%")
            
            # 主要な改善ポイント
            st.markdown("**主な改善ポイント:**")
            
            improvement_points = [
                "風向シフトへの対応速度向上",
                "レイライン接近時の最適角度",
                "タックのタイミング最適化"
            ]
            
            for point in improvement_points:
                st.markdown(f"- {point}")
