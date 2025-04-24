# -*- coding: utf-8 -*-
"""
ui.components.forms.data_cleaning.components.correction_controls

データ修正コントロールのコンポーネント
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Callable, Union, Tuple
import json
from datetime import datetime, timedelta
import uuid
import matplotlib.pyplot as plt

from sailing_data_processor.data_model.container import GPSDataContainer
from sailing_data_processor.validation.data_validator import DataValidator
from sailing_data_processor.validation.correction import InteractiveCorrectionInterface


class CorrectionControls:
    """
    データ修正コントロールコンポーネント
    
    問題の修正操作を提供するUIコンポーネント
    """
    
    def __init__(self, key: str = "correction_controls"):
        """
        初期化
        
        Parameters
        ----------
        key : str, optional
            コンポーネントの一意のキー, by default "correction_controls"
        """
        self.key = key
        
        # セッション状態の初期化
        if f"{self.key}_selected_option" not in st.session_state:
            st.session_state[f"{self.key}_selected_option"] = None
        
        if f"{self.key}_custom_params" not in st.session_state:
            st.session_state[f"{self.key}_custom_params"] = {}
            
        if f"{self.key}_selected_proposal" not in st.session_state:
            st.session_state[f"{self.key}_selected_proposal"] = None
            
        if f"{self.key}_selected_method" not in st.session_state:
            st.session_state[f"{self.key}_selected_method"] = None
            
        if f"{self.key}_preview_mode" not in st.session_state:
            st.session_state[f"{self.key}_preview_mode"] = False
    
    def render(self, 
              problem_type: str,
              problem_indices: List[int],
              container: GPSDataContainer,
              correction_interface: InteractiveCorrectionInterface,
              on_correction: Optional[Callable[[GPSDataContainer], None]] = None) -> Optional[GPSDataContainer]:
        """
        修正コントロールをレンダリング
        
        Parameters
        ----------
        problem_type : str
            問題タイプ
        problem_indices : List[int]
            修正対象の問題インデックスリスト
        container : GPSDataContainer
            データコンテナ
        correction_interface : InteractiveCorrectionInterface
            修正インターフェース
        on_correction : Optional[Callable[[GPSDataContainer], None]], optional
            修正適用時のコールバック関数, by default None
            
        Returns
        -------
        Optional[GPSDataContainer]
            修正後のデータコンテナ（修正が適用された場合のみ）
        """
        if not problem_indices:
            st.warning("修正対象の問題が選択されていません。")
            return None
        
        st.subheader("修正オプション")
        
        # 問題タイプの表示
        problem_type_display = self._get_problem_type_display(problem_type)
        st.write(f"**問題タイプ:** {problem_type_display}")
        st.write(f"**選択された問題:** {len(problem_indices)}件")
        
        # 修正オプションを取得
        correction_options = correction_interface.get_correction_options(problem_type)
        
        if not correction_options:
            st.info(f"この問題タイプに対する修正オプションはありません。")
            return None
        
        # 修正オプションの選択
        selected_option_id = st.radio(
            "修正方法を選択してください:",
            options=[opt["id"] for opt in correction_options],
            format_func=lambda x: next((opt["name"] for opt in correction_options if opt["id"] == x), x),
            key=f"{self.key}_option_selector"
        )
        
        # 選択された修正オプションを保存
        st.session_state[f"{self.key}_selected_option"] = selected_option_id
        
        # 選択されたオプションの詳細を取得
        selected_option = next((opt for opt in correction_options if opt["id"] == selected_option_id), None)
        
        if selected_option:
            # オプションの説明を表示
            st.info(selected_option.get("description", ""))
            
            # 必要に応じてカスタムパラメータ入力フォームを表示
            custom_params = self._render_custom_params(problem_type, selected_option_id, container, problem_indices)
            
            # 修正適用ボタン
            if st.button("修正を適用", key=f"{self.key}_apply_btn"):
                # 修正を適用
                with st.spinner("修正を適用中..."):
                    fixed_container = correction_interface.apply_correction(
                        problem_type=problem_type,
                        option_id=selected_option_id,
                        target_indices=problem_indices,
                        custom_params=custom_params if custom_params else None
                    )
                    
                    if fixed_container:
                        st.success("修正が正常に適用されました。")
                        
                        # 修正適用コールバックを呼び出し
                        if on_correction:
                            on_correction(fixed_container)
                        
                        # 修正されたコンテナを返す
                        return fixed_container
                    else:
                        st.error("修正の適用に失敗しました。")
        
        return None
    
    def _get_problem_type_display(self, problem_type: str) -> str:
        """
        問題タイプの表示名を取得
        
        Parameters
        ----------
        problem_type : str
            問題タイプ
            
        Returns
        -------
        str
            問題タイプの表示名
        """
        problem_type_map = {
            "missing_data": "欠損値",
            "out_of_range": "範囲外の値",
            "duplicates": "重複タイムスタンプ",
            "spatial_anomalies": "空間的異常",
            "temporal_anomalies": "時間的異常"
        }
        
        return problem_type_map.get(problem_type, problem_type)
    
    def _render_custom_params(self, 
                             problem_type: str, 
                             option_id: str,
                             container: GPSDataContainer,
                             problem_indices: List[int]) -> Dict[str, Any]:
        """
        カスタムパラメータの入力フォームをレンダリング
        
        Parameters
        ----------
        problem_type : str
            問題タイプ
        option_id : str
            選択された修正オプションID
        container : GPSDataContainer
            データコンテナ
        problem_indices : List[int]
            問題インデックスリスト
            
        Returns
        -------
        Dict[str, Any]
            入力されたカスタムパラメータ
        """
        custom_params = {}
        
        # 欠損値の修正オプション
        if problem_type == "missing_data":
            if option_id in ["interpolate_linear", "interpolate_time", "fill_forward", "fill_backward"]:
                # 補間対象のカラムを特定
                missing_columns = set()
                
                for idx in problem_indices:
                    if idx < len(container.data):
                        record = container.data.iloc[idx]
                        missing_cols = record.index[record.isna()].tolist()
                        missing_columns.update(missing_cols)
                
                missing_columns = list(missing_columns)
                
                if missing_columns:
                    st.write("**補間対象のカラム選択**")
                    selected_columns = st.multiselect(
                        "処理するカラムを選択:",
                        options=missing_columns,
                        default=missing_columns,
                        key=f"{self.key}_column_selector"
                    )
                    
                    if selected_columns:
                        custom_params["columns"] = selected_columns
            
            elif option_id == "fill_value":
                # 埋める値の入力
                st.write("**欠損値の代替値入力**")
                
                # 欠損値を持つカラムを特定
                missing_columns = set()
                for idx in problem_indices:
                    if idx < len(container.data):
                        record = container.data.iloc[idx]
                        missing_cols = record.index[record.isna()].tolist()
                        missing_columns.update(missing_cols)
                
                missing_columns = list(missing_columns)
                
                if missing_columns:
                    selected_column = st.selectbox(
                        "カラムを選択:",
                        options=missing_columns,
                        key=f"{self.key}_column_for_fill"
                    )
                    
                    # カラムのデータ型に応じた入力フォーム
                    if selected_column and selected_column in container.data.columns:
                        if pd.api.types.is_numeric_dtype(container.data[selected_column]):
                            # 数値入力
                            fill_value = st.number_input(
                                "代替値:",
                                key=f"{self.key}_numeric_fill_value"
                            )
                        else:
                            # テキスト入力
                            fill_value = st.text_input(
                                "代替値:",
                                key=f"{self.key}_text_fill_value"
                            )
                        
                        custom_params["column"] = selected_column
                        custom_params["fill_value"] = fill_value
        
        # 範囲外の値の修正オプション
        elif problem_type == "out_of_range":
            if option_id == "clip_values":
                st.write("**クリッピング範囲の設定**")
                
                # 値範囲の制約を持つカラムを特定
                columns_with_constraints = []
                
                # TODO: 制約情報をDataValidatorから取得
                # ここでは簡易的な判定を行う
                for idx in problem_indices:
                    if idx < len(container.data):
                        # カラム名と範囲を直接入力
                        column = st.text_input(
                            "カラム名:",
                            key=f"{self.key}_range_column"
                        )
                        
                        if column and column in container.data.columns:
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                min_value = st.number_input(
                                    "最小値:",
                                    key=f"{self.key}_min_value"
                                )
                            
                            with col2:
                                max_value = st.number_input(
                                    "最大値:",
                                    key=f"{self.key}_max_value"
                                )
                            
                            custom_params["column"] = column
                            custom_params["min_value"] = min_value
                            custom_params["max_value"] = max_value
                        
                        # 1つだけ処理
                        break
        
        # 重複の修正オプション
        elif problem_type == "duplicates":
            if option_id == "offset_timestamps":
                st.write("**タイムスタンプのオフセット設定**")
                
                offset_ms = st.number_input(
                    "ミリ秒単位のオフセット:",
                    min_value=1,
                    value=1,
                    key=f"{self.key}_offset_ms"
                )
                
                custom_params["offset_ms"] = offset_ms
        
        # 空間的異常の修正オプション
        elif problem_type == "spatial_anomalies":
            if option_id == "spatial_interpolate":
                st.write("**位置補間の設定**")
                
                method = st.selectbox(
                    "補間方法:",
                    options=["linear", "cubic", "nearest"],
                    key=f"{self.key}_spatial_interpolation_method"
                )
                
                custom_params["method"] = method
                custom_params["columns"] = ["latitude", "longitude"]
        
        # 時間的異常の修正オプション
        elif problem_type == "temporal_anomalies":
            if option_id == "fix_timestamps":
                st.write("**時間修正の設定**")
                
                # 時間調整の方法
                adjustment_method = st.radio(
                    "調整方法:",
                    options=["increment", "absolute"],
                    format_func=lambda x: "増分調整" if x == "increment" else "絶対時刻設定",
                    key=f"{self.key}_time_adjustment_method"
                )
                
                if adjustment_method == "increment":
                    seconds_offset = st.number_input(
                        "秒単位のオフセット:",
                        value=1.0,
                        key=f"{self.key}_seconds_offset"
                    )
                    
                    custom_params["method"] = "increment"
                    custom_params["seconds_offset"] = seconds_offset
                else:
                    # 現在の時刻を取得
                    if "timestamp" in container.data.columns and problem_indices:
                        idx = problem_indices[0]
                        if idx < len(container.data):
                            current_time = container.data.iloc[idx]["timestamp"]
                            
                            # 時刻調整
                            new_time = st.text_input(
                                "新しい時刻 (YYYY-MM-DD HH:MM:SS):",
                                value=current_time.strftime("%Y-%m-%d %H:%M:%S") if hasattr(current_time, "strftime") else "",
                                key=f"{self.key}_new_timestamp"
                            )
                            
                            try:
                                parsed_time = pd.to_datetime(new_time)
                                custom_params["method"] = "absolute"
                                custom_params["new_timestamp"] = parsed_time
                            except:
                                st.error("有効な時刻形式を入力してください (YYYY-MM-DD HH:MM:SS)")
        
        # セッション状態に保存
        st.session_state[f"{self.key}_custom_params"] = custom_params
        
        return custom_params
    
    def get_selected_option(self) -> str:
        """
        選択された修正オプションIDを取得
        
        Returns
        -------
        str
            選択された修正オプションID
        """
        return st.session_state.get(f"{self.key}_selected_option")
    
    def get_custom_params(self) -> Dict[str, Any]:
        """
        入力されたカスタムパラメータを取得
        
        Returns
        -------
        Dict[str, Any]
            カスタムパラメータ
        """
        return st.session_state.get(f"{self.key}_custom_params", {})
    
    def render_proposals(self, 
                        container: GPSDataContainer,
                        correction_interface: InteractiveCorrectionInterface,
                        on_correction: Optional[Callable[[GPSDataContainer], None]] = None) -> Optional[GPSDataContainer]:
        """
        修正提案をレンダリング
        
        Parameters
        ----------
        container : GPSDataContainer
            データコンテナ
        correction_interface : InteractiveCorrectionInterface
            修正インターフェース
        on_correction : Optional[Callable[[GPSDataContainer], None]], optional
            修正適用時のコールバック関数, by default None
            
        Returns
        -------
        Optional[GPSDataContainer]
            修正後のデータコンテナ（修正が適用された場合のみ）
        """
        st.subheader("修正提案")
        
        # 修正提案を取得
        proposals = correction_interface.get_fix_proposals()
        
        if not proposals:
            st.info("修正提案はありません。")
            return None
        
        # プレビューモード
        preview_mode = st.session_state.get(f"{self.key}_preview_mode", False)
        
        # プレビューモード切り替えボタン
        if st.button("プレビューモード" if not preview_mode else "通常モードに戻る", key=f"{self.key}_toggle_preview"):
            st.session_state[f"{self.key}_preview_mode"] = not preview_mode
            st.rerun()
        
        # 選択されている提案IDとメソッド
        selected_proposal_id = st.session_state.get(f"{self.key}_selected_proposal")
        selected_method_type = st.session_state.get(f"{self.key}_selected_method")
        
        # 最初の10件のみ表示（バッチ処理は優先表示）
        display_proposals = []
        batch_proposals = [p for p in proposals if p.get("severity") == "batch"]
        individual_proposals = [p for p in proposals if p.get("severity") != "batch"]
        
        # バッチ処理提案を優先的に表示
        display_proposals.extend(batch_proposals[:3])
        
        # 残りを個別提案から追加
        remaining_slots = 7 - len(display_proposals)
        display_proposals.extend(individual_proposals[:remaining_slots])
        
        # プレビューモードの場合、選択された提案のプレビューを表示
        if preview_mode and selected_proposal_id and selected_method_type:
            # 選択された提案を取得
            selected_proposal = next((p for p in proposals if p["id"] == selected_proposal_id), None)
            
            if selected_proposal:
                # プレビューを生成
                with st.spinner("プレビューを生成中..."):
                    preview_container, meta_info = correction_interface.preview_fix_proposal(
                        selected_proposal_id, selected_method_type
                    )
                
                if preview_container:
                    # プレビュー比較表示
                    self._render_preview_comparison(container, preview_container, meta_info)
                    
                    # 修正適用ボタン
                    if st.button("この修正を適用", key=f"{self.key}_apply_preview"):
                        with st.spinner("修正を適用中..."):
                            fixed_container = correction_interface.apply_fix_proposal(
                                selected_proposal_id, selected_method_type
                            )
                            
                            if fixed_container:
                                st.success("修正が正常に適用されました。")
                                
                                # 選択をクリア
                                st.session_state[f"{self.key}_selected_proposal"] = None
                                st.session_state[f"{self.key}_selected_method"] = None
                                
                                # コールバックを呼び出し
                                if on_correction:
                                    on_correction(fixed_container)
                                
                                return fixed_container
                            else:
                                st.error("修正の適用に失敗しました。")
                
                # 戻るボタン
                if st.button("提案一覧に戻る", key=f"{self.key}_back_to_proposals"):
                    st.session_state[f"{self.key}_selected_proposal"] = None
                    st.session_state[f"{self.key}_selected_method"] = None
                    st.rerun()
            
        else:
            # 通常モード - 提案カードを表示
            st.write(f"**{len(proposals)}件の修正提案があります**")
            
            col1, col2 = st.columns(2)
            
            for i, proposal in enumerate(display_proposals):
                with col1 if i % 2 == 0 else col2:
                    # 提案カードを表示
                    self._render_proposal_card(proposal)
            
            # 提案が10件以上ある場合
            if len(proposals) > 10:
                st.info(f"他に{len(proposals) - 10}件の提案があります。問題の種類を絞り込むことで、より関連性の高い提案を表示できます。")
        
        return None
    
    def _render_proposal_card(self, proposal: Dict[str, Any]) -> None:
        """
        修正提案カードをレンダリング
        
        Parameters
        ----------
        proposal : Dict[str, Any]
            表示する修正提案
        """
        # カードのスタイル
        card_style = """
        <style>
        .proposal-card {
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 10px;
            margin-bottom: 10px;
            background-color: #f9f9f9;
        }
        .proposal-card h4 {
            margin-top: 0;
            color: #1E88E5;
        }
        .proposal-card .badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 3px;
            font-size: 12px;
            margin-right: 5px;
        }
        .proposal-card .badge-error {
            background-color: #F44336;
            color: white;
        }
        .proposal-card .badge-warning {
            background-color: #FF9800;
            color: white;
        }
        .proposal-card .badge-info {
            background-color: #2196F3;
            color: white;
        }
        .proposal-card .badge-batch {
            background-color: #673AB7;
            color: white;
        }
        .proposal-card .method-btn {
            margin-right: 5px;
            margin-bottom: 5px;
        }
        </style>
        """
        
        st.markdown(card_style, unsafe_allow_html=True)
        
        # カードの内容
        severity = proposal.get("severity", "info")
        badge_class = f"badge-{severity}" if severity != "batch" else "badge-batch"
        
        # 影響を受けるカラム
        affected_column = proposal.get("affected_column", "")
        column_display = f" ({affected_column})" if affected_column else ""
        
        # 影響を受けるインデックス
        affected_indices = proposal.get("affected_indices", [])
        indices_count = len(affected_indices)
        
        # カード内容のHTML
        card_html = f"""
        <div class="proposal-card">
            <span class="badge {badge_class}">{severity.upper() if severity != "batch" else "バッチ処理"}</span>
            <h4>{proposal.get('description', '提案')}{column_display}</h4>
            <p>影響: {indices_count}件のレコード</p>
        </div>
        """
        
        st.markdown(card_html, unsafe_allow_html=True)
        
        # 修正方法のボタン
        methods = proposal.get("methods", [])
        recommended_method = proposal.get("recommended_method")
        
        # 推奨される方法を先頭に
        if recommended_method:
            methods.sort(key=lambda x: 0 if x.get("type") == recommended_method else 1)
        
        # 修正方法ごとにボタンを表示
        for method in methods[:3]:  # 最大3つまで表示
            method_type = method.get("type", "")
            
            # 品質への影響
            quality_impact = method.get("quality_impact", {})
            change = quality_impact.get("change", 0)
            change_display = f" (+{change:.1f})" if change > 0 else f" ({change:.1f})"
            
            # 推奨マークを追加
            is_recommended = method_type == recommended_method
            recommendation_mark = "⭐ " if is_recommended else ""
            
            btn_label = f"{recommendation_mark}{method.get('description', method_type)}{change_display}"
            
            # ボタンクリック時の処理
            btn_key = f"{self.key}_method_{proposal['id']}_{method_type}"
            if st.button(btn_label, key=btn_key):
                # 選択情報を保存
                st.session_state[f"{self.key}_selected_proposal"] = proposal["id"]
                st.session_state[f"{self.key}_selected_method"] = method_type
                
                # プレビューモードでない場合は、自動的に切り替える
                if not st.session_state.get(f"{self.key}_preview_mode", False):
                    st.session_state[f"{self.key}_preview_mode"] = True
                
                st.rerun()
    
    def _render_preview_comparison(self, 
                                  original: GPSDataContainer, 
                                  preview: GPSDataContainer, 
                                  meta_info: Dict[str, Any]) -> None:
        """
        修正前後の比較表示
        
        Parameters
        ----------
        original : GPSDataContainer
            元のデータ
        preview : GPSDataContainer
            修正後のデータプレビュー
        meta_info : Dict[str, Any]
            メタ情報
        """
        st.subheader("修正プレビュー")
        
        # 変更されたカラム
        changed_columns = meta_info.get("changed_columns", [])
        if not changed_columns:
            st.info("変更はありません。")
            return
        
        # 影響を受けるインデックス
        affected_indices = meta_info.get("affected_indices", [])
        before_values = meta_info.get("before_values", {})
        after_values = meta_info.get("after_values", {})
        
        st.write(f"**影響: {len(affected_indices)}件のレコード、{len(changed_columns)}個のカラム**")
        
        # 変更内容のプレビュー表
        preview_data = []
        
        for idx in affected_indices:
            if idx in before_values and idx in after_values:
                row_before = before_values[idx]
                row_after = after_values[idx]
                
                for col in changed_columns:
                    if col in row_before and col in row_after:
                        preview_data.append({
                            "インデックス": idx,
                            "カラム": col,
                            "修正前": row_before[col],
                            "修正後": row_after[col]
                        })
        
        # プレビューテーブルを表示
        if preview_data:
            preview_df = pd.DataFrame(preview_data)
            st.dataframe(preview_df, use_container_width=True)
            
            # 変更がある場合、データの可視化
            if any(c in ["latitude", "longitude"] for c in changed_columns):
                self._render_spatial_comparison(original, preview, affected_indices)
        else:
            st.info("具体的な変更内容を表示できません。")
    
    def _render_spatial_comparison(self, original: GPSDataContainer, preview: GPSDataContainer, indices: List[int]) -> None:
        """
        空間的な変更の可視化
        
        Parameters
        ----------
        original : GPSDataContainer
            元のデータ
        preview : GPSDataContainer
            修正後のデータ
        indices : List[int]
            影響を受けるインデックス
        """
        # 位置データの変更可視化
        if "latitude" in original.data.columns and "longitude" in original.data.columns:
            st.subheader("位置データの変更")
            
            # 表示するインデックスを最大10件に制限
            display_indices = indices[:10]
            
            # プロットの作成
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # 元のデータをプロット
            for idx in display_indices:
                if idx < len(original.data) and idx < len(preview.data):
                    # 元のデータ
                    lat_orig = original.data.iloc[idx]["latitude"]
                    lon_orig = original.data.iloc[idx]["longitude"]
                    
                    # 修正後のデータ
                    lat_new = preview.data.iloc[idx]["latitude"]
                    lon_new = preview.data.iloc[idx]["longitude"]
                    
                    # データが変わった場合のみ表示
                    if (pd.isna(lat_orig) != pd.isna(lat_new) or 
                        pd.isna(lon_orig) != pd.isna(lon_new) or
                        (not pd.isna(lat_orig) and not pd.isna(lat_new) and lat_orig != lat_new) or
                        (not pd.isna(lon_orig) and not pd.isna(lon_new) and lon_orig != lon_new)):
                        
                        # 元の位置をプロット
                        if not pd.isna(lat_orig) and not pd.isna(lon_orig):
                            ax.scatter(lon_orig, lat_orig, color='red', s=50, alpha=0.7, label=f'元の位置 ({idx})')
                            
                        # 新しい位置をプロット
                        if not pd.isna(lat_new) and not pd.isna(lon_new):
                            ax.scatter(lon_new, lat_new, color='green', s=50, alpha=0.7, label=f'修正後 ({idx})')
                            
                        # 線で結ぶ
                        if (not pd.isna(lat_orig) and not pd.isna(lon_orig) and
                            not pd.isna(lat_new) and not pd.isna(lon_new)):
                            ax.plot([lon_orig, lon_new], [lat_orig, lat_new], 'k--', alpha=0.5)
            
            # 凡例の重複を避ける
            handles, labels = plt.gca().get_legend_handles_labels()
            by_label = dict(zip(labels, handles))
            plt.legend(by_label.values(), by_label.keys())
            
            # グラフの設定
            plt.title('位置データの修正前後比較')
            plt.xlabel('経度')
            plt.ylabel('緯度')
            plt.grid(True)
            
            # プロットを表示
            st.pyplot(fig)
