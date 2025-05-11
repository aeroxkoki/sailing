import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Layout from '../../components/common/Layout';
import Button from '../../components/common/Button';
import Card from '../../components/common/Card';
import FileUpload from '../../components/forms/FileUpload';
import WindChart from '../../components/charts/WindChart';
import MapView from '../../components/analysis/MapView';
import Tabs from '../../components/common/Tabs';
import api from '../../lib/api';
import Select from '../../components/forms/Select';
import Input from '../../components/forms/Input';
import Alert from '../../components/common/Alert';
import { parseGPSFile, GPSPoint } from '../../lib/gps-utils';

// 風向風速推定パラメータの型定義
interface WindEstimationParams {
  boat_type: string;
  min_tack_angle: number;
  use_bayesian: boolean;
  file_format: string;
}

// 風データポイントの型定義
interface WindDataPoint {
  timestamp: number;
  speed: number;
  direction: number;
  confidence: number;
}

// 風向風速推定結果の型定義
interface WindEstimationResult {
  wind_data: WindDataPoint[];
  average_speed: number;
  average_direction: number;
  created_at: string;
  session_id: string;
}

// 風向風速推定ページコンポーネント
export default function WindEstimationPage() {
  const router = useRouter();
  
  // ステート定義
  const [file, setFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<WindEstimationResult | null>(null);
  const [gpsData, setGpsData] = useState<GPSPoint[]>([]);
  const [activeTab, setActiveTab] = useState<string>('chart');
  const [params, setParams] = useState<WindEstimationParams>({
    boat_type: 'default',
    min_tack_angle: 30,
    use_bayesian: true,
    file_format: 'csv'
  });

  // パラメータの更新ハンドラ（イベントオブジェクト用）
  const handleParamChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    setParams({
      ...params,
      [name]: type === 'checkbox' 
        ? (e.target as HTMLInputElement).checked 
        : type === 'number' 
          ? parseFloat(value) 
          : value
    });
  };
  
  // Selectコンポーネント用のパラメータ更新ハンドラ
  const handleSelectChange = (name: string) => (value: string) => {
    setParams({
      ...params,
      [name]: value
    });
  };

  // ファイル選択ハンドラ
  const handleFileChange = async (selectedFile: File | null) => {
    setFile(selectedFile);
    
    // ファイル形式の自動検出
    if (selectedFile) {
      const extension = selectedFile.name.split('.').pop()?.toLowerCase();
      if (extension === 'gpx' || extension === 'csv') {
        setParams({
          ...params,
          file_format: extension
        });
        
        // GPSデータの解析
        try {
          const parsedData = await parseGPSFile(selectedFile);
          setGpsData(parsedData);
          console.log(`GPSデータを解析しました: ${parsedData.length}ポイント`);
        } catch (err) {
          console.error('GPSデータ解析エラー:', err);
          setError('GPSデータの解析に失敗しました。ファイル形式を確認してください。');
        }
      }
    } else {
      setGpsData([]);
    }
  };

  // フォーム送信ハンドラ
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!file) {
      setError('ファイルを選択してください');
      return;
    }
    
    setIsLoading(true);
    setError(null);
    
    try {
      // 風向風速推定APIの呼び出し
      const windSettings = {
        algorithm: params.use_bayesian ? 'bayesian' : 'simple' as 'simple' | 'bayesian' | 'combined',
        minTackAngle: params.min_tack_angle,
        useShiftDetection: true,
        smoothingFactor: 50
      };
      const response = await api.analyzeGpsData(file, { wind: windSettings });
      setResult(response.data);
      console.log('Wind estimation result:', response.data);
    } catch (err: any) {
      console.error('風向風速推定エラー:', err);
      setError(err.message || 'エラーが発生しました。もう一度お試しください。');
    } finally {
      setIsLoading(false);
    }
  };

  // 戦略検出ページへ移動
  const navigateToStrategyDetection = () => {
    if (result?.session_id) {
      router.push({
        pathname: '/analysis/strategy-detection',
        query: { session_id: result.session_id }
      });
    }
  };

  return (
    <Layout>
      <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        <h1 className="text-3xl font-bold text-gray-900">風向風速推定</h1>
        <p className="mt-2 text-gray-600">GPSデータをアップロードして風向風速を推定します。</p>
        
        <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
          {/* 入力フォーム */}
          <Card>
            <h2 className="text-xl font-semibold text-gray-900 mb-4">パラメータ設定</h2>
            <form onSubmit={handleSubmit}>
              {/* ファイルアップロード */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  GPSデータファイル
                </label>
                <FileUpload
                  accept=".csv,.gpx"
                  onChange={handleFileChange}
                  maxSize={10} // 10MB
                />
                {file && (
                  <p className="mt-1 text-sm text-gray-500">
                    選択ファイル: {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
                  </p>
                )}
              </div>
              
              {/* 艇種選択 */}
              <div className="mb-4">
                <label htmlFor="boat_type" className="block text-sm font-medium text-gray-700 mb-1">
                  艇種
                </label>
                <Select
                  id="boat_type"
                  name="boat_type"
                  value={params.boat_type}
                  onChange={handleSelectChange("boat_type")}
                  options={[
                    { value: 'default', label: 'デフォルト' },
                    { value: 'laser', label: 'レーザー' },
                    { value: 'optimist', label: 'オプティミスト' },
                    { value: '470', label: '470' },
                    { value: '49er', label: '49er' }
                  ]}
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
              
              {/* ベイズ推定使用フラグ */}
              <div className="mb-4">
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="use_bayesian"
                    name="use_bayesian"
                    checked={params.use_bayesian}
                    onChange={handleParamChange}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label htmlFor="use_bayesian" className="ml-2 block text-sm text-gray-700">
                    ベイズ推定を使用する
                  </label>
                </div>
              </div>
              
              {/* ファイル形式 */}
              <div className="mb-4">
                <label htmlFor="file_format" className="block text-sm font-medium text-gray-700 mb-1">
                  ファイル形式
                </label>
                <Select
                  id="file_format"
                  name="file_format"
                  value={params.file_format}
                  onChange={handleSelectChange("file_format")}
                  options={[
                    { value: 'csv', label: 'CSV' },
                    { value: 'gpx', label: 'GPX' }
                  ]}
                />
              </div>
              
              {/* 送信ボタン */}
              <div className="mt-6">
                <Button
                  type="submit"
                  variant="primary"
                  isLoading={isLoading}
                  disabled={!file || isLoading}
                  fullWidth
                >
                  風向風速を推定
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
            <h2 className="text-xl font-semibold text-gray-900 mb-4">推定結果</h2>
            {isLoading ? (
              <div className="flex justify-center items-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
              </div>
            ) : result ? (
              <div>
                <div className="mb-4">
                  <h3 className="text-lg font-medium text-gray-900 mb-2">推定風向風速</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-gray-50 p-3 rounded-md">
                      <p className="text-sm text-gray-500">平均風向</p>
                      <p className="text-2xl font-bold">{result.average_direction.toFixed(1)}°</p>
                    </div>
                    <div className="bg-gray-50 p-3 rounded-md">
                      <p className="text-sm text-gray-500">平均風速</p>
                      <p className="text-2xl font-bold">{result.average_speed.toFixed(1)}ノット</p>
                    </div>
                  </div>
                </div>
                
                  {/* タブ切り替え */}
                <Tabs
                  tabs={[
                    { id: 'chart', label: 'チャート' },
                    { id: 'map', label: 'マップ' },
                  ]}
                  activeTab={activeTab}
                  onChange={setActiveTab}
                />
                
                <div className="mt-4">
                  {activeTab === 'chart' ? (
                    <div className="h-64">
                      <WindChart data={result.wind_data} />
                    </div>
                  ) : (
                    <div className="h-80">
                      <MapView
                        gpsData={gpsData || []}
                        windData={result.wind_data}
                        height="320px"
                      />
                    </div>
                  )}
                </div>
                
                <div className="mt-6">
                  <Button
                    variant="secondary"
                    onClick={navigateToStrategyDetection}
                  >
                    戦略検出へ進む
                  </Button>
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-64 text-gray-500">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
                <p>GPSデータをアップロードして風向風速を推定してください。</p>
              </div>
            )}
          </Card>
        </div>
      </div>
    </Layout>
  );
}