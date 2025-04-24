# -*- coding: utf-8 -*-
"""
セーリング戦略分析システム - カードコンポーネント

様々なスタイルのカードコンポーネントを提供します。
"""

import streamlit as st
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from components.styles import Colors, BorderRadius, Shadows, Spacing, FontSizes, FontWeights
from contextlib import contextmanager

def create_card(title=None, subtitle=None, content=None, footer=None, padding="normal", shadow=True, border=False):
    """
    標準カードコンポーネントを作成します。
    
    Parameters:
    -----------
    title : str, optional
        カードのタイトル
    subtitle : str, optional
        カードのサブタイトル
    content : str, optional
        カードの本文内容
    footer : str, optional
        カードのフッター内容
    padding : str, optional
        余白のサイズ ("small", "normal", "large")
    shadow : bool, optional
        影をつけるかどうか
    border : bool, optional
        枠線をつけるかどうか
        
    Returns:
    --------
    None
    """
    # パディングサイズの取得
    if padding == "small":
        padding_size = Spacing.S
    elif padding == "large":
        padding_size = Spacing.L
    else:  # normal
        padding_size = Spacing.M
    
    # 影と枠線のスタイル
    shadow_style = f"box-shadow: {Shadows.SHADOW_1};" if shadow else ""
    border_style = f"border: 1px solid {Colors.GRAY_2};" if border else ""
    
    card_html = f"""
    <div style="
        background-color: {Colors.WHITE};
        border-radius: {BorderRadius.MEDIUM};
        padding: {padding_size};
        margin-bottom: {Spacing.M};
        {shadow_style}
        {border_style}
    ">
        {f'<div style="font-size: {FontSizes.TITLE}; font-weight: {FontWeights.SEMIBOLD}; margin-bottom: {Spacing.S};">{title}</div>' if title else ''}
        {f'<div style="font-size: {FontSizes.SUBTITLE}; color: {Colors.DARK_1}; margin-bottom: {Spacing.S};">{subtitle}</div>' if subtitle else ''}
        {f'<div style="font-size: {FontSizes.BODY}; line-height: 1.5;">{content}</div>' if content else ''}
        {f'<div style="margin-top: {Spacing.M}; padding-top: {Spacing.S}; border-top: 1px solid {Colors.GRAY_2};">{footer}</div>' if footer else ''}
    </div>
    """
    
    st.markdown(card_html, unsafe_allow_html=True)

def create_info_card(title=None, content=None, color=Colors.INFO, icon=None):
    """
    情報表示用のカードを作成します。
    
    Parameters:
    -----------
    title : str, optional
        カードのタイトル
    content : str, optional
        カードの本文内容
    color : str, optional
        カードのアクセントカラー
    icon : str, optional
        表示するアイコン（Font Awesomeクラス）
        
    Returns:
    --------
    None
    """
    # 色に応じた薄い背景色を生成
    if color == Colors.INFO:
        bg_color = "#E3F2FD"
    elif color == Colors.SUCCESS:
        bg_color = "#E8F5E9"
    elif color == Colors.WARNING:
        bg_color = "#FFF3E0"
    elif color == Colors.ERROR:
        bg_color = "#FFEBEE"
    else:
        bg_color = "#F5F5F5"
    
    icon_html = f'<i class="{icon}" style="margin-right: {Spacing.S}; color: {color};"></i>' if icon else ''
    
    card_html = f"""
    <div style="
        background-color: {bg_color};
        border-left: 4px solid {color};
        border-radius: {BorderRadius.SMALL};
        padding: {Spacing.S} {Spacing.M};
        margin-bottom: {Spacing.M};
    ">
        {f'<div style="font-size: {FontSizes.SUBTITLE}; font-weight: {FontWeights.SEMIBOLD}; margin-bottom: {Spacing.XS}; display: flex; align-items: center;">{icon_html}{title}</div>' if title else ''}
        {f'<div style="font-size: {FontSizes.BODY}; line-height: 1.5;">{content}</div>' if content else ''}
    </div>
    """
    
    st.markdown(card_html, unsafe_allow_html=True)

def create_action_card(title, content=None, actions=None, padding="normal", shadow=True):
    """
    アクション付きカードを作成します。
    
    Parameters:
    -----------
    title : str
        カードのタイトル
    content : str, optional
        カードの本文内容
    actions : list of dict, optional
        アクションボタンの設定リスト
        各辞書は以下のキーを持つことができます:
        - label: ボタンのラベル (必須)
        - key: ボタンの一意のキー (オプション)
        - type: ボタンのタイプ (オプション, デフォルトは"secondary")
    padding : str, optional
        余白のサイズ ("small", "normal", "large")
    shadow : bool, optional
        影をつけるかどうか
        
    Returns:
    --------
    dict
        各アクションのキーとクリック状態を含む辞書
    """
    # カード本体の作成
    create_card(title=title, content=content, padding=padding, shadow=shadow)
    
    # アクションボタンの作成
    action_results = {}
    
    if actions:
        cols = st.columns(len(actions))
        
        for i, action in enumerate(actions):
            label = action.get("label", "")
            key = action.get("key", f"action_{i}_{label}")
            button_type = action.get("type", "secondary")
            
            with cols[i]:
                clicked = st.button(label, key=key, type=button_type)
                action_results[key] = clicked
    
    return action_results


@contextmanager
def card(title: str = None, key: str = None, **kwargs):
    """
    カード形式のコンテナを提供するコンテキストマネージャ
    
    Parameters
    ----------
    title : str, optional
        カードのタイトル, by default None
    key : str, optional
        コンポーネントのユニークキー, by default None
    **kwargs
        追加の引数を指定
    
    Examples
    --------
    >>> with card("タイトル"):
    >>>     st.write("カードの内容")
    """
    # スタイルの適用
    padding_size = Spacing.M
    shadow_style = f"box-shadow: {Shadows.SHADOW_1};"
    border_style = ""
    
    card_style = f"""
    <div style="
        background-color: {Colors.WHITE};
        border-radius: {BorderRadius.MEDIUM};
        padding: {padding_size};
        margin-bottom: {Spacing.M};
        {shadow_style}
        {border_style}
    ">
    """
    
    # カードの開始
    st.markdown(card_style, unsafe_allow_html=True)
    
    # タイトルがあれば表示
    if title:
        st.markdown(f"<h3 style='margin-top:0; font-size: {FontSizes.SUBTITLE}; font-weight: {FontWeights.SEMIBOLD};'>{title}</h3>", unsafe_allow_html=True)
    
    # カードのコンテンツを表示
    yield
    
    # カードの終了
    st.markdown("</div>", unsafe_allow_html=True)
