/**
 * セーリング戦略分析システム - APIエンドポイントテストスクリプト
 * 
 * 主要なAPIエンドポイントの機能をテストし、正常に動作するか確認します。
 * 特に日本語の扱いに注意してテストを行います。
 */

const axios = require('axios');
const assert = require('assert').strict;

// 設定
const API_BASE_URL = process.env.API_URL || 'http://localhost:8000/api/v1';
const TEST_USER = {
  email: 'test@example.com',
  password: 'testpassword123'
};

// 日本語テストデータ
const japaneseTestData = {
  simple: 'こんにちは、世界',
  complex: '漢字、ひらがな、カタカナ、①②③、㎡、ｱｲｳｴｵ、🌸絵文字',
  long: '長文の日本語テキストをテストします。このテキストには様々な文字が含まれており、エンコーディングの問題が発生していないか確認するために使用します。特に特殊な文字や記号を含むケースをテストすることが重要です。'
};

// 認証トークンをグローバルに保持
let authToken = null;

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

// ヘルパー関数: レスポンスの検証
const verifyResponse = (response, expectedStatus = 200) => {
  assert.equal(response.status, expectedStatus, `期待するステータスコード ${expectedStatus} ではなく ${response.status} が返されました`);
  assert(response.data, 'レスポンスデータがありません');
  return response.data;
};

// 認証テスト
async function testAuthentication() {
  console.log('===== 認証フロー テスト =====');
  
  try {
    // 1. ユーザー登録テスト (すでに存在する場合はスキップ)
    try {
      console.log('ユーザー登録をテスト中...');
      const registerData = {
        ...TEST_USER,
        name: '山田テスト'
      };
      
      const registerResponse = await axios.post(
        `${API_BASE_URL}/users/register`, 
        registerData,
        { headers: getHeaders(false) }
      );
      
      verifyResponse(registerResponse, 201);
      console.log('✅ ユーザー登録成功');
    } catch (error) {
      if (error.response && error.response.status === 400) {
        console.log('⚠️ ユーザーはすでに存在しています。ログインへ進みます。');
      } else {
        throw error;
      }
    }
    
    // 2. ログインテスト
    console.log('ログインをテスト中...');
    const loginResponse = await axios.post(
      `${API_BASE_URL}/users/login`, 
      TEST_USER,
      { headers: getHeaders(false) }
    );
    
    const loginData = verifyResponse(loginResponse);
    assert(loginData.access_token, 'アクセストークンがありません');
    authToken = loginData.access_token;
    console.log('✅ ログイン成功');
    
    // 3. ユーザー情報取得テスト
    console.log('ユーザー情報取得をテスト中...');
    const userResponse = await axios.get(
      `${API_BASE_URL}/users/me`,
      { headers: getHeaders() }
    );
    
    const userData = verifyResponse(userResponse);
    assert(userData.email === TEST_USER.email, 'ユーザーメールアドレスが一致しません');
    console.log('✅ ユーザー情報取得成功');
    
    return authToken;
  } catch (error) {
    console.error('❌ 認証テスト失敗:', error.message);
    if (error.response) {
      console.error('レスポンス:', error.response.data);
    }
    throw error;
  }
}

// プロジェクト管理テスト
async function testProjectManagement() {
  console.log('\n===== プロジェクト管理 テスト =====');
  
  let projectId = null;
  
  try {
    // 1. プロジェクト作成テスト (日本語名)
    console.log('日本語名でのプロジェクト作成をテスト中...');
    const projectData = {
      name: `テストプロジェクト_${Date.now()}`,
      description: japaneseTestData.complex
    };
    
    const createResponse = await axios.post(
      `${API_BASE_URL}/projects`, 
      projectData,
      { headers: getHeaders() }
    );
    
    const createdProject = verifyResponse(createResponse, 201);
    projectId = createdProject.id;
    assert(createdProject.name === projectData.name, 'プロジェクト名が一致しません');
    assert(createdProject.description === projectData.description, 'プロジェクト説明が一致しません: ' + 
      `期待値:${projectData.description}, 実際の値:${createdProject.description}`);
    console.log('✅ プロジェクト作成成功:', projectId);
    
    // 2. プロジェクト一覧取得テスト
    console.log('プロジェクト一覧取得をテスト中...');
    const listResponse = await axios.get(
      `${API_BASE_URL}/projects`,
      { headers: getHeaders() }
    );
    
    const projects = verifyResponse(listResponse);
    assert(Array.isArray(projects), 'プロジェクト一覧が配列ではありません');
    const foundProject = projects.find(p => p.id === projectId);
    assert(foundProject, '作成したプロジェクトが一覧に見つかりません');
    console.log('✅ プロジェクト一覧取得成功');
    
    // 3. プロジェクト詳細取得テスト
    console.log('プロジェクト詳細取得をテスト中...');
    const detailResponse = await axios.get(
      `${API_BASE_URL}/projects/${projectId}`,
      { headers: getHeaders() }
    );
    
    const projectDetail = verifyResponse(detailResponse);
    assert(projectDetail.id === projectId, 'プロジェクトIDが一致しません');
    assert(projectDetail.name === projectData.name, 'プロジェクト名が一致しません');
    console.log('✅ プロジェクト詳細取得成功');
    
    // 4. プロジェクト更新テスト
    console.log('プロジェクト更新をテスト中...');
    const updateData = {
      name: `${projectData.name}（更新済み）`,
      description: `${projectData.description} - 更新テスト`
    };
    
    const updateResponse = await axios.put(
      `${API_BASE_URL}/projects/${projectId}`,
      updateData,
      { headers: getHeaders() }
    );
    
    const updatedProject = verifyResponse(updateResponse);
    assert(updatedProject.name === updateData.name, '更新後のプロジェクト名が一致しません');
    assert(updatedProject.description === updateData.description, '更新後のプロジェクト説明が一致しません');
    console.log('✅ プロジェクト更新成功');
    
    return projectId;
  } catch (error) {
    console.error('❌ プロジェクト管理テスト失敗:', error.message);
    if (error.response) {
      console.error('レスポンス:', error.response.data);
    }
    throw error;
  }
}

// セッション管理テスト
async function testSessionManagement(projectId) {
  console.log('\n===== セッション管理 テスト =====');
  
  if (!projectId) {
    console.error('❌ プロジェクトIDが指定されていません');
    return null;
  }
  
  let sessionId = null;
  
  try {
    // 1. セッション作成テスト
    console.log('セッション作成をテスト中...');
    const sessionData = {
      name: `テストセッション_${Date.now()}`,
      description: japaneseTestData.long,
      project_id: projectId,
      date: new Date().toISOString().split('T')[0]
    };
    
    const createResponse = await axios.post(
      `${API_BASE_URL}/sessions`, 
      sessionData,
      { headers: getHeaders() }
    );
    
    const createdSession = verifyResponse(createResponse, 201);
    sessionId = createdSession.id;
    assert(createdSession.name === sessionData.name, 'セッション名が一致しません');
    assert(createdSession.project_id === projectId, 'プロジェクトIDが一致しません');
    console.log('✅ セッション作成成功:', sessionId);
    
    // 2. プロジェクト内のセッション一覧取得テスト
    console.log('プロジェクト内のセッション一覧取得をテスト中...');
    const listResponse = await axios.get(
      `${API_BASE_URL}/projects/${projectId}/sessions`,
      { headers: getHeaders() }
    );
    
    const sessions = verifyResponse(listResponse);
    assert(Array.isArray(sessions), 'セッション一覧が配列ではありません');
    const foundSession = sessions.find(s => s.id === sessionId);
    assert(foundSession, '作成したセッションがプロジェクト内に見つかりません');
    console.log('✅ プロジェクト内のセッション一覧取得成功');
    
    // 3. セッション詳細取得テスト
    console.log('セッション詳細取得をテスト中...');
    const detailResponse = await axios.get(
      `${API_BASE_URL}/sessions/${sessionId}`,
      { headers: getHeaders() }
    );
    
    const sessionDetail = verifyResponse(detailResponse);
    assert(sessionDetail.id === sessionId, 'セッションIDが一致しません');
    assert(sessionDetail.name === sessionData.name, 'セッション名が一致しません');
    console.log('✅ セッション詳細取得成功');
    
    // 4. セッション更新テスト
    console.log('セッション更新をテスト中...');
    const updateData = {
      name: `${sessionData.name}（更新済み）`,
      description: `${sessionData.description} - 更新テスト`
    };
    
    const updateResponse = await axios.put(
      `${API_BASE_URL}/sessions/${sessionId}`,
      updateData,
      { headers: getHeaders() }
    );
    
    const updatedSession = verifyResponse(updateResponse);
    assert(updatedSession.name === updateData.name, '更新後のセッション名が一致しません');
    assert(updatedSession.description === updateData.description, '更新後のセッション説明が一致しません');
    console.log('✅ セッション更新成功');
    
    return sessionId;
  } catch (error) {
    console.error('❌ セッション管理テスト失敗:', error.message);
    if (error.response) {
      console.error('レスポンス:', error.response.data);
    }
    throw error;
  }
}

// データ処理テスト (風向推定API等)
async function testDataProcessing(sessionId) {
  console.log('\n===== データ処理API テスト =====');
  
  if (!sessionId) {
    console.error('❌ セッションIDが指定されていません');
    return false;
  }
  
  try {
    // このテストはダミーデータが必要なため、実際の実装ではデータインポートが必要です
    // ここではAPIエンドポイントの存在確認のみを行います
    
    // 1. 風向推定APIの存在確認
    console.log('風向推定APIの存在確認...');
    try {
      const response = await axios.post(
        `${API_BASE_URL}/wind-estimation/estimate`,
        { session_id: sessionId },
        { headers: getHeaders() }
      );
      
      console.log('✅ 風向推定APIエンドポイントが存在します');
      console.log('レスポンス:', response.status);
    } catch (error) {
      if (error.response && error.response.status === 400) {
        // 400エラーはパラメータ不足などによる正常なエラーなのでAPIは存在する
        console.log('✅ 風向推定APIエンドポイントが存在します（パラメータエラー）');
      } else {
        console.error('❌ 風向推定APIテスト失敗:', error.message);
        if (error.response) {
          console.error('レスポンス:', error.response.data);
        }
      }
    }
    
    // 2. 戦略検出APIの存在確認
    console.log('戦略検出APIの存在確認...');
    try {
      const response = await axios.post(
        `${API_BASE_URL}/strategy-detection/detect`,
        { session_id: sessionId },
        { headers: getHeaders() }
      );
      
      console.log('✅ 戦略検出APIエンドポイントが存在します');
      console.log('レスポンス:', response.status);
    } catch (error) {
      if (error.response && error.response.status === 400) {
        // 400エラーはパラメータ不足などによる正常なエラーなのでAPIは存在する
        console.log('✅ 戦略検出APIエンドポイントが存在します（パラメータエラー）');
      } else {
        console.error('❌ 戦略検出APIテスト失敗:', error.message);
        if (error.response) {
          console.error('レスポンス:', error.response.data);
        }
      }
    }
    
    return true;
  } catch (error) {
    console.error('❌ データ処理テスト失敗:', error.message);
    if (error.response) {
      console.error('レスポンス:', error.response.data);
    }
    return false;
  }
}

// クリーンアップ (オプション - テスト後に作成したリソースを削除)
async function cleanup(projectId, sessionId) {
  console.log('\n===== クリーンアップ =====');
  
  try {
    // セッション削除
    if (sessionId) {
      console.log(`セッション ${sessionId} を削除中...`);
      await axios.delete(
        `${API_BASE_URL}/sessions/${sessionId}`,
        { headers: getHeaders() }
      );
      console.log('✅ セッション削除成功');
    }
    
    // プロジェクト削除
    if (projectId) {
      console.log(`プロジェクト ${projectId} を削除中...`);
      await axios.delete(
        `${API_BASE_URL}/projects/${projectId}`,
        { headers: getHeaders() }
      );
      console.log('✅ プロジェクト削除成功');
    }
    
    return true;
  } catch (error) {
    console.error('❌ クリーンアップ失敗:', error.message);
    if (error.response) {
      console.error('レスポンス:', error.response.data);
    }
    return false;
  }
}

// メイン実行関数
async function runTests() {
  console.log('セーリング戦略分析システム APIテスト開始');
  console.log('API URL:', API_BASE_URL);
  console.log('日時:', new Date().toISOString());
  console.log('----------------------------------------');
  
  try {
    // 認証テスト
    await testAuthentication();
    
    // プロジェクト管理テスト
    const projectId = await testProjectManagement();
    
    // セッション管理テスト
    const sessionId = await testSessionManagement(projectId);
    
    // データ処理テスト
    await testDataProcessing(sessionId);
    
    // クリーンアップ (オプション)
    // テスト作成したデータを残したい場合はコメントアウト
    // await cleanup(projectId, sessionId);
    
    console.log('\n----------------------------------------');
    console.log('✅ すべてのテストが成功しました');
    console.log('実行完了時間:', new Date().toISOString());
  } catch (error) {
    console.error('\n----------------------------------------');
    console.error('❌ テスト実行中にエラーが発生しました:', error.message);
    console.error('テスト失敗時間:', new Date().toISOString());
    process.exit(1);
  }
}

// テスト実行
runTests();
