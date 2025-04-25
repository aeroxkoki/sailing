# -*- coding: utf-8 -*-
"""
sailing_data_processor.reporting.elements.timeline.event_timeline

¤ÙóÈ¿¤àé¤ó¯é¹’Ğ›Y‹â¸åüëgY
»üêó°-n¤ÙóÈ¿Ã¯¸ã¤ÖŞü¯Ş*ji	’B“ø
kh:W~Y
"""

from typing import Dict, List, Any, Optional, Union, Tuple
import json
import uuid
from datetime import datetime, timedelta

from sailing_data_processor.reporting.elements.base_element import BaseElement
from sailing_data_processor.reporting.templates.template_model import ElementType, ElementModel


class EventTimeline(BaseElement):
    """
    ¤ÙóÈ¿¤àé¤ó¯é¹
    
    »üêó°-n¤ÙóÈ¿Ã¯¸ã¤ÖŞü¯Ş*ji	’
    B“ø
kh:Y‹¿¤àé¤ó’Ğ›W~Y
    """
    
    def __init__(self, model: Optional[ElementModel] = None, element_id=None, name="¤ÙóÈ¿¤àé¤ó", **kwargs):
        """
        
        
        Parameters
        ----------
        model : Optional[ElementModel], optional
             âÇë, by default None
        element_id : str, optional
             ID, by default None (êÕ)
        name : str, optional
             , by default "¤ÙóÈ¿¤àé¤ó"
        **kwargs : dict
            ]nÖn×íÑÆ£
        """
        # ÇÕ©ëÈg¿¤àé¤ó ¿¤×’-š
        if model is None and 'element_type' not in kwargs:
            kwargs['element_type'] = ElementType.TIMELINE
        
        if element_id is None:
            element_id = f"event_timeline_{uuid.uuid4().hex[:8]}"
        
        super().__init__(model, element_id=element_id, name=name, **kwargs)
        
        # ¤ÙóÈÇü¿
        self._events = []
        
        # h:ª×·çó
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
            "time_format": kwargs.get("time_format", "HH:mm:ss"),
        }
        
        # ª×·çó’×íÑÆ£k-š
        for key, value in self._options.items():
            self.set_property(key, value)
        
        # ¤ÙóÈ¿¤×nš©hr
        self._event_types = {
            "tack": {"color": "#FF5722", "symbol": "ò", "label": "¿Ã¯"},
            "jibe": {"color": "#2196F3", "symbol": "ó", "label": "¸ã¤Ö"},
            "mark_rounding": {"color": "#4CAF50", "symbol": "Î", "label": "Şü¯Ş*"},
            "start": {"color": "#FFC107", "symbol": "¶", "label": "¹¿üÈ"},
            "finish": {"color": "#9C27B0", "symbol": " ", "label": "Õ£ËÃ·å"},
            "custom": {"color": "#607D8B", "symbol": "", "label": "«¹¿à"}
        }
        
        # ¤ÙóÈ¿¤×hÕ£üëÉnşÜ
        self.set_property("event_type_fields", {
            "tack": "is_tack",
            "jibe": "is_jibe",
            "mark_rounding": "is_mark_rounding",
            "start": "is_start",
            "finish": "is_finish"
        })
        
        # s0Å1nÕ£üëÉ
        self.set_property("detail_fields", [
            "speed", "wind_speed", "wind_direction", "heading"
        ])
        
        # Çü¿½ü¹
        self.set_property("data_source", kwargs.get("data_source", ""))
    
    def add_event(self, timestamp, event_type, label=None, details=None, **kwargs):
        """
        ¤ÙóÈ’ı 
        
        Parameters
        ----------
        timestamp : str or datetime
            ¤ÙóÈnzB;
        event_type : str
            ¤ÙóÈ¿¤× ("tack", "jibe", "mark_rounding", "start", "finish", "custom")
        label : str, optional
            ¤ÙóÈnéÙë, by default None
        details : dict, optional
            ¤ÙóÈns0Å1, by default None
        **kwargs : dict
            ]nÖn¤ÙóÈ^'
            
        Returns
        -------
        dict
            ı UŒ_¤ÙóÈÅ1
        """
        # ¿¤à¹¿ó×nb’Á§Ã¯
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp)
            except (ValueError, TypeError):
                try:
                    timestamp = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S")
                except (ValueError, TypeError):
                    raise ValueError(f"!¹j¿¤à¹¿ó×b: {timestamp}")
        
        if not isinstance(timestamp, datetime):
            raise TypeError("¿¤à¹¿ó×odatetimeªÖ¸§¯È~_oISObn‡WgB‹ÅLBŠ~Y")
        
        # ¤ÙóÈ¿¤×n<
        if event_type not in self._event_types and event_type != "custom":
            raise ValueError(f"!¹j¤ÙóÈ¿¤×: {event_type}")
        
        # ¤ÙóÈÅ1’\
        event = {
            "id": str(uuid.uuid4()),
            "timestamp": timestamp.isoformat(),
            "type": event_type,
            "label": label or self._event_types[event_type]["label"],
            "symbol": self._event_types[event_type]["symbol"],
            "color": self._event_types[event_type]["color"],
            "details": details or {}
        }
        
        # ]nÖn^'’ı 
        for key, value in kwargs.items():
            if key not in event:
                event[key] = value
        
        # ¤ÙóÈ’ı 
        self._events.append(event)
        
        return event
    
    def clear_events(self):
        """¤ÙóÈ’¯ê¢"""
        self._events = []
    
    def set_property(self, key: str, value: Any) -> None:
        """
        ×íÑÆ£’-š
        
        Parameters
        ----------
        key : str
            ×íÑÆ£
        value : Any
            ×íÑÆ£$
        """
        super().set_property(key, value)
        
        # _options‚ô°
        if key in self._options:
            self._options[key] = value
    
    def get_property(self, key: str, default: Any = None) -> Any:
        """
        ×íÑÆ£’Ö—
        
        Parameters
        ----------
        key : str
            ×íÑÆ£
        default : Any, optional
            ÇÕ©ëÈ$, by default None
            
        Returns
        -------
        Any
            ×íÑÆ£$
        """
        return super().get_property(key, default)
