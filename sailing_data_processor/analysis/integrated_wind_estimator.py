"""
統合風推定モジュール

このモジュールはGPSデータから風向風速を推定する機能を提供します。
分析ワークフローと連携し、推定結果の保存と表示機能を備えています。
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Tuple, Any, Optional, Union
import time
from datetime import datetime, timedelta

from sailing_data_processor.wind_estimator import WindEstimator
from sailing_data_processor.analysis.analysis_parameters import ParametersManager, ParameterNamespace
from sailing_data_processor.analysis.analysis_cache import AnalysisCache

class IntegratedWindEstimator:
    """
    統合風推定クラス
    
    分析ワークフローと連携して風向風速を推定するための拡張機能を提供します。
    """
    
    def __init__(self, parameters_manager: Optional[ParametersManager] = None,
               cache: Optional[AnalysisCache] = None):
        """
        初期化
        
        Parameters:
        -----------
        parameters_manager : ParametersManager, optional
            パラメータ管理オブジェクト
        cache : AnalysisCache, optional
            結果キャッシュオブジェクト
        """
        self.logger = logging.getLogger(__name__)
        self.parameters_manager = parameters_manager
        self.cache = cache
        
        # 基本風推定器
        self._wind_estimator = None
        
        # 推定結果
        self.estimated_wind = None
        self.estimated_wind_history = []
        self.detected_maneuvers = []
        
        # 処理状態
        self.processing_status = {
            "is_processing": False,
            "progress": 0.0,
            "message": "",
            "step": "",
            "start_time": None,
            "end_time": None
        }
    
    def _get_wind_estimator(self, boat_type: str = "default") -> WindEstimator:
        """
        風推定器を取得（必要に応じて初期化）
        
        Parameters:
        -----------
        boat_type : str, optional
            艇種
            
        Returns:
        --------
        WindEstimator
            風推定器
        """
        if self._wind_estimator is None or self._wind_estimator.boat_type != boat_type:
            self._wind_estimator = WindEstimator(boat_type)
            
            # パラメータマネージャーがあれば設定を適用
            if self.parameters_manager:
                wind_params = self.parameters_manager.get_parameters_by_namespace(ParameterNamespace.WIND_ESTIMATION)
                for key, value in wind_params.items():
                    if key in self._wind_estimator.params:
                        self._wind_estimator.params[key] = value
        
        return self._wind_estimator
    
    def estimate_wind(self, df: pd.DataFrame, boat_type: str = "default",
                   use_cache: bool = True) -> Dict[str, Any]:
        """
        風向風速を推定
        
        Parameters:
        -----------
        df : pd.DataFrame
            推定用データフレーム
        boat_type : str, optional
            艇種
        use_cache : bool, optional
            キャッシュを使用するかどうか
            
        Returns:
        --------
        Dict[str, Any]
            推定結果
        """
        # 処理状態の初期化
        self._update_processing_status(True, 0.0, "風推定を開始しています...", "initialize")
        
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
                cache_params["wind_params"] = self.parameters_manager.get_parameters_by_namespace(
                    ParameterNamespace.WIND_ESTIMATION
                )
            
            try:
                # キャッシュから推定結果を取得
                cached_result = self.cache.compute_from_params(
                    "wind_estimation",
                    cache_params,
                    lambda params: self._perform_wind_estimation(df, boat_type),
                    ttl=3600  # 1時間キャッシュ
                )
                return cached_result
            except Exception as e:
                self.logger.warning(f"キャッシュ処理中にエラーが発生しました: {e}")
                # キャッシュエラーの場合は直接計算
                return self._perform_wind_estimation(df, boat_type)
        else:
            # キャッシュを使用しない場合は直接計算
            return self._perform_wind_estimation(df, boat_type)
    
    def _perform_wind_estimation(self, df: pd.DataFrame, boat_type: str) -> Dict[str, Any]:
        """
        風推定の実行
        
        Parameters:
        -----------
        df : pd.DataFrame
            推定用データフレーム
        boat_type : str
            艇種
            
        Returns:
        --------
        Dict[str, Any]
            推定結果
        """
        try:
            # 処理状態の更新
            self._update_processing_status(True, 10.0, "風推定器を準備しています...", "prepare")
            
            # 風推定器の取得
            wind_estimator = self._get_wind_estimator(boat_type)
            
            # タイムスタンプの並べ替え
            df = df.sort_values('timestamp')
            
            # マニューバー検出
            self._update_processing_status(True, 30.0, "マニューバーを検出しています...", "detect_maneuvers")
            maneuvers_df = wind_estimator.detect_maneuvers(df)
            self.detected_maneuvers = maneuvers_df.to_dict('records') if not maneuvers_df.empty else []
            
            # マニューバーからの風向推定
            self._update_processing_status(True, 60.0, "マニューバーから風を推定しています...", "estimate_from_maneuvers")
            wind_from_maneuvers = wind_estimator.estimate_wind_from_maneuvers(df)
            
            # コースと速度からの風向推定
            self._update_processing_status(True, 80.0, "航跡パターンから風を推定しています...", "estimate_from_course_speed")
            wind_from_course = wind_estimator.estimate_wind_from_course_speed(df)
            
            # 推定結果の保存
            self.estimated_wind = wind_from_maneuvers if wind_from_maneuvers["confidence"] > 0.3 else wind_from_course
            
            # 結果を履歴に追加
            self.estimated_wind_history.append({
                "timestamp": datetime.now().isoformat(),
                "wind": self.estimated_wind,
                "method": self.estimated_wind["method"],
                "confidence": self.estimated_wind["confidence"]
            })
            
            # 結果のフォーマット
            self._update_processing_status(True, 90.0, "結果を集計しています...", "format_results")
            
            result = {
                "wind": self.estimated_wind,
                "detected_maneuvers": self.detected_maneuvers,
                "wind_summary": wind_estimator.get_estimated_wind_summary(),
                "maneuver_count": len(self.detected_maneuvers),
                "timestamp": datetime.now().isoformat(),
                "boat_type": boat_type,
            }
            
            # 処理完了
            self._update_processing_status(False, 100.0, "風推定が完了しました", "complete")
            
            return result
            
        except Exception as e:
            error_msg = f"風推定中にエラーが発生しました: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self._update_processing_status(False, 100.0, error_msg, "error")
            return {"error": error_msg}
    
    def get_optimal_vmg_angles(self, wind_speed: float, boat_type: str = None) -> Dict[str, float]:
        """
        指定風速での最適VMG角度を計算
        
        Parameters:
        -----------
        wind_speed : float
            風速（ノット）
        boat_type : str, optional
            艇種
            
        Returns:
        --------
        Dict[str, float]
            風上・風下の最適VMG角度と速度
        """
        wind_estimator = self._get_wind_estimator(boat_type)
        return wind_estimator.get_optimal_vmg_angles(wind_speed, boat_type)
    
    def get_polar_data(self, boat_type: str = None) -> Dict[str, List[float]]:
        """
        艇種のポーラーデータを取得
        
        Parameters:
        -----------
        boat_type : str, optional
            艇種
            
        Returns:
        --------
        Dict[str, List[float]]
            ポーラーデータ
        """
        wind_estimator = self._get_wind_estimator(boat_type)
        return wind_estimator.get_polar_data(boat_type)
    
    def analyze_tack_gybe_performance(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        タック・ジャイブのパフォーマンスを分析
        
        Parameters:
        -----------
        df : pd.DataFrame
            分析用データフレーム
            
        Returns:
        --------
        Dict[str, Any]
            分析結果
        """
        # 処理状態の更新
        self._update_processing_status(True, 0.0, "タック・ジャイブ分析を開始しています...", "initialize")
        
        try:
            # 風推定器の取得
            wind_estimator = self._get_wind_estimator()
            
            # マニューバー検出
            self._update_processing_status(True, 30.0, "マニューバーを検出しています...", "detect_maneuvers")
            maneuvers_df = wind_estimator.detect_maneuvers(df)
            
            if maneuvers_df.empty:
                self._update_processing_status(False, 100.0, "マニューバーが検出されませんでした", "complete")
                return {
                    "maneuver_count": 0,
                    "tack_count": 0,
                    "gybe_count": 0,
                    "maneuvers": []
                }
            
            # マニューバーの分類
            self._update_processing_status(True, 60.0, "マニューバーを分類しています...", "categorize_maneuvers")
            categorized_df = wind_estimator.categorize_maneuvers(maneuvers_df, df)
            
            # タックとジャイブを抽出
            tacks = categorized_df[categorized_df['maneuver_type'] == 'tack']
            jibes = categorized_df[categorized_df['maneuver_type'] == 'jibe']
            
            # 分析結果の作成
            self._update_processing_status(True, 80.0, "分析結果を集計しています...", "analyze_results")
            
            tack_count = len(tacks)
            jibe_count = len(jibes)
            
            # パフォーマンス統計
            tack_stats = {}
            jibe_stats = {}
            
            if not tacks.empty:
                tack_speed_ratio = tacks['speed_ratio'].mean()
                tack_duration = tacks['maneuver_duration'].mean()
                tack_stats = {
                    "count": tack_count,
                    "avg_speed_ratio": float(tack_speed_ratio),
                    "avg_duration": float(tack_duration),
                    "min_duration": float(tacks['maneuver_duration'].min()),
                    "max_duration": float(tacks['maneuver_duration'].max())
                }
            
            if not jibes.empty:
                jibe_speed_ratio = jibes['speed_ratio'].mean()
                jibe_duration = jibes['maneuver_duration'].mean()
                jibe_stats = {
                    "count": jibe_count,
                    "avg_speed_ratio": float(jibe_speed_ratio),
                    "avg_duration": float(jibe_duration),
                    "min_duration": float(jibes['maneuver_duration'].min()),
                    "max_duration": float(jibes['maneuver_duration'].max())
                }
            
            # 全マニューバーのリスト
            maneuvers = categorized_df.to_dict('records')
            
            # 処理完了
            self._update_processing_status(False, 100.0, "タック・ジャイブ分析が完了しました", "complete")
            
            return {
                "maneuver_count": len(maneuvers),
                "tack_count": tack_count,
                "gybe_count": jibe_count,
                "tack_stats": tack_stats,
                "gybe_stats": jibe_stats,
                "maneuvers": maneuvers
            }
            
        except Exception as e:
            error_msg = f"タック・ジャイブ分析中にエラーが発生しました: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self._update_processing_status(False, 100.0, error_msg, "error")
            return {"error": error_msg}
    
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
    
    def get_wind_direction_distribution(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        風向の分布を計算
        
        Parameters:
        -----------
        df : pd.DataFrame
            分析用データフレーム
            
        Returns:
        --------
        Dict[str, Any]
            風向分布データ
        """
        # 処理状態の更新
        self._update_processing_status(True, 0.0, "風向分布を分析しています...", "initialize")
        
        try:
            # 風推定
            self._update_processing_status(True, 30.0, "風推定を行っています...", "estimate_wind")
            wind_result = self.estimate_wind(df)
            
            if "error" in wind_result:
                self._update_processing_status(False, 100.0, f"風推定エラー: {wind_result['error']}", "error")
                return wind_result
            
            wind_direction = wind_result["wind"]["direction"]
            
            # 艇の進行方向の分布を計算
            self._update_processing_status(True, 60.0, "進行方向の分布を計算しています...", "calculate_distribution")
            
            # 方位角を36の分割に集計（10度ごと）
            bins = np.linspace(0, 360, 37)
            hist, bin_edges = np.histogram(df['course'], bins=bins)
            
            # 相対風向を計算
            df['rel_wind_angle'] = df['course'].apply(
                lambda course: ((course - wind_direction + 180) % 360) - 180
            )
            
            # 風上/風下の判定
            upwind_threshold = 45  # 風上と判定する最大角度
            downwind_threshold = 135  # 風下と判定する最小角度
            
            df['sailing_mode'] = df['rel_wind_angle'].apply(
                lambda angle: 'upwind' if abs(angle) <= upwind_threshold else 
                             ('downwind' if abs(angle) >= downwind_threshold else 'reach')
            )
            
            # モード別の時間集計
            mode_counts = df['sailing_mode'].value_counts()
            total_count = len(df)
            
            upwind_pct = float(mode_counts.get('upwind', 0) / total_count * 100)
            reach_pct = float(mode_counts.get('reach', 0) / total_count * 100)
            downwind_pct = float(mode_counts.get('downwind', 0) / total_count * 100)
            
            # 分布データの作成
            self._update_processing_status(True, 90.0, "結果を集計しています...", "format_results")
            
            distribution_data = {
                "course_histogram": hist.tolist(),
                "angle_bins": [(bin_edges[i] + bin_edges[i+1])/2 for i in range(len(bin_edges)-1)],
                "wind_direction": wind_direction,
                "upwind_percentage": upwind_pct,
                "reach_percentage": reach_pct,
                "downwind_percentage": downwind_pct,
                "upwind_threshold": upwind_threshold,
                "downwind_threshold": downwind_threshold
            }
            
            # 処理完了
            self._update_processing_status(False, 100.0, "風向分布分析が完了しました", "complete")
            
            return distribution_data
            
        except Exception as e:
            error_msg = f"風向分布分析中にエラーが発生しました: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self._update_processing_status(False, 100.0, error_msg, "error")
            return {"error": error_msg}
    
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
