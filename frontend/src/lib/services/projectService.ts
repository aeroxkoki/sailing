/**
 * プロジェクト関連のAPIサービス
 */
import apiClient, { ApiResponse } from '../api';

// プロジェクト型定義
export interface Project {
  id: string;
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
  user_id: string;
  metadata?: Record<string, any>;
}

// プロジェクト作成パラメータ
export interface CreateProjectParams {
  name: string;
  description?: string;
  metadata?: Record<string, any>;
}

// プロジェクト更新パラメータ
export interface UpdateProjectParams {
  name?: string;
  description?: string;
  metadata?: Record<string, any>;
}

/**
 * プロジェクトサービスクラス
 */
class ProjectService {
  private basePath = '/projects';

  /**
   * プロジェクト一覧を取得
   */
  async getAllProjects(): Promise<ApiResponse<Project[]>> {
    try {
      return await apiClient.get<Project[]>(this.basePath);
    } catch (error) {
      console.error('Failed to fetch projects:', error);
      throw error;
    }
  }

  /**
   * プロジェクト詳細を取得
   */
  async getProject(id: string): Promise<ApiResponse<Project>> {
    try {
      return await apiClient.get<Project>(`${this.basePath}/${id}`);
    } catch (error) {
      console.error(`Failed to fetch project ${id}:`, error);
      throw error;
    }
  }

  /**
   * プロジェクトを作成
   */
  async createProject(params: CreateProjectParams): Promise<ApiResponse<Project>> {
    try {
      return await apiClient.post<Project>(this.basePath, params);
    } catch (error) {
      console.error('Failed to create project:', error);
      throw error;
    }
  }

  /**
   * プロジェクトを更新
   */
  async updateProject(id: string, params: UpdateProjectParams): Promise<ApiResponse<Project>> {
    try {
      return await apiClient.put<Project>(`${this.basePath}/${id}`, params);
    } catch (error) {
      console.error(`Failed to update project ${id}:`, error);
      throw error;
    }
  }

  /**
   * プロジェクトを削除
   */
  async deleteProject(id: string): Promise<ApiResponse<void>> {
    try {
      return await apiClient.delete<void>(`${this.basePath}/${id}`);
    } catch (error) {
      console.error(`Failed to delete project ${id}:`, error);
      throw error;
    }
  }

  /**
   * プロジェクト検索
   */
  async searchProjects(query: string): Promise<ApiResponse<Project[]>> {
    try {
      return await apiClient.get<Project[]>(`${this.basePath}/search`, { params: { q: query } });
    } catch (error) {
      console.error('Failed to search projects:', error);
      throw error;
    }
  }
}

// サービスのシングルトンインスタンス
const projectService = new ProjectService();
export default projectService;
