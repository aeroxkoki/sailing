"""
セーリング戦略分析システム - ボタンコンポーネント

様々なスタイルのボタンコンポーネントを提供します。
"""

import streamlit as st
from ..styles import Colors, BorderRadius, Transitions, Spacing, FontWeights

def create_button(label, button_type="primary", size="medium", icon=None, on_click=None, key=None):
    """
    汎用ボタンを作成します。
    
    Parameters:
    -----------
    label : str
        ボタンに表示するテキスト
    button_type : str, optional
        ボタンのタイプ ("primary", "secondary", "text", "warning")
    size : str, optional
        ボタンのサイズ ("small", "medium", "large")
    icon : str, optional
        ボタンの前に表示するアイコン（Font Awesomeクラス）
    on_click : callable, optional
        クリック時に実行する関数
    key : str, optional
        ボタンの一意のキー

    Returns:
    --------
    bool
        ボタンがクリックされたらTrue、そうでなければFalse
    """
    if button_type == "primary":
        return create_primary_button(label, size, icon, on_click, key)
    elif button_type == "secondary":
        return create_secondary_button(label, size, icon, on_click, key)
    elif button_type == "text":
        return create_text_button(label, size, icon, on_click, key)
    elif button_type == "warning":
        return create_warning_button(label, size, icon, on_click, key)
    else:
        # デフォルトはプライマリボタン
        return create_primary_button(label, size, icon, on_click, key)

def create_primary_button(label, size="medium", icon=None, on_click=None, key=None):
    """
    プライマリボタンを作成します。
    
    Parameters:
    -----------
    label : str
        ボタンに表示するテキスト
    size : str, optional
        ボタンのサイズ ("small", "medium", "large")
    icon : str, optional
        ボタンの前に表示するアイコン（Font Awesomeクラス）
    on_click : callable, optional
        クリック時に実行する関数
    key : str, optional
        ボタンの一意のキー

    Returns:
    --------
    bool
        ボタンがクリックされたらTrue、そうでなければFalse
    """
    height, padding, font_size = _get_button_size_properties(size)
    
    button_style = f"""
    <style>
    .stButton button.primary-btn {{
        background-color: {Colors.PRIMARY};
        color: {Colors.WHITE};
        border: none;
        border-radius: {BorderRadius.SMALL};
        padding: {padding};
        height: {height};
        font-weight: {FontWeights.MEDIUM};
        font-size: {font_size};
        width: auto;
        transition: all {Transitions.FAST} ease-out;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
    }}
    .stButton button.primary-btn:hover {{
        background-color: #0D47A1;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }}
    .stButton button.primary-btn:active {{
        background-color: #1565C0;
        transform: translateY(1px);
    }}
    .stButton button.primary-btn:focus {{
        outline: none;
        box-shadow: 0 0 0 2px rgba(21, 101, 192, 0.5);
    }}
    </style>
    """
    
    st.markdown(button_style, unsafe_allow_html=True)
    
    button_icon = f'<i class="{icon}"></i> ' if icon else ''
    button_html = f'<span>{button_icon}{label}</span>'
    
    if key is None:
        key = f"primary_btn_{label}"
    
    clicked = st.button(button_html, key=key, on_click=on_click, type="primary")
    
    return clicked

def create_secondary_button(label, size="medium", icon=None, on_click=None, key=None):
    """
    セカンダリボタンを作成します。
    
    Parameters:
    -----------
    label : str
        ボタンに表示するテキスト
    size : str, optional
        ボタンのサイズ ("small", "medium", "large")
    icon : str, optional
        ボタンの前に表示するアイコン（Font Awesomeクラス）
    on_click : callable, optional
        クリック時に実行する関数
    key : str, optional
        ボタンの一意のキー

    Returns:
    --------
    bool
        ボタンがクリックされたらTrue、そうでなければFalse
    """
    height, padding, font_size = _get_button_size_properties(size)
    
    button_style = f"""
    <style>
    .stButton button.secondary-btn {{
        background-color: {Colors.WHITE};
        color: {Colors.PRIMARY};
        border: 1px solid {Colors.PRIMARY};
        border-radius: {BorderRadius.SMALL};
        padding: {padding};
        height: {height};
        font-weight: {FontWeights.MEDIUM};
        font-size: {font_size};
        width: auto;
        transition: all {Transitions.FAST} ease-out;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
    }}
    .stButton button.secondary-btn:hover {{
        background-color: #E3F2FD;
    }}
    .stButton button.secondary-btn:active {{
        background-color: #BBDEFB;
        transform: translateY(1px);
    }}
    .stButton button.secondary-btn:focus {{
        outline: none;
        box-shadow: 0 0 0 2px rgba(21, 101, 192, 0.3);
    }}
    </style>
    """
    
    st.markdown(button_style, unsafe_allow_html=True)
    
    button_icon = f'<i class="{icon}"></i> ' if icon else ''
    button_html = f'<span>{button_icon}{label}</span>'
    
    if key is None:
        key = f"secondary_btn_{label}"
    
    clicked = st.button(button_html, key=key, on_click=on_click, type="secondary")
    
    return clicked

def create_text_button(label, size="medium", icon=None, on_click=None, key=None):
    """
    テキストボタンを作成します。
    
    Parameters:
    -----------
    label : str
        ボタンに表示するテキスト
    size : str, optional
        ボタンのサイズ ("small", "medium", "large")
    icon : str, optional
        ボタンの前に表示するアイコン（Font Awesomeクラス）
    on_click : callable, optional
        クリック時に実行する関数
    key : str, optional
        ボタンの一意のキー

    Returns:
    --------
    bool
        ボタンがクリックされたらTrue、そうでなければFalse
    """
    height, padding, font_size = _get_button_size_properties(size)
    
    button_style = f"""
    <style>
    .stButton button.text-btn {{
        background-color: transparent;
        color: {Colors.PRIMARY};
        border: none;
        border-radius: {BorderRadius.SMALL};
        padding: {padding};
        height: {height};
        font-weight: {FontWeights.MEDIUM};
        font-size: {font_size};
        width: auto;
        transition: all {Transitions.FAST} ease-out;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
    }}
    .stButton button.text-btn:hover {{
        background-color: {Colors.GRAY_1};
    }}
    .stButton button.text-btn:active {{
        background-color: {Colors.GRAY_2};
        transform: translateY(1px);
    }}
    .stButton button.text-btn:focus {{
        outline: none;
        box-shadow: 0 0 0 2px rgba(21, 101, 192, 0.2);
    }}
    </style>
    """
    
    st.markdown(button_style, unsafe_allow_html=True)
    
    button_icon = f'<i class="{icon}"></i> ' if icon else ''
    button_html = f'<span>{button_icon}{label}</span>'
    
    if key is None:
        key = f"text_btn_{label}"
    
    clicked = st.button(button_html, key=key, on_click=on_click)
    
    return clicked

def create_warning_button(label, size="medium", icon=None, on_click=None, key=None):
    """
    警告ボタンを作成します。
    
    Parameters:
    -----------
    label : str
        ボタンに表示するテキスト
    size : str, optional
        ボタンのサイズ ("small", "medium", "large")
    icon : str, optional
        ボタンの前に表示するアイコン（Font Awesomeクラス）
    on_click : callable, optional
        クリック時に実行する関数
    key : str, optional
        ボタンの一意のキー

    Returns:
    --------
    bool
        ボタンがクリックされたらTrue、そうでなければFalse
    """
    height, padding, font_size = _get_button_size_properties(size)
    
    button_style = f"""
    <style>
    .stButton button.warning-btn {{
        background-color: {Colors.ERROR};
        color: {Colors.WHITE};
        border: none;
        border-radius: {BorderRadius.SMALL};
        padding: {padding};
        height: {height};
        font-weight: {FontWeights.MEDIUM};
        font-size: {font_size};
        width: auto;
        transition: all {Transitions.FAST} ease-out;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
    }}
    .stButton button.warning-btn:hover {{
        background-color: #C62828;
    }}
    .stButton button.warning-btn:active {{
        background-color: #B71C1C;
        transform: translateY(1px);
    }}
    .stButton button.warning-btn:focus {{
        outline: none;
        box-shadow: 0 0 0 2px rgba(239, 83, 80, 0.5);
    }}
    </style>
    """
    
    st.markdown(button_style, unsafe_allow_html=True)
    
    button_icon = f'<i class="{icon}"></i> ' if icon else ''
    button_html = f'<span>{button_icon}{label}</span>'
    
    if key is None:
        key = f"warning_btn_{label}"
    
    clicked = st.button(button_html, key=key, on_click=on_click)
    
    return clicked

def _get_button_size_properties(size):
    """
    ボタンサイズに応じたプロパティを取得します。
    
    Parameters:
    -----------
    size : str
        ボタンのサイズ ("small", "medium", "large")
        
    Returns:
    --------
    tuple
        (高さ, パディング, フォントサイズ)
    """
    if size == "small":
        return "32px", "4px 12px", "12px"
    elif size == "large":
        return "44px", "8px 24px", "16px"
    else:  # medium (default)
        return "38px", "6px 16px", "14px"
