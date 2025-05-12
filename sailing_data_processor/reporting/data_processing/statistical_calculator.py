# -*- coding: utf-8 -*-
"""
Statistical Calculator Module - Provides functionality for statistical calculations.
"""

from typing import Dict, List, Any, Optional, Union, Tuple, Callable
import pandas as pd
import numpy as np

from sailing_data_processor.reporting.data_processing.base_calculator import BaseCalculator


class StatisticalCalculator(BaseCalculator):
    """
    統計値計算
    
    データの統計値を計算します。
    平均、中央値、標準偏差、パーセンタイル、トレンドなどを計算します。
    """
    
    def __init__(self, params: Optional[Dict[str, Any]] = None):
        """
        初期化
        
        Parameters
        ----------
        params : Optional[Dict[str, Any]], optional
            計算パラメータ, by default None
            
            columns: List[str]
                計算対象の列リスト
            metrics: List[str]
                計算する統計指標のリスト ('mean', 'median', 'std', 'min', 'max', 'percentile', 'trend')
            percentiles: List[float]
                計算するパーセンタイル値のリスト (0-100)
            window_size: int
                移動統計値の窓サイズ
            trend_method: str
                トレンド計算方法 ('linear', 'polynomial')
            trend_degree: int
                多項式トレンドの次数
        """
        super().__init__(params)
        
        # デフォルトパラメータの設定
        if 'metrics' not in self.params:
            self.params['metrics'] = ['mean', 'median', 'std', 'min', 'max']
        
        if 'percentiles' not in self.params:
            self.params['percentiles'] = [25, 50, 75]
        
        if 'window_size' not in self.params:
            self.params['window_size'] = 10
        
        if 'trend_method' not in self.params:
            self.params['trend_method'] = 'linear'
        
        if 'trend_degree' not in self.params:
            self.params['trend_degree'] = 1
    
    def _calculate_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        DataFrameの統計値を計算
        
        Parameters
        ----------
        df : pd.DataFrame
            計算対象DataFrame
            
        Returns
        -------
        pd.DataFrame
            計算結果のDataFrame
        """
        # 結果用のDataFrameを作成（元のデータをコピー）
        result_df = df.copy()
        
        # 計算対象の列を決定
        columns = self.params.get('columns', None)
        if columns is None:
            # 数値列のみを計算対象にする
            columns = df.select_dtypes(include=[np.number]).columns.tolist()
        else:
            # 存在する列のみを対象に
            columns = [col for col in columns if col in df.columns]
        
        # 統計指標ごとの計算
        metrics = self.params['metrics']
        
        for col in columns:
            # 平均値
            if 'mean' in metrics:
                result_df[f'{col}_mean'] = df[col].mean()
                
                # 移動平均
                if 'moving' in metrics:
                    window_size = self.params['window_size']
                    result_df[f'{col}_moving_mean'] = df[col].rolling(window=window_size, center=True).mean()
            
            # 中央値
            if 'median' in metrics:
                result_df[f'{col}_median'] = df[col].median()
                
                # 移動中央値
                if 'moving' in metrics:
                    window_size = self.params['window_size']
                    result_df[f'{col}_moving_median'] = df[col].rolling(window=window_size, center=True).median()
            
            # 標準偏差
            if 'std' in metrics:
                result_df[f'{col}_std'] = df[col].std()
                
                # 移動標準偏差
                if 'moving' in metrics:
                    window_size = self.params['window_size']
                    result_df[f'{col}_moving_std'] = df[col].rolling(window=window_size, center=True).std()
            
            # 最小値
            if 'min' in metrics:
                result_df[f'{col}_min'] = df[col].min()
                
                # 移動最小値
                if 'moving' in metrics:
                    window_size = self.params['window_size']
                    result_df[f'{col}_moving_min'] = df[col].rolling(window=window_size, center=True).min()
            
            # 最大値
            if 'max' in metrics:
                result_df[f'{col}_max'] = df[col].max()
                
                # 移動最大値
                if 'moving' in metrics:
                    window_size = self.params['window_size']
                    result_df[f'{col}_moving_max'] = df[col].rolling(window=window_size, center=True).max()
            
            # パーセンタイル
            if 'percentile' in metrics:
                percentiles = self.params['percentiles']
                for p in percentiles:
                    result_df[f'{col}_p{p}'] = df[col].quantile(p / 100)
                    
                    # 移動パーセンタイル
                    if 'moving' in metrics:
                        window_size = self.params['window_size']
                        result_df[f'{col}_moving_p{p}'] = df[col].rolling(window=window_size, center=True).quantile(p / 100)
            
            # トレンド
            if 'trend' in metrics:
                trend_method = self.params['trend_method']
                
                # インデックスを数値に変換
                x = np.arange(len(df))
                y = df[col].values
                
                # 欠損値を除外
                mask = ~np.isnan(y)
                x_valid = x[mask]
                y_valid = y[mask]
                
                if len(x_valid) > 1:  # 有効なデータが2点以上ある場合
                    if trend_method == 'linear':
                        # 線形トレンド
                        slope, intercept = np.polyfit(x_valid, y_valid, 1)
                        trend_line = slope * x + intercept
                        result_df[f'{col}_trend'] = trend_line
                        result_df[f'{col}_trend_slope'] = slope
                    
                    elif trend_method == 'polynomial':
                        # 多項式トレンド
                        degree = self.params['trend_degree']
                        coeffs = np.polyfit(x_valid, y_valid, degree)
                        trend_line = np.zeros_like(x, dtype=float)
                        for i, coef in enumerate(coeffs):
                            trend_line += coef * (x ** (degree - i))
                        result_df[f'{col}_trend'] = trend_line
                        result_df[f'{col}_trend_coeffs'] = str(coeffs)
        
        return result_df
    
    def _calculate_dict_list(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        辞書のリストの統計値を計算
        
        Parameters
        ----------
        data : List[Dict[str, Any]]
            計算対象の辞書リスト
            
        Returns
        -------
        List[Dict[str, Any]]
            計算結果の辞書リスト
        """
        if not data:
            return data
        
        # DataFrameに変換して処理
        df = pd.DataFrame(data)
        result_df = self._calculate_dataframe(df)
        
        # 再度リストに変換
        return result_df.to_dict('records')
    
    def _calculate_list(self, data: List[Any]) -> Dict[str, Any]:
        """
        数値リストの統計値を計算
        
        Parameters
        ----------
        data : List[Any]
            計算対象のリスト
            
        Returns
        -------
        Dict[str, Any]
            統計値の辞書
        """
        if not data or not all(isinstance(x, (int, float)) for x in data if x is not None):
            return {}
        
        # None値をNaNに置換
        cleaned_data = np.array([np.nan if x is None else x for x in data])
        
        # 統計指標ごとの計算
        metrics = self.params['metrics']
        result = {}
        
        # 平均値
        if 'mean' in metrics:
            result['mean'] = np.nanmean(cleaned_data)
        
        # 中央値
        if 'median' in metrics:
            result['median'] = np.nanmedian(cleaned_data)
        
        # 標準偏差
        if 'std' in metrics:
            result['std'] = np.nanstd(cleaned_data)
        
        # 最小値
        if 'min' in metrics:
            result['min'] = np.nanmin(cleaned_data)
        
        # 最大値
        if 'max' in metrics:
            result['max'] = np.nanmax(cleaned_data)
        
        # パーセンタイル
        if 'percentile' in metrics:
            percentiles = self.params['percentiles']
            for p in percentiles:
                result[f'p{p}'] = np.nanpercentile(cleaned_data, p)
        
        # トレンド
        if 'trend' in metrics:
            trend_method = self.params['trend_method']
            
            # インデックスを数値に変換
            x = np.arange(len(cleaned_data))
            y = cleaned_data
            
            # 欠損値を除外
            mask = ~np.isnan(y)
            x_valid = x[mask]
            y_valid = y[mask]
            
            if len(x_valid) > 1:  # 有効なデータが2点以上ある場合
                if trend_method == 'linear':
                    # 線形トレンド
                    slope, intercept = np.polyfit(x_valid, y_valid, 1)
                    result['trend_slope'] = slope
                    result['trend_intercept'] = intercept
                
                elif trend_method == 'polynomial':
                    # 多項式トレンド
                    degree = self.params['trend_degree']
                    coeffs = np.polyfit(x_valid, y_valid, degree)
                    result['trend_coeffs'] = coeffs.tolist()
        
        return result
