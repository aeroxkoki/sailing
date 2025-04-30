# -*- coding: utf-8 -*-
"""
Distribution chart elements for visualization.
This module was split into smaller modules to improve maintainability.
All functionality is now available through the distribution package.
"""

from sailing_data_processor.reporting.elements.visualizations.distribution import (
    DistributionChartElement,
    get_histogram_data,
    get_violin_data,
    get_kde_data,
    gaussian_kde
)

__all__ = [
    'DistributionChartElement',
    'get_histogram_data',
    'get_violin_data',
    'get_kde_data',
    'gaussian_kde'
]
