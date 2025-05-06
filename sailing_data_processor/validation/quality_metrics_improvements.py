# -*- coding: utf-8 -*-
"""
Module for data quality metrics improvements.
This module provides functions for quality metrics calculation and visualization.
"""

from typing import Dict, List, Any, Optional, Tuple, Set
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

# Core functionality imports
from sailing_data_processor.validation.quality_metrics_improvements_core import QualityMetricsCalculatorExtension
from sailing_data_processor.validation.quality_metrics_visualization import QualityMetricsVisualization
from sailing_data_processor.validation.quality_metrics_temporal import QualityMetricsTemporal

# Create a combined class for backward compatibility
class QualityMetricsCalculator(QualityMetricsCalculatorExtension):
    """
    データ品質メトリクスの計算クラス
    
    データ検証結果に基づいてデータ品質を評価し、様々なメトリクスを計算します。
    また、品質スコアの視覚化機能も提供します。
    """
    
    def __init__(self, validation_results=None, data=None):
        """
        初期化
        
        Parameters
        ----------
        validation_results : List[Dict[str, Any]], optional
            DataValidatorから得られた検証結果
        data : pd.DataFrame, optional
            検証されたデータフレーム
        """
        # 親クラスの初期化
        super().__init__(validation_results, data)
        
        # 視覚化クラスの初期化
        self.visualizer = QualityMetricsVisualization(self)
        self.temporal_analyzer = QualityMetricsTemporal(self)
        
    def generate_quality_score_visualization(self) -> Tuple:
        """
        品質スコアのゲージチャートとカテゴリ別バーチャートを生成
        
        Returns
        -------
        Tuple
            ゲージチャートとバーチャート
        """
        return self.visualizer.generate_quality_score_visualization()
    
    def generate_spatial_quality_map(self):
        """
        空間的な品質分布のマップを生成
        
        Returns
        -------
        Object
            品質マップの図
        """
        return self.visualizer.generate_spatial_quality_map()
        
    def generate_temporal_quality_chart(self):
        """
        時間帯別の品質分布チャートを生成
        
        Returns
        -------
        Object
            時間帯別品質チャート
        """
        return self.temporal_analyzer.generate_temporal_quality_chart()
