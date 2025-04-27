# -*- coding: utf-8 -*-
"""
sailing_data_processor.reporting.interaction.context_provider

コンテキスト管理機能を提供するモジュールです。
ビュー間で共有するデータのコンテキスト管理を実装します。
"""

from typing import Dict, List, Any, Optional, Union

class ContextProvider:
    """
    コンテキストプロバイダー
    
    データの共有コンテキストを管理するクラスを提供します。
    """
    
    def __init__(self):
        """初期化"""
        self._context = {}
        self._listeners = {}
    
    def set_value(self, key: str, value: Any) -> None:
        """
        コンテキスト値を設定
        
        Parameters
        ----------
        key : str
            キー
        value : Any
            値
        """
        # 値を保存
        old_value = self._context.get(key)
        self._context[key] = value
        
        # リスナーに通知
        if key in self._listeners and old_value != value:
            for listener in self._listeners[key]:
                try:
                    listener(key, value)
                except Exception as e:
                    print(f"Error in context listener: {e}")
    
    def get_value(self, key: str, default: Any = None) -> Any:
        """
        コンテキスト値を取得
        
        Parameters
        ----------
        key : str
            キー
        default : Any, optional
            デフォルト値, by default None
            
        Returns
        -------
        Any
            値
        """
        return self._context.get(key, default)
    
    def remove_value(self, key: str) -> bool:
        """
        コンテキスト値を削除
        
        Parameters
        ----------
        key : str
            キー
            
        Returns
        -------
        bool
            削除成功時はTrue
        """
        if key in self._context:
            del self._context[key]
            return True
        return False
    
    def get_all(self) -> Dict[str, Any]:
        """
        すべてのコンテキスト値を取得
        
        Returns
        -------
        Dict[str, Any]
            コンテキスト全体
        """
        return self._context.copy()
    
    def add_listener(self, key: str, listener: callable) -> None:
        """
        値変更リスナーを追加
        
        Parameters
        ----------
        key : str
            監視するキー
        listener : callable
            値が変更されたときに呼び出される関数（key, value）を引数に取る
        """
        if key not in self._listeners:
            self._listeners[key] = []
        if listener not in self._listeners[key]:
            self._listeners[key].append(listener)
    
    def remove_listener(self, key: str, listener: callable) -> bool:
        """
        値変更リスナーを削除
        
        Parameters
        ----------
        key : str
            監視しているキー
        listener : callable
            削除するリスナー
            
        Returns
        -------
        bool
            削除成功時はTrue
        """
        if key in self._listeners and listener in self._listeners[key]:
            self._listeners[key].remove(listener)
            return True
        return False
    
    def clear(self) -> None:
        """コンテキストをクリア"""
        self._context = {}
        
    def reset(self) -> None:
        """コンテキストとリスナーをリセット"""
        self._context = {}
        self._listeners = {}