"""
sailing_data_processor.visualization.visualization_sync

可視化コンポーネント間の同期を管理するモジュールです。
マップ、チャート、グラフなどの可視化コンポーネント間のデータや選択状態の同期を管理します。
"""

import uuid
from typing import Dict, List, Any, Optional, Union, Callable, Set, Tuple
from datetime import datetime
import streamlit as st

class SyncConnection:
    """
    可視化コンポーネント間の同期接続を表すクラス
    """
    
    def __init__(self, source_id: str, target_id: str, sync_types: List[str] = None, 
                bidirectional: bool = False, enabled: bool = True):
        """
        初期化
        
        Parameters
        ----------
        source_id : str
            ソースコンポーネントID
        target_id : str
            ターゲットコンポーネントID
        sync_types : List[str], optional
            同期する対象のタイプリスト (例: ["selection", "time", "zoom"])
        bidirectional : bool, optional
            双方向同期を行うかどうか、デフォルトはFalse
        enabled : bool, optional
            同期が有効かどうか、デフォルトはTrue
        """
        self.source_id = source_id
        self.target_id = target_id
        self.sync_types = sync_types or ["selection", "time"]  # デフォルトでは選択と時間を同期
        self.bidirectional = bidirectional
        self.enabled = enabled
        self.connection_id = str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        """
        辞書表現へ変換
        
        Returns
        -------
        Dict[str, Any]
            接続情報を表す辞書
        """
        return {
            "connection_id": self.connection_id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "sync_types": self.sync_types,
            "bidirectional": self.bidirectional,
            "enabled": self.enabled
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SyncConnection":
        """
        辞書から接続オブジェクトを生成
        
        Parameters
        ----------
        data : Dict[str, Any]
            接続情報を表す辞書
            
        Returns
        -------
        SyncConnection
            生成された接続オブジェクト
        """
        connection = cls(
            source_id=data["source_id"],
            target_id=data["target_id"],
            sync_types=data.get("sync_types", ["selection", "time"]),
            bidirectional=data.get("bidirectional", False),
            enabled=data.get("enabled", True)
        )
        if "connection_id" in data:
            connection.connection_id = data["connection_id"]
        return connection


class VisualizationSynchronizer:
    """
    可視化コンポーネント間の同期を管理するクラス
    """
    
    def __init__(self, name: str = "Visualization Synchronizer"):
        """
        初期化
        
        Parameters
        ----------
        name : str, optional
            同期マネージャーの名前
        """
        self.name = name
        self.connections: Dict[str, SyncConnection] = {}  # 接続ID -> 接続オブジェクト
        self.components: Set[str] = set()  # コンポーネントIDのセット
        self.last_values: Dict[str, Dict[str, Any]] = {}  # コンポーネントID -> {同期タイプ -> 値}
        self.propagation_in_progress = False  # 伝播ループ防止フラグ
    
    def register_component(self, component_id: str) -> None:
        """
        同期対象のコンポーネントを登録
        
        Parameters
        ----------
        component_id : str
            登録するコンポーネントID
        """
        self.components.add(component_id)
        if component_id not in self.last_values:
            self.last_values[component_id] = {}
    
    def unregister_component(self, component_id: str) -> None:
        """
        コンポーネントの登録を解除
        
        Parameters
        ----------
        component_id : str
            登録解除するコンポーネントID
        """
        if component_id in self.components:
            self.components.remove(component_id)
        
        # 関連する接続を削除
        connections_to_remove = []
        for connection_id, connection in self.connections.items():
            if connection.source_id == component_id or connection.target_id == component_id:
                connections_to_remove.append(connection_id)
        
        for connection_id in connections_to_remove:
            del self.connections[connection_id]
        
        # 最終値の記録も削除
        if component_id in self.last_values:
            del self.last_values[component_id]
    
    def add_connection(self, source_id: str, target_id: str, sync_types: List[str] = None,
                      bidirectional: bool = False) -> Optional[str]:
        """
        コンポーネント間の同期接続を追加
        
        Parameters
        ----------
        source_id : str
            ソースコンポーネントID
        target_id : str
            ターゲットコンポーネントID
        sync_types : List[str], optional
            同期する対象のタイプリスト
        bidirectional : bool, optional
            双方向同期を行うかどうか
            
        Returns
        -------
        Optional[str]
            生成された接続ID、失敗時はNone
        """
        if source_id not in self.components or target_id not in self.components:
            return None
        
        # 接続オブジェクトを作成
        connection = SyncConnection(
            source_id=source_id,
            target_id=target_id,
            sync_types=sync_types,
            bidirectional=bidirectional
        )
        
        # 接続を登録
        self.connections[connection.connection_id] = connection
        
        # 逆方向の接続も追加（双方向の場合）
        if bidirectional:
            reverse_connection = SyncConnection(
                source_id=target_id,
                target_id=source_id,
                sync_types=sync_types,
                bidirectional=False  # 逆方向は単方向接続として追加
            )
            self.connections[reverse_connection.connection_id] = reverse_connection
        
        return connection.connection_id
    
    def remove_connection(self, connection_id: str) -> bool:
        """
        同期接続を削除
        
        Parameters
        ----------
        connection_id : str
            削除する接続ID
            
        Returns
        -------
        bool
            削除に成功した場合True
        """
        if connection_id not in self.connections:
            return False
        
        connection = self.connections[connection_id]
        bidirectional = connection.bidirectional
        
        # 接続を削除
        del self.connections[connection_id]
        
        # 双方向接続の場合、逆方向の接続も削除
        if bidirectional:
            for reverse_id, reverse_conn in list(self.connections.items()):
                if (reverse_conn.source_id == connection.target_id and 
                    reverse_conn.target_id == connection.source_id):
                    del self.connections[reverse_id]
                    break
        
        return True
    
    def enable_connection(self, connection_id: str, enabled: bool = True) -> bool:
        """
        同期接続の有効/無効を切り替え
        
        Parameters
        ----------
        connection_id : str
            対象の接続ID
        enabled : bool, optional
            有効にする場合True、無効にする場合False
            
        Returns
        -------
        bool
            操作に成功した場合True
        """
        if connection_id not in self.connections:
            return False
        
        self.connections[connection_id].enabled = enabled
        return True
    
    def propagate_value(self, source_id: str, sync_type: str, value: Any) -> Dict[str, bool]:
        """
        値の変更を接続先コンポーネントに伝播
        
        Parameters
        ----------
        source_id : str
            値を変更したソースコンポーネントID
        sync_type : str
            同期するデータのタイプ (例: "selection", "time")
        value : Any
            伝播する値
            
        Returns
        -------
        Dict[str, bool]
            伝播結果 {コンポーネントID: 成功したかどうか}
        """
        # 伝播ループの防止
        if self.propagation_in_progress:
            return {}
        
        self.propagation_in_progress = True
        results = {}
        
        try:
            # まず値を記録
            if source_id in self.last_values:
                self.last_values[source_id][sync_type] = value
            
            # 接続を探索して値を伝播
            for connection in self.connections.values():
                if (connection.source_id == source_id and 
                    sync_type in connection.sync_types and 
                    connection.enabled):
                    
                    target_id = connection.target_id
                    
                    # ターゲットが登録されていることを確認
                    if target_id in self.components:
                        # 値を更新
                        if target_id not in self.last_values:
                            self.last_values[target_id] = {}
                        
                        self.last_values[target_id][sync_type] = value
                        
                        # 成功を記録
                        results[target_id] = True
                    else:
                        results[target_id] = False
        finally:
            self.propagation_in_progress = False
        
        return results
    
    def get_value(self, component_id: str, sync_type: str) -> Any:
        """
        コンポーネントの現在の値を取得
        
        Parameters
        ----------
        component_id : str
            コンポーネントID
        sync_type : str
            同期タイプ
            
        Returns
        -------
        Any
            記録されている値、存在しない場合はNone
        """
        if component_id in self.last_values and sync_type in self.last_values[component_id]:
            return self.last_values[component_id][sync_type]
        return None
    
    def get_connected_components(self, component_id: str, sync_type: Optional[str] = None) -> List[str]:
        """
        指定されたコンポーネントに接続されているコンポーネントIDを取得
        
        Parameters
        ----------
        component_id : str
            元のコンポーネントID
        sync_type : Optional[str], optional
            特定の同期タイプに限定する場合に指定
            
        Returns
        -------
        List[str]
            接続されているコンポーネントIDのリスト
        """
        connected = []
        
        for connection in self.connections.values():
            if connection.source_id == component_id and connection.enabled:
                if sync_type is None or sync_type in connection.sync_types:
                    connected.append(connection.target_id)
            
            # 双方向接続も考慮
            if connection.target_id == component_id and connection.bidirectional and connection.enabled:
                if sync_type is None or sync_type in connection.sync_types:
                    connected.append(connection.source_id)
        
        return connected
    
    def to_dict(self) -> Dict[str, Any]:
        """
        同期マネージャーの状態を辞書に変換
        
        Returns
        -------
        Dict[str, Any]
            状態を表す辞書
        """
        return {
            "name": self.name,
            "components": list(self.components),
            "connections": {
                connection_id: connection.to_dict()
                for connection_id, connection in self.connections.items()
            },
            "last_values": self.last_values
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VisualizationSynchronizer":
        """
        辞書から同期マネージャーを復元
        
        Parameters
        ----------
        data : Dict[str, Any]
            状態を表す辞書
            
        Returns
        -------
        VisualizationSynchronizer
            復元された同期マネージャー
        """
        synchronizer = cls(name=data.get("name", "Visualization Synchronizer"))
        
        # コンポーネントを登録
        for component_id in data.get("components", []):
            synchronizer.register_component(component_id)
        
        # 接続を復元
        for connection_id, connection_data in data.get("connections", {}).items():
            connection = SyncConnection.from_dict(connection_data)
            synchronizer.connections[connection_id] = connection
        
        # 最終値を復元
        synchronizer.last_values = data.get("last_values", {})
        
        return synchronizer

    def get_all_connections(self) -> List[SyncConnection]:
        """
        すべての接続を取得
        
        Returns
        -------
        List[SyncConnection]
            接続オブジェクトのリスト
        """
        return list(self.connections.values())

    def find_connections(self, component_id: str, as_source: bool = True, as_target: bool = True) -> List[SyncConnection]:
        """
        特定のコンポーネントに関連する接続を検索
        
        Parameters
        ----------
        component_id : str
            検索対象のコンポーネントID
        as_source : bool, optional
            ソースとしての接続を含めるかどうか
        as_target : bool, optional
            ターゲットとしての接続を含めるかどうか
            
        Returns
        -------
        List[SyncConnection]
            条件に一致する接続のリスト
        """
        result = []
        
        for connection in self.connections.values():
            if (as_source and connection.source_id == component_id) or \
               (as_target and connection.target_id == component_id):
                result.append(connection)
        
        return result

    def clear_connections(self, component_id: Optional[str] = None) -> None:
        """
        接続をクリア
        
        Parameters
        ----------
        component_id : Optional[str], optional
            指定された場合、そのコンポーネントに関連する接続のみをクリア
        """
        if component_id is None:
            # すべての接続をクリア
            self.connections = {}
        else:
            # 特定のコンポーネントに関連する接続のみをクリア
            connection_ids_to_remove = []
            
            for connection_id, connection in self.connections.items():
                if connection.source_id == component_id or connection.target_id == component_id:
                    connection_ids_to_remove.append(connection_id)
            
            for connection_id in connection_ids_to_remove:
                del self.connections[connection_id]
