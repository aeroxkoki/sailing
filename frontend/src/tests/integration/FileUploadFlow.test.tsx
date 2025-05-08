import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import axios from 'axios';
import MockAdapter from 'axios-mock-adapter';
import HomePage from '@/pages/index';
import { SettingsProvider } from '@/context/SettingsContext';
import { AnalysisProvider } from '@/context/AnalysisContext';

// モックレスポンスデータ
const mockAnalysisResponse = {
  sessionId: 'test-session-123',
  fileName: 'test.gpx',
  startTime: 1683111600000,
  endTime: 1683118800000,
  currentTime: 1683111600000,
  gpsData: [
    { 
      timestamp: 1683111600000, 
      latitude: 35.123, 
      longitude: 139.456, 
      speed: 5.2, 
      heading: 270 
    },
    // 他のポイントデータ...
  ],
  windData: [
    {
      timestamp: 1683111600000,
      latitude: 35.123,
      longitude: 139.456,
      direction: 230,
      speed: 12.3
    },
    // 他の風データ...
  ],
  strategyPoints: [
    {
      id: 'sp1',
      timestamp: 1683112200000,
      latitude: 35.125,
      longitude: 139.458,
      type: 'tack',
      details: { speedLoss: 1.2 }
    },
    // 他の戦略ポイント...
  ],
  averageWindDirection: 230.5,
  averageWindSpeed: 12.3,
  upwindVMG: 4.5,
  downwindVMG: 5.8,
  trackLength: 12.5,
  totalTacks: 8,
  totalJibes: 3,
  performanceScore: 0.78
};

// Axiosのモックセットアップ
const mockAxios = new MockAdapter(axios);

// テスト用にグローバルモックを設定
jest.mock('maplibre-gl', () => ({
  Map: jest.fn(() => ({
    on: jest.fn((event, callback) => {
      if (event === 'load') {
        callback();
      }
      return this;
    }),
    addSource: jest.fn(),
    addLayer: jest.fn(),
    getSource: jest.fn(() => ({
      setData: jest.fn()
    })),
    remove: jest.fn(),
    addControl: jest.fn()
  })),
  NavigationControl: jest.fn()
}));

// ローカルストレージのモック
const localStorageMock = (() => {
  let store = {};
  return {
    getItem: jest.fn(key => store[key] || null),
    setItem: jest.fn((key, value) => {
      store[key] = value.toString();
    }),
    removeItem: jest.fn(key => {
      delete store[key];
    }),
    clear: jest.fn(() => {
      store = {};
    })
  };
})();
Object.defineProperty(window, 'localStorage', { value: localStorageMock });

describe('File Upload Flow Integration Test', () => {
  beforeEach(() => {
    mockAxios.reset();
    jest.clearAllMocks();
  });

  it('renders upload screen initially', () => {
    render(
      <SettingsProvider>
        <AnalysisProvider>
          <HomePage />
        </AnalysisProvider>
      </SettingsProvider>
    );
    
    expect(screen.getByText(/GPSログをアップロード/i)).toBeInTheDocument();
  });

  it('shows loading state during file upload and analysis', async () => {
    // 分析APIエンドポイントのモック設定（遅延付き）
    mockAxios.onPost('/analyze').reply(() => {
      return new Promise(resolve => {
        setTimeout(() => {
          resolve([200, mockAnalysisResponse]);
        }, 100);
      });
    });

    render(
      <SettingsProvider>
        <AnalysisProvider>
          <HomePage />
        </AnalysisProvider>
      </SettingsProvider>
    );
    
    // ファイルアップロード
    const file = new File(['test data'], 'test.gpx', { type: 'application/gpx+xml' });
    const fileInput = screen.getByRole('textbox', { hidden: true });
    await userEvent.upload(fileInput, file);
    
    // ローディング表示の確認
    expect(await screen.findByText(/データ分析中/i)).toBeInTheDocument();
    
    // 分析結果表示への遷移を確認
    await waitFor(() => {
      expect(screen.queryByText(/データ分析中/i)).not.toBeInTheDocument();
    });
  });

  it('displays analysis results after successful upload', async () => {
    // 分析APIエンドポイントのモック設定
    mockAxios.onPost('/analyze').reply(200, mockAnalysisResponse);

    render(
      <SettingsProvider>
        <AnalysisProvider>
          <HomePage />
        </AnalysisProvider>
      </SettingsProvider>
    );
    
    // ファイルアップロード
    const file = new File(['test data'], 'test.gpx', { type: 'application/gpx+xml' });
    const fileInput = screen.getByRole('textbox', { hidden: true });
    await userEvent.upload(fileInput, file);
    
    // 分析結果画面の表示を確認
    await waitFor(() => {
      expect(screen.getByText(/230.5°/)).toBeInTheDocument(); // 平均風向
      expect(screen.getByText(/12.3 kts/)).toBeInTheDocument(); // 平均風速
    });
  });

  it('displays error message when upload fails', async () => {
    // エラーレスポンスのモック設定
    mockAxios.onPost('/analyze').reply(400, {
      message: 'Invalid file format or corrupted data'
    });

    render(
      <SettingsProvider>
        <AnalysisProvider>
          <HomePage />
        </AnalysisProvider>
      </SettingsProvider>
    );
    
    // ファイルアップロード
    const file = new File(['invalid data'], 'corrupt.gpx', { type: 'application/gpx+xml' });
    const fileInput = screen.getByRole('textbox', { hidden: true });
    await userEvent.upload(fileInput, file);
    
    // エラーメッセージの表示を確認
    await waitFor(() => {
      expect(screen.getByText(/エラーが発生しました/i)).toBeInTheDocument();
      expect(screen.getByText(/Invalid file format or corrupted data/i)).toBeInTheDocument();
    });
  });

  it('toggles between different views after analysis', async () => {
    // 分析APIエンドポイントのモック設定
    mockAxios.onPost('/analyze').reply(200, mockAnalysisResponse);

    render(
      <SettingsProvider>
        <AnalysisProvider>
          <HomePage />
        </AnalysisProvider>
      </SettingsProvider>
    );
    
    // ファイルアップロード
    const file = new File(['test data'], 'test.gpx', { type: 'application/gpx+xml' });
    const fileInput = screen.getByRole('textbox', { hidden: true });
    await userEvent.upload(fileInput, file);
    
    // 分析結果画面が表示されるのを待つ
    await waitFor(() => {
      expect(screen.getByText(/230.5°/)).toBeInTheDocument();
    });
    
    // ビューの切り替えボタンを探す
    const windButton = screen.getByText(/風向風速/i);
    const strategyButton = screen.getByText(/戦略/i);
    
    // 風向風速ビューに切り替え
    fireEvent.click(windButton);
    
    // 戦略ビューに切り替え
    fireEvent.click(strategyButton);
    
    // ビュー切り替えが正常に行われたことを確認（特定の要素が表示されるかなど）
    // 注: ビュー切り替えに応じた実際の要素の確認は、実装によって異なります
  });
});
