"""
ui.components.forms.data_cleaning.components.problem_detail

問題詳細表示パネルコンポーネント
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Callable
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

from sailing_data_processor.data_model.container import GPSDataContainer
from sailing_data_processor.validation.data_validator import DataValidator
from sailing_data_processor.validation.visualization import ValidationVisualizer
from sailing_data_processor.validation.quality_metrics import QualityMetricsCalculator


class ProblemDetailPanel:
    """
    問題詳細表示パネルコンポーネント
    
    選択された問題の詳細情報と視覚化を表示するコンポーネント
    """
    
    def __init__(self, key: str = "problem_detail"):
        """
        初期化
        
        Parameters
        ----------
        key : str, optional
            コンポーネントの一意のキー, by default "problem_detail"
        """
        self.key = key
    
    def render(self, 
              problem_index: int,
              container: GPSDataContainer,
              validation_results: List[Dict[str, Any]],
              problem_info: Optional[Dict[str, Any]] = None) -> None:
        """
        問題詳細パネルをレンダリング
        
        Parameters
        ----------
        problem_index : int
            問題のインデックス
        container : GPSDataContainer
            データコンテナ
        validation_results : List[Dict[str, Any]]
            検証結果のリスト
        problem_info : Optional[Dict[str, Any]], optional
            問題情報（事前に計算されている場合）, by default None
        """
        if problem_index is None or problem_index < 0 or problem_index >= len(container.data):
            st.warning("有効な問題インデックスが選択されていません。")
            return
        
        st.subheader(f"問題詳細 (レコード #{problem_index})")
        
        # データから問題のあるレコードを取得
        record_data = container.data.iloc[problem_index]
        
        # 問題情報を取得
        if problem_info is None:
            problem_info = self._find_problem_info(problem_index, validation_results)
        
        # 問題情報と記録データを表示
        col1, col2 = st.columns(2)
        
        with col1:
            self._render_problem_info(problem_info)
        
        with col2:
            self._render_record_data(record_data)
        
        # 問題タイプに応じた視覚化
        self._render_problem_visualization(problem_index, container, validation_results, problem_info)
    
    def _find_problem_info(self, problem_index: int, validation_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        問題情報を検証結果から検索
        
        Parameters
        ----------
        problem_index : int
            問題のインデックス
        validation_results : List[Dict[str, Any]]
            検証結果のリスト
            
        Returns
        -------
        Dict[str, Any]
            問題情報
        """
        problem_info = {
            "problem_types": [],
            "severity": "info",
            "descriptions": []
        }
        
        # 検証結果から問題情報を収集
        for result in validation_results:
            if not result["is_valid"]:
                details = result["details"]
                
                # 問題タイプに応じて検索
                if "out_of_range_indices" in details and problem_index in details["out_of_range_indices"]:
                    problem_info["problem_types"].append("範囲外の値")
                    problem_info["descriptions"].append(result["description"])
                    problem_info["severity"] = self._update_severity(problem_info["severity"], result["severity"])
                    problem_info["value_range_details"] = details
                
                elif "null_indices" in details:
                    for col, indices in details["null_indices"].items():
                        if problem_index in indices:
                            problem_info["problem_types"].append("欠損値")
                            problem_info["descriptions"].append(f"カラム '{col}' に欠損値があります")
                            problem_info["severity"] = self._update_severity(problem_info["severity"], result["severity"])
                            if "missing_columns" not in problem_info:
                                problem_info["missing_columns"] = []
                            problem_info["missing_columns"].append(col)
                
                elif "duplicate_indices" in details:
                    for ts, indices in details["duplicate_indices"].items():
                        if problem_index in indices:
                            problem_info["problem_types"].append("重複タイムスタンプ")
                            problem_info["descriptions"].append(f"タイムスタンプ '{ts}' が重複しています")
                            problem_info["severity"] = self._update_severity(problem_info["severity"], result["severity"])
                            problem_info["duplicate_details"] = {
                                "timestamp": ts,
                                "indices": indices
                            }
                
                elif "anomaly_indices" in details and problem_index in details["anomaly_indices"]:
                    problem_info["problem_types"].append("空間的異常")
                    problem_info["descriptions"].append("空間的な異常（異常な速度など）があります")
                    problem_info["severity"] = self._update_severity(problem_info["severity"], result["severity"])
                    
                    # 異常詳細を検索
                    for anomaly in details.get("anomaly_details", []):
                        if anomaly.get("original_index") == problem_index or anomaly.get("index") == problem_index:
                            problem_info["spatial_details"] = anomaly
                            break
                
                elif "gap_indices" in details and problem_index in details["gap_indices"]:
                    problem_info["problem_types"].append("時間的異常（ギャップ）")
                    problem_info["descriptions"].append("時間的なギャップがあります")
                    problem_info["severity"] = self._update_severity(problem_info["severity"], result["severity"])
                    
                    # ギャップ詳細を検索
                    for gap in details.get("gap_details", []):
                        if gap.get("original_index") == problem_index or gap.get("index") == problem_index:
                            problem_info["gap_details"] = gap
                            break
                
                elif "reverse_indices" in details and problem_index in details["reverse_indices"]:
                    problem_info["problem_types"].append("時間的異常（逆行）")
                    problem_info["descriptions"].append("時間的な逆行があります")
                    problem_info["severity"] = self._update_severity(problem_info["severity"], result["severity"])
                    
                    # 逆行詳細を検索
                    for reverse in details.get("reverse_details", []):
                        if reverse.get("original_index") == problem_index or reverse.get("index") == problem_index:
                            problem_info["reverse_details"] = reverse
                            break
        
        return problem_info
    
    def _update_severity(self, current_severity: str, new_severity: str) -> str:
        """
        重要度を更新（最も高いレベルを保持）
        
        Parameters
        ----------
        current_severity : str
            現在の重要度
        new_severity : str
            新しい重要度
            
        Returns
        -------
        str
            更新された重要度
        """
        severity_order = {"error": 3, "warning": 2, "info": 1}
        
        if severity_order.get(new_severity, 0) > severity_order.get(current_severity, 0):
            return new_severity
        
        return current_severity
    
    def _render_problem_info(self, problem_info: Dict[str, Any]) -> None:
        """
        問題情報を表示
        
        Parameters
        ----------
        problem_info : Dict[str, Any]
            問題情報
        """
        st.write("**問題情報**")
        
        # 問題タイプ
        if problem_info.get("problem_types"):
            problem_types_str = ", ".join(problem_info["problem_types"])
            st.markdown(f"- **問題タイプ:** {problem_types_str}")
        
        # 重要度
        severity = problem_info.get("severity", "info")
        severity_color = "#d9534f" if severity == "error" else "#f0ad4e" if severity == "warning" else "#5bc0de"
        st.markdown(f"- **重要度:** <span style='color:{severity_color};'>{severity}</span>", unsafe_allow_html=True)
        
        # 説明
        if problem_info.get("descriptions"):
            st.markdown(f"- **説明:**")
            for desc in problem_info["descriptions"]:
                st.markdown(f"  - {desc}")
        
        # 詳細情報（問題タイプに応じた追加情報）
        if "value_range_details" in problem_info:
            details = problem_info["value_range_details"]
            column = details.get("column", "")
            min_val = details.get("min_value")
            max_val = details.get("max_value")
            
            valid_range = ""
            if min_val is not None and max_val is not None:
                valid_range = f"{min_val} から {max_val}"
            elif min_val is not None:
                valid_range = f"{min_val} 以上"
            elif max_val is not None:
                valid_range = f"{max_val} 以下"
            
            if column and valid_range:
                st.markdown(f"- **有効範囲:** カラム '{column}' の値は {valid_range} である必要があります")
        
        elif "duplicate_details" in problem_info:
            details = problem_info["duplicate_details"]
            ts = details.get("timestamp", "")
            indices = details.get("indices", [])
            
            if ts and indices:
                st.markdown(f"- **重複詳細:** タイムスタンプ '{ts}' が {len(indices)} 件のレコードで重複しています")
                dup_indices_str = ", ".join([str(idx) for idx in indices[:5]])
                if len(indices) > 5:
                    dup_indices_str += f"... (他 {len(indices) - 5} 件)"
                st.markdown(f"  - **重複レコード:** {dup_indices_str}")
        
        elif "spatial_details" in problem_info:
            details = problem_info["spatial_details"]
            speed = details.get("speed_knots", 0)
            dist = details.get("distance_meters", 0)
            time_diff = details.get("time_diff_seconds", 0)
            
            st.markdown(f"- **空間的異常詳細:**")
            st.markdown(f"  - **速度:** {speed:.2f} ノット (異常検出)")
            if dist and time_diff:
                st.markdown(f"  - **移動距離:** {dist:.2f} メートル")
                st.markdown(f"  - **時間差:** {time_diff:.2f} 秒")
        
        elif "gap_details" in problem_info:
            details = problem_info["gap_details"]
            gap_seconds = details.get("gap_seconds", 0)
            prev_ts = details.get("prev_timestamp", "")
            curr_ts = details.get("curr_timestamp", "")
            
            st.markdown(f"- **時間ギャップ詳細:**")
            st.markdown(f"  - **ギャップ:** {gap_seconds:.2f} 秒")
            if prev_ts and curr_ts:
                st.markdown(f"  - **前のタイムスタンプ:** {prev_ts}")
                st.markdown(f"  - **現在のタイムスタンプ:** {curr_ts}")
        
        elif "reverse_details" in problem_info:
            details = problem_info["reverse_details"]
            diff_seconds = details.get("diff_seconds", 0)
            prev_ts = details.get("prev_timestamp", "")
            curr_ts = details.get("curr_timestamp", "")
            
            st.markdown(f"- **時間逆行詳細:**")
            st.markdown(f"  - **逆行:** {abs(diff_seconds):.2f} 秒")
            if prev_ts and curr_ts:
                st.markdown(f"  - **前のタイムスタンプ:** {prev_ts}")
                st.markdown(f"  - **現在のタイムスタンプ:** {curr_ts}")
    
    def _render_record_data(self, record_data: pd.Series) -> None:
        """
        レコードデータを表示
        
        Parameters
        ----------
        record_data : pd.Series
            レコードデータ
        """
        st.write("**レコードデータ**")
        
        # レコードデータをテーブルとして表示
        record_dict = record_data.to_dict()
        record_df = pd.DataFrame([record_dict])
        st.dataframe(record_df.T, use_container_width=True)
    
    def _render_problem_visualization(self, 
                                     problem_index: int, 
                                     container: GPSDataContainer, 
                                     validation_results: List[Dict[str, Any]],
                                     problem_info: Dict[str, Any]) -> None:
        """
        問題の視覚化を表示
        
        Parameters
        ----------
        problem_index : int
            問題のインデックス
        container : GPSDataContainer
            データコンテナ
        validation_results : List[Dict[str, Any]]
            検証結果のリスト
        problem_info : Dict[str, Any]
            問題情報
        """
        st.subheader("問題の視覚化")
        
        # 問題タイプに応じた視覚化を表示
        if "欠損値" in problem_info.get("problem_types", []):
            self._visualize_missing_values(problem_index, container, problem_info)
        
        if "範囲外の値" in problem_info.get("problem_types", []):
            self._visualize_out_of_range(problem_index, container, problem_info)
        
        if "重複タイムスタンプ" in problem_info.get("problem_types", []):
            self._visualize_duplicates(problem_index, container, problem_info)
        
        if "空間的異常" in problem_info.get("problem_types", []):
            self._visualize_spatial_anomaly(problem_index, container, problem_info)
        
        if any(pt in problem_info.get("problem_types", []) for pt in ["時間的異常（ギャップ）", "時間的異常（逆行）"]):
            self._visualize_temporal_anomaly(problem_index, container, problem_info)
    
    def _visualize_missing_values(self, problem_index: int, container: GPSDataContainer, problem_info: Dict[str, Any]) -> None:
        """
        欠損値の視覚化
        
        Parameters
        ----------
        problem_index : int
            問題のインデックス
        container : GPSDataContainer
            データコンテナ
        problem_info : Dict[str, Any]
            問題情報
        """
        missing_columns = problem_info.get("missing_columns", [])
        
        if not missing_columns:
            st.info("欠損値の詳細情報が見つかりませんでした。")
            return
        
        st.write("**欠損値の視覚化**")
        st.write(f"以下のカラムに欠損値があります: {', '.join(missing_columns)}")
        
        # 時系列コンテキストを表示
        context_size = 5
        start_idx = max(0, problem_index - context_size)
        end_idx = min(len(container.data), problem_index + context_size + 1)
        
        context_data = container.data.iloc[start_idx:end_idx].copy()
        
        # タイムスタンプでインデックス付け（可視化用）
        if "timestamp" in context_data.columns:
            context_data.set_index("timestamp", inplace=True)
        
        # 欠損値のあるカラムのみを選択
        missing_data = context_data[missing_columns]
        
        # 欠損値を視覚化
        for col in missing_columns:
            if pd.api.types.is_numeric_dtype(container.data[col]):
                # 数値データの場合はプロットで視覚化
                fig = px.line(
                    missing_data,
                    y=col,
                    title=f"カラム '{col}' の欠損値（前後の値）"
                )
                
                # 欠損値の位置にマーカーを追加
                null_mask = missing_data[col].isna()
                
                if null_mask.any():
                    # 欠損値の位置にマーカーを追加（タイムスタンプを復元）
                    fig.add_trace(go.Scatter(
                        x=null_mask.index[null_mask],
                        y=[None] * null_mask.sum(),
                        mode="markers",
                        marker=dict(
                            color="red",
                            size=10,
                            symbol="x"
                        ),
                        name="欠損値"
                    ))
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                # 非数値データの場合はテーブルで表示
                st.write(f"カラム '{col}' の欠損値と前後の値:")
                st.dataframe(missing_data[col], use_container_width=True)
    
    def _visualize_out_of_range(self, problem_index: int, container: GPSDataContainer, problem_info: Dict[str, Any]) -> None:
        """
        範囲外の値の視覚化
        
        Parameters
        ----------
        problem_index : int
            問題のインデックス
        container : GPSDataContainer
            データコンテナ
        problem_info : Dict[str, Any]
            問題情報
        """
        if "value_range_details" not in problem_info:
            st.info("範囲外の値の詳細情報が見つかりませんでした。")
            return
        
        details = problem_info["value_range_details"]
        column = details.get("column", "")
        min_val = details.get("min_value")
        max_val = details.get("max_value")
        
        if not column or column not in container.data.columns:
            st.info(f"カラム '{column}' が見つかりません。")
            return
        
        st.write(f"**カラム '{column}' の範囲外の値**")
        
        # レコードの値
        value = container.data.iloc[problem_index][column]
        st.write(f"値: {value}")
        
        valid_range = ""
        if min_val is not None and max_val is not None:
            valid_range = f"{min_val} から {max_val}"
        elif min_val is not None:
            valid_range = f"{min_val} 以上"
        elif max_val is not None:
            valid_range = f"{max_val} 以下"
        
        st.write(f"有効範囲: {valid_range}")
        
        # 分布を表示
        if pd.api.types.is_numeric_dtype(container.data[column]):
            values = container.data[column].dropna()
            
            # ヒストグラム
            fig = px.histogram(
                values,
                title=f"カラム '{column}' の値の分布"
            )
            
            # 有効範囲のラインを追加
            if min_val is not None:
                fig.add_vline(
                    x=min_val,
                    line_dash="dash",
                    line_color="green",
                    annotation_text="最小値"
                )
            
            if max_val is not None:
                fig.add_vline(
                    x=max_val,
                    line_dash="dash",
                    line_color="red",
                    annotation_text="最大値"
                )
            
            # 現在の値のラインを追加
            fig.add_vline(
                x=value,
                line_dash="solid",
                line_color="purple",
                annotation_text="現在の値"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # 箱ひげ図
            fig = px.box(
                values,
                title=f"カラム '{column}' の箱ひげ図"
            )
            
            # 現在の値のポイントを追加
            fig.add_trace(go.Scatter(
                x=["現在の値"],
                y=[value],
                mode="markers",
                marker=dict(
                    color="red",
                    size=10
                ),
                name="現在の値"
            ))
            
            st.plotly_chart(fig, use_container_width=True)
    
    def _visualize_duplicates(self, problem_index: int, container: GPSDataContainer, problem_info: Dict[str, Any]) -> None:
        """
        重複タイムスタンプの視覚化
        
        Parameters
        ----------
        problem_index : int
            問題のインデックス
        container : GPSDataContainer
            データコンテナ
        problem_info : Dict[str, Any]
            問題情報
        """
        if "duplicate_details" not in problem_info:
            st.info("重複タイムスタンプの詳細情報が見つかりませんでした。")
            return
        
        details = problem_info["duplicate_details"]
        timestamp = details.get("timestamp", "")
        indices = details.get("indices", [])
        
        if not timestamp or not indices:
            st.info("重複タイムスタンプの詳細情報が見つかりませんでした。")
            return
        
        st.write(f"**タイムスタンプ '{timestamp}' の重複**")
        
        # 重複レコードを取得
        if "timestamp" in container.data.columns:
            # 同じタイムスタンプを持つレコードを検索
            duplicate_records = container.data[container.data["timestamp"] == timestamp]
            
            if not duplicate_records.empty:
                st.write(f"同じタイムスタンプを持つレコード: {len(duplicate_records)}件")
                st.dataframe(duplicate_records, use_container_width=True)
            
            # タイムライン上での位置を示す
            self._visualize_timeline_context(problem_index, container)
        else:
            st.info("タイムスタンプカラムが見つかりません。")
    
    def _visualize_spatial_anomaly(self, problem_index: int, container: GPSDataContainer, problem_info: Dict[str, Any]) -> None:
        """
        空間的異常の視覚化
        
        Parameters
        ----------
        problem_index : int
            問題のインデックス
        container : GPSDataContainer
            データコンテナ
        problem_info : Dict[str, Any]
            問題情報
        """
        if "spatial_details" not in problem_info:
            st.info("空間的異常の詳細情報が見つかりませんでした。")
            return
        
        if "latitude" not in container.data.columns or "longitude" not in container.data.columns:
            st.info("位置情報（緯度・経度）カラムが見つかりません。")
            return
        
        st.write("**空間的異常の視覚化**")
        
        # 前後のコンテキストを含めたデータを取得
        context_size = 10
        start_idx = max(0, problem_index - context_size)
        end_idx = min(len(container.data), problem_index + context_size + 1)
        
        context_data = container.data.iloc[start_idx:end_idx].copy()
        
        # 異常ポイントをマーク
        context_data["is_anomaly"] = context_data.index == problem_index
        
        # マップを作成
        fig = px.scatter_mapbox(
            context_data,
            lat="latitude",
            lon="longitude",
            color="is_anomaly",
            color_discrete_map={True: "red", False: "blue"},
            zoom=11,
            title="位置データの異常"
        )
        
        # 軌跡を追加
        fig.add_trace(go.Scattermapbox(
            lat=context_data["latitude"],
            lon=context_data["longitude"],
            mode="lines",
            line=dict(width=2, color="gray"),
            showlegend=False
        ))
        
        fig.update_layout(mapbox_style="open-street-map")
        st.plotly_chart(fig, use_container_width=True)
        
        # 速度プロファイルを表示（タイムスタンプがある場合）
        if "timestamp" in context_data.columns and "speed" in context_data.columns:
            # 速度の時系列プロット
            fig = px.line(
                context_data,
                x="timestamp",
                y="speed",
                title="速度の時系列プロファイル"
            )
            
            # 異常ポイントをマーク
            anomaly_point = context_data[context_data["is_anomaly"]]
            if not anomaly_point.empty:
                fig.add_trace(go.Scatter(
                    x=anomaly_point["timestamp"],
                    y=anomaly_point["speed"],
                    mode="markers",
                    marker=dict(
                        color="red",
                        size=10,
                        symbol="star"
                    ),
                    name="異常ポイント"
                ))
            
            st.plotly_chart(fig, use_container_width=True)
        
        # 詳細情報を表示
        details = problem_info["spatial_details"]
        st.write("**異常詳細:**")
        
        detail_items = []
        for key, value in details.items():
            if key not in ["index", "original_index"]:
                detail_items.append({"項目": key, "値": value})
        
        if detail_items:
            st.table(pd.DataFrame(detail_items))
    
    def _visualize_temporal_anomaly(self, problem_index: int, container: GPSDataContainer, problem_info: Dict[str, Any]) -> None:
        """
        時間的異常の視覚化
        
        Parameters
        ----------
        problem_index : int
            問題のインデックス
        container : GPSDataContainer
            データコンテナ
        problem_info : Dict[str, Any]
            問題情報
        """
        if "gap_details" not in problem_info and "reverse_details" not in problem_info:
            st.info("時間的異常の詳細情報が見つかりませんでした。")
            return
        
        if "timestamp" not in container.data.columns:
            st.info("タイムスタンプカラムが見つかりません。")
            return
        
        st.write("**時間的異常の視覚化**")
        
        # 詳細情報を表示
        if "gap_details" in problem_info:
            details = problem_info["gap_details"]
            st.write("**時間ギャップの詳細:**")
            
            detail_items = []
            for key, value in details.items():
                if key not in ["index", "original_index"]:
                    detail_items.append({"項目": key, "値": value})
            
            if detail_items:
                st.table(pd.DataFrame(detail_items))
        
        if "reverse_details" in problem_info:
            details = problem_info["reverse_details"]
            st.write("**時間逆行の詳細:**")
            
            detail_items = []
            for key, value in details.items():
                if key not in ["index", "original_index"]:
                    detail_items.append({"項目": key, "値": value})
            
            if detail_items:
                st.table(pd.DataFrame(detail_items))
        
        # タイムライン上での位置を示す
        self._visualize_timeline_context(problem_index, container)
    
    def _visualize_timeline_context(self, problem_index: int, container: GPSDataContainer) -> None:
        """
        タイムライン上でのコンテキストを視覚化
        
        Parameters
        ----------
        problem_index : int
            問題のインデックス
        container : GPSDataContainer
            データコンテナ
        """
        if "timestamp" not in container.data.columns:
            return
        
        # タイムスタンプでソートされたデータを取得
        sorted_data = container.data.sort_values("timestamp").copy()
        
        # プロット用にインデックスをリセット
        plot_data = sorted_data.reset_index()
        plot_data.rename(columns={"index": "original_index"}, inplace=True)
        
        # 問題インデックスの位置を特定
        problem_positions = plot_data[plot_data["original_index"] == problem_index].index.tolist()
        
        if not problem_positions:
            return
        
        problem_pos = problem_positions[0]
        
        # 前後のコンテキストを取得
        context_size = 15
        start_pos = max(0, problem_pos - context_size)
        end_pos = min(len(plot_data), problem_pos + context_size + 1)
        
        context_data = plot_data.iloc[start_pos:end_pos].copy()
        
        # 問題ポイントをマーク
        context_data["is_problem"] = context_data["original_index"] == problem_index
        
        # タイムスタンプ間隔を計算
        context_data["time_diff"] = context_data["timestamp"].diff().dt.total_seconds()
        
        # タイムラインチャート
        st.write("**タイムライン上の位置:**")
        
        fig = px.scatter(
            context_data,
            x="timestamp",
            y=[1] * len(context_data),  # 同じ高さに表示
            color="is_problem",
            color_discrete_map={True: "red", False: "blue"},
            title="タイムスタンプのシーケンス"
        )
        
        # 線を追加
        fig.add_trace(go.Scatter(
            x=context_data["timestamp"],
            y=[1] * len(context_data),
            mode="lines",
            line=dict(width=1, color="gray"),
            showlegend=False
        ))
        
        fig.update_layout(
            yaxis_visible=False,
            yaxis_showticklabels=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # タイムスタンプ間隔のチャート
        if len(context_data) > 1:
            st.write("**タイムスタンプの間隔:**")
            
            fig = px.bar(
                context_data.iloc[1:],  # 最初の行はNaNになるので除外
                x=range(len(context_data) - 1),  # インデックス
                y="time_diff",
                color="is_problem",
                color_discrete_map={True: "red", False: "blue"},
                labels={"x": "シーケンス位置", "time_diff": "間隔（秒）"},
                title="タイムスタンプの間隔"
            )
            
            st.plotly_chart(fig, use_container_width=True)
