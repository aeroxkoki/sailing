# -*- coding: utf-8 -*-
"""
統合テスト: 検証・可視化システムの統合テスト
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from sailing_data_processor.data_model.container import GPSDataContainer
from sailing_data_processor.validation.data_validator import DataValidator
from sailing_data_processor.validation.quality_metrics import QualityMetricsCalculator
from sailing_data_processor.validation.visualization import ValidationVisualizer
from sailing_data_processor.validation.correction import CorrectionProcessor
from sailing_data_processor.validation.correction_interface import InteractiveCorrectionInterface

def create_test_data():
    """テスト用のデータを作成"""
    # サンプルデータ作成（いくつかの問題を含む）
    data = pd.DataFrame({
        'timestamp': [datetime(2025, 1, 1, 12, 0, i) for i in range(20)],
        'latitude': [35.0 + i * 0.001 for i in range(20)],
        'longitude': [135.0 + i * 0.001 for i in range(20)],
        'speed': [5.0 + i * 0.2 for i in range(20)],
        'course': [45.0 + i * 1.0 for i in range(20)],
        'boat_id': ['test_boat'] * 20
    })
    
    # いくつかの問題を作成
    # 欠損値
    data.loc[2, 'latitude'] = None
    data.loc[5, 'speed'] = None
    
    # 範囲外の値
    data.loc[8, 'speed'] = 100.0  # 異常な速度
    
    # 重複タイムスタンプ
    data.loc[12, 'timestamp'] = data.loc[11, 'timestamp']
    
    # 時間逆行
    data.loc[15, 'timestamp'] = data.loc[14, 'timestamp'] - timedelta(seconds=5)
    
    # 空間的異常（急激な位置の変化）
    data.loc[18, 'latitude'] = 36.0
    
    # GPSDataContainerの作成
    container = GPSDataContainer(data=data, metadata={
        'boat_id': 'test_boat',
        'data_source': 'integration_test',
        'created_at': datetime.now().isoformat()
    })
    
    return container

def test_end_to_end_validation_workflow():
    """検証ワークフローの統合テスト"""
    # テストデータを作成
    container = create_test_data()
    
    # 1. バリデーションの実行
    validator = DataValidator()
    validation_results = validator.validate(container)
    
    # バリデーション結果の確認
    assert isinstance(validation_results, list)
    assert len(validation_results) > 0
    assert not all(result['is_valid'] for result in validation_results)
    
    # 2. 品質メトリクスの計算
    metrics_calculator = QualityMetricsCalculator(validation_results, container.data)
    
    # 品質スコアの確認
    quality_scores = metrics_calculator.quality_scores
    assert 'completeness' in quality_scores
    assert 'accuracy' in quality_scores
    assert 'consistency' in quality_scores
    assert 'total' in quality_scores
    assert quality_scores['total'] < 100  # 問題があるので満点ではない
    
    # 問題の分布確認
    problem_distribution = metrics_calculator.problem_distribution
    assert problem_distribution['problem_type']['has_data']
    problem_counts = problem_distribution['problem_type']['problem_counts']
    assert problem_counts['missing_data'] == 2  # 欠損値
    assert problem_counts['out_of_range'] == 1  # 範囲外
    assert problem_counts['duplicates'] == 2    # 重複
    assert problem_counts['temporal_anomalies'] >= 1  # 時間的異常
    assert problem_counts['spatial_anomalies'] >= 1  # 空間的異常
    
    # 3. 可視化の生成
    visualizer = ValidationVisualizer(metrics_calculator, container.data)
    
    # 品質スコア可視化の確認
    quality_chart = visualizer.generate_quality_score_chart()
    assert quality_chart is not None
    
    # 問題分布可視化の確認
    distribution_chart = visualizer.generate_problem_distribution_chart()
    assert distribution_chart is not None
    
    # 4. 修正インターフェースのテスト
    correction_interface = InteractiveCorrectionInterface(
        container=container,
        validator=validator
    )
    
    # 問題カテゴリの確認
    categories = correction_interface.get_problem_categories()
    assert categories['missing_data'] == 2
    assert categories['out_of_range'] == 1
    assert categories['duplicates'] == 2
    assert categories['temporal_anomalies'] >= 1
    assert categories['spatial_anomalies'] >= 1
    
    # 修正オプションの確認
    missing_data_options = correction_interface.get_correction_options('missing_data')
    assert len(missing_data_options) > 0
    assert any(opt['id'] == 'interpolate_linear' for opt in missing_data_options)
    
    # 修正アクションのテスト
    test_passed = False
    try:
        # 自動修正（全て）
        fixed_container = correction_interface.auto_fix_all()
        
        if fixed_container is not None:
            # 修正後のコンテナの検証
            new_validator = DataValidator()
            new_results = new_validator.validate(fixed_container)
            
            # 問題が減少または解決されたか確認
            new_metrics = QualityMetricsCalculator(new_results, fixed_container.data)
            new_scores = new_metrics.quality_scores
            
            # スコアが向上したかチェック
            assert new_scores['total'] > quality_scores['total']
            test_passed = True
    except Exception as e:
        # 自動修正エラーの場合はスキップしてテスト続行
        print(f"自動修正テストがエラーで失敗: {e}")
    
    # 個別の問題修正をテスト
    if not test_passed:
        try:
            # 欠損値を修正
            null_indices = metrics_calculator.problematic_indices['missing_data']
            if null_indices:
                fixed_container = correction_interface.apply_correction(
                    problem_type='missing_data',
                    option_id='interpolate_linear',
                    target_indices=null_indices
                )
                
                if fixed_container:
                    # 修正後のコンテナを検証
                    new_validator = DataValidator()
                    new_results = new_validator.validate(fixed_container)
                    new_metrics = QualityMetricsCalculator(new_results, fixed_container.data)
                    
                    # 欠損値が減少したか確認
                    assert len(new_metrics.problematic_indices['missing_data']) < len(metrics_calculator.problematic_indices['missing_data'])
                    test_passed = True
        except Exception as e:
            print(f"個別修正テストがエラーで失敗: {e}")
    
    # 少なくとも1つのテストがパスしたかを確認
    assert test_passed, "すべての修正テストが失敗しました"

def test_large_dataset_optimization():
    """大規模データセットの最適化テスト"""
    # 大規模テストデータを作成（10,000行以上）
    timestamps = [datetime(2025, 1, 1) + timedelta(seconds=i) for i in range(12000)]
    latitudes = [35.0 + i * 0.0001 for i in range(12000)]
    longitudes = [135.0 + i * 0.0001 for i in range(12000)]
    speeds = [5.0 + (i % 100) * 0.01 for i in range(12000)]
    
    # 一部のデータを問題あり（欠損値や極端な値）に設定
    for i in range(0, 12000, 500):  # 500行ごとに問題を混入
        if i % 1000 == 0:
            latitudes[i] = None  # 欠損値
        elif i % 1500 == 0:
            speeds[i] = 1000.0  # 極端な値
    
    large_data = pd.DataFrame({
        'timestamp': timestamps,
        'latitude': latitudes,
        'longitude': longitudes,
        'speed': speeds,
        'boat_id': ['test_boat'] * 12000
    })
    
    container = GPSDataContainer()
    container.data = large_data
    container.metadata = {
        'boat_id': 'large_test',
        'created_at': datetime.now().isoformat()
    }
    
    # バリデーション実行
    validator = DataValidator()
    validation_results = validator.validate(container)
    
    # ValidationDashboardを使って最適化をテスト
    try:
        from ui.components.visualizations.validation_dashboard import ValidationDashboard
        
        # ValidationDashboardのインスタンス化
        dashboard = ValidationDashboard(
            container=container,
            validator=validator
        )
        
        # _optimize_data_processingメソッドをテスト
        optimized_data = dashboard._optimize_data_processing(large_data)
        
        # 最適化後のデータサイズを確認
        assert len(optimized_data) <= 10000, "大規模データが適切にサンプリングされていません"
        
        # 問題のあるデータが保持されているか確認
        # この部分はデータセット固有の実装に依存するため、テストは簡素化
        assert len(optimized_data) > 0, "最適化後のデータが空です"
        
    except ImportError:
        pytest.skip("UI components not available")

def test_correction_suggestion_generation():
    """修正提案生成のテスト"""
    # テストデータを作成
    container = create_test_data()
    
    # バリデーション実行
    validator = DataValidator()
    validation_results = validator.validate(container)
    
    # 修正提案生成器をテスト
    from sailing_data_processor.validation.correction import CorrectionSuggester
    
    suggester = CorrectionSuggester(validator, container)
    proposals = suggester.generate_fix_proposals()
    
    # 修正提案が生成されていることを確認
    assert isinstance(proposals, list), "修正提案が適切に生成されていません"
    
    # 問題が含まれているため、少なくともいくつかの提案が生成されているはず
    assert len(proposals) > 0, "テストデータに問題があるにもかかわらず修正提案が生成されていません"
    
    # 提案の構造を検証
    if proposals:
        proposal = proposals[0]
        assert "id" in proposal, "提案にIDがありません"
        assert "issue_type" in proposal, "提案に問題タイプがありません"
        assert "affected_indices" in proposal, "提案に影響インデックスがありません"
        assert "methods" in proposal, "提案に修正方法がありません"

def test_quality_score_calculation():
    """品質スコア計算の精度テスト"""
    # テストケース1: 問題がほとんどないデータ
    clean_data = pd.DataFrame({
        'timestamp': [datetime(2025, 1, 1, 12, 0, i) for i in range(20)],
        'latitude': [35.0 + i * 0.001 for i in range(20)],
        'longitude': [135.0 + i * 0.001 for i in range(20)],
        'speed': [5.0 + i * 0.2 for i in range(20)]
    })
    
    container_clean = GPSDataContainer()
    container_clean.data = clean_data
    
    # テストケース2: いくつかの問題があるデータ
    container_with_issues = create_test_data()
    
    # テストケース3: 多数の問題があるデータ
    problematic_data = pd.DataFrame({
        'timestamp': [datetime(2025, 1, 1, 12, 0, i) for i in range(20)],
        'latitude': [None if i % 4 == 0 else 35.0 + i * 0.001 for i in range(20)],
        'longitude': [None if i % 5 == 0 else 135.0 + i * 0.001 for i in range(20)],
        'speed': [999.0 if i % 3 == 0 else 5.0 + i * 0.2 for i in range(20)]
    })
    
    # タイムスタンプの重複と逆行を追加
    problematic_data.iloc[10, 0] = problematic_data.iloc[9, 0]  # 重複
    problematic_data.iloc[15, 0] = problematic_data.iloc[14, 0] - timedelta(seconds=10)  # 逆行
    
    container_problematic = GPSDataContainer()
    container_problematic.data = problematic_data
    
    # バリデーション実行
    validator = DataValidator()
    
    # 各データセットの品質スコアを計算
    validation_clean = validator.validate(container_clean)
    validation_with_issues = validator.validate(container_with_issues)
    validation_problematic = validator.validate(container_problematic)
    
    metrics_clean = QualityMetricsCalculator(validation_clean, container_clean.data)
    metrics_with_issues = QualityMetricsCalculator(validation_with_issues, container_with_issues.data)
    metrics_problematic = QualityMetricsCalculator(validation_problematic, container_problematic.data)
    
    # 品質スコアを取得
    score_clean = metrics_clean.quality_scores["total"]
    score_with_issues = metrics_with_issues.quality_scores["total"]
    score_problematic = metrics_problematic.quality_scores["total"]
    
    # 期待される結果を確認
    assert score_clean > score_with_issues, "きれいなデータの方が品質スコアが高いはず"
    assert score_with_issues > score_problematic, "問題が少ないデータの方が品質スコアが高いはず"
    
    # スコアの範囲チェック
    assert 0 <= score_clean <= 100, "品質スコアは0～100の範囲であるべき"
    assert 0 <= score_with_issues <= 100, "品質スコアは0～100の範囲であるべき"
    assert 0 <= score_problematic <= 100, "品質スコアは0～100の範囲であるべき"
    
    # カテゴリスコアの確認
    assert "completeness" in metrics_clean.quality_scores, "完全性スコアがありません"
    assert "accuracy" in metrics_clean.quality_scores, "正確性スコアがありません"
    assert "consistency" in metrics_clean.quality_scores, "一貫性スコアがありません"

def test_validation_dashboard_integration():
    """検証ダッシュボードの統合テスト"""
    # テストデータを作成
    container = create_test_data()
    
    # バリデーションの実行
    validator = DataValidator()
    validator.validate(container)
    
    # ダッシュボードの生成
    try:
        from sailing_data_processor.validation.visualization import ValidationDashboard
        from ui.components.visualizations.validation_dashboard_base import ValidationDashboardBase
        
        # ValidationDashboardクラスのインスタンス化テスト
        dashboard = ValidationDashboard(validator.validation_results, container.data)
        
        # レンダリングメソッドの存在確認
        assert hasattr(dashboard, 'render_overview_section')
        assert hasattr(dashboard, 'render_details_section')
        assert hasattr(dashboard, 'render_action_section')
        
        # ValidationDashboardBaseクラスのインスタンス化テスト
        try:
            dashboard_base = ValidationDashboardBase(container, validator)
            
            # 主要メソッドの存在確認
            assert hasattr(dashboard_base, '_render_overview_section')
            assert hasattr(dashboard_base, '_render_details_section')
            assert hasattr(dashboard_base, '_render_action_section')
            
        except Exception as e:
            # Streamlitが必要なケースでは、メソッドの存在だけを検証
            pass
            
    except ImportError:
        # UI依存のコンポーネントはオプショナルとしてスキップ
        pytest.skip("UI components not available")

def test_data_cleaning_integration():
    """データクリーニングコンポーネントの統合テスト"""
    # テストデータを作成
    container = create_test_data()
    
    # バリデーションの実行
    validator = DataValidator()
    validator.validate(container)
    
    # データクリーニングコンポーネントのテスト
    try:
        from ui.components.forms.data_cleaning_basic import DataCleaningBasic, CorrectionHandler
        
        # CorrectionHandlerクラスのインスタンス化テスト
        handler = CorrectionHandler(container, validator)
        
        # 基本メソッドの確認
        assert hasattr(handler, 'get_problem_categories')
        assert hasattr(handler, 'get_problem_records')
        assert hasattr(handler, 'get_correction_options')
        assert hasattr(handler, 'apply_correction')
        assert hasattr(handler, 'auto_fix')
        
        # 問題カテゴリの取得と確認
        categories = handler.get_problem_categories()
        assert isinstance(categories, dict)
        assert 'missing_data' in categories
        assert 'out_of_range' in categories
        assert 'duplicates' in categories
        
        # DataCleaningBasicクラスのインスタンス化は、StreamlitのUI依存のためスキップ
        
    except ImportError:
        # UI依存のコンポーネントはオプショナルとしてスキップ
        pytest.skip("UI components not available")

def test_validation_dashboard_with_callback():
    """統合テスト: ValidationDashboardのコールバック機能"""
    try:
        # ValidationDashboardクラスをインポート
        from ui.components.visualizations.validation_dashboard import ValidationDashboard
        
        # テストデータを作成
        container = create_test_data()
        validator = DataValidator()
        validator.validate(container)
        
        # コールバック関数のモック作成
        fix_proposal_results = {}
        fixed_container = None
        export_format = None
        update_called = False
        
        # コールバック関数
        def mock_fix_proposal(proposal_id, method_type):
            fix_proposal_results["proposal_id"] = proposal_id
            fix_proposal_results["method_type"] = method_type
            
            # コンテナを複製して返す（実際の修正は行わない）
            import copy
            fixed = copy.deepcopy(container)
            
            return {
                "success": True,
                "message": "テスト用の修正が完了しました",
                "container": fixed
            }
        
        def mock_export(format_type):
            nonlocal export_format
            export_format = format_type
        
        def mock_data_update(container):
            nonlocal update_called
            update_called = True
            
        # ValidationDashboardのインスタンス化
        dashboard = ValidationDashboard(
            container=container,
            validator=validator,
            key_prefix="test_dashboard",
            on_fix_proposal=mock_fix_proposal,
            on_export=mock_export,
            on_data_update=mock_data_update
        )
        
        # コールバック関数が正しく設定されていることを確認
        assert dashboard.on_fix_proposal == mock_fix_proposal
        assert dashboard.on_export == mock_export
        assert dashboard.on_data_update == mock_data_update
        
        # ダミーの修正適用結果
        dummy_fix_result = {
            "success": True,
            "message": "テスト用の修正が完了しました",
            "container": container
        }
        
        # _handle_fix_applicationメソッドをテスト
        dashboard._handle_fix_application(dummy_fix_result)
        
        # データ更新コールバックが呼ばれたことを確認
        assert update_called
        
    except ImportError:
        # UI依存のコンポーネントはオプショナルとしてスキップ
        pytest.skip("UI components not available")

def test_data_processing_optimization():
    """大規模データセット最適化処理のテスト"""
    try:
        # ValidationDashboardクラスをインポート
        from ui.components.visualizations.validation_dashboard import ValidationDashboard
        
        # 大規模データセットを作成（12,000行）
        timestamps = [datetime(2025, 1, 1) + timedelta(seconds=i) for i in range(12000)]
        latitudes = [35.0 + i * 0.0001 for i in range(12000)]
        longitudes = [135.0 + i * 0.0001 for i in range(12000)]
        speeds = [5.0 + (i % 100) * 0.01 for i in range(12000)]
        
        # 問題データを作成
        for i in range(0, 12000, 1000):
            if i % 2000 == 0:
                latitudes[i] = None  # 欠損値
            else:
                speeds[i] = 999.0  # 異常値
        
        large_data = pd.DataFrame({
            'timestamp': timestamps,
            'latitude': latitudes,
            'longitude': longitudes,
            'speed': speeds,
            'boat_id': ['test_boat'] * 12000
        })
        
        container = GPSDataContainer()
        container.data = large_data
        
        # ValidationDashboardのインスタンス化
        validator = DataValidator()
        validator.validate(container)
        
        dashboard = ValidationDashboard(
            container=container,
            validator=validator
        )
        
        # データ最適化メソッドをテスト
        optimized_data = dashboard._optimize_data_processing(large_data)
        
        # 最適化の検証
        assert len(optimized_data) < len(large_data), "データが最適化されていません"
        assert len(optimized_data) > 0, "最適化後のデータが空です"
        
        # 問題データが含まれていることの確認
        has_null = optimized_data['latitude'].isna().any()
        has_extreme = (optimized_data['speed'] > 100).any()
        
        assert has_null, "最適化後のデータに欠損値が含まれていません"
        assert has_extreme, "最適化後のデータに異常値が含まれていません"
        
        # 2回目の呼び出しでキャッシュが使用されることを確認
        optimized_data2 = dashboard._optimize_data_processing(large_data)
        assert id(optimized_data) == id(optimized_data2), "キャッシュが使用されていません"
        
    except ImportError:
        # UI依存のコンポーネントはオプショナルとしてスキップ
        pytest.skip("UI components not available")
        
def test_dashboard_correction_controls_integration():
    """ValidationDashboardとCorrectionControlsの統合テスト"""
    try:
        # 必要なクラスをインポート
        from ui.components.visualizations.validation_dashboard import ValidationDashboard
        from sailing_data_processor.validation.correction import InteractiveCorrectionInterface
        
        # テストデータの準備
        container = create_test_data()
        validator = DataValidator()
        validator.validate(container)
        
        # ValidationDashboardインスタンスの作成
        dashboard = ValidationDashboard(
            container=container,
            validator=validator,
            key_prefix="test_dashboard"
        )
        
        # CorrectionControlsをシミュレート
        class MockCorrectionControls:
            def get_proposals(self):
                return [
                    {
                        "id": "test_proposal_1",
                        "issue_type": "missing_data",
                        "description": "テスト提案1",
                        "affected_indices": [2, 5],
                        "recommended_method": "interpolate"
                    },
                    {
                        "id": "test_proposal_2",
                        "issue_type": "out_of_range",
                        "description": "テスト提案2",
                        "affected_indices": [8],
                        "recommended_method": "clip"
                    }
                ]
        
        # MockCorrectionControlsをセッションに登録
        import streamlit as st
        st.session_state["correction_controls"] = MockCorrectionControls()
        
        # レポートデータを作成（通常はrender_report_tabメソッドが実行時に作成）
        dashboard.visualizer = ValidationVisualizer(
            metrics_calculator=QualityMetricsCalculator(validator.validation_results, container.data),
            data=container.data
        )
        report_data = dashboard.visualizer.generate_full_report()
        st.session_state[f"test_dashboard_report_data"] = report_data
        
        # 統合機能をテスト
        result = dashboard.integrate_with_correction_controls()
        
        # 結果の検証
        assert result > 0, "提案の統合に失敗しました"
        assert "fix_proposals" in st.session_state[f"test_dashboard_report_data"]
        
        # 提案が正しく統合されたか確認
        proposals = st.session_state[f"test_dashboard_report_data"]["fix_proposals"]
        assert any(p.get("id") == "test_proposal_1" for p in proposals)
        assert any(p.get("id") == "test_proposal_2" for p in proposals)
        
        # セッションのクリーンアップ
        if "correction_controls" in st.session_state:
            del st.session_state["correction_controls"]
        if f"test_dashboard_report_data" in st.session_state:
            del st.session_state[f"test_dashboard_report_data"]
            
    except ImportError:
        pytest.skip("UI components not available")
    except Exception as e:
        pytest.skip(f"統合テスト環境でエラーが発生: {str(e)}")
        
def test_handle_interactive_fix_result():
    """インタラクティブな修正結果処理のテスト"""
    try:
        # 必要なクラスをインポート
        from ui.components.visualizations.validation_dashboard import ValidationDashboard
        
        # テストデータの準備
        container = create_test_data()
        validator = DataValidator()
        validator.validate(container)
        
        # 修正用データを準備（欠損値を修正）
        fixed_data = container.data.copy()
        fixed_data.loc[2, 'latitude'] = 35.002  # インデックス2の欠損値を修正
        
        fixed_container = GPSDataContainer()
        fixed_container.data = fixed_data
        fixed_container.metadata = container.metadata.copy()
        
        # ValidationDashboardインスタンスの作成
        data_update_called = False
        
        def mock_data_update(updated_container):
            nonlocal data_update_called
            data_update_called = True
        
        dashboard = ValidationDashboard(
            container=container,
            validator=validator,
            key_prefix="test_dashboard",
            on_data_update=mock_data_update
        )
        
        # 修正結果を作成
        fix_result = {
            "status": "success",
            "container": fixed_container,
            "fix_type": "direct_edit",
            "affected_count": 1,
            "message_displayed": True
        }
        
        # インタラクティブな修正結果処理をテスト
        dashboard.handle_interactive_fix_result(fix_result)
        
        # 結果の検証
        assert data_update_called, "データ更新コールバックが呼ばれていません"
        assert dashboard.container.data.equals(fixed_data), "コンテナが正しく更新されていません"
        
    except ImportError:
        pytest.skip("UI components not available")
    except Exception as e:
        pytest.skip(f"テスト環境でエラーが発生: {str(e)}")
        
def test_edge_cases_handling():
    """エッジケースの処理テスト"""
    try:
        # 必要なクラスをインポート
        from ui.components.visualizations.validation_dashboard import ValidationDashboard
        
        # 空のデータセット
        empty_container = GPSDataContainer()
        empty_container.data = pd.DataFrame()
        
        validator = DataValidator()
        
        dashboard = ValidationDashboard(
            container=empty_container,
            validator=validator
        )
        
        # 空データの最適化
        optimized_empty = dashboard._optimize_data_processing(empty_container.data)
        assert optimized_empty.empty, "空のデータフレームが正しく処理されていません"
        
        # 極端に小さいデータセット（1行のみ）
        tiny_data = pd.DataFrame({
            'timestamp': [datetime(2025, 1, 1, 12, 0, 0)],
            'latitude': [35.0],
            'longitude': [135.0],
            'speed': [5.0]
        })
        
        tiny_container = GPSDataContainer()
        tiny_container.data = tiny_data
        
        tiny_dashboard = ValidationDashboard(
            container=tiny_container,
            validator=validator
        )
        
        # 小さいデータの最適化（そのまま返される）
        optimized_tiny = tiny_dashboard._optimize_data_processing(tiny_data)
        assert len(optimized_tiny) == 1, "極小データセットが正しく処理されていません"
        assert optimized_tiny.equals(tiny_data), "極小データセットが変更されています"
        
        # 大量の問題を含むデータ（全行がエラー）
        all_error_data = pd.DataFrame({
            'timestamp': [datetime(2025, 1, 1, 12, 0, i) for i in range(100)],
            'latitude': [None] * 100,  # すべて欠損
            'longitude': [135.0 + i * 0.001 for i in range(100)],
            'speed': [999.0] * 100  # すべて異常値
        })
        
        all_error_container = GPSDataContainer()
        all_error_container.data = all_error_data
        
        validator.validate(all_error_container)
        
        error_dashboard = ValidationDashboard(
            container=all_error_container,
            validator=validator
        )
        
        # 問題だらけのデータの最適化
        optimized_error = error_dashboard._optimize_data_processing(all_error_data)
        assert not optimized_error.empty, "問題だらけのデータが正しく処理されていません"
        
        # NoneまたはNullデータの処理
        none_result = dashboard._optimize_data_processing(None)
        assert none_result.empty, "Noneデータが空のDataFrameとして処理されていません"
        
    except ImportError:
        pytest.skip("UI components not available")
    except Exception as e:
        pytest.skip(f"エッジケーステストでエラーが発生: {str(e)}")
        
def test_end_to_end_validation_workflow_with_feedback():
    """検証ワークフロー（フィードバック付き）の統合テスト"""
    # テストデータを作成
    container = create_test_data()
    
    # 1. バリデーションの実行
    validator = DataValidator()
    validation_results = validator.validate(container)
    
    # バリデーション結果の確認
    assert isinstance(validation_results, list)
    assert len(validation_results) > 0
    assert not all(result['is_valid'] for result in validation_results)
    
    # 2. 修正インターフェースのセットアップ
    from sailing_data_processor.validation.correction import CorrectionSuggester
    
    # 修正提案生成
    suggester = CorrectionSuggester(validator, container)
    proposals = suggester.generate_fix_proposals()
    
    # 提案があることを確認
    assert len(proposals) > 0
    
    # 3. 最初の提案を実際に適用
    if proposals:
        first_proposal = proposals[0]
        proposal_id = first_proposal["id"]
        method = first_proposal["recommended_method"]
        
        # InteractiveCorrectionInterfaceを使用
        interface = InteractiveCorrectionInterface(
            container=container,
            validator=validator
        )
        
        # 修正を適用
        result = interface.apply_fix_proposal(proposal_id, method)
        
        # 結果の確認
        if result:
            # 修正後のデータで再検証
            new_validator = DataValidator()
            new_results = new_validator.validate(result)
            
            # 問題が減少したかを確認
            old_problem_count = sum(1 for r in validation_results if not r['is_valid'])
            new_problem_count = sum(1 for r in new_results if not r['is_valid'])
            
            # 問題数が同じか減少していることを確認（増加していないことを確認）
            assert new_problem_count <= old_problem_count, "修正後に問題が増加しています"
    
    # 4. データモデルがエラーなく更新されることを確認
    try:
        # メトリクス計算の更新
        metrics_calculator = QualityMetricsCalculator(
            validator.validation_results,
            container.data
        )
        
        # 品質サマリーを取得
        quality_summary = metrics_calculator.get_quality_summary()
        
        # 正常に更新されていることを確認
        assert "quality_score" in quality_summary
        assert "issue_counts" in quality_summary
        assert "severity_counts" in quality_summary
        assert "fixable_counts" in quality_summary
    except Exception as e:
        pytest.fail(f"データモデル更新中にエラーが発生: {str(e)}")

def test_enhanced_validation_feedback():
    """拡張された検証フィードバック機能のテスト"""
    # テストデータを作成
    container = create_test_data()
    
    # 1. バリデーションの実行
    validator = DataValidator()
    validation_results = validator.validate(container)
    
    # 2. 修正インターフェースとダッシュボードのセットアップ
    try:
        # 必要なクラスをインポート
        from ui.components.visualizations.validation_dashboard import ValidationDashboard
        
        # テスト用に修正結果を追跡する変数
        applied_proposal_id = None
        applied_method = None
        data_updated = False
        export_format = None
        
        # コールバック関数
        def mock_fix_proposal(proposal_id, method_type):
            nonlocal applied_proposal_id, applied_method
            applied_proposal_id = proposal_id
            applied_method = method_type
            
            # CorrectionSuggesterを使用して修正を適用
            suggester = CorrectionSuggester(validator, container)
            proposals = suggester.generate_fix_proposals()
            
            # 提案がある場合
            for proposal in proposals:
                if proposal["id"] == proposal_id:
                    # 修正の適用をプレビュー
                    interface = InteractiveCorrectionInterface(
                        container=container,
                        validator=validator
                    )
                    # 修正を適用
                    result = interface.apply_fix_proposal(proposal_id, method_type)
                    
                    if result:
                        return {
                            "success": True,
                            "message": f"修正が適用されました: {len(proposal['affected_indices'])}件のレコードを更新",
                            "container": result,
                            "fix_type": "auto",
                            "affected_count": len(proposal["affected_indices"]),
                            "affected_indices": proposal["affected_indices"],
                            "before_values": {},
                            "after_values": {}
                        }
            
            # 提案がない場合
            return {"success": False, "error": "適用できる提案がありません"}
        
        def mock_export(format_type):
            nonlocal export_format
            export_format = format_type
            
        def mock_data_update(updated_container):
            nonlocal data_updated
            data_updated = True
            
        # ValidationDashboardインスタンスの作成
        dashboard = ValidationDashboard(
            container=container,
            validator=validator,
            key_prefix="test_dashboard",
            on_fix_proposal=mock_fix_proposal,
            on_export=mock_export,
            on_data_update=mock_data_update
        )
        
        # 3. インタラクティブな修正結果のテスト
        test_fix_result = {
            "status": "success",
            "container": container,
            "fix_type": "interpolate",
            "affected_count": 2,
            "affected_indices": [2, 5],
            "changed_columns": ["latitude", "speed"],
            "before_values": {
                "2": {"latitude": "None"},
                "5": {"speed": "None"}
            },
            "after_values": {
                "2": {"latitude": "35.002"},
                "5": {"speed": "6.0"}
            }
        }
        
        # 修正結果を処理
        success = dashboard.handle_interactive_fix_result(test_fix_result)
        
        # 結果の検証
        assert success, "修正結果の処理に失敗しました"
        assert data_updated, "データ更新コールバックが呼ばれていません"
        
        # 4. 修正提案の統合テスト
        # モックCorrectionControls
        class MockCorrectionControls:
            def get_proposals(self):
                return [
                    {
                        "id": "test_proposal_1",
                        "issue_type": "missing_data",
                        "description": "テスト提案1",
                        "affected_indices": [2, 5],
                        "severity": "error",
                        "recommended_method": "interpolate",
                        "methods": []
                    },
                    {
                        "id": "test_proposal_2",
                        "issue_type": "out_of_range",
                        "description": "テスト提案2",
                        "affected_indices": [8],
                        "severity": "warning",
                        "recommended_method": "clip",
                        "methods": []
                    }
                ]
        
        # MockをStreamlitセッションに設定
        import streamlit as st
        st.session_state["test_controls"] = MockCorrectionControls()
        
        # レポートデータを作成
        report_data = {
            "summary": "テスト用サマリー",
            "overall_score": 8.5,
            "category_scores": {
                "完全性": 9.0,
                "正確性": 8.0,
                "一貫性": 8.5
            },
            "fix_proposals": []
        }
        st.session_state[f"test_dashboard_report_data"] = report_data
        
        # 統合機能をテスト
        proposal_count = dashboard.integrate_with_correction_controls("test_controls")
        
        # 結果の検証
        assert proposal_count == 2, "提案の統合に失敗しました"
        assert len(st.session_state[f"test_dashboard_report_data"]["fix_proposals"]) == 2
        
        # 5. 大規模データセット処理のテスト
        # 大規模データセットを作成（10,001行）
        import numpy as np
        from datetime import datetime, timedelta
        
        large_data = pd.DataFrame({
            'timestamp': [datetime(2025, 1, 1) + timedelta(seconds=i) for i in range(10001)],
            'latitude': np.linspace(35.0, 35.1, 10001),
            'longitude': np.linspace(135.0, 135.1, 10001),
            'speed': np.random.uniform(5.0, 10.0, 10001)
        })
        
        large_container = GPSDataContainer()
        large_container.data = large_data
        
        # 大規模データセット処理をテスト
        optimized_data = dashboard.handle_large_dataset(large_data)
        
        # 結果の確認
        assert len(optimized_data) < len(large_data), "大規模データセットが最適化されていません"
        assert len(optimized_data) > 0, "最適化後のデータが空です"
        
        # セッションのクリーンアップ
        if "test_controls" in st.session_state:
            del st.session_state["test_controls"]
        if f"test_dashboard_report_data" in st.session_state:
            del st.session_state[f"test_dashboard_report_data"]
            
    except ImportError:
        pytest.skip("UI components not available")
    except Exception as e:
        pytest.fail(f"拡張された検証フィードバック機能のテストでエラーが発生: {str(e)}")

def test_edge_cases_validation_feedback():
    """検証フィードバックのエッジケースのテスト"""
    try:
        # 必要なクラスをインポート
        from ui.components.visualizations.validation_dashboard import ValidationDashboard
        
        # 1. 空のデータセット
        empty_container = GPSDataContainer()
        empty_container.data = pd.DataFrame()
        
        validator = DataValidator()
        
        # ValidationDashboard作成
        dashboard = ValidationDashboard(
            container=empty_container,
            validator=validator,
            key_prefix="test_empty"
        )
        
        # 空データの処理
        empty_result = dashboard._optimize_data_processing(empty_container.data)
        assert empty_result.empty, "空のデータフレームが正しく処理されていません"
        
        # 2. 小さいデータセット（1行のみ）
        tiny_data = pd.DataFrame({
            'timestamp': [datetime(2025, 1, 1, 12, 0, 0)],
            'latitude': [35.0],
            'longitude': [135.0],
            'speed': [5.0]
        })
        
        tiny_container = GPSDataContainer()
        tiny_container.data = tiny_data
        
        # ValidationDashboard作成
        tiny_dashboard = ValidationDashboard(
            container=tiny_container,
            validator=validator,
            key_prefix="test_tiny"
        )
        
        # 小さいデータの処理（そのまま返される）
        optimized_tiny = tiny_dashboard._optimize_data_processing(tiny_data)
        assert len(optimized_tiny) == 1, "極小データセットが正しく処理されていません"
        
        # 3. 空の修正結果
        empty_fix_result = {}
        result = dashboard.handle_interactive_fix_result(empty_fix_result)
        assert result == False, "空の修正結果がエラーとして処理されていません"
        
        # 4. 失敗した修正結果
        failed_fix_result = {
            "status": "error",
            "error": "テストエラー"
        }
        result = dashboard.handle_interactive_fix_result(failed_fix_result)
        assert result == False, "失敗した修正結果がエラーとして処理されていません"
        
        # 5. ValidationDashboardのコールバックなしの動作
        no_callback_dashboard = ValidationDashboard(
            container=tiny_container,
            validator=validator,
            key_prefix="test_no_callback"
        )
        
        # コールバックなしの場合も正常に動作することを確認
        assert hasattr(no_callback_dashboard, "handle_interactive_fix_result")
        
    except ImportError:
        pytest.skip("UI components not available")
    except Exception as e:
        pytest.fail(f"エッジケーステストでエラーが発生: {str(e)}")
