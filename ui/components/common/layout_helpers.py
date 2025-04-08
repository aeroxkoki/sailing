"""
セーリング戦略分析システム - レイアウトヘルパーコンポーネント

レイアウト構築を支援するヘルパーコンポーネントを提供します。
"""

import streamlit as st
from ..styles import Colors, Spacing, BorderRadius, Shadows

def create_spacer(size="M"):
    """
    スペーサーを作成します。
    
    Parameters:
    -----------
    size : str, optional
        スペーサーのサイズ ("XS", "S", "M", "L", "XL", "XXL", "XXXL")
        
    Returns:
    --------
    None
    """
    # サイズによる余白の設定
    if size == "XS":
        margin = Spacing.XS
    elif size == "S":
        margin = Spacing.S
    elif size == "L":
        margin = Spacing.L
    elif size == "XL":
        margin = Spacing.XL
    elif size == "XXL":
        margin = Spacing.XXL
    elif size == "XXXL":
        margin = Spacing.XXXL
    else:  # M (default)
        margin = Spacing.M
    
    # スペーサーのHTML
    spacer_html = f"""
    <div style="margin-top: {margin};"></div>
    """
    
    st.markdown(spacer_html, unsafe_allow_html=True)

def create_divider(margin="M", color=Colors.GRAY_2):
    """
    区切り線を作成します。
    
    Parameters:
    -----------
    margin : str, optional
        区切り線の上下マージン ("XS", "S", "M", "L", "XL")
    color : str, optional
        区切り線の色
        
    Returns:
    --------
    None
    """
    # マージンサイズの設定
    if margin == "XS":
        margin_size = Spacing.XS
    elif margin == "S":
        margin_size = Spacing.S
    elif margin == "L":
        margin_size = Spacing.L
    elif margin == "XL":
        margin_size = Spacing.XL
    else:  # M (default)
        margin_size = Spacing.M
    
    # 区切り線のHTML
    divider_html = f"""
    <hr style="border: 0; height: 1px; background-color: {color}; margin: {margin_size} 0;" />
    """
    
    st.markdown(divider_html, unsafe_allow_html=True)

def create_container(
    content=None, 
    width="100%", 
    padding="M", 
    bg_color=Colors.WHITE, 
    border=False, 
    border_radius="MEDIUM",
    shadow=None
):
    """
    コンテナを作成します。
    
    Parameters:
    -----------
    content : str, optional
        コンテナに表示するHTMLコンテンツ
    width : str, optional
        コンテナの幅（px, %, remなど）
    padding : str, optional
        コンテナの内側の余白 ("XS", "S", "M", "L", "XL")
    bg_color : str, optional
        背景色
    border : bool, optional
        枠線を表示するかどうか
    border_radius : str, optional
        角丸の大きさ ("SMALL", "MEDIUM", "LARGE")
    shadow : str, optional
        影のタイプ (None, "SHADOW_1", "SHADOW_2", "SHADOW_3")
        
    Returns:
    --------
    None
    """
    # パディングサイズの設定
    if padding == "XS":
        padding_size = Spacing.XS
    elif padding == "S":
        padding_size = Spacing.S
    elif padding == "L":
        padding_size = Spacing.L
    elif padding == "XL":
        padding_size = Spacing.XL
    else:  # M (default)
        padding_size = Spacing.M
    
    # ボーダーラジウスの設定
    if border_radius == "SMALL":
        radius = BorderRadius.SMALL
    elif border_radius == "LARGE":
        radius = BorderRadius.LARGE
    else:  # MEDIUM (default)
        radius = BorderRadius.MEDIUM
    
    # シャドウの設定
    shadow_style = ""
    if shadow == "SHADOW_1":
        shadow_style = f"box-shadow: {Shadows.SHADOW_1};"
    elif shadow == "SHADOW_2":
        shadow_style = f"box-shadow: {Shadows.SHADOW_2};"
    elif shadow == "SHADOW_3":
        shadow_style = f"box-shadow: {Shadows.SHADOW_3};"
    
    # ボーダーの設定
    border_style = f"border: 1px solid {Colors.GRAY_2};" if border else ""
    
    # コンテナのHTML
    container_html = f"""
    <div style="
        width: {width};
        padding: {padding_size};
        background-color: {bg_color};
        border-radius: {radius};
        margin-bottom: {Spacing.M};
        {border_style}
        {shadow_style}
    ">
        {content if content else ''}
    </div>
    """
    
    st.markdown(container_html, unsafe_allow_html=True)
