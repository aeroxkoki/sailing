# -*- coding: utf-8 -*-
"""
Module for data connector between map layers and data sources.
This module provides functions for binding and data transformation between layers and data sources.
"""

from typing import Dict, List, Any, Optional, Union, Tuple, Set, Type, Callable
import json
import uuid
from collections import OrderedDict

from sailing_data_processor.reporting.elements.map.layers.base_layer import BaseMapLayer
from sailing_data_processor.reporting.elements.map.layers.layer_manager import LayerManager
from sailing_data_processor.reporting.elements.map.layers.data_connector import DataConnector, LayerEventManager, DataSynchronizer


class EnhancedLayerManager(LayerManager):
    """
    拡張されたマップレイヤーマネージャークラス
    
    レイヤーの管理に加えて、レイヤー間のデータ連携とイベント管理機能を提供します。
    """
    
    def __init__(self):
        """初期化"""
        super().__init__()
        
        # データ連携用のコンポーネント
        self._data_connector = DataConnector()
        self._event_manager = LayerEventManager()
        self._data_synchronizer = DataSynchronizer(self._data_connector, self._event_manager)
        
        # コンテキストデータ
        self._context = {}
    
    @property
    def data_connector(self) -> DataConnector:
        """データコネクタ"""
        return self._data_connector
    
    @property
    def event_manager(self) -> LayerEventManager:
        """イベントマネージャー"""
        return self._event_manager
    
    @property
    def data_synchronizer(self) -> DataSynchronizer:
        """データ同期マネージャー"""
        return self._data_synchronizer
    
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
    
    def clear_context_data(self, key: str = None) -> None:
        """
        コンテキストデータをクリア
        
        Parameters
        ----------
        key : str, optional
            クリアするデータキー, by default None（すべてのデータ）
        """
        if key is None:
            self._context.clear()
        elif key in self._context:
            del self._context[key]
    
    def update_context(self, context: Dict[str, Any]) -> None:
        """
        コンテキストを一括更新
        
        Parameters
        ----------
        context : Dict[str, Any]
            更新するコンテキストデータ
        """
        self._context.update(context)
    
    def get_context(self) -> Dict[str, Any]:
        """
        コンテキスト全体を取得
        
        Returns
        -------
        Dict[str, Any]
            コンテキストデータ
        """
        return self._context.copy()
    
    def trigger_layer_event(self, layer: BaseMapLayer, event_name: str, event_data: Any = None) -> None:
        """
        レイヤーイベントをトリガー
        
        Parameters
        ----------
        layer : BaseMapLayer
            イベントを発行するレイヤー
        event_name : str
            イベント名
        event_data : Any, optional
            イベントデータ, by default None
        """
        if not layer:
            return
        
        # レイヤー自体のイベントトリガー
        layer.trigger(event_name, event_data)
        
        # イベントマネージャーにイベントをパブリッシュ
        self._event_manager.publish(layer, event_name, event_data)
    
    def bind_layer_to_source(self, layer: BaseMapLayer, source_id: str, 
                           field_mappings: Dict[str, str] = None,
                           transform: Union[str, Callable] = None) -> None:
        """
        レイヤーをデータソースにバインド
        
        Parameters
        ----------
        layer : BaseMapLayer
            バインドするレイヤー
        source_id : str
            データソースID
        field_mappings : Dict[str, str], optional
            フィールドマッピング, by default None
        transform : Union[str, Callable], optional
            変換関数, by default None
        """
        if not layer or not source_id:
            return
        
        # データコネクタにバインディング情報を登録
        self._data_connector.bind_layer_to_source(layer, source_id, field_mappings, transform)
        
        # データソースがコンテキストに存在する場合は同期
        if source_id in self._context:
            self._data_connector.update_data(source_id, self._context[source_id])
            self._data_connector.sync_layer_to_data(layer, self._context)
    
    def unbind_layer(self, layer: BaseMapLayer) -> bool:
        """
        レイヤーのバインディングを解除
        
        Parameters
        ----------
        layer : BaseMapLayer
            バインディングを解除するレイヤー
            
        Returns
        -------
        bool
            解除に成功した場合True
        """
        if not layer:
            return False
        
        return self._data_connector.unbind_layer(layer)
    
    def add_sync_pair(self, source_layer: BaseMapLayer, target_layer: BaseMapLayer, 
                    field_mappings: Dict[str, str] = None,
                    transform: Union[str, Callable] = None,
                    bidirectional: bool = False) -> None:
        """
        レイヤー間の同期ペアを追加
        
        Parameters
        ----------
        source_layer : BaseMapLayer
            ソースレイヤー
        target_layer : BaseMapLayer
            ターゲットレイヤー
        field_mappings : Dict[str, str], optional
            フィールドマッピング, by default None
        transform : Union[str, Callable], optional
            変換関数, by default None
        bidirectional : bool, optional
            双方向同期フラグ, by default False
        """
        if not source_layer or not target_layer:
            return
        
        self._data_synchronizer.add_sync_pair(
            source_layer, target_layer, field_mappings, transform, bidirectional
        )
    
    def remove_sync_pair(self, source_layer: BaseMapLayer, target_layer: BaseMapLayer) -> None:
        """
        レイヤー間の同期ペアを削除
        
        Parameters
        ----------
        source_layer : BaseMapLayer
            ソースレイヤー
        target_layer : BaseMapLayer
            ターゲットレイヤー
        """
        if not source_layer or not target_layer:
            return
        
        self._data_synchronizer.remove_sync_pair(source_layer, target_layer)
    
    def sync_layers(self) -> Dict[str, bool]:
        """
        レイヤー間のデータを同期
        
        Returns
        -------
        Dict[str, bool]
            同期結果
        """
        return self._data_synchronizer.sync_layers(self, self._context)
    
    def update_data_source(self, source_id: str, data: Any) -> None:
        """
        データソースを更新し、関連するレイヤーを同期
        
        Parameters
        ----------
        source_id : str
            データソースID
        data : Any
            更新データ
        """
        # コンテキストの更新
        self._context[source_id] = data
        
        # データコネクタの更新
        self._data_connector.update_data(source_id, data)
        
        # 関連するレイヤーを同期
        for layer in self._layers.values():
            if layer.data_source == source_id:
                self._data_connector.sync_layer_to_data(layer, self._context)
    
    def subscribe_to_layer_events(self, subscriber_layer: BaseMapLayer, event_name: str, 
                                  handler: Callable, 
                                  target_layers: List[BaseMapLayer] = None) -> None:
        """
        レイヤーイベントをサブスクライブ
        
        Parameters
        ----------
        subscriber_layer : BaseMapLayer
            サブスクライブするレイヤー
        event_name : str
            イベント名
        handler : Callable
            ハンドラ関数
        target_layers : List[BaseMapLayer], optional
            ターゲットレイヤーのリスト, by default None
        """
        if not subscriber_layer or not event_name or not handler:
            return
        
        self._event_manager.subscribe(subscriber_layer, event_name, handler, target_layers)
    
    def unsubscribe_from_layer_events(self, layer: BaseMapLayer, event_name: str = None) -> None:
        """
        レイヤーイベントのサブスクリプションを解除
        
        Parameters
        ----------
        layer : BaseMapLayer
            サブスクリプションを解除するレイヤー
        event_name : str, optional
            イベント名, by default None（すべてのイベント）
        """
        if not layer:
            return
        
        self._event_manager.unsubscribe(layer, event_name)
    
    # オーバーライドメソッド
    def add_layer(self, layer: BaseMapLayer, group: Optional[str] = None) -> str:
        """
        レイヤーを追加
        
        Parameters
        ----------
        layer : BaseMapLayer
            追加するレイヤー
        group : Optional[str], optional
            グループ名, by default None
            
        Returns
        -------
        str
            追加されたレイヤーのID
        """
        # 基底クラスの処理を呼び出し
        layer_id = super().add_layer(layer, group)
        
        # レイヤーがデータソースを持っている場合は同期
        if layer.data_source and layer.data_source in self._context:
            self._data_connector.sync_layer_to_data(layer, self._context)
        
        # レイヤー追加イベントを発行
        self.trigger_layer_event(layer, "layer_added")
        
        return layer_id
    
    def remove_layer(self, layer_id: str) -> Optional[BaseMapLayer]:
        """
        レイヤーを削除
        
        Parameters
        ----------
        layer_id : str
            削除するレイヤーのID
            
        Returns
        -------
        Optional[BaseMapLayer]
            削除されたレイヤー、存在しない場合はNone
        """
        layer = self.get_layer(layer_id)
        
        if layer:
            # レイヤー削除イベントを発行
            self.trigger_layer_event(layer, "layer_removed")
            
            # バインディングとサブスクリプションを解除
            self._data_connector.unbind_layer(layer)
            self._event_manager.unsubscribe(layer)
        
        # 基底クラスの処理を呼び出し
        return super().remove_layer(layer_id)
    
    def render_layers(self, map_var: str = "map", context: Dict[str, Any] = None) -> str:
        """
        すべてのレイヤーのレンダリングコードを生成
        
        Parameters
        ----------
        map_var : str, optional
            マップ変数名, by default "map"
        context : Dict[str, Any], optional
            レンダリングコンテキスト, by default None
            
        Returns
        -------
        str
            レイヤーをレンダリングするJavaScriptコード
        """
        # コンテキストをマージ
        merged_context = self._context.copy()
        if context:
            merged_context.update(context)
        
        # 基底クラスの処理を呼び出し
        return super().render_layers(map_var, merged_context)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        レイヤーマネージャーの辞書表現を取得
        
        Returns
        -------
        Dict[str, Any]
            レイヤーマネージャーの辞書表現
        """
        # 基底クラスの処理を呼び出し
        data = super().to_dict()
        
        # 拡張部分を追加
        data.update({
            "data_connector": self._data_connector.to_dict(),
            # イベントハンドラとシンクロナイザは関数を含むためシリアライズしない
        })
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], layer_classes: Dict[str, Type[BaseMapLayer]]) -> "EnhancedLayerManager":
        """
        辞書からレイヤーマネージャーを生成
        
        Parameters
        ----------
        data : Dict[str, Any]
            レイヤーマネージャーの辞書表現
        layer_classes : Dict[str, Type[BaseMapLayer]]
            レイヤータイプ名からレイヤークラスへのマッピング
            
        Returns
        -------
        EnhancedLayerManager
            生成されたレイヤーマネージャー
        """
        # 拡張マネージャーを作成
        manager = cls()
        
        # 基底部分のデータを読み込み
        layers_data = data.get("layers", {})
        for layer_id, layer_data in layers_data.items():
            layer_type = layer_data.get("type")
            
            if layer_type in layer_classes:
                layer = layer_classes[layer_type].from_dict(layer_data)
                manager.add_layer(layer)
        
        # グループの復元
        groups_data = data.get("groups", {})
        for group_name, group_ids in groups_data.items():
            for layer_id in group_ids:
                manager.add_to_group(layer_id, group_name)
        
        # 依存関係の復元
        dependencies_data = data.get("dependencies", {})
        for layer_id, deps in dependencies_data.items():
            for dep_id in deps:
                manager.add_dependency(layer_id, dep_id)
        
        # データコネクタの復元
        if "data_connector" in data:
            connector_data = data["data_connector"]
            connector = DataConnector.from_dict(connector_data)
            manager._data_connector = connector
        
        return manager
