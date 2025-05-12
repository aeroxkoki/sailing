# -*- coding: utf-8 -*-
"""
Calculators Module - Provides functionality for various calculations (Backward compatibility module).
"""

# Import for backward compatibility
from sailing_data_processor.reporting.data_processing.base_calculator import BaseCalculator
from sailing_data_processor.reporting.data_processing.performance_calculator import PerformanceCalculator
from sailing_data_processor.reporting.data_processing.statistical_calculator import StatisticalCalculator
from sailing_data_processor.reporting.data_processing.custom_formula_calculator import CustomFormulaCalculator

__all__ = [
    'BaseCalculator',
    'PerformanceCalculator',
    'StatisticalCalculator',
    'CustomFormulaCalculator',
]
