# -*- coding: utf-8 -*-
"""
戦略検出サービスのテスト
"""

import pytest
from datetime import datetime
import pandas as pd
import numpy as np
from uuid import uuid4

from app.services.strategy_detection_service import (
    _filter_by_sensitivity,
    _generate_recommendations,
    _create_strategy_detection_result
)

def test_filter_by_sensitivity():
    """検出感度によるフィルタリングのテスト"""
    # テスト用のストラテジーポイント
    strategy_points = [
        {"timestamp": datetime.now(), "latitude": 35.0, "longitude": 139.0, "strategy_type": "wind_shift", "confidence": 0.9},
        {"timestamp": datetime.now(), "latitude": 35.1, "longitude": 139.1, "strategy_type": "tack", "confidence": 0.7},
        {"timestamp": datetime.now(), "latitude": 35.2, "longitude": 139.2, "strategy_type": "layline", "confidence": 0.5},
        {"timestamp": datetime.now(), "latitude": 35.3, "longitude": 139.3, "strategy_type": "jibe", "confidence": 0.3}
    ]
    
    # 高感度（閾値が低い）でフィルタリング
    high_sensitivity = 0.8  # 検出感度高（confidence > 0.2のポイントを検出）
    filtered_high = _filter_by_sensitivity(strategy_points, high_sensitivity)
    assert len(filtered_high) == 4
    
    # 中感度でフィルタリング
    medium_sensitivity = 0.5  # 検出感度中（confidence > 0.5のポイントを検出）
    filtered_medium = _filter_by_sensitivity(strategy_points, medium_sensitivity)
    assert len(filtered_medium) == 3
    
    # 低感度（閾値が高い）でフィルタリング
    low_sensitivity = 0.2  # 検出感度低（confidence > 0.8のポイントを検出）
    filtered_low = _filter_by_sensitivity(strategy_points, low_sensitivity)
    assert len(filtered_low) == 1

def test_generate_recommendations():
    """推奨事項生成のテスト"""
    # 風向シフトのみ
    wind_shifts = [
        {"timestamp": datetime.now(), "latitude": 35.0, "longitude": 139.0, "strategy_type": "wind_shift", "confidence": 0.9, "metadata": {}}
    ]
    recommendations_wind = _generate_recommendations(wind_shifts)
    assert len(recommendations_wind) == 1
    assert "風向シフト" in recommendations_wind[0]
    
    # タックが多い
    many_tacks = [
        {"timestamp": datetime.now(), "latitude": 35.0, "longitude": 139.0, "strategy_type": "tack", "confidence": 0.9, "metadata": {}}
        for _ in range(6)
    ]
    recommendations_tacks = _generate_recommendations(many_tacks)
    assert len(recommendations_tacks) == 1
    assert "タック回数が多い" in recommendations_tacks[0]
    
    # タックが少ない
    one_tack = [
        {"timestamp": datetime.now(), "latitude": 35.0, "longitude": 139.0, "strategy_type": "tack", "confidence": 0.9, "metadata": {}},
        {"timestamp": datetime.now(), "latitude": 35.1, "longitude": 139.1, "strategy_type": "wind_shift", "confidence": 0.8, "metadata": {}}
    ]
    recommendations_one_tack = _generate_recommendations(one_tack)
    assert len(recommendations_one_tack) == 2
    assert any("タック回数が少ない" in rec for rec in recommendations_one_tack)
    
    # レイラインポイントあり
    with_laylines = [
        {"timestamp": datetime.now(), "latitude": 35.0, "longitude": 139.0, "strategy_type": "layline", "confidence": 0.9, "metadata": {}}
    ]
    recommendations_laylines = _generate_recommendations(with_laylines)
    assert len(recommendations_laylines) == 1
    assert "レイライン" in recommendations_laylines[0]

def test_create_strategy_detection_result():
    """戦略検出結果のAPI応答形式変換テスト"""
    # テスト用のストラテジーポイント
    strategy_points = [
        {"timestamp": datetime.now(), "latitude": 35.0, "longitude": 139.0, "strategy_type": "wind_shift", "confidence": 0.9, "metadata": {}},
        {"timestamp": datetime.now(), "latitude": 35.1, "longitude": 139.1, "strategy_type": "tack", "confidence": 0.8, "metadata": {}},
        {"timestamp": datetime.now(), "latitude": 35.2, "longitude": 139.2, "strategy_type": "jibe", "confidence": 0.7, "metadata": {}},
        {"timestamp": datetime.now(), "latitude": 35.3, "longitude": 139.3, "strategy_type": "layline", "confidence": 0.6, "metadata": {}}
    ]
    
    # セッションID
    session_id = str(uuid4())
    
    # 関数を実行
    result = _create_strategy_detection_result(strategy_points, session_id)
    
    # 結果を検証
    assert 'strategy_points' in result
    assert len(result['strategy_points']) == 4
    assert 'created_at' in result
    assert 'session_id' in result
    assert result['session_id'] == session_id
    assert 'total_tacks' in result
    assert result['total_tacks'] == 1
    assert 'total_jibes' in result
    assert result['total_jibes'] == 1
    assert 'total_wind_shifts' in result
    assert result['total_wind_shifts'] == 1
    assert 'total_layline_hits' in result
    assert result['total_layline_hits'] == 1
    assert 'recommendations' in result
    assert len(result['recommendations']) > 0
