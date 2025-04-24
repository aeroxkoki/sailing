# -*- coding: utf-8 -*-
"""
visualization.visualization_sync

異なる可視化コンポーネント間の同期を実現するモジュールです。
マップ、チャート、タイムライン、プレイバックコントロールなどの間で選択状態やデータを同期します。
"""

from typing import Dict, List, Any, Optional, Tuple, Union, Callable, Set
import streamlit as st
import json

class ViewSynchronizer:
    """
    ビュー同期コンポーネント
    
    複数のビュー（マップ、チャート、タイムライン）間の同期を管理するコンポーネントです。
    """
    
    def __init__(self):
        """初期化"""
        # ビュー登録情報
        self._views = {}
        
        # 接続関係
        self._connections = []
        
        # 同期対象プロパティ
        self._sync_properties = {
            'selected_time': None,
            'selected_point': None,
            'selected_range': None,
            'zoom_level': None,
            'center_position': None,
            'visible_layers': [],
            'active_tool': None
        }
        
        # プロパティの変更をリッスンするコールバック関数のマップ
        self._listeners = {prop: set() for prop in self._sync_properties.keys()}
    
    def register_view(self, view_id: str, view_obj: Any, view_type: str) -> None:
        """
        ビューを登録
        
        Parameters
        ----------
        view_id : str
            ビューのID
        view_obj : Any
            ビューオブジェクト
        view_type : str
            ビューのタイプ（"map", "chart", "timeline", "playback" など）
        """
        self._views[view_id] = {
            "object": view_obj,
            "type": view_type,
            "properties": set()  # このビューが同期する対象のプロパティセット
        }
    
    def unregister_view(self, view_id: str) -> bool:
        """
        ビューの登録解除
        
        Parameters
        ----------
        view_id : str
            ビューのID
            
        Returns
        -------
        bool
            解除に成功した場合True
        """
        if view_id in self._views:
            # このビューのリスナーを全て削除
            for prop in self._sync_properties.keys():
                self._listeners[prop] = {
                    listener for listener in self._listeners[prop] 
                    if listener[0] != view_id
                }
            
            # 接続からも削除
            self._connections = [
                conn for conn in self._connections
                if conn["source"] != view_id and conn["target"] != view_id
            ]
            
            # ビュー登録を削除
            del self._views[view_id]
            
            return True
        return False
    
    def connect_views(self, source_id: str, target_id: str, properties: List[str], 
                    bidirectional: bool = False) -> bool:
        """
        ビュー間の接続を設定
        
        Parameters
        ----------
        source_id : str
            ソースビューのID
        target_id : str
            ターゲットビューのID
        properties : List[str]
            同期するプロパティのリスト
        bidirectional : bool, optional
            双方向同期の場合True
            
        Returns
        -------
        bool
            接続に成功した場合True
        """
        if source_id in self._views and target_id in self._views:
            # 有効なプロパティのみを対象にする
            valid_props = [p for p in properties if p in self._sync_properties]
            
            # 同じ接続が存在するか確認
            for conn in self._connections:
                if conn["source"] == source_id and conn["target"] == target_id:
                    # 既存の接続にプロパティを追加
                    conn["properties"] = list(set(conn["properties"] + valid_props))
                    conn["bidirectional"] = bidirectional
                    
                    # リスナーを更新
                    self._update_view_listeners(source_id, target_id, valid_props, bidirectional)
                    return True
            
            # 新しい接続を追加
            if valid_props:
                self._connections.append({
                    "source": source_id,
                    "target": target_id,
                    "properties": valid_props,
                    "bidirectional": bidirectional
                })
                
                # リスナーを登録
                self._update_view_listeners(source_id, target_id, valid_props, bidirectional)
                return True
        
        return False
    
    def _update_view_listeners(self, source_id: str, target_id: str, 
                             properties: List[str], bidirectional: bool) -> None:
        """
        ビュー間の同期に必要なリスナーを更新
        
        Parameters
        ----------
        source_id : str
            ソースビューのID
        target_id : str
            ターゲットビューのID
        properties : List[str]
            同期するプロパティのリスト
        bidirectional : bool
            双方向同期の場合True
        """
        source_view = self._views.get(source_id)
        target_view = self._views.get(target_id)
        
        if not source_view or not target_view:
            return
        
        # ソースビューのプロパティ集合を更新
        source_view["properties"].update(properties)
        
        # ターゲットビューをリスナーとして登録
        for prop in properties:
            callback = (target_id, self._create_property_updater(target_id, prop))
            self._listeners[prop].add(callback)
        
        # 双方向同期の場合、逆方向のリスナーも登録
        if bidirectional:
            # ターゲットビューのプロパティ集合を更新
            target_view["properties"].update(properties)
            
            # ソースビューをリスナーとして登録
            for prop in properties:
                callback = (source_id, self._create_property_updater(source_id, prop))
                self._listeners[prop].add(callback)
    
    def _create_property_updater(self, view_id: str, property_name: str) -> Callable[[Any], None]:
        """
        プロパティ更新用のコールバック関数を生成
        
        Parameters
        ----------
        view_id : str
            ビューID
        property_name : str
            プロパティ名
            
        Returns
        -------
        Callable[[Any], None]
            プロパティ更新用コールバック関数
        """
        def updater(value):
            view_info = self._views.get(view_id)
            if view_info and view_info["object"]:
                view_obj = view_info["object"]
                # 対応するセッターメソッドがあれば呼び出し
                setter_name = f"set_{property_name}"
                if hasattr(view_obj, setter_name) and callable(getattr(view_obj, setter_name)):
                    getattr(view_obj, setter_name)(value)
        return updater
    
    def disconnect_views(self, source_id: str, target_id: str, 
                       properties: Optional[List[str]] = None) -> bool:
        """
        ビュー間の接続を解除
        
        Parameters
        ----------
        source_id : str
            ソースビューのID
        target_id : str
            ターゲットビューのID
        properties : Optional[List[str]], optional
            解除するプロパティのリスト、Noneの場合はすべて解除
            
        Returns
        -------
        bool
            解除に成功した場合True
        """
        for i, conn in enumerate(self._connections):
            if conn["source"] == source_id and conn["target"] == target_id:
                if properties is None:
                    # すべてのプロパティを解除
                    props_to_remove = conn["properties"].copy()
                    self._connections.pop(i)
                    
                    # リスナーを削除
                    for prop in props_to_remove:
                        self._listeners[prop] = {
                            listener for listener in self._listeners[prop] 
                            if listener[0] != target_id
                        }
                else:
                    # 指定されたプロパティのみ解除
                    props_to_remove = [p for p in properties if p in conn["properties"]]
                    conn["properties"] = [p for p in conn["properties"] if p not in properties]
                    
                    # リスナーを削除
                    for prop in props_to_remove:
                        self._listeners[prop] = {
                            listener for listener in self._listeners[prop] 
                            if listener[0] != target_id
                        }
                    
                    # プロパティがなくなったら接続自体を削除
                    if not conn["properties"]:
                        self._connections.pop(i)
                
                return True
        
        return False
    
    def update_property(self, property_name: str, value: Any, source_id: Optional[str] = None) -> bool:
        """
        同期プロパティの値を設定し、関係するビューに伝播
        
        Parameters
        ----------
        property_name : str
            プロパティ名
        value : Any
            設定する値
        source_id : Optional[str], optional
            値の設定元ビューID（伝播の循環を防ぐため）
            
        Returns
        -------
        bool
            設定に成功した場合True
        """
        if property_name in self._sync_properties:
            # 値を更新
            old_value = self._sync_properties[property_name]
            self._sync_properties[property_name] = value
            
            # 値が変わった場合のみリスナーに通知
            if old_value != value:
                # リスナーに通知
                for listener_id, callback in self._listeners[property_name]:
                    # ソースビュー自身には通知しない（循環を防ぐ）
                    if listener_id != source_id:
                        callback(value)
            
            return True
        
        return False
    
    def update_view_context(self, view_id: str, context_updates: Dict[str, Any]) -> bool:
        """
        ビューからのコンテキスト更新を処理
        
        Parameters
        ----------
        view_id : str
            ビューID
        context_updates : Dict[str, Any]
            更新するプロパティと値の辞書
            
        Returns
        -------
        bool
            更新処理に成功した場合True
        """
        success = True
        
        for prop_name, value in context_updates.items():
            # プロパティ値の更新と伝播
            if not self.update_property(prop_name, value, view_id):
                success = False
        
        return success
    
    def get_property(self, property_name: str) -> Any:
        """
        同期プロパティの値を取得
        
        Parameters
        ----------
        property_name : str
            プロパティ名
            
        Returns
        -------
        Any
            プロパティ値（存在しない場合はNone）
        """
        return self._sync_properties.get(property_name)
    
    def get_all_properties(self) -> Dict[str, Any]:
        """
        すべての同期プロパティを取得
        
        Returns
        -------
        Dict[str, Any]
            プロパティ名: 値の辞書
        """
        return self._sync_properties.copy()
    
    def add_property_listener(self, property_name: str, view_id: str, 
                            callback: Callable[[Any], None]) -> bool:
        """
        プロパティの変更リスナーを追加
        
        Parameters
        ----------
        property_name : str
            リッスンするプロパティ名
        view_id : str
            リスナーのビューID
        callback : Callable[[Any], None]
            値変更時に呼び出すコールバック関数
            
        Returns
        -------
        bool
            リスナー追加に成功した場合True
        """
        if property_name in self._sync_properties:
            self._listeners[property_name].add((view_id, callback))
            return True
        
        return False
    
    def remove_property_listener(self, property_name: str, view_id: str) -> bool:
        """
        プロパティの変更リスナーを削除
        
        Parameters
        ----------
        property_name : str
            リスナーを削除するプロパティ名
        view_id : str
            リスナーのビューID
            
        Returns
        -------
        bool
            リスナー削除に成功した場合True
        """
        if property_name in self._listeners:
            old_size = len(self._listeners[property_name])
            self._listeners[property_name] = {
                listener for listener in self._listeners[property_name] 
                if listener[0] != view_id
            }
            return len(self._listeners[property_name]) < old_size
        
        return False
    
    def get_views(self) -> Dict[str, Dict]:
        """
        登録されているビュー情報を取得
        
        Returns
        -------
        Dict[str, Dict]
            ビュー情報の辞書
        """
        # オブジェクト参照を除いたビュー情報を返す
        return {
            view_id: {
                "type": info["type"],
                "properties": list(info["properties"])
            } 
            for view_id, info in self._views.items()
        }
    
    def get_connections(self) -> List[Dict]:
        """
        ビュー間の接続情報を取得
        
        Returns
        -------
        List[Dict]
            接続情報のリスト
        """
        return self._connections.copy()
    
    def to_dict(self) -> Dict:
        """
        現在の設定を辞書として出力
        
        Returns
        -------
        Dict
            現在の設定を含む辞書
        """
        return {
            "views": self.get_views(),
            "connections": self.get_connections(),
            "properties": {
                # 一部の特殊なオブジェクトは簡略化して保存
                k: v if not isinstance(v, (set, dict, list)) else 
                   str(v) if isinstance(v, set) else v
                for k, v in self._sync_properties.items()
            }
        }
    
    def from_dict(self, config: Dict) -> None:
        """
        辞書から設定を読み込み
        
        Parameters
        ----------
        config : Dict
            設定を含む辞書
        """
        # ビューは既に登録されている必要がある
        
        # 接続を復元
        if "connections" in config:
            for conn in config["connections"]:
                source_id = conn.get("source")
                target_id = conn.get("target")
                properties = conn.get("properties", [])
                bidirectional = conn.get("bidirectional", False)
                
                if source_id and target_id and properties:
                    self.connect_views(source_id, target_id, properties, bidirectional)
        
        # プロパティ値を復元
        if "properties" in config:
            for prop, value in config["properties"].items():
                if prop in self._sync_properties and value is not None:
                    self._sync_properties[prop] = value
