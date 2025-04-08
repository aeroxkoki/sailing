"""
sailing_data_processor.validation.quality_metrics

データ品質メトリクスの計算を行うモジュール
"""

from typing import Dict, List, Any, Optional, Tuple, Set
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from sailing_data_processor.data_model.container import GPSDataContainer


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
        self.validation_results = validation_results
        self.data = data
        
        # カテゴリー別のルール分類
        self.rule_categories = {
            "completeness": ["Required Columns Check", "No Null Values Check"],
            "accuracy": ["Value Range Check", "Spatial Consistency Check"],
            "consistency": ["No Duplicate Timestamps", "Temporal Consistency Check"]
        }
        
        # 問題のあるレコードのインデックスを収集
        self.problematic_indices = self._collect_problematic_indices()
        
        # 品質スコアを計算
        self.quality_scores = self.calculate_overall_score()
        
        # カテゴリ別スコアを計算
        self.category_scores = self.calculate_category_scores()
        
        # 問題分布を計算
        self.problem_distribution = self.get_problem_distribution()
        
        # レコードごとの問題情報を計算
        self.record_issues = self.get_record_issues()
        
        # 時間的・空間的メトリクスを計算
        self.temporal_metrics = self.get_extended_temporal_metrics()
        self.spatial_metrics = self.get_extended_spatial_metrics()
    
    def _collect_problematic_indices(self) -> Dict[str, List[int]]:
        """
        問題のあるレコードのインデックスを収集
        
        Returns
        -------
        Dict[str, List[int]]
            カテゴリ別の問題インデックス
        """
        indices = {
            "missing_data": [],
            "out_of_range": [],
            "duplicates": [],
            "spatial_anomalies": [],
            "temporal_anomalies": [],
            "all": set()  # 全ての問題インデックス（重複なし）
        }
        
        for result in self.validation_results:
            if not result["is_valid"]:
                details = result["details"]
                
                # 欠損値の問題
                if "null_indices" in details:
                    for col, col_indices in details["null_indices"].items():
                        indices["missing_data"].extend(col_indices)
                        indices["all"].update(col_indices)
                
                # 範囲外の値
                if "out_of_range_indices" in details:
                    indices["out_of_range"].extend(details["out_of_range_indices"])
                    indices["all"].update(details["out_of_range_indices"])
                
                # 重複タイムスタンプ
                if "duplicate_indices" in details:
                    for ts, dup_indices in details["duplicate_indices"].items():
                        indices["duplicates"].extend(dup_indices)
                        indices["all"].update(dup_indices)
                
                # 空間的異常
                if "anomaly_indices" in details and "Spatial" in result["rule_name"]:
                    indices["spatial_anomalies"].extend(details["anomaly_indices"])
                    indices["all"].update(details["anomaly_indices"])
                
                # 時間的異常（ギャップや逆行）
                if ((("gap_indices" in details) or ("reverse_indices" in details)) 
                        and "Temporal" in result["rule_name"]):
                    if "gap_indices" in details:
                        indices["temporal_anomalies"].extend(details["gap_indices"])
                        indices["all"].update(details["gap_indices"])
                    if "reverse_indices" in details:
                        indices["temporal_anomalies"].extend(details["reverse_indices"])
                        indices["all"].update(details["reverse_indices"])
        
        # setからリストに変換
        indices["all"] = list(indices["all"])
        
        return indices
    
    def calculate_overall_score(self) -> Dict[str, float]:
        """
        全体的な品質スコアを0-100で計算
        
        Returns
        -------
        Dict[str, float]
            カテゴリー別の品質スコア
        """
        scores = {
            "completeness": 100.0,  # 完全性
            "accuracy": 100.0,      # 正確性
            "consistency": 100.0,   # 一貫性
            "total": 100.0          # 総合スコア
        }
        
        # データポイントが少ない場合は計算しない
        if len(self.data) < 5:
            return scores
        
        # デフォルトのペナルティ重み
        penalty_weights = {
            "error": 1.0,
            "warning": 0.5,
            "info": 0.1
        }
        
        # スコア計算用のカウンター
        penalties = {
            "completeness": 0.0,
            "accuracy": 0.0,
            "consistency": 0.0
        }
        
        issues_count = 0
        
        # 各検証結果のペナルティを計算
        for result in self.validation_results:
            if not result["is_valid"]:
                rule_name = result["rule_name"]
                severity = result["severity"]
                weight = penalty_weights.get(severity, 0.1)
                
                # カテゴリーを特定
                for category, rules in self.rule_categories.items():
                    if any(rule in rule_name for rule in rules):
                        # 検出された問題の深刻度と数に基づいてペナルティを加算
                        details = result["details"]
                        if "out_of_range_count" in details:
                            # 範囲外の値の割合に基づくペナルティ（最大-50）
                            penalty = min(50, (details["out_of_range_count"] / len(self.data) * 100))
                            penalties[category] += penalty * weight
                            issues_count += details["out_of_range_count"]
                        elif "duplicate_count" in details:
                            # 重複の割合に基づくペナルティ（最大-50）
                            penalty = min(50, (details["duplicate_count"] / len(self.data) * 100))
                            penalties[category] += penalty * weight
                            issues_count += details["duplicate_count"]
                        elif "total_null_count" in details:
                            # 欠損値の割合に基づくペナルティ（最大-50）
                            penalty = min(50, (details["total_null_count"] / (len(self.data) * len(details["columns"])) * 100))
                            penalties[category] += penalty * weight
                            issues_count += details["total_null_count"]
                        elif "gap_count" in details:
                            # 時間ギャップの割合に基づくペナルティ（最大-50）
                            penalty = min(50, (details["gap_count"] / len(self.data) * 100))
                            penalties[category] += penalty * weight
                            issues_count += details["gap_count"]
                        elif "missing_columns" in details:
                            # 欠落カラムごとに-25ポイント
                            penalty = min(50, len(details["missing_columns"]) * 25)
                            penalties[category] += penalty * weight
                            issues_count += len(details["missing_columns"])
                        else:
                            # その他の問題には固定ペナルティ
                            penalties[category] += 10 * weight
                            issues_count += 1
        
        # 各カテゴリのスコアを計算
        for category in scores.keys():
            if category != "total":
                scores[category] = max(0, 100 - penalties.get(category, 0))
        
        # 総合スコアは各カテゴリの平均
        category_scores = [scores[cat] for cat in ["completeness", "accuracy", "consistency"]]
        scores["total"] = sum(category_scores) / len(category_scores)
        
        # スコアを小数点以下1桁に丸める
        for key in scores:
            scores[key] = round(scores[key], 1)
        
        return scores
        
    def calculate_quality_scores(self) -> Dict[str, float]:
        """
        データ品質スコアを計算。
        
        総合スコアと各カテゴリ（完全性、正確性、一貫性）のスコアを0〜100の範囲で計算します。
        スコアは問題の重要度と数に基づいて決定されます。

        Returns
        -------
        Dict[str, float]
            各種品質スコア (total, completeness, accuracy, consistency)
        """
        # データポイントが少ない場合は計算しない
        if len(self.data) < 5:
            return {
                "completeness": 100.0,
                "accuracy": 100.0,
                "consistency": 100.0,
                "total": 100.0
            }
        
        # 問題の重要度に基づくペナルティ重み
        penalty_weights = {
            "error": 1.0,
            "warning": 0.5,
            "info": 0.1
        }
        
        # カテゴリ別のペナルティを初期化
        penalties = {
            "completeness": 0.0,
            "accuracy": 0.0,
            "consistency": 0.0
        }
        
        # 各検証結果に基づいてペナルティを計算
        for result in self.validation_results:
            if not result["is_valid"]:
                rule_name = result["rule_name"]
                severity = result["severity"]
                weight = penalty_weights.get(severity, 0.1)
                
                # カテゴリーの特定
                for category, rules in self.rule_categories.items():
                    if any(rule in rule_name for rule in rules):
                        # 検出された問題の深刻度と数に基づいてペナルティを加算
                        details = result["details"]
                        if "out_of_range_count" in details:
                            # 範囲外の値の割合に基づくペナルティ（最大-50）
                            penalty = min(50, (details["out_of_range_count"] / len(self.data) * 100))
                            penalties[category] += penalty * weight
                        elif "duplicate_count" in details:
                            # 重複の割合に基づくペナルティ（最大-50）
                            penalty = min(50, (details["duplicate_count"] / len(self.data) * 100))
                            penalties[category] += penalty * weight
                        elif "total_null_count" in details:
                            # 欠損値の割合に基づくペナルティ（最大-50）
                            total_fields = len(self.data) * len(details.get("columns", []))
                            if total_fields > 0:
                                penalty = min(50, (details["total_null_count"] / total_fields * 100))
                                penalties[category] += penalty * weight
                        elif "gap_count" in details:
                            # 時間ギャップの割合に基づくペナルティ（最大-50）
                            penalty = min(50, (details["gap_count"] / len(self.data) * 100))
                            penalties[category] += penalty * weight
                        elif "missing_columns" in details:
                            # 欠落カラムごとに-25ポイント
                            penalty = min(50, len(details["missing_columns"]) * 25)
                            penalties[category] += penalty * weight
                        elif "anomaly_count" in details:
                            # 異常値の割合に基づくペナルティ（最大-50）
                            penalty = min(50, (details["anomaly_count"] / len(self.data) * 100))
                            penalties[category] += penalty * weight
                        else:
                            # その他の問題には固定ペナルティ
                            penalties[category] += 10 * weight
        
        # 各カテゴリのスコアを計算
        scores = {
            "completeness": max(0, 100 - penalties["completeness"]),
            "accuracy": max(0, 100 - penalties["accuracy"]),
            "consistency": max(0, 100 - penalties["consistency"])
        }
        
        # 総合スコアは各カテゴリの加重平均
        # 完全性と一貫性は基本的なデータ品質に重要、正確性はやや高く重み付け
        weights = {"completeness": 0.3, "accuracy": 0.4, "consistency": 0.3}
        
        total_score = sum(scores[cat] * weights[cat] for cat in ["completeness", "accuracy", "consistency"])
        scores["total"] = total_score
        
        # スコアを小数点以下1桁に丸める
        return {key: round(value, 1) for key, value in scores.items()}
    
    def calculate_category_scores(self) -> Dict[str, Dict[str, float]]:
        """
        カテゴリ別のスコアを計算
        
        Returns
        -------
        Dict[str, Dict[str, float]]
            カテゴリ別の詳細スコア
        """
        category_scores = {}
        
        # 各カテゴリの詳細スコアを計算
        for category, rules in self.rule_categories.items():
            category_scores[category] = {
                "score": self.quality_scores[category],
                "issues": 0,
                "details": {}
            }
            
            # 各ルールの結果を集計
            for result in self.validation_results:
                rule_name = result["rule_name"]
                
                if any(rule in rule_name for rule in rules):
                    if not result["is_valid"]:
                        # 問題カウントを増加
                        category_scores[category]["issues"] += 1
                        
                        # 詳細情報を追加
                        details = result["details"]
                        rule_key = rule_name.replace(" ", "_").lower()
                        
                        if "out_of_range_count" in details:
                            category_scores[category]["details"][rule_key] = {
                                "count": details["out_of_range_count"],
                                "percentage": round(details["out_of_range_count"] / len(self.data) * 100, 2)
                            }
                        elif "duplicate_count" in details:
                            category_scores[category]["details"][rule_key] = {
                                "count": details["duplicate_count"],
                                "percentage": round(details["duplicate_count"] / len(self.data) * 100, 2)
                            }
                        elif "total_null_count" in details:
                            category_scores[category]["details"][rule_key] = {
                                "count": details["total_null_count"],
                                "percentage": round(details["total_null_count"] / (len(self.data) * len(details["columns"])) * 100, 2),
                                "affected_columns": list(details.get("null_counts", {}).keys())
                            }
                        elif "gap_count" in details:
                            category_scores[category]["details"][rule_key] = {
                                "gap_count": details["gap_count"],
                                "reverse_count": details.get("reverse_count", 0),
                                "max_gap": details.get("max_actual_gap", 0),
                                "percentage": round((details["gap_count"] + details.get("reverse_count", 0)) / len(self.data) * 100, 2)
                            }
                        elif "missing_columns" in details:
                            category_scores[category]["details"][rule_key] = {
                                "missing_columns": details["missing_columns"],
                                "count": len(details["missing_columns"])
                            }
                        elif "anomaly_count" in details:
                            category_scores[category]["details"][rule_key] = {
                                "count": details["anomaly_count"],
                                "percentage": round(details["anomaly_count"] / len(self.data) * 100, 2),
                                "max_speed": details.get("max_calculated_speed", 0)
                            }
        
        return category_scores

    def calculate_category_quality_scores(self) -> Dict[str, Dict[str, float]]:
        """
        カテゴリ別の品質スコアを計算。
        
        各品質カテゴリ（完全性、正確性、一貫性）の詳細なスコアと問題情報を計算します。
        カテゴリごとの細分化された問題タイプやその影響範囲も含みます。
        
        Returns
        -------
        Dict[str, Dict[str, float]]
            カテゴリ別の詳細スコア
        """
        category_scores = {}
        
        # 品質スコアを取得
        quality_scores = self.calculate_quality_scores()
        
        # 各カテゴリの詳細スコアを計算
        for category, rules in self.rule_categories.items():
            category_scores[category] = {
                "score": quality_scores[category],
                "issues": 0,
                "details": {},
                "impact_level": self._determine_impact_level(quality_scores[category])
            }
            
            # 各ルールの結果を集計
            for result in self.validation_results:
                rule_name = result["rule_name"]
                
                if any(rule in rule_name for rule in rules):
                    if not result["is_valid"]:
                        # 問題カウントを増加
                        category_scores[category]["issues"] += 1
                        
                        # 詳細情報を追加
                        details = result["details"]
                        rule_key = rule_name.replace(" ", "_").lower()
                        
                        if "out_of_range_count" in details:
                            category_scores[category]["details"][rule_key] = {
                                "count": details["out_of_range_count"],
                                "percentage": round(details["out_of_range_count"] / len(self.data) * 100, 2),
                                "severity": result["severity"],
                                "description": f"{details.get('column', '値')}の{details['out_of_range_count']}件が範囲外"
                            }
                        elif "duplicate_count" in details:
                            category_scores[category]["details"][rule_key] = {
                                "count": details["duplicate_count"],
                                "percentage": round(details["duplicate_count"] / len(self.data) * 100, 2),
                                "severity": result["severity"],
                                "description": f"{details['duplicate_count']}件の重複タイムスタンプ"
                            }
                        elif "total_null_count" in details:
                            total_fields = len(self.data) * len(details.get("columns", []))
                            percentage = 0 if total_fields == 0 else round(details["total_null_count"] / total_fields * 100, 2)
                            
                            category_scores[category]["details"][rule_key] = {
                                "count": details["total_null_count"],
                                "percentage": percentage,
                                "severity": result["severity"],
                                "affected_columns": list(details.get("null_counts", {}).keys()),
                                "description": f"{details['total_null_count']}件の欠損値"
                            }
                        elif "gap_count" in details:
                            category_scores[category]["details"][rule_key] = {
                                "gap_count": details["gap_count"],
                                "reverse_count": details.get("reverse_count", 0),
                                "max_gap": details.get("max_actual_gap", 0),
                                "percentage": round((details["gap_count"] + details.get("reverse_count", 0)) / len(self.data) * 100, 2),
                                "severity": result["severity"],
                                "description": f"{details['gap_count']}件のギャップ、{details.get('reverse_count', 0)}件の逆行"
                            }
                        elif "missing_columns" in details:
                            category_scores[category]["details"][rule_key] = {
                                "missing_columns": details["missing_columns"],
                                "count": len(details["missing_columns"]),
                                "severity": result["severity"],
                                "description": f"{len(details['missing_columns'])}個の必須カラムが欠落"
                            }
                        elif "anomaly_count" in details:
                            category_scores[category]["details"][rule_key] = {
                                "count": details["anomaly_count"],
                                "percentage": round(details["anomaly_count"] / len(self.data) * 100, 2),
                                "max_speed": details.get("max_calculated_speed", 0),
                                "severity": result["severity"],
                                "description": f"{details['anomaly_count']}件の空間的異常"
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
            
            # 問題のあるすべてのレコードのインデックス
            all_problem_indices = self.problematic_indices["all"]
            
            # 時間範囲を決定
            min_time = valid_data["timestamp"].min()
            max_time = valid_data["timestamp"].max()
            time_range = max_time - min_time
            
            # 時間を12個の区間に分割
            hours_bins = 12
            time_step = time_range / hours_bins
            
            # 時間帯ごとのスコアを計算
            temporal_scores = []
            
            for i in range(hours_bins):
                bin_start = min_time + time_step * i
                bin_end = min_time + time_step * (i + 1)
                
                # 時間帯内のレコードを抽出
                bin_mask = (valid_data["timestamp"] >= bin_start) & (valid_data["timestamp"] < bin_end)
                bin_indices = valid_data.index[bin_mask].tolist()
                
                if bin_indices:
                    # 時間帯内の問題レコード数
                    problem_indices_in_bin = set(bin_indices).intersection(set(all_problem_indices))
                    problem_count = len(problem_indices_in_bin)
                    total_count = len(bin_indices)
                    
                    # 問題の割合に基づく品質スコア
                    problem_percentage = problem_count / total_count * 100 if total_count > 0 else 0
                    quality_score = max(0, 100 - problem_percentage)
                    
                    # 人間が読みやすい時間帯ラベルを作成
                    label = f"{bin_start.strftime('%H:%M')}-{bin_end.strftime('%H:%M')}"
                    
                    # 品質スコアを保存
                    temporal_scores.append({
                        "period": f"期間{i+1}",
                        "start_time": bin_start.isoformat(),
                        "end_time": bin_end.isoformat(),
                        "label": label,
                        "quality_score": quality_score,
                        "problem_count": problem_count,
                        "total_count": total_count,
                        "problem_percentage": problem_percentage,
                        "impact_level": self._determine_impact_level(quality_score)
                    })
            
            return temporal_scores
            
        except Exception as e:
            # エラーが発生した場合は空のリストを返す
            print(f"時間帯別の品質スコア計算中にエラー: {e}")
            return []
    
    def get_problem_distribution(self) -> Dict[str, Any]:
        """
        時間/空間における問題分布を計算
        
        Returns
        -------
        Dict[str, Any]
            時間的/空間的な問題分布
        """
        # 問題のある全てのレコードのインデックス
        all_problem_indices = self.problematic_indices["all"]
        
        if not all_problem_indices or len(self.data) == 0:
            return {
                "temporal": {"has_data": False},
                "spatial": {"has_data": False},
                "problem_type": {"has_data": False}
            }
        
        # 時間的分布
        temporal_distribution = self._calculate_temporal_distribution(all_problem_indices)
        
        # 空間的分布
        spatial_distribution = self._calculate_spatial_distribution(all_problem_indices)
        
        # 問題タイプ分布
        problem_type_distribution = self._calculate_problem_type_distribution()
        
        return {
            "temporal": temporal_distribution,
            "spatial": spatial_distribution,
            "problem_type": problem_type_distribution
        }
    
    def _calculate_temporal_distribution(self, problem_indices: List[int]) -> Dict[str, Any]:
        """
        時間的な問題分布を計算
        
        Parameters
        ----------
        problem_indices : List[int]
            問題のあるレコードのインデックス
            
        Returns
        -------
        Dict[str, Any]
            時間的な問題分布
        """
        # タイムスタンプカラムがない場合はスキップ
        if "timestamp" not in self.data.columns:
            return {"has_data": False}
        
        try:
            # 時間範囲を取得
            min_time = self.data["timestamp"].min()
            max_time = self.data["timestamp"].max()
            
            if pd.isna(min_time) or pd.isna(max_time):
                return {"has_data": False}
            
            # 時間範囲全体を10個のビンに分割
            time_range = max_time - min_time
            bin_size = time_range / 10
            
            bins = []
            for i in range(10):
                bin_start = min_time + bin_size * i
                bin_end = min_time + bin_size * (i + 1)
                bins.append((bin_start, bin_end))
            
            # 各ビンの問題カウントを計算
            bin_counts = []
            for bin_start, bin_end in bins:
                # ビン内のレコード数
                bin_mask = (self.data["timestamp"] >= bin_start) & (self.data["timestamp"] < bin_end)
                bin_records = self.data.index[bin_mask].tolist()
                
                # ビン内の問題レコード数
                problem_count = len(set(bin_records).intersection(set(problem_indices)))
                
                bin_counts.append({
                    "start": bin_start,
                    "end": bin_end,
                    "problem_count": problem_count,
                    "total_count": len(bin_records),
                    "problem_percentage": (problem_count / len(bin_records) * 100) if len(bin_records) > 0 else 0
                })
            
            # 問題の集中しているビンを特定
            if bin_counts:
                max_bin = max(bin_counts, key=lambda x: x["problem_percentage"])
                avg_percentage = sum(bin["problem_percentage"] for bin in bin_counts) / len(bin_counts)
                
                hotspots = []
                for bin_data in bin_counts:
                    if bin_data["problem_percentage"] > avg_percentage * 1.5 and bin_data["problem_count"] > 0:
                        hotspots.append(bin_data)
            else:
                max_bin = None
                hotspots = []
            
            return {
                "has_data": True,
                "time_range": {
                    "start": min_time,
                    "end": max_time,
                    "duration_seconds": time_range.total_seconds()
                },
                "bin_counts": bin_counts,
                "max_bin": max_bin,
                "hotspots": hotspots
            }
        
        except Exception as e:
            return {
                "has_data": False,
                "error": str(e)
            }
    
    def _calculate_spatial_distribution(self, problem_indices: List[int]) -> Dict[str, Any]:
        """
        空間的な問題分布を計算
        
        Parameters
        ----------
        problem_indices : List[int]
            問題のあるレコードのインデックス
            
        Returns
        -------
        Dict[str, Any]
            空間的な問題分布
        """
        # 位置情報カラムがない場合はスキップ
        if "latitude" not in self.data.columns or "longitude" not in self.data.columns:
            return {"has_data": False}
        
        try:
            # 位置の範囲を取得
            min_lat = self.data["latitude"].min()
            max_lat = self.data["latitude"].max()
            min_lon = self.data["longitude"].min()
            max_lon = self.data["longitude"].max()
            
            if (pd.isna(min_lat) or pd.isna(max_lat) or 
                pd.isna(min_lon) or pd.isna(max_lon)):
                return {"has_data": False}
            
            # 位置グリッドを生成（3x3グリッド）
            lat_bins = 3
            lon_bins = 3
            lat_step = (max_lat - min_lat) / lat_bins
            lon_step = (max_lon - min_lon) / lon_bins
            
            grid_counts = []
            for i in range(lat_bins):
                lat_start = min_lat + lat_step * i
                lat_end = min_lat + lat_step * (i + 1)
                
                for j in range(lon_bins):
                    lon_start = min_lon + lon_step * j
                    lon_end = min_lon + lon_step * (j + 1)
                    
                    # グリッド内のレコード数
                    grid_mask = ((self.data["latitude"] >= lat_start) & 
                                (self.data["latitude"] < lat_end) & 
                                (self.data["longitude"] >= lon_start) & 
                                (self.data["longitude"] < lon_end))
                    grid_records = self.data.index[grid_mask].tolist()
                    
                    # グリッド内の問題レコード数
                    problem_count = len(set(grid_records).intersection(set(problem_indices)))
                    
                    grid_counts.append({
                        "lat_range": (lat_start, lat_end),
                        "lon_range": (lon_start, lon_end),
                        "center": ((lat_start + lat_end) / 2, (lon_start + lon_end) / 2),
                        "problem_count": problem_count,
                        "total_count": len(grid_records),
                        "problem_percentage": (problem_count / len(grid_records) * 100) if len(grid_records) > 0 else 0
                    })
            
            # 問題の集中しているグリッドを特定
            if grid_counts:
                max_grid = max(grid_counts, key=lambda x: x["problem_percentage"])
                avg_percentage = sum(grid["problem_percentage"] for grid in grid_counts if grid["total_count"] > 0) / sum(1 for grid in grid_counts if grid["total_count"] > 0) if sum(1 for grid in grid_counts if grid["total_count"] > 0) > 0 else 0
                
                hotspots = []
                for grid_data in grid_counts:
                    if (grid_data["problem_percentage"] > avg_percentage * 1.5 and 
                        grid_data["problem_count"] > 0 and 
                        grid_data["total_count"] > 0):
                        hotspots.append(grid_data)
            else:
                max_grid = None
                hotspots = []
            
            return {
                "has_data": True,
                "lat_range": (min_lat, max_lat),
                "lon_range": (min_lon, max_lon),
                "grid_counts": grid_counts,
                "max_grid": max_grid,
                "hotspots": hotspots
            }
        
        except Exception as e:
            return {
                "has_data": False,
                "error": str(e)
            }
    
    def _calculate_problem_type_distribution(self) -> Dict[str, Any]:
        """
        問題タイプごとの詳細分布を計算
        
        Returns
        -------
        Dict[str, Any]
            問題タイプ分布
        """
        # 問題タイプごとの件数
        problem_counts = {
            "missing_data": len(self.problematic_indices.get("missing_data", [])),
            "out_of_range": len(self.problematic_indices.get("out_of_range", [])),
            "duplicates": len(self.problematic_indices.get("duplicates", [])),
            "spatial_anomalies": len(self.problematic_indices.get("spatial_anomalies", [])),
            "temporal_anomalies": len(self.problematic_indices.get("temporal_anomalies", []))
        }
        
        # 問題タイプごとの詳細情報
        problem_details = {}
        
        # 欠損値の詳細
        if problem_counts["missing_data"] > 0:
            columns_with_nulls = {}
            for result in self.validation_results:
                if not result["is_valid"] and "No Null Values Check" in result["rule_name"]:
                    details = result["details"]
                    if "null_counts" in details:
                        for col, count in details["null_counts"].items():
                            if count > 0:
                                columns_with_nulls[col] = count
            
            problem_details["missing_data"] = {
                "affected_columns": columns_with_nulls,
                "total_count": problem_counts["missing_data"]
            }
        
        # 範囲外の値の詳細
        if problem_counts["out_of_range"] > 0:
            out_of_range_info = {}
            for result in self.validation_results:
                if not result["is_valid"] and "Value Range Check" in result["rule_name"]:
                    details = result["details"]
                    column = details.get("column", "")
                    if column and "out_of_range_count" in details:
                        out_of_range_info[column] = {
                            "count": details["out_of_range_count"],
                            "min_value": details.get("min_value"),
                            "max_value": details.get("max_value"),
                            "actual_min": details.get("actual_min"),
                            "actual_max": details.get("actual_max")
                        }
            
            problem_details["out_of_range"] = {
                "affected_columns": out_of_range_info,
                "total_count": problem_counts["out_of_range"]
            }
        
        # 重複の詳細
        if problem_counts["duplicates"] > 0:
            duplicate_info = {}
            for result in self.validation_results:
                if not result["is_valid"] and "No Duplicate Timestamps" in result["rule_name"]:
                    details = result["details"]
                    if "duplicate_count" in details:
                        duplicate_info["timestamp"] = {
                            "count": details["duplicate_count"],
                            "duplicate_timestamps_count": len(details.get("duplicate_timestamps", []))
                        }
            
            problem_details["duplicates"] = {
                "affected_columns": duplicate_info,
                "total_count": problem_counts["duplicates"]
            }
        
        # 空間的異常の詳細
        if problem_counts["spatial_anomalies"] > 0:
            spatial_info = {}
            for result in self.validation_results:
                if not result["is_valid"] and "Spatial Consistency Check" in result["rule_name"]:
                    details = result["details"]
                    if "anomaly_count" in details:
                        spatial_info["position"] = {
                            "count": details["anomaly_count"],
                            "max_speed": details.get("max_calculated_speed", 0)
                        }
            
            problem_details["spatial_anomalies"] = {
                "affected_attributes": spatial_info,
                "total_count": problem_counts["spatial_anomalies"]
            }
        
        # 時間的異常の詳細
        if problem_counts["temporal_anomalies"] > 0:
            temporal_info = {}
            for result in self.validation_results:
                if not result["is_valid"] and "Temporal Consistency Check" in result["rule_name"]:
                    details = result["details"]
                    temporal_info["timestamp"] = {
                        "gap_count": details.get("gap_count", 0),
                        "reverse_count": details.get("reverse_count", 0),
                        "max_gap": details.get("max_actual_gap", 0),
                        "min_gap": details.get("min_actual_gap", 0)
                    }
            
            problem_details["temporal_anomalies"] = {
                "affected_attributes": temporal_info,
                "total_count": problem_counts["temporal_anomalies"]
            }
        
        return {
            "has_data": True,
            "problem_counts": problem_counts,
            "problem_details": problem_details,
            "total_problems": sum(problem_counts.values())
        }
        
    def get_problem_severity_distribution(self) -> Dict[str, int]:
        """
        問題の重要度ごとの分布を取得
        
        Returns
        -------
        Dict[str, int]
            重要度ごとの問題数
        """
        severity_counts = {
            "error": 0,
            "warning": 0,
            "info": 0
        }
        
        for result in self.validation_results:
            if not result["is_valid"]:
                severity = result["severity"]
                severity_counts[severity] += 1
        
        return severity_counts
    
    def get_problematic_columns(self) -> Dict[str, Dict[str, Any]]:
        """
        問題のあるカラムとその詳細を取得
        
        Returns
        -------
        Dict[str, Dict[str, Any]]
            カラム名とその問題詳細のマッピング
        """
        problematic_columns = {}
        
        for result in self.validation_results:
            if not result["is_valid"]:
                details = result["details"]
                
                # カラム特定
                columns = []
                
                if "column" in details:
                    columns = [details["column"]]
                elif "null_counts" in details:
                    columns = [col for col, count in details["null_counts"].items() if count > 0]
                elif "columns" in details:
                    columns = details["columns"]
                
                for col in columns:
                    if col not in problematic_columns:
                        problematic_columns[col] = {
                            "issues": [],
                            "severity": "info"
                        }
                    
                    # 問題の追加
                    issue_type = ""
                    if "No Null Values Check" in result["rule_name"]:
                        issue_type = "missing_values"
                    elif "Value Range Check" in result["rule_name"]:
                        issue_type = "out_of_range"
                    elif "Spatial Consistency" in result["rule_name"] and col in ["latitude", "longitude"]:
                        issue_type = "spatial_anomaly"
                    elif "Temporal Consistency" in result["rule_name"] and col == "timestamp":
                        issue_type = "temporal_anomaly"
                    elif "No Duplicate Timestamps" in result["rule_name"] and col == "timestamp":
                        issue_type = "duplicates"
                    
                    if issue_type and issue_type not in problematic_columns[col]["issues"]:
                        problematic_columns[col]["issues"].append(issue_type)
                    
                    # 最も重要な重要度を設定
                    severity = result["severity"]
                    if severity == "error" or problematic_columns[col]["severity"] == "error":
                        problematic_columns[col]["severity"] = "error"
                    elif severity == "warning" and problematic_columns[col]["severity"] != "error":
                        problematic_columns[col]["severity"] = "warning"
        
        return problematic_columns
    
    def get_quality_summary(self) -> Dict[str, Any]:
        """
        データ品質の要約情報を取得
        
        Returns
        -------
        Dict[str, Any]
            品質サマリー
        """
        # 問題のカウント
        issue_counts = {
            "total_records": len(self.data),
            "problematic_records": len(self.problematic_indices["all"]),
            "problematic_percentage": round(len(self.problematic_indices["all"]) / len(self.data) * 100, 2) if len(self.data) > 0 else 0,
            "missing_data": len(self.problematic_indices["missing_data"]),
            "out_of_range": len(self.problematic_indices["out_of_range"]),
            "duplicates": len(self.problematic_indices["duplicates"]),
            "spatial_anomalies": len(self.problematic_indices["spatial_anomalies"]),
            "temporal_anomalies": len(self.problematic_indices["temporal_anomalies"])
        }
        
        # 重要度別のカウント
        severity_counts = self.get_problem_severity_distribution()
        
        # 問題の修正可能性
        fixable_counts = {
            "auto_fixable": 0,
            "semi_auto_fixable": 0,
            "manual_fix_required": 0
        }
        
        for result in self.validation_results:
            if not result["is_valid"]:
                rule_name = result["rule_name"]
                details = result["details"]
                
                # 修正可能性を判定
                if "No Duplicate Timestamps" in rule_name or "Temporal Consistency" in rule_name:
                    # 重複タイムスタンプや時間的整合性は自動修正可能
                    fixable_counts["auto_fixable"] += 1
                elif "No Null Values Check" in rule_name:
                    # 欠損値は半自動修正（補間または削除）
                    fixable_counts["semi_auto_fixable"] += 1
                elif "Value Range Check" in rule_name or "Spatial Consistency" in rule_name:
                    # 範囲外の値や空間的整合性も半自動修正
                    fixable_counts["semi_auto_fixable"] += 1
                else:
                    # その他は手動修正が必要
                    fixable_counts["manual_fix_required"] += 1
        
        # パフォーマンス関連のメトリクス
        performance_metrics = self._calculate_performance_metrics()
        
        # データ品質サマリーを構築
        return {
            "quality_score": self.quality_scores,
            "issue_counts": issue_counts,
            "severity_counts": severity_counts,
            "fixable_counts": fixable_counts,
            "performance_metrics": performance_metrics,
            "timestamp": datetime.now().isoformat()
        }
    
    def _calculate_performance_metrics(self) -> Dict[str, Any]:
        """
        パフォーマンス関連のメトリクスを計算
        
        Returns
        -------
        Dict[str, Any]
            パフォーマンスメトリクス
        """
        metrics = {
            "data_size": {
                "rows": len(self.data),
                "columns": len(self.data.columns),
                "memory_usage_bytes": self.data.memory_usage(deep=True).sum()
            },
            "processing_speed": {
                "estimated_processing_time_ms": len(self.data) * 0.1  # サンプル計算（実際のパフォーマンス測定に置き換え可能）
            },
            "data_density": {}
        }
        
        # 時間的な密度（1分あたりのデータポイント数など）
        if "timestamp" in self.data.columns and len(self.data) > 1:
            try:
                time_range = (self.data["timestamp"].max() - self.data["timestamp"].min()).total_seconds()
                if time_range > 0:
                    points_per_minute = len(self.data) / (time_range / 60)
                    metrics["data_density"]["points_per_minute"] = round(points_per_minute, 2)
                    metrics["data_density"]["time_range_seconds"] = time_range
            except Exception:
                pass  # タイムスタンプの計算でエラーが発生した場合はスキップ
        
        # 空間的な密度
        if "latitude" in self.data.columns and "longitude" in self.data.columns:
            try:
                lat_range = self.data["latitude"].max() - self.data["latitude"].min()
                lon_range = self.data["longitude"].max() - self.data["longitude"].min()
                if lat_range > 0 and lon_range > 0:
                    # 近似的な面積計算（正確な地理的計算ではない）
                    approx_area = lat_range * lon_range
                    density = len(self.data) / approx_area
                    metrics["data_density"]["spatial_density"] = round(density, 2)
                    metrics["data_density"]["approx_area"] = round(approx_area, 6)
            except Exception:
                pass  # 空間計算でエラーが発生した場合はスキップ
        
        return metrics
        
    def get_fix_recommendations(self) -> List[Dict[str, Any]]:
        """
        検出された問題に対する修正推奨を生成
        
        Returns
        -------
        List[Dict[str, Any]]
            修正推奨のリスト
        """
        recommendations = []
        
        # 各検証結果に対する推奨事項を生成
        for result in self.validation_results:
            if not result["is_valid"]:
                rule_name = result["rule_name"]
                severity = result["severity"]
                details = result["details"]
                
                # 欠落カラムの問題
                if "missing_columns" in details and details["missing_columns"]:
                    for col in details["missing_columns"]:
                        recommendations.append({
                            "rule": rule_name,
                            "severity": severity,
                            "problem_type": "missing_columns",
                            "issue": f"必須カラム '{col}' が欠落しています",
                            "recommendation": "データインポート時にこのカラムをマッピングしてください",
                            "automatic_fix": False,  # 自動修正不可
                            "action_type": "import_mapping",
                            "affected_count": 0,
                            "affected_percentage": 0
                        })
                
                # 欠損値の問題
                elif "total_null_count" in details and details["total_null_count"] > 0:
                    null_counts = details.get("null_counts", {})
                    for col, count in null_counts.items():
                        if count > 0:
                            percentage = (count / len(self.data) * 100) if len(self.data) > 0 else 0
                            recommendations.append({
                                "rule": rule_name,
                                "severity": severity,
                                "problem_type": "missing_data",
                                "issue": f"カラム '{col}' に {count}個の欠損値があります",
                                "recommendation": "線形補間で欠損値を埋めるか、欠損値を持つ行を削除してください",
                                "automatic_fix": True,  # 自動修正可能
                                "action_type": "fill_nulls",
                                "column": col,
                                "method": "interpolate",
                                "affected_count": count,
                                "affected_percentage": percentage,
                                "fix_options": [
                                    {"id": "interpolate", "name": "線形補間", "description": "前後の値から補間"},
                                    {"id": "ffill", "name": "前方向に埋める", "description": "直前の値で埋める"},
                                    {"id": "remove", "name": "行を削除", "description": "欠損値を含む行を削除"}
                                ]
                            })
                
                # 範囲外の値
                elif "out_of_range_count" in details and details["out_of_range_count"] > 0:
                    col = details.get("column", "")
                    min_val = details.get("min_value", None)
                    max_val = details.get("max_value", None)
                    
                    range_str = ""
                    if min_val is not None and max_val is not None:
                        range_str = f"{min_val}から{max_val}の範囲内"
                    elif min_val is not None:
                        range_str = f"{min_val}以上"
                    elif max_val is not None:
                        range_str = f"{max_val}以下"
                    
                    percentage = (details["out_of_range_count"] / len(self.data) * 100) if len(self.data) > 0 else 0
                    recommendations.append({
                        "rule": rule_name,
                        "severity": severity,
                        "problem_type": "out_of_range",
                        "issue": f"カラム '{col}' に {details['out_of_range_count']}個の範囲外の値があります",
                        "recommendation": f"値を{range_str}にクリップするか、異常値を持つ行を削除してください",
                        "automatic_fix": True,  # 自動修正可能
                        "action_type": "clip_values",
                        "column": col,
                        "min_value": min_val,
                        "max_value": max_val,
                        "affected_count": details["out_of_range_count"],
                        "affected_percentage": percentage,
                        "fix_options": [
                            {"id": "clip", "name": "値を制限", "description": f"値を{range_str}に制限"},
                            {"id": "remove", "name": "行を削除", "description": "範囲外の値を含む行を削除"}
                        ]
                    })
                
                # 重複タイムスタンプ
                elif "duplicate_count" in details and details["duplicate_count"] > 0:
                    percentage = (details["duplicate_count"] / len(self.data) * 100) if len(self.data) > 0 else 0
                    recommendations.append({
                        "rule": rule_name,
                        "severity": severity,
                        "problem_type": "duplicates",
                        "issue": f"{details['duplicate_count']}個の重複タイムスタンプがあります",
                        "recommendation": "タイムスタンプを少しずつずらすか、重複行を削除してください",
                        "automatic_fix": True,  # 自動修正可能
                        "action_type": "fix_duplicates",
                        "affected_count": details["duplicate_count"],
                        "affected_percentage": percentage,
                        "fix_options": [
                            {"id": "offset", "name": "時間をずらす", "description": "重複するタイムスタンプを1ミリ秒ずつずらす"},
                            {"id": "remove", "name": "重複を削除", "description": "重複する2番目以降の行を削除"}
                        ]
                    })
                
                # 空間的異常
                elif "anomaly_count" in details and "Spatial Consistency" in rule_name and details["anomaly_count"] > 0:
                    percentage = (details["anomaly_count"] / len(self.data) * 100) if len(self.data) > 0 else 0
                    recommendations.append({
                        "rule": rule_name,
                        "severity": severity,
                        "problem_type": "spatial_anomalies",
                        "issue": f"{details['anomaly_count']}個の空間的異常があります",
                        "recommendation": "異常な位置ジャンプのあるポイントを削除または補間してください",
                        "automatic_fix": True,  # 自動修正可能
                        "action_type": "fix_spatial",
                        "affected_count": details["anomaly_count"],
                        "affected_percentage": percentage,
                        "max_speed": details.get("max_calculated_speed", 0),
                        "fix_options": [
                            {"id": "interpolate", "name": "位置を補間", "description": "異常ポイントの位置を前後から補間"},
                            {"id": "remove", "name": "ポイントを削除", "description": "異常ポイントを削除"}
                        ]
                    })
                
                # 時間的異常（ギャップや逆行）
                elif ("gap_count" in details or "reverse_count" in details) and "Temporal Consistency" in rule_name:
                    gap_count = details.get("gap_count", 0)
                    reverse_count = details.get("reverse_count", 0)
                    total_anomalies = gap_count + reverse_count
                    
                    if total_anomalies > 0:
                        percentage = (total_anomalies / len(self.data) * 100) if len(self.data) > 0 else 0
                        
                        # ギャップの推奨
                        if gap_count > 0:
                            recommendations.append({
                                "rule": rule_name,
                                "severity": severity,
                                "problem_type": "temporal_anomalies",
                                "issue": f"{gap_count}個の時間ギャップがあります",
                                "recommendation": "大きな時間ギャップはセッションの分割を検討してください",
                                "automatic_fix": False,  # 手動での検討が必要
                                "action_type": "mark_gaps",
                                "affected_count": gap_count,
                                "affected_percentage": (gap_count / len(self.data) * 100) if len(self.data) > 0 else 0,
                                "max_gap": details.get("max_actual_gap", 0),
                                "fix_options": [
                                    {"id": "mark_gaps", "name": "ギャップをマーク", "description": "時間ギャップをメタデータに記録"}
                                ]
                            })
                        
                        # 逆行の推奨
                        if reverse_count > 0:
                            recommendations.append({
                                "rule": rule_name,
                                "severity": severity,
                                "problem_type": "temporal_anomalies",
                                "issue": f"{reverse_count}個の時間逆行があります",
                                "recommendation": "時間が逆行しているポイントを修正または削除してください",
                                "automatic_fix": True,  # 自動修正可能
                                "action_type": "fix_reverse",
                                "affected_count": reverse_count,
                                "affected_percentage": (reverse_count / len(self.data) * 100) if len(self.data) > 0 else 0,
                                "fix_options": [
                                    {"id": "fix_reverse", "name": "逆行を修正", "description": "時間逆行を自動修正"},
                                    {"id": "remove", "name": "ポイントを削除", "description": "逆行ポイントを削除"}
                                ]
                            })
        
        # 推奨の優先度でソート
        recommendations.sort(key=lambda x: (
            0 if x["severity"] == "error" else (1 if x["severity"] == "warning" else 2),
            -x.get("affected_percentage", 0)
        ))
        
        return recommendations
        
    def get_record_quality_score(self, record_index: int) -> Dict[str, float]:
        """
        個別レコードの品質スコアを取得
        
        Parameters
        ----------
        record_index : int
            レコードのインデックス
            
        Returns
        -------
        Dict[str, float]
            各スコア（completeness, accuracy, consistency, total）
        """
        # デフォルトのスコア（問題なし）
        scores = {
            "completeness": 100.0,
            "accuracy": 100.0,
            "consistency": 100.0,
            "total": 100.0
        }
        
        # このレコードに関わる問題をチェック
        for problem_type, indices in self.problematic_indices.items():
            if problem_type == "all":
                continue
                
            if record_index in indices:
                # 問題タイプに基づいてスコアを減点
                if problem_type == "missing_data":
                    scores["completeness"] -= 50.0
                elif problem_type == "out_of_range":
                    scores["accuracy"] -= 50.0
                elif problem_type == "duplicates":
                    scores["consistency"] -= 50.0
                elif problem_type == "spatial_anomalies":
                    scores["accuracy"] -= 30.0
                elif problem_type == "temporal_anomalies":
                    scores["consistency"] -= 30.0
        
        # スコアを0〜100の範囲に収める
        for key in scores:
            if key != "total":
                scores[key] = max(0, min(100, scores[key]))
        
        # 総合スコアを計算
        scores["total"] = sum([scores["completeness"], scores["accuracy"], scores["consistency"]]) / 3.0
        scores["total"] = max(0, min(100, scores["total"]))
        
        return scores
        
    def get_extended_temporal_metrics(self) -> Dict[str, Any]:
        """
        拡張された時間的品質メトリクスを計算
        
        Returns
        -------
        Dict[str, Any]
            拡張された時間的品質メトリクス
        """
        # 問題のある全てのレコードのインデックス
        all_problem_indices = self.problematic_indices["all"]
        
        # タイムスタンプカラムがない場合はスキップ
        if "timestamp" not in self.data.columns:
            return {"has_data": False}
        
        try:
            # タイムスタンプが存在するレコードのみを抽出
            valid_data = self.data.dropna(subset=["timestamp"])
            
            if len(valid_data) < 2:
                return {"has_data": False, "reason": "タイムスタンプ付きのデータが不足"}
            
            # 時間範囲を取得
            min_time = valid_data["timestamp"].min()
            max_time = valid_data["timestamp"].max()
            time_range = max_time - min_time
            
            # 時間品質スコアの計算
            time_quality_scores = []
            
            # 時間を12個のビンに分割（時間帯別の分析用）
            hours_bins = 12
            hour_step = 24 / hours_bins
            hour_counts = np.zeros(hours_bins)
            hour_problem_counts = np.zeros(hours_bins)
            
            for idx, row in valid_data.iterrows():
                # 時間帯のビンを計算
                hour = row["timestamp"].hour
                hour_bin = min(hours_bins - 1, int(hour / hour_step))
                hour_counts[hour_bin] += 1
                
                # 問題があれば問題カウントを増やす
                if idx in all_problem_indices:
                    hour_problem_counts[hour_bin] += 1
            
            # 時間帯別の品質スコアを計算
            for i in range(hours_bins):
                if hour_counts[i] > 0:
                    problem_percentage = (hour_problem_counts[i] / hour_counts[i]) * 100
                    quality_score = max(0, 100 - problem_percentage)
                    
                    start_hour = i * hour_step
                    end_hour = (i + 1) * hour_step
                    
                    time_quality_scores.append({
                        "bin_index": i,
                        "start_hour": start_hour,
                        "end_hour": end_hour,
                        "label": f"{int(start_hour)}時-{int(end_hour)}時",
                        "quality_score": quality_score,
                        "problem_count": int(hour_problem_counts[i]),
                        "total_count": int(hour_counts[i])
                    })
            
            # 時間間隔の分析
            timestamps = valid_data["timestamp"].sort_values().tolist()
            intervals = [(timestamps[i+1] - timestamps[i]).total_seconds() 
                      for i in range(len(timestamps) - 1)]
            
            # 基本的な時間統計
            time_stats = {
                "min_time": min_time,
                "max_time": max_time,
                "duration_seconds": time_range.total_seconds(),
                "record_count": len(valid_data),
                "avg_interval_seconds": sum(intervals) / len(intervals) if intervals else 0,
                "min_interval_seconds": min(intervals) if intervals else 0,
                "max_interval_seconds": max(intervals) if intervals else 0
            }
            
            # 問題タイプ別の時間分布
            problem_type_temporal = {}
            
            for problem_type in ["missing_data", "out_of_range", "duplicates", 
                              "spatial_anomalies", "temporal_anomalies"]:
                indices = self.problematic_indices[problem_type]
                if indices:
                    # 対象インデックスの行のみを抽出
                    type_rows = []
                    for idx in indices:
                        if idx < len(self.data) and pd.notna(self.data.iloc[idx].get("timestamp")):
                            type_rows.append({
                                "index": idx,
                                "timestamp": self.data.iloc[idx]["timestamp"]
                            })
                    
                    if type_rows:
                        # 時間順にソート
                        type_rows.sort(key=lambda x: x["timestamp"])
                        
                        # 時間分布を作成
                        problem_type_temporal[problem_type] = {
                            "count": len(type_rows),
                            "min_time": type_rows[0]["timestamp"],
                            "max_time": type_rows[-1]["timestamp"],
                            "duration_seconds": (type_rows[-1]["timestamp"] - type_rows[0]["timestamp"]).total_seconds(),
                            "time_of_day_distribution": self._calculate_time_of_day_distribution(type_rows)
                        }
            
            return {
                "has_data": True,
                "time_stats": time_stats,
                "time_quality_scores": time_quality_scores,
                "problem_type_temporal": problem_type_temporal
            }
            
        except Exception as e:
            return {
                "has_data": False,
                "error": str(e)
            }
    
    def _calculate_time_of_day_distribution(self, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        一日の時間帯ごとの問題分布を計算
        
        Parameters
        ----------
        rows : List[Dict[str, Any]]
            タイムスタンプを含む行のリスト
            
        Returns
        -------
        Dict[str, Any]
            時間帯ごとの分布
        """
        # 時間帯の定義
        time_periods = [
            {"name": "早朝", "start": 5, "end": 8},
            {"name": "午前", "start": 8, "end": 12},
            {"name": "午後", "start": 12, "end": 17},
            {"name": "夕方", "start": 17, "end": 20},
            {"name": "夜間", "start": 20, "end": 24},
            {"name": "深夜", "start": 0, "end": 5}
        ]
        
        # 各時間帯のカウント
        period_counts = {period["name"]: 0 for period in time_periods}
        
        for row in rows:
            hour = row["timestamp"].hour
            for period in time_periods:
                if (period["start"] <= hour < period["end"]):
                    period_counts[period["name"]] += 1
                    break
        
        # 結果を構築
        distribution = {
            "periods": time_periods,
            "counts": period_counts,
            "max_period": max(period_counts.items(), key=lambda x: x[1])[0] if period_counts else None,
            "hour_histogram": [0] * 24
        }
        
        # 時間別のヒストグラム
        for row in rows:
            hour = row["timestamp"].hour
            distribution["hour_histogram"][hour] += 1
        
        return distribution
    
    def get_extended_spatial_metrics(self) -> Dict[str, Any]:
        """
        拡張された空間的品質メトリクスを計算
        
        Returns
        -------
        Dict[str, Any]
            拡張された空間的品質メトリクス
        """
        # 問題のある全てのレコードのインデックス
        all_problem_indices = self.problematic_indices["all"]
        
        # 位置情報カラムがない場合はスキップ
        if "latitude" not in self.data.columns or "longitude" not in self.data.columns:
            return {"has_data": False}
        
        try:
            # 有効な位置情報を持つレコードのみを抽出
            valid_data = self.data.dropna(subset=["latitude", "longitude"])
            
            if len(valid_data) < 5:
                return {"has_data": False, "reason": "位置情報付きのデータが不足"}
            
            # 位置の範囲を取得
            min_lat = valid_data["latitude"].min()
            max_lat = valid_data["latitude"].max()
            min_lon = valid_data["longitude"].min()
            max_lon = valid_data["longitude"].max()
            
            # 空間品質スコアの計算
            # より細かいグリッドで分析（5x5グリッド）
            lat_bins = 5
            lon_bins = 5
            
            lat_step = (max_lat - min_lat) / lat_bins
            lon_step = (max_lon - min_lon) / lon_bins
            
            grid_quality_scores = []
            
            for i in range(lat_bins):
                lat_start = min_lat + lat_step * i
                lat_end = min_lat + lat_step * (i + 1)
                
                for j in range(lon_bins):
                    lon_start = min_lon + lon_step * j
                    lon_end = min_lon + lon_step * (j + 1)
                    
                    # グリッド内のレコード数
                    grid_mask = ((valid_data["latitude"] >= lat_start) & 
                                (valid_data["latitude"] < lat_end) & 
                                (valid_data["longitude"] >= lon_start) & 
                                (valid_data["longitude"] < lon_end))
                    grid_indices = valid_data.index[grid_mask].tolist()
                    
                    if grid_indices:
                        # グリッド内の問題数
                        problem_indices_in_grid = set(grid_indices).intersection(set(all_problem_indices))
                        problem_count = len(problem_indices_in_grid)
                        total_count = len(grid_indices)
                        
                        # 問題の割合に基づく品質スコア
                        problem_percentage = (problem_count / total_count * 100)
                        quality_score = max(0, 100 - problem_percentage)
                        
                        grid_quality_scores.append({
                            "lat_range": (lat_start, lat_end),
                            "lon_range": (lon_start, lon_end),
                            "center": ((lat_start + lat_end) / 2, (lon_start + lon_end) / 2),
                            "quality_score": quality_score,
                            "problem_count": problem_count,
                            "total_count": total_count,
                            "grid_id": f"grid_{i}_{j}"
                        })
            
            # 問題タイプ別の空間分布
            problem_type_spatial = {}
            
            for problem_type in ["missing_data", "out_of_range", "duplicates", 
                              "spatial_anomalies", "temporal_anomalies"]:
                indices = self.problematic_indices[problem_type]
                if indices:
                    # 対象インデックスの行のみを抽出
                    type_points = []
                    for idx in indices:
                        if idx < len(self.data):
                            row = self.data.iloc[idx]
                            lat = row.get("latitude")
                            lon = row.get("longitude")
                            if pd.notna(lat) and pd.notna(lon):
                                type_points.append({
                                    "index": idx,
                                    "latitude": lat,
                                    "longitude": lon
                                })
                    
                    if type_points:
                        # 空間的な統計情報
                        lats = [p["latitude"] for p in type_points]
                        lons = [p["longitude"] for p in type_points]
                        
                        problem_type_spatial[problem_type] = {
                            "count": len(type_points),
                            "points": type_points,
                            "bounds": {
                                "min_lat": min(lats),
                                "max_lat": max(lats),
                                "min_lon": min(lons),
                                "max_lon": max(lons)
                            }
                        }
                        
                        # 密度集中分析
                        if len(type_points) >= 5:
                            # グリッドベースの密度分析
                            density_grid = np.zeros((lat_bins, lon_bins))
                            for point in type_points:
                                lat_idx = min(lat_bins - 1, max(0, int((point["latitude"] - min_lat) / lat_step)))
                                lon_idx = min(lon_bins - 1, max(0, int((point["longitude"] - min_lon) / lon_step)))
                                density_grid[lat_idx, lon_idx] += 1
                            
                            # 高密度エリアの特定
                            hotspots = []
                            avg_density = np.sum(density_grid) / np.count_nonzero(density_grid) if np.count_nonzero(density_grid) > 0 else 0
                            
                            for i in range(lat_bins):
                                for j in range(lon_bins):
                                    if density_grid[i, j] > avg_density * 1.5:
                                        hotspots.append({
                                            "lat_idx": i,
                                            "lon_idx": j,
                                            "center": (
                                                min_lat + lat_step * (i + 0.5),
                                                min_lon + lon_step * (j + 0.5)
                                            ),
                                            "count": int(density_grid[i, j])
                                        })
                            
                            problem_type_spatial[problem_type]["hotspots"] = hotspots
            
            # 拡張分析: 速度と方向の一貫性分析
            track_quality = self.analyze_spatial_quality(valid_data)
            
            return {
                "has_data": True,
                "spatial_bounds": {
                    "min_lat": min_lat,
                    "max_lat": max_lat,
                    "min_lon": min_lon,
                    "max_lon": max_lon
                },
                "grid_quality_scores": grid_quality_scores,
                "problem_type_spatial": problem_type_spatial,
                "track_quality": track_quality
            }
            
        except Exception as e:
            return {
                "has_data": False,
                "error": str(e)
            }
            
    def analyze_spatial_quality(self, valid_data: pd.DataFrame) -> Dict[str, Any]:
        """
        位置情報の品質を詳細に評価する拡張分析
        
        Parameters
        ----------
        valid_data : pd.DataFrame
            有効な位置情報を持つデータフレーム
            
        Returns
        -------
        Dict[str, Any]
            詳細な空間品質メトリクス
        """
        try:
            # 必要なカラムがあるかチェック
            required_cols = ["latitude", "longitude", "timestamp"]
            if not all(col in valid_data.columns for col in required_cols):
                return {
                    "has_data": False,
                    "reason": "必要なカラムが不足しています"
                }
            
            # データを時間順にソート
            sorted_data = valid_data.sort_values("timestamp").copy()
            
            if len(sorted_data) < 3:
                return {
                    "has_data": False,
                    "reason": "分析に必要なデータポイントが不足しています"
                }
            
            # 連続するポイント間の距離と方向を計算
            from geopy.distance import great_circle
            import math
            
            distances = []
            bearings = []
            speeds = []
            acceleration = []
            turn_rates = []
            
            prev_lat = sorted_data["latitude"].iloc[0]
            prev_lon = sorted_data["longitude"].iloc[0]
            prev_time = sorted_data["timestamp"].iloc[0]
            prev_bearing = None
            prev_speed = None
            
            for i in range(1, len(sorted_data)):
                curr_lat = sorted_data["latitude"].iloc[i]
                curr_lon = sorted_data["longitude"].iloc[i]
                curr_time = sorted_data["timestamp"].iloc[i]
                
                # 距離の計算
                distance = great_circle((prev_lat, prev_lon), (curr_lat, curr_lon)).meters
                distances.append(distance)
                
                # 時間差の計算（秒単位）
                time_diff = (curr_time - prev_time).total_seconds()
                
                # 速度の計算（ノット単位、1ノット = 0.514444 m/s）
                if time_diff > 0:
                    speed = (distance / time_diff) / 0.514444
                else:
                    speed = float('nan')
                speeds.append(speed)
                
                # 進行方向の計算（度数単位）
                # 簡易計算（緯度経度を直交座標として近似）
                y = curr_lat - prev_lat
                x = (curr_lon - prev_lon) * math.cos(math.radians((curr_lat + prev_lat) / 2))
                bearing = (math.degrees(math.atan2(x, y)) + 360) % 360
                bearings.append(bearing)
                
                # 加速度の計算
                if prev_speed is not None and not math.isnan(speed) and not math.isnan(prev_speed) and time_diff > 0:
                    accel = (speed - prev_speed) / time_diff
                    acceleration.append(accel)
                elif i > 1:
                    acceleration.append(float('nan'))
                
                # 旋回率の計算
                if prev_bearing is not None and not math.isnan(bearing) and not math.isnan(prev_bearing) and time_diff > 0:
                    # 角度の差分を[-180, 180]の範囲に正規化
                    bearing_diff = (bearing - prev_bearing + 180) % 360 - 180
                    turn_rate = bearing_diff / time_diff
                    turn_rates.append(turn_rate)
                elif i > 1:
                    turn_rates.append(float('nan'))
                
                prev_lat, prev_lon, prev_time = curr_lat, curr_lon, curr_time
                prev_bearing, prev_speed = bearing, speed
            
            # 統計量の計算
            valid_speeds = [s for s in speeds if not math.isnan(s)]
            valid_accel = [a for a in acceleration if not math.isnan(a)]
            valid_turn_rates = [t for t in turn_rates if not math.isnan(t)]
            
            stats = {
                "speed": {
                    "min": min(valid_speeds) if valid_speeds else None,
                    "max": max(valid_speeds) if valid_speeds else None,
                    "mean": sum(valid_speeds) / len(valid_speeds) if valid_speeds else None,
                    "std": np.std(valid_speeds) if valid_speeds else None,
                    "percentiles": {
                        "25": np.percentile(valid_speeds, 25) if valid_speeds else None,
                        "50": np.percentile(valid_speeds, 50) if valid_speeds else None,
                        "75": np.percentile(valid_speeds, 75) if valid_speeds else None,
                        "90": np.percentile(valid_speeds, 90) if valid_speeds else None
                    }
                },
                "acceleration": {
                    "min": min(valid_accel) if valid_accel else None,
                    "max": max(valid_accel) if valid_accel else None,
                    "mean": sum(valid_accel) / len(valid_accel) if valid_accel else None,
                    "std": np.std(valid_accel) if valid_accel else None,
                    "abs_mean": sum(abs(a) for a in valid_accel) / len(valid_accel) if valid_accel else None
                },
                "turn_rate": {
                    "min": min(valid_turn_rates) if valid_turn_rates else None,
                    "max": max(valid_turn_rates) if valid_turn_rates else None,
                    "mean": sum(valid_turn_rates) / len(valid_turn_rates) if valid_turn_rates else None,
                    "std": np.std(valid_turn_rates) if valid_turn_rates else None,
                    "abs_mean": sum(abs(t) for t in valid_turn_rates) / len(valid_turn_rates) if valid_turn_rates else None
                }
            }
            
            # 速度の一貫性評価
            if valid_speeds:
                cv_speed = stats["speed"]["std"] / stats["speed"]["mean"] if stats["speed"]["mean"] > 0 else float('inf')
                stats["speed"]["consistency"] = 100 * (1 - min(1, cv_speed / 2))  # 変動係数を0-100のスコアに変換
            else:
                stats["speed"]["consistency"] = None
            
            # 進行方向の一貫性評価
            if valid_turn_rates:
                avg_abs_turn_rate = stats["turn_rate"]["abs_mean"]
                # 高い旋回率は低いスコアに、ただし旋回が全くないのも不自然なので最高でも95点
                stats["turn_rate"]["consistency"] = 95 * (1 - min(1, avg_abs_turn_rate / 30))
            else:
                stats["turn_rate"]["consistency"] = None
            
            # トラックの品質スコア
            track_quality_score = None
            if stats["speed"]["consistency"] is not None and stats["turn_rate"]["consistency"] is not None:
                track_quality_score = (stats["speed"]["consistency"] * 0.6 + 
                                      stats["turn_rate"]["consistency"] * 0.4)
            
            # 進路情報を保持
            tracks = []
            for i in range(len(distances)):
                if i < len(speeds) and i < len(bearings):
                    tracks.append({
                        "distance_m": distances[i],
                        "speed_knots": speeds[i],
                        "bearing_deg": bearings[i],
                        "acceleration": acceleration[i - 1] if i > 0 and i - 1 < len(acceleration) else None,
                        "turn_rate": turn_rates[i - 1] if i > 0 and i - 1 < len(turn_rates) else None
                    })
            
            # 問題のある区間を検出
            if valid_speeds and valid_turn_rates:
                speed_threshold = stats["speed"]["mean"] + 2 * stats["speed"]["std"]
                turn_rate_threshold = stats["turn_rate"]["abs_mean"] + 2 * stats["turn_rate"]["std"]
                
                problematic_segments = []
                for i, track in enumerate(tracks):
                    issues = []
                    if not math.isnan(track["speed_knots"]) and track["speed_knots"] > speed_threshold:
                        issues.append("異常な速度")
                    if i > 0 and not math.isnan(track["turn_rate"]) and abs(track["turn_rate"]) > turn_rate_threshold:
                        issues.append("急な方向転換")
                    if issues:
                        problematic_segments.append({
                            "segment_idx": i,
                            "issues": issues,
                            "track_data": track
                        })
                
                stats["problematic_segments"] = problematic_segments
                stats["problematic_segments_count"] = len(problematic_segments)
            
            return {
                "has_data": True,
                "track_stats": stats,
                "track_quality_score": track_quality_score,
                "track_length_m": sum(distances),
                "track_segments": tracks[:100]  # 最初の100セグメントのみ返す
            }
            
        except Exception as e:
            return {
                "has_data": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    def calculate_quality_scores(self) -> Dict[str, float]:
        """
        データ品質スコアを計算。
        
        総合スコアと各カテゴリ（完全性、正確性、一貫性）のスコアを0〜100の範囲で計算します。
        スコアは問題の重要度と数に基づいて決定されます。

        Returns
        -------
        Dict[str, float]
            各種品質スコア (total, completeness, accuracy, consistency)
        """
        # データポイントが少ない場合は計算しない
        if len(self.data) < 5:
            return {
                "completeness": 100.0,
                "accuracy": 100.0,
                "consistency": 100.0,
                "total": 100.0
            }
        
        # 問題の重要度に基づくペナルティ重み
        penalty_weights = {
            "error": 1.0,
            "warning": 0.5,
            "info": 0.1
        }
        
        # カテゴリ別のペナルティを初期化
        penalties = {
            "completeness": 0.0,
            "accuracy": 0.0,
            "consistency": 0.0
        }
        
        # 各検証結果に基づいてペナルティを計算
        for result in self.validation_results:
            if not result["is_valid"]:
                rule_name = result["rule_name"]
                severity = result["severity"]
                weight = penalty_weights.get(severity, 0.1)
                
                # カテゴリーの特定
                for category, rules in self.rule_categories.items():
                    if any(rule in rule_name for rule in rules):
                        # 検出された問題の深刻度と数に基づいてペナルティを加算
                        details = result["details"]
                        if "out_of_range_count" in details:
                            # 範囲外の値の割合に基づくペナルティ（最大-50）
                            penalty = min(50, (details["out_of_range_count"] / len(self.data) * 100))
                            penalties[category] += penalty * weight
                        elif "duplicate_count" in details:
                            # 重複の割合に基づくペナルティ（最大-50）
                            penalty = min(50, (details["duplicate_count"] / len(self.data) * 100))
                            penalties[category] += penalty * weight
                        elif "total_null_count" in details:
                            # 欠損値の割合に基づくペナルティ（最大-50）
                            total_fields = len(self.data) * len(details.get("columns", []))
                            if total_fields > 0:
                                penalty = min(50, (details["total_null_count"] / total_fields * 100))
                                penalties[category] += penalty * weight
                        elif "gap_count" in details:
                            # 時間ギャップの割合に基づくペナルティ（最大-50）
                            penalty = min(50, (details["gap_count"] / len(self.data) * 100))
                            penalties[category] += penalty * weight
                        elif "missing_columns" in details:
                            # 欠落カラムごとに-25ポイント
                            penalty = min(50, len(details["missing_columns"]) * 25)
                            penalties[category] += penalty * weight
                        elif "anomaly_count" in details:
                            # 異常値の割合に基づくペナルティ（最大-50）
                            penalty = min(50, (details["anomaly_count"] / len(self.data) * 100))
                            penalties[category] += penalty * weight
                        else:
                            # その他の問題には固定ペナルティ
                            penalties[category] += 10 * weight
        
        # 各カテゴリのスコアを計算
        scores = {
            "completeness": max(0, 100 - penalties["completeness"]),
            "accuracy": max(0, 100 - penalties["accuracy"]),
            "consistency": max(0, 100 - penalties["consistency"])
        }
        
        # 総合スコアは各カテゴリの加重平均
        # 完全性と一貫性は基本的なデータ品質に重要、正確性はやや高く重み付け
        weights = {"completeness": 0.3, "accuracy": 0.4, "consistency": 0.3}
        
        total_score = sum(scores[cat] * weights[cat] for cat in ["completeness", "accuracy", "consistency"])
        scores["total"] = total_score
        
        # スコアを小数点以下1桁に丸める
        return {key: round(value, 1) for key, value in scores.items()}
    
    def calculate_category_quality_scores(self) -> Dict[str, Dict[str, float]]:
        """
        カテゴリ別の品質スコアを計算。
        
        各品質カテゴリ（完全性、正確性、一貫性）の詳細なスコアと問題情報を計算します。
        カテゴリごとの細分化された問題タイプやその影響範囲も含みます。
        
        Returns
        -------
        Dict[str, Dict[str, float]]
            カテゴリ別の詳細スコア
        """
        category_scores = {}
        
        # 品質スコアを取得
        quality_scores = self.calculate_quality_scores()
        
        # 各カテゴリの詳細スコアを計算
        for category, rules in self.rule_categories.items():
            category_scores[category] = {
                "score": quality_scores[category],
                "issues": 0,
                "details": {},
                "impact_level": self._determine_impact_level(quality_scores[category])
            }
            
            # 各ルールの結果を集計
            for result in self.validation_results:
                rule_name = result["rule_name"]
                
                if any(rule in rule_name for rule in rules):
                    if not result["is_valid"]:
                        # 問題カウントを増加
                        category_scores[category]["issues"] += 1
                        
                        # 詳細情報を追加
                        details = result["details"]
                        rule_key = rule_name.replace(" ", "_").lower()
                        
                        if "out_of_range_count" in details:
                            category_scores[category]["details"][rule_key] = {
                                "count": details["out_of_range_count"],
                                "percentage": round(details["out_of_range_count"] / len(self.data) * 100, 2),
                                "severity": result["severity"],
                                "description": f"{details.get('column', '値')}の{details['out_of_range_count']}件が範囲外"
                            }
                        elif "duplicate_count" in details:
                            category_scores[category]["details"][rule_key] = {
                                "count": details["duplicate_count"],
                                "percentage": round(details["duplicate_count"] / len(self.data) * 100, 2),
                                "severity": result["severity"],
                                "description": f"{details['duplicate_count']}件の重複タイムスタンプ"
                            }
                        elif "total_null_count" in details:
                            total_fields = len(self.data) * len(details.get("columns", []))
                            percentage = 0 if total_fields == 0 else round(details["total_null_count"] / total_fields * 100, 2)
                            
                            category_scores[category]["details"][rule_key] = {
                                "count": details["total_null_count"],
                                "percentage": percentage,
                                "severity": result["severity"],
                                "affected_columns": list(details.get("null_counts", {}).keys()),
                                "description": f"{details['total_null_count']}件の欠損値"
                            }
                        elif "gap_count" in details:
                            category_scores[category]["details"][rule_key] = {
                                "gap_count": details["gap_count"],
                                "reverse_count": details.get("reverse_count", 0),
                                "max_gap": details.get("max_actual_gap", 0),
                                "percentage": round((details["gap_count"] + details.get("reverse_count", 0)) / len(self.data) * 100, 2),
                                "severity": result["severity"],
                                "description": f"{details['gap_count']}件のギャップ、{details.get('reverse_count', 0)}件の逆行"
                            }
                        elif "missing_columns" in details:
                            category_scores[category]["details"][rule_key] = {
                                "missing_columns": details["missing_columns"],
                                "count": len(details["missing_columns"]),
                                "severity": result["severity"],
                                "description": f"{len(details['missing_columns'])}個の必須カラムが欠落"
                            }
                        elif "anomaly_count" in details:
                            category_scores[category]["details"][rule_key] = {
                                "count": details["anomaly_count"],
                                "percentage": round(details["anomaly_count"] / len(self.data) * 100, 2),
                                "max_speed": details.get("max_calculated_speed", 0),
                                "severity": result["severity"],
                                "description": f"{details['anomaly_count']}件の空間的異常"
                            }
        
        return category_scores
    
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
            
            # 問題のあるすべてのレコードのインデックス
            all_problem_indices = self.problematic_indices["all"]
            
            # 時間範囲を決定
            min_time = valid_data["timestamp"].min()
            max_time = valid_data["timestamp"].max()
            time_range = max_time - min_time
            
            # 時間を12個の区間に分割
            hours_bins = 12
            time_step = time_range / hours_bins
            
            # 時間帯ごとのスコアを計算
            temporal_scores = []
            
            for i in range(hours_bins):
                bin_start = min_time + time_step * i
                bin_end = min_time + time_step * (i + 1)
                
                # 時間帯内のレコードを抽出
                bin_mask = (valid_data["timestamp"] >= bin_start) & (valid_data["timestamp"] < bin_end)
                bin_indices = valid_data.index[bin_mask].tolist()
                
                if bin_indices:
                    # 時間帯内の問題レコード数
                    problem_indices_in_bin = set(bin_indices).intersection(set(all_problem_indices))
                    problem_count = len(problem_indices_in_bin)
                    total_count = len(bin_indices)
                    
                    # 問題の割合に基づく品質スコア
                    problem_percentage = problem_count / total_count * 100 if total_count > 0 else 0
                    quality_score = max(0, 100 - problem_percentage)
                    
                    # 人間が読みやすい時間帯ラベルを作成
                    label = f"{bin_start.strftime('%H:%M')}-{bin_end.strftime('%H:%M')}"
                    
                    # 品質スコアを保存
                    temporal_scores.append({
                        "period": f"期間{i+1}",
                        "start_time": bin_start.isoformat(),
                        "end_time": bin_end.isoformat(),
                        "label": label,
                        "quality_score": quality_score,
                        "problem_count": problem_count,
                        "total_count": total_count,
                        "problem_percentage": problem_percentage,
                        "impact_level": self._determine_impact_level(quality_score)
                    })
            
            return temporal_scores
            
        except Exception as e:
            # エラーが発生した場合は空のリストを返す
            print(f"時間帯別の品質スコア計算中にエラー: {e}")
            return []
            
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
                        
                        # 品質スコアを保存
                        spatial_scores.append({
                            "grid_id": grid_id,
                            "center": (center_lat, center_lon),
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
            
            # 品質スコアでソート（問題の多いグリッドを先頭に）
            spatial_scores.sort(key=lambda x: x["quality_score"])
            
            return spatial_scores
            
        except Exception as e:
            # エラーが発生した場合は空のリストを返す
            print(f"空間的な品質スコア計算中にエラー: {e}")
            return []
            
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
                        
                        # 問題タイプごとのカウントを集計
                        problem_types = {}
                        for problem_type in ["missing_data", "out_of_range", "duplicates", 
                                          "spatial_anomalies", "temporal_anomalies"]:
                            type_indices = set(self.problematic_indices[problem_type])
                            count = len(type_indices.intersection(set(grid_indices)))
                            if count > 0:
                                problem_types[problem_type] = count
                        
                        # グリッド情報を保存
                        grid_center = ((lat_start + lat_end) / 2, (lon_start + lon_end) / 2)
                        
                        spatial_scores.append({
                            "grid_id": f"grid_{i}_{j}",
                            "lat_range": (lat_start, lat_end),
                            "lon_range": (lon_start, lon_end),
                            "center": grid_center,
                            "quality_score": quality_score,
                            "problem_count": problem_count,
                            "total_count": total_count,
                            "problem_percentage": problem_percentage,
                            "problem_types": problem_types,
                            "bounds": {
                                "min_lat": lat_start,
                                "max_lat": lat_end,
                                "min_lon": lon_start,
                                "max_lon": lon_end
                            },
                            "impact_level": self._determine_impact_level(quality_score)
                        })
            
            return spatial_scores
            
        except Exception as e:
            # エラーが発生した場合は空のリストを返す
            print(f"空間的な品質スコア計算中にエラー: {e}")
            return []
    
    def get_comprehensive_quality_metrics(self) -> Dict[str, Any]:
        """
        包括的な品質メトリクスを計算して取得
        
        カテゴリ別、時間的、空間的な品質メトリクスを含む包括的な分析結果を提供します。
        
        Returns
        -------
        Dict[str, Any]
            包括的な品質メトリクス
        """
        # 基本的な品質スコア
        basic_scores = self.quality_scores.copy()
        
        # カテゴリ別の詳細スコア
        category_details = self.category_scores.copy()
        
        # 問題分布
        distribution = self.problem_distribution
        
        # 時間的な拡張メトリクス
        temporal_metrics = self.get_extended_temporal_metrics()
        
        # 空間的な拡張メトリクス
        spatial_metrics = self.get_extended_spatial_metrics()
        
        # 問題のあるカラム
        problematic_columns = self.get_problematic_columns()
        
        # 重要度分布
        severity_distribution = self.get_problem_severity_distribution()
        
        # データ密度メトリクス
        density_metrics = self._calculate_data_density_metrics()

        # データ品質階層スコア
        hierarchy_scores = self.calculate_hierarchical_quality_scores()
        
        # 包括的な品質メトリクスを構築
        comprehensive_metrics = {
            "basic_scores": basic_scores,
            "category_details": category_details,
            "problem_distribution": distribution,
            "temporal_metrics": temporal_metrics,
            "spatial_metrics": spatial_metrics,
            "problematic_columns": problematic_columns,
            "severity_distribution": severity_distribution,
            "density_metrics": density_metrics,
            "hierarchy_scores": hierarchy_scores,
            "quality_summary": self.get_quality_summary(),
            "record_count": len(self.data),
            "problematic_record_count": len(self.problematic_indices["all"]),
            "generated_at": datetime.now().isoformat()
        }
        
        return comprehensive_metrics
        
    def calculate_hierarchical_quality_scores(self) -> Dict[str, Any]:
        """
        品質スコアを階層構造で計算
        
        組織的・統計的・構造的・意味的な観点から品質スコアを計算します。
        
        Returns
        -------
        Dict[str, Any]
            階層的な品質スコア
        """
        # 階層的な品質カテゴリ
        hierarchy = {
            "organizational": {
                "name": "組織的品質",
                "description": "データの完全性、可用性、準拠性などの組織的な品質",
                "score": 100.0,
                "subcategories": {
                    "completeness": {
                        "name": "完全性",
                        "score": self.quality_scores["completeness"],
                        "weight": 0.6
                    },
                    "compliance": {
                        "name": "準拠性",
                        "score": 100.0, # デフォルト値
                        "weight": 0.4
                    }
                }
            },
            "statistical": {
                "name": "統計的品質",
                "description": "データの統計的な一貫性、正確性、精度など",
                "score": 100.0,
                "subcategories": {
                    "accuracy": {
                        "name": "正確性",
                        "score": self.quality_scores["accuracy"],
                        "weight": 0.5
                    },
                    "precision": {
                        "name": "精度",
                        "score": self._calculate_precision_score(),
                        "weight": 0.5
                    }
                }
            },
            "structural": {
                "name": "構造的品質",
                "description": "データ構造の一貫性、整合性、均一性など",
                "score": 100.0,
                "subcategories": {
                    "consistency": {
                        "name": "一貫性",
                        "score": self.quality_scores["consistency"],
                        "weight": 0.6
                    },
                    "uniformity": {
                        "name": "均一性",
                        "score": self._calculate_uniformity_score(),
                        "weight": 0.4
                    }
                }
            },
            "semantic": {
                "name": "意味的品質",
                "description": "データの意味的な整合性、妥当性など",
                "score": 100.0,
                "subcategories": {
                    "validity": {
                        "name": "妥当性",
                        "score": self._calculate_validity_score(),
                        "weight": 0.5
                    },
                    "relevance": {
                        "name": "関連性",
                        "score": 100.0, # デフォルト値
                        "weight": 0.5
                    }
                }
            }
        }
        
        # 各階層のスコアを計算
        for category_key, category in hierarchy.items():
            weighted_sum = 0
            weight_sum = 0
            for subcat_key, subcat in category["subcategories"].items():
                weighted_sum += subcat["score"] * subcat["weight"]
                weight_sum += subcat["weight"]
            
            if weight_sum > 0:
                category["score"] = weighted_sum / weight_sum
        
        # 総合品質スコア
        overall_score = sum(cat["score"] for cat in hierarchy.values()) / len(hierarchy)
        
        return {
            "categories": hierarchy,
            "overall_score": overall_score
        }
    
    def _calculate_precision_score(self) -> float:
        """
        データ精度スコアの計算
        
        数値データの精度を評価します。
        
        Returns
        -------
        float
            精度スコア（0-100）
        """
        # 精度問題のカウント
        precision_issues = 0
        
        # 範囲外の値の問題を精度問題とみなす
        precision_issues += len(self.problematic_indices["out_of_range"])
        
        # 空間的な異常も精度問題に含める
        precision_issues += len(self.problematic_indices["spatial_anomalies"])
        
        # 精度スコアの計算（問題が多いほどスコアは低下）
        if len(self.data) > 0:
            issue_percentage = min(100, (precision_issues / len(self.data)) * 100)
            precision_score = max(0, 100 - issue_percentage)
        else:
            precision_score = 100.0
        
        return precision_score
    
    def _calculate_uniformity_score(self) -> float:
        """
        データ均一性スコアの計算
        
        データの分布や密度の均一性を評価します。
        
        Returns
        -------
        float
            均一性スコア（0-100）
        """
        uniformity_score = 100.0
        
        # 時間的な均一性を計算
        if "timestamp" in self.data.columns and len(self.data) > 1:
            try:
                # 有効なタイムスタンプを取得
                valid_times = self.data["timestamp"].dropna()
                
                if len(valid_times) >= 2:
                    # タイムスタンプをソート
                    sorted_times = sorted(valid_times)
                    
                    # 時間間隔を計算
                    intervals = [(sorted_times[i+1] - sorted_times[i]).total_seconds() 
                                for i in range(len(sorted_times) - 1)]
                    
                    if intervals:
                        # 変動係数（CV）を計算（標準偏差/平均）
                        mean_interval = sum(intervals) / len(intervals)
                        if mean_interval > 0:
                            std_dev = np.std(intervals)
                            cv = std_dev / mean_interval
                            
                            # CVが小さいほど均一性が高い（0が完全均一、1以上は非常に不均一）
                            temporal_uniformity = max(0, 100 - min(100, cv * 50))
                            
                            # 時間的均一性を全体のスコアに反映（50%のウェイト）
                            uniformity_score = uniformity_score * 0.5 + temporal_uniformity * 0.5
            except Exception:
                pass
        
        # 空間的な均一性を計算
        if "latitude" in self.data.columns and "longitude" in self.data.columns and len(self.data) > 1:
            try:
                density_metrics = self._calculate_data_density_metrics()
                spatial_distribution = density_metrics.get("spatial", {}).get("data_density", {})
                
                if "distribution_score" in spatial_distribution:
                    spatial_uniformity = spatial_distribution["distribution_score"]
                    
                    # 空間的均一性を全体のスコアに反映（既に計算されていればさらに50%のウェイト）
                    uniformity_score = uniformity_score * 0.5 + spatial_uniformity * 0.5
            except Exception:
                pass
        
        return uniformity_score
    
    def _calculate_validity_score(self) -> float:
        """
        データ妥当性スコアの計算
        
        データの意味的な妥当性を評価します。
        
        Returns
        -------
        float
            妥当性スコア（0-100）
        """
        # 妥当性問題のカウント
        validity_issues = 0
        
        # 時間的異常は妥当性問題とみなす
        validity_issues += len(self.problematic_indices["temporal_anomalies"])
        
        # 重複も妥当性問題に含める
        validity_issues += len(self.problematic_indices["duplicates"])
        
        # 妥当性スコアの計算（問題が多いほどスコアは低下）
        if len(self.data) > 0:
            issue_percentage = min(100, (validity_issues / len(self.data)) * 100)
            validity_score = max(0, 100 - issue_percentage)
        else:
            validity_score = 100.0
        
        return validity_score
    
    def get_data_quality_patterns(self) -> Dict[str, Any]:
        """
        データ品質パターンの検出
        
        一般的なデータ品質パターンを検出します。
        
        Returns
        -------
        Dict[str, Any]
            検出されたパターンとその説明
        """
        patterns = []
        
        # パターン1: 欠損値の集中
        if len(self.problematic_indices["missing_data"]) > 0:
            missing_indices = self.problematic_indices["missing_data"]
            
            # 欠損値の時間的な集中を検出
            if "timestamp" in self.data.columns:
                missing_rows = self.data.loc[missing_indices]
                if not missing_rows.empty and "timestamp" in missing_rows.columns:
                    timestamps = missing_rows["timestamp"].dropna()
                    
                    if len(timestamps) >= 3:  # 少なくとも3つの欠損値があること
                        # タイムスタンプをソート
                        sorted_times = sorted(timestamps)
                        
                        # 時間間隔を計算
                        intervals = [(sorted_times[i+1] - sorted_times[i]).total_seconds() 
                                   for i in range(len(sorted_times) - 1)]
                        
                        if intervals:
                            # 隣接する欠損値の平均間隔
                            avg_interval = sum(intervals) / len(intervals)
                            
                            # データ全体の平均間隔
                            all_timestamps = sorted(self.data["timestamp"].dropna())
                            all_intervals = [(all_timestamps[i+1] - all_timestamps[i]).total_seconds() 
                                           for i in range(len(all_timestamps) - 1)]
                            overall_avg_interval = sum(all_intervals) / len(all_intervals) if all_intervals else 0
                            
                            # 欠損値が時間的に集中しているかどうか
                            if overall_avg_interval > 0 and avg_interval < overall_avg_interval * 0.5:
                                patterns.append({
                                    "name": "時間的欠損値集中",
                                    "description": "欠損値が時間的に集中しています。特定の期間のデータ収集に問題があった可能性があります。",
                                    "severity": "warning",
                                    "details": {
                                        "missing_count": len(missing_indices),
                                        "avg_interval": avg_interval,
                                        "overall_avg_interval": overall_avg_interval,
                                        "time_range": [sorted_times[0].isoformat(), sorted_times[-1].isoformat()]
                                    }
                                })
        
        # パターン2: 空間的な異常値の集中
        if len(self.problematic_indices["spatial_anomalies"]) > 0:
            spatial_indices = self.problematic_indices["spatial_anomalies"]
            
            if "latitude" in self.data.columns and "longitude" in self.data.columns:
                anomaly_positions = self.data.loc[spatial_indices, ["latitude", "longitude"]].dropna()
                
                if len(anomaly_positions) >= 3:  # 少なくとも3つの異常値があること
                    # 異常値の空間的な集中度を計算
                    from sklearn.cluster import DBSCAN
                    import numpy as np
                    
                    try:
                        # 位置情報を配列に変換
                        points = anomaly_positions.values
                        
                        # DBSCANによるクラスタリング
                        clustering = DBSCAN(eps=0.001, min_samples=2).fit(points)
                        
                        # クラスタ数（-1はノイズ）
                        n_clusters = len(set(clustering.labels_)) - (1 if -1 in clustering.labels_ else 0)
                        
                        # クラスタに属する異常値の割合
                        clustered_ratio = np.sum(clustering.labels_ != -1) / len(points) if len(points) > 0 else 0
                        
                        if n_clusters > 0 and clustered_ratio > 0.5:
                            patterns.append({
                                "name": "空間的異常値集中",
                                "description": "位置の異常値が空間的に集中しています。特定のエリアでのデータ収集や処理に問題があるかもしれません。",
                                "severity": "warning",
                                "details": {
                                    "anomaly_count": len(spatial_indices),
                                    "cluster_count": n_clusters,
                                    "clustered_ratio": clustered_ratio
                                }
                            })
                    except Exception:
                        # DBSCANの実行に失敗した場合はスキップ
                        pass
        
        # パターン3: データの周期的変動
        if "timestamp" in self.data.columns and len(self.data) > 20:
            try:
                # 時系列データ
                ts_data = self.data.sort_values("timestamp")
                
                # 数値カラムを選択
                numeric_cols = ts_data.select_dtypes(include=np.number).columns
                
                for col in numeric_cols:
                    if col in ["latitude", "longitude"]:
                        continue
                    
                    # 自己相関の計算
                    from statsmodels.tsa.stattools import acf
                    
                    try:
                        # 欠損値を除去
                        valid_data = ts_data[col].dropna()
                        
                        if len(valid_data) > 10:
                            # 自己相関を計算（最大ラグは1/3に設定）
                            max_lag = min(10, len(valid_data) // 3)
                            acf_values = acf(valid_data, nlags=max_lag, fft=True)
                            
                            # 周期性を検出（0.5以上の相関）
                            significant_lags = [i for i, v in enumerate(acf_values) if i > 0 and abs(v) > 0.5]
                            
                            if significant_lags:
                                patterns.append({
                                    "name": "周期的データ変動",
                                    "description": f"カラム '{col}' に周期的な変動パターンが検出されました。",
                                    "severity": "info",
                                    "details": {
                                        "column": col,
                                        "significant_lags": significant_lags,
                                        "correlation_values": [float(acf_values[i]) for i in significant_lags]
                                    }
                                })
                    except Exception:
                        # 自己相関計算に失敗した場合はスキップ
                        pass
            except Exception:
                # 全体的な処理失敗時はスキップ
                pass
        
        # パターン4: 単調増加/減少傾向
        if len(self.data) > 10:
            try:
                # 数値カラムを選択
                numeric_cols = self.data.select_dtypes(include=np.number).columns
                
                for col in numeric_cols:
                    # 緯度経度はスキップ
                    if col in ["latitude", "longitude"]:
                        continue
                    
                    # 単調性の判定
                    valid_data = self.data[col].dropna()
                    
                    if len(valid_data) > 10:
                        # データの差分
                        diffs = np.diff(valid_data)
                        
                        # 増加と減少の比率
                        increase_ratio = np.sum(diffs > 0) / len(diffs) if len(diffs) > 0 else 0
                        decrease_ratio = np.sum(diffs < 0) / len(diffs) if len(diffs) > 0 else 0
                        
                        # 単調性の判定（90%以上が同一方向）
                        if increase_ratio > 0.9:
                            patterns.append({
                                "name": "単調増加",
                                "description": f"カラム '{col}' は単調増加の傾向があります。",
                                "severity": "info",
                                "details": {
                                    "column": col,
                                    "increase_ratio": increase_ratio,
                                    "start_value": float(valid_data.iloc[0]),
                                    "end_value": float(valid_data.iloc[-1])
                                }
                            })
                        elif decrease_ratio > 0.9:
                            patterns.append({
                                "name": "単調減少",
                                "description": f"カラム '{col}' は単調減少の傾向があります。",
                                "severity": "info",
                                "details": {
                                    "column": col,
                                    "decrease_ratio": decrease_ratio,
                                    "start_value": float(valid_data.iloc[0]),
                                    "end_value": float(valid_data.iloc[-1])
                                }
                            })
            except Exception:
                # 処理失敗時はスキップ
                pass
        
        return {
            "pattern_count": len(patterns),
            "patterns": patterns
        }
    
    def _calculate_data_density_metrics(self) -> Dict[str, Any]:
        """
        データ密度に関するメトリクスを計算
        
        データの時間的・空間的な密度、均一性などを計算します。
        
        Returns
        -------
        Dict[str, Any]
            データ密度メトリクス
        """
        metrics = {}
        
        # 時間的なデータ密度（存在する場合）
        if "timestamp" in self.data.columns:
            try:
                # 有効なタイムスタンプのみを抽出
                valid_timestamps = self.data["timestamp"].dropna()
                
                if len(valid_timestamps) >= 2:
                    # 時間範囲
                    time_range = (valid_timestamps.max() - valid_timestamps.min()).total_seconds()
                    
                    # ポイント間の時間間隔
                    sorted_times = sorted(valid_timestamps)
                    intervals = [(sorted_times[i+1] - sorted_times[i]).total_seconds() 
                               for i in range(len(sorted_times) - 1)]
                    
                    # 時間密度メトリクス
                    metrics["temporal"] = {
                        "has_data": True,
                        "time_range_seconds": time_range,
                        "point_count": len(valid_timestamps),
                        "points_per_minute": (len(valid_timestamps) / (time_range / 60)) if time_range > 0 else 0,
                        "points_per_hour": (len(valid_timestamps) / (time_range / 3600)) if time_range > 0 else 0,
                        "avg_interval_seconds": sum(intervals) / len(intervals) if intervals else 0,
                        "min_interval_seconds": min(intervals) if intervals else None,
                        "max_interval_seconds": max(intervals) if intervals else None,
                        "interval_std_seconds": np.std(intervals) if intervals else 0,
                        "uniformity_score": self._calculate_uniformity_score(intervals) if intervals else 0
                    }
                else:
                    metrics["temporal"] = {"has_data": False, "reason": "タイムスタンプデータが不足"}
            except Exception as e:
                metrics["temporal"] = {"has_data": False, "error": str(e)}
        else:
            metrics["temporal"] = {"has_data": False, "reason": "タイムスタンプカラムがありません"}
        
        # 空間的なデータ密度（存在する場合）
        if "latitude" in self.data.columns and "longitude" in self.data.columns:
            try:
                # 有効な位置データのみを抽出
                valid_positions = self.data.dropna(subset=["latitude", "longitude"])
                
                if len(valid_positions) >= 2:
                    # 位置の範囲
                    lat_range = valid_positions["latitude"].max() - valid_positions["latitude"].min()
                    lon_range = valid_positions["longitude"].max() - valid_positions["longitude"].min()
                    
                    # 空間密度メトリクス
                    metrics["spatial"] = {
                        "has_data": True,
                        "lat_range": lat_range,
                        "lon_range": lon_range,
                        "approx_area": lat_range * lon_range,
                        "point_count": len(valid_positions),
                        "points_per_sq_degree": len(valid_positions) / (lat_range * lon_range) if lat_range > 0 and lon_range > 0 else 0,
                        "spatial_distribution": self._calculate_spatial_distribution_metrics(valid_positions)
                    }
                else:
                    metrics["spatial"] = {"has_data": False, "reason": "位置データが不足"}
            except Exception as e:
                metrics["spatial"] = {"has_data": False, "error": str(e)}
        else:
            metrics["spatial"] = {"has_data": False, "reason": "位置カラムがありません"}
        
        return metrics
    
    def _calculate_uniformity_score(self, intervals: List[float]) -> float:
        """
        時間間隔の均一性スコアを計算
        
        Parameters
        ----------
        intervals : List[float]
            時間間隔のリスト（秒）
            
        Returns
        -------
        float
            均一性スコア（0-100）
        """
        if not intervals:
            return 0
        
        # 変動係数（標準偏差/平均）を使用して均一性を評価
        mean_interval = sum(intervals) / len(intervals)
        
        if mean_interval <= 0:
            return 0
        
        std_dev = np.std(intervals)
        cv = std_dev / mean_interval  # 変動係数
        
        # 変動係数が小さいほど均一性が高い
        # 0に近いほど均一、1以上は非常に不均一
        # 0-100のスコアに変換
        uniformity_score = 100 * (1 - min(1, cv / 2))
        
        return uniformity_score
    
    def _calculate_spatial_distribution_metrics(self, positions: pd.DataFrame) -> Dict[str, Any]:
        """
        空間的な分布メトリクスを計算
        
        Parameters
        ----------
        positions : pd.DataFrame
            位置データを含むデータフレーム
            
        Returns
        -------
        Dict[str, Any]
            空間分布メトリクス
        """
        try:
            # 分布の集中度を評価
            # グリッドを使用して空間的な均一性を評価
            lat_bins = 5
            lon_bins = 5
            
            lat_min = positions["latitude"].min()
            lat_max = positions["latitude"].max()
            lon_min = positions["longitude"].min()
            lon_max = positions["longitude"].max()
            
            if lat_max == lat_min:
                lat_max = lat_min + 0.001  # 小さな差を追加して0除算を防ぐ
            if lon_max == lon_min:
                lon_max = lon_min + 0.001
            
            lat_step = (lat_max - lat_min) / lat_bins
            lon_step = (lon_max - lon_min) / lon_bins
            
            # 各グリッドのカウント
            grid_counts = np.zeros((lat_bins, lon_bins))
            
            for _, row in positions.iterrows():
                lat_idx = min(lat_bins - 1, max(0, int((row["latitude"] - lat_min) / lat_step)))
                lon_idx = min(lon_bins - 1, max(0, int((row["longitude"] - lon_min) / lon_step)))
                grid_counts[lat_idx, lon_idx] += 1
            
            # グリッドの統計
            non_zero_grids = np.count_nonzero(grid_counts)
            total_grids = lat_bins * lon_bins
            occupied_ratio = non_zero_grids / total_grids if total_grids > 0 else 0
            
            # ポイント分布の不均一性（標準偏差/平均）
            non_zero_values = grid_counts[grid_counts > 0]
            if len(non_zero_values) > 0:
                mean_count = np.mean(non_zero_values)
                std_count = np.std(non_zero_values)
                cv = std_count / mean_count if mean_count > 0 else 0
                
                # 分布の均一性スコア（0-100）
                distribution_score = 100 * (1 - min(1, cv / 2))
            else:
                distribution_score = 0
            
            # 結果を返す
            return {
                "grid_dimensions": (lat_bins, lon_bins),
                "occupied_grids": non_zero_grids,
                "total_grids": total_grids,
                "occupied_ratio": occupied_ratio,
                "distribution_score": distribution_score
            }
        except Exception as e:
            return {
                "error": str(e),
                "distribution_score": 0
            }
    
    def get_quality_report(self) -> Dict[str, Any]:
        """
        データ品質のレポートを生成
        
        Returns
        -------
        Dict[str, Any]
            品質レポートデータ
        """
        # 基本的な品質情報
        basic_info = {
            "quality_scores": self.quality_scores,
            "category_scores": self.category_scores,
            "issue_counts": self.quality_summary["issue_counts"],
            "severity_counts": self.quality_summary["severity_counts"],
            "timestamp": datetime.now().isoformat()
        }
        
        # 問題の概要
        problem_summary = {
            "total_problems": sum(self.quality_summary["issue_counts"].values()),
            "problem_types": {
                "missing_data": len(self.problematic_indices["missing_data"]),
                "out_of_range": len(self.problematic_indices["out_of_range"]),
                "duplicates": len(self.problematic_indices["duplicates"]),
                "spatial_anomalies": len(self.problematic_indices["spatial_anomalies"]),
                "temporal_anomalies": len(self.problematic_indices["temporal_anomalies"])
            },
            "problematic_columns": self.get_problematic_columns()
        }
        
        # 分布情報
        distribution_info = {
            "temporal": self.temporal_metrics if hasattr(self, "temporal_metrics") else {},
            "spatial": self.spatial_metrics if hasattr(self, "spatial_metrics") else {},
            "problem_distribution": self.problem_distribution
        }
        
        # 修正推奨
        recommendations = self.get_fix_recommendations()
        
        # レポートを構築
        return {
            "basic_info": basic_info,
            "problem_summary": problem_summary,
            "distribution_info": distribution_info,
            "recommendations": recommendations,
            "report_id": f"quality_report_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "generated_at": datetime.now().isoformat()
        }
    
    @property
    def quality_summary(self) -> Dict[str, Any]:
        """
        品質サマリー情報のプロパティ
        
        Returns
        -------
        Dict[str, Any]
            品質サマリー情報
        """
        return self.get_quality_summary()

    @classmethod
    def create_sample_data(cls, rows=50, with_problems=True):
        """
        テスト用のサンプルデータを作成
        
        Parameters
        ----------
        rows : int, optional
            データ行数, by default 50
        with_problems : bool, optional
            問題を含めるかどうか, by default True
            
        Returns
        -------
        Tuple[pd.DataFrame, List[Dict[str, Any]]]
            サンプルデータと検証結果
        """
        # 基本的なデータを作成
        base_time = datetime(2023, 1, 1, 10, 0, 0)
        data = {
            'timestamp': [base_time + timedelta(seconds=i*10) for i in range(rows)],
            'latitude': [35.0 + i * 0.001 for i in range(rows)],
            'longitude': [135.0 + i * 0.001 for i in range(rows)],
            'speed': [5.0 + i * 0.2 for i in range(rows)],
            'heading': [45.0 + (i % 10) * 2 for i in range(rows)]
        }
        
        df = pd.DataFrame(data)
        
        # 問題を作成
        if with_problems:
            # 欠損値の作成
            df.loc[5, 'speed'] = None
            df.loc[15, 'latitude'] = None
            
            # 範囲外の値
            df.loc[10, 'speed'] = 50.0  # 通常ありえない速度
            
            # 重複タイムスタンプ
            df.loc[25, 'timestamp'] = df.loc[24, 'timestamp']
            
            # 空間的異常（急な位置変化）
            df.loc[30, 'latitude'] = 36.0
            
            # 時間的異常（逆行）
            df.loc[40, 'timestamp'] = df.loc[35, 'timestamp'] - timedelta(seconds=30)
        
        # 検証結果のサンプルを作成
        validation_results = []
        
        if with_problems:
            # 欠損値の検証結果
            validation_results.append({
                'rule_name': 'No Null Values Check',
                'is_valid': False,
                'severity': 'warning',
                'details': {
                    'columns': ['latitude', 'longitude', 'speed', 'heading'],
                    'total_null_count': 2,
                    'null_counts': {'latitude': 1, 'longitude': 0, 'speed': 1, 'heading': 0},
                    'null_indices': {'latitude': [15], 'speed': [5]}
                }
            })
            
            # 範囲外の値の検証結果
            validation_results.append({
                'rule_name': 'Value Range Check for speed',
                'is_valid': False,
                'severity': 'error',
                'details': {
                    'column': 'speed',
                    'min_value': 0.0,
                    'max_value': 20.0,
                    'actual_min': None,
                    'actual_max': 50.0,
                    'out_of_range_count': 1,
                    'out_of_range_indices': [10]
                }
            })
            
            # 重複タイムスタンプの検証結果
            validation_results.append({
                'rule_name': 'No Duplicate Timestamps',
                'is_valid': False,
                'severity': 'warning',
                'details': {
                    'duplicate_count': 2,
                    'duplicate_timestamps': [str(df.loc[24, 'timestamp'])],
                    'duplicate_indices': {str(df.loc[24, 'timestamp']): [24, 25]}
                }
            })
            
            # 空間的異常の検証結果
            validation_results.append({
                'rule_name': 'Spatial Consistency Check',
                'is_valid': False,
                'severity': 'warning',
                'details': {
                    'anomaly_count': 1,
                    'anomaly_indices': [30],
                    'max_calculated_speed': 100.0
                }
            })
            
            # 時間的異常の検証結果
            validation_results.append({
                'rule_name': 'Temporal Consistency Check',
                'is_valid': False,
                'severity': 'error',
                'details': {
                    'gap_count': 0,
                    'reverse_count': 1,
                    'reverse_indices': [40],
                    'gap_indices': []
                }
            })
        else:
            # 問題なしの検証結果
            validation_results.append({
                'rule_name': 'Required Columns Check',
                'is_valid': True,
                'severity': 'error',
                'details': {
                    'required_columns': ['timestamp', 'latitude', 'longitude'],
                    'missing_columns': [],
                    'found_columns': ['timestamp', 'latitude', 'longitude'],
                    'all_columns': ['timestamp', 'latitude', 'longitude', 'speed', 'heading']
                }
            })
            
            validation_results.append({
                'rule_name': 'No Null Values Check',
                'is_valid': True,
                'severity': 'warning',
                'details': {
                    'columns': ['latitude', 'longitude', 'speed', 'heading'],
                    'total_null_count': 0,
                    'null_counts': {'latitude': 0, 'longitude': 0, 'speed': 0, 'heading': 0},
                    'null_indices': {}
                }
            })
        
        return df, validation_results
        
    def get_record_issues(self) -> Dict[int, Dict[str, Any]]:
        """
        レコードごとの問題情報を取得
        
        Returns
        -------
        Dict[int, Dict[str, Any]]
            レコードごとの問題情報辞書
        """
        record_issues = {}
        
        # 問題カテゴリとその説明
        issue_categories = {
            "missing_data": "欠損値",
            "out_of_range": "範囲外の値",
            "duplicates": "重複タイムスタンプ",
            "spatial_anomalies": "空間的異常",
            "temporal_anomalies": "時間的異常"
        }
        
        # 各問題タイプで、問題のあるレコードに問題情報を追加
        for category, indices in self.problematic_indices.items():
            if category != "all":
                for idx in indices:
                    if idx not in record_issues:
                        record_issues[idx] = {
                            "issues": [],
                            "issue_count": 0,
                            "severity": "info",
                            "quality_score": self.get_record_quality_score(idx),
                            "fixable": True,  # 修正可能かどうかのフラグ
                            "auto_fixable": True,  # 自動修正可能かどうかのフラグ
                            "fix_options": []  # 修正オプションのリスト
                        }
                    
                    # 問題がまだ追加されていなければ追加
                    if issue_categories[category] not in record_issues[idx]["issues"]:
                        record_issues[idx]["issues"].append(issue_categories[category])
                        record_issues[idx]["issue_count"] += 1
                        
                        # 問題タイプに応じた修正オプションを追加
                        if category == "missing_data":
                            record_issues[idx]["fix_options"].extend([
                                {"id": "interpolate", "name": "値を補間", "type": "missing_data", "description": "前後の値から欠損値を補間します", "difficulty": "easy"},
                                {"id": "ffill", "name": "前の値で埋める", "type": "missing_data", "description": "直前の値で欠損値を埋めます", "difficulty": "easy"},
                                {"id": "bfill", "name": "後の値で埋める", "type": "missing_data", "description": "直後の値で欠損値を埋めます", "difficulty": "easy"},
                                {"id": "remove", "name": "行を削除", "type": "missing_data", "description": "欠損値を含む行を削除します", "difficulty": "medium"}
                            ])
                        elif category == "out_of_range":
                            record_issues[idx]["fix_options"].extend([
                                {"id": "clip", "name": "値を制限", "type": "out_of_range", "description": "範囲外の値を最小値または最大値に制限します", "difficulty": "easy"},
                                {"id": "replace_null", "name": "NULLに置換", "type": "out_of_range", "description": "範囲外の値をNULLに置き換えます", "difficulty": "easy"},
                                {"id": "remove", "name": "行を削除", "type": "out_of_range", "description": "範囲外の値を含む行を削除します", "difficulty": "medium"}
                            ])
                        elif category == "duplicates":
                            record_issues[idx]["fix_options"].extend([
                                {"id": "offset", "name": "時間をずらす", "type": "duplicates", "description": "重複するタイムスタンプを少しずつずらします", "difficulty": "easy"},
                                {"id": "keep_first", "name": "最初を保持", "type": "duplicates", "description": "重複する最初のレコードのみを保持します", "difficulty": "easy"},
                                {"id": "remove", "name": "重複行を削除", "type": "duplicates", "description": "重複するすべての行を削除します", "difficulty": "medium"}
                            ])
                        elif category == "spatial_anomalies":
                            record_issues[idx]["fix_options"].extend([
                                {"id": "interpolate", "name": "位置を補間", "type": "spatial_anomalies", "description": "異常な位置を前後のポイントから補間します", "difficulty": "medium"},
                                {"id": "smooth", "name": "位置を平滑化", "type": "spatial_anomalies", "description": "移動平均で位置を平滑化します", "difficulty": "medium"},
                                {"id": "remove", "name": "ポイントを削除", "type": "spatial_anomalies", "description": "空間的に異常なポイントを削除します", "difficulty": "medium"}
                            ])
                        elif category == "temporal_anomalies":
                            record_issues[idx]["fix_options"].extend([
                                {"id": "fix_reverse", "name": "逆行を修正", "type": "temporal_anomalies", "description": "タイムスタンプが逆行しているポイントを修正します", "difficulty": "medium"},
                                {"id": "mark_gaps", "name": "ギャップをマーク", "type": "temporal_anomalies", "description": "大きな時間ギャップをメタデータにマークします", "difficulty": "easy"},
                                {"id": "remove", "name": "ポイントを削除", "type": "temporal_anomalies", "description": "時間的に異常なポイントを削除します", "difficulty": "medium"}
                            ])
        
        # 検証結果から問題の詳細と重要度を設定
        for result in self.validation_results:
            if not result["is_valid"]:
                severity = result["severity"]
                details = result["details"]
                rule_name = result["rule_name"]
                
                # 対象のインデックスと追加情報を抽出
                target_indices = []
                rule_info = {}
                
                if "null_indices" in details:
                    for col, indices in details["null_indices"].items():
                        target_indices.extend(indices)
                        # カラム情報を追加
                        for idx in indices:
                            if idx not in rule_info:
                                rule_info[idx] = {}
                            rule_info[idx]["column"] = col
                
                if "out_of_range_indices" in details:
                    target_indices.extend(details["out_of_range_indices"])
                    # 範囲情報を追加
                    for idx in details["out_of_range_indices"]:
                        if idx not in rule_info:
                            rule_info[idx] = {}
                        rule_info[idx]["column"] = details.get("column", "")
                        rule_info[idx]["min_value"] = details.get("min_value")
                        rule_info[idx]["max_value"] = details.get("max_value")
                        rule_info[idx]["actual_value"] = self.data.iloc[idx][details.get("column", "")] if idx < len(self.data) else None
                
                if "duplicate_indices" in details:
                    for ts, indices in details["duplicate_indices"].items():
                        target_indices.extend(indices)
                        # タイムスタンプ情報を追加
                        for idx in indices:
                            if idx not in rule_info:
                                rule_info[idx] = {}
                            rule_info[idx]["duplicate_timestamp"] = ts
                            rule_info[idx]["duplicate_with"] = [i for i in indices if i != idx]
                
                if "anomaly_indices" in details:
                    target_indices.extend(details["anomaly_indices"])
                    # 異常詳細を追加
                    if "anomaly_details" in details:
                        anomaly_map = {}
                        for anomaly in details["anomaly_details"]:
                            anomaly_map[anomaly.get("original_index", -1)] = anomaly
                        
                        for idx in details["anomaly_indices"]:
                            if idx not in rule_info:
                                rule_info[idx] = {}
                            if idx in anomaly_map:
                                rule_info[idx]["anomaly_detail"] = anomaly_map[idx]
                
                if "gap_indices" in details or "reverse_indices" in details:
                    gap_indices = details.get("gap_indices", [])
                    reverse_indices = details.get("reverse_indices", [])
                    target_indices.extend(gap_indices + reverse_indices)
                    
                    # ギャップ詳細を追加
                    if "gap_details" in details:
                        gap_map = {}
                        for gap in details["gap_details"]:
                            gap_map[gap.get("original_index", -1)] = gap
                        
                        for idx in gap_indices:
                            if idx not in rule_info:
                                rule_info[idx] = {}
                            if idx in gap_map:
                                rule_info[idx]["gap_detail"] = gap_map[idx]
                    
                    # 逆行詳細を追加
                    if "reverse_details" in details:
                        reverse_map = {}
                        for reverse in details["reverse_details"]:
                            reverse_map[reverse.get("original_index", -1)] = reverse
                        
                        for idx in reverse_indices:
                            if idx not in rule_info:
                                rule_info[idx] = {}
                            if idx in reverse_map:
                                rule_info[idx]["reverse_detail"] = reverse_map[idx]
                
                # 対象インデックスの重要度と追加情報を更新
                for idx in target_indices:
                    if idx in record_issues:
                        # 最も重要な重要度を設定（error > warning > info）
                        if severity == "error" or record_issues[idx]["severity"] == "error":
                            record_issues[idx]["severity"] = "error"
                        elif severity == "warning" or record_issues[idx]["severity"] == "warning":
                            record_issues[idx]["severity"] = "warning"
                        
                        # ルール情報を追加
                        if "problem_details" not in record_issues[idx]:
                            record_issues[idx]["problem_details"] = {}
                        
                        rule_key = rule_name.replace(" ", "_").lower()
                        record_issues[idx]["problem_details"][rule_key] = {
                            "rule_name": rule_name,
                            "severity": severity
                        }
                        
                        # 追加情報をマージ
                        if idx in rule_info:
                            record_issues[idx]["problem_details"][rule_key].update(rule_info[idx])
        
        # 各レコードに位置情報と属性を追加
        for idx, issue_data in record_issues.items():
            if idx < len(self.data):
                row = self.data.iloc[idx]
                # 基本情報
                issue_data["timestamp"] = row.get("timestamp", None)
                issue_data["latitude"] = row.get("latitude", None)
                issue_data["longitude"] = row.get("longitude", None)
                
                # その他の主要カラムの値も保存
                issue_data["values"] = {}
                for col in self.data.columns[:10]:  # 最初の10カラムまで
                    issue_data["values"][col] = row.get(col, None)
                
                # 問題の詳細説明を生成
                issue_data["description"] = f"{issue_data['issue_count']}個の問題: " + ", ".join(issue_data["issues"])
        
        return record_issues
