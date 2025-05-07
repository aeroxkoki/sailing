# -*- coding: utf-8 -*-
"""
検証ダッシュボードクラス
"""
from typing import Dict, List, Any
import pandas as pd
import plotly.graph_objects as go
from sailing_data_processor.validation.quality_metrics import QualityMetricsCalculator
from sailing_data_processor.validation.visualization_modules.visualizer_part1 import ValidationVisualizer

class ValidationDashboard:
    """
    検証ダッシュボードクラス
    
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
        
        # メトリクス計算とビジュアライザーを初期化
        self.metrics_calculator = QualityMetricsCalculator(validation_results, data)
        self.visualizer = ValidationVisualizer(self.metrics_calculator, data)
        
        # フィルタリング状態を初期化
        self.active_filters = {
            "problem_types": ["missing_data", "out_of_range", "duplicates", 
                           "spatial_anomalies", "temporal_anomalies"],
            "severity": ["error", "warning", "info"],
            "time_range": None,
            "position": None
        }

    def render_overview_section(self) -> Dict[str, Any]:
        """
        概要セクションのレンダリング
        
        データ品質の概要情報を含むセクションをレンダリングします。
        品質スコア、カテゴリ別スコア、問題サマリーなどが含まれます。
        
        Returns
        -------
        Dict[str, Any]
            概要セクションの内容
        """
        # 品質サマリーを取得
        quality_summary = self.metrics_calculator.get_quality_summary()
        
        # 品質スコアチャートの生成
        quality_score_chart = self.visualizer.generate_quality_score_chart()
        
        # カテゴリ別スコアチャートの生成
        category_scores_chart = self.visualizer.generate_category_scores_chart()
        
        # 問題分布チャートの生成
        distribution_data = self.visualizer.generate_distribution_charts()
        
        # 問題サマリー情報
        problem_summary = {
            "total_issues": quality_summary.get("total_issues", 0),
            "issue_types": {
                "missing_data": quality_summary.get("issue_counts", {}).get("missing_data", 0),
                "out_of_range": quality_summary.get("issue_counts", {}).get("out_of_range", 0),
                "duplicates": quality_summary.get("issue_counts", {}).get("duplicates", 0),
                "spatial_anomalies": quality_summary.get("issue_counts", {}).get("spatial_anomalies", 0),
                "temporal_anomalies": quality_summary.get("issue_counts", {}).get("temporal_anomalies", 0)
            },
            "impact_level": quality_summary.get("impact_level", "low")
        }
        
        return {
            "quality_summary": quality_summary,
            "charts": {
                "quality_score": quality_score_chart,
                "category_scores": category_scores_chart,
                "problem_distribution": distribution_data
            },
            "problem_summary": problem_summary
        }
    
    def render_details_section(self) -> Dict[str, Any]:
        """
        詳細セクションのレンダリング
        
        データ品質の詳細情報を含むセクションをレンダリングします。
        問題レコードのリスト、空間的・時間的分布、詳細レポートなどが含まれます。
        
        Returns
        -------
        Dict[str, Any]
            詳細セクションの内容
        """
        try:
            # 問題レコードの取得
            record_issues = self.metrics_calculator.get_record_issues()
            
            # 問題レコードをDataFrameに変換
            problem_records = []
            for idx, issue in record_issues.items():
                if isinstance(idx, int) and isinstance(issue, dict):
                    record = self.data.iloc[idx].to_dict() if idx < len(self.data) else {}
                    record["index"] = idx
                    record["issue_type"] = ", ".join(issue.get("issues", []))
                    record["severity"] = issue.get("severity", "")
                    record["quality_score"] = issue.get("quality_score", {}).get("total", 0)
                    problem_records.append(record)
            
            problem_records_df = pd.DataFrame(problem_records) if problem_records else pd.DataFrame()
            
            # 詳細チャートの生成
            try:
                spatial_quality_map = self.visualizer.generate_spatial_quality_map()
            except Exception as e:
                print(f"Error generating spatial quality map: {e}")
                # エラー時はダミーのマップを返す
                spatial_quality_map = go.Figure()
                spatial_quality_map.update_layout(title="空間品質マップ（エラーのため表示できません）")
            
            try:
                temporal_quality_chart = self.visualizer.generate_temporal_quality_chart()
            except Exception as e:
                print(f"Error generating temporal quality chart: {e}")
                # エラー時はダミーのチャートを返す
                temporal_quality_chart = go.Figure()
                temporal_quality_chart.update_layout(title="時間品質チャート（エラーのため表示できません）")
            
            # 詳細レポートの生成
            detailed_report = self.metrics_calculator.get_quality_report()
            
            return {
                "charts": {
                    "spatial_quality": spatial_quality_map,
                    "temporal_quality": temporal_quality_chart
                },
                "problem_records_df": problem_records_df,
                "detailed_report": detailed_report
            }
        except Exception as e:
            # 最終的なフォールバック - エラーが発生した場合も最低限の情報を返す
            print(f"Error rendering details section: {e}")
            return {
                "charts": {},
                "problem_records_df": pd.DataFrame(),
                "detailed_report": {"error": f"レポート生成エラー: {str(e)}"}
            }
    
    def render_action_section(self) -> Dict[str, Any]:
        """アクションセクションのレンダリング"""
        return {}
    
    def handle_filter_change(self, new_filters: Dict[str, Any]) -> List[int]:
        """フィルター変更の処理"""
        return []
    
    def _filter_problem_indices(self) -> Dict[str, List[int]]:
        """フィルターに基づいて問題インデックスをフィルタリング"""
        return {}
    
    def get_filtered_visualizations(self) -> Dict:
        """フィルター適用後の視覚化を取得"""
        return {}
