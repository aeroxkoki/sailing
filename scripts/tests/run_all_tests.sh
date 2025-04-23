#!/bin/bash
# セーリング戦略分析システム - 全テスト実行スクリプト

# 色の設定
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
TEST_DIR="${SCRIPT_DIR}"
REPORT_DIR="${TEST_DIR}/reports"
API_URL=${API_URL:-"http://localhost:8000/api/v1"}

# タイムスタンプ付きのレポートディレクトリを作成
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
CURRENT_REPORT_DIR="${REPORT_DIR}/${TIMESTAMP}"
mkdir -p "${CURRENT_REPORT_DIR}"

echo -e "${YELLOW}セーリング戦略分析システム - 全テスト実行スクリプト${NC}"
echo "----------------------------------------"
echo "テストディレクトリ: ${TEST_DIR}"
echo "レポートディレクトリ: ${CURRENT_REPORT_DIR}"
echo "API URL: ${API_URL}"
echo "開始時間: $(date)"
echo "----------------------------------------"

# バックエンドが起動しているか確認
echo -e "${YELLOW}バックエンドの疎通確認を行っています...${NC}"
HEALTH_CHECK=$(curl -s -o /dev/null -w "%{http_code}" "${API_URL}/health" || echo "Error")

if [ "$HEALTH_CHECK" != "200" ]; then
  echo -e "${RED}エラー: バックエンドに接続できません (ステータス: ${HEALTH_CHECK})${NC}"
  echo "バックエンドが起動しているか確認してください。"
  exit 1
fi

echo -e "${GREEN}バックエンドへの接続を確認しました。${NC}"

# テストのエラーを検出するためのフラグ
error_flag=0

# 1. APIエンドポイントテスト
echo -e "\n${YELLOW}1. APIエンドポイントテストを実行しています...${NC}"
cd "${TEST_DIR}"
API_URL="${API_URL}" node test_api_endpoints.js > "${CURRENT_REPORT_DIR}/api_endpoints_test.log" 2>&1
if [ $? -ne 0 ]; then
  echo -e "${RED}❌ APIエンドポイントテストが失敗しました。${NC}"
  error_flag=1
else
  echo -e "${GREEN}✅ APIエンドポイントテスト成功${NC}"
fi

# 2. 日本語エンコーディングテスト
echo -e "\n${YELLOW}2. 日本語エンコーディングテストを実行しています...${NC}"
API_URL="${API_URL}" node test_japanese_encoding.js > "${CURRENT_REPORT_DIR}/japanese_encoding_test.log" 2>&1
if [ $? -ne 0 ]; then
  echo -e "${RED}❌ 日本語エンコーディングテストが失敗しました。${NC}"
  error_flag=1
else
  echo -e "${GREEN}✅ 日本語エンコーディングテスト成功${NC}"
fi

# 日本語エンコーディングテスト結果をレポートディレクトリにコピー
if [ -f "japanese_encoding_test_report.json" ]; then
  cp "japanese_encoding_test_report.json" "${CURRENT_REPORT_DIR}/"
fi

# 3. パフォーマンステスト
echo -e "\n${YELLOW}3. パフォーマンステストを実行しています...${NC}"
API_URL="${API_URL}" node test_api_performance.js > "${CURRENT_REPORT_DIR}/api_performance_test.log" 2>&1
if [ $? -ne 0 ]; then
  echo -e "${RED}❌ パフォーマンステストが失敗しました。${NC}"
  error_flag=1
else
  echo -e "${GREEN}✅ パフォーマンステスト成功${NC}"
fi

# パフォーマンステスト結果をレポートディレクトリにコピー
if [ -f "api_performance_test_report.json" ]; then
  cp "api_performance_test_report.json" "${CURRENT_REPORT_DIR}/"
fi

# テスト結果サマリーの作成
echo -e "\n${YELLOW}テスト結果サマリーを作成しています...${NC}"

# 結果をJSONとしてファイルに保存
cat > "${CURRENT_REPORT_DIR}/test_summary.json" << EOL
{
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "apiUrl": "${API_URL}",
  "tests": {
    "apiEndpoints": {
      "status": $([ $error_flag -eq 0 ] && echo "\"success\"" || echo "\"failure\""),
      "logFile": "api_endpoints_test.log"
    },
    "japaneseEncoding": {
      "status": $([ $error_flag -eq 0 ] && echo "\"success\"" || echo "\"failure\""),
      "logFile": "japanese_encoding_test.log",
      "reportFile": "japanese_encoding_test_report.json"
    },
    "performance": {
      "status": $([ $error_flag -eq 0 ] && echo "\"success\"" || echo "\"failure\""),
      "logFile": "api_performance_test.log",
      "reportFile": "api_performance_test_report.json"
    }
  },
  "overall": {
    "status": $([ $error_flag -eq 0 ] && echo "\"success\"" || echo "\"failure\"")
  }
}
EOL

# 結果サマリー表示
echo -e "\n${YELLOW}テスト実行結果${NC}"
echo "----------------------------------------"
echo "APIエンドポイントテスト: $([ $error_flag -eq 0 ] && echo "✅ 成功" || echo "❌ 失敗")"
echo "日本語エンコーディングテスト: $([ $error_flag -eq 0 ] && echo "✅ 成功" || echo "❌ 失敗")"
echo "パフォーマンステスト: $([ $error_flag -eq 0 ] && echo "✅ 成功" || echo "❌ 失敗")"
echo "----------------------------------------"
echo "テスト結果レポート: ${CURRENT_REPORT_DIR}"
echo "終了時間: $(date)"

# 最終的な終了ステータスを返す
if [ $error_flag -eq 0 ]; then
  echo -e "${GREEN}すべてのテストが成功しました。${NC}"
  exit 0
else
  echo -e "${RED}一部のテストが失敗しました。詳細はログファイルを確認してください。${NC}"
  exit 1
fi
