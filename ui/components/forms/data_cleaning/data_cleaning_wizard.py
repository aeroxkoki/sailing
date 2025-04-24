# -*- coding: utf-8 -*-
"""
ui.components.forms.data_cleaning.data_cleaning_wizard

データクリーニングウィザードコンポーネント
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Any, Optional, Union, Callable, Tuple
import io
from datetime import datetime, timedelta

from sailing_data_processor.data_model.container import GPSDataContainer
from sailing_data_processor.validation.data_validator import DataValidator


class DataCleaningWizard:
    """
    データクリーニングウィザードコンポーネント
    
    GPSデータの検証と問題の修正を行うウィザード形式のUIコンポーネント
    
    Parameters
    ----------
    key : str, optional
        コンポーネントの一意のキー, by default "data_cleaning_wizard"
    on_clean_complete : Optional[Callable[[GPSDataContainer], None]], optional
        クリーニング完了時のコールバック関数, by default None
    """
    
    def __init__(self, 
                 key: str = "data_cleaning_wizard", 
                 on_clean_complete: Optional[Callable[[GPSDataContainer], None]] = None):
        """
        初期化
        
        Parameters
        ----------
        key : str, optional
            コンポーネントの一意のキー, by default "data_cleaning_wizard"
        on_clean_complete : Optional[Callable[[GPSDataContainer], None]], optional
            クリーニング完了時のコールバック関数, by default None
        """
        self.key = key
        self.on_clean_complete = on_clean_complete
        
        # セッション状態の初期化
        if f"{self.key}_step" not in st.session_state:
            st.session_state[f"{self.key}_step"] = 1
        if f"{self.key}_container" not in st.session_state:
            st.session_state[f"{self.key}_container"] = None
        if f"{self.key}_validation_results" not in st.session_state:
            st.session_state[f"{self.key}_validation_results"] = None
        if f"{self.key}_fixed_container" not in st.session_state:
            st.session_state[f"{self.key}_fixed_container"] = None
        if f"{self.key}_fixes" not in st.session_state:
            st.session_state[f"{self.key}_fixes"] = []
        if f"{self.key}_manual_fixes" not in st.session_state:
            st.session_state[f"{self.key}_manual_fixes"] = {}
        if f"{self.key}_show_fixes" not in st.session_state:
            st.session_state[f"{self.key}_show_fixes"] = {}
    
    def reset(self):
        """ウィザードの状態をリセット"""
        st.session_state[f"{self.key}_step"] = 1
        st.session_state[f"{self.key}_validation_results"] = None
        st.session_state[f"{self.key}_fixed_container"] = None
        st.session_state[f"{self.key}_fixes"] = []
        st.session_state[f"{self.key}_manual_fixes"] = {}
        st.session_state[f"{self.key}_show_fixes"] = {}
    
    def render(self, container: GPSDataContainer = None):
        """
        ウィザードをレンダリング
        
        Parameters
        ----------
        container : GPSDataContainer, optional
            クリーニング対象のGPSデータコンテナ, by default None
        """
        # コンテナを更新
        if container is not None:
            st.session_state[f"{self.key}_container"] = container
        
        # コンテナを取得
        container = st.session_state[f"{self.key}_container"]
        
        if container is None:
            st.warning("データが提供されていません。データをインポートしてください。")
            return
        
        # ステップに応じて表示を切り替え
        step = st.session_state[f"{self.key}_step"]
        
        if step == 1:
            self._render_step1_validation(container)
        elif step == 2:
            self._render_step2_auto_fix(container)
        elif step == 3:
            self._render_step3_manual_fix()
        elif step == 4:
            self._render_step4_preview_and_save()
    
    def _render_step1_validation(self, container: GPSDataContainer):
        """
        ステップ1: データ検証
        
        Parameters
        ----------
        container : GPSDataContainer
            検証対象のGPSデータコンテナ
        """
        st.header("ステップ1: データ検証")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.write("GPSデータの検証を行い、問題がないか確認します。")
            validate_button = st.button("データを検証", key=f"{self.key}_validate_button")
        
        with col2:
            st.write("検証オプション:")
            include_warnings = st.checkbox("警告を含める", value=True, key=f"{self.key}_include_warnings")
            include_info = st.checkbox("情報を含める", value=False, key=f"{self.key}_include_info")
        
        if validate_button or st.session_state.get(f"{self.key}_validation_results") is not None:
            # データ検証の実行
            validator = DataValidator()
            
            if validate_button or st.session_state.get(f"{self.key}_validation_results") is None:
                is_valid, results = validator.validate(container)
                st.session_state[f"{self.key}_validation_results"] = results
            else:
                results = st.session_state[f"{self.key}_validation_results"]
                is_valid = not any(not r["is_valid"] and r["severity"] == 'error' for r in results)
            
            # 検証結果の取得
            issues = []
            for result in results:
                if not result["is_valid"]:
                    severity = result["severity"]
                    if severity == 'error' or \
                       (severity == 'warning' and include_warnings) or \
                       (severity == 'info' and include_info):
                        issues.append(result)
            
            # 結果の表示
            if is_valid and not issues:
                st.success("データは検証に合格しました。問題は見つかりませんでした。")
                st.session_state[f"{self.key}_fixed_container"] = container  # 修正不要
                st.button("次へ: 確認", key=f"{self.key}_step1_next", on_click=self._go_to_step4)
            else:
                if not is_valid:
                    st.error("データは検証に失敗しました。以下の問題を修正してください。")
                else:
                    st.warning("データは検証に合格しましたが、いくつかの問題が見つかりました。")
                
                # 問題の表示
                if issues:
                    for i, issue in enumerate(issues):
                        with st.expander(f"{issue['severity'].upper()}: {issue['rule_name']} - {issue['description']}"):
                            details = issue['details']
                            
                            # 詳細情報を表示
                            for key, value in details.items():
                                if key in ['error', 'message']:
                                    st.error(value)
                                elif isinstance(value, list) and key not in ['missing_columns', 'found_columns', 'all_columns', 'columns']:
                                    st.write(f"**{key}**: {', '.join(map(str, value[:10]))}" + (f" ... 他 {len(value) - 10} 件" if len(value) > 10 else ""))
                                elif isinstance(value, dict) and key not in ['null_counts']:
                                    st.write(f"**{key}**:")
                                    for subkey, subvalue in list(value.items())[:10]:
                                        st.write(f"- {subkey}: {subvalue}")
                                    if len(value) > 10:
                                        st.write(f"... 他 {len(value) - 10} 件")
                                else:
                                    st.write(f"**{key}**: {value}")
                    
                    # 自動修正への移動ボタン
                    st.button("次へ: 自動修正", key=f"{self.key}_step1_next", on_click=self._go_to_step2)
                else:
                    st.info("表示オプションを変更すると、より多くの問題が表示される場合があります。")
                    st.session_state[f"{self.key}_fixed_container"] = container  # 修正不要
                    st.button("次へ: 確認", key=f"{self.key}_step1_next2", on_click=self._go_to_step4)
    
    def _render_step2_auto_fix(self, container: GPSDataContainer):
        """
        ステップ2: 自動修正
        
        Parameters
        ----------
        container : GPSDataContainer
            修正対象のGPSデータコンテナ
        """
        st.header("ステップ2: 自動修正")
        
        st.write("検出された問題の自動修正を行います。")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            autofix_button = st.button("問題を自動修正", key=f"{self.key}_autofix_button")
        
        with col2:
            st.write("修正オプション:")
            st.checkbox("重複タイムスタンプを修正", value=True, key=f"{self.key}_fix_duplicates", disabled=True)
            st.checkbox("欠損値を補間", value=True, key=f"{self.key}_fix_nulls", disabled=True)
            st.checkbox("異常値を削除", value=True, key=f"{self.key}_fix_anomalies", disabled=True)
        
        if autofix_button or st.session_state.get(f"{self.key}_fixes"):
            # 自動修正の実行
            validator = DataValidator()
            
            if autofix_button or not st.session_state.get(f"{self.key}_fixes"):
                fixed_container, fixes = validator.fix_common_issues(container)
                st.session_state[f"{self.key}_fixed_container"] = fixed_container
                st.session_state[f"{self.key}_fixes"] = fixes
            else:
                fixed_container = st.session_state[f"{self.key}_fixed_container"]
                fixes = st.session_state[f"{self.key}_fixes"]
            
            # 修正結果の表示
            if fixes:
                st.success(f"{len(fixes)}件の問題が自動修正されました。")
                
                # 修正内容の表示
                fix_types = {}
                for fix in fixes:
                    fix_type = fix.get('type', 'unknown')
                    if fix_type not in fix_types:
                        fix_types[fix_type] = []
                    fix_types[fix_type].append(fix)
                
                for fix_type, type_fixes in fix_types.items():
                    with st.expander(f"{fix_type} ({len(type_fixes)}件)"):
                        for fix in type_fixes:
                            st.write(fix.get('description', '詳細情報なし'))
                
                # 修正データの基本情報
                st.write("### 修正データ基本情報")
                before_count = len(container.data)
                after_count = len(fixed_container.data)
                difference = before_count - after_count
                
                col1, col2, col3 = st.columns(3)
                col1.metric("修正前データポイント数", before_count)
                col2.metric("修正後データポイント数", after_count)
                col3.metric("削除されたデータポイント数", difference, delta=f"{-difference}")
                
                # 修正データのプレビュー
                st.write("### 修正データプレビュー")
                st.dataframe(fixed_container.data.head(10))
                
                # 検証が残っている場合は手動修正へ、そうでなければ確認へ
                if self._has_remaining_issues(fixed_container):
                    st.button("次へ: 手動修正", key=f"{self.key}_step2_next", on_click=self._go_to_step3)
                else:
                    st.button("次へ: 確認", key=f"{self.key}_step2_next2", on_click=self._go_to_step4)
            else:
                st.info("自動修正可能な問題は見つかりませんでした。")
                
                if self._has_remaining_issues(container):
                    st.button("次へ: 手動修正", key=f"{self.key}_step2_next3", on_click=self._go_to_step3)
                else:
                    st.session_state[f"{self.key}_fixed_container"] = container  # 修正不要
                    st.button("次へ: 確認", key=f"{self.key}_step2_next4", on_click=self._go_to_step4)
        
        # 戻るボタン
        st.button("戻る: データ検証", key=f"{self.key}_step2_back", on_click=self._go_to_step1)
    
    def _render_step3_manual_fix(self):
        """ステップ3: 手動修正"""
        st.header("ステップ3: 手動修正")
        
        # 現在のコンテナを取得
        container = st.session_state.get(f"{self.key}_fixed_container")
        if container is None:
            container = st.session_state.get(f"{self.key}_container")
        
        if container is None:
            st.error("データが見つかりません。")
            st.button("戻る: 自動修正", key=f"{self.key}_step3_back", on_click=self._go_to_step2)
            return
        
        # 最新の検証結果を取得
        validator = DataValidator()
        is_valid, results = validator.validate(container)
        
        # 問題の検出
        issues = []
        for result in results:
            if not result["is_valid"]:
                issues.append(result)
        
        if not issues:
            st.success("すべての問題が修正されました。データはクリーンです。")
            st.button("次へ: 確認", key=f"{self.key}_step3_next", on_click=self._go_to_step4)
            return
        
        st.write("以下の問題は手動修正が必要です。問題を選択して修正オプションを確認してください。")
        
        # 手動修正セクション
        for i, issue in enumerate(issues):
            issue_key = f"{issue['rule_name']}_{i}"
            
            # 問題を表示するエクスパンダー
            with st.expander(f"{issue['severity'].upper()}: {issue['rule_name']} - {issue['description']}", expanded=st.session_state.get(f"{self.key}_show_fixes", {}).get(issue_key, False)):
                # 問題の詳細表示
                details = issue['details']
                st.write("### 問題の詳細")
                
                for key, value in details.items():
                    if key == 'error':
                        st.error(value)
                    elif key == 'message':
                        st.info(value)
                    elif isinstance(value, list) and key not in ['missing_columns', 'found_columns', 'all_columns', 'columns']:
                        st.write(f"**{key}**: {', '.join(map(str, value[:10]))}" + (f" ... 他 {len(value) - 10} 件" if len(value) > 10 else ""))
                    elif isinstance(value, dict) and key not in ['null_counts']:
                        st.write(f"**{key}**:")
                        for subkey, subvalue in list(value.items())[:10]:
                            st.write(f"- {subkey}: {subvalue}")
                        if len(value) > 10:
                            st.write(f"... 他 {len(value) - 10} 件")
                    else:
                        st.write(f"**{key}**: {value}")
                
                # 問題タイプ別の修正オプション
                st.write("### 修正オプション")
                
                if "Required Columns Check" in issue['rule_name']:
                    st.error("必須カラムがありません。データを再インポートするか、カラム名を変更する必要があります。")
                    
                    if 'missing_columns' in details:
                        # カラム名の変更オプション
                        st.write("既存のカラムを必須カラムにマッピングする:")
                        existing_columns = details.get('all_columns', [])
                        
                        for missing_col in details['missing_columns']:
                            col_options = ["(選択してください)"] + existing_columns
                            selected_col = st.selectbox(
                                f"'{missing_col}' にマッピングするカラム:", 
                                col_options,
                                key=f"{self.key}_map_{issue_key}_{missing_col}"
                            )
                            
                            if selected_col != "(選択してください)":
                                # カラム名の変更を手動修正リストに追加
                                if 'column_mapping' not in st.session_state[f"{self.key}_manual_fixes"]:
                                    st.session_state[f"{self.key}_manual_fixes"]['column_mapping'] = {}
                                
                                st.session_state[f"{self.key}_manual_fixes"]['column_mapping'][missing_col] = selected_col
                
                elif "Value Range Check" in issue['rule_name']:
                    column = details.get('column', '')
                    min_value = details.get('min_value', None)
                    max_value = details.get('max_value', None)
                    out_of_range_count = details.get('out_of_range_count', 0)
                    
                    st.write(f"カラム '{column}' の {out_of_range_count} 件の値が範囲外です。")
                    
                    # 修正オプション
                    fix_option = st.radio(
                        "修正方法を選択:",
                        ["範囲外の値を削除", "範囲外の値をクリップ（範囲内に収める）", "特定の値で置換", "修正しない"],
                        key=f"{self.key}_fix_option_{issue_key}"
                    )
                    
                    if fix_option != "修正しない":
                        # 選択内容を手動修正リストに追加
                        if 'value_range_fixes' not in st.session_state[f"{self.key}_manual_fixes"]:
                            st.session_state[f"{self.key}_manual_fixes"]['value_range_fixes'] = []
                        
                        fix_info = {
                            'column': column,
                            'method': fix_option,
                            'min_value': min_value,
                            'max_value': max_value
                        }
                        
                        if fix_option == "特定の値で置換":
                            replacement_value = st.number_input(
                                "置換する値:", 
                                value=0.0,
                                key=f"{self.key}_replacement_{issue_key}"
                            )
                            fix_info['replacement_value'] = replacement_value
                        
                        # 既存の修正があれば更新、なければ追加
                        existing_fix = next((fix for fix in st.session_state[f"{self.key}_manual_fixes"]['value_range_fixes'] 
                                            if fix['column'] == column), None)
                        
                        if existing_fix:
                            existing_fix.update(fix_info)
                        else:
                            st.session_state[f"{self.key}_manual_fixes"]['value_range_fixes'].append(fix_info)
                
                elif "No Null Values Check" in issue['rule_name']:
                    null_counts = details.get('null_counts', {})
                    
                    for col, count in null_counts.items():
                        if count > 0:
                            st.write(f"カラム '{col}' に {count} 件の欠損値があります。")
                            
                            # 修正オプション
                            fix_option = st.radio(
                                f"'{col}' の欠損値修正方法:",
                                ["欠損値を削除", "線形補間", "前方補間", "後方補間", "定数値で置換", "修正しない"],
                                key=f"{self.key}_null_fix_{issue_key}_{col}"
                            )
                            
                            if fix_option != "修正しない":
                                # 選択内容を手動修正リストに追加
                                if 'null_value_fixes' not in st.session_state[f"{self.key}_manual_fixes"]:
                                    st.session_state[f"{self.key}_manual_fixes"]['null_value_fixes'] = []
                                
                                fix_info = {
                                    'column': col,
                                    'method': fix_option,
                                    'count': count
                                }
                                
                                if fix_option == "定数値で置換":
                                    # カラムのデータ型に応じたデフォルト値を設定
                                    if col in container.data.columns:
                                        dtype = container.data[col].dtype
                                        if pd.api.types.is_numeric_dtype(dtype):
                                            default_value = 0.0
                                            is_numeric = True
                                        else:
                                            default_value = ""
                                            is_numeric = False
                                    else:
                                        default_value = 0.0
                                        is_numeric = True
                                    
                                    if is_numeric:
                                        replacement_value = st.number_input(
                                            "置換する値:", 
                                            value=default_value,
                                            key=f"{self.key}_null_replacement_{issue_key}_{col}"
                                        )
                                    else:
                                        replacement_value = st.text_input(
                                            "置換する値:", 
                                            value=default_value,
                                            key=f"{self.key}_null_replacement_{issue_key}_{col}"
                                        )
                                    
                                    fix_info['replacement_value'] = replacement_value
                                
                                # 既存の修正があれば更新、なければ追加
                                existing_fix = next((fix for fix in st.session_state[f"{self.key}_manual_fixes"].get('null_value_fixes', []) 
                                                    if fix['column'] == col), None)
                                
                                if existing_fix:
                                    existing_fix.update(fix_info)
                                else:
                                    st.session_state[f"{self.key}_manual_fixes"]['null_value_fixes'].append(fix_info)
                
                elif "No Duplicate Timestamps" in issue['rule_name']:
                    duplicate_count = details.get('duplicate_count', 0)
                    
                    st.write(f"{duplicate_count} 件のタイムスタンプが重複しています。")
                    
                    # 修正オプション
                    fix_option = st.radio(
                        "重複タイムスタンプの修正方法:",
                        ["重複を少しずつずらす", "重複を削除（先頭のみ保持）", "修正しない"],
                        key=f"{self.key}_duplicate_fix_{issue_key}"
                    )
                    
                    if fix_option != "修正しない":
                        # 選択内容を手動修正リストに追加
                        if 'duplicate_timestamp_fixes' not in st.session_state[f"{self.key}_manual_fixes"]:
                            st.session_state[f"{self.key}_manual_fixes"]['duplicate_timestamp_fixes'] = []
                        
                        fix_info = {
                            'method': fix_option,
                            'count': duplicate_count
                        }
                        
                        # 既存の修正があれば更新、なければ追加
                        if not st.session_state[f"{self.key}_manual_fixes"]['duplicate_timestamp_fixes']:
                            st.session_state[f"{self.key}_manual_fixes"]['duplicate_timestamp_fixes'].append(fix_info)
                        else:
                            st.session_state[f"{self.key}_manual_fixes"]['duplicate_timestamp_fixes'][0] = fix_info
                
                elif "Spatial Consistency Check" in issue['rule_name']:
                    anomaly_count = details.get('anomaly_count', 0)
                    max_speed = details.get('max_calculated_speed', 0)
                    
                    st.write(f"{anomaly_count} 件のポイントが空間的整合性チェックに失敗しました。最大速度: {max_speed:.2f} ノット")
                    
                    # 修正オプション
                    fix_option = st.radio(
                        "空間的整合性の問題の修正方法:",
                        ["異常ポイントを削除", "異常ポイントを補間", "修正しない"],
                        key=f"{self.key}_spatial_fix_{issue_key}"
                    )
                    
                    if fix_option != "修正しない":
                        # 選択内容を手動修正リストに追加
                        if 'spatial_consistency_fixes' not in st.session_state[f"{self.key}_manual_fixes"]:
                            st.session_state[f"{self.key}_manual_fixes"]['spatial_consistency_fixes'] = []
                        
                        fix_info = {
                            'method': fix_option,
                            'count': anomaly_count
                        }
                        
                        # 既存の修正があれば更新、なければ追加
                        if not st.session_state[f"{self.key}_manual_fixes"]['spatial_consistency_fixes']:
                            st.session_state[f"{self.key}_manual_fixes"]['spatial_consistency_fixes'].append(fix_info)
                        else:
                            st.session_state[f"{self.key}_manual_fixes"]['spatial_consistency_fixes'][0] = fix_info
                
                elif "Temporal Consistency Check" in issue['rule_name']:
                    gap_count = details.get('gap_count', 0)
                    reverse_count = details.get('reverse_count', 0)
                    
                    if gap_count > 0:
                        st.write(f"{gap_count} 件の時間ギャップが検出されました。")
                        
                        # ギャップ修正オプション
                        gap_fix_option = st.radio(
                            "時間ギャップの修正方法:",
                            ["無視する", "ギャップにデータを補間"],
                            key=f"{self.key}_gap_fix_{issue_key}"
                        )
                        
                        if gap_fix_option != "無視する":
                            # 選択内容を手動修正リストに追加
                            if 'temporal_gap_fixes' not in st.session_state[f"{self.key}_manual_fixes"]:
                                st.session_state[f"{self.key}_manual_fixes"]['temporal_gap_fixes'] = []
                            
                            fix_info = {
                                'method': gap_fix_option,
                                'count': gap_count
                            }
                            
                            # 既存の修正があれば更新、なければ追加
                            if not st.session_state[f"{self.key}_manual_fixes"]['temporal_gap_fixes']:
                                st.session_state[f"{self.key}_manual_fixes"]['temporal_gap_fixes'].append(fix_info)
                            else:
                                st.session_state[f"{self.key}_manual_fixes"]['temporal_gap_fixes'][0] = fix_info
                    
                    if reverse_count > 0:
                        st.write(f"{reverse_count} 件の時間的逆行が検出されました。")
                        
                        # 逆行修正オプション
                        reverse_fix_option = st.radio(
                            "時間的逆行の修正方法:",
                            ["逆行ポイントを削除", "タイムスタンプを調整", "修正しない"],
                            key=f"{self.key}_reverse_fix_{issue_key}"
                        )
                        
                        if reverse_fix_option != "修正しない":
                            # 選択内容を手動修正リストに追加
                            if 'temporal_reverse_fixes' not in st.session_state[f"{self.key}_manual_fixes"]:
                                st.session_state[f"{self.key}_manual_fixes"]['temporal_reverse_fixes'] = []
                            
                            fix_info = {
                                'method': reverse_fix_option,
                                'count': reverse_count
                            }
                            
                            # 既存の修正があれば更新、なければ追加
                            if not st.session_state[f"{self.key}_manual_fixes"]['temporal_reverse_fixes']:
                                st.session_state[f"{self.key}_manual_fixes"]['temporal_reverse_fixes'].append(fix_info)
                            else:
                                st.session_state[f"{self.key}_manual_fixes"]['temporal_reverse_fixes'][0] = fix_info
                
                else:
                    st.info(f"この問題タイプ ({issue['rule_name']}) の手動修正オプションは現在サポートされていません。")
                
                # このセクションを表示するかどうかをセッションに保存
                st.session_state[f"{self.key}_show_fixes"][issue_key] = True
        
        # 修正実行ボタン
        if st.session_state[f"{self.key}_manual_fixes"]:
            col1, col2 = st.columns([3, 1])
            with col1:
                fix_button = st.button("選択した修正を適用", key=f"{self.key}_manual_fix_button")
            
            with col2:
                # 修正内容のリセット
                if st.button("修正選択をリセット", key=f"{self.key}_reset_fixes_button"):
                    st.session_state[f"{self.key}_manual_fixes"] = {}
                    st.experimental_rerun()
            
            if fix_button:
                # 選択された修正の適用
                fixed_container = self._apply_manual_fixes(container)
                
                # 修正後のコンテナを保存
                st.session_state[f"{self.key}_fixed_container"] = fixed_container
                
                # 検証を再実行して結果を確認
                validator = DataValidator()
                is_valid, results = validator.validate(fixed_container)
                
                if self._has_remaining_issues(fixed_container):
                    st.experimental_rerun()  # 同じステップを再表示（修正後の状態で）
                else:
                    # 問題がなければ次のステップへ
                    self._go_to_step4()
                    st.experimental_rerun()
        
        # ナビゲーションボタン
        st.button("次へ: 確認", key=f"{self.key}_step3_next", on_click=self._go_to_step4)
        st.button("戻る: 自動修正", key=f"{self.key}_step3_back", on_click=self._go_to_step2)
    
    def _render_step4_preview_and_save(self):
        """ステップ4: プレビューと保存"""
        st.header("ステップ4: クリーニング結果の確認")
        
        # 修正後のコンテナを取得
        fixed_container = st.session_state.get(f"{self.key}_fixed_container")
        if fixed_container is None:
            st.error("修正データが見つかりません。")
            st.button("戻る: 手動修正", key=f"{self.key}_step4_back", on_click=self._go_to_step3)
            return
        
        # 元のコンテナを取得（比較用）
        original_container = st.session_state.get(f"{self.key}_container")
        
        # クリーニング結果のサマリー表示
        st.write("### クリーニング結果サマリー")
        
        if original_container:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("元のデータポイント数", len(original_container.data))
            
            with col2:
                st.metric("クリーニング後のデータポイント数", len(fixed_container.data))
            
            with col3:
                difference = len(original_container.data) - len(fixed_container.data)
                if difference != 0:
                    st.metric("処理されたデータポイント数", difference, delta=f"{-difference}")
                else:
                    st.metric("処理されたデータポイント数", difference)
        
        # 修正適用の詳細
        fixes = st.session_state.get(f"{self.key}_fixes", [])
        manual_fixes = st.session_state.get(f"{self.key}_manual_fixes", {})
        
        if fixes or manual_fixes:
            st.write("### 適用された修正")
            
            # 自動修正の表示
            if fixes:
                with st.expander("自動修正", expanded=True):
                    for fix in fixes:
                        st.write(f"- {fix.get('description', '詳細情報なし')}")
            
            # 手動修正の表示
            if manual_fixes:
                with st.expander("手動修正", expanded=True):
                    for fix_type, fix_list in manual_fixes.items():
                        if fix_type == 'column_mapping':
                            st.write("**カラム名の変更:**")
                            for target, source in fix_list.items():
                                st.write(f"- '{source}' を '{target}' にマッピング")
                        elif fix_type == 'value_range_fixes':
                            st.write("**値範囲の修正:**")
                            for fix in fix_list:
                                st.write(f"- カラム '{fix['column']}' の範囲外値を {fix['method']} で修正")
                        elif fix_type == 'null_value_fixes':
                            st.write("**欠損値の修正:**")
                            for fix in fix_list:
                                st.write(f"- カラム '{fix['column']}' の {fix['count']} 件の欠損値を {fix['method']} で修正")
                        elif fix_type == 'duplicate_timestamp_fixes':
                            st.write("**重複タイムスタンプの修正:**")
                            for fix in fix_list:
                                st.write(f"- {fix['count']} 件の重複タイムスタンプを {fix['method']} で修正")
                        elif fix_type == 'spatial_consistency_fixes':
                            st.write("**空間的整合性の修正:**")
                            for fix in fix_list:
                                st.write(f"- {fix['count']} 件の異常ポイントを {fix['method']} で修正")
                        elif fix_type == 'temporal_gap_fixes':
                            st.write("**時間ギャップの修正:**")
                            for fix in fix_list:
                                st.write(f"- {fix['count']} 件の時間ギャップを {fix['method']} で修正")
                        elif fix_type == 'temporal_reverse_fixes':
                            st.write("**時間的逆行の修正:**")
                            for fix in fix_list:
                                st.write(f"- {fix['count']} 件の時間的逆行を {fix['method']} で修正")
                        else:
                            st.write(f"**{fix_type}:** {fix_list}")
        
        # クリーニング後のデータプレビュー
        st.write("### クリーニング後のデータプレビュー")
        st.dataframe(fixed_container.data.head(10))
        
        # データの可視化
        st.write("### クリーニング後のデータ可視化")
        
        if len(fixed_container.data) > 0:
            # タブで分けて表示
            tab1, tab2 = st.tabs(["マップ", "時系列"])
            
            with tab1:
                # マップ表示
                st.subheader("位置データマップ")
                map_data = fixed_container.data[["latitude", "longitude"]].copy()
                st.map(map_data)
            
            with tab2:
                # 時系列グラフ
                st.subheader("タイムスタンプの分布")
                
                # Matplotlib を使った可視化
                fig, ax = plt.subplots(figsize=(10, 4))
                
                # タイムスタンプの時間差を計算
                df = fixed_container.data.copy()
                df = df.sort_values('timestamp')
                df['time_diff'] = df['timestamp'].diff().dt.total_seconds()
                
                # 時間差のヒストグラム
                ax.hist(df['time_diff'].dropna(), bins=30, alpha=0.7)
                ax.set_xlabel('Time Difference (seconds)')
                ax.set_ylabel('Count')
                ax.set_title('Distribution of Time Intervals Between Consecutive Points')
                
                # 対数スケールのチェックボックス
                use_log_scale = st.checkbox("対数スケールを使用", value=False, key=f"{self.key}_log_scale")
                if use_log_scale:
                    ax.set_yscale('log')
                
                st.pyplot(fig)
                
                # 速度の時系列グラフ（ある場合）
                if 'speed' in df.columns:
                    st.subheader("速度の時系列")
                    fig2, ax2 = plt.subplots(figsize=(10, 4))
                    ax2.plot(df['timestamp'], df['speed'])
                    ax2.set_xlabel('Timestamp')
                    ax2.set_ylabel('Speed')
                    ax2.set_title('Speed Over Time')
                    plt.xticks(rotation=45)
                    st.pyplot(fig2)
        
        # 最終検証結果
        validator = DataValidator()
        is_valid, results = validator.validate(fixed_container)
        
        st.write("### 最終検証結果")
        
        if is_valid:
            st.success("データはすべての検証に合格しました。")
        else:
            warnings = [r for r in results if not r["is_valid"] and r["severity"] != 'error']
            errors = [r for r in results if not r["is_valid"] and r["severity"] == 'error']
            
            if errors:
                st.error(f"{len(errors)}件のエラーが残っています。")
                for error in errors:
                    st.write(f"- {error['rule_name']}: {error['description']}")
            
            if warnings:
                st.warning(f"{len(warnings)}件の警告が残っています。")
                for warning in warnings:
                    st.write(f"- {warning['rule_name']}: {warning['description']}")
        
        # クリーニング完了ボタン
        if st.button("クリーニングを完了", key=f"{self.key}_step4_complete"):
            # 修正コンテナをコールバックに渡す
            if self.on_clean_complete:
                self.on_clean_complete(fixed_container)
            
            # 完了メッセージ
            st.success("データクリーニングが完了しました！")
        
        # ナビゲーションボタン
        if self._has_remaining_issues(fixed_container):
            st.button("戻る: 手動修正", key=f"{self.key}_step4_back", on_click=self._go_to_step3)
        else:
            st.button("戻る: 自動修正", key=f"{self.key}_step4_back2", on_click=self._go_to_step2)
    
    def _has_remaining_issues(self, container: GPSDataContainer) -> bool:
        """
        コンテナに未解決の問題があるかチェック
        
        Parameters
        ----------
        container : GPSDataContainer
            チェック対象のGPSデータコンテナ
            
        Returns
        -------
        bool
            未解決の問題がある場合True
        """
        validator = DataValidator()
        is_valid, results = validator.validate(container)
        
        # エラーのある問題を取得
        errors = [r for r in results if not r["is_valid"] and r["severity"] == 'error']
        
        return not is_valid or len(errors) > 0
    
    def _apply_manual_fixes(self, container: GPSDataContainer) -> GPSDataContainer:
        """
        手動修正を適用
        
        Parameters
        ----------
        container : GPSDataContainer
            修正対象のGPSデータコンテナ
            
        Returns
        -------
        GPSDataContainer
            修正後のGPSデータコンテナ
        """
        # データを複製して修正
        data = container.data.copy()
        metadata = container.metadata.copy()
        fixes_applied = []
        
        # 手動修正リストを取得
        manual_fixes = st.session_state.get(f"{self.key}_manual_fixes", {})
        
        # カラム名の変更
        if 'column_mapping' in manual_fixes:
            column_mapping = manual_fixes['column_mapping']
            for target, source in column_mapping.items():
                if source in data.columns:
                    data[target] = data[source]
                    fixes_applied.append({
                        'type': 'column_mapping',
                        'source': source,
                        'target': target,
                        'description': f"カラム '{source}' を '{target}' としてマッピングしました"
                    })
        
        # 値範囲の修正
        if 'value_range_fixes' in manual_fixes:
            for fix in manual_fixes['value_range_fixes']:
                column = fix.get('column')
                method = fix.get('method')
                min_value = fix.get('min_value')
                max_value = fix.get('max_value')
                
                if column not in data.columns:
                    continue
                
                # 範囲外の値を特定
                mask = pd.Series(False, index=data.index)
                if min_value is not None:
                    mask = mask | (data[column] < min_value)
                if max_value is not None:
                    mask = mask | (data[column] > max_value)
                
                out_of_range_count = mask.sum()
                
                if method == "範囲外の値を削除":
                    # 範囲外の値を持つ行を削除
                    data = data[~mask]
                    fixes_applied.append({
                        'type': 'value_range_fix',
                        'column': column,
                        'method': 'delete',
                        'count': out_of_range_count,
                        'description': f"カラム '{column}' の範囲外値 {out_of_range_count} 件を持つ行を削除しました"
                    })
                
                elif method == "範囲外の値をクリップ（範囲内に収める）":
                    # 範囲外の値をクリップ
                    if min_value is not None:
                        data.loc[data[column] < min_value, column] = min_value
                    if max_value is not None:
                        data.loc[data[column] > max_value, column] = max_value
                    
                    fixes_applied.append({
                        'type': 'value_range_fix',
                        'column': column,
                        'method': 'clip',
                        'min_value': min_value,
                        'max_value': max_value,
                        'count': out_of_range_count,
                        'description': f"カラム '{column}' の範囲外値 {out_of_range_count} 件をクリップしました"
                    })
                
                elif method == "特定の値で置換":
                    # 範囲外の値を置換
                    replacement_value = fix.get('replacement_value', 0)
                    data.loc[mask, column] = replacement_value
                    
                    fixes_applied.append({
                        'type': 'value_range_fix',
                        'column': column,
                        'method': 'replace',
                        'replacement_value': replacement_value,
                        'count': out_of_range_count,
                        'description': f"カラム '{column}' の範囲外値 {out_of_range_count} 件を {replacement_value} に置換しました"
                    })
        
        # 欠損値の修正
        if 'null_value_fixes' in manual_fixes:
            for fix in manual_fixes['null_value_fixes']:
                column = fix.get('column')
                method = fix.get('method')
                count = fix.get('count', 0)
                
                if column not in data.columns:
                    continue
                
                if method == "欠損値を削除":
                    # 欠損値を持つ行を削除
                    null_mask = data[column].isnull()
                    data = data[~null_mask]
                    
                    fixes_applied.append({
                        'type': 'null_value_fix',
                        'column': column,
                        'method': 'delete',
                        'count': count,
                        'description': f"カラム '{column}' の欠損値 {count} 件を持つ行を削除しました"
                    })
                
                elif method == "線形補間":
                    # 線形補間
                    data[column] = data[column].interpolate(method='linear')
                    
                    fixes_applied.append({
                        'type': 'null_value_fix',
                        'column': column,
                        'method': 'linear_interpolation',
                        'count': count,
                        'description': f"カラム '{column}' の欠損値 {count} 件を線形補間で修正しました"
                    })
                
                elif method == "前方補間":
                    # 前方向補間 (forward fill)
                    data[column] = data[column].fillna(method='ffill')
                    
                    fixes_applied.append({
                        'type': 'null_value_fix',
                        'column': column,
                        'method': 'forward_fill',
                        'count': count,
                        'description': f"カラム '{column}' の欠損値 {count} 件を前方向補間で修正しました"
                    })
                
                elif method == "後方補間":
                    # 後方向補間 (backward fill)
                    data[column] = data[column].fillna(method='bfill')
                    
                    fixes_applied.append({
                        'type': 'null_value_fix',
                        'column': column,
                        'method': 'backward_fill',
                        'count': count,
                        'description': f"カラム '{column}' の欠損値 {count} 件を後方向補間で修正しました"
                    })
                
                elif method == "定数値で置換":
                    # 定数値で置換
                    replacement_value = fix.get('replacement_value', 0)
                    data[column] = data[column].fillna(replacement_value)
                    
                    fixes_applied.append({
                        'type': 'null_value_fix',
                        'column': column,
                        'method': 'constant_fill',
                        'replacement_value': replacement_value,
                        'count': count,
                        'description': f"カラム '{column}' の欠損値 {count} 件を {replacement_value} に置換しました"
                    })
        
        # 重複タイムスタンプの修正
        if 'duplicate_timestamp_fixes' in manual_fixes and manual_fixes['duplicate_timestamp_fixes']:
            fix = manual_fixes['duplicate_timestamp_fixes'][0]
            method = fix.get('method')
            count = fix.get('count', 0)
            
            if method == "重複を少しずつずらす":
                # 重複タイムスタンプをずらす
                timestamp_col = 'timestamp'
                dups = data.duplicated(subset=[timestamp_col], keep=False)
                dup_timestamps = data.loc[dups, timestamp_col].unique()
                
                for ts in dup_timestamps:
                    duplicates = data[data[timestamp_col] == ts].index
                    
                    if len(duplicates) <= 1:
                        continue
                    
                    # 最初の行は保持し、残りは1ミリ秒ずつずらす
                    for i, idx in enumerate(duplicates[1:], 1):
                        data.loc[idx, timestamp_col] = ts + pd.Timedelta(milliseconds=i)
                
                fixes_applied.append({
                    'type': 'duplicate_timestamp_fix',
                    'method': 'adjust',
                    'count': count,
                    'description': f"{count} 件の重複タイムスタンプを少しずつずらしました"
                })
            
            elif method == "重複を削除（先頭のみ保持）":
                # 重複を削除
                data = data.drop_duplicates(subset=['timestamp'], keep='first')
                
                fixes_applied.append({
                    'type': 'duplicate_timestamp_fix',
                    'method': 'delete',
                    'count': count,
                    'description': f"{count} 件の重複タイムスタンプがある行を削除しました（先頭のみ保持）"
                })
        
        # 空間的整合性の修正
        if 'spatial_consistency_fixes' in manual_fixes and manual_fixes['spatial_consistency_fixes']:
            fix = manual_fixes['spatial_consistency_fixes'][0]
            method = fix.get('method')
            count = fix.get('count', 0)
            
            if method == "異常ポイントを削除":
                # 異常な速度を持つポイントを検出して削除
                validator = DataValidator()
                rule = next((r for r in validator.rules if "Spatial Consistency Check" in r.name), None)
                
                if rule:
                    is_valid, details = rule.validate(data)
                    
                    if not is_valid:
                        anomaly_indices = details.get('anomaly_indices', [])
                        
                        if anomaly_indices:
                            # インデックスをソートして元のデータから異常ポイントを削除
                            sorted_indices = sorted(anomaly_indices, reverse=True)
                            for idx in sorted_indices:
                                if idx < len(data):
                                    data = data.drop(data.index[idx])
                            
                            fixes_applied.append({
                                'type': 'spatial_anomaly_fix',
                                'method': 'delete',
                                'count': len(anomaly_indices),
                                'description': f"{len(anomaly_indices)} 件の空間的整合性のないポイントを削除しました"
                            })
            
            elif method == "異常ポイントを補間":
                # 異常な速度を持つポイントを検出して補間
                validator = DataValidator()
                rule = next((r for r in validator.rules if "Spatial Consistency Check" in r.name), None)
                
                if rule:
                    is_valid, details = rule.validate(data)
                    
                    if not is_valid:
                        anomaly_indices = details.get('anomaly_indices', [])
                        
                        if anomaly_indices:
                            # 異常ポイントの位置を補間
                            for idx in anomaly_indices:
                                if 0 < idx < len(data) - 1:
                                    # 前後のポイントから線形補間
                                    prev_idx = idx - 1
                                    next_idx = idx + 1
                                    
                                    # 緯度・経度の補間
                                    for col in ['latitude', 'longitude']:
                                        prev_val = data.iloc[prev_idx][col]
                                        next_val = data.iloc[next_idx][col]
                                        data.iloc[idx, data.columns.get_loc(col)] = (prev_val + next_val) / 2
                            
                            fixes_applied.append({
                                'type': 'spatial_anomaly_fix',
                                'method': 'interpolate',
                                'count': len(anomaly_indices),
                                'description': f"{len(anomaly_indices)} 件の空間的整合性のないポイントを補間しました"
                            })
        
        # 時間的整合性の修正（時間ギャップ）
        if 'temporal_gap_fixes' in manual_fixes and manual_fixes['temporal_gap_fixes']:
            fix = manual_fixes['temporal_gap_fixes'][0]
            method = fix.get('method')
            count = fix.get('count', 0)
            
            if method == "ギャップにデータを補間":
                # 時間ギャップを持つポイントを検出して補間
                validator = DataValidator()
                rule = next((r for r in validator.rules if "Temporal Consistency Check" in r.name), None)
                
                if rule:
                    is_valid, details = rule.validate(data)
                    
                    if not is_valid:
                        gap_details = details.get('gap_details', [])
                        
                        if gap_details:
                            # データをソート
                            data = data.sort_values('timestamp').reset_index(drop=True)
                            new_rows = []
                            
                            for gap in gap_details:
                                prev_idx = gap['index'] - 1
                                curr_idx = gap['index']
                                
                                if prev_idx >= 0 and curr_idx < len(data):
                                    prev_time = data.iloc[prev_idx]['timestamp']
                                    curr_time = data.iloc[curr_idx]['timestamp']
                                    
                                    # ギャップ時間
                                    gap_seconds = (curr_time - prev_time).total_seconds()
                                    
                                    # 5秒より長いギャップには補間ポイントを追加
                                    if gap_seconds > 5:
                                        # 補間ポイント数の計算（5秒ごとに1ポイント）
                                        num_points = max(1, int(gap_seconds / 5) - 1)
                                        time_interval = gap_seconds / (num_points + 1)
                                        
                                        for i in range(1, num_points + 1):
                                            # 新しい時間ポイント
                                            new_time = prev_time + pd.Timedelta(seconds=time_interval * i)
                                            
                                            # 前後のポイントから位置を線形補間
                                            weight = i / (num_points + 1)
                                            
                                            new_row = {}
                                            for col in data.columns:
                                                if col == 'timestamp':
                                                    new_row[col] = new_time
                                                elif col in ['latitude', 'longitude'] or pd.api.types.is_numeric_dtype(data[col].dtype):
                                                    # 数値カラムは線形補間
                                                    prev_val = data.iloc[prev_idx][col]
                                                    curr_val = data.iloc[curr_idx][col]
                                                    
                                                    if pd.notna(prev_val) and pd.notna(curr_val):
                                                        new_row[col] = prev_val + (curr_val - prev_val) * weight
                                                    else:
                                                        new_row[col] = None
                                                else:
                                                    # 非数値カラムは前方補間
                                                    new_row[col] = data.iloc[prev_idx][col]
                                            
                                            new_rows.append(new_row)
                            
                            # 新しい行を追加
                            if new_rows:
                                data = pd.concat([data, pd.DataFrame(new_rows)], ignore_index=True)
                                data = data.sort_values('timestamp').reset_index(drop=True)
                                
                                fixes_applied.append({
                                    'type': 'temporal_gap_fix',
                                    'method': 'interpolate',
                                    'count': count,
                                    'added_points': len(new_rows),
                                    'description': f"{count} 件の時間ギャップに {len(new_rows)} 個のポイントを補間しました"
                                })
        
        # 時間的整合性の修正（時間的逆行）
        if 'temporal_reverse_fixes' in manual_fixes and manual_fixes['temporal_reverse_fixes']:
            fix = manual_fixes['temporal_reverse_fixes'][0]
            method = fix.get('method')
            count = fix.get('count', 0)
            
            if method == "逆行ポイントを削除":
                # 時間的逆行ポイントを検出して削除
                validator = DataValidator()
                rule = next((r for r in validator.rules if "Temporal Consistency Check" in r.name), None)
                
                if rule:
                    is_valid, details = rule.validate(data)
                    
                    if not is_valid:
                        reverse_indices = details.get('reverse_indices', [])
                        
                        if reverse_indices:
                            # インデックスをソートして元のデータから逆行ポイントを削除
                            sorted_indices = sorted(reverse_indices, reverse=True)
                            for idx in sorted_indices:
                                if idx < len(data):
                                    data = data.drop(data.index[idx])
                            
                            fixes_applied.append({
                                'type': 'temporal_reverse_fix',
                                'method': 'delete',
                                'count': len(reverse_indices),
                                'description': f"{len(reverse_indices)} 件の時間的逆行ポイントを削除しました"
                            })
            
            elif method == "タイムスタンプを調整":
                # 時間的逆行ポイントを検出してタイムスタンプを調整
                validator = DataValidator()
                rule = next((r for r in validator.rules if "Temporal Consistency Check" in r.name), None)
                
                if rule:
                    is_valid, details = rule.validate(data)
                    
                    if not is_valid:
                        reverse_details = details.get('reverse_details', [])
                        
                        if reverse_details:
                            # データをコピー
                            data = data.copy()
                            
                            fixed_count = 0
                            for detail in reverse_details:
                                idx = detail['index']
                                prev_time = detail['prev_timestamp']
                                
                                if idx < len(data):
                                    # 前のタイムスタンプの1秒後に設定
                                    new_time = prev_time + pd.Timedelta(seconds=1)
                                    data.iloc[idx, data.columns.get_loc('timestamp')] = new_time
                                    fixed_count += 1
                            
                            fixes_applied.append({
                                'type': 'temporal_reverse_fix',
                                'method': 'adjust',
                                'count': fixed_count,
                                'description': f"{fixed_count} 件の時間的逆行ポイントのタイムスタンプを調整しました"
                            })
        
        # ソートとインデックスのリセット
        data = data.sort_values('timestamp').reset_index(drop=True)
        
        # 修正後のコンテナを作成
        fixed_container = GPSDataContainer(data, metadata)
        
        # 修正情報をメタデータに追加
        if fixes_applied:
            fixed_container.add_metadata("manual_fixes", fixes_applied)
            fixed_container.add_metadata("fix_timestamp", datetime.now().isoformat())
        
        return fixed_container
    
    def _go_to_step1(self):
        """ステップ1へ移動"""
        st.session_state[f"{self.key}_step"] = 1
    
    def _go_to_step2(self):
        """ステップ2へ移動"""
        st.session_state[f"{self.key}_step"] = 2
    
    def _go_to_step3(self):
        """ステップ3へ移動"""
        st.session_state[f"{self.key}_step"] = 3
    
    def _go_to_step4(self):
        """ステップ4へ移動"""
        st.session_state[f"{self.key}_step"] = 4
    
    def get_cleaned_container(self) -> Optional[GPSDataContainer]:
        """
        クリーニングされたデータコンテナを取得
        
        Returns
        -------
        Optional[GPSDataContainer]
            クリーニングされたデータコンテナ（クリーニングされていない場合はNone）
        """
        return st.session_state.get(f"{self.key}_fixed_container")
