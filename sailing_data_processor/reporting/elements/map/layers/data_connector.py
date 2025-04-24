# -*- coding: utf-8 -*-
"""
sailing_data_processor.reporting.elements.map.layers.data_connector

マップレイヤーとデータソースの連携機能を提供するモジュールです。
このモジュールは、レイヤーとデータソース間のバインディングとデータ変換機能を定義します。
"""

from typing import Dict, List, Any, Optional, Union, Tuple, Set, Callable, Type
import json
import numpy as np
from datetime import datetime

from sailing_data_processor.reporting.elements.map.layers.base_layer import BaseMapLayer


class DataConnector:
    """
    データ連携クラス
    
    レイヤーとデータソース間のバインディングとデータ変換機能を提供します。
    """
    
    def __init__(self):
        """初期化"""
        self._bindings = {}  # {layer_id: {source_id, field_mappings, transform_fn}}
        self._data_cache = {}  # {source_id: data}
        self._transformers = {}  # {transform_name: transform_fn}
        
        # 標準トランスフォーマーの登録
        self._register_standard_transformers()
    
    def _register_standard_transformers(self):
        """標準データ変換関数を登録"""
        self._transformers["identity"] = lambda x: x
        self._transformers["to_float"] = lambda x: float(x) if x is not None else None
        self._transformers["to_int"] = lambda x: int(x) if x is not None else None
        self._transformers["to_str"] = lambda x: str(x) if x is not None else ""
        self._transformers["scale"] = lambda x, factor=1.0: x * factor if x is not None else None
        self._transformers["offset"] = lambda x, offset=0.0: x + offset if x is not None else None
        self._transformers["min_max_normalize"] = lambda x, min_val=0.0, max_val=1.0:
                                                    (x - min_val) / (max_val - min_val) if x is not None and max_val > min_val else None
    
    def register_transformer(self, name: str, transformer_fn: Callable) -> None:
        """
        データ変換関数を登録
        
        Parameters
        ----------
        name : str
            変換関数名
        transformer_fn : Callable
            変換関数
        """
        self._transformers[name] = transformer_fn
    
    def get_transformer(self, name: str) -> Optional[Callable]:
        """
        データ変換関数を取得
        
        Parameters
        ----------
        name : str
            変換関数名
            
        Returns
        -------
        Optional[Callable]
            変換関数、存在しない場合はNone
        """
        return self._transformers.get(name)
    
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
            フィールドマッピング {レイヤーフィールド: ソースフィールド}, by default None
        transform : Union[str, Callable], optional
            データ変換関数名または関数オブジェクト, by default None
        """
        if not layer:
            return
        
        # バインディング情報を記録
        self._bindings[layer.layer_id] = {
            "source_id": source_id,
            "field_mappings": field_mappings or {},
            "transform": transform
        
        # レイヤーのデータソースプロパティを更新
        layer.data_source = source_id
    
    def unbind_layer(self, layer: Union[BaseMapLayer, str]) -> bool:
        """
        レイヤーのバインディングを解除
        
        Parameters
        ----------
        layer : Union[BaseMapLayer, str]
            レイヤーまたはレイヤーID
            
        Returns
        -------
        bool
            解除に成功した場合True
        """
        layer_id = layer if isinstance(layer, str) else (layer.layer_id if layer else None)
        
        if not layer_id or layer_id not in self._bindings:
            return False
        
        # バインディング情報を削除
        del self._bindings[layer_id]
        
        # レイヤーのデータソースプロパティを更新
        if not isinstance(layer, str) and layer:
            layer.data_source = None
        
        return True
    
    def update_data(self, source_id: str, data: Any) -> None:
        """
        データソースを更新
        
        Parameters
        ----------
        source_id : str
            データソースID
        data : Any
            更新データ
        """
        self._data_cache[source_id] = data
    
    def clear_data(self, source_id: str) -> None:
        """
        データソースをクリア
        
        Parameters
        ----------
        source_id : str
            データソースID
        """
        if source_id in self._data_cache:
            del self._data_cache[source_id]
    
    def clear_all_data(self) -> None:
        """全データソースをクリア"""
        self._data_cache.clear()
    
    def get_data(self, source_id: str) -> Optional[Any]:
        """
        データソースからデータを取得
        
        Parameters
        ----------
        source_id : str
            データソースID
            
        Returns
        -------
        Optional[Any]
            データ、存在しない場合はNone
        """
        return self._data_cache.get(source_id)
    
    def get_binding(self, layer: Union[BaseMapLayer, str]) -> Optional[Dict[str, Any]]:
        """
        レイヤーのバインディング情報を取得
        
        Parameters
        ----------
        layer : Union[BaseMapLayer, str]
            レイヤーまたはレイヤーID
            
        Returns
        -------
        Optional[Dict[str, Any]]
            バインディング情報、存在しない場合はNone
        """
        layer_id = layer if isinstance(layer, str) else (layer.layer_id if layer else None)
        
        if not layer_id:
            return None
        
        return self._bindings.get(layer_id)
    
    def transform_data(self, data: Any, transform: Union[str, Callable], **kwargs) -> Any:
        """
        データを変換
        
        Parameters
        ----------
        data : Any
            変換するデータ
        transform : Union[str, Callable]
            変換関数名または関数オブジェクト
        **kwargs
            変換関数に渡す追加パラメータ
            
        Returns
        -------
        Any
            変換後のデータ
        """
        if transform is None:
            return data
        
        if isinstance(transform, str):
            # 名前から変換関数を取得
            transform_fn = self.get_transformer(transform)
            if not transform_fn:
                return data
        else:
            # 関数オブジェクトを直接使用
            transform_fn = transform
        
        try:
            # 変換関数を実行
            return transform_fn(data, **kwargs)
        except Exception as e:
            print(f"Data transformation error: {e}")
            return data
    
    def apply_field_mapping(self, data: Any, field_mappings: Dict[str, str]) -> Dict[str, Any]:
        """
        フィールドマッピングを適用
        
        Parameters
        ----------
        data : Any
            マッピングするデータ
        field_mappings : Dict[str, str]
            フィールドマッピング {ターゲットフィールド: ソースフィールド}
            
        Returns
        -------
        Dict[str, Any]
            マッピング後のデータ
        """
        if not isinstance(data, dict) or not field_mappings:
            return data
        
        result = {}
        for target_field, source_field in field_mappings.items():
            if source_field in data:
                result[target_field] = data[source_field]
        
        return result
    
    def prepare_layer_data(self, layer: BaseMapLayer, context: Dict[str, Any] = None) -> Any:
        """
        レイヤー用のデータを準備
        
        Parameters
        ----------
        layer : BaseMapLayer
            データを準備するレイヤー
        context : Dict[str, Any], optional
            追加コンテキスト, by default None
            
        Returns
        -------
        Any
            準備されたデータ
        """
        if not layer:
            return None
        
        context = context or {}
        binding = self.get_binding(layer)
        
        if not binding:
            # バインディングがない場合、レイヤーのデータソースプロパティからデータを取得
            source_id = layer.data_source
            if not source_id:
                return None
            
            # キャッシュまたはコンテキストからデータを取得
            data = self._data_cache.get(source_id) or context.get(source_id)
            return data
        
        # バインディングからデータを取得
        source_id = binding["source_id"]
        field_mappings = binding["field_mappings"]
        transform = binding["transform"]
        
        # キャッシュまたはコンテキストからデータを取得
        data = self._data_cache.get(source_id) or context.get(source_id)
        
        if data is None:
            return None
        
        # リスト形式の場合、各要素に変換を適用
        if isinstance(data, list):
            if field_mappings:
                data = [self.apply_field_mapping(item, field_mappings) for item in data]
            
            if transform:
                data = [self.transform_data(item, transform) for item in data]
        else:
            # 単一データの場合
            if field_mappings:
                data = self.apply_field_mapping(data, field_mappings)
            
            if transform:
                data = self.transform_data(data, transform)
        
        return data
    
    def sync_layer_to_data(self, layer: BaseMapLayer, context: Dict[str, Any] = None) -> bool:
        """
        レイヤーをデータソースと同期
        
        Parameters
        ----------
        layer : BaseMapLayer
            同期するレイヤー
        context : Dict[str, Any], optional
            追加コンテキスト, by default None
            
        Returns
        -------
        bool
            同期に成功した場合True
        """
        if not layer:
            return False
        
        # レイヤー用のデータを準備
        data = self.prepare_layer_data(layer, context)
        
        if data is None:
            return False
        
        # コンテキストにデータを設定
        context = context or {}
        context[layer.data_source] = data
        
        # レイヤーにデータを設定（レイヤーの準備メソッドを呼び出す）
        try:
            layer.prepare_data(context)
            return True
        except Exception as e:
            print(f"Layer data sync error: {e}")
            return False
    
    def sync_all_layers(self, layers: List[BaseMapLayer], context: Dict[str, Any] = None) -> Dict[str, bool]:
        """
        すべてのレイヤーをデータソースと同期
        
        Parameters
        ----------
        layers : List[BaseMapLayer]
            同期するレイヤーのリスト
        context : Dict[str, Any], optional
            追加コンテキスト, by default None
            
        Returns
        -------
        Dict[str, bool]
            レイヤーIDから同期結果へのマッピング
        """
        results = {}
        context = context or {}
        
        for layer in layers:
            if not layer:
                continue
            
            result = self.sync_layer_to_data(layer, context)
            results[layer.layer_id] = result
        
        return results
    
    def to_dict(self) -> Dict[str, Any]:
        """
        辞書表現を取得
        
        Returns
        -------
        Dict[str, Any]
            辞書表現
        """
        # 変換関数はシリアライズできないので、名前のみ保存
        bindings_dict = {}
        for layer_id, binding in self._bindings.items():
            binding_copy = binding.copy()
            if callable(binding_copy.get("transform")):
                binding_copy["transform"] = None
            bindings_dict[layer_id] = binding_copy
        
        return {
            "bindings": bindings_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DataConnector":
        """
        辞書から生成
        
        Parameters
        ----------
        data : Dict[str, Any]
            辞書表現
            
        Returns
        -------
        DataConnector
            生成されたデータコネクタ
        """
        connector = cls()
        
        bindings = data.get("bindings", {})
        for layer_id, binding in bindings.items():
            connector._bindings[layer_id] = binding
        
        return connector


class LayerEventManager:
    """
    レイヤーイベント管理クラス
    
    レイヤー間のイベント通知と同期を管理します。
    """
    
    def __init__(self):
        """初期化"""
        self._event_handlers = {}  # {event_name: [{layer_id, handler_fn, target_ids}]}
        self._event_targets = {}  # {layer_id: [target_layer_ids]}
    
    def subscribe(self, layer: BaseMapLayer, event_name: str, handler: Callable,
                 target_layers: List[BaseMapLayer] = None) -> None:
        """
        イベントをサブスクライブ
        
        Parameters
        ----------
        layer : BaseMapLayer
            サブスクライブするレイヤー
        event_name : str
            イベント名
        handler : Callable
            ハンドラ関数
        target_layers : List[BaseMapLayer], optional
            ターゲットレイヤーのリスト, by default None
        """
        if not layer:
            return
        
        # イベントハンドラの登録
        if event_name not in self._event_handlers:
            self._event_handlers[event_name] = []
        
        target_ids = []
        if target_layers:
            target_ids = [target.layer_id for target in target_layers if target]
        
        self._event_handlers[event_name].append({
            "layer_id": layer.layer_id,
            "handler": handler,
            "target_ids": target_ids
        })
        
        # ターゲット設定の更新
        for target_layer in (target_layers or []):
            if not target_layer:
                continue
                
            if target_layer.layer_id not in self._event_targets:
                self._event_targets[target_layer.layer_id] = []
            
            if layer.layer_id not in self._event_targets[target_layer.layer_id]:
                self._event_targets[target_layer.layer_id].append(layer.layer_id)
    
    def unsubscribe(self, layer: BaseMapLayer, event_name: str = None) -> None:
        """
        イベントのサブスクリプションを解除
        
        Parameters
        ----------
        layer : BaseMapLayer
            サブスクリプションを解除するレイヤー
        event_name : str, optional
            イベント名, by default None（すべてのイベント）
        """
        if not layer:
            return
        
        layer_id = layer.layer_id
        
        if event_name:
            # 特定のイベントのみ解除
            if event_name in self._event_handlers:
                self._event_handlers[event_name] = [
                    handler for handler in self._event_handlers[event_name]
                    if handler["layer_id"] != layer_id
                ]
        else:
            # すべてのイベントを解除
            for event_name in self._event_handlers:
                self._event_handlers[event_name] = [
                    handler for handler in self._event_handlers[event_name]
                    if handler["layer_id"] != layer_id
                ]
        
        # ターゲット設定の更新
        for target_id, subscribers in self._event_targets.items():
            if layer_id in subscribers:
                subscribers.remove(layer_id)
    
    def publish(self, layer: BaseMapLayer, event_name: str, event_data: Any = None) -> None:
        """
        イベントをパブリッシュ
        
        Parameters
        ----------
        layer : BaseMapLayer
            イベントを発行するレイヤー
        event_name : str
            イベント名
        event_data : Any, optional
            イベントデータ, by default None
        """
        if not layer or event_name not in self._event_handlers:
            return
        
        source_id = layer.layer_id
        
        # 該当するハンドラを呼び出し
        for handler_info in self._event_handlers[event_name]:
            handler = handler_info["handler"]
            layer_id = handler_info["layer_id"]
            target_ids = handler_info["target_ids"]
            
            if not target_ids or source_id in target_ids:
                try:
                    handler(layer, event_name, event_data)
                except Exception as e:
                    print(f"Event handler error: {e}")
    
    def get_layer_subscribers(self, layer: BaseMapLayer) -> List[str]:
        """
        レイヤーのサブスクライバーを取得
        
        Parameters
        ----------
        layer : BaseMapLayer
            レイヤー
            
        Returns
        -------
        List[str]
            サブスクライバーのレイヤーIDリスト
        """
        if not layer:
            return []
        
        return self._event_targets.get(layer.layer_id, []).copy()
    
    def clear(self) -> None:
        """
        すべてのイベントハンドラとターゲット設定をクリア
        """
        self._event_handlers.clear()
        self._event_targets.clear()


class DataSynchronizer:
    """
    データ同期クラス
    
    レイヤー間のデータ同期を管理します。
    """
    
    def __init__(self, data_connector: DataConnector = None, 
                event_manager: LayerEventManager = None):
        """
        初期化
        
        Parameters
        ----------
        data_connector : DataConnector, optional
            データコネクタ, by default None
        event_manager : LayerEventManager, optional
            イベントマネージャー, by default None
        """
        self.data_connector = data_connector or DataConnector()
        self.event_manager = event_manager or LayerEventManager()
        
        # 同期設定
        self._sync_pairs = []  # [(source_layer_id, target_layer_id, sync_config)]
    
    def add_sync_pair(self, source_layer: BaseMapLayer, target_layer: BaseMapLayer, 
                     field_mappings: Dict[str, str] = None,
                     transform: Union[str, Callable] = None,
                     bidirectional: bool = False) -> None:
        """
        同期ペアを追加
        
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
        
        # 同期設定
        sync_config = {
            "field_mappings": field_mappings or {},
            "transform": transform
        
        # 同期ペアを追加
        self._sync_pairs.append((source_layer.layer_id, target_layer.layer_id, sync_config))
        
        # イベントハンドラの登録
        self.event_manager.subscribe(
            source_layer,
            "data_changed",
            self._handle_data_change_event,
            [target_layer]
        )
        
        # 双方向同期の場合
        if bidirectional:
            self._sync_pairs.append((target_layer.layer_id, source_layer.layer_id, sync_config))
            
            self.event_manager.subscribe(
                target_layer,
                "data_changed",
                self._handle_data_change_event,
                [source_layer]
            )
    
    def remove_sync_pair(self, source_layer: BaseMapLayer, target_layer: BaseMapLayer) -> None:
        """
        同期ペアを削除
        
        Parameters
        ----------
        source_layer : BaseMapLayer
            ソースレイヤー
        target_layer : BaseMapLayer
            ターゲットレイヤー
        """
        if not source_layer or not target_layer:
            return
        
        # 同期ペアを削除
        self._sync_pairs = [
            pair for pair in self._sync_pairs
            if not (pair[0] == source_layer.layer_id and pair[1] == target_layer.layer_id)
        ]
        
        # イベントハンドラの解除
        self.event_manager.unsubscribe(source_layer, "data_changed")
    
    def _handle_data_change_event(self, source_layer: BaseMapLayer, event_name: str, 
                                 event_data: Any) -> None:
        """
        データ変更イベントハンドラ
        
        Parameters
        ----------
        source_layer : BaseMapLayer
            ソースレイヤー
        event_name : str
            イベント名
        event_data : Any
            イベントデータ
        """
        if not source_layer or event_name != "data_changed":
            return
        
        # 関連するターゲットレイヤーを同期
        for source_id, target_id, sync_config in self._sync_pairs:
            if source_id == source_layer.layer_id:
                # ターゲットレイヤーを検索して同期
                pass  # 実際の同期処理はレイヤーマネージャーを通じて行う
    
    def sync_layers(self, layer_manager, context: Dict[str, Any] = None) -> Dict[str, bool]:
        """
        レイヤーを同期
        
        Parameters
        ----------
        layer_manager
            レイヤーマネージャー
        context : Dict[str, Any], optional
            追加コンテキスト, by default None
            
        Returns
        -------
        Dict[str, bool]
            同期結果
        """
        results = {}
        context = context or {}
        
        # 同期ペアごとに処理
        for source_id, target_id, sync_config in self._sync_pairs:
            # ソースレイヤーとターゲットレイヤーを取得
            source_layer = layer_manager.get_layer(source_id)
            target_layer = layer_manager.get_layer(target_id)
            
            if not source_layer or not target_layer:
                continue
            
            # ソースレイヤーのデータを準備
            source_data = self.data_connector.prepare_layer_data(source_layer, context)
            
            if source_data is None:
                continue
            
            # ターゲットレイヤーのデータソースを更新
            field_mappings = sync_config.get("field_mappings")
            transform = sync_config.get("transform")
            
            # ソースデータをターゲット用に変換
            if isinstance(source_data, list):
                if field_mappings:
                    source_data = [self.data_connector.apply_field_mapping(item, field_mappings) for item in source_data]
                
                if transform:
                    source_data = [self.data_connector.transform_data(item, transform) for item in source_data]
            else:
                if field_mappings:
                    source_data = self.data_connector.apply_field_mapping(source_data, field_mappings)
                
                if transform:
                    source_data = self.data_connector.transform_data(source_data, transform)
            
            # ターゲットレイヤーのデータソースを更新
            target_source_id = target_layer.data_source
            if target_source_id:
                self.data_connector.update_data(target_source_id, source_data)
                
                # ターゲットレイヤーを同期
                result = self.data_connector.sync_layer_to_data(target_layer, context)
                results[target_id] = result
        
        return results
