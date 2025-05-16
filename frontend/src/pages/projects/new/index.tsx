'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/router';
import Button from '../../../components/common/Button';
import Card from '../../../components/common/Card';
import Input from '../../../components/forms/Input';
import { api } from '../../../lib/api';
import LoadingSpinner from '../../../components/common/LoadingSpinner';

export default function NewProjectPage() {
  const router = useRouter();
  const [projectName, setProjectName] = useState('');
  const [description, setDescription] = useState('');
  const [tags, setTags] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // プロジェクト作成処理
  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!projectName) {
      setError('プロジェクト名を入力してください');
      return;
    }
    
    setIsSubmitting(true);
    setError(null);
    
    try {
      // APIリクエスト
      const response = await api.createProject({
        name: projectName,
        description,
        tags: tags.split(',').map(tag => tag.trim()).filter(tag => tag),
      });
      
      // 成功したらプロジェクト一覧画面に遷移
      router.push('/projects');
    } catch (err: any) {
      console.error('Project creation error:', err);
      setError(err.message || 'プロジェクトの作成に失敗しました');
    } finally {
      setIsSubmitting(false);
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
            variant="ghost"
            onClick={() => router.push('/projects')}
          >
            プロジェクト一覧
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
        <div className="max-w-2xl mx-auto">
          <Card title="新規プロジェクト作成" variant="dark">
            <div className="p-4">
              {isSubmitting ? (
                <div className="flex flex-col items-center justify-center py-8">
                  <LoadingSpinner size="large" color="blue" />
                  <p className="mt-4 text-gray-400">プロジェクトを作成しています...</p>
                </div>
              ) : (
                <form onSubmit={handleCreateProject}>
                  <div className="space-y-6">
                    <div>
                      <label htmlFor="projectName" className="block text-sm font-medium text-gray-300 mb-1">
                        プロジェクト名 *
                      </label>
                      <Input
                        id="projectName"
                        value={projectName}
                        onChange={(e) => setProjectName(e.target.value)}
                        placeholder="例: 2025年春季練習"
                        required
                      />
                    </div>
                    
                    <div>
                      <label htmlFor="description" className="block text-sm font-medium text-gray-300 mb-1">
                        説明
                      </label>
                      <Input
                        id="description"
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                        placeholder="例: 2025年春の練習セッション集"
                        multiline
                        rows={3}
                      />
                    </div>
                    
                    <div>
                      <label htmlFor="tags" className="block text-sm font-medium text-gray-300 mb-1">
                        タグ（カンマ区切り）
                      </label>
                      <Input
                        id="tags"
                        value={tags}
                        onChange={(e) => setTags(e.target.value)}
                        placeholder="例: 練習,春季,2025"
                      />
                      <p className="mt-1 text-xs text-gray-500">
                        複数のタグはカンマで区切ってください。タグを使用すると検索やフィルタリングが容易になります。
                      </p>
                    </div>
                    
                    {error && (
                      <div className="p-3 bg-red-900 bg-opacity-50 border border-red-800 rounded text-red-200">
                        <div className="flex items-start">
                          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                          </svg>
                          <span>{error}</span>
                        </div>
                      </div>
                    )}
                    
                    <div className="flex justify-end space-x-3">
                      <Button
                        variant="ghost"
                        onClick={() => router.push('/projects')}
                        type="button"
                      >
                        キャンセル
                      </Button>
                      <Button
                        variant="primary"
                        type="submit"
                        disabled={isSubmitting}
                      >
                        プロジェクトを作成
                      </Button>
                    </div>
                  </div>
                </form>
              )}
            </div>
          </Card>
          
          <Card
            title="プロジェクトについて"
            variant="dark"
            className="mt-6"
          >
            <div className="p-4">
              <p className="text-gray-400">
                プロジェクトはセッションを整理するためのコンテナです。関連するセーリングセッションをプロジェクトにグループ化できます。
              </p>
              <ul className="mt-4 list-disc list-inside space-y-2 text-gray-400">
                <li>一つのプロジェクトに複数のセッションを含めることができます</li>
                <li>タグを使ってプロジェクトを検索・整理できます</li>
                <li>プロジェクト間で比較分析を行うことができます</li>
                <li>プロジェクトを階層化して整理することも可能です</li>
              </ul>
            </div>
          </Card>
        </div>
      </main>
    </div>
  );
}
