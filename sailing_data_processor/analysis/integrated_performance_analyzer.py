# -*- coding: utf-8 -*-
"""
統合パフォーマンス分析モジュール

このモジュールはセーリングデータからパフォーマンス指標を計算する機能を提供します。
分析ワークフローと連携し、VMG分析、タック・ジャイブ分析、経時分析などの機能を実装します。
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Tuple, Any, Optional, Union
import time
from datetime import datetime, timedelta
import math
from functools import lru_cache

from sailing_data_processor.analysis.analysis_parameters import ParametersManager, ParameterNamespace
from sailing_data_processor.analysis.analysis_cache import AnalysisCache
from sailing_data_processor.analysis.integrated_wind_estimator import IntegratedWindEstimator

class IntegratedPerformanceAnalyzer:
    """
    統合パフォーマンス分析クラス
    
    分析ワークフローと連携してセーリングパフォーマンスを分析するための拡張機能を提供します。
    """
    
    def __init__(self, 
                 parameters_manager: Optional[ParametersManager] = None,
                 cache: Optional[AnalysisCache] = None,
                 wind_estimator: Optional[IntegratedWindEstimator] = None):
        """
        初期化
        
        Parameters:
        -----------
        parameters_manager : ParametersManager, optional
            パラメータ管理オブジェクト
        cache : AnalysisCache, optional
            結果キャッシュオブジェクト
        wind_estimator : IntegratedWindEstimator, optional
            風推定オブジェクト
        """
        self.logger = logging.getLogger(__name__)
        self.parameters_manager = parameters_manager
        self.cache = cache
        self.wind_estimator = wind_estimator
        
        # パフォーマンス分析結果
        self.performance_results = {}
        
        # 処理状態
        self.processing_status = {
            "is_processing": False,
            "progress": 0.0,
            "message": "",
            "step": "",
            "start_time": None,
            "end_time": None
        }
    
    def analyze_performance(self, 
                           df: pd.DataFrame, 
                           boat_type: str = "default",
                           use_cache: bool = True) -> Dict[str, Any]:
        """
        総合的なパフォーマンス分析を実行
        
        Parameters:
        -----------
        df : pd.DataFrame
            セーリングデータフレーム
        boat_type : str, optional
            艇種
        use_cache : bool, optional
            キャッシュを使用するかどうか
            
        Returns:
        --------
        Dict[str, Any]
            パフォーマンス分析結果
        """
        # 処理状態の初期化
        self._update_processing_status(True, 0.0, "パフォーマンス分析を開始しています...", "initialize")
        
        # データのバリデーション
        if df is None or df.empty:
            self._update_processing_status(False, 100.0, "データが空です", "error")
            return {"error": "データが空です"}
        
        required_columns = ['timestamp', 'latitude', 'longitude', 'course', 'speed']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            error_msg = f"必要なカラムがありません: {missing_columns}"
            self._update_processing_status(False, 100.0, error_msg, "error")
            return {"error": error_msg}
        
        # キャッシュをチェック
        if use_cache and self.cache:
            # キャッシュキー生成用のパラメータ
            cache_params = {
                "data_hash": self._hash_dataframe(df),
                "boat_type": boat_type
            }
            
            # パラメーターマネージャーがある場合はパラメータも含める
            if self.parameters_manager:
                cache_params["performance_params"] = self.parameters_manager.get_parameters_by_namespace(
                    ParameterNamespace.PERFORMANCE_ANALYSIS
                )
            
            try:
                # キャッシュから分析結果を取得
                cached_result = self.cache.compute_from_params(
                    "performance_analysis",
                    cache_params,
                    lambda params: self._perform_performance_analysis(df, boat_type),
                    ttl=3600  # 1時間キャッシュ
                )
                return cached_result
            except Exception as e:
                self.logger.warning(f"キャッシュ処理中にエラーが発生しました: {e}")
                # キャッシュエラーの場合は直接計算
                return self._perform_performance_analysis(df, boat_type)
        else:
            # キャッシュを使用しない場合は直接計算
            return self._perform_performance_analysis(df, boat_type)
    
    def _perform_performance_analysis(self, df: pd.DataFrame, boat_type: str) -> Dict[str, Any]:
        """
        パフォーマンス分析の実行
        
        Parameters:
        -----------
        df : pd.DataFrame
            セーリングデータフレーム
        boat_type : str
            艇種
            
        Returns:
        --------
        Dict[str, Any]
            パフォーマンス分析結果
        """
        try:
            # まず風推定を実行
            self._update_processing_status(True, 10.0, "風推定を実行しています...", "estimate_wind")
            
            if not self.wind_estimator:
                self._update_processing_status(False, 100.0, "風推定器が利用できません", "error")
                return {"error": "風推定器が利用できません"}
                
            wind_result = self.wind_estimator.estimate_wind(df, boat_type)
            
            if "error" in wind_result:
                self._update_processing_status(False, 100.0, f"風推定エラー: {wind_result['error']}", "error")
                return {"error": f"風推定エラー: {wind_result['error']}"}
            
            # データの前処理
            self._update_processing_status(True, 20.0, "データを前処理しています...", "preprocess_data")
            
            processed_df = self._preprocess_data(df, wind_result)
            
            # 基本統計の計算
            self._update_processing_status(True, 30.0, "基本統計を計算しています...", "compute_basic_stats")
            
            basic_stats = self._compute_basic_statistics(processed_df)
            
            # VMG分析
            self._update_processing_status(True, 50.0, "VMG分析を実行しています...", "analyze_vmg")
            
            vmg_analysis = self._analyze_vmg(processed_df, wind_result, boat_type)
            
            # タック・ジャイブパフォーマンス分析
            self._update_processing_status(True, 70.0, "タック・ジャイブ分析を実行しています...", "analyze_maneuvers")
            
            maneuver_analysis = self._analyze_maneuvers(processed_df, wind_result)
            
            # パフォーマンス時系列分析
            self._update_processing_status(True, 85.0, "時系列パフォーマンス分析を実行しています...", "analyze_time_series")
            
            time_series = self._analyze_performance_time_series(processed_df)
            
            # 結果のフォーマット
            self._update_processing_status(True, 95.0, "結果を集計しています...", "format_results")
            
            # パフォーマンススコアの計算
            overall_score = self._calculate_overall_performance_score(
                basic_stats, vmg_analysis, maneuver_analysis
            )
            
            result = {
                "basic_stats": basic_stats,
                "vmg_analysis": vmg_analysis,
                "maneuver_analysis": maneuver_analysis,
                "time_series": time_series,
                "overall_performance": {
                    "score": overall_score,
                    "rating": self._score_to_rating(overall_score),
                    "summary": self._generate_performance_summary(
                        overall_score, basic_stats, vmg_analysis, maneuver_analysis
                    )
                },
                "boat_type": boat_type,
                "wind": {
                    "direction": wind_result["wind"]["direction"],
                    "speed": wind_result["wind"]["speed"],
                    "confidence": wind_result["wind"]["confidence"]
                },
                "analysis_timestamp": datetime.now().isoformat()
            }
            
            # 結果を保存
            self.performance_results = result
            
            # 処理完了
            self._update_processing_status(False, 100.0, "パフォーマンス分析が完了しました", "complete")
            
            return result
            
        except Exception as e:
            error_msg = f"パフォーマンス分析中にエラーが発生しました: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self._update_processing_status(False, 100.0, error_msg, "error")
            return {"error": error_msg}
    
    def _preprocess_data(self, df: pd.DataFrame, wind_result: Dict[str, Any]) -> pd.DataFrame:
        """
        分析用にデータを前処理
        
        Parameters:
        -----------
        df : pd.DataFrame
            元のデータフレーム
        wind_result : Dict[str, Any]
            風推定結果
            
        Returns:
        --------
        pd.DataFrame
            前処理済みデータフレーム
        """
        # データのコピーを作成
        processed_df = df.copy()
        
        # タイムスタンプでソート
        processed_df = processed_df.sort_values('timestamp')
        
        # 風向風速情報を追加
        wind_direction = wind_result["wind"]["direction"]
        wind_speed = wind_result["wind"]["speed"]
        
        # 相対風向の計算
        processed_df['rel_wind_angle'] = processed_df['course'].apply(
            lambda course: ((course - wind_direction + 180) % 360) - 180
        )
        
        # 風上・風下・リーチの判定
        processed_df['sailing_mode'] = processed_df['rel_wind_angle'].apply(
            lambda angle: 'upwind' if abs(angle) <= 45 else 
                         ('downwind' if abs(angle) >= 135 else 'reach')
        )
        
        # 風上・風下方向のVMG計算
        processed_df['upwind_vmg'] = processed_df.apply(
            lambda row: row['speed'] * np.cos(np.radians(row['rel_wind_angle'])) 
            if row['sailing_mode'] == 'upwind' else np.nan, 
            axis=1
        )
        
        processed_df['downwind_vmg'] = processed_df.apply(
            lambda row: row['speed'] * np.cos(np.radians(180 - abs(row['rel_wind_angle']))) 
            if row['sailing_mode'] == 'downwind' else np.nan, 
            axis=1
        )
        
        # 加速度と回頭角速度
        processed_df['speed_diff'] = processed_df['speed'].diff()
        processed_df['course_diff'] = processed_df['course'].diff().apply(
            lambda x: ((x + 180) % 360) - 180  # -180〜180の範囲に正規化
        )
        
        # 時間間隔の計算（秒単位）
        processed_df['time_diff'] = processed_df['timestamp'].diff().dt.total_seconds()
        
        # 加速度（ノット/秒）と回頭角速度（度/秒）
        processed_df['acceleration'] = processed_df['speed_diff'] / processed_df['time_diff']
        processed_df['turning_rate'] = processed_df['course_diff'] / processed_df['time_diff']
        
        # 無効な値を処理（最初の行など）
        processed_df.loc[processed_df['time_diff'].isna(), ['acceleration', 'turning_rate']] = 0
        
        # 風の情報を追加
        processed_df['wind_direction'] = wind_direction
        processed_df['wind_speed'] = wind_speed
        
        return processed_df
    
    def _compute_basic_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        基本統計量を計算
        
        Parameters:
        -----------
        df : pd.DataFrame
            データフレーム
            
        Returns:
        --------
        Dict[str, Any]
            基本統計情報
        """
        # データが不足している場合
        if len(df) < 10:
            return {
                "data_points": len(df),
                "insufficient_data": True
            }
        
        # 基本統計
        stats = {
            "data_points": len(df),
            "duration_seconds": (df['timestamp'].max() - df['timestamp'].min()).total_seconds(),
            "speed": {
                "mean": float(df['speed'].mean()),
                "max": float(df['speed'].max()),
                "min": float(df['speed'].min()),
                "std": float(df['speed'].std()),
                "median": float(df['speed'].median()),
                "percentile_75": float(df['speed'].quantile(0.75)),
                "percentile_90": float(df['speed'].quantile(0.9)),
            },
            "vmg": {
                "upwind_mean": float(df['upwind_vmg'].dropna().mean()) if not df['upwind_vmg'].dropna().empty else None,
                "upwind_max": float(df['upwind_vmg'].max()) if not df['upwind_vmg'].dropna().empty else None,
                "downwind_mean": float(df['downwind_vmg'].dropna().mean()) if not df['downwind_vmg'].dropna().empty else None,
                "downwind_max": float(df['downwind_vmg'].max()) if not df['downwind_vmg'].dropna().empty else None
            },
            "sailing_mode_time": {
                "upwind_seconds": float(df[df['sailing_mode'] == 'upwind']['time_diff'].sum()),
                "reach_seconds": float(df[df['sailing_mode'] == 'reach']['time_diff'].sum()),
                "downwind_seconds": float(df[df['sailing_mode'] == 'downwind']['time_diff'].sum())
            },
            "maneuvers": {
                "tack_count": 0,  # タック数は別途計算
                "gybe_count": 0   # ジャイブ数は別途計算
            }
        }
        
        # セーリングモードの時間比率
        total_time = stats["sailing_mode_time"]["upwind_seconds"] + \
                    stats["sailing_mode_time"]["reach_seconds"] + \
                    stats["sailing_mode_time"]["downwind_seconds"]
                    
        if total_time > 0:
            stats["sailing_mode_percentage"] = {
                "upwind": stats["sailing_mode_time"]["upwind_seconds"] / total_time * 100,
                "reach": stats["sailing_mode_time"]["reach_seconds"] / total_time * 100,
                "downwind": stats["sailing_mode_time"]["downwind_seconds"] / total_time * 100
            }
        else:
            stats["sailing_mode_percentage"] = {
                "upwind": 0,
                "reach": 0,
                "downwind": 0
            }
        
        # 距離の計算（海里）
        distance = self._calculate_total_distance(df)
        stats["distance_nm"] = distance
        
        return stats
    
    def _analyze_vmg(self, df: pd.DataFrame, wind_result: Dict[str, Any], boat_type: str) -> Dict[str, Any]:
        """
        VMG（Velocity Made Good）分析
        
        Parameters:
        -----------
        df : pd.DataFrame
            データフレーム
        wind_result : Dict[str, Any]
            風推定結果
        boat_type : str
            艇種
            
        Returns:
        --------
        Dict[str, Any]
            VMG分析結果
        """
        # データが足りない場合
        upwind_data = df[df['sailing_mode'] == 'upwind']
        downwind_data = df[df['sailing_mode'] == 'downwind']
        
        if len(upwind_data) < 10 and len(downwind_data) < 10:
            return {
                "insufficient_data": True,
                "upwind_data_points": len(upwind_data),
                "downwind_data_points": len(downwind_data)
            }
        
        # 風速
        wind_speed = wind_result["wind"]["speed"]
        
        # ポーラー曲線から最適VMG角度と速度を取得
        optimal_vmg = self.wind_estimator.get_optimal_vmg_angles(wind_speed, boat_type) if self.wind_estimator else None
        
        # VMG分析結果
        vmg_analysis = {
            "upwind": {
                "data_points": len(upwind_data),
                "mean_vmg": float(upwind_data['upwind_vmg'].mean()) if not upwind_data.empty else None,
                "max_vmg": float(upwind_data['upwind_vmg'].max()) if not upwind_data.empty else None,
                "mean_angle": float(upwind_data['rel_wind_angle'].abs().mean()) if not upwind_data.empty else None,
                "optimal_vmg": optimal_vmg.get("upwind_vmg") if optimal_vmg else None,
                "optimal_angle": optimal_vmg.get("upwind_angle") if optimal_vmg else None,
                "performance_ratio": None  # 後で計算
            },
            "downwind": {
                "data_points": len(downwind_data),
                "mean_vmg": float(downwind_data['downwind_vmg'].mean()) if not downwind_data.empty else None,
                "max_vmg": float(downwind_data['downwind_vmg'].max()) if not downwind_data.empty else None,
                "mean_angle": float(downwind_data['rel_wind_angle'].abs().mean()) if not downwind_data.empty else None,
                "optimal_vmg": optimal_vmg.get("downwind_vmg") if optimal_vmg else None,
                "optimal_angle": optimal_vmg.get("downwind_angle") if optimal_vmg else None,
                "performance_ratio": None  # 後で計算
            }
        }
        
        # パフォーマンス比率の計算（実際のVMG / 最適VMG）
        if optimal_vmg:
            if vmg_analysis["upwind"]["max_vmg"] and optimal_vmg.get("upwind_vmg"):
                vmg_analysis["upwind"]["performance_ratio"] = vmg_analysis["upwind"]["max_vmg"] / optimal_vmg.get("upwind_vmg")
                
            if vmg_analysis["downwind"]["max_vmg"] and optimal_vmg.get("downwind_vmg"):
                vmg_analysis["downwind"]["performance_ratio"] = vmg_analysis["downwind"]["max_vmg"] / optimal_vmg.get("downwind_vmg")
        
        # VMG角度の分布
        if not upwind_data.empty:
            vmg_analysis["upwind"]["angle_distribution"] = self._calculate_angle_distribution(upwind_data['rel_wind_angle'])
            
        if not downwind_data.empty:
            vmg_analysis["downwind"]["angle_distribution"] = self._calculate_angle_distribution(downwind_data['rel_wind_angle'])
        
        return vmg_analysis
    
    def _analyze_maneuvers(self, df: pd.DataFrame, wind_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        タック・ジャイブなどのマニューバー分析
        
        Parameters:
        -----------
        df : pd.DataFrame
            データフレーム
        wind_result : Dict[str, Any]
            風推定結果
            
        Returns:
        --------
        Dict[str, Any]
            マニューバー分析結果
        """
        # マニューバー情報
        maneuvers = wind_result.get("detected_maneuvers", [])
        
        if not maneuvers:
            return {
                "maneuver_count": 0,
                "insufficient_data": True
            }
        
        # マニューバータイプのカウント
        tack_count = sum(1 for m in maneuvers if m.get('maneuver_type') == 'tack')
        gybe_count = sum(1 for m in maneuvers if m.get('maneuver_type') == 'jibe')
        unknown_count = sum(1 for m in maneuvers if m.get('maneuver_type') == 'unknown')
        
        # タックの分析
        tacks = [m for m in maneuvers if m.get('maneuver_type') == 'tack']
        gybes = [m for m in maneuvers if m.get('maneuver_type') == 'jibe']
        
        # マニューバー分析結果
        maneuver_analysis = {
            "maneuver_count": len(maneuvers),
            "tack_count": tack_count,
            "gybe_count": gybe_count,
            "unknown_count": unknown_count,
            "tacks": {
                "avg_duration": np.mean([t.get('maneuver_duration', 0) for t in tacks]) if tacks else None,
                "min_duration": min([t.get('maneuver_duration', float('inf')) for t in tacks]) if tacks else None,
                "max_duration": max([t.get('maneuver_duration', 0) for t in tacks]) if tacks else None,
                "avg_speed_loss": np.mean([1.0 - t.get('speed_ratio', 1.0) for t in tacks]) if tacks else None
            },
            "gybes": {
                "avg_duration": np.mean([g.get('maneuver_duration', 0) for g in gybes]) if gybes else None,
                "min_duration": min([g.get('maneuver_duration', float('inf')) for g in gybes]) if gybes else None,
                "max_duration": max([g.get('maneuver_duration', 0) for g in gybes]) if gybes else None,
                "avg_speed_loss": np.mean([1.0 - g.get('speed_ratio', 1.0) for g in gybes]) if gybes else None
            }
        }
        
        # マニューバーの時系列分布
        if maneuvers:
            # タイムスタンプのリスト
            maneuver_times = []
            for m in maneuvers:
                if 'timestamp' in m:
                    ts = m['timestamp']
                    if isinstance(ts, str):
                        try:
                            ts = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                        except ValueError:
                            continue
                    maneuver_times.append(ts)
            
            if maneuver_times:
                maneuver_analysis["time_distribution"] = self._calculate_time_distribution(maneuver_times)
        
        return maneuver_analysis
    
    def _analyze_performance_time_series(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        時系列のパフォーマンス分析
        
        Parameters:
        -----------
        df : pd.DataFrame
            データフレーム
            
        Returns:
        --------
        Dict[str, Any]
            時系列分析結果
        """
        if len(df) < 10:
            return {
                "insufficient_data": True
            }
        
        # 分析のウィンドウサイズを設定
        window_size = 10  # デフォルト値
        if self.parameters_manager:
            params = self.parameters_manager.get_parameters_by_namespace(ParameterNamespace.PERFORMANCE_ANALYSIS)
            window_size = params.get("performance_window_size", 10)
        
        # 移動平均でスムージング
        smoothed_df = df.copy()
        smoothed_df['speed_smooth'] = df['speed'].rolling(window=window_size, center=True).mean()
        
        # 風上/風下モードでのVMG移動平均
        upwind_mask = df['sailing_mode'] == 'upwind'
        downwind_mask = df['sailing_mode'] == 'downwind'
        
        # 風上VMGの移動平均（風上モードの時のみ）
        smoothed_df.loc[upwind_mask, 'upwind_vmg_smooth'] = \
            df.loc[upwind_mask, 'upwind_vmg'].rolling(window=window_size, center=True).mean()
        
        # 風下VMGの移動平均（風下モードの時のみ）
        smoothed_df.loc[downwind_mask, 'downwind_vmg_smooth'] = \
            df.loc[downwind_mask, 'downwind_vmg'].rolling(window=window_size, center=True).mean()
        
        # 時系列データの間引き（データ量が多い場合）
        if len(smoothed_df) > 1000:
            # 1000ポイントになるように均等にサンプリング
            indices = np.linspace(0, len(smoothed_df) - 1, 1000).astype(int)
            sampled_df = smoothed_df.iloc[indices]
        else:
            sampled_df = smoothed_df
        
        # 時系列データの準備
        timestamp_iso = [ts.isoformat() for ts in sampled_df['timestamp']]
        
        time_series = {
            "timestamps": timestamp_iso,
            "speed": sampled_df['speed_smooth'].tolist(),
            "course": sampled_df['course'].tolist(),
            "rel_wind_angle": sampled_df['rel_wind_angle'].tolist(),
            "sailing_mode": sampled_df['sailing_mode'].tolist(),
            "upwind_vmg": sampled_df['upwind_vmg_smooth'].tolist(),
            "downwind_vmg": sampled_df['downwind_vmg_smooth'].tolist(),
            "window_size": window_size
        }
        
        return time_series
    
    def _calculate_overall_performance_score(self, basic_stats: Dict[str, Any], 
                                          vmg_analysis: Dict[str, Any], 
                                          maneuver_analysis: Dict[str, Any]) -> float:
        """
        総合パフォーマンススコアの計算
        
        Parameters:
        -----------
        basic_stats : Dict[str, Any]
            基本統計情報
        vmg_analysis : Dict[str, Any]
            VMG分析結果
        maneuver_analysis : Dict[str, Any]
            マニューバー分析結果
            
        Returns:
        --------
        float
            総合パフォーマンススコア (0-100)
        """
        # データが不足している場合
        if basic_stats.get("insufficient_data", False) or \
           vmg_analysis.get("insufficient_data", False):
            return 50.0  # デフォルト値
        
        # VMGパフォーマンス（最大40点）
        vmg_score = 0
        
        # 風上VMGスコア
        upwind_ratio = vmg_analysis.get("upwind", {}).get("performance_ratio")
        if upwind_ratio:
            # 0.7が70点、0.9が90点になるようにスケーリング
            upwind_score = min(100, max(0, upwind_ratio * 100))
            vmg_score += upwind_score * 0.2  # 20点満点
        
        # 風下VMGスコア
        downwind_ratio = vmg_analysis.get("downwind", {}).get("performance_ratio")
        if downwind_ratio:
            downwind_score = min(100, max(0, downwind_ratio * 100))
            vmg_score += downwind_score * 0.2  # 20点満点
        
        # スピードの一貫性（最大30点）
        speed_consistency = 0
        
        speed_std = basic_stats.get("speed", {}).get("std")
        speed_mean = basic_stats.get("speed", {}).get("mean")
        
        if speed_std is not None and speed_mean is not None and speed_mean > 0:
            # 変動係数（標準偏差/平均）
            cv = speed_std / speed_mean
            
            # 変動係数の評価（小さいほど一貫性が高い）
            # 0.1以下なら満点、0.3以上なら0点
            consistency_score = max(0, min(100, (0.3 - cv) / 0.2 * 100))
            speed_consistency = consistency_score * 0.3  # 30点満点
        
        # マニューバーの効率（最大30点）
        maneuver_efficiency = 0
        
        # タック効率
        tack_data = maneuver_analysis.get("tacks", {})
        if tack_data.get("avg_speed_loss") is not None:
            # スピードロスが少ないほど効率が高い
            # 30%以下のロスなら満点、70%以上のロスなら0点
            tack_efficiency = max(0, min(100, (0.7 - tack_data["avg_speed_loss"]) / 0.4 * 100))
            maneuver_efficiency += tack_efficiency * 0.15  # 15点満点
        
        # ジャイブ効率
        gybe_data = maneuver_analysis.get("gybes", {})
        if gybe_data.get("avg_speed_loss") is not None:
            gybe_efficiency = max(0, min(100, (0.7 - gybe_data["avg_speed_loss"]) / 0.4 * 100))
            maneuver_efficiency += gybe_efficiency * 0.15  # 15点満点
        
        # 総合スコア（100点満点）
        overall_score = vmg_score + speed_consistency + maneuver_efficiency
        
        return overall_score
    
    def _score_to_rating(self, score: float) -> str:
        """
        スコアを評価に変換
        
        Parameters:
        -----------
        score : float
            パフォーマンススコア (0-100)
            
        Returns:
        --------
        str
            評価ラベル
        """
        if score >= 90:
            return "優秀"
        elif score >= 80:
            return "非常に良い"
        elif score >= 70:
            return "良い"
        elif score >= 60:
            return "平均以上"
        elif score >= 50:
            return "平均的"
        elif score >= 40:
            return "改善余地あり"
        elif score >= 30:
            return "平均以下"
        else:
            return "さらなる練習が必要"
    
    def _generate_performance_summary(self, score: float, basic_stats: Dict[str, Any], 
                                    vmg_analysis: Dict[str, Any], 
                                    maneuver_analysis: Dict[str, Any]) -> str:
        """
        パフォーマンスサマリーの生成
        
        Parameters:
        -----------
        score : float
            パフォーマンススコア
        basic_stats : Dict[str, Any]
            基本統計情報
        vmg_analysis : Dict[str, Any]
            VMG分析結果
        maneuver_analysis : Dict[str, Any]
            マニューバー分析結果
            
        Returns:
        --------
        str
            パフォーマンスサマリー
        """
        parts = []
        
        # スコアと評価
        rating = self._score_to_rating(score)
        parts.append(f"全体的なパフォーマンスは{rating}です（{score:.1f}点/100点）。")
        
        # 強み
        strengths = []
        
        # VMGパフォーマンス
        upwind_ratio = vmg_analysis.get("upwind", {}).get("performance_ratio")
        downwind_ratio = vmg_analysis.get("downwind", {}).get("performance_ratio")
        
        if upwind_ratio and upwind_ratio >= 0.8:
            strengths.append("風上での高いVMG効率")
        
        if downwind_ratio and downwind_ratio >= 0.8:
            strengths.append("風下での高いVMG効率")
        
        # スピードの一貫性
        speed_std = basic_stats.get("speed", {}).get("std")
        speed_mean = basic_stats.get("speed", {}).get("mean")
        
        if speed_std is not None and speed_mean is not None and speed_mean > 0:
            cv = speed_std / speed_mean
            if cv <= 0.15:
                strengths.append("高い速度の一貫性")
        
        # タック効率
        tack_data = maneuver_analysis.get("tacks", {})
        if tack_data.get("avg_speed_loss") is not None and tack_data["avg_speed_loss"] <= 0.3:
            strengths.append("効率的なタック（速度損失が少ない）")
        
        # 強みの文を追加
        if strengths:
            parts.append(f"強みは{', '.join(strengths)}です。")
        
        # 改善点
        improvements = []
        
        if upwind_ratio and upwind_ratio < 0.7:
            improvements.append("風上でのVMG向上")
        
        if downwind_ratio and downwind_ratio < 0.7:
            improvements.append("風下でのVMG向上")
        
        if speed_std is not None and speed_mean is not None and speed_mean > 0:
            cv = speed_std / speed_mean
            if cv > 0.25:
                improvements.append("速度の一貫性向上")
        
        if tack_data.get("avg_speed_loss") is not None and tack_data["avg_speed_loss"] > 0.5:
            improvements.append("タック時の速度維持")
        
        gybe_data = maneuver_analysis.get("gybes", {})
        if gybe_data.get("avg_speed_loss") is not None and gybe_data["avg_speed_loss"] > 0.5:
            improvements.append("ジャイブ時の速度維持")
        
        # 改善点の文を追加
        if improvements:
            parts.append(f"向上させるべき点は{', '.join(improvements)}です。")
        
        # 特記事項
        # 風上・風下のバランス
        sailing_mode_pct = basic_stats.get("sailing_mode_percentage", {})
        upwind_pct = sailing_mode_pct.get("upwind", 0)
        downwind_pct = sailing_mode_pct.get("downwind", 0)
        
        if upwind_pct > 70:
            parts.append(f"セーリング時間の{upwind_pct:.1f}%が風上走行で、風下練習が少ないです。")
        elif downwind_pct > 70:
            parts.append(f"セーリング時間の{downwind_pct:.1f}%が風下走行で、風上練習が少ないです。")
        
        # タック回数
        tack_count = maneuver_analysis.get("tack_count", 0)
        if tack_count == 0:
            parts.append("タックが検出されていません。")
        elif tack_count <= 2:
            parts.append(f"タックが{tack_count}回のみ検出されており、より多くのタック練習が必要かもしれません。")
        
        return " ".join(parts)
    
    def analyze_vmg_optimization(self, df: pd.DataFrame, boat_type: str = "default") -> Dict[str, Any]:
        """
        VMG最適化分析
        
        Parameters:
        -----------
        df : pd.DataFrame
            セーリングデータフレーム
        boat_type : str, optional
            艇種
            
        Returns:
        --------
        Dict[str, Any]
            VMG最適化分析結果
        """
        # 処理状態の更新
        self._update_processing_status(True, 0.0, "VMG最適化分析を開始しています...", "initialize")
        
        try:
            # 風推定を実行
            self._update_processing_status(True, 20.0, "風推定を実行しています...", "estimate_wind")
            
            if not self.wind_estimator:
                self._update_processing_status(False, 100.0, "風推定器が利用できません", "error")
                return {"error": "風推定器が利用できません"}
                
            wind_result = self.wind_estimator.estimate_wind(df, boat_type)
            
            if "error" in wind_result:
                self._update_processing_status(False, 100.0, f"風推定エラー: {wind_result['error']}", "error")
                return {"error": f"風推定エラー: {wind_result['error']}"}
            
            # データの前処理
            self._update_processing_status(True, 40.0, "データを前処理しています...", "preprocess_data")
            
            processed_df = self._preprocess_data(df, wind_result)
            
            # 最適VMG角度の計算
            self._update_processing_status(True, 60.0, "最適VMG角度を計算しています...", "calculate_optimal_vmg")
            
            wind_speed = wind_result["wind"]["speed"]
            optimal_vmg = self.wind_estimator.get_optimal_vmg_angles(wind_speed, boat_type)
            
            if not optimal_vmg:
                optimal_vmg = {
                    "upwind_angle": 42.0,       # デフォルト値
                    "upwind_vmg": None,
                    "downwind_angle": 150.0,    # デフォルト値
                    "downwind_vmg": None
                }
            
            # VMG最適化分析
            self._update_processing_status(True, 80.0, "VMG分析を行っています...", "analyze_vmg")
            
            # 風上・風下データの抽出
            upwind_data = processed_df[processed_df['sailing_mode'] == 'upwind']
            downwind_data = processed_df[processed_df['sailing_mode'] == 'downwind']
            
            # 風上VMG分析
            upwind_analysis = self._analyze_vmg_optimization(
                upwind_data, 
                'upwind', 
                optimal_vmg.get("upwind_angle"), 
                optimal_vmg.get("upwind_vmg")
            )
            
            # 風下VMG分析
            downwind_analysis = self._analyze_vmg_optimization(
                downwind_data, 
                'downwind', 
                optimal_vmg.get("downwind_angle"), 
                optimal_vmg.get("downwind_vmg")
            )
            
            # 結果の作成
            self._update_processing_status(True, 95.0, "結果を集計しています...", "format_results")
            
            result = {
                "wind_speed": wind_speed,
                "wind_direction": wind_result["wind"]["direction"],
                "upwind": upwind_analysis,
                "downwind": downwind_analysis,
                "optimal_vmg": optimal_vmg,
                "recommendations": self._generate_vmg_recommendations(upwind_analysis, downwind_analysis, optimal_vmg)
            }
            
            # 処理完了
            self._update_processing_status(False, 100.0, "VMG最適化分析が完了しました", "complete")
            
            return result
            
        except Exception as e:
            error_msg = f"VMG最適化分析中にエラーが発生しました: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self._update_processing_status(False, 100.0, error_msg, "error")
            return {"error": error_msg}
    
    def _analyze_vmg_optimization(self, df: pd.DataFrame, mode: str,
                               optimal_angle: Optional[float], 
                               optimal_vmg: Optional[float]) -> Dict[str, Any]:
        """
        風上または風下のVMG最適化分析
        
        Parameters:
        -----------
        df : pd.DataFrame
            分析対象データフレーム
        mode : str
            分析モード ('upwind' or 'downwind')
        optimal_angle : float, optional
            最適角度
        optimal_vmg : float, optional
            最適VMG
            
        Returns:
        --------
        Dict[str, Any]
            VMG最適化分析結果
        """
        if df.empty:
            return {
                "insufficient_data": True,
                "data_points": 0
            }
        
        # VMGカラム名
        vmg_col = 'upwind_vmg' if mode == 'upwind' else 'downwind_vmg'
        
        # 角度とVMGの関係
        angle_vmg_data = []
        
        # 5度間隔でグループ化
        df['angle_bin'] = df['rel_wind_angle'].abs().apply(lambda x: 5 * round(x / 5))
        
        # 各角度ビンごとのVMG平均
        angle_groups = df.groupby('angle_bin')[vmg_col].agg(['mean', 'count', 'std'])
        
        for angle, stats in angle_groups.iterrows():
            if stats['count'] >= 5:  # 十分なデータポイントがある場合のみ
                angle_vmg_data.append({
                    "angle": float(angle),
                    "vmg": float(stats['mean']),
                    "count": int(stats['count']),
                    "std": float(stats['std']) if not np.isnan(stats['std']) else 0.0
                })
        
        # VMGが最大の角度を探す
        best_angle_data = max(angle_vmg_data, key=lambda x: x['vmg']) if angle_vmg_data else None
        
        # 実際のVMGの統計
        actual_vmg_stats = {
            "mean": float(df[vmg_col].mean()),
            "max": float(df[vmg_col].max()),
            "std": float(df[vmg_col].std()),
            "percentile_75": float(df[vmg_col].quantile(0.75)),
            "count": len(df)
        }
        
        # 結果のまとめ
        analysis = {
            "data_points": len(df),
            "angle_vmg_data": angle_vmg_data,
            "best_angle": best_angle_data["angle"] if best_angle_data else None,
            "best_vmg": best_angle_data["vmg"] if best_angle_data else None,
            "actual_vmg_stats": actual_vmg_stats,
            "optimal_angle": optimal_angle,
            "optimal_vmg": optimal_vmg,
            "angle_distribution": self._calculate_angle_distribution(df['rel_wind_angle'])
        }
        
        # 最適角度からのズレ
        if best_angle_data and optimal_angle:
            analysis["angle_deviation"] = best_angle_data["angle"] - optimal_angle
        
        # VMGの最適比
        if best_angle_data and optimal_vmg and optimal_vmg > 0:
            analysis["vmg_ratio"] = best_angle_data["vmg"] / optimal_vmg
        
        return analysis
    
    def _generate_vmg_recommendations(self, upwind_analysis: Dict[str, Any],
                                   downwind_analysis: Dict[str, Any],
                                   optimal_vmg: Dict[str, Any]) -> List[str]:
        """
        VMG最適化のための推奨事項を生成
        
        Parameters:
        -----------
        upwind_analysis : Dict[str, Any]
            風上VMG分析結果
        downwind_analysis : Dict[str, Any]
            風下VMG分析結果
        optimal_vmg : Dict[str, Any]
            最適VMG情報
            
        Returns:
        --------
        List[str]
            推奨事項のリスト
        """
        recommendations = []
        
        # 風上VMGの推奨事項
        if not upwind_analysis.get("insufficient_data", False):
            best_angle = upwind_analysis.get("best_angle")
            optimal_angle = optimal_vmg.get("upwind_angle")
            
            if best_angle is not None and optimal_angle is not None:
                angle_diff = best_angle - optimal_angle
                
                if abs(angle_diff) > 10:
                    if angle_diff > 0:
                        recommendations.append(
                            f"風上航行時は現在の{best_angle:.1f}度より約{abs(angle_diff):.1f}度タイトな角度で走ることでVMGが向上する可能性があります。"
                        )
                    else:
                        recommendations.append(
                            f"風上航行時は現在の{best_angle:.1f}度より約{abs(angle_diff):.1f}度開けた角度で走ることでVMGが向上する可能性があります。"
                        )
                else:
                    recommendations.append(
                        f"風上航行の角度は最適に近い（{best_angle:.1f}度）です。"
                    )
        
        # 風下VMGの推奨事項
        if not downwind_analysis.get("insufficient_data", False):
            best_angle = downwind_analysis.get("best_angle")
            optimal_angle = optimal_vmg.get("downwind_angle")
            
            if best_angle is not None and optimal_angle is not None:
                angle_diff = best_angle - optimal_angle
                
                if abs(angle_diff) > 10:
                    if angle_diff > 0:
                        recommendations.append(
                            f"風下航行時は現在の{best_angle:.1f}度より約{abs(angle_diff):.1f}度タイトな角度で走ることでVMGが向上する可能性があります。"
                        )
                    else:
                        recommendations.append(
                            f"風下航行時は現在の{best_angle:.1f}度より約{abs(angle_diff):.1f}度開けた角度で走ることでVMGが向上する可能性があります。"
                        )
                else:
                    recommendations.append(
                        f"風下航行の角度は最適に近い（{best_angle:.1f}度）です。"
                    )
        
        # VMG一貫性の推奨事項
        if not upwind_analysis.get("insufficient_data", False):
            vmg_std = upwind_analysis.get("actual_vmg_stats", {}).get("std")
            vmg_mean = upwind_analysis.get("actual_vmg_stats", {}).get("mean")
            
            if vmg_std is not None and vmg_mean is not None and vmg_mean > 0:
                cv = vmg_std / vmg_mean  # 変動係数
                
                if cv > 0.25:
                    recommendations.append(
                        "風上VMGの一貫性を高めるために、より安定した角度と速度のバランスを維持することが重要です。"
                    )
        
        # 一般的な推奨事項
        if not recommendations:
            recommendations.append(
                "VMG最適化については特に問題点は見られません。現在の帆走角度と技術を維持してください。"
            )
        
        return recommendations
    
    def analyze_course_efficiency(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        コース効率の分析
        
        Parameters:
        -----------
        df : pd.DataFrame
            セーリングデータフレーム
            
        Returns:
        --------
        Dict[str, Any]
            コース効率分析結果
        """
        # 処理状態の更新
        self._update_processing_status(True, 0.0, "コース効率分析を開始しています...", "initialize")
        
        try:
            # 風推定を実行
            self._update_processing_status(True, 20.0, "風推定を実行しています...", "estimate_wind")
            
            if not self.wind_estimator:
                self._update_processing_status(False, 100.0, "風推定器が利用できません", "error")
                return {"error": "風推定器が利用できません"}
                
            wind_result = self.wind_estimator.estimate_wind(df)
            
            if "error" in wind_result:
                self._update_processing_status(False, 100.0, f"風推定エラー: {wind_result['error']}", "error")
                return {"error": f"風推定エラー: {wind_result['error']}"}
            
            # コース効率分析
            self._update_processing_status(True, 60.0, "コース効率を分析しています...", "analyze_course")
            
            # タイムスタンプでソート
            sorted_df = df.sort_values('timestamp')
            
            # 総移動距離の計算
            total_distance = self._calculate_total_distance(sorted_df)
            
            # 始点と終点
            start_point = (sorted_df['latitude'].iloc[0], sorted_df['longitude'].iloc[0])
            end_point = (sorted_df['latitude'].iloc[-1], sorted_df['longitude'].iloc[-1])
            
            # 直線距離の計算
            direct_distance = self._calculate_distance(
                start_point[0], start_point[1], end_point[0], end_point[1]
            )
            
            # 効率計算
            course_efficiency = direct_distance / total_distance if total_distance > 0 else 0
            
            # 風向に対するコース分析
            wind_direction = wind_result["wind"]["direction"]
            
            # 理想的なコースからの逸脱分析
            deviation_analysis = self._analyze_course_deviation(sorted_df, wind_direction)
            
            # 結果の作成
            self._update_processing_status(True, 90.0, "結果を集計しています...", "format_results")
            
            result = {
                "total_distance_nm": total_distance,
                "direct_distance_nm": direct_distance,
                "course_efficiency": course_efficiency,
                "start_point": start_point,
                "end_point": end_point,
                "wind_direction": wind_direction,
                "deviation_analysis": deviation_analysis,
                "efficiency_rating": self._rate_course_efficiency(course_efficiency),
                "recommendations": self._generate_course_recommendations(
                    course_efficiency, deviation_analysis
                )
            }
            
            # 処理完了
            self._update_processing_status(False, 100.0, "コース効率分析が完了しました", "complete")
            
            return result
            
        except Exception as e:
            error_msg = f"コース効率分析中にエラーが発生しました: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self._update_processing_status(False, 100.0, error_msg, "error")
            return {"error": error_msg}
    
    def _analyze_course_deviation(self, df: pd.DataFrame, wind_direction: float) -> Dict[str, Any]:
        """
        理想的なコースからの逸脱分析
        
        Parameters:
        -----------
        df : pd.DataFrame
            データフレーム
        wind_direction : float
            風向（度）
            
        Returns:
        --------
        Dict[str, Any]
            逸脱分析結果
        """
        # 風に対する相対角度の計算
        df['rel_wind_angle'] = df['course'].apply(
            lambda course: ((course - wind_direction + 180) % 360) - 180
        )
        
        # 風上モードと風下モードを特定
        df['sailing_mode'] = df['rel_wind_angle'].apply(
            lambda angle: 'upwind' if abs(angle) <= 45 else 
                         ('downwind' if abs(angle) >= 135 else 'reach')
        )
        
        # モード別の分析
        upwind_data = df[df['sailing_mode'] == 'upwind']
        downwind_data = df[df['sailing_mode'] == 'downwind']
        reach_data = df[df['sailing_mode'] == 'reach']
        
        # 各モードでの平均角度
        upwind_avg_angle = upwind_data['rel_wind_angle'].abs().mean() if not upwind_data.empty else None
        downwind_avg_angle = downwind_data['rel_wind_angle'].abs().mean() if not downwind_data.empty else None
        
        # 風上時の左右バランス分析
        port_tack = upwind_data[upwind_data['rel_wind_angle'] < 0]
        starboard_tack = upwind_data[upwind_data['rel_wind_angle'] > 0]
        
        port_time = port_tack['timestamp'].max() - port_tack['timestamp'].min() if not port_tack.empty else timedelta(0)
        starboard_time = starboard_tack['timestamp'].max() - starboard_tack['timestamp'].min() if not starboard_tack.empty else timedelta(0)
        
        port_time_seconds = port_time.total_seconds()
        starboard_time_seconds = starboard_time.total_seconds()
        total_upwind_time = port_time_seconds + starboard_time_seconds
        
        # タック比率
        port_ratio = port_time_seconds / total_upwind_time if total_upwind_time > 0 else 0
        starboard_ratio = starboard_time_seconds / total_upwind_time if total_upwind_time > 0 else 0
        
        # 各モードの走行距離の計算
        upwind_distance = self._calculate_total_distance(upwind_data) if not upwind_data.empty else 0
        downwind_distance = self._calculate_total_distance(downwind_data) if not downwind_data.empty else 0
        reach_distance = self._calculate_total_distance(reach_data) if not reach_data.empty else 0
        
        total_distance = upwind_distance + downwind_distance + reach_distance
        
        # 結果の作成
        return {
            "upwind": {
                "distance_nm": upwind_distance,
                "percentage": (upwind_distance / total_distance * 100) if total_distance > 0 else 0,
                "avg_angle": upwind_avg_angle,
                "port_tack_ratio": port_ratio,
                "starboard_tack_ratio": starboard_ratio
            },
            "downwind": {
                "distance_nm": downwind_distance,
                "percentage": (downwind_distance / total_distance * 100) if total_distance > 0 else 0,
                "avg_angle": downwind_avg_angle
            },
            "reach": {
                "distance_nm": reach_distance,
                "percentage": (reach_distance / total_distance * 100) if total_distance > 0 else 0
            }
        }
    
    def _rate_course_efficiency(self, efficiency: float) -> str:
        """
        コース効率を評価
        
        Parameters:
        -----------
        efficiency : float
            コース効率（0-1）
            
        Returns:
        --------
        str
            評価ラベル
        """
        if efficiency >= 0.9:
            return "非常に効率的"
        elif efficiency >= 0.8:
            return "効率的"
        elif efficiency >= 0.6:
            return "平均的"
        elif efficiency >= 0.4:
            return "やや非効率"
        else:
            return "非効率"
    
    def _generate_course_recommendations(self, efficiency: float, 
                                      deviation_analysis: Dict[str, Any]) -> List[str]:
        """
        コース効率向上のための推奨事項を生成
        
        Parameters:
        -----------
        efficiency : float
            コース効率
        deviation_analysis : Dict[str, Any]
            逸脱分析結果
            
        Returns:
        --------
        List[str]
            推奨事項のリスト
        """
        recommendations = []
        
        # 全体的な効率
        if efficiency < 0.5:
            recommendations.append(
                f"コース効率が{efficiency:.1%}と低いため、目的地に向かうより直線的なコースを取ることを検討してください。"
            )
        
        # タックバランス
        port_ratio = deviation_analysis.get("upwind", {}).get("port_tack_ratio", 0)
        starboard_ratio = deviation_analysis.get("upwind", {}).get("starboard_tack_ratio", 0)
        
        if port_ratio > 0 and starboard_ratio > 0:
            if port_ratio > 0.7:
                recommendations.append(
                    f"風上走行時にポートタックに{port_ratio:.1%}の時間を費やしています。両タックのバランスを取ることを検討してください。"
                )
            elif starboard_ratio > 0.7:
                recommendations.append(
                    f"風上走行時にスターボードタックに{starboard_ratio:.1%}の時間を費やしています。両タックのバランスを取ることを検討してください。"
                )
        
        # 風上角度
        upwind_avg_angle = deviation_analysis.get("upwind", {}).get("avg_angle")
        if upwind_avg_angle is not None:
            if upwind_avg_angle < 30:
                recommendations.append(
                    f"風上走行時の平均角度が{upwind_avg_angle:.1f}度と小さいです。VMGを最適化するためにもう少し開けた角度を検討してください。"
                )
            elif upwind_avg_angle > 50:
                recommendations.append(
                    f"風上走行時の平均角度が{upwind_avg_angle:.1f}度と大きいです。VMGを最適化するためにもう少しタイトな角度を検討してください。"
                )
        
        # リーチの使いすぎ
        reach_percentage = deviation_analysis.get("reach", {}).get("percentage", 0)
        if reach_percentage > 40:
            recommendations.append(
                f"全体の{reach_percentage:.1f}%をリーチングに費やしています。風上または風下を効率的に走ることでVMGを向上できる可能性があります。"
            )
        
        # 総合的なフィードバック
        if not recommendations:
            if efficiency >= 0.8:
                recommendations.append(
                    f"コース効率は{efficiency:.1%}と高く、良好なコース取りができています。"
                )
            else:
                recommendations.append(
                    "特に問題は見られませんが、より直線的なコースを取ることでさらに効率を高められる可能性があります。"
                )
        
        return recommendations
    
    def _calculate_total_distance(self, df: pd.DataFrame) -> float:
        """
        GPSポイント間の総距離を計算（海里単位）
        
        Parameters:
        -----------
        df : pd.DataFrame
            データフレーム
            
        Returns:
        --------
        float
            総距離（海里）
        """
        if len(df) < 2:
            return 0.0
        
        total_distance = 0.0
        prev_lat, prev_lon = None, None
        
        for _, row in df.iterrows():
            lat, lon = row['latitude'], row['longitude']
            
            if prev_lat is not None and prev_lon is not None:
                # 2点間の距離を計算（メートル）
                dist_m = self._calculate_distance(prev_lat, prev_lon, lat, lon)
                # メートルから海里に変換（1海里 = 1852メートル）
                dist_nm = dist_m / 1852.0
                total_distance += dist_nm
            
            prev_lat, prev_lon = lat, lon
        
        return total_distance
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        2点間の距離を計算（メートル）
        
        Parameters:
        -----------
        lat1, lon1 : float
            始点の緯度経度
        lat2, lon2 : float
            終点の緯度経度
            
        Returns:
        --------
        float
            距離（メートル）
        """
        # 地球の半径（メートル）
        R = 6371000
        
        # 緯度経度をラジアンに変換
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # 差分
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        # Haversineの公式
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c
        
        return distance
    
    def _calculate_angle_distribution(self, angles: pd.Series) -> Dict[str, List[Any]]:
        """
        角度の分布データを計算
        
        Parameters:
        -----------
        angles : pd.Series
            角度データ
            
        Returns:
        --------
        Dict[str, List[Any]]
            分布データ
        """
        # 10度単位でビンを作成
        bins = list(range(-180, 181, 10))
        labels = [(bins[i] + bins[i+1])/2 for i in range(len(bins)-1)]
        
        # ヒストグラムの計算
        hist, _ = np.histogram(angles, bins=bins)
        
        return {
            "angles": labels,
            "counts": hist.tolist()
        }
    
    def _calculate_time_distribution(self, timestamps: List[datetime]) -> Dict[str, List[Any]]:
        """
        時系列の分布データを計算
        
        Parameters:
        -----------
        timestamps : List[datetime]
            タイムスタンプのリスト
            
        Returns:
        --------
        Dict[str, List[Any]]
            分布データ
        """
        if not timestamps:
            return {"times": [], "counts": []}
        
        # 最小・最大時刻
        min_time = min(timestamps)
        max_time = max(timestamps)
        
        # 期間が短すぎる場合
        if (max_time - min_time).total_seconds() < 60:
            return {
                "times": [t.isoformat() for t in timestamps],
                "counts": [1 for _ in timestamps]
            }
        
        # 適切なビン数を決定
        duration_seconds = (max_time - min_time).total_seconds()
        
        if duration_seconds < 3600:  # 1時間未満
            bin_size_seconds = 60  # 1分間隔
        elif duration_seconds < 86400:  # 1日未満
            bin_size_seconds = 300  # 5分間隔
        else:
            bin_size_seconds = 1800  # 30分間隔
        
        # ビンの作成
        num_bins = int(duration_seconds / bin_size_seconds) + 1
        bins = [min_time + timedelta(seconds=i*bin_size_seconds) for i in range(num_bins)]
        
        # 各ビンに入るタイムスタンプをカウント
        counts = [0] * (len(bins) - 1)
        
        for ts in timestamps:
            for i in range(len(bins) - 1):
                if bins[i] <= ts < bins[i+1]:
                    counts[i] += 1
                    break
        
        return {
            "times": [b.isoformat() for b in bins[:-1]],
            "counts": counts
        }
    
    def get_processing_status(self) -> Dict[str, Any]:
        """
        処理状態を取得
        
        Returns:
        --------
        Dict[str, Any]
            処理状態の辞書
        """
        return self.processing_status.copy()
    
    def _update_processing_status(self, is_processing: bool, progress: float, 
                               message: str, step: str) -> None:
        """
        処理状態を更新
        
        Parameters:
        -----------
        is_processing : bool
            処理中かどうか
        progress : float
            進捗率（0-100）
        message : str
            ステータスメッセージ
        step : str
            現在のステップ
        """
        self.processing_status["is_processing"] = is_processing
        self.processing_status["progress"] = progress
        self.processing_status["message"] = message
        self.processing_status["step"] = step
        
        if is_processing and self.processing_status["start_time"] is None:
            self.processing_status["start_time"] = datetime.now()
        
        if not is_processing:
            self.processing_status["end_time"] = datetime.now()
    
    def _hash_dataframe(self, df: pd.DataFrame) -> str:
        """
        データフレームのハッシュ値を計算（キャッシュキー生成用）
        
        Parameters:
        -----------
        df : pd.DataFrame
            ハッシュ化するデータフレーム
            
        Returns:
        --------
        str
            ハッシュ値
        """
        import hashlib
        import json
        
        # タイムスタンプでソートし、最初と最後の行および行数を使ってハッシュを作成
        # （完全なデータハッシュではなく、近似的に同じデータかを判断）
        
        sorted_df = df.sort_values('timestamp').reset_index(drop=True)
        
        if len(sorted_df) == 0:
            return "empty_df"
        
        # 最初と最後の行のみ使用
        first_row = sorted_df.iloc[0].to_dict()
        last_row = sorted_df.iloc[-1].to_dict()
        
        # timestamp を文字列に変換（ハッシュの安定性のため）
        for row in [first_row, last_row]:
            if 'timestamp' in row and hasattr(row['timestamp'], 'isoformat'):
                row['timestamp'] = row['timestamp'].isoformat()
        
        # ハッシュの作成
        hash_dict = {
            'first_row': first_row,
            'last_row': last_row,
            'row_count': len(sorted_df),
            'column_names': sorted(df.columns.tolist())
        }
        
        hash_str = json.dumps(hash_dict, sort_keys=True)
        hash_value = hashlib.md5(hash_str.encode('utf-8')).hexdigest()
        
        return hash_value
