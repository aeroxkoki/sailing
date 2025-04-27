# -*- coding: utf-8 -*-
"""
sailing_data_processor.reporting.elements.map.layers.layer_manager

マップレイヤーのマネージャークラスを提供するモジュールです。
このモジュールは、レイヤーの追加、削除、管理機能を定義します。
"""

from typing import Dict, List, Any, Optional, Union, Tuple, Set, Type
import json
import uuid
from collections import OrderedDict

from sailing_data_processor.reporting.elements.map.layers.base_layer import BaseMapLayer

class LayerManager:
    """
    マップレイヤーマネージャークラス
    
    複数のレイヤーを管理し、レイヤーの追加、削除、順序管理などの機能を提供します。
    """
    
    def __init__(self):
        """初期化"""
        # レイヤーの辞書 (ID -> レイヤーオブジェクト)
        self._layers = OrderedDict()
        
        # レイヤーグループの辞書 (グループ名 -> [レイヤーID])
        self._groups = {}
        
        # レイヤー依存関係
        self._dependencies = {}
    
    def __len__(self) -> int:
        """レイヤー数を取得"""
        return len(self._layers)
    
    def __iter__(self):
        """レイヤーをイテレート"""
        for layer in self._layers.values():
            yield layer
    
    def __contains__(self, layer_id: str) -> bool:
        """レイヤーの存在確認"""
        return layer_id in self._layers
    
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
        # レイヤーの追加
        self._layers[layer.layer_id] = layer
        
        # グループへの追加
        if group:
            if group not in self._groups:
                self._groups[group] = []
            
            if layer.layer_id not in self._groups[group]:
                self._groups[group].append(layer.layer_id)
        
        return layer.layer_id
    
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
        if layer_id not in self._layers:
            return None
        
        # レイヤーの取得と削除
        layer = self._layers.pop(layer_id)
        
        # グループからの削除
        for group_ids in self._groups.values():
            if layer_id in group_ids:
                group_ids.remove(layer_id)
        
        # 依存関係の削除
        if layer_id in self._dependencies:
            del self._dependencies[layer_id]
        
        # 子レイヤーも削除
        for child in list(layer.children):
            self.remove_layer(child.layer_id)
        
        return layer
    
    def get_layer(self, layer_id: str) -> Optional[BaseMapLayer]:
        """
        レイヤーを取得
        
        Parameters
        ----------
        layer_id : str
            レイヤーID
            
        Returns
        -------
        Optional[BaseMapLayer]
            レイヤーオブジェクト、存在しない場合はNone
        """
        return self._layers.get(layer_id)
    
    def get_layers(self, group: Optional[str] = None) -> List[BaseMapLayer]:
        """
        レイヤーのリストを取得
        
        Parameters
        ----------
        group : Optional[str], optional
            グループ名, by default None
            指定された場合、指定グループのレイヤーのみ返す
            
        Returns
        -------
        List[BaseMapLayer]
            レイヤーのリスト
        """
        if group is None:
            # すべてのレイヤー
            return list(self._layers.values())
        
        if group not in self._groups:
            return []
        
        # 指定グループのレイヤー
        return [self._layers[layer_id] for layer_id in self._groups[group]
                if layer_id in self._layers]
    
    def get_ordered_layers(self) -> List[BaseMapLayer]:
        """
        Z順序でソートされたレイヤーのリストを取得
        
        Returns
        -------
        List[BaseMapLayer]
            Z順序でソートされたレイヤーのリスト
        """
        layers = list(self._layers.values())
        return sorted(layers, key=lambda layer: layer.z_index)
    
    def create_group(self, group_name: str) -> None:
        """
        レイヤーグループを作成
        
        Parameters
        ----------
        group_name : str
            グループ名
        """
        if group_name not in self._groups:
            self._groups[group_name] = []
    
    def remove_group(self, group_name: str) -> None:
        """
        レイヤーグループを削除
        
        Parameters
        ----------
        group_name : str
            グループ名
        """
        if group_name in self._groups:
            del self._groups[group_name]
    
    def add_to_group(self, layer_id: str, group_name: str) -> bool:
        """
        レイヤーをグループに追加
        
        Parameters
        ----------
        layer_id : str
            レイヤーID
        group_name : str
            グループ名
            
        Returns
        -------
        bool
            追加に成功した場合True
        """
        if layer_id not in self._layers:
            return False
        
        if group_name not in self._groups:
            self._groups[group_name] = []
        
        if layer_id not in self._groups[group_name]:
            self._groups[group_name].append(layer_id)
        
        return True
    
    def remove_from_group(self, layer_id: str, group_name: str) -> bool:
        """
        レイヤーをグループから削除
        
        Parameters
        ----------
        layer_id : str
            レイヤーID
        group_name : str
            グループ名
            
        Returns
        -------
        bool
            削除に成功した場合True
        """
        if group_name not in self._groups:
            return False
        
        if layer_id in self._groups[group_name]:
            self._groups[group_name].remove(layer_id)
            return True
        
        return False
    
    def get_groups(self) -> List[str]:
        """
        グループ名のリストを取得
        
        Returns
        -------
        List[str]
            グループ名のリスト
        """
        return list(self._groups.keys())
    
    def get_group_layers(self, group_name: str) -> List[BaseMapLayer]:
        """
        指定グループのレイヤーリストを取得
        
        Parameters
        ----------
        group_name : str
            グループ名
            
        Returns
        -------
        List[BaseMapLayer]
            レイヤーのリスト
        """
        if group_name not in self._groups:
            return []
        
        return [self._layers[layer_id] for layer_id in self._groups[group_name]
                if layer_id in self._layers]
    
    def set_layer_z_index(self, layer_id: str, z_index: int) -> bool:
        """
        レイヤーのZ順序を設定
        
        Parameters
        ----------
        layer_id : str
            レイヤーID
        z_index : int
            Z順序
            
        Returns
        -------
        bool
            設定に成功した場合True
        """
        if layer_id not in self._layers:
            return False
        
        self._layers[layer_id].z_index = z_index
        return True
    
    def move_layer_up(self, layer_id: str) -> bool:
        """
        レイヤーを上に移動（Z順序を大きくする）
        
        Parameters
        ----------
        layer_id : str
            レイヤーID
            
        Returns
        -------
        bool
            移動に成功した場合True
        """
        if layer_id not in self._layers:
            return False
        
        layer = self._layers[layer_id]
        current_z = layer.z_index
        
        # 現在よりZ順序が大きいレイヤーを探す
        higher_layers = [l for l in self._layers.values() if l.z_index > current_z]
        
        if not higher_layers:
            # すでに最上位の場合
            return False
        
        # Z順序が一つ上のレイヤーを探す
        next_z = min(l.z_index for l in higher_layers)
        next_layer = next(l for l in higher_layers if l.z_index == next_z)
        
        # Z順序を交換
        layer.z_index, next_layer.z_index = next_z, current_z
        
        return True
    
    def move_layer_down(self, layer_id: str) -> bool:
        """
        レイヤーを下に移動（Z順序を小さくする）
        
        Parameters
        ----------
        layer_id : str
            レイヤーID
            
        Returns
        -------
        bool
            移動に成功した場合True
        """
        if layer_id not in self._layers:
            return False
        
        layer = self._layers[layer_id]
        current_z = layer.z_index
        
        # 現在よりZ順序が小さいレイヤーを探す
        lower_layers = [l for l in self._layers.values() if l.z_index < current_z]
        
        if not lower_layers:
            # すでに最下位の場合
            return False
        
        # Z順序が一つ下のレイヤーを探す
        prev_z = max(l.z_index for l in lower_layers)
        prev_layer = next(l for l in lower_layers if l.z_index == prev_z)
        
        # Z順序を交換
        layer.z_index, prev_layer.z_index = prev_z, current_z
        
        return True
    
    def reorder_layers(self, layer_ids: List[str]) -> bool:
        """
        レイヤーの順序を再設定
        
        Parameters
        ----------
        layer_ids : List[str]
            レイヤーIDのリスト（新しい順序）
            
        Returns
        -------
        bool
            再設定に成功した場合True
        """
        if not all(layer_id in self._layers for layer_id in layer_ids):
            return False
        
        # 順序に合わせてZ順序を設定
        for i, layer_id in enumerate(layer_ids):
            self._layers[layer_id].z_index = i
        
        return True
    
    def set_layer_visibility(self, layer_id: str, visible: bool) -> bool:
        """
        レイヤーの可視性を設定
        
        Parameters
        ----------
        layer_id : str
            レイヤーID
        visible : bool
            可視性
            
        Returns
        -------
        bool
            設定に成功した場合True
        """
        if layer_id not in self._layers:
            return False
        
        self._layers[layer_id].visible = visible
        return True
    
    def set_group_visibility(self, group_name: str, visible: bool) -> bool:
        """
        グループの可視性を設定
        
        Parameters
        ----------
        group_name : str
            グループ名
        visible : bool
            可視性
            
        Returns
        -------
        bool
            設定に成功した場合True
        """
        if group_name not in self._groups:
            return False
        
        for layer_id in self._groups[group_name]:
            if layer_id in self._layers:
                self._layers[layer_id].visible = visible
        
        return True
    
    def add_dependency(self, layer_id: str, depends_on: str) -> bool:
        """
        レイヤー間の依存関係を追加
        
        Parameters
        ----------
        layer_id : str
            依存するレイヤーのID
        depends_on : str
            依存されるレイヤーのID
            
        Returns
        -------
        bool
            追加に成功した場合True
        """
        if layer_id not in self._layers or depends_on not in self._layers:
            return False
        
        if layer_id not in self._dependencies:
            self._dependencies[layer_id] = set()
        
        self._dependencies[layer_id].add(depends_on)
        return True
    
    def get_dependencies(self, layer_id: str) -> Set[str]:
        """
        レイヤーの依存関係を取得
        
        Parameters
        ----------
        layer_id : str
            レイヤーID
            
        Returns
        -------
        Set[str]
            依存するレイヤーIDのセット
        """
        if layer_id not in self._dependencies:
            return set()
        
        return self._dependencies[layer_id].copy()
    
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
        if context is None:
            context = {}
        
        # Z順序でソート
        ordered_layers = self.get_ordered_layers()
        
        # 各レイヤーのレンダリングコード
        render_codes = []
        
        # 変数定義部分
        var_defs = []
        var_defs.append(f"// レイヤー管理用オブジェクト")
        var_defs.append(f"var layerManager = {}};")
        
        for layer in ordered_layers:
            if not layer.visible:
                continue
            
            # データの準備
            layer_data = layer.prepare_data(context)
            
            # データがあれば変数定義
            if layer_data:
                data_var = f"data_{layer.layer_id}"
                data_json = json.dumps(layer_data)
                var_defs.append(f"var {data_var} = {data_json};")
            
            # レイヤー変数名
            layer_var = f"layer_{layer.layer_id}"
            var_defs.append(f"var {layer_var};")
        
        # レンダリングコード
        render_codes.append("// レイヤーの作成と追加")
        
        for layer in ordered_layers:
            if not layer.visible:
                continue
            
            # レイヤー変数名
            layer_var = f"layer_{layer.layer_id}"
            
            # レイヤーのレンダリングコード
            layer_code = layer.render_layer(map_var)
            render_codes.append(layer_code)
            
            # レイヤーマネージャーへの登録
            render_codes.append(f"layerManager['{layer.layer_id}'] = {layer_var};")
        
        # 最終コード
        code = "\n".join(var_defs) + "\n\n" + "\n".join(render_codes)
        
        return code
    
    def to_dict(self) -> Dict[str, Any]:
        """
        レイヤーマネージャーの辞書表現を取得
        
        Returns
        -------
        Dict[str, Any]
            レイヤーマネージャーの辞書表現
        """
        return {
            "layers": layer_id: layer.to_dict() for layer_id, layer in self._layers.items()},
            "groups": {group_name: group_ids[:] for group_name, group_ids in self._groups.items()},
            "dependencies": {layer_id: list(deps) for layer_id, deps in self._dependencies.items()}
 {
            "layers": layer_id: layer.to_dict() for layer_id, layer in self._layers.items()},
            "groups": {group_name: group_ids[:] for group_name, group_ids in self._groups.items()},
            "dependencies": {layer_id: list(deps) for layer_id, deps in self._dependencies.items()}}
        return {
            "layers": layer_id: layer.to_dict() for layer_id, layer in self._layers.items()},
            "groups": {group_name: group_ids[:] for group_name, group_ids in self._groups.items()},
            "dependencies": {layer_id: list(deps) for layer_id, deps in self._dependencies.items()}}
 {
            "layers": layer_id: layer.to_dict() for layer_id, layer in self._layers.items()},
            "groups": {group_name: group_ids[:] for group_name, group_ids in self._groups.items()},
            "dependencies": {layer_id: list(deps) for layer_id, deps in self._dependencies.items()}}}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], layer_classes: Dict[str, Type[BaseMapLayer]]) -> "LayerManager":
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
        LayerManager
            生成されたレイヤーマネージャー
        """
        manager = cls()
        
        # レイヤーの復元
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
        
        return manager
