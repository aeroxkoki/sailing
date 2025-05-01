# -*- coding: utf-8 -*-
"""
Base distribution chart element module.
This module provides the base class for distribution chart elements.
"""

from typing import Dict, List, Any, Optional, Union
import json
import html

from sailing_data_processor.reporting.elements.visualizations.base_chart import BaseChartElement
from sailing_data_processor.reporting.templates.template_model import ElementType, ElementModel
from sailing_data_processor.reporting.elements.visualizations.distribution.histogram import get_histogram_data
from sailing_data_processor.reporting.elements.visualizations.distribution.violin import get_violin_data
from sailing_data_processor.reporting.elements.visualizations.distribution.kde import get_kde_data


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
            return get_histogram_data(self, data, value_key, category_key)
        elif chart_type == "violin":
            return get_violin_data(self, data, value_key, category_key)
        elif chart_type == "kde":
            return get_kde_data(self, data, value_key, category_key)
        else:
            # デフォルトはヒストグラム
            return get_histogram_data(self, data, value_key, category_key)
    
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
                    }
                },
                "x": {
                    "title": {
                        "display": True,
                        "text": self.get_property("x_axis_title", "値")
                    }
                }
            },
            "plugins": {
                "tooltip": {
                    "mode": "index"
                }
            }
        }
        
        # チャートタイプに応じたオプション
        if chart_type == "histogram":
            # ヒストグラム特有のオプション
            histogram_options = {
                "plugins": {
                    "legend": {
                        "display": self.get_property("category_key") is not None
                    }
                },
                "scales": {
                    "x": {
                        "offset": True,
                        "grid": {
                            "offset": True
                        }
                    }
                }
            }
            
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
                        }
                    }
                }
            }
            
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
                        }
                    }
                }
            }
            
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
