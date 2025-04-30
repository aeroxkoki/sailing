# -*- coding: utf-8 -*-
"""
Distribution chart elements for visualization.
This module provides functions for rendering various distributions.
"""

from sailing_data_processor.reporting.elements.visualizations.distribution.base import DistributionChartElement
from sailing_data_processor.reporting.elements.visualizations.distribution.histogram import get_histogram_data
from sailing_data_processor.reporting.elements.visualizations.distribution.violin import get_violin_data
from sailing_data_processor.reporting.elements.visualizations.distribution.kde import get_kde_data, gaussian_kde

__all__ = [
    'DistributionChartElement',
    'get_histogram_data',
    'get_violin_data',
    'get_kde_data',
    'gaussian_kde'
]
