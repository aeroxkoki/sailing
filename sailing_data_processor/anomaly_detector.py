# -*- coding: utf-8 -*-
"""
GPSデータの異常値検出と修正機能（互換レイヤー）

このモジュールは後方互換性のためのものです。
新しいアプリケーションは sailing_data_processor.anomaly パッケージを使用してください。
"""

import warnings
from typing import Dict, List, Optional

import pandas as pd

# 新しい実装をインポート
from sailing_data_processor.anomaly.base import create_anomaly_detector
# テスト互換性のためにGPSAnomalyDetectorを直接エクスポート
# sailing_data_processor.anomaly.gps モジュールからGPSAnomalyDetectorをインポート
try:
    from sailing_data_processor.anomaly.gps import GPSAnomalyDetector
except ImportError:
    # インポートエラーが発生した場合、直接クラス定義を提供（テスト用）
    class GPSAnomalyDetector:
        """
        テスト用の簡易GPSAnomalyDetector代替クラス
        """
        def __init__(self):
            self.detection_config = {
                'speed_multiplier': 3.0,
                'acceleration_threshold': 2.0,
                'time_gap_threshold': 60.0
            }
            self.interpolation_config = {
                'method': 'linear'
            }

# 警告を表示
warnings.warn(
    "このモジュールは後方互換性のために提供されています。"
    "新しいアプリケーションでは sailing_data_processor.anomaly パッケージを使用してください。",
    DeprecationWarning,
    stacklevel=2
)

class AnomalyDetector:
    """
    GPSデータの異常値検出クラス（互換レイヤー）
    
    このクラスは後方互換性のために提供されています。
    新しいアプリケーションでは sailing_data_processor.anomaly パッケージを使用してください。
    """
    
    def __init__(self):
        """初期化"""
        # 新しい実装のインスタンスを作成（GPS対応版を使用）
        self._detector = create_anomaly_detector('gps')
        
        # 互換性のために元のインターフェースの設定を保持
        self.detection_config = self._detector.detection_config
        self.interpolation_config = self._detector.interpolation_config
    
    def detect(self, df: pd.DataFrame, methods: Optional[List[str]] = None) -> pd.DataFrame:
        """
        後方互換性のための新しいメソッド - detect_anomaliesの別名
        
        Parameters:
        -----------
        df : pd.DataFrame
            検出対象のGPSデータフレーム
            必要なカラム: latitude, longitude, timestamp
        methods : List[str], optional
            使用する検出方法のリスト
            
        Returns:
        --------
        pd.DataFrame
            異常値フラグを追加したデータフレーム
        """
        return self.detect_anomalies(df, methods)
    
    def detect_anomalies(self, df: pd.DataFrame, methods: Optional[List[str]] = None) -> pd.DataFrame:
        """
        複数の方法を組み合わせて異常値を検出
        
        Parameters:
        -----------
        df : pd.DataFrame
            検出対象のGPSデータフレーム
            必要なカラム: latitude, longitude, timestamp
        methods : List[str], optional
            使用する検出方法のリスト
            
        Returns:
        --------
        pd.DataFrame
            異常値フラグを追加したデータフレーム
        """
        # デフォルト値の設定（元の実装と同じ）
        if methods is None:
            methods = ['z_score', 'speed']
        
        # 新しい実装に委譲
        return self._detector.detect_anomalies(df, methods=methods)
    
    def fix_anomalies(self, df: pd.DataFrame, method: str = 'linear') -> pd.DataFrame:
        """
        異常値を修正する
        
        Parameters:
        -----------
        df : pd.DataFrame
            修正対象のGPSデータフレーム
            'is_anomaly'カラムが必要
        method : str
            修正方法
            
        Returns:
        --------
        pd.DataFrame
            修正済みデータフレーム
        """
        # 新しい実装に委譲
        return self._detector.fix_anomalies(df, method=method)
    
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        2点間のHaversine距離を計算（メートル）
        
        Parameters:
        -----------
        lat1, lon1 : float
            始点の緯度・経度
        lat2, lon2 : float
            終点の緯度・経度
            
        Returns:
        --------
        float
            距離（メートル）
        """
        # 新しい実装に委譲
        return self._detector._haversine_distance(lat1, lon1, lat2, lon2)
