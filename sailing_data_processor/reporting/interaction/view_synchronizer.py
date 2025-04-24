# -*- coding: utf-8 -*-
"""
sailing_data_processor.reporting.interaction.view_synchronizer

����������鹒ЛY�����gY
��������������]n�n���������ȓn��W~Y
"""

from typing import Dict, List, Any, Optional, Union, Tuple, Set, Callable
import logging

logger = logging.getLogger(__name__)

class ViewSynchronizer:
    """
    �����������
    
    ��������������]n�n���������ȓn
    ��W~Y
    """
    
    def __init__(self):
        """"""
        self._views = {}  # id -> view
        self._contexts = {}  # id -> context
        self._connections = {}  # (source_id, target_id) -> connection_info
        
        # ��������
        self._event_handlers = {}
    
    def register_view(self, view_id: str, view_object: Any, view_type: Optional[str] = None) -> None:
        """
        ����{2
        
        Parameters
        ----------
        view_id : str
            ���nID
        view_object : Any
            ����ָ���
        view_type : Optional[str], optional
            ���n.^, by default None
        """
        self._views[view_id] = {
            "object": view_object,
            "type": view_type or view_object.__class__.__name__
        }
        self._contexts[view_id] = {}
    
    def unregister_view(self, view_id: str) -> bool:
        """
        ���n{2��d
        
        Parameters
        ----------
        view_id : str
            ���nID
            
        Returns
        -------
        bool
            �dk�W_4oTrue
        """
        if view_id in self._views:
            del self._views[view_id]
        else:
            return False
        
        if view_id in self._contexts:
            del self._contexts[view_id]
        
        # �#Y����Jd
        self._connections = {k: v for k, v in self._connections.items() 
                            if k[0] != view_id and k[1] != view_id}
        
        return True
    
    def get_registered_views(self) -> List[str]:
        """
        {2U�fD����nID�Ȓ֗
        
        Returns
        -------
        List[str]
            ���IDn��
        """
        return list(self._views.keys())
    
    def connect_views(self, source_id: str, target_id: str, sync_props: Optional[List[str]] = None,
                     bidirectional: bool = False) -> bool:
        """
        ����n���-�
        
        Parameters
        ----------
        source_id : str
            ������ID
        target_id : str
            ��������ID
        sync_props : Optional[List[str]], optional
            Y����ƣ��, by default None
        bidirectional : bool, optional
            ̹Y�KiFK, by default False
            
        Returns
        -------
        bool
            ��k�W_4oTrue
        """
        if source_id not in self._views or target_id not in self._views:
            return False
        
        default_props = ["time", "selection", "zoom", "center"]
        sync_properties = sync_props or default_props
        
        self._connections[(source_id, target_id)] = {
            "sync_properties": sync_properties,
            "active": True
        }
        
        # ̹n4o�n�����
        if bidirectional:
            self._connections[(target_id, source_id)] = {
                "sync_properties": sync_properties,
                "active": True
            }
        
        return True
    
    def disconnect_views(self, source_id: str, target_id: str) -> bool:
        """
        ����n����d
        
        Parameters
        ----------
        source_id : str
            ������ID
        target_id : str
            ��������ID
            
        Returns
        -------
        bool
            �dk�W_4oTrue
        """
        if (source_id, target_id) in self._connections:
            del self._connections[(source_id, target_id)]
            return True
        
        return False
    
    def get_connections(self) -> Dict[Tuple[str, str], Dict[str, Any]]:
        """
        Yyfn���1�֗
        
        Returns
        -------
        Dict[Tuple[str, str], Dict[str, Any]]
            ���1n��
        """
        return self._connections.copy()
    
    def set_connection_active(self, source_id: str, target_id: str, active: bool) -> bool:
        """
        ��n��ƣֶK�-�
        
        Parameters
        ----------
        source_id : str
            ������ID
        target_id : str
            ��������ID
        active : bool
            ��ƣ�kY�KiFK
            
        Returns
        -------
        bool
            -�k�W_4oTrue
        """
        if (source_id, target_id) in self._connections:
            self._connections[(source_id, target_id)]["active"] = active
            return True
        
        return False
    
    def update_view_context(self, view_id: str, context_update: Dict[str, Any]) -> bool:
        """
        �����ƭ�Ȓ��
        
        Parameters
        ----------
        view_id : str
            ���ID
        context_update : Dict[str, Any]
            ��Y���ƭ���1
            
        Returns
        -------
        bool
            ��k�W_4oTrue
        """
        if view_id not in self._contexts:
            return False
        
        # ��ƭ����
        self._contexts[view_id].update(context_update)
        
        # ��Hk	���
        self._propagate_context_changes(view_id, context_update)
        
        return True
    
    def get_view_context(self, view_id: str) -> Optional[Dict[str, Any]]:
        """
        �����ƭ�Ȓ֗
        
        Parameters
        ----------
        view_id : str
            ���ID
            
        Returns
        -------
        Optional[Dict[str, Any]]
            ��ƭ���1
        """
        return self._contexts.get(view_id, {}).copy() if view_id in self._contexts else None
    
    def add_event_handler(self, event_type: str, handler: Callable[[str, Any], None]) -> None:
        """
        ����������
        
        Parameters
        ----------
        event_type : str
            ���ȿ�� ("time_change", "selection_change", etc.)
        handler : Callable[[str, Any], None]
            ����p (view_id, value) �pk֋
        """
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        
        self._event_handlers[event_type].append(handler)
    
    def remove_event_handler(self, event_type: str, handler: Callable[[str, Any], None]) -> bool:
        """
        ��������Jd
        
        Parameters
        ----------
        event_type : str
            ���ȿ��
        handler : Callable[[str, Any], None]
            JdY�����p
            
        Returns
        -------
        bool
            Jdk�W_4oTrue
        """
        if event_type in self._event_handlers and handler in self._event_handlers[event_type]:
            self._event_handlers[event_type].remove(handler)
            return True
        
        return False
    
    def _propagate_context_changes(self, source_id: str, changes: Dict[str, Any]) -> None:
        """
        ��ƭ��	����Hk�
        
        Parameters
        ----------
        source_id : str
            ������ID
        changes : Dict[str, Any]
            	�
        """
        # 	�n�����g2b	
        propagated = set()
        self._propagate_to_targets(source_id, changes, propagated)
    
    def _propagate_to_targets(self, source_id: str, changes: Dict[str, Any], 
                             propagated: Set[Tuple[str, str]]) -> None:
        """
        	����Hk�0�k�
        
        Parameters
        ----------
        source_id : str
            ������ID
        changes : Dict[str, Any]
            	�
        propagated : Set[Tuple[str, str]]
            �k�n��n���
        """
        for (src, tgt), conn_info in self._connections.items():
            # �k�n��o����
            if (src, tgt) in propagated:
                continue
                
            # ^��ƣ�~_o�an��o����
            if not conn_info["active"] or src != source_id:
                continue
                
            # Y����ƣ�գ���
            sync_props = conn_info["sync_properties"]
            filtered_changes = {k: v for k, v in changes.items() if k in sync_props}
            
            if filtered_changes:
                # ����k��
                propagated.add((src, tgt))
                
                # ��������n��ƭ�Ȓ��
                if tgt in self._contexts:
                    self._contexts[tgt].update(filtered_changes)
                
                # �����������
                self._update_target_view(tgt, filtered_changes)
                
                # 	���0�k�
                self._propagate_to_targets(tgt, filtered_changes, propagated)
    
    def _update_target_view(self, target_id: str, changes: Dict[str, Any]) -> None:
        """
        �����������
        
        Parameters
        ----------
        target_id : str
            ��������ID
        changes : Dict[str, Any]
            	�
        """
        target_view_info = self._views.get(target_id)
        if not target_view_info:
            return
            
        target_view = target_view_info["object"]
        
        # ������k�X_���
        try:
            for prop, value in changes.items():
                # time ���ƣn
                if prop == "time" and hasattr(target_view, "set_current_time"):
                    target_view.set_current_time(value)
                
                # selection ���ƣn
                elif prop == "selection" and hasattr(target_view, "set_selection"):
                    target_view.set_selection(value)
                
                # zoom ���ƣn
                elif prop == "zoom" and hasattr(target_view, "set_zoom"):
                    target_view.set_zoom(value)
                
                # center ���ƣn
                elif prop == "center" and hasattr(target_view, "set_center"):
                    if isinstance(value, (list, tuple)) and len(value) >= 2:
                        target_view.set_center(value[0], value[1])
                
                # ]n�n���ƣn
                elif hasattr(target_view, f"set_{prop}"):
                    getattr(target_view, f"set_{prop}")(value)
                
                # ��������n|s�W
                if prop in self._event_handlers:
                    for handler in self._event_handlers[prop]:
                        try:
                            handler(target_id, value)
                        except Exception as e:
                            logger.error(f"Error in event handler for {prop}: {e}")
        except Exception as e:
            logger.error(f"Error updating target view {target_id}: {e}")
    
    def reset(self) -> None:
        """����������"""
        self._views = {}
        self._contexts = {}
        self._connections = {}
        self._event_handlers = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        ��餺��j��k	�
        
        Returns
        -------
        Dict[str, Any]
            ��餺(n���
        """
        # ����1�ָ����gdO	
        views_info = {}
        for view_id, view_info in self._views.items():
            views_info[view_id] = {
                "type": view_info["type"]
            }
        
        # ���1
        connections = {}
        for (src, tgt), conn_info in self._connections.items():
            connections[f"{src}->{tgt}"] = {
                "source": src,
                "target": tgt,
                "sync_properties": conn_info["sync_properties"],
                "active": conn_info["active"]
            }
        
        return {
            "views": views_info,
            "contexts": self._contexts,
            "connections": connections
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], view_objects: Dict[str, Any]) -> 'ViewSynchronizer':
        """
        ��K���󹒩C
        
        Parameters
        ----------
        data : Dict[str, Any]
            ��餺U�_���
        view_objects : Dict[str, Any]
            ���IDh�ָ���n����
            
        Returns
        -------
        ViewSynchronizer
            �CU�_���
        """
        instance = cls()
        
        # ����{2
        for view_id, view_info in data.get("views", {}).items():
            if view_id in view_objects:
                instance.register_view(
                    view_id=view_id,
                    view_object=view_objects[view_id],
                    view_type=view_info.get("type")
                )
        
        # ��ƭ�Ȓ�C
        for view_id, context in data.get("contexts", {}).items():
            if view_id in instance._contexts:
                instance._contexts[view_id] = context.copy()
        
        # ����C
        for _, conn_info in data.get("connections", {}).items():
            source_id = conn_info.get("source")
            target_id = conn_info.get("target")
            if source_id in instance._views and target_id in instance._views:
                instance._connections[(source_id, target_id)] = {
                    "sync_properties": conn_info.get("sync_properties", ["time", "selection"]),
                    "active": conn_info.get("active", True)
                }
        
        return instance
