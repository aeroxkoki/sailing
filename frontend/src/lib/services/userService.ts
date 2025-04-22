/**
 * ユーザー関連のAPIサービス
 */
import apiClient, { ApiResponse } from '../api';

// ユーザー型定義
export interface User {
  id: string;
  email: string;
  name: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
  preferences?: Record<string, any>;
}

// ログインパラメータ
export interface LoginParams {
  email: string;
  password: string;
}

// 登録パラメータ
export interface RegisterParams {
  email: string;
  password: string;
  name: string;
}

// プロファイル更新パラメータ
export interface UpdateProfileParams {
  name?: string;
  email?: string;
  preferences?: Record<string, any>;
}

// 認証レスポンス
export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

/**
 * ユーザーサービスクラス
 */
class UserService {
  private basePath = '/users';

  /**
   * ログイン
   */
  async login(params: LoginParams): Promise<ApiResponse<AuthResponse>> {
    try {
      const response = await apiClient.post<AuthResponse>('/auth/login', params);
      
      if (response.data.access_token) {
        apiClient.setToken(response.data.access_token);
      }
      
      return response;
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  }

  /**
   * ユーザー登録
   */
  async register(params: RegisterParams): Promise<ApiResponse<AuthResponse>> {
    try {
      const response = await apiClient.post<AuthResponse>('/auth/register', params);
      
      if (response.data.access_token) {
        apiClient.setToken(response.data.access_token);
      }
      
      return response;
    } catch (error) {
      console.error('Registration failed:', error);
      throw error;
    }
  }

  /**
   * ログアウト
   */
  async logout(): Promise<void> {
    try {
      await apiClient.post<void>('/auth/logout', {});
      apiClient.clearToken();
    } catch (error) {
      console.error('Logout failed:', error);
      // トークンはクリアする
      apiClient.clearToken();
      throw error;
    }
  }

  /**
   * 現在のユーザー情報を取得
   */
  async getCurrentUser(): Promise<ApiResponse<User>> {
    try {
      return await apiClient.get<User>(`${this.basePath}/me`);
    } catch (error) {
      console.error('Failed to fetch current user:', error);
      throw error;
    }
  }

  /**
   * プロファイル更新
   */
  async updateProfile(params: UpdateProfileParams): Promise<ApiResponse<User>> {
    try {
      return await apiClient.put<User>(`${this.basePath}/me`, params);
    } catch (error) {
      console.error('Failed to update profile:', error);
      throw error;
    }
  }

  /**
   * パスワード変更
   */
  async changePassword(oldPassword: string, newPassword: string): Promise<ApiResponse<void>> {
    try {
      return await apiClient.put<void>(`${this.basePath}/me/password`, {
        old_password: oldPassword,
        new_password: newPassword
      });
    } catch (error) {
      console.error('Failed to change password:', error);
      throw error;
    }
  }

  /**
   * パスワードリセットリクエスト
   */
  async requestPasswordReset(email: string): Promise<ApiResponse<void>> {
    try {
      return await apiClient.post<void>('/auth/password-reset-request', { email });
    } catch (error) {
      console.error('Failed to request password reset:', error);
      throw error;
    }
  }

  /**
   * パスワードリセット実行
   */
  async resetPassword(token: string, newPassword: string): Promise<ApiResponse<void>> {
    try {
      return await apiClient.post<void>('/auth/password-reset', {
        token,
        new_password: newPassword
      });
    } catch (error) {
      console.error('Failed to reset password:', error);
      throw error;
    }
  }

  /**
   * ユーザーが認証済みかチェック
   */
  isAuthenticated(): boolean {
    // ローカルストレージにトークンがあるかを確認
    const token = localStorage.getItem('auth_token');
    return !!token;
  }
}

// サービスのシングルトンインスタンス
const userService = new UserService();
export default userService;
