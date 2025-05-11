'use client';

import React, { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';
import { useRouter } from 'next/router';
import { useSettings } from '../../context/SettingsContext';
import { useAnalysis } from '../../context/AnalysisContext';
import Button from '../../components/common/Button';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import AnalysisPanel from '../../components/analysis/AnalysisPanel';
import SettingsPanel from '../../components/settings/SettingsPanel';

// マップ関連のコンポーネントを動的インポート（SSR対策）
const MapView = dynamic(() => import('../../components/map/MapView'), { ssr: false });
const TrackLayer = dynamic(() => import('../../components/map/TrackLayer'), { ssr: false });
const WindLayer = dynamic(() => import('../../components/map/WindLayer'), { ssr: false });
const StrategyPointLayer = dynamic(() => import('../../components/map/StrategyPointLayer'), { ssr: false });

export default function AnalysisPage() {
  const router = useRouter();
  const { settings, updateSettings } = useSettings();
  const { data, isAnalyzing, error, applySettings } = useAnalysis();
  const [activeView, setActiveView] = useState<'track' | 'wind' | 'strategy'>('track');
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [mapInstance, setMapInstance] = useState<any>(null);
  
  // URLクエリパラメータからセッションIDを取得
  const { session_id } = router.query;
  
  // データがない場合はホームページに戻る
  useEffect(() => {
    if (!data.sessionId && !isAnalyzing && router.isReady) {
      router.push('/');
    }
  }, [data.sessionId, isAnalyzing, router]);
  
  // 設定適用ハンドラ
  const handleApplySettings = async () => {
    await applySettings(settings);
    setSettingsOpen(false);
  };
  
  // SettingsPanel用のupdateSettingsラッパー
  const updateSettingsWrapper = (category: string, key: string, value: any) => {
    // TypeScriptの型の制限を回避するために、anyを使用
    (updateSettings as any)(category, key, value);
  };
  
  // エクスポートハンドラ
  const handleExport = async (format: 'pdf' | 'csv' | 'gpx') => {
    try {
      // エクスポート機能の実装
      console.log(`Exporting as ${format}`);
    } catch (err) {
      console.error('Export error:', err);
    }
  };
  
  // エラー表示
  if (error) {
    return (
      <div className="flex flex-col min-h-screen bg-black text-gray-200">
        <header className="bg-gray-900 py-3 px-4 border-b border-gray-700">
          <div className="flex items-center">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 10l-2 1m0 0l-2-1m2 1v2.5M20 7l-2 1m2-1l-2-1m2 1v2.5M14 4l-2-1-2 1M4 7l2-1M4 7l2 1M4 7v2.5M12 21l-2-1m2 1l2-1m-2 1v-2.5M6 18l-2-1v-2.5M18 18l2-1v-2.5" />
            </svg>
            <h1 className="text-xl font-semibold ml-2 text-blue-200">セーリング分析</h1>
          </div>
        </header>
        
        <main className="flex-1 flex flex-col items-center justify-center p-6 bg-gray-900">
          <div className="max-w-md w-full mx-auto p-6 bg-red-900 bg-opacity-50 border border-red-800 rounded">
            <h3 className="text-lg font-medium text-red-200">エラーが発生しました</h3>
            <p className="mt-2 text-red-300">{error}</p>
            <Button 
              variant="primary" 
              className="mt-4"
              onClick={() => router.push('/')}
            >
              ホームに戻る
            </Button>
          </div>
        </main>
      </div>
    );
  }
  
  // 分析中の表示
  if (isAnalyzing) {
    return (
      <div className="flex flex-col min-h-screen bg-black text-gray-200">
        <header className="bg-gray-900 py-3 px-4 border-b border-gray-700">
          <div className="flex items-center">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 10l-2 1m0 0l-2-1m2 1v2.5M20 7l-2 1m2-1l-2-1m2 1v2.5M14 4l-2-1-2 1M4 7l2-1M4 7l2 1M4 7v2.5M12 21l-2-1m2 1l2-1m-2 1v-2.5M6 18l-2-1v-2.5M18 18l2-1v-2.5" />
            </svg>
            <h1 className="text-xl font-semibold ml-2 text-blue-200">セーリング分析</h1>
          </div>
        </header>
        
        <main className="flex-1 flex flex-col items-center justify-center p-6 bg-gray-900">
          <LoadingSpinner size="large" />
          <h2 className="mt-6 text-xl font-medium text-gray-300">データ分析中...</h2>
          <p className="mt-2 text-gray-500">風向風速と戦略ポイントを計算しています</p>
        </main>
      </div>
    );
  }
  
  // メイン分析画面
  return (
    <div className="flex flex-col h-screen bg-black text-gray-200">
      {/* ヘッダー */}
      <header className="bg-gray-900 py-3 px-4 flex items-center justify-between border-b border-gray-700 z-10">
        <div className="flex items-center">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 10l-2 1m0 0l-2-1m2 1v2.5M20 7l-2 1m2-1l-2-1m2 1v2.5M14 4l-2-1-2 1M4 7l2-1M4 7l2 1M4 7v2.5M12 21l-2-1m2 1l2-1m-2 1v-2.5M6 18l-2-1v-2.5M18 18l2-1v-2.5" />
          </svg>
          <h1 className="text-xl font-semibold ml-2 text-blue-200">セーリング分析</h1>
          {data.fileName && (
            <span className="ml-4 text-sm text-gray-400">{data.fileName}</span>
          )}
        </div>
        
        <div className="flex items-center space-x-4">
          <div className="hidden md:flex space-x-2">
            <Button
              variant={activeView === 'track' ? 'primary' : 'ghost'}
              size="sm"
              onClick={() => setActiveView('track')}
              icon={
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
                </svg>
              }
            >
              航跡
            </Button>
            <Button
              variant={activeView === 'wind' ? 'primary' : 'ghost'}
              size="sm"
              onClick={() => setActiveView('wind')}
              icon={
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
                </svg>
              }
            >
              風向風速
            </Button>
            <Button
              variant={activeView === 'strategy' ? 'primary' : 'ghost'}
              size="sm"
              onClick={() => setActiveView('strategy')}
              icon={
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              }
            >
              戦略
            </Button>
            
            <Button
              variant={settingsOpen ? 'primary' : 'ghost'}
              size="sm"
              onClick={() => setSettingsOpen(!settingsOpen)}
              icon={
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              }
            >
              設定
            </Button>
          </div>
          
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setMenuOpen(!menuOpen)}
            icon={
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            }
          />
        </div>
      </header>
      
      {/* メインコンテンツ */}
      <main className="flex-1 relative overflow-hidden">
        {/* モバイルメニュー */}
        {menuOpen && (
          <div className="absolute top-0 right-0 w-64 h-full bg-gray-900 z-50 shadow-lg p-4">
            <div className="flex justify-end mb-4">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setMenuOpen(false)}
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </Button>
            </div>
            <div className="space-y-2">
              <Button
                variant={activeView === 'track' ? 'primary' : 'outline'}
                fullWidth
                onClick={() => {
                  setActiveView('track');
                  setMenuOpen(false);
                }}
              >
                航跡表示
              </Button>
              <Button
                variant={activeView === 'wind' ? 'primary' : 'outline'}
                fullWidth
                onClick={() => {
                  setActiveView('wind');
                  setMenuOpen(false);
                }}
              >
                風向風速表示
              </Button>
              <Button
                variant={activeView === 'strategy' ? 'primary' : 'outline'}
                fullWidth
                onClick={() => {
                  setActiveView('strategy');
                  setMenuOpen(false);
                }}
              >
                戦略表示
              </Button>
              <hr className="border-gray-700 my-4" />
              <Button
                variant="outline"
                fullWidth
                onClick={() => {
                  setSettingsOpen(true);
                  setMenuOpen(false);
                }}
              >
                設定
              </Button>
              <Button
                variant="outline"
                fullWidth
                onClick={() => handleExport('pdf')}
              >
                PDFエクスポート
              </Button>
              <Button
                variant="outline"
                fullWidth
                onClick={() => handleExport('csv')}
              >
                CSVエクスポート
              </Button>
            </div>
          </div>
        )}
        
        {/* 設定パネル */}
        <SettingsPanel
          isOpen={settingsOpen}
          onClose={() => setSettingsOpen(false)}
          onApply={handleApplySettings}
          settings={settings}
          updateSettings={updateSettingsWrapper}
        />
        
        {/* 地図表示エリア */}
        <div className="h-full">
          <MapView
            style={settings.display.mapStyle || 'dark'}
            onMapLoaded={(map) => setMapInstance(map)}
          >
            {mapInstance && (
              <>
                {/* 現在のビューに応じたレイヤー表示 */}
                {activeView === 'track' && (
                  <TrackLayer
                    map={mapInstance}
                    trackData={data.gpsData}
                    colorScheme={settings.display.colorScheme}
                    selectedTime={data.currentTime}
                  />
                )}
                
                {activeView === 'wind' && (
                  <WindLayer
                    map={mapInstance}
                    windPoints={data.windData}
                    selectedTime={data.currentTime}
                  />
                )}
                
                {activeView === 'strategy' && (
                  <StrategyPointLayer
                    map={mapInstance}
                    strategyPoints={data.strategyPoints}
                    showLabels={settings.display.showLabels}
                    selectedTime={data.currentTime}
                  />
                )}
              </>
            )}
          </MapView>
          
          {/* 分析パネル */}
          <AnalysisPanel
            activeView={activeView}
            onViewChange={setActiveView}
            onSettingsOpen={() => setSettingsOpen(true)}
            data={data}
          />
        </div>
      </main>
    </div>
  );
}
