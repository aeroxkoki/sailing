# -*- coding: utf-8 -*-
"""
データ品質メトリクス計算モジュール
This module provides functionality for calculating quality metrics of GPS data.
"""

from typing import Dict, List, Any, Optional, Tuple, Set
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import uuid

# データモデルインポートエラーのリスクを回避するため、直接インポートは行わない
# 代わりに動的インポートまたはタイプヒントのみの参照を使用
try:
    from sailing_data_processor.data_model.container import GPSDataContainer
except ImportError:
    # インポートが失敗した場合でもクラス自体の定義は可能に
    pass


class QualityMetricsCalculator:
    """
    データ品質メトリクスの計算クラス
    
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
        
        # 問題のあるレコードのインデックスを収集
        self.problematic_indices = self._collect_problematic_indices()
        
        # 品質スコアを計算
        self.quality_scores = self._calculate_quality_scores()
        
        # カテゴリ別スコアを計算
        self.category_scores = self._calculate_category_scores()
        
        # 問題分布
        self.problem_distribution = {}
        
        # レコードごとの問題情報
        self.record_issues = {}
        
        # 時間的・空間的メトリクス
        self.temporal_metrics = {}
        self.spatial_metrics = {}
        
    def _collect_problematic_indices(self) -> Dict[str, List[int]]:
        """
        バリデーション結果から問題のあるレコードインデックスを収集
        
        Returns
        -------
        Dict[str, List[int]]
            カテゴリごとの問題インデックス
        """
        indices = {
            "missing_data": [],
            "out_of_range": [],
            "duplicates": [],
            "spatial_anomalies": [],
            "temporal_anomalies": [],
            "all": []
        }
        
        for result in self.validation_results:
            if not result.get('is_valid', True):
                details = result.get('details', {})
                rule_name = result.get('rule_name', '')
                
                # 欠損値の問題
                if rule_name == "No Null Values Check":
                    null_indices = []
                    for col, idxs in details.get('null_indices', {}).items():
                        null_indices.extend(idxs)
                    indices["missing_data"].extend(null_indices)
                    indices["all"].extend(null_indices)
                
                # 範囲外の値の問題
                elif rule_name == "Value Range Check":
                    out_indices = details.get('out_of_range_indices', [])
                    indices["out_of_range"].extend(out_indices)
                    indices["all"].extend(out_indices)
                
                # 重複タイムスタンプの問題
                elif rule_name == "No Duplicate Timestamps":
                    dup_indices = []
                    for ts, idxs in details.get('duplicate_indices', {}).items():
                        dup_indices.extend(idxs)
                    indices["duplicates"].extend(dup_indices)
                    indices["all"].extend(dup_indices)
                
                # 空間的異常の問題
                elif rule_name == "Spatial Consistency Check":
                    spatial_indices = details.get('anomaly_indices', [])
                    indices["spatial_anomalies"].extend(spatial_indices)
                    indices["all"].extend(spatial_indices)
                
                # 時間的異常の問題
                elif rule_name == "Temporal Consistency Check":
                    temporal_indices = details.get('reverse_indices', [])
                    indices["temporal_anomalies"].extend(temporal_indices)
                    indices["all"].extend(temporal_indices)
        
        # 重複を除去
        for key in indices:
            indices[key] = sorted(list(set(indices[key])))
        
        return indices
    
    def _calculate_quality_scores(self) -> Dict[str, float]:
        """
        全体的な品質スコアを計算
        
        Returns
        -------
        Dict[str, float]
            品質スコア
        """
        scores = {
            "completeness": 100.0,
            "accuracy": 100.0,
            "consistency": 100.0,
            "total": 100.0
        }
        
        # データサイズを取得
        data_size = len(self.data) if not self.data.empty else 1
        
        # 完全性スコア計算
        missing_count = len(self.problematic_indices["missing_data"])
        if missing_count > 0:
            # 欠損値が多いほどスコアを下げる
            completeness_score = 100.0 * (1 - (missing_count / data_size))
            penalty = min(50.0, missing_count * 2.0)  # 多すぎると50ポイント以上下がる
            scores["completeness"] = max(0.0, completeness_score - penalty)
        
        # 精度スコア計算
        accuracy_issues = len(self.problematic_indices["out_of_range"]) + len(self.problematic_indices["spatial_anomalies"])
        if accuracy_issues > 0:
            # 精度問題が多いほどスコアを下げる
            accuracy_score = 100.0 * (1 - (accuracy_issues / data_size))
            penalty = min(40.0, accuracy_issues * 3.0)  # 多すぎると40ポイント以上下がる
            scores["accuracy"] = max(0.0, accuracy_score - penalty)
        
        # 一貫性スコア計算
        consistency_issues = len(self.problematic_indices["duplicates"]) + len(self.problematic_indices["temporal_anomalies"])
        if consistency_issues > 0:
            # 一貫性問題が多いほどスコアを下げる
            consistency_score = 100.0 * (1 - (consistency_issues / data_size))
            penalty = min(60.0, consistency_issues * 5.0)  # 多すぎると60ポイント以上下がる
            scores["consistency"] = max(0.0, consistency_score - penalty)
        
        # 総合スコア計算 - 各カテゴリのスコアの加重平均
        # 一貫性は特に重要なので、より重みを高く
        weights = {"completeness": 0.3, "accuracy": 0.3, "consistency": 0.4}
        weighted_sum = sum(scores[cat] * weight for cat, weight in weights.items())
        scores["total"] = weighted_sum / sum(weights.values())
        
        return scores
    
    def _calculate_category_scores(self) -> Dict[str, Dict[str, Any]]:
        """
        カテゴリ別の詳細スコアを計算
        
        Returns
        -------
        Dict[str, Dict[str, Any]]
            カテゴリ別スコア情報
        """
        category_scores = {}
        
        for category in self.rule_categories:
            # そのカテゴリに関連する問題数をカウント
            issue_count = 0
            details = {}
            
            for result in self.validation_results:
                rule_name = result.get('rule_name', '')
                if rule_name in self.rule_categories[category] and not result.get('is_valid', True):
                    issue_count += 1
                    # ルールごとの問題カウントを保存
                    rule_key = rule_name.lower().replace(' ', '_')
                    details[rule_key] = result.get('details', {})
            
            # カテゴリスコアを設定
            category_scores[category] = {
                "score": self.quality_scores[category],
                "issues": issue_count,
                "details": details
            }
        
        return category_scores
    
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
        
        # 重要度別の問題数をカウント
        severity_counts = self.get_problem_severity_distribution()
        
        # 修正可能な問題数をカウント（簡易版）
        fixable_counts = {
            "auto": missing_data_count + dupes_count,  # 自動修正可能
            "manual": out_of_range_count,              # 手動修正推奨
            "unfixable": spatial_count + temporal_count # 再測定必要
        }
        
        # 品質サマリーを構築
        return {
            "quality_score": self.quality_scores.get("total", 100.0),
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
            "severity_counts": severity_counts,
            "fixable_counts": fixable_counts,
            "impact_level": self._determine_impact_level(self.quality_scores.get("total", 100.0))
        }
        
    @property
    def quality_summary(self):
        """
        品質サマリーのプロパティ
        
        Returns
        -------
        Dict[str, Any]
            品質サマリー情報
        """
        return self.get_quality_summary()
    
    def calculate_quality_scores(self) -> Dict[str, float]:
        """
        品質スコアを計算する（テスト用メソッド）
        
        Returns
        -------
        Dict[str, float]
            品質スコア
        """
        return self._calculate_quality_scores()
    
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
            
            if rows > 12:
                validation_results.append({
                    'rule_name': 'No Duplicate Timestamps',
                    'is_valid': False,
                    'severity': 'warning',
                    'details': {
                        'duplicate_count': 2,
                        'duplicate_timestamps': [data.loc[11, 'timestamp']],
                        'duplicate_indices': {str(data.loc[11, 'timestamp']): [11, 12]}
                    }
                })
            
            if rows > 15:
                validation_results.append({
                    'rule_name': 'Temporal Consistency Check',
                    'is_valid': False,
                    'severity': 'warning',
                    'details': {
                        'reverse_count': 1,
                        'reverse_indices': [15]
                    }
                })
            
            if rows > 18:
                validation_results.append({
                    'rule_name': 'Spatial Consistency Check',
                    'is_valid': False,
                    'severity': 'warning',
                    'details': {
                        'anomaly_count': 1,
                        'max_calculated_speed': 50.0,
                        'anomaly_indices': [18]
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
        # 問題タイプごとのカウントを集計
        problem_type_counts = {
            "missing_data": len(self.problematic_indices.get("missing_data", [])),
            "out_of_range": len(self.problematic_indices.get("out_of_range", [])),
            "duplicates": len(self.problematic_indices.get("duplicates", [])),
            "spatial_anomalies": len(self.problematic_indices.get("spatial_anomalies", [])),
            "temporal_anomalies": len(self.problematic_indices.get("temporal_anomalies", []))
        }
        
        # 時間的な分布情報を構築
        temporal_metrics = {
            "has_data": len(self.problematic_indices.get("all", [])) > 0,
            "problematic_periods": []
        }
        
        if not self.data.empty and "timestamp" in self.data.columns:
            # タイムスタンプごとに問題が発生した時間帯を特定
            try:
                timestamps = pd.to_datetime(self.data["timestamp"])
                min_time = timestamps.min()
                max_time = timestamps.max()
                
                # 時間帯ごとの問題数をカウント
                for i, idx in enumerate(self.problematic_indices.get("all", [])):
                    if idx < len(self.data):
                        row = self.data.iloc[idx]
                        if "timestamp" in row:
                            ts = row["timestamp"]
                            temporal_metrics["problematic_periods"].append({
                                "timestamp": ts.isoformat() if hasattr(ts, "isoformat") else str(ts),
                                "count": 1
                            })
            except Exception:
                # 時間情報の解析エラー
                pass
        
        # 空間的な分布情報を構築
        spatial_metrics = {
            "has_data": len(self.problematic_indices.get("all", [])) > 0,
            "problematic_areas": []
        }
        
        if not self.data.empty and "latitude" in self.data.columns and "longitude" in self.data.columns:
            # 問題のある場所のクラスタリング
            for i, idx in enumerate(self.problematic_indices.get("all", [])):
                if idx < len(self.data):
                    row = self.data.iloc[idx]
                    if not pd.isna(row.get("latitude")) and not pd.isna(row.get("longitude")):
                        spatial_metrics["problematic_areas"].append({
                            "latitude": row["latitude"],
                            "longitude": row["longitude"],
                            "count": 1
                        })
        
        # 問題タイプの分布情報を構築
        problem_type_distribution = {
            "has_data": sum(problem_type_counts.values()) > 0,
            "problem_counts": problem_type_counts
        }
        
        # 問題分布情報を構築し保存
        self.problem_distribution = {
            "temporal": temporal_metrics,
            "spatial": spatial_metrics,
            "problem_type": problem_type_distribution
        }
        
        return self.problem_distribution
    
    def get_record_issues(self):
        """
        レコードごとの問題情報を取得
        
        Returns
        -------
        Dict[int, Dict[str, Any]]
            各レコードの問題情報
        """
        # 問題カテゴリとその説明
        issue_categories = {
            "missing_data": "欠損値",
            "out_of_range": "範囲外の値",
            "duplicates": "重複タイムスタンプ",
            "spatial_anomalies": "空間的異常",
            "temporal_anomalies": "時間的異常"
        }
        
        # レコードごとの問題情報を収集
        record_issues = {}
        
        # 各問題タイプで、問題のあるレコードに問題情報を追加
        for category, indices in self.problematic_indices.items():
            if category != "all":
                for idx in indices:
                    if idx not in record_issues:
                        record_issues[idx] = {
                            "issues": [],
                            "issue_count": 0,
                            "severity": "info",
                            "quality_score": {"total": 100.0},
                            "fix_options": [],
                            "description": ""
                        }
                    
                    # 問題がまだ追加されていなければ追加
                    issue_description = issue_categories.get(category, category)
                    if issue_description not in record_issues[idx]["issues"]:
                        record_issues[idx]["issues"].append(issue_description)
                        record_issues[idx]["issue_count"] += 1
                        
                        # 修正オプションを追加
                        fix_option = {
                            "id": f"fix_{category}_{idx}",
                            "name": f"{issue_description}の修正",
                            "type": "auto" if category in ["missing_data", "duplicates"] else "manual"
                        }
                        record_issues[idx]["fix_options"].append(fix_option)
        
        # 問題の重要度を設定
        for result in self.validation_results:
            if not result.get("is_valid", True):
                severity = result.get("severity", "info")
                details = result.get("details", {})
                
                # 重要度を設定する対象のインデックスを抽出
                target_indices = []
                
                if "null_indices" in details:
                    for col, indices in details["null_indices"].items():
                        target_indices.extend(indices)
                
                if "out_of_range_indices" in details:
                    target_indices.extend(details.get("out_of_range_indices", []))
                
                if "duplicate_indices" in details:
                    for ts, indices in details.get("duplicate_indices", {}).items():
                        target_indices.extend(indices)
                
                if "anomaly_indices" in details:
                    target_indices.extend(details.get("anomaly_indices", []))
                
                if "reverse_indices" in details:
                    target_indices.extend(details.get("reverse_indices", []))
                
                # 対象インデックスの重要度を更新
                for idx in target_indices:
                    if idx in record_issues:
                        # 最も重要な重要度を設定（error > warning > info）
                        current_severity = record_issues[idx]["severity"]
                        if severity == "error" or current_severity == "error":
                            record_issues[idx]["severity"] = "error"
                        elif severity == "warning" or current_severity == "warning":
                            record_issues[idx]["severity"] = "warning"
        
        # 各レコードに追加情報を設定
        for idx, issue_data in record_issues.items():
            # 品質スコアの更新 - 問題数と重要度に応じて減少
            issue_count = issue_data["issue_count"]
            severity_penalty = 10 if issue_data["severity"] == "warning" else 20 if issue_data["severity"] == "error" else 5
            quality_score = max(0, 100 - (issue_count * severity_penalty))
            issue_data["quality_score"] = {
                "total": quality_score,
                "impact": self._determine_impact_level(quality_score)
            }
            
            # 問題の詳細説明を生成
            issue_data["description"] = f"{issue_count}個の問題: " + ", ".join(issue_data["issues"])
            
            # データの一部を保存（データがある場合）
            if idx < len(self.data):
                row = self.data.iloc[idx]
                if "timestamp" in row:
                    issue_data["timestamp"] = row["timestamp"]
                if "latitude" in row and "longitude" in row:
                    issue_data["position"] = [row["latitude"], row["longitude"]]
        
        self.record_issues = record_issues
        return record_issues
        
    def get_problem_severity_distribution(self) -> Dict[str, int]:
        """
        問題の重要度別分布を取得
        
        Returns
        -------
        Dict[str, int]
            重要度別の問題数
        """
        severity_counts = {"error": 0, "warning": 0, "info": 0}
        
        # バリデーション結果から重要度をカウント
        for result in self.validation_results:
            if not result.get("is_valid", True):
                severity = result.get("severity", "info")
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        return severity_counts
        
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
        
        # データからNaNを除外して計算
        valid_data = self.data.dropna(subset=["latitude", "longitude"])
        if valid_data.empty:
            return []
            
        # 緯度・経度の範囲を取得
        lat_min, lat_max = valid_data["latitude"].min(), valid_data["latitude"].max()
        lon_min, lon_max = valid_data["longitude"].min(), valid_data["longitude"].max()
        
        # グリッド分割数（データ量によって調整）
        data_size = len(valid_data)
        if data_size <= 10:
            grid_count = 2
        elif data_size <= 100:
            grid_count = 3
        else:
            grid_count = 4
        
        # グリッドの作成
        lat_step = (lat_max - lat_min) / grid_count if lat_max > lat_min else 0.01
        lon_step = (lon_max - lon_min) / grid_count if lon_max > lon_min else 0.01
        
        grids = []
        for i in range(grid_count):
            for j in range(grid_count):
                grid_lat_min = lat_min + i * lat_step
                grid_lat_max = lat_min + (i + 1) * lat_step
                grid_lon_min = lon_min + j * lon_step
                grid_lon_max = lon_min + (j + 1) * lon_step
                
                # グリッド内のデータポイントをフィルタリング
                grid_data = valid_data[
                    (valid_data["latitude"] >= grid_lat_min) & 
                    (valid_data["latitude"] < grid_lat_max) & 
                    (valid_data["longitude"] >= grid_lon_min) & 
                    (valid_data["longitude"] < grid_lon_max)
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
                    "center": [(grid_lat_min + grid_lat_max) / 2, (grid_lon_min + grid_lon_max) / 2],
                    "bounds": {
                        "min_lat": grid_lat_min,
                        "max_lat": grid_lat_max,
                        "min_lon": grid_lon_min,
                        "max_lon": grid_lon_max
                    },
                "lat_range": [grid_lat_min, grid_lat_max],  # 明示的にlat_rangeを追加
                "lon_range": [grid_lon_min, grid_lon_max],  # 明示的にlon_rangeを追加
                "lat_range": [grid_lat_min, grid_lat_max],  # 明示的にlat_rangeを追加
                "lon_range": [grid_lon_min, grid_lon_max],  # 明示的にlon_rangeを追加
                "lat_range": [grid_lat_min, grid_lat_max],  # 明示的にlat_rangeを追加
                "lon_range": [grid_lon_min, grid_lon_max],  # 明示的にlon_rangeを追加
                "lat_range": [grid_lat_min, grid_lat_max],  # 明示的にlat_rangeを追加
                "lon_range": [grid_lon_min, grid_lon_max],  # 明示的にlon_rangeを追加
                    "quality_score": quality_score,
                    "problem_count": problem_count,
                    "total_count": len(grid_data),
                    "problem_percentage": 100.0 * problem_count / len(grid_data) if len(grid_data) > 0 else 0.0,
                    "impact_level": self._determine_impact_level(quality_score)
                }
                
                grids.append(grid_info)
        
        # グリッドがない場合のフォールバック（データが1点だけの場合など）
        if not grids and not valid_data.empty:
            center_lat = (lat_min + lat_max) / 2
            center_lon = (lon_min + lon_max) / 2
            
            # 少なくとも1つのグリッドを作成
            grids.append({
                "grid_id": "grid_single",
                "center": [center_lat, center_lon],
                "bounds": {
                    "min_lat": lat_min - 0.001,
                    "max_lat": lat_max + 0.001,
                    "min_lon": lon_min - 0.001,
                    "max_lon": lon_max + 0.001
                },
                "lat_range": [lat_min - 0.001, lat_max + 0.001],  # 明示的にlat_rangeを追加
                "lon_range": [lon_min - 0.001, lon_max + 0.001],  # 明示的にlon_rangeを追加
                "lat_range": [lat_min - 0.001, lat_max + 0.001],  # 明示的にlat_rangeを追加
                "lon_range": [lon_min - 0.001, lon_max + 0.001],  # 明示的にlon_rangeを追加
                "lat_range": [lat_min - 0.001, lat_max + 0.001],  # 明示的にlat_rangeを追加
                "lon_range": [lon_min - 0.001, lon_max + 0.001],  # 明示的にlon_rangeを追加
                "lat_range": [lat_min - 0.001, lat_max + 0.001],  # 明示的にlat_rangeを追加
                "lon_range": [lon_min - 0.001, lon_max + 0.001],  # 明示的にlon_rangeを追加
                "quality_score": 100.0,  # データが1点だけなら問題がなさそう
                "problem_count": 0,
                "total_count": len(valid_data),
                "problem_percentage": 0.0,
                "impact_level": "low"
            })
        
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
            # テストケースのため最低限の空のリストを返す
            return []
        
        # タイムスタンプをdatetimeに変換
        try:
            timestamps = pd.to_datetime(self.data["timestamp"])
            
            # 時間範囲の取得
            start_time = timestamps.min()
            end_time = timestamps.max()
            
            # 期間が短すぎる場合は一つの時間帯として扱う
            time_range = (end_time - start_time).total_seconds()
            if time_range < 60:  # 1分未満
                # 最低1つは返す
                problem_count = 0
                for idx in self.data.index:
                    if idx in self.problematic_indices.get("all", []):
                        problem_count += 1
                
                quality_score = 100.0
                if len(self.data) > 0:
                    quality_score = 100.0 * (1 - (problem_count / len(self.data)))
                    
                period_info = {
                    "period": 0,
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "label": f"{start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}",
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
            
        except Exception as e:
            # エラー時は空リストを返す
            return []
        
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
            "problem_types": {}
        }
        
        # 問題タイプの分布
        if total_problems > 0:
            problem_summary["problem_types"] = {
                k: {
                    "count": v,
                    "percentage": 100.0 * v / total_problems if total_problems > 0 else 0.0
                } for k, v in basic_info["issue_counts"].items() if v > 0
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
