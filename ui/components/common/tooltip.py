# -*- coding: utf-8 -*-
"""
セーリング戦略分析システム - ツールチップコンポーネント

ツールチップを提供します。
"""

import streamlit as st
from ..styles import Colors, BorderRadius, Shadows, FontSizes, FontWeights, Transitions

def create_tooltip(content, tooltip_text, position="top", width="200px", icon=None):
    """
    ツールチップ付きのコンテンツを作成します。
    
    Parameters:
    -----------
    content : str
        ツールチップを付けるコンテンツ
    tooltip_text : str
        ツールチップに表示するテキスト
    position : str, optional
        ツールチップの表示位置 ("top", "right", "bottom", "left")
    width : str, optional
        ツールチップの幅
    icon : str, optional
        表示するアイコン（Font Awesomeクラス）
        
    Returns:
    --------
    None
    """
    # ポジションに応じたスタイル
    if position == "right":
        position_style = f"""
            left: 100%;
            top: 50%;
            transform: translateY(-50%);
            margin-left: 8px;
        """
    elif position == "bottom":
        position_style = f"""
            top: 100%;
            left: 50%;
            transform: translateX(-50%);
            margin-top: 8px;
        """
    elif position == "left":
        position_style = f"""
            right: 100%;
            top: 50%;
            transform: translateY(-50%);
            margin-right: 8px;
        """
    else:  # top (default)
        position_style = f"""
            bottom: 100%;
            left: 50%;
            transform: translateX(-50%);
            margin-bottom: 8px;
        """
    
    # CSSスタイルの定義
    tooltip_style = f"""
    <style>
    .tooltip-container {{
        position: relative;
        display: inline-block;
    }}
    
    .tooltip-container .tooltip-content {{
        visibility: hidden;
        position: absolute;
        {position_style}
        background-color: {Colors.DARK_2};
        color: {Colors.WHITE};
        padding: 8px 12px;
        border-radius: {BorderRadius.SMALL};
        font-size: {FontSizes.SMALL};
        line-height: 1.4;
        z-index: 1000;
        width: {width};
        box-shadow: {Shadows.SHADOW_2};
        opacity: 0;
        transition: opacity {Transitions.FAST} ease-out;
        pointer-events: none;
        text-align: left;
    }}
    
    .tooltip-container:hover .tooltip-content {{
        visibility: visible;
        opacity: 1;
    }}
    </style>
    """
    
    # アイコン部分のHTML
    if icon:
        content = f'<i class="{icon}"></i>'
    
    # ツールチップのHTML生成
    tooltip_html = f"""
    {tooltip_style}
    <div class="tooltip-container">
        <span>{content}</span>
        <div class="tooltip-content">{tooltip_text}</div>
    </div>
    """
    
    st.markdown(tooltip_html, unsafe_allow_html=True)
