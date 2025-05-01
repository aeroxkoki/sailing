# -*- coding: utf-8 -*-
"""
時系列分析グラフ要素モジュール。
このモジュールは、複数パラメータの時間変化を表示するための要素を提供します。
"""

from typing import Dict, List, Any, Optional
import math

from sailing_data_processor.reporting.elements.visualizations.base_chart import BaseChartElement
from sailing_data_processor.reporting.templates.template_model import ElementType, ElementModel


class TimeSeriesElement(BaseChartElement):
    """
    時系列分析グラフ要素
    
    複数パラメータの時間変化を表示するための要素です。
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
            kwargs['chart_type'] = "line"
        
        super().__init__(model, **kwargs)
    
    def get_chart_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        時系列グラフのデータを取得
        
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
            return {"type": "line", "data": {"labels": [], "datasets": []}}
        
        # 時間キーと値キーを取得
        time_key = self.get_property("time_key", "time")
        value_keys = self.get_property("value_keys", [])
        
        # 値キーが指定されていない場合は、データから推測
        if not value_keys and isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            # 最初のデータ項目からキーを取得（時間キーを除く）
            value_keys = [key for key in data[0].keys() if key != time_key]
        
        # 時間ラベルと各系列のデータを抽出
        labels = []
        datasets = []
        
        if isinstance(data, list) and all(isinstance(item, dict) for item in data):
            # 時間ラベルを抽出
            labels = [item.get(time_key, "") for item in data]
            
            # 各値キーに対してデータセットを作成
            colors = self._get_colors(len(value_keys))
            
            for i, key in enumerate(value_keys):
                values = [item.get(key, None) for item in data]
                
                # データセットを作成
                dataset = {
                    "label": self.get_property(f"label_{key}", key),
                    "data": values,
                    "fill": False,
                    "borderColor": colors[i],
                    "backgroundColor": colors[i].replace("1)", "0.1)"),
                    "borderWidth": 2,
                    "pointRadius": 3,
                    "pointBackgroundColor": colors[i],
                    "tension": 0.1
                }
                
                datasets.append(dataset)
        
        # 移動平均の追加
        moving_avg = self.get_property("moving_average", False)
        if moving_avg and datasets:
            window_size = self.get_property("moving_average_window", 5)
            
            for dataset in datasets:
                # 移動平均を計算
                values = dataset["data"]
                if all(v is not None for v in values):
                    avg_values = self._calculate_moving_average(values, window_size)
                    
                    # 移動平均データセットを作成
                    avg_dataset = {
                        "label": f"{dataset['label']} (移動平均)",
                        "data": avg_values,
                        "fill": False,
                        "borderColor": dataset["borderColor"].replace("1)", "0.7)"),
                        "backgroundColor": "transparent",
                        "borderWidth": 1,
                        "borderDash": [5, 5],
                        "pointRadius": 0,
                        "tension": 0.4
                    }
                    
                    datasets.append(avg_dataset)
        
        # トレンドラインの追加
        trendline = self.get_property("trendline", False)
        if trendline and datasets and all(len(dataset["data"]) == len(labels) for dataset in datasets):
            for dataset in datasets:
                if "移動平均" in dataset["label"]:
                    continue  # 移動平均系列にはトレンドラインを追加しない
                
                # トレンドラインを計算
                values = dataset["data"]
                if all(v is not None for v in values):
                    trend_values = self._calculate_trendline(values)
                    
                    # トレンドラインデータセットを作成
                    trend_dataset = {
                        "label": f"{dataset['label']} (トレンド)",
                        "data": trend_values,
                        "fill": False,
                        "borderColor": dataset["borderColor"].replace("1)", "0.5)"),
                        "backgroundColor": "transparent",
                        "borderWidth": 2,
                        "borderDash": [10, 5],
                        "pointRadius": 0,
                        "tension": 0
                    }
                    
                    datasets.append(trend_dataset)
        
        # 異常値のハイライト
        highlight_outliers = self.get_property("highlight_outliers", False)
        if highlight_outliers and datasets:
            threshold = self.get_property("outlier_threshold", 2.0)  # 標準偏差の倍数
            
            for dataset in datasets:
                if "移動平均" in dataset["label"] or "トレンド" in dataset["label"]:
                    continue  # 派生系列には異常値ハイライトを適用しない
                
                values = dataset["data"]
                if all(v is not None for v in values):
                    # 異常値を検出
                    outlier_indices = self._detect_outliers(values, threshold)
                    
                    if outlier_indices:
                        # 異常値用のデータセットを作成
                        outlier_data = [None] * len(values)
                        for idx in outlier_indices:
                            outlier_data[idx] = values[idx]
                        
                        outlier_dataset = {
                            "label": f"{dataset['label']} (異常値)",
                            "data": outlier_data,
                            "fill": False,
                            "borderColor": "rgba(255, 0, 0, 1)",
                            "backgroundColor": "rgba(255, 0, 0, 0.8)",
                            "borderWidth": 0,
                            "pointRadius": 6,
                            "pointStyle": "circle",
                            "showLine": False
                        }
                        
                        datasets.append(outlier_dataset)
        
        # チャートデータの作成
        chart_data = {
            "type": "line",
            "data": {
                "labels": labels,
                "datasets": datasets
            }
        }
        
        return chart_data
    
    def get_chart_options(self) -> Dict[str, Any]:
        """
        時系列グラフのオプションを取得
        
        Returns
        -------
        Dict[str, Any]
            チャートオプション
        """
        options = super().get_chart_options()
        
        # 時系列グラフ特有のオプション
        timeseries_options = {
            "scales": {
                "x": {
                    "type": "time",
                    "time": {
                        "unit": self.get_property("time_unit", "minute"),
                        "displayFormats": {
                            "minute": "HH:mm",
                            "hour": "HH:mm",
                            "day": "MM/DD",
                            "week": "MM/DD",
                            "month": "YYYY/MM",
                            "year": "YYYY"
                        }
                    },
                    "title": {
                        "display": True,
                        "text": self.get_property("x_axis_title", "時間")
                    }
                },
                "y": {
                    "beginAtZero": self.get_property("begin_at_zero", False),
                    "title": {
                        "display": True,
                        "text": self.get_property("y_axis_title", "値")
                    }
                }
            },
            "plugins": {
                "tooltip": {
                    "mode": "index",
                    "intersect": False
                },
                "zoom": {
                    "pan": {
                        "enabled": True,
                        "mode": "x"
                    },
                    "zoom": {
                        "enabled": True,
                        "mode": "x",
                        "speed": 0.1
                    }
                }
            },
            "interaction": {
                "mode": "nearest",
                "axis": "x",
                "intersect": False
            }
        }
        
        # オプションを結合
        self._merge_options(options, timeseries_options)
        
        return options
    
    def get_chart_libraries(self) -> List[str]:
        """
        チャートの描画に必要なライブラリのリストを取得
        
        Returns
        -------
        List[str]
            ライブラリのURLリスト
        """
        return [
            "https://cdn.jsdelivr.net/npm/chart.js@3.7.1/dist/chart.min.js",
            "https://cdn.jsdelivr.net/npm/moment@2.29.1/moment.min.js",
            "https://cdn.jsdelivr.net/npm/chartjs-adapter-moment@1.0.0/dist/chartjs-adapter-moment.min.js",
            "https://cdn.jsdelivr.net/npm/hammerjs@2.0.8/hammer.min.js",
            "https://cdn.jsdelivr.net/npm/chartjs-plugin-zoom@1.2.1/dist/chartjs-plugin-zoom.min.js"
        ]
    
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
            "rgba(54, 162, 235, 1)",  # 青
            "rgba(255, 99, 132, 1)",  # 赤
            "rgba(75, 192, 192, 1)",  # 緑
            "rgba(255, 159, 64, 1)",  # オレンジ
            "rgba(153, 102, 255, 1)",  # 紫
            "rgba(255, 205, 86, 1)",  # 黄
            "rgba(201, 203, 207, 1)",  # グレー
            "rgba(0, 128, 128, 1)",   # ティール
            "rgba(255, 0, 255, 1)",   # マゼンタ
            "rgba(128, 0, 0, 1)"      # マルーン
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
                color = base_colors[base_idx].replace("1)", f"{opacity})")
                colors.append(color)
        
        return colors
    
    def _calculate_moving_average(self, values: List[float], window_size: int) -> List[Optional[float]]:
        """
        移動平均を計算
        
        Parameters
        ----------
        values : List[float]
            元データ
        window_size : int
            ウィンドウサイズ
            
        Returns
        -------
        List[Optional[float]]
            移動平均値
        """
        result = [None] * len(values)
        
        for i in range(len(values)):
            # ウィンドウの範囲を計算
            start = max(0, i - window_size + 1)
            # ウィンドウ内の値の平均を計算
            window_values = values[start:i+1]
            if window_values:
                result[i] = sum(window_values) / len(window_values)
        
        return result
    
    def _calculate_trendline(self, values: List[float]) -> List[float]:
        """
        トレンドライン（線形回帰）を計算
        
        Parameters
        ----------
        values : List[float]
            元データ
            
        Returns
        -------
        List[float]
            トレンドライン値
        """
        # X座標（インデックス）
        x = list(range(len(values)))
        
        # 平均値を計算
        mean_x = sum(x) / len(x)
        mean_y = sum(values) / len(values)
        
        # 傾きと切片を計算
        numerator = sum((x[i] - mean_x) * (values[i] - mean_y) for i in range(len(x)))
        denominator = sum((x[i] - mean_x) ** 2 for i in range(len(x)))
        
        slope = numerator / denominator if denominator != 0 else 0
        intercept = mean_y - slope * mean_x
        
        # トレンドライン値を計算
        trend_values = [slope * i + intercept for i in range(len(values))]
        
        return trend_values
    
    def _detect_outliers(self, values: List[float], threshold: float) -> List[int]:
        """
        異常値を検出
        
        Parameters
        ----------
        values : List[float]
            元データ
        threshold : float
            異常値判定のしきい値（標準偏差の倍数）
            
        Returns
        -------
        List[int]
            異常値のインデックスリスト
        """
        # 平均と標準偏差を計算
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        std_dev = math.sqrt(variance)
        
        # しきい値を超える値を異常値として検出
        outliers = []
        for i, value in enumerate(values):
            if abs(value - mean) > threshold * std_dev:
                outliers.append(i)
        
        return outliers
    
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
