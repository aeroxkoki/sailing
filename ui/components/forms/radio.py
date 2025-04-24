# -*- coding: utf-8 -*-
"""
セーリング戦略分析システム - ラジオボタンコンポーネント

ラジオボタンのコンポーネントを提供します。
"""

import streamlit as st
from ..styles import Colors, BorderRadius, FontSizes, Spacing, FontWeights, Transitions

def create_radio_group(
    label,
    options,
    index=0,
    format_func=None,
    help=None,
    horizontal=False,
    disabled=False,
    key=None,
    label_visibility="visible"
):
    """
    ラジオボタンのグループを作成します。
    
    Parameters:
    -----------
    label : str
        ラジオグループのラベル
    options : list
        選択肢のリスト
    index : int, optional
        デフォルトで選択される選択肢のインデックス
    format_func : callable, optional
        選択肢の表示方法をカスタマイズする関数
    help : str, optional
        ヘルプテキスト
    horizontal : bool, optional
        水平方向に表示するかどうか
    disabled : bool, optional
        無効状態にするかどうか
    key : str, optional
        コンポーネントの一意のキー
    label_visibility : str, optional
        ラベルの表示設定 ("visible", "hidden", "collapsed")
        
    Returns:
    --------
    any
        選択された値
    """
    # CSSスタイルの定義
    radio_style = f"""
    <style>
    div[data-testid="stRadio"] label {{
        font-size: {FontSizes.BODY};
        color: {Colors.DARK_2};
        font-weight: 500;
        margin-bottom: {Spacing.XS};
    }}
    
    div[data-testid="stRadio"] div[role="radiogroup"] {{
        background-color: {Colors.WHITE};
        border: 1px solid {Colors.GRAY_2};
        border-radius: {BorderRadius.SMALL};
        padding: {Spacing.S};
    }}
    
    div[data-testid="stRadio"] label[data-baseweb="radio"] span[data-baseweb="icon"] div {{
        border-color: {Colors.GRAY_MID};
        transition: all {Transitions.FAST} ease-out;
    }}
    
    div[data-testid="stRadio"] label[data-baseweb="radio"] span[data-baseweb="icon"] div::before {{
        background-color: {Colors.PRIMARY};
    }}
    
    div[data-testid="stRadio"] label[aria-disabled="true"] span[data-baseweb="icon"] div {{
        border-color: {Colors.GRAY_2};
        background-color: {Colors.GRAY_1};
    }}
    
    div[data-testid="stRadio"] label[data-baseweb="radio"] {{
        font-size: {FontSizes.BODY};
        color: {Colors.DARK_2};
        font-weight: {FontWeights.NORMAL};
    }}
    </style>
    """
    
    st.markdown(radio_style, unsafe_allow_html=True)
    
    selected_value = st.radio(
        label=label,
        options=options,
        index=index,
        format_func=format_func,
        help=help,
        horizontal=horizontal,
        disabled=disabled,
        key=key,
        label_visibility=label_visibility
    )
    
    return selected_value
