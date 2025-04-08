"""
sailing_data_processor.wind_estimator モジュール

GPSデータから風向風速を推定する機能を提供するモジュール
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Union, Any
import math
from functools import lru_cache
import warnings
import re

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
        self.version = "2.0.0"
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
            "default_downwind_angle": 150.0
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
    
    def _adjust_params_by_boat_type(self, boat_type: str) -> None:
        """
        艇種に応じたパラメータ調整
        
        Parameters:
        -----------
        boat_type : str
            艇種
        """
        # 艇種に基づく調整
        if boat_type == "laser":
            # レーザーは小型艇なのでタックが素早い
            self.params["min_maneuver_duration"] = 2.0
            self.params["max_maneuver_duration"] = 10.0
            self.params["upwind_threshold"] = 40.0
            self.params["default_upwind_angle"] = 45.0
            
        elif boat_type == "49er":
            # 49erは高速艇でタック時の減速が顕著
            self.params["tack_speed_drop_threshold"] = 40.0
            self.params["default_upwind_angle"] = 38.0
            self.params["default_downwind_angle"] = 140.0
            
        elif boat_type == "470":
            # 470は標準的なディンギー
            self.params["min_maneuver_duration"] = 3.0
            self.params["default_upwind_angle"] = 42.0
            
        elif boat_type == "nacra17":
            # Nacra17は高速カタマラン
            self.params["min_maneuver_duration"] = 3.5
            self.params["default_upwind_angle"] = 35.0
            self.params["default_downwind_angle"] = 135.0
            
        elif boat_type == "finn":
            # フィンはやや重く安定している
            self.params["min_maneuver_duration"] = 4.0
            self.params["upwind_threshold"] = 47.0
            self.params["default_upwind_angle"] = 44.0
    
    def estimate_wind_from_maneuvers(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        マニューバーパターンから風向を推定
        
        タック・ジャイブのパターンから風軸と風速を推定します。
        同一地点での往復なら、その中間方向が風向になります。
        
        Parameters:
        -----------
        df : pd.DataFrame
            GPS時系列データフレーム
            必要なカラム：
            - timestamp: 時刻
            - latitude, longitude: 位置
            - course: 進行方位（度）
            - speed: 速度（ノット）
            
        Returns:
        --------
        Dict[str, Any]
            推定された風情報：
            - direction: 風向（度、0-360）
            - speed: 風速（ノット）
            - confidence: 信頼度（0-1）
            - method: 推定方法
            - timestamp: 推定時刻
        """
        # データ確認
        if df.empty or len(df) < 10:
            return self._create_wind_result(0, 0, 0, "insufficient_data")
        
        # 必要なカラムが存在するか確認
        required_columns = ['timestamp', 'latitude', 'longitude', 'course', 'speed']
        if not all(col in df.columns for col in required_columns):
            missing_cols = [col for col in required_columns if col not in df.columns]
            warn_msg = f"データに必要なカラムがありません: {missing_cols}"
            warnings.warn(warn_msg)
            return self._create_wind_result(0, 0, 0, "missing_columns")
            
        # マニューバーを検出
        maneuvers_df = self.detect_maneuvers(df)
        
        # 十分なマニューバーがない場合
        if len(maneuvers_df) < 2:
            # マニューバーが足りない場合は進行方向と速度から直接推定
            return self.estimate_wind_from_course_speed(df)
        
        # タック/ジャイブを分類
        maneuvers_df = self.categorize_maneuvers(maneuvers_df, df)
        
        # タックのみを抽出（より信頼性の高い風向推定が可能）
        tacks_df = maneuvers_df[maneuvers_df['maneuver_type'] == 'tack'].copy()
        
        # タックが不足している場合は全マニューバーを使用
        if len(tacks_df) < 2:
            analyzed_df = maneuvers_df
        else:
            analyzed_df = tacks_df
        
        # マニューバー前後の方位から風向を推定
        wind_directions = []
        wind_confidences = []
        timestamps = []
        
        for _, maneuver in analyzed_df.iterrows():
            before_bearing = maneuver['before_bearing']
            after_bearing = maneuver['after_bearing']
            timestamp = maneuver['timestamp']
            
            # タックの場合：往復方向の中間が風向
            # 2つの方位の差の半分をオフセットとして使用
            angle_diff = self._calculate_angle_difference(after_bearing, before_bearing)
            
            # タックは通常180度近くの方位変化がある
            wind_dir = (before_bearing + angle_diff / 2) % 360
            
            # 風向が本当に往復の中間にあるという仮定の信頼度を計算
            # 理想的なタックなら方位変化は180度に近い
            abs_diff = abs(angle_diff)
            confidence = 1.0 - min(1.0, abs(abs_diff - 180) / 90)
            
            # 風向は「風が吹いてくる方向」として統一
            # タックは風上へのターンなので、求まった方向とは逆（180度反転）
            wind_dir = (wind_dir + 180) % 360
            
            wind_directions.append(wind_dir)
            wind_confidences.append(confidence)
            timestamps.append(timestamp)
        
        # 複数の推定結果がある場合は重み付き平均
        if wind_directions:
            # 最新の方が信頼性が高いと仮定して時間重みを追加
            time_weights = np.linspace(0.5, 1.0, len(timestamps))
            
            # 信頼度と時間重みを積算
            combined_weights = wind_confidences * time_weights
            
            # 角度の加重平均（円環統計）
            sin_avg = np.average(np.sin(np.radians(wind_directions)), weights=combined_weights)
            cos_avg = np.average(np.cos(np.radians(wind_directions)), weights=combined_weights)
            
            avg_wind_dir = (math.degrees(math.atan2(sin_avg, cos_avg)) + 360) % 360
            
            # 信頼度の平均
            avg_confidence = np.mean(wind_confidences)
            
            # 風速の推定（タック前後の速度変化から）
            wind_speed = self._estimate_wind_speed_from_maneuvers(analyzed_df, df)
            
            # 最新のタイムスタンプ
            latest_timestamp = max(timestamps)
            
            return self._create_wind_result(
                avg_wind_dir, wind_speed, avg_confidence, 
                "maneuver_analysis", latest_timestamp
            )
        
        # マニューバーからの推定ができなかった場合は代替手法
        return self.estimate_wind_from_course_speed(df)
    
    def _estimate_wind_speed_from_maneuvers(self, maneuvers_df: pd.DataFrame, full_df: pd.DataFrame) -> float:
        """
        マニューバーデータから風速を推定
        
        Parameters:
        -----------
        maneuvers_df : pd.DataFrame
            マニューバーのデータフレーム
        full_df : pd.DataFrame
            完全な航跡データフレーム
            
        Returns:
        --------
        float
            推定風速（ノット）
        """
        # マニューバーがない場合は代替手法
        if maneuvers_df.empty:
            return self._estimate_wind_speed_from_speed_variations(full_df)
        
        # 各マニューバー前後の速度変化から風速を推定
        wind_speed_estimates = []
        
        for _, maneuver in maneuvers_df.iterrows():
            # マニューバー前後のデータを取得
            maneuver_time = maneuver['timestamp']
            
            # 前後の時間帯
            pre_time_start = maneuver_time - timedelta(seconds=30)
            pre_time_end = maneuver_time - timedelta(seconds=5)
            post_time_start = maneuver_time + timedelta(seconds=5)
            post_time_end = maneuver_time + timedelta(seconds=30)
            
            # 前後の速度データ
            pre_data = full_df[(full_df['timestamp'] >= pre_time_start) & 
                               (full_df['timestamp'] <= pre_time_end)]
            post_data = full_df[(full_df['timestamp'] >= post_time_start) & 
                                (full_df['timestamp'] <= post_time_end)]
            
            # 十分なデータがある場合
            if len(pre_data) >= 3 and len(post_data) >= 3:
                pre_speed = pre_data['speed'].mean()
                post_speed = post_data['speed'].mean()
                
                # ジャイブ／タックの場合、艇速から風速を推定（ボート特性による）
                if maneuver['maneuver_type'] == 'tack':
                    # 風上なら一般に艇速は風速の0.6～0.8倍程度
                    avg_speed = max(pre_speed, post_speed)
                    est_wind_speed = avg_speed / 0.7  # 簡易的な推定
                else:  # ジャイブの場合
                    # 風下なら一般に艇速は風速の0.5～0.7倍程度
                    avg_speed = max(pre_speed, post_speed)
                    est_wind_speed = avg_speed / 0.6  # 簡易的な推定
                
                wind_speed_estimates.append(est_wind_speed)
        
        # 複数の推定値の中央値を取る（外れ値に堅牢）
        if wind_speed_estimates:
            return float(np.median(wind_speed_estimates))
        
        # 推定できない場合は代替手法
        return self._estimate_wind_speed_from_speed_variations(full_df)
    
    def _estimate_wind_speed_from_speed_variations(self, df: pd.DataFrame) -> float:
        """
        速度変動から風速を推定（代替手法）
        
        Parameters:
        -----------
        df : pd.DataFrame
            航跡データフレーム
            
        Returns:
        --------
        float
            推定風速（ノット）
        """
        # 十分なデータがない場合
        if len(df) < 10:
            return 0.0
        
        # 速度の90%値を取得（最高速度近辺）
        top_speed = df['speed'].quantile(0.9)
        
        # 艇種ごとの特性に基づいて風速を推定
        if self.boat_type == "laser":
            # レーザーのポーラー特性（例）
            est_wind_speed = top_speed / 0.65  # 上位速度は風速の65%程度
        elif self.boat_type == "49er":
            # 49erは高速艇
            est_wind_speed = top_speed / 0.75
        else:
            # デフォルト（一般的なディンギー）
            est_wind_speed = top_speed / 0.7
        
        # 非現実的な値は補正
        est_wind_speed = max(3.0, min(30.0, est_wind_speed))
        
        return float(est_wind_speed)
    
    def estimate_wind_from_course_speed(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        艇の進行方向と速度から風向風速を推定
        
        艇の進路・速度分布と一般的なセーリング理論に基づいて
        風向風速を推定します。
        
        Parameters:
        -----------
        df : pd.DataFrame
            GPS時系列データフレーム
            必要なカラム：
            - timestamp: 時刻
            - course: 進行方位（度）
            - speed: 速度（ノット）
            
        Returns:
        --------
        Dict[str, Any]
            推定された風情報：
            - direction: 風向（度、0-360）
            - speed: 風速（ノット）
            - confidence: 信頼度（0-1）
            - method: 推定方法
            - timestamp: 推定時刻
        """
        # データ確認
        if df.empty or len(df) < 10:
            return self._create_wind_result(0, 0, 0, "insufficient_data")
        
        # 必要なカラムが存在するか確認
        required_columns = ['timestamp', 'course', 'speed']
        if not all(col in df.columns for col in required_columns):
            missing_cols = [col for col in required_columns if col not in df.columns]
            warn_msg = f"データに必要なカラムがありません: {missing_cols}"
            warnings.warn(warn_msg)
            return self._create_wind_result(0, 0, 0, "missing_columns")
        
        # 最新のタイムスタンプ
        latest_timestamp = df['timestamp'].max()
        
        # コースのローズチャート分析（頻度分布）
        course_bins = np.linspace(0, 360, 37)  # 10度ごとに区切る
        course_hist, _ = np.histogram(df['course'], bins=course_bins)
        
        # 最頻値のインデックスを取得
        most_common_indices = np.argsort(-course_hist)[:2]
        
        # 最頻値ビンの中心値
        bin_centers = (course_bins[:-1] + course_bins[1:]) / 2
        most_common_courses = [bin_centers[i] for i in most_common_indices]
        
        # もし2つの最頻値が約180度離れていれば、おそらく往復航路
        course_diff = self._calculate_angle_difference(most_common_courses[0], most_common_courses[1])
        
        if 150 <= abs(course_diff) <= 210:
            # 往復航路と判断、風向は2つの最頻値の中間方向（風上方向）の反対
            wind_dir = (most_common_courses[0] + course_diff / 2) % 360
            
            # 風向は「風が吹いてくる方向」として統一
            wind_dir = (wind_dir + 180) % 360
            
            # 信頼度は分布の鋭さに依存
            top_freq = course_hist[most_common_indices[0]]
            second_freq = course_hist[most_common_indices[1]]
            total_freq = np.sum(course_hist)
            
            # 全体に対するトップ2の比率で信頼度を計算
            confidence = min(0.85, (top_freq + second_freq) / total_freq * 1.5)
            
            # 風速の推定
            wind_speed = self._estimate_wind_speed_from_speed_variations(df)
            
            return self._create_wind_result(
                wind_dir, wind_speed, confidence, 
                "course_distribution", latest_timestamp
            )
        
        # 角度分布から推定できない場合、速度分布とコースの関係から推定
        return self._estimate_wind_from_speed_course_correlation(df)
    
    def _estimate_wind_from_speed_course_correlation(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        速度とコースの相関から風向風速を推定
        
        Parameters:
        -----------
        df : pd.DataFrame
            航跡データフレーム
            
        Returns:
        --------
        Dict[str, Any]
            推定された風情報
        """
        # データ確認
        if df.empty or len(df) < 10:
            return self._create_wind_result(0, 0, 0, "insufficient_data")
        
        # 最新のタイムスタンプ
        latest_timestamp = df['timestamp'].max()
        
        # 風向の候補方向（10度ごと）
        candidate_wind_dirs = np.linspace(0, 350, 36)
        
        # 各候補方向について評価スコアを計算
        scores = []
        
        for wind_dir in candidate_wind_dirs:
            # 風向に対する相対角度を計算
            df['rel_angle'] = df['course'].apply(
                lambda course: self._calculate_angle_difference(course, wind_dir)
            )
            df['abs_rel_angle'] = df['rel_angle'].abs()
            
            # 風上/風下のスコアリング
            upwind_mask = df['abs_rel_angle'] <= self.params["upwind_threshold"]
            downwind_mask = df['abs_rel_angle'] >= self.params["downwind_threshold"]
            
            # データを分割
            upwind_df = df[upwind_mask]
            downwind_df = df[downwind_mask]
            reach_df = df[~upwind_mask & ~downwind_mask]
            
            # 風向の評価スコア
            score = 0
            
            # 風上データについてVMG極大値を評価
            if len(upwind_df) >= 5:
                # VMG計算（風向に対する前進成分）
                upwind_df['vmg'] = upwind_df.apply(
                    lambda row: row['speed'] * np.cos(np.radians(row['abs_rel_angle'])), 
                    axis=1
                )
                
                # 風上のVMG最大値
                max_upwind_vmg = upwind_df['vmg'].max()
                
                # 風上の最適角度に近い場合スコア加算
                optimal_angles = upwind_df[upwind_df['vmg'] > max_upwind_vmg * 0.9]['abs_rel_angle']
                if len(optimal_angles) > 0:
                    avg_optimal_angle = optimal_angles.mean()
                    # 風上の最適角度は艇種によって異なるが、一般に35-45度程度
                    upwind_score = 1.0 - min(1.0, abs(avg_optimal_angle - self.params["default_upwind_angle"]) / 20)
                    score += upwind_score * 2.0  # 風上は重要なので重み付け
            
            # 風下データについてもVMG極大値を評価
            if len(downwind_df) >= 5:
                # VMG計算（風向に対する前進成分）
                downwind_df['vmg'] = downwind_df.apply(
                    lambda row: row['speed'] * np.cos(np.radians(180 - row['abs_rel_angle'])), 
                    axis=1
                )
                
                # 風下のVMG最大値
                max_downwind_vmg = downwind_df['vmg'].max()
                
                # 風下の最適角度に近い場合スコア加算
                optimal_angles = downwind_df[downwind_df['vmg'] > max_downwind_vmg * 0.9]['abs_rel_angle']
                if len(optimal_angles) > 0:
                    avg_optimal_angle = optimal_angles.mean()
                    # 風下の最適角度は艇種によって異なるが、一般に135-160度程度
                    downwind_score = 1.0 - min(1.0, abs(avg_optimal_angle - self.params["default_downwind_angle"]) / 30)
                    score += downwind_score
            
            # リーチングの速度分布も考慮
            if len(reach_df) >= 5:
                # リーチングのピーク速度（90度付近で最も速いはず）
                reach_df['beam_factor'] = reach_df.apply(
                    lambda row: 1.0 - abs(abs(row['rel_angle']) - 90) / 45, 
                    axis=1
                )
                reach_df['weighted_speed'] = reach_df['speed'] * reach_df['beam_factor']
                
                if reach_df['weighted_speed'].max() > df['speed'].mean() * 1.2:
                    score += 0.5
            
            scores.append(score)
        
        # 最高スコアの風向を選択
        best_idx = np.argmax(scores)
        best_wind_dir = candidate_wind_dirs[best_idx]
        best_score = scores[best_idx]
        
        # 信頼度の計算（最大3点のスコアに対する比率）
        confidence = min(0.8, best_score / 3.0)
        
        # スコアが低すぎる場合は信頼度を下げる
        if best_score < 1.0:
            confidence = min(confidence, 0.4)
        
        # 風速の推定
        wind_speed = self._estimate_wind_speed_from_speed_variations(df)
        
        return self._create_wind_result(
            best_wind_dir, wind_speed, confidence, 
            "vmg_analysis", latest_timestamp
        )
    
    def detect_maneuvers(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        航跡データからマニューバー（タック・ジャイブ）を検出
        
        Parameters:
        -----------
        df : pd.DataFrame
            GPS時系列データフレーム
            必要なカラム：
            - timestamp: 時刻
            - latitude, longitude: 位置
            - course: 進行方位（度）
            - speed: 速度（ノット）
            
        Returns:
        --------
        pd.DataFrame
            検出されたマニューバーのデータフレーム
            カラム：
            - timestamp: マニューバー時刻
            - latitude, longitude: マニューバー位置
            - before_bearing: マニューバー前の方位
            - after_bearing: マニューバー後の方位
            - bearing_change: 方位変化量（度）
            - speed_before: マニューバー前の速度
            - speed_after: マニューバー後の速度
            - speed_ratio: 速度比率（後/前）
            - maneuver_type: マニューバータイプ（初期値はunknown）
        """
        # データ確認
        if df.empty or len(df) < 10:
            return pd.DataFrame()
        
        # 必要なカラムが存在するか確認
        required_columns = ['timestamp', 'latitude', 'longitude', 'course', 'speed']
        if not all(col in df.columns for col in required_columns):
            missing_cols = [col for col in required_columns if col not in df.columns]
            warn_msg = f"データに必要なカラムがありません: {missing_cols}"
            warnings.warn(warn_msg)
            return pd.DataFrame()
            
        # データをコピーして前処理
        df_copy = df.copy()
        
        # 時間順にソート
        df_copy = df_copy.sort_values('timestamp')
        
        # 方位の差分を計算（連続するデータポイント間）
        df_copy['course_prev'] = df_copy['course'].shift(1)
        df_copy['bearing_change'] = df_copy.apply(
            lambda row: self._calculate_angle_difference(row['course'], row['course_prev'])
            if not pd.isna(row['course_prev']) else 0,
            axis=1
        )
        
        # 速度の変化率を計算
        df_copy['speed_prev'] = df_copy['speed'].shift(1)
        df_copy['speed_change_ratio'] = df_copy['speed'] / df_copy['speed_prev'].replace(0, 0.01)
        
        # 極端な値を除外
        df_copy.loc[df_copy['speed_change_ratio'] > 5, 'speed_change_ratio'] = 1
        
        # 移動ウィンドウでの方位変化の合計（マニューバー検出用）
        window_size = self.params["maneuver_window_size"]
        min_angle_change = self.params["min_tack_angle_change"]
        
        df_copy['bearing_change_sum'] = df_copy['bearing_change'].rolling(window=window_size, center=True).sum()
        
        # 方向転換の検出（移動ウィンドウ内の累積変化がmin_angle_changeを超える場合）
        df_copy['is_maneuver'] = df_copy['bearing_change_sum'] > min_angle_change
        
        # 連続する方向転換を1つのイベントとしてグループ化
        df_copy['maneuver_group'] = (df_copy['is_maneuver'] != df_copy['is_maneuver'].shift(1)).cumsum()
        
        # 方向転換グループごとに最適な転換点を見つける
        maneuver_points = []
        
        for group_id, group in df_copy[df_copy['is_maneuver']].groupby('maneuver_group'):
            if len(group) > 0:
                # グループの中心点を見つける（グループの中央または最大変化点）
                if len(group) >= 5:
                    # 大きなグループの場合は速度変化も考慮して最適点を選択
                    central_idx = self._find_optimal_maneuver_point(group, df_copy)
                else:
                    # 小さなグループの場合は単純に方位変化最大点を選択
                    central_idx = group['bearing_change'].idxmax()
                
                if central_idx is not None and central_idx in df_copy.index:
                    central_point = df_copy.loc[central_idx]
                    
                    # 前後の方位と速度を取得
                    # 前方のデータポイント（マニューバー前）
                    before_window = df_copy[(df_copy['timestamp'] < central_point['timestamp']) & 
                                          (df_copy['timestamp'] >= central_point['timestamp'] - timedelta(seconds=10))]
                    
                    # 後方のデータポイント（マニューバー後）
                    after_window = df_copy[(df_copy['timestamp'] > central_point['timestamp']) & 
                                         (df_copy['timestamp'] <= central_point['timestamp'] + timedelta(seconds=10))]
                    
                    # 前後のデータが十分ある場合のみ処理
                    if len(before_window) >= 3 and len(after_window) >= 3:
                        # 前後の平均方位と速度
                        before_bearing = before_window['course'].mean()
                        after_bearing = after_window['course'].mean()
                        bearing_change = self._calculate_angle_difference(after_bearing, before_bearing)
                        
                        speed_before = before_window['speed'].mean()
                        speed_after = after_window['speed'].mean()
                        speed_ratio = speed_after / speed_before if speed_before > 0 else 1.0
                        
                        # マニューバー時間の長さ（後で分類に使用）
                        maneuver_duration = (after_window['timestamp'].min() - before_window['timestamp'].max()).total_seconds()
                        
                        # マニューバーエントリーの作成
                        maneuver_entry = {
                            'timestamp': central_point['timestamp'],
                            'latitude': central_point['latitude'],
                            'longitude': central_point['longitude'],
                            'before_bearing': before_bearing,
                            'after_bearing': after_bearing,
                            'bearing_change': bearing_change,
                            'speed_before': speed_before,
                            'speed_after': speed_after,
                            'speed_ratio': speed_ratio,
                            'maneuver_duration': maneuver_duration,
                            'maneuver_type': 'unknown'  # 初期値
                        }
                        
                        maneuver_points.append(maneuver_entry)
        
        # 結果をデータフレームに変換
        result_df = pd.DataFrame(maneuver_points)
        
        # 必要なマニューバー属性がない場合は空のデータフレームを返す
        if result_df.empty or 'bearing_change' not in result_df.columns:
            return pd.DataFrame()
        
        # 極端な値のフィルタリング
        min_duration = self.params["min_maneuver_duration"]
        max_duration = self.params["max_maneuver_duration"]
        
        # 方位変化と所要時間でフィルタリング
        result_df = result_df[
            (abs(result_df['bearing_change']) >= self.params["min_tack_angle_change"]) &
            (result_df['maneuver_duration'] >= min_duration) &
            (result_df['maneuver_duration'] <= max_duration)
        ]
        
        # 検出結果を保存
        self.detected_maneuvers = result_df.to_dict('records')
        
        return result_df
    
    def _find_optimal_maneuver_point(self, group: pd.DataFrame, full_df: pd.DataFrame) -> Optional[int]:
        """
        マニューバーグループ内で最適な転換点を見つける
        
        方位変化と速度変化を考慮して、最も可能性の高いマニューバー地点を特定します。
        
        Parameters:
        -----------
        group : pd.DataFrame
            マニューバーグループのデータフレーム
        full_df : pd.DataFrame
            全データのデータフレーム
            
        Returns:
        --------
        int or None
            最適なマニューバー地点のインデックス
        """
        if group.empty:
            return None
        
        # 方位変化が最大の地点
        max_bearing_change_idx = group['bearing_change'].idxmax()
        
        # 速度降下が最大の地点
        if 'speed_change_ratio' in group.columns:
            # 速度低下点（速度比が1未満 = 減速）
            speed_drop_points = group[group['speed_change_ratio'] < 1]
            if not speed_drop_points.empty:
                min_speed_ratio_idx = speed_drop_points['speed_change_ratio'].idxmin()
            else:
                min_speed_ratio_idx = None
        else:
            min_speed_ratio_idx = None
        
        # 方位変化と速度変化の両方がある場合は、それらの間の地点を選択
        if min_speed_ratio_idx is not None:
            # 方位変化地点と速度低下地点のインデックス差
            idx_diff = abs(full_df.index.get_loc(max_bearing_change_idx) - 
                          full_df.index.get_loc(min_speed_ratio_idx))
            
            if idx_diff <= 5:  # 5ポイント以内なら関連していると判断
                # 2つの地点の時間差
                t1 = full_df.loc[max_bearing_change_idx, 'timestamp']
                t2 = full_df.loc[min_speed_ratio_idx, 'timestamp']
                
                if t1 <= t2:
                    # 通常は方位変化が先、速度低下が後
                    # 方位変化地点を優先（より正確なマニューバー開始点）
                    return max_bearing_change_idx
                else:
                    # 速度低下が先の場合は中間点を計算
                    mid_time = t1 - (t1 - t2) / 2
                    # 時間的に最も近いポイントを見つける
                    time_diffs = abs(full_df.loc[group.index, 'timestamp'] - mid_time)
                    return time_diffs.idxmin()
        
        # デフォルトは方位変化最大点
        return max_bearing_change_idx
    
    def categorize_maneuvers(self, maneuvers_df: pd.DataFrame, full_df: pd.DataFrame) -> pd.DataFrame:
        """
        検出されたマニューバーをタック/ジャイブに分類
        
        Parameters:
        -----------
        maneuvers_df : pd.DataFrame
            検出されたマニューバーのデータフレーム
        full_df : pd.DataFrame
            完全な航跡データフレーム
            
        Returns:
        --------
        pd.DataFrame
            タイプ分類されたマニューバーのデータフレーム
        """
        if maneuvers_df.empty or len(maneuvers_df) == 0:
            return maneuvers_df
        
        # コピーを作成
        result_df = maneuvers_df.copy()
        
        # 風向を推定
        estimated_wind = self.estimate_wind_from_course_speed(full_df)
        wind_direction = estimated_wind['direction']
        
        # 各マニューバーを分類
        for idx, maneuver in result_df.iterrows():
            before_bearing = maneuver['before_bearing']
            after_bearing = maneuver['after_bearing']
            bearing_change = maneuver['bearing_change']
            speed_ratio = maneuver['speed_ratio']
            
            # 風向に対する相対角度を計算
            before_rel_wind = self._calculate_angle_difference(before_bearing, wind_direction)
            after_rel_wind = self._calculate_angle_difference(after_bearing, wind_direction)
            
            # 風上/風下判定の閾値
            upwind_threshold = self.params["upwind_threshold"]
            downwind_threshold = self.params["downwind_threshold"]
            
            # 風上/風下の判定
            before_is_upwind = abs(before_rel_wind) <= upwind_threshold
            before_is_downwind = abs(before_rel_wind) >= downwind_threshold
            
            after_is_upwind = abs(after_rel_wind) <= upwind_threshold
            after_is_downwind = abs(after_rel_wind) >= downwind_threshold
            
            # マニューバータイプの判定
            maneuver_type = 'unknown'
            
            # タックの判定条件
            tack_conditions = [
                # 両方風上、または風上→クローズリーチ、またはクローズリーチ→風上
                (before_is_upwind or abs(before_rel_wind) <= 60) and 
                (after_is_upwind or abs(after_rel_wind) <= 60),
                
                # 方位変化が60〜180度
                abs(bearing_change) >= 60 and abs(bearing_change) <= 180,
                
                # タック時は通常速度が落ちる
                speed_ratio < 0.9 or speed_ratio > 1.3  # タック後の加速も考慮
            ]
            
            # ジャイブの判定条件
            jibe_conditions = [
                # 両方風下、または風下→ブロードリーチ、またはブロードリーチ→風下
                (before_is_downwind or abs(before_rel_wind) >= 120) and 
                (after_is_downwind or abs(after_rel_wind) >= 120),
                
                # 方位変化が60〜180度
                abs(bearing_change) >= 60 and abs(bearing_change) <= 180
            ]
            
            # 判定
            if all(tack_conditions):
                maneuver_type = 'tack'
            elif all(jibe_conditions):
                maneuver_type = 'jibe'
            
            # 分類結果をセット
            result_df.at[idx, 'maneuver_type'] = maneuver_type
            
            # 風情報を追加
            result_df.at[idx, 'wind_direction'] = wind_direction
            result_df.at[idx, 'before_rel_wind'] = before_rel_wind
            result_df.at[idx, 'after_rel_wind'] = after_rel_wind
        
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
    
    def _create_wind_result(self, direction: float, speed: float, confidence: float, 
                          method: str, timestamp: datetime = None) -> Dict[str, Any]:
        """
        風向風速推定結果を標準形式で作成
        
        Parameters:
        -----------
        direction : float
            風向（度、0-360）
        speed : float
            風速（ノット）
        confidence : float
            信頼度（0-1）
        method : str
            推定方法
        timestamp : datetime, optional
            推定時刻
            
        Returns:
        --------
        Dict[str, Any]
            推定された風情報
        """
        result = {
            "direction": direction,
            "speed": speed,
            "confidence": confidence,
            "method": method,
            "timestamp": timestamp if timestamp is not None else datetime.now()
        }
        
        # 推定結果を保存
        self.estimated_wind = result
        
        return result
    
    def _calculate_angle_difference(self, angle1: float, angle2: float) -> float:
        """
        2つの角度の差を計算（-180〜180度の範囲で返す）
        
        Parameters:
        -----------
        angle1 : float
            1つ目の角度（度、0-360）
        angle2 : float
            2つ目の角度（度、0-360）
            
        Returns:
        --------
        float
            角度差（度、-180〜180）
        """
        # 角度が無効な場合は0を返す
        if not isinstance(angle1, (int, float)) or not isinstance(angle2, (int, float)):
            return 0
        
        # 角度を0-360の範囲に正規化
        a1 = angle1 % 360
        a2 = angle2 % 360
        
        # 角度差を計算（-180〜180度の範囲）
        diff = ((a1 - a2 + 180) % 360) - 180
        
        return diff
    
    def get_wind_direction_name(self, wind_direction: float) -> str:
        """
        風向を方位名に変換
        
        Parameters:
        -----------
        wind_direction : float
            風向（度、0-360、風が吹いてくる方向）
            
        Returns:
        --------
        str
            風向の方位名（例: "北東", "南南西"）
        """
        # 方位名のリスト（16方位）
        directions = [
            "北", "北北東", "北東", "東北東", 
            "東", "東南東", "南東", "南南東",
            "南", "南南西", "南西", "西南西", 
            "西", "西北西", "北西", "北北西"
        ]
        
        # 度数を16方位に変換
        idx = round(wind_direction / 22.5) % 16
        
        return directions[idx] + "の風"
    
    def get_estimated_wind_summary(self) -> str:
        """
        推定された風の要約を文字列で取得
        
        Returns:
        --------
        str
            風の要約情報
        """
        wind = self.estimated_wind
        
        if wind["confidence"] <= 0:
            return "風向風速は推定できませんでした。"
        
        direction_name = self.get_wind_direction_name(wind["direction"])
        confidence_pct = int(wind["confidence"] * 100)
        
        return (
            f"{direction_name} {wind['direction']:.1f}°、"
            f"{wind['speed']:.1f}ノット "
            f"（信頼度: {confidence_pct}%、推定方法: {wind['method']}）"
        )
    
    def get_polar_data(self, boat_type: str = None) -> Dict[str, List[float]]:
        """
        艇種のポーラーデータを取得またはダミーデータを生成

        Parameters:
        -----------
        boat_type : str, optional
            艇種（デフォルト: インスタンス初期化時の設定）

        Returns:
        --------
        Dict[str, List[float]]
            ポーラーデータ（風速と方位角ごとの艇速）
        """
        if boat_type is None:
            boat_type = self.boat_type

        # TODO: 実際のポーラーデータの読み込み
        # ここではダミーデータを返す
        angles = list(range(0, 181, 5))  # 0°から180°まで5°刻み
        
        # 風速6ノットでの艇速
        speed_6knots = []
        for angle in angles:
            if angle < 30:
                # 風上すぎる領域は速度ゼロ
                speed = 0
            elif angle < 50:
                # 風上は風速の約40-60%
                speed = 6 * (0.4 + (angle - 30) * 0.01)
            elif angle < 90:
                # クローズリーチが最速（風速の約70-80%）
                speed = 6 * (0.7 + (angle - 50) * 0.002)
            elif angle < 150:
                # リーチングからブロードリーチ（風速の約80-65%）
                speed = 6 * (0.8 - (angle - 90) * 0.0025)
            else:
                # 風下は風速の約65-60%
                speed = 6 * (0.65 - (angle - 150) * 0.001)
            
            speed_6knots.append(round(speed, 2))

        # 風速10ノットでの艇速（やや速くなる）
        speed_10knots = []
        for angle in angles:
            if angle < 28:
                # 風上すぎる領域は速度ゼロ（風が強い方が風上に向かいやすい）
                speed = 0
            elif angle < 45:
                # 風上は風速の約45-65%
                speed = 10 * (0.45 + (angle - 28) * 0.012)
            elif angle < 90:
                # クローズリーチが最速（風速の約65-75%）
                speed = 10 * (0.65 + (angle - 45) * 0.002)
            elif angle < 150:
                # リーチングからブロードリーチ（風速の約75-68%）
                speed = 10 * (0.75 - (angle - 90) * 0.0012)
            else:
                # 風下は風速の約68-65%
                speed = 10 * (0.68 - (angle - 150) * 0.0006)
            
            speed_10knots.append(round(speed, 2))

        # 風速14ノットでの艇速（さらに速い）
        speed_14knots = []
        for angle in angles:
            if angle < 27:
                # 風上すぎる領域は速度ゼロ
                speed = 0
            elif angle < 45:
                # 風上は風速の約48-68%
                speed = 14 * (0.48 + (angle - 27) * 0.011)
            elif angle < 100:
                # クローズリーチが最速（風速の約68-72%）
                speed = 14 * (0.68 + (angle - 45) * 0.0007)
            elif angle < 150:
                # リーチングからブロードリーチ（風速の約72-70%）
                speed = 14 * (0.72 - (angle - 100) * 0.0004)
            else:
                # 風下は風速の約70-67%
                speed = 14 * (0.70 - (angle - 150) * 0.0006)
            
            speed_14knots.append(round(speed, 2))

        return {
            "angles": angles,
            "wind_speeds": [6, 10, 14],
            "boat_speeds": [speed_6knots, speed_10knots, speed_14knots]
        }

    def get_optimal_vmg_angles(self, wind_speed: float, boat_type: str = None) -> Dict[str, float]:
        """
        指定風速での最適VMG角度を計算

        Parameters:
        -----------
        wind_speed : float
            風速（ノット）
        boat_type : str, optional
            艇種（デフォルト: インスタンス初期化時の設定）

        Returns:
        --------
        Dict[str, float]
            風上・風下のVMG最適角度と速度
        """
        if boat_type is None:
            boat_type = self.boat_type

        # ポーラーデータを取得
        polar_data = self.get_polar_data(boat_type)
        
        # 風速をインターポレーション（指定された風速のポーラーがない場合）
        wind_speeds = polar_data["wind_speeds"]
        boat_speeds = polar_data["boat_speeds"]
        angles = polar_data["angles"]
        
        # 風速のインターポレーション
        if wind_speed <= wind_speeds[0]:
            # 最低風速以下
            interpolated_speeds = boat_speeds[0].copy()
            
        elif wind_speed >= wind_speeds[-1]:
            # 最高風速以上
            interpolated_speeds = boat_speeds[-1].copy()
            
        else:
            # 風速の間をインターポレーション
            for i in range(len(wind_speeds) - 1):
                if wind_speeds[i] <= wind_speed < wind_speeds[i+1]:
                    ratio = (wind_speed - wind_speeds[i]) / (wind_speeds[i+1] - wind_speeds[i])
                    interpolated_speeds = [
                        boat_speeds[i][j] + ratio * (boat_speeds[i+1][j] - boat_speeds[i][j])
                        for j in range(len(angles))
                    ]
                    break
        
        # VMGの計算
        vmg_upwind = []  # 風上方向への投影成分
        vmg_downwind = []  # 風下方向への投影成分
        
        for i, angle in enumerate(angles):
            # VMG = boat_speed * cos(angle)
            vmg_up = interpolated_speeds[i] * math.cos(math.radians(angle))
            vmg_down = interpolated_speeds[i] * math.cos(math.radians(180 - angle))
            
            vmg_upwind.append(vmg_up)
            vmg_downwind.append(vmg_down)
        
        # 風上の最適VMG
        max_upwind_vmg = max(vmg_upwind)
        max_upwind_idx = vmg_upwind.index(max_upwind_vmg)
        optimal_upwind_angle = angles[max_upwind_idx]
        optimal_upwind_speed = interpolated_speeds[max_upwind_idx]
        
        # 風下の最適VMG
        max_downwind_vmg = max(vmg_downwind)
        max_downwind_idx = vmg_downwind.index(max_downwind_vmg)
        optimal_downwind_angle = angles[max_downwind_idx]
        optimal_downwind_speed = interpolated_speeds[max_downwind_idx]
        
        return {
            "upwind_angle": optimal_upwind_angle,
            "upwind_boat_speed": optimal_upwind_speed,
            "upwind_vmg": max_upwind_vmg,
            "downwind_angle": optimal_downwind_angle,
            "downwind_boat_speed": optimal_downwind_speed,
            "downwind_vmg": max_downwind_vmg
        }
