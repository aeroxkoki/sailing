"""
sailing_data_processor.validation.visualization_integration

データ検証結果の視覚化クラスの統合モジュール
"""

from typing import Dict, List, Any, Optional, Tuple, Set
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

from sailing_data_processor.data_model.container import GPSDataContainer
from sailing_data_processor.validation.data_validator import DataValidator
from sailing_data_processor.validation.quality_metrics import QualityMetricsCalculator
from sailing_data_processor.validation.quality_metrics_integration import EnhancedQualityMetricsCalculator
from sailing_data_processor.validation.visualization import ValidationVisualizer
from sailing_data_processor.validation.visualization_improvements import EnhancedValidationVisualization


class EnhancedValidationVisualizer(ValidationVisualizer):
    """
    拡張されたデータ検証結果の視覚化クラス

    既存のValidationVisualizerクラスを継承し、新しい視覚化機能を追加します。

    Parameters
    ----------
    quality_metrics : QualityMetricsCalculator
        データ品質メトリクス計算クラス
    data : pd.DataFrame
        検証されたデータフレーム
    """

    def __init__(self, quality_metrics: QualityMetricsCalculator, data: pd.DataFrame):
        """
        初期化

        Parameters
        ----------
        quality_metrics : QualityMetricsCalculator
            データ品質メトリクス計算クラス
        data : pd.DataFrame
            検証されたデータフレーム
        """
        # 親クラスの初期化
        super().__init__(quality_metrics, data)

        # quality_metricsが通常のQualityMetricsCalculatorであれば、EnhancedQualityMetricsCalculatorに変換
        if not isinstance(quality_metrics, EnhancedQualityMetricsCalculator):
            self.enhanced_metrics = EnhancedQualityMetricsCalculator(
                quality_metrics.validation_results, data)
        else:
            self.enhanced_metrics = quality_metrics

        # 拡張視覚化クラスのインスタンス作成
        self.enhanced_visualization = EnhancedValidationVisualization(
            self.enhanced_metrics, data)

    def generate_quality_score_visualization(self) -> Tuple[go.Figure, go.Figure]:
        """
        品質スコアのゲージチャートとカテゴリ別バーチャートを生成。
        
        品質スコアの視覚的表現として、総合スコアを円形ゲージで、
        カテゴリ別スコア（完全性、正確性、一貫性）を棒グラフで表示します。
        
        Returns
        -------
        Tuple[go.Figure, go.Figure]
            ゲージチャートとバーチャート
        """
        # 拡張機能による実装を使用
        return self.enhanced_metrics.generate_quality_score_visualization()

    def generate_spatial_quality_map(self) -> go.Figure:
        """
        空間的な品質分布のマップを生成。
        
        GPSデータの空間的な品質分布を地図上に視覚化します。
        各エリアは品質スコアによって色分けされ、品質の空間的な変動を把握できます。
        
        Returns
        -------
        go.Figure
            品質マップの図
        """
        # 拡張機能による実装を使用
        return self.enhanced_metrics.generate_spatial_quality_map()

    def generate_temporal_quality_chart(self) -> go.Figure:
        """
        時間帯別の品質分布チャートを生成。
        
        時間帯ごとの品質スコアをグラフ化し、時間的な品質の変動を視覚化します。
        各時間帯のデータ量と問題発生率も表示します。
        
        Returns
        -------
        go.Figure
            時間帯別品質チャート
        """
        # 拡張機能による実装を使用
        return self.enhanced_metrics.generate_temporal_quality_chart()

    def generate_quality_score_dashboard(self) -> Dict[str, go.Figure]:
        """
        品質スコアダッシュボードを生成

        各種品質スコアの視覚的表現を含むダッシュボード要素を生成します。

        Returns
        -------
        Dict[str, go.Figure]
            ダッシュボード要素の辞書
        """
        return self.enhanced_visualization.generate_quality_score_dashboard()

    def generate_problem_distribution_visualization(self) -> Dict[str, go.Figure]:
        """
        問題分布の視覚化を生成

        問題の時間的・空間的分布を視覚化します。

        Returns
        -------
        Dict[str, go.Figure]
            問題分布の視覚化の辞書
        """
        return self.enhanced_visualization.generate_problem_distribution_visualization()

    def generate_quality_score_card(self) -> Dict[str, Any]:
        """
        品質スコアのカード形式表示データを生成

        Returns
        -------
        Dict[str, Any]
            カード表示用のデータ
        """
        return self.enhanced_visualization.generate_quality_score_card()


# 簡単なファクトリ関数を提供
def create_validation_visualizer(validator: DataValidator, container: GPSDataContainer, enhanced: bool = True) -> ValidationVisualizer:
    """
    ValidationVisualizerの適切なインスタンスを作成する

    Parameters
    ----------
    validator : DataValidator
        データ検証器
    container : GPSDataContainer
        GPSデータコンテナ
    enhanced : bool, optional
        拡張機能を使用するかどうか, by default True

    Returns
    -------
    ValidationVisualizer
        通常または拡張されたValidationVisualizerインスタンス
    """
    if enhanced:
        # 検証が実行されていない場合は実行
        if not validator.validation_results:
            validator.validate(container)
            
        # 拡張されたクラスを使用
        metrics = EnhancedQualityMetricsCalculator(validator.validation_results, container.data)
        return EnhancedValidationVisualizer(metrics, container.data)
    else:
        # 既存のクラスを使用
        return ValidationVisualizer(validator, container)
