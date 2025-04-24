# -*- coding: utf-8 -*-
"""
セーリング戦略分析システム - 入力コンポーネント

テキスト入力、数値入力、パスワード入力などのコンポーネントを提供します。
"""

import streamlit as st
from ..styles import Colors, BorderRadius, FontSizes, Spacing, Transitions

def create_text_input(
    label, 
    value="", 
    placeholder=None,
    help=None,
    disabled=False,
    max_chars=None,
    key=None,
    label_visibility="visible"
):
    """
    テキスト入力フィールドを作成します。
    
    Parameters:
    -----------
    label : str
        入力フィールドのラベル
    value : str, optional
        初期値
    placeholder : str, optional
        プレースホルダーテキスト
    help : str, optional
        ヘルプテキスト
    disabled : bool, optional
        無効状態にするかどうか
    max_chars : int, optional
        最大文字数
    key : str, optional
        コンポーネントの一意のキー
    label_visibility : str, optional
        ラベルの表示設定 ("visible", "hidden", "collapsed")
        
    Returns:
    --------
    str
        入力された値
    """
    # CSSスタイルの定義
    input_style = f"""
    <style>
    div[data-testid="stTextInput"] label {{
        font-size: {FontSizes.BODY};
        color: {Colors.DARK_2};
        font-weight: 500;
        margin-bottom: {Spacing.XS};
    }}
    
    div[data-testid="stTextInput"] input {{
        background-color: {Colors.WHITE};
        border: 1px solid {Colors.GRAY_2};
        border-radius: {BorderRadius.SMALL};
        padding: 8px 12px;
        transition: border-color {Transitions.FAST} ease-out;
        font-size: {FontSizes.BODY};
    }}
    
    div[data-testid="stTextInput"] input:focus {{
        border-color: {Colors.PRIMARY};
        box-shadow: 0 0 0 1px {Colors.PRIMARY};
    }}
    
    div[data-testid="stTextInput"] input:hover:not(:focus) {{
        border-color: {Colors.GRAY_MID};
    }}
    
    div[data-testid="stTextInput"] input:disabled {{
        background-color: {Colors.GRAY_1};
        color: {Colors.GRAY_MID};
        cursor: not-allowed;
    }}
    </style>
    """
    
    st.markdown(input_style, unsafe_allow_html=True)
    
    input_value = st.text_input(
        label=label,
        value=value,
        placeholder=placeholder,
        help=help,
        disabled=disabled,
        max_chars=max_chars,
        key=key,
        label_visibility=label_visibility
    )
    
    return input_value

def create_number_input(
    label, 
    value=0,
    min_value=None,
    max_value=None,
    step=None, 
    format=None,
    help=None,
    disabled=False,
    key=None,
    label_visibility="visible"
):
    """
    数値入力フィールドを作成します。
    
    Parameters:
    -----------
    label : str
        入力フィールドのラベル
    value : int or float, optional
        初期値
    min_value : int or float, optional
        最小値
    max_value : int or float, optional
        最大値
    step : int or float, optional
        増減量
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
        入力された値
    """
    # CSSスタイルの定義
    input_style = f"""
    <style>
    div[data-testid="stNumberInput"] label {{
        font-size: {FontSizes.BODY};
        color: {Colors.DARK_2};
        font-weight: 500;
        margin-bottom: {Spacing.XS};
    }}
    
    div[data-testid="stNumberInput"] input {{
        background-color: {Colors.WHITE};
        border: 1px solid {Colors.GRAY_2};
        border-radius: {BorderRadius.SMALL};
        padding: 8px 12px;
        transition: border-color {Transitions.FAST} ease-out;
        font-size: {FontSizes.BODY};
    }}
    
    div[data-testid="stNumberInput"] input:focus {{
        border-color: {Colors.PRIMARY};
        box-shadow: 0 0 0 1px {Colors.PRIMARY};
    }}
    
    div[data-testid="stNumberInput"] input:hover:not(:focus) {{
        border-color: {Colors.GRAY_MID};
    }}
    
    div[data-testid="stNumberInput"] input:disabled {{
        background-color: {Colors.GRAY_1};
        color: {Colors.GRAY_MID};
        cursor: not-allowed;
    }}
    
    /* ステッパーボタンのスタイル */
    div[data-testid="stNumberInput"] button {{
        border: none;
        background: transparent;
        color: {Colors.PRIMARY};
        transition: color {Transitions.FAST} ease-out;
    }}
    
    div[data-testid="stNumberInput"] button:hover {{
        color: {Colors.SECONDARY};
    }}
    </style>
    """
    
    st.markdown(input_style, unsafe_allow_html=True)
    
    input_value = st.number_input(
        label=label,
        value=value,
        min_value=min_value,
        max_value=max_value,
        step=step,
        format=format,
        help=help,
        disabled=disabled,
        key=key,
        label_visibility=label_visibility
    )
    
    return input_value

def create_password_input(
    label, 
    value="", 
    placeholder=None,
    help=None,
    disabled=False,
    max_chars=None,
    key=None,
    label_visibility="visible"
):
    """
    パスワード入力フィールドを作成します。
    
    Parameters:
    -----------
    label : str
        入力フィールドのラベル
    value : str, optional
        初期値
    placeholder : str, optional
        プレースホルダーテキスト
    help : str, optional
        ヘルプテキスト
    disabled : bool, optional
        無効状態にするかどうか
    max_chars : int, optional
        最大文字数
    key : str, optional
        コンポーネントの一意のキー
    label_visibility : str, optional
        ラベルの表示設定 ("visible", "hidden", "collapsed")
        
    Returns:
    --------
    str
        入力された値
    """
    # パスワード入力はテキスト入力と同じスタイルを使用
    input_style = f"""
    <style>
    div[data-testid="stTextInput"].stPasswordInput label {{
        font-size: {FontSizes.BODY};
        color: {Colors.DARK_2};
        font-weight: 500;
        margin-bottom: {Spacing.XS};
    }}
    
    div[data-testid="stTextInput"].stPasswordInput input {{
        background-color: {Colors.WHITE};
        border: 1px solid {Colors.GRAY_2};
        border-radius: {BorderRadius.SMALL};
        padding: 8px 12px;
        transition: border-color {Transitions.FAST} ease-out;
        font-size: {FontSizes.BODY};
    }}
    
    div[data-testid="stTextInput"].stPasswordInput input:focus {{
        border-color: {Colors.PRIMARY};
        box-shadow: 0 0 0 1px {Colors.PRIMARY};
    }}
    
    div[data-testid="stTextInput"].stPasswordInput input:hover:not(:focus) {{
        border-color: {Colors.GRAY_MID};
    }}
    
    div[data-testid="stTextInput"].stPasswordInput input:disabled {{
        background-color: {Colors.GRAY_1};
        color: {Colors.GRAY_MID};
        cursor: not-allowed;
    }}
    </style>
    """
    
    st.markdown(input_style, unsafe_allow_html=True)
    
    input_value = st.text_input(
        label=label,
        value=value,
        placeholder=placeholder,
        help=help,
        disabled=disabled,
        max_chars=max_chars,
        key=key,
        label_visibility=label_visibility,
        type="password"
    )
    
    return input_value
