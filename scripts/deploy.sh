#!/bin/bash
# セーリング戦略分析システム デプロイスクリプト
# 本番環境へのデプロイを自動化します

# 色の定義
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== セーリング戦略分析システム デプロイスクリプト ===${NC}"

# 引数チェック
if [ "$1" != "backend" ] && [ "$1" != "frontend" ] && [ "$1" != "all" ] && [ "$1" != "test" ]; then
  echo -e "${RED}使用法: $0 [backend|frontend|all|test]${NC}"
  echo -e "  backend: バックエンドのみデプロイ"
  echo -e "  frontend: フロントエンドのみデプロイ"
  echo -e "  all: バックエンドとフロントエンドの両方をデプロイ"
  echo -e "  test: デプロイ後のテストを実行"
  exit 1
fi

# プロジェクトのルートディレクトリに移動
cd "$(dirname "$0")/.."
ROOT_DIR=$(pwd)

# 環境変数の読み込み
if [ -f "$ROOT_DIR/.env" ]; then
  echo -e "${BLUE}環境変数ファイルを読み込んでいます...${NC}"
  source "$ROOT_DIR/.env"
fi

# バックエンドのデプロイ
deploy_backend() {
  echo -e "${BLUE}バックエンドのデプロイを開始します...${NC}"
  
  cd "$ROOT_DIR/backend"
  
  # 依存関係のチェック
  if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}requirements.txtが見つかりません。${NC}"
    exit 1
  fi
  
  # ファイルエンコーディングの修正
  echo "ファイルのエンコーディングを修正しています..."
  python3 fix_encoding.py
  
  # 環境変数の設定確認
  echo -e "${YELLOW}バックエンドの環境変数を確認してください:${NC}"
  echo -e "- CORS_ORIGINS: フロントエンドのURL (例: https://sailing-strategy-analyzer.vercel.app)"
  echo -e "- DATABASE_URL: データベース接続URL"
  echo -e "- STORAGE_URL: Supabaseストレージバケットのパス"
  
  # Renderへのデプロイ（Renderのサービスフックを使用）
  echo -e "${GREEN}バックエンドの準備が完了しました${NC}"
  echo -e "${BLUE}Renderウェブサイトで手動デプロイを実行してください:${NC}"
  echo "https://dashboard.render.com/web/srv-xxxxx"
  
  # デプロイ確認
  read -p "Renderのデプロイを開始しましたか？(y/n): " render_deploy
  if [[ $render_deploy =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}デプロイの完了までしばらくお待ちください (通常5〜10分)${NC}"
  else
    echo -e "${YELLOW}Renderでのデプロイを行ってください。${NC}"
  fi
  
  echo -e "${GREEN}バックエンドのデプロイ準備が完了しました${NC}"
}

# フロントエンドのデプロイ
deploy_frontend() {
  echo -e "${BLUE}フロントエンドのデプロイを開始します...${NC}"
  
  cd "$ROOT_DIR/frontend"
  
  # 環境変数の設定確認
  if [ ! -f ".env.local" ] && [ ! -f ".env.production" ]; then
    echo -e "${YELLOW}フロントエンドの環境変数ファイルが見つかりません。新規作成します...${NC}"
    
    # .env.productionの作成
    cat > .env.production << EOF
NEXT_PUBLIC_API_URL=https://sailing-strategy-api.onrender.com
NEXT_PUBLIC_APP_VERSION=0.1.0
NEXT_PUBLIC_APP_NAME=セーリング戦略分析システム
EOF
    
    echo -e "${GREEN}.env.productionファイルを作成しました${NC}"
  fi
  
  # next.config.jsの確認
  if [ ! -f "next.config.js" ]; then
    echo -e "${RED}next.config.jsが見つかりません。${NC}"
    exit 1
  fi
  
  # 依存関係のインストール
  echo "依存関係をインストールしています..."
  npm install
  
  # ビルド
  echo "ビルドを実行しています..."
  npm run build
  
  # ビルド成功の確認
  if [ $? -ne 0 ]; then
    echo -e "${RED}ビルドが失敗しました。エラーを確認してください。${NC}"
    exit 1
  fi
  
  # Vercelへのデプロイ（Vercel CLIがインストールされている場合）
  if command -v vercel &> /dev/null; then
    echo "Vercelにデプロイしています..."
    vercel --prod
    
    if [ $? -eq 0 ]; then
      echo -e "${GREEN}フロントエンドのデプロイが完了しました${NC}"
    else
      echo -e "${RED}Vercelへのデプロイ中にエラーが発生しました。${NC}"
    fi
  else
    echo -e "${BLUE}Vercel CLIがインストールされていないか、ログインされていません${NC}"
    echo -e "${BLUE}以下の手順でVercel CLIをインストールできます:${NC}"
    echo "npm install -g vercel"
    echo "vercel login"
    echo -e "${BLUE}または、Vercelウェブサイトで手動デプロイを実行してください:${NC}"
    echo "https://vercel.com/import/git"
    echo -e "${GREEN}フロントエンドのデプロイ準備が完了しました${NC}"
  fi
}

# デプロイ後のテスト実行
run_deployment_tests() {
  echo -e "${BLUE}デプロイ後のテストを実行します...${NC}"
  
  cd "$ROOT_DIR"
  
  # テストスクリプトの実行
  if [ -f "scripts/test_deployment.py" ]; then
    echo "デプロイ後のテストを実行しています..."
    python3 scripts/test_deployment.py --verbose
    
    if [ $? -eq 0 ]; then
      echo -e "${GREEN}テストが成功しました${NC}"
    else
      echo -e "${RED}テストが失敗しました。デプロイを確認してください。${NC}"
    fi
  else
    echo -e "${RED}テストスクリプトが見つかりません。scripts/test_deployment.pyを作成してください。${NC}"
  fi
}

# 要求に応じてデプロイを実行
if [ "$1" = "backend" ] || [ "$1" = "all" ]; then
  deploy_backend
fi

if [ "$1" = "frontend" ] || [ "$1" = "all" ]; then
  deploy_frontend
fi

if [ "$1" = "test" ]; then
  run_deployment_tests
fi

echo -e "${GREEN}デプロイスクリプトが完了しました${NC}"
echo -e "${BLUE}本番環境の確認を忘れずに行ってください。${NC}"