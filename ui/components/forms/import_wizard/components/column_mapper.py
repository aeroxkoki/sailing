# -*- coding: utf-8 -*-
"""
ui.components.forms.import_wizard.components.column_mapper

列マッピング用のUIコンポーネント
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple, Set
import json
import os
from pathlib import Path


def column_mapper(
    columns: List[str],
    required_fields: List[str],
    optional_fields: List[Dict[str, str]],
    current_mapping: Dict[str, str] = None,
    sample_data: Optional[pd.DataFrame] = None,
    key_prefix: str = "column_mapper"
) -> Dict[str, str]:
    """
    CSVの列マッピングUIを提供
    
    Parameters
    ----------
    columns : List[str]
        CSVファイルの列名リスト
    required_fields : List[str]
        必須フィールドのリスト
    optional_fields : List[Dict[str, str]]
        オプションフィールドのリスト（各辞書はkeyとlabelを含む）
    current_mapping : Dict[str, str], optional
        現在のマッピング（key: 変換後のフィールド名, value: 元の列名）
    sample_data : Optional[pd.DataFrame], optional
        サンプルデータ（プレビュー表示用）
    key_prefix : str, optional
        Streamlitコンポーネントのキープレフィックス
        
    Returns
    -------
    Dict[str, str]
        更新された列マッピング
    """
    mapping = current_mapping.copy() if current_mapping else {}
    
    st.write("### 列マッピング")
    st.write("CSVファイルの列を必要なフィールドにマッピングしてください。")
    
    with st.expander("列マッピングのヘルプ", expanded=False):
        st.markdown("""
        **列マッピングとは？**
        
        CSVファイルの列名とシステムが必要とするフィールド名が一致しない場合、このマッピングで対応関係を指定します。
        
        例えば、CSVファイルに「GPS_Time」という列がある場合、それを「timestamp」（タイムスタンプ）フィールドとして使うことをここで指定します。
        
        **必須フィールド**は全て指定する必要があります。**オプションフィールド**は、対応する列がある場合のみ指定してください。
        """)
    
    # マッピング設定の保存/読み込み
    mapping_profiles = _load_mapping_profiles()
    if mapping_profiles:
        st.write("#### 保存されたマッピング設定")
        col1, col2 = st.columns([3, 1])
        
        with col1:
            selected_profile = st.selectbox(
                "保存済みのマッピング設定",
                options=["選択してください"] + list(mapping_profiles.keys()),
                key=f"{key_prefix}_profile_select"
            )
        
        with col2:
            if selected_profile != "選択してください":
                if st.button("適用", key=f"{key_prefix}_apply_profile"):
                    # 存在する列のみをマッピングに使用
                    profile_mapping = mapping_profiles[selected_profile]
                    mapping = {k: v for k, v in profile_mapping.items() if v in columns}
                    st.success(f"マッピング設定 '{selected_profile}' を適用しました")
    
    # 必須フィールドのマッピング
    st.write("#### 必須フィールド")
    
    for field in required_fields:
        # 列のオプションを作成（"---"は選択なしを表す）
        options = ["---"] + columns
        
        # 現在のマッピングを検索、なければ最初のオプションを使用
        current_value = mapping.get(field, "---")
        current_index = options.index(current_value) if current_value in options else 0
        
        # フィールド説明（フィールド名によって変更）
        field_label = _get_field_label(field)
        
        # 選択ボックス
        selected = st.selectbox(
            field_label,
            options=options,
            index=current_index,
            key=f"{key_prefix}_{field}"
        )
        
        # 選択内容をマッピングに反映
        if selected != "---":
            mapping[field] = selected
        elif field in mapping:
            # '---'が選択された場合は、マッピングから削除
            del mapping[field]
        
        # サンプルデータがあれば、選択された列のサンプル値を表示
        if sample_data is not None and selected in sample_data.columns:
            sample_values = sample_data[selected].dropna().head(3).tolist()
            sample_str = ", ".join([str(val) for val in sample_values])
            st.caption(f"サンプル値: {sample_str}")
    
    # オプションフィールドのマッピング
    st.write("#### オプションフィールド")
    st.write("データに含まれる場合は選択してください。")
    
    # 2列レイアウト
    col1, col2 = st.columns(2)
    
    for i, field_info in enumerate(optional_fields):
        field = field_info["key"]
        field_label = field_info["label"]
        
        # 列のオプションを作成
        options = ["（なし）"] + columns
        current_value = mapping.get(field, "（なし）")
        current_index = options.index(current_value) if current_value in options else 0
        
        # 2列交互に配置
        with col1 if i % 2 == 0 else col2:
            selected = st.selectbox(
                f"{field_label} ({field})",
                options=options,
                index=current_index,
                key=f"{key_prefix}_opt_{field}"
            )
            
            # 選択内容をマッピングに反映
            if selected != "（なし）":
                mapping[field] = selected
            elif field in mapping:
                del mapping[field]
            
            # サンプルデータがあれば、選択された列のサンプル値を表示
            if sample_data is not None and selected in sample_data.columns:
                sample_values = sample_data[selected].dropna().head(2).tolist()
                sample_str = ", ".join([str(val) for val in sample_values])
                st.caption(f"サンプル値: {sample_str}")
    
    # マッピング設定の保存
    st.write("#### マッピング設定の保存")
    col_save1, col_save2 = st.columns([3, 1])
    
    with col_save1:
        new_profile_name = st.text_input(
            "マッピング設定名",
            key=f"{key_prefix}_new_profile_name",
            placeholder="設定名を入力（例：MyGPSデバイス）"
        )
    
    with col_save2:
        if st.button("保存", key=f"{key_prefix}_save_profile"):
            if new_profile_name:
                # 保存処理
                _save_mapping_profile(new_profile_name, mapping)
                st.success(f"マッピング設定 '{new_profile_name}' を保存しました")
            else:
                st.warning("設定名を入力してください")
    
    # マッピングのプレビュー
    if mapping and sample_data is not None:
        st.write("#### マッピングプレビュー")
        preview_df = pd.DataFrame()
        
        # マッピングされた列だけを表示
        for target, source in mapping.items():
            if source in sample_data.columns:
                preview_df[target] = sample_data[source]
        
        if not preview_df.empty:
            st.dataframe(preview_df.head())
        else:
            st.info("プレビューデータがありません")
    
    return mapping


def _get_field_label(field_name: str) -> str:
    """
    フィールド名から表示用ラベルを取得
    
    Parameters
    ----------
    field_name : str
        フィールド名
        
    Returns
    -------
    str
        表示用ラベル
    """
    labels = {
        "timestamp": "タイムスタンプ (timestamp)",
        "latitude": "緯度 (latitude)",
        "longitude": "経度 (longitude)",
        "speed": "速度 (speed)",
        "course": "方位 (course)",
        "elevation": "高度 (elevation)",
        "heart_rate": "心拍数 (heart_rate)",
        "cadence": "ケイデンス (cadence)",
        "power": "パワー (power)",
        "distance": "距離 (distance)",
        "temperature": "温度 (temperature)",
        "wind_speed": "風速 (wind_speed)",
        "wind_direction": "風向 (wind_direction)"
    }
    
    return labels.get(field_name, field_name)


def _load_mapping_profiles() -> Dict[str, Dict[str, str]]:
    """
    保存されたマッピングプロファイルを読み込む
    
    Returns
    -------
    Dict[str, Dict[str, str]]
        プロファイル名とマッピングの辞書
    """
    try:
        # 設定ディレクトリのパス
        config_dir = Path.home() / ".sailing_analyzer"
        mapping_file = config_dir / "column_mappings.json"
        
        # ディレクトリがなければ作成
        config_dir.mkdir(exist_ok=True)
        
        # ファイルが存在しない場合は空の辞書を返す
        if not mapping_file.exists():
            return {}
        
        # ファイルから読み込み
        with open(mapping_file, "r", encoding="utf-8") as f:
            return json.load(f)
    
    except Exception as e:
        st.warning(f"マッピング設定の読み込みに失敗しました: {e}")
        return {}


def _save_mapping_profile(profile_name: str, mapping: Dict[str, str]) -> bool:
    """
    マッピングプロファイルを保存
    
    Parameters
    ----------
    profile_name : str
        プロファイル名
    mapping : Dict[str, str]
        保存するマッピング
        
    Returns
    -------
    bool
        保存成功かどうか
    """
    try:
        # 現在のプロファイルを読み込み
        profiles = _load_mapping_profiles()
        
        # 新しいプロファイルを追加
        profiles[profile_name] = mapping
        
        # 設定ディレクトリのパス
        config_dir = Path.home() / ".sailing_analyzer"
        mapping_file = config_dir / "column_mappings.json"
        
        # ディレクトリがなければ作成
        config_dir.mkdir(exist_ok=True)
        
        # ファイルに保存
        with open(mapping_file, "w", encoding="utf-8") as f:
            json.dump(profiles, f, ensure_ascii=False, indent=2)
        
        return True
    
    except Exception as e:
        st.warning(f"マッピング設定の保存に失敗しました: {e}")
        return False
