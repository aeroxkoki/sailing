# -*- coding: utf-8 -*-
"""
Module for data connector between map layers and data sources.
This module provides functions for binding and data transformation between layers and data sources.
"""

from typing import Dict, List, Any, Optional, Union, Tuple, Callable
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


class DataAggregator:
    """
    データ集約の基底クラス
    
    様々なデータ集約処理の基底となるクラスを提供します。
    """
    
    def __init__(self, params: Optional[Dict[str, Any]] = None):
        """
        初期化
        
        Parameters
        ----------
        params : Optional[Dict[str, Any]], optional
            集約パラメータ, by default None
        """
        self.params = params or {}
    
    def aggregate(self, data: Any) -> Any:
        """
        データを集約
        
        Parameters
        ----------
        data : Any
            集約対象データ
            
        Returns
        -------
        Any
            集約後のデータ
        """
        # 特定のデータ型に対応した集約処理を呼び出す
        if isinstance(data, pd.DataFrame):
            return self._aggregate_dataframe(data)
        elif isinstance(data, list):
            if len(data) > 0 and isinstance(data[0], dict):
                return self._aggregate_dict_list(data)
            else:
                return self._aggregate_list(data)
        elif isinstance(data, dict):
            return self._aggregate_dict(data)
        else:
            return data
    
    def _aggregate_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        DataFrameを集約
        
        Parameters
        ----------
        df : pd.DataFrame
            集約対象DataFrame
            
        Returns
        -------
        pd.DataFrame
            集約後のDataFrame
        """
        # 具体的な集約はサブクラスで実装
        return df
    
    def _aggregate_dict_list(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        辞書のリストを集約
        
        Parameters
        ----------
        data : List[Dict[str, Any]]
            集約対象の辞書リスト
            
        Returns
        -------
        List[Dict[str, Any]]
            集約後の辞書リスト
        """
        # DataFrameに変換して処理
        df = pd.DataFrame(data)
        result_df = self._aggregate_dataframe(df)
        return result_df.to_dict('records')
    
    def _aggregate_list(self, data: List[Any]) -> List[Any]:
        """
        リストを集約
        
        Parameters
        ----------
        data : List[Any]
            集約対象のリスト
            
        Returns
        -------
        List[Any]
            集約後のリスト
        """
        # 具体的な集約はサブクラスで実装
        return data
    
    def _aggregate_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        辞書を集約
        
        Parameters
        ----------
        data : Dict[str, Any]
            集約対象の辞書
            
        Returns
        -------
        Dict[str, Any]
            集約後の辞書
        """
        # 具体的な集約はサブクラスで実装
        return data


class TimeAggregator(DataAggregator):
    """
    時間ベースの集約
    
    時間軸に沿ってデータを集約します。
    時間間隔（1分、5分、1時間など）でデータをグループ化し、統計値を計算します。
    """
    
    def __init__(self, params: Optional[Dict[str, Any]] = None):
        """
        初期化
        
        Parameters
        ----------
        params : Optional[Dict[str, Any]], optional
            集約パラメータ, by default None
            
            time_column: str
                時間列の名前
            time_unit: str
                時間単位 ('1min', '5min', '1h', '1d' など pandas の周期指定)
            aggregation_funcs: Dict[str, str]
                列ごとの集約関数 ('mean', 'sum', 'min', 'max', 'count' など)
            include_columns: List[str]
                集約に含める列のリスト
            exclude_columns: List[str]
                集約から除外する列のリスト
        """
        super().__init__(params)
        
        # デフォルトパラメータの設定
        if 'time_column' not in self.params:
            self.params['time_column'] = 'timestamp'
        
        if 'time_unit' not in self.params:
            self.params['time_unit'] = '1min'
        
        if 'aggregation_funcs' not in self.params:
            self.params['aggregation_funcs'] = {}
    
    def _aggregate_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        DataFrameを時間ベースで集約
        
        Parameters
        ----------
        df : pd.DataFrame
            集約対象DataFrame
            
        Returns
        -------
        pd.DataFrame
            集約後のDataFrame
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
        
        # 集約に含める列を決定
        include_columns = self.params.get('include_columns', None)
        exclude_columns = self.params.get('exclude_columns', [])
        
        if include_columns is not None:
            # 含める列が指定されている場合は、その列のみを使用
            columns_to_aggregate = [col for col in include_columns if col in df.columns and col != time_column]
        else:
            # 除外する列を考慮して集約対象の列を決定
            columns_to_aggregate = [col for col in df.columns if col != time_column and col not in exclude_columns]
        
        # 列ごとの集約関数を決定
        aggregation_funcs = self.params['aggregation_funcs']
        default_agg_func = 'mean'  # デフォルトの集約関数
        
        agg_dict = {}
        for col in columns_to_aggregate:
            # 列の集約関数を決定
            if col in aggregation_funcs:
                agg_dict[col] = aggregation_funcs[col]
            else:
                # 数値列は平均、カテゴリ列は最頻値をデフォルトとする
                if pd.api.types.is_numeric_dtype(df[col]):
                    agg_dict[col] = default_agg_func
                else:
                    agg_dict[col] = lambda x: x.mode()[0] if len(x.mode()) > 0 else None
        
        # 時間単位でグループ化して集約
        time_unit = self.params['time_unit']
        
        # 時間列をインデックスに設定
        df_indexed = df.set_index(time_column)
        
        # 時間単位でリサンプリングして集約
        resampled = df_indexed.resample(time_unit)
        
        if agg_dict:
            # 列ごとに異なる集約関数を適用
            result_df = resampled.agg(agg_dict)
        else:
            # デフォルトの集約関数を適用
            result_df = resampled.agg(default_agg_func)
        
        # インデックスを列に戻す
        result_df = result_df.reset_index()
        
        return result_df
    
    def _aggregate_dict_list(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        辞書のリストを時間ベースで集約
        
        Parameters
        ----------
        data : List[Dict[str, Any]]
            集約対象の辞書リスト
            
        Returns
        -------
        List[Dict[str, Any]]
            集約後の辞書リスト
        """
        if not data:
            return data
        
        # DataFrameに変換して処理
        df = pd.DataFrame(data)
        result_df = self._aggregate_dataframe(df)
        
        # 再度リストに変換
        return result_df.to_dict('records')


class SpatialAggregator(DataAggregator):
    """
    空間ベースの集約
    
    空間情報（緯度・経度）に基づいてデータを集約します。
    グリッドまたは距離ベースでデータをグループ化し、統計値を計算します。
    """
    
    def __init__(self, params: Optional[Dict[str, Any]] = None):
        """
        初期化
        
        Parameters
        ----------
        params : Optional[Dict[str, Any]], optional
            集約パラメータ, by default None
            
            lat_column: str
                緯度列の名前
            lng_column: str
                経度列の名前
            method: str
                集約方法 ('grid', 'distance')
            grid_size: float
                グリッドサイズ（度単位、グリッド方式の場合）
            distance_threshold: float
                距離の閾値（メートル単位、距離方式の場合）
            aggregation_funcs: Dict[str, str]
                列ごとの集約関数
            include_columns: List[str]
                集約に含める列のリスト
            exclude_columns: List[str]
                集約から除外する列のリスト
        """
        super().__init__(params)
        
        # デフォルトパラメータの設定
        if 'lat_column' not in self.params:
            self.params['lat_column'] = 'latitude'
        
        if 'lng_column' not in self.params:
            self.params['lng_column'] = 'longitude'
        
        if 'method' not in self.params:
            self.params['method'] = 'grid'
        
        if 'grid_size' not in self.params:
            self.params['grid_size'] = 0.001  # 約100mのグリッド
        
        if 'distance_threshold' not in self.params:
            self.params['distance_threshold'] = 100.0  # 100メートル
        
        if 'aggregation_funcs' not in self.params:
            self.params['aggregation_funcs'] = {}
    
    def _aggregate_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        DataFrameを空間ベースで集約
        
        Parameters
        ----------
        df : pd.DataFrame
            集約対象DataFrame
            
        Returns
        -------
        pd.DataFrame
            集約後のDataFrame
        """
        # 緯度経度列を確認
        lat_column = self.params['lat_column']
        lng_column = self.params['lng_column']
        
        if lat_column not in df.columns or lng_column not in df.columns:
            return df
        
        # 集約に含める列を決定
        include_columns = self.params.get('include_columns', None)
        exclude_columns = self.params.get('exclude_columns', [])
        
        if include_columns is not None:
            # 含める列が指定されている場合は、その列のみを使用
            columns_to_aggregate = [col for col in include_columns if col in df.columns and col not in [lat_column, lng_column]]
        else:
            # 除外する列を考慮して集約対象の列を決定
            columns_to_aggregate = [col for col in df.columns if col not in [lat_column, lng_column] and col not in exclude_columns]
        
        # 列ごとの集約関数を決定
        aggregation_funcs = self.params['aggregation_funcs']
        default_agg_func = 'mean'  # デフォルトの集約関数
        
        # 集約方法による分岐
        method = self.params['method']
        
        if method == 'grid':
            # グリッドベースの集約
            grid_size = self.params['grid_size']
            
            # グリッドIDを計算
            df['grid_lat'] = (df[lat_column] / grid_size).astype(int)
            df['grid_lng'] = (df[lng_column] / grid_size).astype(int)
            
            # グリッドでグループ化
            grouped = df.groupby(['grid_lat', 'grid_lng'])
            
            # 集約関数の適用
            agg_dict = {}
            # 緯度経度は平均値を取る
            agg_dict[lat_column] = 'mean'
            agg_dict[lng_column] = 'mean'
            
            for col in columns_to_aggregate:
                # 列の集約関数を決定
                if col in aggregation_funcs:
                    agg_dict[col] = aggregation_funcs[col]
                else:
                    # 数値列は平均、カテゴリ列は最頻値をデフォルトとする
                    if pd.api.types.is_numeric_dtype(df[col]):
                        agg_dict[col] = default_agg_func
                    else:
                        agg_dict[col] = lambda x: x.mode()[0] if len(x.mode()) > 0 else None
            
            # 集約の実行
            result_df = grouped.agg(agg_dict).reset_index()
            
            # 一時的なグリッド列を削除
            result_df = result_df.drop(['grid_lat', 'grid_lng'], axis=1)
        
        elif method == 'distance':
            # 距離ベースの集約
            distance_threshold = self.params['distance_threshold']
            
            # 距離ベースのクラスタリングには複雑なロジックが必要
            # ここでは簡易的な実装として、DBSCAN（密度ベースのクラスタリング）を使用
            from sklearn.cluster import DBSCAN
            from sklearn.preprocessing import StandardScaler
            
            # 緯度経度データを抽出
            coords = df[[lat_column, lng_column]].values
            
            # 座標データをスケーリング
            coords_scaled = StandardScaler().fit_transform(coords)
            
            # DBSCANによるクラスタリング
            # eps値は距離閾値に基づいて設定（要調整）
            db = DBSCAN(eps=distance_threshold/10000.0, min_samples=1).fit(coords_scaled)
            
            # クラスタラベルをDataFrameに追加
            df['cluster'] = db.labels_
            
            # クラスタでグループ化
            grouped = df.groupby('cluster')
            
            # 集約関数の適用
            agg_dict = {}
            # 緯度経度は平均値を取る
            agg_dict[lat_column] = 'mean'
            agg_dict[lng_column] = 'mean'
            
            for col in columns_to_aggregate:
                # 列の集約関数を決定
                if col in aggregation_funcs:
                    agg_dict[col] = aggregation_funcs[col]
                else:
                    # 数値列は平均、カテゴリ列は最頻値をデフォルトとする
                    if pd.api.types.is_numeric_dtype(df[col]):
                        agg_dict[col] = default_agg_func
                    else:
                        agg_dict[col] = lambda x: x.mode()[0] if len(x.mode()) > 0 else None
            
            # 集約の実行
            result_df = grouped.agg(agg_dict).reset_index()
            
            # クラスタ列を削除
            result_df = result_df.drop('cluster', axis=1)
        
        else:
            return df
        
        return result_df
    
    def _aggregate_dict_list(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        辞書のリストを空間ベースで集約
        
        Parameters
        ----------
        data : List[Dict[str, Any]]
            集約対象の辞書リスト
            
        Returns
        -------
        List[Dict[str, Any]]
            集約後の辞書リスト
        """
        if not data:
            return data
        
        # DataFrameに変換して処理
        df = pd.DataFrame(data)
        result_df = self._aggregate_dataframe(df)
        
        # 再度リストに変換
        return result_df.to_dict('records')


class CategoryAggregator(DataAggregator):
    """
    カテゴリベースの集約
    
    カテゴリ情報に基づいてデータを集約します。
    指定されたカテゴリ列でデータをグループ化し、統計値を計算します。
    """
    
    def __init__(self, params: Optional[Dict[str, Any]] = None):
        """
        初期化
        
        Parameters
        ----------
        params : Optional[Dict[str, Any]], optional
            集約パラメータ, by default None
            
            category_columns: List[str]
                カテゴリ列のリスト
            aggregation_funcs: Dict[str, str]
                列ごとの集約関数
            include_columns: List[str]
                集約に含める列のリスト
            exclude_columns: List[str]
                集約から除外する列のリスト
        """
        super().__init__(params)
        
        # デフォルトパラメータの設定
        if 'category_columns' not in self.params:
            self.params['category_columns'] = []
        
        if 'aggregation_funcs' not in self.params:
            self.params['aggregation_funcs'] = {}
    
    def _aggregate_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        DataFrameをカテゴリベースで集約
        
        Parameters
        ----------
        df : pd.DataFrame
            集約対象DataFrame
            
        Returns
        -------
        pd.DataFrame
            集約後のDataFrame
        """
        # カテゴリ列を確認
        category_columns = self.params['category_columns']
        valid_category_columns = [col for col in category_columns if col in df.columns]
        
        if not valid_category_columns:
            return df
        
        # 集約に含める列を決定
        include_columns = self.params.get('include_columns', None)
        exclude_columns = self.params.get('exclude_columns', [])
        
        if include_columns is not None:
            # 含める列が指定されている場合は、その列のみを使用
            columns_to_aggregate = [col for col in include_columns if col in df.columns and col not in valid_category_columns]
        else:
            # 除外する列を考慮して集約対象の列を決定
            columns_to_aggregate = [col for col in df.columns if col not in valid_category_columns and col not in exclude_columns]
        
        # 列ごとの集約関数を決定
        aggregation_funcs = self.params['aggregation_funcs']
        default_agg_func = 'mean'  # デフォルトの集約関数
        
        agg_dict = {}
        for col in columns_to_aggregate:
            # 列の集約関数を決定
            if col in aggregation_funcs:
                agg_dict[col] = aggregation_funcs[col]
            else:
                # 数値列は平均、カテゴリ列は最頻値をデフォルトとする
                if pd.api.types.is_numeric_dtype(df[col]):
                    agg_dict[col] = default_agg_func
                else:
                    agg_dict[col] = lambda x: x.mode()[0] if len(x.mode()) > 0 else None
        
        # カテゴリ列でグループ化
        grouped = df.groupby(valid_category_columns)
        
        # 集約関数の適用
        if agg_dict:
            result_df = grouped.agg(agg_dict).reset_index()
        else:
            # デフォルトの集約関数を適用
            result_df = grouped.agg(default_agg_func).reset_index()
        
        return result_df
    
    def _aggregate_dict_list(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        辞書のリストをカテゴリベースで集約
        
        Parameters
        ----------
        data : List[Dict[str, Any]]
            集約対象の辞書リスト
            
        Returns
        -------
        List[Dict[str, Any]]
            集約後の辞書リスト
        """
        if not data:
            return data
        
        # DataFrameに変換して処理
        df = pd.DataFrame(data)
        result_df = self._aggregate_dataframe(df)
        
        # 再度リストに変換
        return result_df.to_dict('records')
