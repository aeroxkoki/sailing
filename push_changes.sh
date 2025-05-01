#!/bin/bash
# GitHubに変更を反映するスクリプト

# 現在の日時を取得
current_datetime=$(date "+%Y-%m-%d %H:%M:%S")

# カレントディレクトリを確認
echo "現在のディレクトリ: $(pwd)"

# リポジトリのルートディレクトリに移動（必要に応じて変更）
cd /Users/koki_air/Documents/GitHub/sailing-strategy-analyzer || { echo "リポジトリディレクトリが見つかりません"; exit 1; }
echo "リポジトリディレクトリに移動しました: $(pwd)"

# 変更を確認
echo "変更されたファイル:"
git status -s

# 変更をステージング
git add sailing_data_processor/wind_field_fusion_system.py sailing_data_processor/wind_field_prediction.py tests/test_wind_field_fusion_system.py
echo "変更をステージングしました"

# コミット
git commit -m "循環参照の問題を修正: wind_field_prediction.py から wind_field_fusion_system.py の依存関係を解消 ($current_datetime)"
echo "変更をコミットしました"

# プッシュ
git push origin main
echo "変更をGitHubにプッシュしました"

echo "完了しました"
