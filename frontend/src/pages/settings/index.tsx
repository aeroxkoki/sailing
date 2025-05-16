'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/router';
import { useSettings } from '../../context/SettingsContext';
import Button from '../../components/common/Button';
import Card from '../../components/common/Card';
import WindSettings from '../../components/settings/WindSettings';
import StrategySettings from '../../components/settings/StrategySettings';
import DisplaySettings from '../../components/settings/DisplaySettings';
import AdvancedSettings from '../../components/settings/AdvancedSettings';

/**
 * 設定ページコンポーネント
 */
export default function SettingsPage() {
  const router = useRouter();
  const { settings, updateSettings, resetSettings } = useSettings();
  const [activeTab, setActiveTab] = useState('wind');
  const [isSaved, setIsSaved] = useState(false);

  // 設定を保存
  const handleSaveSettings = () => {
    // 設定はコンテキストに既に保存されているため、
    // ここではローカルストレージにも保存
    if (typeof window !== 'undefined') {
      localStorage.setItem('app-settings', JSON.stringify(settings));
    }
    setIsSaved(true);
    
    // 成功メッセージを表示した後、リセット
    setTimeout(() => {
      setIsSaved(false);
    }, 3000);
  };

  // 設定を更新
  const handleUpdateSettings = (category: string, key: string, value: any) => {
    // TypeScriptの型の制限を回避するために、anyを使用
    (updateSettings as any)(category, key, value);
  };

  return (
    <div className="min-h-screen bg-black text-gray-200">
      <header className="bg-gray-900 py-4 px-6 flex items-center justify-between border-b border-gray-700">
        <div className="flex items-center">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
            <path d="M3 6a3 3 0 013-3h10a1 1 0 01.8 1.6L14.25 8l2.55 3.4A1 1 0 0116 13H6a1 1 0 00-1 1v3a1 1 0 11-2 0V6z" />
          </svg>
          <h1 className="text-xl font-semibold ml-2 text-blue-200">セーリング戦略分析</h1>
        </div>
        <div className="flex items-center space-x-2">
          <Button 
            variant="ghost"
            onClick={() => router.push('/')}
          >
            ホームに戻る
          </Button>
        </div>
      </header>

      <main className="container mx-auto py-8 px-4">
        <div className="flex flex-col md:flex-row gap-6">
          {/* サイドバー */}
          <div className="w-full md:w-64 flex-shrink-0">
            <Card title="設定メニュー" variant="dark" className="sticky top-4">
              <div className="flex flex-col space-y-2 p-2">
                <Button
                  variant={activeTab === 'wind' ? 'primary' : 'ghost'}
                  fullWidth
                  onClick={() => setActiveTab('wind')}
                >
                  風向風速設定
                </Button>
                <Button
                  variant={activeTab === 'strategy' ? 'primary' : 'ghost'}
                  fullWidth
                  onClick={() => setActiveTab('strategy')}
                >
                  戦略検出設定
                </Button>
                <Button
                  variant={activeTab === 'display' ? 'primary' : 'ghost'}
                  fullWidth
                  onClick={() => setActiveTab('display')}
                >
                  表示設定
                </Button>
                <Button
                  variant={activeTab === 'advanced' ? 'primary' : 'ghost'}
                  fullWidth
                  onClick={() => setActiveTab('advanced')}
                >
                  詳細設定
                </Button>
                
                <div className="border-t border-gray-700 my-2 pt-2">
                  <Button
                    variant="outline"
                    fullWidth
                    onClick={resetSettings}
                  >
                    設定をリセット
                  </Button>
                </div>
              </div>
            </Card>
          </div>
          
          {/* メインコンテンツ */}
          <div className="flex-grow">
            <Card 
              title={
                activeTab === 'wind' ? '風向風速設定' : 
                activeTab === 'strategy' ? '戦略検出設定' : 
                activeTab === 'display' ? '表示設定' : '詳細設定'
              } 
              variant="dark"
            >
              <div className="p-4">
                {activeTab === 'wind' && (
                  <WindSettings
                    settings={settings.wind}
                    onChange={(key, value) => handleUpdateSettings('wind', key, value)}
                  />
                )}
                
                {activeTab === 'strategy' && (
                  <StrategySettings
                    settings={settings.strategy}
                    onChange={(key, value) => handleUpdateSettings('strategy', key, value)}
                  />
                )}
                
                {activeTab === 'display' && (
                  <DisplaySettings
                    settings={settings.display}
                    onChange={(key, value) => handleUpdateSettings('display', key, value)}
                  />
                )}
                
                {activeTab === 'advanced' && (
                  <AdvancedSettings
                    settings={settings.advanced}
                    onChange={(key, value) => handleUpdateSettings('advanced', key, value)}
                  />
                )}
                
                <div className="mt-6 flex flex-col sm:flex-row justify-end space-y-2 sm:space-y-0 sm:space-x-2">
                  <Button
                    variant="primary"
                    onClick={handleSaveSettings}
                  >
                    設定を保存
                  </Button>
                  <Button
                    variant="ghost"
                    onClick={() => router.push('/')}
                  >
                    キャンセル
                  </Button>
                </div>
                
                {isSaved && (
                  <div className="mt-4 p-3 bg-green-900 bg-opacity-50 border border-green-800 rounded text-green-200">
                    <div className="flex items-start">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      <span>設定が保存されました</span>
                    </div>
                  </div>
                )}
              </div>
            </Card>
            
            <Card
              title="設定情報"
              variant="dark"
              className="mt-6"
            >
              <div className="p-4">
                <p className="mb-4 text-gray-400">
                  これらの設定は分析時のアルゴリズムや表示に影響します。設定を変更した後、新しい分析を開始すると適用されます。
                </p>
                <div className="text-sm text-gray-500">
                  <p>アプリケーションバージョン: {process.env.NEXT_PUBLIC_APP_VERSION || '0.1.0'}</p>
                  <p className="mt-1">ブラウザにこれらの設定が保存されます</p>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}
