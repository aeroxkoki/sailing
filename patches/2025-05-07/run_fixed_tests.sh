#\!/bin/bash
# セーリング戦略分析システム - 修正適用・テスト実行スクリプト
# 作成日: 2025-05-07

# 色の定義
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# プロジェクトルートディレクトリ
PROJECT_ROOT="/Users/koki_air/Documents/GitHub/sailing-strategy-analyzer"

# パッチディレクトリ
PATCH_DIR="${PROJECT_ROOT}/patches/2025-05-07"

echo -e "${BLUE}=======================================${NC}"
echo -e "${BLUE}セーリング戦略分析システム - バグ修正スクリプト${NC}"
echo -e "${BLUE}=======================================${NC}"

# 1. キャッシュマネージャーの修正
echo -e "\n${YELLOW}1. キャッシュマネージャーの修正を適用します...${NC}"
python3 "${PATCH_DIR}/fix_missing_methods.py" 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ キャッシュマネージャーの修正が完了しました${NC}"
else
    echo -e "${RED}✗ キャッシュマネージャーの修正に失敗しました${NC}"
fi

# 2. マップ表示クラスの修正
echo -e "\n${YELLOW}2. マップ表示クラスの修正を適用します...${NC}"
python3 "${PATCH_DIR}/fix_visualization.py" 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ マップ表示クラスの修正が完了しました${NC}"
else
    echo -e "${RED}✗ マップ表示クラスの修正に失敗しました${NC}"
fi

# 3. 最適VMG計算クラスの修正
echo -e "\n${YELLOW}3. 最適VMG計算クラスの修正を適用します...${NC}"
python3 "${PATCH_DIR}/fix_optimal_vmg.py" 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ 最適VMG計算クラスの修正が完了しました${NC}"
else
    echo -e "${RED}✗ 最適VMG計算クラスの修正に失敗しました${NC}"
fi

# 4. 品質メトリクスクラスの修正
echo -e "\n${YELLOW}4. 品質メトリクスクラスの修正を適用します...${NC}"
python3 "${PATCH_DIR}/fix_quality_metrics.py" 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ 品質メトリクスクラスの修正が完了しました${NC}"
else
    echo -e "${RED}✗ 品質メトリクスクラスの修正に失敗しました${NC}"
fi

# 5. セッションマネージャーの修正
echo -e "\n${YELLOW}5. セッションマネージャーの修正を適用します...${NC}"
python3 "${PATCH_DIR}/fix_session_manager.py" 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ セッションマネージャーの修正が完了しました${NC}"
else
    echo -e "${RED}✗ セッションマネージャーの修正に失敗しました${NC}"
fi

# テストの実行
echo -e "\n${YELLOW}修正されたコードのテストを実行します...${NC}"
cd "${PROJECT_ROOT}"
python3 -m pytest tests/test_data_model.py::TestCacheFunctions::test_cached_decorator tests/test_map_display.py::TestSailingMapDisplay::test_create_map tests/test_optimal_vmg_calculator.py::TestOptimalVMGCalculator::test_find_optimal_twa tests/test_quality_metrics.py::test_quality_metrics tests/test_quality_metrics.py::test_visualization tests/test_project/test_session_manager.py -v

echo -e "\n${BLUE}=======================================${NC}"
echo -e "${BLUE}修正およびテスト実行が完了しました${NC}"
echo -e "${BLUE}=======================================${NC}"

# GitHubへの変更のプッシュ
echo -e "\n${YELLOW}変更をGitHubにプッシュしますか？ (y/n)${NC}"
read -r PUSH_CHANGES

if [ "$PUSH_CHANGES" = "y" ]; then
    echo -e "\n${YELLOW}変更をコミットしてプッシュします...${NC}"
    cd "${PROJECT_ROOT}"
    git add .
    git commit -m "Fix: キャッシュマネージャー、マップ表示、VMG計算、品質メトリクス、セッションマネージャーの修正"
    git push origin main
    echo -e "${GREEN}✓ 変更がプッシュされました${NC}"
else
    echo -e "${YELLOW}変更はローカルに保存されました。後で手動でプッシュしてください。${NC}"
fi

echo -e "\n${GREEN}スクリプトの実行が完了しました。${NC}"
