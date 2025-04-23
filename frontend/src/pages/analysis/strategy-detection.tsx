import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Layout from '../../components/common/Layout';
import Button from '../../components/common/Button';
import Card from '../../components/common/Card';
import { strategyDetectionApi } from '../../lib/api';
import Select from '../../components/forms/Select';
import Input from '../../components/forms/Input';
import Alert from '../../components/common/Alert';

// 戦略検出パラメータの型定義
interface StrategyDetectionParams {
  session_id: string;
  detection_sensitivity: number;
  min_tack_angle: number;
  min_jibe_angle: number;
  strategy_types?: string[];
}

// 戦略ポイントの型定義
interface StrategyPoint {
  timestamp: number;
  latitude: number;
  longitude: number;
  strategy_type: string;
  confidence: number;
  metadata?: any;
}

// 戦略検出結果の型定義
interface StrategyDetectionResult {
  strategy_points: StrategyPoint[];
  created_at: string;
  session_id: string;
  track_length?: number;
  total_tacks?: number;
  total_jibes?: number;
  upwind_percentage?: number;
  downwind_percentage?: number;
  reaching_percentage?: number;
  performance_score?: number;
  recommendations?: string[];
}

// 戦略検出ページコンポーネント
export default function StrategyDetectionPage() {
  const router = useRouter();
  const { session_id } = router.query;
  
  // ステート定義
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<StrategyDetectionResult | null>(null);
  const [params, setParams] = useState<StrategyDetectionParams>({
    session_id: '',
    detection_sensitivity: 0.5,
    min_tack_angle: 45,
    min_jibe_angle: 45
  });

  // セッションIDがクエリパラメータから取得されたら更新
  useEffect(() => {
    if (session_id) {
      setParams(prev => ({
        ...prev,
        session_id: session_id as string
      }));
    }
  }, [session_id]);

  // パラメータの更新ハンドラ
  const handleParamChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    setParams({
      ...params,
      [name]: type === 'number' ? parseFloat(value) : value
    });
  };

  // フォーム送信ハンドラ
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!params.session_id) {
      setError('セッションIDが必要です');
      return;
    }
    
    setIsLoading(true);
    setError(null);
    
    try {
      // 戦略検出APIの呼び出し
      const response = await strategyDetectionApi.detectStrategies(params);
      setResult(response.data);
      console.log('Strategy detection result:', response.data);
    } catch (err: any) {
      console.error('戦略検出エラー:', err);
      setError(err.message || 'エラーが発生しました。もう一度お試しください。');
    } finally {
      setIsLoading(false);
    }
  };

  // プロジェクト詳細ページへ移動
  const navigateToProjectDetail = () => {
    if (result?.session_id) {
      router.push({
        pathname: '/projects/sessions',
        query: { session_id: result.session_id }
      });
    }
  };

  return (
    <Layout>
      <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        <h1 className="text-3xl font-bold text-gray-900">戦略検出</h1>
        <p className="mt-2 text-gray-600">セッションデータから戦略ポイントを検出します。</p>
        
        <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
          {/* 入力フォーム */}
          <Card>
            <h2 className="text-xl font-semibold text-gray-900 mb-4">パラメータ設定</h2>
            <form onSubmit={handleSubmit}>
              {/* セッションID */}
              <div className="mb-4">
                <label htmlFor="session_id" className="block text-sm font-medium text-gray-700 mb-1">
                  セッションID
                </label>
                <Input
                  type="text"
                  id="session_id"
                  name="session_id"
                  value={params.session_id}
                  onChange={handleParamChange}
                  disabled={!!session_id}
                  required
                />
                {session_id && (
                  <p className="mt-1 text-sm text-gray-500">
                    風向風速推定から自動設定されました
                  </p>
                )}
              </div>
              
              {/* 検出感度 */}
              <div className="mb-4">
                <label htmlFor="detection_sensitivity" className="block text-sm font-medium text-gray-700 mb-1">
                  検出感度 (0-1)
                </label>
                <Input
                  type="number"
                  id="detection_sensitivity"
                  name="detection_sensitivity"
                  value={params.detection_sensitivity.toString()}
                  onChange={handleParamChange}
                  min={0}
                  max={1}
                  step={0.1}
                />
              </div>
              
              {/* 最小タック角度 */}
              <div className="mb-4">
                <label htmlFor="min_tack_angle" className="block text-sm font-medium text-gray-700 mb-1">
                  最小タック角度 (度)
                </label>
                <Input
                  type="number"
                  id="min_tack_angle"
                  name="min_tack_angle"
                  value={params.min_tack_angle.toString()}
                  onChange={handleParamChange}
                  min={15}
                  max={90}
                  step={5}
                />
              </div>
              
              {/* 最小ジャイブ角度 */}
              <div className="mb-4">
                <label htmlFor="min_jibe_angle" className="block text-sm font-medium text-gray-700 mb-1">
                  最小ジャイブ角度 (度)
                </label>
                <Input
                  type="number"
                  id="min_jibe_angle"
                  name="min_jibe_angle"
                  value={params.min_jibe_angle.toString()}
                  onChange={handleParamChange}
                  min={15}
                  max={90}
                  step={5}
                />
              </div>
              
              {/* 送信ボタン */}
              <div className="mt-6">
                <Button
                  type="submit"
                  variant="primary"
                  isLoading={isLoading}
                  disabled={!params.session_id || isLoading}
                  fullWidth
                >
                  戦略検出を実行
                </Button>
              </div>
              
              {/* エラーメッセージ */}
              {error && (
                <Alert variant="error" className="mt-4">
                  {error}
                </Alert>
              )}
            </form>
          </Card>
          
          {/* 結果表示 */}
          <Card>
            <h2 className="text-xl font-semibold text-gray-900 mb-4">検出結果</h2>
            {isLoading ? (
              <div className="flex justify-center items-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
              </div>
            ) : result ? (
              <div>
                <div className="mb-4">
                  <h3 className="text-lg font-medium text-gray-900 mb-2">航跡統計</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-gray-50 p-3 rounded-md">
                      <p className="text-sm text-gray-500">検出戦略ポイント</p>
                      <p className="text-2xl font-bold">{result.strategy_points.length}</p>
                    </div>
                    <div className="bg-gray-50 p-3 rounded-md">
                      <p className="text-sm text-gray-500">総航跡距離</p>
                      <p className="text-2xl font-bold">{result.track_length ? 
                        `${(result.track_length / 1000).toFixed(2)} km` : 'N/A'}</p>
                    </div>
                  </div>
                </div>
                
                <div className="mb-4">
                  <h3 className="text-lg font-medium text-gray-900 mb-2">マニューバー統計</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-gray-50 p-3 rounded-md">
                      <p className="text-sm text-gray-500">タック回数</p>
                      <p className="text-2xl font-bold">{result.total_tacks || 'N/A'}</p>
                    </div>
                    <div className="bg-gray-50 p-3 rounded-md">
                      <p className="text-sm text-gray-500">ジャイブ回数</p>
                      <p className="text-2xl font-bold">{result.total_jibes || 'N/A'}</p>
                    </div>
                  </div>
                </div>
                
                {result.performance_score !== undefined && (
                  <div className="mb-4">
                    <h3 className="text-lg font-medium text-gray-900 mb-2">パフォーマンススコア</h3>
                    <div className="bg-gray-50 p-3 rounded-md">
                      <div className="flex items-center">
                        <div className="w-full bg-gray-200 rounded-full h-2.5">
                          <div 
                            className="bg-blue-600 h-2.5 rounded-full" 
                            style={{ width: `${result.performance_score}%` }}
                          ></div>
                        </div>
                        <span className="ml-3 text-lg font-bold">{result.performance_score.toFixed(0)}</span>
                      </div>
                    </div>
                  </div>
                )}
                
                {result.recommendations && result.recommendations.length > 0 && (
                  <div className="mb-4">
                    <h3 className="text-lg font-medium text-gray-900 mb-2">推奨事項</h3>
                    <ul className="bg-gray-50 p-3 rounded-md list-disc list-inside space-y-1">
                      {result.recommendations.map((recommendation, index) => (
                        <li key={index} className="text-sm text-gray-700">{recommendation}</li>
                      ))}
                    </ul>
                  </div>
                )}
                
                <div className="mt-6">
                  <Button
                    variant="secondary"
                    onClick={navigateToProjectDetail}
                  >
                    セッション詳細へ
                  </Button>
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-64 text-gray-500">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
                <p>パラメータを設定して戦略検出を実行してください。</p>
              </div>
            )}
          </Card>
        </div>
      </div>
    </Layout>
  );
}