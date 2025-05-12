# -*- coding: utf-8 -*-
"""
sailing_data_processor.boat_fusion.boat_data_fusion_analysis モジュール

船舶データの分析機能を提供します。
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union, Any
from datetime import datetime, timedelta
import math

def calc_boat_reliability(model, boat_id: str, wind_estimates: pd.DataFrame) -> float:
    """
    各艇の信頼性係数を計算（艇のスキル、データの一貫性、過去の履歴に基づく）
    
    Parameters:
    -----------
    model : BoatDataFusionModel
        モデルインスタンス
    boat_id : str
        艇ID
    wind_estimates : pd.DataFrame
        艇の風向風速推定データ
        
    Returns:
    --------
    float
        信頼性係数（0.0〜1.0）
    """
    # 基本信頼係数はスキルレベル（未設定の場合は中央値0.5）
    base_reliability = model.boat_skill_levels.get(boat_id, 0.5)
    
    # データの一貫性を評価
    consistency_score = 0.7  # デフォルト値
    
    if len(wind_estimates) > 2:
        # 風向と風速の標準偏差を計算
        dir_std = np.std(wind_estimates['wind_direction'])
        speed_std = np.std(wind_estimates['wind_speed_knots'])
        
        # 風向の一貫性（循環データなので特殊処理）
        sin_vals = np.sin(np.radians(wind_estimates['wind_direction']))
        cos_vals = np.cos(np.radians(wind_estimates['wind_direction']))
        r_mean = math.sqrt(np.mean(sin_vals)**2 + np.mean(cos_vals)**2)
        
        # r_meanは0（完全にランダム）から1（完全に一定）の範囲
        dir_consistency = r_mean
        
        # 風速の変動係数（標準偏差/平均）
        if wind_estimates['wind_speed_knots'].mean() > 0:
            speed_cv = speed_std / wind_estimates['wind_speed_knots'].mean()
            speed_consistency = max(0, 1 - speed_cv / 0.5)  # 変動係数0.5以上で信頼性0
        else:
            speed_consistency = 0.5
        
        # 総合一貫性スコア
        consistency_score = 0.7 * dir_consistency + 0.3 * speed_consistency
    
    # 過去の推定履歴との一致度
    history_score = 0.8  # デフォルト値
    
    if model.estimation_history and len(wind_estimates) > 0:
        latest_estimate = wind_estimates.iloc[-1]
        
        # 最新の推定と過去の推定との差異
        deviations = []
        
        for hist_entry in model.estimation_history[-5:]:  # 最新5件を使用
            # 時間差（分）
            time_diff_minutes = (latest_estimate['timestamp'] - hist_entry['timestamp']).total_seconds() / 60
            if abs(time_diff_minutes) > 30:  # 30分以上離れた履歴は使用しない
                continue
            
            # 風向の差（循環性を考慮）
            dir_diff = abs((latest_estimate['wind_direction'] - hist_entry['wind_direction'] + 180) % 360 - 180)
            
            # 風速の差
            speed_diff = abs(latest_estimate['wind_speed_knots'] - hist_entry['wind_speed_knots'])
            
            # 時間経過を考慮した差異を計算
            expected_dir_change = model.direction_time_change * abs(time_diff_minutes)
            expected_speed_change = model.speed_time_change * abs(time_diff_minutes)
            
            adjusted_dir_diff = max(0, dir_diff - expected_dir_change)
            adjusted_speed_diff = max(0, speed_diff - expected_speed_change)
            
            # 正規化スコア
            if hist_entry['wind_speed_knots'] > 0:
                norm_dir_score = max(0, 1 - adjusted_dir_diff / 45)  # 45度以上の差で0点
                norm_speed_score = max(0, 1 - adjusted_speed_diff / (hist_entry['wind_speed_knots'] * 0.3))  # 30%以上の差で0点
            else:
                norm_dir_score = max(0, 1 - adjusted_dir_diff / 45)
                norm_speed_score = max(0, 1 - adjusted_speed_diff / 3)  # 3ノット以上の差で0点
            
            deviations.append(0.7 * norm_dir_score + 0.3 * norm_speed_score)
        
        if deviations:
            history_score = np.mean(deviations)
    
    # 総合信頼性スコア
    reliability = 0.4 * base_reliability + 0.4 * consistency_score + 0.2 * history_score
    
    # 艇種の特性を考慮した調整
    if boat_id in model.boat_types:
        boat_type = model.boat_types[boat_id]
        if boat_type in model.boat_type_characteristics:
            # 総合的な艇種性能スコア
            type_score = np.mean([
                model.boat_type_characteristics[boat_type]['upwind_efficiency'],
                model.boat_type_characteristics[boat_type]['downwind_efficiency'],
                model.boat_type_characteristics[boat_type]['pointing_ability']
            ])
            
            # 信頼性スコアを艇種性能で微調整
            reliability *= (0.9 + 0.2 * (type_score - 1.0))
    
    # 0.0〜1.0の範囲に制限
    return max(0.0, min(1.0, reliability))
