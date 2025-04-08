"""
ui.components.validation.interactive_fix

問題箇所のインタラクティブな修正インターフェースコンポーネント
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Callable, Tuple, Union
from datetime import datetime, timedelta

from sailing_data_processor.data_model.container import GPSDataContainer
from sailing_data_processor.validation.data_validator import DataValidator
from sailing_data_processor.validation.data_cleaner import DataCleaner

from ui.components.validation.basic_fix_options import BasicFixOptions


class InteractiveFix:
    """
    問題箇所のインタラクティブな修正インターフェースコンポーネント
    
    Parameters
    ----------
    container : GPSDataContainer
        GPSデータコンテナ
    validator : DataValidator
        データ検証器
    cleaner : Optional[DataCleaner], optional
        データクリーナー, by default None
    key_prefix : str, optional
        Streamlitのキープレフィックス, by default "interactive_fix"
    on_fix_applied : Optional[Callable[[Dict[str, Any]], None]], optional
        修正適用時のコールバック関数, by default None
    """
    
    def __init__(self, 
                container: GPSDataContainer, 
                validator: DataValidator,
                cleaner: Optional[DataCleaner] = None,
                key_prefix: str = "interactive_fix",
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
            Streamlitのキープレフィックス, by default "interactive_fix"
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
        
        # 基本的な修正オプションコンポーネント
        self.fix_options = BasicFixOptions(
            container=container,
            validator=validator,
            cleaner=cleaner,
            key_prefix=f"{key_prefix}_options",
            on_fix_applied=on_fix_applied
        )
        
        # セッション状態の初期化
        if f"{self.key_prefix}_selected_record" not in st.session_state:
            st.session_state[f"{self.key_prefix}_selected_record"] = None
        
        if f"{self.key_prefix}_edit_mode" not in st.session_state:
            st.session_state[f"{self.key_prefix}_edit_mode"] = False
        
        if f"{self.key_prefix}_modified_values" not in st.session_state:
            st.session_state[f"{self.key_prefix}_modified_values"] = {}
        
        if f"{self.key_prefix}_selected_tab" not in st.session_state:
            st.session_state[f"{self.key_prefix}_selected_tab"] = "レコード選択"
        
        if f"{self.key_prefix}_batch_selection" not in st.session_state:
            st.session_state[f"{self.key_prefix}_batch_selection"] = []
    
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
        indices["all"] = sorted(list(indices["all"]))
        
        return indices
    
    def render(self) -> Dict[str, Any]:
        """
        インタラクティブな修正インターフェースをレンダリング
        
        Returns
        -------
        Dict[str, Any]
            修正適用の結果
        """
        result = {"status": "no_action", "applied_fix": None}
        
        if len(self.problematic_indices["all"]) == 0:
            st.success("データに問題は見つかりませんでした。")
            return result
        
        # モードタブ
        tabs = ["レコード選択", "バッチ修正", "問題カテゴリ別"]
        selected_tab = st.radio(
            "修正モード",
            options=tabs,
            index=tabs.index(st.session_state[f"{self.key_prefix}_selected_tab"]),
            horizontal=True,
            key=f"{self.key_prefix}_tab_select"
        )
        
        # セッション状態の更新
        st.session_state[f"{self.key_prefix}_selected_tab"] = selected_tab
        
        # 選択したタブに基づいて表示
        if selected_tab == "レコード選択":
            fix_result = self._render_record_selection_mode()
            if fix_result["status"] == "success":
                result = fix_result
        
        elif selected_tab == "バッチ修正":
            fix_result = self._render_batch_mode()
            if fix_result["status"] == "success":
                result = fix_result
        
        elif selected_tab == "問題カテゴリ別":
            fix_result = self._render_category_mode()
            if fix_result["status"] == "success":
                result = fix_result
        
        return result
    
    def _render_record_selection_mode(self) -> Dict[str, Any]:
        """
        レコード選択モードのUI表示
        
        Returns
        -------
        Dict[str, Any]
            修正適用の結果
        """
        result = {"status": "no_action", "applied_fix": None}
        
        st.subheader("問題レコードを選択して修正")
        
        # 問題レコードの一覧を表示
        problem_df = self._create_problem_records_dataframe()
        
        # 問題タイプによるフィルタリング
        problem_types = ["すべての問題"]
        for p_type in self.problematic_indices.keys():
            if p_type != "all" and self.problematic_indices[p_type]:
                problem_types.append(self._get_problem_type_name(p_type))
        
        selected_filter = st.selectbox(
            "問題タイプでフィルタ",
            options=problem_types,
            index=0,
            key=f"{self.key_prefix}_problem_filter"
        )
        
        # フィルタリングされたデータフレーム
        if selected_filter != "すべての問題":
            filter_type = next((k for k, v in self._get_problem_type_names().items() 
                            if v == selected_filter), None)
            
            if filter_type and filter_type in self.problematic_indices:
                filtered_indices = self.problematic_indices[filter_type]
                filtered_df = problem_df[problem_df["インデックス"].isin(filtered_indices)]
            else:
                filtered_df = problem_df
        else:
            filtered_df = problem_df
        
        # データフレーム表示
        if not filtered_df.empty:
            st.dataframe(filtered_df, use_container_width=True)
        else:
            st.info("フィルタ条件に一致する問題レコードがありません。")
            return result
        
        # レコード選択
        selected_idx = st.selectbox(
            "修正するレコードを選択",
            options=filtered_df["インデックス"].tolist(),
            format_func=lambda x: f"レコード {x}: {self._get_record_summary(x)}",
            key=f"{self.key_prefix}_record_selector"
        )
        
        # 選択レコードをセッション状態に保存
        st.session_state[f"{self.key_prefix}_selected_record"] = selected_idx
        
        # 選択したレコードを表示
        if selected_idx is not None:
            return self._render_record_edit_interface(selected_idx)
        
        return result
    
    def _render_batch_mode(self) -> Dict[str, Any]:
        """
        バッチ修正モードのUI表示
        
        Returns
        -------
        Dict[str, Any]
            修正適用の結果
        """
        result = {"status": "no_action", "applied_fix": None}
        
        st.subheader("複数レコードの一括修正")
        
        # 問題カテゴリごとの件数表示
        st.write("問題タイプ別の件数:")
        
        # 問題タイプ別の件数を表形式で表示
        counts = []
        for p_type, indices in self.problematic_indices.items():
            if p_type != "all":
                counts.append({
                    "問題タイプ": self._get_problem_type_name(p_type),
                    "件数": len(indices),
                    "割合": f"{len(indices) / max(1, len(self.container.data)) * 100:.1f}%"
                })
        
        # 合計
        counts.append({
            "問題タイプ": "合計 (重複あり)",
            "件数": sum(len(indices) for p_type, indices in self.problematic_indices.items() if p_type != "all"),
            "割合": f"{sum(len(indices) for p_type, indices in self.problematic_indices.items() if p_type != 'all') / max(1, len(self.container.data)) * 100:.1f}%"
        })
        
        # 合計 (重複なし)
        counts.append({
            "問題タイプ": "合計 (重複なし)",
            "件数": len(self.problematic_indices["all"]),
            "割合": f"{len(self.problematic_indices['all']) / max(1, len(self.container.data)) * 100:.1f}%"
        })
        
        counts_df = pd.DataFrame(counts)
        st.dataframe(counts_df, use_container_width=True, hide_index=True)
        
        # 一括修正の対象選択
        st.subheader("修正対象を選択")
        
        # 問題タイプ別の選択
        problem_type_options = []
        for p_type, indices in self.problematic_indices.items():
            if p_type != "all" and indices:
                problem_type_options.append({
                    "label": f"{self._get_problem_type_name(p_type)} ({len(indices)}件)",
                    "type": p_type
                })
        
        selected_types = []
        
        # チェックボックスで問題タイプを選択
        for opt in problem_type_options:
            if st.checkbox(
                opt["label"],
                value=False,
                key=f"{self.key_prefix}_batch_type_{opt['type']}"
            ):
                selected_types.append(opt["type"])
        
        # 選択された問題タイプのレコードを特定
        selected_indices = []
        for p_type in selected_types:
            selected_indices.extend(self.problematic_indices[p_type])
        
        # 重複を除去
        selected_indices = sorted(list(set(selected_indices)))
        
        # 選択されたレコード数の表示
        if selected_indices:
            st.write(f"**選択済み:** {len(selected_indices)}件のレコード")
            
            # 選択されたレコードをセッション状態に保存
            st.session_state[f"{self.key_prefix}_batch_selection"] = selected_indices
            
            # バッチ修正オプションの表示
            st.subheader("バッチ修正オプション")
            
            # 共通の問題タイプを特定
            common_problem_types = []
            for p_type in selected_types:
                common_problem_types.append(p_type)
            
            if common_problem_types:
                # 一緒に修正できる問題タイプがあれば、オプションを表示
                st.write("**一括修正で解決可能な問題タイプ:**")
                
                for p_type in common_problem_types:
                    st.write(f"- {self._get_problem_type_name(p_type)}")
                
                # BasicFixOptionsを使って修正オプションを表示
                fix_result = self.fix_options.render(None, selected_indices)
                
                if fix_result["status"] == "success":
                    return fix_result
            else:
                st.info("選択されたレコードに共通の問題タイプが見つかりません。異なる問題タイプを持つレコードは個別に修正することをお勧めします。")
        else:
            st.info("修正対象の問題タイプを選択してください。")
        
        return result
    
    def _render_category_mode(self) -> Dict[str, Any]:
        """
        問題カテゴリ別のUI表示
        
        Returns
        -------
        Dict[str, Any]
            修正適用の結果
        """
        result = {"status": "no_action", "applied_fix": None}
        
        st.subheader("問題タイプ別に修正")
        
        # 問題タイプの選択
        problem_types = []
        for p_type, indices in self.problematic_indices.items():
            if p_type != "all" and indices:
                problem_types.append((p_type, self._get_problem_type_name(p_type), len(indices)))
        
        if not problem_types:
            st.info("修正可能な問題が見つかりません。")
            return result
        
        # 問題タイプを選択
        selected_type = st.selectbox(
            "問題タイプを選択",
            options=[p[0] for p in problem_types],
            format_func=lambda x: next((f"{p[1]} ({p[2]}件)" for p in problem_types if p[0] == x), x),
            key=f"{self.key_prefix}_category_selector"
        )
        
        if selected_type:
            # 選択された問題タイプのレコードを特定
            target_indices = self.problematic_indices[selected_type]
            
            # BasicFixOptionsを使って修正オプションを表示
            fix_result = self.fix_options.render(selected_type, target_indices)
            
            if fix_result["status"] == "success":
                return fix_result
        
        return result
    
    def _render_record_edit_interface(self, record_idx: int) -> Dict[str, Any]:
        """
        選択したレコードの編集インターフェースを表示
        
        Parameters
        ----------
        record_idx : int
            選択したレコードのインデックス
            
        Returns
        -------
        Dict[str, Any]
            修正適用の結果
        """
        result = {"status": "no_action", "applied_fix": None}
        
        if record_idx is None or record_idx >= len(self.container.data):
            st.error("有効なレコードが選択されていません。")
            return result
        
        # 選択したレコードのデータ
        record = self.container.data.iloc[record_idx]
        
        # レコードの問題タイプを特定
        record_problem_types = []
        for p_type, indices in self.problematic_indices.items():
            if p_type != "all" and record_idx in indices:
                record_problem_types.append(p_type)
        
        # レコード情報の表示
        st.subheader(f"レコード {record_idx} の詳細と修正")
        
        # 問題タイプの表示
        problem_type_names = [self._get_problem_type_name(p) for p in record_problem_types]
        st.write(f"**問題タイプ:** {', '.join(problem_type_names)}")
        
        # レコードの基本情報
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**基本情報:**")
            
            if "timestamp" in record:
                ts = record["timestamp"]
                ts_str = ts.strftime("%Y-%m-%d %H:%M:%S") if isinstance(ts, (datetime, pd.Timestamp)) else str(ts)
                st.write(f"タイムスタンプ: {ts_str}")
            
            if "latitude" in record and "longitude" in record:
                st.write(f"位置: ({record['latitude']:.6f}, {record['longitude']:.6f})")
            
            if "speed" in record:
                st.write(f"速度: {record['speed']:.2f}")
        
        with col2:
            st.write("**問題の詳細:**")
            
            for p_type in record_problem_types:
                st.write(f"- {self._get_problem_type_name(p_type)}")
                
                # 問題タイプごとの詳細情報
                if p_type == "missing_data":
                    null_cols = [col for col in record.index if pd.isna(record[col])]
                    if null_cols:
                        st.write(f"  - 欠損カラム: {', '.join(null_cols)}")
                
                elif p_type == "out_of_range":
                    # 範囲外の値の詳細を検出
                    for result in self.validator.validation_results:
                        if not result["is_valid"] and "Value Range Check" in result["rule_name"]:
                            details = result["details"]
                            if "out_of_range_indices" in details and record_idx in details["out_of_range_indices"]:
                                col = details.get("column", "")
                                min_val = details.get("min_value", "なし")
                                max_val = details.get("max_value", "なし")
                                actual_val = record.get(col, "")
                                
                                st.write(f"  - カラム '{col}': 値 {actual_val} (許容範囲: {min_val}～{max_val})")
                
                elif p_type == "duplicates":
                    # 重複タイムスタンプの詳細
                    if "timestamp" in record:
                        ts = record["timestamp"]
                        duplicates = self.container.data[self.container.data["timestamp"] == ts].index.tolist()
                        other_dupes = [idx for idx in duplicates if idx != record_idx]
                        
                        if other_dupes:
                            st.write(f"  - 重複インデックス: {', '.join(map(str, other_dupes))}")
                
                elif p_type == "spatial_anomalies":
                    # 空間的異常の詳細
                    for result in self.validator.validation_results:
                        if not result["is_valid"] and "Spatial Consistency Check" in result["rule_name"]:
                            details = result["details"]
                            if "anomaly_details" in details:
                                for anomaly in details["anomaly_details"]:
                                    if anomaly.get("original_index") == record_idx:
                                        st.write(f"  - 距離: {anomaly.get('distance_meters', 0):.2f}m")
                                        st.write(f"  - 経過時間: {anomaly.get('time_diff_seconds', 0):.2f}秒")
                                        st.write(f"  - 計算速度: {anomaly.get('speed_knots', 0):.2f}ノット")
                                        break
                
                elif p_type == "temporal_anomalies":
                    # 時間的異常の詳細
                    for result in self.validator.validation_results:
                        if not result["is_valid"] and "Temporal Consistency Check" in result["rule_name"]:
                            details = result["details"]
                            
                            # 時間ギャップの詳細
                            if "gap_details" in details:
                                for gap in details["gap_details"]:
                                    if gap.get("original_index") == record_idx:
                                        st.write(f"  - 時間ギャップ: {gap.get('gap_seconds', 0):.2f}秒")
                                        break
                            
                            # 時間逆行の詳細
                            if "reverse_details" in details:
                                for rev in details["reverse_details"]:
                                    if rev.get("original_index") == record_idx:
                                        st.write(f"  - 時間逆行: {abs(rev.get('diff_seconds', 0)):.2f}秒")
                                        break
        
        # 修正オプションの表示
        st.subheader("修正オプション")
        
        # 編集モード切り替え
        edit_mode = st.radio(
            "修正方法",
            options=["推奨修正を適用", "値を直接編集"],
            horizontal=True,
            key=f"{self.key_prefix}_edit_mode_toggle",
            index=0 if not st.session_state[f"{self.key_prefix}_edit_mode"] else 1
        )
        
        # セッション状態の更新
        st.session_state[f"{self.key_prefix}_edit_mode"] = (edit_mode == "値を直接編集")
        
        if edit_mode == "推奨修正を適用":
            # 修正オプション表示
            fix_result = self.fix_options.render(None, [record_idx])
            
            if fix_result["status"] == "success":
                return fix_result
        else:
            # 直接編集モードの表示
            return self._render_direct_edit_interface(record_idx, record, record_problem_types)
        
        return result
    
    def _render_direct_edit_interface(self, record_idx: int, record: pd.Series, problem_types: List[str]) -> Dict[str, Any]:
        """
        レコードを直接編集するインターフェースを表示
        
        Parameters
        ----------
        record_idx : int
            レコードのインデックス
        record : pd.Series
            レコードデータ
        problem_types : List[str]
            レコードの問題タイプリスト
            
        Returns
        -------
        Dict[str, Any]
            修正適用の結果
        """
        result = {"status": "no_action", "applied_fix": None}
        
        st.write("**値を直接編集:**")
        
        # 編集値の初期化（必要に応じて）
        if f"{self.key_prefix}_modified_values" not in st.session_state:
            st.session_state[f"{self.key_prefix}_modified_values"] = {}
        
        modified_values = {}
        
        # 問題タイプに関連するカラムの編集フォームを表示
        for p_type in problem_types:
            if p_type == "missing_data":
                # 欠損値の編集
                null_cols = [col for col in record.index if pd.isna(record[col])]
                
                if null_cols:
                    st.write(f"**欠損値の編集:**")
                    
                    for col in null_cols:
                        col_type = str(record[col].dtype) if not pd.isna(record[col]) else "unknown"
                        
                        # データ型に応じた入力ウィジェット
                        if "float" in col_type or "int" in col_type:
                            # 数値入力
                            new_val = st.number_input(
                                f"{col}",
                                value=0.0,
                                key=f"{self.key_prefix}_{record_idx}_edit_{col}"
                            )
                        elif "datetime" in col_type or col == "timestamp":
                            # 日付/時刻入力
                            new_date = st.date_input(
                                f"{col} (日付)",
                                value=datetime.now().date(),
                                key=f"{self.key_prefix}_{record_idx}_edit_{col}_date"
                            )
                            new_time = st.time_input(
                                f"{col} (時刻)",
                                value=datetime.now().time(),
                                key=f"{self.key_prefix}_{record_idx}_edit_{col}_time"
                            )
                            new_val = pd.Timestamp(datetime.combine(new_date, new_time))
                        else:
                            # テキスト入力
                            new_val = st.text_input(
                                f"{col}",
                                value="",
                                key=f"{self.key_prefix}_{record_idx}_edit_{col}"
                            )
                        
                        modified_values[col] = new_val
            
            elif p_type == "out_of_range":
                # 範囲外の値の編集
                for result in self.validator.validation_results:
                    if not result["is_valid"] and "Value Range Check" in result["rule_name"]:
                        details = result["details"]
                        if "out_of_range_indices" in details and record_idx in details["out_of_range_indices"]:
                            col = details.get("column", "")
                            min_val = details.get("min_value")
                            max_val = details.get("max_value")
                            current_val = record.get(col, "")
                            
                            if col in record.index:
                                st.write(f"**範囲外の値の編集:**")
                                
                                # 最小値と最大値を制限に設定
                                min_input = float(min_val) if min_val is not None else float("-inf")
                                max_input = float(max_val) if max_val is not None else float("inf")
                                
                                new_val = st.number_input(
                                    f"{col} (現在値: {current_val}, 許容範囲: {min_val if min_val is not None else '制限なし'}～{max_val if max_val is not None else '制限なし'})",
                                    value=float(current_val) if not pd.isna(current_val) else 0.0,
                                    min_value=min_input if min_input != float("-inf") else None,
                                    max_value=max_input if max_input != float("inf") else None,
                                    key=f"{self.key_prefix}_{record_idx}_edit_{col}"
                                )
                                
                                modified_values[col] = new_val
            
            elif p_type == "duplicates":
                # 重複タイムスタンプの編集
                if "timestamp" in record:
                    st.write(f"**重複タイムスタンプの編集:**")
                    
                    current_ts = record["timestamp"]
                    current_ts_str = current_ts.strftime("%Y-%m-%d %H:%M:%S") if isinstance(current_ts, (datetime, pd.Timestamp)) else str(current_ts)
                    
                    # 日付と時刻を分けて編集
                    current_date = current_ts.date() if isinstance(current_ts, (datetime, pd.Timestamp)) else datetime.now().date()
                    current_time = current_ts.time() if isinstance(current_ts, (datetime, pd.Timestamp)) else datetime.now().time()
                    
                    new_date = st.date_input(
                        f"日付 (現在: {current_date})",
                        value=current_date,
                        key=f"{self.key_prefix}_{record_idx}_edit_timestamp_date"
                    )
                    
                    new_time = st.time_input(
                        f"時刻 (現在: {current_time})",
                        value=current_time,
                        key=f"{self.key_prefix}_{record_idx}_edit_timestamp_time"
                    )
                    
                    # ミリ秒まで調整できるスライダー
                    current_ms = current_ts.microsecond // 1000 if isinstance(current_ts, (datetime, pd.Timestamp)) else 0
                    new_ms = st.slider(
                        "ミリ秒",
                        min_value=0,
                        max_value=999,
                        value=current_ms,
                        key=f"{self.key_prefix}_{record_idx}_edit_timestamp_ms"
                    )
                    
                    # 新しいタイムスタンプを作成
                    new_ts = datetime.combine(new_date, new_time).replace(microsecond=new_ms * 1000)
                    new_val = pd.Timestamp(new_ts)
                    
                    st.write(f"新しいタイムスタンプ: {new_val}")
                    modified_values["timestamp"] = new_val
            
            elif p_type == "spatial_anomalies":
                # 位置情報の編集
                if "latitude" in record and "longitude" in record:
                    st.write(f"**位置情報の編集:**")
                    
                    current_lat = record["latitude"]
                    current_lon = record["longitude"]
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        new_lat = st.number_input(
                            f"緯度 (現在: {current_lat:.6f})",
                            value=float(current_lat) if not pd.isna(current_lat) else 0.0,
                            min_value=-90.0,
                            max_value=90.0,
                            format="%.6f",
                            key=f"{self.key_prefix}_{record_idx}_edit_latitude"
                        )
                        modified_values["latitude"] = new_lat
                    
                    with col2:
                        new_lon = st.number_input(
                            f"経度 (現在: {current_lon:.6f})",
                            value=float(current_lon) if not pd.isna(current_lon) else 0.0,
                            min_value=-180.0,
                            max_value=180.0,
                            format="%.6f",
                            key=f"{self.key_prefix}_{record_idx}_edit_longitude"
                        )
                        modified_values["longitude"] = new_lon
            
            elif p_type == "temporal_anomalies":
                # タイムスタンプの編集（重複とは別に）
                if "timestamp" in record and "duplicates" not in problem_types:
                    st.write(f"**タイムスタンプの編集:**")
                    
                    current_ts = record["timestamp"]
                    current_ts_str = current_ts.strftime("%Y-%m-%d %H:%M:%S") if isinstance(current_ts, (datetime, pd.Timestamp)) else str(current_ts)
                    
                    # 日付と時刻を分けて編集
                    current_date = current_ts.date() if isinstance(current_ts, (datetime, pd.Timestamp)) else datetime.now().date()
                    current_time = current_ts.time() if isinstance(current_ts, (datetime, pd.Timestamp)) else datetime.now().time()
                    
                    new_date = st.date_input(
                        f"日付 (現在: {current_date})",
                        value=current_date,
                        key=f"{self.key_prefix}_{record_idx}_edit_timestamp_date"
                    )
                    
                    new_time = st.time_input(
                        f"時刻 (現在: {current_time})",
                        value=current_time,
                        key=f"{self.key_prefix}_{record_idx}_edit_timestamp_time"
                    )
                    
                    # 新しいタイムスタンプを作成
                    new_val = pd.Timestamp(datetime.combine(new_date, new_time))
                    
                    st.write(f"新しいタイムスタンプ: {new_val}")
                    modified_values["timestamp"] = new_val
        
        # 編集内容を保存
        st.session_state[f"{self.key_prefix}_modified_values"] = modified_values
        
        # 修正適用ボタン
        if modified_values and st.button("変更を適用", type="primary"):
            result = self._apply_direct_edit(record_idx, modified_values)
        
        return result
    
    def _apply_direct_edit(self, record_idx: int, modified_values: Dict[str, Any]) -> Dict[str, Any]:
        """
        直接編集を適用
        
        Parameters
        ----------
        record_idx : int
            レコードのインデックス
        modified_values : Dict[str, Any]
            修正された値
            
        Returns
        -------
        Dict[str, Any]
            修正適用の結果
        """
        try:
            # データのコピーを作成
            data = self.container.data.copy()
            
            # 修正情報
            fix_info = {
                "type": "direct_edit",
                "record_idx": record_idx,
                "modified_columns": list(modified_values.keys()),
                "timestamp": datetime.now().isoformat()
            }
            
            # 値を更新
            for col, val in modified_values.items():
                if col in data.columns:
                    data.loc[record_idx, col] = val
            
            # タイムスタンプ列があれば、ソート
            if "timestamp" in data.columns:
                data = data.sort_values("timestamp").reset_index(drop=True)
            
            # 修正されたデータでコンテナを更新
            fixed_container = GPSDataContainer(data, self.container.metadata.copy())
            
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
            affected_count = 1
            
            # コールバック関数を呼び出し
            if self.on_fix_applied:
                self.on_fix_applied({
                    "container": fixed_container,
                    "fix": fix_info
                })
            
            # 成功メッセージ
            st.success(f"レコード {record_idx} が正常に更新されました。")
            
            return {
                "status": "success",
                "affected_count": affected_count,
                "fix_type": "direct_edit",
                "container": fixed_container,
                "fix_info": fix_info
            }
            
        except Exception as e:
            st.error(f"修正の適用中にエラーが発生しました: {e}")
            return {"status": "error", "message": str(e)}
    
    def _create_problem_records_dataframe(self) -> pd.DataFrame:
        """
        問題のあるレコードのデータフレームを作成
        
        Returns
        -------
        pd.DataFrame
            問題レコードのデータフレーム
        """
        # 全ての問題インデックス
        problem_indices = sorted(self.problematic_indices["all"])
        
        if not problem_indices:
            return pd.DataFrame()
        
        # 問題レコード情報を収集
        problem_records = []
        
        for idx in problem_indices:
            if idx < len(self.container.data):
                record = self.container.data.iloc[idx]
                
                # 問題タイプを収集
                problem_types = []
                for p_type, indices in self.problematic_indices.items():
                    if p_type != "all" and idx in indices:
                        problem_types.append(self._get_problem_type_name(p_type))
                
                # 基本情報を抽出
                record_info = {
                    "インデックス": idx,
                    "問題タイプ": ", ".join(problem_types),
                    "問題数": len(problem_types)
                }
                
                # タイムスタンプがあれば追加
                if "timestamp" in record:
                    ts = record["timestamp"]
                    if isinstance(ts, (datetime, pd.Timestamp)):
                        record_info["タイムスタンプ"] = ts
                    else:
                        record_info["タイムスタンプ"] = str(ts)
                
                # 位置情報があれば追加
                if "latitude" in record and "longitude" in record:
                    record_info["緯度"] = record["latitude"]
                    record_info["経度"] = record["longitude"]
                
                # 速度があれば追加
                if "speed" in record:
                    record_info["速度"] = record["speed"]
                
                problem_records.append(record_info)
        
        # データフレームに変換
        problem_df = pd.DataFrame(problem_records)
        
        return problem_df
    
    def _get_record_summary(self, record_idx: int) -> str:
        """
        レコードの概要を取得
        
        Parameters
        ----------
        record_idx : int
            レコードのインデックス
            
        Returns
        -------
        str
            レコードの概要
        """
        if record_idx >= len(self.container.data):
            return "インデックス範囲外"
        
        record = self.container.data.iloc[record_idx]
        summary_parts = []
        
        # 問題タイプ
        problem_types = []
        for p_type, indices in self.problematic_indices.items():
            if p_type != "all" and record_idx in indices:
                problem_types.append(self._get_problem_type_name(p_type))
        
        if problem_types:
            summary_parts.append(f"問題: {', '.join(problem_types)}")
        
        # タイムスタンプ
        if "timestamp" in record:
            ts = record["timestamp"]
            ts_str = ts.strftime("%Y-%m-%d %H:%M:%S") if isinstance(ts, (datetime, pd.Timestamp)) else str(ts)
            summary_parts.append(f"時刻: {ts_str}")
        
        # 位置
        if "latitude" in record and "longitude" in record:
            summary_parts.append(f"位置: ({record['latitude']:.6f}, {record['longitude']:.6f})")
        
        return " | ".join(summary_parts)
    
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
        type_names = self._get_problem_type_names()
        return type_names.get(problem_type, problem_type)
    
    def _get_problem_type_names(self) -> Dict[str, str]:
        """
        問題タイプ名のマッピングを取得
        
        Returns
        -------
        Dict[str, str]
            問題タイプ名のマッピング
        """
        return {
            "missing_data": "欠損値",
            "out_of_range": "範囲外の値",
            "duplicates": "重複タイムスタンプ",
            "spatial_anomalies": "空間的異常",
            "temporal_anomalies": "時間的異常",
            "all": "すべての問題"
        }


def interactive_fix(container: GPSDataContainer, 
                  validator: DataValidator,
                  cleaner: Optional[DataCleaner] = None,
                  key_prefix: str = "interactive_fix",
                  on_fix_applied: Optional[Callable[[Dict[str, Any]], None]] = None) -> Dict[str, Any]:
    """
    問題箇所のインタラクティブな修正インターフェースを提供するヘルパー関数
    
    Parameters
    ----------
    container : GPSDataContainer
        GPSデータコンテナ
    validator : DataValidator
        データ検証器
    cleaner : Optional[DataCleaner], optional
        データクリーナー, by default None
    key_prefix : str, optional
        Streamlitのキープレフィックス, by default "interactive_fix"
    on_fix_applied : Optional[Callable[[Dict[str, Any]], None]], optional
        修正適用時のコールバック関数, by default None
        
    Returns
    -------
    Dict[str, Any]
        修正適用の結果
    """
    fix_component = InteractiveFix(
        container=container,
        validator=validator,
        cleaner=cleaner,
        key_prefix=key_prefix,
        on_fix_applied=on_fix_applied
    )
    
    return fix_component.render()
