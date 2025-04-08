"""
ui.components.common.alerts

アラート表示用のコンポーネント
"""

import streamlit as st
from typing import Literal, Optional


def alert(message: str, type: Literal["info", "success", "warning", "error"] = "info", icon: bool = True) -> None:
    """
    アラートメッセージを表示する
    
    Parameters
    ----------
    message : str
        表示するメッセージ
    type : Literal["info", "success", "warning", "error"], optional
        アラートの種類, by default "info"
    icon : bool, optional
        アイコンを表示するかどうか, by default True
    """
    if type == "info":
        st.info(message, icon=icon)
    elif type == "success":
        st.success(message, icon=icon)
    elif type == "warning":
        st.warning(message, icon=icon)
    elif type == "error":
        st.error(message, icon=icon)
