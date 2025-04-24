# -*- coding: utf-8 -*-
"""
ui.integrated.components.dashboard.widgets.base_widget

ダッシュボードウィジェットの基本クラス
"""

import streamlit as st
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple, List


class BaseWidget(ABC):
    """
    ダッシュボードウィジェットの基本抽象クラス。
    すべてのウィジェットはこのクラスを継承する必要があります。
    """

    def __init__(self, widget_id: str, title: str, description: str = "", 
                 width: int = 1, height: int = 1, config: Dict[str, Any] = None):
        """
        ウィジェットの初期化
        
        Args:
            widget_id: ウィジェットの一意のID
            title: ウィジェットのタイトル
            description: ウィジェットの説明
            width: ウィジェットの幅（グリッド単位、1～3）
            height: ウィジェットの高さ（グリッド単位、1～3）
            config: ウィジェットの追加構成
        """
        self.widget_id = widget_id
        self.title = title
        self.description = description
        self.width = min(max(width, 1), 3)  # 1から3の間に制限
        self.height = min(max(height, 1), 3)  # 1から3の間に制限
        self.config = config or {}
        self.visible = True

    @abstractmethod
    def render(self, session_data: Dict[str, Any] = None) -> None:
        """
        ウィジェットを描画する抽象メソッド。
        すべてのサブクラスで実装する必要があります。
        
        Args:
            session_data: 現在のセッションデータ
        """
        pass

    def get_config(self) -> Dict[str, Any]:
        """
        ウィジェットの構成を取得
        
        Returns:
            ウィジェットの構成情報
        """
        return {
            "widget_id": self.widget_id,
            "title": self.title,
            "description": self.description,
            "width": self.width,
            "height": self.height,
            "config": self.config,
            "visible": self.visible,
            "type": self.__class__.__name__
        }

    def update_config(self, config: Dict[str, Any]) -> None:
        """
        ウィジェットの構成を更新
        
        Args:
            config: 新しい構成情報
        """
        if "title" in config:
            self.title = config["title"]
        if "description" in config:
            self.description = config["description"]
        if "width" in config:
            self.width = min(max(config["width"], 1), 3)
        if "height" in config:
            self.height = min(max(config["height"], 1), 3)
        if "config" in config:
            self.config.update(config["config"])
        if "visible" in config:
            self.visible = config["visible"]

    def render_header(self) -> None:
        """
        ウィジェットヘッダーを描画
        """
        st.markdown(f"### {self.title}")
        if self.description:
            st.markdown(f"<small>{self.description}</small>", unsafe_allow_html=True)
        st.markdown("---")

    def render_placeholder(self) -> None:
        """
        データがない場合のプレースホルダーを描画
        """
        st.info("このウィジェットに表示するデータがありません。")

    def render_error(self, error_message: str) -> None:
        """
        エラーメッセージを描画
        
        Args:
            error_message: 表示するエラーメッセージ
        """
        st.error(f"エラー: {error_message}")

    def render_settings(self) -> Dict[str, Any]:
        """
        ウィジェット設定UIを描画し、新しい設定を返す
        
        Returns:
            更新された設定
        """
        st.subheader(f"{self.title}の設定")
        
        new_title = st.text_input("タイトル", self.title)
        new_description = st.text_area("説明", self.description)
        new_width = st.slider("幅", 1, 3, self.width)
        new_height = st.slider("高さ", 1, 3, self.height)
        
        return {
            "title": new_title,
            "description": new_description,
            "width": new_width,
            "height": new_height
        }

    @classmethod
    def get_widget_info(cls) -> Dict[str, Any]:
        """
        ウィジェットの静的情報を取得
        
        Returns:
            ウィジェット情報（名前、説明、カテゴリなど）
        """
        return {
            "name": cls.__name__,
            "description": cls.__doc__.strip() if cls.__doc__ else "",
            "category": "一般"
        }
