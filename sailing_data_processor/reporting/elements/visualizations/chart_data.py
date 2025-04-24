# -*- coding: utf-8 -*-
"""
sailing_data_processor.reporting.elements.visualizations.chart_data

チャートデータの処理と変換を行うモジュールです。
データバインディングや集計、変換などの機能を提供します。
"""

from typing import Dict, List, Any, Optional, Union, Tuple, Callable
import copy
import numpy as np
import pandas as pd
from datetime import datetime


class ChartData:
    """
    チャートデータクラス
    
    データソースからデータを取得、処理、変換するための機能を提供します。
    """
    
    def __init__(self, data: Any = None):
        """
        初期化
        
        Parameters
        ----------
        data : Any, optional
            初期データ, by default None
        """
        self.data = data
        self.transformations = []
    
    def from_context(self, context: Dict[str, Any], data_source: str) -> 'ChartData':
        """
        コンテキストからデータを取得
        
        Parameters
        ----------
        context : Dict[str, Any]
            データコンテキスト
        data_source : str
            データソース名
            
        Returns
        -------
        ChartData
            データが設定されたチャートデータオブジェクト
        """
        if not data_source or data_source not in context:
            self.data = None
            return self
        
        self.data = context[data_source]
        return self
    
    def select_fields(self, fields: List[str]) -> 'ChartData':
        """
        特定のフィールドを選択
        
        Parameters
        ----------
        fields : List[str]
            選択するフィールド名のリスト
            
        Returns
        -------
        ChartData
            処理されたチャートデータオブジェクト
        """
        if self.data is None:
            return self
        
        # リスト形式のデータの場合
        if isinstance(self.data, list) and all(isinstance(item, dict) for item in self.data):
            result = []
            for item in self.data:
                new_item = {}
                for field in fields:
                    if field in item:
                        new_item[field] = item[field]
                result.append(new_item)
            
            self.data = result
        
        # 辞書形式のデータの場合
        elif isinstance(self.data, dict):
            result = {}
            for field in fields:
                if field in self.data:
                    result[field] = self.data[field]
            
            self.data = result
        
        return self
    
    def filter(self, condition: Callable[[Any], bool]) -> 'ChartData':
        """
        条件に基づいてデータをフィルタリング
        
        Parameters
        ----------
        condition : Callable[[Any], bool]
            フィルタリング条件（各データ項目に適用される関数）
            
        Returns
        -------
        ChartData
            フィルタリングされたチャートデータオブジェクト
        """
        if self.data is None or not isinstance(self.data, list):
            return self
        
        self.data = [item for item in self.data if condition(item)]
        return self
    
    def map(self, transform: Callable[[Any], Any]) -> 'ChartData':
        """
        各データ項目に変換関数を適用
        
        Parameters
        ----------
        transform : Callable[[Any], Any]
            変換関数
            
        Returns
        -------
        ChartData
            変換されたチャートデータオブジェクト
        """
        if self.data is None:
            return self
        
        if isinstance(self.data, list):
            self.data = [transform(item) for item in self.data]
        else:
            self.data = transform(self.data)
        
        return self
    
    def sort(self, key: Optional[str] = None, reverse: bool = False) -> 'ChartData':
        """
        データを並べ替え
        
        Parameters
        ----------
        key : Optional[str], optional
            並べ替えに使用するフィールド名, by default None
        reverse : bool, optional
            逆順にするかどうか, by default False
            
        Returns
        -------
        ChartData
            並べ替えられたチャートデータオブジェクト
        """
        if self.data is None or not isinstance(self.data, list):
            return self
        
        if key is None:
            self.data = sorted(self.data, reverse=reverse)
        elif all(isinstance(item, dict) and key in item for item in self.data):
            self.data = sorted(self.data, key=lambda x: x[key], reverse=reverse)
        
        return self
    
    def limit(self, count: int) -> 'ChartData':
        """
        データの数を制限
        
        Parameters
        ----------
        count : int
            最大データ数
            
        Returns
        -------
        ChartData
            制限されたチャートデータオブジェクト
        """
        if self.data is None or not isinstance(self.data, list):
            return self
        
        self.data = self.data[:count]
        return self
    
    def group_by(self, key: str, aggregation: Dict[str, str]) -> 'ChartData':
        """
        データをグループ化して集計
        
        Parameters
        ----------
        key : str
            グループ化するフィールド名
        aggregation : Dict[str, str]
            集計方法（フィールド名: 集計関数名）
            
        Returns
        -------
        ChartData
            グループ化されたチャートデータオブジェクト
        """
        if self.data is None or not isinstance(self.data, list) or len(self.data) == 0:
            return self
        
        if not all(isinstance(item, dict) and key in item for item in self.data):
            return self
        
        # データフレームに変換
        df = pd.DataFrame(self.data)
        
        # グループ化と集計
        agg_funcs = {}
        for field, func_name in aggregation.items():
            if field in df.columns:
                agg_funcs[field] = func_name
        
        if not agg_funcs:
            return self
        
        grouped = df.groupby(key).agg(agg_funcs).reset_index()
        
        # 結果をリストに戻す
        self.data = grouped.to_dict(orient='records')
        
        return self
    
    def to_time_series(self, time_key: str, value_key: str, time_format: Optional[str] = None) -> 'ChartData':
        """
        データを時系列形式に変換
        
        Parameters
        ----------
        time_key : str
            時間データのフィールド名
        value_key : str
            値データのフィールド名
        time_format : Optional[str], optional
            時間のフォーマット, by default None
            
        Returns
        -------
        ChartData
            時系列形式に変換されたチャートデータオブジェクト
        """
        if self.data is None or not isinstance(self.data, list):
            return self
        
        if not all(isinstance(item, dict) and time_key in item and value_key in item for item in self.data):
            return self
        
        # 時間データの変換
        result = []
        for item in self.data:
            time_val = item[time_key]
            
            # 時間のフォーマット変換
            if time_format and isinstance(time_val, str):
                try:
                    dt = datetime.strptime(time_val, time_format)
                    time_val = dt.isoformat()
                except ValueError:
                    pass
            
            result.append({
                "x": time_val,
                "y": item[value_key]
            })
        
        self.data = result
        return self
    
    def to_pie_data(self, label_key: str, value_key: str) -> 'ChartData':
        """
        データを円グラフ形式に変換
        
        Parameters
        ----------
        label_key : str
            ラベルデータのフィールド名
        value_key : str
            値データのフィールド名
            
        Returns
        -------
        ChartData
            円グラフ形式に変換されたチャートデータオブジェクト
        """
        if self.data is None or not isinstance(self.data, list):
            return self
        
        if not all(isinstance(item, dict) and label_key in item and value_key in item for item in self.data):
            return self
        
        labels = [item[label_key] for item in self.data]
        values = [item[value_key] for item in self.data]
        
        self.data = {
            "labels": labels,
            "datasets": [{
                "data": values,
                "backgroundColor": self._generate_colors(len(values))
            }]
        
        return self
    
    def to_bar_data(self, label_key: str, value_key: str, series_key: Optional[str] = None) -> 'ChartData':
        """
        データを棒グラフ形式に変換
        
        Parameters
        ----------
        label_key : str
            ラベルデータのフィールド名
        value_key : str
            値データのフィールド名
        series_key : Optional[str], optional
            系列データのフィールド名, by default None
            
        Returns
        -------
        ChartData
            棒グラフ形式に変換されたチャートデータオブジェクト
        """
        if self.data is None or not isinstance(self.data, list):
            return self
        
        if not all(isinstance(item, dict) and label_key in item and value_key in item for item in self.data):
            return self
        
        # 単一系列の場合
        if series_key is None:
            labels = [item[label_key] for item in self.data]
            values = [item[value_key] for item in self.data]
            
            self.data = {
                "labels": labels,
                "datasets": [{
                    "data": values,
                    "backgroundColor": self._generate_colors(1)[0],
                    "borderColor": self._generate_border_colors(1)[0],
                    "borderWidth": 1
                }]
        else:
            # 複数系列の場合
            if not all(series_key in item for item in self.data):
                return self
            
            # ラベルと系列の一意なリストを取得
            labels = list(set(item[label_key] for item in self.data))
            series = list(set(item[series_key] for item in self.data))
            
            # 系列ごとにデータセットを作成
            datasets = []
            colors = self._generate_colors(len(series))
            border_colors = self._generate_border_colors(len(series))
            
            for i, s in enumerate(series):
                # この系列のデータを抽出
                series_data = {item[label_key]: item[value_key] for item in self.data if item[series_key] == s}
                
                # すべてのラベルに対する値を取得
                values = [series_data.get(label, 0) for label in labels]
                
                datasets.append({
                    "label": str(s),
                    "data": values,
                    "backgroundColor": colors[i],
                    "borderColor": border_colors[i],
                    "borderWidth": 1
                })
            
            self.data = {
                "labels": labels,
                "datasets": datasets
        
        return self
    
    def to_scatter_data(self, x_key: str, y_key: str, series_key: Optional[str] = None) -> 'ChartData':
        """
        データを散布図形式に変換
        
        Parameters
        ----------
        x_key : str
            X軸データのフィールド名
        y_key : str
            Y軸データのフィールド名
        series_key : Optional[str], optional
            系列データのフィールド名, by default None
            
        Returns
        -------
        ChartData
            散布図形式に変換されたチャートデータオブジェクト
        """
        if self.data is None or not isinstance(self.data, list):
            return self
        
        if not all(isinstance(item, dict) and x_key in item and y_key in item for item in self.data):
            return self
        
        # 単一系列の場合
        if series_key is None:
            points = [{"x": item[x_key], "y": item[y_key]} for item in self.data]
            
            self.data = {
                "datasets": [{
                    "data": points,
                    "backgroundColor": self._generate_colors(1)[0],
                    "borderColor": self._generate_border_colors(1)[0],
                    "borderWidth": 1,
                    "pointRadius": 4,
                    "pointHoverRadius": 6
                }]
        else:
            # 複数系列の場合
            if not all(series_key in item for item in self.data):
                return self
            
            # 系列の一意なリストを取得
            series = list(set(item[series_key] for item in self.data))
            
            # 系列ごとにデータセットを作成
            datasets = []
            colors = self._generate_colors(len(series))
            border_colors = self._generate_border_colors(len(series))
            
            for i, s in enumerate(series):
                # この系列のデータを抽出
                series_data = [{"x": item[x_key], "y": item[y_key]} for item in self.data if item[series_key] == s]
                
                datasets.append({
                    "label": str(s),
                    "data": series_data,
                    "backgroundColor": colors[i],
                    "borderColor": border_colors[i],
                    "borderWidth": 1,
                    "pointRadius": 4,
                    "pointHoverRadius": 6
                })
            
            self.data = {
                "datasets": datasets
        
        return self
    
    def to_line_data(self, x_key: str, y_key: str, series_key: Optional[str] = None) -> 'ChartData':
        """
        データを折れ線グラフ形式に変換
        
        Parameters
        ----------
        x_key : str
            X軸データのフィールド名
        y_key : str
            Y軸データのフィールド名
        series_key : Optional[str], optional
            系列データのフィールド名, by default None
            
        Returns
        -------
        ChartData
            折れ線グラフ形式に変換されたチャートデータオブジェクト
        """
        if self.data is None or not isinstance(self.data, list):
            return self
        
        if not all(isinstance(item, dict) and x_key in item and y_key in item for item in self.data):
            return self
        
        # 前処理：データをX値でソート
        self.data = sorted(self.data, key=lambda item: item[x_key])
        
        # 単一系列の場合
        if series_key is None:
            x_values = [item[x_key] for item in self.data]
            y_values = [item[y_key] for item in self.data]
            
            self.data = {
                "labels": x_values,
                "datasets": [{
                    "data": y_values,
                    "backgroundColor": self._generate_colors(1)[0] + "33",  # 透明度を追加
                    "borderColor": self._generate_border_colors(1)[0],
                    "borderWidth": 2,
                    "tension": 0.1,
                    "fill": True
                }]
        else:
            # 複数系列の場合
            if not all(series_key in item for item in self.data):
                return self
            
            # 系列の一意なリストを取得
            series = list(set(item[series_key] for item in self.data))
            
            # すべてのX値の一意なリストを取得
            all_x_values = sorted(list(set(item[x_key] for item in self.data)))
            
            # 系列ごとにデータセットを作成
            datasets = []
            colors = self._generate_colors(len(series))
            border_colors = self._generate_border_colors(len(series))
            
            for i, s in enumerate(series):
                # この系列のデータを抽出
                series_data = {item[x_key]: item[y_key] for item in self.data if item[series_key] == s}
                
                # すべてのX値に対する値を取得
                values = [series_data.get(x, None) for x in all_x_values]
                
                datasets.append({
                    "label": str(s),
                    "data": values,
                    "backgroundColor": colors[i] + "33",  # 透明度を追加
                    "borderColor": border_colors[i],
                    "borderWidth": 2,
                    "tension": 0.1,
                    "fill": True
                })
            
            self.data = {
                "labels": all_x_values,
                "datasets": datasets
        
        return self
    
    def set_data(self, data: Any) -> 'ChartData':
        """
        データを直接設定
        
        Parameters
        ----------
        data : Any
            設定するデータ
            
        Returns
        -------
        ChartData
            データが設定されたチャートデータオブジェクト
        """
        self.data = data
        return self
    
    def get_data(self) -> Any:
        """
        データを取得
        
        Returns
        -------
        Any
            現在のデータ
        """
        return self.data
    
    def _generate_colors(self, count: int) -> List[str]:
        """
        指定された数の色を生成
        
        Parameters
        ----------
        count : int
            色の数
            
        Returns
        -------
        List[str]
            生成された色のリスト（RGBA形式）
        """
        colors = [
            "rgba(54, 162, 235, 0.7)",    # 青
            "rgba(255, 99, 132, 0.7)",    # 赤
            "rgba(75, 192, 192, 0.7)",    # 緑/シアン
            "rgba(255, 159, 64, 0.7)",    # オレンジ
            "rgba(153, 102, 255, 0.7)",   # 紫
            "rgba(255, 205, 86, 0.7)",    # 黄
            "rgba(201, 203, 207, 0.7)",   # グレー
            "rgba(255, 99, 71, 0.7)",     # トマト
            "rgba(50, 205, 50, 0.7)",     # ライム
            "rgba(65, 105, 225, 0.7)"     # ロイヤルブルー
        ]
        
        # 必要な色の数が用意されている色より多い場合は繰り返す
        if count > len(colors):
            colors = colors * (count // len(colors) + 1)
        
        return colors[:count]
    
    def _generate_border_colors(self, count: int) -> List[str]:
        """
        指定された数の境界線色を生成
        
        Parameters
        ----------
        count : int
            色の数
            
        Returns
        -------
        List[str]
            生成された色のリスト（RGBA形式）
        """
        colors = [
            "rgba(54, 162, 235, 1)",    # 青
            "rgba(255, 99, 132, 1)",    # 赤
            "rgba(75, 192, 192, 1)",    # 緑/シアン
            "rgba(255, 159, 64, 1)",    # オレンジ
            "rgba(153, 102, 255, 1)",   # 紫
            "rgba(255, 205, 86, 1)",    # 黄
            "rgba(201, 203, 207, 1)",   # グレー
            "rgba(255, 99, 71, 1)",     # トマト
            "rgba(50, 205, 50, 1)",     # ライム
            "rgba(65, 105, 225, 1)"     # ロイヤルブルー
        ]
        
        # 必要な色の数が用意されている色より多い場合は繰り返す
        if count > len(colors):
            colors = colors * (count // len(colors) + 1)
        
        return colors[:count]


class ChartDataTransformation:
    """
    チャートデータ変換クラス
    
    データ変換操作を定義し、実行するための基底クラスです。
    """
    
    def __init__(self, transform_func: Callable[[Any], Any]):
        """
        初期化
        
        Parameters
        ----------
        transform_func : Callable[[Any], Any]
            変換関数
        """
        self.transform_func = transform_func
    
    def apply(self, data: Any) -> Any:
        """
        変換を適用
        
        Parameters
        ----------
        data : Any
            変換するデータ
            
        Returns
        -------
        Any
            変換されたデータ
        """
        return self.transform_func(data)
