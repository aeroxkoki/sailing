"""
sailing_data_processor.reporting.elements.map.layers.base_layer

マップレイヤーの基底クラスを提供するモジュールです。
このモジュールは、すべてのマップレイヤーに共通する機能を定義します。
"""

from typing import Dict, List, Any, Optional, Union, Tuple, Set, Callable
import json
import uuid
from abc import ABC, abstractmethod

class BaseMapLayer(ABC):
    """
    マップレイヤーの基底クラス
    
    すべてのマップレイヤータイプに共通する機能を提供します。
    """
    
    def __init__(self, layer_id: Optional[str] = None, name: str = "unnamed_layer", 
                description: str = "", **kwargs):
        """
        初期化
        
        Parameters
        ----------
        layer_id : Optional[str], optional
            レイヤーID, by default None
        name : str, optional
            レイヤー名, by default "unnamed_layer"
        description : str, optional
            レイヤーの説明, by default ""
        **kwargs : dict
            追加のプロパティ
        """
        # 一意なレイヤーIDを生成
        self.layer_id = layer_id if layer_id else f"layer_{str(uuid.uuid4())[:8]}"
        self.name = name
        self.description = description
        
        # 基本プロパティ
        self._properties = {
            "visible": kwargs.get("visible", True),
            "opacity": kwargs.get("opacity", 1.0),
            "z_index": kwargs.get("z_index", 0),
            "selectable": kwargs.get("selectable", True),
            "interactive": kwargs.get("interactive", True),
            "data_source": kwargs.get("data_source", None),
        }
        
        # スタイル設定
        self._styles = {}
        
        # 子レイヤー関連
        self._parent = None
        self._children = set()
        
        # イベントハンドラ
        self._event_handlers = {}
        
        # その他のプロパティを追加
        for key, value in kwargs.items():
            if key not in self._properties:
                self._properties[key] = value
    
    def __repr__(self) -> str:
        """オブジェクトの文字列表現"""
        return f"<{self.__class__.__name__} {self.layer_id}: {self.name}>"
    
    @property
    def visible(self) -> bool:
        """レイヤーの表示状態"""
        return self._properties.get("visible", True)
    
    @visible.setter
    def visible(self, value: bool) -> None:
        """レイヤーの表示状態を設定"""
        self._properties["visible"] = bool(value)
    
    @property
    def opacity(self) -> float:
        """レイヤーの不透明度 (0.0～1.0)"""
        return self._properties.get("opacity", 1.0)
    
    @opacity.setter
    def opacity(self, value: float) -> None:
        """レイヤーの不透明度を設定"""
        self._properties["opacity"] = max(0.0, min(1.0, float(value)))
    
    @property
    def z_index(self) -> int:
        """レイヤーのZ順序"""
        return self._properties.get("z_index", 0)
    
    @z_index.setter
    def z_index(self, value: int) -> None:
        """レイヤーのZ順序を設定"""
        self._properties["z_index"] = int(value)
    
    @property
    def data_source(self) -> Optional[str]:
        """データソース名"""
        return self._properties.get("data_source")
    
    @data_source.setter
    def data_source(self, value: Optional[str]) -> None:
        """データソース名を設定"""
        self._properties["data_source"] = value
    
    @property
    def parent(self):
        """親レイヤー"""
        return self._parent
    
    @parent.setter
    def parent(self, parent_layer) -> None:
        """親レイヤーを設定"""
        # 現在の親から削除
        if self._parent:
            self._parent._children.discard(self)
        
        # 新しい親を設定
        self._parent = parent_layer
        
        # 新しい親の子に追加
        if parent_layer:
            parent_layer._children.add(self)
    
    @property
    def children(self) -> Set["BaseMapLayer"]:
        """子レイヤーのセット"""
        return self._children.copy()
    
    def add_child(self, child_layer: "BaseMapLayer") -> None:
        """
        子レイヤーを追加
        
        Parameters
        ----------
        child_layer : BaseMapLayer
            追加する子レイヤー
        """
        child_layer.parent = self
    
    def remove_child(self, child_layer: "BaseMapLayer") -> None:
        """
        子レイヤーを削除
        
        Parameters
        ----------
        child_layer : BaseMapLayer
            削除する子レイヤー
        """
        if child_layer in self._children:
            child_layer._parent = None
            self._children.discard(child_layer)
    
    def get_property(self, key: str, default: Any = None) -> Any:
        """
        プロパティ値を取得
        
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
        return self._properties.get(key, default)
    
    def set_property(self, key: str, value: Any) -> None:
        """
        プロパティ値を設定
        
        Parameters
        ----------
        key : str
            プロパティキー
        value : Any
            プロパティ値
        """
        self._properties[key] = value
    
    def get_style(self, key: str, default: Any = None) -> Any:
        """
        スタイル値を取得
        
        Parameters
        ----------
        key : str
            スタイルキー
        default : Any, optional
            デフォルト値, by default None
            
        Returns
        -------
        Any
            スタイル値
        """
        return self._styles.get(key, default)
    
    def set_style(self, key: str, value: Any) -> None:
        """
        スタイル値を設定
        
        Parameters
        ----------
        key : str
            スタイルキー
        value : Any
            スタイル値
        """
        self._styles[key] = value
    
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
        イベントハンドラを削除
        
        Parameters
        ----------
        event_name : str
            イベント名
        handler : Optional[Callable], optional
            ハンドラ関数, by default None
            Noneの場合は指定イベントのすべてのハンドラを削除
        """
        if event_name not in self._event_handlers:
            return
        
        if handler is None:
            # すべてのハンドラを削除
            self._event_handlers[event_name] = []
        else:
            # 特定のハンドラを削除
            self._event_handlers[event_name] = [
                h for h in self._event_handlers[event_name] if h != handler
            ]
    
    def trigger(self, event_name: str, event_data: Any = None) -> None:
        """
        イベントをトリガー
        
        Parameters
        ----------
        event_name : str
            イベント名
        event_data : Any, optional
            イベントデータ, by default None
        """
        if event_name in self._event_handlers:
            for handler in self._event_handlers[event_name]:
                handler(self, event_data)
    
    def get_bounds(self) -> Optional[Tuple[Tuple[float, float], Tuple[float, float]]]:
        """
        レイヤーの境界ボックスを取得
        
        Returns
        -------
        Optional[Tuple[Tuple[float, float], Tuple[float, float]]]
            ((min_lat, min_lng), (max_lat, max_lng))の形式の境界ボックス
            または境界が定義できない場合はNone
        """
        # デフォルトでは境界がないためNoneを返す
        # サブクラスで実装する必要がある
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        レイヤーの辞書表現を取得
        
        Returns
        -------
        Dict[str, Any]
            レイヤーの辞書表現
        """
        return {
            "layer_id": self.layer_id,
            "name": self.name,
            "description": self.description,
            "type": self.__class__.__name__,
            "properties": self._properties.copy(),
            "styles": self._styles.copy()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaseMapLayer":
        """
        辞書からレイヤーを生成
        
        Parameters
        ----------
        data : Dict[str, Any]
            レイヤーの辞書表現
            
        Returns
        -------
        BaseMapLayer
            生成されたレイヤー
        """
        layer = cls(
            layer_id=data.get("layer_id"),
            name=data.get("name", "unnamed_layer"),
            description=data.get("description", "")
        )
        
        # プロパティを復元
        properties = data.get("properties", {})
        for key, value in properties.items():
            layer.set_property(key, value)
        
        # スタイルを復元
        styles = data.get("styles", {})
        for key, value in styles.items():
            layer.set_style(key, value)
        
        return layer
    
    @abstractmethod
    def render_layer(self, map_var: str = "map") -> str:
        """
        レイヤーのレンダリングコードを生成
        
        Parameters
        ----------
        map_var : str, optional
            マップ変数名, by default "map"
            
        Returns
        -------
        str
            レイヤーをレンダリングするJavaScriptコード
        """
        pass
    
    def prepare_data(self, context: Dict[str, Any]) -> Any:
        """
        データを準備
        
        Parameters
        ----------
        context : Dict[str, Any]
            レンダリングコンテキスト
            
        Returns
        -------
        Any
            準備されたデータ
        """
        # データソースからデータを取得
        if self.data_source and self.data_source in context:
            return context[self.data_source]
        
        return None
