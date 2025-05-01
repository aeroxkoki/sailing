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
from sailing_data_processor.reporting.elements.visualizations.wind_rose_element import WindRoseElement
from sailing_data_processor.reporting.elements.visualizations.polar_diagram_element import PolarDiagramElement

# 統計グラフ要素
from sailing_data_processor.reporting.elements.visualizations.time_series_element import TimeSeriesElement
from sailing_data_processor.reporting.elements.visualizations.box_plot_element import BoxPlotElement

# 拡張版セーリング特化型グラフ要素
from sailing_data_processor.reporting.elements.visualizations.enhanced_sailing_charts import (
    EnhancedWindRoseElement,
    EnhancedCoursePerformanceElement,
    EnhancedTackingAngleElement
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
    'PolarDiagramElement',
    
    # 統計グラフ要素
    'TimeSeriesElement',
    'BoxPlotElement',
    
    # 拡張版セーリング特化型グラフ要素
    'EnhancedWindRoseElement',
    'EnhancedCoursePerformanceElement',
    'EnhancedTackingAngleElement',
    
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
