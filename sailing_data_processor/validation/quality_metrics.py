# -*- coding: utf-8 -*-
"""
sailing_data_processor.validation.quality_metrics

データ品質メトリクスの計算を行うモジュール
"""

from typing import Dict, List, Any, Optional, Tuple, Set
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# データモデルインポートエラーのリスクを回避するため、直接インポートは行わない
# 代わりに動的インポートまたはタイプヒントのみの参照を使用
try:
    from sailing_data_processor.data_model.container import GPSDataContainer
except ImportError:
    # インポートが失敗した場合でもクラス自体の定義は可能に
    pass


class QualityMetricsCalculator:
    """
    データ品質メトリクスの計算クラス - 簡略化バージョン
    
    Parameters
    ----------
    validation_results : List[Dict[str, Any]]
        DataValidatorから得られた検証結果
    data : pd.DataFrame
        検証されたデータフレーム
    """
    
    def __init__(self, validation_results: List[Dict[str, Any]], data: pd.DataFrame):
        """
        初期化
        
        Parameters
        ----------
        validation_results : List[Dict[str, Any]]
            DataValidatorから得られた検証結果
        data : pd.DataFrame
            検証されたデータフレーム
        """
        self.validation_results = validation_results if validation_results else []
        self.data = data if data is not None else pd.DataFrame()
        
        # カテゴリー別のルール分類
        self.rule_categories = {
            "completeness": ["Required Columns Check", "No Null Values Check"],
            "accuracy": ["Value Range Check", "Spatial Consistency Check"],
            "consistency": ["No Duplicate Timestamps", "Temporal Consistency Check"]
        }
        
        # 問題のあるレコードのインデックスを収集 - 簡略化
        self.problematic_indices = {
            "missing_data": [],
            "out_of_range": [],
            "duplicates": [],
            "spatial_anomalies": [],
            "temporal_anomalies": [],
            "all": []
        }
        
        # 品質スコアを簡略化
        self.quality_scores = {
            "completeness": 100.0,
            "accuracy": 100.0,
            "consistency": 100.0,
            "total": 100.0
        }
        
        # カテゴリ別スコアを簡略化
        self.category_scores = {}
        for category in self.rule_categories:
            self.category_scores[category] = {
                "score": 100.0,
                "issues": 0,
                "details": {}
            }
        
        # 問題分布を簡略化
        self.problem_distribution = {
            "temporal": {"has_data": False},
            "spatial": {"has_data": False},
            "problem_type": {"has_data": False}
        }
        
        # レコードごとの問題情報を簡略化
        self.record_issues = {}
        
        # 時間的・空間的メトリクスを簡略化
        self.temporal_metrics = {"has_data": False}
        self.spatial_metrics = {"has_data": False}
    
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
    
    @staticmethod
    def create_sample_data(rows=20, with_problems=True):
        """
        テスト用サンプルデータを作成するユーティリティメソッド
        
        Parameters
        ----------
        rows : int, optional
            生成する行数, by default 20
        with_problems : bool, optional
            問題データを含めるかどうか, by default True
            
        Returns
        -------
        Tuple[pd.DataFrame, List[Dict[str, Any]]]
            サンプルデータフレームとバリデーション結果
        """
        # 基本データの作成
        data = pd.DataFrame({
            'timestamp': [datetime(2025, 1, 1, 12, 0, i) for i in range(rows)],
            'latitude': [35.0 + i * 0.001 for i in range(rows)],
            'longitude': [135.0 + i * 0.001 for i in range(rows)],
            'speed': [5.0 + i * 0.2 for i in range(rows)],
            'course': [45.0 + i * 1.0 for i in range(rows)],
            'boat_id': ['test_boat'] * rows
        })
        
        validation_results = [
            {
                'rule_name': 'Required Columns Check',
                'is_valid': True,
                'severity': 'error',
                'details': {'required_columns': ['timestamp', 'latitude', 'longitude']}
            }
        ]
        
        # 問題データを含める場合
        if with_problems:
            # 欠損値
            data.loc[2, 'latitude'] = None
            data.loc[5, 'speed'] = None
            
            # 範囲外の値
            data.loc[8, 'speed'] = 100.0  # 異常な速度
            
            # 重複タイムスタンプ
            if rows > 12:
                data.loc[12, 'timestamp'] = data.loc[11, 'timestamp']
            
            # 時間逆行
            if rows > 15:
                data.loc[15, 'timestamp'] = data.loc[14, 'timestamp'] - timedelta(seconds=5)
            
            # 空間的異常（急激な位置の変化）
            if rows > 18:
                data.loc[18, 'latitude'] = 36.0
                
            # バリデーション結果を更新
            validation_results.append({
                'rule_name': 'No Null Values Check',
                'is_valid': False,
                'severity': 'error',
                'details': {
                    'columns': ['latitude', 'longitude', 'speed'],
                    'total_null_count': 2,
                    'null_counts': {'latitude': 1, 'longitude': 0, 'speed': 1},
                    'null_indices': {'latitude': [2], 'speed': [5]}
                }
            })
            
            validation_results.append({
                'rule_name': 'Value Range Check',
                'is_valid': False,
                'severity': 'warning',
                'details': {
                    'column': 'speed',
                    'min_value': 0.0,
                    'max_value': 20.0,
                    'actual_min': 5.0,
                    'actual_max': 100.0,
                    'out_of_range_count': 1,
                    'out_of_range_indices': [8]
                }
            })
        
        return data, validation_results
    
    def get_problem_distribution(self):
        """
        問題の分布情報を取得
        
        Returns
        -------
        Dict[str, Any]
            問題の時間的・空間的・タイプ別分布
        """
        return self.problem_distribution
    
    def get_record_issues(self):
        """
        レコードごとの問題情報を取得
        
        Returns
        -------
        Dict[int, Dict[str, Any]]
            各レコードの問題情報
        """
        return self.record_issues
        
    def _calculate_precision_score(self) -> float:
        """
        精度スコアを計算する
        
        Returns
        -------
        float
            精度スコア (0-100)
        """
        # 範囲外の値などの精度に関わる問題をカウント
        precision_issues = len(self.problematic_indices.get("out_of_range", []))
        
        # データ全体に対する問題の割合を計算
        total_records = len(self.data) if not self.data.empty else 1
        precision_score = 100.0 * (1 - (precision_issues / total_records))
        
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
        validity_issues = len(self.problematic_indices.get("temporal_anomalies", []))
        
        # データ全体に対する問題の割合を計算
        total_records = len(self.data) if not self.data.empty else 1
        validity_score = 100.0 * (1 - (validity_issues / total_records))
        
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
            return 100.0
        
        # 間隔の標準偏差を計算
        mean_interval = np.mean(intervals)
        std_interval = np.std(intervals)
        
        # 変動係数（標準偏差/平均）を計算
        cv = std_interval / mean_interval if mean_interval > 0 else 0
        
        # 変動係数からスコアを計算（変動係数が小さいほど均一）
        # 変動係数0は完全に均一、経験的に0.5以上は非常に不均一と仮定
        uniformity_score = 100.0 * (1 - min(1.0, cv / 0.5))
        
        return max(0.0, min(100.0, uniformity_score))
        
    def calculate_hierarchical_quality_scores(self) -> Dict[str, Any]:
        """
        階層的品質スコアを計算する
        
        Returns
        -------
        Dict[str, Any]
            階層構造の品質スコア情報
        """
        # カテゴリとサブカテゴリの階層構造を定義
        categories = {
            "organizational": {
                "name": "組織的品質",
                "description": "データの構造と組織に関する品質",
                "score": 0.0,
                "subcategories": {
                    "completeness": {
                        "name": "完全性",
                        "score": self.quality_scores.get("completeness", 100.0),
                        "weight": 0.6
                    },
                    "metadata": {
                        "name": "メタデータ品質",
                        "score": 95.0,  # 簡略化のため固定値
                        "weight": 0.4
                    }
                }
            },
            "statistical": {
                "name": "統計的品質",
                "description": "データの統計的特性に関する品質",
                "score": 0.0,
                "subcategories": {
                    "distribution": {
                        "name": "分布の適切さ",
                        "score": 90.0,  # 簡略化のため固定値
                        "weight": 0.5
                    },
                    "outliers": {
                        "name": "外れ値の扱い",
                        "score": self.quality_scores.get("accuracy", 100.0),
                        "weight": 0.5
                    }
                }
            },
            "structural": {
                "name": "構造的品質",
                "description": "データの内部構造に関する品質",
                "score": 0.0,
                "subcategories": {
                    "consistency": {
                        "name": "一貫性",
                        "score": self.quality_scores.get("consistency", 100.0),
                        "weight": 0.7
                    },
                    "integrity": {
                        "name": "整合性",
                        "score": 92.0,  # 簡略化のため固定値
                        "weight": 0.3
                    }
                }
            },
            "semantic": {
                "name": "意味的品質",
                "description": "データの意味と解釈に関する品質",
                "score": 0.0,
                "subcategories": {
                    "accuracy": {
                        "name": "正確性",
                        "score": self._calculate_precision_score(),
                        "weight": 0.5
                    },
                    "validity": {
                        "name": "妥当性",
                        "score": self._calculate_validity_score(),
                        "weight": 0.5
                    }
                }
            }
        }
        
        # カテゴリごとのスコアを計算
        overall_score = 0.0
        total_weight = 0.0
        
        for cat_key, category in categories.items():
            cat_score = 0.0
            cat_weight = 0.0
            
            for subcat_key, subcat in category["subcategories"].items():
                cat_score += subcat["score"] * subcat["weight"]
                cat_weight += subcat["weight"]
            
            category["score"] = cat_score / cat_weight if cat_weight > 0 else 0.0
            overall_score += category["score"]
            total_weight += 1.0
        
        # 総合スコアの計算
        overall_score = overall_score / total_weight if total_weight > 0 else 0.0
        
        return {
            "categories": categories,
            "overall_score": overall_score
        }
        
    def get_data_quality_patterns(self) -> Dict[str, Any]:
        """
        データ品質パターンを検出する
        
        Returns
        -------
        Dict[str, Any]
            検出されたパターン情報
        """
        patterns = []
        
        # 1. 欠損値パターンの検出
        missing_indices = self.problematic_indices.get("missing_data", [])
        if missing_indices:
            # 欠損値が連続しているかチェック
            missing_indices = sorted(missing_indices)
            consecutive_runs = []
            current_run = [missing_indices[0]] if missing_indices else []
            
            for i in range(1, len(missing_indices)):
                if missing_indices[i] == missing_indices[i-1] + 1:
                    current_run.append(missing_indices[i])
                else:
                    if len(current_run) > 1:
                        consecutive_runs.append(current_run)
                    current_run = [missing_indices[i]]
            
            if current_run and len(current_run) > 1:
                consecutive_runs.append(current_run)
            
            # 連続欠損があればパターンとして追加
            if consecutive_runs:
                patterns.append({
                    "name": "連続欠損値",
                    "description": "連続するレコードで欠損値が発生",
                    "severity": "error",
                    "details": {
                        "runs": consecutive_runs,
                        "run_count": len(consecutive_runs),
                        "max_run_length": max(len(run) for run in consecutive_runs)
                    }
                })
        
        # 2. 周期的な異常の検出
        anomaly_indices = self.problematic_indices.get("spatial_anomalies", []) + \
                        self.problematic_indices.get("temporal_anomalies", [])
        
        if anomaly_indices and len(anomaly_indices) > 1:
            anomaly_indices = sorted(anomaly_indices)
            diffs = [anomaly_indices[i] - anomaly_indices[i-1] for i in range(1, len(anomaly_indices))]
            
            # 差分の標準偏差が小さい（周期的）かチェック
            if len(diffs) > 2 and np.std(diffs) / np.mean(diffs) < 0.2:
                patterns.append({
                    "name": "周期的異常",
                    "description": "ほぼ一定間隔で異常値が発生",
                    "severity": "warning",
                    "details": {
                        "indices": anomaly_indices,
                        "period": np.mean(diffs),
                        "period_std": np.std(diffs)
                    }
                })
        
        return {
            "pattern_count": len(patterns),
            "patterns": patterns
        }
        
    def get_comprehensive_quality_metrics(self) -> Dict[str, Any]:
        """
        包括的な品質メトリクスを取得する
        
        Returns
        -------
        Dict[str, Any]
            包括的な品質メトリクス情報
        """
        # 階層的スコアの計算
        hierarchy_scores = self.calculate_hierarchical_quality_scores()
        
        # 問題分布の取得
        problem_distribution = self.get_problem_distribution()
        
        # カラム別の問題数を集計
        problematic_columns = {}
        for result in self.validation_results:
            if not result.get("is_valid", True):
                details = result.get("details", {})
                
                # Null値の問題
                null_counts = details.get("null_counts", {})
                for col, count in null_counts.items():
                    if col not in problematic_columns:
                        problematic_columns[col] = {"total": 0, "types": {}}
                    problematic_columns[col]["total"] += count
                    problematic_columns[col]["types"]["missing"] = problematic_columns[col]["types"].get("missing", 0) + count
                
                # 範囲外の問題
                if details.get("column") and details.get("out_of_range_count", 0) > 0:
                    col = details["column"]
                    if col not in problematic_columns:
                        problematic_columns[col] = {"total": 0, "types": {}}
                    problematic_columns[col]["total"] += details["out_of_range_count"]
                    problematic_columns[col]["types"]["out_of_range"] = details["out_of_range_count"]
        
        # 重要度別の問題数を集計
        severity_distribution = {"error": 0, "warning": 0, "info": 0}
        for result in self.validation_results:
            if not result.get("is_valid", True):
                severity = result.get("severity", "info")
                severity_distribution[severity] = severity_distribution.get(severity, 0) + 1
        
        # データ密度メトリクスを計算
        density_metrics = {"coverage": 0.0, "sampling_rate": 0.0}
        if not self.data.empty and "timestamp" in self.data.columns:
            timestamps = pd.to_datetime(self.data["timestamp"])
            if len(timestamps) > 1:
                time_range = (timestamps.max() - timestamps.min()).total_seconds()
                if time_range > 0:
                    density_metrics["coverage"] = time_range
                    density_metrics["sampling_rate"] = len(timestamps) / time_range
        
        # 問題のあるレコード数を計算
        problematic_record_count = len(set(self.problematic_indices.get("all", [])))
        
        # 包括的メトリクスの構築
        return {
            "basic_scores": self.quality_scores,
            "category_details": self.category_scores,
            "problem_distribution": problem_distribution,
            "temporal_metrics": self.temporal_metrics,
            "spatial_metrics": self.spatial_metrics,
            "problematic_columns": problematic_columns,
            "severity_distribution": severity_distribution,
            "density_metrics": density_metrics,
            "hierarchy_scores": hierarchy_scores,
            "quality_summary": self.get_quality_summary(),
            "record_count": len(self.data),
            "problematic_record_count": problematic_record_count,
            "generated_at": datetime.now().isoformat()
        }
        
    def calculate_spatial_quality_scores(self) -> List[Dict[str, Any]]:
        """
        空間的な品質スコアを計算する
        
        Returns
        -------
        List[Dict[str, Any]]
            空間グリッドごとの品質スコア
        """
        if self.data.empty or "latitude" not in self.data.columns or "longitude" not in self.data.columns:
            return []
        
        # 緯度・経度の範囲を取得
        lat_min, lat_max = self.data["latitude"].min(), self.data["latitude"].max()
        lon_min, lon_max = self.data["longitude"].min(), self.data["longitude"].max()
        
        # グリッド分割数（簡易的に固定値）
        grid_count = 3
        
        # グリッドの作成
        lat_step = (lat_max - lat_min) / grid_count
        lon_step = (lon_max - lon_min) / grid_count
        
        grids = []
        for i in range(grid_count):
            for j in range(grid_count):
                grid_lat_min = lat_min + i * lat_step
                grid_lat_max = lat_min + (i + 1) * lat_step
                grid_lon_min = lon_min + j * lon_step
                grid_lon_max = lon_min + (j + 1) * lon_step
                
                # グリッド内のデータポイントをフィルタリング
                grid_data = self.data[
                    (self.data["latitude"] >= grid_lat_min) & 
                    (self.data["latitude"] < grid_lat_max) & 
                    (self.data["longitude"] >= grid_lon_min) & 
                    (self.data["longitude"] < grid_lon_max)
                ]
                
                # グリッド内のデータがなければスキップ
                if grid_data.empty:
                    continue
                
                # グリッド内の問題数をカウント
                problem_count = 0
                for idx in grid_data.index:
                    if idx in self.problematic_indices.get("all", []):
                        problem_count += 1
                
                # 品質スコアの計算
                quality_score = 100.0
                if len(grid_data) > 0:
                    quality_score = 100.0 * (1 - (problem_count / len(grid_data)))
                
                # グリッド情報の作成
                grid_info = {
                    "grid_id": f"grid_{i}_{j}",
                    "center": {
                        "latitude": (grid_lat_min + grid_lat_max) / 2,
                        "longitude": (grid_lon_min + grid_lon_max) / 2
                    },
                    "bounds": {
                        "lat_min": grid_lat_min,
                        "lat_max": grid_lat_max,
                        "lon_min": grid_lon_min,
                        "lon_max": grid_lon_max
                    },
                    "quality_score": quality_score,
                    "problem_count": problem_count,
                    "total_count": len(grid_data),
                    "problem_percentage": 100.0 * problem_count / len(grid_data) if len(grid_data) > 0 else 0.0,
                    "impact_level": self._determine_impact_level(quality_score)
                }
                
                grids.append(grid_info)
        
        return grids
        
    def calculate_temporal_quality_scores(self) -> List[Dict[str, Any]]:
        """
        時間帯別の品質スコアを計算する
        
        Returns
        -------
        List[Dict[str, Any]]
            時間帯ごとの品質スコア
        """
        if self.data.empty or "timestamp" not in self.data.columns:
            return []
        
        # タイムスタンプをdatetimeに変換
        timestamps = pd.to_datetime(self.data["timestamp"])
        
        # 時間範囲の取得
        start_time = timestamps.min()
        end_time = timestamps.max()
        
        # 期間が短すぎる場合は一つの時間帯として扱う
        time_range = (end_time - start_time).total_seconds()
        if time_range < 60:  # 1分未満
            return []
        
        # 時間帯の数（簡易的に固定値）
        period_count = min(5, max(1, int(time_range / 600)))  # 10分ごとに区切る（最大5区間）
        
        # 時間帯の作成
        period_duration = timedelta(seconds=time_range / period_count)
        periods = []
        
        for i in range(period_count):
            period_start = start_time + i * period_duration
            period_end = start_time + (i + 1) * period_duration
            
            # 時間帯のラベル作成
            label = f"{period_start.strftime('%H:%M')} - {period_end.strftime('%H:%M')}"
            
            # 時間帯内のデータポイントをフィルタリング
            period_data_indices = self.data[
                (timestamps >= period_start) & 
                (timestamps < period_end)
            ].index.tolist()
            
            # 時間帯内のデータがなければスキップ
            if not period_data_indices:
                continue
            
            # 時間帯内の問題数をカウント
            problem_count = 0
            for idx in period_data_indices:
                if idx in self.problematic_indices.get("all", []):
                    problem_count += 1
            
            # 品質スコアの計算
            quality_score = 100.0
            if period_data_indices:
                quality_score = 100.0 * (1 - (problem_count / len(period_data_indices)))
            
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
                "impact_level": self._determine_impact_level(quality_score)
            }
            
            periods.append(period_info)
        
        return periods
        
    def get_quality_report(self) -> Dict[str, Any]:
        """
        品質レポートを生成する
        
        Returns
        -------
        Dict[str, Any]
            詳細な品質レポート
        """
        # 基本情報の集約
        basic_info = {
            "quality_scores": self.quality_scores,
            "category_scores": self.category_scores,
            "issue_counts": self.get_quality_summary().get("issue_counts", {})
        }
        
        # 問題サマリーの作成
        total_problems = sum(basic_info["issue_counts"].values())
        problem_summary = {
            "total_problems": total_problems,
            "problem_types": {
                k: {
                    "count": v,
                    "percentage": 100.0 * v / total_problems if total_problems > 0 else 0.0
                } for k, v in basic_info["issue_counts"].items() if v > 0
            }
        }
        
        # 分布情報の取得
        distribution_info = {
            "temporal": self.calculate_temporal_quality_scores(),
            "spatial": self.calculate_spatial_quality_scores(),
            "problem_patterns": self.get_data_quality_patterns()
        }
        
        # 推奨事項の生成
        recommendations = []
        
        # 欠損値の問題がある場合
        if basic_info["issue_counts"].get("missing_data", 0) > 0:
            recommendations.append({
                "id": "rec_missing_data",
                "title": "欠損値の処理",
                "description": "欠損値を適切な方法で補完または除外してください",
                "priority": "high" if basic_info["issue_counts"]["missing_data"] > 5 else "medium"
            })
        
        # 範囲外の値がある場合
        if basic_info["issue_counts"].get("out_of_range", 0) > 0:
            recommendations.append({
                "id": "rec_outliers",
                "title": "異常値の処理",
                "description": "範囲外の値を修正または除外してください",
                "priority": "medium"
            })
        
        # 時間的異常がある場合
        if basic_info["issue_counts"].get("temporal_anomalies", 0) > 0:
            recommendations.append({
                "id": "rec_temporal",
                "title": "時間的整合性の確保",
                "description": "時間順序の逆転やギャップを修正してください",
                "priority": "high"
            })
        
        # レポートの構築
        return {
            "basic_info": basic_info,
            "problem_summary": problem_summary,
            "distribution_info": distribution_info,
            "recommendations": recommendations,
            "report_id": f"quality_report_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "generated_at": datetime.now().isoformat()
        }
