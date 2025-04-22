/**
 * 連携テスト用スクリプト
 * 
 * バックエンドAPIとの接続テストを行います。
 * Node.jsがインストールされている環境で実行できます。
 * 
 * 使用方法:
 * node test_connection.js [API_URL]
 * 
 * APIのURLが指定されない場合は、環境変数またはデフォルト値が使用されます。
 */

const axios = require('axios');

// 接続先URLの決定
const API_URL = process.argv[2] || process.env.API_URL || 'https://sailing-analyzer-backend.onrender.com';

// ヘルスチェックエンドポイント
const ENDPOINTS = [
  '/health',                // ルートヘルスチェック
  '/api/v1/health',         // API v1 ヘルスチェック
  '/api/v1/health/check',   // 簡易ヘルスチェック
  '/api/v1/projects'        // プロジェクト一覧 (認証必要かもしれません)
];

// 色付きコンソール出力用
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  dim: '\x1b[2m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m'
};

// メイン処理
async function main() {
  console.log(`${colors.bright}${colors.cyan}バックエンド接続テスト${colors.reset}`);
  console.log(`${colors.dim}対象URL: ${API_URL}${colors.reset}`);
  console.log('-'.repeat(50));

  let success = 0;
  let failed = 0;

  for (const endpoint of ENDPOINTS) {
    const url = `${API_URL}${endpoint}`;
    
    try {
      console.log(`${colors.bright}エンドポイント: ${endpoint}${colors.reset}`);
      const startTime = Date.now();
      const response = await axios.get(url, {
        timeout: 10000,
        headers: {
          'Accept': 'application/json',
        }
      });
      const elapsedTime = Date.now() - startTime;
      
      console.log(`${colors.green}✓ 成功 (${elapsedTime}ms)${colors.reset}`);
      console.log(`  ステータス: ${response.status}`);
      
      // レスポンスの内容を簡潔に表示
      if (response.data) {
        if (typeof response.data === 'object') {
          const keys = Object.keys(response.data);
          console.log(`  データキー: ${keys.join(', ')}`);
          
          // ステータスキーがあれば表示
          if (response.data.status) {
            console.log(`  ステータス: ${response.data.status}`);
          }

          // データベース接続情報があれば表示
          if (response.data.database) {
            const db = response.data.database;
            console.log(`  データベース: ${db.status || 'unknown'}`);
            if (db.message) console.log(`  メッセージ: ${db.message}`);
          }
        } else {
          console.log(`  データ: ${JSON.stringify(response.data).substring(0, 100)}...`);
        }
      }
      
      success++;
    } catch (error) {
      failed++;
      console.log(`${colors.red}✗ 失敗${colors.reset}`);
      
      if (error.response) {
        console.log(`  ステータス: ${error.response.status}`);
        console.log(`  メッセージ: ${error.message}`);
        if (error.response.data) {
          console.log(`  エラー詳細: ${JSON.stringify(error.response.data).substring(0, 150)}`);
        }
      } else if (error.request) {
        console.log(`  エラー: レスポンスがありません (タイムアウトまたは接続エラー)`);
        console.log(`  メッセージ: ${error.message}`);
      } else {
        console.log(`  エラー: ${error.message}`);
      }
    }
    
    console.log('-'.repeat(50));
  }

  // 結果サマリー
  console.log(`${colors.bright}テスト結果:${colors.reset}`);
  console.log(`  総テスト数: ${ENDPOINTS.length}`);
  console.log(`  ${colors.green}成功: ${success}${colors.reset}`);
  console.log(`  ${colors.red}失敗: ${failed}${colors.reset}`);
  
  if (failed === 0) {
    console.log(`${colors.green}${colors.bright}全テスト成功！バックエンドは正常に動作しています。${colors.reset}`);
  } else {
    console.log(`${colors.yellow}${colors.bright}一部のテストが失敗しました。エラー詳細を確認してください。${colors.reset}`);
  }
}

// スクリプト実行
main().catch(error => {
  console.error(`${colors.red}実行エラー:${colors.reset}`, error);
  process.exit(1);
});
