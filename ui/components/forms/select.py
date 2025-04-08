"""
セーリング戦略分析システム - 選択コンポーネント

ドロップダウン選択、複数選択などのコンポーネントを提供します。
"""

import streamlit as st
from ..styles import Colors, BorderRadius, FontSizes, Spacing, Transitions

def create_select(
    label, 
    options,
    index=0,
    format_func=None,
    help=None,
    disabled=False,
    key=None,
    label_visibility="visible"
):
    """
    ドロップダウン選択を作成します。
    
    Parameters:
    -----------
    label : str
        選択コンポーネントのラベル
    options : list
        選択肢のリスト
    index : int, optional
        デフォルトで選択される選択肢のインデックス
    format_func : callable, optional
        選択肢の表示方法をカスタマイズする関数
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
    any
        選択された値
    """
    # CSSスタイルの定義
    select_style = f"""
    <style>
    div[data-testid="stSelectbox"] label {{
        font-size: {FontSizes.BODY};
        color: {Colors.DARK_2};
        font-weight: 500;
        margin-bottom: {Spacing.XS};
    }}
    
    div[data-testid="stSelectbox"] div[data-baseweb="select"] {{
        background-color: {Colors.WHITE};
        border: 1px solid {Colors.GRAY_2};
        border-radius: {BorderRadius.SMALL};
        transition: border-color {Transitions.FAST} ease-out;
    }}
    
    div[data-testid="stSelectbox"] div[data-baseweb="select"]:focus-within {{
        border-color: {Colors.PRIMARY};
        box-shadow: 0 0 0 1px {Colors.PRIMARY};
    }}
    
    div[data-testid="stSelectbox"] div[data-baseweb="select"]:hover:not(:focus-within) {{
        border-color: {Colors.GRAY_MID};
    }}
    
    div[data-testid="stSelectbox"] div[data-baseweb="select"] div {{
        font-size: {FontSizes.BODY};
    }}
    
    div[data-testid="stSelectbox"] div[aria-disabled="true"] {{
        background-color: {Colors.GRAY_1};
        color: {Colors.GRAY_MID};
        cursor: not-allowed;
    }}
    </style>
    """
    
    st.markdown(select_style, unsafe_allow_html=True)
    
    selected_value = st.selectbox(
        label=label,
        options=options,
        index=index,
        format_func=format_func,
        help=help,
        disabled=disabled,
        key=key,
        label_visibility=label_visibility
    )
    
    return selected_value

def create_multi_select(
    label, 
    options,
    default=None,
    format_func=None,
    help=None,
    disabled=False,
    key=None,
    label_visibility="visible"
):
    """
    複数選択コンポーネントを作成します。
    
    Parameters:
    -----------
    label : str
        選択コンポーネントのラベル
    options : list
        選択肢のリスト
    default : list, optional
        デフォルトで選択される選択肢のリスト
    format_func : callable, optional
        選択肢の表示方法をカスタマイズする関数
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
    list
        選択された値のリスト
    """
    # CSSスタイルの定義
    multi_select_style = f"""
    <style>
    div[data-testid="stMultiSelect"] label {{
        font-size: {FontSizes.BODY};
        color: {Colors.DARK_2};
        font-weight: 500;
        margin-bottom: {Spacing.XS};
    }}
    
    div[data-testid="stMultiSelect"] div[data-baseweb="select"] {{
        background-color: {Colors.WHITE};
        border: 1px solid {Colors.GRAY_2};
        border-radius: {BorderRadius.SMALL};
        transition: border-color {Transitions.FAST} ease-out;
    }}
    
    div[data-testid="stMultiSelect"] div[data-baseweb="select"]:focus-within {{
        border-color: {Colors.PRIMARY};
        box-shadow: 0 0 0 1px {Colors.PRIMARY};
    }}
    
    div[data-testid="stMultiSelect"] div[data-baseweb="select"]:hover:not(:focus-within) {{
        border-color: {Colors.GRAY_MID};
    }}
    
    div[data-testid="stMultiSelect"] div[data-baseweb="tag"] {{
        background-color: {Colors.PRIMARY};
        color: {Colors.WHITE};
        border-radius: {BorderRadius.SMALL};
    }}
    
    div[data-testid="stMultiSelect"] div[data-baseweb="tag"] button {{
        color: {Colors.WHITE};
    }}
    
    div[data-testid="stMultiSelect"] div[aria-disabled="true"] {{
        background-color: {Colors.GRAY_1};
        color: {Colors.GRAY_MID};
        cursor: not-allowed;
    }}
    </style>
    """
    
    st.markdown(multi_select_style, unsafe_allow_html=True)
    
    selected_values = st.multiselect(
        label=label,
        options=options,
        default=default,
        format_func=format_func,
        help=help,
        disabled=disabled,
        key=key,
        label_visibility=label_visibility
    )
    
    return selected_values
