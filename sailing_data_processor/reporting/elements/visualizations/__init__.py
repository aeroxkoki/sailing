# -*- coding: utf-8 -*-
"""
Module for data connector between map layers and data sources.
This module provides functions for binding and data transformation between layers and data sources.
"""

from sailing_data_processor.reporting.elements.visualizations.base_chart import BaseChartElement
from sailing_data_processor.reporting.elements.visualizations.chart_data import ChartData
from sailing_data_processor.reporting.elements.visualizations.chart_renderer import (
    BaseChartRenderer, 
    PlotlyRenderer, 
    ChartJSRenderer, 
    MatplotlibRenderer,
    RendererFactory
)

# 基本グラフ要素
from sailing_data_processor.reporting.elements.visualizations.basic_charts import (
    LineChartElement,
    ScatterChartElement,
    BarChartElement,
    PieChartElement
)

# セーリング特化型グラフ要素
# 注意: sailing_charts.pyから分割された個別モジュールに移行
from sailing_data_processor.reporting.elements.visualizations.components.wind_rose_element import WindRoseElement
# 残りのコンポーネントは後で移行
from sailing_data_processor.reporting.elements.visualizations.sailing_charts import (
    CoursePerformanceElement,
    TackingAngleElement,
    StrategyPointMapElement
)

# 拡張版セーリング特化型グラフ要素
from sailing_data_processor.reporting.elements.visualizations.enhanced_sailing_charts import (
    EnhancedWindRoseElement,
    EnhancedCoursePerformanceElement,
    EnhancedTackingAngleElement
)
from sailing_data_processor.reporting.elements.visualizations.statistical_charts import (
    TimeSeriesElement,
    BoxPlotElement,
    HeatMapElement,
    CorrelationElement
)
from sailing_data_processor.reporting.elements.visualizations.map_elements import (
    TrackMapElement,
    HeatMapLayerElement,
    StrategyPointLayerElement,
    WindFieldElement
)
from sailing_data_processor.reporting.elements.visualizations.timeline_elements import (
    EventTimelineElement,
    ParameterTimelineElement,
    SegmentComparisonElement,
    DataViewerElement
)

__all__ = [
    # チャート基本要素
    'BaseChartElement',
    'ChartData',
    'BaseChartRenderer',
    'PlotlyRenderer',
    'ChartJSRenderer',
    'MatplotlibRenderer',
    'RendererFactory',
    
    # 基本グラフ要素
    'LineChartElement',
    'ScatterChartElement',
    'BarChartElement',
    'PieChartElement',
    
    # セーリング特化型グラフ要素
    'WindRoseElement',
    'CoursePerformanceElement',
    'TackingAngleElement',
    'StrategyPointMapElement',
    
    # 拡張版セーリング特化型グラフ要素
    'EnhancedWindRoseElement',
    'EnhancedCoursePerformanceElement',
    'EnhancedTackingAngleElement',
    
    # 統計グラフ要素
    'TimeSeriesElement',
    'BoxPlotElement',
    'HeatMapElement',
    'CorrelationElement',
    
    # マップ要素
    'TrackMapElement',
    'HeatMapLayerElement',
    'StrategyPointLayerElement',
    'WindFieldElement',
    
    # タイムライン要素
    'EventTimelineElement',
    'ParameterTimelineElement',
    'SegmentComparisonElement',
    'DataViewerElement'
]
