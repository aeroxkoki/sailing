#!/bin/bash

# パッチスクリプトの実行ディレクトリを取得
SCRIPT_DIR=$(dirname "$0")
# プロジェクトのルートディレクトリを取得
PROJECT_ROOT=$(cd "$SCRIPT_DIR/../.." && pwd)

# カレントディレクトリをプロジェクトルートに変更
cd "$PROJECT_ROOT" || { echo "Failed to change directory to project root"; exit 1; }

echo "Applying quality metrics patch..."
python3 "$SCRIPT_DIR/fix_quality_metrics.py"
if [ $? -ne 0 ]; then
    echo "Failed to apply quality metrics patch"
    exit 1
fi

echo "Applying missing methods patch..."
python3 "$SCRIPT_DIR/fix_missing_methods.py"
if [ $? -ne 0 ]; then
    echo "Failed to apply missing methods patch"
    exit 1
fi

echo "Running quality metrics tests..."
python3 -m pytest tests/validation/test_quality_metrics.py -v || { echo "Quality metrics tests failed"; exit 1; }

echo "Running quality metrics visualization tests..."
python3 -m pytest tests/test_quality_metrics.py -v || { echo "Quality metrics visualization tests failed"; exit 1; }

echo "All tests passed successfully!"
exit 0
