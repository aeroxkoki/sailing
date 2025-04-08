"""
セーリング戦略分析システム - テキストエリアコンポーネント

複数行のテキスト入力コンポーネントを提供します。
"""

import streamlit as st
from ..styles import Colors, BorderRadius, FontSizes, Spacing, Transitions

def create_text_area(
    label,
    value="",
    height=None,
    max_chars=None,
    placeholder=None,
    help=None,
    disabled=False,
    key=None,
    label_visibility="visible"
):
    """
    テキストエリアを作成します。
    
    Parameters:
    -----------
    label : str
        テキストエリアのラベル
    value : str, optional
        初期値
    height : int, optional
        テキストエリアの高さ（ピクセル単位）
    max_chars : int, optional
        最大文字数
    placeholder : str, optional
        プレースホルダーテキスト
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
    str
        入力されたテキスト
    """
    # CSSスタイルの定義
    textarea_style = f"""
    <style>
    div[data-testid="stTextArea"] label {{
        font-size: {FontSizes.BODY};
        color: {Colors.DARK_2};
        font-weight: 500;
        margin-bottom: {Spacing.XS};
    }}
    
    div[data-testid="stTextArea"] textarea {{
        background-color: {Colors.WHITE};
        border: 1px solid {Colors.GRAY_2};
        border-radius: {BorderRadius.SMALL};
        padding: 8px 12px;
        transition: border-color {Transitions.FAST} ease-out;
        font-size: {FontSizes.BODY};
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
    }}
    
    div[data-testid="stTextArea"] textarea:focus {{
        border-color: {Colors.PRIMARY};
        box-shadow: 0 0 0 1px {Colors.PRIMARY};
    }}
    
    div[data-testid="stTextArea"] textarea:hover:not(:focus) {{
        border-color: {Colors.GRAY_MID};
    }}
    
    div[data-testid="stTextArea"] textarea:disabled {{
        background-color: {Colors.GRAY_1};
        color: {Colors.GRAY_MID};
        cursor: not-allowed;
    }}
    </style>
    """
    
    st.markdown(textarea_style, unsafe_allow_html=True)
    
    input_text = st.text_area(
        label=label,
        value=value,
        height=height,
        max_chars=max_chars,
        placeholder=placeholder,
        help=help,
        disabled=disabled,
        key=key,
        label_visibility=label_visibility
    )
    
    return input_text
