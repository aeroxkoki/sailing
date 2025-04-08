#!/bin/bash
# インポートウィザードテスト実行スクリプト

echo "インポートウィザードテストを開始します..."
cd "$(dirname "$0")"
streamlit run test_import_wizard.py
