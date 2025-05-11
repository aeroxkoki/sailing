'use client';

import React, { useState } from 'react';

export default function HomePage() {
  const [testState, setTestState] = useState('初期状態');

  return (
    <div className="min-h-screen bg-black text-gray-200 p-8">
      <h1 className="text-3xl font-bold mb-6 text-blue-400">
        セーリング戦略分析システム
      </h1>
      
      <div className="bg-gray-800 p-6 rounded-lg mb-6">
        <h2 className="text-xl font-semibold mb-4">動作確認</h2>
        <p className="mb-4">このページが表示されていれば、基本的な動作は正常です。</p>
        <p className="mb-4">現在の状態: <span className="text-green-400">{testState}</span></p>
        <button 
          onClick={() => setTestState('ボタンがクリックされました！')}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded"
        >
          通常のボタンテスト
        </button>
      </div>
      
      <div className="bg-gray-800 p-6 rounded-lg">
        <h2 className="text-xl font-semibold mb-4">インポートなし</h2>
        <p>外部コンポーネントをインポートしていません。これで動作する場合はインポートの問題です。</p>
      </div>
    </div>
  );
}
