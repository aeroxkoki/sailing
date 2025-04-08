"""
sailing_data_processor.visualization.visualization_manager

可視化コンポーネントの管理と連携を担当するシステム。
マップ、チャート、グラフなどの可視化コンポーネント間の連携と
統一的なインターフェースを提供します。
"""

import uuid
from typing import Dict, List, Any, Optional, Union, Callable, Type, Set
from collections import OrderedDict
import streamlit as st
import json

# 基本可視化コンポーネントの抽象クラス
class VisualizationComponent:
    """
    可視化コンポーネントの基底クラス
    """
    
    def __init__(self, component_id: str = None, component_type: str = "base", name: str = None):
        """
        初期化
        
        Parameters
        ----------
        component_id : str, optional
            コンポーネントID、指定されない場合は自動生成
        component_type : str, optional
            コンポーネントタイプ
        name : str, optional
            コンポーネント名
        """
        self._component_id = component_id or str(uuid.uuid4())
        self._component_type = component_type
        self._name = name or f"{component_type}_{self._component_id[:8]}"
        self._visible = True
        self._properties = {}
        self._event_handlers = {}
        self._data_source = None
    
    @property
    def component_id(self) -> str:
        """コンポーネントID"""
        return self._component_id
    
    @property
    def component_type(self) -> str:
        """コンポーネントタイプ"""
        return self._component_type
    
    @property
    def name(self) -> str:
        """コンポーネント名"""
        return self._name
    
    @name.setter
    def name(self, value: str):
        """コンポーネント名を設定"""
        self._name = value
    
    @property
    def visible(self) -> bool:
        """表示状態"""
        return self._visible
    
    @visible.setter
    def visible(self, value: bool):
        """表示状態を設定"""
        self._visible = bool(value)
    
    @property
    def data_source(self) -> Optional[str]:
        """データソース"""
        return self._data_source
    
    @data_source.setter
    def data_source(self, value: Optional[str]):
        """データソースを設定"""
        self._data_source = value
    
    def get_property(self, key: str, default: Any = None) -> Any:
        """
        プロパティを取得
        
        Parameters
        ----------
        key : str
            プロパティキー
        default : Any, optional
            デフォルト値
            
        Returns
        -------
        Any
            プロパティ値
        """
        return self._properties.get(key, default)
    
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
        self._properties[key] = value
    
    def update_properties(self, properties: Dict[str, Any]) -> None:
        """
        複数のプロパティを一括更新
        
        Parameters
        ----------
        properties : Dict[str, Any]
            プロパティ辞書
        """
        if properties:
            self._properties.update(properties)
    
    def get_properties(self) -> Dict[str, Any]:
        """
        すべてのプロパティを取得
        
        Returns
        -------
        Dict[str, Any]
            プロパティ辞書
        """
        return self._properties.copy()
    
    def on(self, event_name: str, handler: Callable) -> None:
        """
        イベントハンドラを登録
        
        Parameters
        ----------
        event_name : str
            イベント名
        handler : Callable
            ハンドラ関数
        """
        if event_name not in self._event_handlers:
            self._event_handlers[event_name] = []
        self._event_handlers[event_name].append(handler)
    
    def off(self, event_name: str, handler: Optional[Callable] = None) -> None:
        """
        イベントハンドラを解除
        
        Parameters
        ----------
        event_name : str
            イベント名
        handler : Optional[Callable], optional
            ハンドラ関数、Noneの場合は当該イベントのすべてのハンドラを解除
        """
        if event_name not in self._event_handlers:
            return
        
        if handler is None:
            self._event_handlers[event_name] = []
        else:
            self._event_handlers[event_name] = [
                h for h in self._event_handlers[event_name] if h != handler
            ]
    
    def trigger(self, event_name: str, event_data: Any = None) -> None:
        """
        イベントを発火
        
        Parameters
        ----------
        event_name : str
            イベント名
        event_data : Any, optional
            イベントデータ
        """
        if event_name not in self._event_handlers:
            return
        
        for handler in self._event_handlers[event_name]:
            try:
                handler(self, event_name, event_data)
            except Exception as e:
                st.error(f"イベントハンドラでエラーが発生: {str(e)}")
    
    def render(self, context: Dict[str, Any] = None) -> Any:
        """
        コンポーネントをレンダリング
        
        Parameters
        ----------
        context : Dict[str, Any], optional
            レンダリングコンテキスト
            
        Returns
        -------
        Any
            レンダリング結果
        """
        # 基底クラスでは何もしない
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        辞書表現に変換
        
        Returns
        -------
        Dict[str, Any]
            辞書表現
        """
        return {
            "component_id": self._component_id,
            "component_type": self._component_type,
            "name": self._name,
            "visible": self._visible,
            "properties": self._properties,
            "data_source": self._data_source
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VisualizationComponent":
        """
        辞書から生成
        
        Parameters
        ----------
        data : Dict[str, Any]
            辞書データ
            
        Returns
        -------
        VisualizationComponent
            生成されたオブジェクト
        """
        component = cls(
            component_id=data.get("component_id"),
            component_type=data.get("component_type", "base"),
            name=data.get("name")
        )
        component._visible = data.get("visible", True)
        component._properties = data.get("properties", {}).copy()
        component._data_source = data.get("data_source")
        
        return component


class VisualizationManager:
    """
    可視化コンポーネントの管理と連携を行うマネージャークラス
    """
    
    def __init__(self):
        """初期化"""
        self._components = {}  # コンポーネントID -> コンポーネント
        self._component_by_type = {}  # コンポーネントタイプ -> コンポーネントIDのセット
        self._sync_pairs = {}  # コンポーネントID -> 同期先コンポーネントIDのセット
        self._context = {}  # データコンテキスト
        self._global_event_handlers = {}  # イベント名 -> ハンドラリスト
    
    def add_component(self, component: VisualizationComponent) -> str:
        """
        コンポーネントを追加
        
        Parameters
        ----------
        component : VisualizationComponent
            追加するコンポーネント
            
        Returns
        -------
        str
            コンポーネントID
        """
        if not component:
            return None
        
        component_id = component.component_id
        self._components[component_id] = component
        
        # タイプごとの管理
        component_type = component.component_type
        if component_type not in self._component_by_type:
            self._component_by_type[component_type] = set()
        self._component_by_type[component_type].add(component_id)
        
        # イベント伝播
        self.trigger_global_event("component_added", {
            "component_id": component_id,
            "component": component
        })
        
        return component_id
    
    def remove_component(self, component_id: str) -> Optional[VisualizationComponent]:
        """
        コンポーネントを削除
        
        Parameters
        ----------
        component_id : str
            削除するコンポーネントID
            
        Returns
        -------
        Optional[VisualizationComponent]
            削除されたコンポーネント、存在しない場合はNone
        """
        if component_id not in self._components:
            return None
        
        component = self._components.pop(component_id)
        
        # タイプごとの管理から削除
        component_type = component.component_type
        if component_type in self._component_by_type:
            self._component_by_type[component_type].discard(component_id)
            if not self._component_by_type[component_type]:
                del self._component_by_type[component_type]
        
        # 同期ペアから削除
        if component_id in self._sync_pairs:
            del self._sync_pairs[component_id]
        
        # 他のコンポーネントの同期先から削除
        for other_id, sync_targets in list(self._sync_pairs.items()):
            if component_id in sync_targets:
                sync_targets.remove(component_id)
        
        # イベント伝播
        self.trigger_global_event("component_removed", {
            "component_id": component_id,
            "component": component
        })
        
        return component
    
    def get_component(self, component_id: str) -> Optional[VisualizationComponent]:
        """
        コンポーネントを取得
        
        Parameters
        ----------
        component_id : str
            コンポーネントID
            
        Returns
        -------
        Optional[VisualizationComponent]
            コンポーネント、存在しない場合はNone
        """
        return self._components.get(component_id)
    
    def get_components_by_type(self, component_type: str) -> List[VisualizationComponent]:
        """
        指定タイプのコンポーネントをすべて取得
        
        Parameters
        ----------
        component_type : str
            コンポーネントタイプ
            
        Returns
        -------
        List[VisualizationComponent]
            コンポーネントのリスト
        """
        if component_type not in self._component_by_type:
            return []
        
        return [
            self._components[component_id]
            for component_id in self._component_by_type[component_type]
            if component_id in self._components
        ]
    
    def get_all_components(self) -> List[VisualizationComponent]:
        """
        すべてのコンポーネントを取得
        
        Returns
        -------
        List[VisualizationComponent]
            コンポーネントのリスト
        """
        return list(self._components.values())
    
    def add_sync_pair(self, source_id: str, target_id: str) -> bool:
        """
        コンポーネント間の同期ペアを追加
        
        Parameters
        ----------
        source_id : str
            ソースコンポーネントID
        target_id : str
            ターゲットコンポーネントID
            
        Returns
        -------
        bool
            追加に成功した場合True
        """
        if source_id not in self._components or target_id not in self._components:
            return False
        
        if source_id not in self._sync_pairs:
            self._sync_pairs[source_id] = set()
        
        self._sync_pairs[source_id].add(target_id)
        
        # イベント伝播
        self.trigger_global_event("sync_pair_added", {
            "source_id": source_id,
            "target_id": target_id
        })
        
        return True
    
    def remove_sync_pair(self, source_id: str, target_id: str) -> bool:
        """
        コンポーネント間の同期ペアを削除
        
        Parameters
        ----------
        source_id : str
            ソースコンポーネントID
        target_id : str
            ターゲットコンポーネントID
            
        Returns
        -------
        bool
            削除に成功した場合True
        """
        if source_id not in self._sync_pairs:
            return False
        
        if target_id not in self._sync_pairs[source_id]:
            return False
        
        self._sync_pairs[source_id].remove(target_id)
        
        if not self._sync_pairs[source_id]:
            del self._sync_pairs[source_id]
        
        # イベント伝播
        self.trigger_global_event("sync_pair_removed", {
            "source_id": source_id,
            "target_id": target_id
        })
        
        return True
    
    def get_sync_targets(self, source_id: str) -> Set[str]:
        """
        同期先コンポーネントのIDを取得
        
        Parameters
        ----------
        source_id : str
            ソースコンポーネントID
            
        Returns
        -------
        Set[str]
            同期先コンポーネントIDのセット
        """
        return self._sync_pairs.get(source_id, set()).copy()
    
    def get_sync_sources(self, target_id: str) -> Set[str]:
        """
        同期元コンポーネントのIDを取得
        
        Parameters
        ----------
        target_id : str
            ターゲットコンポーネントID
            
        Returns
        -------
        Set[str]
            同期元コンポーネントIDのセット
        """
        sources = set()
        for source_id, targets in self._sync_pairs.items():
            if target_id in targets:
                sources.add(source_id)
        return sources
    
    def propagate_selection(self, source_id: str, selection_data: Any) -> Dict[str, bool]:
        """
        選択状態を同期先に伝播
        
        Parameters
        ----------
        source_id : str
            ソースコンポーネントID
        selection_data : Any
            選択データ
            
        Returns
        -------
        Dict[str, bool]
            伝播結果
        """
        results = {}
        
        if source_id not in self._components or source_id not in self._sync_pairs:
            return results
        
        for target_id in self._sync_pairs[source_id]:
            if target_id not in self._components:
                results[target_id] = False
                continue
            
            target = self._components[target_id]
            try:
                # 選択イベントを発火
                target.trigger("selection_changed", selection_data)
                results[target_id] = True
            except Exception as e:
                st.error(f"選択状態伝播エラー: {str(e)}")
                results[target_id] = False
        
        return results
    
    def set_context_data(self, key: str, data: Any) -> None:
        """
        コンテキストデータを設定
        
        Parameters
        ----------
        key : str
            データキー
        data : Any
            設定するデータ
        """
        self._context[key] = data
        
        # データソースとして使用しているコンポーネントに通知
        for component in self._components.values():
            if component.data_source == key:
                component.trigger("data_updated", data)
    
    def get_context_data(self, key: str) -> Optional[Any]:
        """
        コンテキストデータを取得
        
        Parameters
        ----------
        key : str
            データキー
            
        Returns
        -------
        Optional[Any]
            データ、存在しない場合はNone
        """
        return self._context.get(key)
    
    def get_context(self) -> Dict[str, Any]:
        """
        コンテキスト全体を取得
        
        Returns
        -------
        Dict[str, Any]
            コンテキストデータ
        """
        return self._context.copy()
    
    def on_global_event(self, event_name: str, handler: Callable) -> None:
        """
        グローバルイベントハンドラを登録
        
        Parameters
        ----------
        event_name : str
            イベント名
        handler : Callable
            ハンドラ関数
        """
        if event_name not in self._global_event_handlers:
            self._global_event_handlers[event_name] = []
        self._global_event_handlers[event_name].append(handler)
    
    def off_global_event(self, event_name: str, handler: Optional[Callable] = None) -> None:
        """
        グローバルイベントハンドラを解除
        
        Parameters
        ----------
        event_name : str
            イベント名
        handler : Optional[Callable], optional
            ハンドラ関数、Noneの場合は当該イベントのすべてのハンドラを解除
        """
        if event_name not in self._global_event_handlers:
            return
        
        if handler is None:
            self._global_event_handlers[event_name] = []
        else:
            self._global_event_handlers[event_name] = [
                h for h in self._global_event_handlers[event_name] if h != handler
            ]
    
    def trigger_global_event(self, event_name: str, event_data: Any = None) -> None:
        """
        グローバルイベントを発火
        
        Parameters
        ----------
        event_name : str
            イベント名
        event_data : Any, optional
            イベントデータ
        """
        if event_name not in self._global_event_handlers:
            return
        
        for handler in self._global_event_handlers[event_name]:
            try:
                handler(event_name, event_data)
            except Exception as e:
                st.error(f"グローバルイベントハンドラでエラーが発生: {str(e)}")
    
    def render_components(self, component_type: Optional[str] = None, 
                          container: Optional[Any] = None,
                          context: Optional[Dict[str, Any]] = None) -> None:
        """
        コンポーネントをレンダリング
        
        Parameters
        ----------
        component_type : Optional[str], optional
            特定タイプのコンポーネントのみをレンダリング, by default None
        container : Optional[Any], optional
            レンダリング先のコンテナ, by default None
        context : Optional[Dict[str, Any]], optional
            レンダリングコンテキスト, by default None
        """
        # マージされたコンテキストを作成
        merged_context = self._context.copy()
        if context:
            merged_context.update(context)
        
        # レンダリング対象のコンポーネントを選択
        components = []
        if component_type:
            components = self.get_components_by_type(component_type)
        else:
            components = self.get_all_components()
        
        # コンポーネントを可視状態でフィルタリング
        visible_components = [c for c in components if c.visible]
        
        # コンテナが指定されていない場合はデフォルトでStreamlitに直接レンダリング
        if container is None:
            for component in visible_components:
                st.subheader(component.name)
                component.render(merged_context)
        else:
            # コンテナにレンダリング
            with container:
                for component in visible_components:
                    with st.expander(component.name, expanded=True):
                        component.render(merged_context)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        辞書表現に変換
        
        Returns
        -------
        Dict[str, Any]
            辞書表現
        """
        return {
            "components": {
                component_id: component.to_dict()
                for component_id, component in self._components.items()
            },
            "sync_pairs": {
                source_id: list(targets)
                for source_id, targets in self._sync_pairs.items()
            }
        }
    
    def save_to_json(self, file_path: str) -> bool:
        """
        JSON形式で保存
        
        Parameters
        ----------
        file_path : str
            保存先ファイルパス
            
        Returns
        -------
        bool
            保存に成功した場合True
        """
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self.to_dict(), f, indent=2)
            return True
        except Exception as e:
            st.error(f"保存エラー: {str(e)}")
            return False
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], 
                  component_classes: Dict[str, Type[VisualizationComponent]]) -> "VisualizationManager":
        """
        辞書から生成
        
        Parameters
        ----------
        data : Dict[str, Any]
            辞書データ
        component_classes : Dict[str, Type[VisualizationComponent]]
            コンポーネントタイプからクラスへのマッピング
            
        Returns
        -------
        VisualizationManager
            生成されたオブジェクト
        """
        manager = cls()
        
        # コンポーネントの復元
        components_data = data.get("components", {})
        for component_id, component_data in components_data.items():
            component_type = component_data.get("component_type", "base")
            if component_type in component_classes:
                component = component_classes[component_type].from_dict(component_data)
                manager.add_component(component)
            else:
                # 未知のタイプの場合は基底クラスで復元
                component = VisualizationComponent.from_dict(component_data)
                manager.add_component(component)
        
        # 同期ペアの復元
        sync_pairs_data = data.get("sync_pairs", {})
        for source_id, targets in sync_pairs_data.items():
            for target_id in targets:
                manager.add_sync_pair(source_id, target_id)
        
        return manager
    
    @classmethod
    def load_from_json(cls, file_path: str, 
                       component_classes: Dict[str, Type[VisualizationComponent]]) -> Optional["VisualizationManager"]:
        """
        JSON形式から読み込み
        
        Parameters
        ----------
        file_path : str
            ファイルパス
        component_classes : Dict[str, Type[VisualizationComponent]]
            コンポーネントタイプからクラスへのマッピング
            
        Returns
        -------
        Optional[VisualizationManager]
            読み込まれたオブジェクト、失敗した場合はNone
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return cls.from_dict(data, component_classes)
        except Exception as e:
            st.error(f"読み込みエラー: {str(e)}")
            return None
