#!/bin/bash
# セーリング戦略分析システムの修正パッチを適用して実行するスクリプト

# 現在のディレクトリに移動
cd "$(dirname "$0")"

# パッチディレクトリのパスを設定
PATCH_DIR="$(pwd)"
PROJECT_DIR="$(cd ../../ && pwd)"

echo "パッチディレクトリ: $PATCH_DIR"
echo "プロジェクトディレクトリ: $PROJECT_DIR"

echo "======= 修正パッチを適用しています ======="

# 各パッチを実行
echo "1. キャッシュマネージャーの修正を適用..."
python3 "$PATCH_DIR/fix_cache_manager.py"

echo "2. 最適VMG計算機の修正を適用..."
python3 "$PATCH_DIR/fix_optimal_vmg.py"

echo "3. タック識別ロジックの修正を適用..."
python3 "$PATCH_DIR/fix_tack_identification.py"

echo "4. 品質メトリクス可視化機能の修正を適用..."
python3 "$PATCH_DIR/fix_quality_metrics.py"

echo "5. セッションマネージャーのテスト修正を適用..."
python3 "$PATCH_DIR/fix_session_manager.py"

echo "======= 修正が完了しました ======="

# 修正後のテストを実行
echo "======= テストを実行します ======="
cd "$PROJECT_DIR"
python3 -m pytest tests/test_data_model.py::TestCacheFunctions::test_cached_decorator tests/test_optimal_vmg_calculator.py::TestOptimalVMGCalculator::test_find_optimal_twa tests/test_quality_metrics.py::test_visualization tests/test_sailing_data_processor.py::TestSailingDataProcessor::test_anomaly_detection tests/test_sailing_visualizer.py::TestSailingVisualizer::test_create_performance_summary tests/test_tack_identification.py::TestTackIdentification::test_determine_tack_type_basic tests/test_tack_identification.py::TestTackIdentification::test_determine_tack_type_comprehensive tests/test_tack_identification.py::TestTackIdentification::test_determine_tack_type_edge_cases tests/test_wind_estimator_improved.py::TestWindEstimatorImproved::test_categorize_maneuver tests/test_project/test_import_integration.py::TestImportIntegration::test_process_import_result tests/test_project/test_import_integration.py::TestImportIntegration::test_auto_assign_project_by_tag tests/test_project/test_import_integration.py::TestImportIntegration::test_auto_assign_project_by_date tests/test_project/test_import_integration.py::TestImportIntegration::test_apply_project_settings tests/test_project/test_project_storage_advanced.py::TestProjectStorageAdvanced::test_search_projects tests/test_project/test_session_manager.py::TestSessionManager::test_init tests/test_project/test_session_manager.py::TestSessionManager::test_get_all_sessions tests/test_project/test_session_manager.py::TestSessionManager::test_add_session_to_project tests/test_project/test_session_manager.py::TestSessionManager::test_remove_session_from_project tests/test_project/test_session_manager.py::TestSessionManager::test_move_session -v

echo "======= テスト完了 ======="
