'use client';

import React, { useState, useEffect, useRef } from 'react';
import Layout from '@/components/common/Layout';
import MapView from '@/components/map/MapView';
import TrackLayer from '@/components/map/TrackLayer';
import WindLayer from '@/components/map/WindLayer';
import StrategyPointLayer from '@/components/map/StrategyPointLayer';
import AnalysisPanel from '@/components/analysis/AnalysisPanel';
import LoadingSpinner from '@/components/common/LoadingSpinner';
import SettingsPanel from '@/components/settings/SettingsPanel';
import { AnalysisData } from '@/types/analysis';
import { GpsPoint, WindDataPoint, StrategyPoint, StrategyPointType } from '@/types/gps';

// デモ用のサンプルデータ
const SAMPLE_DATA: AnalysisData = {
  sessionId: 'demo-session-001',
  fileName: 'demo-sailing-data.gpx',
  startTime: Date.now() - 3600000, // 1時間前
  endTime: Date.now(),
  currentTime: Date.now() - 1800000, // 30分前（中間点）
  gpsData: generateSampleGpsData(500),
  windData: generateSampleWindData(100),
  strategyPoints: generateSampleStrategyPoints(20),
  averageWindDirection: 225, // 南西
  averageWindSpeed: 12,
  maxWindSpeed: 18,
  windStability: 0.75,
  averageSpeed: 6.5,
  maxSpeed: 9.2,
  upwindVMG: 4.2,
  downwindVMG: 5.8,
  trackLength: 8.5,
  totalTacks: 12,
  totalJibes: 8,
  tackEfficiency: 0.75,
  jibeEfficiency: 0.68,
  performanceScore: 0.72,
};

const AnalysisDemo: React.FC = () => {
  const [activeView, setActiveView] = useState<'track' | 'wind' | 'strategy'>('track');
  const [data, setData] = useState<AnalysisData>(SAMPLE_DATA);
  const [loading, setLoading] = useState(true);
  const [playing, setPlaying] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const mapRef = useRef<maplibregl.Map | null>(null);

  // マップのロード完了ハンドラ
  const handleMapLoaded = (map: maplibregl.Map) => {
    mapRef.current = map;
    setLoading(false);
  };

  // 時間変更ハンドラ
  const handleTimeChange = (time: number) => {
    setData(prev => ({
      ...prev,
      currentTime: time
    }));
  };

  // 初期データのロード（実際のアプリではAPIから）
  useEffect(() => {
    // デモでは少し遅延を入れてロード完了を示す
    const timer = setTimeout(() => {
      setLoading(false);
    }, 1500);
    
    return () => clearTimeout(timer);
  }, []);

  return (
    <Layout>
      <div className="relative w-full h-screen bg-black">
        {/* ローディングオーバーレイ */}
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-70 z-50">
            <LoadingSpinner size="large" />
            <span className="ml-4 text-xl text-gray-200">データを読み込み中...</span>
          </div>
        )}

        {/* マップエリア */}
        <div className="absolute inset-0">
          <MapView
            style="dark"
            onMapLoaded={handleMapLoaded}
          >
            {mapRef.current && (
              <>
                {/* アクティブなビューに応じたレイヤー表示 */}
                {activeView === 'track' && (
                  <TrackLayer
                    map={mapRef.current}
                    trackData={data.gpsData}
                    colorScheme="speed"
                    selectedTime={data.currentTime}
                  />
                )}
                
                {activeView === 'wind' && (
                  <WindLayer
                    map={mapRef.current}
                    windPoints={data.windData}
                    showHeatmap={true}
                    selectedTime={data.currentTime}
                  />
                )}
                
                {activeView === 'strategy' && (
                  <StrategyPointLayer
                    map={mapRef.current}
                    strategyPoints={data.strategyPoints}
                    showLabels={true}
                    selectedTime={data.currentTime}
                    onPointClick={(point) => {
                      console.log('Strategy point clicked:', point);
                      // ここで戦略ポイントの詳細を表示するモーダルを開くなどの処理
                    }}
                  />
                )}
              </>
            )}
          </MapView>
        </div>

        {/* 分析パネル */}
        <AnalysisPanel
          activeView={activeView}
          onViewChange={setActiveView}
          onSettingsOpen={() => setSettingsOpen(true)}
          data={data}
          onTimeChange={handleTimeChange}
          playing={playing}
          onPlayingChange={setPlaying}
        />

        {/* 設定パネル */}
        <SettingsPanel
          isOpen={settingsOpen}
          onClose={() => setSettingsOpen(false)}
          onApply={() => {
            // 設定適用時の処理
            setSettingsOpen(false);
            // 実際の実装では、設定を適用してデータを再分析するAPIを呼び出す
            console.log('設定を適用して再分析');
          }}
        />
      </div>
    </Layout>
  );
};

// サンプルGPSデータ生成関数
function generateSampleGpsData(count: number): GpsPoint[] {
  const points: GpsPoint[] = [];
  const startTime = SAMPLE_DATA.startTime;
  const endTime = SAMPLE_DATA.endTime;
  const duration = endTime - startTime;
  
  // 東京湾の座標周辺
  const centerLat = 35.5;
  const centerLon = 139.8;
  
  for (let i = 0; i < count; i++) {
    const progress = i / (count - 1);
    const timestamp = startTime + progress * duration;
    
    // 簡単な航跡の動きを生成（8の字）
    const angle = progress * Math.PI * 4;
    const radius = 0.05;
    const latOffset = Math.sin(angle) * radius;
    const lonOffset = Math.sin(angle * 2) * radius;
    
    // 速度変化
    const speedBase = 5 + Math.sin(angle * 3) * 2;
    const speed = Math.max(2, speedBase + Math.random() * 2);
    
    points.push({
      id: `gps-${i}`,
      timestamp,
      latitude: centerLat + latOffset,
      longitude: centerLon + lonOffset,
      speed,
      heading: (Math.atan2(
        Math.cos(angle) * radius,
        Math.cos(angle * 2) * 2 * radius
      ) * 180 / Math.PI + 360) % 360,
    });
  }
  
  return points;
}

// サンプル風データ生成関数
function generateSampleWindData(count: number): WindDataPoint[] {
  const points: WindDataPoint[] = [];
  const startTime = SAMPLE_DATA.startTime;
  const endTime = SAMPLE_DATA.endTime;
  const duration = endTime - startTime;
  
  // 東京湾の座標周辺（格子状に広げる）
  const centerLat = 35.5;
  const centerLon = 139.8;
  const gridSize = Math.ceil(Math.sqrt(count));
  const spacing = 0.1;
  
  for (let i = 0; i < count; i++) {
    const gridX = i % gridSize;
    const gridY = Math.floor(i / gridSize);
    
    const progress = i / (count - 1);
    const timestamp = startTime + progress * duration;
    
    // 風向と風速の変化（ゆっくりと変化する）
    const baseDirection = 225; // 南西
    const directionVariation = Math.sin(progress * Math.PI * 2) * 30;
    const direction = (baseDirection + directionVariation + 360) % 360;
    
    const baseSpeed = 12;
    const speedVariation = Math.sin(progress * Math.PI * 3) * 4;
    const speed = Math.max(5, baseSpeed + speedVariation + Math.random() * 2);
    
    points.push({
      id: `wind-${i}`,
      timestamp,
      latitude: centerLat - 0.05 + (gridX / gridSize) * spacing * 2,
      longitude: centerLon - 0.05 + (gridY / gridSize) * spacing * 2,
      direction,
      speed,
    });
  }
  
  return points;
}

// サンプル戦略ポイント生成関数
function generateSampleStrategyPoints(count: number): StrategyPoint[] {
  const points: StrategyPoint[] = [];
  const startTime = SAMPLE_DATA.startTime;
  const endTime = SAMPLE_DATA.endTime;
  const duration = endTime - startTime;
  
  // 戦略ポイントのタイプ配列（確率重みづけ）
  const types = [
    StrategyPointType.TACK,
    StrategyPointType.TACK,
    StrategyPointType.TACK,
    StrategyPointType.JIBE,
    StrategyPointType.JIBE,
    StrategyPointType.MARK_ROUNDING,
    StrategyPointType.WIND_SHIFT,
    StrategyPointType.WIND_SHIFT,
    StrategyPointType.LAYLINE,
  ];
  
  // スタートとフィニッシュを追加
  const gpsData = generateSampleGpsData(count * 10);
  
  // スタートポイント
  points.push({
    id: 'start-point',
    type: StrategyPointType.START,
    timestamp: startTime + 60000, // 1分後
    latitude: gpsData[10].latitude,
    longitude: gpsData[10].longitude,
    details: {
      name: 'スタート',
      description: 'レースのスタートポイント',
    },
    evaluation: {
      score: 0.85,
      comments: 'リーウェイ側からのよいスタート。タイミングがやや遅れた。',
    },
  });
  
  // フィニッシュポイント
  points.push({
    id: 'finish-point',
    type: StrategyPointType.FINISH,
    timestamp: endTime - 120000, // 終了2分前
    latitude: gpsData[gpsData.length - 20].latitude,
    longitude: gpsData[gpsData.length - 20].longitude,
    details: {
      name: 'フィニッシュ',
      description: 'レースのフィニッシュポイント',
    },
    evaluation: {
      score: 0.92,
      comments: 'クリーンなフィニッシュ。最終アプローチが良好。',
    },
  });
  
  // その他の戦略ポイント
  for (let i = 0; i < count - 2; i++) {
    const progress = (i + 1) / (count - 1);
    const timestamp = startTime + progress * duration * 0.9; // スタートとフィニッシュの間に分布
    
    // GPSデータからポイントを選択
    const gpsIndex = Math.floor(progress * gpsData.length * 0.9);
    
    // ランダムな戦略ポイントタイプ
    const typeIndex = Math.floor(Math.random() * types.length);
    const type = types[typeIndex];
    
    // 評価スコア（0.4〜1.0）
    const score = 0.4 + Math.random() * 0.6;
    
    // タイプに応じた詳細と評価
    let details: any = {};
    let evaluation: any = { score };
    
    switch (type) {
      case StrategyPointType.TACK:
        details = {
          name: 'タック',
          duration: 5 + Math.random() * 5,
          angleChange: 90 + Math.random() * 20,
        };
        evaluation.comments = score > 0.7 
          ? '効率的なタック。最小限の速度ロス。' 
          : 'タック中の速度ロスが大きい。スムーズさを改善する必要あり。';
        break;
        
      case StrategyPointType.JIBE:
        details = {
          name: 'ジャイブ',
          duration: 4 + Math.random() * 4,
          angleChange: 80 + Math.random() * 30,
        };
        evaluation.comments = score > 0.7 
          ? 'コントロールの効いたジャイブ。適切なタイミング。' 
          : 'ジャイブ時の不安定さが見られる。バランスに注意。';
        break;
        
      case StrategyPointType.MARK_ROUNDING:
        details = {
          name: 'マーク回航',
          markName: `Mark ${Math.floor(Math.random() * 5) + 1}`,
          distance: 5 + Math.random() * 10,
        };
        evaluation.comments = score > 0.7 
          ? '効率的なマーク回航。適切なアプローチ角度。' 
          : 'マーク接近が遅すぎる。早めの準備が必要。';
        break;
        
      case StrategyPointType.WIND_SHIFT:
        details = {
          name: '風向シフト',
          shiftAmount: Math.floor(Math.random() * 30 + 10),
          duration: Math.floor(Math.random() * 300 + 60),
        };
        evaluation.comments = score > 0.7 
          ? '風向シフトに対する素早い対応。好位置取り。' 
          : '風向シフトの認識が遅れた。より早い対応が必要。';
        break;
        
      case StrategyPointType.LAYLINE:
        details = {
          name: 'レイライン',
          markName: `Mark ${Math.floor(Math.random() * 5) + 1}`,
          distanceToMark: 50 + Math.random() * 100,
        };
        evaluation.comments = score > 0.7 
          ? '適切なレイライン判断。オーバースタンドを避けられた。' 
          : 'レイラインに対して遅すぎる判断。距離ロスが大きい。';
        break;
    }
    
    points.push({
      id: `strategy-${i}`,
      type,
      timestamp,
      latitude: gpsData[gpsIndex].latitude,
      longitude: gpsData[gpsIndex].longitude,
      details,
      evaluation,
    });
  }
  
  // 時間順にソート
  return points.sort((a, b) => a.timestamp - b.timestamp);
}

export default AnalysisDemo;