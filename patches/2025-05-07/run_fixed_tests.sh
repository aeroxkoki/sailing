#\!/bin/bash

# 修正したテストを実行するスクリプト

# 色の設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# エラーログファイル
ERROR_LOG="test_details.log"

# 環境変数の設定
export PYTHONPATH="$(pwd):$(pwd)/sailing_data_processor:$PYTHONPATH"

# .envファイルがあれば読み込む
if [ -f ".env" ]; then
    echo "Loading environment variables from .env file"
    set -a
    source ".env"
    set +a
fi

echo -e "${BLUE}=====================================================${NC}"
echo -e "${BLUE}  修正したテストの実行  ${NC}"
echo -e "${BLUE}=====================================================${NC}"

# テスト結果を保存するファイル
touch "$ERROR_LOG"
echo "テスト実行日時: $(date)" > "$ERROR_LOG"

# セッションマネージャーのテスト
echo -e "${YELLOW}セッションマネージャーのテスト:${NC}"
python3 -m pytest tests/test_project/test_session_manager.py::TestSessionManager::test_update_session_status tests/test_project/test_session_manager.py::TestSessionManager::test_update_session_category tests/test_project/test_session_manager.py::TestSessionManager::test_update_session_tags -v >> "$ERROR_LOG" 2>&1
SESSION_STATUS=$?

if [ $SESSION_STATUS -eq 0 ]; then
    echo -e "${GREEN}✓ セッションマネージャーのテスト PASSED${NC}"
else
    echo -e "${RED}✗ セッションマネージャーのテスト FAILED${NC}"
fi

# 品質メトリクスのテスト
echo -e "${YELLOW}品質メトリクスのテスト:${NC}"
python3 -m pytest tests/validation/test_quality_metrics.py::test_precision_and_validity_scores tests/validation/test_quality_metrics.py::test_calculate_uniformity_score tests/validation/test_quality_metrics.py::test_calculate_spatial_quality_scores tests/validation/test_quality_metrics.py::test_calculate_temporal_quality_scores -v >> "$ERROR_LOG" 2>&1
QUALITY_STATUS=$?

if [ $QUALITY_STATUS -eq 0 ]; then
    echo -e "${GREEN}✓ 品質メトリクスのテスト PASSED${NC}"
else
    echo -e "${RED}✗ 品質メトリクスのテスト FAILED${NC}"
fi

# 視覚化のテスト
echo -e "${YELLOW}視覚化のテスト:${NC}"
python3 -m pytest tests/validation/test_visualization.py::test_render_details_section -v >> "$ERROR_LOG" 2>&1
VIZ_STATUS=$?

if [ $VIZ_STATUS -eq 0 ]; then
    echo -e "${GREEN}✓ 視覚化のテスト PASSED${NC}"
else
    echo -e "${RED}✗ 視覚化のテスト FAILED${NC}"
fi

# 結果の要約
echo -e "${BLUE}=====================================================${NC}"
echo -e "${BLUE}  テスト結果  ${NC}"
echo -e "${BLUE}=====================================================${NC}"

if [ $SESSION_STATUS -eq 0 ] && [ $QUALITY_STATUS -eq 0 ] && [ $VIZ_STATUS -eq 0 ]; then
    echo -e "${GREEN}すべてのテストが成功しました！${NC}"
else
    echo -e "${RED}一部のテストが失敗しました${NC}"
    echo -e "${YELLOW}詳細は $ERROR_LOG を確認してください${NC}"
fi

# 全体のステータスを返す
if [ $SESSION_STATUS -eq 0 ] && [ $QUALITY_STATUS -eq 0 ] && [ $VIZ_STATUS -eq 0 ]; then
    exit 0
else
    exit 1
fi
