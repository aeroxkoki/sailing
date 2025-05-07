# -*- coding: utf-8 -*-
"""
ValidationVisualization クラス
既存のValidationVisualizationクラスとの互換性のためのラッパークラス
"""

from typing import Dict, List, Any, Tuple
import pandas as pd
import plotly.graph_objects as go
from sailing_data_processor.data_model.container import GPSDataContainer
from sailing_data_processor.validation.data_validator import DataValidator
from sailing_data_processor.validation.quality_metrics import QualityMetricsCalculator
from sailing_data_processor.validation.visualization_modules.visualizer_part1 import ValidationVisualizer
# 循環インポートを避けるため、遅延インポート（必要な時だけインポート）
# from sailing_data_processor.validation.visualization_modules.validation_dashboard import ValidationDashboard

class ValidationVisualization:
    """
    既存のValidationVisualizationクラスとの互換性のためのラッパークラス
    
    Parameters
    ----------
    validator : DataValidator
        データ検証器
    container : GPSDataContainer
        GPSデータコンテナ
    """
    
    def __init__(self, validator: DataValidator, container: GPSDataContainer):
        """
        初期化
        
        Parameters
        ----------
        validator : DataValidator
            データ検証器
        container : GPSDataContainer
            GPSデータコンテナ
        """
        self.validator = validator
        self.container = container
        self.data = container.data
        
        # 検証が実行されていない場合は実行
        if not validator.validation_results:
            validator.validate(container)
        
        self.validation_results = validator.validation_results
        
        # 新しいクラスを使用
        self.metrics_calculator = QualityMetricsCalculator(validator.validation_results, container.data)
        self.visualizer = ValidationVisualizer(self.metrics_calculator, container.data)
        
        # 循環インポートを避けるために、ここでダッシュボードをインポートして初期化
        try:
            from sailing_data_processor.validation.visualization_modules.validation_dashboard import ValidationDashboard
            self.dashboard = ValidationDashboard(validator.validation_results, container.data)
        except ImportError:
            self.dashboard = None
        
        # データ品質スコアの計算
        self.quality_score = self.metrics_calculator.quality_scores
        
        # 問題のあるレコードのインデックスを収集
        self.problematic_indices = self.metrics_calculator.problematic_indices
        
        # レコードごとの問題集計を計算（互換性のため）
        self.record_issues = self._calculate_record_issues()
        
        # データクオリティサマリー
        self.quality_summary = self.metrics_calculator.get_quality_summary()
    
    def _calculate_record_issues(self) -> Dict[int, Dict[str, Any]]:
        """
        レコードごとの問題集計を計算（互換性のためのメソッド）
        
        Returns
        -------
        Dict[int, Dict[str, Any]]
            インデックスごとの問題詳細
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
                            "severity": "info"
                        }
                    
                    # 問題がまだ追加されていなければ追加
                    if issue_categories[category] not in record_issues[idx]["issues"]:
                        record_issues[idx]["issues"].append(issue_categories[category])
                        record_issues[idx]["issue_count"] += 1
        
        # 問題の重要度を設定
        for result in self.validation_results:
            if not result["is_valid"]:
                severity = result["severity"]
                details = result["details"]
                
                # 重要度を設定する対象のインデックスを抽出
                target_indices = []
                
                if "null_indices" in details:
                    for col, indices in details["null_indices"].items():
                        target_indices.extend(indices)
                
                if "out_of_range_indices" in details:
                    target_indices.extend(details["out_of_range_indices"])
                
                if "duplicate_indices" in details:
                    for ts, indices in details["duplicate_indices"].items():
                        target_indices.extend(indices)
                
                if "anomaly_indices" in details:
                    target_indices.extend(details["anomaly_indices"])
                
                if "gap_indices" in details:
                    target_indices.extend(details["gap_indices"])
                
                if "reverse_indices" in details:
                    target_indices.extend(details["reverse_indices"])
                
                # 対象インデックスの重要度を更新
                for idx in target_indices:
                    if idx in record_issues:
                        # 最も重要な重要度を設定（error > warning > info）
                        if severity == "error" or record_issues[idx]["severity"] == "error":
                            record_issues[idx]["severity"] = "error"
                        elif severity == "warning" or record_issues[idx]["severity"] == "warning":
                            record_issues[idx]["severity"] = "warning"
        
        # 各レコードに具体的な問題情報を追加
        for idx, issue_data in record_issues.items():
            # データの一部を保存
            if idx < len(self.data):
                row = self.data.iloc[idx]
                issue_data["timestamp"] = row.get("timestamp", None)
                issue_data["latitude"] = row.get("latitude", None)
                issue_data["longitude"] = row.get("longitude", None)
                
                # 問題の詳細説明を生成
                issue_data["description"] = f"{issue_data['issue_count']}個の問題: " + ", ".join(issue_data["issues"])
        
        return record_issues
    
    # 元のクラスのメソッドを新しいクラスのメソッドに委譲
    def get_quality_score_visualization(self) -> Tuple[go.Figure, go.Figure]:
        """
        データ品質スコアの視覚化（互換性のためのメソッド）
        """
        return self.visualizer.generate_quality_score_visualization()
    
    def get_issues_summary_visualization(self) -> Tuple[go.Figure, go.Figure, pd.DataFrame]:
        """
        検出された問題の概要視覚化（互換性のためのメソッド）
        """
        # 問題の重要度別カウント
        severity_counts = self.metrics_calculator.get_problem_severity_distribution()
        
        # 重要度別の棒グラフ
        severity_fig = go.Figure()
        colors = {"error": "red", "warning": "orange", "info": "blue"}
        
        for severity, count in severity_counts.items():
            if count > 0:
                severity_fig.add_trace(go.Bar(
                    x=[severity.capitalize()],
                    y=[count],
                    name=severity.capitalize(),
                    marker_color=colors[severity]
                ))
        
        severity_fig.update_layout(
            title="重要度別の問題数",
            xaxis_title="重要度",
            yaxis_title="問題数",
            height=350,
            margin=dict(t=50, b=50, l=30, r=30)
        )
        
        # 問題タイプ別の棒グラフ
        type_fig = self.visualizer.generate_problem_distribution_chart()
        
        # サマリーテーブル
        summary_data = {
            "カテゴリ": ["総レコード数", "問題のあるレコード数", "問題のあるレコード割合",
                     "エラー", "警告", "情報"],
            "値": [
                len(self.data),
                len(self.problematic_indices["all"]),
                f"{(len(self.problematic_indices['all']) / len(self.data) * 100):.2f}%" if len(self.data) > 0 else "0.00%",
                severity_counts["error"],
                severity_counts["warning"],
                severity_counts["info"]
            ]
        }
        
        summary_df = pd.DataFrame(summary_data)
        
        return severity_fig, type_fig, summary_df
    
    def get_spatial_issues_map(self) -> go.Figure:
        """
        空間的な問題の地図表示（互換性のためのメソッド）
        """
        return self.visualizer.generate_problem_heatmap()
    
    def get_temporal_issues_visualization(self) -> go.Figure:
        """
        時間的な問題の視覚化（互換性のためのメソッド）
        """
        return self.visualizer.generate_timeline_chart()
