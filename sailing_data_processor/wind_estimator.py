# -*- coding: utf-8 -*-
# 最適化されたwind_estimator.pyファイルに置き換え

"""
sailing_data_processor.wind_estimator モジュール（最適化版）

GPSデータから風向風速を推定する機能を提供するモジュール
パフォーマンス改善のために最適化されています
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Union, Any
import math
from functools import lru_cache
import warnings
import re
import gc

class WindEstimator:
    """
    風向風速推定クラス
    
    GPSデータから艇の動きを分析し、風向風速を推定するためのクラス。
    特に以下の機能を提供します：
    - タック/ジャイブなどのマニューバーの特定
    - 風速・風向の推定
    - 風上・風下方位の判定
    """
    
    def __init__(self, boat_type: str = "default"):
        """
        初期化
        
        Parameters:
        -----------
        boat_type : str, optional
            艇種（デフォルト: "default"）
        """
        # コード情報
        self.version = "2.1.0"  # 最適化バージョン
        self.name = "WindEstimator"
        
        # 艇種設定
        self.boat_type = boat_type
        
        # 風向風速推定のデフォルトパラメータ
        # （艇種毎にカスタマイズ可能）
        self.params = {
            # 風上判定の最大角度（度）- 風向との差がこの値未満なら風上と判定
            "upwind_threshold": 45.0,
            
            # 風下判定の最小角度（度）- 風向との差がこの値より大きければ風下と判定
            "downwind_threshold": 120.0,
            
            # タック/ジャイブ検出の最小方位変化（度）
            "min_tack_angle_change": 60.0,
            
            # タック/ジャイブ検出の最小時間間隔（秒）
            "min_maneuver_duration": 3.0,
            
            # タック/ジャイブ検出の最大時間間隔（秒）
            "max_maneuver_duration": 20.0,
            
            # マニューバー検出の移動ウィンドウサイズ
            "maneuver_window_size": 5,
            
            # 風向推定の平滑化ウィンドウサイズ
            "wind_smoothing_window": 5,
            
            # 速度変化に基づくタック検出の閾値（%）- タック中は通常速度が落ちる
            "tack_speed_drop_threshold": 30.0,
            
            # 風向風速推定における最小速度閾値（ノット）- これ未満の速度は信頼性が低い
            "min_speed_threshold": 2.0,
            
            # 風上帆走時の艇速に対する見かけ風向の補正係数
            "upwind_correction_factor": 0.8,
            
            # 風下帆走時の艇速に対する見かけ風向の補正係数
            "downwind_correction_factor": 1.2,
            
            # 風向推定のための最適VMGでの風向に対する舵角の標準値（度）
            # 風上：風向から何度開けるか、風下：風向から何度狭めるか
            "default_upwind_angle": 42.0,
            "default_downwind_angle": 150.0,
            
            # キャッシュサイズ
            "cache_size": 128
        }
        
        # 艇種に応じたパラメータ調整
        self._adjust_params_by_boat_type(boat_type)
        
        # 風向風速の推定結果
        self.estimated_wind = {
            "direction": 0.0,   # 度（0-360、真北基準）
            "speed": 0.0,       # ノット
            "confidence": 0.0,  # 信頼度（0-1）
            "method": "none",   # 推定方法
            "timestamp": None   # タイムスタンプ
        }
        
        # マニューバー検出結果
        self.detected_maneuvers = []
        
        # 計算用一時変数（メモリの最適化のため明示的に宣言）
        self._temp_bearings = None
        self._temp_speeds = None
        
    def _adjust_params_by_boat_type(self, boat_type: str) -> None:
        """
        艇種に応じたパラメータ調整
        
        Parameters:
        -----------
        boat_type : str
            艇種
        """
        # 艇種ごとのカスタム設定
        if boat_type.lower() == "laser":
            self.params["default_upwind_angle"] = 45.0
            self.params["default_downwind_angle"] = 140.0
            self.params["tack_speed_drop_threshold"] = 40.0
        elif boat_type.lower() == "470":
            self.params["default_upwind_angle"] = 42.0
            self.params["default_downwind_angle"] = 145.0
            self.params["tack_speed_drop_threshold"] = 35.0
        elif boat_type.lower() == "49er":
            self.params["default_upwind_angle"] = 38.0
            self.params["default_downwind_angle"] = 155.0
            self.params["tack_speed_drop_threshold"] = 30.0
        # その他の艇種は必要に応じて追加

    def estimate_wind_from_single_boat(self, gps_data: pd.DataFrame, min_tack_angle: float = 30.0,
                                     boat_type: str = None, use_bayesian: bool = True) -> pd.DataFrame:
        """
        単一艇のGPSデータから風向風速を推定
        
        Parameters:
        -----------
        gps_data : pd.DataFrame
            GPSデータフレーム
            必要なカラム：
            - timestamp: 時刻
            - latitude, longitude: 位置
            - speed: 速度（m/s）
            - course: 進行方位（度）
        min_tack_angle : float, optional
            タック検出の最小角度（度）
        boat_type : str, optional
            艇種
        use_bayesian : bool, optional
            ベイズ推定を使用するか
            
        Returns:
        --------
        pd.DataFrame
            推定された風向風速のデータフレーム
            カラム：
            - timestamp: タイムスタンプ
            - wind_direction: 風向（度）
            - wind_speed: 風速（ノット）
            - confidence: 信頼度（0-1）
            - method: 推定方法
        """
        # データ確認
        if gps_data.empty or len(gps_data) < 10:
            warnings.warn("データポイントが不足しています")
            return pd.DataFrame(columns=[
                'timestamp', 'wind_direction', 'wind_speed', 'confidence', 'method'
            ])
        
        # 必要なカラムのチェック
        required_columns = ['timestamp', 'latitude', 'longitude']
        if not all(col in gps_data.columns for col in required_columns):
            missing_cols = [col for col in required_columns if col not in gps_data.columns]
            warnings.warn(f"必要なカラムがありません: {missing_cols}")
            return pd.DataFrame(columns=[
                'timestamp', 'wind_direction', 'wind_speed', 'confidence', 'method'
            ])
        
        # 艇種の設定（指定があれば更新）
        if boat_type and boat_type != self.boat_type:
            self.boat_type = boat_type
            self._adjust_params_by_boat_type(boat_type)
        
        # データのコピーを作成（元データを変更しないため）
        df = gps_data.copy()
        
        # データの前処理
        df = self._preprocess_data(df)
        
        # 一時変数の初期化（メモリ最適化）
        self._temp_bearings = None
        self._temp_speeds = None
        
        # マニューバー（タック/ジャイブ）の検出
        tack_params = {'min_tack_angle': min_tack_angle}
        maneuvers = self.detect_maneuvers(df)
        
        # マニューバーに基づく風向推定
        wind_from_maneuvers = None
        if len(maneuvers) >= 2:
            try:
                wind_from_maneuvers = self._estimate_wind_from_maneuvers(maneuvers, df)
            except Exception as e:
                warnings.warn(f"マニューバーからの風向推定エラー: {str(e)}")
        
        # コース/速度の変化に基づく風向推定
        wind_from_course = None
        try:
            wind_from_course = self.estimate_wind_from_course_speed(df)
        except Exception as e:
            warnings.warn(f"コース/速度からの風向推定エラー: {str(e)}")
        
        # VMG解析に基づく風向推定
        wind_from_vmg = None
        try:
            wind_from_vmg = self._estimate_wind_from_vmg_analysis(df)
        except Exception as e:
            warnings.warn(f"VMG解析からの風向推定エラー: {str(e)}")
        
        # 統合推定（ベイズを使用する場合）
        if use_bayesian and wind_from_maneuvers and wind_from_course and wind_from_vmg:
            final_estimate = self._bayesian_wind_estimate([
                wind_from_maneuvers,
                wind_from_course,
                wind_from_vmg
            ])
        else:
            # 最も信頼度の高い推定を使用
            candidates = [est for est in [wind_from_maneuvers, wind_from_course, wind_from_vmg] if est is not None]
            if not candidates:
                final_estimate = {
                    "direction": 0.0,
                    "speed": 0.0,
                    "confidence": 0.0,
                    "method": "none",
                    "timestamp": df['timestamp'].iloc[-1] if not df.empty else None
                }
            else:
                final_estimate = max(candidates, key=lambda x: x["confidence"])
        
        # 結果をデータフレームに変換
        result_df = self._create_wind_time_series(df, final_estimate)
        
        # 結果を記録
        self.estimated_wind = final_estimate
        
        # 一時変数のクリア（メモリ解放）
        self._temp_bearings = None
        self._temp_speeds = None
        
        # ガベージコレクション
        gc.collect()
        
        return result_df
    
    # ベクトル演算に最適化された前処理関数
    def _preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        風向風速推定のためのデータ前処理（ベクトル化演算最適化版）
        
        Parameters:
        -----------
        df : pd.DataFrame
            処理するGPSデータフレーム
            
        Returns:
        --------
        pd.DataFrame
            前処理されたデータフレーム
        """
        # タイムスタンプのソート
        if not df.empty and 'timestamp' in df.columns:
            df = df.sort_values('timestamp').reset_index(drop=True)
        
        # 速度カラムがない場合、座標から計算
        if 'speed' not in df.columns:
            # 時間差分
            df['time_diff'] = df['timestamp'].diff().dt.total_seconds()
            
            # 最初の行はNaNになるので0で埋める
            df.loc[0, 'time_diff'] = 0
            
            # 距離計算のベクトル化バージョン
            lat_diff = df['latitude'].diff().fillna(0)
            lon_diff = df['longitude'].diff().fillna(0)
            
            # 簡易的な距離計算（ベクトル化）
            # 緯度1度は約111km、経度1度は緯度によって変わる（cos(lat)を掛ける）
            lat_km = lat_diff * 111.0
            # 経度の距離変換（緯度による調整）
            lon_km = lon_diff * 111.0 * np.cos(np.radians(df['latitude']))
            
            # 総距離（km）
            distance_km = np.sqrt(lat_km**2 + lon_km**2)
            
            # 速度計算（km/h→m/s）
            # 有効な時間差分（ゼロ除算回避）のみ計算
            mask = df['time_diff'] > 0
            df.loc[mask, 'speed'] = distance_km[mask] / df.loc[mask, 'time_diff'] * 1000 / 3.6
            
            # 無効な値を0に設定
            df.loc[~mask, 'speed'] = 0
        
        # コースカラムがない場合、座標から計算
        if 'course' not in df.columns:
            # 緯度経度の差分を計算
            lat_diff = df['latitude'].diff().fillna(0)
            lon_diff = df['longitude'].diff().fillna(0)
            
            # 方位を計算（ベクトル化）- arctan2は象限を考慮
            # 北を0度として時計回りに角度を計算
            df['course'] = np.degrees(np.arctan2(lon_diff, lat_diff)) % 360
            
            # 最初の行は前の点からの差分が計算できないので、次の点と同じ方位とする
            if len(df) > 1:
                df.loc[0, 'course'] = df.loc[1, 'course']
        
        # 不要な列を削除してメモリ効率を向上
        if 'time_diff' in df.columns:
            df = df.drop(columns=['time_diff'])
        
        # NaNを除去
        df = df.dropna(subset=['speed', 'course']).reset_index(drop=True)
        
        return df

    # LRUキャッシュを使った一時データセット生成（メモリ使用量削減のため）
    @lru_cache(maxsize=64)  # キャッシュサイズを増加
    def _get_course_speed_dataset(self, dataset_hash: str) -> Tuple[np.ndarray, np.ndarray]:
        """
        コースと速度のデータセットを取得（キャッシュ付き）
        
        Parameters:
        -----------
        dataset_hash : str
            データセットを識別するためのハッシュ文字列
            
        Returns:
        --------
        Tuple[np.ndarray, np.ndarray]
            (コース配列, 速度配列)のタプル
        """
        # 実際にはハッシュではなく、キャッシュ用の識別子として利用
        # 中身はダミーとして返す
        return (self._temp_bearings, self._temp_speeds)
    
    # ベクトル化された風向推定（コースと速度から）
    def estimate_wind_from_course_speed(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        コースと速度のデータから風向を推定（追加最適化版）
        
        Parameters:
        -----------
        df : pd.DataFrame
            GPSデータフレーム
            
        Returns:
        --------
        Dict[str, Any]
            風向風速推定結果
        """
        if df.empty or len(df) < 5:
            return self._create_wind_result(0.0, 0.0, 0.0, "insufficient_data", None)
            
        # 必要なカラムがあるかチェック
        if 'course' not in df.columns or 'speed' not in df.columns:
            return self._create_wind_result(0.0, 0.0, 0.0, "missing_data", None)
        
        # 最新のタイムスタンプを取得（後で使うため先に取得）
        latest_timestamp = df['timestamp'].max()
        
        # 有効なデータのみを抽出（最小速度以上のもの）
        min_speed_threshold = self.params["min_speed_threshold"]
        # コピーを避けて参照のみに変更（メモリ効率改善）
        valid_mask = df['speed'] >= min_speed_threshold
        
        if np.sum(valid_mask) < 5:
            return self._create_wind_result(0.0, 0.0, 0.0, "insufficient_valid_data", None)
        
        # ベクトル化のためのnumpy配列（マスク適用でコピーを最小化）
        courses = df.loc[valid_mask, 'course'].values
        speeds = df.loc[valid_mask, 'speed'].values
        
        # 一時保存（キャッシュに使用）
        self._temp_bearings = courses
        self._temp_speeds = speeds
        
        # コンパス全周を10度ずつ、36個の候補風向を評価（ベクトル演算）
        candidate_wind_dirs = np.arange(0, 360, 10)
        scores = np.zeros(len(candidate_wind_dirs))
        
        # パラメータを事前抽出して繰り返しアクセスによるオーバーヘッドを削減
        upwind_threshold = self.params["upwind_threshold"]
        downwind_threshold = self.params["downwind_threshold"]
        default_upwind_angle = self.params["default_upwind_angle"]
        default_downwind_angle = self.params["default_downwind_angle"]
        
        # メモリ割り当てを最小化するため、事前に配列を作成
        rel_angles = np.zeros_like(courses)
        abs_rel_angles = np.zeros_like(courses)
        
        # 各候補風向に対する評価をベクトル化
        for i, wind_dir in enumerate(candidate_wind_dirs):
            # コースと風向の相対角度を計算（ベクトル化）
            np.subtract(courses, wind_dir, out=rel_angles)
            np.add(rel_angles, 180, out=rel_angles)
            np.mod(rel_angles, 360, out=rel_angles)
            np.subtract(rel_angles, 180, out=rel_angles)
            np.abs(rel_angles, out=abs_rel_angles)
            
            # 風上・風下のカテゴリ分け
            upwind_mask = abs_rel_angles < upwind_threshold
            downwind_mask = abs_rel_angles > downwind_threshold
            
            # 風上・風下でのスピード比率
            upwind_count = np.sum(upwind_mask)
            downwind_count = np.sum(downwind_mask)
            
            if upwind_count > 0 and downwind_count > 0:
                upwind_speeds = speeds[upwind_mask]
                downwind_speeds = speeds[downwind_mask]
                
                # 風上と風下の平均速度の比率を計算
                upwind_avg = np.mean(upwind_speeds)
                downwind_avg = np.mean(downwind_speeds)
                
                if upwind_avg > 0:
                    speed_ratio = downwind_avg / upwind_avg
                    
                    # 一般的に風下速度 > 風上速度となるはず
                    # 1.2〜1.8くらいが典型的な比率
                    # 理論的には比率が近いほど正確な風向の可能性が高い
                    expected_ratio = 1.5  # 典型的な比率
                    ratio_score = 1.0 - min(0.5, abs(speed_ratio - expected_ratio) / expected_ratio)
                    scores[i] += ratio_score
            
            # 風上範囲の角度分布（十分なデータポイントがある場合のみ）
            if upwind_count >= 5:
                upwind_angles = abs_rel_angles[upwind_mask]
                # ヒストグラムによるピーク検出（ベクトル化）- ビン数を減らして計算量削減
                hist, bin_edges = np.histogram(upwind_angles, bins=5, range=(0, 90))
                
                if np.max(hist) > 0:
                    # ピークの位置を特定（最頻値）
                    peak_idx = np.argmax(hist)
                    # bin_centersの計算を簡略化
                    peak_angle = bin_edges[peak_idx] + (bin_edges[peak_idx+1] - bin_edges[peak_idx]) / 2
                    
                    # 典型的な風上角度との比較
                    angle_diff = abs(peak_angle - default_upwind_angle)
                    angle_score = 1.0 - min(1.0, angle_diff / 20.0)
                    scores[i] += angle_score * 2.0  # 風上は重要なので重み付け
            
            # 風下範囲の角度分布（十分なデータポイントがある場合のみ）
            if downwind_count >= 5:
                downwind_angles = abs_rel_angles[downwind_mask]
                # ヒストグラムによるピーク検出（ベクトル化）- ビン数を減らして計算量削減
                hist, bin_edges = np.histogram(downwind_angles, bins=5, range=(90, 180))
                
                if np.max(hist) > 0:
                    # ピークの位置を特定（最頻値）
                    peak_idx = np.argmax(hist)
                    # bin_centersの計算を簡略化
                    peak_angle = bin_edges[peak_idx] + (bin_edges[peak_idx+1] - bin_edges[peak_idx]) / 2
                    
                    # 典型的な風下角度との比較
                    angle_diff = abs(peak_angle - default_downwind_angle)
                    angle_score = 1.0 - min(1.0, angle_diff / 30.0)
                    scores[i] += angle_score
        
        # 最高スコアの風向を選択（アルゴリズムを変更せずに効率化）
        best_idx = np.argmax(scores)
        best_wind_dir = candidate_wind_dirs[best_idx]
        best_score = scores[best_idx]
        
        # 信頼度の計算
        confidence = min(0.7, best_score / 4.0)
        
        # スコアが低すぎる場合は信頼度を下げる
        if best_score < 1.0:
            confidence = min(confidence, 0.3)
        
        # 風速推定
        wind_speed = self._estimate_wind_speed_from_speed_variations(df)
        
        return self._create_wind_result(
            best_wind_dir, wind_speed, confidence, 
            "course_speed_analysis", latest_timestamp
        )
    
    # 風速推定のベクトル化版
    def _estimate_wind_speed_from_speed_variations(self, df: pd.DataFrame) -> float:
        """
        艇速変動から風速を推定（ベクトル化版）
        
        Parameters:
        -----------
        df : pd.DataFrame
            GPSデータフレーム
            
        Returns:
        --------
        float
            推定風速（ノット）
        """
        if df.empty or 'speed' not in df.columns:
            return 0.0
            
        # 有効なデータのみを使用
        valid_speeds = df[df['speed'] > 0.5]['speed'].values
        
        if len(valid_speeds) < 5:
            return 0.0
        
        # 基本的な風速推定（艇速の中央値に基づく）
        median_speed = np.median(valid_speeds)
        max_speed = np.percentile(valid_speeds, 95)  # 外れ値を除外するため95パーセンタイル使用
        
        # 風速 = 最大艇速 x 0.6〜0.8程度（艇種により異なる）
        # 一般的な推定式: 風速 = 最大艇速 x 0.7
        estimated_wind_speed = max_speed * 0.7
        
        # 中央値との比率で調整（風速変動度合いを反映）
        if median_speed > 0:
            variation_ratio = max_speed / median_speed
            
            # 変動が大きい場合（強風の可能性）
            if variation_ratio > 1.5:
                estimated_wind_speed *= 1.1
            # 変動が小さい場合（弱風・安定風の可能性）
            elif variation_ratio < 1.2:
                estimated_wind_speed *= 0.9
        
        return round(estimated_wind_speed, 1)  # 小数点以下1桁に丸める

    def _create_wind_result(self, direction: float, speed: float, confidence: float, 
                           method: str, timestamp: Optional[datetime]) -> Dict[str, Any]:
        """
        風向風速の推定結果を作成
        
        Parameters:
        -----------
        direction : float
            風向（度、真北基準）
        speed : float
            風速（ノット）
        confidence : float
            信頼度（0-1）
        method : str
            推定方法
        timestamp : datetime or None
            タイムスタンプ
            
        Returns:
        --------
        Dict[str, Any]
            風向風速推定結果
        """
        return {
            "direction": direction,
            "speed": speed,
            "confidence": confidence,
            "method": method,
            "timestamp": timestamp
        }
    
    def _create_wind_time_series(self, gps_df: pd.DataFrame, 
                                wind_estimate: Dict[str, Any]) -> pd.DataFrame:
        """
        GPSデータに対応する風向風速の時系列データを作成
        
        Parameters:
        -----------
        gps_df : pd.DataFrame
            GPSデータフレーム
        wind_estimate : Dict[str, Any]
            風向風速推定結果
            
        Returns:
        --------
        pd.DataFrame
            風向風速の時系列データフレーム
        """
        if gps_df.empty:
            return pd.DataFrame(columns=[
                'timestamp', 'wind_direction', 'wind_speed', 'confidence', 'method'
            ])
            
        # タイムスタンプの取得
        timestamps = gps_df['timestamp'].copy()
        
        # 推定値の取得
        direction = wind_estimate["direction"]
        speed = wind_estimate["speed"]
        confidence = wind_estimate["confidence"]
        method = wind_estimate["method"]
        
        # データフレーム作成（ベクトル化）
        wind_df = pd.DataFrame({
            'timestamp': timestamps,
            'wind_direction': np.full(len(timestamps), direction),
            'wind_speed': np.full(len(timestamps), speed),
            'confidence': np.full(len(timestamps), confidence),
            'method': np.full(len(timestamps), method)
        })
        
        return wind_df
    
    # メモリ解放用メソッド（強化版）
    def cleanup(self):
        """メモリを明示的に解放（最適化）"""
        # 一時データの解放
        self._temp_bearings = None
        self._temp_speeds = None
        self.detected_maneuvers = []
        
        # すべてのキャッシュをクリア
        self._get_course_speed_dataset.cache_clear()
        self._calculate_angle_difference.cache_clear()
        
        # メモリ使用効率向上のためのガベージコレクション
        gc.collect()
        
    def _estimate_wind_from_maneuvers(self, maneuvers: pd.DataFrame, full_df: pd.DataFrame) -> Dict[str, Any]:
        """
        マニューバー（タック/ジャイブ）から風向風速を推定（最適化版）
        
        Parameters:
        -----------
        maneuvers : pd.DataFrame
            検出されたマニューバーのデータフレーム
        full_df : pd.DataFrame
            完全なGPSデータフレーム
            
        Returns:
        --------
        Dict[str, Any]
            風向風速推定結果
        """
        if maneuvers.empty or len(maneuvers) < 2:
            return None
        
        # 最新のタイムスタンプ
        latest_timestamp = full_df['timestamp'].max()
        
        # ベクトル計算のための配列準備
        before_bearings = maneuvers['before_bearing'].values
        after_bearings = maneuvers['after_bearing'].values
        timestamps = maneuvers['timestamp'].values
        
        # 風向計算（ベクトル化）
        angle_diffs = np.zeros(len(maneuvers), dtype=np.float32)
        wind_directions = np.zeros(len(maneuvers), dtype=np.float32)
        confidences = np.zeros(len(maneuvers), dtype=np.float32)
        
        # ベクトル化した角度差と風向計算
        for i in range(len(maneuvers)):
            # 角度差の計算
            angle_diff = self._calculate_angle_difference(after_bearings[i], before_bearings[i])
            angle_diffs[i] = angle_diff
            
            # 風向の計算（往復の中間方向の反対）
            wind_dir = (before_bearings[i] + angle_diff / 2) % 360
            # タックは風上への操船なので、求まった方向とは反対（180度反転）
            wind_dir = (wind_dir + 180) % 360
            wind_directions[i] = wind_dir
            
            # 信頼度の計算
            abs_diff = abs(angle_diff)
            confidences[i] = 1.0 - min(1.0, abs(abs_diff - 180) / 90)
        
        # 重み付き平均の計算
        # 最新のマニューバーほど信頼性が高いとして時間重みを追加
        time_weights = np.linspace(0.5, 1.0, len(timestamps))
        
        # 信頼度と時間重みを積算
        combined_weights = confidences * time_weights
        
        # 角度の加重平均（円環統計）- ベクトル化
        sin_values = np.sin(np.radians(wind_directions))
        cos_values = np.cos(np.radians(wind_directions))
        
        weighted_sin = np.average(sin_values, weights=combined_weights)
        weighted_cos = np.average(cos_values, weights=combined_weights)
        
        avg_wind_dir = np.degrees(np.arctan2(weighted_sin, weighted_cos)) % 360
        avg_confidence = np.mean(confidences)
        
        # 風速の推定
        wind_speed = self._estimate_wind_speed_from_maneuvers(maneuvers, full_df)
        
        return self._create_wind_result(
            float(avg_wind_dir), wind_speed, float(avg_confidence),
            "maneuver_analysis", latest_timestamp
        )
    
    def _estimate_wind_speed_from_maneuvers(self, maneuvers_df: pd.DataFrame, full_df: pd.DataFrame) -> float:
        """
        マニューバー前後の速度から風速を推定（最適化版）
        
        Parameters:
        -----------
        maneuvers_df : pd.DataFrame
            マニューバーのデータフレーム
        full_df : pd.DataFrame
            完全なGPSデータフレーム
            
        Returns:
        --------
        float
            推定風速（ノット）
        """
        if maneuvers_df.empty:
            return self._estimate_wind_speed_from_speed_variations(full_df)
        
        # 風速推定値を格納する配列
        wind_speeds = []
        
        # データをnumpy配列として取得（ベクトル計算の準備）
        timestamps = pd.to_datetime(maneuvers_df['timestamp'].values)
        speeds_array = full_df['speed'].values
        times_array = pd.to_datetime(full_df['timestamp'].values)
        maneuver_types = maneuvers_df['maneuver_type'].values if 'maneuver_type' in maneuvers_df.columns else None
        
        # 各マニューバーについて処理
        for i, timestamp in enumerate(timestamps):
            # マニューバー前後の時間範囲
            pre_time_start = timestamp - timedelta(seconds=30)
            pre_time_end = timestamp - timedelta(seconds=5)
            post_time_start = timestamp + timedelta(seconds=5)
            post_time_end = timestamp + timedelta(seconds=30)
            
            # 前後のインデックスをベクトル計算
            pre_indices = np.where((times_array >= pre_time_start) & (times_array <= pre_time_end))[0]
            post_indices = np.where((times_array >= post_time_start) & (times_array <= post_time_end))[0]
            
            # 十分なデータがある場合
            if len(pre_indices) >= 3 and len(post_indices) >= 3:
                # 前後の平均速度
                pre_speed = np.mean(speeds_array[pre_indices])
                post_speed = np.mean(speeds_array[post_indices])
                
                # マニューバータイプによる推定係数
                maneuver_type = maneuver_types[i] if maneuver_types is not None else "unknown"
                
                # 最大速度を基に風速を推定
                max_speed = max(pre_speed, post_speed)
                
                if maneuver_type == "tack":
                    # 風上なら一般に艇速は風速の0.6～0.8倍程度
                    est_wind_speed = max_speed / 0.7
                else:  # ジャイブまたは不明の場合
                    # 風下なら一般に艇速は風速の0.6～0.7倍程度
                    est_wind_speed = max_speed / 0.65
                
                wind_speeds.append(est_wind_speed)
        
        # 複数の推定値の中央値（外れ値に堅牢）
        if wind_speeds:
            return float(np.median(wind_speeds))
        
        # 推定できない場合は代替手法
        return self._estimate_wind_speed_from_speed_variations(full_df)
    
    def _estimate_wind_from_vmg_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        VMG（Velocity Made Good）分析に基づく風向推定（追加最適化版）
        
        この関数は分析処理の中で比較的計算コストが高い部分を最適化します。
        
        Parameters:
        -----------
        df : pd.DataFrame
            GPSデータフレーム
            
        Returns:
        --------
        Dict[str, Any]
            風向風速推定結果
        """
        if df.empty or len(df) < 10:
            return None
        
        # 必要なカラムがあるか確認
        if 'course' not in df.columns or 'speed' not in df.columns:
            return None
            
        # 最新のタイムスタンプ（後で使うため先に取得）
        latest_timestamp = df['timestamp'].max()
        
        # パラメータを事前抽出して繰り返しアクセスによるオーバーヘッドを削減
        upwind_threshold = self.params["upwind_threshold"]
        downwind_threshold = self.params["downwind_threshold"]
        default_upwind_angle = self.params["default_upwind_angle"]
        default_downwind_angle = self.params["default_downwind_angle"]
        
        # 十分な速度のデータポイントのみ使用（コピーせずマスクのみ）
        min_speed = max(1.0, self.params["min_speed_threshold"])
        valid_mask = df['speed'] >= min_speed
        
        if np.sum(valid_mask) < 10:
            return None
            
        # コースと速度の配列を取得（マスク適用で直接抽出）
        courses = df.loc[valid_mask, 'course'].values
        speeds = df.loc[valid_mask, 'speed'].values
        
        # 風向の候補（45度刻みに変更して初期スクリーニングの計算量をさらに削減）
        wind_dirs = np.arange(0, 360, 45)
        vmg_scores = np.zeros(len(wind_dirs), dtype=np.float32)
        
        # 角度計算用の事前計算配列（メモリ再利用）
        rel_angles = np.zeros_like(courses)
        cos_angles = np.zeros_like(courses, dtype=np.float32)
        
        # 最適角度のキャッシュとして機能するディクショナリ
        # (削減された計算でも十分な精度を維持)
        angle_cache = {}
        
        # 1. 粗いスキャン: 45度刻みで最適方向を見つける
        for i, wind_dir in enumerate(wind_dirs):
            # 相対角度計算を効率化（一度の演算で完了）
            rel_angles = (courses - wind_dir + 180) % 360 - 180
            abs_angles = np.abs(rel_angles)
            
            # 風上・風下マスク（事前計算・再利用）
            upwind_mask = abs_angles <= upwind_threshold
            downwind_mask = abs_angles >= downwind_threshold
            
            # 風上・風下のデータポイント数を高速カウント
            upwind_count = np.count_nonzero(upwind_mask)
            downwind_count = np.count_nonzero(downwind_mask)
            
            # スコア計算（単純化）
            score = 0.0
            
            # 十分なデータがある場合のみVMG計算
            if upwind_count >= 5:
                # コサインの一括計算（radians変換も含む）
                cos_values = np.cos(np.radians(abs_angles[upwind_mask]))
                
                # VMG計算（ベクトル化）
                upwind_vmgs = speeds[upwind_mask] * cos_values
                
                if len(upwind_vmgs) > 0:
                    max_vmg_idx = np.argmax(upwind_vmgs)
                    best_angle = abs_angles[upwind_mask][max_vmg_idx]
                    
                    # 最適角度との差をスコア化（簡略化）
                    angle_diff = abs(best_angle - default_upwind_angle)
                    score += 1.5 * (1.0 - min(1.0, angle_diff / 20.0))
                    
                    # キャッシュに保存
                    angle_cache[f"{wind_dir}_upwind"] = best_angle
            
            if downwind_count >= 5:
                # 風下の場合は180度との差の余弦を使う（計算効率化）
                cos_values = np.cos(np.pi - np.radians(abs_angles[downwind_mask]))
                
                # VMG計算（ベクトル化）
                downwind_vmgs = speeds[downwind_mask] * cos_values
                
                if len(downwind_vmgs) > 0:
                    max_vmg_idx = np.argmax(downwind_vmgs)
                    best_angle = abs_angles[downwind_mask][max_vmg_idx]
                    
                    # 簡略化したスコア計算
                    angle_diff = abs(best_angle - default_downwind_angle)
                    score += 1.0 - min(1.0, angle_diff / 25.0)
                    
                    # キャッシュに保存
                    angle_cache[f"{wind_dir}_downwind"] = best_angle
            
            vmg_scores[i] = score
        
        # 最高スコアの風向を選択
        best_idx = np.argmax(vmg_scores)
        coarse_wind_dir = wind_dirs[best_idx]
        best_score = vmg_scores[best_idx]
        
        # 2. 精密スキャン: 粗いスキャンで得た最良の風向周辺だけを詳細分析
        # 計算量を削減するため、最適範囲のみを分析
        fine_range = 30  # 前後30度を分析（範囲を縮小）
        fine_step = 10   # 10度ステップ（ステップを増加）
        
        # 範囲計算を最適化
        range_min = (coarse_wind_dir - fine_range + 360) % 360
        range_max = (coarse_wind_dir + fine_range) % 360
        
        # 範囲が360度を跨ぐ場合の特別処理（簡略化）
        if range_min > range_max:
            # 範囲が360度を超える場合、2つの範囲に分割
            fine_dirs = []
            dir1 = range_min
            while dir1 < 360:
                fine_dirs.append(dir1)
                dir1 += fine_step
            
            dir2 = 0
            while dir2 <= range_max:
                fine_dirs.append(dir2)
                dir2 += fine_step
                
            fine_wind_dirs = np.array(fine_dirs)
        else:
            # 通常の範囲処理
            fine_wind_dirs = np.arange(range_min, range_max + 1, fine_step)
        
        # 詳細分析が必要な場合のみ実行
        if len(fine_wind_dirs) > 0 and best_score > 0:
            # 事前割り当てした配列（再利用）
            fine_scores = np.zeros(len(fine_wind_dirs), dtype=np.float32)
            
            # VMG計算を最適化（前計算したキャッシュを活用）
            for i, wind_dir in enumerate(fine_wind_dirs):
                # 相対角度の高速計算
                rel_angles = (courses - wind_dir + 180) % 360 - 180
                abs_angles = np.abs(rel_angles)
                
                # マスク計算
                upwind_mask = abs_angles <= upwind_threshold
                downwind_mask = abs_angles >= downwind_threshold
                
                # 風上・風下データの高速カウント
                upwind_count = np.count_nonzero(upwind_mask)
                downwind_count = np.count_nonzero(downwind_mask)
                
                # VMG計算を行うに十分なデータがあるか確認
                if upwind_count >= 3 and downwind_count >= 3:
                    # 風上VMGの直接計算（最適化・簡略化）
                    # キャッシュされた最適角度があれば使用
                    if f"{coarse_wind_dir}_upwind" in angle_cache:
                        target_upwind_angle = angle_cache[f"{coarse_wind_dir}_upwind"]
                        # 最適角度に近いデータポイントを探す（計算省略）
                        # 各データポイントで再計算せず、事前計算した角度に基づく
                        upwind_vmg_score = np.mean(speeds[upwind_mask] * 
                                                 (1.0 - abs(abs_angles[upwind_mask] - target_upwind_angle) / 45.0))
                    else:
                        # 直接VMG計算（省略されたケース）
                        upwind_vmg_score = np.mean(speeds[upwind_mask] * np.cos(np.radians(abs_angles[upwind_mask])))
                    
                    # 風下VMGも同様に最適化
                    if f"{coarse_wind_dir}_downwind" in angle_cache:
                        target_downwind_angle = angle_cache[f"{coarse_wind_dir}_downwind"]
                        downwind_vmg_score = np.mean(speeds[downwind_mask] * 
                                                   (1.0 - abs(abs_angles[downwind_mask] - target_downwind_angle) / 60.0))
                    else:
                        # 直接VMG計算
                        downwind_vmg_score = np.mean(speeds[downwind_mask] * np.cos(np.pi - np.radians(abs_angles[downwind_mask])))
                    
                    # 合計スコア（単純化）
                    fine_scores[i] = upwind_vmg_score * 1.5 + downwind_vmg_score
            
            # 最良の詳細風向を選択
            if np.max(fine_scores) > 0:
                fine_best_idx = np.argmax(fine_scores)
                best_wind_dir = fine_wind_dirs[fine_best_idx]
                # スコアは粗い方を使用（一貫性を保つため）
            else:
                best_wind_dir = coarse_wind_dir
        else:
            best_wind_dir = coarse_wind_dir
        
        # 信頼度の計算（単純化）
        confidence = min(0.75, best_score / 3.0)
        
        # スコアが低すぎる場合は信頼度を下げる
        if best_score < 1.0:
            confidence = min(confidence, 0.4)
        
        # 風速の推定（他のメソッドを再利用）
        wind_speed = self._estimate_wind_speed_from_speed_variations(df)
        
        return self._create_wind_result(
            float(best_wind_dir), wind_speed, float(confidence),
            "vmg_analysis", latest_timestamp
        )
    
    def _bayesian_wind_estimate(self, estimates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        複数の風向推定をベイズ統合（最適化版）
        
        Parameters:
        -----------
        estimates : List[Dict[str, Any]]
            風向風速推定結果のリスト
            
        Returns:
        --------
        Dict[str, Any]
            統合された風向風速推定結果
        """
        # 早期リターンで冗長な処理を削減
        if not estimates:
            return None
        
        # 1つだけの場合はそのまま返す（処理スキップ）
        if len(estimates) == 1:
            return estimates[0]
        
        # 有効な推定結果を事前に絞り込み（高速フィルタリング）
        # リスト内包表記を1回のループで済ませる
        valid_estimates = []
        for est in estimates:
            if est and est.get("confidence", 0) > 0:
                valid_estimates.append(est)
        
        # 有効な推定が1つもなければ早期リターン
        if not valid_estimates:
            return None
        
        # 1つだけの場合は処理を簡略化
        if len(valid_estimates) == 1:
            return valid_estimates[0]
        
        # データを一度で抽出（繰り返し辞書アクセスを回避）
        directions = []
        confidences = []
        speeds = []
        timestamps = []
        
        for est in valid_estimates:
            directions.append(est["direction"])
            confidences.append(est["confidence"])
            speeds.append(est["speed"])
            if est["timestamp"] is not None:
                timestamps.append(est["timestamp"])
        
        # numpy配列変換（一括処理）
        directions = np.array(directions, dtype=np.float32)
        confidences = np.array(confidences, dtype=np.float32)
        speeds = np.array(speeds, dtype=np.float32)
        
        # 効率的な角度計算（ラジアン変換を一度に実行）
        rad_angles = np.radians(directions)
        sin_vals = np.sin(rad_angles)
        cos_vals = np.cos(rad_angles)
        
        # 重みつき平均の加速（事前計算した値を利用）
        # confidencesの合計が0になる可能性をチェック
        conf_sum = np.sum(confidences)
        if conf_sum > 0:
            weighted_sin = np.sum(sin_vals * confidences) / conf_sum
            weighted_cos = np.sum(cos_vals * confidences) / conf_sum
            avg_dir = np.degrees(np.arctan2(weighted_sin, weighted_cos)) % 360
        else:
            # 信頼度がすべて0の場合は単純平均
            avg_dir = np.degrees(np.arctan2(np.mean(sin_vals), np.mean(cos_vals))) % 360
        
        # 風速の重み付き平均（高速計算）
        avg_speed = np.sum(speeds * confidences) / conf_sum if conf_sum > 0 else np.mean(speeds)
        
        # 信頼度の効率的な統合（計算を単純化）
        max_confidence = np.max(confidences)
        combined_confidence = max_confidence + ((1 - max_confidence) * min(0.3, len(valid_estimates) * 0.1))
        combined_confidence = min(0.95, combined_confidence)  # 上限値で制限
        
        # タイムスタンプは直接最大値を取得（条件付きループを削減）
        latest_ts = max(timestamps) if timestamps else None
        
        # 結果生成（キャスト不要でそのまま適用）
        return self._create_wind_result(
            avg_dir, avg_speed, combined_confidence,
            "bayesian_fusion", latest_ts
        )
    
    @lru_cache(maxsize=1024)  # キャッシュサイズをさらに増加
    def _calculate_angle_difference(self, angle1: float, angle2: float) -> float:
        """
        2つの角度間の最小差を計算する（キャッシュ付き高速版）
        
        Parameters:
        -----------
        angle1 : float
            1つ目の角度（度、0-360）
        angle2 : float
            2つ目の角度（度、0-360）
            
        Returns:
        --------
        float
            最小角度差（度、-180〜180）
        """
        # 高速化のため、丸め処理を行い小数点以下を制限（キャッシュヒット率向上）
        # 0.5度単位で丸めることでキャッシュの効率を大幅に向上（差は無視できる程度）
        a1 = round(angle1 * 2) / 2
        a2 = round(angle2 * 2) / 2
        
        # 0-360の範囲に高速に正規化
        a1 %= 360
        a2 %= 360
        
        # 最短経路の差を計算（一行に集約して演算回数削減）
        return ((a1 - a2 + 180) % 360) - 180
    
    def detect_maneuvers(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        航跡データからマニューバー（タック・ジャイブ）を検出（最適化版）
        
        Parameters:
        -----------
        df : pd.DataFrame
            GPSデータフレーム
            
        Returns:
        --------
        pd.DataFrame
            検出されたマニューバーのデータフレーム
        """
        if df.empty or len(df) < 10:
            return pd.DataFrame()
        
        # 必要なカラムの確認
        required_columns = ['timestamp', 'latitude', 'longitude', 'course', 'speed']
        if not all(col in df.columns for col in required_columns):
            warnings.warn("マニューバー検出に必要なカラムがありません")
            return pd.DataFrame()
        
        # コースの変化率を計算（ベクトル化）
        df_copy = df.copy()
        df_copy['course_prev'] = df_copy['course'].shift(1)
        
        # NaNを除外
        df_copy = df_copy.dropna(subset=['course_prev'])
        
        if len(df_copy) < 5:
            return pd.DataFrame()
        
        # コース変化の計算（ベクトル化）
        course_array = df_copy['course'].values
        course_prev_array = df_copy['course_prev'].values
        bearing_change = np.zeros(len(df_copy), dtype=np.float32)
        
        # ベクトル計算の準備
        for i in range(len(df_copy)):
            # 効率的な角度差の計算
            angle_diff = ((course_array[i] - course_prev_array[i] + 180) % 360) - 180
            bearing_change[i] = abs(angle_diff)
        
        df_copy['bearing_change'] = bearing_change
        
        # 移動平均でノイズを軽減（ウィンドウサイズはパラメータから取得）
        window_size = self.params['maneuver_window_size']
        df_copy['bearing_change_ma'] = df_copy['bearing_change'].rolling(
            window=window_size, min_periods=1, center=True
        ).mean()
        
        # マニューバー（大きな方向転換）の検出
        # タック/ジャイブの判定を安定化するためしきい値より大きい変化を検出
        min_angle_change = self.params['min_tack_angle_change']
        df_copy['is_maneuver'] = df_copy['bearing_change_ma'] > min_angle_change
        
        # 連続するフラグを一つのマニューバーとしてグループ化
        df_copy['maneuver_group'] = (df_copy['is_maneuver'] != df_copy['is_maneuver'].shift(1)).cumsum()
        
        # マニューバーとみなされるグループのみ抽出
        maneuver_groups = df_copy[df_copy['is_maneuver']].groupby('maneuver_group')
        
        # 各マニューバーグループから代表点を抽出
        maneuver_points = []
        
        for group_id, group in maneuver_groups:
            if len(group) > 0:
                # グループ内で最も大きな方向変化を持つ点を中心とする
                central_idx = group['bearing_change'].idxmax()
                central_point = df.loc[central_idx]
                
                # 前後のデータポイントを取得（タイムベース）
                timestamp = central_point['timestamp']
                before_time = timestamp - timedelta(seconds=5)
                after_time = timestamp + timedelta(seconds=5)
                
                # 前後の時間帯のデータを抽出
                before_df = df[(df['timestamp'] < timestamp) & (df['timestamp'] >= before_time)]
                after_df = df[(df['timestamp'] > timestamp) & (df['timestamp'] <= after_time)]
                
                # 前後に十分なデータがある場合のみ処理
                if len(before_df) >= 2 and len(after_df) >= 2:
                    # 平均値の計算（効率化）
                    before_bearing = before_df['course'].mean()
                    after_bearing = after_df['course'].mean()
                    bearing_change = self._calculate_angle_difference(after_bearing, before_bearing)
                    
                    speed_before = before_df['speed'].mean()
                    speed_after = after_df['speed'].mean()
                    
                    # 速度比の計算（ゼロ除算回避）
                    speed_ratio = speed_after / speed_before if speed_before > 0 else 1.0
                    
                    # マニューバー時間計算
                    maneuver_duration = (after_df['timestamp'].min() - before_df['timestamp'].max()).total_seconds()
                    
                    # マニューバーポイントを追加
                    maneuver_points.append({
                        'timestamp': timestamp,
                        'latitude': central_point['latitude'],
                        'longitude': central_point['longitude'],
                        'before_bearing': before_bearing,
                        'after_bearing': after_bearing,
                        'bearing_change': bearing_change,
                        'speed_before': speed_before,
                        'speed_after': speed_after,
                        'speed_ratio': speed_ratio,
                        'maneuver_duration': maneuver_duration,
                        'maneuver_type': 'unknown'  # タイプは後で分類
                    })
        
        # データフレームに変換
        if not maneuver_points:
            return pd.DataFrame()
            
        result_df = pd.DataFrame(maneuver_points)
        
        # マニューバーのタイプを分類（タック/ジャイブ）
        if not result_df.empty:
            result_df = self.categorize_maneuvers(result_df, df)
        
        return result_df
    
    def categorize_maneuvers(self, maneuvers_df: pd.DataFrame, full_df: pd.DataFrame) -> pd.DataFrame:
        """
        検出されたマニューバーをタック/ジャイブに分類（最適化版）
        
        Parameters:
        -----------
        maneuvers_df : pd.DataFrame
            検出されたマニューバーのデータフレーム
        full_df : pd.DataFrame
            完全なGPSデータフレーム
            
        Returns:
        --------
        pd.DataFrame
            分類されたマニューバーのデータフレーム
        """
        if maneuvers_df.empty:
            return maneuvers_df
            
        # コピーを作成
        result_df = maneuvers_df.copy()
        
        # 風向推定（必要なだけ）
        wind_result = self.estimate_wind_from_course_speed(full_df)
        wind_direction = wind_result['direction']
        
        # ベクトル化のための配列を準備
        before_bearings = result_df['before_bearing'].values
        after_bearings = result_df['after_bearing'].values
        bearing_changes = result_df['bearing_change'].values
        speed_ratios = result_df['speed_ratio'].values
        
        # 新しい列を作成
        result_df['wind_direction'] = wind_direction
        result_df['before_rel_wind'] = np.zeros(len(result_df), dtype=np.float32)
        result_df['after_rel_wind'] = np.zeros(len(result_df), dtype=np.float32)
        result_df['maneuver_type'] = "unknown"
        
        # ベクトル化した角度計算
        for i in range(len(result_df)):
            # 風向との相対角度
            before_rel_wind = self._calculate_angle_difference(before_bearings[i], wind_direction)
            after_rel_wind = self._calculate_angle_difference(after_bearings[i], wind_direction)
            
            result_df.at[i, 'before_rel_wind'] = before_rel_wind
            result_df.at[i, 'after_rel_wind'] = after_rel_wind
            
            # マニューバータイプの判定（ベクトル化しにくいので個別処理）
            # 風上判定
            before_is_upwind = abs(before_rel_wind) <= self.params["upwind_threshold"]
            after_is_upwind = abs(after_rel_wind) <= self.params["upwind_threshold"]
            
            # 風下判定
            before_is_downwind = abs(before_rel_wind) >= self.params["downwind_threshold"]
            after_is_downwind = abs(after_rel_wind) >= self.params["downwind_threshold"]
            
            # タックの判定（風上またはクローズリーチでのターン）
            tack_conditions = [
                # 両方風上、または風上→クローズリーチ、またはクローズリーチ→風上
                (before_is_upwind or abs(before_rel_wind) <= 60) and 
                (after_is_upwind or abs(after_rel_wind) <= 60),
                
                # 方位変化が60〜180度
                abs(bearing_changes[i]) >= 60 and abs(bearing_changes[i]) <= 180,
                
                # タック時は通常速度が落ちる
                speed_ratios[i] < 0.9 or speed_ratios[i] > 1.3  # タック後の加速も考慮
            ]
            
            # ジャイブの判定（風下またはブロードリーチでのターン）
            jibe_conditions = [
                # 両方風下、または風下→ブロードリーチ、またはブロードリーチ→風下
                (before_is_downwind or abs(before_rel_wind) >= 120) and 
                (after_is_downwind or abs(after_rel_wind) >= 120),
                
                # 方位変化が60〜180度
                abs(bearing_changes[i]) >= 60 and abs(bearing_changes[i]) <= 180
            ]
            
            # 分類結果を設定
            if all(tack_conditions):
                result_df.at[i, 'maneuver_type'] = 'tack'
            elif all(jibe_conditions):
                result_df.at[i, 'maneuver_type'] = 'jibe'
        
        return result_df

    def is_upwind(self, course: float, wind_direction: float) -> bool:
        """
        与えられた進行方向が風上かどうかを判定
        
        Parameters:
        -----------
        course : float
            進行方向（度、0-360）
        wind_direction : float
            風向（度、0-360、風が吹いてくる方向）
            
        Returns:
        --------
        bool
            True: 風上, False: 風上ではない
        """
        # 風向との相対角度（絶対値）
        rel_angle = abs(self._calculate_angle_difference(course, wind_direction))
        
        # 風上判定（閾値以下なら風上）
        return rel_angle <= self.params["upwind_threshold"]
    
    def is_downwind(self, course: float, wind_direction: float) -> bool:
        """
        与えられた進行方向が風下かどうかを判定
        
        Parameters:
        -----------
        course : float
            進行方向（度、0-360）
        wind_direction : float
            風向（度、0-360、風が吹いてくる方向）
            
        Returns:
        --------
        bool
            True: 風下, False: 風下ではない
        """
        # 風向との相対角度（絶対値）
        rel_angle = abs(self._calculate_angle_difference(course, wind_direction))
        
        # 風下判定（閾値以上なら風下）
        return rel_angle >= self.params["downwind_threshold"]
