#\!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全モジュールのインポートテスト
"""

import pytest
import sys
import os

# テスト対象モジュールのパスを追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# インポートテスト対象のモジュールリスト
modules_to_test = [
    'sailing_data_processor',
    'sailing_data_processor.wind',
    'sailing_data_processor.boat_fusion',
    'sailing_data_processor.wind.wind_estimator',
    'sailing_data_processor.wind.wind_estimator_utils',
    'sailing_data_processor.wind.wind_estimator_maneuvers',
    'sailing_data_processor.wind.wind_estimator_calculation',
    'sailing_data_processor.boat_fusion.boat_data_fusion_base',
    'sailing_data_processor.boat_fusion.boat_data_fusion_analysis',
    'sailing_data_processor.boat_fusion.boat_data_fusion_integration',
    'sailing_data_processor.boat_fusion.boat_data_fusion_utils'
]

@pytest.mark.parametrize("module_name", modules_to_test)
def test_module_import(module_name):
    """各モジュールがインポート可能かテスト"""
    try:
        module = __import__(module_name, fromlist=[''])
        assert module is not None
        print(f"Successfully imported {module_name}")
    except ImportError as e:
        pytest.fail(f"Failed to import {module_name}: {e}")
