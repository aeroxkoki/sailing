"""
統合戦略検出モジュール

このモジュールはセーリングデータから戦略的判断ポイントを検出する機能を提供します。
分析ワークフローと連携し、風向シフト、タック判断、レイラインなどの検出と分析を行います。
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Tuple, Any, Optional, Union
import time
from datetime import datetime, timedelta
import math

from sailing_data_processor.strategy.detector import StrategyDetector
from sailing_data_processor.strategy.strategy_detector_with_propagation import StrategyDetectorWithPropagation
from sailing_data_processor.strategy.points import StrategyPoint, WindShiftPoint, TackPoint, LaylinePoint
from sailing_data_processor.analysis.analysis_parameters import ParametersManager, ParameterNamespace
from sailing_data_processor.analysis.analysis_cache import AnalysisCache
from sailing_data_processor.analysis.integrated_wind_estimator import IntegratedWindEstimator

class IntegratedStrategyDetector:
    """
    統合戦略検出クラス
    
    分析ワークフローと連携して戦略的判断ポイントを検出するための拡張機能を提供します。
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
        
        # 基本戦略検出器
        self._strategy_detector = None
        self._strategy_detector_with_propagation = None
        
        # 検出結果
        self.detected_points = []
        self.wind_shifts = []
        self.tack_points = []
        self.layline_points = []
        
        # 処理状態
        self.processing_status = {
            "is_processing": False,
            "progress": 0.0,
            "message": "",
            "step": "",
            "start_time": None,
            "end_time": None
        }
    
    def _get_strategy_detector(self, use_propagation: bool = False) -> Union[StrategyDetector, StrategyDetectorWithPropagation]:
        """
        戦略検出器を取得（必要に応じて初期化）
        
        Parameters:
        -----------
        use_propagation : bool, optional
            風向予測を使用するかどうか
            
        Returns:
        --------
        Union[StrategyDetector, StrategyDetectorWithPropagation]
            戦略検出器
        """
        # 風向予測機能を使用するかどうかで検出器を選択
        if use_propagation:
            if self._strategy_detector_with_propagation is None:
                self._strategy_detector_with_propagation = StrategyDetectorWithPropagation()
                
                # パラメータの適用
                if self.parameters_manager:
                    self._apply_parameters(self._strategy_detector_with_propagation)
            
            return self._strategy_detector_with_propagation
        else:
            if self._strategy_detector is None:
                self._strategy_detector = StrategyDetector()
                
                # パラメータの適用
                if self.parameters_manager:
                    self._apply_parameters(self._strategy_detector)
            
            return self._strategy_detector
    
    def _apply_parameters(self, detector: Union[StrategyDetector, StrategyDetectorWithPropagation]) -> None:
        """
        検出器にパラメータを適用
        
        Parameters:
        -----------
        detector : Union[StrategyDetector, StrategyDetectorWithPropagation]
            パラメータを適用する検出器
        """
        if not self.parameters_manager:
            return
        
        # 戦略検出パラメータを取得
        strategy_params = self.parameters_manager.get_parameters_by_namespace(ParameterNamespace.STRATEGY_DETECTION)
        
        # 基本パラメータの設定
        for key, value in strategy_params.items():
            if key in detector.config:
                detector.config[key] = value
        
        # 風向予測機能を使用する場合の追加パラメータ
        if isinstance(detector, StrategyDetectorWithPropagation):
            for key, value in strategy_params.items():
                if key in detector.propagation_config:
                    detector.propagation_config[key] = value
    
    def detect_strategy_points(self, 
                              df: pd.DataFrame,
                              course_data: Optional[Dict[str, Any]] = None,
                              wind_field: Optional[Dict[str, Any]] = None,
                              use_propagation: bool = False,
                              use_cache: bool = True) -> Dict[str, Any]:
        """
        戦略的判断ポイントを検出
        
        Parameters:
        -----------
        df : pd.DataFrame
            セーリングデータフレーム
        course_data : Dict[str, Any], optional
            コース情報
        wind_field : Dict[str, Any], optional
            風の場データ
        use_propagation : bool, optional
            風向予測を使用するかどうか
        use_cache : bool, optional
            キャッシュを使用するかどうか
            
        Returns:
        --------
        Dict[str, Any]
            検出結果
        """
        # 処理状態の初期化
        self._update_processing_status(True, 0.0, "戦略ポイント検出を開始しています...", "initialize")
        
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
        
        # 風の場データがなければ風推定を実行
        if wind_field is None and self.wind_estimator:
            self._update_processing_status(True, 10.0, "風推定を実行しています...", "estimate_wind")
            wind_result = self.wind_estimator.estimate_wind(df, use_cache=use_cache)
            
            if "error" in wind_result:
                self._update_processing_status(False, 100.0, f"風推定エラー: {wind_result['error']}", "error")
                return {"error": f"風推定エラー: {wind_result['error']}"}
                
            # 風推定結果から風の場データを生成
            wind_field = self._create_wind_field_from_estimation(wind_result, df)
        
        # コース情報がなければ基本コース情報を生成
        if course_data is None:
            self._update_processing_status(True, 15.0, "コース情報を生成しています...", "create_course_data")
            course_data = self._create_basic_course_data(df)
        
        # キャッシュをチェック
        if use_cache and self.cache:
            # キャッシュキー生成用のパラメータ
            cache_params = {
                "data_hash": self._hash_dataframe(df),
                "use_propagation": use_propagation,
                "course_hash": self._hash_course_data(course_data),
                "wind_field_hash": self._hash_wind_field(wind_field)
            }
            
            # パラメーターマネージャーがある場合はパラメータも含める
            if self.parameters_manager:
                cache_params["strategy_params"] = self.parameters_manager.get_parameters_by_namespace(
                    ParameterNamespace.STRATEGY_DETECTION
                )
            
            try:
                # キャッシュから検出結果を取得
                cached_result = self.cache.compute_from_params(
                    "strategy_detection",
                    cache_params,
                    lambda params: self._perform_strategy_detection(df, course_data, wind_field, use_propagation),
                    ttl=3600  # 1時間キャッシュ
                )
                return cached_result
            except Exception as e:
                self.logger.warning(f"キャッシュ処理中にエラーが発生しました: {e}")
                # キャッシュエラーの場合は直接計算
                return self._perform_strategy_detection(df, course_data, wind_field, use_propagation)
        else:
            # キャッシュを使用しない場合は直接計算
            return self._perform_strategy_detection(df, course_data, wind_field, use_propagation)
    
    def _perform_strategy_detection(self, 
                                   df: pd.DataFrame,
                                   course_data: Dict[str, Any],
                                   wind_field: Dict[str, Any],
                                   use_propagation: bool) -> Dict[str, Any]:
        """
        戦略検出の実行
        
        Parameters:
        -----------
        df : pd.DataFrame
            セーリングデータフレーム
        course_data : Dict[str, Any]
            コース情報
        wind_field : Dict[str, Any]
            風の場データ
        use_propagation : bool
            風向予測を使用するかどうか
            
        Returns:
        --------
        Dict[str, Any]
            検出結果
        """
        try:
            # 処理状態の更新
            self._update_processing_status(True, 20.0, "戦略検出器を準備しています...", "prepare")
            
            # 戦略検出器の取得
            detector = self._get_strategy_detector(use_propagation)
            
            # 風向シフトの検出
            self._update_processing_status(True, 30.0, "風向シフトを検出しています...", "detect_wind_shifts")
            if use_propagation and isinstance(detector, StrategyDetectorWithPropagation):
                # 風向予測機能を使用
                wind_shifts = detector.detect_wind_shifts_with_propagation(course_data, wind_field)
            else:
                # 通常の風向シフト検出
                wind_shifts = detector.detect_wind_shifts(course_data, wind_field)
            
            self.wind_shifts = wind_shifts
            
            # 最適タックポイントの検出
            self._update_processing_status(True, 60.0, "最適タックポイントを検出しています...", "detect_tack_points")
            tack_points = detector.detect_optimal_tacks(course_data, wind_field)
            self.tack_points = tack_points
            
            # レイラインの検出
            self._update_processing_status(True, 80.0, "レイラインを検出しています...", "detect_laylines")
            layline_points = detector.detect_laylines(course_data, wind_field)
            self.layline_points = layline_points
            
            # 検出結果の統合
            self._update_processing_status(True, 90.0, "結果を集計しています...", "format_results")
            
            # すべての検出ポイントを統合
            all_points = wind_shifts + tack_points + layline_points
            
            # 重要度でソート
            all_points.sort(key=lambda p: p.strategic_score if hasattr(p, 'strategic_score') else 0, reverse=True)
            
            # 結果を保存
            self.detected_points = all_points
            
            # 結果の辞書を作成
            result = {
                "wind_shifts": self._strategy_points_to_dict(wind_shifts),
                "tack_points": self._strategy_points_to_dict(tack_points),
                "layline_points": self._strategy_points_to_dict(layline_points),
                "all_points": self._strategy_points_to_dict(all_points),
                "timestamp": datetime.now().isoformat(),
                "point_count": len(all_points),
                "wind_shift_count": len(wind_shifts),
                "tack_point_count": len(tack_points),
                "layline_count": len(layline_points),
                "use_propagation": use_propagation
            }
            
            # 処理完了
            self._update_processing_status(False, 100.0, "戦略ポイント検出が完了しました", "complete")
            
            return result
            
        except Exception as e:
            error_msg = f"戦略検出中にエラーが発生しました: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self._update_processing_status(False, 100.0, error_msg, "error")
            return {"error": error_msg}
    
    def _strategy_points_to_dict(self, points: List[StrategyPoint]) -> List[Dict[str, Any]]:
        """
        戦略ポイントをJSON変換可能な辞書リストに変換
        
        Parameters:
        -----------
        points : List[StrategyPoint]
            戦略ポイントのリスト
            
        Returns:
        --------
        List[Dict[str, Any]]
            辞書のリスト
        """
        result = []
        
        for point in points:
            point_dict = {
                "type": point.__class__.__name__,
                "latitude": point.position[0] if hasattr(point, 'position') and point.position else None,
                "longitude": point.position[1] if hasattr(point, 'position') and point.position else None,
                "time_estimate": point.time_estimate.isoformat() if hasattr(point, 'time_estimate') and point.time_estimate else None,
                "strategic_score": getattr(point, 'strategic_score', 0.5),
                "note": getattr(point, 'note', '')
            }
            
            # 風向シフトポイントの追加情報
            if isinstance(point, WindShiftPoint):
                point_dict.update({
                    "shift_angle": point.shift_angle,
                    "before_direction": point.before_direction,
                    "after_direction": point.after_direction,
                    "wind_speed": point.wind_speed,
                    "shift_probability": point.shift_probability
                })
            
            # タックポイントの追加情報
            elif isinstance(point, TackPoint):
                point_dict.update({
                    "tack_type": point.tack_type,
                    "suggested_tack": point.suggested_tack,
                    "vmg_gain": point.vmg_gain,
                    "confidence": point.confidence
                })
            
            # レイラインポイントの追加情報
            elif isinstance(point, LaylinePoint):
                point_dict.update({
                    "mark_id": point.mark_id,
                    "distance_to_mark": point.distance_to_mark,
                    "approach_angle": point.approach_angle,
                    "confidence": point.confidence
                })
            
            result.append(point_dict)
        
        return result
    
    def _create_wind_field_from_estimation(self, wind_result: Dict[str, Any], df: pd.DataFrame) -> Dict[str, Any]:
        """
        風推定結果から風の場データを生成
        
        Parameters:
        -----------
        wind_result : Dict[str, Any]
            風推定結果
        df : pd.DataFrame
            セーリングデータフレーム
            
        Returns:
        --------
        Dict[str, Any]
            風の場データ
        """
        if "error" in wind_result:
            return None
        
        # 航跡データの範囲を取得
        lat_min, lat_max = df["latitude"].min(), df["latitude"].max()
        lon_min, lon_max = df["longitude"].min(), df["longitude"].max()
        
        # 範囲を少し拡大
        lat_margin = (lat_max - lat_min) * 0.1
        lon_margin = (lon_max - lon_min) * 0.1
        lat_min -= lat_margin
        lat_max += lat_margin
        lon_min -= lon_margin
        lon_max += lon_margin
        
        # グリッドサイズ（3x3の単純なグリッド）
        grid_size = 3
        
        # グリッドデータの作成
        lat_grid = np.linspace(lat_min, lat_max, grid_size)
        lon_grid = np.linspace(lon_min, lon_max, grid_size)
        lat_mesh, lon_mesh = np.meshgrid(lat_grid, lon_grid)
        
        # 風データ
        wind_direction = wind_result["wind"]["direction"]
        wind_speed = wind_result["wind"]["speed"]
        
        # 風向風速の格子データ（一定の風向風速）
        wind_directions = np.ones_like(lat_mesh) * wind_direction
        wind_speeds = np.ones_like(lat_mesh) * wind_speed
        
        # 信頼度（中心が高く、周辺が低い単純なパターン）
        confidence = np.ones_like(lat_mesh) * 0.7
        
        # 風の場データとして整形
        wind_field = {
            "lat_grid": lat_mesh,
            "lon_grid": lon_mesh,
            "wind_direction": wind_directions,
            "wind_speed": wind_speeds,
            "confidence": confidence,
            "time": datetime.now(),
            "source": "wind_estimation",
            "metadata": {
                "estimation_method": wind_result["wind"]["method"],
                "confidence": wind_result["wind"]["confidence"]
            }
        }
        
        return wind_field
    
    def _create_basic_course_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        基本的なコース情報を生成
        
        Parameters:
        -----------
        df : pd.DataFrame
            セーリングデータフレーム
            
        Returns:
        --------
        Dict[str, Any]
            コース情報
        """
        # タイムスタンプの範囲を取得
        start_time = df["timestamp"].min()
        end_time = df["timestamp"].max()
        
        # 位置の範囲を取得
        lat_min, lat_max = df["latitude"].min(), df["latitude"].max()
        lon_min, lon_max = df["longitude"].min(), df["longitude"].max()
        
        # 中心点を計算
        center_lat = (lat_min + lat_max) / 2
        center_lon = (lon_min + lon_max) / 2
        
        # 航跡データを基に単純なコースを生成
        course_data = {
            "name": "自動生成コース",
            "start_time": start_time,
            "end_time": end_time,
            "center": [center_lat, center_lon],
            "boundary": [[lat_min, lon_min], [lat_max, lon_max]],
            "legs": []
        }
        
        # データポイントから単純なレグを生成
        sample_rate = max(1, len(df) // 10)  # データの10分の1をサンプリング
        path_points = []
        
        for i in range(0, len(df), sample_rate):
            row = df.iloc[i]
            point = {
                "lat": row["latitude"],
                "lon": row["longitude"],
                "timestamp": row["timestamp"] if isinstance(row["timestamp"], str) else row["timestamp"].isoformat()
            }
            path_points.append(point)
        
        # 一つのレグとして追加
        if path_points:
            leg = {
                "name": "航跡レグ",
                "start": path_points[0],
                "end": path_points[-1],
                "path": {
                    "path_points": path_points
                }
            }
            course_data["legs"].append(leg)
        
        return course_data
    
    def analyze_wind_shifts(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        風向シフトを分析
        
        Parameters:
        -----------
        df : pd.DataFrame
            セーリングデータフレーム
            
        Returns:
        --------
        Dict[str, Any]
            風向シフト分析結果
        """
        # 処理状態の更新
        self._update_processing_status(True, 0.0, "風向シフト分析を開始しています...", "initialize")
        
        try:
            # まず風推定を実行
            self._update_processing_status(True, 20.0, "風推定を実行しています...", "estimate_wind")
            
            if not self.wind_estimator:
                self._update_processing_status(False, 100.0, "風推定器が利用できません", "error")
                return {"error": "風推定器が利用できません"}
                
            wind_result = self.wind_estimator.estimate_wind(df)
            
            if "error" in wind_result:
                self._update_processing_status(False, 100.0, f"風推定エラー: {wind_result['error']}", "error")
                return {"error": f"風推定エラー: {wind_result['error']}"}
            
            # マニューバーを取得
            maneuvers = wind_result.get("detected_maneuvers", [])
            
            if not maneuvers:
                self._update_processing_status(False, 100.0, "マニューバーが検出されませんでした", "complete")
                return {
                    "shift_count": 0,
                    "shifts": [],
                    "average_shift_angle": 0,
                    "has_significant_shifts": False
                }
            
            # 時系列に沿って風向の変化を分析
            self._update_processing_status(True, 60.0, "風向の変化を分析しています...", "analyze_shifts")
            
            # マニューバーから風向変化を推定
            shifts = []
            prev_direction = None
            
            for i, maneuver in enumerate(maneuvers):
                if 'before_bearing' in maneuver and 'after_bearing' in maneuver:
                    # マニューバー前後の方位から風向変化を推定
                    if i > 0 and prev_direction is not None:
                        # 風向の変化
                        wind_dir_change = self._calculate_angle_difference(
                            maneuver.get('wind_direction', prev_direction),
                            prev_direction
                        )
                        
                        if abs(wind_dir_change) >= 3.0:  # 3度以上の変化を記録
                            shift = {
                                "timestamp": maneuver.get('timestamp'),
                                "position": [maneuver.get('latitude'), maneuver.get('longitude')],
                                "shift_angle": wind_dir_change,
                                "before_direction": prev_direction,
                                "after_direction": maneuver.get('wind_direction', prev_direction),
                                "is_significant": abs(wind_dir_change) >= 10.0  # 10度以上で重要な変化
                            }
                            shifts.append(shift)
                    
                    # 現在の風向を記録
                    prev_direction = maneuver.get('wind_direction')
            
            # 風向シフト分析結果の作成
            self._update_processing_status(True, 90.0, "分析結果を集計しています...", "format_results")
            
            # 有意な風向シフトの数
            significant_shifts = [s for s in shifts if s["is_significant"]]
            
            # 分析結果
            result = {
                "shift_count": len(shifts),
                "significant_shift_count": len(significant_shifts),
                "shifts": shifts,
                "average_shift_angle": np.mean([abs(s["shift_angle"]) for s in shifts]) if shifts else 0,
                "has_significant_shifts": len(significant_shifts) > 0,
                "wind_direction": wind_result["wind"]["direction"],
                "wind_speed": wind_result["wind"]["speed"]
            }
            
            # 処理完了
            self._update_processing_status(False, 100.0, "風向シフト分析が完了しました", "complete")
            
            return result
            
        except Exception as e:
            error_msg = f"風向シフト分析中にエラーが発生しました: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self._update_processing_status(False, 100.0, error_msg, "error")
            return {"error": error_msg}
    
    def optimize_laylines(self, df: pd.DataFrame, marks: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        レイラインの最適化分析
        
        Parameters:
        -----------
        df : pd.DataFrame
            セーリングデータフレーム
        marks : List[Dict[str, Any]], optional
            マーク情報のリスト
            
        Returns:
        --------
        Dict[str, Any]
            レイライン分析結果
        """
        # 処理状態の更新
        self._update_processing_status(True, 0.0, "レイライン分析を開始しています...", "initialize")
        
        try:
            # まず風推定を実行
            self._update_processing_status(True, 20.0, "風推定を実行しています...", "estimate_wind")
            
            if not self.wind_estimator:
                self._update_processing_status(False, 100.0, "風推定器が利用できません", "error")
                return {"error": "風推定器が利用できません"}
                
            wind_result = self.wind_estimator.estimate_wind(df)
            
            if "error" in wind_result:
                self._update_processing_status(False, 100.0, f"風推定エラー: {wind_result['error']}", "error")
                return {"error": f"風推定エラー: {wind_result['error']}"}
            
            # マークが指定されていない場合は、データの範囲から生成
            if marks is None or len(marks) == 0:
                self._update_processing_status(True, 40.0, "仮想マークを生成しています...", "create_marks")
                marks = self._create_virtual_marks(df)
            
            # VMG最適角度を取得
            self._update_processing_status(True, 50.0, "VMG最適角度を計算しています...", "calculate_vmg")
            wind_speed = wind_result["wind"]["speed"]
            optimal_angles = self.wind_estimator.get_optimal_vmg_angles(wind_speed)
            
            if not optimal_angles:
                optimal_upwind_angle = 42.0  # デフォルト値
                optimal_downwind_angle = 150.0  # デフォルト値
            else:
                optimal_upwind_angle = optimal_angles.get("upwind_angle", 42.0)
                optimal_downwind_angle = optimal_angles.get("downwind_angle", 150.0)
            
            # 各マークについてレイラインを計算
            self._update_processing_status(True, 60.0, "レイラインを計算しています...", "calculate_laylines")
            
            laylines = []
            wind_direction = wind_result["wind"]["direction"]
            
            for mark in marks:
                mark_id = mark.get("id", str(len(laylines)))
                mark_lat = mark.get("latitude")
                mark_lon = mark.get("longitude")
                mark_type = mark.get("type", "windward")  # 風上/風下マーク
                
                # マークの座標が有効かチェック
                if mark_lat is None or mark_lon is None:
                    continue
                
                # マークに対する2つのレイライン（左右）を計算
                if mark_type == "windward":
                    # 風上マークの場合
                    starboard_angle = (wind_direction - optimal_upwind_angle) % 360
                    port_angle = (wind_direction + optimal_upwind_angle) % 360
                else:
                    # 風下マークの場合
                    starboard_angle = (wind_direction - optimal_downwind_angle) % 360
                    port_angle = (wind_direction + optimal_downwind_angle) % 360
                
                # 安全マージンを追加（デフォルト10度）
                safety_margin = 10.0
                if self.parameters_manager:
                    strategy_params = self.parameters_manager.get_parameters_by_namespace(ParameterNamespace.STRATEGY_DETECTION)
                    safety_margin = strategy_params.get("layline_safety_margin", 10.0)
                
                # マージンを適用
                if mark_type == "windward":
                    starboard_angle = (starboard_angle + safety_margin) % 360
                    port_angle = (port_angle - safety_margin) % 360
                else:
                    starboard_angle = (starboard_angle - safety_margin) % 360
                    port_angle = (port_angle + safety_margin) % 360
                
                # レイラインポイントを生成
                # スターボードタックのレイライン
                starboard_layline = {
                    "mark_id": mark_id,
                    "mark_position": [mark_lat, mark_lon],
                    "mark_type": mark_type,
                    "tack": "starboard",
                    "approach_angle": starboard_angle,
                    "layline_positions": self._calculate_layline_positions(mark_lat, mark_lon, starboard_angle, 5)
                }
                
                # ポートタックのレイライン
                port_layline = {
                    "mark_id": mark_id,
                    "mark_position": [mark_lat, mark_lon],
                    "mark_type": mark_type,
                    "tack": "port",
                    "approach_angle": port_angle,
                    "layline_positions": self._calculate_layline_positions(mark_lat, mark_lon, port_angle, 5)
                }
                
                laylines.append(starboard_layline)
                laylines.append(port_layline)
            
            # レイライン分析結果の作成
            self._update_processing_status(True, 90.0, "分析結果を集計しています...", "format_results")
            
            result = {
                "laylines": laylines,
                "marks": marks,
                "wind_direction": wind_direction,
                "wind_speed": wind_speed,
                "optimal_upwind_angle": optimal_upwind_angle,
                "optimal_downwind_angle": optimal_downwind_angle,
                "safety_margin": safety_margin
            }
            
            # 処理完了
            self._update_processing_status(False, 100.0, "レイライン分析が完了しました", "complete")
            
            return result
            
        except Exception as e:
            error_msg = f"レイライン分析中にエラーが発生しました: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self._update_processing_status(False, 100.0, error_msg, "error")
            return {"error": error_msg}
    
    def _create_virtual_marks(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        航跡データから仮想マークを生成
        
        Parameters:
        -----------
        df : pd.DataFrame
            セーリングデータフレーム
            
        Returns:
        --------
        List[Dict[str, Any]]
            マーク情報のリスト
        """
        # 位置の範囲を取得
        lat_min, lat_max = df["latitude"].min(), df["latitude"].max()
        lon_min, lon_max = df["longitude"].min(), df["longitude"].max()
        
        # 中心点を計算
        center_lat = (lat_min + lat_max) / 2
        center_lon = (lon_min + lon_max) / 2
        
        # 範囲のサイズ
        lat_range = lat_max - lat_min
        lon_range = lon_max - lon_min
        
        # 風上と風下のマークを生成
        marks = [
            {
                "id": "windward_mark",
                "name": "風上マーク",
                "type": "windward",
                "latitude": center_lat + lat_range * 0.4,
                "longitude": center_lon
            },
            {
                "id": "leeward_mark",
                "name": "風下マーク",
                "type": "leeward",
                "latitude": center_lat - lat_range * 0.4,
                "longitude": center_lon
            }
        ]
        
        return marks
    
    def _calculate_layline_positions(self, mark_lat: float, mark_lon: float, 
                                 angle: float, points: int = 5) -> List[List[float]]:
        """
        マークからのレイラインの位置を計算
        
        Parameters:
        -----------
        mark_lat : float
            マークの緯度
        mark_lon : float
            マークの経度
        angle : float
            進入角度（度）
        points : int, optional
            生成するポイント数
            
        Returns:
        --------
        List[List[float]]
            [緯度, 経度]のリスト
        """
        # 地球半径（メートル）
        earth_radius = 6371000
        
        # レイラインの長さ（メートル）
        layline_length = 1000  # 1km
        
        # 角度をラジアンに変換（北が0、時計回り）
        angle_rad = math.radians(90 - angle)  # 方位から方角への変換
        
        # 各ポイントの距離
        distances = np.linspace(0, layline_length, points)
        
        positions = []
        for dist in distances:
            # 球面上の距離計算
            angular_distance = dist / earth_radius
            
            # 新しい緯度・経度を計算
            new_lat = math.asin(
                math.sin(math.radians(mark_lat)) * math.cos(angular_distance) +
                math.cos(math.radians(mark_lat)) * math.sin(angular_distance) * math.cos(angle_rad)
            )
            
            new_lon = math.radians(mark_lon) + math.atan2(
                math.sin(angle_rad) * math.sin(angular_distance) * math.cos(math.radians(mark_lat)),
                math.cos(angular_distance) - math.sin(math.radians(mark_lat)) * math.sin(new_lat)
            )
            
            # ラジアンから度に変換
            new_lat = math.degrees(new_lat)
            new_lon = math.degrees(new_lon)
            
            positions.append([new_lat, new_lon])
        
        return positions
    
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
    
    def _calculate_angle_difference(self, angle1: float, angle2: float) -> float:
        """
        2つの角度間の最小差分を計算（-180〜180度の範囲）
        
        Parameters:
        -----------
        angle1 : float
            1つ目の角度（度）
        angle2 : float
            2つ目の角度（度）
            
        Returns:
        --------
        float
            角度差（度）
        """
        return ((angle1 - angle2 + 180) % 360) - 180
    
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
    
    def _hash_course_data(self, course_data: Dict[str, Any]) -> str:
        """
        コース情報のハッシュ値を計算
        
        Parameters:
        -----------
        course_data : Dict[str, Any]
            コース情報
            
        Returns:
        --------
        str
            ハッシュ値
        """
        import hashlib
        import json
        
        # 簡略化したコース情報
        simplified_data = {
            "name": course_data.get("name", ""),
            "center": course_data.get("center", []),
            "boundary": course_data.get("boundary", []),
            "legs_count": len(course_data.get("legs", [])),
        }
        
        # レグ情報の追加
        if "legs" in course_data and course_data["legs"]:
            legs_info = []
            for leg in course_data["legs"]:
                legs_info.append({
                    "name": leg.get("name", ""),
                    "start": [leg.get("start", {}).get("lat"), leg.get("start", {}).get("lon")],
                    "end": [leg.get("end", {}).get("lat"), leg.get("end", {}).get("lon")],
                })
            simplified_data["legs_info"] = legs_info
        
        # ハッシュの作成
        hash_str = json.dumps(simplified_data, sort_keys=True)
        hash_value = hashlib.md5(hash_str.encode('utf-8')).hexdigest()
        
        return hash_value
    
    def _hash_wind_field(self, wind_field: Dict[str, Any]) -> str:
        """
        風の場データのハッシュ値を計算
        
        Parameters:
        -----------
        wind_field : Dict[str, Any]
            風の場データ
            
        Returns:
        --------
        str
            ハッシュ値
        """
        import hashlib
        import json
        
        if wind_field is None:
            return "no_wind_field"
        
        # 簡略化した風の場情報
        simplified_data = {
            "source": wind_field.get("source", ""),
            "time": str(wind_field.get("time", "")),
        }
        
        # 風向風速の平均値
        if "wind_direction" in wind_field and isinstance(wind_field["wind_direction"], np.ndarray):
            simplified_data["avg_direction"] = float(np.mean(wind_field["wind_direction"]))
        
        if "wind_speed" in wind_field and isinstance(wind_field["wind_speed"], np.ndarray):
            simplified_data["avg_speed"] = float(np.mean(wind_field["wind_speed"]))
        
        # グリッドサイズ
        if "lat_grid" in wind_field and isinstance(wind_field["lat_grid"], np.ndarray):
            simplified_data["grid_shape"] = wind_field["lat_grid"].shape
        
        # メタデータ
        if "metadata" in wind_field:
            simplified_data["metadata"] = wind_field["metadata"]
        
        # ハッシュの作成
        hash_str = json.dumps(simplified_data, sort_keys=True)
        hash_value = hashlib.md5(hash_str.encode('utf-8')).hexdigest()
        
        return hash_value
