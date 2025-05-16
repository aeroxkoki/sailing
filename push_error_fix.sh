#!/bin/bash

# 修正したファイルをGitに追加
git add frontend/src/components/map/StrategyPointLayer.tsx
git add frontend/src/components/map/TrackLayer.tsx
git add frontend/src/components/map/WindLayer.tsx
git add frontend/src/pages/_error.tsx

# コミットを作成
git commit -m "Fix critical Next.js error and React Hook dependencies"

# GitHubにプッシュ
git push origin main

echo "変更をGitHubにプッシュしました"
