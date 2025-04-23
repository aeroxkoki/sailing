/**
 * API接続用クライアント
 * バックエンドとの通信を担当
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';

// API設定
// 環境に応じたAPIのベースURL設定
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 
  (process.env.NODE_ENV === 'production'
    ? 'https://sailing-strategy-api.onrender.com'
    : 'http://localhost:8000');

// デバッグ出力
console.log(`Using API URL: ${API_BASE_URL} (NODE_ENV: ${process.env.NODE_ENV})`);
const API_VERSION = '/api/v1';
const API_TIMEOUT = 15000; // 15秒

// デバッグモードではAPIのベースURLを表示
if (process.env.NODE_ENV !== 'production') {
  console.log(`API_BASE_URL: ${API_BASE_URL}`);
}

// レスポンス型定義
export interface ApiResponse<T> {
  data: T;
  status: number;
  message?: string;
}

// エラー型定義
export interface ApiError {
  status: number;
  message: string;
  details?: any;
}

/**
 * APIクライアントクラス
 */
class ApiClient {
  private client: AxiosInstance;
  private token: string | null = null;

  constructor() {
    // Axiosインスタンスの初期化
    this.client = axios.create({
      baseURL: `${API_BASE_URL}${API_VERSION}`,
      timeout: API_TIMEOUT,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Accept-Charset': 'utf-8',
      },
    });

    // リクエストインターセプター
    this.client.interceptors.request.use(
      (config) => {
        // 認証トークンがあれば追加
        if (this.token) {
          config.headers.Authorization = `Bearer ${this.token}`;
        }
        
        // 日本語対応のため明示的にUTF-8を指定
        config.headers['Content-Type'] = 'application/json; charset=utf-8';
        
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // レスポンスインターセプター
    this.client.interceptors.response.use(
      (response) => {
        // 型変換を避けるためAxiosResponseをそのまま返す
        return response;
      },
      (error) => {
        return Promise.reject(error);
      }
    );
  }

  /**
   * トークンをセット
   */
  setToken(token: string): void {
    this.token = token;
    localStorage.setItem('auth_token', token);
  }

  /**
   * トークンをクリア
   */
  clearToken(): void {
    this.token = null;
    localStorage.removeItem('auth_token');
  }

  /**
   * セッションからトークンをロード
   */
  loadToken(): void {
    const token = localStorage.getItem('auth_token');
    if (token) {
      this.token = token;
    }
  }

  /**
   * 成功レスポンスの処理
   */
  private handleSuccess<T>(response: AxiosResponse): ApiResponse<T> {
    return {
      data: response.data,
      status: response.status,
      message: 'Success',
    };
  }

  /**
   * エラーレスポンスの処理
   */
  private handleError(error: AxiosError): Promise<ApiError> {
    let errorResponse: ApiError = {
      status: 500,
      message: 'Unknown error occurred',
    };

    if (error.response) {
      // サーバーからのレスポンスがある場合
      const { status, data } = error.response;
      const errorData = data as any; // 型アサーションでanyに変換
      errorResponse = {
        status,
        message: errorData.message || errorData.detail || 'An error occurred',
        details: errorData,
      };

      // 認証エラーの場合 (401)
      if (status === 401) {
        this.clearToken();
        // 認証ページへリダイレクト処理をここに追加可能
      }
    } else if (error.request) {
      // リクエストは送信されたがレスポンスがない場合
      errorResponse = {
        status: 0,
        message: 'No response from server',
      };
    }

    console.error('API Error:', errorResponse);
    return Promise.reject(errorResponse);
  }

  /**
   * GETリクエスト
   */
  async get<T>(url: string, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    try {
      const response = await this.client.get<T>(url, config);
      return this.handleSuccess(response);
    } catch (error) {
      return Promise.reject(this.handleError(error as AxiosError));
    }
  }

  /**
   * POSTリクエスト
   */
  async post<T>(url: string, data: any, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    try {
      const response = await this.client.post<T>(url, data, config);
      return this.handleSuccess(response);
    } catch (error) {
      return Promise.reject(this.handleError(error as AxiosError));
    }
  }

  /**
   * PUTリクエスト
   */
  async put<T>(url: string, data: any, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    try {
      const response = await this.client.put<T>(url, data, config);
      return this.handleSuccess(response);
    } catch (error) {
      return Promise.reject(this.handleError(error as AxiosError));
    }
  }

  /**
   * DELETEリクエスト
   */
  async delete<T>(url: string, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    try {
      const response = await this.client.delete<T>(url, config);
      // 204 No Contentの場合は空のデータを返す
      if (response.status === 204) {
        return {
          data: {} as T,
          status: 204,
          message: 'Successfully deleted'
        };
      }
      return this.handleSuccess(response);
    } catch (error) {
      return Promise.reject(this.handleError(error as AxiosError));
    }
  }

  /**
   * ファイルアップロード
   */
  async uploadFile<T>(url: string, file: File, additionalData?: Record<string, any>): Promise<ApiResponse<T>> {
    const formData = new FormData();
    formData.append('file', file);

    // 追加データがある場合は追加
    if (additionalData) {
      Object.entries(additionalData).forEach(([key, value]) => {
        formData.append(key, value);
      });
    }

    const config: AxiosRequestConfig = {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    };

    try {
      const response = await this.client.post<T>(url, formData, config);
      return this.handleSuccess(response);
    } catch (error) {
      return Promise.reject(this.handleError(error as AxiosError));
    }
  }
}

// APIクライアントのシングルトンインスタンス
const apiClient = new ApiClient();

// 初期化時にローカルストレージからトークンをロード
if (typeof window !== 'undefined') {
  apiClient.loadToken();
}

// 風向風速推定関連API
export const windEstimationApi = {
  // 風向風速推定実行
  estimateWind: async (file: File, params: any): Promise<ApiResponse<any>> => {
    const formData = new FormData();
    formData.append('gps_data', file);
    
    // パラメータの追加
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        formData.append(key, String(value));
      }
    });
    
    const config: AxiosRequestConfig = {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    };
    
    return apiClient.post<any>('/wind-estimation/estimate', formData, config);
  },
};

// 戦略検出関連API
export const strategyDetectionApi = {
  // 戦略検出実行
  detectStrategies: async (params: any): Promise<ApiResponse<any>> => {
    return apiClient.post<any>('/strategy-detection/detect', params);
  },
};

// プロジェクト関連API
export const projectApi = {
  // プロジェクト一覧取得
  getProjects: async (): Promise<ApiResponse<any>> => {
    return apiClient.get<any>('/projects');
  },
  
  // プロジェクト詳細取得
  getProject: async (id: string): Promise<ApiResponse<any>> => {
    return apiClient.get<any>(`/projects/${id}`);
  },
  
  // プロジェクト作成
  createProject: async (data: any): Promise<ApiResponse<any>> => {
    return apiClient.post<any>('/projects', data);
  },
};

export default apiClient;
