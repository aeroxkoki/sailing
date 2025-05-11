'use client';

import React, { useState } from 'react';
import Button from '@/components/common/Button';

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
        <Button 
          onClick={() => setTestState('ボタンがクリックされました！')}
          variant="primary"
        >
          Buttonコンポーネントテスト
        </Button>
      </div>
      
      <div className="bg-gray-800 p-6 rounded-lg">
        <h2 className="text-xl font-semibold mb-4">Buttonコンポーネント追加</h2>
        <p>Buttonコンポーネントを追加しました。エラーが出る場合はここに問題があります。</p>
      </div>
    </div>
  );
}
