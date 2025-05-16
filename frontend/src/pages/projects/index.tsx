'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Button from '../../components/common/Button';
import Card from '../../components/common/Card';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ProjectList from '../../components/project/ProjectList';
import { api } from '../../lib/api';

export default function ProjectsPage() {
  const router = useRouter();
  const [projects, setProjects] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // プロジェクト一覧を取得
  useEffect(() => {
    const fetchProjects = async () => {
      try {
        // MVPでは簡易的に実装
        // 本来はページネーションなどが必要
        const response = await api.getProjects();
        setProjects(response.data.items || []);
      } catch (err: any) {
        console.error('Error fetching projects:', err);
        setError(err.message || 'プロジェクトの取得に失敗しました');
      } finally {
        setLoading(false);
      }
    };

    fetchProjects();
  }, []);

  // プロジェクト削除処理
  const handleDeleteProject = async (projectId: string) => {
    try {
      await api.deleteProject(projectId);
      // 一覧を更新
      setProjects(projects.filter(project => project.id !== projectId));
    } catch (err: any) {
      console.error('Error deleting project:', err);
      alert(`削除に失敗しました: ${err.message || '不明なエラー'}`);
    }
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
            variant="primary"
            onClick={() => router.push('/projects/new')}
          >
            新規プロジェクト
          </Button>
          <Button
            variant="ghost"
            onClick={() => router.push('/')}
          >
            ホームに戻る
          </Button>
        </div>
      </header>

      <main className="container mx-auto py-8 px-4">
        <div className="mb-6 flex justify-between items-center">
          <h2 className="text-2xl font-semibold text-gray-100">プロジェクト一覧</h2>
          <div className="flex space-x-2">
            {/* 将来的に検索やフィルタリング機能を追加 */}
          </div>
        </div>

        {loading ? (
          <div className="flex flex-col items-center justify-center py-12">
            <LoadingSpinner size="large" color="blue" />
            <p className="mt-4 text-gray-400">プロジェクトを読み込んでいます...</p>
          </div>
        ) : error ? (
          <Card variant="dark">
            <div className="p-4">
              <div className="p-3 bg-red-900 bg-opacity-50 border border-red-800 rounded text-red-200">
                <div className="flex items-start">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                  <span>{error}</span>
                </div>
              </div>
              <div className="mt-4 flex justify-center">
                <Button
                  variant="primary"
                  onClick={() => window.location.reload()}
                >
                  再読み込み
                </Button>
              </div>
            </div>
          </Card>
        ) : projects.length === 0 ? (
          <Card variant="dark">
            <div className="p-8 text-center">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-16 w-16 mx-auto text-gray-600 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
              </svg>
              <h3 className="text-xl font-medium text-gray-400 mb-2">プロジェクトがありません</h3>
              <p className="text-gray-500 mb-6">
                まだプロジェクトが作成されていません。<br />
                「新規プロジェクト」ボタンをクリックして最初のプロジェクトを作成しましょう。
              </p>
              <Button
                variant="primary"
                onClick={() => router.push('/projects/new')}
              >
                新規プロジェクト作成
              </Button>
            </div>
          </Card>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {/* MVPでは実装が間に合わない可能性があるため、シンプルな代替表示 */}
            {projects.map((project) => (
              <Card key={project.id} variant="dark" className="h-full">
                <div className="p-4 flex flex-col h-full">
                  <h3 className="text-lg font-medium text-blue-300">{project.name}</h3>
                  {project.description && (
                    <p className="text-gray-400 mt-2 flex-grow">{project.description}</p>
                  )}
                  <div className="mt-4 flex flex-wrap gap-2">
                    {project.tags && project.tags.map((tag: string) => (
                      <span key={tag} className="inline-block px-2 py-1 text-xs bg-gray-800 text-gray-300 rounded">
                        {tag}
                      </span>
                    ))}
                  </div>
                  <div className="mt-4 pt-3 border-t border-gray-700 flex justify-between">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => router.push(`/projects/${project.id}`)}
                    >
                      詳細
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        if (confirm('このプロジェクトを削除しますか？')) {
                          handleDeleteProject(project.id);
                        }
                      }}
                    >
                      削除
                    </Button>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
