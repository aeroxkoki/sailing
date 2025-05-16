#!/bin/bash

# スクリプトが存在するディレクトリをプロジェクトルートとして使用
cd "$(dirname "$0")"

# 変更をステージングエリアに追加
git add .github/workflows/frontend-ci.yml
git add vercel.json
git add frontend/vercel.json
git add manual_deploy.sh

# 変更をコミット
git commit -m "Fix Vercel deployment by simplifying configuration and workflow"

# 変更をプッシュ（mainブランチ）
git push origin main

echo "Vercel deployment final fix pushed to GitHub"
