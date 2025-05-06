# -*- coding: utf-8 -*-
"""
Module for quality metrics calculation improvements.
This module provides extended functions for quality metrics calculation.
"""

from typing import Dict, List, Any, Optional, Tuple, Set
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

# ロギング設定
logger = logging.getLogger(__name__)

# 必要なモジュールを遅延インポートするための準備
try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    logger.warning("plotly モジュールをインポートできませんでした。視覚化機能は利用できません。")
    PLOTLY_AVAILABLE = False
    # モックオブジェクトを作成して他のコードが動作できるようにする
    class MockGo:
        def __init__(self):
            self.Figure = MockFigure
        def __getattr__(self, name):
            return MockClass()
    
    class MockFigure:
        def __init__(self, *args, **kwargs):
            pass
        def __getattr__(self, name):
            return lambda *args, **kwargs: None
    
    class MockClass:
        def __init__(self, *args, **kwargs):
            pass
        def __call__(self, *args, **kwargs):
            return MockFigure()
    
    go = MockGo()

# データモデルインポートエラーのリスクを回避するため、直接インポートは行わない
# 代わりに動的インポートまたはタイプヒントのみの参照を使用
try:
    from sailing_data_processor.data_model.container import GPSDataContainer
except ImportError:
    # インポートが失敗した場合でもクラス自体の定義は可能に
    pass

class QualityMetricsCalculatorExtension:
    """
    データ品質メトリクスの計算クラスの拡張部分
    これは既存のQualityMetricsCalculatorに追加される新しいメソッドを含む
    """
    
    def __init__(self, validation_results=None, data=None):
        """
        初期化メソッド - 簡略化バージョン
        元のクラスに対応するダミーの初期化メソッド
        
        Parameters
        ----------
        validation_results : List[Dict[str, Any]], optional
            DataValidatorから得られた検証結果
        data : pd.DataFrame, optional
            検証されたデータフレーム
        """
        # 簡略化した初期化
        self.validation_results = validation_results if validation_results else []
        self.data = data if data is not None else pd.DataFrame()
        self.problematic_indices = {
            "missing_data": [],
            "out_of_range": [],
            "duplicates": [],
            "spatial_anomalies": [],
            "temporal_anomalies": [],
            "all": []
        }
        
        # 検証結果から問題レコードのインデックスを抽出
        if validation_results:
            self._process_validation_results()
        
        # ルールカテゴリーの定義
        self.rule_categories = {
            "completeness": ["Required Columns Check", "No Null Values Check"],
            "accuracy": ["Value Range Check", "Spatial Consistency Check"],
            "consistency": ["No Duplicate Timestamps", "Temporal Consistency Check"]
        }
        
        # 品質スコアを簡略化
        self.quality_scores = {
            "completeness": 100.0,
            "accuracy": 100.0,
            "consistency": 100.0,
            "total": 100.0
        }
    
    def calculate_quality_scores(self) -> Dict[str, float]:
        """
        データ品質スコアを計算。
        
        0〜100の範囲で全体的なデータ品質を評価し、
        問題の重要度に基づく重み付け計算を行います。
        
        Returns
        -------
        Dict[str, float]
            各種品質スコア (total, completeness, accuracy, consistency)
        """
        # レコード総数を取得
        total_records = len(self.data)
        if total_records == 0:
            return {
                "total": 100.0,
                "completeness": 100.0,
                "accuracy": 100.0,
                "consistency": 100.0
            }
        
        # 問題のあるレコード数とその重み付け
        error_count = len(self.problematic_indices.get("all", set()))
        
        # 問題タイプごとの重み
        weights = {
            "missing_data": 1.0,  # エラー
            "out_of_range": 1.0,  # エラー
            "duplicates": 0.5,    # 警告
            "spatial_anomalies": 0.5,  # 警告
            "temporal_anomalies": 0.5  # 警告
        }
        
        # 重み付けされた問題スコアの計算
        weighted_sum = 0
        for problem_type, indices in self.problematic_indices.items():
            if problem_type != "all":
                weighted_sum += len(indices) * weights.get(problem_type, 0.1)
        
        # 総合スコアの計算（100点満点）
        total_score = max(0, 100 - (weighted_sum * 100 / total_records))
        
        # カテゴリ別スコアを計算
        category_scores = self.calculate_category_quality_scores()
        
        return {
            "total": round(total_score, 1),
            "completeness": category_scores["completeness"],
            "accuracy": category_scores["accuracy"],
            "consistency": category_scores["consistency"]
        }
    
    def calculate_category_quality_scores(self) -> Dict[str, float]:
        """
        カテゴリ別の品質スコアを計算。（基本バージョン）
        
        完全性（Completeness）: 欠損値や必須項目の充足度
        正確性（Accuracy）: 値の範囲や形式の正確さ
        一貫性（Consistency）: 時間的・空間的な整合性
        
        Returns
        -------
        Dict[str, float]
            カテゴリ別のスコア
        """
        total_records = len(self.data)
        if total_records == 0:
            return {
                "completeness": 100.0,
                "accuracy": 100.0,
                "consistency": 100.0
            }
        
        # カテゴリごとの問題数をカウント
        completeness_issues = len(self.problematic_indices.get("missing_data", []))
        accuracy_issues = len(self.problematic_indices.get("out_of_range", []))
        consistency_issues = len(self.problematic_indices.get("duplicates", [])) + \
                             len(self.problematic_indices.get("spatial_anomalies", [])) + \
                             len(self.problematic_indices.get("temporal_anomalies", []))
        
        # カラム数（欠損値チェック用）
        total_fields = len(self.data.columns) * total_records
        
        # スコアの計算
        completeness_score = max(0, 100 - (completeness_issues * 100 / total_fields))
        accuracy_score = max(0, 100 - (accuracy_issues * 100 / total_records))
        consistency_score = max(0, 100 - (consistency_issues * 100 / total_records))
        
        return {
            "completeness": round(completeness_score, 1),
            "accuracy": round(accuracy_score, 1),
            "consistency": round(consistency_score, 1)
        }
    
    def _process_validation_results(self):
        """
        検証結果から問題のあるレコードのインデックスを抽出する
        
        validation_resultsを解析して、各問題タイプに対応するインデックスを抽出し、
        problematic_indicesディクショナリを更新します。
        """
        # 問題インデックスをリセット
        self.problematic_indices = {
            "missing_data": [],
            "out_of_range": [],
            "duplicates": [],
            "spatial_anomalies": [],
            "temporal_anomalies": [],
            "all": []
        }
        
        # 各検証結果を処理
        for result in self.validation_results:
            if not result.get("is_valid", True):
                rule_name = result.get("rule_name", "")
                details = result.get("details", {})
                
                # ルールタイプに基づいて問題インデックスを抽出
                if "No Null Values Check" in rule_name:
                    # Null値のインデックスを抽出
                    null_indices = []
                    for col, indices in details.get("null_indices", {}).items():
                        if indices:
                            null_indices.extend(indices)
                    
                    if null_indices:
                        self.problematic_indices["missing_data"].extend(null_indices)
                        self.problematic_indices["all"].extend(null_indices)
                
                elif "Value Range Check" in rule_name:
                    # 範囲外の値のインデックスを抽出
                    out_indices = details.get("out_of_range_indices", [])
                    if out_indices:
                        self.problematic_indices["out_of_range"].extend(out_indices)
                        self.problematic_indices["all"].extend(out_indices)
                
                elif "No Duplicate Timestamps" in rule_name:
                    # 重複タイムスタンプのインデックスを抽出
                    dup_indices = []
                    for ts, indices in details.get("duplicate_indices", {}).items():
                        if indices:
                            dup_indices.extend(indices)
                    
                    if dup_indices:
                        self.problematic_indices["duplicates"].extend(dup_indices)
                        self.problematic_indices["all"].extend(dup_indices)
                
                elif "Spatial Consistency Check" in rule_name:
                    # 空間的異常のインデックスを抽出
                    spatial_indices = details.get("anomaly_indices", [])
                    if spatial_indices:
                        self.problematic_indices["spatial_anomalies"].extend(spatial_indices)
                        self.problematic_indices["all"].extend(spatial_indices)
                
                elif "Temporal Consistency Check" in rule_name:
                    # 時間的異常のインデックスを抽出
                    gap_indices = details.get("gap_indices", [])
                    reverse_indices = details.get("reverse_indices", [])
                    temporal_indices = gap_indices + reverse_indices
                    
                    if temporal_indices:
                        self.problematic_indices["temporal_anomalies"].extend(temporal_indices)
                        self.problematic_indices["all"].extend(temporal_indices)
        
        # 重複を除去し、ソート
        for key in self.problematic_indices:
            self.problematic_indices[key] = sorted(list(set(self.problematic_indices[key])))
            
    def _calculate_problem_type_distribution_for_period(self, indices):
        """
        特定期間の問題タイプ分布を計算
        
        Parameters
        ----------
        indices : List[int]
            対象期間のインデックスリスト
            
        Returns
        -------
        Dict[str, int]
            問題タイプごとのカウント
        """
        # 問題タイプごとのカウントを初期化
        problem_counts = {
            "missing_data": 0,
            "out_of_range": 0,
            "duplicates": 0,
            "spatial_anomalies": 0,
            "temporal_anomalies": 0
        }
        
        # インデックスが問題タイプに含まれているかチェック
        for problem_type, problem_indices in self.problematic_indices.items():
            if problem_type != "all":
                # 対象期間のインデックスと問題インデックスの積集合
                problem_indices_in_period = set(indices).intersection(set(problem_indices))
                problem_counts[problem_type] = len(problem_indices_in_period)
        
        return problem_counts
    
    def _get_score_color(self, score: float) -> str:
        """
        スコアに応じた色を返す
        
        Parameters
        ----------
        score : float
            品質スコア（0-100）
            
        Returns
        -------
        str
            対応する色のHEXコード
        """
        if score >= 90:
            return "#27AE60"  # 濃い緑
        elif score >= 75:
            return "#2ECC71"  # 緑
        elif score >= 50:
            return "#F1C40F"  # 黄色
        elif score >= 25:
            return "#E67E22"  # オレンジ
        else:
            return "#E74C3C"  # 赤
            
    def _determine_impact_level(self, score: float) -> str:
        """
        品質スコアから影響レベルを決定する
        
        Parameters
        ----------
        score : float
            品質スコア (0-100)
            
        Returns
        -------
        str
            影響レベル
        """
        if score >= 90:
            return "low"       # 低影響
        elif score >= 75:
            return "medium"    # 中程度の影響
        elif score >= 50:
            return "high"      # 高影響
        else:
            return "critical"  # 重大な影響
            
    def get_quality_summary(self) -> Dict[str, Any]:
        """
        データ品質の要約情報を取得
        
        Returns
        -------
        Dict[str, Any]
            品質サマリー
        """
        # 問題件数のカウント
        total_issues = len(self.problematic_indices.get("all", []))
        missing_data_count = len(self.problematic_indices.get("missing_data", []))
        out_of_range_count = len(self.problematic_indices.get("out_of_range", []))
        dupes_count = len(self.problematic_indices.get("duplicates", []))
        spatial_count = len(self.problematic_indices.get("spatial_anomalies", []))
        temporal_count = len(self.problematic_indices.get("temporal_anomalies", []))
        
        # 品質サマリーを構築
        return {
            "overall_score": self.quality_scores.get("total", 100.0),
            "completeness_score": self.quality_scores.get("completeness", 100.0),
            "accuracy_score": self.quality_scores.get("accuracy", 100.0),
            "consistency_score": self.quality_scores.get("consistency", 100.0),
            "total_issues": total_issues,
            "issue_counts": {
                "missing_data": missing_data_count,
                "out_of_range": out_of_range_count,
                "duplicates": dupes_count,
                "spatial_anomalies": spatial_count,
                "temporal_anomalies": temporal_count
            },
            "impact_level": self._determine_impact_level(self.quality_scores.get("total", 100.0))
        }
        
    def _calculate_precision_score(self) -> float:
        """
        精度スコアを計算する
        
        Returns
        -------
        float
            精度スコア (0-100)
        """
        # 範囲外の値などの精度に関わる問題をカウント
        out_of_range_issues = 0
        spatial_anomalies = 0
        
        # バリデーション結果から範囲外問題と空間的異常をカウント
        for result in self.validation_results:
            if not result.get("is_valid", True):
                details = result.get("details", {})
                if result.get("rule_name") == "Value Range Check":
                    out_of_range_issues += details.get("out_of_range_count", 0)
                elif result.get("rule_name") == "Spatial Consistency Check":
                    spatial_anomalies += details.get("anomaly_count", 0)
        
        # 問題の総数を計算
        precision_issues = out_of_range_issues + spatial_anomalies
        
        # データ全体に対する問題の割合を計算
        total_records = len(self.data) if not self.data.empty else 1
        precision_score = 100.0 * (1 - (precision_issues / total_records))
        
        # 問題件数に基づくペナルティを適用
        if precision_issues > 0:
            # 問題が多いほどペナルティが大きくなる
            penalty = min(30.0, precision_issues * 2.0)
            precision_score = max(0.0, precision_score - penalty)
        
        # スコアの範囲を0-100に調整
        return max(0.0, min(100.0, precision_score))

    def _calculate_validity_score(self) -> float:
        """
        妥当性スコアを計算する
        
        Returns
        -------
        float
            妥当性スコア (0-100)
        """
        # 時間的異常などの妥当性に関わる問題をカウント
        temporal_anomalies = 0
        duplication_issues = 0
        
        # バリデーション結果から時間的異常と重複問題をカウント
        for result in self.validation_results:
            if not result.get("is_valid", True):
                details = result.get("details", {})
                if result.get("rule_name") == "Temporal Consistency Check":
                    temporal_anomalies += details.get("reverse_count", 0)
                elif result.get("rule_name") == "No Duplicate Timestamps":
                    duplication_issues += details.get("duplicate_count", 0)
        
        # 問題の総数を計算
        validity_issues = temporal_anomalies + duplication_issues
        
        # データ全体に対する問題の割合を計算
        total_records = len(self.data) if not self.data.empty else 1
        validity_score = 100.0 * (1 - (validity_issues / total_records))
        
        # 問題件数に基づくペナルティを適用
        if validity_issues > 0:
            # 時間的整合性は重要なので、より大きなペナルティを適用
            penalty = min(40.0, validity_issues * 3.0)
            validity_score = max(0.0, validity_score - penalty)
        
        # スコアの範囲を0-100に調整
        return max(0.0, min(100.0, validity_score))
        
    def _calculate_uniformity_score(self, intervals: List[float]) -> float:
        """
        データの均一性スコアを計算する
        
        Parameters
        ----------
        intervals : List[float]
            データポイント間の間隔
        
        Returns
        -------
        float
            均一性スコア (0-100)
        """
        if not intervals or len(intervals) <= 1:
            return 0.0  # 間隔データが不十分な場合はスコア0
        
        # 空のリストや無効な値をフィルタリング
        valid_intervals = [interval for interval in intervals if interval is not None and not np.isnan(interval) and interval > 0]
        
        # 有効な間隔が少なすぎる場合
        if len(valid_intervals) <= 1:
            return 0.0  # 判断できない場合もスコア0
        
        # 間隔の標準偏差を計算
        mean_interval = np.mean(valid_intervals)
        std_interval = np.std(valid_intervals)
        
        # 変動係数（標準偏差/平均）を計算
        cv = std_interval / mean_interval if mean_interval > 0 else float('inf')
        
        # 極端な値の検出（平均から標準偏差の3倍以上外れた値）
        outlier_count = 0
        for interval in valid_intervals:
            if abs(interval - mean_interval) > 3 * std_interval:
                outlier_count += 1
        
        # 変動係数からスコアを計算（変動係数が小さいほど均一）
        # 変動係数0は完全に均一、経験的に0.5以上は非常に不均一と仮定
        uniformity_score = 100.0 * (1 - min(1.0, cv / 0.5))
        
        # 極端な値によるペナルティを適用
        if outlier_count > 0:
            outlier_penalty = min(20.0, outlier_count * 5.0)
            uniformity_score = max(0.0, uniformity_score - outlier_penalty)
        
        return max(0.0, min(100.0, uniformity_score))
        
    def calculate_spatial_quality_scores(self) -> List[Dict[str, Any]]:
        """
        空間グリッド別の品質スコアを計算。
        
        データを空間的なグリッドに分割し、各グリッドの品質スコアと問題情報を計算します。
        これにより、空間的な品質変動を視覚的に把握できます。
        
        Returns
        -------
        List[Dict[str, Any]]
            各グリッドの品質情報
        """
        # 位置情報カラムがない場合
        if "latitude" not in self.data.columns or "longitude" not in self.data.columns:
            return []
            
        try:
            # 有効な位置情報を持つレコードのみを抽出
            valid_data = self.data.dropna(subset=["latitude", "longitude"])
            
            if len(valid_data) < 5:  # 最低5ポイント必要
                return []
                
            # 問題のあるすべてのレコードのインデックス
            all_problem_indices = self.problematic_indices["all"]
            
            # 位置の範囲を取得
            min_lat = valid_data["latitude"].min()
            max_lat = valid_data["latitude"].max()
            min_lon = valid_data["longitude"].min()
            max_lon = valid_data["longitude"].max()
            
            # 適切なグリッドサイズを決定（5x5グリッド）
            lat_bins = 5
            lon_bins = 5
            
            # 範囲が狭すぎる場合は調整
            if max_lat - min_lat < 0.001:
                center_lat = (max_lat + min_lat) / 2
                min_lat = center_lat - 0.005
                max_lat = center_lat + 0.005
                
            if max_lon - min_lon < 0.001:
                center_lon = (max_lon + min_lon) / 2
                min_lon = center_lon - 0.005
                max_lon = center_lon + 0.005
                
            lat_step = (max_lat - min_lat) / lat_bins
            lon_step = (max_lon - min_lon) / lon_bins
            
            # グリッドごとの品質スコアを計算
            spatial_scores = []
            
            for i in range(lat_bins):
                lat_start = min_lat + lat_step * i
                lat_end = min_lat + lat_step * (i + 1)
                
                for j in range(lon_bins):
                    lon_start = min_lon + lon_step * j
                    lon_end = min_lon + lon_step * (j + 1)
                    
                    # グリッド内のレコードを抽出
                    grid_mask = ((valid_data["latitude"] >= lat_start) & 
                                (valid_data["latitude"] < lat_end) & 
                                (valid_data["longitude"] >= lon_start) & 
                                (valid_data["longitude"] < lon_end))
                    grid_indices = valid_data.index[grid_mask].tolist()
                    
                    if grid_indices:  # グリッド内にデータがある場合
                        # グリッド内の問題レコード数
                        problem_indices_in_grid = set(grid_indices).intersection(set(all_problem_indices))
                        problem_count = len(problem_indices_in_grid)
                        total_count = len(grid_indices)
                        
                        # 問題の割合に基づく品質スコア
                        problem_percentage = problem_count / total_count * 100 if total_count > 0 else 0
                        quality_score = max(0, 100 - problem_percentage)
                        
                        # グリッドの中心座標
                        center_lat = (lat_start + lat_end) / 2
                        center_lon = (lon_start + lon_end) / 2
                        
                        # グリッドIDを生成
                        grid_id = f"grid_{i}_{j}"
                        
                        # 問題タイプごとの分布も計算
                        problem_type_distribution = self._calculate_problem_type_distribution_for_period(grid_indices)
                        
                        # 品質スコアを保存
                        spatial_scores.append({
                            "grid_id": grid_id,
                            "center": [center_lat, center_lon],
                            "bounds": {
                                "min_lat": lat_start,
                                "max_lat": lat_end,
                                "min_lon": lon_start,
                                "max_lon": lon_end
                            },
                            "quality_score": quality_score,
                            "problem_count": problem_count,
                            "total_count": total_count,
                            "problem_percentage": problem_percentage,
                            "impact_level": self._determine_impact_level(quality_score)
                        })
            
            return spatial_scores
            
        except Exception as e:
            # エラーが発生した場合は空のリストを返す
            print(f"空間的な品質スコア計算中にエラー: {e}")
            return []
            
    def calculate_temporal_quality_scores(self) -> List[Dict[str, Any]]:
        """
        時間帯別の品質スコアを計算。
        
        データを時間帯ごとに分析し、それぞれの時間帯の品質スコアと問題情報を計算します。
        これにより、時間的な品質変動を特定できます。
        
        Returns
        -------
        List[Dict[str, Any]]
            各時間帯の品質情報
        """
        # タイムスタンプカラムがない場合
        if "timestamp" not in self.data.columns:
            return []
        
        try:
            # 有効なタイムスタンプのみを抽出
            valid_data = self.data.dropna(subset=["timestamp"])
            
            if len(valid_data) < 2:
                return []
            
            # タイムスタンプをdatetimeに変換
            timestamps = pd.to_datetime(valid_data["timestamp"])
            
            # 問題のあるすべてのレコードのインデックス
            all_problem_indices = self.problematic_indices["all"]
            
            # 時間範囲を決定
            min_time = timestamps.min()
            max_time = timestamps.max()
            
            # 期間が短すぎる場合は一つの時間帯として扱う
            time_range = (max_time - min_time).total_seconds()
            if time_range < 60:  # 1分未満
                # 最低1つは返す
                problem_count = 0
                for idx in self.data.index:
                    if idx in all_problem_indices:
                        problem_count += 1
                
                quality_score = 100.0
                if len(self.data) > 0:
                    quality_score = 100.0 * (1 - (problem_count / len(self.data)))
                    
                period_info = {
                    "period": 0,
                    "start_time": min_time.isoformat(),
                    "end_time": max_time.isoformat(),
                    "label": f"{min_time.strftime('%H:%M')} - {max_time.strftime('%H:%M')}",
                    "quality_score": quality_score,
                    "problem_count": problem_count,
                    "total_count": len(self.data),
                    "problem_percentage": 100.0 * problem_count / len(self.data) if len(self.data) > 0 else 0.0,
                    "impact_level": self._determine_impact_level(quality_score)
                }
                
                return [period_info]
            
            # 時間帯の数（簡易的に固定値）
            period_count = min(5, max(1, int(time_range / 600)))  # 10分ごとに区切る（最大5区間）
            
            # 時間帯の作成
            period_duration = timedelta(seconds=time_range / period_count)
            periods = []
            
            for i in range(period_count):
                period_start = min_time + i * period_duration
                period_end = min_time + (i + 1) * period_duration
                
                # 時間帯のラベル作成
                label = f"{period_start.strftime('%H:%M')} - {period_end.strftime('%H:%M')}"
                
                # 時間帯内のデータポイントをフィルタリング
                period_data_indices = valid_data[
                    (timestamps >= period_start) & 
                    (timestamps < period_end)
                ].index.tolist()
                
                # 時間帯内のデータがなければスキップ
                if not period_data_indices:
                    continue
                
                # 時間帯内の問題数をカウント
                problem_count = 0
                for idx in period_data_indices:
                    if idx in all_problem_indices:
                        problem_count += 1
                
                # 品質スコアの計算
                quality_score = 100.0
                if period_data_indices:
                    quality_score = 100.0 * (1 - (problem_count / len(period_data_indices)))
                
                # 問題タイプごとの分布も計算
                problem_type_distribution = self._calculate_problem_type_distribution_for_period(period_data_indices)
                
                # 時間帯情報の作成
                period_info = {
                    "period": i,
                    "start_time": period_start.isoformat(),
                    "end_time": period_end.isoformat(),
                    "label": label,
                    "quality_score": quality_score,
                    "problem_count": problem_count,
                    "total_count": len(period_data_indices),
                    "problem_percentage": 100.0 * problem_count / len(period_data_indices) if period_data_indices else 0.0,
                    "impact_level": self._determine_impact_level(quality_score),
                    "problem_types": problem_type_distribution
                }
                
                periods.append(period_info)
            
            return periods
            
        except Exception as e:
            # エラーが発生した場合は空のリストを返す
            print(f"時間帯別の品質スコア計算中にエラー: {e}")
            return []
