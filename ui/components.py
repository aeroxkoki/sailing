# -*- coding: utf-8 -*-
"""
セーリング戦略分析システム - UIコンポーネントライブラリ

再利用可能なUIコンポーネントを提供するモジュール
フェーズ2のUI/UX改善に合わせて拡張されたコンポーネント
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import folium
import numpy as np
import json
import os
from datetime import datetime, timedelta
import base64
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from io import BytesIO, StringIO

# グローバルCSS定義
def load_css():
    """共通CSSスタイルをロードする"""
    st.markdown("""
    <style>
    /* カラーパレット */
    :root {
        --main-color: #1565C0;
        --accent-color: #00ACC1;
        --success-color: #26A69A;
        --error-color: #EF5350;
        --warning-color: #FFA726;
        --bg-color: #FAFAFA;
        --card-bg-color: #FFFFFF;
        --text-main: #212121;
        --text-secondary: #757575;
        --text-disabled: #BDBDBD;
        --divider-color: #EEEEEE;
    }
    
    /* タイポグラフィ */
    h1 {
        font-size: 32px !important;
        font-weight: 700 !important;
        color: var(--text-main) !important;
    }
    
    h2 {
        font-size: 24px !important;
        font-weight: 700 !important;
        color: var(--text-main) !important;
    }
    
    h3 {
        font-size: 20px !important;
        font-weight: 600 !important;
        color: var(--text-main) !important;
    }
    
    .subtitle {
        font-size: 16px !important;
        font-weight: 600 !important;
        color: var(--text-secondary) !important;
    }
    
    .body-large {
        font-size: 16px !important;
        font-weight: 400 !important;
    }
    
    .body {
        font-size: 14px !important;
        font-weight: 400 !important;
    }
    
    .body-small {
        font-size: 12px !important;
        font-weight: 400 !important;
    }
    
    .label {
        font-size: 12px !important;
        font-weight: 500 !important;
        color: var(--text-secondary) !important;
    }
    
    /* カードコンポーネント */
    .card {
        background-color: var(--card-bg-color);
        border-radius: 8px;
        padding: 16px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 16px;
    }
    
    /* メトリックカード */
    .metric-card {
        background-color: white;
        border-radius: 8px;
        padding: 16px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: transform 0.2s;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    .metric-title {
        color: var(--text-secondary);
        font-size: 14px;
        margin-bottom: 8px;
    }
    
    .metric-value {
        color: var(--text-main);
        font-size: 24px;
        font-weight: 700;
        margin: 0;
    }
    
    .metric-subtitle {
        color: var(--text-secondary);
        font-size: 12px;
        margin: 2px 0 0 0;
    }
    
    /* アラートメッセージ */
    .alert {
        padding: 12px 16px;
        border-radius: 8px;
        margin-bottom: 16px;
        display: flex;
        align-items: flex-start;
    }
    
    .alert-info {
        background-color: rgba(21, 101, 192, 0.1);
        border-left: 4px solid var(--main-color);
    }
    
    .alert-success {
        background-color: rgba(38, 166, 154, 0.1);
        border-left: 4px solid var(--success-color);
    }
    
    .alert-warning {
        background-color: rgba(255, 167, 38, 0.1);
        border-left: 4px solid var(--warning-color);
    }
    
    .alert-error {
        background-color: rgba(239, 83, 80, 0.1);
        border-left: 4px solid var(--error-color);
    }
    
    /* ナビゲーションメニュー */
    .nav-item {
        padding: 8px 16px;
        display: flex;
        align-items: center;
        border-radius: 4px;
        margin-bottom: 8px;
        cursor: pointer;
        text-decoration: none;
        color: var(--text-main);
    }
    
    .nav-item:hover {
        background-color: rgba(0, 0, 0, 0.05);
    }
    
    .nav-item.active {
        background-color: rgba(21, 101, 192, 0.1);
        color: var(--main-color);
        font-weight: 500;
    }
    
    .nav-item i {
        margin-right: 12px;
    }
    
    /* その他のユーティリティ */
    .text-center {
        text-align: center !important;
    }
    
    .flex-center {
        display: flex;
        justify-content: center;
        align-items: center;
    }
    
    /* モバイル対応 */
    @media (max-width: 640px) {
        .hide-mobile {
            display: none !important;
        }
    }
    
    /* レスポンシブグリッド */
    .grid-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 16px;
        width: 100%;
    }
    
    /* データカードスタイル */
    .data-card {
        background-color: white;
        border-radius: 8px;
        padding: 16px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: all 0.2s ease;
    }
    
    .data-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    
    /* インタラクティブマップコントロール */
    .map-controls {
        background-color: white;
        border-radius: 4px;
        padding: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        position: absolute;
        top: 10px;
        right: 10px;
        z-index: 1000;
    }
    
    /* フィードバックフォーム */
    .feedback-form {
        background-color: var(--bg-color);
        border-radius: 8px;
        padding: 16px;
        border: 1px solid var(--divider-color);
    }
    
    /* ドラッグ&ドロップエリア */
    .dropzone {
        border: 2px dashed var(--divider-color);
        border-radius: 8px;
        padding: 24px;
        text-align: center;
        transition: all 0.2s ease;
        background-color: rgba(0, 0, 0, 0.02);
    }
    
    .dropzone:hover, .dropzone.active {
        border-color: var(--accent-color);
        background-color: rgba(0, 172, 193, 0.05);
    }
    
    /* タイムライン */
    .timeline {
        position: relative;
        padding-left: 24px;
        margin-bottom: 24px;
    }
    
    .timeline::before {
        content: "";
        position: absolute;
        top: 0;
        bottom: 0;
        left: 8px;
        width: 2px;
        background-color: var(--divider-color);
    }
    
    .timeline-item {
        position: relative;
        margin-bottom: 16px;
        padding-bottom: 8px;
    }
    
    .timeline-item::before {
        content: "";
        position: absolute;
        left: -20px;
        top: 4px;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background-color: var(--accent-color);
    }
    </style>
    """, unsafe_allow_html=True)

# ナビゲーションコンポーネント
def create_navigation(logo_path: Optional[str] = None):
    """
    サイドバーナビゲーションを作成
    
    Parameters
    ----------
    logo_path : str, optional
        ロゴ画像のパス
    
    Returns
    -------
    str
        選択されたナビゲーション項目
    """
    with st.sidebar:
        if logo_path:
            st.image(logo_path, width=120)
        
        st.title("セーリング分析")
        
        nav_items = {
            "マップビュー": "map-marker",
            "データ管理": "database",
            "パフォーマンス分析": "chart-line",
            "設定": "cog"
        }
        
        for nav_name, icon in nav_items.items():
            html = f'<div class="nav-item {"active" if "page" in st.session_state and st.session_state.page == nav_name else ""}">'
            html += f'<i class="fas fa-{icon}"></i> {nav_name}</div>'
            if st.markdown(html, unsafe_allow_html=True):
                st.session_state.page = nav_name
                return nav_name
        
        # データサマリー
        st.markdown("---")
        st.markdown("#### 現在のデータセット")
        if 'boats_data' in st.session_state and st.session_state.boats_data:
            st.write(f"{len(st.session_state.boats_data)}艇のデータ読み込み済み")
        else:
            st.write("データがありません")
    
    # デフォルト選択がない場合は最初の項目を返す
    if "page" not in st.session_state:
        st.session_state.page = "マップビュー"
    
    return st.session_state.page

# メトリックカード
def render_metric_card(title: str, value: str, unit: str = "", 
                     subtitle: Optional[str] = None, 
                     icon: Optional[str] = None, 
                     color: Optional[str] = None):
    """
    スタイリングされたメトリックカードを表示
    
    Parameters
    ----------
    title : str
        メトリックのタイトル
    value : str
        表示する値
    unit : str, optional
        単位（例: "ノット", "分"）
    subtitle : str, optional
        サブタイトルまたは補足情報
    icon : str, optional
        Font Awesomeアイコン名（例: "tachometer-alt"）
    color : str, optional
        値の表示色（例: "#1565C0"）
    """
    value_style = f"color: {color};" if color else ""
    
    icon_html = f'<i class="fas fa-{icon}" style="font-size: 24px; color: {color if color else "var(--main-color)"};"></i>' if icon else ""
    
    card_html = f"""
    <div class="metric-card">
        <h3 class="metric-title">{title}</h3>
        <div style="display: flex; align-items: center;">
            {f"<div style='margin-right: 12px;'>{icon_html}</div>" if icon else ""}
            <div>
                <h2 class="metric-value" style="{value_style}">{value} {unit}</h2>
                {f'<p class="metric-subtitle">{subtitle}</p>' if subtitle else ""}
            </div>
        </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

# アラートメッセージ
def alert(message: str, type: str = "info", icon: Optional[str] = None, dismissible: bool = False):
    """
    スタイリングされたアラートメッセージを表示
    
    Parameters
    ----------
    message : str
        アラートメッセージ
    type : str, optional
        アラートタイプ（"info", "success", "warning", "error"）
    icon : str, optional
        Font Awesomeアイコン名（デフォルトはタイプに応じて自動選択）
    dismissible : bool, optional
        閉じるボタンを表示するか
    """
    if icon is None:
        if type == "info":
            icon = "info-circle"
        elif type == "success":
            icon = "check-circle"
        elif type == "warning":
            icon = "exclamation-triangle"
        elif type == "error":
            icon = "exclamation-circle"
    
    alert_html = f"""
    <div class="alert alert-{type}">
        <div style="margin-right: 12px;">
            <i class="fas fa-{icon}"></i>
        </div>
        <div style="flex-grow: 1;">
            {message}
        </div>
        {"<div><i class='fas fa-times'></i></div>" if dismissible else ""}
    </div>
    """
    st.markdown(alert_html, unsafe_allow_html=True)

# アクションボタングループ
def action_button_group(actions: List[Tuple[str, str, Optional[str], str]], key_prefix: str = ""):
    """
    アクションボタングループを表示
    
    Parameters
    ----------
    actions : List[Tuple[str, str, Optional[str], str]]
        アクション定義のリスト
        各タプルは (ラベル, アイコン, 説明, ボタンタイプ) を含む
    key_prefix : str, optional
        ボタンキーのプレフィックス
    
    Returns
    -------
    Dict[str, bool]
        各ボタンのクリック状態を示す辞書
    """
    cols = st.columns(len(actions))
    results = {}
    
    for i, (label, icon, desc, btn_type) in enumerate(actions):
        with cols[i]:
            # アイコンを追加（Font Awesome）
            button_label = f"<i class='fas fa-{icon}'></i> {label}" if icon else label
            
            # ボタンのスタイルに応じたレンダリング
            if btn_type == "primary":
                button_html = f"""
                <button class="button-primary" style="width: 100%;">
                    {button_label}
                </button>
                """
                btn_clicked = st.button(label, type="primary", key=f"{key_prefix}_{i}")
            else:
                btn_clicked = st.button(label, key=f"{key_prefix}_{i}")
            
            if desc:
                st.caption(desc)
            
            results[label] = btn_clicked
    
    return results

# ヘッダーセクション
def section_header(title: str, description: Optional[str] = None, button: Optional[Tuple[str, str]] = None):
    """
    セクションヘッダーを表示
    
    Parameters
    ----------
    title : str
        セクションタイトル
    description : str, optional
        セクションの説明
    button : Tuple[str, str], optional
        (ボタンラベル, ボタンアイコン) のタプル
    
    Returns
    -------
    bool
        ボタンがクリックされたかどうか
    """
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.header(title)
        if description:
            st.markdown(f"<p class='body'>{description}</p>", unsafe_allow_html=True)
    
    button_clicked = False
    if button:
        with col2:
            button_label, button_icon = button
            button_clicked = st.button(f"{button_label} {button_icon}", type="primary")
    
    st.markdown("<hr style='margin-top: 0; margin-bottom: 24px;'>", unsafe_allow_html=True)
    return button_clicked

# データカード
def data_card(title: str, content, footer: Optional[str] = None):
    """
    データを表示するカードコンポーネント
    
    Parameters
    ----------
    title : str
        カードのタイトル
    content : Any
        カードのコンテンツ（文字列、DataFrame、または表示可能なオブジェクト）
    footer : str, optional
        カードのフッター
    """
    with st.container():
        st.markdown(f"<div class='card'><h3>{title}</h3>", unsafe_allow_html=True)
        
        if isinstance(content, pd.DataFrame):
            st.dataframe(content)
        elif isinstance(content, (str, float, int)):
            st.markdown(f"<p>{content}</p>", unsafe_allow_html=True)
        else:
            st.write(content)
        
        if footer:
            st.markdown(f"<p class='body-small'>{footer}</p>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

# タブナビゲーション（改良版）
def styled_tabs(tabs: List[str]):
    """
    スタイリングされたタブナビゲーションを作成
    
    Parameters
    ----------
    tabs : List[str]
        タブラベルのリスト
    
    Returns
    -------
    int
        選択されたタブのインデックス
    """
    if 'current_tab' not in st.session_state:
        st.session_state.current_tab = 0
    
    # タブのHTMLを構築
    tabs_html = "<div style='display: flex; border-bottom: 1px solid #EEEEEE; margin-bottom: 16px;'>"
    
    for i, tab in enumerate(tabs):
        is_active = (i == st.session_state.current_tab)
        active_style = "color: var(--main-color); border-bottom: 2px solid var(--main-color);" if is_active else ""
        tabs_html += f"""
        <div style="padding: 8px 16px; cursor: pointer; {active_style}" 
             onclick="this.parentElement.querySelectorAll('div').forEach(el => el.style.color = 'inherit'); 
                     this.parentElement.querySelectorAll('div').forEach(el => el.style.borderBottom = 'none');
                     this.style.color = 'var(--main-color)';
                     this.style.borderBottom = '2px solid var(--main-color)';
                     Streamlit.setComponentValue({i});">
            {tab}
        </div>
        """
    
    tabs_html += "</div>"
    
    selected = st.markdown(tabs_html, unsafe_allow_html=True)
    if selected is not None:
        st.session_state.current_tab = selected
    
    return st.session_state.current_tab

# データダウンロードリンク
def download_link(data, filename: str, text: str, mime: str = "text/csv"):
    """
    データダウンロードリンクを生成
    
    Parameters
    ----------
    data : bytes
        ダウンロードするデータ（バイナリ）
    filename : str
        ダウンロードファイル名
    text : str
        リンクテキスト
    mime : str, optional
        MIMEタイプ
    """
    b64 = base64.b64encode(data).decode()
    href = f'<a href="data:{mime};base64,{b64}" download="{filename}" class="download-button">{text}</a>'
    st.markdown(href, unsafe_allow_html=True)

# 設定パネル
def settings_panel(title: str, settings: Dict[str, Any], on_change: Optional[Callable] = None):
    """
    設定パネルを表示
    
    Parameters
    ----------
    title : str
        設定パネルのタイトル
    settings : Dict[str, Any]
        設定項目の辞書
    on_change : Callable, optional
        設定変更時のコールバック関数
    
    Returns
    -------
    Dict[str, Any]
        更新された設定
    """
    with st.expander(title, expanded=True):
        updated_settings = {}
        
        for key, config in settings.items():
            label = config.get("label", key)
            help_text = config.get("help", "")
            value = config.get("value")
            type_ = config.get("type", "text")
            options = config.get("options", [])
            
            if type_ == "select":
                updated_settings[key] = st.selectbox(label, options, index=options.index(value) if value in options else 0, help=help_text)
            elif type_ == "multiselect":
                updated_settings[key] = st.multiselect(label, options, default=value or [], help=help_text)
            elif type_ == "checkbox":
                updated_settings[key] = st.checkbox(label, value=value or False, help=help_text)
            elif type_ == "slider":
                min_val = config.get("min", 0)
                max_val = config.get("max", 100)
                step = config.get("step", 1)
                updated_settings[key] = st.slider(label, min_value=min_val, max_value=max_val, value=value or min_val, step=step, help=help_text)
            elif type_ == "radio":
                updated_settings[key] = st.radio(label, options, index=options.index(value) if value in options else 0, help=help_text)
            else:  # "text" as default
                updated_settings[key] = st.text_input(label, value=value or "", help=help_text)
        
        if on_change and st.button("設定を保存"):
            on_change(updated_settings)
    
    return updated_settings

# データプレビューコンポーネント
def data_preview(df: pd.DataFrame, max_rows: int = 5):
    """
    データフレームのプレビューを表示
    
    Parameters
    ----------
    df : pandas.DataFrame
        プレビューするデータフレーム
    max_rows : int, optional
        表示する最大行数
    """
    preview_df = df.head(max_rows)
    
    st.dataframe(preview_df, use_container_width=True)
    
    if len(df) > max_rows:
        st.caption(f"表示: 最初の{max_rows}行 (全{len(df)}行中)")
    
    # データの基本統計を表示
    num_cols = df.select_dtypes(include=['number']).columns
    if len(num_cols) > 0:
        with st.expander("基本統計を表示"):
            st.dataframe(df[num_cols].describe().round(2), use_container_width=True)

# インタラクティブマップ表示
def interactive_map(map_object, width=800, height=600, with_controls=True, control_position="topright"):
    """
    インタラクティブなマップ表示とオプションのコントロールを提供
    
    Parameters
    ----------
    map_object : folium.Map
        表示するマップオブジェクト
    width : int, optional
        マップの幅（ピクセル）
    height : int, optional
        マップの高さ（ピクセル）
    with_controls : bool, optional
        マップコントロールを表示するか
    control_position : str, optional
        コントロールの位置（"topright", "topleft", "bottomright", "bottomleft"）
    
    Returns
    -------
    folium.Map
        更新されたマップオブジェクト
    """
    # マップコントロールの追加
    if with_controls:
        # レイヤーコントロールの追加
        folium.LayerControl(position=control_position).add_to(map_object)
        
        # ミニマップの追加
        from folium.plugins import MiniMap
        minimap = MiniMap(toggle_display=True, position=control_position)
        map_object.add_child(minimap)
        
        # 距離測定ツールの追加
        from folium.plugins import MeasureControl
        measure_control = MeasureControl(
            position=control_position,
            primary_length_unit='meters',
            secondary_length_unit='kilometers',
            primary_area_unit='sqmeters',
            secondary_area_unit='sqkilometers'
        )
        map_object.add_child(measure_control)
        
        # フルスクリーンコントロールの追加
        from folium.plugins import Fullscreen
        Fullscreen(position=control_position).add_to(map_object)
    
    # マップを表示
    from streamlit_folium import folium_static
    folium_static(map_object, width=width, height=height)
    
    return map_object

# マップ設定パネル
def map_settings_panel(map_tiles, default_tile="OpenStreetMap", key_prefix="map"):
    """
    マップ設定パネルを表示
    
    Parameters
    ----------
    map_tiles : Dict[str, str]
        マップタイルの辞書 {名前: URL}
    default_tile : str, optional
        デフォルトで選択するタイル名
    key_prefix : str, optional
        ウィジェットキーのプレフィックス
    
    Returns
    -------
    Dict[str, Any]
        マップ設定
    """
    settings = {}
    
    with st.container():
        # マップタイル選択
        settings["tile"] = st.selectbox(
            "地図スタイル", 
            options=list(map_tiles.keys()),
            index=list(map_tiles.keys()).index(default_tile) if default_tile in map_tiles else 0,
            key=f"{key_prefix}_tile"
        )
        
        # 表示設定
        col1, col2 = st.columns(2)
        
        with col1:
            settings["show_labels"] = st.checkbox("ラベルを表示", value=True, key=f"{key_prefix}_labels")
            settings["show_tracks"] = st.checkbox("航跡を表示", value=True, key=f"{key_prefix}_tracks")
        
        with col2:
            settings["show_markers"] = st.checkbox("マーカーを表示", value=True, key=f"{key_prefix}_markers")
            settings["sync_time"] = st.checkbox("時間を同期", value=False, key=f"{key_prefix}_sync")
        
        # 追加設定（エキスパンダー内）
        with st.expander("詳細設定"):
            settings["marker_size"] = st.slider("マーカーサイズ", 5, 20, 10, 1, key=f"{key_prefix}_msize")
            settings["line_width"] = st.slider("線の太さ", 1, 10, 3, 1, key=f"{key_prefix}_lwidth")
            settings["opacity"] = st.slider("透明度", 0.1, 1.0, 0.8, 0.1, key=f"{key_prefix}_opacity")
    
    return settings

# 時間範囲選択
def time_range_selector(df: pd.DataFrame, time_column: str = "timestamp", key_prefix: str = "time"):
    """
    データフレームの時間範囲選択ウィジェットを表示
    
    Parameters
    ----------
    df : pandas.DataFrame
        時間データを含むデータフレーム
    time_column : str, optional
        時間カラム名
    key_prefix : str, optional
        ウィジェットキーのプレフィックス
    
    Returns
    -------
    Tuple[datetime, datetime]
        選択された開始時刻と終了時刻
    """
    if time_column not in df.columns:
        return None, None
    
    min_time = df[time_column].min()
    max_time = df[time_column].max()
    
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input(
            "開始日",
            value=min_time.date(),
            min_value=min_time.date(),
            max_value=max_time.date(),
            key=f"{key_prefix}_start_date"
        )
        
        start_time = st.time_input(
            "開始時刻",
            value=min_time.time(),
            key=f"{key_prefix}_start_time"
        )
    
    with col2:
        end_date = st.date_input(
            "終了日",
            value=max_time.date(),
            min_value=min_time.date(),
            max_value=max_time.date(),
            key=f"{key_prefix}_end_date"
        )
        
        end_time = st.time_input(
            "終了時刻",
            value=max_time.time(),
            key=f"{key_prefix}_end_time"
        )
    
    start_datetime = datetime.combine(start_date, start_time)
    end_datetime = datetime.combine(end_date, end_time)
    
    # 時間範囲を示すスライダー（ビジュアル用）
    total_seconds = (max_time - min_time).total_seconds()
    start_ratio = (start_datetime - min_time).total_seconds() / total_seconds
    end_ratio = (end_datetime - min_time).total_seconds() / total_seconds
    
    # Streamlitのスライダーは連続的な値しかサポートしていないので
    # 範囲を0-100にマッピングして表示
    values = st.slider(
        "時間範囲",
        min_value=0,
        max_value=100,
        value=(int(start_ratio * 100), int(end_ratio * 100)),
        key=f"{key_prefix}_range_slider"
    )
    
    # スライダーの値からdatetimeに変換し直す
    if values != (int(start_ratio * 100), int(end_ratio * 100)):
        start_ratio, end_ratio = values[0] / 100, values[1] / 100
        start_datetime = min_time + timedelta(seconds=start_ratio * total_seconds)
        end_datetime = min_time + timedelta(seconds=end_ratio * total_seconds)
    
    return start_datetime, end_datetime

# ドラッグ＆ドロップファイルアップロード
def enhanced_file_uploader(label: str, 
                          accepted_types: List[str], 
                          key: str = None, 
                          help_text: str = None,
                          icon: str = "file-upload",
                          multiple_files: bool = False,
                          on_upload: Optional[Callable] = None):
    """
    拡張されたファイルアップロードコンポーネント
    
    Parameters
    ----------
    label : str
        ファイルアップロードのラベル
    accepted_types : List[str]
        許可されるファイル形式（例: ["csv", "gpx"]）
    key : str, optional
        コンポーネントのキー
    help_text : str, optional
        ヘルプテキスト
    icon : str, optional
        Font Awesomeアイコン名
    multiple_files : bool, optional
        複数ファイルのアップロードを許可するか
    on_upload : Callable, optional
        アップロード後のコールバック関数
        
    Returns
    -------
    UploadedFile or List[UploadedFile]
        アップロードされたファイル、またはファイルのリスト
    """
    # 標準的なStreamlitアップローダー
    uploaded_files = st.file_uploader(
        label,
        type=accepted_types,
        key=key,
        help=help_text,
        accept_multiple_files=multiple_files
    )
    
    # 視覚的にリッチなドラッグ＆ドロップエリアを提供
    if not uploaded_files:
        types_str = ", ".join([f".{t}" for t in accepted_types])
        multi_text = "複数ファイルをドラッグ可能" if multiple_files else ""
        
        dropzone_html = f"""
        <div class="dropzone">
            <i class="fas fa-{icon}" style="font-size: 32px; color: var(--text-secondary); margin-bottom: 8px;"></i>
            <p>ここにファイルをドラッグ＆ドロップ</p>
            <p class="body-small">または下のボタンをクリックしてファイルを選択</p>
            <p class="label">{types_str} {multi_text}</p>
        </div>
        """
        st.markdown(dropzone_html, unsafe_allow_html=True)
    
    # ファイルがアップロードされた場合の表示
    if uploaded_files and not multiple_files:
        uploaded_files = [uploaded_files]  # リストに統一
    
    if uploaded_files:
        for file in uploaded_files:
            file_info = f"""
            <div class="data-card" style="margin-bottom: 8px;">
                <div style="display: flex; align-items: center;">
                    <div style="margin-right: 12px;">
                        <i class="fas fa-file" style="font-size: 24px; color: var(--accent-color);"></i>
                    </div>
                    <div style="flex-grow: 1;">
                        <h3 style="margin: 0; font-size: 16px;">{file.name}</h3>
                        <p class="body-small" style="margin: 2px 0 0 0;">サイズ: {file.size / 1024:.1f} KB - タイプ: {file.type}</p>
                    </div>
                </div>
            </div>
            """
            st.markdown(file_info, unsafe_allow_html=True)
        
        # コールバック関数があれば実行
        if on_upload:
            on_upload(uploaded_files if multiple_files else uploaded_files[0])
    
    return uploaded_files if multiple_files else (uploaded_files[0] if uploaded_files else None)

# ユーザーフィードバックフォーム
def feedback_form(title: str = "フィードバック", key_prefix: str = "feedback"):
    """
    ユーザーフィードバックを収集するフォーム
    
    Parameters
    ----------
    title : str, optional
        フォームのタイトル
    key_prefix : str, optional
        フォーム要素のキープレフィックス
        
    Returns
    -------
    Dict[str, Any]
        フィードバックデータ（送信された場合）
    """
    with st.expander(title, expanded=False):
        st.markdown('<div class="feedback-form">', unsafe_allow_html=True)
        
        # 評価スタープレースホルダー
        st.markdown("""
        <div style="display: flex; justify-content: center; margin-bottom: 16px;">
            <div style="display: flex;">
                <i class="fas fa-star" style="color: gold; font-size: 24px; margin: 0 4px;"></i>
                <i class="fas fa-star" style="color: gold; font-size: 24px; margin: 0 4px;"></i>
                <i class="fas fa-star" style="color: gold; font-size: 24px; margin: 0 4px;"></i>
                <i class="fas fa-star" style="color: gold; font-size: 24px; margin: 0 4px;"></i>
                <i class="fas fa-star" style="color: #EEEEEE; font-size: 24px; margin: 0 4px;"></i>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 実際の評価スライダー
        rating = st.slider("満足度", 1, 5, 4, key=f"{key_prefix}_rating")
        
        # カテゴリ選択
        feedback_type = st.radio(
            "フィードバックの種類",
            ["UI/UX", "機能", "パフォーマンス", "バグ報告", "その他"],
            horizontal=True,
            key=f"{key_prefix}_type"
        )
        
        # 詳細コメント
        comment = st.text_area("詳細コメント", key=f"{key_prefix}_comment")
        
        # 連絡先情報（オプション）
        with st.expander("連絡先情報（オプション）"):
            email = st.text_input("メールアドレス", key=f"{key_prefix}_email")
        
        # 送信ボタン
        submitted = st.button("フィードバックを送信", type="primary", key=f"{key_prefix}_submit")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        if submitted:
            if not comment:
                st.error("コメントを入力してください")
                return None
            
            # フィードバックデータを収集
            feedback_data = {
                "rating": rating,
                "type": feedback_type,
                "comment": comment,
                "email": email,
                "timestamp": datetime.now().isoformat()
            }
            
            # 成功メッセージ
            st.success("フィードバックを受け付けました。ありがとうございます！")
            
            return feedback_data
        
        return None

# 拡張ユーザーフィードバックフォーム
def enhanced_feedback_form(title: str = "フィードバック", 
                          context: str = None,
                          categories: List[str] = None,
                          context_data: Any = None,
                          show_immediate: bool = False,
                          key_prefix: str = "enhanced_feedback",
                          save_callback: Callable = None):
    """
    拡張されたユーザーフィードバック収集フォーム
    
    Parameters
    ----------
    title : str, optional
        フォームのタイトル
    context : str, optional
        フィードバックの文脈/カテゴリ
    categories : List[str], optional
        フィードバックカテゴリの選択肢（デフォルトはUI/UX、機能、パフォーマンス、バグ報告、その他）
    context_data : Any, optional
        フィードバックに添付するコンテキストデータ
    show_immediate : bool, optional
        即座にフォームを表示するか（Trueの場合は展開状態で表示）
    key_prefix : str, optional
        フォーム要素のキープレフィックス
    save_callback : Callable, optional
        フィードバック保存後に呼び出すコールバック関数
        
    Returns
    -------
    Dict[str, Any]
        フィードバックデータ（送信された場合）
    """
    # フィードバックカテゴリのデフォルト値
    if categories is None:
        categories = ["UI/UX", "機能", "パフォーマンス", "バグ報告", "画面表示", "その他"]
    
    # フィードバックフォームのコンテナ
    form_container = st.expander(title, expanded=show_immediate)
    
    with form_container:
        # フィードバックフォームのスタイル
        st.markdown(f"""
        <div class="feedback-form" style="border-left: 4px solid var(--accent-color); padding-left: 16px;">
            <h3 style="color: var(--accent-color); margin-top: 0;">{title}</h3>
            {f'<p class="body">コンテキスト: {context}</p>' if context else ''}
        </div>
        """, unsafe_allow_html=True)
        
        # インタラクティブな星評価
        cols = st.columns([1, 3])
        with cols[0]:
            st.write("総合評価:")
        with cols[1]:
            # 視覚的に魅力的な星評価のプレースホルダー
            rating_html = """
            <div style="display: flex; align-items: center; margin-bottom: 8px;">
            """
            for i in range(1, 6):
                star_color = "var(--accent-color)" if i <= 4 else "#EEEEEE"
                rating_html += f"""
                <div id="star_{i}" style="cursor: pointer; padding: 0 4px;">
                    <i class="fas fa-star" style="color: {star_color}; font-size: 28px;"></i>
                </div>
                """
            rating_html += "</div>"
            st.markdown(rating_html, unsafe_allow_html=True)
            
            # 実際の評価スライダー（HTML星評価の下に配置）
            rating = st.slider(
                "評価レベル", 
                1, 5, 4, 
                key=f"{key_prefix}_rating",
                help="1=非常に不満、5=非常に満足",
                label_visibility="collapsed"
            )
        
        # フィードバックの詳細度に応じた段階的な入力
        satisfaction_level = ["非常に不満", "不満", "普通", "満足", "非常に満足"][rating-1]
        
        # 満足度に応じたメッセージ
        if rating <= 2:
            st.warning(f"満足度が低いようです（{satisfaction_level}）。改善点を教えていただけますと幸いです。")
        elif rating >= 4:
            st.success(f"高評価をありがとうございます（{satisfaction_level}）。さらに良くするためのご意見もぜひお聞かせください。")
        
        # カテゴリ選択（水平ラジオボタン）
        feedback_type = st.radio(
            "フィードバックの種類:",
            categories,
            horizontal=True,
            key=f"{key_prefix}_type"
        )
        
        # 詳細コメント（多めのスペース）
        comment = st.text_area(
            "詳細コメント:",
            height=120,
            placeholder="ご意見、ご感想、改善案などをご記入ください。具体的なフィードバックは開発チームにとって非常に貴重です。",
            key=f"{key_prefix}_comment"
        )
        
        # 追加情報（コンテキスト機能に応じて表示）
        additional_data = {}
        
        if feedback_type == "バグ報告":
            # バグ報告の場合は追加情報を収集
            st.subheader("バグの詳細情報")
            bug_cols = st.columns(2)
            with bug_cols[0]:
                additional_data["severity"] = st.selectbox(
                    "重要度:",
                    ["低", "中", "高", "致命的"],
                    index=1,
                    key=f"{key_prefix}_severity"
                )
            with bug_cols[1]:
                additional_data["reproducible"] = st.checkbox(
                    "再現可能ですか？",
                    value=True,
                    key=f"{key_prefix}_reproducible"
                )
            
            additional_data["steps"] = st.text_area(
                "再現手順:",
                placeholder="1. まず...\n2. 次に...\n3. その結果...",
                key=f"{key_prefix}_steps"
            )
        
        elif feedback_type == "UI/UX" or feedback_type == "画面表示":
            # UI/UXフィードバックの場合は追加情報
            ui_cols = st.columns(2)
            with ui_cols[0]:
                additional_data["device"] = st.selectbox(
                    "デバイス:",
                    ["デスクトップ", "タブレット", "スマートフォン", "その他"],
                    key=f"{key_prefix}_device"
                )
            with ui_cols[1]:
                additional_data["browser"] = st.selectbox(
                    "ブラウザ:",
                    ["Chrome", "Firefox", "Safari", "Edge", "その他"],
                    key=f"{key_prefix}_browser"
                )
                
            # スクリーンショットのアップロード（オプション）
            additional_data["screenshot"] = st.file_uploader(
                "スクリーンショット（オプション）:",
                type=["png", "jpg", "jpeg"],
                key=f"{key_prefix}_screenshot"
            )
        
        # 連絡先情報（オプション）
        with st.expander("連絡先情報（オプション）"):
            contact_cols = st.columns(2)
            with contact_cols[0]:
                name = st.text_input(
                    "お名前:",
                    key=f"{key_prefix}_name"
                )
            with contact_cols[1]:
                email = st.text_input(
                    "メールアドレス:",
                    key=f"{key_prefix}_email",
                    help="回答が必要な場合のみ入力してください"
                )
                
            follow_up = st.checkbox(
                "このフィードバックについて連絡を希望する",
                key=f"{key_prefix}_follow_up"
            )
        
        # 送信ボタン
        col1, col2 = st.columns([3, 1])
        with col2:
            submitted = st.button(
                "送信",
                type="primary",
                key=f"{key_prefix}_submit"
            )
            
        # 送信処理
        if submitted:
            # バリデーション
            if not comment:
                st.error("コメントを入力してください")
                return None
            
            # フィードバックデータを収集
            feedback_data = {
                "rating": rating,
                "satisfaction": satisfaction_level,
                "type": feedback_type,
                "comment": comment,
                "context": context,
                "additional_data": additional_data,
                "contact": {
                    "name": name if 'name' in locals() else "",
                    "email": email if 'email' in locals() else "",
                    "follow_up": follow_up if 'follow_up' in locals() else False
                },
                "context_data": context_data,
                "timestamp": datetime.now().isoformat(),
                "source": "enhanced_feedback_form"
            }
            
            # スクリーンショットの処理
            if 'screenshot' in additional_data and additional_data['screenshot'] is not None:
                # 実際の実装では、スクリーンショットを適切に保存
                feedback_data['has_screenshot'] = True
            
            # 成功メッセージ
            st.success("フィードバックを受け付けました。ありがとうございます！")
            
            # コールバック関数があれば実行
            if save_callback:
                try:
                    save_callback(feedback_data)
                except Exception as e:
                    st.warning(f"フィードバックの保存中にエラーが発生しました: {str(e)}")
            
            # フォームを閉じる
            form_container.expanded = False
            
            return feedback_data
        
        return None

# 改良されたデータカード（インタラクティブ機能付き）
def interactive_data_card(title: str, 
                        content: Any,
                        actions: Optional[List[Tuple[str, str, Optional[Callable]]]] = None,
                        footer: Optional[str] = None,
                        expanded: bool = True,
                        key: Optional[str] = None):
    """
    インタラクティブなデータカードコンポーネント
    
    Parameters
    ----------
    title : str
        カードのタイトル
    content : Any
        カードのコンテンツ
    actions : List[Tuple[str, str, Callable]], optional
        (ラベル, アイコン, コールバック) のタプルのリスト
    footer : str, optional
        カードのフッター
    expanded : bool, optional
        デフォルトで展開するか
    key : str, optional
        カードのキー
        
    Returns
    -------
    Any
        actions が指定されている場合、実行されたアクションの結果
    """
    card_id = key or f"card_{hash(title)}"
    
    # カードのヘッダー部分
    header_html = f"""
    <div class="data-card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <h3 style="margin: 0;">{title}</h3>
            <div>
    """
    
    # アクションボタン
    if actions:
        for i, (label, icon, _) in enumerate(actions):
            header_html += f"""
            <button onclick="Streamlit.setComponentValue('action_{card_id}_{i}')"
                    style="background: none; border: none; cursor: pointer; margin-left: 8px;">
                <i class="fas fa-{icon}" title="{label}"></i>
            </button>
            """
    
    # 展開/折りたたみボタン
    toggle_icon = "chevron-up" if expanded else "chevron-down"
    header_html += f"""
            <button onclick="Streamlit.setComponentValue('toggle_{card_id}')"
                    style="background: none; border: none; cursor: pointer; margin-left: 8px;">
                <i class="fas fa-{toggle_icon}"></i>
            </button>
        </div>
    </div>
    """
    
    # ヘッダーの表示
    clicked = st.markdown(header_html, unsafe_allow_html=True)
    
    # クリックイベントの処理
    result = None
    if clicked:
        if clicked.startswith('action_') and actions:
            action_idx = int(clicked.split('_')[-1])
            if action_idx < len(actions) and actions[action_idx][2]:
                result = actions[action_idx][2]()
        elif clicked == f'toggle_{card_id}':
            # 展開/折りたたみ状態を切り替え
            st.session_state[f'expanded_{card_id}'] = not st.session_state.get(f'expanded_{card_id}', expanded)
    
    # カードの本体部分
    if st.session_state.get(f'expanded_{card_id}', expanded):
        with st.container():
            if isinstance(content, pd.DataFrame):
                st.dataframe(content, use_container_width=True)
            elif isinstance(content, str) and content.strip().startswith("<"):
                # HTMLコンテンツの場合
                st.markdown(content, unsafe_allow_html=True)
            elif isinstance(content, (str, float, int)):
                st.markdown(f"<p>{content}</p>", unsafe_allow_html=True)
            else:
                st.write(content)
            
            if footer:
                st.markdown(f"<p class='body-small'>{footer}</p>", unsafe_allow_html=True)
    
    # 閉じタグ
    st.markdown("</div>", unsafe_allow_html=True)
    
    return result

# 高度なチャートコンテナ
def chart_container(chart_func: Callable, settings: Dict[str, Any], **kwargs):
    """
    対話的な設定付きのチャートコンテナを表示
    
    Parameters
    ----------
    chart_func : Callable
        チャート生成関数
    settings : Dict[str, Any]
        チャート設定の辞書
    **kwargs
        chart_funcに渡す追加の引数
    
    Returns
    -------
    Dict[str, Any]
        更新された設定
    """
    # 2カラムレイアウト
    col1, col2 = st.columns([3, 1])
    
    updated_settings = {}
    
    # 設定パネル
    with col2:
        with st.container():
            st.subheader("チャート設定")
            for key, config in settings.items():
                label = config.get("label", key)
                help_text = config.get("help", "")
                value = config.get("value")
                type_ = config.get("type", "text")
                options = config.get("options", [])
                
                if type_ == "select":
                    updated_settings[key] = st.selectbox(label, options, index=options.index(value) if value in options else 0, help=help_text)
                elif type_ == "multiselect":
                    updated_settings[key] = st.multiselect(label, options, default=value or [], help=help_text)
                elif type_ == "checkbox":
                    updated_settings[key] = st.checkbox(label, value=value or False, help=help_text)
                elif type_ == "slider":
                    min_val = config.get("min", 0)
                    max_val = config.get("max", 100)
                    step = config.get("step", 1)
                    updated_settings[key] = st.slider(label, min_value=min_val, max_value=max_val, value=value or min_val, step=step, help=help_text)
                elif type_ == "radio":
                    updated_settings[key] = st.radio(label, options, index=options.index(value) if value in options else 0, help=help_text)
                elif type_ == "color":
                    # 色選択ウィジェット
                    updated_settings[key] = st.color_picker(label, value=value or "#1565C0", help=help_text)
                else:  # "text" as default
                    updated_settings[key] = st.text_input(label, value=value or "", help=help_text)
            
            # 設定をリセットするボタン
            if st.button("デフォルト設定に戻す"):
                updated_settings = {k: config.get("default", config.get("value")) for k, config in settings.items()}
    
    # チャート表示
    with col1:
        # 更新された設定をkwargsに追加
        kwargs.update(updated_settings)
        
        # チャート生成関数を呼び出し
        fig = chart_func(**kwargs)
        
        # Plotlyチャートを表示
        if fig is not None:
            st.plotly_chart(fig, use_container_width=True)
            
            # エクスポートボタン
            export_col1, export_col2 = st.columns(2)
            with export_col1:
                if st.button("PNG形式で保存", key=f"png_export_{hash(str(kwargs))}"):
                    try:
                        img_bytes = fig.to_image(format="png", engine="kaleido")
                        b64 = base64.b64encode(img_bytes).decode()
                        href = f'<a href="data:image/png;base64,{b64}" download="chart_export.png">クリックしてダウンロード</a>'
                        st.markdown(href, unsafe_allow_html=True)
                    except Exception as e:
                        st.warning(f"エクスポートエラー: {str(e)}")
            
            with export_col2:
                if st.button("インタラクティブHTML形式で保存", key=f"html_export_{hash(str(kwargs))}"):
                    try:
                        html_str = fig.to_html(include_plotlyjs="cdn")
                        b64 = base64.b64encode(html_str.encode()).decode()
                        href = f'<a href="data:text/html;base64,{b64}" download="chart_export.html">クリックしてダウンロード</a>'
                        st.markdown(href, unsafe_allow_html=True)
                    except Exception as e:
                        st.warning(f"エクスポートエラー: {str(e)}")
    
    return updated_settings

# データファイル処理ユーティリティ
def process_file(file, file_type=None, encoding='utf-8'):
    """
    アップロードされたファイルを処理して適切な形式に変換
    
    Parameters
    ----------
    file : UploadedFile
        アップロードされたファイルオブジェクト
    file_type : str, optional
        ファイルタイプ（自動検出も可能）
    encoding : str, optional
        ファイルエンコーディング
    
    Returns
    -------
    Tuple[pd.DataFrame, Optional[str]]
        (処理されたデータフレーム, エラーメッセージ)
    """
    if file is None:
        return None, "ファイルが指定されていません"
    
    # ファイルタイプの自動検出
    if file_type is None:
        if file.name.lower().endswith('.csv'):
            file_type = 'csv'
        elif file.name.lower().endswith('.gpx'):
            file_type = 'gpx'
        elif file.name.lower().endswith(('.xls', '.xlsx')):
            file_type = 'excel'
        elif file.name.lower().endswith('.json'):
            file_type = 'json'
        else:
            return None, f"未対応のファイル形式です: {file.name}"
    
    try:
        # ファイルタイプに応じた処理
        if file_type == 'csv':
            return process_csv(file, encoding)
        elif file_type == 'gpx':
            return process_gpx(file)
        elif file_type == 'excel':
            return process_excel(file)
        elif file_type == 'json':
            return process_json(file, encoding)
        else:
            return None, f"未対応のファイル形式です: {file_type}"
    except Exception as e:
        return None, f"ファイル処理中にエラーが発生しました: {str(e)}"

def process_csv(file, encoding='utf-8'):
    """
    CSVファイルを処理してデータフレームに変換
    
    Parameters
    ----------
    file : UploadedFile
        アップロードされたCSVファイル
    encoding : str, optional
        ファイルエンコーディング
    
    Returns
    -------
    Tuple[pd.DataFrame, Optional[str]]
        (処理されたデータフレーム, エラーメッセージ)
    """
    try:
        # CSVファイルの読み込み試行
        df = pd.read_csv(file, encoding=encoding)
        
        # 必須カラムの確認
        required_columns = ['latitude', 'longitude']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return None, f"必須カラム {', '.join(missing_columns)} がCSVファイルに見つかりません"
        
        # タイムスタンプ列の処理
        if 'timestamp' in df.columns:
            try:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            except:
                return None, "タイムスタンプ列の形式が無効です"
        else:
            # タイムスタンプがない場合はインデックスから生成
            df['timestamp'] = pd.date_range(start='2025-03-01', periods=len(df), freq='10S')
        
        return df, None
        
    except UnicodeDecodeError:
        # エンコーディングが違う場合は別のエンコーディングで再試行
        try:
            other_encoding = 'latin1' if encoding == 'utf-8' else 'utf-8'
            return process_csv(file, other_encoding)
        except:
            return None, f"CSVファイルのエンコーディングが認識できません。エンコーディングを明示的に指定してください。"
    except Exception as e:
        return None, f"CSVファイルの処理中にエラーが発生しました: {str(e)}"

def process_gpx(file):
    """
    GPXファイルを処理してデータフレームに変換
    
    Parameters
    ----------
    file : UploadedFile
        アップロードされたGPXファイル
    
    Returns
    -------
    Tuple[pd.DataFrame, Optional[str]]
        (処理されたデータフレーム, エラーメッセージ)
    """
    try:
        import xml.etree.ElementTree as ET
        from io import BytesIO
        import re
        
        # ファイル内容を読み込み
        content = file.getvalue()
        
        # XMLをパース
        namespaces = {
            'gpx': 'http://www.topografix.com/GPX/1/1',
            'ns3': 'http://www.garmin.com/xmlschemas/TrackPointExtension/v1'
        }
        
        tree = ET.parse(BytesIO(content))
        root = tree.getroot()
        
        # トラックポイントを抽出
        track_points = []
        
        for trk in root.findall('.//gpx:trk', namespaces):
            for trkseg in trk.findall('.//gpx:trkseg', namespaces):
                for trkpt in trkseg.findall('.//gpx:trkpt', namespaces):
                    point = {
                        'latitude': float(trkpt.get('lat')),
                        'longitude': float(trkpt.get('lon'))
                    }
                    
                    time_elem = trkpt.find('.//gpx:time', namespaces)
                    if time_elem is not None and time_elem.text:
                        # ISO 8601形式の時間文字列をパース
                        time_str = time_elem.text
                        point['timestamp'] = pd.to_datetime(time_str)
                    
                    # 拡張データの取得（存在する場合）
                    extensions = trkpt.find('.//gpx:extensions', namespaces)
                    if extensions is not None:
                        # 速度
                        speed = extensions.find('.//ns3:speed', namespaces)
                        if speed is not None and speed.text:
                            point['speed'] = float(speed.text)
                        
                        # コース
                        course = extensions.find('.//ns3:course', namespaces)
                        if course is not None and course.text:
                            point['course'] = float(course.text)
                    
                    track_points.append(point)
        
        # DataFrameに変換
        if not track_points:
            return None, "GPXファイルにトラックポイントが見つかりません"
        
        df = pd.DataFrame(track_points)
        
        # タイムスタンプがない場合は生成
        if 'timestamp' not in df.columns:
            df['timestamp'] = pd.date_range(start='2025-03-01', periods=len(df), freq='10S')
        
        return df, None
    
    except Exception as e:
        return None, f"GPXファイルの処理中にエラーが発生しました: {str(e)}"

def process_excel(file):
    """
    Excelファイルを処理してデータフレームに変換
    
    Parameters
    ----------
    file : UploadedFile
        アップロードされたExcelファイル
    
    Returns
    -------
    Tuple[pd.DataFrame, Optional[str]]
        (処理されたデータフレーム, エラーメッセージ)
    """
    try:
        # Excelファイルの読み込み
        df = pd.read_excel(file)
        
        # 必須カラムの確認
        required_columns = ['latitude', 'longitude']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return None, f"必須カラム {', '.join(missing_columns)} がExcelファイルに見つかりません"
        
        # タイムスタンプ列の処理
        if 'timestamp' in df.columns:
            try:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            except:
                return None, "タイムスタンプ列の形式が無効です"
        else:
            # タイムスタンプがない場合はインデックスから生成
            df['timestamp'] = pd.date_range(start='2025-03-01', periods=len(df), freq='10S')
        
        return df, None
        
    except Exception as e:
        return None, f"Excelファイルの処理中にエラーが発生しました: {str(e)}"

def process_json(file, encoding='utf-8'):
    """
    JSONファイルを処理してデータフレームに変換
    
    Parameters
    ----------
    file : UploadedFile
        アップロードされたJSONファイル
    encoding : str, optional
        ファイルエンコーディング
    
    Returns
    -------
    Tuple[pd.DataFrame, Optional[str]]
        (処理されたデータフレーム, エラーメッセージ)
    """
    try:
        # JSONファイルの読み込み
        content = file.getvalue().decode(encoding)
        data = json.loads(content)
        
        # JSONの形式に応じた処理
        if isinstance(data, list):
            # リスト形式の場合はそのままDataFrameに変換
            df = pd.DataFrame(data)
        elif isinstance(data, dict):
            # 辞書形式の場合は構造を確認
            if 'data' in data and isinstance(data['data'], list):
                df = pd.DataFrame(data['data'])
            elif 'features' in data and isinstance(data['features'], list):
                # GeoJSON形式の処理
                features = []
                for feature in data['features']:
                    if 'geometry' in feature and 'coordinates' in feature['geometry']:
                        props = feature.get('properties', {})
                        coords = feature['geometry']['coordinates']
                        if len(coords) >= 2:
                            point = {'longitude': coords[0], 'latitude': coords[1]}
                            point.update(props)
                            features.append(point)
                df = pd.DataFrame(features)
            else:
                # 単一オブジェクトの場合
                df = pd.DataFrame([data])
        else:
            return None, "JSON形式が認識できません"
        
        # 必須カラムの確認
        required_columns = ['latitude', 'longitude']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return None, f"必須カラム {', '.join(missing_columns)} がJSONファイルに見つかりません"
        
        # タイムスタンプ列の処理
        if 'timestamp' in df.columns:
            try:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            except:
                return None, "タイムスタンプ列の形式が無効です"
        else:
            # タイムスタンプがない場合はインデックスから生成
            df['timestamp'] = pd.date_range(start='2025-03-01', periods=len(df), freq='10S')
        
        return df, None
        
    except Exception as e:
        return None, f"JSONファイルの処理中にエラーが発生しました: {str(e)}"

# データエクスポート機能
def export_dataframe(df, format='csv', filename='export', include_index=False):
    """
    データフレームを指定された形式でエクスポート
    
    Parameters
    ----------
    df : pd.DataFrame
        エクスポートするデータフレーム
    format : str, optional
        エクスポート形式 ('csv', 'excel', 'json')
    filename : str, optional
        出力ファイル名（拡張子なし）
    include_index : bool, optional
        インデックスを含めるか
    
    Returns
    -------
    Tuple[bytes, str, str]
        (エクスポートされたデータ, ファイル名, MIMEタイプ)
    """
    try:
        if format == 'csv':
            # CSVエクスポート
            csv_buffer = StringIO()
            df.to_csv(csv_buffer, index=include_index)
            data = csv_buffer.getvalue().encode('utf-8')
            mime = "text/csv"
            ext = "csv"
        elif format == 'excel':
            # Excelエクスポート
            excel_buffer = BytesIO()
            df.to_excel(excel_buffer, index=include_index)
            data = excel_buffer.getvalue()
            mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ext = "xlsx"
        elif format == 'json':
            # JSONエクスポート
            json_str = df.to_json(orient='records', date_format='iso')
            data = json_str.encode('utf-8')
            mime = "application/json"
            ext = "json"
        else:
            raise ValueError(f"未対応のエクスポート形式: {format}")
        
        return data, f"{filename}.{ext}", mime
    except Exception as e:
        st.error(f"エクスポート中にエラーが発生しました: {str(e)}")
        return None, None, None

# データセット比較ビューアー
def dataset_comparison_viewer(datasets, key_columns=None, metrics=None, 
                             visualization_type="table", key_prefix="compare"):
    """
    複数のデータセットの比較ビューを表示
    
    Parameters
    ----------
    datasets : Dict[str, pd.DataFrame]
        比較するデータセットの辞書 {名前: データフレーム}
    key_columns : List[str], optional
        比較する主要なカラム
    metrics : List[str], optional
        計算する統計指標リスト
    visualization_type : str, optional
        表示タイプ ("table", "chart", "stats")
    key_prefix : str, optional
        ウィジェットキーのプレフィックス
    """
    if not datasets:
        st.warning("比較するデータセットがありません")
        return
    
    # デフォルトのメトリクスを設定
    if metrics is None:
        metrics = ["mean", "std", "min", "max"]
    
    # 表示タイプの選択
    viz_type = st.radio(
        "表示タイプ",
        options=["テーブル表示", "チャート表示", "統計比較"],
        index=["table", "chart", "stats"].index(visualization_type),
        horizontal=True,
        key=f"{key_prefix}_viz_type"
    )
    
    # 利用可能なカラムを取得
    all_columns = set()
    numeric_columns = set()
    for name, df in datasets.items():
        all_columns.update(df.columns)
        numeric_columns.update(df.select_dtypes(include=['number']).columns)
    
    # キーカラムがない場合は自動選択
    if key_columns is None:
        if 'timestamp' in all_columns:
            key_columns = ['timestamp']
        elif len(all_columns) > 0:
            key_columns = [list(all_columns)[0]]
        else:
            st.error("比較可能なカラムがありません")
            return
    
    # 表示するカラムを選択
    if viz_type != "統計比較":
        selected_columns = st.multiselect(
            "表示するカラム",
            options=list(all_columns),
            default=key_columns + list(set(numeric_columns) - set(key_columns))[:3],
            key=f"{key_prefix}_columns"
        )
    else:
        selected_columns = st.multiselect(
            "比較するカラム",
            options=list(numeric_columns),
            default=list(numeric_columns)[:3],
            key=f"{key_prefix}_stat_columns"
        )
    
    if not selected_columns:
        st.warning("表示するカラムを選択してください")
        return
    
    # 表示方法に応じた処理
    if viz_type == "テーブル表示":
        # テーブル表示
        tabs = st.tabs(list(datasets.keys()))
        for i, (name, df) in enumerate(datasets.items()):
            with tabs[i]:
                visible_cols = [col for col in selected_columns if col in df.columns]
                if visible_cols:
                    st.dataframe(df[visible_cols], use_container_width=True)
                else:
                    st.warning(f"{name} には選択されたカラムがありません")
    
    elif viz_type == "チャート表示":
        # チャート表示
        if 'timestamp' in selected_columns or 'timestamp' in key_columns:
            # 時系列チャート
            time_col = 'timestamp'
            value_cols = [col for col in selected_columns if col != time_col and col in numeric_columns]
            
            if value_cols:
                for value_col in value_cols:
                    st.subheader(f"{value_col} の比較")
                    fig = go.Figure()
                    
                    for name, df in datasets.items():
                        if time_col in df.columns and value_col in df.columns:
                            fig.add_trace(go.Scatter(
                                x=df[time_col],
                                y=df[value_col],
                                mode='lines',
                                name=name
                            ))
                    
                    fig.update_layout(
                        xaxis_title=time_col,
                        yaxis_title=value_col,
                        legend_title="データセット",
                        height=400
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("表示可能な数値カラムがありません")
        
        elif len(selected_columns) >= 2 and all(col in numeric_columns for col in selected_columns[:2]):
            # 散布図
            x_col, y_col = selected_columns[:2]
            
            fig = go.Figure()
            
            for name, df in datasets.items():
                if x_col in df.columns and y_col in df.columns:
                    fig.add_trace(go.Scatter(
                        x=df[x_col],
                        y=df[y_col],
                        mode='markers',
                        name=name
                    ))
            
            fig.update_layout(
                xaxis_title=x_col,
                yaxis_title=y_col,
                legend_title="データセット",
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("チャート表示には適切なカラムの組み合わせが必要です")
    
    elif viz_type == "統計比較":
        # 統計比較
        if not selected_columns:
            st.warning("比較するカラムを選択してください")
            return
        
        # 統計計算
        stats_data = []
        
        for name, df in datasets.items():
            dataset_stats = {"データセット": name}
            
            for col in selected_columns:
                if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
                    for metric in metrics:
                        if metric == "mean":
                            dataset_stats[f"{col} (平均)"] = df[col].mean()
                        elif metric == "std":
                            dataset_stats[f"{col} (標準偏差)"] = df[col].std()
                        elif metric == "min":
                            dataset_stats[f"{col} (最小)"] = df[col].min()
                        elif metric == "max":
                            dataset_stats[f"{col} (最大)"] = df[col].max()
                        elif metric == "median":
                            dataset_stats[f"{col} (中央値)"] = df[col].median()
                        elif metric == "count":
                            dataset_stats[f"{col} (カウント)"] = df[col].count()
            
            stats_data.append(dataset_stats)
        
        # 統計データの表示
        stats_df = pd.DataFrame(stats_data)
        st.dataframe(stats_df.set_index("データセット").round(3), use_container_width=True)
        
        # 統計チャート
        for col in selected_columns:
            if all(f"{col} (平均)" in stats for stats in stats_data):
                st.subheader(f"{col} の統計比較")
                
                labels = [stats["データセット"] for stats in stats_data]
                means = [stats[f"{col} (平均)"] for stats in stats_data]
                
                std_values = None
                if all(f"{col} (標準偏差)" in stats for stats in stats_data):
                    std_values = [stats[f"{col} (標準偏差)"] for stats in stats_data]
                
                fig = go.Figure()
                
                if std_values:
                    # エラーバー付きのバーチャート
                    fig.add_trace(go.Bar(
                        x=labels,
                        y=means,
                        error_y=dict(
                            type='data',
                            array=std_values,
                            visible=True
                        ),
                        name=f"{col} (平均±標準偏差)"
                    ))
                else:
                    # 標準のバーチャート
                    fig.add_trace(go.Bar(
                        x=labels,
                        y=means,
                        name=f"{col} (平均)"
                    ))
                
                fig.update_layout(
                    xaxis_title="データセット",
                    yaxis_title=col,
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)

# インタラクティブマップ表示
def interactive_map(map_object, width=800, height=600, with_controls=True, control_position="topright"):
    """
    インタラクティブなマップ表示とオプションのコントロールを提供
    
    Parameters
    ----------
    map_object : folium.Map
        表示するマップオブジェクト
    width : int, optional
        マップの幅（ピクセル）
    height : int, optional
        マップの高さ（ピクセル）
    with_controls : bool, optional
        マップコントロールを表示するか
    control_position : str, optional
        コントロールの位置（"topright", "topleft", "bottomright", "bottomleft"）
    
    Returns
    -------
    folium.Map
        更新されたマップオブジェクト
    """
    # マップコントロールの追加
    if with_controls:
        # レイヤーコントロールの追加
        folium.LayerControl(position=control_position).add_to(map_object)
        
        # ミニマップの追加
        from folium.plugins import MiniMap
        minimap = MiniMap(toggle_display=True, position=control_position)
        map_object.add_child(minimap)
        
        # 距離測定ツールの追加
        from folium.plugins import MeasureControl
        measure_control = MeasureControl(
            position=control_position,
            primary_length_unit='meters',
            secondary_length_unit='kilometers',
            primary_area_unit='sqmeters',
            secondary_area_unit='sqkilometers'
        )
        map_object.add_child(measure_control)
        
        # フルスクリーンコントロールの追加
        from folium.plugins import Fullscreen
        Fullscreen(position=control_position).add_to(map_object)
    
    # マップを表示
    from streamlit_folium import folium_static
    folium_static(map_object, width=width, height=height)
    
    return map_object

# ドラッグ＆ドロップファイルアップロード
def enhanced_file_uploader(label: str, 
                          accepted_types: List[str], 
                          key: str = None, 
                          help_text: str = None,
                          icon: str = "file-upload",
                          multiple_files: bool = False,
                          on_upload: Optional[Callable] = None):
    """
    拡張されたファイルアップロードコンポーネント
    
    Parameters
    ----------
    label : str
        ファイルアップロードのラベル
    accepted_types : List[str]
        許可されるファイル形式（例: ["csv", "gpx"]）
    key : str, optional
        コンポーネントのキー
    help_text : str, optional
        ヘルプテキスト
    icon : str, optional
        Font Awesomeアイコン名
    multiple_files : bool, optional
        複数ファイルのアップロードを許可するか
    on_upload : Callable, optional
        アップロード後のコールバック関数
        
    Returns
    -------
    UploadedFile or List[UploadedFile]
        アップロードされたファイル、またはファイルのリスト
    """
    # 標準的なStreamlitアップローダー
    uploaded_files = st.file_uploader(
        label,
        type=accepted_types,
        key=key,
        help=help_text,
        accept_multiple_files=multiple_files
    )
    
    # 視覚的にリッチなドラッグ＆ドロップエリアを提供
    if not uploaded_files:
        types_str = ", ".join([f".{t}" for t in accepted_types])
        multi_text = "複数ファイルをドラッグ可能" if multiple_files else ""
        
        dropzone_html = f"""
        <div class="dropzone">
            <i class="fas fa-{icon}" style="font-size: 32px; color: var(--text-secondary); margin-bottom: 8px;"></i>
            <p>ここにファイルをドラッグ＆ドロップ</p>
            <p class="body-small">または下のボタンをクリックしてファイルを選択</p>
            <p class="label">{types_str} {multi_text}</p>
        </div>
        """
        st.markdown(dropzone_html, unsafe_allow_html=True)
    
    # ファイルがアップロードされた場合の表示
    if uploaded_files and not multiple_files:
        uploaded_files = [uploaded_files]  # リストに統一
    
    if uploaded_files:
        for file in uploaded_files:
            file_info = f"""
            <div class="data-card" style="margin-bottom: 8px;">
                <div style="display: flex; align-items: center;">
                    <div style="margin-right: 12px;">
                        <i class="fas fa-file" style="font-size: 24px; color: var(--accent-color);"></i>
                    </div>
                    <div style="flex-grow: 1;">
                        <h3 style="margin: 0; font-size: 16px;">{file.name}</h3>
                        <p class="body-small" style="margin: 2px 0 0 0;">サイズ: {file.size / 1024:.1f} KB - タイプ: {file.type}</p>
                    </div>
                </div>
            </div>
            """
            st.markdown(file_info, unsafe_allow_html=True)
        
        # コールバック関数があれば実行
        if on_upload:
            on_upload(uploaded_files if multiple_files else uploaded_files[0])
    
    return uploaded_files if multiple_files else (uploaded_files[0] if uploaded_files else None)