#!/bin/bash
# セーリング戦略分析システム - テスト依存関係インストールスクリプト

# 色の設定
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}セーリング戦略分析システム - テスト依存関係インストールスクリプト${NC}"
echo "----------------------------------------"

# Node.jsがインストールされているか確認
if ! command -v node &> /dev/null
then
    echo -e "${RED}エラー: Node.jsがインストールされていません。${NC}"
    echo "https://nodejs.org/ja/ からインストールしてください。"
    exit 1
fi

# npm がインストールされているか確認
if ! command -v npm &> /dev/null
then
    echo -e "${RED}エラー: npmがインストールされていません。${NC}"
    echo "Node.jsと一緒にnpmをインストールしてください。"
    exit 1
fi

# Node.jsとnpmのバージョン表示
echo -e "${GREEN}Node.jsバージョン: $(node -v)${NC}"
echo -e "${GREEN}npmバージョン: $(npm -v)${NC}"

# package.jsonが存在しない場合は作成
if [ ! -f "package.json" ]; then
    echo -e "${YELLOW}package.jsonが見つかりません。新規作成します...${NC}"
    npm init -y
    # package.jsonをテスト用に更新
    node -e "
        const fs = require('fs');
        const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'));
        packageJson.name = 'sailing-strategy-analyzer-tests';
        packageJson.description = 'セーリング戦略分析システム APIテスト';
        packageJson.scripts = {
            ...packageJson.scripts,
            'test:api': 'node test_api_endpoints.js',
            'test:japanese': 'node test_japanese_encoding.js',
            'test:performance': 'node test_api_performance.js',
            'test:all': 'npm run test:api && npm run test:japanese && npm run test:performance'
        };
        fs.writeFileSync('package.json', JSON.stringify(packageJson, null, 2), 'utf8');
    "
    echo -e "${GREEN}package.json を作成しました${NC}"
fi

# 必要なパッケージのインストール
echo -e "${YELLOW}必要なパッケージをインストールしています...${NC}"
npm install axios fs-extra assert

echo -e "${GREEN}インストール完了！${NC}"
echo ""
echo "テストの実行方法:"
echo "  APIエンドポイントテスト:        npm run test:api"
echo "  日本語エンコーディングテスト:   npm run test:japanese"
echo "  パフォーマンステスト:           npm run test:performance"
echo "  すべてのテスト:                 npm run test:all"
echo ""
echo "環境変数の設定:"
echo "  API URLを指定する場合:          API_URL=https://your-api-url npm run test:api"
echo ""
echo -e "${YELLOW}注意: テストを実行する前に、バックエンドが起動していることを確認してください。${NC}"
