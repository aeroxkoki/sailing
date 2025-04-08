"""
ui.components.validation.basic_fix_options

基本的な修正オプションコンポーネント
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Callable, Tuple, Union
from datetime import datetime, timedelta

from sailing_data_processor.data_model.container import GPSDataContainer
from sailing_data_processor.validation.data_validator import DataValidator
from sailing_data_processor.validation.data_cleaner import DataCleaner


class BasicFixOptions:
    """
    データ問題に対する基本的な修正オプションを提供するコンポーネント
    
    Parameters
    ----------
    container : GPSDataContainer
        GPSデータコンテナ
    validator : DataValidator
        データ検証器
    cleaner : Optional[DataCleaner], optional
        データクリーナー, by default None
    key_prefix : str, optional
        Streamlitのキープレフィックス, by default "fix_options"
    on_fix_applied : Optional[Callable[[Dict[str, Any]], None]], optional
        修正適用時のコールバック関数, by default None
    """
    
    def __init__(self, 
                container: GPSDataContainer, 
                validator: DataValidator,
                cleaner: Optional[DataCleaner] = None,
                key_prefix: str = "fix_options",
                on_fix_applied: Optional[Callable[[Dict[str, Any]], None]] = None):
        """
        初期化
        
        Parameters
        ----------
        container : GPSDataContainer
            GPSデータコンテナ
        validator : DataValidator
            データ検証器
        cleaner : Optional[DataCleaner], optional
            データクリーナー, by default None
        key_prefix : str, optional
            Streamlitのキープレフィックス, by default "fix_options"
        on_fix_applied : Optional[Callable[[Dict[str, Any]], None]], optional
            修正適用時のコールバック関数, by default None
        """
        self.container = container
        self.validator = validator
        self.cleaner = cleaner or DataCleaner(validator, container)
        self.key_prefix = key_prefix
        self.on_fix_applied = on_fix_applied
        
        # 問題のあるレコードのインデックス
        validation_results = self.validator.validation_results
        self.problematic_indices = self._collect_problematic_indices(validation_results)
        
        # 修正タイプ別の説明
        self.fix_type_descriptions = {
            "missing_data": "欠損値は、データの完全性と信頼性に悪影響を与えます。以下の方法で修正できます。",
            "out_of_range": "範囲外の値は、分析結果を歪める可能性があります。以下の方法で修正できます。",
            "duplicates": "重複タイムスタンプは、タイムライン分析の正確性を損なう可能性があります。以下の方法で修正できます。",
            "spatial_anomalies": "空間的異常は、位置データの信頼性に影響します。以下の方法で修正できます。",
            "temporal_anomalies": "時間的異常は、時系列分析の正確性を損なう可能性があります。以下の方法で修正できます。"
        }
        
        # 修正方法のオプション
        self.fix_method_options = {
            "missing_data": [
                {"id": "interpolate", "name": "線形補間", "description": "前後のデータポイントから値を補間します。"},
                {"id": "ffill", "name": "前方向に埋める", "description": "直前の有効な値で欠損値を埋めます。"},
                {"id": "bfill", "name": "後方向に埋める", "description": "直後の有効な値で欠損値を埋めます。"},
                {"id": "drop", "name": "行を削除", "description": "欠損値を含む行を削除します。"}
            ],
            "out_of_range": [
                {"id": "clip", "name": "値をクリップ", "description": "範囲外の値を許容範囲内の最小値/最大値に調整します。"},
                {"id": "replace", "name": "平均値に置換", "description": "範囲外の値を該当カラムの平均値で置き換えます。"},
                {"id": "drop", "name": "行を削除", "description": "範囲外の値を含む行を削除します。"}
            ],
            "duplicates": [
                {"id": "offset", "name": "時間をずらす", "description": "重複するタイムスタンプを1ミリ秒ずつずらして一意にします。"},
                {"id": "drop", "name": "重複を削除", "description": "重複する2番目以降の行を削除します。"}
            ],
            "spatial_anomalies": [
                {"id": "interpolate", "name": "位置を補間", "description": "異常ポイントの位置を前後のポイントから補間します。"},
                {"id": "drop", "name": "ポイントを削除", "description": "空間的に異常なポイントを削除します。"}
            ],
            "temporal_anomalies": [
                {"id": "fix_reverse", "name": "時間逆行を修正", "description": "時間逆行を自動修正します。"},
                {"id": "drop", "name": "ポイントを削除", "description": "時間的に異常なポイントを削除します。"}
            ]
        }
        
        # 修正適用後のデータプレビュー
        self.fix_previews = {}
    
    def _collect_problematic_indices(self, validation_results: List[Dict[str, Any]]) -> Dict[str, List[int]]:
        """
        問題のあるレコードのインデックスを収集
        
        Parameters
        ----------
        validation_results : List[Dict[str, Any]]
            検証結果
            
        Returns
        -------
        Dict[str, List[int]]
            カテゴリ別の問題インデックス
        """
        indices = {
            "missing_data": [],
            "out_of_range": [],
            "duplicates": [],
            "spatial_anomalies": [],
            "temporal_anomalies": [],
            "all": set()  # 全ての問題インデックス（重複なし）
        }
        
        for result in validation_results:
            if not result["is_valid"]:
                details = result["details"]
                
                # 欠損値の問題
                if "null_indices" in details:
                    for col, col_indices in details["null_indices"].items():
                        indices["missing_data"].extend(col_indices)
                        indices["all"].update(col_indices)
                
                # 範囲外の値
                if "out_of_range_indices" in details:
                    indices["out_of_range"].extend(details["out_of_range_indices"])
                    indices["all"].update(details["out_of_range_indices"])
                
                # 重複タイムスタンプ
                if "duplicate_indices" in details:
                    for ts, dup_indices in details["duplicate_indices"].items():
                        indices["duplicates"].extend(dup_indices)
                        indices["all"].update(dup_indices)
                
                # 空間的異常
                if "anomaly_indices" in details and "Spatial" in result["rule_name"]:
                    indices["spatial_anomalies"].extend(details["anomaly_indices"])
                    indices["all"].update(details["anomaly_indices"])
                
                # 時間的異常（ギャップや逆行）
                if (((("gap_indices" in details) or ("reverse_indices" in details)) 
                        and "Temporal" in result["rule_name"])):
                    if "gap_indices" in details:
                        indices["temporal_anomalies"].extend(details["gap_indices"])
                        indices["all"].update(details["gap_indices"])
                    if "reverse_indices" in details:
                        indices["temporal_anomalies"].extend(details["reverse_indices"])
                        indices["all"].update(details["reverse_indices"])
        
        # setからリストに変換
        indices["all"] = list(indices["all"])
        
        return indices
    
    def render(self, problem_type: Optional[str] = None, selected_indices: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        修正オプションをレンダリング
        
        Parameters
        ----------
        problem_type : Optional[str], optional
            表示する問題タイプ, by default None
            指定しない場合はすべての問題タイプを表示
        selected_indices : Optional[List[int]], optional
            選択されたレコードのインデックス, by default None
            
        Returns
        -------
        Dict[str, Any]
            修正適用の結果
        """
        result = {"status": "no_action", "applied_fix": None}
        
        if problem_type is not None and problem_type in self.problematic_indices:
            # 特定の問題タイプのみ表示
            self._render_fix_options_for_type(problem_type, selected_indices)
        else:
            # すべての問題タイプを表示
            for p_type, indices in self.problematic_indices.items():
                if p_type != "all" and indices:
                    with st.expander(f"{self._get_problem_type_name(p_type)} ({len(indices)}件)"):
                        self._render_fix_options_for_type(p_type, selected_indices)
        
        # 修正適用の確認と結果（全問題対象）
        if st.session_state.get(f"{self.key_prefix}_apply_fix", False):
            # フラグをリセット
            st.session_state[f"{self.key_prefix}_apply_fix"] = False
            
            # 修正対象と方法
            target_type = st.session_state.get(f"{self.key_prefix}_target_type")
            fix_method = st.session_state.get(f"{self.key_prefix}_fix_method")
            
            if target_type and fix_method:
                # 修正を適用
                with st.spinner("修正を適用中..."):
                    try:
                        # 修正の適用
                        fixed_result = self._apply_fix(target_type, fix_method, selected_indices)
                        
                        if fixed_result["status"] == "success":
                            # 成功メッセージ
                            st.success(f"修正が正常に適用されました。影響を受けたレコード: {fixed_result['affected_count']}件")
                            
                            # 結果を格納
                            result = fixed_result
                            
                            # コールバック関数を呼び出し
                            if self.on_fix_applied:
                                self.on_fix_applied(fixed_result)
                        else:
                            st.error(f"修正の適用に失敗しました: {fixed_result['message']}")
                    except Exception as e:
                        st.error(f"修正の適用中にエラーが発生しました: {e}")
        
        return result
    
    def _render_fix_options_for_type(self, problem_type: str, selected_indices: Optional[List[int]] = None) -> None:
        """
        特定の問題タイプの修正オプションをレンダリング
        
        Parameters
        ----------
        problem_type : str
            問題タイプ
        selected_indices : Optional[List[int]], optional
            選択されたレコードのインデックス, by default None
        """
        # 問題説明
        st.markdown(self.fix_type_descriptions.get(problem_type, "この問題タイプに対する修正オプションがあります。"))
        
        # 対象レコードの確認
        target_indices = selected_indices or self.problematic_indices[problem_type]
        
        if not target_indices:
            st.info("修正対象のレコードがありません。")
            return
        
        st.write(f"**対象レコード数:** {len(target_indices)}件")
        
        # 修正方法の選択
        fix_options = self.fix_method_options.get(problem_type, [])
        
        if fix_options:
            # 修正方法の選択ラジオボタン
            selected_method = st.radio(
                "修正方法を選択",
                options=[opt["name"] for opt in fix_options],
                key=f"{self.key_prefix}_{problem_type}_method"
            )
            
            # 選択された方法の説明を表示
            for opt in fix_options:
                if opt["name"] == selected_method:
                    st.info(opt["description"])
                    selected_method_id = opt["id"]
                    break
            
            # 修正プレビューの表示
            st.subheader("修正プレビュー")
            
            # プレビューの計算と表示（必要に応じて）
            preview_key = f"{problem_type}_{selected_method_id}"
            
            if preview_key not in self.fix_previews:
                # プレビューを計算
                preview_result = self._calculate_fix_preview(problem_type, selected_method_id, target_indices)
                self.fix_previews[preview_key] = preview_result
            else:
                preview_result = self.fix_previews[preview_key]
            
            # プレビューの表示
            if preview_result:
                if "preview_df" in preview_result:
                    # データフレームの表示
                    if not preview_result["preview_df"].empty:
                        st.dataframe(preview_result["preview_df"], use_container_width=True)
                    else:
                        st.info("プレビューデータがありません。")
                
                if "message" in preview_result:
                    st.info(preview_result["message"])
            else:
                st.info("プレビューを生成できませんでした。")
            
            # 修正適用ボタン
            if st.button(f"この修正を適用", key=f"{self.key_prefix}_{problem_type}_apply"):
                # 次のレンダリングで修正を適用するためにフラグを設定
                st.session_state[f"{self.key_prefix}_apply_fix"] = True
                st.session_state[f"{self.key_prefix}_target_type"] = problem_type
                st.session_state[f"{self.key_prefix}_fix_method"] = selected_method_id
                
                # 再レンダリングを強制
                st.experimental_rerun()
        else:
            st.info("この問題タイプに対する修正オプションはありません。")
    
    def _calculate_fix_preview(self, problem_type: str, fix_method: str, target_indices: List[int]) -> Dict[str, Any]:
        """
        修正適用のプレビューを計算
        
        Parameters
        ----------
        problem_type : str
            問題タイプ
        fix_method : str
            修正方法ID
        target_indices : List[int]
            対象レコードのインデックス
            
        Returns
        -------
        Dict[str, Any]
            プレビュー情報
        """
        try:
            # 元のデータのコピー
            original_data = self.container.data.copy()
            
            # 修正対象のレコードを抽出
            target_rows = original_data.loc[target_indices].copy()
            
            # 問題タイプと修正方法に基づいてプレビューを生成
            if problem_type == "missing_data":
                # 欠損値の修正プレビュー
                return self._preview_missing_data_fix(target_rows, fix_method)
            
            elif problem_type == "out_of_range":
                # 範囲外の値の修正プレビュー
                return self._preview_out_of_range_fix(target_rows, fix_method)
            
            elif problem_type == "duplicates":
                # 重複タイムスタンプの修正プレビュー
                return self._preview_duplicates_fix(target_rows, fix_method)
            
            elif problem_type == "spatial_anomalies":
                # 空間的異常の修正プレビュー
                return self._preview_spatial_anomalies_fix(target_rows, fix_method)
            
            elif problem_type == "temporal_anomalies":
                # 時間的異常の修正プレビュー
                return self._preview_temporal_anomalies_fix(target_rows, fix_method)
            
            return {"message": "このタイプのプレビューはサポートされていません。", "preview_df": pd.DataFrame()}
            
        except Exception as e:
            return {"message": f"プレビューの生成中にエラーが発生しました: {e}", "preview_df": pd.DataFrame()}
    
    def _preview_missing_data_fix(self, target_rows: pd.DataFrame, fix_method: str) -> Dict[str, Any]:
        """
        欠損値修正のプレビューを生成
        
        Parameters
        ----------
        target_rows : pd.DataFrame
            対象レコード
        fix_method : str
            修正方法ID
            
        Returns
        -------
        Dict[str, Any]
            プレビュー情報
        """
        # 欠損値を含むカラムを特定
        null_columns = []
        for col in target_rows.columns:
            if target_rows[col].isna().any():
                null_columns.append(col)
        
        if not null_columns:
            return {"message": "欠損値を含むカラムが見つかりませんでした。", "preview_df": pd.DataFrame()}
        
        # プレビュー生成用の一部のレコードを抽出
        original = target_rows.copy()
        modified = target_rows.copy()
        
        # 修正方法に基づいてプレビューを生成
        if fix_method == "interpolate":
            # 線形補間
            for col in null_columns:
                if pd.api.types.is_numeric_dtype(modified[col]):
                    modified[col] = modified[col].interpolate(method="linear")
        
        elif fix_method == "ffill":
            # 前方向に埋める
            for col in null_columns:
                modified[col] = modified[col].ffill()
        
        elif fix_method == "bfill":
            # 後方向に埋める
            for col in null_columns:
                modified[col] = modified[col].bfill()
        
        elif fix_method == "drop":
            # 欠損値を含む行を削除
            modified = modified.dropna(subset=null_columns)
            # メッセージを追加
            return {
                "message": f"この修正により {original.shape[0] - modified.shape[0]} 行が削除されます。",
                "preview_df": original.head(10)  # 削除前のデータを表示
            }
        
        # 変更前と変更後の表示用データフレームを作成
        preview_df = self._create_comparison_dataframe(original, modified, null_columns, max_rows=10)
        
        return {
            "message": f"{len(null_columns)}個のカラムに欠損値が見つかりました。修正方法: {fix_method}",
            "preview_df": preview_df
        }
    
    def _preview_out_of_range_fix(self, target_rows: pd.DataFrame, fix_method: str) -> Dict[str, Any]:
        """
        範囲外の値の修正プレビューを生成
        
        Parameters
        ----------
        target_rows : pd.DataFrame
            対象レコード
        fix_method : str
            修正方法ID
            
        Returns
        -------
        Dict[str, Any]
            プレビュー情報
        """
        # 範囲外の値を持つカラムと許容範囲を特定
        range_info = {}
        
        for result in self.validator.validation_results:
            if not result["is_valid"] and "Value Range Check" in result["rule_name"]:
                details = result["details"]
                column = details.get("column", "")
                min_value = details.get("min_value")
                max_value = details.get("max_value")
                
                if column and column in target_rows.columns:
                    range_info[column] = {"min": min_value, "max": max_value}
        
        if not range_info:
            return {"message": "範囲外の値を含むカラムが見つかりませんでした。", "preview_df": pd.DataFrame()}
        
        # プレビュー生成用の一部のレコードを抽出
        original = target_rows.copy()
        modified = target_rows.copy()
        
        # 修正方法に基づいてプレビューを生成
        if fix_method == "clip":
            # 値をクリップ
            for col, range_val in range_info.items():
                if pd.api.types.is_numeric_dtype(modified[col]):
                    modified[col] = modified[col].clip(lower=range_val["min"], upper=range_val["max"])
        
        elif fix_method == "replace":
            # 平均値に置換
            for col in range_info.keys():
                if pd.api.types.is_numeric_dtype(modified[col]):
                    # 範囲内の値から平均を計算
                    col_info = range_info[col]
                    valid_values = original[col]
                    
                    if col_info["min"] is not None:
                        valid_values = valid_values[valid_values >= col_info["min"]]
                    
                    if col_info["max"] is not None:
                        valid_values = valid_values[valid_values <= col_info["max"]]
                    
                    if not valid_values.empty:
                        mean_value = valid_values.mean()
                        
                        # 範囲外の値を平均値に置換
                        if col_info["min"] is not None:
                            modified.loc[modified[col] < col_info["min"], col] = mean_value
                        
                        if col_info["max"] is not None:
                            modified.loc[modified[col] > col_info["max"], col] = mean_value
        
        elif fix_method == "drop":
            # 範囲外の値を含む行を削除
            drop_mask = pd.Series(False, index=modified.index)
            
            for col, range_val in range_info.items():
                if pd.api.types.is_numeric_dtype(modified[col]):
                    col_mask = pd.Series(False, index=modified.index)
                    
                    if range_val["min"] is not None:
                        col_mask = col_mask | (modified[col] < range_val["min"])
                    
                    if range_val["max"] is not None:
                        col_mask = col_mask | (modified[col] > range_val["max"])
                    
                    drop_mask = drop_mask | col_mask
            
            modified = modified[~drop_mask]
            
            # メッセージを追加
            return {
                "message": f"この修正により {original.shape[0] - modified.shape[0]} 行が削除されます。",
                "preview_df": original.head(10)  # 削除前のデータを表示
            }
        
        # 変更前と変更後の表示用データフレームを作成
        affected_columns = list(range_info.keys())
        preview_df = self._create_comparison_dataframe(original, modified, affected_columns, max_rows=10)
        
        return {
            "message": f"{len(range_info)}個のカラムに範囲外の値が見つかりました。修正方法: {fix_method}",
            "preview_df": preview_df
        }
    
    def _preview_duplicates_fix(self, target_rows: pd.DataFrame, fix_method: str) -> Dict[str, Any]:
        """
        重複タイムスタンプの修正プレビューを生成
        
        Parameters
        ----------
        target_rows : pd.DataFrame
            対象レコード
        fix_method : str
            修正方法ID
            
        Returns
        -------
        Dict[str, Any]
            プレビュー情報
        """
        if "timestamp" not in target_rows.columns:
            return {"message": "タイムスタンプカラムが見つかりませんでした。", "preview_df": pd.DataFrame()}
        
        # 重複タイムスタンプを含む行を特定
        original = target_rows.copy()
        modified = target_rows.copy()
        
        # 重複タイムスタンプをグループ化
        duplicates = original[original.duplicated(subset=["timestamp"], keep=False)]
        duplicate_groups = duplicates.groupby("timestamp")
        
        if duplicate_groups.ngroups == 0:
            return {"message": "重複タイムスタンプがデータに見つかりませんでした。", "preview_df": pd.DataFrame()}
        
        # 修正方法に基づいてプレビューを生成
        if fix_method == "offset":
            # タイムスタンプをずらす - プレビュー表示用に一部だけ処理
            sample_ts = list(duplicate_groups.groups.keys())[:3]  # 最初の3つのタイムスタンプのみ
            
            for ts in sample_ts:
                group_indices = duplicate_groups.get_group(ts).index
                
                # 最初の行はそのまま、2番目以降は1ミリ秒ずつずらす
                for i, idx in enumerate(group_indices[1:], 1):
                    modified.loc[idx, "timestamp"] = ts + pd.Timedelta(milliseconds=i)
        
        elif fix_method == "drop":
            # 重複を削除 - 2番目以降を削除
            modified = modified.drop_duplicates(subset=["timestamp"], keep="first")
            
            # メッセージを追加
            return {
                "message": f"この修正により {original.shape[0] - modified.shape[0]} 行が削除されます。",
                "preview_df": duplicates.head(10)  # 重複行を表示
            }
        
        # 変更前と変更後の表示用データフレームを作成
        preview_df = self._create_timestamp_comparison_dataframe(original, modified, max_rows=10)
        
        return {
            "message": f"{duplicate_groups.ngroups}個の重複タイムスタンプが見つかりました。修正方法: {fix_method}",
            "preview_df": preview_df
        }
    
    def _preview_spatial_anomalies_fix(self, target_rows: pd.DataFrame, fix_method: str) -> Dict[str, Any]:
        """
        空間的異常の修正プレビューを生成
        
        Parameters
        ----------
        target_rows : pd.DataFrame
            対象レコード
        fix_method : str
            修正方法ID
            
        Returns
        -------
        Dict[str, Any]
            プレビュー情報
        """
        if "latitude" not in target_rows.columns or "longitude" not in target_rows.columns:
            return {"message": "位置情報カラム（latitude, longitude）が見つかりませんでした。", "preview_df": pd.DataFrame()}
        
        # プレビュー生成用の一部のレコードを抽出
        original = target_rows.copy()
        modified = target_rows.copy()
        
        # 空間的異常の詳細を取得
        anomaly_details = []
        
        for result in self.validator.validation_results:
            if not result["is_valid"] and "Spatial Consistency Check" in result["rule_name"]:
                if "anomaly_details" in result["details"]:
                    anomaly_details = result["details"]["anomaly_details"]
                    break
        
        if not anomaly_details:
            return {"message": "空間的異常の詳細が見つかりませんでした。", "preview_df": pd.DataFrame()}
        
        # 修正方法に基づいてプレビューを生成
        if fix_method == "interpolate":
            # 位置を補間 - プレビュー用に一部処理
            for anomaly in anomaly_details[:5]:  # 最初の5件のみ
                idx = anomaly.get("original_index")
                if idx in modified.index:
                    # 欠損値に置き換え（実際の補間は適用時に行う）
                    modified.loc[idx, "latitude"] = np.nan
                    modified.loc[idx, "longitude"] = np.nan
            
            # ダミーデータで補間を表示
            modified["latitude"] = modified["latitude"].interpolate(method="linear")
            modified["longitude"] = modified["longitude"].interpolate(method="linear")
        
        elif fix_method == "drop":
            # 異常ポイントを削除
            anomaly_indices = [anomaly.get("original_index") for anomaly in anomaly_details]
            anomaly_indices = [idx for idx in anomaly_indices if idx in modified.index]
            
            modified = modified.drop(anomaly_indices)
            
            # メッセージを追加
            return {
                "message": f"この修正により {len(anomaly_indices)} 行が削除されます。",
                "preview_df": original.head(10)  # 削除前のデータを表示
            }
        
        # 変更前と変更後の表示用データフレームを作成
        preview_df = self._create_comparison_dataframe(original, modified, ["latitude", "longitude"], max_rows=10)
        
        return {
            "message": f"{len(anomaly_details)}個の空間的異常が見つかりました。修正方法: {fix_method}",
            "preview_df": preview_df
        }
    
    def _preview_temporal_anomalies_fix(self, target_rows: pd.DataFrame, fix_method: str) -> Dict[str, Any]:
        """
        時間的異常の修正プレビューを生成
        
        Parameters
        ----------
        target_rows : pd.DataFrame
            対象レコード
        fix_method : str
            修正方法ID
            
        Returns
        -------
        Dict[str, Any]
            プレビュー情報
        """
        if "timestamp" not in target_rows.columns:
            return {"message": "タイムスタンプカラムが見つかりませんでした。", "preview_df": pd.DataFrame()}
        
        # プレビュー生成用の一部のレコードを抽出
        original = target_rows.copy()
        modified = target_rows.copy()
        
        # 時間的異常の詳細を取得
        reverse_indices = []
        gap_indices = []
        
        for result in self.validator.validation_results:
            if not result["is_valid"] and "Temporal Consistency Check" in result["rule_name"]:
                details = result["details"]
                if "reverse_indices" in details:
                    reverse_indices = details["reverse_indices"]
                if "gap_indices" in details:
                    gap_indices = details["gap_indices"]
                break
        
        if not reverse_indices and not gap_indices:
            return {"message": "時間的異常が見つかりませんでした。", "preview_df": pd.DataFrame()}
        
        # 修正方法に基づいてプレビューを生成
        if fix_method == "fix_reverse":
            # 時間逆行を修正 - プレビュー用に一部処理
            sample_indices = reverse_indices[:5]  # 最初の5件のみ
            
            # 全データの取得
            all_data = self.container.data.copy()
            
            for idx in sample_indices:
                if idx in modified.index and idx > 0:
                    # 前のタイムスタンプ + 1秒に設定
                    prev_ts = all_data.iloc[idx-1]["timestamp"]
                    modified.loc[idx, "timestamp"] = prev_ts + pd.Timedelta(seconds=1)
        
        elif fix_method == "drop":
            # 時間的異常ポイントを削除
            anomaly_indices = reverse_indices + gap_indices
            anomaly_indices = [idx for idx in anomaly_indices if idx in modified.index]
            
            modified = modified.drop(anomaly_indices)
            
            # メッセージを追加
            return {
                "message": f"この修正により {len(anomaly_indices)} 行が削除されます。",
                "preview_df": original.head(10)  # 削除前のデータを表示
            }
        
        # 変更前と変更後の表示用データフレームを作成
        preview_df = self._create_timestamp_comparison_dataframe(original, modified, max_rows=10)
        
        return {
            "message": f"{len(reverse_indices)}個の時間逆行と{len(gap_indices)}個の時間ギャップが見つかりました。修正方法: {fix_method}",
            "preview_df": preview_df
        }
    
    def _create_comparison_dataframe(self, original: pd.DataFrame, modified: pd.DataFrame, 
                                  focus_columns: List[str], max_rows: int = 10) -> pd.DataFrame:
        """
        変更前と変更後を表示するデータフレームを作成
        
        Parameters
        ----------
        original : pd.DataFrame
            元のデータ
        modified : pd.DataFrame
            修正後のデータ
        focus_columns : List[str]
            フォーカスするカラム
        max_rows : int, optional
            最大行数, by default 10
            
        Returns
        -------
        pd.DataFrame
            比較用データフレーム
        """
        # 最初の数行のみ抽出
        orig_sample = original.head(max_rows)
        mod_sample = modified.head(max_rows)
        
        # 比較用のデータフレームを作成
        comparison_rows = []
        
        for idx in orig_sample.index:
            if idx in mod_sample.index:
                orig_row = orig_sample.loc[idx]
                mod_row = mod_sample.loc[idx]
                
                row_data = {"インデックス": idx}
                
                # 影響を受けたカラムのみ表示
                for col in focus_columns:
                    if col in orig_row and col in mod_row:
                        # 特定のデータ型に対する表示の調整
                        orig_val = orig_row[col]
                        mod_val = mod_row[col]
                        
                        if isinstance(orig_val, pd.Timestamp) or isinstance(orig_val, datetime):
                            orig_val = orig_val.strftime("%Y-%m-%d %H:%M:%S")
                        
                        if isinstance(mod_val, pd.Timestamp) or isinstance(mod_val, datetime):
                            mod_val = mod_val.strftime("%Y-%m-%d %H:%M:%S")
                        
                        row_data[f"{col} (元)"] = orig_val
                        row_data[f"{col} (修正後)"] = mod_val
                
                comparison_rows.append(row_data)
        
        # データフレームに変換
        comparison_df = pd.DataFrame(comparison_rows)
        
        return comparison_df
    
    def _create_timestamp_comparison_dataframe(self, original: pd.DataFrame, modified: pd.DataFrame, 
                                            max_rows: int = 10) -> pd.DataFrame:
        """
        タイムスタンプの変更前と変更後を表示するデータフレームを作成
        
        Parameters
        ----------
        original : pd.DataFrame
            元のデータ
        modified : pd.DataFrame
            修正後のデータ
        max_rows : int, optional
            最大行数, by default 10
            
        Returns
        -------
        pd.DataFrame
            比較用データフレーム
        """
        # タイムスタンプだけに特化した比較
        return self._create_comparison_dataframe(original, modified, ["timestamp"], max_rows)
    
    def _apply_fix(self, problem_type: str, fix_method: str, selected_indices: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        修正を適用
        
        Parameters
        ----------
        problem_type : str
            問題タイプ
        fix_method : str
            修正方法ID
        selected_indices : Optional[List[int]], optional
            選択されたレコードのインデックス, by default None
            
        Returns
        -------
        Dict[str, Any]
            修正適用の結果
        """
        try:
            # 修正対象のインデックス
            target_indices = selected_indices or self.problematic_indices[problem_type]
            
            if not target_indices:
                return {"status": "error", "message": "修正対象のレコードがありません。"}
            
            # 元のデータのコピー
            data = self.container.data.copy()
            
            # 修正情報
            fix_info = {
                "type": problem_type,
                "method": fix_method,
                "target_indices": target_indices,
                "timestamp": datetime.now().isoformat()
            }
            
            # 問題タイプと修正方法に基づいてデータを修正
            if problem_type == "missing_data":
                # 欠損値の修正
                fixed_data = self._fix_missing_data(data, fix_method, target_indices)
            
            elif problem_type == "out_of_range":
                # 範囲外の値の修正
                fixed_data = self._fix_out_of_range(data, fix_method, target_indices)
            
            elif problem_type == "duplicates":
                # 重複タイムスタンプの修正
                fixed_data = self._fix_duplicates(data, fix_method, target_indices)
            
            elif problem_type == "spatial_anomalies":
                # 空間的異常の修正
                fixed_data = self._fix_spatial_anomalies(data, fix_method, target_indices)
            
            elif problem_type == "temporal_anomalies":
                # 時間的異常の修正
                fixed_data = self._fix_temporal_anomalies(data, fix_method, target_indices)
            
            else:
                return {"status": "error", "message": f"不明な問題タイプ: {problem_type}"}
            
            # 修正後のデータが空でないことを確認
            if fixed_data.empty and not data.empty:
                return {"status": "error", "message": "修正によりすべてのデータが削除されました。"}
            
            # 修正されたデータでコンテナを更新
            fixed_container = GPSDataContainer(fixed_data, self.container.metadata.copy())
            
            # 修正情報をメタデータに追加
            if "fix_history" not in fixed_container.metadata:
                fixed_container.metadata["fix_history"] = []
            
            fixed_container.metadata["fix_history"].append(fix_info)
            
            # コンテナを更新
            self.container = fixed_container
            
            # 検証とキャッシュの更新
            self.validator.validate(self.container)
            self.problematic_indices = self._collect_problematic_indices(self.validator.validation_results)
            self.cleaner = DataCleaner(self.validator, self.container)
            
            # 修正の影響を受けたレコード数
            if fix_method == "drop":
                affected_count = len(target_indices)
            else:
                affected_count = len([idx for idx in target_indices if idx in data.index])
            
            return {
                "status": "success",
                "affected_count": affected_count,
                "problem_type": problem_type,
                "fix_method": fix_method,
                "container": fixed_container,
                "fix_info": fix_info
            }
            
        except Exception as e:
            return {"status": "error", "message": f"修正適用中にエラーが発生しました: {e}"}
    
    def _fix_missing_data(self, data: pd.DataFrame, fix_method: str, target_indices: List[int]) -> pd.DataFrame:
        """
        欠損値を修正
        
        Parameters
        ----------
        data : pd.DataFrame
            修正対象のデータ
        fix_method : str
            修正方法ID
        target_indices : List[int]
            対象レコードのインデックス
            
        Returns
        -------
        pd.DataFrame
            修正後のデータ
        """
        # 欠損値を含むカラムを特定
        target_data = data.loc[target_indices]
        null_columns = []
        
        for col in target_data.columns:
            if target_data[col].isna().any():
                null_columns.append(col)
        
        if not null_columns:
            return data  # 修正なし
        
        # データのコピーを作成
        fixed_data = data.copy()
        
        # 修正方法に基づいて処理
        if fix_method == "interpolate":
            # 線形補間
            for col in null_columns:
                if pd.api.types.is_numeric_dtype(fixed_data[col]):
                    fixed_data[col] = fixed_data[col].interpolate(method="linear")
        
        elif fix_method == "ffill":
            # 前方向に埋める
            for col in null_columns:
                fixed_data[col] = fixed_data[col].ffill()
        
        elif fix_method == "bfill":
            # 後方向に埋める
            for col in null_columns:
                fixed_data[col] = fixed_data[col].bfill()
        
        elif fix_method == "drop":
            # 欠損値を含む行を削除
            rows_to_drop = []
            
            for idx in target_indices:
                if idx in fixed_data.index:
                    row = fixed_data.loc[idx]
                    if any(pd.isna(row[col]) for col in null_columns):
                        rows_to_drop.append(idx)
            
            fixed_data = fixed_data.drop(rows_to_drop).reset_index(drop=True)
        
        return fixed_data
    
    def _fix_out_of_range(self, data: pd.DataFrame, fix_method: str, target_indices: List[int]) -> pd.DataFrame:
        """
        範囲外の値を修正
        
        Parameters
        ----------
        data : pd.DataFrame
            修正対象のデータ
        fix_method : str
            修正方法ID
        target_indices : List[int]
            対象レコードのインデックス
            
        Returns
        -------
        pd.DataFrame
            修正後のデータ
        """
        # 範囲外の値を持つカラムと許容範囲を特定
        range_info = {}
        
        for result in self.validator.validation_results:
            if not result["is_valid"] and "Value Range Check" in result["rule_name"]:
                details = result["details"]
                column = details.get("column", "")
                min_value = details.get("min_value")
                max_value = details.get("max_value")
                
                if column and column in data.columns:
                    range_info[column] = {"min": min_value, "max": max_value}
        
        if not range_info:
            return data  # 修正なし
        
        # データのコピーを作成
        fixed_data = data.copy()
        
        # 修正方法に基づいて処理
        if fix_method == "clip":
            # 値をクリップ
            for col, range_val in range_info.items():
                if pd.api.types.is_numeric_dtype(fixed_data[col]):
                    for idx in target_indices:
                        if idx in fixed_data.index:
                            value = fixed_data.loc[idx, col]
                            
                            # 範囲外ならクリップ
                            if range_val["min"] is not None and value < range_val["min"]:
                                fixed_data.loc[idx, col] = range_val["min"]
                            elif range_val["max"] is not None and value > range_val["max"]:
                                fixed_data.loc[idx, col] = range_val["max"]
        
        elif fix_method == "replace":
            # 平均値に置換
            for col, range_val in range_info.items():
                if pd.api.types.is_numeric_dtype(fixed_data[col]):
                    # 範囲内の値から平均を計算
                    valid_values = fixed_data[col]
                    
                    if range_val["min"] is not None:
                        valid_values = valid_values[valid_values >= range_val["min"]]
                    
                    if range_val["max"] is not None:
                        valid_values = valid_values[valid_values <= range_val["max"]]
                    
                    if not valid_values.empty:
                        mean_value = valid_values.mean()
                        
                        # 範囲外の値を平均値に置換
                        for idx in target_indices:
                            if idx in fixed_data.index:
                                value = fixed_data.loc[idx, col]
                                
                                if ((range_val["min"] is not None and value < range_val["min"]) or
                                    (range_val["max"] is not None and value > range_val["max"])):
                                    fixed_data.loc[idx, col] = mean_value
        
        elif fix_method == "drop":
            # 範囲外の値を含む行を削除
            rows_to_drop = []
            
            for idx in target_indices:
                if idx in fixed_data.index:
                    row = fixed_data.loc[idx]
                    
                    for col, range_val in range_info.items():
                        if pd.api.types.is_numeric_dtype(fixed_data[col]):
                            value = row[col]
                            
                            if ((range_val["min"] is not None and value < range_val["min"]) or
                                (range_val["max"] is not None and value > range_val["max"])):
                                rows_to_drop.append(idx)
                                break
            
            fixed_data = fixed_data.drop(rows_to_drop).reset_index(drop=True)
        
        return fixed_data
    
    def _fix_duplicates(self, data: pd.DataFrame, fix_method: str, target_indices: List[int]) -> pd.DataFrame:
        """
        重複タイムスタンプを修正
        
        Parameters
        ----------
        data : pd.DataFrame
            修正対象のデータ
        fix_method : str
            修正方法ID
        target_indices : List[int]
            対象レコードのインデックス
            
        Returns
        -------
        pd.DataFrame
            修正後のデータ
        """
        if "timestamp" not in data.columns:
            return data  # 修正なし
        
        # データのコピーを作成
        fixed_data = data.copy()
        
        # 重複タイムスタンプを含む行を特定
        target_data = fixed_data.loc[target_indices]
        duplicates = target_data[target_data.duplicated(subset=["timestamp"], keep=False)]
        
        if duplicates.empty:
            return data  # 修正なし
        
        # 修正方法に基づいて処理
        if fix_method == "offset":
            # タイムスタンプをずらす
            duplicate_groups = duplicates.groupby("timestamp")
            
            for ts, group in duplicate_groups:
                indices = group.index.tolist()
                
                # 最初の行はそのまま、2番目以降は1ミリ秒ずつずらす
                for i, idx in enumerate(indices[1:], 1):
                    if idx in fixed_data.index:
                        fixed_data.loc[idx, "timestamp"] = ts + pd.Timedelta(milliseconds=i)
        
        elif fix_method == "drop":
            # 重複を削除 - 2番目以降を削除
            # まず重複を特定
            duplicate_indices = []
            
            for _, group in fixed_data.groupby("timestamp"):
                if len(group) > 1:
                    # 最初の行を除く
                    duplicate_indices.extend(group.index.tolist()[1:])
            
            # 対象インデックス内の重複のみ削除
            rows_to_drop = [idx for idx in duplicate_indices if idx in target_indices]
            fixed_data = fixed_data.drop(rows_to_drop).reset_index(drop=True)
        
        # タイムスタンプでソート
        fixed_data = fixed_data.sort_values("timestamp").reset_index(drop=True)
        
        return fixed_data
    
    def _fix_spatial_anomalies(self, data: pd.DataFrame, fix_method: str, target_indices: List[int]) -> pd.DataFrame:
        """
        空間的異常を修正
        
        Parameters
        ----------
        data : pd.DataFrame
            修正対象のデータ
        fix_method : str
            修正方法ID
        target_indices : List[int]
            対象レコードのインデックス
            
        Returns
        -------
        pd.DataFrame
            修正後のデータ
        """
        if "latitude" not in data.columns or "longitude" not in data.columns:
            return data  # 修正なし
        
        # データのコピーを作成
        fixed_data = data.copy()
        
        # 修正方法に基づいて処理
        if fix_method == "interpolate":
            # 位置を補間
            for idx in target_indices:
                if idx in fixed_data.index:
                    # 異常ポイントを欠損値に置き換え
                    fixed_data.loc[idx, "latitude"] = np.nan
                    fixed_data.loc[idx, "longitude"] = np.nan
            
            # 欠損値を補間
            fixed_data["latitude"] = fixed_data["latitude"].interpolate(method="linear")
            fixed_data["longitude"] = fixed_data["longitude"].interpolate(method="linear")
        
        elif fix_method == "drop":
            # 異常ポイントを削除
            fixed_data = fixed_data.drop(target_indices).reset_index(drop=True)
        
        return fixed_data
    
    def _fix_temporal_anomalies(self, data: pd.DataFrame, fix_method: str, target_indices: List[int]) -> pd.DataFrame:
        """
        時間的異常を修正
        
        Parameters
        ----------
        data : pd.DataFrame
            修正対象のデータ
        fix_method : str
            修正方法ID
        target_indices : List[int]
            対象レコードのインデックス
            
        Returns
        -------
        pd.DataFrame
            修正後のデータ
        """
        if "timestamp" not in data.columns:
            return data  # 修正なし
        
        # データのコピーを作成
        fixed_data = data.copy()
        
        # 時間的異常の詳細を取得
        reverse_indices = []
        gap_indices = []
        
        for result in self.validator.validation_results:
            if not result["is_valid"] and "Temporal Consistency Check" in result["rule_name"]:
                details = result["details"]
                if "reverse_indices" in details:
                    reverse_indices = details["reverse_indices"]
                if "gap_indices" in details:
                    gap_indices = details["gap_indices"]
                break
        
        # 対象インデックス内の異常のみ処理
        reverse_indices = [idx for idx in reverse_indices if idx in target_indices]
        gap_indices = [idx for idx in gap_indices if idx in target_indices]
        
        if not reverse_indices and not gap_indices:
            return data  # 修正なし
        
        # 修正方法に基づいて処理
        if fix_method == "fix_reverse":
            # 時間逆行を修正
            # タイムスタンプでソート
            sorted_data = fixed_data.sort_values("timestamp")
            
            for idx in reverse_indices:
                if idx in fixed_data.index and idx > 0:
                    # 前のタイムスタンプ + 1秒に設定
                    prev_idx = idx - 1
                    if prev_idx in fixed_data.index:
                        prev_ts = fixed_data.loc[prev_idx, "timestamp"]
                        fixed_data.loc[idx, "timestamp"] = prev_ts + pd.Timedelta(seconds=1)
        
        elif fix_method == "drop":
            # 時間的異常ポイントを削除
            rows_to_drop = reverse_indices + gap_indices
            fixed_data = fixed_data.drop(rows_to_drop).reset_index(drop=True)
        
        # タイムスタンプでソート
        fixed_data = fixed_data.sort_values("timestamp").reset_index(drop=True)
        
        return fixed_data
    
    def _get_problem_type_name(self, problem_type: str) -> str:
        """
        問題タイプの名前を取得
        
        Parameters
        ----------
        problem_type : str
            問題タイプ
            
        Returns
        -------
        str
            問題タイプの名前
        """
        type_names = {
            "missing_data": "欠損値",
            "out_of_range": "範囲外の値",
            "duplicates": "重複タイムスタンプ",
            "spatial_anomalies": "空間的異常",
            "temporal_anomalies": "時間的異常",
            "all": "すべての問題"
        }
        return type_names.get(problem_type, problem_type)


def basic_fix_options(container: GPSDataContainer, 
                     validator: DataValidator,
                     cleaner: Optional[DataCleaner] = None,
                     key_prefix: str = "fix_options",
                     problem_type: Optional[str] = None,
                     selected_indices: Optional[List[int]] = None,
                     on_fix_applied: Optional[Callable[[Dict[str, Any]], None]] = None) -> Dict[str, Any]:
    """
    データ問題に対する基本的な修正オプションを提供するヘルパー関数
    
    Parameters
    ----------
    container : GPSDataContainer
        GPSデータコンテナ
    validator : DataValidator
        データ検証器
    cleaner : Optional[DataCleaner], optional
        データクリーナー, by default None
    key_prefix : str, optional
        Streamlitのキープレフィックス, by default "fix_options"
    problem_type : Optional[str], optional
        表示する問題タイプ, by default None
    selected_indices : Optional[List[int]], optional
        選択されたレコードのインデックス, by default None
    on_fix_applied : Optional[Callable[[Dict[str, Any]], None]], optional
        修正適用時のコールバック関数, by default None
        
    Returns
    -------
    Dict[str, Any]
        修正適用の結果
    """
    fix_options_component = BasicFixOptions(
        container=container,
        validator=validator,
        cleaner=cleaner,
        key_prefix=key_prefix,
        on_fix_applied=on_fix_applied
    )
    
    return fix_options_component.render(problem_type, selected_indices)
