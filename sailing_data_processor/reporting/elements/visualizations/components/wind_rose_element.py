#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
風配図要素モジュール

このモジュールは風向・風速データを風配図として表示するためのチャートコンポーネントを提供します。
"""

from typing import Dict, List, Any, Optional
from datetime import datetime

from ...base_element import BaseElement

class WindRoseElement(BaseElement):
    """
    風配図要素クラス
    
    風向・風速データを風配図（チャートJS拡張）として表示するためのコンポーネント
    """
    
    def __init__(self, element_id: str, title: str = "風配図"):
        """
        コンストラクタ
        
        Parameters
        ----------
        element_id : str
            要素ID
        title : str, optional
            タイトル, by default "風配図"
        """
        super().__init__(element_id, title)
        self.chart_id = f"wind-rose-{element_id}"
        self.wind_data = []
        
    def add_wind_data(self, direction: float, speed: float, frequency: float = 1.0):
        """
        風データを追加
        
        Parameters
        ----------
        direction : float
            風向 (度)
        speed : float
            風速 (ノット)
        frequency : float, optional
            頻度/重み, by default 1.0
        """
        self.wind_data.append({
            "direction": direction,
            "speed": speed,
            "frequency": frequency
        })
    
    def get_chart_data(self) -> Dict[str, Any]:
        """
        チャートデータを取得
        
        Returns
        -------
        Dict[str, Any]
            チャートJSデータ形式
        """
        # 方位を16方位に分類
        direction_bins = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", 
                         "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
        bin_values = [0] * len(direction_bins)
        
        # データを方位ビンに集約
        for item in self.wind_data:
            dir_index = round(item["direction"] / 22.5) % 16
            bin_values[dir_index] += item["speed"] * item["frequency"]
        
        # カラースケール（風速に応じた色）
        color_scale = [
            "rgba(200, 230, 255, 0.8)",  # 弱い風
            "rgba(150, 210, 255, 0.8)",
            "rgba(100, 180, 255, 0.8)",
            "rgba(50, 150, 255, 0.8)",
            "rgba(0, 120, 255, 0.8)"     # 強い風
        ]
        
        # 色を割り当て
        colors = self._get_colors_for_values(bin_values, color_scale)
        
        return {
            "labels": direction_bins,
            "datasets": [{
                "data": bin_values,
                "backgroundColor": colors,
                "borderColor": "rgba(0, 0, 0, 0.1)",
                "borderWidth": 1
            }]
        }
    
    def get_chart_options(self) -> Dict[str, Any]:
        """
        チャートオプションを取得
        
        Returns
        -------
        Dict[str, Any]
            チャートJSオプション
        """
        options = {
            "plugins": {
                "title": {
                    "display": True,
                    "text": self.title,
                    "font": {
                        "size": 16
                    }
                },
                "legend": {
                    "display": False
                },
                "tooltip": {
                    "callbacks": {
                        "label": "function(context) { return context.raw.toFixed(1) + ' knots'; }"
                    }
                }
            },
            "scales": {
                "r": {
                    "beginAtZero": True,
                    "ticks": {
                        "display": False
                    },
                    "grid": {
                        "color": "rgba(0, 0, 0, 0.1)"
                    }
                }
            }
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
        
        # 風配図特有のオプション
        wind_rose_options = {
            "type": "polarArea",
            "options": {
                "elements": {
                    "arc": {
                        "borderWidth": 1,
                        "borderColor": "rgba(0, 0, 0, 0.1)"
                    }
                }
            }
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
