"""
最適化された戦略検出器モジュール - パフォーマンス最適化

このモジュールは、既存のStrategyDetectorWithPropagationを拡張し、
大規模データ処理時のパフォーマンスと安定性を向上させる改良を加えています。
"""

# モジュールインポート
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union, Any
from datetime import datetime, timedelta
import math
import warnings
from functools import lru_cache

# 内部モジュールのインポート
from sailing_data_processor.strategy.strategy_detector_with_propagation import StrategyDetectorWithPropagation
from sailing_data_processor.strategy.points import StrategyPoint, WindShiftPoint, TackPoint, LaylinePoint
from sailing_data_processor.optimized_wind_field_fusion_system import OptimizedWindFieldFusionSystem

class OptimizedStrategyDetector(StrategyDetectorWithPropagation):
    """
    最適化された戦略検出器
    
    StrategyDetectorWithPropagationのパフォーマンスを最適化し、
    大規模データセットでの処理効率を向上させる拡張クラス。
    
    主な改良点:
    - 複雑な戦略計算の最適化
    - タイムスタンプ処理の改善
    - ポイントフィルタリングの効率化
    - メモリ使用量の削減
    - 計算キャッシュの活用
    """
    
    def __init__(self, vmg_calculator=None, wind_fusion_system=None):
        """
        初期化
        
        Parameters:
        -----------
        vmg_calculator : OptimalVMGCalculator, optional
            VMG計算機
        wind_fusion_system : WindFieldFusionSystem or OptimizedWindFieldFusionSystem, optional
            風統合システム
        """
        # 親クラスの初期化
        super().__init__(vmg_calculator, wind_fusion_system)
        
        # 最適化設定
        self.optimization_config = {
            'use_caching': True,           # 計算結果のキャッシュを使用
            'limit_search_depth': True,    # 深い検索を制限して計算効率向上
            'batch_processing': True,      # バッチ処理で処理効率向上
            'early_filtering': True,       # 早期フィルタリングで不要な計算を回避
            'adaptive_resolution': True    # データ量に応じた解像度調整
        }
        
        # キャッシュ
        self.timestamp_cache = {}  # タイムスタンプ変換用キャッシュ
        self.distance_cache = {}   # 距離計算用キャッシュ
        self.angle_cache = {}      # 角度計算用キャッシュ
        
    def detect_wind_shifts_with_propagation(self, course_data: Dict[str, Any], 
                                         wind_field: Dict[str, Any]) -> List[WindShiftPoint]:
        """
        風の移動を考慮した風向シフトポイントの検出（最適化版）
        
        Parameters:
        -----------
        course_data : Dict[str, Any]
            コース計算結果
        wind_field : Dict[str, Any]
            風の場データ
            
        Returns:
        --------
        List[WindShiftPoint]
            検出された風向シフトポイント
        """
        # パスポイントの事前評価と処理対象の絞り込み
        course_data = self._preprocess_course_data(course_data)
        
        # 親クラスのメソッド呼び出し
        wind_shifts = super().detect_wind_shifts_with_propagation(
            course_data, wind_field)
        
        return wind_shifts
    
    def _preprocess_course_data(self, course_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        コースデータを前処理して最適化
        
        Parameters:
        -----------
        course_data : Dict[str, Any]
            コースデータ
            
        Returns:
        --------
        Dict[str, Any]
            最適化されたコースデータ
        """
        # コースデータのコピーを作成
        preprocessed_data = course_data.copy()
        
        if 'legs' not in preprocessed_data:
            return preprocessed_data
        
        # 各レグを処理
        for leg_idx, leg in enumerate(preprocessed_data['legs']):
            if 'path' not in leg or 'path_points' not in leg['path']:
                continue
            
            path_points = leg['path']['path_points']
            
            # 解像度の調整が有効な場合
            if self.optimization_config['adaptive_resolution'] and len(path_points) > 100:
                # 適切なサンプリングレートを計算
                sample_rate = max(1, len(path_points) // 50)  # 最大50ポイントに削減
                
                # スキップはしない方が良いインデックスを特定
                key_indices = self._identify_key_path_indices(path_points)
                
                # サンプリングされたポイントと重要ポイントを結合
                sampled_points = []
                for i in range(0, len(path_points), sample_rate):
                    sampled_points.append(path_points[i])
                
                # 重要ポイントが含まれていない場合は追加
                for idx in key_indices:
                    if all(p != path_points[idx] for p in sampled_points):
                        sampled_points.append(path_points[idx])
                
                # ソートして順序を維持
                if 'time' in path_points[0]:
                    sampled_points.sort(key=lambda p: p['time'])
                
                # 結果を設定
                preprocessed_data['legs'][leg_idx]['path']['path_points'] = sampled_points
        
        return preprocessed_data
    
    def _identify_key_path_indices(self, path_points: List[Dict[str, Any]]) -> List[int]:
        """
        パス内の重要なポイントのインデックスを特定
        
        Parameters:
        -----------
        path_points : List[Dict]
            パスポイントのリスト
            
        Returns:
        --------
        List[int]
            重要なポイントのインデックス
        """
        key_indices = []
        
        # 最初と最後のポイントは常に重要
        key_indices.append(0)
        key_indices.append(len(path_points) - 1)
        
        # コースの変化が大きい箇所を重要とみなす
        if len(path_points) >= 3 and 'course' in path_points[0]:
            for i in range(1, len(path_points) - 1):
                prev_course = path_points[i-1].get('course', 0)
                curr_course = path_points[i].get('course', 0)
                next_course = path_points[i+1].get('course', 0)
                
                # コース変化を計算
                course_change1 = abs(self._calculate_angle_difference(curr_course, prev_course))
                course_change2 = abs(self._calculate_angle_difference(next_course, curr_course))
                
                # 大きな変化がある場合
                if course_change1 > 10 or course_change2 > 10:
                    key_indices.append(i)
        
        # ユニークにして返す
        return sorted(list(set(key_indices)))
    
    def _normalize_to_timestamp(self, t) -> float:
        """
        任意の時間表現を統一された浮動小数点秒数に変換（最適化版）
        
        Parameters:
        -----------
        t : any
            変換する時間値（datetime, timedelta, int, float等）
            
        Returns:
        --------
        float
            UNIX時間または秒数
        """
        # キャッシュを使用
        if self.optimization_config['use_caching']:
            # オブジェクトIDをキーとして使用（イミュータブルでない型対応）
            cache_key = id(t)
            if cache_key in self.timestamp_cache:
                return self.timestamp_cache[cache_key]
        
        # 型に基づいた効率的な変換
        result = None
        
        if isinstance(t, datetime):
            # datetimeはUNIX時間（エポックからの秒数）に変換
            result = t.timestamp()
        elif isinstance(t, timedelta):
            # timedeltaは秒数に変換
            result = t.total_seconds()
        elif isinstance(t, (int, float)):
            # 数値はそのまま秒数として使用
            result = float(t)
        elif isinstance(t, dict) and 'timestamp' in t:
            # timestamp キーを持つ辞書型の場合、再帰的に処理
            result = self._normalize_to_timestamp(t['timestamp'])
        elif isinstance(t, str):
            try:
                # 数値文字列の場合は数値変換
                result = float(t)
            except ValueError:
                try:
                    # ISO形式の日時文字列の場合
                    dt = datetime.fromisoformat(t.replace('Z', '+00:00'))
                    result = dt.timestamp()
                except (ValueError, TypeError):
                    # 変換できない場合は無限大を返す
                    result = float('inf')
        else:
            # その他の型は文字列化して数値変換を試みる
            try:
                result = float(str(t))
            except (ValueError, TypeError):
                # 変換できなければ無限大を返す（比較不能）
                result = float('inf')
        
        # キャッシュに保存
        if self.optimization_config['use_caching']:
            self.timestamp_cache[cache_key] = result
        
        return result

    def _get_time_difference_seconds(self, time1, time2) -> float:
        """
        異なる時間タイプ間の差分を秒で取得するヘルパー関数（最適化版）
        
        Parameters:
        -----------
        time1, time2 : any
            比較する時間値（datetime, timedelta, int, float, etc）
            
        Returns:
        --------
        float
            時間差（秒）、変換できない場合は無限大
        """
        # 両方の時間を正規化して差の絶対値を返す
        try:
            ts1 = self._normalize_to_timestamp(time1)
            ts2 = self._normalize_to_timestamp(time2)
            
            # いずれかが無限大の場合は比較不能
            if ts1 == float('inf') or ts2 == float('inf'):
                return float('inf')
                
            return abs(ts1 - ts2)
        except Exception as e:
            # エラーが発生した場合は無限大を返す
            return float('inf')
    
    def _filter_duplicate_shift_points(self, shift_points: List[WindShiftPoint]) -> List[WindShiftPoint]:
        """
        重複する風向シフトポイントをフィルタリング（最適化版）
        
        Parameters:
        -----------
        shift_points : List[WindShiftPoint]
            シフトポイントのリスト
            
        Returns:
        --------
        List[WindShiftPoint]
            フィルタリング後のシフトポイントリスト
        """
        if len(shift_points) <= 1:
            return shift_points
        
        # 最適化: 空間インデックスを使用して検索を高速化
        if self.optimization_config['batch_processing']:
            return self._batch_filter_duplicate_points(shift_points)
        
        # 通常のフィルタリング処理（個別比較）
        filtered_points = []
        sorted_points = sorted(shift_points, key=lambda p: self._normalize_to_timestamp(p.time_estimate))
        
        for point in sorted_points:
            is_duplicate = False
            
            for existing in filtered_points:
                # 位置的に近いか（300m以内）
                position_close = self._calculate_distance(
                    point.position[0], point.position[1],
                    existing.position[0], existing.position[1]
                ) < 300
                
                # 時間的に近いか（5分以内）
                time_diff = self._get_time_difference_seconds(point.time_estimate, existing.time_estimate)
                time_close = time_diff < 300
                
                # シフト角度が類似しているか（15度以内）
                angle_similar = abs(self._calculate_angle_difference(
                    point.shift_angle, existing.shift_angle
                )) < 15
                
                # 重複条件
                if position_close and time_close and angle_similar:
                    # 信頼度が高い方を保持
                    if point.shift_probability > existing.shift_probability:
                        # 既存ポイントを置き換え
                        filtered_points.remove(existing)
                        filtered_points.append(point)
                    
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                filtered_points.append(point)
        
        return filtered_points
    
    def _batch_filter_duplicate_points(self, points: List[Union[WindShiftPoint, TackPoint, LaylinePoint]]) -> List[Union[WindShiftPoint, TackPoint, LaylinePoint]]:
        """
        ポイントをバッチ処理でフィルタリング（高速化版）
        
        Parameters:
        -----------
        points : List[Union[WindShiftPoint, TackPoint, LaylinePoint]]
            フィルタリング対象のポイントリスト
            
        Returns:
        --------
        List[Union[WindShiftPoint, TackPoint, LaylinePoint]]
            フィルタリング後のポイントリスト
        """
        if len(points) <= 1:
            return points
        
        # ポイントの種類を判断
        point_type = type(points[0])
        
        # バッチ処理のためのNumPy配列を準備
        positions = np.array([(p.position[0], p.position[1]) for p in points])
        timestamps = np.array([self._normalize_to_timestamp(p.time_estimate) for p in points])
        
        # ポイント種類に応じた特徴量を取得
        if point_type == WindShiftPoint:
            features = np.array([p.shift_angle for p in points])
            qualities = np.array([p.shift_probability for p in points])
            feature_thresh = 15  # 角度差15度以内は類似
            
        elif point_type == TackPoint:
            features = np.array([p.vmg_gain for p in points])
            qualities = np.array([p.vmg_gain for p in points])
            feature_thresh = 0.05  # VMG利得の差5%以内は類似
            
        elif point_type == LaylinePoint:
            features = np.array([p.mark_distance for p in points])
            qualities = np.array([p.confidence for p in points])
            feature_thresh = 100  # 距離差100m以内は類似
            
        else:
            # 未知のポイント型は通常処理で
            return self._filter_duplicate_shift_points(points)
        
        # グループ分けの結果（各ポイントの所属グループID）
        group_ids = np.zeros(len(points), dtype=int)
        next_group_id = 1
        
        # すべてのポイントをグループ化
        for i in range(len(points)):
            # すでにグループ割り当て済みならスキップ
            if group_ids[i] > 0:
                continue
            
            # このポイントの新しいグループを作成
            group_ids[i] = next_group_id
            
            # このポイントと近いポイントを同じグループに
            for j in range(i + 1, len(points)):
                if group_ids[j] > 0:
                    continue
                
                # 位置的に近いか
                lat1, lon1 = positions[i]
                lat2, lon2 = positions[j]
                
                # 距離計算の高速化（キャッシュ使用）
                cache_key = (lat1, lon1, lat2, lon2)
                if cache_key in self.distance_cache:
                    distance = self.distance_cache[cache_key]
                else:
                    distance = self._calculate_distance(lat1, lon1, lat2, lon2)
                    self.distance_cache[cache_key] = distance
                
                position_close = distance < 300
                
                # 時間的に近いか
                time_diff = abs(timestamps[i] - timestamps[j])
                time_close = time_diff < 300  # 5分以内
                
                # 特徴量が類似しているか
                feature_diff = abs(features[i] - features[j])
                feature_similar = feature_diff < feature_thresh
                
                # 重複条件に合致する場合、同じグループに割り当て
                if position_close and (time_close or feature_similar):
                    group_ids[j] = next_group_id
            
            # 次のグループIDを準備
            next_group_id += 1
        
        # 各グループから最高品質のポイントを選択
        filtered_points = []
        
        for group_id in range(1, next_group_id):
            group_indices = np.where(group_ids == group_id)[0]
            
            if len(group_indices) == 0:
                continue
            
            # グループ内で最高品質のポイントを選択
            best_idx = group_indices[np.argmax(qualities[group_indices])]
            filtered_points.append(points[best_idx])
        
        return filtered_points
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        2点間の距離を計算（最適化版、キャッシュ対応）
        
        Parameters:
        -----------
        lat1, lon1 : float
            始点の緯度・経度
        lat2, lon2 : float
            終点の緯度・経度
            
        Returns:
        --------
        float
            距離（メートル）
        """
        # キャッシュチェック
        if self.optimization_config['use_caching']:
            cache_key = (lat1, lon1, lat2, lon2)
            if cache_key in self.distance_cache:
                return self.distance_cache[cache_key]
            
            # 逆順のキーでもチェック
            reverse_key = (lat2, lon2, lat1, lon1)
            if reverse_key in self.distance_cache:
                return self.distance_cache[reverse_key]
        
        # 地球の半径（メートル）
        R = 6371000
        
        # 緯度・経度をラジアンに変換
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # 差分
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        # Haversine公式
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c
        
        # キャッシュに保存
        if self.optimization_config['use_caching']:
            self.distance_cache[cache_key] = distance
        
        return distance
    
    def _calculate_angle_difference(self, angle1: float, angle2: float) -> float:
        """
        2つの角度の差を計算（最適化版、キャッシュ対応）
        
        Parameters:
        -----------
        angle1, angle2 : float
            角度（度）
            
        Returns:
        --------
        float
            角度差（度、-180〜180）
        """
        # キャッシュチェック
        if self.optimization_config['use_caching']:
            cache_key = (angle1, angle2)
            if cache_key in self.angle_cache:
                return self.angle_cache[cache_key]
        
        # 角度差の計算
        diff = (angle1 - angle2 + 180) % 360 - 180
        
        # キャッシュに保存
        if self.optimization_config['use_caching']:
            self.angle_cache[cache_key] = diff
        
        return diff
    
    def _filter_duplicate_tack_points(self, tack_points: List[TackPoint]) -> List[TackPoint]:
        """
        重複するタックポイントをフィルタリング（最適化版）
        
        Parameters:
        -----------
        tack_points : List[TackPoint]
            タックポイントのリスト
            
        Returns:
        --------
        List[TackPoint]
            フィルタリング後のタックポイントリスト
        """
        # 最適化: バッチ処理を使用
        if self.optimization_config['batch_processing']:
            return self._batch_filter_duplicate_points(tack_points)
        
        # 親クラスの実装を使用
        return super()._filter_duplicate_tack_points(tack_points)
    
    def _filter_duplicate_laylines(self, layline_points: List[LaylinePoint]) -> List[LaylinePoint]:
        """
        重複するレイラインポイントをフィルタリング（最適化版）
        
        Parameters:
        -----------
        layline_points : List[LaylinePoint]
            レイラインポイントのリスト
            
        Returns:
        --------
        List[LaylinePoint]
            フィルタリング後のレイラインポイントリスト
        """
        # 最適化: バッチ処理を使用
        if self.optimization_config['batch_processing']:
            return self._batch_filter_duplicate_points(layline_points)
        
        # 親クラスの実装を使用
        return super()._filter_duplicate_laylines(layline_points)
    
    def clear_caches(self):
        """
        すべてのキャッシュをクリア
        """
        self.timestamp_cache.clear()
        self.distance_cache.clear()
        self.angle_cache.clear()
