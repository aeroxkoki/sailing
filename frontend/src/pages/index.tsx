'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Button from '../components/common/Button';
import Card from '../components/common/Card';
import LoadingSpinner from '../components/common/LoadingSpinner';
import FileUploader from '../components/upload/FileUploader';
import FileList from '../components/upload/FileList';
import Menu from '../components/common/Menu';
import MobileMenu from '../components/common/MobileMenu';
import { api } from '../lib/api';
import { useAnalysis } from '../context/AnalysisContext';

export default function HomePage() {
  const router = useRouter();
  const { uploadFile } = useAnalysis();
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [loading, setLoading] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [apiStatus, setApiStatus] = useState<{status: string; message?: string} | null>(null);
  const [checkingApi, setCheckingApi] = useState(false);

  // ページロード時にAPIの健全性をチェック
  useEffect(() => {
    const checkApiHealth = async () => {
      setCheckingApi(true);
      try {
        const health = await api.checkHealth();
        setApiStatus(health);
        // APIエラーの場合はエラーメッセージを表示
        if (health.status === 'error') {
          setError(health.message || 'APIサーバーに問題があります。');
        }
      } catch (err) {
        console.error('API health check failed:', err);
        setApiStatus({
          status: 'error',
          message: 'APIサーバーの健全性チェックに失敗しました。'
        });
        setError('APIサーバーに接続できません。ネットワーク接続を確認してください。');
      } finally {
        setCheckingApi(false);
      }
    };

    checkApiHealth();
  }, []);

  const handleFileSelect = async (files: File[]) => {
    setSelectedFiles(files);
    setError(null);
  };
  
  const handleRemoveFile = (index: number) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  };
  
  const handleStartAnalysis = async () => {
    if (selectedFiles.length === 0) {
      setError('分析するファイルを選択してください。');
      return;
    }
    
    setLoading(true);
    
    try {
      // 最初のファイルを分析（MVPでは1つのファイルのみサポート）
      await uploadFile(selectedFiles[0]);
      
      // 分析ページに遷移
      router.push('/analysis');
    } catch (err: any) {
      console.error('Upload error:', err);
      setError(err.message || 'ファイルのアップロードに失敗しました。');
    } finally {
      setLoading(false);
    }
  };

  const menuItems = [
    {
      id: 'new-project',
      label: '新規プロジェクト',
      onClick: () => router.push('/projects/new'),
    },
    {
      id: 'open-project',
      label: 'プロジェクトを開く',
      onClick: () => router.push('/projects'),
    },
    {
      id: 'settings',
      label: '設定',
      onClick: () => router.push('/settings'),
    },
  ];

  return (
    <div className="min-h-screen bg-black text-gray-200">
      {/* モバイルメニュー */}
      <MobileMenu 
        isOpen={mobileMenuOpen}
        onClose={() => setMobileMenuOpen(false)}
        items={menuItems}
      />
      
      <header className="bg-gray-900 py-4 px-6 flex items-center justify-between border-b border-gray-700">
        <div className="flex items-center">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
            <path d="M3 6a3 3 0 013-3h10a1 1 0 01.8 1.6L14.25 8l2.55 3.4A1 1 0 0116 13H6a1 1 0 00-1 1v3a1 1 0 11-2 0V6z" />
          </svg>
          <h1 className="text-xl font-semibold ml-2 text-blue-200">セーリング戦略分析</h1>
        </div>
        <div className="flex items-center">
          {/* デスクトップメニュー */}
          <div className="hidden md:relative md:block">
            <Button
              variant="ghost"
              onClick={() => setMenuOpen(!menuOpen)}
              icon={
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M3 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 10a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 15a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
                </svg>
              }
            >
              メニュー
            </Button>
            <Menu
              items={menuItems}
              isOpen={menuOpen}
              onClose={() => setMenuOpen(false)}
            />
          </div>
          
          {/* モバイルメニューボタン */}
          <div className="md:hidden">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setMobileMenuOpen(true)}
              aria-label="メニューを開く"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </Button>
          </div>
        </div>
      </header>

      <main className="container mx-auto py-8 px-4">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2">
            <Card
              title="GPSデータアップロード"
              variant="dark"
              className="mb-8"
            >
              {loading ? (
                <div className="flex flex-col items-center justify-center p-12">
                  <LoadingSpinner size="large" color="blue" />
                  <p className="mt-4 text-gray-400">データ分析中...</p>
                </div>
              ) : (
                <>
                  <FileUploader
                    onFileSelect={handleFileSelect}
                    acceptedFileTypes=".gpx,.csv,.fit,.tcx"
                    multiple={true}
                  />
                  
                  <FileList 
                    files={selectedFiles}
                    onRemove={handleRemoveFile}
                    disabled={loading}
                  />
                  
                  {selectedFiles.length > 0 && (
                    <div className="mt-4 flex justify-end">
                      <Button
                        variant="primary"
                        onClick={handleStartAnalysis}
                        disabled={loading}
                      >
                        分析開始
                      </Button>
                    </div>
                  )}
                </>
              )}
              
              {error && (
                <div className="mt-4 p-3 bg-red-900 bg-opacity-50 border border-red-800 rounded text-red-200">
                  <div className="flex items-start">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                    <div>
                      <p>{error}</p>
                      {apiStatus?.status === 'error' && (
                        <div className="mt-2">
                          <p className="text-sm">
                            APIサーバー（{process.env.NEXT_PUBLIC_API_URL}）に接続できませんでした。
                            以下の対処法をお試しください：
                          </p>
                          <ul className="list-disc list-inside text-sm mt-1 space-y-1">
                            <li>インターネット接続を確認してください</li>
                            <li>しばらく待ってからページを再読み込みしてください</li>
                            <li>問題が続く場合は管理者に連絡してください</li>
                          </ul>
                          <p className="text-sm mt-2">
                            または、接続不要のデモ分析を見ることもできます：{' '}
                            <button 
                              className="text-blue-400 underline" 
                              onClick={() => router.push('/analysis/demo')}
                            >
                              デモを見る
                            </button>
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </Card>
            
            <Card
              title="はじめに"
              variant="dark"
            >
              <div className="p-4">
                <h3 className="text-lg font-medium text-gray-200 mb-4">セーリング戦略分析システムへようこそ</h3>
                <p className="text-gray-400 mb-6">
                  GPSログをアップロードすると、自動的に風向風速の推定と戦略分析が実行されます。
                </p>
                <div className="space-y-4 text-gray-400">
                  <div>
                    <h4 className="font-medium text-gray-300 mb-2">対応フォーマット</h4>
                    <ul className="list-disc list-inside space-y-1">
                      <li>GPX - GPS Exchange Format</li>
                      <li>CSV - カンマ区切りファイル</li>
                      <li>FIT - Flexible and Interoperable Data Transfer</li>
                      <li>TCX - Training Center XML</li>
                    </ul>
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-300 mb-2">分析内容</h4>
                    <ul className="list-disc list-inside space-y-1">
                      <li>風向風速の推定</li>
                      <li>タック・ジャイブの検出</li>
                      <li>戦略ポイントの評価</li>
                      <li>パフォーマンス分析</li>
                    </ul>
                  </div>
                </div>
              </div>
            </Card>
          </div>
          
          <div>
            <Card
              title="クイックアクション"
              variant="dark"
              className="mb-8"
            >
              <div className="space-y-3">
                <Button variant="primary" fullWidth onClick={() => router.push('/projects/new')}>
                  新規プロジェクト作成
                </Button>
                <Button variant="outline" fullWidth onClick={() => router.push('/projects')}>
                  既存プロジェクトを開く
                </Button>
                <Button variant="outline" fullWidth onClick={() => router.push('/analysis/demo')}>
                  デモ分析を見る
                </Button>
              </div>
            </Card>
            
            <Card
              title="最近のプロジェクト"
              variant="dark"
            >
              <div className="p-4">
                <p className="text-sm text-gray-500 text-center py-4">
                  最近のプロジェクトはまだありません
                </p>
              </div>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}