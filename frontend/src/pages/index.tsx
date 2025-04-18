import React from 'react';
import { useRouter } from 'next/router';
import Layout from '../components/common/Layout';
import Button from '../components/common/Button';
import Card from '../components/common/Card';

export default function Home() {
  const router = useRouter();

  // アプリケーションの主な機能
  const features = [
    {
      title: 'GPSデータ解析',
      description: 'セーリングのGPSトラッキングデータを解析し、航路や速度、風向などを視覚化します。',
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
        </svg>
      ),
    },
    {
      title: '風向風速推定',
      description: 'GPSデータから風向風速を推定し、セーリング中の環境条件を可視化します。',
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
    },
    {
      title: '戦略分析',
      description: 'タックやジャイブなどの戦略的ポイントを検出し、レース中の意思決定を評価します。',
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      ),
    },
    {
      title: 'パフォーマンス評価',
      description: '理想的な速度プロファイルと比較して、セーリングパフォーマンスを評価します。',
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      ),
    },
  ];

  // クイックリンク
  const quickLinks = [
    { name: 'プロジェクト作成', href: '/projects/new', description: '新しいプロジェクトを作成して、セッションを管理します。' },
    { name: 'セッションインポート', href: '/sessions/new', description: 'GPSデータをインポートして新しいセッションを作成します。' },
    { name: 'データ分析', href: '/dashboard', description: '既存のデータを分析して、インサイトを得ます。' },
    { name: 'ヘルプガイド', href: '/help', description: 'アプリケーションの使い方を学びます。' },
  ];

  return (
    <Layout useSidebar={false}>
      {/* ヒーローセクション */}
      <div className="bg-white">
        <div className="max-w-7xl mx-auto py-16 px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="text-4xl font-extrabold tracking-tight text-gray-900 sm:text-5xl">
              セーリング戦略分析システム
            </h1>
            <p className="mt-4 max-w-2xl mx-auto text-xl text-gray-500">
              GPSデータを活用して風向風速を推定し、セーリング競技者の意思決定を客観的に評価するツール
            </p>
            <div className="mt-8 flex justify-center">
              <Button
                variant="primary"
                onClick={() => router.push('/dashboard')}
                className="px-8 py-3 text-base font-medium"
              >
                ダッシュボードへ
              </Button>
              <Button
                variant="secondary"
                onClick={() => router.push('/projects')}
                className="ml-4 px-8 py-3 text-base font-medium"
              >
                プロジェクト一覧
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* 機能紹介セクション */}
      <div className="bg-gray-50 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-extrabold text-gray-900 text-center mb-12">
            主な機能
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature, index) => (
              <div
                key={index}
                className="bg-white p-6 rounded-lg shadow-md transition-transform duration-300 hover:transform hover:scale-105"
              >
                <div className="flex justify-center mb-4">
                  {feature.icon}
                </div>
                <h3 className="text-xl font-bold text-gray-900 text-center mb-2">
                  {feature.title}
                </h3>
                <p className="text-gray-600 text-center">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* クイックリンクセクション */}
      <div className="bg-white py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-extrabold text-gray-900 text-center mb-8">
            クイックスタート
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {quickLinks.map((link, index) => (
              <Card
                key={index}
                hoverable
                onClick={() => router.push(link.href)}
              >
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  {link.name}
                </h3>
                <p className="text-gray-600">{link.description}</p>
              </Card>
            ))}
          </div>
        </div>
      </div>

      {/* CTA セクション */}
      <div className="bg-blue-600">
        <div className="max-w-7xl mx-auto py-12 px-4 sm:px-6 lg:py-16 lg:px-8 lg:flex lg:items-center lg:justify-between">
          <h2 className="text-3xl font-extrabold tracking-tight text-white sm:text-4xl">
            <span className="block">セーリングパフォーマンスを向上させましょう</span>
            <span className="block text-blue-200">今すぐデータを分析して、インサイトを得ましょう。</span>
          </h2>
          <div className="mt-8 flex lg:mt-0 lg:flex-shrink-0">
            <div className="inline-flex rounded-md shadow">
              <Button
                variant="secondary"
                onClick={() => router.push('/sessions/new')}
                className="px-5 py-3 text-base font-medium"
              >
                データをインポート
              </Button>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}