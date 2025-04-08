"""
ui.integrated.components.validation.interactive_correction

インタラクティブなデータ修正UIコンポーネント
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Any, Optional, Tuple, Callable

from sailing_data_processor.data_model.container import GPSDataContainer
from sailing_data_processor.validation.correction import DataCorrector

class InteractiveCorrection:
    """
    インタラクティブなデータ修正UIコンポーネント
    
    データ検証結果に基づいて問題を特定し、ユーザーがインタラクティブに修正できるUI
    """
    
    def __init__(self, container: GPSDataContainer, key_prefix: str = "interactive_correction"):
        """
        コンポーネントの初期化
        
        Parameters
        ----------
        container : GPSDataContainer
            対象のデータコンテナ
        key_prefix : str, optional
            セッション状態のキープレフィックス, by default "interactive_correction"
        """
        self.container = container
        self.key_prefix = key_prefix
        self.corrector = DataCorrector(container)
        
        # セッション状態の初期化
        if f"{self.key_prefix}_state" not in st.session_state:
            st.session_state[f"{self.key_prefix}_state"] = {
                "selected_problem": None,
                "selected_method": None,
                "correction_params": {},
                "modified_container": None,
                "modification_history": []
            }
    
    def render(self, problems: List[Dict[str, Any]]):
        """
        修正UIをレンダリング
        
        Parameters
        ----------
        problems : List[Dict[str, Any]]
            検証で検出された問題のリスト
        
        Returns
        -------
        Optional[GPSDataContainer]
            修正されたデータコンテナ（修正されていない場合はNone）
        """
        state = self._get_state()
        
        # 問題がない場合
        if not problems:
            st.success("検出された問題はありません。修正は必要ありません。")
            return None
        
        # 問題の種類をカテゴリごとに分類
        problem_categories = self._categorize_problems(problems)
        
        # 問題リストの表示
        self._render_problem_list(problem_categories)
        
        # 選択された問題の詳細表示
        selected_problem = state["selected_problem"]
        if selected_problem:
            problem = next((p for p in problems if p["rule_name"] == selected_problem), None)
            if problem:
                self._render_problem_detail(problem)
                
                # 修正方法の選択と実行
                if self._render_correction_methods(problem):
                    # 修正が実行された場合
                    return state["modified_container"]
        
        return None
    
    def _get_state(self) -> Dict[str, Any]:
        """セッション状態を取得"""
        return st.session_state[f"{self.key_prefix}_state"]
    
    def _set_state(self, state: Dict[str, Any]):
        """セッション状態を設定"""
        st.session_state[f"{self.key_prefix}_state"] = state
    
    def _update_state(self, **kwargs):
        """セッション状態を更新"""
        state = self._get_state()
        for key, value in kwargs.items():
            state[key] = value
        self._set_state(state)
    
    def _categorize_problems(self, problems: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        問題をカテゴリごとに分類
        
        Parameters
        ----------
        problems : List[Dict[str, Any]]
            問題リスト
            
        Returns
        -------
        Dict[str, List[Dict[str, Any]]]
            カテゴリごとの問題リスト
        """
        categories = {}
        
        for problem in problems:
            category = problem.get("category", "その他")
            
            if category not in categories:
                categories[category] = []
            
            categories[category].append(problem)
        
        return categories
    
    def _render_problem_list(self, problem_categories: Dict[str, List[Dict[str, Any]]]):
        """
        問題リストを表示
        
        Parameters
        ----------
        problem_categories : Dict[str, List[Dict[str, Any]]]
            カテゴリごとの問題リスト
        """
        st.markdown("### 検出された問題")
        
        # 選択中の問題
        selected_problem = self._get_state()["selected_problem"]
        
        # カテゴリごとに問題を表示
        for category, problems in problem_categories.items():
            with st.expander(f"{category} ({len(problems)}件)", expanded=True):
                for problem in problems:
                    severity = problem.get("severity", "info")
                    severity_icon = {
                        "error": "❌",
                        "warning": "⚠️",
                        "info": "ℹ️"
                    }.get(severity, "ℹ️")
                    
                    # 問題を選択するボタン
                    button_style = "primary" if selected_problem == problem["rule_name"] else "secondary"
                    
                    if st.button(
                        f"{severity_icon} {problem['rule_name']}",
                        key=f"problem_{problem['rule_name']}",
                        type=button_style
                    ):
                        self._update_state(
                            selected_problem=problem["rule_name"],
                            selected_method=None,
                            correction_params={}
                        )
                        st.rerun()
    
    def _render_problem_detail(self, problem: Dict[str, Any]):
        """
        選択された問題の詳細を表示
        
        Parameters
        ----------
        problem : Dict[str, Any]
            表示する問題
        """
        st.markdown("---")
        st.markdown(f"### 問題の詳細: {problem['rule_name']}")
        
        # 問題の基本情報
        st.markdown(f"**説明:** {problem['description']}")
        
        severity = problem.get("severity", "info")
        severity_text = {
            "error": "エラー（修正が必要）",
            "warning": "警告（確認が必要）",
            "info": "情報（参考）"
        }.get(severity, "不明")
        
        st.markdown(f"**重要度:** {severity_text}")
        
        # 影響を受けるデータポイントの情報
        if "affected_indices" in problem and problem["affected_indices"]:
            indices = problem["affected_indices"]
            st.markdown(f"**影響を受けるデータポイント:** {len(indices)}件")
            
            # 影響を受けるデータの表示
            affected_data = self.container.data.iloc[indices]
            st.dataframe(affected_data.head(10), use_container_width=True)
            
            # 影響箇所の可視化
            self._visualize_problem(problem)
    
    def _visualize_problem(self, problem: Dict[str, Any]):
        """
        問題箇所を可視化
        
        Parameters
        ----------
        problem : Dict[str, Any]
            可視化する問題
        """
        # 問題の種類に基づいて適切な可視化を選択
        problem_type = problem["rule_name"].lower()
        
        if "affected_indices" not in problem or not problem["affected_indices"]:
            return
        
        indices = problem["affected_indices"]
        
        # すべてのデータと問題箇所のデータを取得
        all_data = self.container.data
        problem_data = all_data.iloc[indices]
        
        # 時系列データの可視化
        if "timestamp" in all_data.columns:
            if any(x in problem_type for x in ["gap", "missing", "duplicate", "order"]):
                self._visualize_timestamp_problem(all_data, problem_data)
            
        # 位置データの可視化
        if "latitude" in all_data.columns and "longitude" in all_data.columns:
            if any(x in problem_type for x in ["coordinate", "gps", "position"]):
                self._visualize_coordinate_problem(all_data, problem_data)
            
        # 異常値の可視化
        if "outlier" in problem_type and "column" in problem:
            self._visualize_outlier_problem(all_data, problem_data, problem.get("column"))
    
    def _visualize_timestamp_problem(self, all_data: pd.DataFrame, problem_data: pd.DataFrame):
        """
        タイムスタンプ関連の問題を可視化
        
        Parameters
        ----------
        all_data : pd.DataFrame
            すべてのデータ
        problem_data : pd.DataFrame
            問題箇所のデータ
        """
        st.markdown("#### タイムスタンプの問題箇所")
        
        # タイムスタンプの差分を計算
        if len(all_data) > 1:
            all_data_sorted = all_data.sort_values("timestamp")
            time_diffs = all_data_sorted["timestamp"].diff().dt.total_seconds()
            
            # 時間間隔のヒストグラム
            fig = px.histogram(
                time_diffs.dropna(),
                nbins=30,
                title="タイムスタンプ間隔の分布"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # 問題箇所をハイライト表示
            fig = go.Figure()
            
            # すべてのデータポイント
            fig.add_trace(go.Scatter(
                x=all_data_sorted["timestamp"],
                y=range(len(all_data_sorted)),
                mode="markers",
                name="すべてのデータ",
                marker=dict(color="blue", size=5, opacity=0.5)
            ))
            
            # 問題箇所
            problem_data_sorted = problem_data.sort_values("timestamp")
            fig.add_trace(go.Scatter(
                x=problem_data_sorted["timestamp"],
                y=[all_data_sorted.index.get_indexer([idx])[0] if idx in all_data_sorted.index else 0 
                   for idx in problem_data_sorted.index],
                mode="markers",
                name="問題箇所",
                marker=dict(color="red", size=8)
            ))
            
            fig.update_layout(
                title="タイムスタンプの分布（問題箇所はハイライト表示）",
                xaxis_title="時間",
                yaxis_title="データポイントのインデックス",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    def _visualize_coordinate_problem(self, all_data: pd.DataFrame, problem_data: pd.DataFrame):
        """
        座標関連の問題を可視化
        
        Parameters
        ----------
        all_data : pd.DataFrame
            すべてのデータ
        problem_data : pd.DataFrame
            問題箇所のデータ
        """
        st.markdown("#### 座標データの問題箇所")
        
        # 地図上での可視化
        fig = go.Figure()
        
        # すべての軌跡
        fig.add_trace(go.Scattermapbox(
            lat=all_data["latitude"],
            lon=all_data["longitude"],
            mode="lines+markers",
            name="正常なデータ",
            marker=dict(size=5, color="blue"),
            line=dict(width=2, color="blue")
        ))
        
        # 問題箇所
        fig.add_trace(go.Scattermapbox(
            lat=problem_data["latitude"],
            lon=problem_data["longitude"],
            mode="markers",
            name="問題箇所",
            marker=dict(size=8, color="red")
        ))
        
        # 地図の中心位置
        center_lat = all_data["latitude"].mean()
        center_lon = all_data["longitude"].mean()
        
        fig.update_layout(
            mapbox=dict(
                style="open-street-map",
                center=dict(lat=center_lat, lon=center_lon),
                zoom=12
            ),
            height=500,
            margin=dict(l=0, r=0, t=30, b=0)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _visualize_outlier_problem(self, all_data: pd.DataFrame, problem_data: pd.DataFrame, column: str):
        """
        異常値の問題を可視化
        
        Parameters
        ----------
        all_data : pd.DataFrame
            すべてのデータ
        problem_data : pd.DataFrame
            問題箇所のデータ
        column : str
            異常値が検出された列
        """
        if column not in all_data.columns:
            return
        
        st.markdown(f"#### 列「{column}」の異常値")
        
        # 箱ひげ図による可視化
        fig = go.Figure()
        
        fig.add_trace(go.Box(
            y=all_data[column],
            name="すべてのデータ",
            boxpoints="outliers",
            marker=dict(color="blue"),
            line=dict(color="blue")
        ))
        
        # 問題箇所を散布図で追加
        fig.add_trace(go.Scatter(
            x=[column] * len(problem_data),
            y=problem_data[column],
            mode="markers",
            name="異常値",
            marker=dict(color="red", size=8)
        ))
        
        fig.update_layout(
            title=f"列「{column}」の値分布と異常値",
            height=400,
            yaxis_title=column
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 時系列での可視化
        if "timestamp" in all_data.columns:
            fig = go.Figure()
            
            # すべてのデータポイント
            fig.add_trace(go.Scatter(
                x=all_data["timestamp"],
                y=all_data[column],
                mode="lines+markers",
                name="すべてのデータ",
                marker=dict(color="blue", size=5, opacity=0.5)
            ))
            
            # 問題箇所
            fig.add_trace(go.Scatter(
                x=problem_data["timestamp"],
                y=problem_data[column],
                mode="markers",
                name="異常値",
                marker=dict(color="red", size=8)
            ))
            
            fig.update_layout(
                title=f"列「{column}」の時系列変化と異常値",
                xaxis_title="時間",
                yaxis_title=column,
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    def _render_correction_methods(self, problem: Dict[str, Any]) -> bool:
        """
        問題に適した修正方法を表示し、実行する
        
        Parameters
        ----------
        problem : Dict[str, Any]
            修正対象の問題
            
        Returns
        -------
        bool
            修正が実行された場合はTrue、それ以外はFalse
        """
        st.markdown("---")
        st.markdown("### 修正方法")
        
        # 問題の種類に基づいて適切な修正方法を選択
        problem_type = problem["rule_name"].lower()
        state = self._get_state()
        
        # タイムスタンプの問題
        if any(x in problem_type for x in ["timestamp", "gap", "duplicate"]):
            return self._render_timestamp_correction(problem)
            
        # 座標の問題
        elif any(x in problem_type for x in ["coordinate", "gps", "position"]):
            return self._render_coordinate_correction(problem)
            
        # 欠損値の問題
        elif any(x in problem_type for x in ["missing"]):
            return self._render_missing_value_correction(problem)
            
        # 異常値の問題
        elif any(x in problem_type for x in ["outlier"]):
            return self._render_outlier_correction(problem)
            
        # その他の問題
        else:
            st.info("この問題に対する自動修正方法は現在実装されていません。")
            return False
    
    def _render_timestamp_correction(self, problem: Dict[str, Any]) -> bool:
        """
        タイムスタンプ修正UIを表示
        
        Parameters
        ----------
        problem : Dict[str, Any]
            修正対象の問題
            
        Returns
        -------
        bool
            修正が実行された場合はTrue、それ以外はFalse
        """
        state = self._get_state()
        
        # 問題サブタイプの判定
        problem_type = problem["rule_name"].lower()
        
        # タイムスタンプの重複問題
        if "duplicate" in problem_type:
            return self._render_duplicate_timestamp_correction(problem)
            
        # タイムスタンプのギャップ問題
        elif "gap" in problem_type:
            return self._render_timestamp_gap_correction(problem)
            
        # タイムスタンプの順序問題
        elif "order" in problem_type:
            return self._render_timestamp_order_correction(problem)
            
        # その他のタイムスタンプ問題
        else:
            st.info("この問題に対する自動修正方法は現在実装されていません。")
            return False
    
    def _render_duplicate_timestamp_correction(self, problem: Dict[str, Any]) -> bool:
        """
        重複タイムスタンプ修正UIを表示
        
        Parameters
        ----------
        problem : Dict[str, Any]
            修正対象の問題
            
        Returns
        -------
        bool
            修正が実行された場合はTrue、それ以外はFalse
        """
        state = self._get_state()
        
        # 修正方法の選択
        methods = [
            "最初の行を保持",
            "最後の行を保持",
            "値を平均化",
            "タイムスタンプを微調整"
        ]
        
        selected_method = state.get("selected_method")
        method_index = methods.index(selected_method) if selected_method in methods else 0
        
        method = st.radio(
            "重複タイムスタンプの修正方法:",
            methods,
            index=method_index,
            key=f"{self.key_prefix}_duplicate_method"
        )
        
        if method != state.get("selected_method"):
            self._update_state(selected_method=method, correction_params={})
        
        # 修正実行ボタン
        if st.button("修正を実行", key=f"{self.key_prefix}_execute_duplicate", type="primary"):
            # 修正処理
            st.info("重複タイムスタンプの修正を実行中...")
            
            try:
                # 修正方法に応じた処理
                if method == "最初の行を保持":
                    modified_container = self.corrector.fix_duplicate_timestamps(
                        keep="first"
                    )
                elif method == "最後の行を保持":
                    modified_container = self.corrector.fix_duplicate_timestamps(
                        keep="last"
                    )
                elif method == "値を平均化":
                    modified_container = self.corrector.fix_duplicate_timestamps(
                        keep="mean"
                    )
                elif method == "タイムスタンプを微調整":
                    modified_container = self.corrector.fix_duplicate_timestamps(
                        keep="adjust"
                    )
                else:
                    st.error("サポートされていない修正方法です。")
                    return False
                
                if modified_container:
                    # 修正結果を保存
                    self._update_state(
                        modified_container=modified_container,
                        modification_history=state["modification_history"] + [{
                            "problem": problem["rule_name"],
                            "method": method,
                            "timestamp": datetime.now().isoformat()
                        }]
                    )
                    
                    # 修正結果の表示
                    st.success("重複タイムスタンプの修正が完了しました！")
                    
                    # 修正前後の比較
                    self._render_correction_comparison(
                        title="修正前後の比較",
                        before_df=self.container.data,
                        after_df=modified_container.data,
                        problem=problem
                    )
                    
                    return True
                else:
                    st.error("修正処理に失敗しました。")
            
            except Exception as e:
                st.error(f"修正中にエラーが発生しました: {str(e)}")
        
        return False
    
    def _render_timestamp_gap_correction(self, problem: Dict[str, Any]) -> bool:
        """
        タイムスタンプのギャップ修正UIを表示
        
        Parameters
        ----------
        problem : Dict[str, Any]
            修正対象の問題
            
        Returns
        -------
        bool
            修正が実行された場合はTrue、それ以外はFalse
        """
        state = self._get_state()
        
        # 修正方法の選択
        methods = [
            "間隔を埋める行を挿入",
            "ギャップを無視",
            "セグメントに分割"
        ]
        
        selected_method = state.get("selected_method")
        method_index = methods.index(selected_method) if selected_method in methods else 0
        
        method = st.radio(
            "ギャップの修正方法:",
            methods,
            index=method_index,
            key=f"{self.key_prefix}_gap_method"
        )
        
        if method != state.get("selected_method"):
            self._update_state(selected_method=method, correction_params={})
        
        # パラメータの設定
        params = state.get("correction_params", {})
        
        if method == "間隔を埋める行を挿入":
            # ギャップしきい値の設定
            gap_threshold = st.slider(
                "ギャップとみなす時間差 (秒):",
                10, 300, params.get("gap_threshold", 30), 5,
                key=f"{self.key_prefix}_gap_threshold"
            )
            
            # 挿入間隔の設定
            fill_interval = st.slider(
                "挿入する間隔 (秒):",
                1, 30, params.get("fill_interval", 5), 1,
                key=f"{self.key_prefix}_fill_interval"
            )
            
            params.update({
                "gap_threshold": gap_threshold,
                "fill_interval": fill_interval
            })
            
        elif method == "セグメントに分割":
            # ギャップしきい値の設定
            gap_threshold = st.slider(
                "ギャップとみなす時間差 (秒):",
                10, 300, params.get("gap_threshold", 30), 5,
                key=f"{self.key_prefix}_gap_threshold_segment"
            )
            
            params.update({
                "gap_threshold": gap_threshold
            })
        
        self._update_state(correction_params=params)
        
        # 修正実行ボタン
        if st.button("修正を実行", key=f"{self.key_prefix}_execute_gap", type="primary"):
            # 修正処理
            st.info("タイムスタンプのギャップ修正を実行中...")
            
            try:
                # 修正方法に応じた処理
                if method == "間隔を埋める行を挿入":
                    modified_container = self.corrector.fix_timestamp_gaps(
                        gap_threshold=params["gap_threshold"],
                        method="interpolate",
                        interval=params["fill_interval"]
                    )
                elif method == "ギャップを無視":
                    modified_container = self.corrector.fix_timestamp_gaps(
                        gap_threshold=0,  # しきい値なし
                        method="ignore"
                    )
                elif method == "セグメントに分割":
                    modified_container = self.corrector.fix_timestamp_gaps(
                        gap_threshold=params["gap_threshold"],
                        method="segment"
                    )
                else:
                    st.error("サポートされていない修正方法です。")
                    return False
                
                if modified_container:
                    # 修正結果を保存
                    self._update_state(
                        modified_container=modified_container,
                        modification_history=state["modification_history"] + [{
                            "problem": problem["rule_name"],
                            "method": method,
                            "params": params,
                            "timestamp": datetime.now().isoformat()
                        }]
                    )
                    
                    # 修正結果の表示
                    st.success("タイムスタンプのギャップ修正が完了しました！")
                    
                    # 修正前後の比較
                    self._render_correction_comparison(
                        title="修正前後の比較",
                        before_df=self.container.data,
                        after_df=modified_container.data,
                        problem=problem
                    )
                    
                    return True
                else:
                    st.error("修正処理に失敗しました。")
            
            except Exception as e:
                st.error(f"修正中にエラーが発生しました: {str(e)}")
        
        return False
    
    def _render_timestamp_order_correction(self, problem: Dict[str, Any]) -> bool:
        """
        タイムスタンプの順序修正UIを表示
        
        Parameters
        ----------
        problem : Dict[str, Any]
            修正対象の問題
            
        Returns
        -------
        bool
            修正が実行された場合はTrue、それ以外はFalse
        """
        state = self._get_state()
        
        st.markdown("タイムスタンプの順序を修正します。データはタイムスタンプでソートされます。")
        
        # 修正実行ボタン
        if st.button("順序を修正", key=f"{self.key_prefix}_execute_order", type="primary"):
            # 修正処理
            st.info("タイムスタンプの順序修正を実行中...")
            
            try:
                # タイムスタンプでソート
                modified_container = self.corrector.sort_by_timestamp()
                
                if modified_container:
                    # 修正結果を保存
                    self._update_state(
                        modified_container=modified_container,
                        modification_history=state["modification_history"] + [{
                            "problem": problem["rule_name"],
                            "method": "タイムスタンプでソート",
                            "timestamp": datetime.now().isoformat()
                        }]
                    )
                    
                    # 修正結果の表示
                    st.success("タイムスタンプの順序修正が完了しました！")
                    
                    # 修正前後の比較
                    self._render_correction_comparison(
                        title="修正前後の比較",
                        before_df=self.container.data,
                        after_df=modified_container.data,
                        problem=problem
                    )
                    
                    return True
                else:
                    st.error("修正処理に失敗しました。")
            
            except Exception as e:
                st.error(f"修正中にエラーが発生しました: {str(e)}")
        
        return False
    
    def _render_coordinate_correction(self, problem: Dict[str, Any]) -> bool:
        """
        座標データ修正UIを表示
        
        Parameters
        ----------
        problem : Dict[str, Any]
            修正対象の問題
            
        Returns
        -------
        bool
            修正が実行された場合はTrue、それ以外はFalse
        """
        state = self._get_state()
        
        # 修正方法の選択
        methods = [
            "異常値を線形補間",
            "移動平均フィルタ",
            "地理的に不可能な点を除外"
        ]
        
        selected_method = state.get("selected_method")
        method_index = methods.index(selected_method) if selected_method in methods else 0
        
        method = st.radio(
            "座標データの修正方法:",
            methods,
            index=method_index,
            key=f"{self.key_prefix}_coordinate_method"
        )
        
        if method != state.get("selected_method"):
            self._update_state(selected_method=method, correction_params={})
        
        # パラメータの設定
        params = state.get("correction_params", {})
        
        if method == "移動平均フィルタ":
            # ウィンドウサイズの設定
            window_size = st.slider(
                "移動平均ウィンドウサイズ:",
                3, 21, params.get("window_size", 5), 2,
                key=f"{self.key_prefix}_window_size"
            )
            
            params.update({
                "window_size": window_size
            })
            
        elif method == "地理的に不可能な点を除外":
            # 速度しきい値の設定
            speed_threshold = st.slider(
                "最大可能速度 (m/s):",
                10, 100, params.get("speed_threshold", 30), 5,
                key=f"{self.key_prefix}_speed_threshold"
            )
            
            params.update({
                "speed_threshold": speed_threshold
            })
        
        self._update_state(correction_params=params)
        
        # 修正実行ボタン
        if st.button("修正を実行", key=f"{self.key_prefix}_execute_coordinate", type="primary"):
            # 修正処理
            st.info("座標データの修正を実行中...")
            
            try:
                # 修正方法に応じた処理
                if method == "異常値を線形補間":
                    # 異常値をNaNに置き換えて線形補間
                    if "affected_indices" in problem:
                        indices = problem["affected_indices"]
                        modified_container = self.corrector.fix_coordinate_outliers(
                            outlier_indices=indices,
                            method="interpolate"
                        )
                    else:
                        st.error("異常値のインデックスが特定できません。")
                        return False
                        
                elif method == "移動平均フィルタ":
                    modified_container = self.corrector.fix_coordinates_with_moving_average(
                        window_size=params["window_size"]
                    )
                    
                elif method == "地理的に不可能な点を除外":
                    modified_container = self.corrector.fix_impossible_movements(
                        speed_threshold=params["speed_threshold"]
                    )
                else:
                    st.error("サポートされていない修正方法です。")
                    return False
                
                if modified_container:
                    # 修正結果を保存
                    self._update_state(
                        modified_container=modified_container,
                        modification_history=state["modification_history"] + [{
                            "problem": problem["rule_name"],
                            "method": method,
                            "params": params,
                            "timestamp": datetime.now().isoformat()
                        }]
                    )
                    
                    # 修正結果の表示
                    st.success("座標データの修正が完了しました！")
                    
                    # 修正前後の比較
                    self._render_correction_comparison(
                        title="修正前後の比較",
                        before_df=self.container.data,
                        after_df=modified_container.data,
                        problem=problem,
                        coordinate_visualization=True
                    )
                    
                    return True
                else:
                    st.error("修正処理に失敗しました。")
            
            except Exception as e:
                st.error(f"修正中にエラーが発生しました: {str(e)}")
        
        return False
    
    def _render_missing_value_correction(self, problem: Dict[str, Any]) -> bool:
        """
        欠損値修正UIを表示
        
        Parameters
        ----------
        problem : Dict[str, Any]
            修正対象の問題
            
        Returns
        -------
        bool
            修正が実行された場合はTrue、それ以外はFalse
        """
        state = self._get_state()
        
        # 修正方法の選択
        methods = [
            "線形補間",
            "前方向に伝播",
            "後方向に伝播",
            "固定値で埋める",
            "欠損値を含む行を削除"
        ]
        
        selected_method = state.get("selected_method")
        method_index = methods.index(selected_method) if selected_method in methods else 0
        
        method = st.radio(
            "欠損値の修正方法:",
            methods,
            index=method_index,
            key=f"{self.key_prefix}_missing_method"
        )
        
        if method != state.get("selected_method"):
            self._update_state(selected_method=method, correction_params={})
        
        # 対象列の取得
        target_column = problem.get("column")
        if not target_column:
            # 対象列が指定されていない場合、すべての列が対象
            target_column = "全ての列"
        
        st.markdown(f"**対象列:** {target_column}")
        
        # パラメータの設定
        params = state.get("correction_params", {})
        
        if method == "固定値で埋める":
            # 固定値の設定
            if target_column != "全ての列":
                # 特定列の場合
                col_type = self.container.data[target_column].dtype
                
                if pd.api.types.is_numeric_dtype(col_type):
                    fill_value = st.number_input(
                        f"{target_column}の埋め値:",
                        value=params.get("fill_value", 0.0),
                        key=f"{self.key_prefix}_fill_value"
                    )
                else:
                    fill_value = st.text_input(
                        f"{target_column}の埋め値:",
                        value=params.get("fill_value", ""),
                        key=f"{self.key_prefix}_fill_value"
                    )
                
                params.update({
                    "column": target_column,
                    "fill_value": fill_value
                })
            else:
                # すべての列の場合
                st.warning("すべての列に対して固定値を設定する場合、データタイプごとにデフォルト値が使用されます。")
                
                # 数値列には0、文字列列には空文字、タイムスタンプ列にはNaT
                params.update({
                    "column": target_column,
                    "fill_value": None  # デフォルト値を使用
                })
        else:
            params.update({
                "column": target_column
            })
        
        self._update_state(correction_params=params)
        
        # 修正実行ボタン
        if st.button("修正を実行", key=f"{self.key_prefix}_execute_missing", type="primary"):
            # 修正処理
            st.info("欠損値の修正を実行中...")
            
            try:
                # 修正方法に応じた処理
                if method == "線形補間":
                    modified_container = self.corrector.fix_missing_values(
                        column=params["column"] if params["column"] != "全ての列" else None,
                        method="interpolate"
                    )
                elif method == "前方向に伝播":
                    modified_container = self.corrector.fix_missing_values(
                        column=params["column"] if params["column"] != "全ての列" else None,
                        method="ffill"
                    )
                elif method == "後方向に伝播":
                    modified_container = self.corrector.fix_missing_values(
                        column=params["column"] if params["column"] != "全ての列" else None,
                        method="bfill"
                    )
                elif method == "固定値で埋める":
                    modified_container = self.corrector.fix_missing_values(
                        column=params["column"] if params["column"] != "全ての列" else None,
                        method="value",
                        fill_value=params.get("fill_value")
                    )
                elif method == "欠損値を含む行を削除":
                    modified_container = self.corrector.fix_missing_values(
                        column=params["column"] if params["column"] != "全ての列" else None,
                        method="drop"
                    )
                else:
                    st.error("サポートされていない修正方法です。")
                    return False
                
                if modified_container:
                    # 修正結果を保存
                    self._update_state(
                        modified_container=modified_container,
                        modification_history=state["modification_history"] + [{
                            "problem": problem["rule_name"],
                            "method": method,
                            "params": params,
                            "timestamp": datetime.now().isoformat()
                        }]
                    )
                    
                    # 修正結果の表示
                    st.success("欠損値の修正が完了しました！")
                    
                    # 修正前後の比較
                    self._render_correction_comparison(
                        title="修正前後の比較",
                        before_df=self.container.data,
                        after_df=modified_container.data,
                        problem=problem
                    )
                    
                    return True
                else:
                    st.error("修正処理に失敗しました。")
            
            except Exception as e:
                st.error(f"修正中にエラーが発生しました: {str(e)}")
        
        return False
    
    def _render_outlier_correction(self, problem: Dict[str, Any]) -> bool:
        """
        異常値修正UIを表示
        
        Parameters
        ----------
        problem : Dict[str, Any]
            修正対象の問題
            
        Returns
        -------
        bool
            修正が実行された場合はTrue、それ以外はFalse
        """
        state = self._get_state()
        
        # 修正方法の選択
        methods = [
            "平均値に置き換え",
            "中央値に置き換え",
            "上下限値でクリップ",
            "線形補間",
            "異常値を含む行を削除"
        ]
        
        selected_method = state.get("selected_method")
        method_index = methods.index(selected_method) if selected_method in methods else 0
        
        method = st.radio(
            "異常値の修正方法:",
            methods,
            index=method_index,
            key=f"{self.key_prefix}_outlier_method"
        )
        
        if method != state.get("selected_method"):
            self._update_state(selected_method=method, correction_params={})
        
        # 対象列の取得
        target_column = problem.get("column")
        if not target_column:
            # 対象列が指定されていない場合、すべての数値列が対象
            st.warning("対象列が指定されていません。すべての数値列が処理対象となります。")
            target_column = "全ての数値列"
        
        st.markdown(f"**対象列:** {target_column}")
        
        # 異常値の検出方法
        detection_methods = [
            "標準偏差ベース (μ±nσ)",
            "IQRベース (Q1-k*IQR, Q3+k*IQR)"
        ]
        
        params = state.get("correction_params", {})
        detection_method = params.get("detection_method", detection_methods[0])
        detection_index = detection_methods.index(detection_method) if detection_method in detection_methods else 0
        
        selected_detection = st.radio(
            "異常値の検出方法:",
            detection_methods,
            index=detection_index,
            key=f"{self.key_prefix}_detection_method"
        )
        
        # 検出パラメータ
        if selected_detection == "標準偏差ベース (μ±nσ)":
            n_std = st.slider(
                "標準偏差の倍数 (n):",
                1.0, 5.0, params.get("n_std", 3.0), 0.1,
                key=f"{self.key_prefix}_n_std"
            )
            
            params.update({
                "detection_method": selected_detection,
                "n_std": n_std
            })
        else:  # IQRベース
            k_iqr = st.slider(
                "IQRの倍数 (k):",
                1.0, 3.0, params.get("k_iqr", 1.5), 0.1,
                key=f"{self.key_prefix}_k_iqr"
            )
            
            params.update({
                "detection_method": selected_detection,
                "k_iqr": k_iqr
            })
        
        params.update({
            "column": target_column
        })
        
        self._update_state(correction_params=params)
        
        # 修正実行ボタン
        if st.button("修正を実行", key=f"{self.key_prefix}_execute_outlier", type="primary"):
            # 修正処理
            st.info("異常値の修正を実行中...")
            
            try:
                # 異常値の検出方法に応じたパラメータを設定
                if params["detection_method"] == "標準偏差ベース (μ±nσ)":
                    detect_params = {
                        "method": "std",
                        "n_std": params["n_std"]
                    }
                else:  # IQRベース
                    detect_params = {
                        "method": "iqr",
                        "k": params["k_iqr"]
                    }
                
                # 修正方法に応じた処理
                if method == "平均値に置き換え":
                    modified_container = self.corrector.fix_numeric_outliers(
                        column=params["column"] if params["column"] != "全ての数値列" else None,
                        detection_params=detect_params,
                        replacement="mean"
                    )
                elif method == "中央値に置き換え":
                    modified_container = self.corrector.fix_numeric_outliers(
                        column=params["column"] if params["column"] != "全ての数値列" else None,
                        detection_params=detect_params,
                        replacement="median"
                    )
                elif method == "上下限値でクリップ":
                    modified_container = self.corrector.fix_numeric_outliers(
                        column=params["column"] if params["column"] != "全ての数値列" else None,
                        detection_params=detect_params,
                        replacement="clip"
                    )
                elif method == "線形補間":
                    modified_container = self.corrector.fix_numeric_outliers(
                        column=params["column"] if params["column"] != "全ての数値列" else None,
                        detection_params=detect_params,
                        replacement="interpolate"
                    )
                elif method == "異常値を含む行を削除":
                    modified_container = self.corrector.fix_numeric_outliers(
                        column=params["column"] if params["column"] != "全ての数値列" else None,
                        detection_params=detect_params,
                        replacement="drop"
                    )
                else:
                    st.error("サポートされていない修正方法です。")
                    return False
                
                if modified_container:
                    # 修正結果を保存
                    self._update_state(
                        modified_container=modified_container,
                        modification_history=state["modification_history"] + [{
                            "problem": problem["rule_name"],
                            "method": method,
                            "params": params,
                            "timestamp": datetime.now().isoformat()
                        }]
                    )
                    
                    # 修正結果の表示
                    st.success("異常値の修正が完了しました！")
                    
                    # 修正前後の比較
                    self._render_correction_comparison(
                        title="修正前後の比較",
                        before_df=self.container.data,
                        after_df=modified_container.data,
                        problem=problem,
                        column=params["column"] if params["column"] != "全ての数値列" else None
                    )
                    
                    return True
                else:
                    st.error("修正処理に失敗しました。")
            
            except Exception as e:
                st.error(f"修正中にエラーが発生しました: {str(e)}")
        
        return False
    
    def _render_correction_comparison(
        self,
        title: str,
        before_df: pd.DataFrame,
        after_df: pd.DataFrame,
        problem: Dict[str, Any],
        column: str = None,
        coordinate_visualization: bool = False
    ):
        """
        修正前後の比較を表示
        
        Parameters
        ----------
        title : str
            比較タイトル
        before_df : pd.DataFrame
            修正前のデータフレーム
        after_df : pd.DataFrame
            修正後のデータフレーム
        problem : Dict[str, Any]
            修正対象の問題
        column : str, optional
            特定の列の場合は列名, by default None
        coordinate_visualization : bool, optional
            座標の可視化を行うかどうか, by default False
        """
        st.markdown(f"#### {title}")
        
        # 基本統計情報の比較
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**修正前**")
            st.markdown(f"- データポイント数: {len(before_df)}")
            if "timestamp" in before_df.columns:
                time_range = before_df["timestamp"].max() - before_df["timestamp"].min()
                st.markdown(f"- 時間範囲: {time_range.total_seconds() / 60:.1f}分")
            
            # 欠損値の数
            missing_count = before_df.isna().sum().sum()
            st.markdown(f"- 欠損値の数: {missing_count}")
            
            # 列別の欠損値
            if column and column in before_df.columns:
                col_missing = before_df[column].isna().sum()
                st.markdown(f"- 列「{column}」の欠損値: {col_missing}")
        
        with col2:
            st.markdown("**修正後**")
            st.markdown(f"- データポイント数: {len(after_df)}")
            if "timestamp" in after_df.columns:
                time_range = after_df["timestamp"].max() - after_df["timestamp"].min()
                st.markdown(f"- 時間範囲: {time_range.total_seconds() / 60:.1f}分")
            
            # 欠損値の数
            missing_count = after_df.isna().sum().sum()
            st.markdown(f"- 欠損値の数: {missing_count}")
            
            # 列別の欠損値
            if column and column in after_df.columns:
                col_missing = after_df[column].isna().sum()
                st.markdown(f"- 列「{column}」の欠損値: {col_missing}")
        
        # データプレビュー
        st.markdown("##### データプレビュー")
        
        tab1, tab2 = st.tabs(["修正前", "修正後"])
        
        with tab1:
            st.dataframe(before_df.head(10), use_container_width=True)
        
        with tab2:
            st.dataframe(after_df.head(10), use_container_width=True)
        
        # 問題の種類に応じた可視化
        problem_type = problem["rule_name"].lower()
        
        # 座標データの可視化
        if coordinate_visualization or any(x in problem_type for x in ["coordinate", "gps", "position"]):
            self._visualize_coordinate_comparison(before_df, after_df)
        
        # 列データの可視化
        if column and column in before_df.columns and column in after_df.columns:
            self._visualize_column_comparison(before_df, after_df, column)
        
        # タイムスタンプデータの可視化
        if any(x in problem_type for x in ["timestamp", "gap", "duplicate", "order"]):
            self._visualize_timestamp_comparison(before_df, after_df)
    
    def _visualize_coordinate_comparison(self, before_df: pd.DataFrame, after_df: pd.DataFrame):
        """
        座標データの修正前後比較を可視化
        
        Parameters
        ----------
        before_df : pd.DataFrame
            修正前のデータフレーム
        after_df : pd.DataFrame
            修正後のデータフレーム
        """
        if "latitude" not in before_df.columns or "longitude" not in before_df.columns:
            return
        
        if "latitude" not in after_df.columns or "longitude" not in after_df.columns:
            return
        
        st.markdown("##### 軌跡の比較")
        
        fig = go.Figure()
        
        # 修正前の軌跡
        fig.add_trace(go.Scattermapbox(
            lat=before_df["latitude"],
            lon=before_df["longitude"],
            mode="lines+markers",
            name="修正前",
            marker=dict(size=5, color="blue"),
            line=dict(width=2, color="blue")
        ))
        
        # 修正後の軌跡
        fig.add_trace(go.Scattermapbox(
            lat=after_df["latitude"],
            lon=after_df["longitude"],
            mode="lines+markers",
            name="修正後",
            marker=dict(size=5, color="red"),
            line=dict(width=2, color="red")
        ))
        
        # 地図の中心位置
        center_lat = before_df["latitude"].mean()
        center_lon = before_df["longitude"].mean()
        
        fig.update_layout(
            mapbox=dict(
                style="open-street-map",
                center=dict(lat=center_lat, lon=center_lon),
                zoom=12
            ),
            height=500,
            margin=dict(l=0, r=0, t=30, b=0)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _visualize_column_comparison(self, before_df: pd.DataFrame, after_df: pd.DataFrame, column: str):
        """
        列データの修正前後比較を可視化
        
        Parameters
        ----------
        before_df : pd.DataFrame
            修正前のデータフレーム
        after_df : pd.DataFrame
            修正後のデータフレーム
        column : str
            対象列
        """
        st.markdown(f"##### 列「{column}」の比較")
        
        # 数値データの場合
        if pd.api.types.is_numeric_dtype(before_df[column].dtype):
            # 箱ひげ図による比較
            fig = go.Figure()
            
            fig.add_trace(go.Box(
                y=before_df[column],
                name="修正前",
                boxpoints="outliers",
                marker=dict(color="blue"),
                line=dict(color="blue")
            ))
            
            fig.add_trace(go.Box(
                y=after_df[column],
                name="修正後",
                boxpoints="outliers",
                marker=dict(color="red"),
                line=dict(color="red")
            ))
            
            fig.update_layout(
                title=f"列「{column}」の分布比較",
                height=400,
                yaxis_title=column
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # 時系列での比較
            if "timestamp" in before_df.columns and "timestamp" in after_df.columns:
                fig = go.Figure()
                
                # 修正前
                fig.add_trace(go.Scatter(
                    x=before_df["timestamp"],
                    y=before_df[column],
                    mode="lines+markers",
                    name="修正前",
                    marker=dict(color="blue", size=5, opacity=0.5)
                ))
                
                # 修正後
                fig.add_trace(go.Scatter(
                    x=after_df["timestamp"],
                    y=after_df[column],
                    mode="lines+markers",
                    name="修正後",
                    marker=dict(color="red", size=5, opacity=0.5)
                ))
                
                fig.update_layout(
                    title=f"列「{column}」の時系列変化比較",
                    xaxis_title="時間",
                    yaxis_title=column,
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
    
    def _visualize_timestamp_comparison(self, before_df: pd.DataFrame, after_df: pd.DataFrame):
        """
        タイムスタンプデータの修正前後比較を可視化
        
        Parameters
        ----------
        before_df : pd.DataFrame
            修正前のデータフレーム
        after_df : pd.DataFrame
            修正後のデータフレーム
        """
        if "timestamp" not in before_df.columns or "timestamp" not in after_df.columns:
            return
        
        st.markdown("##### タイムスタンプの比較")
        
        # タイムスタンプの差分を計算
        before_sorted = before_df.sort_values("timestamp")
        after_sorted = after_df.sort_values("timestamp")
        
        before_diffs = before_sorted["timestamp"].diff().dt.total_seconds().dropna()
        after_diffs = after_sorted["timestamp"].diff().dt.total_seconds().dropna()
        
        # 時間間隔のヒストグラム比較
        fig = go.Figure()
        
        fig.add_trace(go.Histogram(
            x=before_diffs,
            nbinsx=30,
            name="修正前",
            opacity=0.7,
            marker_color="blue"
        ))
        
        fig.add_trace(go.Histogram(
            x=after_diffs,
            nbinsx=30,
            name="修正後",
            opacity=0.7,
            marker_color="red"
        ))
        
        fig.update_layout(
            title="タイムスタンプ間隔の分布比較",
            xaxis_title="間隔 (秒)",
            yaxis_title="頻度",
            barmode="overlay",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # データポイント分布の比較
        fig = go.Figure()
        
        # 修正前のデータポイント
        fig.add_trace(go.Scatter(
            x=before_sorted["timestamp"],
            y=range(len(before_sorted)),
            mode="markers",
            name="修正前",
            marker=dict(color="blue", size=5, opacity=0.5)
        ))
        
        # 修正後のデータポイント
        fig.add_trace(go.Scatter(
            x=after_sorted["timestamp"],
            y=range(len(after_sorted)),
            mode="markers",
            name="修正後",
            marker=dict(color="red", size=5, opacity=0.5)
        ))
        
        fig.update_layout(
            title="データポイントの時間分布比較",
            xaxis_title="時間",
            yaxis_title="データポイントのインデックス",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def get_modified_container(self) -> Optional[GPSDataContainer]:
        """
        修正後のデータコンテナを取得
        
        Returns
        -------
        Optional[GPSDataContainer]
            修正後のデータコンテナ（修正されていない場合はNone）
        """
        return self._get_state()["modified_container"]
    
    def get_modification_history(self) -> List[Dict[str, Any]]:
        """
        修正履歴を取得
        
        Returns
        -------
        List[Dict[str, Any]]
            修正履歴のリスト
        """
        return self._get_state()["modification_history"]
