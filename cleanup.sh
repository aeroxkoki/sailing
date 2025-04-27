#!/bin/bash
# セーリング戦略分析システム - リポジトリ整理スクリプト

echo "リポジトリの整理を開始します..."

# 1. アーカイブと古いディレクトリを削除
echo "不要なディレクトリを削除中..."
rm -rf archive
rm -rf sailing_strategy_analyzer.egg-info
rm -rf benchmark_results
rm -rf test_venv

# 2. バックアップファイルを削除
echo "バックアップファイルを削除中..."
find . -name "*.bak" -type f -delete

# 3. エンコーディング修正スクリプトを削除
echo "一時的なエンコーディングスクリプトを削除中..."
rm -f add_encoding_declaration.py
rm -f better_syntax_fix.py
rm -f check_binary_content.py
rm -f check_encoding.py
rm -f check_encoding_issues.py
rm -f clean_encoding_once_for_all.py
rm -f encoding_checker.py
rm -f fix_all_encodings.py
rm -f fix_encoding.py
rm -f fix_encoding_issues.py
rm -f fix_file_encoding.py
rm -f fix_missing_braces.py
rm -f fix_module_encodings.py
rm -f fix_module_imports.py
rm -f fix_null_bytes.py
rm -f fix_nulls.py
rm -f fix_python_syntax.py
rm -f null_byte_remover.sh
rm -f remove_nulls.py
rm -f remove_nulls.sh
rm -f recreate_files.py
rm -f restore_file.py

# 4. デバッグ/テストの一時ファイルを削除
echo "デバッグ/テストファイルを削除中..."
rm -f debug_parse_issue.py
rm -f debug_strategy_detector.py
rm -f debug_strategy_detector.log
rm -f debug_test.py
rm -f anomaly_test.py
rm -f edge_case_tests.py
rm -f edge_case_tests.log
rm -f edge_case_test_results.json
rm -f extended_test.py
rm -f minimal_test.py
rm -f simple_test.py
rm -f test_collection_debug.py
rm -f test_demo_import.py
rm -f test_element_type.py
rm -f test_error.log
rm -f test_error_wind.log
rm -f test_details.log
rm -f test_imports.py
rm -f test_minimal.py
rm -f test_module_imports.py
rm -f test_propagation.py
rm -f test_propagation.log
rm -f test_wind_field_methods.py
rm -f verify_wind_propagation.py
rm -f pytest.log
rm -f streamlit_cloud.log
rm -f app.log

# 5. テストデータをtests/resourcesに移動
echo "テストデータを整理中..."
mkdir -p tests/resources
cp -r test_data/* tests/resources/
rm -rf test_data

echo "リポジトリ整理が完了しました。"
