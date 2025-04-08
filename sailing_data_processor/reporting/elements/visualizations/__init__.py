"""
sailing_data_processor.reporting.elements.visualizations

可視化要素に関連するモジュールを提供するパッケージです。
チャート、マップ、ダイアグラムなどの高度な可視化要素を定義します。
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
from sailing_data_processor.reporting.elements.visualizations.sailing_charts import (
    WindRoseElement,
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
