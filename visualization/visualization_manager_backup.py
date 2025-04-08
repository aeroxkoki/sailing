"""
visualization.visualization_manager

可視化コンポーネントの全体管理を行うモジュールです。
異なる可視化コンポーネント（マップ、チャート、タイムライン等）を統合的に管理し、
それらの間の連携を調整します。
"""

import streamlit as st
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
import json

class VisualizationManager:
    """
    可視化コンポーネントの管理クラス
    
    異なる可視化コンポーネント間の連携・同期やレイアウト管理を行います。
    """
    
    def __init__(self):
        """初期化"""
        # コンポーネントの登録辞書
        self._components = {}
        
        # コンポーネント間の同期設定
        self._sync_links = []
        
        # レイアウト設定
        self._layout_config = {
            "layout_type": "default",  # "default", "map_focused", "chart_focused", "split"
            "visible_components": [],  # 表示するコンポーネントのIDリスト
            "sizes": {}  # コンポーネントIDをキーとする相対サイズ辞書
        }
        
        # 共有データコンテキスト
        self._data_context = {}
        
        # 選択状態の共有
        self._selection_context = {
            "selected_time": None,
            "selected_point": None,
            "selected_range": None,
            "selected_items": []
        }
    
    def register_component(self, component_id: str, component: Any, component_type: str) -> None:
        """
        可視化コンポーネントを登録
        
        Parameters
        ----------
        component_id : str
            コンポーネントの一意ID
        component : Any
            コンポーネントオブジェクト
        component_type : str
            コンポーネントのタイプ（"map", "chart", "timeline", ...）
        """
        self._components[component_id] = {
            "component": component,
            "type": component_type,
            "visible": True,
            "position": len(self._components)
        }
        
        # デフォルトで表示コンポーネントに追加
        if component_id not in self._layout_config["visible_components"]:
            self._layout_config["visible_components"].append(component_id)
    
    def unregister_component(self, component_id: str) -> bool:
        """
        コンポーネントの登録を解除
        
        Parameters
        ----------
        component_id : str
            登録解除するコンポーネントのID
            
        Returns
        -------
        bool
            登録解除に成功した場合True
        """
        if component_id in self._components:
            del self._components[component_id]
            
            # 同期リンクからも削除
            self._sync_links = [link for link in self._sync_links 
                               if link["source_id"] != component_id and link["target_id"] != component_id]
            
            # レイアウト設定からも削除
            if component_id in self._layout_config["visible_components"]:
                self._layout_config["visible_components"].remove(component_id)
            
            if component_id in self._layout_config["sizes"]:
                del self._layout_config["sizes"][component_id]
            
            return True
        
        return False
    
    def get_component(self, component_id: str) -> Optional[Any]:
        """
        登録済みコンポーネントを取得
        
        Parameters
        ----------
        component_id : str
            取得するコンポーネントのID
            
        Returns
        -------
        Optional[Any]
            コンポーネントオブジェクト、なければNone
        """
        component_info = self._components.get(component_id)
        return component_info["component"] if component_info else None
    
    def get_all_components(self) -> Dict[str, Dict]:
        """
        全登録コンポーネントの情報を取得
        
        Returns
        -------
        Dict[str, Dict]
            コンポーネントIDをキー、コンポーネント情報を値とする辞書
        """
        return self._components
    
    def set_layout(self, layout_type: str, visible_components: Optional[List[str]] = None) -> None:
        """
        レイアウト設定を変更
        
        Parameters
        ----------
        layout_type : str
            レイアウトタイプ
        visible_components : Optional[List[str]], optional
            表示するコンポーネントIDのリスト
        """
        self._layout_config["layout_type"] = layout_type
        
        if visible_components is not None:
            self._layout_config["visible_components"] = [
                comp_id for comp_id in visible_components if comp_id in self._components
            ]
    
    def set_component_visibility(self, component_id: str, visible: bool) -> bool:
        """
        コンポーネントの表示/非表示を設定
        
        Parameters
        ----------
        component_id : str
            表示設定を変更するコンポーネントID
        visible : bool
            表示する場合True、非表示の場合False
            
        Returns
        -------
        bool
            設定変更に成功した場合True
        """
        if component_id in self._components:
            self._components[component_id]["visible"] = visible
            
            # 表示コンポーネントリストも更新
            if visible and component_id not in self._layout_config["visible_components"]:
                self._layout_config["visible_components"].append(component_id)
            elif not visible and component_id in self._layout_config["visible_components"]:
                self._layout_config["visible_components"].remove(component_id)
            
            return True
        
        return False
    
    def set_component_sizes(self, sizes: Dict[str, float]) -> None:
        """
        コンポーネントの相対サイズを設定
        
        Parameters
        ----------
        sizes : Dict[str, float]
            コンポーネントIDをキー、相対サイズを値とする辞書
        """
        # 有効なコンポーネントIDのみ設定を更新
        for comp_id, size in sizes.items():
            if comp_id in self._components:
                self._layout_config["sizes"][comp_id] = float(size)
    
    def add_sync_link(self, source_id: str, target_id: str, 
                     properties: List[str], bidirectional: bool = False) -> bool:
        """
        コンポーネント間の同期リンクを追加
        
        Parameters
        ----------
        source_id : str
            ソースコンポーネントID
        target_id : str
            ターゲットコンポーネントID
        properties : List[str]
            同期するプロパティのリスト
        bidirectional : bool, optional
            双方向同期の場合True
            
        Returns
        -------
        bool
            リンク追加に成功した場合True
        """
        if source_id in self._components and target_id in self._components:
            # 同じリンクが既に存在するか確認
            for link in self._sync_links:
                if (link["source_id"] == source_id and link["target_id"] == target_id and
                    set(link["properties"]) == set(properties)):
                    # 既存のリンクを更新
                    link["bidirectional"] = bidirectional
                    return True
            
            # 新しいリンクを追加
            self._sync_links.append({
                "source_id": source_id,
                "target_id": target_id,
                "properties": properties,
                "bidirectional": bidirectional
            })
            
            return True
        
        return False
    
    def remove_sync_link(self, source_id: str, target_id: str, 
                        properties: Optional[List[str]] = None) -> bool:
        """
        同期リンクを削除
        
        Parameters
        ----------
        source_id : str
            ソースコンポーネントID
        target_id : str
            ターゲットコンポーネントID
        properties : Optional[List[str]], optional
            削除するプロパティのリスト。Noneの場合はすべてのプロパティのリンクを削除
            
        Returns
        -------
        bool
            リンク削除に成功した場合True
        """
        # 削除するリンクを検索
        for i, link in enumerate(self._sync_links):
            if link["source_id"] == source_id and link["target_id"] == target_id:
                if properties is None:
                    # すべてのプロパティのリンクを削除
                    self._sync_links.pop(i)
                    return True
                else:
                    # 指定されたプロパティのみリンクから削除
                    link["properties"] = [p for p in link["properties"] if p not in properties]
                    
                    # プロパティがなくなったらリンク自体を削除
                    if not link["properties"]:
                        self._sync_links.pop(i)
                    
                    return True
        
        return False
    
    def propagate_change(self, source_id: str, property_name: str, value: Any) -> None:
        """
        コンポーネントの変更を関連コンポーネントに伝播
        
        Parameters
        ----------
        source_id : str
            変更ソースのコンポーネントID
        property_name : str
            変更されたプロパティ名
        value : Any
            新しい値
        """
        # 変更を共有コンテキストに記録
        if property_name == "selected_time":
            self._selection_context["selected_time"] = value
        elif property_name == "selected_point":
            self._selection_context["selected_point"] = value
        elif property_name == "selected_range":
            self._selection_context["selected_range"] = value
        elif property_name == "selected_items":
            self._selection_context["selected_items"] = value
        
        # リンクされたコンポーネントに変更を伝播
        for link in self._sync_links:
            # ソースからターゲットへの伝播
            if link["source_id"] == source_id and property_name in link["properties"]:
                target_comp = self.get_component(link["target_id"])
                if target_comp and hasattr(target_comp, f"set_{property_name}"):
                    # set_プロパティ名 メソッドがあれば呼び出し
                    getattr(target_comp, f"set_{property_name}")(value)
            
            # 双方向リンクの場合、ターゲットからソースへの伝播も考慮
            if link["bidirectional"] and link["target_id"] == source_id and property_name in link["properties"]:
                source_comp = self.get_component(link["source_id"])
                if source_comp and hasattr(source_comp, f"set_{property_name}"):
                    getattr(source_comp, f"set_{property_name}")(value)
    
    def set_data_context(self, data_key: str, data: Any) -> None:
        """
        共有データコンテキストにデータを設定
        
        Parameters
        ----------
        data_key : str
            データのキー
        data : Any
            データ値
        """
        self._data_context[data_key] = data
    
    def get_data_context(self, data_key: str) -> Optional[Any]:
        """
        共有データコンテキストからデータを取得
        
        Parameters
        ----------
        data_key : str
            取得するデータのキー
            
        Returns
        -------
        Optional[Any]
            データ値、キーが存在しない場合はNone
        """
        return self._data_context.get(data_key)
    
    def get_all_data_context(self) -> Dict[str, Any]:
        """
        全データコンテキストを取得
        
        Returns
        -------
        Dict[str, Any]
            データコンテキスト全体
        """
        return self._data_context
    
    def render_layout(self) -> None:
        """
        現在のレイアウト設定に基づいてコンポーネントをレンダリング
        """
        layout_type = self._layout_config["layout_type"]
        visible_components = self._layout_config["visible_components"]
        
        # 表示するコンポーネントのみに絞る
        components_to_render = {
            comp_id: self._components[comp_id]
            for comp_id in visible_components
            if comp_id in self._components and self._components[comp_id]["visible"]
        }
        
        if not components_to_render:
            st.warning("表示するコンポーネントがありません。")
            return
        
        # レイアウトタイプに基づいてレンダリング
        if layout_type == "default":
            # デフォルトレイアウト: すべて縦に並べる
            for comp_id, comp_info in components_to_render.items():
                with st.container():
                    st.subheader(comp_info.get("component").name if hasattr(comp_info.get("component"), "name") else comp_id)
                    comp_info.get("component").render()
        
        elif layout_type == "map_focused":
            # マップフォーカスレイアウト: マップが大きく、他は小さく
            map_components = {k: v for k, v in components_to_render.items() if v["type"] == "map"}
            other_components = {k: v for k, v in components_to_render.items() if v["type"] != "map"}
            
            # マップコンポーネントを表示
            for comp_id, comp_info in map_components.items():
                with st.container():
                    st.subheader(comp_info.get("component").name if hasattr(comp_info.get("component"), "name") else comp_id)
                    comp_info.get("component").render()
            
            # 他のコンポーネントを並べて表示
            if other_components:
                cols = st.columns(len(other_components))
                for i, (comp_id, comp_info) in enumerate(other_components.items()):
                    with cols[i]:
                        st.subheader(comp_info.get("component").name if hasattr(comp_info.get("component"), "name") else comp_id)
                        comp_info.get("component").render()
        
        elif layout_type == "chart_focused":
            # チャートフォーカスレイアウト: チャートが大きく、他は小さく
            chart_components = {k: v for k, v in components_to_render.items() if v["type"] == "chart"}
            other_components = {k: v for k, v in components_to_render.items() if v["type"] != "chart"}
            
            # チャートコンポーネントを表示
            for comp_id, comp_info in chart_components.items():
                with st.container():
                    st.subheader(comp_info.get("component").name if hasattr(comp_info.get("component"), "name") else comp_id)
                    comp_info.get("component").render()
            
            # 他のコンポーネントを並べて表示
            if other_components:
                cols = st.columns(len(other_components))
                for i, (comp_id, comp_info) in enumerate(other_components.items()):
                    with cols[i]:
                        st.subheader(comp_info.get("component").name if hasattr(comp_info.get("component"), "name") else comp_id)
                        comp_info.get("component").render()
        
        elif layout_type == "split":
            # 分割レイアウト: 2列に分ける
            half = len(components_to_render) // 2
            left_components = dict(list(components_to_render.items())[:half])
            right_components = dict(list(components_to_render.items())[half:])
            
            col1, col2 = st.columns(2)
            
            # 左側のコンポーネント
            with col1:
                for comp_id, comp_info in left_components.items():
                    st.subheader(comp_info.get("component").name if hasattr(comp_info.get("component"), "name") else comp_id)
                    comp_info.get("component").render()
            
            # 右側のコンポーネント
            with col2:
                for comp_id, comp_info in right_components.items():
                    st.subheader(comp_info.get("component").name if hasattr(comp_info.get("component"), "name") else comp_id)
                    comp_info.get("component").render()
        
        else:
            # カスタムレイアウト（サイズ指定がある場合）
            if self._layout_config["sizes"]:
                # サイズに基づいてカスタムカラムを作成
                size_components = {
                    comp_id: comp_info
                    for comp_id, comp_info in components_to_render.items()
                    if comp_id in self._layout_config["sizes"]
                }
                
                if size_components:
                    # サイズの合計を計算
                    total_size = sum(self._layout_config["sizes"].get(comp_id, 1) 
                                    for comp_id in size_components.keys())
                    
                    # 相対サイズを計算
                    rel_sizes = [self._layout_config["sizes"].get(comp_id, 1) / total_size
                                for comp_id in size_components.keys()]
                    
                    # カラムを作成
                    cols = st.columns(rel_sizes)
                    
                    # 各カラムにコンポーネントをレンダリング
                    for i, (comp_id, comp_info) in enumerate(size_components.items()):
                        with cols[i]:
                            st.subheader(comp_info.get("component").name if hasattr(comp_info.get("component"), "name") else comp_id)
                            comp_info.get("component").render()
                
                # サイズ指定のないコンポーネント
                other_components = {
                    comp_id: comp_info
                    for comp_id, comp_info in components_to_render.items()
                    if comp_id not in self._layout_config["sizes"]
                }
                
                # サイズ指定なしのコンポーネントは縦に並べる
                for comp_id, comp_info in other_components.items():
                    with st.container():
                        st.subheader(comp_info.get("component").name if hasattr(comp_info.get("component"), "name") else comp_id)
                        comp_info.get("component").render()
            else:
                # サイズ指定がなければデフォルトと同じ
                for comp_id, comp_info in components_to_render.items():
                    with st.container():
                        st.subheader(comp_info.get("component").name if hasattr(comp_info.get("component"), "name") else comp_id)
                        comp_info.get("component").render()
    
    def to_dict(self) -> Dict:
        """
        現在の設定を辞書として出力
        
        Returns
        -------
        Dict
            現在の設定を含む辞書
        """
        return {
            "components": {
                comp_id: {
                    "type": comp_info["type"],
                    "visible": comp_info["visible"],
                    "position": comp_info["position"]
                } for comp_id, comp_info in self._components.items()
            },
            "sync_links": self._sync_links,
            "layout_config": self._layout_config,
        }
    
    def from_dict(self, config_dict: Dict) -> None:
        """
        辞書から設定を読み込み
        
        Parameters
        ----------
        config_dict : Dict
            設定を含む辞書
        """
        # レイアウト設定の読み込み
        if "layout_config" in config_dict:
            self._layout_config = config_dict["layout_config"]
        
        # 同期リンクの読み込み
        if "sync_links" in config_dict:
            self._sync_links = config_dict["sync_links"]
    
    def save_config(self, filepath: str) -> bool:
        """
        設定をJSONファイルに保存
        
        Parameters
        ----------
        filepath : str
            保存先ファイルパス
            
        Returns
        -------
        bool
            保存に成功した場合True
        """
        try:
            config = self.to_dict()
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            st.error(f"設定の保存に失敗しました: {str(e)}")
            return False
    
    def load_config(self, filepath: str) -> bool:
        """
        設定をJSONファイルから読み込み
        
        Parameters
        ----------
        filepath : str
            読み込むファイルパス
            
        Returns
        -------
        bool
            読み込みに成功した場合True
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                config = json.load(f)
            self.from_dict(config)
            return True
        except Exception as e:
            st.error(f"設定の読み込みに失敗しました: {str(e)}")
            return False
