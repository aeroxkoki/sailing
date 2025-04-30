# -*- coding: utf-8 -*-
"""
Validation module for data quality checking and correction.
"""

from sailing_data_processor.validation.data_validator import DataValidator
from sailing_data_processor.validation.data_cleaner import DataCleaner, FixProposal
from sailing_data_processor.validation.quality_metrics import QualityMetricsCalculator
from sailing_data_processor.validation.correction import CorrectionProcessor
from sailing_data_processor.validation.correction_options import get_correction_options
from sailing_data_processor.validation.correction_suggester import CorrectionSuggester
from sailing_data_processor.validation.correction_interface import InteractiveCorrectionInterface

__all__ = [
    'DataValidator',
    'DataCleaner',
    'FixProposal',
    'QualityMetricsCalculator',
    'CorrectionProcessor',
    'get_correction_options',
    'CorrectionSuggester',
    'InteractiveCorrectionInterface'
]
