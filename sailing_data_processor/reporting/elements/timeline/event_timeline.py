# -*- coding: utf-8 -*-
"""
Module for data connector between map layers and data sources.
This module provides functions for binding and data transformation between layers and data sources.
"""

from typing import Dict, List, Any, Optional, Union, Tuple
import json
import uuid
from datetime import datetime, timedelta

from sailing_data_processor.reporting.elements.base_element import BaseElement
from sailing_data_processor.reporting.templates.template_model import ElementType, ElementModel


class EventTimeline(BaseElement):
    """
    ���ȿ�����
    
    ����-n�����ï�������*ji	�
    B��
kh:Y������ЛW~Y
    """
    
    def __init__(self, model: Optional[ElementModel] = None, element_id=None, name="���ȿ����", **kwargs):
        """
        
        
        Parameters
        ----------
        model : Optional[ElementModel], optional
            � ���, by default None
        element_id : str, optional
            � ID, by default None (��)
        name : str, optional
            � 
, by default "���ȿ����"
        **kwargs : dict
            ]n�n���ƣ
        """
        # �թ��g����� ��ג-�
        if model is None and 'element_type' not in kwargs:
            kwargs['element_type'] = ElementType.TIMELINE
        
        if element_id is None:
            element_id = f"event_timeline_{uuid.uuid4().hex[:8]}"
        
        super().__init__(model, element_id=element_id, name=name, **kwargs)
        
        # �������
        self._events = []
        
        # h:�׷��
        self._options = {}
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
 "show_tacks": kwargs.get("show_tacks", True),
            "show_jibes": kwargs.get("show_jibes", True),
            "show_marks": kwargs.get("show_marks", True),
            "show_custom": kwargs.get("show_custom", True),
            "event_height": kwargs.get("event_height", 20),
            "group_events": kwargs.get("group_events", True),
            "timeline_height": kwargs.get("timeline_height", 150),
            "handle_overflow": kwargs.get("handle_overflow", True),
            "tooltip_placement": kwargs.get("tooltip_placement", "top"),
            "time_format": kwargs.get("time_format", "HH:mm:ss"),}
        }
        
        # �׷�����ƣk-�
        for key, value in self._options.items():
            self.set_property(key, value)
        
        # ���ȿ��n��hr
        self._event_types = {
            "tack": "color": "#FF5722", "symbol": "�", "label": "�ï"},
            "jibe": {"color": "#2196F3", "symbol": "�", "label": "���"},
            "mark_rounding": {"color": "#4CAF50", "symbol": "�", "label": "����*"},
            "start": {"color": "#FFC107", "symbol": "�", "label": "����"},
            "finish": {"color": "#9C27B0", "symbol": "�", "label": "գ�÷�"},
            "custom": {"color": "#607D8B", "symbol": "", "label": "����"}
            }
            }
            }
 {
            "tack": "color": "#FF5722", "symbol": "�", "label": "�ï"},
            "jibe": {"color": "#2196F3", "symbol": "�", "label": "���"},
            "mark_rounding": {"color": "#4CAF50", "symbol": "�", "label": "����*"},
            "start": {"color": "#FFC107", "symbol": "�", "label": "����"},
            "finish": {"color": "#9C27B0", "symbol": "�", "label": "գ�÷�"},
            "custom": {"color": "#607D8B", "symbol": "", "label": "����"}}
        }
            }
            }
            }
        
        # ���ȿ��hգ���n��
        self.set_property("event_type_fields", {
            "tack": "is_tack",
            "jibe": "is_jibe",
            "mark_rounding": "is_mark_rounding",
            "start": "is_start",
            "finish": "is_finish"
 "tack": "is_tack",
            "jibe": "is_jibe",
            "mark_rounding": "is_mark_rounding",
            "start": "is_start",
            "finish": "is_finish"}
        })
        
        # s0�1nգ���
        self.set_property("detail_fields", [
            "speed", "wind_speed", "wind_direction", "heading"
        ])
        
        # ������
        self.set_property("data_source", kwargs.get("data_source", ""))
    
    def add_event(self, timestamp, event_type, label=None, details=None, **kwargs):
        """
        ���Ȓ��
        
        Parameters
        ----------
        timestamp : str or datetime
            ����nzB;
        event_type : str
            ���ȿ�� ("tack", "jibe", "mark_rounding", "start", "finish", "custom")
        label : str, optional
            ����n���, by default None
        details : dict, optional
            ����ns0�1, by default None
        **kwargs : dict
            ]n�n����^'
            
        Returns
        -------
        dict
            ��U�_�����1
        """
        # ��๿��nb���ï
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp)
            except (ValueError, TypeError):
                try:
                    timestamp = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S")
                except (ValueError, TypeError):
                    raise ValueError(f"!�j��๿��b: {timestamp}")
                    }
        
        if not isinstance(timestamp, datetime):
            raise TypeError("��๿��odatetime�ָ���~_oISObn�WgB�ŁLB�~Y")
        
        # ���ȿ��n<
        if event_type not in self._event_types and event_type != "custom":
            raise ValueError(f"!�j���ȿ��: {event_type}")
            }
        
        # �����1�\
        event = {
            "id": str(uuid.uuid4()),
            "timestamp": timestamp.isoformat(),
            "type": event_type,
            "label": label or self._event_types[event_type]["label"],
            "symbol": self._event_types[event_type]["symbol"],
            "color": self._event_types[event_type]["color"],
            "details": details or }
 {
            "id": str(uuid.uuid4()),
            "timestamp": timestamp.isoformat(),
            "type": event_type,
            "label": label or self._event_types[event_type]["label"],
            "symbol": self._event_types[event_type]["symbol"],
            "color": self._event_types[event_type]["color"],
            "details": details or }}
        }
        
        # ]n�n^'���
        for key, value in kwargs.items():
            if key not in event:
                event[key] = value
        
        # ���Ȓ��
        self._events.append(event)
        
        return event
    
    def clear_events(self):
        """���Ȓ��"""
        self._events = []
    
    def set_property(self, key: str, value: Any) -> None:
        """
        ���ƣ�-�
        
        Parameters
        ----------
        key : str
            ���ƣ
        value : Any
            ���ƣ$
        """
        super().set_property(key, value)
        
        # _options���
        if key in self._options:
            self._options[key] = value
    
    def get_property(self, key: str, default: Any = None) -> Any:
        """
        ���ƣ�֗
        
        Parameters
        ----------
        key : str
            ���ƣ
        default : Any, optional
            �թ��$, by default None
            
        Returns
        -------
        Any
            ���ƣ$
        """
        return super().get_property(key, default)
