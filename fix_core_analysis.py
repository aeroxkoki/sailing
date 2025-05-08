#\!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
core_analysis.pyファイルを修正する
"""

import os
import sys

def replace_core_analysis():
    """core_analysis.pyファイルを既知の正しい内容で置き換える"""
    file_path = 'sailing_data_processor/core_analysis.py'
    
    # 正しい内容
    content = """# -*- coding: utf-8 -*-
# sailing_data_processor/core_analysis.py
\"\"\"
セーリングデータ分析の基本モジュール

SailingDataAnalyzerクラスを提供し、GPSデータからの分析機能を実装します。
\"\"\"

from typing import Dict, List, Tuple, Optional, Union, Any
import pandas as pd
import numpy as np
import gc
from datetime import datetime, timedelta
import logging
import math

# ロギング設定
logger = logging.getLogger(__name__)


class SailingDataAnalyzer:
    \"\"\"セーリングデータ分析の基本クラス\"\"\"
    
    def __init__(self):
        \"\"\"初期化\"\"\"
        # 分析データの保存
        self.processed_data = {}  # 前処理済みデータ
        self.wind_estimates = {}  # 風推定結果
        self.wind_field_data = {}  # 風場データ
        self.strategy_points = {}  # 戦略ポイント
        
        # 分析設定
        self.analysis_config = {
            "wind_estimation": {
                "method": "tack_based",  # tack_based, vmg_based, combined
                "smoothing": 0.5,  # スムージング係数（0-1）
                "confidence_threshold": 0.7  # 信頼度閾値
            },
            "strategy_detection": {
                "sensitivity": 0.7,  # 検出感度（0-1）
                "min_angle_change": 45.0,  # 最小角度変化（度）
                "min_speed_change": 1.0,  # 最小速度変化（ノット）
                "window_size": 5  # 分析ウィンドウサイズ
            },
            "performance_analysis": {
                "use_polar": True,  # ポーラー曲線を使用するか
                "optimum_vmg_upwind": 40.0,  # 最適風上VMG角度（度）
                "optimum_vmg_downwind": 150.0  # 最適風下VMG角度（度）
            }
        }

    def analyze_wind(self, boat_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        \"\"\"
        複数艇のデータから風向風速を推定する
        
        Parameters:
        -----------
        boat_data : Dict[str, pd.DataFrame]
            艇ID: データフレームの辞書
            
        Returns:
        --------
        Dict[str, Any]
            風推定結果
        \"\"\"
        if not boat_data:
            return {"error": "データがありません"}
        
        method = self.analysis_config["wind_estimation"]["method"]
        
        try:
            # 各艇からの風推定値を取得
            boat_wind_estimates = {}
            
            for boat_id, df in boat_data.items():
                # 基本的な前処理
                if 'speed' not in df.columns or df['speed'].isna().all():
                    logger.warning(f"艇 {boat_id} は速度データがないため、風推定から除外します")
                    continue
                    
                if 'course' not in df.columns or df['course'].isna().all():
                    logger.warning(f"艇 {boat_id} は方位データがないため、風推定から除外します")
                    continue
                
                # 風推定メソッドに基づいて推定
                if method == "tack_based":
                    wind_estimate = self._estimate_wind_from_tacks(df)
                elif method == "vmg_based":
                    wind_estimate = self._estimate_wind_from_vmg(df)
                else:  # combined
                    tack_estimate = self._estimate_wind_from_tacks(df)
                    vmg_estimate = self._estimate_wind_from_vmg(df)
                    
                    # 両方の推定値を統合
                    if "error" not in tack_estimate and "error" not in vmg_estimate:
                        wind_direction = (tack_estimate["direction"] + vmg_estimate["direction"]) / 2
                        wind_speed = (tack_estimate["speed"] + vmg_estimate["speed"]) / 2
                        wind_estimate = {
                            "direction": wind_direction,
                            "speed": wind_speed,
                            "confidence": min(tack_estimate["confidence"], vmg_estimate["confidence"])
                        }
                    elif "error" not in tack_estimate:
                        wind_estimate = tack_estimate
                    elif "error" not in vmg_estimate:
                        wind_estimate = vmg_estimate
                    else:
                        wind_estimate = {"error": "両方の風推定メソッドが失敗しました"}
                
                if "error" not in wind_estimate:
                    boat_wind_estimates[boat_id] = wind_estimate
            
            if not boat_wind_estimates:
                return {"error": "風推定に使用できるデータがありません"}
            
            # 複数艇からの推定値を統合
            combined_wind = self._combine_wind_estimates(boat_wind_estimates)
            
            # 推定結果を保存
            self.wind_estimates = combined_wind
            
            return {
                "wind": combined_wind,
                "method": method,
                "boat_estimates": boat_wind_estimates
            }
            
        except Exception as e:
            error_msg = f"風推定中にエラーが発生しました: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {"error": error_msg}
    
    def _estimate_wind_from_tacks(self, df: pd.DataFrame) -> Dict[str, Any]:
        \"\"\"
        タック点から風向風速を推定する内部メソッド
        
        Parameters:
        -----------
        df : pd.DataFrame
            GPSデータ
            
        Returns:
        --------
        Dict[str, Any]
            風推定結果
        \"\"\"
        # コースの差分を計算して大きな方位変化を検出
        course_diff = df['course'].diff().abs()
        
        # タック点の検出（大きな方位変化）
        min_angle_change = self.analysis_config["strategy_detection"]["min_angle_change"]
        tack_indices = course_diff[course_diff > min_angle_change].index
        
        if len(tack_indices) < 3:
            # タックが少なすぎて信頼性の高い風向推定ができない
            return {"error": "タックが少なすぎます（3回以上必要）"}
        
        # タック前後の艇の方位から風向を推定
        wind_directions = []
        confidence_values = []
        
        for idx in tack_indices:
            idx_pos = df.index.get_loc(idx)
            
            # インデックスが範囲外にならないように確認
            if idx_pos < 2 or idx_pos >= len(df) - 2:
                continue
                
            # タック前後の方位
            pre_tack_idx = df.index[idx_pos - 2]
            post_tack_idx = df.index[idx_pos + 2]
            
            pre_course = df.loc[pre_tack_idx, 'course']
            post_course = df.loc[post_tack_idx, 'course']
            
            # 方位差を計算（-180〜180度に正規化）
            course_change = ((post_course - pre_course + 180) % 360) - 180
            
            # タックの場合（概ね90度以上の方位変化）
            if abs(course_change) >= 90:
                # 両方の方位の中間が風向の候補（±90度）
                # 風上方向への変化なのでタックと判定
                mid_course = (pre_course + post_course) / 2
                
                # コース変化の方向に応じて風向を推定
                if course_change > 0:
                    wind_dir = (mid_course + 90) % 360
                else:
                    wind_dir = (mid_course - 90) % 360
                
                # 信頼度（タックの鋭さに基づく）
                confidence = min(1.0, abs(course_change) / 180.0)
                
                wind_directions.append(wind_dir)
                confidence_values.append(confidence)
        
        if not wind_directions:
            return {"error": "有効なタックが検出できませんでした"}
        
        # 風向の平均（円環統計）
        sin_sum = sum(np.sin(np.radians(wd)) * conf for wd, conf in zip(wind_directions, confidence_values))
        cos_sum = sum(np.cos(np.radians(wd)) * conf for wd, conf in zip(wind_directions, confidence_values))
        
        if sin_sum == 0 and cos_sum == 0:
            avg_wind_direction = 0
        else:
            avg_wind_direction = (np.degrees(np.arctan2(sin_sum, cos_sum)) + 360) % 360
        
        # 風速の推定（船の速度から概算）
        # タック前後の速度差から風速を推定（簡易的）
        speed_diffs = []
        
        for idx in tack_indices:
            idx_pos = df.index.get_loc(idx)
            
            # インデックスが範囲外にならないように確認
            if idx_pos < 3 or idx_pos >= len(df) - 3:
                continue
                
            # タック前後の速度
            pre_speed_idx = df.index[idx_pos - 3]
            post_speed_idx = df.index[idx_pos + 3]
            
            pre_speed = df.loc[pre_speed_idx, 'speed']
            post_speed = df.loc[post_speed_idx, 'speed']
            
            # 速度差の絶対値
            speed_diff = abs(post_speed - pre_speed)
            speed_diffs.append(speed_diff)
        
        # 風速推定（簡易的なアプローチ）
        if speed_diffs:
            # タック前後の速度差の平均の2倍程度が風速の目安
            estimated_wind_speed = min(40.0, max(3.0, np.mean(speed_diffs) * 2.5))
        else:
            # デフォルト値
            estimated_wind_speed = 10.0
        
        # 全体の信頼度
        overall_confidence = min(1.0, len(wind_directions) / 10.0)
        
        return {
            "direction": avg_wind_direction,
            "speed": estimated_wind_speed,
            "confidence": overall_confidence,
            "tack_points": len(wind_directions),
            "method": "tack_based"
        }
    
    def _estimate_wind_from_vmg(self, df: pd.DataFrame) -> Dict[str, Any]:
        \"\"\"
        VMG分析から風向風速を推定する内部メソッド
        
        Parameters:
        -----------
        df : pd.DataFrame
            GPSデータ
            
        Returns:
        --------
        Dict[str, Any]
            風推定結果
        \"\"\"
        if len(df) < 100:
            return {"error": "データポイントが不足しています"}
        
        # 方位ごとの速度分布を分析
        # 10度ごとにビンを作成
        course_bins = {}
        for i in range(0, 36):
            bin_center = i * 10
            bin_min = (bin_center - 5) % 360
            bin_max = (bin_center + 5) % 360
            
            # 該当ビン内のデータを抽出
            if bin_min < bin_max:
                bin_data = df[(df['course'] >= bin_min) & (df['course'] < bin_max)]
            else:  # 360度の境界をまたぐ場合
                bin_data = df[(df['course'] >= bin_min) | (df['course'] < bin_max)]
            
            if len(bin_data) >= 5:  # 十分なデータがある場合のみ
                avg_speed = bin_data['speed'].mean()
                course_bins[bin_center] = avg_speed
        
        if len(course_bins) < 12:  # 少なくとも1/3の方位をカバーする必要あり
            return {"error": "方位データの分布が不十分です"}
        
        # VMGの対称性から風向を推定
        best_wind_dir = 0
        best_symmetry = float('-inf')
        
        for test_wind_dir in range(0, 360, 5):
            # 各方位のVMGを計算
            vmg_values = {}
            for course, speed in course_bins.items():
                # 風に対する相対角度
                relative_angle = ((course - test_wind_dir + 180) % 360) - 180
                
                # VMG計算（風上・風下方向の速度成分）
                vmg = speed * np.cos(np.radians(relative_angle))
                vmg_values[relative_angle] = vmg
            
            # 対称性スコアの計算
            symmetry_score = 0
            point_count = 0
            
            for angle, vmg in vmg_values.items():
                # 対称的な角度（反対側）
                opposite_angle = -angle if angle \!= 0 else 180
                
                # 最も近い角度を探す
                closest_opp = None
                min_diff = 20  # 20度以内の角度を探す
                
                for test_angle in vmg_values.keys():
                    angle_diff = abs(test_angle - opposite_angle)
                    if angle_diff < min_diff:
                        min_diff = angle_diff
                        closest_opp = test_angle
                
                if closest_opp is not None:
                    # VMGの対称性を評価（風上と風下で正負が逆）
                    opp_vmg = vmg_values[closest_opp]
                    similarity = -vmg * opp_vmg  # 対称的ならば正の値
                    
                    symmetry_score += similarity
                    point_count += 1
            
            # 正規化
            if point_count > 0:
                symmetry_score /= point_count
                
                if symmetry_score > best_symmetry:
                    best_symmetry = symmetry_score
                    best_wind_dir = test_wind_dir
        
        # 風速の推定（最大・最小速度の比から）
        speed_values = list(course_bins.values())
        max_speed = max(speed_values)
        min_speed = min(speed_values)
        
        # 風速推定（簡易的なアプローチ）
        if max_speed > min_speed:
            # 最大と最小の比率から風速を概算
            speed_ratio = max_speed / min_speed if min_speed > 0 else 2.0
            estimated_wind_speed = max_speed * 0.7 * min(2.0, speed_ratio / 2.0)
            estimated_wind_speed = min(40.0, max(3.0, estimated_wind_speed))
        else:
            # デフォルト値
            estimated_wind_speed = 10.0
        
        # 信頼度の計算
        confidence = min(1.0, best_symmetry / 10.0)
        
        return {
            "direction": best_wind_dir,
            "speed": estimated_wind_speed,
            "confidence": max(0.1, confidence),
            "symmetry_score": best_symmetry,
            "method": "vmg_based"
        }
    
    def _combine_wind_estimates(self, boat_estimates: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        \"\"\"
        複数艇からの風推定値を統合する内部メソッド
        
        Parameters:
        -----------
        boat_estimates : Dict[str, Dict[str, Any]]
            艇ごとの風推定結果
            
        Returns:
        --------
        Dict[str, Any]
            統合された風推定結果
        \"\"\"
        if not boat_estimates:
            return {
                "direction": 0.0,
                "speed": 0.0,
                "confidence": 0.0
            }
        
        if len(boat_estimates) == 1:
            # 1艇のみの場合はそのまま返す
            return list(boat_estimates.values())[0]
        
        # 各艇の風向・風速・信頼度を抽出
        wind_dirs = []
        wind_speeds = []
        confidences = []
        
        for boat_id, estimate in boat_estimates.items():
            wind_dirs.append(estimate["direction"])
            wind_speeds.append(estimate["speed"])
            confidences.append(estimate["confidence"])
        
        # 信頼度による重み付け
        total_confidence = sum(confidences)
        
        if total_confidence > 0:
            # 風向の重み付き平均（円環統計）
            sin_sum = sum(np.sin(np.radians(wd)) * conf for wd, conf in zip(wind_dirs, confidences))
            cos_sum = sum(np.cos(np.radians(wd)) * conf for wd, conf in zip(wind_dirs, confidences))
            
            avg_wind_direction = (np.degrees(np.arctan2(sin_sum, cos_sum)) + 360) % 360
            
            # 風速の重み付き平均
            avg_wind_speed = sum(ws * conf for ws, conf in zip(wind_speeds, confidences)) / total_confidence
            
            # 総合信頼度
            overall_confidence = total_confidence / len(confidences)
        else:
            # 信頼度がすべて0の場合
            avg_wind_direction = np.mean(wind_dirs) % 360
            avg_wind_speed = np.mean(wind_speeds)
            overall_confidence = 0.1
        
        return {
            "direction": avg_wind_direction,
            "speed": avg_wind_speed,
            "confidence": overall_confidence
        }
    
    def cleanup(self):
        \"\"\"メモリをクリーンアップする\"\"\"
        self.processed_data.clear()
        self.wind_estimates.clear()
        self.wind_field_data.clear()
        self.strategy_points.clear()
        gc.collect()
"""
    
    try:
        # ファイルにUTF-8エンコーディングで書き込む
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Successfully replaced {file_path}")
        return True
    except Exception as e:
        print(f"Error replacing {file_path}: {e}")
        return False

if __name__ == "__main__":
    replace_core_analysis()
