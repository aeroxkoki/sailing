"""
sailing_data_processor.data_model

共通データ構造とデータアクセスパターンを提供するモジュール
"""

# バージョン情報
__version__ = '1.0.0'

# コンテナクラスをインポート
from .container import DataContainer, GPSDataContainer, WindDataContainer, StrategyPointContainer

# キャッシュ機能をインポート
from .cache_manager import (
    CacheManager, cache_manager, 
    cached, memoize, clear_cache, get_cache_stats
)

# デフォルトでエクスポートするシンボル
__all__ = [
    # データコンテナ
    'DataContainer',
    'GPSDataContainer',
    'WindDataContainer',
    'StrategyPointContainer',
    
    # キャッシュ関連
    'CacheManager',
    'cache_manager',
    'cached',
    'memoize',
    'clear_cache',
    'get_cache_stats'
]
