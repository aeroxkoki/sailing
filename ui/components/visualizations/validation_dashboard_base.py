# -*- coding: utf-8 -*-
"""
ui.components.visualizations.validation_dashboard_base

データ検証ダッシュボードの基本クラス
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Callable
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

from sailing_data_processor.data_model.container import GPSDataContainer
from sailing_data_processor.validation.data_validator import DataValidator
from sailing_data_processor.validation.quality_metrics import QualityMetricsCalculator
from sailing_data_processor.validation.visualization import ValidationVisualizer


class ValidationDashboardBase:
    """
    データ検証ダッシュボードの基本クラス
    
    Parameters
    ----------
    container : GPSDataContainer
        GPSデータコンテナ
    validator : Optional[DataValidator], optional
        データ検証器, by default None
    key_prefix : str, optional
        Streamlitのキープレフィックス, by default "validation_dashboard"
    """
    
    def __init__(self, 
                container: GPSDataContainer, 
                validator: Optional[DataValidator] = None,
                key_prefix: str = "validation_dashboard"):
        """
        初期化
        
        Parameters
        ----------
        container : GPSDataContainer
            GPSデータコンテナ
        validator : Optional[DataValidator], optional
            データ検証器, by default None
        key_prefix : str, optional
            Streamlitのキープレフィックス, by default "validation_dashboard"
        """
        self.container = container
        self.validator = validator or DataValidator()
        self.key_prefix = key_prefix
        
        # 検証が実行されていない場合は実行
        if not self.validator.validation_results:
            self.validator.validate(self.container)
        
        # メトリクス計算とビジュアライザーを初期化
        self.metrics_calculator = QualityMetricsCalculator(
            self.validator.validation_results,
            self.container.data
        )
        self.visualizer = ValidationVisualizer(
            self.metrics_calculator,
            self.container.data
        )
        
        # セッション状態の初期化
        if f"{self.key_prefix}_selected_problem_type" not in st.session_state:
            st.session_state[f"{self.key_prefix}_selected_problem_type"] = "all"
        
        if f"{self.key_prefix}_selected_severity" not in st.session_state:
            st.session_state[f"{self.key_prefix}_selected_severity"] = ["error", "warning", "info"]
        
        # 問題タイプの日本語表示名
        self.problem_type_names = {
            "all": "すべての問題",
            "missing_data": "欠損値",
            "out_of_range": "範囲外の値",
            "duplicates": "重複データ",
            "spatial_anomalies": "空間的異常",
            "temporal_anomalies": "時間的異常"
        }
        
        # 重要度の日本語表示名
        self.severity_names = {
            "error": "エラー",
            "warning": "警告",
            "info": "情報"
        }
    
    def render(self):
        """
        ダッシュボードをレンダリング
        """
        st.subheader("データ検証ダッシュボード")
        
        # ダッシュボードコントロールの追加
        self._render_dashboard_controls()
        
        # 概要、詳細、アクションの3タブを作成
        tab1, tab2, tab3, tab4 = st.tabs(["概要", "詳細", "アクション", "拡張分析"])
        
        with tab1:
            self._render_overview_section()
        
        with tab2:
            self._render_details_section()
        
        with tab3:
            self._render_action_section()
            
        with tab4:
            self._render_extended_analysis_section()
    
    def _render_overview_section(self):
        """
        概要セクションをレンダリング
        """
        st.write("### データ品質の概要")
        
        # 品質サマリーを取得
        quality_summary = self.metrics_calculator.get_quality_summary()
        quality_scores = self.metrics_calculator.quality_scores
        
        # 品質スコアの表示
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("総合品質スコア", f"{quality_scores['total']:.1f}/100")
        
        with col2:
            issue_counts = quality_summary["issue_counts"]
            st.metric("問題のあるレコード", 
                    f"{issue_counts['problematic_records']}/{issue_counts['total_records']}",
                    f"{issue_counts['problematic_percentage']:.1f}%")
        
        with col3:
            fixable_counts = quality_summary["fixable_counts"]
            auto_fixable = fixable_counts["auto_fixable"] + fixable_counts["semi_auto_fixable"]
            st.metric("自動修正可能な問題", 
                    f"{auto_fixable}",
                    f"{auto_fixable / max(1, sum(fixable_counts.values())) * 100:.1f}%")
        
        # 品質スコアのゲージとカテゴリスコアの可視化
        col1, col2 = st.columns(2)
        
        with col1:
            quality_gauge = self.visualizer.generate_quality_score_chart()
            st.plotly_chart(quality_gauge, use_container_width=True)
        
        with col2:
            category_chart = self.visualizer.generate_category_scores_chart()
            st.plotly_chart(category_chart, use_container_width=True)
        
        # 問題分布の円グラフ
        problem_dist = self.visualizer.generate_problem_distribution_chart()
        st.plotly_chart(problem_dist, use_container_width=True)
        
        # 空間的な問題分布
        st.write("### 空間的な問題分布")
        problem_heatmap = self.visualizer.generate_problem_heatmap()
        st.plotly_chart(problem_heatmap, use_container_width=True)
        
        # 時間的な問題分布
        st.write("### 時間的な問題分布")
        timeline_chart = self.visualizer.generate_timeline_chart()
        st.plotly_chart(timeline_chart, use_container_width=True)
    
    def _render_details_section(self):
        """
        詳細セクションをレンダリング
        """
        st.write("### 詳細分析")
        
        # フィルタリングコントロール
        col1, col2 = st.columns(2)
        
        with col1:
            # 問題タイプの選択
            problem_types = list(self.problem_type_names.keys())
            
            selected_index = problem_types.index(st.session_state[f"{self.key_prefix}_selected_problem_type"]) \
                            if st.session_state[f"{self.key_prefix}_selected_problem_type"] in problem_types else 0
            
            selected_option = st.selectbox(
                "問題タイプで絞り込み",
                options=problem_types,
                format_func=lambda x: self.problem_type_names.get(x, x),
                index=selected_index,
                key=f"{self.key_prefix}_problem_type_selector"
            )
            
            # 選択された問題タイプを保存
            st.session_state[f"{self.key_prefix}_selected_problem_type"] = selected_option
        
        with col2:
            # 重要度の選択
            severity_types = list(self.severity_names.keys())
            
            selected_severity = st.multiselect(
                "重要度で絞り込み",
                options=severity_types,
                default=st.session_state[f"{self.key_prefix}_selected_severity"],
                format_func=lambda x: self.severity_names.get(x, x),
                key=f"{self.key_prefix}_severity_selector"
            )
            
            # 選択された重要度を保存（空の場合はすべて選択）
            if not selected_severity:
                selected_severity = severity_types
            
            st.session_state[f"{self.key_prefix}_selected_severity"] = selected_severity
        
        # 問題リストの表示
        self._render_filtered_problem_list(
            selected_option,
            selected_severity
        )
        
        # 拡張分析
        self._render_extended_analysis()
    
    def _render_filtered_problem_list(self, problem_type: str, severity_list: List[str]):
        """
        フィルタリングされた問題リストを表示
        
        Parameters
        ----------
        problem_type : str
            選択された問題タイプ
        severity_list : List[str]
            選択された重要度リスト
        """
        # 問題リストのフィルタリング
        filtered_issues = []
        
        for result in self.validator.validation_results:
            if not result["is_valid"] and result["severity"] in severity_list:
                # 問題タイプでフィルタリング
                if problem_type == "all":
                    filtered_issues.append(result)
                elif problem_type == "missing_data" and "No Null Values Check" in result["rule_name"]:
                    filtered_issues.append(result)
                elif problem_type == "out_of_range" and "Value Range Check" in result["rule_name"]:
                    filtered_issues.append(result)
                elif problem_type == "duplicates" and "No Duplicate Timestamps" in result["rule_name"]:
                    filtered_issues.append(result)
                elif problem_type == "spatial_anomalies" and "Spatial Consistency Check" in result["rule_name"]:
                    filtered_issues.append(result)
                elif problem_type == "temporal_anomalies" and "Temporal Consistency Check" in result["rule_name"]:
                    filtered_issues.append(result)
        
        if filtered_issues:
            st.write(f"**{len(filtered_issues)}件の問題が見つかりました**")
            
            # 問題リストをテーブル形式で表示
            problem_data = []
            
            for i, issue in enumerate(filtered_issues):
                severity = issue["severity"]
                rule_name = issue["rule_name"]
                details = issue["details"]
                
                # 問題の件数と説明を取得
                issue_count = 0
                description = ""
                
                if "out_of_range_count" in details:
                    issue_count = details["out_of_range_count"]
                    column = details.get("column", "")
                    description = f"カラム '{column}' に範囲外の値が {issue_count}個"
                elif "total_null_count" in details:
                    issue_count = details["total_null_count"]
                    description = f"欠損値が {issue_count}個"
                elif "duplicate_count" in details:
                    issue_count = details["duplicate_count"]
                    description = f"重複タイムスタンプが {issue_count}個"
                elif "anomaly_count" in details:
                    issue_count = details["anomaly_count"]
                    description = f"空間的異常が {issue_count}個"
                elif "gap_count" in details or "reverse_count" in details:
                    gap_count = details.get("gap_count", 0)
                    reverse_count = details.get("reverse_count", 0)
                    issue_count = gap_count + reverse_count
                    
                    if gap_count > 0 and reverse_count > 0:
                        description = f"時間ギャップが {gap_count}個、時間逆行が {reverse_count}個"
                    elif gap_count > 0:
                        description = f"時間ギャップが {gap_count}個"
                    elif reverse_count > 0:
                        description = f"時間逆行が {reverse_count}個"
                else:
                    # その他の問題
                    description = rule_name
                
                # レコードを追加
                problem_data.append({
                    "ID": i + 1,
                    "重要度": severity,
                    "ルール": rule_name,
                    "件数": issue_count,
                    "説明": description
                })
            
            # データフレームに変換
            problem_df = pd.DataFrame(problem_data)
            
            # 表示
            st.dataframe(problem_df, use_container_width=True)
            
            # 問題詳細の表示
            st.write("### 問題の詳細表示")
            
            selected_problem_id = st.selectbox(
                "詳細を表示する問題を選択:",
                options=problem_df["ID"].tolist(),
                format_func=lambda x: f"問題 #{x}: {problem_df[problem_df['ID']==x]['説明'].values[0]}",
                key=f"{self.key_prefix}_problem_select"
            )
            
            # 選択された問題の詳細を表示
            if selected_problem_id:
                # 問題インデックスを取得
                problem_idx = selected_problem_id - 1
                
                if problem_idx < len(filtered_issues):
                    issue = filtered_issues[problem_idx]
                    
                    # 問題の詳細を表示
                    with st.expander("問題の詳細", expanded=True):
                        # 詳細情報を表示
                        st.write(f"**ルール:** {issue['rule_name']}")
                        st.write(f"**説明:** {issue['description']}")
                        st.write(f"**重要度:** {issue['severity']}")
                        
                        # 詳細情報
                        details = issue["details"]
                        
                        for k, v in details.items():
                            if k not in ["error", "message"]:
                                if isinstance(v, list) and len(v) > 10:
                                    st.write(f"**{k}:** {v[:10]} ... (他 {len(v) - 10} 項目)")
                                elif isinstance(v, dict) and len(v) > 10:
                                    st.write(f"**{k}:** {dict(list(v.items())[:10])} ... (他 {len(v) - 10} 項目)")
                                else:
                                    st.write(f"**{k}:** {v}")
        else:
            st.info("選択された条件に一致する問題は見つかりませんでした。")
    
    def _render_extended_analysis(self):
        """
        拡張分析セクションをレンダリング
        """
        st.write("### 拡張分析")
        
        # 時間的品質メトリクス
        with st.expander("時間的品質メトリクス", expanded=False):
            temporal_metrics = self.metrics_calculator.get_extended_temporal_metrics()
            
            if temporal_metrics.get("has_data", False):
                # 時間帯品質スコアの表示
                if "time_quality_scores" in temporal_metrics and temporal_metrics["time_quality_scores"]:
                    scores = temporal_metrics["time_quality_scores"]
                    
                    # データフレーム作成
                    score_df = pd.DataFrame(scores)
                    
                    # チャート作成
                    fig = px.bar(
                        score_df, 
                        x="label", 
                        y="quality_score",
                        labels={"quality_score": "品質スコア", "label": "時間帯"},
                        title="時間帯別の品質スコア",
                        color="quality_score",
                        color_continuous_scale=["red", "orange", "yellow", "green"],
                        range_color=[0, 100],
                        hover_data=["problem_count", "total_count"]
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                
                # 時間統計情報の表示
                if "time_stats" in temporal_metrics:
                    stats = temporal_metrics["time_stats"]
                    st.write("#### 時間統計")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("レコード数", stats.get("record_count", 0))
                    
                    with col2:
                        duration_hours = stats.get("duration_seconds", 0) / 3600
                        st.metric("計測時間", f"{duration_hours:.1f} 時間")
                    
                    with col3:
                        avg_interval = stats.get("avg_interval_seconds", 0)
                        st.metric("平均間隔", f"{avg_interval:.1f} 秒")
            else:
                st.info("時間的品質メトリクスの計算に必要なデータがありません。")
        
        # 空間的品質メトリクス
        with st.expander("空間的品質メトリクス", expanded=False):
            spatial_metrics = self.metrics_calculator.get_extended_spatial_metrics()
            
            if spatial_metrics.get("has_data", False):
                # グリッド品質スコアの表示
                if "grid_quality_scores" in spatial_metrics and spatial_metrics["grid_quality_scores"]:
                    scores = spatial_metrics["grid_quality_scores"]
                    
                    # データフレーム作成
                    score_df = pd.DataFrame([
                        {
                            "latitude": grid["center"][0],
                            "longitude": grid["center"][1],
                            "quality_score": grid["quality_score"],
                            "problem_count": grid["problem_count"],
                            "total_count": grid["total_count"],
                            "text": f"品質: {grid['quality_score']:.1f}, 問題: {grid['problem_count']}/{grid['total_count']}"
                        }
                        for grid in scores
                    ])
                    
                    # マップ作成
                    fig = px.scatter_mapbox(
                        score_df,
                        lat="latitude",
                        lon="longitude",
                        color="quality_score",
                        size="total_count",
                        color_continuous_scale=["red", "orange", "yellow", "green"],
                        range_color=[0, 100],
                        zoom=10,
                        center={
                            "lat": score_df["latitude"].mean(),
                            "lon": score_df["longitude"].mean()
                        },
                        mapbox_style="open-street-map",
                        hover_data=["problem_count", "total_count"],
                        text="text",
                        title="空間的な品質スコアマップ"
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                
                # 問題タイプ別の空間分布
                if "problem_type_spatial" in spatial_metrics:
                    st.write("#### 問題タイプ別の空間分布")
                    
                    problem_types = spatial_metrics["problem_type_spatial"].keys()
                    
                    if problem_types:
                        selected_type = st.selectbox(
                            "問題タイプを選択",
                            options=list(problem_types),
                            format_func=lambda x: self.problem_type_names.get(x, x),
                            key=f"{self.key_prefix}_spatial_problem_type"
                        )
                        
                        if selected_type in spatial_metrics["problem_type_spatial"]:
                            type_data = spatial_metrics["problem_type_spatial"][selected_type]
                            
                            if "points" in type_data and type_data["points"]:
                                # ポイントのデータフレームを作成
                                points_df = pd.DataFrame(type_data["points"])
                                
                                # マップ作成
                                fig = px.scatter_mapbox(
                                    points_df,
                                    lat="latitude",
                                    lon="longitude",
                                    zoom=10,
                                    center={
                                        "lat": points_df["latitude"].mean(),
                                        "lon": points_df["longitude"].mean()
                                    },
                                    mapbox_style="open-street-map",
                                    title=f"{self.problem_type_names.get(selected_type, selected_type)}の空間分布"
                                )
                                
                                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("空間的品質メトリクスの計算に必要なデータがありません。")
    
    def _render_action_section(self):
        """
        アクションセクションをレンダリング
        """
        st.write("### 修正アクション")
        
        # 自動修正オプションの表示
        st.write("#### 自動修正オプション")
        st.write("""
        一般的な問題は自動的に修正できます。自動修正では以下の処理が行われます：
        - 重複タイムスタンプの調整
        - 欠損値の補間
        - 空間的・時間的異常の修正
        """)
        
        # 自動修正ボタン
        if st.button("自動修正を実行", key=f"{self.key_prefix}_auto_fix"):
            with st.spinner("自動修正を実行中..."):
                try:
                    # 自動修正を実行
                    fixed_container, fixes = self.validator.fix_common_issues(self.container)
                    
                    if fixed_container:
                        # 修正情報を表示
                        st.success("自動修正が完了しました。")
                        
                        # 修正内容のサマリーを表示
                        fix_data = []
                        
                        for fix in fixes:
                            fix_type = fix.get("type", "")
                            description = fix.get("description", "")
                            removed_count = fix.get("removed_count", 0)
                            
                            fix_data.append({
                                "修正タイプ": fix_type,
                                "説明": description,
                                "修正数": removed_count if removed_count > 0 else ""
                            })
                        
                        # 修正内容テーブルの表示
                        st.write("#### 修正内容")
                        st.dataframe(pd.DataFrame(fix_data), use_container_width=True)
                        
                        # 修正後のコンテナを返すコールバックを提供
                        self.container = fixed_container
                        
                        # 検証器とメトリクス計算を更新
                        self.validator.validate(self.container)
                        self.metrics_calculator = QualityMetricsCalculator(
                            self.validator.validation_results,
                            self.container.data
                        )
                        self.visualizer = ValidationVisualizer(
                            self.metrics_calculator,
                            self.container.data
                        )
                        
                        # 更新後の品質スコアを表示
                        st.write("#### 修正後の品質スコア")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            quality_gauge = self.visualizer.generate_quality_score_chart()
                            st.plotly_chart(quality_gauge, use_container_width=True)
                        
                        with col2:
                            category_chart = self.visualizer.generate_category_scores_chart()
                            st.plotly_chart(category_chart, use_container_width=True)
                except Exception as e:
                    st.error(f"自動修正中にエラーが発生しました: {str(e)}")
        
        # 問題タイプ別の修正オプション
        st.write("#### 問題タイプ別の修正")
        st.write("データクリーニングコンポーネントを使用して、より詳細な修正を行うことができます。")
        
        # 修正対象の問題タイプを選択
        fix_problem_types = {
            "missing_data": "欠損値の修正",
            "out_of_range": "範囲外の値の修正",
            "duplicates": "重複の修正",
            "spatial_anomalies": "空間的異常の修正",
            "temporal_anomalies": "時間的異常の修正"
        }
        
        # 各問題タイプの件数を表示
        categories = self.metrics_calculator.problematic_indices
        
        for problem_type, display_name in fix_problem_types.items():
            count = len(categories.get(problem_type, []))
            if count > 0:
                st.write(f"- {display_name}: {count}件")
        
        st.info("修正を実行するには、「データクリーニング」セクションを使用してください。")
    
    def _render_dashboard_controls(self):
        """
        ダッシュボードのコントロールをレンダリング
        """
        # 検証概要情報の表示
        quality_summary = self.metrics_calculator.get_quality_summary()
        quality_scores = self.metrics_calculator.quality_scores
        
        # ダッシュボードのメタデータを表示
        with st.expander("検証概要", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "品質スコア", 
                    f"{quality_scores['total']:.1f}/100",
                    delta=None
                )
            
            with col2:
                issue_counts = quality_summary["issue_counts"]
                st.metric(
                    "問題数", 
                    f"{issue_counts['problematic_records']}件",
                    f"{issue_counts['problematic_percentage']:.1f}%"
                )
            
            with col3:
                # 日時フォーマット
                timestamp = quality_summary.get("timestamp")
                if timestamp:
                    try:
                        dt = datetime.fromisoformat(timestamp)
                        formatted_time = dt.strftime("%Y-%m-%d %H:%M")
                    except:
                        formatted_time = timestamp
                else:
                    formatted_time = "N/A"
                
                st.metric("検証実行時間", formatted_time)
            
            # 追加情報
            st.write("### 検出された問題タイプ")
            
            # 問題カテゴリの件数を取得
            categories = self.metrics_calculator.problematic_indices
            category_counts = {
                "missing_data": len(categories.get("missing_data", [])),
                "out_of_range": len(categories.get("out_of_range", [])),
                "duplicates": len(categories.get("duplicates", [])),
                "spatial_anomalies": len(categories.get("spatial_anomalies", [])),
                "temporal_anomalies": len(categories.get("temporal_anomalies", [])),
            }
            
            # カラムを作成してカテゴリごとの件数を表示
            cols = st.columns(5)
            for i, (cat, name) in enumerate(self.problem_type_names.items()):
                if cat != "all" and i-1 < len(cols):
                    count = category_counts.get(cat, 0)
                    if count > 0:
                        cols[i-1].metric(name, f"{count}件")
            
            # フィルタリングについての説明
            st.info("「詳細」タブでは、問題タイプや重要度でフィルタリングして詳細を確認できます。")
    
    def _render_extended_analysis_section(self):
        """
        拡張分析セクションをレンダリング
        
        より詳細な時間的・空間的分析を提供する
        """
        st.write("### 拡張データ品質分析")
        
        # 時間的な品質分析
        st.write("#### 時間的な品質分析")
        
        # 視覚化方法の選択
        view_mode = st.radio(
            "分析タイプを選択",
            ["時間帯別品質", "問題タイプ分布", "追加分析"],
            horizontal=True,
            key=f"{self.key_prefix}_time_view_mode"
        )
        
        if view_mode == "時間帯別品質":
            # 時間帯別の品質スコアを表示
            hourly_chart = self.visualizer.generate_hourly_quality_chart()
            st.plotly_chart(hourly_chart, use_container_width=True)
            
            # 解説を追加
            st.markdown("""
            **時間帯別品質スコアについて**:
            * 緑色の時間帯はデータ品質が高い時間を示しています
            * 赤色の時間帯はデータ品質に問題がある時間を示しています
            * グラフ上にカーソルを合わせると詳細情報が表示されます
            """)
            
        elif view_mode == "問題タイプ分布":
            # 時間帯別の問題タイプ分布を表示
            tod_chart = self.visualizer.generate_time_of_day_distribution()
            st.plotly_chart(tod_chart, use_container_width=True)
            
            # 解説を追加
            st.markdown("""
            **問題タイプ分布について**:
            * 各棒グラフの色は問題タイプを示しています
            * 時間帯ごとにどの問題が多いかを確認できます
            * これにより、特定の時間帯に発生しやすい問題が分かります
            """)
            
        elif view_mode == "追加分析":
            # スピードプロファイルチャートを表示
            track_chart = self.visualizer.generate_track_quality_chart()
            st.plotly_chart(track_chart, use_container_width=True)
            
            speed_chart = self.visualizer.generate_speed_profile_chart()
            st.plotly_chart(speed_chart, use_container_width=True)
            
            # 解説を追加
            st.markdown("""
            **トラック品質分析について**:
            * 上部のゲージはトラックデータの品質評価を示しています
            * 速度と方向の一貫性も個別に評価されています
            * 下部のチャートはトラックの詳細な速度と方向変化を示しています
            * 赤色のマーカーは問題があるポイントを示しています
            """)
        
        # 空間的な品質分析
        st.write("#### 空間的な品質分析")
        
        # 視覚化方法の選択
        spatial_view_mode = st.radio(
            "分析タイプを選択",
            ["品質ヒートマップ", "品質グリッド", "問題マップ"],
            horizontal=True,
            key=f"{self.key_prefix}_spatial_view_mode"
        )
        
        if spatial_view_mode == "品質ヒートマップ":
            # 問題ヒートマップを表示
            heatmap = self.visualizer.generate_problem_heatmap()
            st.plotly_chart(heatmap, use_container_width=True)
            
            # 解説を追加
            st.markdown("""
            **品質ヒートマップについて**:
            * 色が濃い領域は問題が集中している領域を示しています
            * マップ上でズームやパンが可能です
            * カーソルを合わせると詳細情報が表示されます
            """)
            
        elif spatial_view_mode == "品質グリッド":
            # 空間的な品質グリッドを表示
            grid = self.visualizer.generate_spatial_quality_grid()
            st.plotly_chart(grid, use_container_width=True)
            
            # 解説を追加
            st.markdown("""
            **品質グリッドについて**:
            * 各点の色は品質スコアを示しています（緑=良好、赤=問題あり）
            * 点の大きさはデータポイントの数に比例しています
            * グリッド形式で空間全体の品質を評価できます
            """)
            
        elif spatial_view_mode == "問題マップ":
            # データ品質マップを表示
            quality_map = self.visualizer.generate_data_quality_map()
            st.plotly_chart(quality_map, use_container_width=True)
            
            # 解説を追加
            st.markdown("""
            **問題マップについて**:
            * 各ポイントの色は品質スコアを示しています
            * 赤色のポイントは問題がある地点を示しています
            * カーソルを合わせると詳細情報が表示されます
            """)
    
    def get_container(self) -> GPSDataContainer:
        """
        現在のデータコンテナを取得
        
        Returns
        -------
        GPSDataContainer
            現在のデータコンテナ
        """
        return self.container
