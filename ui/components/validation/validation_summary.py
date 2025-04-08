"""
ui.components.validation.validation_summary

検証結果のサマリーを表示するコンポーネント
強化バージョン：より視覚的で直感的な品質スコア表示と問題概要
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from sailing_data_processor.validation.quality_metrics import QualityMetricsCalculator
from sailing_data_processor.data_model.container import GPSDataContainer


class ValidationSummary:
    """
    検証結果のサマリーを表示するコンポーネント
    強化バージョン：より視覚的で直感的な品質スコア表示と問題概要
    
    Parameters
    ----------
    metrics_calculator : QualityMetricsCalculator
        品質メトリクス計算クラス
    container : Optional[GPSDataContainer], optional
        GPSデータコンテナ, by default None
    key_prefix : str, optional
        Streamlitのキープレフィックス, by default "validation_summary"
    on_fix_button_click : Optional[Callable[[], None]], optional
        修正ボタンがクリックされた際のコールバック, by default None
    """
    
    def __init__(self, 
                metrics_calculator: QualityMetricsCalculator, 
                container: Optional[GPSDataContainer] = None,
                key_prefix: str = "validation_summary",
                on_fix_button_click: Optional[Callable[[], None]] = None):
        """
        初期化
        
        Parameters
        ----------
        metrics_calculator : QualityMetricsCalculator
            品質メトリクス計算クラス
        container : Optional[GPSDataContainer], optional
            GPSデータコンテナ, by default None
        key_prefix : str, optional
            Streamlitのキープレフィックス, by default "validation_summary"
        on_fix_button_click : Optional[Callable[[], None]], optional
            修正ボタンがクリックされた際のコールバック, by default None
        """
        self.metrics_calculator = metrics_calculator
        self.container = container
        self.key_prefix = key_prefix
        self.on_fix_button_click = on_fix_button_click
        
        # 品質サマリーを取得
        self.quality_summary = self.metrics_calculator.get_quality_summary()
        
        # 品質スコアを取得
        self.quality_scores = self.metrics_calculator.quality_scores
        
        # 問題カテゴリとその日本語名
        self.category_names = {
            "missing_data": "欠損値",
            "out_of_range": "範囲外の値",
            "duplicates": "重複データ",
            "spatial_anomalies": "空間的異常",
            "temporal_anomalies": "時間的異常"
        }
        
        # 重要度の日本語名
        self.severity_names = {
            "error": "エラー",
            "warning": "警告",
            "info": "情報"
        }
        
        # 問題タイプごとの色の定義
        self.problem_type_colors = {
            "missing_data": "#3366CC",  # 青
            "out_of_range": "#DC3912",  # 赤
            "duplicates": "#FF9900",    # オレンジ
            "spatial_anomalies": "#109618",  # 緑
            "temporal_anomalies": "#990099"  # 紫
        }
        
        # 重要度ごとの色の定義
        self.severity_colors = {
            "error": "#DC3912",    # 赤
            "warning": "#FF9900",  # オレンジ
            "info": "#3366CC"      # 青
        }
        
        # セッション状態の初期化
        if f"{self.key_prefix}_selected_tab" not in st.session_state:
            st.session_state[f"{self.key_prefix}_selected_tab"] = "概要"
        
    def render(self):
        """
        サマリーを表示
        """
        with st.container():
            self._render_summary_header()
            
            # タブでセクションを分ける
            tabs = st.tabs(["概要", "カテゴリ別", "問題分布", "修正可能性"])
            
            with tabs[0]:
                self._render_overall_summary()
            
            with tabs[1]:
                self._render_category_summary()
            
            with tabs[2]:
                self._render_problem_distribution()
            
            with tabs[3]:
                self._render_fixability_summary()
    
    def _render_summary_header(self):
        """
        サマリーヘッダーを表示
        """
        st.markdown("## データ検証サマリー")
        
        # メトリック行を表示
        col1, col2, col3, col4 = st.columns(4)
        
        issue_counts = self.quality_summary["issue_counts"]
        
        with col1:
            st.metric(
                label="品質スコア", 
                value=f"{self.quality_scores['total']:.1f}/100",
                delta=None
            )
        
        with col2:
            problematic_percentage = issue_counts["problematic_percentage"]
            st.metric(
                label="問題のあるレコード", 
                value=f"{issue_counts['problematic_records']}/{issue_counts['total_records']}",
                delta=f"{problematic_percentage:.1f}%", 
                delta_color="inverse"
            )
        
        with col3:
            severity_counts = self.quality_summary["severity_counts"]
            st.metric(
                label="エラー数", 
                value=severity_counts["error"],
                delta=None,
                help="修正が必要な重大な問題"
            )
        
        with col4:
            fixable_counts = self.quality_summary["fixable_counts"]
            auto_fixable = fixable_counts["auto_fixable"] + fixable_counts["semi_auto_fixable"]
            total_issues = sum(fixable_counts.values())
            
            fixable_percentage = (auto_fixable / max(1, total_issues)) * 100
            
            st.metric(
                label="自動修正可能", 
                value=f"{auto_fixable}/{total_issues}",
                delta=f"{fixable_percentage:.1f}%",
                help="自動または半自動で修正可能な問題の割合"
            )
        
        # 区切り線
        st.divider()
    
    def _render_overall_summary(self):
        """
        全体的なサマリーを表示
        """
        # 品質スコアのゲージチャート
        col1, col2 = st.columns(2)
        
        with col1:
            # 品質スコアのゲージチャート
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=self.quality_scores["total"],
                title={"text": "データ品質スコア"},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": "darkblue"},
                    "steps": [
                        {"range": [0, 50], "color": "red"},
                        {"range": [50, 75], "color": "orange"},
                        {"range": [75, 90], "color": "yellow"},
                        {"range": [90, 100], "color": "green"}
                    ],
                    "threshold": {
                        "line": {"color": "black", "width": 4},
                        "thickness": 0.75,
                        "value": self.quality_scores["total"]
                    }
                }
            ))
            
            fig.update_layout(
                height=250,
                margin=dict(t=30, b=0, l=30, r=30)
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # カテゴリ別スコアのバーチャート
            categories = ["completeness", "accuracy", "consistency"]
            values = [self.quality_scores[cat] for cat in categories]
            
            # カテゴリ名の日本語対応
            category_names = {
                "completeness": "完全性",
                "accuracy": "正確性",
                "consistency": "一貫性"
            }
            
            display_categories = [category_names[cat] for cat in categories]
            
            fig = go.Figure(data=[
                go.Bar(
                    x=display_categories,
                    y=values,
                    marker_color=['#1f77b4', '#ff7f0e', '#2ca02c'],
                    text=[f"{val:.1f}" for val in values],
                    textposition="auto"
                )
            ])
            
            fig.update_layout(
                title="カテゴリ別スコア",
                yaxis_range=[0, 100],
                height=250,
                margin=dict(t=50, b=0, l=30, r=30),
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # サマリー情報を表形式で表示
        st.markdown("### データ検証結果の詳細")
        
        issue_counts = self.quality_summary["issue_counts"]
        severity_counts = self.quality_summary["severity_counts"]
        fixable_counts = self.quality_summary["fixable_counts"]
        
        # データ検証の要約情報
        data = {
            "カテゴリ": [
                "総レコード数", "問題ありレコード数", "問題ありレコード比率",
                "エラー", "警告", "情報",
                "自動修正可能", "半自動修正可能", "手動修正必要"
            ],
            "値": [
                issue_counts["total_records"],
                issue_counts["problematic_records"],
                f"{issue_counts['problematic_percentage']:.2f}%",
                severity_counts["error"],
                severity_counts["warning"],
                severity_counts["info"],
                fixable_counts["auto_fixable"],
                fixable_counts["semi_auto_fixable"],
                fixable_counts["manual_fix_required"]
            ]
        }
        
        # DataFrameに変換して表示
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    
    def _render_category_summary(self):
        """
        カテゴリ別のサマリーを表示
        """
        # 問題タイプ別の問題数
        problem_counts = {
            category: len(self.metrics_calculator.problematic_indices[key])
            for key, category in self.category_names.items()
        }
        
        # 問題の重要度分布
        severity_counts = self.quality_summary["severity_counts"]
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 問題タイプ別のチャート
            fig = go.Figure()
            
            non_zero_counts = {k: v for k, v in problem_counts.items() if v > 0}
            
            if non_zero_counts:
                fig.add_trace(go.Pie(
                    labels=list(non_zero_counts.keys()),
                    values=list(non_zero_counts.values()),
                    hole=0.4,
                    marker_colors=['blue', 'red', 'green', 'purple', 'orange']
                ))
                
                fig.update_layout(
                    title="問題タイプの分布",
                    height=300,
                    margin=dict(t=50, b=0, l=30, r=30)
                )
            else:
                fig.update_layout(
                    title="問題タイプの分布 (問題なし)",
                    annotations=[{
                        'text': '問題は検出されませんでした',
                        'showarrow': False,
                        'x': 0.5,
                        'y': 0.5
                    }],
                    height=300,
                    margin=dict(t=50, b=0, l=30, r=30)
                )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # 重要度別のチャート
            fig = go.Figure()
            
            non_zero_severity = {k: v for k, v in severity_counts.items() if v > 0}
            
            if non_zero_severity:
                fig.add_trace(go.Pie(
                    labels=[self.severity_names[k] for k in non_zero_severity.keys()],
                    values=list(non_zero_severity.values()),
                    hole=0.4,
                    marker_colors=['red', 'orange', 'blue']
                ))
                
                fig.update_layout(
                    title="問題の重要度分布",
                    height=300,
                    margin=dict(t=50, b=0, l=30, r=30)
                )
            else:
                fig.update_layout(
                    title="問題の重要度分布 (問題なし)",
                    annotations=[{
                        'text': '問題は検出されませんでした',
                        'showarrow': False,
                        'x': 0.5,
                        'y': 0.5
                    }],
                    height=300,
                    margin=dict(t=50, b=0, l=30, r=30)
                )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # カテゴリ別の詳細スコア
        st.markdown("### カテゴリ別の詳細スコア")
        
        category_scores = self.metrics_calculator.category_scores
        
        # カテゴリ別スコアの詳細表
        rows = []
        
        for category, details in category_scores.items():
            cat_name = {
                "completeness": "完全性",
                "accuracy": "正確性", 
                "consistency": "一貫性"
            }.get(category, category)
            
            rows.append({
                "カテゴリ": cat_name,
                "スコア": f"{details['score']:.1f}/100",
                "問題数": details["issues"],
                "詳細": ', '.join([k for k, v in details.get("details", {}).items() if v])
            })
        
        # DataFrameに変換して表示
        if rows:
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("カテゴリ別スコアの詳細情報はありません。")
    
    def _render_problem_distribution(self):
        """
        問題の分布を表示
        """
        # 問題タイプごとの件数とその分布を表示
        st.markdown("### 問題タイプ別の分布")
        
        problem_indices = self.metrics_calculator.problematic_indices
        
        # 問題カウントを取得
        problem_counts = {
            type_key: len(indices) 
            for type_key, indices in problem_indices.items() 
            if type_key != "all"
        }
        
        # 問題がない場合のメッセージ
        if sum(problem_counts.values()) == 0:
            st.info("問題は検出されませんでした。")
            return
        
        # 表形式で問題タイプごとの件数を表示
        problem_data = []
        
        for type_key, count in problem_counts.items():
            if count > 0:
                problem_data.append({
                    "問題タイプ": self.category_names.get(type_key, type_key),
                    "件数": count,
                    "全体に対する割合": f"{(count / max(1, len(problem_indices['all'])) * 100):.1f}%"
                })
        
        if problem_data:
            df = pd.DataFrame(problem_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        
        # 水平バーチャートで視覚化
        if problem_data:
            fig = px.bar(
                df, 
                x="件数", 
                y="問題タイプ",
                color="問題タイプ",
                orientation='h',
                title="問題タイプ別の件数",
                text="件数"
            )
            
            fig.update_layout(
                height=300,
                margin=dict(t=50, b=0, l=30, r=30),
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # 問題の詳細情報（各カテゴリの詳細）
        st.markdown("### 各問題タイプの詳細")
        
        # 問題タイプの詳細情報
        problem_type_distribution = self.metrics_calculator.problem_distribution.get("problem_type", {})
        
        if problem_type_distribution.get("has_data", False):
            problem_details = problem_type_distribution.get("problem_details", {})
            
            for problem_type, details in problem_details.items():
                # 問題タイプごとのエキスパンダー
                with st.expander(f"{self.category_names.get(problem_type, problem_type)} の詳細", expanded=False):
                    st.write(f"**合計**: {details.get('total_count', 0)}件")
                    
                    # 欠損値
                    if problem_type == "missing_data" and "affected_columns" in details:
                        st.write("**影響を受けるカラム:**")
                        for col, count in details["affected_columns"].items():
                            st.write(f"- {col}: {count}件")
                    
                    # 範囲外の値
                    elif problem_type == "out_of_range" and "affected_columns" in details:
                        st.write("**影響を受けるカラム:**")
                        for col, info in details["affected_columns"].items():
                            if isinstance(info, dict):
                                st.write(f"- {col}: {info.get('count', 0)}件")
                                if 'min_value' in info and 'max_value' in info:
                                    st.write(f"  許容範囲: {info['min_value']} ~ {info['max_value']}")
                                if 'actual_min' in info and 'actual_max' in info:
                                    st.write(f"  実際の範囲: {info['actual_min']} ~ {info['actual_max']}")
                            else:
                                st.write(f"- {col}: {info}件")
                    
                    # 重複
                    elif problem_type == "duplicates" and "affected_columns" in details:
                        st.write("**重複情報:**")
                        for col, info in details["affected_columns"].items():
                            if isinstance(info, dict):
                                st.write(f"- {col}: {info.get('count', 0)}件の重複")
                                if 'duplicate_timestamps_count' in info:
                                    st.write(f"  重複タイムスタンプ数: {info['duplicate_timestamps_count']}")
                            else:
                                st.write(f"- {col}: {info}件")
                    
                    # 空間的異常
                    elif problem_type == "spatial_anomalies" and "affected_attributes" in details:
                        st.write("**空間的異常の詳細:**")
                        for attr, info in details["affected_attributes"].items():
                            if isinstance(info, dict):
                                st.write(f"- {attr}: {info.get('count', 0)}件の異常")
                                if 'max_speed' in info:
                                    st.write(f"  最大速度: {info['max_speed']:.1f}ノット")
                            else:
                                st.write(f"- {attr}: {info}件")
                    
                    # 時間的異常
                    elif problem_type == "temporal_anomalies" and "affected_attributes" in details:
                        st.write("**時間的異常の詳細:**")
                        for attr, info in details["affected_attributes"].items():
                            if isinstance(info, dict):
                                if 'gap_count' in info:
                                    st.write(f"- 時間ギャップ: {info['gap_count']}件")
                                if 'reverse_count' in info:
                                    st.write(f"- 時間逆行: {info['reverse_count']}件")
                                if 'max_gap' in info:
                                    st.write(f"  最大ギャップ: {info['max_gap']:.1f}秒")
                            else:
                                st.write(f"- {attr}: {info}件")
        else:
            st.info("問題タイプの詳細情報はありません。")
    
    def _render_fixability_summary(self):
        """
        修正可能性のサマリーを表示
        """
        st.markdown("### 修正可能性の概要")
        
        fixable_counts = self.quality_summary["fixable_counts"]
        
        # 修正可能性のグラフを表示
        if sum(fixable_counts.values()) > 0:
            # 円グラフのデータ
            labels = ["自動修正可能", "半自動修正可能", "手動修正必要"]
            values = [
                fixable_counts["auto_fixable"],
                fixable_counts["semi_auto_fixable"],
                fixable_counts["manual_fix_required"]
            ]
            colors = ["green", "orange", "red"]
            
            # 値が0のものを除外
            non_zero = [(l, v, c) for l, v, c in zip(labels, values, colors) if v > 0]
            
            if non_zero:
                labels, values, colors = zip(*non_zero)
                
                # 円グラフを作成
                fig = go.Figure(data=[
                    go.Pie(
                        labels=labels,
                        values=values,
                        hole=0.4,
                        marker_colors=colors
                    )
                ])
                
                fig.update_layout(
                    title="修正可能性の分布",
                    height=300,
                    margin=dict(t=50, b=0, l=30, r=30)
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # 修正可能性の説明
                st.markdown("""
                **修正可能性の説明:**
                
                - **自動修正可能**: システムが自動的に修正できる問題です（例: 重複タイムスタンプの調整）
                - **半自動修正可能**: ユーザーの確認や選択を必要とする修正が可能な問題です（例: 欠損値の補間）
                - **手動修正必要**: 手動での介入が必要な問題です（例: 必須カラムの欠落）
                """)
                
                # 自動修正推奨の表示
                if fixable_counts["auto_fixable"] > 0 or fixable_counts["semi_auto_fixable"] > 0:
                    st.markdown("### 修正オプション")
                    
                    # 自動修正の説明と実行ボタン
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown("""
                        **自動修正**を実行すると、システムが自動的に修正可能な問題を処理します：
                        - 重複タイムスタンプの調整
                        - 欠損値の線形補間
                        - 範囲外の値のクリッピング
                        - 時間的異常の処理
                        """)
                    
                    with col2:
                        # 自動修正ボタン（実際の処理は呼び出し側で実装）
                        st.button(
                            "自動修正を実行", 
                            key=f"{self.key_prefix}_auto_fix_button",
                            type="primary",
                            help="自動修正が適用可能な問題を自動的に修正します"
                        )
            else:
                st.info("修正可能な問題はありません。")
        else:
            st.info("修正可能な問題はありません。")
