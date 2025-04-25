# -*- coding: utf-8 -*-
"""
sailing_data_processor.reporting.elements.visualizations.distribution_charts

分布図チャート要素を提供するモジュールです。
ヒストグラム、バイオリンプロット、カーネル密度推定などの分布可視化要素を実装します。
"""

from typing import Dict, List, Any, Optional, Union, Tuple
import json
import html
import math
import numpy as np

from sailing_data_processor.reporting.elements.visualizations.base_chart import BaseChartElement
from sailing_data_processor.reporting.templates.template_model import ElementType, ElementModel


class DistributionChartElement(BaseChartElement):
    """
    分布図要素
    
    データの分布を表示するためのチャート要素です。
    ヒストグラム、バイオリンプロット、KDEなどの表示形式をサポートします。
    """
    
    def __init__(self, model: Optional[ElementModel] = None, **kwargs):
        """
        初期化
        
        Parameters
        ----------
        model : Optional[ElementModel], optional
            要素モデル, by default None
        **kwargs : dict
            モデルが提供されない場合に使用されるプロパティ
        """
        # デフォルトでチャート要素タイプを設定
        if model is None and 'element_type' not in kwargs:
            kwargs['element_type'] = ElementType.CHART
        
        if model is None and 'chart_type' not in kwargs:
            kwargs['chart_type'] = "bar"
        
        super().__init__(model, **kwargs)
    
    def get_chart_libraries(self) -> List[str]:
        """
        チャートの描画に必要なライブラリのリストを取得
        
        Returns
        -------
        List[str]
            ライブラリのURLリスト
        """
        chart_type = self.get_property("distribution_type", "histogram")
        libraries = [
            "https://cdn.jsdelivr.net/npm/chart.js@3.7.1/dist/chart.min.js"
        ]
        
        # チャートタイプによって追加のライブラリが必要な場合はここで追加
        if chart_type == "violin":
            libraries.append("https://cdn.jsdelivr.net/npm/chartjs-chart-box-and-violin-plot@3.0.0/build/Chart.BoxPlot.min.js")
        
        return libraries
    
    def get_chart_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        分布図のデータを取得
        
        Parameters
        ----------
        context : Dict[str, Any]
            コンテキスト
            
        Returns
        -------
        Dict[str, Any]
            チャートデータ
        """
        # データソースからデータを取得
        data = None
        if self.data_source and self.data_source in context:
            data = context[self.data_source]
        
        # データがない場合は空のデータを返す
        if not data:
            return {"type": "bar", "data": {"labels": [], "datasets": []}}
        
        # グラフの種類を取得
        chart_type = self.get_property("distribution_type", "histogram")
        
        # 値キーを取得
        value_key = self.get_property("value_key", "value")
        
        # カテゴリ/グループキーを取得
        category_key = self.get_property("category_key", None)
        
        # データを分布形式に変換
        if chart_type == "histogram":
            return self._prepare_histogram_data(data, value_key, category_key)
        elif chart_type == "violin":
            return self._prepare_violin_data(data, value_key, category_key)
        elif chart_type == "kde":
            return self._prepare_kde_data(data, value_key, category_key)
        else:
            # デフォルトはヒストグラム
            return self._prepare_histogram_data(data, value_key, category_key)
    
    def _prepare_histogram_data(self, data: Any, value_key: str, category_key: Optional[str]) -> Dict[str, Any]:
        """
        ヒストグラム用のデータを準備
        
        Parameters
        ----------
        data : Any
            元データ
        value_key : str
            値キー
        category_key : Optional[str]
            カテゴリ/グループキー
            
        Returns
        -------
        Dict[str, Any]
            チャートデータ
        """
        # ビンの数を取得
        bin_count = self.get_property("bin_count", 10)
        
        # データ型に応じた処理
        values = []
        categories = []
        
        if isinstance(data, list):
            if len(data) > 0 and isinstance(data[0], dict):
                # 辞書のリストの場合
                for item in data:
                    if value_key in item:
                        value = item[value_key]
                        if isinstance(value, (int, float)):
                            values.append(value)
                            if category_key and category_key in item:
                                categories.append(item[category_key])
            else:
                # 単純なリストの場合
                values = [v for v in data if isinstance(v, (int, float))]
        
        # 値がない場合は空のデータを返す
        if not values:
            return {"type": "bar", "data": {"labels": [], "datasets": []}}
        
        # カテゴリがある場合はカテゴリごとに処理
        if category_key and categories:
            # カテゴリのユニーク値を取得
            unique_categories = sorted(list(set(categories)))
            
            # カテゴリごとに値をグループ化
            category_values = {cat: [] for cat in unique_categories}
            for i, value in enumerate(values):
                if i < len(categories):
                    cat = categories[i]
                    if cat in category_values:
                        category_values[cat].append(value)
            
            # 共通のビン範囲を決定
            min_val = min(values)
            max_val = max(values)
            bin_width = (max_val - min_val) / bin_count
            
            # ビンの境界を計算
            bin_edges = [min_val + i * bin_width for i in range(bin_count + 1)]
            
            # ラベルを設定（ビンの中央値）
            labels = [(bin_edges[i] + bin_edges[i + 1]) / 2 for i in range(len(bin_edges) - 1)]
            labels = [f"{label:.2f}" for label in labels]
            
            # カテゴリごとにヒストグラムを計算
            datasets = []
            colors = self._get_colors(len(unique_categories))
            
            for i, category in enumerate(unique_categories):
                cat_values = category_values[category]
                
                # 空のカテゴリはスキップ
                if not cat_values:
                    continue
                
                # ヒストグラムのカウントを計算
                counts, _ = np.histogram(cat_values, bins=bin_edges)
                
                datasets.append({
                    "label": str(category),
                    "data": counts.tolist(),
                    "backgroundColor": colors[i],
                    "borderColor": colors[i].replace("0.6", "1.0"),
                    "borderWidth": 1
                })
            
            return {
                "type": "bar",
                "data": {
                    "labels": labels,
                    "datasets": datasets
 {
                "type": "bar",
                "data": {
                    "labels": labels,
                    "datasets": datasets}
            return {
                "type": "bar",
                "data": {
                    "labels": labels,
                    "datasets": datasets}
 {
                "type": "bar",
                "data": {
                    "labels": labels,
                    "datasets": datasets}}
        
        else:
            # カテゴリなしの場合、単一のヒストグラムを計算
            min_val = min(values)
            max_val = max(values)
            bin_width = (max_val - min_val) / bin_count
            
            # ビンの境界を計算
            bin_edges = [min_val + i * bin_width for i in range(bin_count + 1)]
            
            # ラベルを設定（ビンの中央値）
            labels = [(bin_edges[i] + bin_edges[i + 1]) / 2 for i in range(len(bin_edges) - 1)]
            labels = [f"{label:.2f}" for label in labels]
            
            # ヒストグラムのカウントを計算
            counts, _ = np.histogram(values, bins=bin_edges)
            
            return {
                "type": "bar",
                "data": {
                    "labels": labels,
                    "datasets": [{
                        "label": self.get_property("dataset_label", "頻度"),
                        "data": counts.tolist(),
                        "backgroundColor": "rgba(54, 162, 235, 0.6)",
                        "borderColor": "rgba(54, 162, 235, 1.0)",
                        "borderWidth": 1
 {
                "type": "bar",
                "data": {
                    "labels": labels,
                    "datasets": [{
                        "label": self.get_property("dataset_label", "頻度"),
                        "data": counts.tolist(),
                        "backgroundColor": "rgba(54, 162, 235, 0.6)",
                        "borderColor": "rgba(54, 162, 235, 1.0)",
                        "borderWidth": 1}
                    }]
    
    def _prepare_violin_data(self, data: Any, value_key: str, category_key: Optional[str]) -> Dict[str, Any]:
        """
        バイオリンプロット用のデータを準備
        
        Parameters
        ----------
        data : Any
            元データ
        value_key : str
            値キー
        category_key : Optional[str]
            カテゴリ/グループキー
            
        Returns
        -------
        Dict[str, Any]
            チャートデータ
        """
        # データ型に応じた処理
        values = []
        categories = []
        
        if isinstance(data, list):
            if len(data) > 0 and isinstance(data[0], dict):
                # 辞書のリストの場合
                for item in data:
                    if value_key in item:
                        value = item[value_key]
                        if isinstance(value, (int, float)):
                            values.append(value)
                            if category_key and category_key in item:
                                categories.append(item[category_key])
            else:
                # 単純なリストの場合
                values = [v for v in data if isinstance(v, (int, float))]
        
        # 値がない場合は空のデータを返す
        if not values:
            return {"type": "violin", "data": {"labels": [], "datasets": []}}
        
        # カテゴリがある場合はカテゴリごとに処理
        if category_key and categories:
            # カテゴリのユニーク値を取得
            unique_categories = sorted(list(set(categories)))
            
            # カテゴリごとに値をグループ化
            category_values = {cat: [] for cat in unique_categories}
            for i, value in enumerate(values):
                if i < len(categories):
                    cat = categories[i]
                    if cat in category_values:
                        category_values[cat].append(value)
            
            # ラベルを設定
            labels = unique_categories
            
            # データを準備
            violin_data = []
            for category in unique_categories:
                violin_data.append(category_values[category])
            
            return {
                "type": "violin",
                "data": {
                    "labels": labels,
                    "datasets": [{
                        "label": self.get_property("dataset_label", "分布"),
                        "data": violin_data,
                        "backgroundColor": "rgba(54, 162, 235, 0.6)",
                        "borderColor": "rgba(54, 162, 235, 1.0)",
                        "borderWidth": 1,
                        "outlierColor": "rgba(255, 99, 132, 0.8)",
                        "outlierRadius": 5
 {
                "type": "violin",
                "data": {
                    "labels": labels,
                    "datasets": [{
                        "label": self.get_property("dataset_label", "分布"),
                        "data": violin_data,
                        "backgroundColor": "rgba(54, 162, 235, 0.6)",
                        "borderColor": "rgba(54, 162, 235, 1.0)",
                        "borderWidth": 1,
                        "outlierColor": "rgba(255, 99, 132, 0.8)",
                        "outlierRadius": 5}
                    }]
        
        else:
            # カテゴリなしの場合、単一のバイオリンプロット
            return {
                "type": "violin",
                "data": {
                    "labels": ["全データ"],
                    "datasets": [{
                        "label": self.get_property("dataset_label", "分布"),
                        "data": [values],
                        "backgroundColor": "rgba(54, 162, 235, 0.6)",
                        "borderColor": "rgba(54, 162, 235, 1.0)",
                        "borderWidth": 1,
                        "outlierColor": "rgba(255, 99, 132, 0.8)",
                        "outlierRadius": 5
 {
                "type": "violin",
                "data": {
                    "labels": ["全データ"],
                    "datasets": [{
                        "label": self.get_property("dataset_label", "分布"),
                        "data": [values],
                        "backgroundColor": "rgba(54, 162, 235, 0.6)",
                        "borderColor": "rgba(54, 162, 235, 1.0)",
                        "borderWidth": 1,
                        "outlierColor": "rgba(255, 99, 132, 0.8)",
                        "outlierRadius": 5}
                    }]
    
    def _prepare_kde_data(self, data: Any, value_key: str, category_key: Optional[str]) -> Dict[str, Any]:
        """
        カーネル密度推定(KDE)用のデータを準備
        
        Parameters
        ----------
        data : Any
            元データ
        value_key : str
            値キー
        category_key : Optional[str]
            カテゴリ/グループキー
            
        Returns
        -------
        Dict[str, Any]
            チャートデータ
        """
        # 解像度（点の数）を取得
        resolution = self.get_property("kde_resolution", 100)
        
        # バンド幅係数
        bandwidth_factor = self.get_property("kde_bandwidth_factor", 1.0)
        
        # データ型に応じた処理
        values = []
        categories = []
        
        if isinstance(data, list):
            if len(data) > 0 and isinstance(data[0], dict):
                # 辞書のリストの場合
                for item in data:
                    if value_key in item:
                        value = item[value_key]
                        if isinstance(value, (int, float)):
                            values.append(value)
                            if category_key and category_key in item:
                                categories.append(item[category_key])
            else:
                # 単純なリストの場合
                values = [v for v in data if isinstance(v, (int, float))]
        
        # 値がない場合は空のデータを返す
        if not values:
            return {"type": "line", "data": {"labels": [], "datasets": []}}
        
        # カテゴリがある場合はカテゴリごとに処理
        if category_key and categories:
            # カテゴリのユニーク値を取得
            unique_categories = sorted(list(set(categories)))
            
            # カテゴリごとに値をグループ化
            category_values = {cat: [] for cat in unique_categories}
            for i, value in enumerate(values):
                if i < len(categories):
                    cat = categories[i]
                    if cat in category_values:
                        category_values[cat].append(value)
            
            # 共通のx軸の範囲を決定
            min_val = min(values)
            max_val = max(values)
            range_vals = max_val - min_val
            
            # 範囲を少し広げる
            x_min = min_val - range_vals * 0.05
            x_max = max_val + range_vals * 0.05
            
            # x軸の値を生成
            x_vals = np.linspace(x_min, x_max, resolution)
            
            # カテゴリごとにKDEを計算
            datasets = []
            colors = self._get_colors(len(unique_categories))
            
            for i, category in enumerate(unique_categories):
                cat_values = category_values[category]
                
                # 空のカテゴリはスキップ
                if not cat_values:
                    continue
                
                # KDEを計算（ガウシアンカーネルを使用）
                kde_values = self._gaussian_kde(cat_values, x_vals, bandwidth_factor)
                
                datasets.append({
                    "label": str(category),
                    "data": kde_values,
                    "borderColor": colors[i],
                    "backgroundColor": colors[i].replace("1.0", "0.2"),
                    "borderWidth": 2,
                    "fill": True,
                    "tension": 0.4,
                    "pointRadius": 0
                })
            
            return {
                "type": "line",
                "data": {
                    "labels": x_vals.tolist(),
                    "datasets": datasets
 {
                "type": "line",
                "data": {
                    "labels": x_vals.tolist(),
                    "datasets": datasets}
            return {
                "type": "line",
                "data": {
                    "labels": x_vals.tolist(),
                    "datasets": datasets}
 {
                "type": "line",
                "data": {
                    "labels": x_vals.tolist(),
                    "datasets": datasets}}
        
        else:
            # カテゴリなしの場合、単一のKDEを計算
            min_val = min(values)
            max_val = max(values)
            range_vals = max_val - min_val
            
            # 範囲を少し広げる
            x_min = min_val - range_vals * 0.05
            x_max = max_val + range_vals * 0.05
            
            # x軸の値を生成
            x_vals = np.linspace(x_min, x_max, resolution)
            
            # KDEを計算
            kde_values = self._gaussian_kde(values, x_vals, bandwidth_factor)
            
            return {
                "type": "line",
                "data": {
                    "labels": x_vals.tolist(),
                    "datasets": [{
                        "label": self.get_property("dataset_label", "密度"),
                        "data": kde_values,
                        "borderColor": "rgba(54, 162, 235, 1.0)",
                        "backgroundColor": "rgba(54, 162, 235, 0.2)",
                        "borderWidth": 2,
                        "fill": True,
                        "tension": 0.4,
                        "pointRadius": 0
 {
                "type": "line",
                "data": {
                    "labels": x_vals.tolist(),
                    "datasets": [{
                        "label": self.get_property("dataset_label", "密度"),
                        "data": kde_values,
                        "borderColor": "rgba(54, 162, 235, 1.0)",
                        "backgroundColor": "rgba(54, 162, 235, 0.2)",
                        "borderWidth": 2,
                        "fill": True,
                        "tension": 0.4,
                        "pointRadius": 0}
                    }]
    
    def get_chart_options(self) -> Dict[str, Any]:
        """
        分布図のオプションを取得
        
        Returns
        -------
        Dict[str, Any]
            チャートオプション
        """
        options = super().get_chart_options()
        
        # グラフの種類を取得
        chart_type = self.get_property("distribution_type", "histogram")
        
        # 分布図共通のオプション
        distribution_options = {
            "scales": {
                "y": {
                    "beginAtZero": True,
                    "title": {
                        "display": True,
                        "text": self.get_property("y_axis_title", "頻度" if chart_type == "histogram" else "密度")
 {
            "scales": {
                "y": {
                    "beginAtZero": True,
                    "title": {
                        "display": True,
                        "text": self.get_property("y_axis_title", "頻度" if chart_type == "histogram" else "密度")}
                },
                "x": {
                    "title": {
                        "display": True,
                        "text": self.get_property("x_axis_title", "値")
 {
                    "title": {
                        "display": True,
                        "text": self.get_property("x_axis_title", "値")}
            },
            "plugins": {
                "tooltip": {
                    "mode": "index"
 {
                "tooltip": {
                    "mode": "index"}
        
        # チャートタイプに応じたオプション
        if chart_type == "histogram":
            # ヒストグラム特有のオプション
            histogram_options = {
                "plugins": {
                    "legend": {
                        "display": self.get_property("category_key") is not None
 {
                "plugins": {
                    "legend": {
                        "display": self.get_property("category_key") is not None}
                },
                "scales": {
                    "x": {
                        "offset": True,
                        "grid": {
                            "offset": True
 {
                    "x": {
                        "offset": True,
                        "grid": {
                            "offset": True}
            
            # カテゴリがある場合の表示設定
            if self.get_property("category_key"):
                histogram_options["barPercentage"] = 0.9
                histogram_options["categoryPercentage"] = 0.8
                
                if self.get_property("stacked", False):
                    histogram_options["scales"]["y"]["stacked"] = True
                    histogram_options["scales"]["x"]["stacked"] = True
            
            # オプションを結合
            self._merge_options(distribution_options, histogram_options)
        
        elif chart_type == "violin":
            # バイオリンプロット特有のオプション
            violin_options = {
                "scales": {
                    "y": {
                        "ticks": {
                            "min": self.get_property("y_min", None),
                            "max": self.get_property("y_max", None)
 {
                "scales": {
                    "y": {
                        "ticks": {
                            "min": self.get_property("y_min", None),
                            "max": self.get_property("y_max", None)}
            
            # オプションを結合
            self._merge_options(distribution_options, violin_options)
        
        elif chart_type == "kde":
            # KDE特有のオプション
            kde_options = {
                "scales": {
                    "y": {
                        "beginAtZero": True,
                        "ticks": {
                            "min": 0
 {
                "scales": {
                    "y": {
                        "beginAtZero": True,
                        "ticks": {
                            "min": 0}
            
            # オプションを結合
            self._merge_options(distribution_options, kde_options)
        
        # オプションを結合
        self._merge_options(options, distribution_options)
        
        return options
    
    def get_chart_initialization_code(self, config_var: str = "config") -> str:
        """
        分布図初期化用のJavaScriptコードを取得
        
        Parameters
        ----------
        config_var : str, optional
            設定変数名, by default "config"
            
        Returns
        -------
        str
            初期化コード
        """
        chart_type = self.get_property("distribution_type", "histogram")
        
        if chart_type == "violin":
            return f"""
                Chart.register(ChartBoxPlot);
                var ctx = document.getElementById('{self.chart_id}').getContext('2d');
                new Chart(ctx, {config_var});
            """
        else:
            return f"""
                var ctx = document.getElementById('{self.chart_id}').getContext('2d');
                new Chart(ctx, {config_var});
            """
    
    def _gaussian_kde(self, data: List[float], x_grid: np.ndarray, bandwidth_factor: float = 1.0) -> List[float]:
        """
        ガウシアンカーネル密度推定を計算
        
        Parameters
        ----------
        data : List[float]
            データ値
        x_grid : np.ndarray
            評価するx座標のグリッド
        bandwidth_factor : float, optional
            バンド幅係数, by default 1.0
            
        Returns
        -------
        List[float]
            KDE値
        """
        # データをNumPy配列に変換
        data_np = np.array(data)
        
        # シルバーマンの経験則に基づくバンド幅の推定
        n = len(data_np)
        sigma = np.std(data_np)
        
        # サンプル数が少ない場合、分散が0の場合の対策
        if n < 2 or sigma < 1e-6:
            sigma = 1.0
        
        # バンド幅の計算（シルバーマンの公式）
        bandwidth = 0.9 * sigma * n**(-0.2) * bandwidth_factor
        
        # KDEの計算
        kde_values = []
        for x in x_grid:
            # 各データポイントからの距離を計算
            distances = (x - data_np) / bandwidth
            
            # ガウシアンカーネルを適用
            kernel_values = np.exp(-0.5 * distances**2) / (np.sqrt(2 * np.pi) * bandwidth)
            
            # KDE値の計算
            kde_value = np.sum(kernel_values) / n
            kde_values.append(kde_value)
        
        return kde_values
    
    def _get_colors(self, count: int) -> List[str]:
        """
        指定された数のカラーリストを取得
        
        Parameters
        ----------
        count : int
            必要な色の数
            
        Returns
        -------
        List[str]
            色のリスト
        """
        base_colors = [
            "rgba(54, 162, 235, 1.0)",  # 青
            "rgba(255, 99, 132, 1.0)",  # 赤
            "rgba(75, 192, 192, 1.0)",  # 緑
            "rgba(255, 159, 64, 1.0)",  # オレンジ
            "rgba(153, 102, 255, 1.0)",  # 紫
            "rgba(255, 205, 86, 1.0)",  # 黄
            "rgba(201, 203, 207, 1.0)",  # グレー
            "rgba(0, 128, 128, 1.0)",  # ティール
            "rgba(255, 0, 255, 1.0)",  # マゼンタ
            "rgba(128, 0, 0, 1.0)"     # マルーン
        ]
        
        # 必要な色の数がベース色より多い場合は、透明度を変えて追加
        colors = []
        for i in range(count):
            if i < len(base_colors):
                colors.append(base_colors[i])
            else:
                # ベース色のインデックス
                base_idx = i % len(base_colors)
                # 透明度を調整（0.3から0.9の範囲）
                opacity = 0.3 + (0.6 * ((i // len(base_colors)) % 2))
                color = base_colors[base_idx].replace("1.0", f"{opacity}")
                colors.append(color)
        
        return colors
    
    def _merge_options(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """
        オプション辞書を再帰的にマージ
        
        Parameters
        ----------
        target : Dict[str, Any]
            ターゲット辞書
        source : Dict[str, Any]
            ソース辞書
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._merge_options(target[key], value)
            else:
                target[key] = value
