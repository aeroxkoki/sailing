import axios from 'axios';
import MockAdapter from 'axios-mock-adapter';
import api from '@/lib/api';

// Axiosのモックを作成
const mockAxios = new MockAdapter(axios);

describe('API Client', () => {
  afterEach(() => {
    // 各テスト後にモックをリセット
    mockAxios.reset();
  });

  describe('analyzeGpsData', () => {
    it('uploads file and returns analysis results', async () => {
      const mockResponse = {
        sessionId: 'test-session-123',
        fileName: 'test.gpx',
        startTime: 1683111600000,
        endTime: 1683118800000,
        averageWindDirection: 230.5,
        averageWindSpeed: 12.3,
      };

      // モックレスポンスを設定
      mockAxios.onPost('/analyze').reply(200, mockResponse);

      // テスト用のファイル作成
      const file = new File(['test data'], 'test.gpx', { type: 'application/gpx+xml' });
      
      // 設定オブジェクト
      const settings = {
        wind: {
          algorithm: 'combined',
          minTackAngle: 30,
        },
        strategy: {
          sensitivity: 70,
        },
      };

      // APIコール
      const response = await api.analyzeGpsData(file, settings);
      
      // レスポンスの検証
      expect(response.data).toEqual(mockResponse);
      
      // FormDataの検証はaxios-mock-adapterでは直接できないため省略
    });

    it('handles errors correctly', async () => {
      // エラーレスポンスを設定
      mockAxios.onPost('/analyze').reply(400, {
        message: 'Invalid file format',
      });

      const file = new File(['test data'], 'invalid.doc', { type: 'application/msword' });
      
      // エラーハンドリングの検証
      await expect(api.analyzeGpsData(file)).rejects.toEqual(
        expect.objectContaining({
          status: 400,
          message: 'Invalid file format',
        })
      );
    });
  });

  describe('estimateWind', () => {
    it('sends wind estimation request and returns results', async () => {
      const sessionId = 'test-session-123';
      const settings = {
        algorithm: 'bayesian',
        smoothingFactor: 50,
      };
      
      const mockResponse = {
        windData: [/* モックデータ */],
        averageWindDirection: 230.5,
        averageWindSpeed: 12.3,
      };
      
      mockAxios.onPost(`/sessions/${sessionId}/wind-estimation`).reply(200, mockResponse);
      
      const response = await api.estimateWind(sessionId, settings);
      expect(response.data).toEqual(mockResponse);
    });
  });

  describe('detectStrategyPoints', () => {
    it('sends strategy detection request and returns results', async () => {
      const sessionId = 'test-session-123';
      const settings = {
        sensitivity: 70,
        detectTypes: ['tack', 'jibe', 'mark'],
      };
      
      const mockResponse = {
        strategyPoints: [/* モックデータ */],
        totalTacks: 15,
        totalJibes: 8,
        performanceScore: 0.78,
      };
      
      mockAxios.onPost(`/sessions/${sessionId}/strategy-detection`).reply(200, mockResponse);
      
      const response = await api.detectStrategyPoints(sessionId, settings);
      expect(response.data).toEqual(mockResponse);
    });
  });

  describe('exportAnalysis', () => {
    it('requests file export and returns blob', async () => {
      const sessionId = 'test-session-123';
      const format = 'pdf';
      const mockBlob = new Blob(['test pdf content'], { type: 'application/pdf' });
      
      mockAxios.onGet(`/sessions/${sessionId}/export`, { params: { format } }).reply(200, mockBlob);
      
      const response = await api.exportAnalysis(sessionId, format);
      expect(response.data).toEqual(mockBlob);
    });
  });

  describe('token handling', () => {
    beforeEach(() => {
      // ローカルストレージのモック
      Storage.prototype.getItem = jest.fn().mockReturnValue('test-token');
    });
    
    it('includes auth token in request headers when available', async () => {
      mockAxios.onGet('/sessions').reply(config => {
        // ヘッダーにトークンが含まれているか確認
        expect(config.headers.Authorization).toBe('Bearer test-token');
        return [200, { items: [] }];
      });
      
      await api.getSessions();
    });
  });
});
