'use client';

import React, { useState } from 'react';
import Button from '@/components/common/Button';
import Card from '@/components/common/Card';
import LoadingSpinner from '@/components/common/LoadingSpinner';
import FileUploader from '@/components/upload/FileUploader';
import Menu from '@/components/common/Menu';
import MobileMenu from '@/components/common/MobileMenu';

export default function HomePage() {
  const [loading, setLoading] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const handleFileSelect = (file: File) => {
    setSelectedFile(file);
    // 通常はここでAPIを呼び出して分析を開始します
    setLoading(true);
    // 分析処理をシミュレート
    setTimeout(() => {
      setLoading(false);
    }, 3000);
  };

  const menuItems = [
    {
      id: 'new-project',
      label: '新規プロジェクト',
      onClick: () => console.log('新規プロジェクト'),
    },
    {
      id: 'open-project',
      label: 'プロジェクトを開く',
      onClick: () => console.log('プロジェクトを開く'),
    },
    {
      id: 'settings',
      label: '設定',
      onClick: () => console.log('設定'),
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
              icon={
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              }
            />
          </div>
        </div>
      </header>

      <main className="container mx-auto py-8 px-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="md:col-span-2">
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
                <FileUploader
                  onFileSelect={handleFileSelect}
                  acceptedFileTypes=".gpx,.csv,.fit,.tcx"
                />
              )}
            </Card>
            
            {selectedFile && !loading && (
              <Card
                title="分析結果"
                variant="dark"
              >
                <div className="p-4">
                  <h3 className="text-lg font-medium text-gray-200 mb-4">ファイル: {selectedFile.name}</h3>
                  <p className="text-gray-400 mb-6">
                    これはサンプル分析結果表示です。実際の実装では、アップロードされたファイルの分析結果がここに表示されます。
                  </p>
                  <div className="flex space-x-4">
                    <Button variant="primary">詳細分析</Button>
                    <Button variant="outline">レポート作成</Button>
                  </div>
                </div>
              </Card>
            )}
          </div>
          
          <div>
            <Card
              title="コンポーネントサンプル"
              variant="dark"
              className="mb-8"
            >
              <div className="space-y-6">
                <div>
                  <h3 className="text-sm font-medium text-gray-400 mb-2">ボタンバリエーション</h3>
                  <div className="space-y-2">
                    <Button variant="primary" className="mb-2 mr-2">プライマリ</Button>
                    <Button variant="secondary" className="mb-2 mr-2">セカンダリ</Button>
                    <Button variant="outline" className="mb-2 mr-2">アウトライン</Button>
                    <Button variant="ghost" className="mb-2 mr-2">ゴースト</Button>
                  </div>
                </div>
                
                <div>
                  <h3 className="text-sm font-medium text-gray-400 mb-2">サイズバリエーション</h3>
                  <div className="space-y-2">
                    <Button variant="primary" size="sm" className="mb-2 mr-2">Small</Button>
                    <Button variant="primary" size="md" className="mb-2 mr-2">Medium</Button>
                    <Button variant="primary" size="lg" className="mb-2 mr-2">Large</Button>
                  </div>
                </div>
                
                <div>
                  <h3 className="text-sm font-medium text-gray-400 mb-2">ローディング状態</h3>
                  <Button variant="primary" isLoading className="mb-2 mr-2">ローディング</Button>
                </div>
                
                <div>
                  <h3 className="text-sm font-medium text-gray-400 mb-2">アイコン付き</h3>
                  <Button 
                    variant="primary" 
                    icon={
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M4 5a2 2 0 00-2 2v8a2 2 0 002 2h12a2 2 0 002-2V7a2 2 0 00-2-2h-1.586a1 1 0 01-.707-.293l-1.121-1.121A2 2 0 0011.172 3H8.828a2 2 0 00-1.414.586L6.293 4.707A1 1 0 015.586 5H4zm6 9a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd" />
                      </svg>
                    }
                  >
                    アイコン付き
                  </Button>
                </div>
                
                <div>
                  <h3 className="text-sm font-medium text-gray-400 mb-2">全幅ボタン</h3>
                  <Button variant="primary" fullWidth>全幅ボタン</Button>
                </div>
              </div>
            </Card>
            
            <Card
              title="ローディングスピナー"
              variant="dark"
            >
              <div className="grid grid-cols-3 gap-4 p-4">
                <div className="flex flex-col items-center">
                  <LoadingSpinner size="small" color="blue" />
                  <span className="mt-2 text-xs text-gray-500">Small</span>
                </div>
                <div className="flex flex-col items-center">
                  <LoadingSpinner size="medium" color="white" />
                  <span className="mt-2 text-xs text-gray-500">Medium</span>
                </div>
                <div className="flex flex-col items-center">
                  <LoadingSpinner size="large" color="gray" />
                  <span className="mt-2 text-xs text-gray-500">Large</span>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}
