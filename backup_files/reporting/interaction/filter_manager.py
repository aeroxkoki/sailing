# -*- coding: utf-8 -*-
"""
Module for data connector between map layers and data sources.
This module provides functions for binding and data transformation between layers and data sources.
"""

from typing import Dict, List, Any, Optional, Union, Callable

class FilterManager:
    """
    フィルタマネージャー
    
    データのフィルタリング機能を提供するクラスです。
    """
    
    def __init__(self):
        """初期化"""
        self._filters = {}  # フィルタ定義
        self._active_filters = {}  # アクティブなフィルタ
        self._filter_listeners = []  # フィルタ変更リスナー
    
    def register_filter(self, filter_id: str, filter_config: Dict[str, Any]) -> bool:
        """
        フィルタを登録
        
        Parameters
        ----------
        filter_id : str
            フィルタID
        filter_config : Dict[str, Any]
            フィルタ設定
            
        Returns
        -------
        bool
            登録成功時はTrue
        """
        if not filter_id:
            return False
        
        # 必須フィールドがあるか確認
        required_fields = ['type', 'target']
        for field in required_fields:
            if field not in filter_config:
                return False
        
        # フィルタ登録
        self._filters[filter_id] = filter_config.copy()
        
        # デフォルトでは非アクティブ
        if 'active' not in self._filters[filter_id]:
            self._filters[filter_id]['active'] = False
        
        return True
    
    def unregister_filter(self, filter_id: str) -> bool:
        """
        フィルタ登録を解除
        
        Parameters
        ----------
        filter_id : str
            フィルタID
            
        Returns
        -------
        bool
            解除成功時はTrue
        """
        if filter_id in self._filters:
            del self._filters[filter_id]
            
            # アクティブフィルタからも削除
            if filter_id in self._active_filters:
                del self._active_filters[filter_id]
                
                # リスナーに通知
                self._notify_filter_change()
            
            return True
        
        return False
    
    def set_filter_active(self, filter_id: str, active: bool) -> bool:
        """
        フィルタのアクティブ状態を設定
        
        Parameters
        ----------
        filter_id : str
            フィルタID
        active : bool
            アクティブにするかどうか
            
        Returns
        -------
        bool
            設定成功時はTrue
        """
        if filter_id not in self._filters:
            return False
        
        # アクティブ状態を更新
        self._filters[filter_id]['active'] = active
        
        # アクティブフィルタリストを更新
        if active:
            self._active_filters[filter_id] = self._filters[filter_id]
        elif filter_id in self._active_filters:
            del self._active_filters[filter_id]
        
        # リスナーに通知
        self._notify_filter_change()
        
        return True
    
    def update_filter_config(self, filter_id: str, config_update: Dict[str, Any]) -> bool:
        """
        フィルタ設定を更新
        
        Parameters
        ----------
        filter_id : str
            フィルタID
        config_update : Dict[str, Any]
            更新する設定
            
        Returns
        -------
        bool
            更新成功時はTrue
        """
        if filter_id not in self._filters:
            return False
        
        # 設定を更新
        self._filters[filter_id].update(config_update)
        
        # アクティブなフィルタの場合は、そちらも更新
        if filter_id in self._active_filters:
            self._active_filters[filter_id] = self._filters[filter_id]
            
            # リスナーに通知
            self._notify_filter_change()
        
        return True
    
    def get_filter(self, filter_id: str) -> Optional[Dict[str, Any]]:
        """
        フィルタ設定を取得
        
        Parameters
        ----------
        filter_id : str
            フィルタID
            
        Returns
        -------
        Optional[Dict[str, Any]]
            フィルタ設定
        """
        return self._filters.get(filter_id, {}).copy() if filter_id in self._filters else None
    
    def get_all_filters(self) -> Dict[str, Dict[str, Any]]:
        """
        すべてのフィルタを取得
        
        Returns
        -------
        Dict[str, Dict[str, Any]]
            フィルタIDとフィルタ設定のマップ
        """
        return {k: v.copy() for k, v in self._filters.items()}
    
    def get_active_filters(self) -> Dict[str, Dict[str, Any]]:
        """
        アクティブなフィルタをすべて取得
        
        Returns
        -------
        Dict[str, Dict[str, Any]]
            アクティブなフィルタIDとフィルタ設定のマップ
        """
        return {k: v.copy() for k, v in self._active_filters.items()}
    
    def apply_filters(self, data: Any, target: Optional[str] = None) -> Any:
        """
        データにフィルタを適用
        
        Parameters
        ----------
        data : Any
            フィルタを適用するデータ
        target : Optional[str], optional
            特定のターゲットのみフィルタリング, by default None
            
        Returns
        -------
        Any
            フィルタリング後のデータ
        """
        # アクティブなフィルタがなければ、そのまま返す
        if not self._active_filters:
            return data
        
        # 各フィルタを適用
        filtered_data = data
        for filter_id, filter_config in self._active_filters.items():
            # ターゲット指定がある場合、一致するもののみ適用
            if target and filter_config.get('target') != target:
                continue
            
            try:
                # フィルタタイプに応じた処理
                filter_type = filter_config.get('type')
                
                if filter_type == 'range':
                    filtered_data = self._apply_range_filter(filtered_data, filter_config)
                elif filter_type == 'value':
                    filtered_data = self._apply_value_filter(filtered_data, filter_config)
                elif filter_type == 'text':
                    filtered_data = self._apply_text_filter(filtered_data, filter_config)
                elif filter_type == 'custom':
                    filtered_data = self._apply_custom_filter(filtered_data, filter_config)
            except Exception as e:
                print(f"Error applying filter {filter_id}: {e}")
        
        return filtered_data
    
    def add_filter_listener(self, listener: Callable[[], None]) -> None:
        """
        フィルタ変更リスナーを追加
        
        Parameters
        ----------
        listener : Callable[[], None]
            フィルタ変更時に呼び出される関数
        """
        if listener not in self._filter_listeners:
            self._filter_listeners.append(listener)
    
    def remove_filter_listener(self, listener: Callable[[], None]) -> bool:
        """
        フィルタ変更リスナーを削除
        
        Parameters
        ----------
        listener : Callable[[], None]
            削除するリスナー
            
        Returns
        -------
        bool
            削除成功時はTrue
        """
        if listener in self._filter_listeners:
            self._filter_listeners.remove(listener)
            return True
        return False
    
    def _notify_filter_change(self) -> None:
        """フィルタ変更をリスナーに通知"""
        for listener in self._filter_listeners:
            try:
                listener()
            except Exception as e:
                print(f"Error in filter listener: {e}")
    
    def _apply_range_filter(self, data: Any, filter_config: Dict[str, Any]) -> Any:
        """範囲フィルタを適用"""
        # 必要な設定があるか確認
        if 'field' not in filter_config:
            return data
        
        # データの種類ごとに処理
        if isinstance(data, list):
            # リスト内の辞書の場合
            if data and isinstance(data[0], dict):
                field = filter_config['field']
                min_val = filter_config.get('min')
                max_val = filter_config.get('max')
                
                # 条件に合うものだけを残す
                result = []
                for item in data:
                    if field not in item:
                        result.append(item)
                        continue
                    
                    value = item[field]
                    
                    # 数値かどうか確認
                    if not isinstance(value, (int, float)):
                        result.append(item)
                        continue
                    
                    # 最小値のチェック
                    if min_val is not None and value < min_val:
                        continue
                    
                    # 最大値のチェック
                    if max_val is not None and value > max_val:
                        continue
                    
                    result.append(item)
                
                return result
            
        return data
    
    def _apply_value_filter(self, data: Any, filter_config: Dict[str, Any]) -> Any:
        """値フィルタを適用"""
        # 必要な設定があるか確認
        if 'field' not in filter_config or 'values' not in filter_config:
            return data
        
        # データの種類ごとに処理
        if isinstance(data, list):
            # リスト内の辞書の場合
            if data and isinstance(data[0], dict):
                field = filter_config['field']
                values = filter_config['values']
                exclude = filter_config.get('exclude', False)
                
                # 条件に合うものだけを残す
                result = []
                for item in data:
                    if field not in item:
                        result.append(item)
                        continue
                    
                    value = item[field]
                    
                    # 含める/除外する値のリストに含まれるかチェック
                    if (value in values) != exclude:
                        result.append(item)
                
                return result
            
        return data
    
    def _apply_text_filter(self, data: Any, filter_config: Dict[str, Any]) -> Any:
        """テキストフィルタを適用"""
        # 必要な設定があるか確認
        if 'field' not in filter_config or 'text' not in filter_config:
            return data
        
        # データの種類ごとに処理
        if isinstance(data, list):
            # リスト内の辞書の場合
            if data and isinstance(data[0], dict):
                field = filter_config['field']
                text = filter_config['text']
                case_sensitive = filter_config.get('case_sensitive', False)
                
                # 条件に合うものだけを残す
                result = []
                for item in data:
                    if field not in item:
                        result.append(item)
                        continue
                    
                    value = item[field]
                    
                    # 文字列でない場合は変換
                    if not isinstance(value, str):
                        value = str(value)
                    
                    # 大文字小文字を区別しない場合
                    if not case_sensitive:
                        value = value.lower()
                        text = text.lower()
                    
                    # テキストが含まれるかチェック
                    if text in value:
                        result.append(item)
                
                return result
            
        return data
    
    def _apply_custom_filter(self, data: Any, filter_config: Dict[str, Any]) -> Any:
        """カスタムフィルタを適用"""
        # 必要な設定があるか確認
        if 'filter_func' not in filter_config:
            return data
        
        # フィルタ関数を取得
        filter_func = filter_config['filter_func']
        
        # 関数として呼び出し可能か確認
        if not callable(filter_func):
            return data
        
        try:
            # フィルタ関数を呼び出し
            return filter_func(data, filter_config)
        except Exception as e:
            print(f"Error in custom filter: {e}")
            return data
