"""
ui.integrated.components.dashboard.widgets.data_quality_widget

データ品質情報のサマリーを表示するダッシュボードウィジェット
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

class DataQualityWidget:
    """データ品質サマリーウィジェット"""
    
    def __init__(self):
        """初期化"""
        self.title = "データ品質サマリー"
    
    def render(self, data_quality):
        """
        データ品質サマリーウィジェットの描画
        
        Parameters
        ----------
        data_quality : dict
            データ品質情報を含む辞書
            {
                'gps_quality': GPS品質スコア (0-100),
                'data_completeness': データ完全性スコア (0-100),
                'issues': {
                    'total': 問題の総数,
                    'fixed': 修正された問題数,
                    'types': {'問題タイプ': 数, ...}
                },
                'coverage': {
                    'データタイプ': カバレッジ率 (0-100), ...
                }
            }
        """
        # カードのスタイル設定
        with st.container():
            st.write(f"### {self.title}")
            
            # 基本情報の表示
            col1, col2, col3 = st.columns(3)
            
            with col1:
                gps_quality = data_quality['gps_quality']
                color = "normal" if gps_quality >= 95 else ("off" if gps_quality < 80 else "")
                st.metric("GPS品質", f"{gps_quality}%", delta_color=color)
            
            with col2:
                completeness = data_quality['data_completeness']
                color = "normal" if completeness >= 95 else ("off" if completeness < 80 else "")
                st.metric("データ完全性", f"{completeness}%", delta_color=color)
            
            with col3:
                issues = data_quality['issues']
                fixed_ratio = issues['fixed'] / issues['total'] if issues['total'] > 0 else 1.0
                st.metric("問題解決率", f"{fixed_ratio * 100:.0f}%", f"{issues['fixed']}/{issues['total']} 修正済")
            
            # データカバレッジのチャート
            self._render_coverage_chart(data_quality['coverage'])
            
            # 問題タイプの内訳を表示
            self._render_issues_breakdown(data_quality['issues'])
    
    def _render_coverage_chart(self, coverage_data):
        """
        データカバレッジのチャートを描画
        
        Parameters
        ----------
        coverage_data : dict
            データタイプごとのカバレッジ率
            {'データタイプ': カバレッジ率 (0-100), ...}
        """
        # データ変換
        df = pd.DataFrame({
            'data_type': list(coverage_data.keys()),
            'coverage': list(coverage_data.values())
        })
        
        # カバレッジのソート
        df = df.sort_values(by='coverage', ascending=False)
        
        # バーチャートの作成
        fig = px.bar(
            df,
            y='data_type',
            x='coverage',
            orientation='h',
            title="データカバレッジ",
            labels={'data_type': 'データタイプ', 'coverage': 'カバレッジ率 (%)'},
            color='coverage',
            color_continuous_scale=['red', 'yellow', 'green'],
            range_color=[0, 100]
        )
        
        # レイアウト設定
        fig.update_layout(
            height=200,
            margin=dict(l=0, r=0, t=40, b=0),
            coloraxis_showscale=False,
            xaxis=dict(range=[0, 100])
        )
        
        # 基準線の追加
        fig.add_vline(x=90, line_dash="dash", line_color="gray")
        
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    def _render_issues_breakdown(self, issues_data):
        """
        問題タイプの内訳を表示
        
        Parameters
        ----------
        issues_data : dict
            問題に関する情報
            {
                'total': 問題の総数,
                'fixed': 修正された問題数,
                'types': {'問題タイプ': 数, ...}
            }
        """
        # 問題の種類
        types = issues_data.get('types', {})
        
        if not types:
            st.info("データ品質の問題は検出されていません。")
            return
        
        # 問題タイプの内訳
        with st.expander("検出された問題", expanded=False):
            # データフレームを作成
            df = pd.DataFrame({
                '問題タイプ': list(types.keys()),
                '件数': list(types.values())
            })
            
            # テーブル表示
            st.dataframe(df, use_container_width=True)
            
            # 修正ステータス
            if issues_data['fixed'] < issues_data['total']:
                remaining = issues_data['total'] - issues_data['fixed']
                st.warning(f"未修正の問題が {remaining} 件あります。データバリデーションページで修正することをお勧めします。")
            else:
                st.success("すべての問題が修正されています。")
