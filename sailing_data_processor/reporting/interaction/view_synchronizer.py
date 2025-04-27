# -*- coding: utf-8 -*-
"""
sailing_data_processor.reporting.interaction.view_synchronizer

ビュー間の同期機能を提供するモジュールです。
異なるビューやチャート間の連携を実現するクラスを実装します。
"""

from typing import Dict, List, Any, Optional, Union, Tuple, Set, Callable
import logging

logger = logging.getLogger(__name__)

class ViewSynchronizer:
    """
    ビュー同期マネージャー
    
    異なるビューやチャート間の連携を実現するための
    クラスを実装します。
    """
    
    def __init__(self):
        """初期化"""
        self._views = {}  # id -> view
        self._contexts = {}  # id -> context
        self._connections = {}  # (source_id, target_id) -> connection_info
        
        # イベントハンドラー
        self._event_handlers = {}
    
    def register_view(self, view_id: str, view_object: Any, view_type: Optional[str] = None) -> None:
        """
        ビュー登録
        
        Parameters
        ----------
        view_id : str
            ビューID
        view_object : Any
            ビューオブジェクト
        view_type : Optional[str], optional
            ビュータイプ, by default None
        """
        self._views[view_id] = {
            "object": view_object,
            "type": view_type or view_object.__class__.__name__
        }
        self._contexts[view_id] = {}
    
    def unregister_view(self, view_id: str) -> bool:
        """
        ビュー登録解除
        
        Parameters
        ----------
        view_id : str
            ビューID
            
        Returns
        -------
        bool
            解除成功時はTrue
        """
        if view_id in self._views:
            del self._views[view_id]
        else:
            return False
        
        if view_id in self._contexts:
            del self._contexts[view_id]
        
        # 関連する接続を削除
        self._connections = {k: v for k, v in self._connections.items() 
                            if k[0] != view_id and k[1] != view_id}
        
        return True
    
    def get_registered_views(self) -> List[str]:
        """
        登録済みビューIDリスト取得
        
        Returns
        -------
        List[str]
            ビューIDのリスト
        """
        return list(self._views.keys())
    
    def connect_views(self, source_id: str, target_id: str, sync_props: Optional[List[str]] = None,
                     bidirectional: bool = False) -> bool:
        """
        ビュー間の接続
        
        Parameters
        ----------
        source_id : str
            ソースビューID
        target_id : str
            ターゲットビューID
        sync_props : Optional[List[str]], optional
            同期するプロパティ, by default None
        bidirectional : bool, optional
            双方向同期するか, by default False
            
        Returns
        -------
        bool
            接続成功時はTrue
        """
        if source_id not in self._views or target_id not in self._views:
            return False
        
        default_props = ["time", "selection", "zoom", "center"]
        sync_properties = sync_props or default_props
        
        self._connections[(source_id, target_id)] = {
            "sync_properties": sync_properties,
            "active": True
        }
        
        # 双方向の場合は逆方向の接続も設定
        if bidirectional:
            self._connections[(target_id, source_id)] = {
                "sync_properties": sync_properties,
                "active": True
            }
        
        return True
    
    def disconnect_views(self, source_id: str, target_id: str) -> bool:
        """
        ビュー間の接続解除
        
        Parameters
        ----------
        source_id : str
            ソースビューID
        target_id : str
            ターゲットビューID
            
        Returns
        -------
        bool
            解除成功時はTrue
        """
        if (source_id, target_id) in self._connections:
            del self._connections[(source_id, target_id)]
            return True
        
        return False
    
    def get_connections(self) -> Dict[Tuple[str, str], Dict[str, Any]]:
        """
        現在の接続情報取得
        
        Returns
        -------
        Dict[Tuple[str, str], Dict[str, Any]]
            接続情報の辞書
        """
        return self._connections.copy()
    
    def set_connection_active(self, source_id: str, target_id: str, active: bool) -> bool:
        """
        接続のアクティブ状態設定
        
        Parameters
        ----------
        source_id : str
            ソースビューID
        target_id : str
            ターゲットビューID
        active : bool
            アクティブ状態するか
            
        Returns
        -------
        bool
            設定成功時はTrue
        """
        if (source_id, target_id) in self._connections:
            self._connections[(source_id, target_id)]["active"] = active
            return True
        
        return False
    
    def update_view_context(self, view_id: str, context_update: Dict[str, Any]) -> bool:
        """
        ビューコンテキスト更新
        
        Parameters
        ----------
        view_id : str
            ビューID
        context_update : Dict[str, Any]
            更新するコンテキスト情報
            
        Returns
        -------
        bool
            更新成功時はTrue
        """
        if view_id not in self._contexts:
            return False
        
        # コンテキスト更新
        self._contexts[view_id].update(context_update)
        
        # 他方に変更を伝播
        self._propagate_context_changes(view_id, context_update)
        
        return True
    
    def get_view_context(self, view_id: str) -> Optional[Dict[str, Any]]:
        """
        ビューコンテキスト取得
        
        Parameters
        ----------
        view_id : str
            ビューID
            
        Returns
        -------
        Optional[Dict[str, Any]]
            コンテキスト情報
        """
        return self._contexts.get(view_id, {}).copy() if view_id in self._contexts else None
    
    def add_event_handler(self, event_type: str, handler: Callable[[str, Any], None]) -> None:
        """
        イベントハンドラー追加
        
        Parameters
        ----------
        event_type : str
            イベント種別 ("time_change", "selection_change", etc.)
        handler : Callable[[str, Any], None]
            ハンドラ関数 (view_id, value) を受け取る
        """
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        
        self._event_handlers[event_type].append(handler)
    
    def remove_event_handler(self, event_type: str, handler: Callable[[str, Any], None]) -> bool:
        """
        イベントハンドラー削除
        
        Parameters
        ----------
        event_type : str
            イベント種別
        handler : Callable[[str, Any], None]
            削除するハンドラ関数
            
        Returns
        -------
        bool
            削除成功時はTrue
        """
        if event_type in self._event_handlers and handler in self._event_handlers[event_type]:
            self._event_handlers[event_type].remove(handler)
            return True
        
        return False
    
    def _propagate_context_changes(self, source_id: str, changes: Dict[str, Any]) -> None:
        """
        コンテキスト変更を他方に伝播
        
        Parameters
        ----------
        source_id : str
            ソースビューID
        changes : Dict[str, Any]]
            変更情報
        """
        # 変更の循環参照を避ける
        propagated = set()
        self._propagate_to_targets(source_id, changes, propagated)
    
    def _propagate_to_targets(self, source_id: str, changes: Dict[str, Any], 
                             propagated: Set[Tuple[str, str]]) -> None:
        """
        変更を対象ビューに再帰的に伝播
        
        Parameters
        ----------
        source_id : str
            ソースビューID
        changes : Dict[str, Any]
            変更情報
        propagated : Set[Tuple[str, str]]
            既に伝播した接続のセット
        """
        for (src, tgt), conn_info in self._connections.items():
            # 既に処理した接続はスキップ
            if (src, tgt) in propagated:
                continue
                
            # 非アクティブまたは異なるソースはスキップ
            if not conn_info["active"] or src != source_id:
                continue
                
            # 同期するプロパティをフィルタリング
            sync_props = conn_info["sync_properties"]
            filtered_changes = {k: v for k, v in changes.items() if k in sync_props}
            
            if filtered_changes:
                # 処理済みに記録
                propagated.add((src, tgt))
                
                # ターゲットビューのコンテキスト更新
                if tgt in self._contexts:
                    self._contexts[tgt].update(filtered_changes)
                
                # ターゲットビュー更新
                self._update_target_view(tgt, filtered_changes)
                
                # 変更を再帰的に伝播
                self._propagate_to_targets(tgt, filtered_changes, propagated)
    
    def _update_target_view(self, target_id: str, changes: Dict[str, Any]) -> None:
        """
        ターゲットビュー更新
        
        Parameters
        ----------
        target_id : str
            ターゲットビューID
        changes : Dict[str, Any]
            変更情報
        """
        target_view_info = self._views.get(target_id)
        if not target_view_info:
            return
            
        target_view = target_view_info["object"]
        
        # 各プロパティに対して処理
        try:
            for prop, value in changes.items():
                # time プロパティの処理
                if prop == "time" and hasattr(target_view, "set_current_time"):
                    target_view.set_current_time(value)
                
                # selection プロパティの処理
                elif prop == "selection" and hasattr(target_view, "set_selection"):
                    target_view.set_selection(value)
                
                # zoom プロパティの処理
                elif prop == "zoom" and hasattr(target_view, "set_zoom"):
                    target_view.set_zoom(value)
                
                # center プロパティの処理
                elif prop == "center" and hasattr(target_view, "set_center"):
                    if isinstance(value, (list, tuple)) and len(value) >= 2:
                        target_view.set_center(value[0], value[1])
                
                # その他のプロパティの処理
                elif hasattr(target_view, f"set_{prop}"):
                    getattr(target_view, f"set_{prop}")(value)
                
                # イベントハンドラーの実行
                if prop in self._event_handlers:
                    for handler in self._event_handlers[prop]:
                        try:
                            handler(target_id, value)
                        except Exception as e:
                            logger.error(f"Error in event handler for {prop}: {e}")
        except Exception as e:
            logger.error(f"Error updating target view {target_id}: {e}")
    
    def reset(self) -> None:
        """全ての状態をリセット"""
        self._views = {}
        self._contexts = {}
        self._connections = {}
        self._event_handlers = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        状態を辞書形式に変換
        
        Returns
        -------
        Dict[str, Any]
            状態の辞書
        """
        # ビュー情報（オブジェクト自体は除外）
        views_info = {}
        for view_id, view_info in self._views.items():
            views_info[view_id] = {
                "type": view_info["type"]
            }
        
        # 接続情報
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
        辞書から状態を復元
        
        Parameters
        ----------
        data : Dict[str, Any]
            状態を表す辞書
        view_objects : Dict[str, Any]
            ビューIDとオブジェクトの対応表
            
        Returns
        -------
        ViewSynchronizer
            復元されたインスタンス
        """
        instance = cls()
        
        # ビュー登録
        for view_id, view_info in data.get("views", {}).items():
            if view_id in view_objects:
                instance.register_view(
                    view_id=view_id,
                    view_object=view_objects[view_id],
                    view_type=view_info.get("type")
                )
        
        # コンテキスト復元
        for view_id, context in data.get("contexts", {}).items():
            if view_id in instance._contexts:
                instance._contexts[view_id] = context.copy()
        
        # 接続復元
        for _, conn_info in data.get("connections", {}).items():
            source_id = conn_info.get("source")
            target_id = conn_info.get("target")
            if source_id in instance._views and target_id in instance._views:
                instance._connections[(source_id, target_id)] = {
                    "sync_properties": conn_info.get("sync_properties", ["time", "selection"]),
                    "active": conn_info.get("active", True)
                }
        
        return instance
