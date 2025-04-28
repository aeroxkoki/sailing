# -*- coding: utf-8 -*-
"""
Module for event timeline visualization.
This module provides a timeline component for displaying sailing events over time.
"""

from typing import Dict, List, Any, Optional, Union, Tuple
import json
import uuid
from datetime import datetime, timedelta

from sailing_data_processor.reporting.elements.base_element import BaseElement
from sailing_data_processor.reporting.templates.template_model import ElementType, ElementModel


class EventTimeline(BaseElement):
    """
    イベントタイムライン
    
    セーリング中の操船イベント（タック、ジャイブ、マーク回航など）を
    時系列で表示するためのタイムラインコンポーネント
    """
    
    def __init__(self, model: Optional[ElementModel] = None, element_id=None, name="イベントタイムライン", **kwargs):
        """
        初期化
        
        Parameters
        ----------
        model : Optional[ElementModel], optional
            要素モデル, by default None
        element_id : str, optional
            要素ID, by default None (自動生成)
        name : str, optional
            要素名, by default "イベントタイムライン"
        **kwargs : dict
            その他のプロパティ
        """
        # デフォルトタイプが設定されていない場合、設定
        if model is None and 'element_type' not in kwargs:
            kwargs['element_type'] = ElementType.TIMELINE
        
        if element_id is None:
            element_id = f"event_timeline_{uuid.uuid4().hex[:8]}"
        
        super().__init__(model, element_id=element_id, name=name, **kwargs)
        
        # イベントリスト
        self._events = []
        
        # デフォルト設定
        self._options = {
            "show_tacks": kwargs.get("show_tacks", True),
            "show_jibes": kwargs.get("show_jibes", True),
            "show_marks": kwargs.get("show_marks", True),
            "show_custom": kwargs.get("show_custom", True),
            "event_height": kwargs.get("event_height", 20),
            "group_events": kwargs.get("group_events", True),
            "timeline_height": kwargs.get("timeline_height", 150),
            "handle_overflow": kwargs.get("handle_overflow", True),
            "tooltip_placement": kwargs.get("tooltip_placement", "top"),
            "time_format": kwargs.get("time_format", "HH:mm:ss")
        }
        
        # デフォルトプロパティを設定
        for key, value in self._options.items():
            self.set_property(key, value)
        
        # イベントタイプの定義
        self._event_types = {
            "tack": {"color": "#FF5722", "symbol": "T", "label": "タック"},
            "jibe": {"color": "#2196F3", "symbol": "J", "label": "ジャイブ"},
            "mark_rounding": {"color": "#4CAF50", "symbol": "M", "label": "マーク回航"},
            "start": {"color": "#FFC107", "symbol": "S", "label": "スタート"},
            "finish": {"color": "#9C27B0", "symbol": "F", "label": "フィニッシュ"},
            "custom": {"color": "#607D8B", "symbol": "C", "label": "カスタム"}
        }
        
        # イベントタイプとフィールドの対応
        self.set_property("event_type_fields", {
            "tack": "is_tack",
            "jibe": "is_jibe",
            "mark_rounding": "is_mark_rounding",
            "start": "is_start",
            "finish": "is_finish"
        })
        
        # 詳細情報のフィールド
        self.set_property("detail_fields", [
            "speed", "wind_speed", "wind_direction", "heading"
        ])
        
        # データソース
        self.set_property("data_source", kwargs.get("data_source", ""))
    
    def add_event(self, timestamp, event_type, label=None, details=None, **kwargs):
        """
        イベント追加
        
        Parameters
        ----------
        timestamp : str or datetime
            イベントの時刻
        event_type : str
            イベントタイプ ("tack", "jibe", "mark_rounding", "start", "finish", "custom")
        label : str, optional
            イベントのラベル, by default None
        details : dict, optional
            イベントの詳細情報, by default None
        **kwargs : dict
            その他のイベント属性
            
        Returns
        -------
        dict
            追加されたイベント情報
        """
        # タイムスタンプの形式を確認
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp)
            except (ValueError, TypeError):
                try:
                    timestamp = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S")
                except (ValueError, TypeError):
                    raise ValueError(f"無効なタイムスタンプ形式: {timestamp}")
        
        if not isinstance(timestamp, datetime):
            raise TypeError("タイムスタンプはdatetime型である必要があり、または有効なISO形式の文字列である必要があります")
        
        # イベントタイプの確認
        if event_type not in self._event_types and event_type != "custom":
            raise ValueError(f"無効なイベントタイプ: {event_type}")
        
        # イベント情報を作成
        event = {
            "id": str(uuid.uuid4()),
            "timestamp": timestamp.isoformat(),
            "type": event_type,
            "label": label or self._event_types[event_type]["label"],
            "symbol": self._event_types[event_type]["symbol"],
            "color": self._event_types[event_type]["color"],
            "details": details or {}
        }
        
        # その他の属性を追加
        for key, value in kwargs.items():
            if key not in event:
                event[key] = value
        
        # イベント追加
        self._events.append(event)
        
        return event
    
    def clear_events(self):
        """イベントをクリア"""
        self._events = []
    
    def set_property(self, key: str, value: Any) -> None:
        """
        プロパティを設定
        
        Parameters
        ----------
        key : str
            プロパティキー
        value : Any
            プロパティ値
        """
        super().set_property(key, value)
        
        # _optionsも更新
        if key in self._options:
            self._options[key] = value
    
    def get_property(self, key: str, default: Any = None) -> Any:
        """
        プロパティを取得
        
        Parameters
        ----------
        key : str
            プロパティキー
        default : Any, optional
            デフォルト値, by default None
            
        Returns
        -------
        Any
            プロパティ値
        """
        return super().get_property(key, default)
