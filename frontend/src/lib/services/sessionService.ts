/**
 * セッション関連のAPIサービス
 */
import apiClient, { ApiResponse } from '../api';

// セッション型定義
export interface Session {
  id: string;
  name: string;
  project_id: string;
  description?: string;
  created_at: string;
  updated_at: string;
  user_id: string;
  metadata?: Record<string, any>;
  gps_data_summary?: {
    start_time: string;
    end_time: string;
    track_length: number;
    points_count: number;
  };
  tags?: string[];
}

// セッション作成パラメータ
export interface CreateSessionParams {
  name: string;
  project_id: string;
  description?: string;
  metadata?: Record<string, any>;
  tags?: string[];
}

// セッション更新パラメータ
export interface UpdateSessionParams {
  name?: string;
  description?: string;
  metadata?: Record<string, any>;
  tags?: string[];
}

// GPSデータインポートパラメータ
export interface ImportGpsDataParams {
  session_id: string;
  file: File;
  options?: {
    skip_validation?: boolean;
    auto_clean?: boolean;
    column_mapping?: Record<string, string>;
  };
}

/**
 * セッションサービスクラス
 */
class SessionService {
  private basePath = '/sessions';

  /**
   * プロジェクトに紐づくセッション一覧を取得
   */
  async getSessionsByProject(projectId: string): Promise<ApiResponse<Session[]>> {
    try {
      return await apiClient.get<Session[]>(`/projects/${projectId}/sessions`);
    } catch (error) {
      console.error(`Failed to fetch sessions for project ${projectId}:`, error);
      throw error;
    }
  }

  /**
   * セッション詳細を取得
   */
  async getSession(id: string): Promise<ApiResponse<Session>> {
    try {
      return await apiClient.get<Session>(`${this.basePath}/${id}`);
    } catch (error) {
      console.error(`Failed to fetch session ${id}:`, error);
      throw error;
    }
  }

  /**
   * セッションを作成
   */
  async createSession(params: CreateSessionParams): Promise<ApiResponse<Session>> {
    try {
      return await apiClient.post<Session>(this.basePath, params);
    } catch (error) {
      console.error('Failed to create session:', error);
      throw error;
    }
  }

  /**
   * セッションを更新
   */
  async updateSession(id: string, params: UpdateSessionParams): Promise<ApiResponse<Session>> {
    try {
      return await apiClient.put<Session>(`${this.basePath}/${id}`, params);
    } catch (error) {
      console.error(`Failed to update session ${id}:`, error);
      throw error;
    }
  }

  /**
   * セッションを削除
   */
  async deleteSession(id: string): Promise<ApiResponse<void>> {
    try {
      return await apiClient.delete<void>(`${this.basePath}/${id}`);
    } catch (error) {
      console.error(`Failed to delete session ${id}:`, error);
      throw error;
    }
  }

  /**
   * GPSデータをインポート
   */
  async importGpsData(params: ImportGpsDataParams): Promise<ApiResponse<any>> {
    try {
      const { session_id, file, options = {} } = params;
      return await apiClient.uploadFile<any>(
        `${this.basePath}/${session_id}/import`,
        file,
        options
      );
    } catch (error) {
      console.error('Failed to import GPS data:', error);
      throw error;
    }
  }

  /**
   * タグでセッションを検索
   */
  async getSessionsByTags(tags: string[]): Promise<ApiResponse<Session[]>> {
    try {
      return await apiClient.get<Session[]>(`${this.basePath}/tags`, {
        params: { tags: tags.join(',') }
      });
    } catch (error) {
      console.error('Failed to fetch sessions by tags:', error);
      throw error;
    }
  }

  /**
   * セッションを検索
   */
  async searchSessions(query: string): Promise<ApiResponse<Session[]>> {
    try {
      return await apiClient.get<Session[]>(`${this.basePath}/search`, {
        params: { q: query }
      });
    } catch (error) {
      console.error('Failed to search sessions:', error);
      throw error;
    }
  }
}

// サービスのシングルトンインスタンス
const sessionService = new SessionService();
export default sessionService;
