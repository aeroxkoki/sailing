# -*- coding: utf-8 -*-
"""
sailing_data_processor.wind_estimator モジュール

このモジュールは下位互換性のために維持されています。
新しいコードは sailing_data_processor.wind モジュールを使用してください。
"""

# 互換性のため、WindEstimatorクラスを再エクスポート
from sailing_data_processor.wind.wind_estimator import WindEstimator

# 警告メッセージ
import warnings
warnings.warn(
    "This module is deprecated. Use sailing_data_processor.wind.wind_estimator instead.",
    DeprecationWarning,
    stacklevel=2
)
