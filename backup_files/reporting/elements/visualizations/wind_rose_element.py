# -*- coding: utf-8 -*-
"""
Module for sailing chart visualization components.
This module provides specialized chart elements for sailing data visualization.
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
            return {"type": "polarArea", "data": {"labels": [], "datasets": []}}
        
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
                    if time_end:
                        to_str = time_end.split("T")[0] if "T" in time_end else time_end
                        filter_info += f" 終了: {to_str}"
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
        chart_data = {
            "type": "polarArea",
            "data": {
                "labels": direction_labels,
                "datasets": datasets
            }
        }
        
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
            },
            "plugins": {
                "legend": {
                    "position": self.get_property("legend_position", "top")
                },
                "tooltip": {
                    "callbacks": {
                        "label": "function(context) { return context.label + ': ' + context.raw.toFixed(1); }"
                    }
                },
                "datalabels": {
                    "display": self.get_property("show_labels", False),
                    "color": "white",
                    "font": {
                        "weight": "bold"
                    },
                    "formatter": "function(value) { return value.toFixed(1); }"
                }
            },
            "animation": {
                "duration": self.get_property("animation_duration", 1000),
                "easing": "easeOutQuart"
            }
        }
        
        # 詳細表示が有効な場合の追加設定
        if self.get_property("show_details", True):
            wind_rose_options["plugins"]["tooltip"]["callbacks"] = {
                "title": "function(context) { return context[0].label; }",
                "label": "function(context) { var dataIndex = context.dataIndex; var value = context.raw; " +
                         "return [" +
                         "'値: ' + value.toFixed(1)," +
                         "'全体に対する割合: ' + (value / context.chart.data.datasets[0].data.reduce((a,b) => a + b, 0) * 100).toFixed(1) + '%'" +
                         "]; }"
            }
            
        # 拡張カラースケールの設定
        color_scale_type = self.get_property("color_scale_type", "sequential")
        if color_scale_type == "diverging":
            wind_rose_options["plugins"]["colorschemes"] = {
                "scheme": "brewer.diverging.Spectral11",
                "reverse": False
            }
        elif color_scale_type == "categorical":
            wind_rose_options["plugins"]["colorschemes"] = {
                "scheme": "brewer.qualitative.Set3",
                "override": True
            }
            
        # 角度ラインのカスタマイズ
        angle_lines_enabled = self.get_property("angle_lines_enabled", True)
        angle_lines_color = self.get_property("angle_lines_color", "rgba(0, 0, 0, 0.1)")
        wind_rose_options["scale"]["angleLines"] = {
            "display": angle_lines_enabled,
            "color": angle_lines_color
        }
        
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
                    
            # サブタイトルの追加
            filter_text = "期間フィルター適用:"
            if time_start:
                from_str = time_start.split("T")[0] if "T" in time_start else time_start
                filter_text += f" 開始: {from_str}"
            if time_end:
                to_str = time_end.split("T")[0] if "T" in time_end else time_end
                filter_text += f" 終了: {to_str}"
            
            options["plugins"]["title"]["subtitle"] = {
                "display": True,
                "text": filter_text,
                "font": {
                    "size": 12,
                    "style": "italic"
                },
                "color": "rgba(100, 100, 100, 0.8)"
            }
        
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
