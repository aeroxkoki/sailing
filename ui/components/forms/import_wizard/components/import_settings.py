# -*- coding: utf-8 -*-
"""
ui.components.forms.import_wizard.components.import_settings

インポート設定用のUIコンポーネント
"""

import streamlit as st
from typing import Dict, Any, Optional, List
import json
from pathlib import Path


def import_settings_form(
    file_format: str,
    current_settings: Dict[str, Any] = None,
    key_prefix: str = "import_settings"
) -> Dict[str, Any]:
    """
    インポート設定フォームを表示
    
    Parameters
    ----------
    file_format : str
        ファイル形式（CSV, GPX, TCX, FITなど）
    current_settings : Dict[str, Any], optional
        現在の設定値
    key_prefix : str, optional
        Streamlitのキープレフィックス
        
    Returns
    -------
    Dict[str, Any]
        更新された設定
    """
    settings = current_settings.copy() if current_settings else {}
    
    # ファイル形式に応じて表示する設定項目を変更
    if file_format == "CSV":
        return _csv_settings_form(settings, key_prefix)
    elif file_format == "GPX":
        return _gpx_settings_form(settings, key_prefix)
    elif file_format == "TCX":
        return _tcx_settings_form(settings, key_prefix)
    elif file_format == "FIT":
        return _fit_settings_form(settings, key_prefix)
    else:
        st.info(f"{file_format}形式の詳細設定はありません。")
        return settings


def _csv_settings_form(settings: Dict[str, Any], key_prefix: str) -> Dict[str, Any]:
    """
    CSV用の設定フォーム
    
    Parameters
    ----------
    settings : Dict[str, Any]
        現在の設定
    key_prefix : str
        キープレフィックス
        
    Returns
    -------
    Dict[str, Any]
        更新された設定
    """
    st.write("### CSVインポート設定")
    
    # 保存済み設定プロファイルの読み込み
    setting_profiles = _load_setting_profiles("CSV")
    if setting_profiles:
        st.write("#### 保存された設定")
        col1, col2 = st.columns([3, 1])
        
        with col1:
            selected_profile = st.selectbox(
                "設定プロファイル",
                options=["選択してください"] + list(setting_profiles.keys()),
                key=f"{key_prefix}_csv_profile_select"
            )
        
        with col2:
            if selected_profile != "選択してください":
                if st.button("適用", key=f"{key_prefix}_csv_apply_profile"):
                    settings.update(setting_profiles[selected_profile])
                    st.success(f"設定 '{selected_profile}' を適用しました")
    
    # 基本設定
    with st.expander("基本設定", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            # 区切り文字
            delimiter_options = {
                ",": "カンマ (,)",
                ";": "セミコロン (;)",
                "\\t": "タブ (\\t)",
                "|": "パイプ (|)",
                " ": "スペース ( )"
            }
            
            delimiter = settings.get("delimiter", ",")
            if delimiter not in delimiter_options:
                delimiter_options[delimiter] = f"カスタム ({delimiter})"
            
            delimiter_selection = st.selectbox(
                "区切り文字",
                options=list(delimiter_options.keys()),
                format_func=lambda x: delimiter_options[x],
                index=list(delimiter_options.keys()).index(delimiter),
                key=f"{key_prefix}_csv_delimiter"
            )
            
            if delimiter_selection == "custom":
                custom_delimiter = st.text_input(
                    "カスタム区切り文字",
                    value=delimiter if delimiter not in [",", ";", "\\t", "|", " "] else "",
                    key=f"{key_prefix}_csv_custom_delimiter"
                )
                settings["delimiter"] = custom_delimiter if custom_delimiter else ","
            else:
                settings["delimiter"] = delimiter_selection
        
        with col2:
            # エンコーディング
            encoding_options = [
                "utf-8", "utf-8-sig", "latin1", "cp1252", 
                "shift-jis", "cp932", "euc-jp", "iso-2022-jp"
            ]
            
            encoding = settings.get("encoding", "utf-8")
            encoding_index = encoding_options.index(encoding) if encoding in encoding_options else 0
            
            settings["encoding"] = st.selectbox(
                "エンコーディング",
                options=encoding_options,
                index=encoding_index,
                key=f"{key_prefix}_csv_encoding"
            )
        
        # スキップする行数
        settings["skiprows"] = st.number_input(
            "スキップする行数",
            min_value=0,
            value=settings.get("skiprows", 0),
            help="ヘッダー行以外にスキップする行数（ヘッダーの前にメタデータがある場合など）",
            key=f"{key_prefix}_csv_skiprows"
        )
        
        # 列マッピング自動検出
        settings["auto_mapping"] = st.checkbox(
            "列マッピングを自動検出",
            value=settings.get("auto_mapping", True),
            help="列名から自動的にマッピングを提案します",
            key=f"{key_prefix}_csv_auto_mapping"
        )
    
    # 日付・時刻設定
    with st.expander("日付・時刻設定", expanded=False):
        # 日付形式
        settings["date_format"] = st.text_input(
            "日付形式（空白の場合は自動検出）",
            value=settings.get("date_format", ""),
            help="例: %Y-%m-%d %H:%M:%S（YYYY-MM-DD HH:MM:SS形式）",
            placeholder="%Y-%m-%d %H:%M:%S",
            key=f"{key_prefix}_csv_date_format"
        )
        
        with st.expander("一般的な日付形式例", expanded=False):
            st.markdown("""
            - `%Y-%m-%d %H:%M:%S` - 2023-01-31 14:30:00
            - `%Y/%m/%d %H:%M:%S` - 2023/01/31 14:30:00
            - `%d/%m/%Y %H:%M:%S` - 31/01/2023 14:30:00
            - `%m/%d/%Y %H:%M:%S` - 01/31/2023 14:30:00
            - `%Y-%m-%dT%H:%M:%S` - 2023-01-31T14:30:00（ISO形式）
            - `%Y%m%d%H%M%S` - 20230131143000（区切りなし）
            
            詳細は[Python日付フォーマット](https://docs.python.org/ja/3/library/datetime.html#strftime-and-strptime-format-codes)を参照してください。
            """)
    
    # 設定の保存
    _show_save_settings_form(settings, "CSV", key_prefix)
    
    return settings


def _gpx_settings_form(settings: Dict[str, Any], key_prefix: str) -> Dict[str, Any]:
    """
    GPX用の設定フォーム
    
    Parameters
    ----------
    settings : Dict[str, Any]
        現在の設定
    key_prefix : str
        キープレフィックス
        
    Returns
    -------
    Dict[str, Any]
        更新された設定
    """
    st.write("### GPXインポート設定")
    
    # 保存済み設定プロファイルの読み込み
    setting_profiles = _load_setting_profiles("GPX")
    if setting_profiles:
        st.write("#### 保存された設定")
        col1, col2 = st.columns([3, 1])
        
        with col1:
            selected_profile = st.selectbox(
                "設定プロファイル",
                options=["選択してください"] + list(setting_profiles.keys()),
                key=f"{key_prefix}_gpx_profile_select"
            )
        
        with col2:
            if selected_profile != "選択してください":
                if st.button("適用", key=f"{key_prefix}_gpx_apply_profile"):
                    settings.update(setting_profiles[selected_profile])
                    st.success(f"設定 '{selected_profile}' を適用しました")
    
    # GPX特有の設定
    with st.expander("インポート設定", expanded=True):
        # トラックポイントの優先設定
        settings["prefer_trkpt"] = st.checkbox(
            "トラックポイントを優先（推奨）",
            value=settings.get("prefer_trkpt", True),
            help="トラックポイント（<trkpt>）を優先的に使用します。無効にするとルートポイント（<rtept>）を優先します",
            key=f"{key_prefix}_gpx_prefer_trkpt"
        )
        
        # ウェイポイントのインポート
        settings["include_waypoints"] = st.checkbox(
            "ウェイポイントを含める",
            value=settings.get("include_waypoints", False),
            help="GPXファイル内のウェイポイント（<wpt>）もインポートします",
            key=f"{key_prefix}_gpx_include_waypoints"
        )
        
        # 拡張データを含める
        settings["include_extensions"] = st.checkbox(
            "拡張データを含める",
            value=settings.get("include_extensions", True),
            help="GPXファイル内の拡張データ（心拍数、ケイデンスなど）を含めます",
            key=f"{key_prefix}_gpx_include_extensions"
        )
    
    # 設定の保存
    _show_save_settings_form(settings, "GPX", key_prefix)
    
    return settings


def _tcx_settings_form(settings: Dict[str, Any], key_prefix: str) -> Dict[str, Any]:
    """
    TCX用の設定フォーム
    
    Parameters
    ----------
    settings : Dict[str, Any]
        現在の設定
    key_prefix : str
        キープレフィックス
        
    Returns
    -------
    Dict[str, Any]
        更新された設定
    """
    st.write("### TCXインポート設定")
    
    # 保存済み設定プロファイルの読み込み
    setting_profiles = _load_setting_profiles("TCX")
    if setting_profiles:
        st.write("#### 保存された設定")
        col1, col2 = st.columns([3, 1])
        
        with col1:
            selected_profile = st.selectbox(
                "設定プロファイル",
                options=["選択してください"] + list(setting_profiles.keys()),
                key=f"{key_prefix}_tcx_profile_select"
            )
        
        with col2:
            if selected_profile != "選択してください":
                if st.button("適用", key=f"{key_prefix}_tcx_apply_profile"):
                    settings.update(setting_profiles[selected_profile])
                    st.success(f"設定 '{selected_profile}' を適用しました")
    
    # TCX特有の設定
    with st.expander("インポート設定", expanded=True):
        # 拡張データを含める
        settings["include_extensions"] = st.checkbox(
            "拡張データを含める",
            value=settings.get("include_extensions", True),
            help="TCXファイル内の拡張データ（心拍数、ケイデンスなど）を含めます",
            key=f"{key_prefix}_tcx_include_extensions"
        )
        
        # ラップ情報を含める
        settings["include_laps"] = st.checkbox(
            "ラップ情報を含める",
            value=settings.get("include_laps", True),
            help="トレーニングデータのラップ情報を含めます",
            key=f"{key_prefix}_tcx_include_laps"
        )
    
    # 設定の保存
    _show_save_settings_form(settings, "TCX", key_prefix)
    
    return settings


def _fit_settings_form(settings: Dict[str, Any], key_prefix: str) -> Dict[str, Any]:
    """
    FIT用の設定フォーム
    
    Parameters
    ----------
    settings : Dict[str, Any]
        現在の設定
    key_prefix : str
        キープレフィックス
        
    Returns
    -------
    Dict[str, Any]
        更新された設定
    """
    st.write("### FITインポート設定")
    
    # 保存済み設定プロファイルの読み込み
    setting_profiles = _load_setting_profiles("FIT")
    if setting_profiles:
        st.write("#### 保存された設定")
        col1, col2 = st.columns([3, 1])
        
        with col1:
            selected_profile = st.selectbox(
                "設定プロファイル",
                options=["選択してください"] + list(setting_profiles.keys()),
                key=f"{key_prefix}_fit_profile_select"
            )
        
        with col2:
            if selected_profile != "選択してください":
                if st.button("適用", key=f"{key_prefix}_fit_apply_profile"):
                    settings.update(setting_profiles[selected_profile])
                    st.success(f"設定 '{selected_profile}' を適用しました")
    
    # FIT特有の設定
    with st.expander("インポート設定", expanded=True):
        # 全てのフィールドを含める
        settings["include_all_fields"] = st.checkbox(
            "すべてのフィールドを含める",
            value=settings.get("include_all_fields", False),
            help="FITファイル内の全フィールドをインポートします（大量のデータになる場合があります）",
            key=f"{key_prefix}_fit_include_all_fields"
        )
    
    # 設定の保存
    _show_save_settings_form(settings, "FIT", key_prefix)
    
    return settings


def _show_save_settings_form(settings: Dict[str, Any], format_type: str, key_prefix: str):
    """
    設定を保存するフォームを表示
    
    Parameters
    ----------
    settings : Dict[str, Any]
        保存する設定
    format_type : str
        ファイル形式（CSV, GPX, TCX, FIT）
    key_prefix : str
        キープレフィックス
    """
    st.write("#### 設定の保存")
    col_save1, col_save2 = st.columns([3, 1])
    
    with col_save1:
        profile_name = st.text_input(
            "設定名",
            key=f"{key_prefix}_{format_type.lower()}_profile_name",
            placeholder=f"マイ{format_type}設定"
        )
    
    with col_save2:
        if st.button("保存", key=f"{key_prefix}_{format_type.lower()}_save_settings"):
            if profile_name:
                # 保存処理
                success = _save_setting_profile(profile_name, settings, format_type)
                if success:
                    st.success(f"設定 '{profile_name}' を保存しました")
            else:
                st.warning("設定名を入力してください")


def _load_setting_profiles(format_type: str) -> Dict[str, Dict[str, Any]]:
    """
    保存された設定プロファイルを読み込む
    
    Parameters
    ----------
    format_type : str
        ファイル形式（CSV, GPX, TCX, FIT）
        
    Returns
    -------
    Dict[str, Dict[str, Any]]
        プロファイル名と設定の辞書
    """
    try:
        # 設定ディレクトリのパス
        config_dir = Path.home() / ".sailing_analyzer"
        settings_file = config_dir / f"{format_type.lower()}_settings.json"
        
        # ディレクトリがなければ作成
        config_dir.mkdir(exist_ok=True)
        
        # ファイルが存在しない場合は空の辞書を返す
        if not settings_file.exists():
            return {}
        
        # ファイルから読み込み
        with open(settings_file, "r", encoding="utf-8") as f:
            return json.load(f)
    
    except Exception as e:
        st.warning(f"設定の読み込みに失敗しました: {e}")
        return {}


def _save_setting_profile(profile_name: str, settings: Dict[str, Any], format_type: str) -> bool:
    """
    設定プロファイルを保存
    
    Parameters
    ----------
    profile_name : str
        プロファイル名
    settings : Dict[str, Any]
        保存する設定
    format_type : str
        ファイル形式（CSV, GPX, TCX, FIT）
        
    Returns
    -------
    bool
        保存成功かどうか
    """
    try:
        # 現在のプロファイルを読み込み
        profiles = _load_setting_profiles(format_type)
        
        # 新しいプロファイルを追加
        profiles[profile_name] = settings
        
        # 設定ディレクトリのパス
        config_dir = Path.home() / ".sailing_analyzer"
        settings_file = config_dir / f"{format_type.lower()}_settings.json"
        
        # ディレクトリがなければ作成
        config_dir.mkdir(exist_ok=True)
        
        # ファイルに保存
        with open(settings_file, "w", encoding="utf-8") as f:
            json.dump(profiles, f, ensure_ascii=False, indent=2)
        
        return True
    
    except Exception as e:
        st.warning(f"設定の保存に失敗しました: {e}")
        return False
