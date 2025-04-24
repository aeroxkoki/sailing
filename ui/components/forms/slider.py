# -*- coding: utf-8 -*-
"""
セーリング戦略分析システム - スライダーコンポーネント

単一値スライダーと範囲スライダーのコンポーネントを提供します。
"""

import streamlit as st
from ..styles import Colors, BorderRadius, FontSizes, Spacing, Transitions

def create_slider(
    label,
    min_value=0,
    max_value=100,
    value=None,
    step=None,
    format=None,
    help=None,
    disabled=False,
    key=None,
    label_visibility="visible"
):
    """
    単一値スライダーを作成します。
    
    Parameters:
    -----------
    label : str
        スライダーのラベル
    min_value : int or float, optional
        最小値
    max_value : int or float, optional
        最大値
    value : int or float, optional
        初期値 (None の場合、中央値)
    step : int or float, optional
        ステップ値
    format : str, optional
        表示フォーマット
    help : str, optional
        ヘルプテキスト
    disabled : bool, optional
        無効状態にするかどうか
    key : str, optional
        コンポーネントの一意のキー
    label_visibility : str, optional
        ラベルの表示設定 ("visible", "hidden", "collapsed")
        
    Returns:
    --------
    int or float
        スライダーの値
    """
    # デフォルト値が指定されていない場合は中央値を使用
    if value is None:
        value = (min_value + max_value) / 2
    
    # CSSスタイルの定義
    slider_style = f"""
    <style>
    div[data-testid="stSlider"] p {{
        font-size: {FontSizes.BODY};
        color: {Colors.DARK_2};
        font-weight: 500;
        margin-bottom: {Spacing.XS};
    }}
    
    div[data-testid="stSlider"] div[data-baseweb="slider"] {{
        margin-top: {Spacing.M};
    }}
    
    div[data-testid="stSlider"] div[data-baseweb="slider"] div[role="slider"] {{
        background-color: {Colors.PRIMARY};
        border-color: {Colors.PRIMARY};
        transition: all {Transitions.FAST} ease-out;
    }}
    
    div[data-testid="stSlider"] div[data-baseweb="slider"] div[role="slider"]:hover {{
        background-color: {Colors.PRIMARY};
        border-color: {Colors.PRIMARY};
        transform: scale(1.1);
    }}
    
    div[data-testid="stSlider"] div[data-baseweb="slider"] div[data-testid="stTickBar"] {{
        background-color: {Colors.GRAY_2};
    }}
    
    div[data-testid="stSlider"] div[data-baseweb="slider"] div[data-testid="stTickBar"] div {{
        background-color: {Colors.PRIMARY};
    }}
    
    div[data-testid="stSlider"][aria-disabled="true"] div[data-baseweb="slider"] div[role="slider"] {{
        background-color: {Colors.GRAY_MID};
        border-color: {Colors.GRAY_MID};
    }}
    </style>
    """
    
    st.markdown(slider_style, unsafe_allow_html=True)
    
    slider_value = st.slider(
        label=label,
        min_value=min_value,
        max_value=max_value,
        value=value,
        step=step,
        format=format,
        help=help,
        disabled=disabled,
        key=key,
        label_visibility=label_visibility
    )
    
    return slider_value

def create_range_slider(
    label,
    min_value=0,
    max_value=100,
    value=None,
    step=None,
    format=None,
    help=None,
    disabled=False,
    key=None,
    label_visibility="visible"
):
    """
    範囲スライダーを作成します。
    
    Parameters:
    -----------
    label : str
        スライダーのラベル
    min_value : int or float, optional
        最小値
    max_value : int or float, optional
        最大値
    value : tuple of (int or float), optional
        初期値の範囲 (例: (25, 75))、None の場合、全範囲
    step : int or float, optional
        ステップ値
    format : str, optional
        表示フォーマット
    help : str, optional
        ヘルプテキスト
    disabled : bool, optional
        無効状態にするかどうか
    key : str, optional
        コンポーネントの一意のキー
    label_visibility : str, optional
        ラベルの表示設定 ("visible", "hidden", "collapsed")
        
    Returns:
    --------
    tuple of (int or float)
        選択された範囲値 (start, end)
    """
    # デフォルト値が指定されていない場合は全範囲の1/4と3/4を使用
    if value is None:
        range_size = max_value - min_value
        value = (min_value + range_size / 4, max_value - range_size / 4)
    
    # 同じスタイルを使用（単一スライダーと共有）
    slider_style = f"""
    <style>
    div[data-testid="stSlider"] p {{
        font-size: {FontSizes.BODY};
        color: {Colors.DARK_2};
        font-weight: 500;
        margin-bottom: {Spacing.XS};
    }}
    
    div[data-testid="stSlider"] div[data-baseweb="slider"] {{
        margin-top: {Spacing.M};
    }}
    
    div[data-testid="stSlider"] div[data-baseweb="slider"] div[role="slider"] {{
        background-color: {Colors.PRIMARY};
        border-color: {Colors.PRIMARY};
        transition: all {Transitions.FAST} ease-out;
    }}
    
    div[data-testid="stSlider"] div[data-baseweb="slider"] div[role="slider"]:hover {{
        background-color: {Colors.PRIMARY};
        border-color: {Colors.PRIMARY};
        transform: scale(1.1);
    }}
    
    div[data-testid="stSlider"] div[data-baseweb="slider"] div[data-testid="stTickBar"] {{
        background-color: {Colors.GRAY_2};
    }}
    
    div[data-testid="stSlider"] div[data-baseweb="slider"] div[data-testid="stTickBar"] div {{
        background-color: {Colors.PRIMARY};
    }}
    
    div[data-testid="stSlider"][aria-disabled="true"] div[data-baseweb="slider"] div[role="slider"] {{
        background-color: {Colors.GRAY_MID};
        border-color: {Colors.GRAY_MID};
    }}
    </style>
    """
    
    st.markdown(slider_style, unsafe_allow_html=True)
    
    range_values = st.slider(
        label=label,
        min_value=min_value,
        max_value=max_value,
        value=value,
        step=step,
        format=format,
        help=help,
        disabled=disabled,
        key=key,
        label_visibility=label_visibility
    )
    
    return range_values
