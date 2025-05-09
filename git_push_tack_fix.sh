#!/bin/bash
# タック識別ロジックの修正をGitHubにプッシュするスクリプト

# カレントディレクトリをプロジェクトルートに移動
cd "$(dirname "$0")" || { echo "ディレクトリの移動に失敗しました"; exit 1; }

# 修正を適用
echo "タック識別ロジックの修正を適用しています..."
python3 direct_tack_fix.py || { echo "修正の適用に失敗しました"; exit 1; }

# テストを実行
echo "修正後のテストを実行しています..."
python3 run_tests_post_fix.py || { echo "テストが失敗しました"; exit 1; }

# Gitコマンドの実行
echo "GitHubに変更をプッシュしています..."

# 変更をステージング
git add sailing_data_processor/strategy/strategy_detector_utils.py
git add direct_tack_fix.py
git add run_tests_post_fix.py
git add git_push_tack_fix.sh

# コミット
git commit -m "タック識別ロジックの修正: 特殊ケース (90, 90) の対応、風向風速推定の改善"

# プッシュ
git push origin HEAD

echo "完了しました！"
