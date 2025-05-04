# -*- coding: utf-8 -*-
"""
データ検証フィードバック統合のテスト

このテストファイルは、ValidationDashboardの改良版と
エッジケース対応、パフォーマンス最適化の検証を行います。
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time

from sailing_data_processor.data_model.container import GPSDataContainer
from sailing_data_processor.validation.data_validator import DataValidator
from sailing_data_processor.validation.quality_metrics import QualityMetricsCalculator
from sailing_data_processor.validation.visualization import ValidationVisualizer
from sailing_data_processor.validation.visualization_modules.validation_dashboard import ValidationDashboard


def create_test_data(size=20, with_problems=True):
    """
    テスト用のデータを作成
    
    Parameters
    ----------
    size : int, optional
        データサイズ, by default 20
    with_problems : bool, optional
        問題データを含めるかどうか, by default True
        
    Returns
    -------
    GPSDataContainer
        テスト用のGPSデータコンテナ
    """
    # サンプルデータ作成
    data = pd.DataFrame({
        'timestamp': [datetime(2025, 1, 1, 12, 0, i) for i in range(size)],
        'latitude': [35.0 + i * 0.001 for i in range(size)],
        'longitude': [135.0 + i * 0.001 for i in range(size)],
        'speed': [5.0 + i * 0.2 for i in range(size)],
        'course': [45.0 + i * 1.0 for i in range(size)],
        'boat_id': ['test_boat'] * size
    })
    
    # 問題データを含める場合
    if with_problems:
        # 欠損値
        data.loc[2, 'latitude'] = None
        data.loc[5, 'speed'] = None
        
        # 範囲外の値
        data.loc[8, 'speed'] = 100.0  # 異常な速度
        
        # 重複タイムスタンプ
        if size > 12:
            data.loc[12, 'timestamp'] = data.loc[11, 'timestamp']
        
        # 時間逆行
        if size > 15:
            data.loc[15, 'timestamp'] = data.loc[14, 'timestamp'] - timedelta(seconds=5)
        
        # 空間的異常（急激な位置の変化）
        if size > 18:
            data.loc[18, 'latitude'] = 36.0
    
    # GPSDataContainerの作成
    container = GPSDataContainer(data=data, metadata={
        'boat_id': 'test_boat',
        'data_source': 'integration_test',
        'created_at': datetime.now().isoformat()
    })
    
    return container


def test_validation_dashboard_initialization():
    """ValidationDashboardの初期化テスト"""
    # テストデータを作成
    container = create_test_data()
    validator = DataValidator()
    validator.validate(container)
    
    # 基本的な初期化
    dashboard = ValidationDashboard(
        container=container,
        validator=validator,
        key_prefix="test_dashboard"
    )
    
    # 初期化が正しく行われたことを確認
    assert dashboard.container == container
    assert dashboard.validator == validator
    assert dashboard.key_prefix == "test_dashboard"
    assert dashboard.enable_advanced_features == True
    assert hasattr(dashboard, '_processing_state')
    assert hasattr(dashboard, '_cache_timestamp')
    assert hasattr(dashboard, '_cache_expiry')
    
    # コールバック機能付きの初期化
    def mock_fix_proposal(proposal_id, method_type):
        return {"success": True}
        
    def mock_export(format_type):
        pass
        
    def mock_data_update(container):
        pass
    
    # 拡張機能を無効にした初期化
    dashboard_advanced = ValidationDashboard(
        container=container,
        validator=validator,
        key_prefix="test_advanced",
        on_fix_proposal=mock_fix_proposal,
        on_export=mock_export,
        on_data_update=mock_data_update,
        enable_advanced_features=False
    )
    
    # 拡張機能フラグと拡張コールバックが正しく設定されたか確認
    assert dashboard_advanced.enable_advanced_features == False
    assert dashboard_advanced.on_fix_proposal == mock_fix_proposal
    assert dashboard_advanced.on_export == mock_export
    assert dashboard_advanced.on_data_update == mock_data_update


def test_optimize_data_processing():
    """データ処理最適化機能のテスト"""
    # テストデータを作成
    container = create_test_data(size=20)
    validator = DataValidator()
    validator.validate(container)
    
    dashboard = ValidationDashboard(
        container=container,
        validator=validator,
        key_prefix="test_optimize"
    )
    
    # 小規模データの場合（そのまま返される）
    small_data = dashboard._optimize_data_processing(container.data)
    assert len(small_data) == len(container.data)
    assert small_data.equals(container.data)
    
    # 大規模データの場合
    large_size = 15000
    large_data = pd.DataFrame({
        'timestamp': [datetime(2025, 1, 1, 12, 0, i % 60) + timedelta(minutes=i // 60) for i in range(large_size)],
        'latitude': [35.0 + (i % 1000) * 0.0001 for i in range(large_size)],
        'longitude': [135.0 + (i % 1000) * 0.0001 for i in range(large_size)],
        'speed': [5.0 + (i % 100) * 0.05 for i in range(large_size)],
        'course': [45.0 + (i % 360) for i in range(large_size)],
        'boat_id': ['test_boat'] * large_size
    })
    
    # 問題データを追加
    for i in range(0, large_size, 1000):
        if i % 2000 == 0:
            large_data.loc[i, 'latitude'] = None
        else:
            large_data.loc[i, 'speed'] = 999.0
    
    # 大きなデータを最適化
    optimized_data = dashboard._optimize_data_processing(large_data)
    
    # 最適化されたデータのサイズが小さくなったことを確認
    assert len(optimized_data) < len(large_data)
    assert len(optimized_data) > 0
    
    # 問題データが含まれていることを確認
    assert optimized_data['latitude'].isna().any()
    assert (optimized_data['speed'] > 100).any()
    
    # 2回目の呼び出しでキャッシュが使用されることを確認
    optimized_data2 = dashboard._optimize_data_processing(large_data)
    assert id(optimized_data) == id(optimized_data2)


def test_implement_caching():
    """キャッシュ機能のテスト"""
    container = create_test_data()
    validator = DataValidator()
    validator.validate(container)
    
    dashboard = ValidationDashboard(
        container=container,
        validator=validator,
        key_prefix="test_cache"
    )
    
    # キャッシュのテスト用カウンタ
    call_count = 0
    
    # テスト用計算関数
    def test_compute():
        nonlocal call_count
        call_count += 1
        return {"result": "test", "timestamp": time.time()}
    
    # キャッシュを使用して計算
    result1 = dashboard._implement_caching("test", "key1", test_compute)
    assert call_count == 1
    
    # 同じキーで再度呼び出し（キャッシュヒット）
    result2 = dashboard._implement_caching("test", "key1", test_compute)
    assert call_count == 1  # 関数は再実行されていない
    assert result1 == result2
    
    # 別のキーで呼び出し（キャッシュミス）
    result3 = dashboard._implement_caching("test", "key2", test_compute)
    assert call_count == 2  # 関数が再実行された
    assert result1 != result3
    
    # キャッシュの有効期限テスト
    # 現在のキャッシュ有効期限を保存
    original_expiry = dashboard._cache_expiry
    
    try:
        # テスト用に短い有効期限を設定
        dashboard._cache_expiry = 0.1  # 100ミリ秒
        
        # 計算を実行してキャッシュに保存
        result4 = dashboard._implement_caching("test", "key3", test_compute)
        assert call_count == 3
        
        # すぐに再度呼び出し（キャッシュヒット）
        result5 = dashboard._implement_caching("test", "key3", test_compute)
        assert call_count == 3
        assert result4 == result5
        
        # 有効期限が切れるまで待機
        time.sleep(0.2)
        
        # 再度呼び出し（有効期限切れ→キャッシュミス）
        result6 = dashboard._implement_caching("test", "key3", test_compute)
        assert call_count == 4
        assert result4 != result6
    
    finally:
        # 元の有効期限に戻す
        dashboard._cache_expiry = original_expiry


def test_edge_cases():
    """エッジケース対応のテスト"""
    # 空のデータセット
    empty_container = GPSDataContainer()
    empty_container.data = pd.DataFrame()
    
    validator = DataValidator()
    dashboard = ValidationDashboard(
        container=empty_container,
        validator=validator,
        key_prefix="test_edge"
    )
    
    # 空データの処理
    optimized_empty = dashboard._optimize_data_processing(empty_container.data)
    assert optimized_empty.empty
    
    # Noneデータの処理
    none_result = dashboard._optimize_data_processing(None)
    assert none_result.empty
    
    # 1行だけのデータ
    tiny_container = GPSDataContainer()
    tiny_container.data = pd.DataFrame({
        'timestamp': [datetime(2025, 1, 1, 12, 0, 0)],
        'latitude': [35.0],
        'longitude': [135.0],
        'speed': [5.0]
    })
    
    tiny_dashboard = ValidationDashboard(
        container=tiny_container,
        validator=validator,
        key_prefix="test_tiny"
    )
    
    # 1行データの処理（そのまま返される）
    optimized_tiny = tiny_dashboard._optimize_data_processing(tiny_container.data)
    assert len(optimized_tiny) == 1
    assert optimized_tiny.equals(tiny_container.data)
    
    # 問題だらけのデータ（全行が問題）
    problem_data = pd.DataFrame({
        'timestamp': [datetime(2025, 1, 1, 12, 0, i) for i in range(20)],
        'latitude': [None] * 20,  # すべて欠損
        'longitude': [135.0 + i * 0.001 for i in range(20)],
        'speed': [999.0] * 20  # すべて異常値
    })
    
    problem_container = GPSDataContainer()
    problem_container.data = problem_data
    
    problem_dashboard = ValidationDashboard(
        container=problem_container,
        validator=validator,
        key_prefix="test_problem"
    )
    
    # 問題データの処理
    optimized_problem = problem_dashboard._optimize_data_processing(problem_data)
    assert not optimized_problem.empty
    assert optimized_problem['latitude'].isna().all()
    assert (optimized_problem['speed'] > 100).all()


def test_handle_interactive_fix_result():
    """インタラクティブな修正結果処理のテスト"""
    # テストデータを作成
    container = create_test_data()
    validator = DataValidator()
    validator.validate(container)
    
    # データ更新フラグ
    update_called = False
    
    def mock_data_update(updated_container):
        nonlocal update_called
        update_called = True
    
    dashboard = ValidationDashboard(
        container=container,
        validator=validator,
        key_prefix="test_fix",
        on_data_update=mock_data_update
    )
    
    # 空の修正結果
    empty_result = {}
    result = dashboard.handle_interactive_fix_result(empty_result)
    assert not result
    
    # 失敗した修正結果
    failed_result = {
        "status": "error",
        "error": "テストエラー"
    }
    result = dashboard.handle_interactive_fix_result(failed_result)
    assert not result
    
    # 成功した修正結果（コンテナなし）
    success_no_container = {
        "status": "success"
    }
    result = dashboard.handle_interactive_fix_result(success_no_container)
    assert result
    assert not update_called
    
    # 成功した修正結果（コンテナあり）
    fixed_container = create_test_data(with_problems=False)
    success_with_container = {
        "status": "success",
        "container": fixed_container,
        "fix_type": "auto",
        "affected_indices": [2, 5, 8, 12, 15, 18],
        "affected_count": 6,
        "message_displayed": True
    }
    
    result = dashboard.handle_interactive_fix_result(success_with_container)
    assert result
    assert update_called
    assert dashboard.container == fixed_container


def test_identify_important_points():
    """重要ポイント特定機能のテスト"""
    # テストデータを作成
    container = create_test_data(size=100)
    validator = DataValidator()
    validator.validate(container)
    
    dashboard = ValidationDashboard(
        container=container,
        validator=validator,
        key_prefix="test_important"
    )
    
    # 重要ポイントを特定
    important_points = dashboard._identify_important_points(container.data)
    
    # 結果の検証
    assert isinstance(important_points, list)
    assert len(important_points) > 0
    assert len(important_points) < len(container.data)  # すべてのポイントが返されるわけではない
    
    # 最大値・最小値が含まれているか
    max_speed_idx = container.data['speed'].idxmax()
    min_speed_idx = container.data['speed'].idxmin()
    
    assert max_speed_idx in important_points
    assert min_speed_idx in important_points
    
    # 先頭と末尾が含まれているか
    assert 0 in important_points
    assert len(container.data) - 1 in important_points
    
    # 空データの処理
    empty_data = pd.DataFrame()
    empty_points = dashboard._identify_important_points(empty_data)
    assert empty_points == []
    
    # 極小データの処理
    tiny_data = container.data.head(5)
    tiny_points = dashboard._identify_important_points(tiny_data)
    assert tiny_points == []  # 10行未満なので空リストが返される
    
    # エラーケース（数値でないデータ）
    text_data = pd.DataFrame({
        'col1': ['a', 'b', 'c'],
        'col2': ['d', 'e', 'f']
    })
    text_points = dashboard._identify_important_points(text_data)
    assert text_points == []  # エラーがあっても空リストが返される


def test_render_spatial_problem_visualization():
    """空間問題可視化機能のテスト"""
    # テストデータを作成（位置データあり）
    container = create_test_data()
    validator = DataValidator()
    validator.validate(container)
    
    dashboard = ValidationDashboard(
        container=container,
        validator=validator,
        key_prefix="test_spatial"
    )
    
    # 問題インデックスを取得
    problem_indices = [2, 8, 15, 18]  # サンプルの問題インデックス
    
    # 可視化メソッドの実行（実際の描画はしない）
    # エラーが発生しないことを確認
    try:
        dashboard._render_spatial_problem_visualization(problem_indices)
        visualization_works = True
    except Exception as e:
        visualization_works = False
        print(f"可視化エラー: {e}")
    
    assert visualization_works
    
    # 位置データなしの場合
    no_position_data = pd.DataFrame({
        'timestamp': [datetime(2025, 1, 1, 12, 0, i) for i in range(10)],
        'speed': [5.0 + i * 0.2 for i in range(10)]
    })
    
    no_position_container = GPSDataContainer()
    no_position_container.data = no_position_data
    
    no_position_dashboard = ValidationDashboard(
        container=no_position_container,
        validator=validator,
        key_prefix="test_no_position"
    )
    
    # 位置データなしでのテスト
    try:
        no_position_dashboard._render_spatial_problem_visualization([0, 1, 2])
        no_position_works = True
    except Exception as e:
        no_position_works = False
        print(f"位置データなしエラー: {e}")
    
    assert no_position_works


def test_handle_large_dataset():
    """大規模データセット処理機能のテスト"""
    # テストデータを作成
    container = create_test_data()
    validator = DataValidator()
    validator.validate(container)
    
    dashboard = ValidationDashboard(
        container=container,
        validator=validator,
        key_prefix="test_large"
    )
    
    # 小規模データの処理（そのまま返される）
    small_data = dashboard.handle_large_dataset(container.data, max_size=100)
    assert len(small_data) == len(container.data)
    assert small_data.equals(container.data)
    
    # 大規模データの処理
    large_size = 15000
    large_data = pd.DataFrame({
        'timestamp': [datetime(2025, 1, 1, 12, 0, i % 60) + timedelta(minutes=i // 60) for i in range(large_size)],
        'latitude': [35.0 + (i % 1000) * 0.0001 for i in range(large_size)],
        'longitude': [135.0 + (i % 1000) * 0.0001 for i in range(large_size)],
        'speed': [5.0 + (i % 100) * 0.05 for i in range(large_size)]
    })
    
    # 最適化（サイズ制限を小さくして強制的に最適化）
    optimized_large = dashboard.handle_large_dataset(large_data, max_size=1000)
    
    # 結果の検証
    assert len(optimized_large) < len(large_data)
    assert len(optimized_large) <= 10000  # デフォルトの最大サイズ
    
    # 2回目の呼び出し（キャッシュが使用される）
    optimized_large2 = dashboard.handle_large_dataset(large_data, max_size=1000)
    assert id(optimized_large) == id(optimized_large2)  # 同じオブジェクト
    
    # 空データの処理
    empty_data = pd.DataFrame()
    optimized_empty = dashboard.handle_large_dataset(empty_data)
    assert optimized_empty.empty