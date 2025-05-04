# -*- coding: utf-8 -*-
# sailing_data_processor/core.py
"""
セーリングデータ処理の統合モジュール

SailingDataProcessorクラスを提供し、GPSデータから風推定、
パフォーマンス最適化、戦略分析を統合的に実行する。
"""

from typing import Dict, List, Tuple, Optional, Union, Any
import pandas as pd
import gc
import io
from datetime import datetime, timedelta

# 内部モジュールのインポート
from .core_io import SailingDataIO
from .core_analysis import SailingDataAnalyzer


class SailingDataProcessor(SailingDataIO, SailingDataAnalyzer):
    """セーリングデータ処理の統合クラス - GPSデータから風推定・戦略分析を実行"""
    
    def __init__(self):
        """初期化"""
        # 親クラスの初期化
        SailingDataIO.__init__(self)
        SailingDataAnalyzer.__init__(self)
        
        # 共有データ属性は統一する（両方の親クラスで使用される属性）
        self.boat_data = {}  # boat_id: DataFrameの辞書
        self.synced_data = {}  # 同期済みデータ
    
    def cleanup(self):
        """メモリをクリーンアップする"""
        # SailingDataIOからの属性
        self.boat_data.clear()
        self.synced_data.clear()
        
        # SailingDataAnalyzerからの属性
        self.processed_data.clear()
        self.wind_estimates.clear()
        self.wind_field_data.clear()
        
        gc.collect()
