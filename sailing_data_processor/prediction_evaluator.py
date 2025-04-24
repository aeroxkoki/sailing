# -*- coding: utf-8 -*-
"""
sailing_data_processor.prediction_evaluator モジュール

風の予測精度評価を行うためのモジュール。
過去の予測と実際の風データを比較し、予測品質の履歴を追跡します。
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union, Any
from datetime import datetime, timedelta
import math
from collections import deque

class PredictionEvaluator:
    """
    風の予測品質を評価するクラス
    
    機能:
    - 過去の予測値と実測値の比較
    - 予測誤差の統計的分析
    - 条件ごとの予測精度評価
    """
    
    def __init__(self, max_history_size: int = 100):
        """
        初期化
        
        Parameters:
        -----------
        max_history_size : int
            履歴保持の最大サイズ
        """
        # 評価履歴
        self.evaluation_history = deque(maxlen=max_history_size)
        
        # 最新の評価スコア
        self.current_scores = {
            'direction_mae': None,      # 風向平均絶対誤差（度）
            'speed_mae': None,          # 風速平均絶対誤差（ノット）
            'direction_bias': None,     # 風向バイアス（度）
            'speed_bias': None,         # 風速バイアス（ノット）
            'prediction_success': None  # 予測成功率（0-1）
        }
        
        # 条件別の累積スコア
        self.condition_scores = {
            'light_wind': {'direction_mae': [], 'speed_mae': [], 'count': 0},
            'medium_wind': {'direction_mae': [], 'speed_mae': [], 'count': 0},
            'strong_wind': {'direction_mae': [], 'speed_mae': [], 'count': 0},
            'shifting_wind': {'direction_mae': [], 'speed_mae': [], 'count': 0},
            'steady_wind': {'direction_mae': [], 'speed_mae': [], 'count': 0}
        }
        
        # 予測ホライズン別のスコア
        self.horizon_scores = {
            'short': {'direction_mae': [], 'speed_mae': [], 'count': 0},  # 5分以内
            'medium': {'direction_mae': [], 'speed_mae': [], 'count': 0}, # 5-15分
            'long': {'direction_mae': [], 'speed_mae': [], 'count': 0}    # 15分以上
        }
    
    def evaluate_prediction(self, predicted: Dict[str, Any], actual: Dict[str, Any],
                         prediction_time: datetime, evaluation_time: datetime) -> Dict[str, float]:
        """
        予測風データと実際の風データを比較して予測品質を評価
        
        Parameters:
        -----------
        predicted : Dict[str, Any]
            予測風データ（wind_direction, wind_speed, confidence）
        actual : Dict[str, Any]
            実際の風データ（wind_direction, wind_speed）
        prediction_time : datetime
            予測が行われた時間
        evaluation_time : datetime
            評価時点（実際のデータが測定された時間）
            
        Returns:
        --------
        Dict[str, float]
            評価結果
        """
        # 必要なデータが揃っているか確認
        if not all(k in predicted for k in ['wind_direction', 'wind_speed', 'confidence']):
            return {'error': 'Incomplete prediction data'}
        
        if not all(k in actual for k in ['wind_direction', 'wind_speed']):
            return {'error': 'Incomplete actual data'}
        
        # 風向の差（-180〜180度の範囲）
        direction_diff = self._calculate_angle_difference(
            actual['wind_direction'], predicted['wind_direction']
        )
        
        # 風速の差
        speed_diff = actual['wind_speed'] - predicted['wind_speed']
        
        # 予測ホライズン（予測から実測までの時間）
        horizon_seconds = (evaluation_time - prediction_time).total_seconds()
        
        # 予測信頼度
        predicted_confidence = predicted.get('confidence', 0.5)
        
        # 評価結果
        evaluation = {
            'direction_error': direction_diff,  # 風向誤差（度）
            'speed_error': speed_diff,          # 風速誤差（ノット）
            'direction_abs_error': abs(direction_diff),  # 風向絶対誤差（度）
            'speed_abs_error': abs(speed_diff),          # 風速絶対誤差（ノット）
            'horizon_seconds': horizon_seconds,          # 予測ホライズン（秒）
            'predicted_confidence': predicted_confidence, # 予測信頼度
            'evaluation_time': evaluation_time,          # 評価時間
            'prediction_time': prediction_time           # 予測時間
        }
        
        # 風条件の分類
        wind_speed = actual['wind_speed']
        if wind_speed < 5:
            condition = 'light_wind'
        elif wind_speed < 15:
            condition = 'medium_wind'
        else:
            condition = 'strong_wind'
        
        evaluation['wind_condition'] = condition
        
        # 風の安定性の分類（他の評価データがある場合のみ）
        if self.evaluation_history:
            last_eval = self.evaluation_history[-1]
            if 'wind_direction' in last_eval and abs(self._calculate_angle_difference(
                    actual['wind_direction'], last_eval['wind_direction'])) > 10:
                stability = 'shifting_wind'
            else:
                stability = 'steady_wind'
            
            evaluation['wind_stability'] = stability
        else:
            evaluation['wind_stability'] = 'unknown'
        
        # 予測ホライズンの分類
        if horizon_seconds <= 300:  # 5分以内
            horizon_category = 'short'
        elif horizon_seconds <= 900:  # 15分以内
            horizon_category = 'medium'
        else:
            horizon_category = 'long'
        
        evaluation['horizon_category'] = horizon_category
        
        # 予測成功の判定
        direction_success = abs(direction_diff) <= 15  # 風向15度以内
        speed_success = abs(speed_diff) <= 2          # 風速2ノット以内
        evaluation['prediction_success'] = 1 if direction_success and speed_success else 0
        
        # 評価履歴に追加
        self.evaluation_history.append({
            **evaluation,
            'wind_direction': actual['wind_direction'],
            'wind_speed': actual['wind_speed']
        })
        
        # 条件別スコアの更新
        self.condition_scores[condition]['direction_mae'].append(abs(direction_diff))
        self.condition_scores[condition]['speed_mae'].append(abs(speed_diff))
        self.condition_scores[condition]['count'] += 1
        
        if 'wind_stability' in evaluation and evaluation['wind_stability'] != 'unknown':
            stability = evaluation['wind_stability']
            self.condition_scores[stability]['direction_mae'].append(abs(direction_diff))
            self.condition_scores[stability]['speed_mae'].append(abs(speed_diff))
            self.condition_scores[stability]['count'] += 1
        
        # ホライズン別スコアの更新
        self.horizon_scores[horizon_category]['direction_mae'].append(abs(direction_diff))
        self.horizon_scores[horizon_category]['speed_mae'].append(abs(speed_diff))
        self.horizon_scores[horizon_category]['count'] += 1
        
        # 全体スコアの更新
        self._update_current_scores()
        
        return evaluation
    
    def get_prediction_quality_report(self) -> Dict[str, Any]:
        """
        予測品質の総合レポートを生成
        
        Returns:
        --------
        Dict[str, Any]
            予測品質レポート
        """
        if not self.evaluation_history:
            return {
                'status': 'No evaluation data available',
                'sample_size': 0
            }
        
        # 最新の評価スコア
        current_scores = self.current_scores.copy()
        
        # 条件別の平均スコア
        condition_avg = {}
        for condition, data in self.condition_scores.items():
            if data['count'] > 0:
                condition_avg[condition] = {
                    'direction_mae': np.mean(data['direction_mae']) if data['direction_mae'] else None,
                    'speed_mae': np.mean(data['speed_mae']) if data['speed_mae'] else None,
                    'sample_size': data['count']
                }
        
        # ホライズン別の平均スコア
        horizon_avg = {}
        for horizon, data in self.horizon_scores.items():
            if data['count'] > 0:
                horizon_avg[horizon] = {
                    'direction_mae': np.mean(data['direction_mae']) if data['direction_mae'] else None,
                    'speed_mae': np.mean(data['speed_mae']) if data['speed_mae'] else None,
                    'sample_size': data['count']
                }
        
        # 時間経過による誤差の傾向
        time_trend = self._analyze_error_trend()
        
        # サンプルサイズ
        sample_size = len(self.evaluation_history)
        
        # 全体の成功率
        success_rate = self._calculate_success_rate()
        
        return {
            'status': 'success',
            'sample_size': sample_size,
            'current_scores': current_scores,
            'condition_scores': condition_avg,
            'horizon_scores': horizon_avg,
            'time_trend': time_trend,
            'success_rate': success_rate,
            'last_update': datetime.now()
        }
    
    def _update_current_scores(self):
        """
        現在の評価スコアを最新の評価履歴から更新
        """
        if not self.evaluation_history:
            return
        
        # 最新の30評価（または全て）を使用
        recent_evals = list(self.evaluation_history)[-30:]
        
        # 風向の平均絶対誤差
        self.current_scores['direction_mae'] = np.mean([e['direction_abs_error'] for e in recent_evals])
        
        # 風速の平均絶対誤差
        self.current_scores['speed_mae'] = np.mean([e['speed_abs_error'] for e in recent_evals])
        
        # 風向のバイアス
        self.current_scores['direction_bias'] = np.mean([e['direction_error'] for e in recent_evals])
        
        # 風速のバイアス
        self.current_scores['speed_bias'] = np.mean([e['speed_error'] for e in recent_evals])
        
        # 予測成功率
        self.current_scores['prediction_success'] = np.mean([e['prediction_success'] for e in recent_evals])
    
    def _analyze_error_trend(self) -> Dict[str, Any]:
        """
        誤差の時間的傾向を分析
        
        Returns:
        --------
        Dict[str, Any]
            誤差傾向の分析結果
        """
        if len(self.evaluation_history) < 10:
            return {'status': 'Insufficient data for trend analysis'}
        
        # 全評価をホライズンでグループ化
        horizon_groups = {
            'short': [],   # 5分以内
            'medium': [],  # 5-15分
            'long': []     # 15分以上
        }
        
        for eval_data in self.evaluation_history:
            horizon_seconds = eval_data['horizon_seconds']
            if horizon_seconds <= 300:
                horizon_groups['short'].append(eval_data)
            elif horizon_seconds <= 900:
                horizon_groups['medium'].append(eval_data)
            else:
                horizon_groups['long'].append(eval_data)
        
        # 各グループの平均誤差
        trend_result = {}
        for horizon, evals in horizon_groups.items():
            if evals:
                trend_result[horizon] = {
                    'direction_mae': np.mean([e['direction_abs_error'] for e in evals]),
                    'speed_mae': np.mean([e['speed_abs_error'] for e in evals]),
                    'sample_size': len(evals)
                }
        
        # 誤差と予測ホライズンの相関
        horizons = [e['horizon_seconds'] for e in self.evaluation_history]
        dir_errors = [e['direction_abs_error'] for e in self.evaluation_history]
        speed_errors = [e['speed_abs_error'] for e in self.evaluation_history]
        
        dir_correlation = np.corrcoef(horizons, dir_errors)[0, 1] if len(horizons) > 1 else 0
        speed_correlation = np.corrcoef(horizons, speed_errors)[0, 1] if len(horizons) > 1 else 0
        
        trend_result['correlation'] = {
            'direction_horizon_corr': dir_correlation,
            'speed_horizon_corr': speed_correlation
        }
        
        return trend_result
    
    def _calculate_success_rate(self) -> Dict[str, float]:
        """
        予測成功率を計算
        
        Returns:
        --------
        Dict[str, float]
            成功率の詳細
        """
        if not self.evaluation_history:
            return {'overall': 0.0}
        
        # 最新の30評価（または全て）を使用
        recent_evals = list(self.evaluation_history)[-30:]
        
        # 全体の成功率
        overall_rate = np.mean([e['prediction_success'] for e in recent_evals])
        
        # 方向のみの成功率（15度以内）
        direction_rate = np.mean([1 if e['direction_abs_error'] <= 15 else 0 for e in recent_evals])
        
        # 速度のみの成功率（2ノット以内）
        speed_rate = np.mean([1 if e['speed_abs_error'] <= 2 else 0 for e in recent_evals])
        
        return {
            'overall': overall_rate,
            'direction_only': direction_rate,
            'speed_only': speed_rate
        }
    
    def _calculate_angle_difference(self, angle1: float, angle2: float) -> float:
        """
        2つの角度の差を計算（-180〜180度の範囲）
        
        Parameters:
        -----------
        angle1, angle2 : float
            角度（度）
            
        Returns:
        --------
        float
            角度差（度、-180〜180）
        """
        diff = (angle1 - angle2 + 180) % 360 - 180
        return diff
    
    def reset_statistics(self):
        """
        統計データをリセット
        """
        self.evaluation_history.clear()
        
        # 最新の評価スコア
        self.current_scores = {
            'direction_mae': None,
            'speed_mae': None,
            'direction_bias': None,
            'speed_bias': None,
            'prediction_success': None
        }
        
        # 条件別の累積スコア
        for condition in self.condition_scores:
            self.condition_scores[condition] = {'direction_mae': [], 'speed_mae': [], 'count': 0}
        
        # 予測ホライズン別のスコア
        for horizon in self.horizon_scores:
            self.horizon_scores[horizon] = {'direction_mae': [], 'speed_mae': [], 'count': 0}
