'use client';

import React from 'react';

export default function DebugPage() {
  // 環境変数の確認
  const envVars = {
    API_URL: process.env.NEXT_PUBLIC_API_URL,
    APP_NAME: process.env.NEXT_PUBLIC_APP_NAME,
    APP_VERSION: process.env.NEXT_PUBLIC_APP_VERSION,
    SUPABASE_URL: process.env.NEXT_PUBLIC_SUPABASE_URL,
  };

  return (
    <div className="min-h-screen bg-gray-900 text-gray-200 p-8">
      <h1 className="text-2xl font-bold mb-8">デバッグ情報</h1>
      
      <div className="bg-gray-800 p-6 rounded-lg mb-6">
        <h2 className="text-xl font-semibold mb-4">環境変数</h2>
        <ul className="space-y-2">
          {Object.entries(envVars).map(([key, value]) => (
            <li key={key} className="font-mono text-sm">
              <span className="text-blue-400">{key}:</span>{' '}
              <span className="text-green-400">{value || 'undefined'}</span>
            </li>
          ))}
        </ul>
      </div>
      
      <div className="bg-gray-800 p-6 rounded-lg mb-6">
        <h2 className="text-xl font-semibold mb-4">React動作確認</h2>
        <p className="mb-4">このページが表示されていれば、Reactは正常に動作しています。</p>
        <button 
          onClick={() => alert('ボタンがクリックされました！')}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded"
        >
          クリックテスト
        </button>
      </div>
      
      <div className="bg-gray-800 p-6 rounded-lg">
        <h2 className="text-xl font-semibold mb-4">スタイル確認</h2>
        <div className="flex space-x-4">
          <div className="bg-blue-600 p-4 rounded">Blue Box</div>
          <div className="bg-green-600 p-4 rounded">Green Box</div>
          <div className="bg-red-600 p-4 rounded">Red Box</div>
        </div>
      </div>
    </div>
  );
}
