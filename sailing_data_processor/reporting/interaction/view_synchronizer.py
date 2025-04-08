"""
sailing_data_processor.reporting.interaction.view_synchronizer

ÓåüÞÍü¸ãü¯é¹’Ð›Y‹â¸åüëgY
ÞÃ×Óåü¿¤àé¤óÓåü]nÖnÓåü³óÝüÍóÈ“n’¡W~Y
"""

from typing import Dict, List, Any, Optional, Union, Tuple, Set, Callable
import logging

logger = logging.getLogger(__name__)

class ViewSynchronizer:
    """
    ÓåüÞÍü¸ãü¯é¹
    
    ÞÃ×Óåü¿¤àé¤óÓåü]nÖnÓåü³óÝüÍóÈ“n
    ’¡W~Y
    """
    
    def __init__(self):
        """"""
        self._views = {}  # id -> view
        self._contexts = {}  # id -> context
        self._connections = {}  # (source_id, target_id) -> connection_info
        
        # ¤ÙóÈÏóÉé
        self._event_handlers = {}
    
    def register_view(self, view_id: str, view_object: Any, view_type: Optional[str] = None) -> None:
        """
        Óåü’{2
        
        Parameters
        ----------
        view_id : str
            ÓåünID
        view_object : Any
            ÓåüªÖ¸§¯È
        view_type : Optional[str], optional
            Óåün.^, by default None
        """
        self._views[view_id] = {
            "object": view_object,
            "type": view_type or view_object.__class__.__name__
        }
        self._contexts[view_id] = {}
    
    def unregister_view(self, view_id: str) -> bool:
        """
        Óåün{2’ãd
        
        Parameters
        ----------
        view_id : str
            ÓåünID
            
        Returns
        -------
        bool
            ãdkŸW_4oTrue
        """
        if view_id in self._views:
            del self._views[view_id]
        else:
            return False
        
        if view_id in self._contexts:
            del self._contexts[view_id]
        
        # ¢#Y‹¥š’Jd
        self._connections = {k: v for k, v in self._connections.items() 
                            if k[0] != view_id and k[1] != view_id}
        
        return True
    
    def get_registered_views(self) -> List[str]:
        """
        {2UŒfD‹ÓåünIDê¹È’Ö—
        
        Returns
        -------
        List[str]
            ÓåüIDnê¹È
        """
        return list(self._views.keys())
    
    def connect_views(self, source_id: str, target_id: str, sync_props: Optional[List[str]] = None,
                     bidirectional: bool = False) -> bool:
        """
        Óåü“n¥š’-š
        
        Parameters
        ----------
        source_id : str
            ½ü¹ÓåüID
        target_id : str
            ¿ü²ÃÈÓåüID
        sync_props : Optional[List[str]], optional
            Y‹×íÑÆ£ê¹È, by default None
        bidirectional : bool, optional
            Ì¹Y‹KiFK, by default False
            
        Returns
        -------
        bool
            ¥škŸW_4oTrue
        """
        if source_id not in self._views or target_id not in self._views:
            return False
        
        default_props = ["time", "selection", "zoom", "center"]
        sync_properties = sync_props or default_props
        
        self._connections[(source_id, target_id)] = {
            "sync_properties": sync_properties,
            "active": True
        }
        
        # Ì¹n4o¹n¥š‚ý 
        if bidirectional:
            self._connections[(target_id, source_id)] = {
                "sync_properties": sync_properties,
                "active": True
            }
        
        return True
    
    def disconnect_views(self, source_id: str, target_id: str) -> bool:
        """
        Óåü“n¥š’ãd
        
        Parameters
        ----------
        source_id : str
            ½ü¹ÓåüID
        target_id : str
            ¿ü²ÃÈÓåüID
            
        Returns
        -------
        bool
            ãdkŸW_4oTrue
        """
        if (source_id, target_id) in self._connections:
            del self._connections[(source_id, target_id)]
            return True
        
        return False
    
    def get_connections(self) -> Dict[Tuple[str, str], Dict[str, Any]]:
        """
        Yyfn¥šÅ1’Ö—
        
        Returns
        -------
        Dict[Tuple[str, str], Dict[str, Any]]
            ¥šÅ1nžø
        """
        return self._connections.copy()
    
    def set_connection_active(self, source_id: str, target_id: str, active: bool) -> bool:
        """
        ¥šn¢¯Æ£Ö¶K’-š
        
        Parameters
        ----------
        source_id : str
            ½ü¹ÓåüID
        target_id : str
            ¿ü²ÃÈÓåüID
        active : bool
            ¢¯Æ£ÖkY‹KiFK
            
        Returns
        -------
        bool
            -škŸW_4oTrue
        """
        if (source_id, target_id) in self._connections:
            self._connections[(source_id, target_id)]["active"] = active
            return True
        
        return False
    
    def update_view_context(self, view_id: str, context_update: Dict[str, Any]) -> bool:
        """
        Óåü³óÆ­¹È’ô°
        
        Parameters
        ----------
        view_id : str
            ÓåüID
        context_update : Dict[str, Any]
            ô°Y‹³óÆ­¹ÈÅ1
            
        Returns
        -------
        bool
            ô°kŸW_4oTrue
        """
        if view_id not in self._contexts:
            return False
        
        # ³óÆ­¹Èô°
        self._contexts[view_id].update(context_update)
        
        # ¥šHk	ô’­
        self._propagate_context_changes(view_id, context_update)
        
        return True
    
    def get_view_context(self, view_id: str) -> Optional[Dict[str, Any]]:
        """
        Óåü³óÆ­¹È’Ö—
        
        Parameters
        ----------
        view_id : str
            ÓåüID
            
        Returns
        -------
        Optional[Dict[str, Any]]
            ³óÆ­¹ÈÅ1
        """
        return self._contexts.get(view_id, {}).copy() if view_id in self._contexts else None
    
    def add_event_handler(self, event_type: str, handler: Callable[[str, Any], None]) -> None:
        """
        ¤ÙóÈÏóÉé’ý 
        
        Parameters
        ----------
        event_type : str
            ¤ÙóÈ¿¤× ("time_change", "selection_change", etc.)
        handler : Callable[[str, Any], None]
            ÏóÉé¢p (view_id, value) ’pkÖ‹
        """
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        
        self._event_handlers[event_type].append(handler)
    
    def remove_event_handler(self, event_type: str, handler: Callable[[str, Any], None]) -> bool:
        """
        ¤ÙóÈÏóÉé’Jd
        
        Parameters
        ----------
        event_type : str
            ¤ÙóÈ¿¤×
        handler : Callable[[str, Any], None]
            JdY‹ÏóÉé¢p
            
        Returns
        -------
        bool
            JdkŸW_4oTrue
        """
        if event_type in self._event_handlers and handler in self._event_handlers[event_type]:
            self._event_handlers[event_type].remove(handler)
            return True
        
        return False
    
    def _propagate_context_changes(self, source_id: str, changes: Dict[str, Any]) -> None:
        """
        ³óÆ­¹È	ô’¥šHk­
        
        Parameters
        ----------
        source_id : str
            ½ü¹ÓåüID
        changes : Dict[str, Any]
            	ô…¹
        """
        # 	ônýáª°Âg2b	
        propagated = set()
        self._propagate_to_targets(source_id, changes, propagated)
    
    def _propagate_to_targets(self, source_id: str, changes: Dict[str, Any], 
                             propagated: Set[Tuple[str, str]]) -> None:
        """
        	ô’¥šHk0„k­
        
        Parameters
        ----------
        source_id : str
            ½ü¹ÓåüID
        changes : Dict[str, Any]
            	ô…¹
        propagated : Set[Tuple[str, str]]
            âk­n¥šn»ÃÈ
        """
        for (src, tgt), conn_info in self._connections.items():
            # âkæn¥šo¹­Ã×
            if (src, tgt) in propagated:
                continue
                
            # ^¢¯Æ£Ö~_oþan¥šo¹­Ã×
            if not conn_info["active"] or src != source_id:
                continue
                
            # Y‹×íÑÆ£’Õ£ë¿êó°
            sync_props = conn_info["sync_properties"]
            filtered_changes = {k: v for k, v in changes.items() if k in sync_props}
            
            if filtered_changes:
                # ¥š’æký 
                propagated.add((src, tgt))
                
                # ¿ü²ÃÈÓåün³óÆ­¹È’ô°
                if tgt in self._contexts:
                    self._contexts[tgt].update(filtered_changes)
                
                # ¿ü²ÃÈÓåü’ô°
                self._update_target_view(tgt, filtered_changes)
                
                # 	ô’0„k­
                self._propagate_to_targets(tgt, filtered_changes, propagated)
    
    def _update_target_view(self, target_id: str, changes: Dict[str, Any]) -> None:
        """
        ¿ü²ÃÈÓåü’ô°
        
        Parameters
        ----------
        target_id : str
            ¿ü²ÃÈÓåüID
        changes : Dict[str, Any]
            	ô…¹
        """
        target_view_info = self._views.get(target_id)
        if not target_view_info:
            return
            
        target_view = target_view_info["object"]
        
        # Óåü¿¤×kÜX_ô°æ
        try:
            for prop, value in changes.items():
                # time ×íÑÆ£n
                if prop == "time" and hasattr(target_view, "set_current_time"):
                    target_view.set_current_time(value)
                
                # selection ×íÑÆ£n
                elif prop == "selection" and hasattr(target_view, "set_selection"):
                    target_view.set_selection(value)
                
                # zoom ×íÑÆ£n
                elif prop == "zoom" and hasattr(target_view, "set_zoom"):
                    target_view.set_zoom(value)
                
                # center ×íÑÆ£n
                elif prop == "center" and hasattr(target_view, "set_center"):
                    if isinstance(value, (list, tuple)) and len(value) >= 2:
                        target_view.set_center(value[0], value[1])
                
                # ]nÖn×íÑÆ£n
                elif hasattr(target_view, f"set_{prop}"):
                    getattr(target_view, f"set_{prop}")(value)
                
                # ¤ÙóÈÏóÉén|súW
                if prop in self._event_handlers:
                    for handler in self._event_handlers[prop]:
                        try:
                            handler(target_id, value)
                        except Exception as e:
                            logger.error(f"Error in event handler for {prop}: {e}")
        except Exception as e:
            logger.error(f"Error updating target view {target_id}: {e}")
    
    def reset(self) -> None:
        """ÞÍü¸ãü’ê»ÃÈ"""
        self._views = {}
        self._contexts = {}
        self._connections = {}
        self._event_handlers = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        ·ê¢é¤ºïýjžøk	Û
        
        Returns
        -------
        Dict[str, Any]
            ·ê¢é¤º(nÇü¿
        """
        # ÓåüÅ1ªÖ¸§¯ÈÂgdO	
        views_info = {}
        for view_id, view_info in self._views.items():
            views_info[view_id] = {
                "type": view_info["type"]
            }
        
        # ¥šÅ1
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
        žøK‰¤ó¹¿ó¹’©C
        
        Parameters
        ----------
        data : Dict[str, Any]
            ·ê¢é¤ºUŒ_Çü¿
        view_objects : Dict[str, Any]
            ÓåüIDhªÖ¸§¯ÈnÞÃÔó°
            
        Returns
        -------
        ViewSynchronizer
            ©CUŒ_¤ó¹¿ó¹
        """
        instance = cls()
        
        # Óåü’{2
        for view_id, view_info in data.get("views", {}).items():
            if view_id in view_objects:
                instance.register_view(
                    view_id=view_id,
                    view_object=view_objects[view_id],
                    view_type=view_info.get("type")
                )
        
        # ³óÆ­¹È’©C
        for view_id, context in data.get("contexts", {}).items():
            if view_id in instance._contexts:
                instance._contexts[view_id] = context.copy()
        
        # ¥š’©C
        for _, conn_info in data.get("connections", {}).items():
            source_id = conn_info.get("source")
            target_id = conn_info.get("target")
            if source_id in instance._views and target_id in instance._views:
                instance._connections[(source_id, target_id)] = {
                    "sync_properties": conn_info.get("sync_properties", ["time", "selection"]),
                    "active": conn_info.get("active", True)
                }
        
        return instance
