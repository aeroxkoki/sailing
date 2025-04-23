/**
 * セーリング戦略分析システム - 日本語エンコーディングテストスクリプト
 * 
 * 様々な日本語文字（漢字、ひらがな、カタカナ、半角カナ、特殊文字）を含むリクエストを生成し、
 * APIエンドポイントへのリクエスト送信と応答の確認を行います。
 */

const axios = require('axios');
const fs = require('fs').promises;
const assert = require('assert').strict;

// 設定
const API_BASE_URL = process.env.API_URL || 'http://localhost:8000/api/v1';
const TEST_USER = {
  email: 'test@example.com',
  password: 'testpassword123'
};
const REPORT_FILE = './japanese_encoding_test_report.json';

// 認証トークンをグローバルに保持
let authToken = null;

// 日本語テストデータセット
const japaneseTestDataSets = [
  {
    name: '基本的な日本語',
    data: 'こんにちは世界'
  },
  {
    name: '漢字',
    data: '漢字テスト：伝統的な日本の文字。複雑で美しい。'
  },
  {
    name: 'ひらがな',
    data: 'ひらがなのテスト：あいうえおかきくけこさしすせそたちつてと'
  },
  {
    name: 'カタカナ',
    data: 'カタカナのテスト：アイウエオカキクケコサシスセソタチツテト'
  },
  {
    name: '半角カナ',
    data: '半角カナのテスト：ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄ'
  },
  {
    name: '記号と数字',
    data: '記号と数字：①②③、【】「」『』〒→←↑↓■◆●★☆♪♭♯'
  },
  {
    name: '絵文字',
    data: '絵文字テスト：🌸🌺🌼🌟🌠🌞🌈🌊🎉🎊🎁🎂🎄🎵🎸'
  },
  {
    name: '複合文字',
    data: '複合文字テスト：がぎぐげご（濁点）、ぱぴぷぺぽ（半濁点）'
  },
  {
    name: '長文テキスト',
    data: `これは日本語の長文テキストテストです。様々な種類の文字を含んでいます。
    漢字（伝統的な日本の文字）、ひらがな（あいうえお）、カタカナ（アイウエオ）、
    半角カナ（ｱｲｳｴｵ）、記号（【】「」『』）、数字（①②③）、絵文字（🌸🎉）などを
    組み合わせて、エンコーディングの問題が発生しないかをテストします。
    特に長文の場合、文字化けやエンコーディングの問題が発生しやすいため、
    このようなテストデータを用意しました。`
  },
  {
    name: '制御文字を含むテキスト',
    data: 'テスト\n改行\tタブ\r復帰'
  },
  {
    name: '全角英数字',
    data: '全角英数字：ＡＢＣａｂｃ１２３'
  },
  {
    name: '機種依存文字',
    data: '機種依存文字：㍻㍼㍽㍾㌀㌁㌂㌃㌄'
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

// ヘルパー関数: レスポンスデータの検証
const verifyJapaneseText = (original, received) => {
  // 完全一致チェック
  const exactMatch = original === received;
  
  // 文字数チェック
  const lengthMatch = original.length === received.length;
  
  // 異なる文字のリスト
  const diffChars = [];
  if (!exactMatch) {
    const minLength = Math.min(original.length, received.length);
    for (let i = 0; i < minLength; i++) {
      if (original[i] !== received[i]) {
        diffChars.push({
          position: i,
          original: original[i],
          originalCode: original.charCodeAt(i).toString(16),
          received: received[i],
          receivedCode: received.charCodeAt(i).toString(16)
        });
      }
    }
    
    // 長さが異なる場合、余分または不足している文字を記録
    if (original.length > received.length) {
      for (let i = received.length; i < original.length; i++) {
        diffChars.push({
          position: i,
          original: original[i],
          originalCode: original.charCodeAt(i).toString(16),
          received: '(不足)',
          receivedCode: ''
        });
      }
    } else if (received.length > original.length) {
      for (let i = original.length; i < received.length; i++) {
        diffChars.push({
          position: i,
          original: '(余分)',
          originalCode: '',
          received: received[i],
          receivedCode: received.charCodeAt(i).toString(16)
        });
      }
    }
  }
  
  return {
    exactMatch,
    lengthMatch,
    diffChars,
    original,
    received
  };
};

// 認証処理
async function authenticate() {
  console.log('認証処理を開始...');
  
  try {
    // ログイン
    const loginResponse = await axios.post(
      `${API_BASE_URL}/users/login`, 
      TEST_USER,
      { headers: getHeaders(false) }
    );
    
    if (loginResponse.status !== 200 || !loginResponse.data.access_token) {
      throw new Error('ログインに失敗しました');
    }
    
    authToken = loginResponse.data.access_token;
    console.log('✅ ログイン成功');
    return true;
  } catch (error) {
    console.error('❌ 認証処理に失敗しました:', error.message);
    if (error.response) {
      console.error('レスポンス:', error.response.data);
    }
    return false;
  }
}

// プロジェクト作成テスト
async function testProjectCreation(testData) {
  const result = {
    testName: testData.name,
    success: false,
    originalData: testData.data,
    receivedData: null,
    details: null,
    error: null
  };
  
  try {
    // 一意なプロジェクト名を生成
    const projectName = `日本語テスト_${testData.name}_${Date.now()}`;
    
    // プロジェクト作成
    const createResponse = await axios.post(
      `${API_BASE_URL}/projects`, 
      {
        name: projectName,
        description: testData.data
      },
      { headers: getHeaders() }
    );
    
    if (createResponse.status !== 201) {
      throw new Error(`プロジェクト作成に失敗しました: ${createResponse.status}`);
    }
    
    const createdProject = createResponse.data;
    const projectId = createdProject.id;
    
    // 作成したプロジェクトの取得
    const getResponse = await axios.get(
      `${API_BASE_URL}/projects/${projectId}`,
      { headers: getHeaders() }
    );
    
    if (getResponse.status !== 200) {
      throw new Error(`プロジェクト取得に失敗しました: ${getResponse.status}`);
    }
    
    const receivedProject = getResponse.data;
    
    // 日本語テキストの検証
    result.receivedData = receivedProject.description;
    result.details = verifyJapaneseText(testData.data, receivedProject.description);
    result.success = result.details.exactMatch;
    
    // テスト後プロジェクトを削除
    await axios.delete(
      `${API_BASE_URL}/projects/${projectId}`,
      { headers: getHeaders() }
    );
    
    return result;
  } catch (error) {
    result.error = error.message;
    if (error.response) {
      result.error += ` - レスポンス: ${JSON.stringify(error.response.data)}`;
    }
    return result;
  }
}

// セッション作成テスト
async function testSessionCreation(testData) {
  const result = {
    testName: testData.name,
    success: false,
    originalData: testData.data,
    receivedData: null,
    details: null,
    error: null
  };
  
  try {
    // 一時的なプロジェクトを作成
    const tempProjectResponse = await axios.post(
      `${API_BASE_URL}/projects`, 
      {
        name: `一時プロジェクト_${Date.now()}`,
        description: '日本語エンコーディングテスト用'
      },
      { headers: getHeaders() }
    );
    
    if (tempProjectResponse.status !== 201) {
      throw new Error('一時プロジェクト作成に失敗しました');
    }
    
    const projectId = tempProjectResponse.data.id;
    
    // セッション作成
    const sessionName = `日本語セッション_${testData.name}_${Date.now()}`;
    const sessionResponse = await axios.post(
      `${API_BASE_URL}/sessions`, 
      {
        name: sessionName,
        description: testData.data,
        project_id: projectId,
        date: new Date().toISOString().split('T')[0]
      },
      { headers: getHeaders() }
    );
    
    if (sessionResponse.status !== 201) {
      throw new Error(`セッション作成に失敗しました: ${sessionResponse.status}`);
    }
    
    const sessionId = sessionResponse.data.id;
    
    // 作成したセッションの取得
    const getResponse = await axios.get(
      `${API_BASE_URL}/sessions/${sessionId}`,
      { headers: getHeaders() }
    );
    
    if (getResponse.status !== 200) {
      throw new Error(`セッション取得に失敗しました: ${getResponse.status}`);
    }
    
    const receivedSession = getResponse.data;
    
    // 日本語テキストの検証
    result.receivedData = receivedSession.description;
    result.details = verifyJapaneseText(testData.data, receivedSession.description);
    result.success = result.details.exactMatch;
    
    // テスト後、セッションとプロジェクトを削除
    await axios.delete(
      `${API_BASE_URL}/sessions/${sessionId}`,
      { headers: getHeaders() }
    );
    
    await axios.delete(
      `${API_BASE_URL}/projects/${projectId}`,
      { headers: getHeaders() }
    );
    
    return result;
  } catch (error) {
    result.error = error.message;
    if (error.response) {
      result.error += ` - レスポンス: ${JSON.stringify(error.response.data)}`;
    }
    return result;
  }
}

// 検索パラメータテスト
async function testSearchParameters(testData) {
  const result = {
    testName: testData.name,
    success: false,
    originalData: testData.data,
    receivedData: null,
    details: null,
    error: null
  };
  
  try {
    // プロジェクト検索APIを使用
    const searchResponse = await axios.get(
      `${API_BASE_URL}/projects/search?query=${encodeURIComponent(testData.data)}`,
      { headers: getHeaders() }
    );
    
    if (searchResponse.status !== 200) {
      throw new Error(`検索リクエストに失敗しました: ${searchResponse.status}`);
    }
    
    // リクエストが成功したことを確認（結果の内容は問わない）
    result.success = true;
    result.receivedData = 'リクエスト成功（検索パラメータは正しく送信されました）';
    
    return result;
  } catch (error) {
    result.error = error.message;
    if (error.response) {
      result.error += ` - レスポンス: ${JSON.stringify(error.response.data)}`;
    }
    return result;
  }
}

// テスト結果の保存
async function saveResults(results) {
  try {
    // 成功率の計算
    const totalTests = results.length;
    const successfulTests = results.filter(r => r.success).length;
    const successRate = (successfulTests / totalTests) * 100;
    
    // 結果サマリー
    const summary = {
      totalTests,
      successfulTests,
      successRate: `${successRate.toFixed(2)}%`,
      timestamp: new Date().toISOString(),
      apiUrl: API_BASE_URL,
      results
    };
    
    // ファイルに保存
    await fs.writeFile(REPORT_FILE, JSON.stringify(summary, null, 2), 'utf8');
    console.log(`✅ テスト結果を ${REPORT_FILE} に保存しました`);
    
    return summary;
  } catch (error) {
    console.error(`❌ テスト結果の保存に失敗しました: ${error.message}`);
    return null;
  }
}

// メイン実行関数
async function runTests() {
  console.log('セーリング戦略分析システム 日本語エンコーディングテスト開始');
  console.log('API URL:', API_BASE_URL);
  console.log('日時:', new Date().toISOString());
  console.log('----------------------------------------');
  
  // 結果を格納する配列
  const results = [];
  
  try {
    // 認証
    const authenticated = await authenticate();
    if (!authenticated) {
      throw new Error('認証に失敗したためテストを中断します');
    }
    
    // 各テストデータセットでテスト実行
    console.log(`${japaneseTestDataSets.length}個のテストデータセットで実行します...`);
    
    for (const [index, testData] of japaneseTestDataSets.entries()) {
      console.log(`\n[${index + 1}/${japaneseTestDataSets.length}] "${testData.name}" テスト実行中...`);
      
      // プロジェクト作成テスト
      console.log(`  プロジェクト作成テスト...`);
      const projectResult = await testProjectCreation(testData);
      results.push({...projectResult, testType: 'プロジェクト作成'});
      console.log(`  ${projectResult.success ? '✅ 成功' : '❌ 失敗'}`);
      
      // セッション作成テスト
      console.log(`  セッション作成テスト...`);
      const sessionResult = await testSessionCreation(testData);
      results.push({...sessionResult, testType: 'セッション作成'});
      console.log(`  ${sessionResult.success ? '✅ 成功' : '❌ 失敗'}`);
      
      // 検索パラメータテスト
      console.log(`  検索パラメータテスト...`);
      const searchResult = await testSearchParameters(testData);
      results.push({...searchResult, testType: '検索パラメータ'});
      console.log(`  ${searchResult.success ? '✅ 成功' : '❌ 失敗'}`);
    }
    
    // 結果を保存
    const summary = await saveResults(results);
    
    // 結果サマリー表示
    console.log('\n----------------------------------------');
    console.log('テスト結果サマリー:');
    console.log(`  総テスト数: ${summary.totalTests}`);
    console.log(`  成功: ${summary.successfulTests}`);
    console.log(`  成功率: ${summary.successRate}`);
    
    // エラーや文字化けが発生したテストケースを表示
    const failedTests = results.filter(r => !r.success);
    if (failedTests.length > 0) {
      console.log('\n失敗したテストケース:');
      for (const test of failedTests) {
        console.log(`  - ${test.testType}: ${test.testName}`);
        if (test.error) {
          console.log(`    エラー: ${test.error}`);
        } else if (test.details && test.details.diffChars.length > 0) {
          console.log(`    文字化け: ${test.details.diffChars.length}文字`);
          for (const diff of test.details.diffChars.slice(0, 3)) { // 最初の3つだけ表示
            console.log(`    位置${diff.position}: '${diff.original}'(${diff.originalCode}) → '${diff.received}'(${diff.receivedCode})`);
          }
          if (test.details.diffChars.length > 3) {
            console.log(`    ... 他 ${test.details.diffChars.length - 3} 文字`);
          }
        }
      }
    }
    
    console.log('\n----------------------------------------');
    console.log(`✅ すべてのテストが実行されました（成功率: ${summary.successRate}）`);
    console.log('実行完了時間:', new Date().toISOString());
    
    // 全て成功した場合は正常終了、それ以外はエラー終了
    if (summary.totalTests === summary.successfulTests) {
      process.exit(0);
    } else {
      process.exit(1);
    }
  } catch (error) {
    console.error('\n----------------------------------------');
    console.error('❌ テスト実行中にエラーが発生しました:', error.message);
    console.error('テスト失敗時間:', new Date().toISOString());
    
    // 途中までの結果を保存
    if (results.length > 0) {
      await saveResults(results);
    }
    
    process.exit(1);
  }
}

// テスト実行
runTests();
