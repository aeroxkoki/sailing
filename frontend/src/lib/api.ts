import axios, { AxiosInstance, AxiosResponse } from 'axios';
import { AppSettings, ApiError } from '../types';

// APIクライアントの設定
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Axios インスタンスの作成
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30秒タイムアウト
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  }
});

// リクエストインターセプター
apiClient.interceptors.request.use(
  (config) => {
    // JWTトークンがある場合はヘッダーに追加（クライアントサイドのみで実行）
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('auth_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// レスポンスインターセプター
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // エラーハンドリング
    if (error.response) {
      // サーバーからのレスポンスがある場合
      const { status, data } = error.response;
      
      // 認証エラー時の処理
      if (status === 401) {
        if (typeof window !== 'undefined') {
          localStorage.removeItem('auth_token');
          // 必要に応じてリダイレクト
        }
      }
      
      // エラーメッセージの整形
      const message = data.message || data.error || '不明なエラーが発生しました';
      return Promise.reject({ status, message, data } as ApiError);
    } else if (error.request) {
      // リクエストは送信されたがレスポンスがない場合
      return Promise.reject({ 
        status: 0, 
        message: 'サーバーに接続できません。ネットワーク接続を確認してください。' 
      } as ApiError);
    } else {
      // リクエスト設定中にエラーが発生した場合
      return Promise.reject({ 
        status: 0, 
        message: 'リクエストの送信中にエラーが発生しました。' 
      } as ApiError);
    }
  }
);

// APIエンドポイント関数
export const api = {
  // データアップロードと分析
  analyzeGpsData: async (file: File, settings?: Partial<AppSettings>): Promise<AxiosResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    
    // 設定パラメータの追加
    if (settings) {
      // 設定オブジェクトを適切なフォーマットに変換
      Object.entries(settings).forEach(([category, options]: [string, any]) => {
        Object.entries(options).forEach(([key, value]) => {
          // 配列や複雑なオブジェクトはJSON文字列に変換
          if (typeof value === 'object' && value !== null) {
            formData.append(`${category}.${key}`, JSON.stringify(value));
          } else {
            formData.append(`${category}.${key}`, String(value));
          }
        });
      });
    }
    
    return apiClient.post('/api/v1/analyze', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
  
  // 風向風速推定
  estimateWind: async (sessionId: string, settings?: Partial<AppSettings['wind']>): Promise<AxiosResponse> => {
    return apiClient.post(`/api/v1/sessions/${sessionId}/wind-estimation`, settings);
  },
  
  // 戦略ポイント検出
  detectStrategyPoints: async (sessionId: string, settings?: Partial<AppSettings['strategy']>): Promise<AxiosResponse> => {
    return apiClient.post(`/api/v1/sessions/${sessionId}/strategy-detection`, settings);
  },
  
  // 結果のエクスポート
  exportAnalysis: async (sessionId: string, format: 'pdf' | 'csv' | 'gpx' | 'json', includeSettings: boolean = true): Promise<AxiosResponse> => {
    return apiClient.get(`/api/v1/sessions/${sessionId}/export`, {
      params: { format, includeSettings },
      responseType: 'blob',
    });
  },
  
  // セッション情報取得
  getSession: async (sessionId: string): Promise<AxiosResponse> => {
    return apiClient.get(`/api/v1/sessions/${sessionId}`);
  },
  
  // セッション一覧取得
  getSessions: async (page = 1, limit = 10): Promise<AxiosResponse> => {
    return apiClient.get('/api/v1/sessions', {
      params: { page, limit }
    });
  },
};

export default api;
