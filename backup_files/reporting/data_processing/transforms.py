# -*- coding: utf-8 -*-
"""
Module for data connector between map layers and data sources.
This module provides functions for binding and data transformation between layers and data sources.
"""

from typing import Dict, List, Any, Optional, Union, Tuple, Callable
import pandas as pd
import numpy as np


class DataTransformer:
    """
    データ変換の基底クラス
    
    様々なデータ変換処理の基底となるクラスを提供します。
    """
    
    def __init__(self, params: Optional[Dict[str, Any]] = None):
        """
        初期化
        
        Parameters
        ----------
        params : Optional[Dict[str, Any]], optional
            変換パラメータ, by default None
        """
        self.params = params or {}
    
    def transform(self, data: Any) -> Any:
        """
        データを変換
        
        Parameters
        ----------
        data : Any
            変換対象データ
            
        Returns
        -------
        Any
            変換後のデータ
        """
        # 特定のデータ型に対応した変換処理を呼び出す
        if isinstance(data, pd.DataFrame):
            return self._transform_dataframe(data)
        elif isinstance(data, list):
            if len(data) > 0 and isinstance(data[0], dict):
                return self._transform_dict_list(data)
            else:
                return self._transform_list(data)
        elif isinstance(data, dict):
            return self._transform_dict(data)
        else:
            return data
    
    def _transform_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        DataFrameを変換
        
        Parameters
        ----------
        df : pd.DataFrame
            変換対象DataFrameイ
            
        Returns
        -------
        pd.DataFrame
            変換後のDataFrame
        """
        # 具体的な変換はサブクラスで実装
        return df
    
    def _transform_dict_list(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        辞書のリストを変換
        
        Parameters
        ----------
        data : List[Dict[str, Any]]
            変換対象の辞書リスト
            
        Returns
        -------
        List[Dict[str, Any]]
            変換後の辞書リスト
        """
        # 具体的な変換はサブクラスで実装
        return data
    
    def _transform_list(self, data: List[Any]) -> List[Any]:
        """
        リストを変換
        
        Parameters
        ----------
        data : List[Any]
            変換対象のリスト
            
        Returns
        -------
        List[Any]
            変換後のリスト
        """
        # 具体的な変換はサブクラスで実装
        return data
    
    def _transform_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        辞書を変換
        
        Parameters
        ----------
        data : Dict[str, Any]
            変換対象の辞書
            
        Returns
        -------
        Dict[str, Any]
            変換後の辞書
        """
        # 具体的な変換はサブクラスで実装
        return data


class SmoothingTransform(DataTransformer):
    """
    データ平滑化変換
    
    時系列データにスムージングを適用します。
    複数の平滑化方法（移動平均、指数平滑化、メディアンフィルタなど）をサポートします。
    """
    
    def __init__(self, params: Optional[Dict[str, Any]] = None):
        """
        初期化
        
        Parameters
        ----------
        params : Optional[Dict[str, Any]], optional
            変換パラメータ, by default None
            
            method: str
                平滑化方法（'moving_avg', 'exponential', 'median', 'gaussian'）
            window_size: int
                窓サイズ（移動平均、メディアンフィルタ用）
            alpha: float
                指数平滑化のα値（0 < alpha <= 1）
            sigma: float
                ガウシアンフィルタの標準偏差
            columns: List[str]
                平滑化対象の列名のリスト
        """
        super().__init__(params)
        
        # デフォルトパラメータの設定
        if 'method' not in self.params:
            self.params['method'] = 'moving_avg'
        
        if 'window_size' not in self.params:
            self.params['window_size'] = 5
        
        if 'alpha' not in self.params:
            self.params['alpha'] = 0.3
        
        if 'sigma' not in self.params:
            self.params['sigma'] = 1.0
    
    def _transform_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        DataFrameにスムージングを適用
        
        Parameters
        ----------
        df : pd.DataFrame
            変換対象DataFrame
            
        Returns
        -------
        pd.DataFrame
            平滑化後のDataFrame
        """
        # 出力用データフレームを作成（元のデータをコピー）
        result_df = df.copy()
        
        # 平滑化対象の列を特定
        columns = self.params.get('columns', None)
        if columns is None:
            # 数値列のみをスムージング対象に
            columns = df.select_dtypes(include=[np.number]).columns.tolist()
        else:
            # 存在する列のみを対象に
            columns = [col for col in columns if col in df.columns]
        
        # 平滑化方法による分岐
        method = self.params['method']
        
        if method == 'moving_avg':
            # 移動平均
            window_size = self.params['window_size']
            for col in columns:
                result_df[col] = df[col].rolling(window=window_size, center=True).mean()
                # NaN値を前後の値で補間
                result_df[col] = result_df[col].interpolate(method='linear', limit_direction='both')
        
        elif method == 'exponential':
            # 指数平滑化
            alpha = self.params['alpha']
            for col in columns:
                result_df[col] = df[col].ewm(alpha=alpha).mean()
        
        elif method == 'median':
            # メディアンフィルタ
            window_size = self.params['window_size']
            for col in columns:
                result_df[col] = df[col].rolling(window=window_size, center=True).median()
                # NaN値を前後の値で補間
                result_df[col] = result_df[col].interpolate(method='linear', limit_direction='both')
        
        elif method == 'gaussian':
            # ガウシアンフィルタ
            window_size = self.params['window_size']
            sigma = self.params['sigma']
            
            # ガウシアンウィンドウの作成
            x = np.arange(-window_size // 2 + 1, window_size // 2 + 1)
            gaussian_window = np.exp(-(x**2) / (2 * sigma**2))
            gaussian_window = gaussian_window / np.sum(gaussian_window)
            
            for col in columns:
                # 畳み込みでガウシアンフィルタを適用
                result_df[col] = np.convolve(df[col].fillna(0), gaussian_window, mode='same')
                # 元データがNaNの位置を再度NaNに
                mask = df[col].isna()
                result_df.loc[mask, col] = np.nan
        
        return result_df
    
    def _transform_dict_list(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        辞書のリストに平滑化を適用
        
        Parameters
        ----------
        data : List[Dict[str, Any]]
            変換対象の辞書リスト
            
        Returns
        -------
        List[Dict[str, Any]]
            平滑化後の辞書リスト
        """
        if not data:
            return data
        
        # DataFrameに変換して処理
        df = pd.DataFrame(data)
        smoothed_df = self._transform_dataframe(df)
        
        # 再度リストに変換
        return smoothed_df.to_dict('records')
    
    def _transform_list(self, data: List[Any]) -> List[Any]:
        """
        数値リストに平滑化を適用
        
        Parameters
        ----------
        data : List[Any]
            変換対象のリスト
            
        Returns
        -------
        List[Any]
            平滑化後のリスト
        """
        if not data or not all(isinstance(x, (int, float)) for x in data if x is not None):
            return data
        
        # 平滑化方法による分岐
        method = self.params['method']
        
        if method == 'moving_avg':
            # 移動平均
            window_size = self.params['window_size']
            series = pd.Series(data)
            result = series.rolling(window=window_size, center=True).mean()
            # NaN値を補間
            result = result.interpolate(method='linear', limit_direction='both')
            return result.tolist()
        
        elif method == 'exponential':
            # 指数平滑化
            alpha = self.params['alpha']
            series = pd.Series(data)
            result = series.ewm(alpha=alpha).mean()
            return result.tolist()
        
        elif method == 'median':
            # メディアンフィルタ
            window_size = self.params['window_size']
            series = pd.Series(data)
            result = series.rolling(window=window_size, center=True).median()
            # NaN値を補間
            result = result.interpolate(method='linear', limit_direction='both')
            return result.tolist()
        
        elif method == 'gaussian':
            # ガウシアンフィルタ
            window_size = self.params['window_size']
            sigma = self.params['sigma']
            
            # ガウシアンウィンドウの作成
            x = np.arange(-window_size // 2 + 1, window_size // 2 + 1)
            gaussian_window = np.exp(-(x**2) / (2 * sigma**2))
            gaussian_window = gaussian_window / np.sum(gaussian_window)
            
            # Noneを0に置換
            numeric_data = [0 if x is None else x for x in data]
            
            # 畳み込みでガウシアンフィルタを適用
            result = np.convolve(numeric_data, gaussian_window, mode='same')
            
            # 元データがNoneの位置を再度Noneに
            return [None if data[i] is None else result[i] for i in range(len(data))]
        
        return data


class ResamplingTransform(DataTransformer):
    """
    データリサンプリング変換
    
    時系列データのサンプリング周期を変更します。
    「間引き」「補間」などの処理をサポートします。
    """
    
    def __init__(self, params: Optional[Dict[str, Any]] = None):
        """
        初期化
        
        Parameters
        ----------
        params : Optional[Dict[str, Any]], optional
            変換パラメータ, by default None
            
            method: str
                リサンプリング方法（'downsample', 'upsample'）
            rule: str
                リサンプリングの周期（pandas のオフセット文字列, e.g. '1s', '5min'）
            time_column: str
                時間列の名前
            interpolation: str
                補間方法（'linear', 'cubic', 'nearest', etc.）
        """
        super().__init__(params)
        
        # デフォルトパラメータの設定
        if 'method' not in self.params:
            self.params['method'] = 'downsample'
        
        if 'rule' not in self.params:
            self.params['rule'] = '1s'
        
        if 'time_column' not in self.params:
            self.params['time_column'] = 'timestamp'
        
        if 'interpolation' not in self.params:
            self.params['interpolation'] = 'linear'
    
    def _transform_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        DataFrameをリサンプリング
        
        Parameters
        ----------
        df : pd.DataFrame
            変換対象DataFrame
            
        Returns
        -------
        pd.DataFrame
            リサンプリング後のDataFrame
        """
        # 時間列を確認
        time_column = self.params['time_column']
        if time_column not in df.columns:
            return df
        
        # 時間列が時間型ではない場合は変換
        if not pd.api.types.is_datetime64_any_dtype(df[time_column]):
            try:
                df[time_column] = pd.to_datetime(df[time_column])
            except:
                return df
        
        # インデックスを時間列に設定
        df_indexed = df.set_index(time_column)
        
        # リサンプリング方法による分岐
        method = self.params['method']
        rule = self.params['rule']
        interpolation = self.params['interpolation']
        
        if method == 'downsample':
            # ダウンサンプリング（データ量の削減）
            # 数値列に対しては平均を取り、カテゴリ列は最頻値を使用
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            category_cols = list(set(df.columns) - set(numeric_cols) - {time_column})
            
            # 数値列のリサンプリング
            if numeric_cols:
                resampled_numeric = df_indexed[numeric_cols].resample(rule).mean()
            else:
                resampled_numeric = pd.DataFrame(index=df_indexed.resample(rule).indices.keys())
            
            # カテゴリ列のリサンプリング
            if category_cols:
                resampled_category = df_indexed[category_cols].resample(rule).apply(lambda x: x.mode().iloc[0] if not x.empty and len(x.mode()) > 0 else None)
                result_df = pd.concat([resampled_numeric, resampled_category], axis=1)
            else:
                result_df = resampled_numeric
        
        elif method == 'upsample':
            # アップサンプリング（データ量の増加）
            # 補間方法を指定してリサンプリング
            result_df = df_indexed.resample(rule).asfreq()
            
            # 数値列の補間
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if numeric_cols:
                result_df[numeric_cols] = result_df[numeric_cols].interpolate(method=interpolation, limit_direction='both')
            
            # カテゴリ列の処理（前方の値を使用）
            category_cols = list(set(df.columns) - set(numeric_cols) - {time_column})
            if category_cols:
                result_df[category_cols] = result_df[category_cols].ffill()
        
        else:
            return df
        
        # インデックスを列に戻す
        result_df = result_df.reset_index()
        
        return result_df
    
    def _transform_dict_list(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        辞書のリストをリサンプリング
        
        Parameters
        ----------
        data : List[Dict[str, Any]]
            変換対象の辞書リスト
            
        Returns
        -------
        List[Dict[str, Any]]
            リサンプリング後の辞書リスト
        """
        if not data:
            return data
        
        # DataFrameに変換して処理
        df = pd.DataFrame(data)
        resampled_df = self._transform_dataframe(df)
        
        # 再度リストに変換
        return resampled_df.to_dict('records')


class NormalizationTransform(DataTransformer):
    """
    データ正規化変換
    
    数値データを特定の範囲に変換します。
    複数の正規化方法（min-max正規化、Z-score正規化など）をサポートします。
    """
    
    def __init__(self, params: Optional[Dict[str, Any]] = None):
        """
        初期化
        
        Parameters
        ----------
        params : Optional[Dict[str, Any]], optional
            変換パラメータ, by default None
            
            method: str
                正規化方法（'min_max', 'z_score', 'robust'）
            target_min: float
                min-max正規化の最小値（デフォルト：0）
            target_max: float
                min-max正規化の最大値（デフォルト：1）
            columns: List[str]
                正規化対象の列名のリスト
        """
        super().__init__(params)
        
        # デフォルトパラメータの設定
        if 'method' not in self.params:
            self.params['method'] = 'min_max'
        
        if 'target_min' not in self.params:
            self.params['target_min'] = 0.0
        
        if 'target_max' not in self.params:
            self.params['target_max'] = 1.0
    
    def _transform_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        DataFrameに正規化を適用
        
        Parameters
        ----------
        df : pd.DataFrame
            変換対象DataFrame
            
        Returns
        -------
        pd.DataFrame
            正規化後のDataFrame
        """
        # 出力用データフレームを作成（元のデータをコピー）
        result_df = df.copy()
        
        # 正規化対象の列を特定
        columns = self.params.get('columns', None)
        if columns is None:
            # 数値列のみを正規化対象に
            columns = df.select_dtypes(include=[np.number]).columns.tolist()
        else:
            # 存在する列のみを対象に
            columns = [col for col in columns if col in df.columns]
        
        # 正規化方法による分岐
        method = self.params['method']
        
        if method == 'min_max':
            # min-max正規化
            target_min = self.params['target_min']
            target_max = self.params['target_max']
            
            for col in columns:
                min_val = df[col].min()
                max_val = df[col].max()
                
                if max_val != min_val:  # 除算エラー回避
                    result_df[col] = target_min + (df[col] - min_val) * (target_max - target_min) / (max_val - min_val)
                else:
                    result_df[col] = target_min
        
        elif method == 'z_score':
            # Z-score正規化
            for col in columns:
                mean_val = df[col].mean()
                std_val = df[col].std()
                
                if std_val != 0:  # 除算エラー回避
                    result_df[col] = (df[col] - mean_val) / std_val
                else:
                    result_df[col] = 0
        
        elif method == 'robust':
            # ロバスト正規化（中央値と四分位範囲を使用）
            for col in columns:
                median_val = df[col].median()
                q1 = df[col].quantile(0.25)
                q3 = df[col].quantile(0.75)
                iqr = q3 - q1
                
                if iqr != 0:  # 除算エラー回避
                    result_df[col] = (df[col] - median_val) / iqr
                else:
                    result_df[col] = 0
        
        return result_df
    
    def _transform_dict_list(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        辞書のリストに正規化を適用
        
        Parameters
        ----------
        data : List[Dict[str, Any]]
            変換対象の辞書リスト
            
        Returns
        -------
        List[Dict[str, Any]]
            正規化後の辞書リスト
        """
        if not data:
            return data
        
        # DataFrameに変換して処理
        df = pd.DataFrame(data)
        normalized_df = self._transform_dataframe(df)
        
        # 再度リストに変換
        return normalized_df.to_dict('records')
    
    def _transform_list(self, data: List[Any]) -> List[Any]:
        """
        数値リストに正規化を適用
        
        Parameters
        ----------
        data : List[Any]
            変換対象のリスト
            
        Returns
        -------
        List[Any]
            正規化後のリスト
        """
        if not data or not all(isinstance(x, (int, float)) for x in data if x is not None):
            return data
        
        # None値をNaNに置換
        cleaned_data = [np.nan if x is None else x for x in data]
        
        # 正規化方法による分岐
        method = self.params['method']
        
        if method == 'min_max':
            # min-max正規化
            target_min = self.params['target_min']
            target_max = self.params['target_max']
            
            min_val = np.nanmin(cleaned_data)
            max_val = np.nanmax(cleaned_data)
            
            if max_val != min_val:  # 除算エラー回避
                result = [target_min + (x - min_val) * (target_max - target_min) / (max_val - min_val) if not np.isnan(x) else None for x in cleaned_data]
            else:
                result = [target_min if not np.isnan(x) else None for x in cleaned_data]
        
        elif method == 'z_score':
            # Z-score正規化
            mean_val = np.nanmean(cleaned_data)
            std_val = np.nanstd(cleaned_data)
            
            if std_val != 0:  # 除算エラー回避
                result = [(x - mean_val) / std_val if not np.isnan(x) else None for x in cleaned_data]
            else:
                result = [0 if not np.isnan(x) else None for x in cleaned_data]
        
        elif method == 'robust':
            # ロバスト正規化
            median_val = np.nanmedian(cleaned_data)
            q1 = np.nanpercentile(cleaned_data, 25)
            q3 = np.nanpercentile(cleaned_data, 75)
            iqr = q3 - q1
            
            if iqr != 0:  # 除算エラー回避
                result = [(x - median_val) / iqr if not np.isnan(x) else None for x in cleaned_data]
            else:
                result = [0 if not np.isnan(x) else None for x in cleaned_data]
        
        else:
            result = data
        
        return result
