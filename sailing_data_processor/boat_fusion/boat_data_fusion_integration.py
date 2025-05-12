# -*- coding: utf-8 -*-
"""
sailing_data_processor.boat_fusion.boat_data_fusion_integration モジュール

船舶データの統合機能を提供します。
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union, Any
from datetime import datetime, timedelta
import math

def fuse_wind_estimates(model, boats_estimates: Dict[str, pd.DataFrame], 
                      time_point: datetime = None) -> Optional[Dict[str, Any]]:
    """
    複数艇からの風向風速推定を融合
    
    Parameters:
    -----------
    model : BoatDataFusionModel
        モデルインスタンス
    boats_estimates : Dict[str, pd.DataFrame]
        艇ID:風向風速推定DataFrameの辞書
    time_point : datetime, optional
        対象時間点（指定がない場合は最新の共通時間）
        
    Returns:
    --------
    Dict[str, Any] or None
        融合された風向風速データと信頼度
    """
    if not boats_estimates or len(boats_estimates) == 0:
        return None
    
    # 時間点の決定
    if time_point is None:
        # 各艇の最後の推定時刻を取得
        all_times = []
        for boat_id, df in boats_estimates.items():
            if 'timestamp' in df.columns and not df.empty:
                all_times.append(df['timestamp'].iloc[-1])
        
        if not all_times:
            return None
        
        # 最も古い「最新」時刻を使用
        time_point = min(all_times)
    
    # 各艇の推定データを収集
    boat_data = []
    
    for boat_id, df in boats_estimates.items():
        if 'timestamp' not in df.columns or df.empty:
            continue
        
        # 指定時間に最も近いデータを探す
        time_diffs = abs((df['timestamp'] - time_point).dt.total_seconds())
        
        if time_diffs.min() <= 60:  # 60秒以内のデータのみ使用
            closest_idx = time_diffs.idxmin()
            
            # データを取得
            wind_dir = df.loc[closest_idx, 'wind_direction']
            wind_speed = df.loc[closest_idx, 'wind_speed_knots']
            confidence = df.loc[closest_idx, 'confidence'] if 'confidence' in df.columns else 0.7
            
            # 位置情報（あれば）
            latitude = df.loc[closest_idx, 'latitude'] if 'latitude' in df.columns else None
            longitude = df.loc[closest_idx, 'longitude'] if 'longitude' in df.columns else None
            
            # 信頼性係数を計算
            reliability = model.calc_boat_reliability(boat_id, df)
            
            # 統合スコア
            combined_weight = confidence * reliability
            
            boat_data.append({
                'boat_id': boat_id,
                'timestamp': df.loc[closest_idx, 'timestamp'],
                'wind_direction': wind_dir,
                'wind_speed_knots': wind_speed,
                'latitude': latitude,
                'longitude': longitude,
                'raw_confidence': confidence,
                'reliability': reliability,
                'weight': combined_weight
            })
    
    if not boat_data:
        return None
    
    # ベイズ更新を使用した風向風速の統合
    integrated_estimate = model._bayesian_wind_integration(boat_data, time_point)
    
    # 履歴に追加
    model.estimation_history.append({
        'timestamp': time_point,
        'wind_direction': integrated_estimate['wind_direction'],
        'wind_speed_knots': integrated_estimate['wind_speed']
    })
    
    # 履歴が長すぎる場合は古いエントリを削除
    if len(model.estimation_history) > 100:
        model.estimation_history = model.estimation_history[-100:]
    
    # 時間変化モデルの更新
    model._update_time_change_model()
    
    return integrated_estimate
