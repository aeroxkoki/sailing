/**
 * セーリング戦略分析システム - APIパフォーマンステストスクリプト
 * 
 * API各エンドポイントの応答時間を計測し、パフォーマンスに関する問題を検出します。
 * 異なるデータ量や同時リクエスト時の挙動もテストします。
 */

const axios = require('axios');
const fs = require('fs').promises;

// 設定
const API_BASE_URL = process.env.API_URL || 'http://localhost:8000/api/v1';
const TEST_USER = {
  email: 'test@example.com',
  password: 'testpassword123'
};
const REPORT_FILE = './api_performance_test_report.json';
const DEFAULT_ITERATIONS = 5;  // 各テストの実行回数
const CONCURRENT_REQUESTS = 3; // 同時リクエスト数

// 認証トークンをグローバルに保持
let authToken = null;

// テスト対象エンドポイント
const endpoints = [
  {
    name: 'ヘルスチェック',
    method: 'GET',
    url: '/health',
    auth: false,
    data: null
  },
  {
    name: 'ユーザーログイン',
    method: 'POST',
    url: '/users/login',
    auth: false,
    data: TEST_USER
  },
  {
    name: 'プロジェクト一覧取得',
    method: 'GET',
    url: '/projects',
    auth: true,
    data: null
  },
  {
    name: 'プロジェクト作成',
    method: 'POST',
    url: '/projects',
    auth: true,
    data: {
      name: 'パフォーマンステスト用プロジェクト',
      description: '応答時間の計測のためのテストプロジェクト'
    }
  },
  {
    name: '風向推定',
    method: 'POST',
    url: '/wind-estimation/estimate',
    auth: true,
    data: {
      session_id: 'dummy_session_id' // ダミーID（実際のテストでは存在するIDに置き換える）
    }
  }
];

// ヘルパー関数: リクエストヘッダーの作成
const getHeaders = (withAuth = true) => {
  const headers = {
    'Content-Type': 'application/json; charset=utf-8',
    'Accept': 'application/json'
  };
  
  if (withAuth && authToken) {
    headers['Authorization'] = `Bearer ${authToken}`;
  }
  
  return headers;
};

// 認証処理
async function authenticate() {
  console.log('認証処理を開始...');
  
  try {
    // ログイン
    const startTime = Date.now();
    const loginResponse = await axios.post(
      `${API_BASE_URL}/users/login`, 
      TEST_USER,
      { headers: getHeaders(false) }
    );
    const duration = Date.now() - startTime;
    
    if (loginResponse.status !== 200 || !loginResponse.data.access_token) {
      throw new Error('ログインに失敗しました');
    }
    
    authToken = loginResponse.data.access_token;
    console.log(`✅ ログイン成功 (${duration}ms)`);
    return true;
  } catch (error) {
    console.error('❌ 認証処理に失敗しました:', error.message);
    if (error.response) {
      console.error('レスポンス:', error.response.data);
    }
    return false;
  }
}

// 単一エンドポイントのパフォーマンステスト
async function testEndpointPerformance(endpoint, iterations = DEFAULT_ITERATIONS) {
  console.log(`\n[${endpoint.name}] パフォーマンステスト (${iterations}回)...`);
  
  const results = [];
  
  // ダミーセッションIDを実際のIDに置き換え（セッションが必要なエンドポイントの場合）
  let data = endpoint.data;
  if (data && data.session_id === 'dummy_session_id') {
    try {
      // プロジェクトを作成
      const projectResponse = await axios.post(
        `${API_BASE_URL}/projects`,
        {
          name: `一時プロジェクト_${Date.now()}`,
          description: 'パフォーマンステスト用'
        },
        { headers: getHeaders() }
      );
      
      const projectId = projectResponse.data.id;
      
      // セッションを作成
      const sessionResponse = await axios.post(
        `${API_BASE_URL}/sessions`,
        {
          name: `一時セッション_${Date.now()}`,
          description: 'パフォーマンステスト用',
          project_id: projectId,
          date: new Date().toISOString().split('T')[0]
        },
        { headers: getHeaders() }
      );
      
      data = { ...data, session_id: sessionResponse.data.id };
      
      console.log(`  セッションID ${sessionResponse.data.id} を使用します`);
    } catch (error) {
      console.warn('  セッション作成に失敗しました。ダミーIDのまま続行します');
    }
  }
  
  // 指定回数のテスト実行
  for (let i = 0; i < iterations; i++) {
    try {
      const startTime = Date.now();
      
      let response;
      if (endpoint.method === 'GET') {
        response = await axios.get(
          `${API_BASE_URL}${endpoint.url}`,
          { 
            headers: getHeaders(endpoint.auth)
          }
        );
      } else if (endpoint.method === 'POST') {
        response = await axios.post(
          `${API_BASE_URL}${endpoint.url}`,
          data,
          { 
            headers: getHeaders(endpoint.auth)
          }
        );
      }
      
      const duration = Date.now() - startTime;
      
      results.push({
        iteration: i + 1,
        duration,
        status: response.status,
        dataSize: JSON.stringify(response.data).length
      });
      
      console.log(`  反復 ${i+1}: ${duration}ms, ステータス: ${response.status}, データサイズ: ${JSON.stringify(response.data).length} バイト`);
    } catch (error) {
      results.push({
        iteration: i + 1,
        error: error.message,
        status: error.response ? error.response.status : 'N/A'
      });
      
      console.error(`  反復 ${i+1} 失敗: ${error.message}`);
    }
    
    // 連続リクエストによるレート制限を回避するための短い待機
    if (i < iterations - 1) {
      await new Promise(resolve => setTimeout(resolve, 100));
    }
  }
  
  // 結果の分析
  const successfulResults = results.filter(r => !r.error);
  let summary = {
    endpoint: endpoint.name,
    url: endpoint.url,
    method: endpoint.method,
    iterations,
    successRate: `${(successfulResults.length / iterations * 100).toFixed(2)}%`,
    results
  };
  
  if (successfulResults.length > 0) {
    const durations = successfulResults.map(r => r.duration);
    summary = {
      ...summary,
      avgDuration: durations.reduce((sum, d) => sum + d, 0) / durations.length,
      minDuration: Math.min(...durations),
      maxDuration: Math.max(...durations),
      medianDuration: calculateMedian(durations)
    };
    
    console.log(`  結果サマリー:`);
    console.log(`    平均応答時間: ${summary.avgDuration.toFixed(2)}ms`);
    console.log(`    最小応答時間: ${summary.minDuration}ms`);
    console.log(`    最大応答時間: ${summary.maxDuration}ms`);
    console.log(`    中央値応答時間: ${summary.medianDuration}ms`);
    console.log(`    成功率: ${summary.successRate}`);
  } else {
    console.error(`  テスト失敗: 成功したリクエストがありません`);
  }
  
  return summary;
}

// 同時リクエストのパフォーマンステスト
async function testConcurrentRequests(endpoint, concurrentCount = CONCURRENT_REQUESTS) {
  console.log(`\n[${endpoint.name}] 同時リクエストテスト (${concurrentCount}件同時)...`);
  
  // 同時リクエストの準備
  const requests = [];
  for (let i = 0; i < concurrentCount; i++) {
    requests.push((() => {
      const startTime = Date.now();
      
      let request;
      if (endpoint.method === 'GET') {
        request = axios.get(
          `${API_BASE_URL}${endpoint.url}`,
          { 
            headers: getHeaders(endpoint.auth)
          }
        );
      } else if (endpoint.method === 'POST') {
        request = axios.post(
          `${API_BASE_URL}${endpoint.url}`,
          endpoint.data,
          { 
            headers: getHeaders(endpoint.auth)
          }
        );
      }
      
      return request
        .then(response => {
          const duration = Date.now() - startTime;
          return {
            requestId: i + 1,
            duration,
            status: response.status,
            dataSize: JSON.stringify(response.data).length
          };
        })
        .catch(error => {
          return {
            requestId: i + 1,
            error: error.message,
            status: error.response ? error.response.status : 'N/A'
          };
        });
    })());
  }
  
  // 全リクエストを同時に実行
  const results = await Promise.all(requests);
  
  // 結果の分析
  const successfulResults = results.filter(r => !r.error);
  let summary = {
    endpoint: endpoint.name,
    url: endpoint.url,
    method: endpoint.method,
    concurrentCount,
    successRate: `${(successfulResults.length / concurrentCount * 100).toFixed(2)}%`,
    results
  };
  
  if (successfulResults.length > 0) {
    const durations = successfulResults.map(r => r.duration);
    summary = {
      ...summary,
      avgDuration: durations.reduce((sum, d) => sum + d, 0) / durations.length,
      minDuration: Math.min(...durations),
      maxDuration: Math.max(...durations),
      medianDuration: calculateMedian(durations)
    };
    
    console.log(`  結果サマリー:`);
    console.log(`    平均応答時間: ${summary.avgDuration.toFixed(2)}ms`);
    console.log(`    最小応答時間: ${summary.minDuration}ms`);
    console.log(`    最大応答時間: ${summary.maxDuration}ms`);
    console.log(`    中央値応答時間: ${summary.medianDuration}ms`);
    console.log(`    成功率: ${summary.successRate}`);
    
    for (const result of results) {
      if (result.error) {
        console.error(`  リクエスト ${result.requestId} 失敗: ${result.error}`);
      } else {
        console.log(`  リクエスト ${result.requestId}: ${result.duration}ms, ステータス: ${result.status}`);
      }
    }
  } else {
    console.error(`  テスト失敗: 成功したリクエストがありません`);
  }
  
  return summary;
}

// ヘルパー関数: 中央値の計算
function calculateMedian(numbers) {
  if (numbers.length === 0) return 0;
  
  const sorted = [...numbers].sort((a, b) => a - b);
  const middle = Math.floor(sorted.length / 2);
  
  if (sorted.length % 2 === 0) {
    return (sorted[middle - 1] + sorted[middle]) / 2;
  } else {
    return sorted[middle];
  }
}

// テスト結果の保存
async function saveResults(results) {
  try {
    // システム情報の取得
    const systemInfo = {
      timestamp: new Date().toISOString(),
      apiUrl: API_BASE_URL,
      userAgent: `Node.js ${process.version}`
    };
    
    // 結果データの作成
    const reportData = {
      systemInfo,
      results
    };
    
    // ファイルに保存
    await fs.writeFile(REPORT_FILE, JSON.stringify(reportData, null, 2), 'utf8');
    console.log(`\n✅ テスト結果を ${REPORT_FILE} に保存しました`);
    
    return reportData;
  } catch (error) {
    console.error(`\n❌ テスト結果の保存に失敗しました: ${error.message}`);
    return null;
  }
}

// メイン実行関数
async function runTests() {
  console.log('セーリング戦略分析システム APIパフォーマンステスト開始');
  console.log('API URL:', API_BASE_URL);
  console.log('日時:', new Date().toISOString());
  console.log('----------------------------------------');
  
  // 結果を格納する配列
  const results = {
    serialTests: [],
    concurrentTests: []
  };
  
  try {
    // 認証（後続のテストで使用するため）
    const authenticated = await authenticate();
    if (!authenticated && endpoints.some(e => e.auth)) {
      console.warn('⚠️ 認証に失敗しました。認証が必要なエンドポイントのテストはスキップされる可能性があります。');
    }
    
    // シリアルテスト（各エンドポイントを順番にテスト）
    console.log('\n==== シリアルテスト（エンドポイント個別パフォーマンステスト） ====');
    for (const endpoint of endpoints) {
      // 認証が必要だが認証に失敗している場合はスキップ
      if (endpoint.auth && !authenticated) {
        console.warn(`⚠️ ${endpoint.name} はスキップされます（認証に失敗しているため）`);
        continue;
      }
      
      const result = await testEndpointPerformance(endpoint);
      results.serialTests.push(result);
    }
    
    // 同時リクエストテスト（選択されたエンドポイントを同時に呼び出し）
    console.log('\n==== 同時リクエストテスト ====');
    // 同時リクエストテストを行うエンドポイントを選択（GETエンドポイントが適切）
    const concurrentTestEndpoints = endpoints.filter(e => e.method === 'GET' && (!e.auth || authenticated));
    
    for (const endpoint of concurrentTestEndpoints) {
      const result = await testConcurrentRequests(endpoint);
      results.concurrentTests.push(result);
    }
    
    // 結果の保存
    await saveResults(results);
    
    console.log('\n----------------------------------------');
    console.log('✅ すべてのパフォーマンステストが完了しました');
    console.log('実行完了時間:', new Date().toISOString());
  } catch (error) {
    console.error('\n----------------------------------------');
    console.error('❌ テスト実行中にエラーが発生しました:', error.message);
    console.error('テスト失敗時間:', new Date().toISOString());
    
    // 途中までの結果を保存
    if (results.serialTests.length > 0 || results.concurrentTests.length > 0) {
      await saveResults(results);
    }
    
    process.exit(1);
  }
}

// テスト実行
runTests();
