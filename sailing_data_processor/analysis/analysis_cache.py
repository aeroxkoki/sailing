"""
分析結果キャッシュ管理システムモジュール

このモジュールはブラウザストレージと連携した分析結果のキャッシング機能を提供します。
中間結果の効率的な保存と再利用、キャッシュ無効化条件の設定などの機能を含みます。
"""

import time
import datetime
import logging
import json
import hashlib
from typing import Dict, List, Any, Optional, Union, Callable, Tuple

# デフォルトのキャッシュ設定
DEFAULT_CACHE_MAX_SIZE = 10 * 1024 * 1024  # 10MB
DEFAULT_CACHE_TTL = 3600  # 1時間（秒）

class CacheItem:
    """キャッシュアイテムを表すクラス"""
    
    def __init__(self, key: str, value: Any, metadata: Dict[str, Any] = None, 
                expiration: Optional[float] = None, size_bytes: Optional[int] = None):
        """
        初期化
        
        Parameters:
        -----------
        key : str
            キャッシュキー
        value : Any
            キャッシュする値
        metadata : Dict[str, Any], optional
            メタデータ
        expiration : float, optional
            有効期限（UNIXタイムスタンプ）
        size_bytes : int, optional
            データサイズ（バイト）
        """
        self.key = key
        self.value = value
        self.metadata = metadata or {}
        self.created_at = time.time()
        self.last_accessed_at = self.created_at
        self.access_count = 0
        self.expiration = expiration
        
        # サイズを計算（指定がなければ概算）
        if size_bytes is not None:
            self.size_bytes = size_bytes
        else:
            # サイズの概算
            try:
                # JSONに変換してサイズを推定
                json_str = json.dumps(value)
                self.size_bytes = len(json_str.encode('utf-8'))
            except (TypeError, OverflowError):
                # JSONに変換できない場合はデフォルト値
                self.size_bytes = 1024
    
    def is_expired(self) -> bool:
        """
        キャッシュアイテムが期限切れかどうかを判定
        
        Returns:
        --------
        bool
            期限切れの場合True
        """
        if self.expiration is None:
            return False
        return time.time() > self.expiration
    
    def update_access_time(self) -> None:
        """アクセス時刻と回数を更新"""
        self.last_accessed_at = time.time()
        self.access_count += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """
        辞書形式に変換
        
        Returns:
        --------
        Dict[str, Any]
            辞書形式のキャッシュアイテム
        """
        return {
            "key": self.key,
            "value": self.value,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "last_accessed_at": self.last_accessed_at,
            "access_count": self.access_count,
            "expiration": self.expiration,
            "size_bytes": self.size_bytes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CacheItem':
        """
        辞書からキャッシュアイテムを作成
        
        Parameters:
        -----------
        data : Dict[str, Any]
            辞書データ
            
        Returns:
        --------
        CacheItem
            作成されたキャッシュアイテム
        """
        item = cls(
            key=data.get("key", ""),
            value=data.get("value"),
            metadata=data.get("metadata", {}),
            expiration=data.get("expiration"),
            size_bytes=data.get("size_bytes")
        )
        
        # その他のプロパティを復元
        item.created_at = data.get("created_at", item.created_at)
        item.last_accessed_at = data.get("last_accessed_at", item.last_accessed_at)
        item.access_count = data.get("access_count", 0)
        
        return item

class AnalysisCache:
    """
    分析結果キャッシュ管理クラス
    
    ブラウザストレージと連携し、分析結果のキャッシングを行います。
    """
    
    def __init__(self, storage_interface=None, namespace: str = "analysis_cache",
                max_size_bytes: int = DEFAULT_CACHE_MAX_SIZE,
                default_ttl: int = DEFAULT_CACHE_TTL):
        """
        初期化
        
        Parameters:
        -----------
        storage_interface : StorageInterface, optional
            データ永続化に使用するストレージインターフェース
        namespace : str, optional
            キャッシュ名前空間
        max_size_bytes : int, optional
            キャッシュの最大サイズ（バイト）
        default_ttl : int, optional
            デフォルトのキャッシュ有効期間（秒）
        """
        self.logger = logging.getLogger(f"{__name__}.{namespace}")
        self.storage = storage_interface
        self.namespace = namespace
        self.max_size_bytes = max_size_bytes
        self.default_ttl = default_ttl
        self.storage_key_prefix = f"cache_{namespace}_"
        
        # メモリ内キャッシュ
        self.memory_cache: Dict[str, CacheItem] = {}
        
        # キャッシュ状態
        self.current_size_bytes = 0
        self.hit_count = 0
        self.miss_count = 0
        self.eviction_count = 0
        
        # 無効化設定
        self.invalidation_callbacks: List[Callable[[str], bool]] = []
    
    def _generate_key(self, prefix: str, params: Dict[str, Any]) -> str:
        """
        パラメータからキャッシュキーを生成
        
        Parameters:
        -----------
        prefix : str
            キープレフィックス
        params : Dict[str, Any]
            パラメータ辞書
            
        Returns:
        --------
        str
            生成されたキャッシュキー
        """
        # パラメータを安定したJSONに変換
        # （ソートして順序を一定に）
        sorted_params = json.dumps(params, sort_keys=True)
        
        # ハッシュ生成
        hash_obj = hashlib.md5(sorted_params.encode('utf-8'))
        hash_hex = hash_obj.hexdigest()
        
        # プレフィックスとハッシュを組み合わせてキーを生成
        key = f"{prefix}_{hash_hex}"
        
        return key
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None, 
           metadata: Dict[str, Any] = None, overwrite: bool = True) -> bool:
        """
        キャッシュに値を設定
        
        Parameters:
        -----------
        key : str
            キャッシュキー
        value : Any
            キャッシュする値
        ttl : int, optional
            有効期間（秒）、Noneの場合はデフォルト値を使用
        metadata : Dict[str, Any], optional
            メタデータ
        overwrite : bool, optional
            既存キーを上書きするかどうか
            
        Returns:
        --------
        bool
            設定に成功したかどうか
        """
        # 既存キーのチェック
        if key in self.memory_cache and not overwrite:
            return False
        
        # 有効期限の計算
        expiration = None
        if ttl is not None:
            expiration = time.time() + ttl
        elif self.default_ttl is not None:
            expiration = time.time() + self.default_ttl
        
        # キャッシュアイテムの作成
        cache_item = CacheItem(key, value, metadata, expiration)
        
        # キャッシュサイズが上限を超える場合、古いアイテムを削除
        if key not in self.memory_cache:
            new_size = self.current_size_bytes + cache_item.size_bytes
            if new_size > self.max_size_bytes:
                self._evict_items(cache_item.size_bytes)
        else:
            # 既存アイテムのサイズを差し引く
            self.current_size_bytes -= self.memory_cache[key].size_bytes
        
        # メモリキャッシュに保存
        self.memory_cache[key] = cache_item
        self.current_size_bytes += cache_item.size_bytes
        
        # ストレージがあれば永続化
        if self.storage:
            try:
                storage_key = f"{self.storage_key_prefix}{key}"
                self.storage.save(storage_key, cache_item.to_dict())
            except Exception as e:
                self.logger.warning(f"キャッシュアイテムの永続化に失敗しました: {e}")
        
        return True
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        キャッシュから値を取得
        
        Parameters:
        -----------
        key : str
            キャッシュキー
        default : Any, optional
            キャッシュミス時のデフォルト値
            
        Returns:
        --------
        Any
            キャッシュされた値、存在しない場合はデフォルト値
        """
        # メモリキャッシュをチェック
        cache_item = self.memory_cache.get(key)
        
        # メモリキャッシュになければストレージをチェック
        if cache_item is None and self.storage:
            try:
                storage_key = f"{self.storage_key_prefix}{key}"
                item_dict = self.storage.load(storage_key)
                if item_dict:
                    cache_item = CacheItem.from_dict(item_dict)
                    # メモリキャッシュにも追加
                    self.memory_cache[key] = cache_item
                    self.current_size_bytes += cache_item.size_bytes
            except Exception as e:
                self.logger.warning(f"ストレージからのキャッシュ読み込みに失敗しました: {e}")
        
        # キャッシュアイテムが見つかった場合
        if cache_item:
            # 期限切れチェック
            if cache_item.is_expired():
                # 期限切れの場合は削除
                self.delete(key)
                self.miss_count += 1
                return default
            
            # 無効化条件のチェック
            for callback in self.invalidation_callbacks:
                try:
                    if callback(key):
                        # 無効化条件に該当する場合は削除
                        self.delete(key)
                        self.miss_count += 1
                        return default
                except Exception as e:
                    self.logger.warning(f"キャッシュ無効化コールバックでエラーが発生しました: {e}")
            
            # アクセス情報を更新
            cache_item.update_access_time()
            self.hit_count += 1
            
            return cache_item.value
        else:
            # キャッシュミス
            self.miss_count += 1
            return default
    
    def compute_if_absent(self, key: str, compute_func: Callable[[], Any], 
                        ttl: Optional[int] = None, metadata: Dict[str, Any] = None) -> Any:
        """
        キャッシュに値がなければ計算して設定
        
        Parameters:
        -----------
        key : str
            キャッシュキー
        compute_func : Callable[[], Any]
            値を計算する関数
        ttl : int, optional
            有効期間（秒）
        metadata : Dict[str, Any], optional
            メタデータ
            
        Returns:
        --------
        Any
            キャッシュされた値または計算された値
        """
        # キャッシュをチェック
        cached_value = self.get(key)
        if cached_value is not None:
            return cached_value
        
        # 値を計算
        computed_value = compute_func()
        
        # キャッシュに設定
        self.set(key, computed_value, ttl, metadata)
        
        return computed_value
    
    def compute_from_params(self, prefix: str, params: Dict[str, Any], 
                          compute_func: Callable[[Dict[str, Any]], Any],
                          ttl: Optional[int] = None, 
                          metadata: Dict[str, Any] = None) -> Any:
        """
        パラメータからキャッシュキーを生成し、存在しなければ計算して設定
        
        Parameters:
        -----------
        prefix : str
            キープレフィックス
        params : Dict[str, Any]
            パラメータ辞書
        compute_func : Callable[[Dict[str, Any]], Any]
            パラメータから値を計算する関数
        ttl : int, optional
            有効期間（秒）
        metadata : Dict[str, Any], optional
            メタデータ
            
        Returns:
        --------
        Any
            キャッシュされた値または計算された値
        """
        # パラメータからキャッシュキーを生成
        key = self._generate_key(prefix, params)
        
        # メタデータに元パラメータを追加
        computed_metadata = {
            "source_prefix": prefix,
            "source_params": params,
            "computed_at": time.time()
        }
        if metadata:
            computed_metadata.update(metadata)
        
        # キャッシュをチェックし、なければ計算
        return self.compute_if_absent(
            key, 
            lambda: compute_func(params),
            ttl,
            computed_metadata
        )
    
    def delete(self, key: str) -> bool:
        """
        キャッシュから値を削除
        
        Parameters:
        -----------
        key : str
            キャッシュキー
            
        Returns:
        --------
        bool
            削除に成功したかどうか
        """
        # メモリキャッシュから削除
        if key in self.memory_cache:
            # サイズを減算
            self.current_size_bytes -= self.memory_cache[key].size_bytes
            del self.memory_cache[key]
        
        # ストレージからも削除
        if self.storage:
            try:
                storage_key = f"{self.storage_key_prefix}{key}"
                self.storage.delete(storage_key)
            except Exception as e:
                self.logger.warning(f"ストレージからのキャッシュ削除に失敗しました: {e}")
                return False
        
        return True
    
    def clear(self) -> bool:
        """
        すべてのキャッシュをクリア
        
        Returns:
        --------
        bool
            クリアに成功したかどうか
        """
        # メモリキャッシュをクリア
        self.memory_cache.clear()
        self.current_size_bytes = 0
        
        # ストレージのキャッシュもクリア
        if self.storage:
            try:
                keys = self.storage.list_keys(self.storage_key_prefix)
                for key in keys:
                    self.storage.delete(key)
            except Exception as e:
                self.logger.warning(f"ストレージからのキャッシュクリアに失敗しました: {e}")
                return False
        
        return True
    
    def keys(self) -> List[str]:
        """
        キャッシュのキー一覧を取得
        
        Returns:
        --------
        List[str]
            キャッシュキーのリスト
        """
        # メモリキャッシュのキーを取得
        memory_keys = set(self.memory_cache.keys())
        
        # ストレージのキーも取得
        storage_keys = set()
        if self.storage:
            try:
                prefix_len = len(self.storage_key_prefix)
                keys = self.storage.list_keys(self.storage_key_prefix)
                storage_keys = {key[prefix_len:] for key in keys}
            except Exception as e:
                self.logger.warning(f"ストレージからのキー一覧取得に失敗しました: {e}")
        
        # 両方のキーをマージ
        return list(memory_keys.union(storage_keys))
    
    def add_invalidation_callback(self, callback: Callable[[str], bool]) -> None:
        """
        キャッシュ無効化コールバックを追加
        
        Parameters:
        -----------
        callback : Callable[[str], bool]
            キーを受け取り、無効化するかどうかを返す関数
        """
        if callback not in self.invalidation_callbacks:
            self.invalidation_callbacks.append(callback)
    
    def remove_invalidation_callback(self, callback: Callable[[str], bool]) -> bool:
        """
        キャッシュ無効化コールバックを削除
        
        Parameters:
        -----------
        callback : Callable[[str], bool]
            削除するコールバック関数
            
        Returns:
        --------
        bool
            削除に成功したかどうか
        """
        if callback in self.invalidation_callbacks:
            self.invalidation_callbacks.remove(callback)
            return True
        return False
    
    def cleanup_expired(self) -> int:
        """
        期限切れのキャッシュを削除
        
        Returns:
        --------
        int
            削除されたアイテム数
        """
        deleted_count = 0
        current_time = time.time()
        
        # 期限切れのアイテムを削除
        expired_keys = []
        for key, item in list(self.memory_cache.items()):
            if item.expiration and current_time > item.expiration:
                expired_keys.append(key)
        
        # 削除処理
        for key in expired_keys:
            self.delete(key)
            deleted_count += 1
        
        return deleted_count
    
    def _evict_items(self, required_bytes: int) -> int:
        """
        必要なスペースを確保するためにアイテムを削除
        
        Parameters:
        -----------
        required_bytes : int
            必要なバイト数
            
        Returns:
        --------
        int
            削除されたアイテム数
        """
        if not self.memory_cache:
            return 0
        
        # 最低でも必要スペースの20%を解放
        target_bytes = max(required_bytes, self.max_size_bytes * 0.2)
        freed_bytes = 0
        evicted_count = 0
        
        # まず期限切れのアイテムを削除
        expired_keys = []
        current_time = time.time()
        for key, item in self.memory_cache.items():
            if item.expiration and current_time > item.expiration:
                expired_keys.append(key)
        
        for key in expired_keys:
            freed_bytes += self.memory_cache[key].size_bytes
            self.delete(key)
            evicted_count += 1
        
        # 期限切れアイテムの削除だけで十分なら終了
        if freed_bytes >= target_bytes:
            self.eviction_count += evicted_count
            return evicted_count
        
        # アクセス時刻でソート（古い順）
        sorted_items = sorted(
            self.memory_cache.items(),
            key=lambda x: x[1].last_accessed_at
        )
        
        # 必要なスペースが確保できるまで削除
        for key, item in sorted_items:
            # 既に削除されている可能性があるのでチェック
            if key not in self.memory_cache:
                continue
                
            freed_bytes += item.size_bytes
            self.delete(key)
            evicted_count += 1
            
            if freed_bytes >= target_bytes:
                break
        
        self.eviction_count += evicted_count
        return evicted_count
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        キャッシュの統計情報を取得
        
        Returns:
        --------
        Dict[str, Any]
            統計情報の辞書
        """
        total_requests = self.hit_count + self.miss_count
        hit_rate = self.hit_count / total_requests if total_requests > 0 else 0
        
        return {
            "namespace": self.namespace,
            "item_count": len(self.memory_cache),
            "current_size_bytes": self.current_size_bytes,
            "max_size_bytes": self.max_size_bytes,
            "usage_percent": (self.current_size_bytes / self.max_size_bytes) * 100 if self.max_size_bytes > 0 else 0,
            "hit_count": self.hit_count,
            "miss_count": self.miss_count,
            "hit_rate": hit_rate,
            "eviction_count": self.eviction_count
        }
    
    def save_cache_state(self) -> bool:
        """
        キャッシュの状態をストレージに保存
        
        Returns:
        --------
        bool
            保存に成功したかどうか
        """
        if not self.storage:
            return False
        
        try:
            # 統計情報の保存
            stats_key = f"{self.storage_key_prefix}stats"
            stats = self.get_cache_stats()
            stats["saved_at"] = time.time()
            self.storage.save(stats_key, stats)
            
            # インデックスの保存
            index_key = f"{self.storage_key_prefix}index"
            index_data = {
                "keys": list(self.memory_cache.keys()),
                "updated_at": time.time()
            }
            self.storage.save(index_key, index_data)
            
            return True
        except Exception as e:
            self.logger.error(f"キャッシュ状態の保存に失敗しました: {e}")
            return False
    
    def load_cache_state(self) -> bool:
        """
        ストレージからキャッシュの状態を読み込み
        
        Returns:
        --------
        bool
            読み込みに成功したかどうか
        """
        if not self.storage:
            return False
        
        try:
            # インデックスの読み込み
            index_key = f"{self.storage_key_prefix}index"
            index_data = self.storage.load(index_key)
            
            if not index_data or "keys" not in index_data:
                return False
                
            # キャッシュアイテムの読み込み
            for key in index_data["keys"]:
                storage_key = f"{self.storage_key_prefix}{key}"
                item_dict = self.storage.load(storage_key)
                
                if item_dict:
                    cache_item = CacheItem.from_dict(item_dict)
                    
                    # 期限切れでなければメモリキャッシュに追加
                    if not cache_item.is_expired():
                        self.memory_cache[key] = cache_item
                        self.current_size_bytes += cache_item.size_bytes
            
            # 統計情報の復元（ヒットカウントなど）
            stats_key = f"{self.storage_key_prefix}stats"
            stats = self.storage.load(stats_key)
            
            if stats:
                self.hit_count = stats.get("hit_count", 0)
                self.miss_count = stats.get("miss_count", 0)
                self.eviction_count = stats.get("eviction_count", 0)
            
            return True
        except Exception as e:
            self.logger.error(f"キャッシュ状態の読み込みに失敗しました: {e}")
            return False
    
    def get_cached_results_for_prefix(self, prefix: str) -> List[Tuple[str, Any, Dict[str, Any]]]:
        """
        指定プレフィックスのキャッシュ結果を取得
        
        Parameters:
        -----------
        prefix : str
            キャッシュキーのプレフィックス
            
        Returns:
        --------
        List[Tuple[str, Any, Dict[str, Any]]]
            (キー, 値, メタデータ)のタプルリスト
        """
        results = []
        
        for key, item in self.memory_cache.items():
            if key.startswith(prefix):
                results.append((key, item.value, item.metadata))
        
        return results
    
    def invalidate_by_prefix(self, prefix: str) -> int:
        """
        指定プレフィックスのキャッシュを無効化
        
        Parameters:
        -----------
        prefix : str
            キャッシュキーのプレフィックス
            
        Returns:
        --------
        int
            無効化されたアイテム数
        """
        invalidated_count = 0
        keys_to_delete = []
        
        # 削除するキーを収集
        for key in list(self.memory_cache.keys()):
            if key.startswith(prefix):
                keys_to_delete.append(key)
        
        # 削除実行
        for key in keys_to_delete:
            if self.delete(key):
                invalidated_count += 1
        
        return invalidated_count
