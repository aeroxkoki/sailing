# -*- coding: utf-8 -*-
"""
セーリング戦略分析システム - 日付ピッカーコンポーネント

日付選択と日付範囲選択のコンポーネントを提供します。
"""

import streamlit as st
from datetime import datetime, date, timedelta
from ..styles import Colors, BorderRadius, FontSizes, Spacing, Transitions

def create_date_picker(
    label,
    value=None,
    min_value=None,
    max_value=None,
    help=None,
    key=None,
    format="YYYY-MM-DD",
    label_visibility="visible"
):
    """
    日付選択ピッカーを作成します。
    
    Parameters:
    -----------
    label : str
        日付ピッカーのラベル
    value : datetime.date, optional
        選択されるデフォルトの日付 (None の場合、今日)
    min_value : datetime.date, optional
        選択可能な最小日付
    max_value : datetime.date, optional
        選択可能な最大日付
    help : str, optional
        ヘルプテキスト
    key : str, optional
        コンポーネントの一意のキー
    format : str, optional
        日付表示フォーマット
    label_visibility : str, optional
        ラベルの表示設定 ("visible", "hidden", "collapsed")
        
    Returns:
    --------
    datetime.date
        選択された日付
    """
    # デフォルト値が指定されていない場合は今日の日付を使用
    if value is None:
        value = date.today()
    
    # CSSスタイルの定義
    date_picker_style = f"""
    <style>
    div[data-testid="stDateInput"] label {{
        font-size: {FontSizes.BODY};
        color: {Colors.DARK_2};
        font-weight: 500;
        margin-bottom: {Spacing.XS};
    }}
    
    div[data-testid="stDateInput"] div[data-baseweb="input"] {{
        background-color: {Colors.WHITE};
        border: 1px solid {Colors.GRAY_2};
        border-radius: {BorderRadius.SMALL};
        transition: border-color {Transitions.FAST} ease-out;
    }}
    
    div[data-testid="stDateInput"] div[data-baseweb="input"]:focus-within {{
        border-color: {Colors.PRIMARY};
        box-shadow: 0 0 0 1px {Colors.PRIMARY};
    }}
    
    div[data-testid="stDateInput"] div[data-baseweb="input"]:hover:not(:focus-within) {{
        border-color: {Colors.GRAY_MID};
    }}
    
    div[data-testid="stDateInput"] input {{
        font-size: {FontSizes.BODY};
    }}
    
    /* カレンダー内の今日の日付のスタイル */
    div[data-baseweb="calendar"] div[data-baseweb="calendar-cell"]:not([disabled])[data-highlighted="today"] {{
        background-color: {Colors.PRIMARY} !important;
        color: {Colors.WHITE} !important;
    }}
    
    /* カレンダー内の選択された日付のスタイル */
    div[data-baseweb="calendar"] div[data-baseweb="calendar-cell"][aria-selected="true"] {{
        background-color: {Colors.SECONDARY} !important;
        color: {Colors.WHITE} !important;
    }}
    </style>
    """
    
    st.markdown(date_picker_style, unsafe_allow_html=True)
    
    selected_date = st.date_input(
        label=label,
        value=value,
        min_value=min_value,
        max_value=max_value,
        help=help,
        key=key,
        format=format,
        label_visibility=label_visibility
    )
    
    return selected_date

def create_date_range_picker(
    label,
    values=None,
    min_value=None,
    max_value=None,
    help=None,
    key=None,
    format="YYYY-MM-DD",
    label_visibility="visible"
):
    """
    日付範囲ピッカーを作成します。
    
    Parameters:
    -----------
    label : str
        日付範囲ピッカーのラベル
    values : tuple of datetime.date, optional
        デフォルトで選択される日付範囲 (start_date, end_date)
        None の場合、(今日, 1週間後)
    min_value : datetime.date, optional
        選択可能な最小日付
    max_value : datetime.date, optional
        選択可能な最大日付
    help : str, optional
        ヘルプテキスト
    key : str, optional
        コンポーネントの一意のキー
    format : str, optional
        日付表示フォーマット
    label_visibility : str, optional
        ラベルの表示設定 ("visible", "hidden", "collapsed")
        
    Returns:
    --------
    tuple of datetime.date
        選択された日付範囲 (start_date, end_date)
    """
    # デフォルト値が指定されていない場合は今日から1週間の範囲を使用
    if values is None:
        today = date.today()
        one_week_later = today + timedelta(days=7)
        values = (today, one_week_later)
    
    # CSSスタイルは単一日付ピッカーと同じ
    date_picker_style = f"""
    <style>
    div[data-testid="stDateInput"] label {{
        font-size: {FontSizes.BODY};
        color: {Colors.DARK_2};
        font-weight: 500;
        margin-bottom: {Spacing.XS};
    }}
    
    div[data-testid="stDateInput"] div[data-baseweb="input"] {{
        background-color: {Colors.WHITE};
        border: 1px solid {Colors.GRAY_2};
        border-radius: {BorderRadius.SMALL};
        transition: border-color {Transitions.FAST} ease-out;
    }}
    
    div[data-testid="stDateInput"] div[data-baseweb="input"]:focus-within {{
        border-color: {Colors.PRIMARY};
        box-shadow: 0 0 0 1px {Colors.PRIMARY};
    }}
    
    div[data-testid="stDateInput"] div[data-baseweb="input"]:hover:not(:focus-within) {{
        border-color: {Colors.GRAY_MID};
    }}
    
    div[data-testid="stDateInput"] input {{
        font-size: {FontSizes.BODY};
    }}
    
    /* カレンダー内の今日の日付のスタイル */
    div[data-baseweb="calendar"] div[data-baseweb="calendar-cell"]:not([disabled])[data-highlighted="today"] {{
        background-color: {Colors.PRIMARY} !important;
        color: {Colors.WHITE} !important;
    }}
    
    /* カレンダー内の選択された日付のスタイル */
    div[data-baseweb="calendar"] div[data-baseweb="calendar-cell"][aria-selected="true"] {{
        background-color: {Colors.SECONDARY} !important;
        color: {Colors.WHITE} !important;
    }}
    
    /* カレンダー内の範囲選択のスタイル */
    div[data-baseweb="calendar"] div[data-baseweb="calendar-cell"][data-in-range="true"] {{
        background-color: {Colors.SECONDARY}30 !important;
    }}
    </style>
    """
    
    st.markdown(date_picker_style, unsafe_allow_html=True)
    
    date_range = st.date_input(
        label=label,
        value=values,
        min_value=min_value,
        max_value=max_value,
        help=help,
        key=key,
        format=format,
        label_visibility=label_visibility
    )
    
    # 単一の日付を選択した場合でも適切に処理（タプルにする）
    if isinstance(date_range, date):
        return (date_range, date_range)
    
    return date_range
