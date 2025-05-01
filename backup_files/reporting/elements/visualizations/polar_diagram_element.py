# -*- coding: utf-8 -*-
"""
ポーラーダイアグラム要素モジュール。
このモジュールは、風向に対する船速の極座標表示を行うための要素を提供します。
"""

from typing import Dict, List, Any, Optional
import math

from sailing_data_processor.reporting.elements.visualizations.base_chart import BaseChartElement
from sailing_data_processor.reporting.templates.template_model import ElementType, ElementModel

class PolarDiagramElement(BaseChartElement):
    """
    ポーラーダイアグラム要素
    
    風向に対する船速の極座標表示を行うための要素です。
    風速ごとの速度曲線を表示し、各風向における最適な帆走性能を視覚化します。
    
    機能:
    - 複数風速での船速プロファイル表示
    - 実測値と理論値（ターゲット）の比較
    - 風速別のフィルタリングと色分け
    - VMG（Velocity Made Good）の最適ポイント表示
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
            kwargs['chart_type'] = "polar"
        
        # 拡張デフォルトプロパティ
        if model is None:
            # 表示設定のデフォルト値
            if 'show_target_curve' not in kwargs:
                kwargs['show_target_curve'] = True
                
            if 'show_actual_data' not in kwargs:
                kwargs['show_actual_data'] = True
                
            if 'show_vmg_points' not in kwargs:
                kwargs['show_vmg_points'] = True
                
            if 'angle_range' not in kwargs:
                kwargs['angle_range'] = 'full'  # full, upwind, downwind, custom
                
            if 'custom_angle_min' not in kwargs:
                kwargs['custom_angle_min'] = 0
                
            if 'custom_angle_max' not in kwargs:
                kwargs['custom_angle_max'] = 360
                
            if 'wind_speeds' not in kwargs:
                kwargs['wind_speeds'] = [5, 10, 15, 20]  # 表示する風速値
                
            if 'max_boat_speed' not in kwargs:
                kwargs['max_boat_speed'] = 'auto'  # 自動または数値
                
            if 'angle_step' not in kwargs:
                kwargs['angle_step'] = 5  # 角度ステップ（度数）
                
            if 'renderer' not in kwargs:
                kwargs['renderer'] = "plotly"  # plotly, chartjs
        
        super().__init__(model, **kwargs)
    
    def get_chart_libraries(self) -> List[str]:
        """
        チャートの描画に必要なライブラリのリストを取得
        
        Returns
        -------
        List[str]
            ライブラリのURLリスト
        """
        renderer = self.get_property("renderer", "plotly")
        
        if renderer == "plotly":
            return ["https://cdn.jsdelivr.net/npm/plotly.js@2.27.1/dist/plotly.min.js"]
        else:
            return [
                "https://cdn.jsdelivr.net/npm/chart.js@3.7.1/dist/chart.min.js",
                "https://cdn.jsdelivr.net/npm/chartjs-chart-matrix@1.1.1/dist/chartjs-chart-matrix.min.js",
                "https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2.0.0/dist/chartjs-plugin-datalabels.min.js"
            ]
            
    def get_chart_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        ポーラーダイアグラムのデータを取得
        
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
            return self._create_empty_polar_chart()
        
        # レンダラータイプに基づいてデータ形式を選択
        renderer = self.get_property("renderer", "plotly")
        
        if renderer == "plotly":
            return self._create_plotly_polar_data(data)
        else:
            return self._create_chartjs_polar_data(data)
            
    def _create_plotly_polar_data(self, data: Any) -> Dict[str, Any]:
        """
        Plotly用のポーラーデータを作成
        
        Parameters
        ----------
        data : Any
            元データ
            
        Returns
        -------
        Dict[str, Any]
            Plotly形式のポーラーチャートデータ
        """
        # 風速リストを取得
        wind_speeds = self.get_property("wind_speeds", [5, 10, 15, 20])
        
        # 角度範囲の設定
        angle_range = self.get_property("angle_range", "full")
        if angle_range == "upwind":
            angle_min, angle_max = 0, 90
        elif angle_range == "downwind":
            angle_min, angle_max = 90, 180
        elif angle_range == "custom":
            angle_min = self.get_property("custom_angle_min", 0)
            angle_max = self.get_property("custom_angle_max", 360)
        else:  # full
            angle_min, angle_max = 0, 360
        
        # 角度ステップを取得
        angle_step = self.get_property("angle_step", 5)
        
        # グラフのトレースデータを準備
        traces = []
        
        # 最大ボート速度を設定
        max_boat_speed = self.get_property("max_boat_speed", "auto")
        
        if max_boat_speed == "auto":
            max_boat_speed = 10  # デフォルト値
        
        # レイアウトを設定
        layout = {
            "title": self.title,
            "polar": {
                "radialaxis": {
                    "visible": True,
                    "range": [0, max_boat_speed],
                    "title": {
                        "text": "ボート速度（kt）"
                    }
                },
                "angularaxis": {
                    "visible": True,
                    "direction": "clockwise",
                    "dtick": 30,
                    "period": 360
                }
            },
            "showlegend": True,
            "legend": {
                "x": 1,
                "y": 0.9
            }
        }
        
        return {
            "data": traces,
            "layout": layout
        }
    
    def _create_chartjs_polar_data(self, data: Any) -> Dict[str, Any]:
        """
        Chart.js用のポーラーデータを作成
        
        Parameters
        ----------
        data : Any
            元データ
            
        Returns
        -------
        Dict[str, Any]
            Chart.js形式のポーラーチャートデータ
        """
        # 角度範囲の設定
        angle_range = self.get_property("angle_range", "full")
        if angle_range == "upwind":
            angle_min, angle_max = 0, 90
        elif angle_range == "downwind":
            angle_min, angle_max = 90, 180
        elif angle_range == "custom":
            angle_min = self.get_property("custom_angle_min", 0)
            angle_max = self.get_property("custom_angle_max", 360)
        else:  # full
            angle_min, angle_max = 0, 360
        
        # 角度ステップを取得
        angle_step = self.get_property("angle_step", 5)
        
        # 角度ラベルを生成
        angles = list(range(angle_min, angle_max + 1, angle_step))
        if angle_max - angle_min == 360:
            # 360度の場合は最後のラベルを省略（最初と重複するため）
            angles = angles[:-1]
        
        angle_labels = [f"{angle}°" for angle in angles]
        
        # データセットを準備
        datasets = []
        
        # 最大ボート速度を設定
        max_boat_speed = self.get_property("max_boat_speed", "auto")
        
        if max_boat_speed == "auto":
            max_boat_speed = 10  # デフォルト値
        
        return {
            "type": "radar",
            "data": {
                "labels": angle_labels,
                "datasets": datasets
            },
            "options": {
                "scales": {
                    "r": {
                        "beginAtZero": True,
                        "max": max_boat_speed,
                        "ticks": {
                            "stepSize": max_boat_speed / 5
                        }
                    }
                },
                "elements": {
                    "line": {
                        "tension": 0.1
                    }
                }
            }
        }
    
    def _get_color_for_wind_speed(self, wind_speed: float) -> str:
        """
        風速ごとのカラーコードを取得
        
        Parameters
        ----------
        wind_speed : float
            風速値
            
        Returns
        -------
        str
            RGBAカラーコード
        """
        # 風速別のカラースケールを定義
        color_scale = {
            5: "rgba(135, 206, 250, 1)",  # 薄い青（弱風）
            8: "rgba(30, 144, 255, 1)",   # 濃い青（やや弱風）
            10: "rgba(0, 128, 0, 1)",     # 緑（中風）
            12: "rgba(255, 165, 0, 1)",   # オレンジ（やや強風）
            15: "rgba(255, 69, 0, 1)",    # 赤オレンジ（強風）
            18: "rgba(220, 20, 60, 1)",   # 深紅（かなり強風）
            20: "rgba(128, 0, 0, 1)",     # 暗赤色（非常に強風）
            25: "rgba(85, 0, 0, 1)"       # 非常に暗い赤（猛烈な風）
        }
        
        # 風速に最も近いカラーを返す
        wind_speeds = sorted(color_scale.keys())
        
        if wind_speed <= wind_speeds[0]:
            return color_scale[wind_speeds[0]]
        
        if wind_speed >= wind_speeds[-1]:
            return color_scale[wind_speeds[-1]]
        
        # 風速の間を線形補間
        for i in range(len(wind_speeds) - 1):
            if wind_speeds[i] <= wind_speed <= wind_speeds[i + 1]:
                return color_scale[wind_speeds[i if wind_speed - wind_speeds[i] < wind_speeds[i + 1] - wind_speed else i + 1]]
        
        # デフォルトカラー
        return "rgba(70, 130, 180, 1)"  # スチールブルー
    
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
    
    def get_chart_options(self) -> Dict[str, Any]:
        """
        ポーラーダイアグラムのオプションを取得
        
        Returns
        -------
        Dict[str, Any]
            チャートオプション
        """
        options = super().get_chart_options()
        
        # レンダラタイプに基づいて異なるオプションを設定
        renderer = self.get_property("renderer", "plotly")
        
        if renderer == "plotly":
            # Plotlyのオプションは get_chart_data 内で設定されるため、空のオプションを返す
            return options
        else:
            # Chart.js のオプション
            polar_options = {
                "scales": {
                    "r": {
                        "beginAtZero": True,
                        "angleLines": {
                            "display": True,
                            "color": "rgba(0, 0, 0, 0.1)"
                        },
                        "grid": {
                            "color": "rgba(0, 0, 0, 0.1)"
                        },
                        "ticks": {
                            "backdropColor": "rgba(255, 255, 255, 0.75)",
                            "color": "#666"
                        },
                        "pointLabels": {
                            "font": {
                                "size": 10
                            }
                        }
                    }
                },
                "plugins": {
                    "legend": {
                        "position": "right",
                        "labels": {
                            "font": {
                                "size": 11
                            }
                        }
                    },
                    "tooltip": {
                        "callbacks": {
                            "label": "function(context) { return context.dataset.label + ': ' + context.raw.toFixed(1) + ' kt'; }"
                        }
                    }
                },
                "animation": {
                    "duration": 1000,
                    "easing": "easeOutQuart"
                }
            }
            
            # オプションを結合
            self._merge_options(options, polar_options)
            
            return options
    
    def _create_empty_polar_chart(self) -> Dict[str, Any]:
        """
        空のポーラーチャートデータを作成
        
        Returns
        -------
        Dict[str, Any]
            空のチャートデータ
        """
        renderer = self.get_property("renderer", "plotly")
        
        if renderer == "plotly":
            return {
                "data": [],
                "layout": {
                    "polar": {
                        "radialaxis": {
                            "visible": True,
                            "range": [0, 10]
                        },
                        "angularaxis": {
                            "visible": True,
                            "direction": "clockwise",
                            "dtick": 30
                        }
                    },
                    "showlegend": True
                }
            }
        else:
            labels = [f"{i}°" for i in range(0, 360, 30)]
            return {
                "type": "radar",
                "data": {
                    "labels": labels,
                    "datasets": []
                }
            }
