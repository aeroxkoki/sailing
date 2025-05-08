import { useState, useCallback } from 'react';
import { AxiosResponse } from 'axios';
import { ApiError } from '../types';

/**
 * API呼び出しを行うカスタムフック
 * ローディング状態とエラー処理をカプセル化
 */
export function useApi<T = any>() {
  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<ApiError | null>(null);

  /**
   * API呼び出しを実行する関数
   * @param apiCall - API呼び出し関数（Promiseを返す）
   * @param onSuccess - 成功時のコールバック
   * @param onError - エラー時のコールバック
   */
  const execute = useCallback(
    async <R = T>(
      apiCall: () => Promise<AxiosResponse<R>>, 
      onSuccess?: (data: R) => void, 
      onError?: (error: ApiError) => void
    ): Promise<R | null> => {
      setIsLoading(true);
      setError(null);

      try {
        const response = await apiCall();
        const result = response.data;
        
        setData(result as unknown as T);
        if (onSuccess) onSuccess(result);
        
        return result;
      } catch (err: any) {
        const apiError = err as ApiError;
        setError(apiError);
        if (onError) onError(apiError);
        
        return null;
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  /**
   * データをリセットする関数
   */
  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setIsLoading(false);
  }, []);

  return {
    data,
    isLoading,
    error,
    execute,
    reset
  };
}

export default useApi;