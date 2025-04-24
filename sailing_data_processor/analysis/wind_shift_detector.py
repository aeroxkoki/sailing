# -*- coding: utf-8 -*-
"""
sailing_data_processor.analysis.wind_shift_detector モジュール

GPSデータと風データから風向シフトを高精度に検出するための機能を提供します。
様々な検出手法を組み合わせ、ノイズに強い分析を実現します。
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union, Any
from datetime import datetime, timedelta
import math
from scipy import signal
from scipy.stats import circmean, circstd
import warnings

class StatisticalShiftDetector:
    """
    統計的手法による風向シフト検出クラス
    """
    
    def __init__(self, params):
        """初期化"""
        self.params = params
        
    def detect(self, wind_data: pd.DataFrame) -> List[Dict[str, Any]]:
        """統計的手法による検出実装"""
        if wind_data.empty or len(wind_data) < 10:
            return []
            
        # 時系列データとして処理
        df = wind_data.copy().sort_values('timestamp')
        
        # 風向の差分を計算
        df['wind_dir_prev'] = df['wind_direction'].shift(1)
        df['wind_dir_change'] = df.apply(
            lambda row: self._calculate_angle_difference(row['wind_direction'], row['wind_dir_prev']),
            axis=1
        )
        
        # 移動平均 (ノイズ軽減)
        window_size = self.params.get("window_size", 5)
        df['wind_dir_smooth'] = df['wind_direction'].rolling(window=window_size, center=True).apply(
            lambda x: circmean(np.radians(x)) * 180 / np.pi
        )
        
        # 標準偏差を計算し、異常値を検出
        df['wind_dir_rolling_std'] = df['wind_direction'].rolling(window=window_size, center=True).apply(
            lambda x: circstd(np.radians(x)) * 180 / np.pi
        )
        
        # シフト検出の閾値
        min_shift_angle = self.params.get("min_shift_angle", 5.0)
        
        # 重要な変化点を特定
        shift_points = []
        
        # 1. 大きな変化があった点
        significant_changes = df[abs(df['wind_dir_change']) > min_shift_angle].copy()
        
        # 2. 繰り返しパターンの検出 (類似の値が続いた後に変化)
        for idx, row in significant_changes.iterrows():
            # 前後のデータを取得
            time_before = row['timestamp'] - timedelta(minutes=5)
            time_after = row['timestamp'] + timedelta(minutes=5)
            
            data_before = df[(df['timestamp'] >= time_before) & (df['timestamp'] < row['timestamp'])]
            data_after = df[(df['timestamp'] > row['timestamp']) & (df['timestamp'] <= time_after)]
            
            # 前後の風向の平均
            if len(data_before) >= 3 and len(data_after) >= 3:
                before_mean = circmean(np.radians(data_before['wind_direction'])) * 180 / np.pi
                after_mean = circmean(np.radians(data_after['wind_direction'])) * 180 / np.pi
                
                # 変化量
                dir_change = self._calculate_angle_difference(after_mean, before_mean)
                
                # 信頼度の計算 (標準偏差が小さいほど高信頼度)
                before_std = circstd(np.radians(data_before['wind_direction'])) * 180 / np.pi
                after_std = circstd(np.radians(data_after['wind_direction'])) * 180 / np.pi
                
                consistency_score = 1.0 - min(1.0, (before_std + after_std) / 30.0)
                magnitude_score = min(1.0, abs(dir_change) / 20.0)
                
                confidence = (consistency_score * 0.6) + (magnitude_score * 0.4)
                
                # 風速の変化も考慮
                if 'wind_speed' in data_before.columns and 'wind_speed' in data_after.columns:
                    speed_before = data_before['wind_speed'].mean()
                    speed_after = data_after['wind_speed'].mean()
                    speed_change = speed_after - speed_before
                    speed_change_pct = abs(speed_change) / max(0.1, speed_before)
                    
                    # 風速変化も考慮して信頼度を調整
                    if speed_change_pct > 0.2:
                        confidence = confidence * 1.2
                
                # 結果を追加
                if confidence > self.params.get("confidence_threshold", 0.6):
                    shift_point = {
                        'timestamp': row['timestamp'],
                        'position': (row.get('latitude', None), row.get('longitude', None)),
                        'before_direction': before_mean,
                        'after_direction': after_mean,
                        'direction_change': dir_change,
                        'confidence': min(1.0, confidence),
                        'before_speed': data_before['wind_speed'].mean() if 'wind_speed' in data_before.columns else None,
                        'after_speed': data_after['wind_speed'].mean() if 'wind_speed' in data_after.columns else None,
                        'detection_method': 'statistical',
                        'shift_type': self._classify_shift_type(dir_change, 
                                                              data_before, 
                                                              data_after)
                    }
                    shift_points.append(shift_point)
        
        return shift_points
        
    def _calculate_angle_difference(self, angle1: float, angle2: float) -> float:
        """2つの角度の差を計算（-180〜180度の範囲で返す）"""
        if not isinstance(angle1, (int, float)) or not isinstance(angle2, (int, float)):
            return 0
        
        a1 = angle1 % 360
        a2 = angle2 % 360
        
        diff = ((a1 - a2 + 180) % 360) - 180
        
        return diff
        
    def _classify_shift_type(self, dir_change: float, 
                           data_before: pd.DataFrame, 
                           data_after: pd.DataFrame) -> str:
        """シフトタイプの分類"""
        # 持続的シフト vs 振動
        if len(data_after) < 5:
            return "UNKNOWN"
            
        # 変化後のデータの標準偏差
        after_std = circstd(np.radians(data_after['wind_direction'])) * 180 / np.pi
        
        # トレンド変化の検出
        if 'timestamp' in data_before.columns and 'wind_direction' in data_before.columns:
            try:
                # 前のデータで線形回帰
                x_before = [(t - data_before['timestamp'].min()).total_seconds() 
                           for t in data_before['timestamp']]
                y_before = [d for d in data_before['wind_direction']]
                
                if len(x_before) >= 3 and len(set(y_before)) > 1:
                    slope_before = np.polyfit(x_before, y_before, 1)[0]
                    
                    # 後のデータで線形回帰
                    x_after = [(t - data_after['timestamp'].min()).total_seconds() 
                              for t in data_after['timestamp']]
                    y_after = [d for d in data_after['wind_direction']]
                    
                    if len(x_after) >= 3 and len(set(y_after)) > 1:
                        slope_after = np.polyfit(x_after, y_after, 1)[0]
                        
                        # スロープの変化が大きければトレンド変化
                        if abs(slope_after - slope_before) > 0.1:
                            return "TREND"
            except:
                pass  # 回帰分析が失敗した場合は無視
        
        # 振動 vs 持続的シフト
        if after_std > 8.0:  # 変化後の変動が大きい
            return "OSCILLATION"
        elif abs(dir_change) > 10.0:  # 大きな変化
            return "PERSISTENT"
        else:
            return "PHASE"


class SignalProcessingDetector:
    """
    信号処理手法による風向シフト検出クラス
    """
    
    def __init__(self, params):
        """初期化"""
        self.params = params
        
    def detect(self, wind_data: pd.DataFrame) -> List[Dict[str, Any]]:
        """信号処理による検出実装"""
        if wind_data.empty or len(wind_data) < 20:  # より多くのデータポイントが必要
            return []
            
        # 時系列データとして処理
        df = wind_data.copy().sort_values('timestamp')
        
        # 角度データの前処理（連続性の確保）
        wind_dir_rad = np.radians(df['wind_direction'])
        sin_vals = np.sin(wind_dir_rad)
        cos_vals = np.cos(wind_dir_rad)
        
        # ノイズフィルタリング (Savitzky-Golay フィルタ)
        if len(df) >= 5:
            window_length = min(len(df) - (len(df) % 2 - 1), 15)  # 奇数になるよう調整
            if window_length >= 5:
                sin_smooth = signal.savgol_filter(sin_vals, window_length, 3)
                cos_smooth = signal.savgol_filter(cos_vals, window_length, 3)
                
                # 平滑化された角度を計算
                df['wind_dir_smooth'] = np.degrees(np.arctan2(sin_smooth, cos_smooth)) % 360
            else:
                # データが少ない場合は単純な移動平均
                df['wind_dir_smooth'] = df['wind_direction'].rolling(window=3, center=True).apply(
                    lambda x: circmean(np.radians(x)) * 180 / np.pi, raw=True
                ).fillna(df['wind_direction'])
        else:
            df['wind_dir_smooth'] = df['wind_direction']
        
        # 変化率（導関数）の計算
        df['timestamp_seconds'] = df['timestamp'].apply(lambda x: x.timestamp())
        df['time_diff'] = df['timestamp_seconds'].diff()
        df['dir_diff'] = df.apply(
            lambda row: self._calculate_angle_difference(row['wind_dir_smooth'], 
                                                      row['wind_dir_smooth'].shift(1)),
            axis=1
        )
        df['dir_change_rate'] = df['dir_diff'] / df['time_diff'].replace(0, 0.1)
        
        # 変化率の移動平均（異常値の影響を軽減）
        df['dir_change_rate_smooth'] = df['dir_change_rate'].rolling(
            window=5, center=True).mean().fillna(df['dir_change_rate'])
        
        # 変化率の急激な変動点を検出 (ピーク検出)
        if len(df) >= 10:  # ピーク検出に十分なデータポイント
            # ピーク検出のパラメータ
            prominence = self.params.get("peak_prominence", 0.2)  # ピークの顕著さ
            width = self.params.get("peak_width", 2)  # ピークの幅
            
            # 変化率の絶対値を使用
            abs_change_rate = np.abs(df['dir_change_rate_smooth'].fillna(0).values)
            
            # ピーク検出
            peaks, properties = signal.find_peaks(abs_change_rate, 
                                             prominence=prominence,
                                             width=width)
            
            # 検出されたピークをシフトポイントとして処理
            shift_points = []
            
            for peak_idx in peaks:
                if peak_idx > 0 and peak_idx < len(df) - 1:
                    peak_row = df.iloc[peak_idx]
                    
                    # 前後のデータウィンドウ
                    time_before = peak_row['timestamp'] - timedelta(minutes=3)
                    time_after = peak_row['timestamp'] + timedelta(minutes=3)
                    
                    data_before = df[(df['timestamp'] >= time_before) & 
                                   (df['timestamp'] < peak_row['timestamp'])]
                    data_after = df[(df['timestamp'] > peak_row['timestamp']) & 
                                  (df['timestamp'] <= time_after)]
                    
                    # 前後のウィンドウに十分なデータがある場合
                    if len(data_before) >= 3 and len(data_after) >= 3:
                        # 前後の風向平均
                        before_mean = circmean(np.radians(data_before['wind_dir_smooth'])) * 180 / np.pi
                        after_mean = circmean(np.radians(data_after['wind_dir_smooth'])) * 180 / np.pi
                        
                        # 変化量
                        dir_change = self._calculate_angle_difference(after_mean, before_mean)
                        
                        # 最小シフト角度より大きければ記録
                        min_shift_angle = self.params.get("min_shift_angle", 5.0)
                        if abs(dir_change) >= min_shift_angle:
                            # 信頼度の計算 (ピークの顕著さに基づく)
                            peak_prominences = properties["prominences"][list(peaks).index(peak_idx)]
                            confidence = min(1.0, peak_prominences / 2.0)
                            
                            # 結果を追加
                            if confidence > self.params.get("confidence_threshold", 0.6):
                                shift_point = {
                                    'timestamp': peak_row['timestamp'],
                                    'position': (peak_row.get('latitude', None), peak_row.get('longitude', None)),
                                    'before_direction': before_mean,
                                    'after_direction': after_mean,
                                    'direction_change': dir_change,
                                    'confidence': confidence,
                                    'before_speed': data_before['wind_speed'].mean() if 'wind_speed' in data_before.columns else None,
                                    'after_speed': data_after['wind_speed'].mean() if 'wind_speed' in data_after.columns else None,
                                    'detection_method': 'signal_processing',
                                    'shift_type': self._classify_shift_type(dir_change, 
                                                                          data_before, 
                                                                          data_after)
                                }
                                shift_points.append(shift_point)
            
            return shift_points
        
        return []
    
    def _calculate_angle_difference(self, angle1: float, angle2: float) -> float:
        """2つの角度の差を計算（-180〜180度の範囲で返す）"""
        if not isinstance(angle1, (int, float)) or not isinstance(angle2, (int, float)):
            return 0
        
        a1 = angle1 % 360
        a2 = angle2 % 360
        
        diff = ((a1 - a2 + 180) % 360) - 180
        
        return diff
        
    def _classify_shift_type(self, dir_change: float, 
                           data_before: pd.DataFrame, 
                           data_after: pd.DataFrame) -> str:
        """シフトタイプの分類"""
        if len(data_after) < 5 or len(data_before) < 5:
            return "UNKNOWN"
        
        # フーリエ変換でパターン分析
        if 'wind_dir_smooth' in data_before.columns and 'wind_dir_smooth' in data_after.columns:
            try:
                # 前のデータのスペクトル分析
                before_fft = np.abs(np.fft.rfft(data_before['wind_dir_smooth'].values))
                # 後のデータのスペクトル分析
                after_fft = np.abs(np.fft.rfft(data_after['wind_dir_smooth'].values))
                
                # スペクトルの変化
                if len(before_fft) > 1 and len(after_fft) > 1:
                    before_low_freq = before_fft[1:min(3, len(before_fft))].mean()
                    after_low_freq = after_fft[1:min(3, len(after_fft))].mean()
                    
                    # 低周波成分の変化が大きければ持続的シフト
                    if after_low_freq > before_low_freq * 2:
                        return "PERSISTENT"
                    
                    # 高周波成分の変化
                    before_high_freq = before_fft[min(3, len(before_fft)):].mean() if len(before_fft) > 3 else 0
                    after_high_freq = after_fft[min(3, len(after_fft)):].mean() if len(after_fft) > 3 else 0
                    
                    # 高周波成分の変化が大きければ振動
                    if after_high_freq > before_high_freq * 1.5:
                        return "OSCILLATION"
            except:
                pass  # FFT分析が失敗した場合は無視
                
        # 変化の大きさで分類
        if abs(dir_change) > 15.0:
            return "PERSISTENT"
        elif abs(dir_change) > 8.0:
            return "PHASE"
        else:
            return "OSCILLATION"


class MLShiftDetector:
    """
    機械学習手法による風向シフト検出クラス
    """
    
    def __init__(self, params):
        """初期化"""
        self.params = params
        
        # 特徴量エンジニアリングのパラメータ
        self.feature_params = {
            "window_sizes": [3, 5, 10],  # 異なるウィンドウサイズ
            "polynomial_degree": 2,  # 多項式特徴量の次数
        }
        
        # 簡易的な判別モデル (実際のプロジェクトでは機械学習モデルをロード)
        self.model = self._create_simple_model()
        
    def _create_simple_model(self):
        """
        簡易的な判別モデルを作成
        
        注: 実際のプロジェクトでは scikit-learn や TensorFlow などを使用した
        本格的な機械学習モデルを実装・または事前学習済みモデルをロード
        """
        class SimpleModel:
            def predict_proba(self, features):
                """特徴量から風向シフトの確率を予測する簡易モデル"""
                # 特徴量の重み付け (簡易的な線形モデル)
                weights = {
                    'dir_std_short': -0.2,  # 短期的な風向のばらつき
                    'dir_std_long': -0.1,   # 長期的な風向のばらつき
                    'dir_change_short': 0.3, # 短期的な風向変化
                    'dir_change_long': 0.2,  # 長期的な風向変化
                    'speed_change': 0.1,     # 風速変化
                    'trend_change': 0.4,     # トレンド変化
                }
                
                # 結果格納用
                probas = []
                
                for feature_set in features:
                    # 特徴量と重みの積和で確率を計算
                    prob = 0
                    for feat_name, weight in weights.items():
                        if feat_name in feature_set:
                            prob += feature_set[feat_name] * weight
                    
                    # シグモイド関数で0-1に正規化
                    prob = 1 / (1 + math.exp(-prob))
                    probas.append(prob)
                
                return np.array(probas)
                
        return SimpleModel()
        
    def detect(self, wind_data: pd.DataFrame) -> List[Dict[str, Any]]:
        """機械学習モデルを使用した検出実装"""
        if wind_data.empty or len(wind_data) < 15:  # 十分なデータポイントが必要
            return []
            
        # 時系列データとして処理
        df = wind_data.copy().sort_values('timestamp')
        
        # 特徴量の抽出
        features = self._extract_features(df)
        
        # 候補点の選定 (時間軸上でスライディングウィンドウを移動)
        candidate_points = []
        confidence_threshold = self.params.get("confidence_threshold", 0.6)
        
        for i in range(5, len(df) - 5):  # 両端のデータは除外
            current_point = df.iloc[i]
            
            # 前後のデータウィンドウ
            before_data = df.iloc[i-5:i]
            after_data = df.iloc[i+1:i+6]
            
            if len(before_data) >= 3 and len(after_data) >= 3:
                # 特徴量の計算
                point_features = self._compute_point_features(current_point, before_data, after_data)
                
                # モデルによる予測
                shift_probability = self.model.predict_proba([point_features])[0]
                
                # 閾値を超える確率の場合は候補点として記録
                if shift_probability > confidence_threshold:
                    candidate_points.append({
                        'index': i,
                        'timestamp': current_point['timestamp'],
                        'probability': shift_probability,
                        'features': point_features
                    })
        
        # 近接した候補点をマージ
        merged_candidates = self._merge_close_candidates(candidate_points, df)
        
        # シフトポイントの作成
        shift_points = []
        
        for candidate in merged_candidates:
            idx = candidate['index']
            if idx > 0 and idx < len(df) - 1:
                # 選定された点の情報
                center_row = df.iloc[idx]
                
                # 前後のデータウィンドウ
                time_before = center_row['timestamp'] - timedelta(minutes=3)
                time_after = center_row['timestamp'] + timedelta(minutes=3)
                
                data_before = df[(df['timestamp'] >= time_before) & 
                               (df['timestamp'] < center_row['timestamp'])]
                data_after = df[(df['timestamp'] > center_row['timestamp']) & 
                              (df['timestamp'] <= time_after)]
                
                # 前後の風向平均
                if len(data_before) >= 3 and len(data_after) >= 3:
                    before_mean = circmean(np.radians(data_before['wind_direction'])) * 180 / np.pi
                    after_mean = circmean(np.radians(data_after['wind_direction'])) * 180 / np.pi
                    
                    # 変化量
                    dir_change = self._calculate_angle_difference(after_mean, before_mean)
                    
                    # 最小シフト角度より大きければ記録
                    min_shift_angle = self.params.get("min_shift_angle", 5.0)
                    if abs(dir_change) >= min_shift_angle:
                        # 結果を追加
                        shift_point = {
                            'timestamp': center_row['timestamp'],
                            'position': (center_row.get('latitude', None), center_row.get('longitude', None)),
                            'before_direction': before_mean,
                            'after_direction': after_mean,
                            'direction_change': dir_change,
                            'confidence': candidate['probability'],
                            'before_speed': data_before['wind_speed'].mean() if 'wind_speed' in data_before.columns else None,
                            'after_speed': data_after['wind_speed'].mean() if 'wind_speed' in data_after.columns else None,
                            'detection_method': 'machine_learning',
                            'shift_type': self._classify_shift_type(dir_change, 
                                                                  data_before, 
                                                                  data_after,
                                                                  candidate['features'])
                        }
                        shift_points.append(shift_point)
        
        return shift_points
        
    def _extract_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """特徴量の抽出"""
        features_df = df.copy()
        
        # 異なるウィンドウサイズでの統計量
        for window in self.feature_params["window_sizes"]:
            # 風向の移動平均と標準偏差
            features_df[f'wind_dir_ma_{window}'] = features_df['wind_direction'].rolling(
                window=window, center=True).apply(
                    lambda x: circmean(np.radians(x)) * 180 / np.pi
                )
            
            features_df[f'wind_dir_std_{window}'] = features_df['wind_direction'].rolling(
                window=window, center=True).apply(
                    lambda x: circstd(np.radians(x)) * 180 / np.pi
                )
            
            # 風速の統計量 (存在する場合)
            if 'wind_speed' in features_df.columns:
                features_df[f'wind_speed_ma_{window}'] = features_df['wind_speed'].rolling(
                    window=window, center=True).mean()
                features_df[f'wind_speed_std_{window}'] = features_df['wind_speed'].rolling(
                    window=window, center=True).std()
        
        # 時間差分特徴量
        features_df['timestamp_seconds'] = features_df['timestamp'].apply(lambda x: x.timestamp())
        features_df['time_diff'] = features_df['timestamp_seconds'].diff()
        
        # 角度変化率
        for window in self.feature_params["window_sizes"]:
            col = f'wind_dir_ma_{window}'
            if col in features_df.columns:
                features_df[f'dir_change_{window}'] = features_df.apply(
                    lambda row: self._calculate_angle_difference(
                        row[col], features_df[col].shift(window//2)),
                    axis=1
                )
                features_df[f'dir_change_rate_{window}'] = features_df[f'dir_change_{window}'] / (
                    features_df['time_diff'] * window/2).replace(0, 0.1)
        
        return features_df
        
    def _compute_point_features(self, current_point, before_data, after_data) -> Dict[str, float]:
        """個別の点に対する特徴量を計算"""
        features = {}
        
        # 前後の風向の統計量
        before_mean = circmean(np.radians(before_data['wind_direction'])) * 180 / np.pi
        after_mean = circmean(np.radians(after_data['wind_direction'])) * 180 / np.pi
        before_std = circstd(np.radians(before_data['wind_direction'])) * 180 / np.pi
        after_std = circstd(np.radians(after_data['wind_direction'])) * 180 / np.pi
        
        # 変化量特徴量
        dir_change = self._calculate_angle_difference(after_mean, before_mean)
        features['dir_change_short'] = abs(dir_change) / 20.0  # 正規化
        
        # 標準偏差特徴量
        features['dir_std_short'] = (before_std + after_std) / 30.0  # 正規化
        
        # 風速特徴量 (存在する場合)
        if 'wind_speed' in before_data.columns and 'wind_speed' in after_data.columns:
            before_speed = before_data['wind_speed'].mean()
            after_speed = after_data['wind_speed'].mean()
            speed_change = (after_speed - before_speed) / max(0.1, before_speed)
            features['speed_change'] = min(1.0, abs(speed_change))
        else:
            features['speed_change'] = 0.0
        
        # トレンド特徴量
        if len(before_data) >= 3 and len(after_data) >= 3:
            try:
                # 前のデータでの線形トレンド
                x_before = [(t - before_data['timestamp'].min()).total_seconds() 
                           for t in before_data['timestamp']]
                y_before = [d for d in before_data['wind_direction']]
                
                slope_before = np.polyfit(x_before, y_before, 1)[0] if len(set(y_before)) > 1 else 0
                
                # 後のデータでの線形トレンド
                x_after = [(t - after_data['timestamp'].min()).total_seconds() 
                          for t in after_data['timestamp']]
                y_after = [d for d in after_data['wind_direction']]
                
                slope_after = np.polyfit(x_after, y_after, 1)[0] if len(set(y_after)) > 1 else 0
                
                # トレンド変化特徴量
                trend_change = abs(slope_after - slope_before) * 10  # スケーリング
                features['trend_change'] = min(1.0, trend_change)
            except:
                features['trend_change'] = 0.0
        else:
            features['trend_change'] = 0.0
        
        # 長期的な特徴量 (可能であれば)
        if hasattr(current_point, 'wind_dir_std_10'):
            features['dir_std_long'] = current_point['wind_dir_std_10'] / 20.0
        else:
            features['dir_std_long'] = features['dir_std_short']
            
        if hasattr(current_point, 'dir_change_10'):
            features['dir_change_long'] = abs(current_point['dir_change_10']) / 30.0
        else:
            features['dir_change_long'] = features['dir_change_short']
        
        return features
        
    def _merge_close_candidates(self, candidates: List[Dict[str, Any]], 
                              df: pd.DataFrame) -> List[Dict[str, Any]]:
        """近接した候補点をマージ"""
        if not candidates:
            return []
            
        # タイムスタンプでソート
        sorted_candidates = sorted(candidates, key=lambda x: x['timestamp'])
        
        merged = []
        current_group = [sorted_candidates[0]]
        
        for i in range(1, len(sorted_candidates)):
            current = sorted_candidates[i]
            previous = current_group[-1]
            
            # 近接判定 (60秒以内なら同一グループとする)
            time_diff = (current['timestamp'] - previous['timestamp']).total_seconds()
            
            if time_diff <= 60:
                # 同一グループに追加
                current_group.append(current)
            else:
                # 前のグループから最良の候補を選定
                best_candidate = max(current_group, key=lambda x: x['probability'])
                merged.append(best_candidate)
                
                # 新しいグループを開始
                current_group = [current]
        
        # 最後のグループを処理
        if current_group:
            best_candidate = max(current_group, key=lambda x: x['probability'])
            merged.append(best_candidate)
        
        return merged
        
    def _calculate_angle_difference(self, angle1: float, angle2: float) -> float:
        """2つの角度の差を計算（-180〜180度の範囲で返す）"""
        if not isinstance(angle1, (int, float)) or not isinstance(angle2, (int, float)):
            return 0
        
        a1 = angle1 % 360
        a2 = angle2 % 360
        
        diff = ((a1 - a2 + 180) % 360) - 180
        
        return diff
        
    def _classify_shift_type(self, dir_change: float, 
                           data_before: pd.DataFrame, 
                           data_after: pd.DataFrame,
                           features: Dict[str, float]) -> str:
        """機械学習特徴量を使ったシフトタイプの分類"""
        # 特徴量を使った分類
        if features.get('trend_change', 0) > 0.6:
            return "TREND"
        elif features.get('dir_std_short', 0) > 0.5 or features.get('dir_std_long', 0) > 0.6:
            return "OSCILLATION"
        elif abs(dir_change) > 12.0:
            return "PERSISTENT"
        else:
            return "PHASE"


class AdaptiveShiftDetector:
    """
    適応型シフト検出器
    
    データの特性に基づいて最適な検出戦略を選択
    """
    
    def __init__(self, params):
        """初期化"""
        self.params = params
        
        # 各検出器のインスタンス化
        self.statistical_detector = StatisticalShiftDetector(params)
        self.signal_detector = SignalProcessingDetector(params)
        self.ml_detector = MLShiftDetector(params)
        
    def detect(self, wind_data: pd.DataFrame) -> List[Dict[str, Any]]:
        """最適な検出戦略を選択して実行"""
        if wind_data.empty or len(wind_data) < 10:
            return []
            
        # データの特性分析
        data_characteristics = self._analyze_data_characteristics(wind_data)
        
        # 戦略選択
        strategy = self._select_strategy(data_characteristics)
        
        # 選択した戦略で検出
        if strategy == "statistical":
            results = self.statistical_detector.detect(wind_data)
        elif strategy == "signal_processing":
            results = self.signal_detector.detect(wind_data)
        elif strategy == "machine_learning":
            results = self.ml_detector.detect(wind_data)
        elif strategy == "ensemble":
            # 全ての手法を使用して結果をマージ
            results = self._ensemble_detect(wind_data)
        else:
            # デフォルトは統計的手法
            results = self.statistical_detector.detect(wind_data)
        
        return results
        
    def _analyze_data_characteristics(self, wind_data: pd.DataFrame) -> Dict[str, Any]:
        """データの特性を分析"""
        characteristics = {}
        
        # サンプルサイズ
        characteristics["sample_size"] = len(wind_data)
        
        # サンプリング頻度
        if len(wind_data) >= 2:
            time_diffs = []
            timestamps = sorted(wind_data['timestamp'])
            for i in range(1, len(timestamps)):
                diff = (timestamps[i] - timestamps[i-1]).total_seconds()
                if diff > 0:  # 有効な差分のみ
                    time_diffs.append(diff)
            
            if time_diffs:
                characteristics["sampling_interval"] = np.median(time_diffs)
                characteristics["regular_sampling"] = np.std(time_diffs) < np.mean(time_diffs) * 0.5
            else:
                characteristics["sampling_interval"] = 1.0
                characteristics["regular_sampling"] = False
        else:
            characteristics["sampling_interval"] = 1.0
            characteristics["regular_sampling"] = False
        
        # 風向のばらつき
        if 'wind_direction' in wind_data.columns and len(wind_data) > 0:
            characteristics["direction_std"] = circstd(np.radians(wind_data['wind_direction'])) * 180 / np.pi
            
            # 風向の自己相関
            if len(wind_data) > 20:
                try:
                    # 円周データなので sin/cos 成分で自己相関を計算
                    sin_vals = np.sin(np.radians(wind_data['wind_direction']))
                    acf_sin = np.correlate(sin_vals - np.mean(sin_vals), 
                                        sin_vals - np.mean(sin_vals), mode='same')
                    acf_sin = acf_sin[len(acf_sin)//2:] / acf_sin[len(acf_sin)//2]
                    
                    # 自己相関の減衰速度
                    if len(acf_sin) > 5:
                        characteristics["autocorrelation_decay"] = 1.0 - acf_sin[5]
                    else:
                        characteristics["autocorrelation_decay"] = 0.5
                except:
                    characteristics["autocorrelation_decay"] = 0.5
            else:
                characteristics["autocorrelation_decay"] = 0.5
        else:
            characteristics["direction_std"] = 0.0
            characteristics["autocorrelation_decay"] = 0.5
        
        return characteristics
        
    def _select_strategy(self, characteristics: Dict[str, Any]) -> str:
        """データ特性に基づく最適戦略の選択"""
        # サンプルサイズに基づく選択
        sample_size = characteristics.get("sample_size", 0)
        
        if sample_size < 15:
            return "statistical"  # 少数サンプルでは統計的手法
        elif sample_size < 30:
            # 中程度のサンプルサイズ
            if characteristics.get("direction_std", 0) > 15.0:
                # ばらつきが大きい場合は信号処理
                return "signal_processing"
            else:
                # ばらつきが小さい場合は統計
                return "statistical"
        else:
            # 大きなサンプルサイズ
            if characteristics.get("regular_sampling", False):
                # 規則的なサンプリングでは信号処理が有効
                return "signal_processing"
            elif characteristics.get("autocorrelation_decay", 0.5) > 0.7:
                # 自己相関の減衰が速い（ノイズが多い）場合は機械学習
                return "machine_learning"
            elif sample_size > 50:
                # 十分な量のデータがあれば全手法を使用
                return "ensemble"
            else:
                # デフォルトは信号処理
                return "signal_processing"
                
    def _ensemble_detect(self, wind_data: pd.DataFrame) -> List[Dict[str, Any]]:
        """全検出器を使用して結果を統合"""
        # 各検出器の結果を取得
        statistical_results = self.statistical_detector.detect(wind_data)
        signal_results = self.signal_detector.detect(wind_data)
        ml_results = self.ml_detector.detect(wind_data)
        
        # 全結果を結合
        all_results = statistical_results + signal_results + ml_results
        
        # 結果を時間でソート
        all_results.sort(key=lambda x: x['timestamp'])
        
        # 近接した検出結果をマージ
        merged_results = []
        
        if not all_results:
            return []
            
        current_group = [all_results[0]]
        
        for i in range(1, len(all_results)):
            current = all_results[i]
            previous = current_group[-1]
            
            # 60秒以内なら同一シフトと見なす
            time_diff = (current['timestamp'] - previous['timestamp']).total_seconds()
            
            if time_diff <= 60:
                # 同一グループに追加
                current_group.append(current)
            else:
                # 前のグループを処理
                merged_result = self._merge_shift_group(current_group)
                merged_results.append(merged_result)
                
                # 新しいグループを開始
                current_group = [current]
        
        # 最後のグループを処理
        if current_group:
            merged_result = self._merge_shift_group(current_group)
            merged_results.append(merged_result)
        
        return merged_results
        
    def _merge_shift_group(self, shift_group: List[Dict[str, Any]]) -> Dict[str, Any]:
        """近接したシフト検出結果のマージ"""
        if not shift_group:
            return {}
            
        # 信頼度による重み付け
        total_weight = sum(s['confidence'] for s in shift_group)
        
        if total_weight == 0:
            # 重みの合計がゼロの場合は単純平均
            weights = [1.0/len(shift_group)] * len(shift_group)
        else:
            weights = [s['confidence']/total_weight for s in shift_group]
        
        # 重み付き平均の計算
        timestamps = [s['timestamp'] for s in shift_group]
        mean_timestamp = min(timestamps) + (max(timestamps) - min(timestamps)) / 2
        
        # 風向の重み付き平均 (円環統計)
        before_dirs = [s['before_direction'] for s in shift_group]
        before_dir_rads = np.radians(before_dirs)
        mean_before_dir = np.degrees(np.arctan2(
            np.sum(np.sin(before_dir_rads) * weights),
            np.sum(np.cos(before_dir_rads) * weights)
        )) % 360
        
        after_dirs = [s['after_direction'] for s in shift_group]
        after_dir_rads = np.radians(after_dirs)
        mean_after_dir = np.degrees(np.arctan2(
            np.sum(np.sin(after_dir_rads) * weights),
            np.sum(np.cos(after_dir_rads) * weights)
        )) % 360
        
        # 風速の重み付き平均
        before_speeds = [s.get('before_speed', 0) for s in shift_group]
        mean_before_speed = np.sum(np.array(before_speeds) * weights)
        
        after_speeds = [s.get('after_speed', 0) for s in shift_group]
        mean_after_speed = np.sum(np.array(after_speeds) * weights)
        
        # 位置の重み付き平均
        positions = [s.get('position', (None, None)) for s in shift_group]
        valid_positions = [(lat, lon) for lat, lon in positions if lat is not None and lon is not None]
        
        if valid_positions:
            mean_lat = np.sum([p[0] for p in valid_positions]) / len(valid_positions)
            mean_lon = np.sum([p[1] for p in valid_positions]) / len(valid_positions)
            mean_position = (mean_lat, mean_lon)
        else:
            mean_position = (None, None)
        
        # 信頼度は最大値を採用
        max_confidence = max(s['confidence'] for s in shift_group)
        
        # 方向変化の計算
        dir_change = self._calculate_angle_difference(mean_after_dir, mean_before_dir)
        
        # シフトタイプは多数決
        shift_types = [s['shift_type'] for s in shift_group]
        unique_types = set(shift_types)
        type_counts = {t: shift_types.count(t) for t in unique_types}
        majority_type = max(type_counts.items(), key=lambda x: x[1])[0]
        
        # 最も信頼度が高い検出方法を記録
        best_method = max(shift_group, key=lambda x: x['confidence'])['detection_method']
        
        return {
            'timestamp': mean_timestamp,
            'position': mean_position,
            'before_direction': mean_before_dir,
            'after_direction': mean_after_dir,
            'direction_change': dir_change,
            'confidence': max_confidence,
            'before_speed': mean_before_speed,
            'after_speed': mean_after_speed,
            'detection_method': f"ensemble:{best_method}",
            'shift_type': majority_type,
            'ensemble_size': len(shift_group),
            'detection_methods': [s['detection_method'] for s in shift_group]
        }
        
    def _calculate_angle_difference(self, angle1: float, angle2: float) -> float:
        """2つの角度の差を計算（-180〜180度の範囲で返す）"""
        if not isinstance(angle1, (int, float)) or not isinstance(angle2, (int, float)):
            return 0
        
        a1 = angle1 % 360
        a2 = angle2 % 360
        
        diff = ((a1 - a2 + 180) % 360) - 180
        
        return diff


class WindShiftDetector:
    """
    風向シフト検出クラス
    
    GPSデータと風データから風向シフトを高精度に検出するアルゴリズムを提供します。
    複数の検出方法をサポートし、ノイズに強い分析を実現します。
    """
    
    SHIFT_TYPES = {
        "OSCILLATION": 0,  # 振動（短期的な変動）
        "PERSISTENT": 1,   # 持続的シフト（一定方向への変化）
        "TREND": 2,        # トレンド変化（徐々に変化）
        "PHASE": 3,        # 位相変化（パターンの変化）
        "UNKNOWN": 99      # 未分類
    }
    
    def __init__(self, detection_method="adaptive", window_size=None, sensitivity=0.7, **kwargs):
        """
        初期化
        
        Parameters
        ----------
        detection_method : str, optional
            検出方法 ("statistical", "signal_processing", "machine_learning", "adaptive")
        window_size : int, optional
            分析時間窓のサイズ (秒), by default None (自動決定)
        sensitivity : float, optional
            検出感度 (0.0-1.0), by default 0.7
        **kwargs : dict
            追加のパラメータ
        """
        self.method = detection_method
        self.window_size = window_size
        self.sensitivity = max(0.1, min(1.0, sensitivity))
        
        # 追加パラメータ
        self.params = {
            "min_shift_angle": kwargs.get("min_shift_angle", 5.0),  # 最小シフト角度
            "confidence_threshold": kwargs.get("confidence_threshold", 0.6),  # 信頼度閾値
            "noise_filter": kwargs.get("noise_filter", "kalman"),  # ノイズフィルタ
            "trend_detection": kwargs.get("trend_detection", True),  # トレンド検出
            "use_location_context": kwargs.get("use_location_context", False),  # 位置情報の活用
        }
        
        # 感度による閾値調整
        self._adjust_thresholds_by_sensitivity()
        
        # 検出器の初期化
        self._init_detector()
        
        # 結果のキャッシュ
        self._detection_cache = {}
    
    def _adjust_thresholds_by_sensitivity(self):
        """感度に基づく閾値の調整"""
        # 感度が高いほど小さなシフトも検出
        self.params["min_shift_angle"] = max(3.0, 10.0 - self.sensitivity * 7.0)
        
        # 感度が高いほど信頼度閾値を下げる
        self.params["confidence_threshold"] = max(0.4, 0.9 - self.sensitivity * 0.3)
        
        # 時間窓の自動調整
        if self.window_size is None:
            # 感度が高いほど狭い窓で詳細に検出
            self.window_size = int(300 - self.sensitivity * 240)  # 60〜300秒
    
    def _init_detector(self):
        """検出器の初期化"""
        # ウィンドウサイズのパラメータ設定
        if self.window_size is not None:
            self.params["window_size"] = self.window_size
        
        if self.method == "statistical":
            self._detector = StatisticalShiftDetector(self.params)
        elif self.method == "signal_processing":
            self._detector = SignalProcessingDetector(self.params)
        elif self.method == "machine_learning":
            self._detector = MLShiftDetector(self.params)
        elif self.method == "adaptive":
            self._detector = AdaptiveShiftDetector(self.params)
        else:
            raise ValueError(f"Unknown detection method: {self.method}")
    
    def detect_shifts(self, wind_data, track_data=None, course_info=None):
        """
        風向シフトを検出
        
        Parameters
        ----------
        wind_data : DataFrame or array-like
            風向・風速データ
        track_data : DataFrame or array-like, optional
            GPS軌跡データ, by default None
        course_info : dict, optional
            コース情報, by default None
            
        Returns
        -------
        list
            検出されたシフト情報のリスト
        """
        # キャッシュキーの作成
        cache_key = self._create_cache_key(wind_data)
        
        # キャッシュに結果があればそれを返す
        if cache_key in self._detection_cache:
            return self._detection_cache[cache_key]
        
        # データフレームに変換
        df = self._ensure_dataframe(wind_data)
        
        # 必要なカラムが揃っているか確認
        if df.empty or 'wind_direction' not in df.columns:
            return []
        
        # GPSトラックデータがあれば結合
        if track_data is not None:
            track_df = self._ensure_dataframe(track_data)
            if not track_df.empty and 'timestamp' in track_df.columns:
                # 時間的に最も近いGPSデータを探す
                df = self._join_nearest_track_data(df, track_df)
        
        # 風向シフトの検出
        shift_results = self._detector.detect(df)
        
        # コース情報に基づく位置的な文脈を付与
        if course_info is not None and self.params["use_location_context"]:
            shift_results = self._add_course_context(shift_results, course_info)
        
        # シフトの重要度を評価
        shift_results = [
            {**shift, 'significance': self.evaluate_shift_significance(shift)}
            for shift in shift_results
        ]
        
        # 重要度でソート
        shift_results.sort(key=lambda x: x.get('significance', 0), reverse=True)
        
        # 結果をキャッシュ
        self._detection_cache[cache_key] = shift_results
        
        return shift_results
    
    def classify_shift(self, shift_data):
        """
        シフトタイプの分類
        
        Parameters
        ----------
        shift_data : dict
            シフト情報
            
        Returns
        -------
        str
            シフトタイプ（"OSCILLATION", "PERSISTENT", "TREND", "PHASE", "UNKNOWN"）
        """
        if not shift_data or 'shift_type' not in shift_data:
            return "UNKNOWN"
            
        return shift_data['shift_type']
    
    def evaluate_shift_significance(self, shift_data, context=None):
        """
        シフトの重要度評価
        
        Parameters
        ----------
        shift_data : dict
            シフト情報
        context : dict, optional
            評価のための追加コンテキスト, by default None
            
        Returns
        -------
        float
            重要度スコア (0-1)
        """
        if not shift_data:
            return 0.0
            
        # 基本スコア（信頼度に基づく）
        base_score = shift_data.get('confidence', 0.0)
        
        # 変化量による補正
        dir_change = abs(shift_data.get('direction_change', 0.0))
        magnitude_score = min(1.0, dir_change / 30.0)
        
        # シフトタイプによる重み付け
        type_weights = {
            "PERSISTENT": 1.0,  # 持続的シフトは重要
            "TREND": 0.9,       # トレンド変化もかなり重要
            "PHASE": 0.7,       # 位相変化は中程度
            "OSCILLATION": 0.5, # 振動は重要度低め
            "UNKNOWN": 0.3      # 未分類は最も低い
        }
        
        type_weight = type_weights.get(shift_data.get('shift_type', "UNKNOWN"), 0.3)
        
        # 風速変化による補正
        speed_score = 0.0
        if 'before_speed' in shift_data and 'after_speed' in shift_data:
            before_speed = shift_data.get('before_speed', 0.0)
            after_speed = shift_data.get('after_speed', 0.0)
            
            if before_speed > 0:
                speed_change_pct = abs(after_speed - before_speed) / before_speed
                speed_score = min(0.3, speed_change_pct)
        
        # コンテキストによる補正
        context_score = 0.0
        if context is not None:
            # コース上の戦略的ポイントに近いシフトを重視
            if 'strategic_points' in context and 'position' in shift_data:
                lat, lon = shift_data['position']
                if lat is not None and lon is not None:
                    min_distance = float('inf')
                    for point in context['strategic_points']:
                        point_lat, point_lon = point['position']
                        distance = self._calculate_distance(lat, lon, point_lat, point_lon)
                        min_distance = min(min_distance, distance)
                    
                    # 戦略ポイントに近いほど重要度が高い（500m以内で効果）
                    if min_distance < 500:
                        context_score += 0.3 * (1 - min_distance / 500)
        
        # 総合スコアの計算
        significance = (base_score * 0.3) + (magnitude_score * 0.3) + (type_weight * 0.2) + (speed_score * 0.1) + (context_score * 0.1)
        
        # 0-1の範囲に正規化
        return min(1.0, max(0.0, significance))
    
    def analyze_shift_patterns(self, shifts, time_period=None):
        """
        シフトパターンの分析
        
        Parameters
        ----------
        shifts : list
            シフト情報のリスト
        time_period : tuple, optional
            分析期間 (開始時刻, 終了時刻), by default None
            
        Returns
        -------
        dict
            パターン分析結果
        """
        if not shifts:
            return {
                "count": 0,
                "pattern_type": "none",
                "avg_interval": None,
                "dominant_direction": None,
                "has_oscillation": False,
                "has_persistent": False
            }
        
        # 時間でフィルタリング
        if time_period is not None:
            start_time, end_time = time_period
            filtered_shifts = [s for s in shifts 
                            if start_time <= s['timestamp'] <= end_time]
        else:
            filtered_shifts = shifts
        
        # シフト数が少なすぎる場合
        if len(filtered_shifts) < 2:
            if len(filtered_shifts) == 1:
                shift_type = filtered_shifts[0].get('shift_type', 'UNKNOWN')
                return {
                    "count": 1,
                    "pattern_type": "single_shift",
                    "avg_interval": None,
                    "dominant_direction": filtered_shifts[0].get('direction_change', 0),
                    "has_oscillation": shift_type == "OSCILLATION",
                    "has_persistent": shift_type == "PERSISTENT"
                }
            else:
                return {
                    "count": 0,
                    "pattern_type": "none",
                    "avg_interval": None,
                    "dominant_direction": None,
                    "has_oscillation": False,
                    "has_persistent": False
                }
        
        # 時間順にソート
        sorted_shifts = sorted(filtered_shifts, key=lambda x: x['timestamp'])
        
        # 時間間隔の分析
        intervals = []
        for i in range(1, len(sorted_shifts)):
            interval = (sorted_shifts[i]['timestamp'] - sorted_shifts[i-1]['timestamp']).total_seconds()
            intervals.append(interval)
        
        avg_interval = sum(intervals) / len(intervals) if intervals else None
        std_interval = np.std(intervals) if len(intervals) >= 2 else float('inf')
        
        # 周期性の分析
        is_periodic = False
        if std_interval < avg_interval * 0.4:  # 間隔のばらつきが小さい
            is_periodic = True
        
        # 方向性の分析
        directions = [s.get('direction_change', 0) for s in sorted_shifts]
        
        # 振動判定（正負の繰り返し）
        sign_changes = 0
        for i in range(1, len(directions)):
            if (directions[i] > 0 and directions[i-1] < 0) or (directions[i] < 0 and directions[i-1] > 0):
                sign_changes += 1
        
        is_oscillating = sign_changes >= len(directions) * 0.4
        
        # 主方向の判定
        positive_shifts = sum(1 for d in directions if d > 0)
        negative_shifts = sum(1 for d in directions if d < 0)
        
        if positive_shifts > negative_shifts * 2:
            dominant_dir = "positive"  # 右シフト優勢
        elif negative_shifts > positive_shifts * 2:
            dominant_dir = "negative"  # 左シフト優勢
        else:
            dominant_dir = "mixed"     # 混合
        
        # シフトタイプの集計
        type_counts = {}
        for shift in sorted_shifts:
            shift_type = shift.get('shift_type', 'UNKNOWN')
            type_counts[shift_type] = type_counts.get(shift_type, 0) + 1
        
        # 最も多いタイプ
        dominant_type = max(type_counts.items(), key=lambda x: x[1])[0] if type_counts else 'UNKNOWN'
        
        # パターンタイプの総合判定
        pattern_type = "mixed"
        if is_periodic and is_oscillating:
            pattern_type = "regular_oscillation"
        elif is_periodic and not is_oscillating:
            pattern_type = "regular_shifts"
        elif is_oscillating:
            pattern_type = "irregular_oscillation"
        elif dominant_dir != "mixed":
            pattern_type = "directional_trend"
        
        # 結果を返す
        return {
            "count": len(sorted_shifts),
            "pattern_type": pattern_type,
            "avg_interval": avg_interval,
            "interval_std": std_interval,
            "is_periodic": is_periodic,
            "is_oscillating": is_oscillating,
            "dominant_direction": dominant_dir,
            "dominant_shift_type": dominant_type,
            "type_distribution": type_counts,
            "has_oscillation": "OSCILLATION" in type_counts,
            "has_persistent": "PERSISTENT" in type_counts,
            "has_trend": "TREND" in type_counts
        }
    
    def get_detection_params(self):
        """
        現在の検出パラメータを取得
        
        Returns
        -------
        dict
            パラメータの辞書
        """
        return {
            "method": self.method,
            "window_size": self.window_size,
            "sensitivity": self.sensitivity,
            **self.params
        }
    
    def set_detection_params(self, **params):
        """
        検出パラメータを設定
        
        Parameters
        ----------
        **params : dict
            設定するパラメータ
            
        Returns
        -------
        bool
            設定が成功したかどうか
        """
        # パラメータの更新
        if "method" in params:
            self.method = params["method"]
        
        if "window_size" in params:
            self.window_size = params["window_size"]
        
        if "sensitivity" in params:
            self.sensitivity = max(0.1, min(1.0, params["sensitivity"]))
            self._adjust_thresholds_by_sensitivity()
        
        # その他のパラメータ
        for key, value in params.items():
            if key in self.params:
                self.params[key] = value
        
        # 検出器の再初期化
        self._init_detector()
        
        # キャッシュのクリア
        self._detection_cache = {}
        
        return True
    
    def _ensure_dataframe(self, data):
        """データをPandasデータフレームに変換"""
        if isinstance(data, pd.DataFrame):
            return data
        elif hasattr(data, 'to_dataframe'):
            return data.to_dataframe()
        elif isinstance(data, dict):
            return pd.DataFrame(data)
        elif isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            return pd.DataFrame(data)
        else:
            warnings.warn("Unrecognized data format. Empty DataFrame returned.")
            return pd.DataFrame()
    
    def _create_cache_key(self, data):
        """キャッシュキーの作成"""
        if isinstance(data, pd.DataFrame):
            # データフレームの場合はサイズとタイムスタンプ範囲を使用
            if 'timestamp' in data.columns and not data.empty:
                min_time = data['timestamp'].min()
                max_time = data['timestamp'].max()
                return f"{self.method}_{len(data)}_{min_time}_{max_time}"
            else:
                return f"{self.method}_{len(data)}"
        else:
            # その他の場合はオブジェクトのIDを使用
            return f"{self.method}_{id(data)}"
    
    def _join_nearest_track_data(self, wind_df, track_df):
        """風データに最も近いGPSトラックデータを結合"""
        result_df = wind_df.copy()
        
        # 必要なカラムを確認
        if 'timestamp' not in wind_df.columns or 'timestamp' not in track_df.columns:
            return result_df
            
        # トラックデータからの追加カラム
        track_columns = ['latitude', 'longitude', 'course', 'speed']
        available_columns = [col for col in track_columns if col in track_df.columns]
        
        if not available_columns:
            return result_df
        
        # 各風データポイントに対して最も近いトラックデータを見つける
        for idx, row in result_df.iterrows():
            wind_time = row['timestamp']
            
            # 時間差の計算
            track_df['time_diff'] = abs((track_df['timestamp'] - wind_time).dt.total_seconds())
            
            # 最も近いデータポイント
            closest_idx = track_df['time_diff'].idxmin()
            closest_row = track_df.loc[closest_idx]
            
            # 近接性の確認 (5分以内)
            if closest_row['time_diff'] <= 300:
                for col in available_columns:
                    result_df.at[idx, col] = closest_row[col]
        
        return result_df
    
    def _add_course_context(self, shifts, course_info):
        """コース情報に基づく文脈の追加"""
        if not shifts or not course_info:
            return shifts
        
        enhanced_shifts = []
        
        # コース情報から重要ポイントを抽出
        strategic_points = course_info.get('strategic_points', [])
        marks = course_info.get('marks', [])
        
        # 全ての重要ポイント（マークを含む）
        all_points = strategic_points + marks
        
        for shift in shifts:
            shift_copy = shift.copy()
            
            # 位置情報があれば最も近いポイントを探す
            if 'position' in shift and shift['position'][0] is not None:
                lat, lon = shift['position']
                
                nearest_point = None
                min_distance = float('inf')
                
                for point in all_points:
                    if 'position' in point:
                        point_lat, point_lon = point['position']
                        distance = self._calculate_distance(lat, lon, point_lat, point_lon)
                        
                        if distance < min_distance:
                            min_distance = distance
                            nearest_point = point
                
                # 近いポイントがあれば情報を追加 (500m以内)
                if nearest_point and min_distance < 500:
                    shift_copy['nearest_point'] = {
                        'name': nearest_point.get('name', 'Unknown'),
                        'type': nearest_point.get('type', 'point'),
                        'distance': min_distance
                    }
            
            enhanced_shifts.append(shift_copy)
        
        return enhanced_shifts
    
    def _calculate_distance(self, lat1, lon1, lat2, lon2):
        """2点間の距離を計算 (ヒュベニの公式、単位: メートル)"""
        # 地球半径（メートル）
        earth_radius = 6371000
        
        # 緯度経度をラジアンに変換
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # 緯度と経度の差
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        # ヒュベニの公式
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = earth_radius * c
        
        return distance
