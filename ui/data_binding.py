"""
ui.data_binding

データコンテナとUIコンポーネントの連携を行うモジュール
"""

from typing import Dict, List, Any, Optional, TypeVar, Generic, Union, Callable, Set
import streamlit as st
from sailing_data_processor.data_model.container import DataContainer, GPSDataContainer, WindDataContainer, StrategyPointContainer

# 型変数の定義
T = TypeVar('T')

class DataBindingManager:
    """
    データコンテナとUIコンポーネント間のデータバインディングを管理するクラス
    
    このクラスは、データの変更を検知し、UIコンポーネントに通知する役割を担います。
    また、UIからの操作によるデータ更新も管理します。
    """
    
    def __init__(self):
        """初期化"""
        # コンテナのハッシュ値を保存する辞書
        self._container_hashes: Dict[str, str] = {}
        
        # 更新通知を受け取るコールバック関数の辞書
        # キー: コンテナID, 値: コールバック関数のリスト
        self._update_callbacks: Dict[str, List[Callable[[DataContainer], None]]] = {}
        
        # データの変更フラグ
        self._data_changed = False
        
        # セッション状態の初期化
        if 'data_containers' not in st.session_state:
            st.session_state.data_containers = {}
    
    def register_container(self, container_id: str, container: DataContainer) -> None:
        """
        データコンテナを登録
        
        Parameters
        ----------
        container_id : str
            コンテナの識別子
        container : DataContainer
            登録するデータコンテナ
        """
        # セッション状態にコンテナを保存
        st.session_state.data_containers[container_id] = container
        
        # 現在のハッシュ値を記録
        self._container_hashes[container_id] = container.get_hash()
        
        # コールバック用の空リストを初期化
        if container_id not in self._update_callbacks:
            self._update_callbacks[container_id] = []
        
        # データ変更フラグをセット
        self._data_changed = True
    
    def get_container(self, container_id: str) -> Optional[DataContainer]:
        """
        データコンテナを取得
        
        Parameters
        ----------
        container_id : str
            コンテナの識別子
            
        Returns
        -------
        Optional[DataContainer]
            登録されているデータコンテナ（存在しない場合はNone）
        """
        return st.session_state.data_containers.get(container_id)
    
    def get_all_containers(self) -> Dict[str, DataContainer]:
        """
        登録されているすべてのデータコンテナを取得
        
        Returns
        -------
        Dict[str, DataContainer]
            コンテナIDとデータコンテナのマッピング
        """
        return st.session_state.data_containers
    
    def update_container(self, container_id: str, container: DataContainer) -> None:
        """
        データコンテナを更新
        
        Parameters
        ----------
        container_id : str
            コンテナの識別子
        container : DataContainer
            更新するデータコンテナ
        """
        # コンテナを更新
        st.session_state.data_containers[container_id] = container
        
        # ハッシュ値を更新
        new_hash = container.get_hash()
        old_hash = self._container_hashes.get(container_id)
        self._container_hashes[container_id] = new_hash
        
        # ハッシュ値が変化した場合は通知
        if old_hash != new_hash:
            self._notify_update(container_id, container)
            self._data_changed = True
    
    def register_callback(self, container_id: str, callback: Callable[[DataContainer], None]) -> None:
        """
        データ更新時のコールバック関数を登録
        
        Parameters
        ----------
        container_id : str
            コンテナの識別子
        callback : Callable[[DataContainer], None]
            データ更新時に呼び出されるコールバック関数
        """
        if container_id not in self._update_callbacks:
            self._update_callbacks[container_id] = []
        
        self._update_callbacks[container_id].append(callback)
    
    def unregister_callback(self, container_id: str, callback: Callable[[DataContainer], None]) -> None:
        """
        登録したコールバック関数を解除
        
        Parameters
        ----------
        container_id : str
            コンテナの識別子
        callback : Callable[[DataContainer], None]
            解除するコールバック関数
        """
        if container_id in self._update_callbacks:
            try:
                self._update_callbacks[container_id].remove(callback)
            except ValueError:
                pass  # コールバックが見つからない場合は何もしない
    
    def _notify_update(self, container_id: str, container: DataContainer) -> None:
        """
        データ更新を通知
        
        Parameters
        ----------
        container_id : str
            コンテナの識別子
        container : DataContainer
            更新されたデータコンテナ
        """
        if container_id in self._update_callbacks:
            for callback in self._update_callbacks[container_id]:
                try:
                    callback(container)
                except Exception as e:
                    st.error(f"コールバック実行エラー: {e}")
    
    def check_updates(self) -> Set[str]:
        """
        すべてのコンテナの更新を確認
        
        Returns
        -------
        Set[str]
            更新があったコンテナのID
        """
        updated_containers: Set[str] = set()
        
        for container_id, container in st.session_state.data_containers.items():
            current_hash = container.get_hash()
            stored_hash = self._container_hashes.get(container_id)
            
            if stored_hash != current_hash:
                self._container_hashes[container_id] = current_hash
                self._notify_update(container_id, container)
                updated_containers.add(container_id)
                self._data_changed = True
        
        return updated_containers
    
    def has_data_changed(self) -> bool:
        """
        データの変更フラグを取得
        
        Returns
        -------
        bool
            データが変更された場合はTrue
        """
        return self._data_changed
    
    def reset_change_flag(self) -> None:
        """データの変更フラグをリセット"""
        self._data_changed = False
    
    def apply_to_container(self, container_id: str, func: Callable[[DataContainer], DataContainer]) -> Optional[DataContainer]:
        """
        データコンテナに関数を適用し、結果を更新
        
        Parameters
        ----------
        container_id : str
            コンテナの識別子
        func : Callable[[DataContainer], DataContainer]
            適用する関数
            
        Returns
        -------
        Optional[DataContainer]
            更新されたデータコンテナ（存在しない場合はNone）
        """
        container = self.get_container(container_id)
        if container is None:
            return None
        
        # 関数を適用
        updated_container = func(container)
        
        # 結果を更新
        self.update_container(container_id, updated_container)
        
        return updated_container
    
    def create_filtered_view(self, 
                            source_container_id: str, 
                            filter_func: Callable[[DataContainer], DataContainer],
                            target_container_id: Optional[str] = None) -> Optional[str]:
        """
        フィルタ関数を適用した新しいビューを作成
        
        Parameters
        ----------
        source_container_id : str
            元のコンテナの識別子
        filter_func : Callable[[DataContainer], DataContainer]
            フィルタリング関数
        target_container_id : Optional[str], optional
            保存先のコンテナID（指定がない場合は自動生成）
            
        Returns
        -------
        Optional[str]
            作成されたビューのコンテナID（失敗した場合はNone）
        """
        source_container = self.get_container(source_container_id)
        if source_container is None:
            return None
        
        # フィルタ関数を適用
        filtered_container = filter_func(source_container)
        
        # 保存先IDの設定
        if target_container_id is None:
            target_container_id = f"{source_container_id}_filtered_{len(self._container_hashes)}"
        
        # 結果を登録
        self.register_container(target_container_id, filtered_container)
        
        return target_container_id

class UIStateManager:
    """
    UIの状態管理を行うクラス
    
    このクラスは、UIコンポーネント間で共有される状態を管理します。
    例: 選択中のデータセット、表示設定、表示範囲など
    """
    
    def __init__(self):
        """初期化"""
        # UI状態の初期化
        if 'ui_state' not in st.session_state:
            st.session_state.ui_state = {
                'selected_datasets': [],
                'map_settings': {
                    'center': [35.45, 139.65],  # デフォルト: 東京湾
                    'zoom': 13,
                    'tile': 'OpenStreetMap',
                    'show_tracks': True,
                    'show_markers': True,
                    'color_by': 'speed'
                },
                'time_window': {
                    'start': None,
                    'end': None,
                    'current': None,
                    'playing': False,
                    'speed': 1.0
                },
                'display_options': {
                    'show_wind': True,
                    'show_strategy_points': True,
                    'show_performance_metrics': True
                },
                'filters': {
                    'speed_min': 0,
                    'speed_max': 100
                }
            }
    
    def get_state(self, key: str, default: Any = None) -> Any:
        """
        UI状態を取得
        
        Parameters
        ----------
        key : str
            状態のキー
        default : Any, optional
            キーが存在しない場合のデフォルト値
            
        Returns
        -------
        Any
            状態の値
        """
        return st.session_state.ui_state.get(key, default)
    
    def set_state(self, key: str, value: Any) -> None:
        """
        UI状態を設定
        
        Parameters
        ----------
        key : str
            状態のキー
        value : Any
            設定する値
        """
        st.session_state.ui_state[key] = value
    
    def update_map_settings(self, **kwargs) -> None:
        """
        マップ設定を更新
        
        Parameters
        ----------
        **kwargs
            更新するキーと値
        """
        for key, value in kwargs.items():
            if key in st.session_state.ui_state['map_settings']:
                st.session_state.ui_state['map_settings'][key] = value
    
    def update_time_window(self, **kwargs) -> None:
        """
        時間ウィンドウ設定を更新
        
        Parameters
        ----------
        **kwargs
            更新するキーと値
        """
        for key, value in kwargs.items():
            if key in st.session_state.ui_state['time_window']:
                st.session_state.ui_state['time_window'][key] = value
    
    def update_display_options(self, **kwargs) -> None:
        """
        表示オプションを更新
        
        Parameters
        ----------
        **kwargs
            更新するキーと値
        """
        for key, value in kwargs.items():
            if key in st.session_state.ui_state['display_options']:
                st.session_state.ui_state['display_options'][key] = value
    
    def update_filters(self, **kwargs) -> None:
        """
        フィルタ設定を更新
        
        Parameters
        ----------
        **kwargs
            更新するキーと値
        """
        for key, value in kwargs.items():
            if key in st.session_state.ui_state['filters']:
                st.session_state.ui_state['filters'][key] = value
    
    def select_datasets(self, dataset_ids: List[str]) -> None:
        """
        データセットを選択
        
        Parameters
        ----------
        dataset_ids : List[str]
            選択するデータセットのID
        """
        st.session_state.ui_state['selected_datasets'] = dataset_ids
    
    def get_selected_datasets(self) -> List[str]:
        """
        選択中のデータセットを取得
        
        Returns
        -------
        List[str]
            選択中のデータセットのID
        """
        return st.session_state.ui_state['selected_datasets']
    
    def set_current_time(self, timestamp: Any) -> None:
        """
        現在の表示時間を設定
        
        Parameters
        ----------
        timestamp : Any
            設定するタイムスタンプ
        """
        st.session_state.ui_state['time_window']['current'] = timestamp
    
    def get_current_time(self) -> Any:
        """
        現在の表示時間を取得
        
        Returns
        -------
        Any
            現在のタイムスタンプ
        """
        return st.session_state.ui_state['time_window']['current']
