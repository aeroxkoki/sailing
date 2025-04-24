# -*- coding: utf-8 -*-
"""
セーリング戦略分析システム - バッジコンポーネント

様々なスタイルのバッジコンポーネントを提供します。
"""

import streamlit as st
from ..styles import Colors, BorderRadius, FontSizes, FontWeights

def create_badge(text, badge_type="primary", size="medium", icon=None):
    """
    バッジを作成します。
    
    Parameters:
    -----------
    text : str
        バッジに表示するテキスト
    badge_type : str, optional
        バッジのタイプ ("primary", "secondary", "success", "warning", "error", "info")
    size : str, optional
        バッジのサイズ ("small", "medium", "large")
    icon : str, optional
        表示するアイコン（Font Awesomeクラス）
        
    Returns:
    --------
    None
    """
    # バッジタイプに応じた色の設定
    if badge_type == "primary":
        bg_color = Colors.PRIMARY
        text_color = Colors.WHITE
    elif badge_type == "secondary":
        bg_color = Colors.SECONDARY
        text_color = Colors.WHITE
    elif badge_type == "success":
        bg_color = Colors.SUCCESS
        text_color = Colors.WHITE
    elif badge_type == "warning":
        bg_color = Colors.WARNING
        text_color = Colors.DARK_2
    elif badge_type == "error":
        bg_color = Colors.ERROR
        text_color = Colors.WHITE
    elif badge_type == "info":
        bg_color = Colors.INFO
        text_color = Colors.WHITE
    else:
        bg_color = Colors.GRAY_MID
        text_color = Colors.WHITE
    
    # サイズに応じたスタイルの設定
    if size == "small":
        font_size = "10px"
        padding = "2px 6px"
        icon_size = "8px"
    elif size == "large":
        font_size = "14px"
        padding = "4px 12px"
        icon_size = "14px"
    else:  # medium
        font_size = "12px"
        padding = "3px 8px"
        icon_size = "12px"
    
    # アイコン部分のHTML
    icon_html = f'<i class="{icon}" style="font-size: {icon_size}; margin-right: 4px;"></i>' if icon else ''
    
    # バッジのHTML生成
    badge_html = f"""
    <span style="
        display: inline-flex;
        align-items: center;
        background-color: {bg_color};
        color: {text_color};
        border-radius: {BorderRadius.SMALL};
        font-size: {font_size};
        font-weight: {FontWeights.MEDIUM};
        padding: {padding};
        line-height: 1;
        white-space: nowrap;
    ">
        {icon_html}{text}
    </span>
    """
    
    st.markdown(badge_html, unsafe_allow_html=True)
