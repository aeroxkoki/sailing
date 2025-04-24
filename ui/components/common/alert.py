# -*- coding: utf-8 -*-
"""
セーリング戦略分析システム - アラートコンポーネント

様々なスタイルのアラートコンポーネントを提供します。
"""

import streamlit as st
from ..styles import Colors, BorderRadius, Spacing, FontSizes, FontWeights

def create_alert(message, alert_type="info", dismissible=False, icon=None):
    """
    アラートを作成します。
    
    Parameters:
    -----------
    message : str
        アラートに表示するメッセージ
    alert_type : str, optional
        アラートのタイプ ("info", "success", "warning", "error")
    dismissible : bool, optional
        閉じるボタンを表示するかどうか
    icon : str, optional
        表示するアイコン（Font Awesomeクラス）
        
    Returns:
    --------
    bool
        dismissible=Trueの場合、アラートが閉じられたかどうか
    """
    if alert_type == "info":
        return create_info_alert(message, dismissible, icon)
    elif alert_type == "success":
        return create_success_alert(message, dismissible, icon)
    elif alert_type == "warning":
        return create_warning_alert(message, dismissible, icon)
    elif alert_type == "error":
        return create_error_alert(message, dismissible, icon)
    else:
        # デフォルトは情報アラート
        return create_info_alert(message, dismissible, icon)

def create_info_alert(message, dismissible=False, icon=None):
    """
    情報アラートを作成します。
    
    Parameters:
    -----------
    message : str
        アラートに表示するメッセージ
    dismissible : bool, optional
        閉じるボタンを表示するかどうか
    icon : str, optional
        表示するアイコン（Font Awesomeクラス）
        
    Returns:
    --------
    bool
        dismissible=Trueの場合、アラートが閉じられたかどうか
    """
    return _create_alert_by_type(message, "info", Colors.INFO, "#E3F2FD", dismissible, icon)

def create_success_alert(message, dismissible=False, icon=None):
    """
    成功アラートを作成します。
    
    Parameters:
    -----------
    message : str
        アラートに表示するメッセージ
    dismissible : bool, optional
        閉じるボタンを表示するかどうか
    icon : str, optional
        表示するアイコン（Font Awesomeクラス）
        
    Returns:
    --------
    bool
        dismissible=Trueの場合、アラートが閉じられたかどうか
    """
    return _create_alert_by_type(message, "success", Colors.SUCCESS, "#E8F5E9", dismissible, icon)

def create_warning_alert(message, dismissible=False, icon=None):
    """
    警告アラートを作成します。
    
    Parameters:
    -----------
    message : str
        アラートに表示するメッセージ
    dismissible : bool, optional
        閉じるボタンを表示するかどうか
    icon : str, optional
        表示するアイコン（Font Awesomeクラス）
        
    Returns:
    --------
    bool
        dismissible=Trueの場合、アラートが閉じられたかどうか
    """
    return _create_alert_by_type(message, "warning", Colors.WARNING, "#FFF3E0", dismissible, icon)

def create_error_alert(message, dismissible=False, icon=None):
    """
    エラーアラートを作成します。
    
    Parameters:
    -----------
    message : str
        アラートに表示するメッセージ
    dismissible : bool, optional
        閉じるボタンを表示するかどうか
    icon : str, optional
        表示するアイコン（Font Awesomeクラス）
        
    Returns:
    --------
    bool
        dismissible=Trueの場合、アラートが閉じられたかどうか
    """
    return _create_alert_by_type(message, "error", Colors.ERROR, "#FFEBEE", dismissible, icon)

def _create_alert_by_type(message, alert_type, color, bg_color, dismissible=False, icon=None):
    """
    指定されたタイプのアラートを作成します。
    
    Parameters:
    -----------
    message : str
        アラートに表示するメッセージ
    alert_type : str
        アラートのタイプ
    color : str
        アラートの色
    bg_color : str
        アラートの背景色
    dismissible : bool, optional
        閉じるボタンを表示するかどうか
    icon : str, optional
        表示するアイコン（Font Awesomeクラス）
        
    Returns:
    --------
    bool
        dismissible=Trueの場合、アラートが閉じられたかどうか
    """
    # アイコンのデフォルト設定
    if icon is None:
        if alert_type == "info":
            icon = "fas fa-info-circle"
        elif alert_type == "success":
            icon = "fas fa-check-circle"
        elif alert_type == "warning":
            icon = "fas fa-exclamation-triangle"
        elif alert_type == "error":
            icon = "fas fa-times-circle"
    
    # セッション状態の処理
    alert_key = f"alert_{alert_type}_{message}"
    if alert_key not in st.session_state:
        st.session_state[alert_key] = True
    
    # 閉じられていない場合のみ表示
    if st.session_state[alert_key]:
        icon_html = f'<i class="{icon}" style="margin-right: {Spacing.S}; color: {color};"></i>' if icon else ''
        close_button = ''
        
        if dismissible:
            close_button = f"""
            <div style="position: absolute; top: {Spacing.S}; right: {Spacing.S}; cursor: pointer;"
                 onclick="this.parentElement.style.display='none'; 
                         fetch('/_stcore/component_communication',
                         {{method: 'POST', 
                           headers: {{'Content-Type': 'application/json'}}, 
                           body: JSON.stringify({{id: '{alert_key}', value: false}})
                         }});">
                <i class="fas fa-times" style="color: {Colors.DARK_1};"></i>
            </div>
            """
        
        alert_html = f"""
        <div style="
            position: relative;
            background-color: {bg_color};
            border-left: 4px solid {color};
            border-radius: {BorderRadius.SMALL};
            padding: {Spacing.S} {Spacing.M};
            margin-bottom: {Spacing.M};
            display: flex;
            align-items: center;
        ">
            {icon_html}
            <div style="font-size: {FontSizes.BODY}; line-height: 1.5; flex-grow: 1;">{message}</div>
            {close_button}
        </div>
        """
        
        st.markdown(alert_html, unsafe_allow_html=True)
    
    return not st.session_state[alert_key]
