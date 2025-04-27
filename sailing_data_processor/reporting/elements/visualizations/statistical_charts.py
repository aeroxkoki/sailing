# -*- coding: utf-8 -*-
"""
sailing_data_processor.reporting.elements.visualizations.statistical_charts

統計分析チャート要素を提供するモジュールです。
時系列分析、ボックスプロット、ヒートマップ、相関分析などの
統計的な可視化要素を実装します。
"""

from typing import Dict, List, Any, Optional, Union, Tuple
import json
import html
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
            return {"type": "line", "data": "labels": [], "datasets": []}}
        
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
                dataset = {}
                    "label": self.get_property(f"label_key}", key),
                    "data": values,
                    "fill": False,
                    "borderColor": colors[i],
                    "backgroundColor": colors[i].replace("1)", "0.1)"),
                    "borderWidth": 2,
                    "pointRadius": 3,
                    "pointBackgroundColor": colors[i],
                    "tension": 0.1
 {
                    "label": self.get_property(f"label_key}", key),
                    "data": values,
                    "fill": False,
                    "borderColor": colors[i],
                    "backgroundColor": colors[i].replace("1)", "0.1)"),
                    "borderWidth": 2,
                    "pointRadius": 3,
                    "pointBackgroundColor": colors[i],
                    "tension": 0.1}
                
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
                        "label": f"dataset['label']} (移動平均)",
                        "data": avg_values,
                        "fill": False,
                        "borderColor": dataset["borderColor"].replace("1)", "0.7)"),
                        "backgroundColor": "transparent",
                        "borderWidth": 1,
                        "borderDash": [5, 5],
                        "pointRadius": 0,
                        "tension": 0.4
 {
                        "label": f"dataset['label']} (移動平均)",
                        "data": avg_values,
                        "fill": False,
                        "borderColor": dataset["borderColor"].replace("1)", "0.7)"),
                        "backgroundColor": "transparent",
                        "borderWidth": 1,
                        "borderDash": [5, 5],
                        "pointRadius": 0,
                        "tension": 0.4}
                    
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
                        "label": f"dataset['label']} (トレンド)",
                        "data": trend_values,
                        "fill": False,
                        "borderColor": dataset["borderColor"].replace(")", ", 0.5)"),
                        "backgroundColor": "transparent",
                        "borderWidth": 2,
                        "borderDash": [10, 5],
                        "pointRadius": 0,
                        "tension": 0
 {
                        "label": f"dataset['label']} (トレンド)",
                        "data": trend_values,
                        "fill": False,
                        "borderColor": dataset["borderColor"].replace(")", ", 0.5)"),
                        "backgroundColor": "transparent",
                        "borderWidth": 2,
                        "borderDash": [10, 5],
                        "pointRadius": 0,
                        "tension": 0}
                    
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
                            "label": f"dataset['label']} (異常値)",
                            "data": outlier_data,
                            "fill": False,
                            "borderColor": "rgba(255, 0, 0, 1)",
                            "backgroundColor": "rgba(255, 0, 0, 0.8)",
                            "borderWidth": 0,
                            "pointRadius": 6,
                            "pointStyle": "circle",
                            "showLine": False
 {
                            "label": f"dataset['label']} (異常値)",
                            "data": outlier_data,
                            "fill": False,
                            "borderColor": "rgba(255, 0, 0, 1)",
                            "backgroundColor": "rgba(255, 0, 0, 0.8)",
                            "borderWidth": 0,
                            "pointRadius": 6,
                            "pointStyle": "circle",
                            "showLine": False}
                        
                        datasets.append(outlier_dataset)
        
        # チャートデータの作成
        chart_data = {
            "type": "line",
            "data": {
                "labels": labels,
                "datasets": datasets
            }
        }
 {
            "type": "line",
            "data": "labels": labels,
                "datasets": datasets}
        
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
                    }
                }
 {
            "scales": {
                "x": {
                    "type": "time",
                    "time": {
                        "unit": self.get_property("time_unit", "minute"),
                        "displayFormats": "minute": "HH:mm",
                            "hour": "HH:mm",
                            "day": "MM/DD",
                            "week": "MM/DD",
                            "month": "YYYY/MM",
                            "year": "YYYY"}
                    },
                    "title": {
                        "display": True,
                        "text": self.get_property("x_axis_title", "時間")
                    }
            }
            }
 "display": True,
                        "text": self.get_property("x_axis_title", "時間")}
                },
                "y": {
                    "beginAtZero": self.get_property("begin_at_zero", False),
                    "title": {
                        "display": True,
                        "text": self.get_property("y_axis_title", "値")
                    }
                }
 {
                    "beginAtZero": self.get_property("begin_at_zero", False),
                    "title": "display": True,
                        "text": self.get_property("y_axis_title", "値")}
            },
            "plugins": {
                "tooltip": {
                    "mode": "index",
                    "intersect": False
                }
            }
 {
                "tooltip": "mode": "index",
                    "intersect": False}
                },
                "zoom": {
                    "pan": {
                        "enabled": True,
                        "mode": "x"
                    }
                }
 {
                    "pan": "enabled": True,
                        "mode": "x"}
                    },
                    "zoom": {
                        "enabled": True,
                        "mode": "x",
                        "speed": 0.1
                    }
 "enabled": True,
                        "mode": "x",
                        "speed": 0.1}
            },
            "interaction": {
                "mode": "nearest",
                "axis": "x",
                "intersect": False
            }
 "mode": "nearest",
                "axis": "x",
                "intersect": False}
        
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


class BoxPlotElement(BaseChartElement):
    """
    ボックスプロット要素
    
    パフォーマンス指標の統計分布を表示するための要素です。
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
            kwargs['chart_type'] = "boxplot"
        
        super().__init__(model, **kwargs)
    
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
            "https://cdn.jsdelivr.net/npm/chartjs-chart-box-and-violin-plot@3.0.0/build/Chart.BoxPlot.min.js"
        ]
    
    def get_chart_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        ボックスプロットのデータを取得
        
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
            return {"type": "boxplot", "data": "labels": [], "datasets": []}}
        
        # グループキーと値キーを取得
        group_key = self.get_property("group_key", "group")
        value_key = self.get_property("value_key", "value")
        
        # データの形式によって処理を分岐
        labels = []
        datasets = []
        
        # 辞書形式の場合
        if isinstance(data, dict):
            if "labels" in data and "values" in data:
                # 各グループのラベルとデータが直接提供されている場合
                labels = data["labels"]
                
                # データセットを作成
                datasets.append({
                    "label": self.get_property("dataset_label", "データ分布"),
                    "data": data["values"],
                    "backgroundColor": "rgba(54, 162, 235, 0.5)",
                    "borderColor": "rgba(54, 162, 235, 1)",
                    "borderWidth": 1,
                    "outlierColor": "rgba(255, 99, 132, 0.8)",
                    "outlierRadius": 5,
                    "itemRadius": 0,
                    "itemStyle": "circle",
                    "itemBackgroundColor": "rgba(54, 162, 235, 0.2)",
                    "itemBorderColor": "rgba(54, 162, 235, 1)"
                })
        
        # リスト形式の場合
        elif isinstance(data, list):
            if all(isinstance(item, dict) for item in data):
                # 辞書のリストの場合、グループ別にデータを集計
                grouped_data = {}
                
                for item in data:
                    if group_key in item and value_key in item:
                        group = item[group_key]
                        value = item[value_key]
                        
                        if group not in grouped_data:
                            grouped_data[group] = []
                        
                        grouped_data[group].append(value)
                
                # ラベルとデータを抽出
                for group, values in grouped_data.items():
                    labels.append(group)
                    
                dataset_data = [grouped_data[group] for group in labels]
                
                # データセットを作成
                datasets.append({
                    "label": self.get_property("dataset_label", "データ分布"),
                    "data": dataset_data,
                    "backgroundColor": "rgba(54, 162, 235, 0.5)",
                    "borderColor": "rgba(54, 162, 235, 1)",
                    "borderWidth": 1,
                    "outlierColor": "rgba(255, 99, 132, 0.8)",
                    "outlierRadius": 5,
                    "itemRadius": 0,
                    "itemStyle": "circle",
                    "itemBackgroundColor": "rgba(54, 162, 235, 0.2)",
                    "itemBorderColor": "rgba(54, 162, 235, 1)"
                })
            
            elif all(isinstance(item, list) for item in data):
                # リストのリストの場合、各リストをボックスプロットとして扱う
                labels = self.get_property("labels", [f"グループ {i+1}" for i in range(len(data))])
                
                # データセットを作成
                datasets.append({
                    "label": self.get_property("dataset_label", "データ分布"),
                    "data": data,
                    "backgroundColor": "rgba(54, 162, 235, 0.5)",
                    "borderColor": "rgba(54, 162, 235, 1)",
                    "borderWidth": 1,
                    "outlierColor": "rgba(255, 99, 132, 0.8)",
                    "outlierRadius": 5,
                    "itemRadius": 0,
                    "itemStyle": "circle",
                    "itemBackgroundColor": "rgba(54, 162, 235, 0.2)",
                    "itemBorderColor": "rgba(54, 162, 235, 1)"
                })
        
        # 複数データセットの場合
        multi_datasets = self.get_property("multi_datasets", [])
        if multi_datasets:
            # 既存のデータセットをクリア
            datasets = []
            
            colors = self._get_colors(len(multi_datasets))
            
            for i, dataset_config in enumerate(multi_datasets):
                dataset_data = dataset_config.get("data", [])
                
                if not dataset_data and dataset_config.get("data_source") in context:
                    # データソースからデータを取得
                    source_data = context[dataset_config["data_source"]]
                    
                    # データ形式に応じて処理
                    if isinstance(source_data, list):
                        if all(isinstance(item, dict) for item in source_data):
                            # グループ別にデータを集計
                            grouped_data = {}
                            
                            group_key = dataset_config.get("group_key", group_key)
                            value_key = dataset_config.get("value_key", value_key)
                            
                            for item in source_data:
                                if group_key in item and value_key in item:
                                    group = item[group_key]
                                    value = item[value_key]
                                    
                                    if group not in grouped_data:
                                        grouped_data[group] = []
                                    
                                    grouped_data[group].append(value)
                            
                            # ラベルの更新
                            if not labels:
                                labels = list(grouped_data.keys())
                            
                            dataset_data = [grouped_data.get(group, []) for group in labels]
                
                # データセットを作成
                color = colors[i]
                
                datasets.append({
                    "label": dataset_config.get("label", f"データセット i+1}"),
                    "data": dataset_data,
                    "backgroundColor": color.replace("1)", "0.5)"),
                    "borderColor": color,
                    "borderWidth": 1,
                    "outlierColor": "rgba(255, 99, 132, 0.8)",
                    "outlierRadius": 5,
                    "itemRadius": 0,
                    "itemStyle": "circle",
                    "itemBackgroundColor": color.replace("1)", "0.2)"),
                    "itemBorderColor": color
                })
        
        # チャートデータの作成
        chart_data = {
            "type": "boxplot",
            "data": {
                "labels": labels,
                "datasets": datasets
            }
        }
 {
            "type": "boxplot",
            "data": "labels": labels,
                "datasets": datasets}
        
        return chart_data
    
    def get_chart_options(self) -> Dict[str, Any]:
        """
        ボックスプロットのオプションを取得
        
        Returns
        -------
        Dict[str, Any]
            チャートオプション
        """
        options = super().get_chart_options()
        
        # ボックスプロット特有のオプション
        boxplot_options = {
            "scales": {
                "y": {
                    "beginAtZero": self.get_property("begin_at_zero", False),
                    "title": {
                        "display": True,
                        "text": self.get_property("y_axis_title", "値")
                    }
                }
            }
 {
            "scales": {
                "y": {
                    "beginAtZero": self.get_property("begin_at_zero", False),
                    "title": "display": True,
                        "text": self.get_property("y_axis_title", "値")}
                },
                "x": {
                    "title": {
                        "display": True,
                        "text": self.get_property("x_axis_title", "グループ")
                    }
        }
                }
 {
                    "title": "display": True,
                        "text": self.get_property("x_axis_title", "グループ")}
            },
            "plugins": {
                "tooltip": {
                    "callbacks": {
                        "title": "function(context) return context[0].label; }",
                        "label": "function(context) { return ['最小値: ' + context.raw.min.toFixed(2), '第1四分位: ' + context.raw.q1.toFixed(2), '中央値: ' + context.raw.median.toFixed(2), '第3四分位: ' + context.raw.q3.toFixed(2), '最大値: ' + context.raw.max.toFixed(2)]; }"
            }
 {
                "tooltip": {
            }
        }
                    "callbacks": {
                        "title": "function(context) return context[0].label; }",
                        "label": "function(context) { return ['最小値: ' + context.raw.min.toFixed(2), '第1四分位: ' + context.raw.q1.toFixed(2), '中央値: ' + context.raw.median.toFixed(2), '第3四分位: ' + context.raw.q3.toFixed(2), '最大値: ' + context.raw.max.toFixed(2)]; }"}
        
        # オプションを結合
        self._merge_options(options, boxplot_options)
        
        return options
    
    def get_chart_initialization_code(self, config_var: str = "config") -> str:
        """
        ボックスプロット初期化用のJavaScriptコードを取得
        
        Parameters
        ----------
        config_var : str, optional
            設定変数名, by default "config"
            
        Returns
        -------
        str
            初期化コード
        """
        return f"""
            Chart.register(ChartBoxPlot);
            var ctx = document.getElementById('{self.chart_id}').getContext('2d');
            new Chart(ctx, {config_var});
        """
    
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


class HeatMapElement(BaseChartElement):
    """
    ヒートマップ要素
    
    XYグリッドでのデータ分布を表示するための要素です。
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
            kwargs['chart_type'] = "matrix"
        
        super().__init__(model, **kwargs)
    
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
            "https://cdn.jsdelivr.net/npm/chartjs-chart-matrix@1.1.1/dist/chartjs-chart-matrix.min.js"
        ]
    
    def get_chart_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        ヒートマップのデータを取得
        
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
            return {"type": "matrix", "data": "datasets": []}}
        
        # X軸とY軸のラベルを取得
        x_labels = self.get_property("x_labels", [])
        y_labels = self.get_property("y_labels", [])
        
        # カラースケールの取得
        color_scale = self.get_property("color_scale", [
            "rgba(0, 0, 255, 0.5)",  # 青 (低)
            "rgba(0, 255, 255, 0.5)",  # シアン
            "rgba(0, 255, 0, 0.5)",  # 緑
            "rgba(255, 255, 0, 0.5)",  # 黄
            "rgba(255, 0, 0, 0.5)"   # 赤 (高)
        ])
        
        # データの形式によって処理を分岐
        matrix_data = []
        
        if isinstance(data, list):
            if all(isinstance(item, dict) for item in data):
                # 辞書のリストの場合
                x_key = self.get_property("x_key", "x")
                y_key = self.get_property("y_key", "y")
                value_key = self.get_property("value_key", "value")
                
                for item in data:
                    if x_key in item and y_key in item and value_key in item:
                        matrix_data.append({
                            "x": item[x_key],
                            "y": item[y_key],
                            "v": item[value_key]
                        })
            
            elif all(isinstance(item, list) for item in data):
                # 2次元配列の場合
                for i, row in enumerate(data):
                    for j, value in enumerate(row):
                        y_label = y_labels[i] if i < len(y_labels) else str(i)
                        x_label = x_labels[j] if j < len(x_labels) else str(j)
                        
                        matrix_data.append({
                            "x": x_label,
                            "y": y_label,
                            "v": value
                        })
        
        elif isinstance(data, dict):
            # データが辞書の場合、特定の形式を想定
            if "data" in data and isinstance(data["data"], list):
                matrix_data = data["data"]
            elif "values" in data and isinstance(data["values"], list):
                if "x_labels" in data and "y_labels" in data:
                    x_labels = data["x_labels"]
                    y_labels = data["y_labels"]
                
                values = data["values"]
                for i, row in enumerate(values):
                    for j, value in enumerate(row):
                        y_label = y_labels[i] if i < len(y_labels) else str(i)
                        x_label = x_labels[j] if j < len(x_labels) else str(j)
                        
                        matrix_data.append({
                            "x": x_label,
                            "y": y_label,
                            "v": value
                        })
        
        # データがない場合は空のデータを返す
        if not matrix_data:
            return {"type": "matrix", "data": "datasets": []}}
        
        # 値の範囲を計算
        values = [item["v"] for item in matrix_data]
        min_value = min(values)
        max_value = max(values)
        
        # 値に基づいて色を決定する関数
        def get_color_for_value(value):
            if min_value == max_value:
                # 単一値の場合
                return color_scale[len(color_scale) // 2]
            
            # 値を0-1の範囲に正規化
            normalized = (value - min_value) / (max_value - min_value)
            
            # 正規化された値に基づいてカラースケールのインデックスを計算
            index = min(int(normalized * (len(color_scale) - 1)), len(color_scale) - 2)
            
            # 連続的な色を計算（インデックスとインデックス+1の間を補間）
            color1 = color_scale[index]
            color2 = color_scale[index + 1]
            t = normalized * (len(color_scale) - 1) - index  # 補間係数（0-1）
            
            # RGBAの値を抽出
            rgba1 = self._parse_rgba(color1)
            rgba2 = self._parse_rgba(color2)
            
            # 線形補間
            r = rgba1[0] + t * (rgba2[0] - rgba1[0])
            g = rgba1[1] + t * (rgba2[1] - rgba1[1])
            b = rgba1[2] + t * (rgba2[2] - rgba1[2])
            a = rgba1[3] + t * (rgba2[3] - rgba1[3])
            
            return f"rgba({int(r)}, {int(g)}, {int(b)}, {a})"
        
        # 各データポイントの背景色を設定
        for item in matrix_data:
            item["backgroundColor"] = get_color_for_value(item["v"])
        
        # チャートデータの作成
        chart_data = {
            "type": "matrix",
            "data": {
                "datasets": [{
                    "label": self.get_property("dataset_label", "データ分布"),
                    "data": matrix_data,
                    "width": self.get_property("cell_width", 30),
                    "height": self.get_property("cell_height", 30),
                    "borderWidth": 1,
                    "borderColor": "rgba(0, 0, 0, 0.1)"
            }
        }
 {
            "type": "matrix",
            "data": {
                "datasets": ["label": self.get_property("dataset_label", "データ分布"),
                    "data": matrix_data,
                    "width": self.get_property("cell_width", 30),
                    "height": self.get_property("cell_height", 30),
                    "borderWidth": 1,
                    "borderColor": "rgba(0, 0, 0, 0.1)"}
                }]
        
        return chart_data
    
    def get_chart_options(self) -> Dict[str, Any]:
        """
        ヒートマップのオプションを取得
        
        Returns
        -------
        Dict[str, Any]
            チャートオプション
        """
        options = super().get_chart_options()
        
        # X軸とY軸のラベルを取得
        x_labels = self.get_property("x_labels", [])
        y_labels = self.get_property("y_labels", [])
        
        # ヒートマップ特有のオプション
        heatmap_options = {
            "scales": {
                "x": {
                    "type": "category",
                    "labels": x_labels,
                    "title": {
                        "display": True,
                        "text": self.get_property("x_axis_title", "X軸")
                    }
                }
            }
 {
            "scales": {
                "x": {
                    "type": "category",
                    "labels": x_labels,
                    "title": "display": True,
                        "text": self.get_property("x_axis_title", "X軸")}
                },
                "y": {
                    "type": "category",
                    "labels": y_labels,
                    "title": {
                        "display": True,
                        "text": self.get_property("y_axis_title", "Y軸")
                    }
        }
                }
 {
                    "type": "category",
                    "labels": y_labels,
                    "title": "display": True,
                        "text": self.get_property("y_axis_title", "Y軸")}
            },
            "plugins": {
                "legend": {
                    "display": False
                }
            }
 {
                "legend": "display": False}
                },
                "tooltip": {
        }
                    "callbacks": {
                        "title": "function(context) return ''; }",
                        "label": "function(context) { return [context.raw.x + ', ' + context.raw.y, '値: ' + context.raw.v.toFixed(2)]; }"
 {
                    "callbacks": {
                        "title": "function(context) return ''; }",
                        "label": "function(context) { return [context.raw.x + ', ' + context.raw.y, '値: ' + context.raw.v.toFixed(2)]; }"}
        
        # オプションを結合
        self._merge_options(options, heatmap_options)
        
        return options
    
    def get_chart_initialization_code(self, config_var: str = "config") -> str:
        """
        ヒートマップ初期化用のJavaScriptコードを取得
        
        Parameters
        ----------
        config_var : str, optional
            設定変数名, by default "config"
            
        Returns
        -------
        str
            初期化コード
        """
        return f"""
            // Chart.jsのMatrixコントローラーを登録
            Chart.register(MatrixController);
            
            var ctx = document.getElementById('{self.chart_id}').getContext('2d');
            new Chart(ctx, {config_var});
        """
    
    def _parse_rgba(self, rgba_str: str) -> Tuple[float, float, float, float]:
        """
        rgba文字列からRGBA値を抽出
        
        Parameters
        ----------
        rgba_str : str
            rgba形式の色文字列 (例: "rgba(255, 0, 0, 0.5)")
            
        Returns
        -------
        Tuple[float, float, float, float]
            (r, g, b, a)のタプル
        """
        # rgba(255, 0, 0, 0.5) 形式からRGBA値を抽出
        parts = rgba_str.replace("rgba(", "").replace(")", "").split(",")
        r = float(parts[0].strip())
        g = float(parts[1].strip())
        b = float(parts[2].strip())
        a = float(parts[3].strip())
        
        return (r, g, b, a)
    
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


class CorrelationElement(BaseChartElement):
    """
    相関分析グラフ要素
    
    パラメータ間の相関関係を可視化するための要素です。
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
            kwargs['chart_type'] = "scatter"
        
        super().__init__(model, **kwargs)
    
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
            "https://cdn.jsdelivr.net/npm/chartjs-plugin-annotation@1.4.0/dist/chartjs-plugin-annotation.min.js",
            "https://cdn.jsdelivr.net/npm/regression@2.0.1/dist/regression.min.js"
        ]
    
    def get_chart_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        相関分析グラフのデータを取得
        
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
            return {"type": "scatter", "data": "datasets": []}}
        
        # X軸とY軸のパラメータ名を取得
        x_param = self.get_property("x_param", "")
        y_param = self.get_property("y_param", "")
        
        # データの形式によって処理を分岐
        x_values = []
        y_values = []
        
        if isinstance(data, list):
            if all(isinstance(item, dict) for item in data):
                # 辞書のリストの場合
                for item in data:
                    if x_param in item and y_param in item:
                        x_val = item[x_param]
                        y_val = item[y_param]
                        
                        if isinstance(x_val, (int, float)) and isinstance(y_val, (int, float)):
                            x_values.append(x_val)
                            y_values.append(y_val)
            
            elif all(isinstance(item, list) for item in data) and all(len(item) == 2 for item in data):
                # [x, y]形式のリストのリストの場合
                for item in data:
                    x_val, y_val = item
                    
                    if isinstance(x_val, (int, float)) and isinstance(y_val, (int, float)):
                        x_values.append(x_val)
                        y_values.append(y_val)
        
        elif isinstance(data, dict):
            # 辞書形式の場合
            if "x" in data and "y" in data and len(data["x"]) == len(data["y"]):
                x_values = data["x"]
                y_values = data["y"]
        
        # データがない場合は空のデータを返す
        if not x_values or not y_values:
            return {"type": "scatter", "data": "datasets": []}}
        
        # データポイントを作成
        points = []
        for i in range(len(x_values)):
            points.append({"x": x_values[i], "y": y_values[i]})
        
        # 回帰直線用のデータポイントを準備
        regression_data = [[x_values[i], y_values[i]] for i in range(len(x_values))]
        
        # 相関係数を計算
        correlation = self._calculate_correlation(x_values, y_values)
        
        # 回帰直線の計算
        show_trendline = self.get_property("show_trendline", True)
        regression_points = []
        
        if show_trendline:
            # 回帰直線の種類
            regression_type = self.get_property("regression_type", "linear")
            
            # 回帰直線用のポイントを計算（フロントエンドで計算するためのデータを準備）
            regression_points = {
                "type": regression_type,
                "data": regression_data
            }
 "type": regression_type,
                "data": regression_data}
        
        # データセットを作成
        datasets = [
            {
                "label": self.get_property("dataset_label", f"x_param} vs {y_param}"),
                "data": points,
                "backgroundColor": "rgba(54, 162, 235, 0.5)",
                "borderColor": "rgba(54, 162, 235, 1)",
                "borderWidth": 1,
                "pointRadius": 5,
                "pointHoverRadius": 7
            {
                "label": self.get_property("dataset_label", f"x_param} vs {y_param}"),
                "data": points,
                "backgroundColor": "rgba(54, 162, 235, 0.5)",
                "borderColor": "rgba(54, 162, 235, 1)",
                "borderWidth": 1,
                "pointRadius": 5,
                "pointHoverRadius": 7}
        ]
        
        # トレンドライン用のデータセットを追加
        if show_trendline:
            datasets.append({
                "label": self.get_property("trendline_label", "回帰直線"),
                "data": [],  # JavaScriptで計算するため、ここでは空配列
                "borderColor": "rgba(255, 99, 132, 1)",
                "borderWidth": 2,
                "pointRadius": 0,
                "fill": false,
                "showLine": true,
                "regression": regression_points
            })
        
        # チャートデータの作成
        chart_data = {
            "type": "scatter",
            "data": {
                "datasets": datasets
            }
        }
 {
            "type": "scatter",
            "data": "datasets": datasets}
            },
            "correlation": correlation
        
        return chart_data
    
    def get_chart_options(self) -> Dict[str, Any]:
        """
        相関分析グラフのオプションを取得
        
        Returns
        -------
        Dict[str, Any]
            チャートオプション
        """
        options = super().get_chart_options()
        
        # X軸とY軸のパラメータ名を取得
        x_param = self.get_property("x_param", "")
        y_param = self.get_property("y_param", "")
        
        # 相関分析グラフ特有のオプション
        correlation_options = {
            "scales": {
                "x": {
                    "title": {
                        "display": True,
                        "text": self.get_property("x_axis_title", x_param)
                    }
                }
            }
 {
            "scales": {
                "x": {
                    "title": "display": True,
                        "text": self.get_property("x_axis_title", x_param)}
                },
                "y": {
                    "title": {
                        "display": True,
                        "text": self.get_property("y_axis_title", y_param)
                    }
        }
                }
 {
                    "title": "display": True,
                        "text": self.get_property("y_axis_title", y_param)}
            },
            "plugins": {
                "tooltip": {
                    "callbacks": {
                        "label": "function(context) return context.raw.x.toFixed(2) + ', ' + context.raw.y.toFixed(2); }"
                }
            }
 {
                "tooltip": {
                    "callbacks": {
            }
                        "label": "function(context) return context.raw.x.toFixed(2) + ', ' + context.raw.y.toFixed(2); }"}
        }
            }
                }
        
        # オプションを結合
        self._merge_options(options, correlation_options)
        
        return options
    
    def get_chart_initialization_code(self, config_var: str = "config") -> str:
        """
        相関分析グラフ初期化用のJavaScriptコードを取得
        
        Parameters
        ----------
        config_var : str, optional
            設定変数名, by default "config"
            
        Returns
        -------
        str
            初期化コード
        """
        return f"""
            // 回帰計算を行う
            config.data.datasets.forEach(function(dataset, i) {{
                if (dataset.regression) {{
                    // 回帰結果を計算
                    var regressionType = dataset.regression.type || 'linear';
                    var result = regression[regressionType](dataset.regression.data);
                    
                    // 線形回帰の場合、r2（決定係数）を表示
                    var r2 = result.r2 ? result.r2.toFixed(3) : '';
                    var rSquared = r2 ? ' (R² = ' + r2 + ')' : '';
                    
                    // 相関係数（別途計算）
                    var correlationText = '';
                    if (config.correlation) {correlationText = ' (r = ' + config.correlation.toFixed(3) + ')';
                    }}
                    
                    // タイトルを更新
                    dataset.label = dataset.label + correlationText;
                    
                    // データ範囲を取得
                    var xValues = dataset.regression.data.map(function(point) {return point[0]; }});
                    var minX = Math.min.apply(null, xValues);
                    var maxX = Math.max.apply(null, xValues);
                    
                    // 回帰直線の点を生成
                    var step = (maxX - minX) / 100;
                    var regressionPoints = [];
                    
                    for (var x = minX; x <= maxX; x += step) {{
                        var y = result.predict(x)[1];
                        regressionPoints.push({x: x, y: y }});
                    }}
                    
                    // データセットを更新
                    dataset.data = regressionPoints;
                }}
            }});
            
            var ctx = document.getElementById('{self.chart_id}').getContext('2d');
            new Chart(ctx, {config_var});
        """
    
    def _calculate_correlation(self, x_values: List[float], y_values: List[float]) -> float:
        """
        ピアソン相関係数を計算
        
        Parameters
        ----------
        x_values : List[float]
            X値のリスト
        y_values : List[float]
            Y値のリスト
            
        Returns
        -------
        float
            相関係数
        """
        n = len(x_values)
        
        # 平均を計算
        mean_x = sum(x_values) / n
        mean_y = sum(y_values) / n
        
        # 共分散と標準偏差を計算
        sum_xy = sum((x_values[i] - mean_x) * (y_values[i] - mean_y) for i in range(n))
        sum_x2 = sum((x - mean_x) ** 2 for x in x_values)
        sum_y2 = sum((y - mean_y) ** 2 for y in y_values)
        
        # 相関係数を計算
        if sum_x2 == 0 or sum_y2 == 0:
            return 0
        
        correlation = sum_xy / (math.sqrt(sum_x2) * math.sqrt(sum_y2))
        
        return correlation
    
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
