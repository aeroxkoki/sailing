# -*- coding: utf-8 -*-
"""
ボックスプロット要素モジュール。
このモジュールは、パフォーマンス指標の統計分布を表示するための要素を提供します。
"""

from typing import Dict, List, Any, Optional
import math

from sailing_data_processor.reporting.elements.visualizations.base_chart import BaseChartElement
from sailing_data_processor.reporting.templates.template_model import ElementType, ElementModel


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
            return {"type": "boxplot", "data": {"labels": [], "datasets": []}}
        
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
                    "label": dataset_config.get("label", f"データセット {i+1}"),
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
                },
                "x": {
                    "title": {
                        "display": True,
                        "text": self.get_property("x_axis_title", "グループ")
                    }
                }
            },
            "plugins": {
                "tooltip": {
                    "callbacks": {
                        "title": "function(context) { return context[0].label; }",
                        "label": "function(context) { return ['最小値: ' + context.raw.min.toFixed(2), '第1四分位: ' + context.raw.q1.toFixed(2), '中央値: ' + context.raw.median.toFixed(2), '第3四分位: ' + context.raw.q3.toFixed(2), '最大値: ' + context.raw.max.toFixed(2)]; }"
                    }
                }
            }
        }
        
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
