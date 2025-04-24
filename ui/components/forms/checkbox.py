# -*- coding: utf-8 -*-
"""
セーリング戦略分析システム - チェックボックスコンポーネント

チェックボックス、チェックボックスグループのコンポーネントを提供します。
"""

import streamlit as st
from ..styles import Colors, BorderRadius, FontSizes, Spacing, FontWeights

def create_checkbox(
    label,
    value=False,
    help=None,
    disabled=False,
    key=None,
    label_visibility="visible"
):
    """
    チェックボックスを作成します。
    
    Parameters:
    -----------
    label : str
        チェックボックスのラベル
    value : bool, optional
        初期値
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
    bool
        チェックボックスの状態
    """
    # CSSスタイルの定義
    checkbox_style = f"""
    <style>
    div[data-testid="stCheckbox"] label {{
        font-size: {FontSizes.BODY};
        color: {Colors.DARK_2};
        font-weight: {FontWeights.NORMAL};
    }}
    
    div[data-testid="stCheckbox"] span[data-baseweb="checkbox"] div {{
        border-color: {Colors.GRAY_MID};
        border-radius: {BorderRadius.SMALL};
    }}
    
    div[data-testid="stCheckbox"] span[data-baseweb="checkbox"] div[aria-checked="true"] {{
        background-color: {Colors.PRIMARY};
        border-color: {Colors.PRIMARY};
    }}
    
    div[data-testid="stCheckbox"] span[data-baseweb="checkbox"] div[aria-checked="true"]::before {{
        border-bottom-color: {Colors.WHITE};
        border-right-color: {Colors.WHITE};
    }}
    
    div[data-testid="stCheckbox"] span[data-baseweb="checkbox"] div[aria-disabled="true"] {{
        background-color: {Colors.GRAY_1};
        border-color: {Colors.GRAY_2};
    }}
    </style>
    """
    
    st.markdown(checkbox_style, unsafe_allow_html=True)
    
    checked = st.checkbox(
        label=label,
        value=value,
        help=help,
        disabled=disabled,
        key=key,
        label_visibility=label_visibility
    )
    
    return checked

def create_checkbox_group(
    label,
    options,
    default=None,
    help=None,
    disabled=False,
    key_prefix=None
):
    """
    チェックボックスグループを作成します。
    
    Parameters:
    -----------
    label : str
        グループのラベル
    options : list
        選択肢のリスト
    default : list, optional
        デフォルトで選択される選択肢のリスト
    help : str, optional
        ヘルプテキスト
    disabled : bool, optional
        全てのチェックボックスを無効状態にするかどうか
    key_prefix : str, optional
        キー生成の際のプレフィックス
        
    Returns:
    --------
    list
        選択された値のリスト
    """
    if default is None:
        default = []
    
    if key_prefix is None:
        key_prefix = f"checkbox_group_{label}"
    
    # グループラベルのスタイル
    group_label_style = f"""
    <div style="
        font-size: {FontSizes.BODY};
        color: {Colors.DARK_2};
        font-weight: 500;
        margin-bottom: {Spacing.XS};
    ">{label}</div>
    """
    
    st.markdown(group_label_style, unsafe_allow_html=True)
    
    # ヘルプテキストの表示
    if help:
        help_style = f"""
        <div style="
            font-size: {FontSizes.SMALL};
            color: {Colors.GRAY_MID};
            margin-bottom: {Spacing.XS};
        ">{help}</div>
        """
        st.markdown(help_style, unsafe_allow_html=True)
    
    # チェックボックスグループのコンテナ
    group_container_style = f"""
    <div style="
        background-color: {Colors.WHITE};
        border: 1px solid {Colors.GRAY_2};
        border-radius: {BorderRadius.SMALL};
        padding: {Spacing.S};
        margin-bottom: {Spacing.M};
    ">
    """
    
    st.markdown(group_container_style, unsafe_allow_html=True)
    
    # 各チェックボックスの作成
    selected_values = []
    
    for i, option in enumerate(options):
        # オプションが辞書の場合（ラベルと値を分ける）
        if isinstance(option, dict) and 'label' in option and 'value' in option:
            option_label = option['label']
            option_value = option['value']
        else:
            option_label = str(option)
            option_value = option
        
        # デフォルト値の設定
        default_checked = option_value in default
        
        # チェックボックスの作成
        key = f"{key_prefix}_{i}"
        checked = create_checkbox(
            label=option_label,
            value=default_checked,
            disabled=disabled,
            key=key
        )
        
        if checked:
            selected_values.append(option_value)
    
    # コンテナの終了
    st.markdown("</div>", unsafe_allow_html=True)
    
    return selected_values
