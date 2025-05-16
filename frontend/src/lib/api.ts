import axios, { AxiosInstance, AxiosResponse } from 'axios';
import { AppSettings, ApiError } from '../types';

// APIレスポンス型定義
export type ApiResponse<T = any> = AxiosResponse<T>;

// オフラインモードかどうかの判定フラグ（ローカルストレージに保存）
let isOfflineMode = false;
if (typeof window !== 'undefined') {
  isOfflineMode = localStorage.getItem('offlineMode') === 'true';
}

// APIクライアントの設定
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
console.log('API_BASE_URL:', API_BASE_URL); // デバッグ用

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
  // API接続の健全性チェック
  checkHealth: async (): Promise<{status: string; message?: string; offlineMode?: boolean}> => {
    // オフラインモードの場合は強制的にエラーを返さない
    if (isOfflineMode) {
      return { 
        status: 'warning', 
        message: 'オフラインモードでの実行中',
        offlineMode: true 
      };
    }
    
    try {
      // より短いタイムアウトを設定し、/api/v1/health/pingエンドポイントを試す
      const response = await apiClient.get('/api/v1/health/ping', { timeout: 3000 });
      return { status: 'ok', message: response.data.message || 'APIサーバーに接続できました' };
    } catch (error: any) {
      console.error('Health check error:', error);
      
      // 詳細なエラー情報をログ出力
      if (error.config) {
        console.log('Request config:', {
          url: error.config.url,
          baseURL: error.config.baseURL,
          timeout: error.config.timeout
        });
      }
      
      if (error.response) {
        return { status: 'error', message: `APIサーバーからエラーレスポンス: ${error.response.status}` };
      } else if (error.request) {
        return { status: 'error', message: 'APIサーバーに接続できません。サーバーが停止しているか、ネットワーク接続を確認してください。' };
      } else {
        return { status: 'error', message: '接続リクエストの作成中にエラーが発生しました。' };
      }
    }
  },
  
  // オフラインモードの切り替え
  toggleOfflineMode: (enabled: boolean): void => {
    if (typeof window !== 'undefined') {
      isOfflineMode = enabled;
      localStorage.setItem('offlineMode', enabled ? 'true' : 'false');
      console.log(`オフラインモードを${enabled ? '有効' : '無効'}にしました`);
    }
  },
  
  // オフラインモード状態の取得
  isOfflineMode: (): boolean => {
    return isOfflineMode;
  },
  
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
  
  // プロジェクト関連の機能
  
  // プロジェクト作成
  createProject: async (projectData: {
    name: string;
    description?: string;
    tags?: string[];
    parentId?: string;
  }): Promise<AxiosResponse> => {
    return apiClient.post('/api/v1/projects', projectData);
  },
  
  // プロジェクト一覧取得
  getProjects: async (page = 1, limit = 20): Promise<AxiosResponse> => {
    return apiClient.get('/api/v1/projects', {
      params: { page, limit }
    });
  },
  
  // プロジェクト詳細取得
  getProject: async (projectId: string): Promise<AxiosResponse> => {
    return apiClient.get(`/api/v1/projects/${projectId}`);
  },
  
  // プロジェクト更新
  updateProject: async (projectId: string, projectData: {
    name?: string;
    description?: string;
    tags?: string[];
  }): Promise<AxiosResponse> => {
    return apiClient.put(`/api/v1/projects/${projectId}`, projectData);
  },
  
  // プロジェクト削除
  deleteProject: async (projectId: string): Promise<AxiosResponse> => {
    return apiClient.delete(`/api/v1/projects/${projectId}`);
  },
  
  // プロジェクトにセッションを追加
  addSessionToProject: async (projectId: string, sessionId: string, displayName?: string): Promise<AxiosResponse> => {
    return apiClient.post(`/api/v1/projects/${projectId}/sessions`, {
      sessionId,
      displayName
    });
  },
};

// apiClientのエクスポート
export { apiClient };

// デフォルトエクスポート
export default api;
