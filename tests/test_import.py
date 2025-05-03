#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
インポートテスト
"""

import sys
import os
import pytest

# レポジトリのルートパスを追加
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

def test_import_sailing_data_processor():
    """sailing_data_processorパッケージのインポートテスト"""
    import sailing_data_processor
    assert sailing_data_processor.__version__ is not None

def test_import_wind_propagation_model():
    """WindPropagationModelのインポートテスト"""
    from sailing_data_processor.wind_propagation_model import WindPropagationModel
    model = WindPropagationModel()
    assert model is not None
