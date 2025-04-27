#!/bin/bash

# セーリング戦略分析システム テスト実行スクリプト v2.0
# このスクリプトはプロジェクトのテストを一括で実行し、詳細なレポートを生成します
# 
# 実行方法:
#   ./run_tests.sh                  - すべてのテストを実行
#   ./run_tests.sh --unit           - 単体テストのみ実行
#   ./run_tests.sh --integration    - 統合テストのみ実行
#   ./run_tests.sh --wind           - 風関連テストのみ実行

# 色の設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# エラーログファイル
ERROR_LOG="test_error.log"
REPORT_FILE="test_report.md"
TEST_LOG_DIR="test_logs"

# テストモード（デフォルトはall）
TEST_MODE="all"

# コマンドライン引数の処理
if [ "$1" == "--unit" ]; then
    TEST_MODE="unit"
    REPORT_FILE="test_report_unit.md"
    ERROR_LOG="test_error_unit.log"
elif [ "$1" == "--integration" ]; then
    TEST_MODE="integration"
    REPORT_FILE="test_report_integration.md"
    ERROR_LOG="test_error_integration.log"
elif [ "$1" == "--wind" ]; then
    TEST_MODE="wind"
    REPORT_FILE="test_report_wind.md"
    ERROR_LOG="test_error_wind.log"
fi

# ロゴの表示
echo -e "${BLUE}"
echo "====================================================="
echo "  セーリング戦略分析システム テスト実行スクリプト  "
echo "====================================================="
echo -e "${NC}"

# 現在の作業ディレクトリを保存
ORIGINAL_DIR=$(pwd)

# プロジェクトのルートディレクトリに移動
cd "$(dirname "$0")"
PROJECT_ROOT=$(pwd)

# エラーログの初期化
if [ -f "$ERROR_LOG" ]; then
    rm "$ERROR_LOG"
fi
touch "$ERROR_LOG"
echo "テスト実行日時: $(date)" > "$ERROR_LOG"
echo "プロジェクトルート: $PROJECT_ROOT" >> "$ERROR_LOG"
echo "環境情報:" >> "$ERROR_LOG"
echo "----------------------------" >> "$ERROR_LOG"
python3 --version >> "$ERROR_LOG" 2>&1
echo "----------------------------" >> "$ERROR_LOG"

# 環境変数の設定（より堅牢な方法で）
export PYTHONPATH="$PROJECT_ROOT:$PROJECT_ROOT/sailing_data_processor:$PYTHONPATH"
# .envファイルがあれば読み込む
if [ -f "$PROJECT_ROOT/.env" ]; then
    echo "Loading environment variables from .env file"
    set -a
    source "$PROJECT_ROOT/.env"
    set +a
fi

echo -e "${YELLOW}テスト環境情報:${NC}"
echo "Project Root: $PROJECT_ROOT"
echo "Python Path: $PYTHONPATH"
echo "Python Version: $(python3 --version)"

# テスト結果のカウンター
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# テスト結果を集計する関数
collect_results() {
    local status=$1
    local test_name=$2
    local log_file=$3
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    if [ $status -eq 0 ]; then
        PASSED_TESTS=$((PASSED_TESTS + 1))
        echo -e "${GREEN}✓ $test_name ... PASSED${NC}"
    else
        FAILED_TESTS=$((FAILED_TESTS + 1))
        echo -e "${RED}✗ $test_name ... FAILED${NC}"
        
        # エラーログに詳細を記録
        echo "====== $test_name FAILED ======" >> "$ERROR_LOG"
        if [ -n "$log_file" ] && [ -f "$log_file" ]; then
            cat "$log_file" >> "$ERROR_LOG"
        else
            echo "No detailed log available" >> "$ERROR_LOG"
        fi
        echo "===============================" >> "$ERROR_LOG"
    fi
}

# セクションヘッダー表示関数
show_section() {
    echo ""
    echo -e "${BLUE}====================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}====================================================${NC}"
}

# 環境チェック関数
check_environment() {
    echo -e "${YELLOW}環境チェック:${NC}"
    
    # インポートテストの実行
    TEST_IMPORT_LOG="test_import.log"
    python3 -c "import sys; print(sys.path); import sailing_data_processor; print('Import successful!')" > "$TEST_IMPORT_LOG" 2>&1
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ 基本インポートチェック PASSED${NC}"
    else
        echo -e "${RED}✗ 基本インポートチェック FAILED${NC}"
        echo "インポートエラーの詳細:" >> "$ERROR_LOG"
        cat "$TEST_IMPORT_LOG" >> "$ERROR_LOG"
        echo "修正方法: PYTHONPATHを確認し、必要に応じて.envファイルを調整してください。" >> "$ERROR_LOG"
    fi
    
    # 必要ならクリーンアップ
    if [ -f "$TEST_IMPORT_LOG" ]; then 
        rm "$TEST_IMPORT_LOG"
    fi
}

# 環境チェックの実行
check_environment

# 基本インポートテスト
show_section "基本インポートテスト"
IMPORT_LOG="import_test.log"
python3 test_import.py > "$IMPORT_LOG" 2>&1
collect_results $? "基本インポートテスト" "$IMPORT_LOG"

# スタンドアロンテスト
show_section "スタンドアロンテスト"

# スタンドアロンテストディレクトリが存在するか確認
if [ -d "standalone_tests" ]; then
    # スタンドアロンテストの実行
    for test_file in standalone_tests/test_*.py; do
        test_name=$(basename "$test_file" .py)
        echo "実行中: $test_name"
        LOG_FILE="${test_name}.log"
        python3 "$test_file" > "$LOG_FILE" 2>&1
        collect_results $? "$test_name" "$LOG_FILE"
        
        # ログファイルのクリーンアップ（オプション）
        if [ -f "$LOG_FILE" ]; then
            rm "$LOG_FILE"
        fi
    done
else
    echo -e "${YELLOW}スタンドアロンテストディレクトリが見つかりません${NC}"
fi

# 直接テストモジュールの実行
show_section "風の移動予測モデルテスト"
WIND_TEST_LOG="wind_propagation_test.log"
python3 verify_wind_propagation.py > "$WIND_TEST_LOG" 2>&1
collect_results $? "風の移動予測モデルテスト" "$WIND_TEST_LOG"

# ログディレクトリの作成
mkdir -p "$TEST_LOG_DIR"

# PyTestの実行（インストールされている場合）
show_section "PyTestテスト"
if command -v pytest &> /dev/null; then
    # テストモードに応じたテスト実行
    PYTEST_LOG="$TEST_LOG_DIR/pytest.log"
    
    if [ "$TEST_MODE" == "unit" ]; then
        echo -e "${YELLOW}単体テストのみ実行します${NC}"
        python3 -m pytest -v -m "unit" --cov=sailing_data_processor --cov-report=term --no-header -s > "$PYTEST_LOG" 2>&1
    elif [ "$TEST_MODE" == "integration" ]; then
        echo -e "${YELLOW}統合テストのみ実行します${NC}"
        python3 -m pytest -v -m "integration" --cov=sailing_data_processor --cov-report=term --no-header -s > "$PYTEST_LOG" 2>&1
    elif [ "$TEST_MODE" == "wind" ]; then
        echo -e "${YELLOW}風関連テストのみ実行します${NC}"
        echo "テスト対象: tests/test_wind_*.py"
        python3 -m pytest tests/test_wind_*.py -v --cov=sailing_data_processor --cov-report=term --no-header -s > "$PYTEST_LOG" 2>&1
    else
        # すべてのテストを実行
        echo -e "${YELLOW}すべてのテストを実行します${NC}"
        python3 -m pytest -v --cov=sailing_data_processor --cov-report=term --cov-config=.coveragerc --no-header -s > "$PYTEST_LOG" 2>&1
    fi
    
    PYTEST_STATUS=$?
    
    if [ $PYTEST_STATUS -eq 0 ]; then
        echo -e "${GREEN}✓ PyTestテスト PASSED${NC}"
    else
        echo -e "${RED}✗ PyTestテスト FAILED${NC}"
        echo "PyTestのエラー詳細を$ERROR_LOGに記録しました"
        echo "====== PyTest FAILED ======" >> "$ERROR_LOG"
        cat "$PYTEST_LOG" >> "$ERROR_LOG"
        echo "===========================" >> "$ERROR_LOG"
    fi
else
    echo -e "${YELLOW}PyTestがインストールされていません${NC}"
fi

# 結果のサマリー
show_section "テスト結果サマリー"
echo "総テスト数: $TOTAL_TESTS"
echo -e "${GREEN}成功: $PASSED_TESTS${NC}"
echo -e "${RED}失敗: $FAILED_TESTS${NC}"

# 成功率の計算と表示
if [ $TOTAL_TESTS -gt 0 ]; then
    SUCCESS_RATE=$((PASSED_TESTS * 100 / TOTAL_TESTS))
    echo -e "成功率: ${YELLOW}$SUCCESS_RATE%${NC}"
    
    # 全テスト成功時のメッセージ
    if [ $FAILED_TESTS -eq 0 ]; then
        echo -e "${GREEN}すべてのテストが成功しました！${NC}"
    else
        echo -e "${YELLOW}エラーログは次のファイルに保存されています: $ERROR_LOG${NC}"
    fi
else
    echo "テストは実行されませんでした"
fi

# ログファイルのクリーンアップ
if [ -f "$IMPORT_LOG" ]; then rm "$IMPORT_LOG"; fi
if [ -f "$WIND_TEST_LOG" ]; then rm "$WIND_TEST_LOG"; fi
if [ -f "$PYTEST_LOG" ]; then rm "$PYTEST_LOG"; fi

# テスト結果レポートの生成
REPORT_FILE="test_report.md"
echo "# セーリング戦略分析システム テスト結果" > "$REPORT_FILE"
echo "実行日時: $(date)" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "## テスト集計" >> "$REPORT_FILE"
echo "- 総テスト数: $TOTAL_TESTS" >> "$REPORT_FILE"
echo "- 成功: $PASSED_TESTS" >> "$REPORT_FILE"
echo "- 失敗: $FAILED_TESTS" >> "$REPORT_FILE"
echo "- 成功率: $SUCCESS_RATE%" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

if [ $FAILED_TESTS -gt 0 ] && [ -f "$ERROR_LOG" ]; then
    echo "## エラー詳細" >> "$REPORT_FILE"
    echo "エラーログ内容:" >> "$REPORT_FILE"
    echo '```' >> "$REPORT_FILE"
    cat "$ERROR_LOG" >> "$REPORT_FILE"
    echo '```' >> "$REPORT_FILE"
fi

echo -e "${GREEN}テスト結果レポートが $REPORT_FILE に生成されました${NC}"

# 元のディレクトリに戻る
cd "$ORIGINAL_DIR"

# 終了コード（失敗したテストがあれば非ゼロ）
exit $FAILED_TESTS
