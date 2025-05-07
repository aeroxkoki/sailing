# -*- coding: utf-8 -*-
"""
sailing_data_processor.data_model.cache_manager

キャッシング機能を提供するモジュール
"""

from functools import wraps
import hashlib
import inspect
from typing import Callable, Any, Dict, Tuple, TypeVar, Union, Optional
import time
import warnings

# 型変数の定義
R = TypeVar('R')  # 戻り値の型

def hash_args(*args, **kwargs) -> str:
    """
    引数からハッシュ値を生成
    
    Parameters
    ----------
    *args : Any
        位置引数
    **kwargs : Any
        キーワード引数
        
    Returns
    -------
    str
        ハッシュ値（16進数文字列）
    """
    hash_obj = hashlib.md5()
    
    # 位置引数のハッシュ
    for arg in args:
        hash_obj.update(str(arg).encode('utf-8'))
    
    # キーワード引数のハッシュ（ソートして順序を一定に）
    for key in sorted(kwargs.keys()):
        hash_obj.update(f"{key}:{kwargs[key]}".encode('utf-8'))
        
    return hash_obj.hexdigest()

class CacheManager:
    """
    アプリケーション全体で使用するキャッシュマネージャ
    シングルトンパターンで実装
    """
    _instance = None
    _caches: Dict[str, Dict[str, Any]] = {}
    _stats: Dict[str, Dict[str, int]] = {}
    
    def __new__(cls):
        """シングルトンパターン実装"""
        if cls._instance is None:
            cls._instance = super(CacheManager, cls).__new__(cls)
            cls._instance._caches = {}
            cls._instance._stats = {}
        return cls._instance
    
    def get_cache(self, name: str) -> Dict[str, Any]:
        """
        名前付きキャッシュを取得
        
        Parameters
        ----------
        name : str
            キャッシュの名前
            
        Returns
        -------
        Dict[str, Any]
            キャッシュ辞書
        """
        if name not in self._caches:
            self._caches[name] = {}
            self._stats[name] = {
                'hits': 0,
                'misses': 0,
                'size': 0,
                'max_size': 0
            }
        return self._caches[name]
    
    def clear_cache(self, name: str = None) -> None:
        """
        キャッシュをクリア
        
        Parameters
        ----------
        name : str, optional
            キャッシュの名前、Noneの場合は全キャッシュをクリア
        """
        if name is None:
            self._caches.clear()
            self._stats.clear()
        elif name in self._caches:
            self._caches[name].clear()
            if name in self._stats:
                self._stats[name]['size'] = 0
                # ヒット数とミス数は維持
    
    def get_stats(self, name: str = None) -> Dict[str, Any]:
        """
        キャッシュの統計情報を取得
        
        Parameters
        ----------
        name : str, optional
            キャッシュの名前、Noneの場合は全キャッシュの統計情報
            
        Returns
        -------
        Dict[str, Any]
            統計情報を含む辞書
        """
        if name is None:
            all_stats = {}
            for cache_name, stats in self._stats.items():
                all_stats[cache_name] = stats.copy()
                if stats['hits'] + stats['misses'] > 0:
                    all_stats[cache_name]['hit_ratio'] = stats['hits'] / (stats['hits'] + stats['misses'])
                else:
                    all_stats[cache_name]['hit_ratio'] = 0
            return all_stats
        
        elif name in self._stats:
            stats = self._stats[name].copy()
            if stats['hits'] + stats['misses'] > 0:
                stats['hit_ratio'] = stats['hits'] / (stats['hits'] + stats['misses'])
            else:
                stats['hit_ratio'] = 0
            return stats
        
        return {}
    
    def cached(self, cache_name: str, max_size: int = 128, ttl: Optional[float] = None) -> Callable:
        """
        関数の結果をキャッシュするデコレータ
        
        Parameters
        ----------
        cache_name : str
            使用するキャッシュの名前
        max_size : int, optional
            キャッシュの最大サイズ、デフォルトは128
        ttl : float, optional
            キャッシュエントリの有効期間（秒）、Noneの場合は無期限
            
        Returns
        -------
        Callable
            デコレートされた関数
        """
        def decorator(func: Callable[..., R]) -> Callable[..., R]:
            """デコレータ本体"""
            cache = self.get_cache(cache_name)
            
            # 統計情報の最大サイズを更新
            self._stats[cache_name]['max_size'] = max(self._stats[cache_name]['max_size'], max_size)
            
            @wraps(func)
            def wrapper(*args, **kwargs) -> R:
                """ラッパー関数"""
                # キャッシュキーの生成
                key = hash_args(*args, **kwargs)
                
                # キャッシュにヒットした場合
                if key in cache:
                    entry = cache[key]
                    
                    # TTLが設定されている場合は有効期限をチェック
                    if ttl is not None and time.time() - entry['timestamp'] > ttl:
                        del cache[key]
                        self._stats[cache_name]['size'] -= 1
                        # TTLが切れたのでミスとしてカウント
                        self._stats[cache_name]['misses'] += 1
                    else:
                        self._stats[cache_name]['hits'] += 1
                        return entry['result']
                
                # キャッシュミスの場合は関数を実行
                # ミスをカウントするのは一度だけにする
                self._stats[cache_name]['misses'] += 1
                result = func(*args, **kwargs)
                
                # キャッシュサイズ管理（LRU方式）
                if len(cache) >= max_size:
                    # 最も古いアイテムを削除
                    # 注意: これはシンプルなLRU実装です。本格的なLRUにはOrderedDictを使用するべき
                    oldest_key = min(cache.keys(), key=lambda k: cache[k]['timestamp'] if 'timestamp' in cache[k] else 0)
                    del cache[oldest_key]
                    self._stats[cache_name]['size'] -= 1
                
                # 結果をキャッシュに保存
                cache[key] = {
                    'result': result,
                    'timestamp': time.time()
                }
                self._stats[cache_name]['size'] += 1
                
                return result
            
            return wrapper
        
        return decorator
    
    def memoize(self, func: Callable[..., R]) -> Callable[..., R]:
        """
        関数の結果をメモ化するシンプルなデコレータ
        関数名をキャッシュ名として使用
        
        Parameters
        ----------
        func : Callable[..., R]
            メモ化する関数
            
        Returns
        -------
        Callable[..., R]
            メモ化された関数
        """
        cache_name = func.__name__
        return self.cached(cache_name)(func)


# グローバルなキャッシュマネージャのインスタンス
cache_manager = CacheManager()

# 便利なデコレータ
def cached(cache_name: str = None, max_size: int = 128, ttl: Optional[float] = None) -> Callable:
    """
    関数の結果をキャッシュするデコレータ（グローバルマネージャを使用）
    
    Parameters
    ----------
    cache_name : str, optional
        使用するキャッシュの名前、Noneの場合は関数名を使用
    max_size : int, optional
        キャッシュの最大サイズ、デフォルトは128
    ttl : float, optional
        キャッシュエントリの有効期間（秒）、Noneの場合は無期限
        
    Returns
    -------
    Callable
        デコレータ
    """
    def decorator(func: Callable[..., R]) -> Callable[..., R]:
        nonlocal cache_name
        if cache_name is None:
            cache_name = func.__name__
        return cache_manager.cached(cache_name, max_size, ttl)(func)
    
    return decorator

def memoize(func: Callable[..., R]) -> Callable[..., R]:
    """
    関数の結果をメモ化するシンプルなデコレータ（グローバルマネージャを使用）
    
    Parameters
    ----------
    func : Callable[..., R]
        メモ化する関数
        
    Returns
    -------
    Callable[..., R]
        メモ化された関数
    """
    return cache_manager.memoize(func)

def clear_cache(name: str = None) -> None:
    """
    キャッシュをクリア（グローバルマネージャを使用）
    
    Parameters
    ----------
    name : str, optional
        キャッシュの名前、Noneの場合は全キャッシュをクリア
    """
    cache_manager.clear_cache(name)

def get_cache_stats(name: str = None) -> Dict[str, Any]:
    """
    キャッシュの統計情報を取得（グローバルマネージャを使用）
    
    Parameters
    ----------
    name : str, optional
        キャッシュの名前、Noneの場合は全キャッシュの統計情報
        
    Returns
    -------
    Dict[str, Any]
        統計情報を含む辞書
    """
    return cache_manager.get_stats(name)
