# -*- coding: utf-8 -*-
"""
Module for sailing metrics calculations.
This module is now a wrapper that imports the refactored metrics modules.
"""

from typing import Dict, List, Any, Optional, Union, Tuple, Callable
import pandas as pd
import numpy as np

# Import the refactored metrics classes
from sailing_data_processor.reporting.data_processing.metrics import (
    SailingMetricsCalculator,
    VMGCalculator,
    ManeuverEfficiencyCalculator,
    LegAnalysisCalculator,
    SpeedMetricsCalculator,
    WindAngleCalculator,
    MetricsUtils
)

# For backward compatibility, re-export the main calculator
__all__ = ['SailingMetricsCalculator']
