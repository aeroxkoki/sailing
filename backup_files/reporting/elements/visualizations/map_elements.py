# -*- coding: utf-8 -*-
"""
マップ要素モジュール - 航跡、ヒートマップ、戦略ポイント、風場を地図上に表示するための要素
"""

# このファイルは各マップ要素クラスを個別のファイルに分割しました
# 後方互換性のために、このファイルでは新しい場所からクラスをインポートして提供します

from sailing_data_processor.reporting.elements.visualizations.map.track_map import TrackMapElement
from sailing_data_processor.reporting.elements.visualizations.map.heat_map import HeatMapLayerElement
from sailing_data_processor.reporting.elements.visualizations.map.strategy_points import StrategyPointLayerElement
from sailing_data_processor.reporting.elements.visualizations.map.wind_field import WindFieldElement

# エクスポートするクラスのリスト
__all__ = [
    'TrackMapElement',
    'HeatMapLayerElement',
    'StrategyPointLayerElement',
    'WindFieldElement'
]
