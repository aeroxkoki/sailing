# -*- coding: utf-8 -*-
"""
Module for data connector between map layers and data sources.
This module provides functions for binding and data transformation between layers and data sources.
"""

from typing import Dict, List, Any, Optional, Union, Tuple
import json
import html
import math

from sailing_data_processor.reporting.elements.visualizations.base_chart import BaseChartElement
from sailing_data_processor.reporting.templates.template_model import ElementType, ElementModel


class WindRoseElement(BaseChartElement):
    """
    風配図（Wind Rose）要素
    
    風向別の風速と頻度を表示するための要素です。
    方位別の風向風速の分布を極座標で表現します。
    
    拡張機能:
    - カラースケールのカスタマイズ
    - 方位別の風速と頻度の詳細表示
    - 時間範囲フィルタリング機能
    - データ表示形式のカスタマイズ
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
            kwargs['chart_type'] = "windrose"
        
        # 拡張デフォルトプロパティ
        if model is None:
            # カスタムカラースケールのデフォルト設定
            if 'color_scale_type' not in kwargs:
                kwargs['color_scale_type'] = 'sequential'  # sequential, diverging, categorical
            
            # 詳細表示のデフォルト設定
            if 'show_details' not in kwargs:
                kwargs['show_details'] = True
                
            # 表示モードのデフォルト設定
            if 'display_mode' not in kwargs:
                kwargs['display_mode'] = 'frequency'  # frequency, speed, both
                
            # 時間範囲フィルタリング設定
            if 'time_filter_enabled' not in kwargs:
                kwargs['time_filter_enabled'] = False
                
            # カスタマイズ可能な角度分割数
            if 'angle_divisions' not in kwargs:
                kwargs['angle_divisions'] = 16
                
            # 方位表示形式
            if 'direction_format' not in kwargs:
                kwargs['direction_format'] = 'cardinal'  # cardinal, degrees, both
        
        super().__init__(model, **kwargs)
    
    def get_chart_libraries(self) -> List[str]:
        """
        チャートの描画に必要なライブラリのリストを取得
        
        Returns
        -------
        List[str]
            ライブラリのURLリスト
        """
        libraries = [
            "https://cdn.jsdelivr.net/npm/chart.js@3.7.1/dist/chart.min.js",
            "https://cdn.jsdelivr.net/npm/chartjs-chart-matrix@1.1.1/dist/chartjs-chart-matrix.min.js",
            "https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2.0.0/dist/chartjs-plugin-datalabels.min.js",
            "https://cdn.jsdelivr.net/npm/moment@2.29.1/moment.min.js"
        ]
        
        # 詳細表示が有効な場合、追加のライブラリを読み込む
        if self.get_property("show_details", True):
            libraries.append("https://cdn.jsdelivr.net/npm/d3@7.0.0/dist/d3.min.js")
            
        # 拡張機能のサポート
        if self.get_property("enable_advanced_features", False):
            libraries.append("https://cdn.jsdelivr.net/npm/chart.js-windrose-plugin@1.0.0/dist/chartjs-windrose.min.js")
            
        return libraries
    
    def get_chart_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        風配図のデータを取得
        
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
            return {"type": "polarArea", "data": "labels": [], "datasets": []}}
        
        # 角度分割数の取得（デフォルト：16方位）
        angle_divisions = self.get_property("angle_divisions", 16)
        
        # カラースケールの取得
        color_scale = self.get_property("color_scale", [
            "rgba(53, 162, 235, 0.2)",
            "rgba(53, 162, 235, 0.4)",
            "rgba(53, 162, 235, 0.6)",
            "rgba(53, 162, 235, 0.8)",
            "rgba(53, 162, 235, 1.0)"
        ])
        
        # 複数カラースケールプリセットのサポート
        color_scale_preset = self.get_property("color_scale_preset", "blue")
        if color_scale_preset == "blue":
            # 青のグラデーション（デフォルト）
            color_scale = [
                "rgba(53, 162, 235, 0.2)",
                "rgba(53, 162, 235, 0.4)",
                "rgba(53, 162, 235, 0.6)",
                "rgba(53, 162, 235, 0.8)",
                "rgba(53, 162, 235, 1.0)"
            ]
        elif color_scale_preset == "rainbow":
            # 虹色のグラデーション
            color_scale = [
                "rgba(75, 192, 192, 0.7)",  # 緑/シアン
                "rgba(54, 162, 235, 0.7)",  # 青
                "rgba(153, 102, 255, 0.7)", # 紫
                "rgba(255, 99, 132, 0.7)",  # 赤/ピンク
                "rgba(255, 159, 64, 0.7)"   # オレンジ
            ]
        elif color_scale_preset == "thermal":
            # 熱分布のグラデーション
            color_scale = [
                "rgba(0, 0, 255, 0.7)",     # 青（弱）
                "rgba(0, 255, 255, 0.7)",   # シアン
                "rgba(0, 255, 0, 0.7)",     # 緑
                "rgba(255, 255, 0, 0.7)",   # 黄
                "rgba(255, 0, 0, 0.7)"      # 赤（強）
            ]
        elif color_scale_preset == "monochrome":
            # モノクロのグラデーション
            color_scale = [
                "rgba(220, 220, 220, 0.7)",
                "rgba(180, 180, 180, 0.7)",
                "rgba(140, 140, 140, 0.7)",
                "rgba(100, 100, 100, 0.7)",
                "rgba(60, 60, 60, 0.7)"
            ]
        
        # 方位表示形式の取得
        direction_format = self.get_property("direction_format", "cardinal")  # cardinal, degrees, both
        
        # 風配図の方位名を生成
        direction_labels = []
        for i in range(angle_divisions):
            angle = i * (360.0 / angle_divisions)
            
            # 基本的な方位名（N, E, S, W など）
            cardinal_name = ""
            if angle == 0:
                cardinal_name = "N"
            elif angle == 90:
                cardinal_name = "E"
            elif angle == 180:
                cardinal_name = "S"
            elif angle == 270:
                cardinal_name = "W"
            elif angle == 45:
                cardinal_name = "NE"
            elif angle == 135:
                cardinal_name = "SE"
            elif angle == 225:
                cardinal_name = "SW"
            elif angle == 315:
                cardinal_name = "NW"
            elif angle == 22.5:
                cardinal_name = "NNE"
            elif angle == 67.5:
                cardinal_name = "ENE"
            elif angle == 112.5:
                cardinal_name = "ESE"
            elif angle == 157.5:
                cardinal_name = "SSE"
            elif angle == 202.5:
                cardinal_name = "SSW"
            elif angle == 247.5:
                cardinal_name = "WSW"
            elif angle == 292.5:
                cardinal_name = "WNW"
            elif angle == 337.5:
                cardinal_name = "NNW"
            
            # 表示形式に基づいたラベルを生成
            if direction_format == "cardinal" and cardinal_name:
                direction_labels.append(cardinal_name)
            elif direction_format == "degrees" or not cardinal_name:
                direction_labels.append(f"{int(angle)}°")
            elif direction_format == "both" and cardinal_name:
                direction_labels.append(f"{cardinal_name} ({int(angle)}°)")
            else:
                direction_labels.append(f"{int(angle)}°")
        
        # 時間範囲フィルタリング
        time_filter_enabled = self.get_property("time_filter_enabled", False)
        time_start = self.get_property("time_start", None)
        time_end = self.get_property("time_end", None)
        time_key = self.get_property("time_key", "timestamp")
        
        # データの形式に合わせて処理
        # 想定データ形式：方位別の頻度または風速
        datasets = []
        
        if isinstance(data, dict) and "directions" in data and "values" in data:
            # 方位と値がキーとして提供されている場合
            directions = data["directions"]
            values = data["values"]
            
            if len(directions) == len(values):
                # 時間フィルタリングは辞書形式では対応困難なため実装せず
                datasets.append({
                    "label": data.get("label", "風配図"),
                    "data": values,
                    "backgroundColor": self._get_colors_for_values(values, color_scale),
                    "borderWidth": 1
                })
        elif isinstance(data, list):
            # データがリストの場合
            if all(isinstance(item, dict) for item in data):
                # 辞書のリストの場合、各辞書に方位と値のキーがあるか確認
                direction_key = self.get_property("direction_key", "direction")
                value_key = self.get_property("value_key", "value")
                
                # フィルタリング適用前のデータ
                filtered_data = data
                
                # 時間範囲フィルタリング
                if time_filter_enabled and (time_start or time_end):
                    filtered_data = []
                    
                    for item in data:
                        if time_key in item:
                            time_val = item[time_key]
                            time_obj = None
                            
                            # 時間値の変換
                            if isinstance(time_val, str):
                                try:
                                    # ISO形式の文字列からDateオブジェクトへ変換
                                    import datetime
                                    time_obj = datetime.datetime.fromisoformat(time_val.replace('Z', '+00:00'))
                                except (ValueError, AttributeError):
                                    # 変換に失敗した場合は別の形式を試みる
                                    try:
                                        import dateutil.parser
                                        time_obj = dateutil.parser.parse(time_val)
                                    except:
                                        continue
                            elif isinstance(time_val, (int, float)):
                                # Unixタイムスタンプから変換
                                import datetime
                                time_obj = datetime.datetime.fromtimestamp(time_val)
                            
                            # 時間オブジェクトが取得できなかった場合はスキップ
                            if not time_obj:
                                continue
                            
                            # 時間範囲チェック
                            time_start_obj = None
                            time_end_obj = None
                            
                            if time_start:
                                try:
                                    time_start_obj = datetime.datetime.fromisoformat(time_start.replace('Z', '+00:00'))
                                except (ValueError, AttributeError):
                                    try:
                                        import dateutil.parser
                                        time_start_obj = dateutil.parser.parse(time_start)
                                    except:
                                        pass
                            
                            if time_end:
                                try:
                                    time_end_obj = datetime.datetime.fromisoformat(time_end.replace('Z', '+00:00'))
                                except (ValueError, AttributeError):
                                    try:
                                        import dateutil.parser
                                        time_end_obj = dateutil.parser.parse(time_end)
                                    except:
                                        pass
                            
                            # 範囲チェック
                            in_range = True
                            if time_start_obj and time_obj < time_start_obj:
                                in_range = False
                            if time_end_obj and time_obj > time_end_obj:
                                in_range = False
                            
                            # 範囲内のデータのみ追加
                            if in_range:
                                filtered_data.append(item)
                
                # 方位別に値を集計
                values_by_direction = [0] * angle_divisions
                
                for item in filtered_data:
                    if direction_key in item and value_key in item:
                        direction = item[direction_key]
                        value = item[value_key]
                        
                        # 方位を角度に変換して対応するインデックスを計算
                        if isinstance(direction, (int, float)):
                            angle = direction
                        elif isinstance(direction, str):
                            # 方位名から角度に変換（N=0, E=90, S=180, W=270など）
                            direction = direction.upper()
                            if direction == "N":
                                angle = 0
                            elif direction == "NE":
                                angle = 45
                            elif direction == "E":
                                angle = 90
                            elif direction == "SE":
                                angle = 135
                            elif direction == "S":
                                angle = 180
                            elif direction == "SW":
                                angle = 225
                            elif direction == "W":
                                angle = 270
                            elif direction == "NW":
                                angle = 315
                            else:
                                # 角度表記の文字列の場合（例：「45°」）
                                try:
                                    angle = float(direction.replace("°", ""))
                                except ValueError:
                                    continue
                        else:
                            continue
                        
                        # 角度を正規化（0-360の範囲に収める）
                        angle = angle % 360
                        
                        # 対応するインデックスを計算
                        index = int(round(angle / (360.0 / angle_divisions))) % angle_divisions
                        
                        # 値を加算
                        values_by_direction[index] += value
                
                # データセットラベルを作成
                dataset_label = self.get_property("label", "風配図")
                if time_filter_enabled and (time_start or time_end):
                    # フィルター情報をラベルに追加
                    filter_info = "（期間フィルター"
                    if time_start:
                        from_str = time_start.split("T")[0] if "T" in time_start else time_start
                        filter_info += f" 開始: {from_str}"
                        }
                    if time_end:
                        to_str = time_end.split("T")[0] if "T" in time_end else time_end
                        filter_info += f" 終了: {to_str}"
                        }
                    filter_info += "）"
                    dataset_label += filter_info
                
                # データセットを作成
                datasets.append({
                    "label": dataset_label,
                    "data": values_by_direction,
                    "backgroundColor": self._get_colors_for_values(values_by_direction, color_scale),
                    "borderWidth": 1
                })
        
        # 風配図データの作成
        chart_data = {}
            "type": "polarArea",
            "data": {
                "labels": direction_labels,
                "datasets": datasets
            }
 {
            "type": "polarArea",
            "data": "labels": direction_labels,
                "datasets": datasets}
            
        
        return chart_data
    
    def get_chart_options(self) -> Dict[str, Any]:
        """
        風配図のオプションを取得
        
        Returns
        -------
        Dict[str, Any]
            チャートオプション
        """
        options = super().get_chart_options()
        
        # 風配図特有のオプション
        wind_rose_options = {
            "scale": {
                "ticks": {
                    "beginAtZero": True,
                    "precision": self.get_property("tick_precision", 0),
                    "maxTicksLimit": self.get_property("max_ticks", 5)
                }
            }
        }
 {
            "scale": {
                "ticks": "beginAtZero": True,
                    "precision": self.get_property("tick_precision", 0),
                    "maxTicksLimit": self.get_property("max_ticks", 5)}
                
            },
            "plugins": {
                "legend": {
                    "position": self.get_property("legend_position", "top")
                }
            }
 {
                "legend": "position": self.get_property("legend_position", "top")}
                },
                "tooltip": {
                    "callbacks": {
                        "label": "function(context) return context.label + ': ' + context.raw.toFixed(1); }"
                }
 {
                    "callbacks": {
                        "label": "function(context) return context.label + ': ' + context.raw.toFixed(1); }"}
                    
                },
                "datalabels": {
                    "display": self.get_property("show_labels", False),
                    "color": "white",
                    "font": {
                        "weight": "bold"
                    }
                }
 {
                    "display": self.get_property("show_labels", False),
                    "color": "white",
                    "font": "weight": "bold"}
                    },
                    "formatter": "function(value) { return value.toFixed(1); }"
                
            },
            "animation": {
                "duration": self.get_property("animation_duration", 1000),
                "easing": "easeOutQuart"
            }
 "duration": self.get_property("animation_duration", 1000),
                "easing": "easeOutQuart"}
            
        
        # 詳細表示が有効な場合の追加設定
        if self.get_property("show_details", True):
            wind_rose_options["plugins"]["tooltip"]["callbacks"] = {
                "title": "function(context) return context[0].label; }",
                "label": "function(context) { var dataIndex = context.dataIndex; var value = context.raw; " +
 {
                "title": "function(context) return context[0].label; }",
                "label": "function(context) { var dataIndex = context.dataIndex; var value = context.raw; " +}
                         "return [" +
                         "'値: ' + value.toFixed(1)," +
                         "'全体に対する割合: ' + (value / context.chart.data.datasets[0].data.reduce((a,b) => a + b, 0) * 100).toFixed(1) + '%'" +
                         "]; }"
            
        # 拡張カラースケールの設定
        color_scale_type = self.get_property("color_scale_type", "sequential")
        if color_scale_type == "diverging":
            wind_rose_options["plugins"]["colorschemes"] = {
                "scheme": "brewer.diverging.Spectral11",
                "reverse": False
            }
 "scheme": "brewer.diverging.Spectral11",
                "reverse": False}
            wind_rose_options["plugins"]["colorschemes"] = {
                "scheme": "brewer.diverging.Spectral11",
                "reverse": False}
 {
                "scheme": "brewer.diverging.Spectral11",
                "reverse": False}}
            wind_rose_options["plugins"]["colorschemes"] = {
                "scheme": "brewer.diverging.Spectral11",
                "reverse": False}
 {
                "scheme": "brewer.diverging.Spectral11",
                "reverse": False}}
            
        elif color_scale_type == "categorical":
            wind_rose_options["plugins"]["colorschemes"] = {
                "scheme": "brewer.qualitative.Set3",
                "override": True
            }
 "scheme": "brewer.qualitative.Set3",
                "override": True}
            wind_rose_options["plugins"]["colorschemes"] = {
                "scheme": "brewer.qualitative.Set3",
                "override": True}
 {
                "scheme": "brewer.qualitative.Set3",
                "override": True}}
            wind_rose_options["plugins"]["colorschemes"] = {
                "scheme": "brewer.qualitative.Set3",
                "override": True}
 {
                "scheme": "brewer.qualitative.Set3",
                "override": True}}
            
        # 角度ラインのカスタマイズ
        angle_lines_enabled = self.get_property("angle_lines_enabled", True)
        angle_lines_color = self.get_property("angle_lines_color", "rgba(0, 0, 0, 0.1)")
        wind_rose_options["scale"]["angleLines"] = {
            "display": angle_lines_enabled,
            "color": angle_lines_color
        }
 "display": angle_lines_enabled,
            "color": angle_lines_color}
        wind_rose_options["scale"]["angleLines"] = {
            "display": angle_lines_enabled,
            "color": angle_lines_color}
 {
            "display": angle_lines_enabled,
            "color": angle_lines_color}}
        wind_rose_options["scale"]["angleLines"] = {
            "display": angle_lines_enabled,
            "color": angle_lines_color}
 {
            "display": angle_lines_enabled,
            "color": angle_lines_color}}
        
        # 時間フィルタリングの表示
        time_filter_enabled = self.get_property("time_filter_enabled", False)
        time_start = self.get_property("time_start", None)
        time_end = self.get_property("time_end", None)
        
        if time_filter_enabled and (time_start or time_end):
            # フィルター情報をタイトルに追加
            title_text = options.get("plugins", {}).get("title", {}).get("text", self.title)
            
            # タイトルが存在しなければ作成、存在すれば更新
            if "plugins" not in options:
                options["plugins"] = {}
            if "title" not in options["plugins"]:
                options["plugins"]["title"] = {
                    "display": True,
                    "text": title_text,
                    "font": {
                        "size": 16
                    }
                }
 {
                    "display": True,
                    "text": title_text,
                    "font": "size": 16}
                options["plugins"]["title"] = {
                    "display": True,
                    "text": title_text,
                    "font": "size": 16}
 {
                    "display": True,
                    "text": title_text,
                    "font": "size": 16}}
                options["plugins"]["title"] = {
                    "display": True,
                    "text": title_text,
                    "font": "size": 16}
 {
                    "display": True,
                    "text": title_text,
                    "font": "size": 16}}
                    
                
            # サブタイトルの追加
            filter_text = "期間フィルター適用:"
            if time_start:
                from_str = time_start.split("T")[0] if "T" in time_start else time_start
                filter_text += f" 開始: {from_str}"
                }
            if time_end:
                to_str = time_end.split("T")[0] if "T" in time_end else time_end
                filter_text += f" 終了: {to_str}"
                }
            
            options["plugins"]["title"]["subtitle"] = {
                "display": True,
                "text": filter_text,
                "font": {
                    "size": 12,
                    "style": "italic"
                }
            }
 {
                "display": True,
                "text": filter_text,
                "font": "size": 12,
                    "style": "italic"}
                },
                "color": "rgba(100, 100, 100, 0.8)"
            
        
        # オプションを結合
        self._merge_options(options, wind_rose_options)
        
        return options
    
    def get_chart_initialization_code(self, config_var: str = "config") -> str:
        """
        風配図初期化用のJavaScriptコードを取得
        
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
            // チャートJSのPolarAreaチャートを拡張して風配図を作成
            var ctx = document.getElementById('{self.chart_id}').getContext('2d');
            new Chart(ctx, {config_var});
        """
    
    def _get_colors_for_values(self, values: List[float], color_scale: List[str]) -> List[str]:
        """
        値のリストに対応する色を取得
        
        Parameters
        ----------
        values : List[float]
            値のリスト
        color_scale : List[str]
            カラースケール
            
        Returns
        -------
        List[str]
            値に対応する色のリスト
        """
        if not values or max(values) == 0:
            return [color_scale[0]] * len(values)
        
        max_value = max(values)
        colors = []
        
        for value in values:
            # 値に応じてカラースケールから色を選択
            if max_value == 0:
                index = 0
            else:
                # 値を0-1の範囲に正規化してカラースケールのインデックスを計算
                normalized = value / max_value
                index = min(int(normalized * len(color_scale)), len(color_scale) - 1)
            
            colors.append(color_scale[index])
        
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
                        }
                    }
                }
 {
                "data": [],
                "layout": {
                    "polar": {
                        "radialaxis": "visible": True,
                            "range": [0, 10]}
                        },
                        "angularaxis": {
                            "visible": True,
                            "direction": "clockwise",
                            "dtick": 30
                        }
 "visible": True,
                            "direction": "clockwise",
                            "dtick": 30}
                        
                    },
                    "showlegend": True
                
            
        else:
            return {
                "type": "radar",
                "data": {
                    "labels": [f"i}°" for i in range(0, 360, 30)],
                    "datasets": []
 {
                "type": "radar",
                "data": {
                    "labels": [f"i}°" for i in range(0, 360, 30)],
                    "datasets": []}
            return {
                "type": "radar",
                "data": {
                    "labels": [f"i}°" for i in range(0, 360, 30)],
                    "datasets": []}
 {
                "type": "radar",
                "data": {
                    "labels": [f"i}°" for i in range(0, 360, 30)],
                    "datasets": []}}
                
            
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
        
        # データの形式に応じて処理
        if isinstance(data, dict):
            # ターゲット（理論値）曲線
            if self.get_property("show_target_curve", True) and "target" in data:
                target_data = data["target"]
                
                # 風速別のターゲット曲線
                for wind_speed in wind_speeds:
                    speed_key = f"wind_{wind_speed}"
                    if speed_key in target_data:
                        # この風速でのターゲット曲線データ
                        angles = []
                        speeds = []
                        
                        for angle, speed in target_data[speed_key].items():
                            try:
                                angle_val = float(angle.replace("°", ""))
                                if angle_min <= angle_val <= angle_max:
                                    angles.append(angle_val)
                                    speeds.append(float(speed))
                            except (ValueError, TypeError):
                                continue
                        
                        if angles and speeds:
                            # 閉じた曲線のために最初のポイントを末尾に追加
                            if angle_max - angle_min == 360:
                                angles.append(angles[0])
                                speeds.append(speeds[0])
                            
                            traces.append({
                                "type": "scatterpolar",
                                "r": speeds,
                                "theta": angles,
                                "name": f"ターゲット（wind_speed}kt）",
                                "mode": "lines",
                                "line": {
                                    "color": self._get_color_for_wind_speed(wind_speed),
                                    "width": 2,
                                    "dash": "solid"
                                }
 "color": self._get_color_for_wind_speed(wind_speed),
                                    "width": 2,
                                    "dash": "solid"}
                                
                            })
            
            # 実測値
            if self.get_property("show_actual_data", True) and "actual" in data:
                actual_data = data["actual"]
                
                # 風速別の実測データ
                for wind_speed in wind_speeds:
                    speed_key = f"wind_{wind_speed}"
                    if speed_key in actual_data:
                        # この風速での実測データ
                        angles = []
                        speeds = []
                        
                        for angle, speed in actual_data[speed_key].items():
                            try:
                                angle_val = float(angle.replace("°", ""))
                                if angle_min <= angle_val <= angle_max:
                                    angles.append(angle_val)
                                    speeds.append(float(speed))
                            except (ValueError, TypeError):
                                continue
                        
                        if angles and speeds:
                            traces.append({
                                "type": "scatterpolar",
                                "r": speeds,
                                "theta": angles,
                                "name": f"実測（wind_speed}kt）",
                                "mode": "markers",
                                "marker": {
                                    "size": 8,
                                    "color": self._get_color_for_wind_speed(wind_speed),
                                    "symbol": "circle"
                                }
 "size": 8,
                                    "color": self._get_color_for_wind_speed(wind_speed),
                                    "symbol": "circle"}
                                
                            })
            
            # VMGポイント
            if self.get_property("show_vmg_points", True) and "vmg" in data:
                vmg_data = data["vmg"]
                
                for wind_speed in wind_speeds:
                    speed_key = f"wind_{wind_speed}"
                    if speed_key in vmg_data:
                        # この風速でのVMGデータ
                        upwind_vmg = vmg_data[speed_key].get("upwind", {})
                        downwind_vmg = vmg_data[speed_key].get("downwind", {})
                        
                        upwind_angle = upwind_vmg.get("angle")
                        upwind_speed = upwind_vmg.get("speed")
                        downwind_angle = downwind_vmg.get("angle")
                        downwind_speed = downwind_vmg.get("speed")
                        
                        # 有効なデータが存在する場合のみ表示
                        if upwind_angle is not None and upwind_speed is not None:
                            traces.append({
                                "type": "scatterpolar",
                                "r": [upwind_speed],
                                "theta": [upwind_angle],
                                "name": f"上り最適VMG（wind_speed}kt）",
                                "mode": "markers",
                                "marker": {
                                    "size": 12,
                                    "color": self._get_color_for_wind_speed(wind_speed),
                                    "symbol": "star",
                                    "line": {
                                        "width": 2,
                                        "color": "white"
                                    }
                                }
 {
                                    "size": 12,
                                    "color": self._get_color_for_wind_speed(wind_speed),
                                    "symbol": "star",
                                    "line": "width": 2,
                                        "color": "white"}
                                    
                                
                            })
                        
                        if downwind_angle is not None and downwind_speed is not None:
                            traces.append({
                                "type": "scatterpolar",
                                "r": [downwind_speed],
                                "theta": [downwind_angle],
                                "name": f"下り最適VMG（wind_speed}kt）",
                                "mode": "markers",
                                "marker": {
                                    "size": 12,
                                    "color": self._get_color_for_wind_speed(wind_speed),
                                    "symbol": "diamond",
                                    "line": {
                                        "width": 2,
                                        "color": "white"
                                    }
                                }
 {
                                    "size": 12,
                                    "color": self._get_color_for_wind_speed(wind_speed),
                                    "symbol": "diamond",
                                    "line": "width": 2,
                                        "color": "white"}
                                    
                                
                            })
        
        elif isinstance(data, list):
            # リスト形式のデータ処理
            # 風速でグループ化
            data_by_wind_speed = {}
            
            for item in data:
                if isinstance(item, dict):
                    wind_speed = item.get("wind_speed")
                    angle = item.get("angle")
                    boat_speed = item.get("boat_speed")
                    data_type = item.get("type", "actual")  # actual, target, vmg
                    
                    if wind_speed is not None and angle is not None and boat_speed is not None:
                        # 最も近い風速値を見つける
                        nearest_wind_speed = min(wind_speeds, key=lambda x: abs(x - wind_speed))
                        
                        if abs(nearest_wind_speed - wind_speed) <= 2.5:  # 2.5ノット以内なら同じ風速とみなす
                            if nearest_wind_speed not in data_by_wind_speed:
                                data_by_wind_speed[nearest_wind_speed] = {"actual": [], "target": [], "vmg": []}
                            
                            # データタイプに基づいて分類
                            if angle_min <= angle <= angle_max:
                                data_by_wind_speed[nearest_wind_speed][data_type].append({
                                    "angle": angle,
                                    "speed": boat_speed
                                })
            
            # データをトレースに変換
            for wind_speed, type_data in data_by_wind_speed.items():
                # 実測値
                if self.get_property("show_actual_data", True) and type_data["actual"]:
                    actual_points = sorted(type_data["actual"], key=lambda x: x["angle"])
                    
                    angles = [point["angle"] for point in actual_points]
                    speeds = [point["speed"] for point in actual_points]
                    
                    traces.append({
                        "type": "scatterpolar",
                        "r": speeds,
                        "theta": angles,
                        "name": f"実測（wind_speed}kt）",
                        "mode": "markers",
                        "marker": {
                            "size": 8,
                            "color": self._get_color_for_wind_speed(wind_speed),
                            "symbol": "circle"
                        }
 "size": 8,
                            "color": self._get_color_for_wind_speed(wind_speed),
                            "symbol": "circle"}
                        
                    })
                
                # ターゲット値
                if self.get_property("show_target_curve", True) and type_data["target"]:
                    target_points = sorted(type_data["target"], key=lambda x: x["angle"])
                    
                    angles = [point["angle"] for point in target_points]
                    speeds = [point["speed"] for point in target_points]
                    
                    # 閉じた曲線のために最初のポイントを末尾に追加
                    if angle_max - angle_min == 360 and angles[0] != angles[-1]:
                        angles.append(angles[0])
                        speeds.append(speeds[0])
                    
                    traces.append({
                        "type": "scatterpolar",
                        "r": speeds,
                        "theta": angles,
                        "name": f"ターゲット（wind_speed}kt）",
                        "mode": "lines",
                        "line": {
                            "color": self._get_color_for_wind_speed(wind_speed),
                            "width": 2,
                            "dash": "solid"
                        }
 "color": self._get_color_for_wind_speed(wind_speed),
                            "width": 2,
                            "dash": "solid"}
                        
                    })
                
                # VMGポイント
                if self.get_property("show_vmg_points", True) and type_data["vmg"]:
                    for vmg_point in type_data["vmg"]:
                        angle = vmg_point["angle"]
                        speed = vmg_point["speed"]
                        direction = "上り" if 0 <= angle <= 90 or 270 <= angle <= 360 else "下り"
                        symbol = "star" if direction == "上り" else "diamond"
                        
                        traces.append({
                            "type": "scatterpolar",
                            "r": [speed],
                            "theta": [angle],
                            "name": f"direction}最適VMG（{wind_speed}kt）",
                            "mode": "markers",
                            "marker": {
                                "size": 12,
                                "color": self._get_color_for_wind_speed(wind_speed),
                                "symbol": symbol,
                                "line": {
                                    "width": 2,
                                    "color": "white"
                                }
                            }
 {
                                "size": 12,
                                "color": self._get_color_for_wind_speed(wind_speed),
                                "symbol": symbol,
                                "line": "width": 2,
                                    "color": "white"}
                                
                            
                        })
        
        # 最大ボート速度を設定
        max_boat_speed = self.get_property("max_boat_speed", "auto")
        
        if max_boat_speed == "auto" and traces:
            # すべてのトレースのrの最大値を検索
            max_speed = 0
            for trace in traces:
                if "r" in trace and trace["r"]:
                    max_speed = max(max_speed, max(trace["r"]))
            
            # 余裕を持たせて切りのいい値に丸める
            max_boat_speed = math.ceil(max_speed * 1.1)
        elif max_boat_speed == "auto":
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
                }
            }
        }
 {
            "title": self.title,
            "polar": {
                "radialaxis": {
                    "visible": True,
                    "range": [0, max_boat_speed],
                    "title": "text": "ボート速度（kt）"}
                    
                },
                "angularaxis": {
                    "visible": True,
                    "direction": "clockwise",
                    "dtick": 30,
                    "period": 360
        }
                }
 "visible": True,
                    "direction": "clockwise",
                    "dtick": 30,
                    "period": 360}
                
            },
            "showlegend": True,
            "legend": {
                "x": 1,
                "y": 0.9
            }
 "x": 1,
                "y": 0.9}
            
        
        return {
            "data": traces,
            "layout": layout
 "data": traces,
            "layout": layout}
        return {
            "data": traces,
            "layout": layout}
 {
            "data": traces,
            "layout": layout}}
        
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
        
        # 風速リストを取得
        wind_speeds = self.get_property("wind_speeds", [5, 10, 15, 20])
        
        # データセットを準備
        datasets = []
        
        # データの形式に応じて処理
        if isinstance(data, dict):
            # ターゲット（理論値）曲線
            if self.get_property("show_target_curve", True) and "target" in data:
                target_data = data["target"]
                
                # 風速別のターゲット曲線
                for wind_speed in wind_speeds:
                    speed_key = f"wind_{wind_speed}"
                    if speed_key in target_data:
                        # この風速でのターゲット曲線データ
                        speed_values = [0] * len(angles)
                        
                        for i, angle in enumerate(angles):
                            angle_str = f"{angle}°"
                            if angle_str in target_data[speed_key]:
                                speed_values[i] = float(target_data[speed_key][angle_str])
                            elif str(angle) in target_data[speed_key]:
                                speed_values[i] = float(target_data[speed_key][str(angle)])
                        
                        datasets.append({
                            "label": f"ターゲット（wind_speed}kt）",
                            "data": speed_values,
                            "fill": False,
                            "backgroundColor": self._get_color_for_wind_speed(wind_speed).replace("1)", "0.2)"),
                            "borderColor": self._get_color_for_wind_speed(wind_speed),
                            "borderWidth": 2,
                            "pointRadius": 0
                        })
            
            # 実測値
            if self.get_property("show_actual_data", True) and "actual" in data:
                actual_data = data["actual"]
                
                # 風速別の実測データ
                for wind_speed in wind_speeds:
                    speed_key = f"wind_{wind_speed}"
                    if speed_key in actual_data:
                        # この風速での実測データ
                        speed_values = [None] * len(angles)
                        
                        for i, angle in enumerate(angles):
                            angle_str = f"{angle}°"
                            if angle_str in actual_data[speed_key]:
                                speed_values[i] = float(actual_data[speed_key][angle_str])
                            elif str(angle) in actual_data[speed_key]:
                                speed_values[i] = float(actual_data[speed_key][str(angle)])
                        
                        datasets.append({
                            "label": f"実測（wind_speed}kt）",
                            "data": speed_values,
                            "fill": False,
                            "backgroundColor": self._get_color_for_wind_speed(wind_speed),
                            "borderColor": self._get_color_for_wind_speed(wind_speed),
                            "borderWidth": 1,
                            "pointRadius": 4,
                            "pointStyle": "circle"
                        })
        
        elif isinstance(data, list):
            # リスト形式のデータ処理
            # 風速でグループ化
            data_by_wind_speed = {}
            
            for item in data:
                if isinstance(item, dict):
                    wind_speed = item.get("wind_speed")
                    angle = item.get("angle")
                    boat_speed = item.get("boat_speed")
                    data_type = item.get("type", "actual")  # actual, target
                    
                    if wind_speed is not None and angle is not None and boat_speed is not None:
                        # 最も近い風速値を見つける
                        nearest_wind_speed = min(wind_speeds, key=lambda x: abs(x - wind_speed))
                        
                        if abs(nearest_wind_speed - wind_speed) <= 2.5:  # 2.5ノット以内なら同じ風速とみなす
                            if nearest_wind_speed not in data_by_wind_speed:
                                data_by_wind_speed[nearest_wind_speed] = {"actual": }, "target": {}}
                            
                            # 最も近い角度インデックスを見つける
                            nearest_angle_idx = min(range(len(angles)), key=lambda i: abs(angles[i] - angle))
                            
                            if abs(angles[nearest_angle_idx] - angle) <= angle_step / 2:  # 角度ステップの半分以内なら同じ角度とみなす
                                # その角度での平均または最大値を計算
                                if angles[nearest_angle_idx] in data_by_wind_speed[nearest_wind_speed][data_type]:
                                    # 既存の値との平均を取る
                                    current = data_by_wind_speed[nearest_wind_speed][data_type][angles[nearest_angle_idx]]
                                    data_by_wind_speed[nearest_wind_speed][data_type][angles[nearest_angle_idx]] = (current + boat_speed) / 2
                                else:
                                    data_by_wind_speed[nearest_wind_speed][data_type][angles[nearest_angle_idx]] = boat_speed
            
            # データをデータセットに変換
            for wind_speed, type_data in data_by_wind_speed.items():
                # ターゲット値
                if self.get_property("show_target_curve", True) and type_data["target"]:
                    target_values = [None] * len(angles)
                    
                    for i, angle in enumerate(angles):
                        if angle in type_data["target"]:
                            target_values[i] = type_data["target"][angle]
                    
                    datasets.append({
                        "label": f"ターゲット（wind_speed}kt）",
                        "data": target_values,
                        "fill": False,
                        "backgroundColor": self._get_color_for_wind_speed(wind_speed).replace("1)", "0.2)"),
                        "borderColor": self._get_color_for_wind_speed(wind_speed),
                        "borderWidth": 2,
                        "pointRadius": 0
                    })
                
                # 実測値
                if self.get_property("show_actual_data", True) and type_data["actual"]:
                    actual_values = [None] * len(angles)
                    
                    for i, angle in enumerate(angles):
                        if angle in type_data["actual"]:
                            actual_values[i] = type_data["actual"][angle]
                    
                    datasets.append({
                        "label": f"実測（wind_speed}kt）",
                        "data": actual_values,
                        "fill": False,
                        "backgroundColor": self._get_color_for_wind_speed(wind_speed),
                        "borderColor": self._get_color_for_wind_speed(wind_speed),
                        "borderWidth": 1,
                        "pointRadius": 4,
                        "pointStyle": "circle"
                    })
        
        # 最大ボート速度を設定
        max_boat_speed = self.get_property("max_boat_speed", "auto")
        
        if max_boat_speed == "auto" and datasets:
            # すべてのデータセットの最大値を検索
            max_speed = 0
            for dataset in datasets:
                for value in dataset["data"]:
                    if value is not None:
                        max_speed = max(max_speed, value)
            
            # 余裕を持たせて切りのいい値に丸める
            max_boat_speed = math.ceil(max_speed * 1.1)
        elif max_boat_speed == "auto":
            max_boat_speed = 10  # デフォルト値
        
        return {
            "type": "radar",
            "data": {
                "labels": angle_labels,
                "datasets": datasets
            }
 {
            "type": "radar",
            "data": "labels": angle_labels,
                "datasets": datasets}
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
                }
            }
 {
                "scales": {
                    "r": {
                        "beginAtZero": True,
                        "max": max_boat_speed,
                        "ticks": "stepSize": max_boat_speed / 5}
                        
                    
                },
                "elements": {
                    "line": {
                        "tension": 0.1
                    }
            }
                }
 {
                    }
                }
            }
                    "line": "tension": 0.1}
                    
                
            
        
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
                        }
                    }
                }
            }
 {
                "scales": {
                    "r": {
                        "beginAtZero": True,
                        "angleLines": "display": True,
                            "color": "rgba(0, 0, 0, 0.1)"}
                        },
                        "grid": {
                            "color": "rgba(0, 0, 0, 0.1)"
 "color": "rgba(0, 0, 0, 0.1)"}
                        },
                        "ticks": {
                            "backdropColor": "rgba(255, 255, 255, 0.75)",
                            "color": "#666"
            }
                        }
 "backdropColor": "rgba(255, 255, 255, 0.75)",
                            "color": "#666"}
                        },
                        "pointLabels": {
                            "font": {
                                "size": 10
                            }
                        }
 {
                            "font": "size": 10}
                            
                        
                    
                },
                "plugins": {
                    "legend": {
                        "position": "right",
                        "labels": {
                            "font": {
                                "size": 11
                            }
                        }
                    }
                }
 {
                    "legend": {
                        "position": "right",
                        "labels": {
                            "font": "size": 11}
                            
                        
                    },
                    "tooltip": {
                        "callbacks": {
                            "label": "function(context) return context.dataset.label + ': ' + context.raw.toFixed(1) + ' kt'; }"
                    }
                    }
 {
                        "callbacks": {
                        }
                            "label": "function(context) return context.dataset.label + ': ' + context.raw.toFixed(1) + ' kt'; }"}
                        
                    
                },
                "animation": {
                    "duration": 1000,
                    "easing": "easeOutQuart"
                }
 "duration": 1000,
                    "easing": "easeOutQuart"}
                
            
            # オプションを結合
            self._merge_options(options, polar_options)
            
            return options
    
    def render(self, context: Dict[str, Any]) -> str:
        """
        要素をHTMLにレンダリング
        
        Parameters
        ----------
        context : Dict[str, Any]
            レンダリングコンテキスト
            
        Returns
        -------
        str
            レンダリングされたHTML
        """
        # 条件チェック
        if not self.evaluate_conditions(context):
            return ""
        
        # レンダラータイプの取得
        renderer_type = self.get_property("renderer", "plotly")
        
        # データとオプションを取得
        chart_data = self.get_chart_data(context)
        chart_options = self.get_chart_options()
        
        # ディメンションを取得
        width, height = self.get_chart_dimensions()
        
        # レンダラーを作成
        from sailing_data_processor.reporting.elements.visualizations.chart_renderer import RendererFactory
        renderer = RendererFactory.create_renderer(renderer_type, self.chart_id)
        
        # チャートをレンダリング
        html_content = renderer.render(chart_data, width, height)
        
        return html_content
    
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


class CoursePerformanceElement(BaseChartElement):
    """
    コースパフォーマンスグラフ要素
    
    風向に対する速度プロファイルを表示するための要素です。
    風向角度ごとのボートスピード特性を視覚化し、ターゲット速度との比較やVMG（Velocity Made Good）
    分析を可能にします。
    
    拡張機能:
    - ターゲット速度線との精密な比較
    - VMG（Velocity Made Good）分析の詳細表示
    - パフォーマンス効率指標の計算と表示
    - カスタムボートポーラー対応
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
            kwargs['chart_type'] = "radar"
            
        # 拡張デフォルトプロパティ
        if model is None:
            # 詳細表示のデフォルト設定
            if 'show_details' not in kwargs:
                kwargs['show_details'] = True
                
            # 効率指標表示のデフォルト設定
            if 'show_efficiency' not in kwargs:
                kwargs['show_efficiency'] = True
                
            # ボートポーラー参照の設定
            if 'polar_reference' not in kwargs:
                kwargs['polar_reference'] = None  # "470", "49er", "finn", "laser" など
                
            # 表示角度範囲の設定
            if 'angle_range' not in kwargs:
                kwargs['angle_range'] = 'full'  # full, upwind, downwind
        
        super().__init__(model, **kwargs)
        
    def get_chart_libraries(self) -> List[str]:
        """
        チャートの描画に必要なライブラリのリストを取得
        
        Returns
        -------
        List[str]
            ライブラリのURLリスト
        """
        libraries = [
            "https://cdn.jsdelivr.net/npm/chart.js@3.7.1/dist/chart.min.js",
            "https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2.0.0/dist/chartjs-plugin-datalabels.min.js"
        ]
        
        # 詳細表示が有効な場合、追加のライブラリを読み込む
        if self.get_property("show_details", True):
            libraries.append("https://cdn.jsdelivr.net/npm/d3@7.0.0/dist/d3.min.js")
            libraries.append("https://cdn.jsdelivr.net/npm/chartjs-plugin-crosshair@1.2.0/dist/chartjs-plugin-crosshair.min.js")
        
        # 効率指標表示が有効な場合、計算のためのライブラリを追加
        if self.get_property("show_efficiency", True):
            libraries.append("https://cdn.jsdelivr.net/npm/mathjs@9.5.0/lib/browser/math.min.js")
            
        return libraries
    
    def get_chart_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        コースパフォーマンスのデータを取得
        
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
            return {"type": "radar", "data": "labels": [], "datasets": []}}
        
        # 角度分割数の取得（デフォルト：36方位、10度間隔）
        angle_divisions = self.get_property("angle_divisions", 36)
        
        # 方位ラベルを生成
        direction_labels = []
        for i in range(angle_divisions):
            angle = i * (360.0 / angle_divisions)
            direction_labels.append(f"{int(angle)}°")
        
        # データセットの準備
        datasets = []
        
        # 実績データの処理
        actual_dataset = self._process_performance_data(data, "actual", "実績速度", "rgba(54, 162, 235, 0.5)")
        if actual_dataset:
            datasets.append(actual_dataset)
        
        # ターゲット速度データの処理
        target_dataset = self._process_performance_data(data, "target", "ターゲット速度", "rgba(255, 99, 132, 0.5)")
        if target_dataset:
            datasets.append(target_dataset)
        
        # VMG（Velocity Made Good）データの処理
        vmg_dataset = self._process_performance_data(data, "vmg", "VMG", "rgba(75, 192, 192, 0.5)")
        if vmg_dataset:
            datasets.append(vmg_dataset)
        
        # チャートデータの作成
        chart_data = {
            "type": "radar",
            "data": {
                "labels": direction_labels,
                "datasets": datasets
            }
        }
 {
            "type": "radar",
            "data": "labels": direction_labels,
                "datasets": datasets}
            
        
        return chart_data
    
    def get_chart_options(self) -> Dict[str, Any]:
        """
        コースパフォーマンスのオプションを取得
        
        Returns
        -------
        Dict[str, Any]
            チャートオプション
        """
        options = super().get_chart_options()
        
        # コースパフォーマンス特有のオプション
        performance_options = {
            "scale": {
                "angleLines": {
                    "display": True,
                    "color": self.get_property("angle_lines_color", "rgba(0, 0, 0, 0.1)")
                }
            }
        }
 {
            "scale": {
                "angleLines": "display": True,
                    "color": self.get_property("angle_lines_color", "rgba(0, 0, 0, 0.1)")}
                },
                "ticks": {
                    "beginAtZero": True,
                    "precision": 1,
                    "maxTicksLimit": self.get_property("max_ticks", 5)
                }
 "beginAtZero": True,
                    "precision": 1,
                    "maxTicksLimit": self.get_property("max_ticks", 5)}
                
            },
            "plugins": {
                "legend": {
                    "position": "top"
                }
            }
 {
                "legend": "position": "top"}
                },
                "tooltip": {
                    "callbacks": {
                        "label": "function(context) return context.dataset.label + ': ' + context.raw.toFixed(1) + ' kt'; }"
                }
 {
                    "callbacks": {
                        "label": "function(context) return context.dataset.label + ': ' + context.raw.toFixed(1) + ' kt'; }"}
                    
                
            
        
        # 詳細表示が有効な場合の追加設定
        if self.get_property("show_details", True):
            performance_options["plugins"]["tooltip"]["callbacks"] = {
                "title": "function(context) return '風向角: ' + context[0].label; }",
                "label": "function(context) { return context.dataset.label + ': ' + context.raw.toFixed(1) + ' kt'; }"
 {
                "title": "function(context) return '風向角: ' + context[0].label; }",
                "label": "function(context) { return context.dataset.label + ': ' + context.raw.toFixed(1) + ' kt'; }"}
            performance_options["plugins"]["tooltip"]["callbacks"] = {
                "title": "function(context) return '風向角: ' + context[0].label; }",
                "label": "function(context) { return context.dataset.label + ': ' + context.raw.toFixed(1) + ' kt'; }"}
 {
                "title": "function(context) return '風向角: ' + context[0].label; }",
                "label": "function(context) { return context.dataset.label + ': ' + context.raw.toFixed(1) + ' kt'; }"}}
            performance_options["plugins"]["tooltip"]["callbacks"] = {
                "title": "function(context) return '風向角: ' + context[0].label; }",
                "label": "function(context) { return context.dataset.label + ': ' + context.raw.toFixed(1) + ' kt'; }"}
 {
                "title": "function(context) return '風向角: ' + context[0].label; }",
                "label": "function(context) { return context.dataset.label + ': ' + context.raw.toFixed(1) + ' kt'; }"}}
            
            # 追加のプラグイン設定（クロスヘアなど）
            performance_options["plugins"]["crosshair"] = {
                "line": {
                    "color": "rgba(100, 100, 100, 0.4)",
                    "width": 1
                }
            }
 {
                "line": "color": "rgba(100, 100, 100, 0.4)",
                    "width": 1}
                },
                "sync": {
                    "enabled": True
 "enabled": True}
                
            
        # 効率指標表示が有効な場合
        if self.get_property("show_efficiency", True):
            # サブタイトルに効率指標を追加
            performance_options["plugins"]["title"] = {
                "display": True,
                "text": self.title,
                "subtitle": {
                    "display": True,
                    "text": "パフォーマンス効率: 計算中...",
                    "font": {
                        "size": 12,
                        "style": "italic"
                    }
                }
            }
 {
                "display": True,
                "text": self.title,
                "subtitle": {
                    "display": True,
                    "text": "パフォーマンス効率: 計算中...",
                    "font": "size": 12,
                        "style": "italic"}
            performance_options["plugins"]["title"] = {
                "display": True,
                "text": self.title,
                "subtitle": {
                    "display": True,
                    "text": "パフォーマンス効率: 計算中...",
                    "font": "size": 12,
                        "style": "italic"}
            }
 {
                "display": True,
                "text": self.title,
                "subtitle": {
                    "display": True,
                    "text": "パフォーマンス効率: 計算中...",
                    "font": "size": 12,
                        "style": "italic"}}
            performance_options["plugins"]["title"] = {
                "display": True,
                "text": self.title,
                "subtitle": {
                    "display": True,
                    "text": "パフォーマンス効率: 計算中...",
                    "font": "size": 12,
                        "style": "italic"}
            }
 {
                "display": True,
                "text": self.title,
                "subtitle": {
                    "display": True,
                    "text": "パフォーマンス効率: 計算中...",
                    "font": "size": 12,
            }
                        "style": "italic"}}
                    
                
            
        # 表示角度範囲の設定
        angle_range = self.get_property("angle_range", "full")
        if angle_range != "full":
            if angle_range == "upwind":
                # 風上範囲 (通常は0-90度と270-360度)
                performance_options["scale"]["startAngle"] = 270
                performance_options["scale"]["endAngle"] = 90
            elif angle_range == "downwind":
                # 風下範囲 (通常は90-270度)
                performance_options["scale"]["startAngle"] = 90
                performance_options["scale"]["endAngle"] = 270
        
        # ボートポーラー参照が指定されている場合、グラフに注釈を追加
        polar_reference = self.get_property("polar_reference", None)
        if polar_reference:
            performance_options["plugins"]["subtitle"] = {
                "display": True,
                "text": f"ボートポーラー参照: polar_reference}",
                "color": "rgba(100, 100, 100, 0.8)"
 {
                "display": True,
                "text": f"ボートポーラー参照: polar_reference}",
                "color": "rgba(100, 100, 100, 0.8)"}
            performance_options["plugins"]["subtitle"] = {
                "display": True,
                "text": f"ボートポーラー参照: polar_reference}",
                "color": "rgba(100, 100, 100, 0.8)"}
 {
                "display": True,
                "text": f"ボートポーラー参照: polar_reference}",
                "color": "rgba(100, 100, 100, 0.8)"}}
            performance_options["plugins"]["subtitle"] = {
                "display": True,
                "text": f"ボートポーラー参照: polar_reference}",
                "color": "rgba(100, 100, 100, 0.8)"}
 {
                "display": True,
                "text": f"ボートポーラー参照: polar_reference}",
                "color": "rgba(100, 100, 100, 0.8)"}}
            
        # オプションを結合
        self._merge_options(options, performance_options)
        
        return options
    
    def _process_performance_data(self, data: Any, key: str, label: str, color: str) -> Optional[Dict[str, Any]]:
        """
        パフォーマンスデータを処理してデータセットを作成
        
        Parameters
        ----------
        data : Any
            元データ
        key : str
            データキー
        label : str
            データセットラベル
        color : str
            データセットの色
            
        Returns
        -------
        Optional[Dict[str, Any]]
            処理されたデータセット、データがない場合はNone
        """
        angle_divisions = self.get_property("angle_divisions", 36)
        values = [0] * angle_divisions
        
        # データの形式によって処理を分岐
        if isinstance(data, dict) and key in data and isinstance(data[key], list):
            # キーで指定された値がリストの場合
            raw_values = data[key]
            if len(raw_values) == angle_divisions:
                values = raw_values
            elif len(raw_values) > 0:
                # データの長さが一致しない場合は補間
                for i in range(angle_divisions):
                    angle = i * (360.0 / angle_divisions)
                    nearest_idx = self._find_nearest_angle_index(data.get("angles", [i * (360.0 / len(raw_values)) for i in range(len(raw_values))]), angle)
                    if 0 <= nearest_idx < len(raw_values):
                        values[i] = raw_values[nearest_idx]
        
        elif isinstance(data, list):
            # リスト形式のデータの場合
            if all(isinstance(item, dict) for item in data):
                # 辞書のリストの場合
                angle_key = self.get_property("angle_key", "angle")
                value_key = key  # actual, target, vmgなどのキー
                
                for item in data:
                    if angle_key in item and value_key in item:
                        angle = item[angle_key]
                        value = item[value_key]
                        
                        # 角度を正規化（0-360の範囲に収める）
                        angle = angle % 360
                        
                        # 対応するインデックスを計算
                        index = int(round(angle / (360.0 / angle_divisions))) % angle_divisions
                        
                        # 値を設定（同じ角度の場合は平均または最大値を使用可能）
                        if values[index] == 0:
                            values[index] = value
                        else:
                            # デフォルトは平均値
                            avg_method = self.get_property("average_method", "mean")
                            if avg_method == "max":
                                values[index] = max(values[index], value)
                            else:  # mean
                                values[index] = (values[index] + value) / 2
        
        # データセットが空の場合はNoneを返す
        if all(v == 0 for v in values):
            return None
        
        # データセットを作成
        dataset = {
            "label": self.get_property(f"key}_label", label),
            "data": values,
            "fill": True,
            "backgroundColor": color,
            "borderColor": color.replace("0.5", "1"),
            "pointBackgroundColor": color.replace("0.5", "1"),
            "pointBorderColor": "#fff",
            "pointHoverBackgroundColor": "#fff",
            "pointHoverBorderColor": color.replace("0.5", "1")
 {
            "label": self.get_property(f"key}_label", label),
            "data": values,
            "fill": True,
            "backgroundColor": color,
            "borderColor": color.replace("0.5", "1"),
            "pointBackgroundColor": color.replace("0.5", "1"),
            "pointBorderColor": "#fff",
            "pointHoverBackgroundColor": "#fff",
            "pointHoverBorderColor": color.replace("0.5", "1")}
        
        return dataset
    
    def _find_nearest_angle_index(self, angles: List[float], target_angle: float) -> int:
        """
        最も近い角度のインデックスを見つける
        
        Parameters
        ----------
        angles : List[float]
            角度のリスト
        target_angle : float
            対象の角度
            
        Returns
        -------
        int
            最も近い角度のインデックス
        """
        if not angles:
            return -1
        
        # 角度の差を計算（360度を考慮）
        def angle_diff(a1, a2):
            diff = abs(a1 - a2)
            return min(diff, 360 - diff)
        
        nearest_idx = 0
        min_diff = angle_diff(angles[0], target_angle)
        
        for i in range(1, len(angles)):
            diff = angle_diff(angles[i], target_angle)
            if diff < min_diff:
                min_diff = diff
                nearest_idx = i
        
        return nearest_idx
    
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


class TackingAngleElement(BaseChartElement):
    """
    タッキングアングル分析要素
    
    タッキング角度のヒストグラムを表示するための要素です。
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
        return [
            "https://cdn.jsdelivr.net/npm/chart.js@3.7.1/dist/chart.min.js",
            "https://cdn.jsdelivr.net/npm/chartjs-plugin-annotation@1.4.0/dist/chartjs-plugin-annotation.min.js"
        ]
    
    def get_chart_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        タッキングアングル分析のデータを取得
        
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
            return {"type": "bar", "data": "labels": [], "datasets": []}}
        
        # ビンの数を取得（角度範囲の分割数）
        num_bins = self.get_property("num_bins", 18)  # デフォルトは10度間隔
        
        # 最小角度と最大角度を取得
        min_angle = self.get_property("min_angle", 70)  # デフォルトは70度
        max_angle = self.get_property("max_angle", 140)  # デフォルトは140度
        
        # 最適角度範囲を取得
        optimal_min = self.get_property("optimal_min", 85)
        optimal_max = self.get_property("optimal_max", 95)
        
        # ビンの幅を計算
        bin_width = (max_angle - min_angle) / num_bins
        
        # ヒストグラムのビンを初期化
        bins = [0] * num_bins
        bin_edges = [min_angle + i * bin_width for i in range(num_bins + 1)]
        bin_labels = [f"{int(edge)}°" for edge in bin_edges[:-1]]
        
        # データの形式によって処理を分岐
        if isinstance(data, dict) and "angles" in data and isinstance(data["angles"], list):
            # キー"angles"のリスト形式の場合
            angles = data["angles"]
            
            for angle in angles:
                if min_angle <= angle < max_angle:
                    bin_idx = min(int((angle - min_angle) / bin_width), num_bins - 1)
                    bins[bin_idx] += 1
        
        elif isinstance(data, list):
            # リスト形式のデータの場合
            if all(isinstance(item, (int, float)) for item in data):
                # 数値のリストの場合（角度のリスト）
                for angle in data:
                    if min_angle <= angle < max_angle:
                        bin_idx = min(int((angle - min_angle) / bin_width), num_bins - 1)
                        bins[bin_idx] += 1
            
            elif all(isinstance(item, dict) for item in data):
                # 辞書のリストの場合
                angle_key = self.get_property("angle_key", "tacking_angle")
                
                for item in data:
                    if angle_key in item:
                        angle = item[angle_key]
                        if min_angle <= angle < max_angle:
                            bin_idx = min(int((angle - min_angle) / bin_width), num_bins - 1)
                            bins[bin_idx] += 1
        
        # 背景色の設定
        background_colors = []
        for i in range(len(bins)):
            edge = bin_edges[i]
            
            # 最適範囲内は緑色、それ以外は青色
            if optimal_min <= edge < optimal_max:
                background_colors.append("rgba(75, 192, 192, 0.6)")  # 緑色
            else:
                background_colors.append("rgba(54, 162, 235, 0.6)")  # 青色
        
        # データセットを作成
        datasets = [{
            "label": self.get_property("label", "タッキング角度分布"),
            "data": bins,
            "backgroundColor": background_colors,
            "borderColor": [c.replace("0.6", "1") for c in background_colors],
            "borderWidth": 1
        }]
        
        # チャートデータの作成
        chart_data = {
            "type": "bar",
            "data": {
                "labels": bin_labels,
                "datasets": datasets
            }
        }
 {
            "type": "bar",
            "data": "labels": bin_labels,
                "datasets": datasets}
            
        
        return chart_data
    
    def get_chart_options(self) -> Dict[str, Any]:
        """
        タッキングアングル分析のオプションを取得
        
        Returns
        -------
        Dict[str, Any]
            チャートオプション
        """
        options = super().get_chart_options()
        
        # 最適角度範囲を取得
        optimal_min = self.get_property("optimal_min", 85)
        optimal_max = self.get_property("optimal_max", 95)
        
        # タッキングアングル分析特有のオプション
        tacking_options = {
            "scales": {
                "y": {
                    "beginAtZero": True,
                    "title": {
                        "display": True,
                        "text": "頻度"
                    }
                }
            }
        }
 {
            "scales": {
                "y": {
                    "beginAtZero": True,
                    "title": "display": True,
                        "text": "頻度"}
                    
                },
                "x": {
                    "title": {
                        "display": True,
                        "text": "タッキング角度"
                    }
        }
                }
 {
                    "title": "display": True,
                        "text": "タッキング角度"}
                    
                
            },
            "plugins": {
                "legend": {
                    "display": True,
                    "position": "top"
                }
            }
 {
                "legend": "display": True,
                    "position": "top"}
                },
                "tooltip": {
        }
                    "callbacks": {
                        "title": "function(context) return '角度: ' + context[0].label; }",
                        "label": "function(context) { return '頻度: ' + context.raw; }"
 {
                    "callbacks": {
                        "title": "function(context) return '角度: ' + context[0].label; }",
                        "label": "function(context) { return '頻度: ' + context.raw; }"}
                    
                },
                "annotation": {
                    "annotations": {
                        "optimal_range": {
                            "type": "box",
                            "xMin": f"optimal_min}°",
                            "xMax": f"{optimal_max}°",
                            "backgroundColor": "rgba(75, 192, 192, 0.2)",
                            "borderColor": "rgba(75, 192, 192, 1)",
                            "borderWidth": 1,
                            "label": {
                                "enabled": True,
                                "content": "最適範囲",
                                "position": "top"
                            }
                }
 {
                    "annotations": {
                        "optimal_range": {
                            "type": "box",
                            "xMin": f"optimal_min}°",
                            "xMax": f"{optimal_max}°",
                            "backgroundColor": "rgba(75, 192, 192, 0.2)",
                            "borderColor": "rgba(75, 192, 192, 1)",
                            "borderWidth": 1,
                            "label": {
                                "enabled": True,
                                "content": "最適範囲",
                                "position": "top"}
                            
                        
                    
                }
                
            
        
        # オプションを結合
        self._merge_options(options, tacking_options)
        
        return options
    
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


class StrategyPointMapElement(BaseChartElement):
    """
    戦略ポイントマップ要素
    
    コース上の重要戦略ポイントを地図上に表示するための要素です。
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
        # デフォルトでマップ要素タイプを設定
        if model is None and 'element_type' not in kwargs:
            kwargs['element_type'] = ElementType.MAP
        
        if model is None and 'chart_type' not in kwargs:
            kwargs['chart_type'] = "strategy_map"
        
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
            "https://unpkg.com/leaflet@1.7.1/dist/leaflet.js",
            "https://unpkg.com/leaflet-draw@1.0.4/dist/leaflet.draw.js"
        ]
    
    def render(self, context: Dict[str, Any]) -> str:
        """
        要素をHTMLにレンダリング
        
        Parameters
        ----------
        context : Dict[str, Any]
            レンダリングコンテキスト
            
        Returns
        -------
        str
            レンダリングされたHTML
        """
        # 条件チェック
        if not self.evaluate_conditions(context):
            return ""
        
        # データソースからデータを取得
        data = None
        if self.data_source and self.data_source in context:
            data = context[self.data_source]
        
        # データがない場合
        if not data:
            return f'<div id="{self.element_id}" class="report-map-empty">戦略ポイントデータがありません</div>'
        
        # CSSスタイルの取得
        css_style = self.get_css_styles()
        width, height = self.get_chart_dimensions()
        
        # マップのデフォルト中心位置と拡大レベル
        center_lat = self.get_property("center_lat", 35.4498)
        center_lng = self.get_property("center_lng", 139.6649)
        zoom_level = self.get_property("zoom_level", 13)
        
        # データをJSON文字列に変換
        data_json = json.dumps(data)
        
        # ポイントタイプ別のアイコン設定
        icon_config = self.get_property("icon_config", {
            "tack": "color": "blue", "icon": "exchange-alt"},
            "gybe": {"color": "green", "icon": "random"},
            "mark_rounding": {"color": "red", "icon": "flag"},
            "wind_shift": {"color": "purple", "icon": "wind"},
            "default": {"color": "gray", "icon": "map-marker"}
            }
            }
 {
            "tack": "color": "blue", "icon": "exchange-alt"},
            "gybe": {"color": "green", "icon": "random"},
            "mark_rounding": {"color": "red", "icon": "flag"},
            "wind_shift": {"color": "purple", "icon": "wind"},
            "default": {"color": "gray", "icon": "map-marker"}}
        })
            }
        
        icon_config_json = json.dumps(icon_config)
        
        # マップ要素のレンダリング
        html_content = f'''
        <div id="{self.element_id}" class="report-map-container" style="{css_style}">
            <!-- Leaflet CSS -->
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
            <link rel="stylesheet" href="https://unpkg.com/leaflet-draw@1.0.4/dist/leaflet.draw.css" />
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css" />
            
            <div id="{self.chart_id}" style="width: {width}; height: {height};"></div>
            
            }
            <script>
                (function() {{
                    // マップデータ
                    var mapData = data_json};
                    var iconConfig = {icon_config_json};
                    
                    }
                    // マップ初期化
                    window.addEventListener('load', function() {{
                        // マップの作成
                        var map = L.map('self.chart_id}').setView([{center_lat}, {center_lng}], {zoom_level});
                        
                        // 地図タイルの追加
                        L.tileLayer('https://{s}}.tile.openstreetmap.org/{z}}/{x}}/{y}}.png', {attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                        }}).addTo(map);
                        
                        // GPSトラックの表示
                        if (mapData.track) {{
                            var trackPoints = [];
                            for (var i = 0; i < mapData.track.length; i++) {{
                                var point = mapData.track[i];
                                if (point.lat && point.lng) {trackPoints.push([point.lat, point.lng]);
                                }}
                            }}
                            
                            if (trackPoints.length > 0) {{
                                // トラックラインを描画
                                var trackLine = L.polyline(trackPoints, {color: 'blue',
                                    weight: 3,
                                    opacity: 0.7
                                }}).addTo(map);
                                
                                // 自動的にトラック全体が表示されるようにズーム
                                map.fitBounds(trackLine.getBounds());
                            }}
                        }}
                        
                        // 戦略ポイントの表示
                        if (mapData.points) {{
                            for (var i = 0; i < mapData.points.length; i++) {{
                                var point = mapData.points[i];
                                if (point.lat && point.lng) {{
                                    // ポイントタイプに基づいてアイコンを選択
                                    var pointType = point.type || 'default';
                                    var iconCfg = iconConfig[pointType] || iconConfig.default;
                                    
                                    // マーカーの作成
                                    var marker = L.marker([point.lat, point.lng], {title: point.name || point.description || pointType
                                    }}).addTo(map);
                                    
                                    // ポップアップの追加
                                    var popupContent = '<div class="strategy-point-popup">';
                                    if (point.name) popupContent += '<h4>' + point.name + '</h4>';
                                    if (point.type) popupContent += '<p>タイプ: ' + point.type + '</p>';
                                    if (point.description) popupContent += '<p>' + point.description + '</p>';
                                    if (point.time) popupContent += '<p>時間: ' + point.time + '</p>';
                                    popupContent += '</div>';
                                    
                                    marker.bindPopup(popupContent);
                                }}
                            }}
                        }}
                    }});
                }})();
            </script>
        </div>
        '''
        
        return html_content
