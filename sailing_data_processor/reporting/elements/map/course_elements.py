"""
Module for data connector between map layers and data sources.
This module provides functions for binding and data transformation between layers and data sources.
"""

from typing import Dict, List, Any, Optional, Union, Tuple
import json
import uuid
import os
import pathlib

from sailing_data_processor.reporting.elements.visualizations.map_elements import StrategyPointLayerElement
from sailing_data_processor.reporting.templates.template_model import ElementType, ElementModel


class CourseElementsLayer(StrategyPointLayerElement):
    """
    コース要素レイヤー
    
    セーリングコース上のマーク、ライン、レイライン、戦略ポイントを管理します。
    現在のコース状態を視覚化するためのレイヤーです。
    """
    
    def __init__(self, model: Optional[ElementModel] = None, **kwargs):
        """
        初期化
        
        Parameters
        ----------
        model : Optional[ElementModel], optional
            モデル設定, by default None
        **kwargs : dict
            追加パラメータとしてレイヤーに渡す設定オプション
        """
        super().__init__(model, **kwargs)
        
        # マーク設定の初期化
        self.set_property("marks", self.get_property("marks", []))
        self.set_property("course_shape", self.get_property("course_shape", "windward_leeward"))
        self.set_property("start_line", self.get_property("start_line", {}))
        self.set_property("finish_line", self.get_property("finish_line", {}))
        
        # レイライン設定の初期化
        self.set_property("show_laylines", self.get_property("show_laylines", True))
        self.set_property("tacking_angle", self.get_property("tacking_angle", 90))
        self.set_property("layline_style", self.get_property("layline_style", {
            "color": "rgba(255, 0, 0, 0.6)",
            "weight": 2,
            "dashArray": "5,5"
        }))
        
        # マップID設定
        self.map_id = self.get_property("map_id", f"course_map_{uuid.uuid4().hex[:8]}")
        
    def render_html(self, data: Any = None) -> str:
        """
        HTML表示用のレンダリング
        
        Parameters
        ----------
        data : Any, optional
            表示するデータ, by default None
            
        Returns
        -------
        str
            HTML文字列
        """
        # マップ設定
        center_auto = self.get_property("center_auto", True)
        center = self.get_property("center", [35.6585, 139.7454])
        zoom_level = self.get_property("zoom_level", 13)
        
        # コース設定
        marks = self.get_property("marks", [])
        course_shape = self.get_property("course_shape", "windward_leeward")
        start_line = self.get_property("start_line", {})
        finish_line = self.get_property("finish_line", {})
        
        # レイライン設定
        show_laylines = self.get_property("show_laylines", True)
        tacking_angle = self.get_property("tacking_angle", 90)
        layline_style = self.get_property("layline_style", {
            "color": "rgba(255, 0, 0, 0.6)",
            "weight": 2,
            "dashArray": "5,5"
        })
        
        # 戦略設定
        strategy_points = self.get_property("strategy_points", [])
        optimal_route = self.get_property("optimal_route", {})
        risk_areas = self.get_property("risk_areas", [])
        
        # マップの表示設定
        map_type = self.get_property("map_type", "osm")
        show_track = self.get_property("show_track", True)
        track_color = self.get_property("track_color", "rgba(54, 162, 235, 0.8)")
        track_width = self.get_property("track_width", 3)
        
        # ポイントアイコン設定
        point_icons = self.get_property("point_icons", {
            "mark": {"color": "red", "icon": "map-marker-alt"},
            "start": {"color": "green", "icon": "flag"},
            "finish": {"color": "blue", "icon": "flag-checkered"},
            "advantage": {"color": "green", "icon": "thumbs-up"},
            "caution": {"color": "orange", "icon": "exclamation-triangle"},
            "information": {"color": "blue", "icon": "info-circle"},
            "default": {"color": "gray", "icon": "map-marker-alt"}
        })
        
        # データをJSON形式に変換
        data_json = json.dumps(data)
        
        # コース設定をJSON形式に変換
        course_config = {
            "marks": marks,
            "course_shape": course_shape,
            "start_line": start_line,
            "finish_line": finish_line,
            "show_laylines": show_laylines,
            "tacking_angle": tacking_angle,
            "layline_style": layline_style,
            "strategy_points": strategy_points,
            "optimal_route": optimal_route,
            "risk_areas": risk_areas
        }
        course_config_json = json.dumps(course_config)
        
        # マップ設定をJSON形式に変換
        map_config = {
            "map_type": map_type,
            "center_auto": center_auto,
            "center": center,
            "zoom_level": zoom_level,
            "show_track": show_track,
            "track_color": track_color,
            "track_width": track_width,
            "point_icons": point_icons
        }
        map_config_json = json.dumps(map_config)
        
        # 静的ファイルのパスを取得
        module_path = pathlib.Path(__file__).parent.parent.parent.parent
        js_path = module_path / 'reporting' / 'static' / 'js' / 'course_elements.js'
        
        # HTMLテンプレート
        html_content = f'''
        <div id="{self.map_id}" class="course-map-container" style="width: 100%; height: 500px;">
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css" />
            <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
            <script src="https://unpkg.com/leaflet-geometryutil@0.9.3/dist/leaflet.geometryutil.js"></script>
            
            <style>
                .course-map-container {{
                    border: 1px solid #ccc;
                    border-radius: 5px;
                    overflow: hidden;
                }}
                .course-mark-icon-wrapper {{
                    background: none;
                    border: none;
                }}
                .course-mark-icon {{
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    width: 32px;
                    height: 32px;
                    border-radius: 50%;
                    color: white;
                    box-shadow: 0 1px 5px rgba(0,0,0,0.4);
                }}
                .course-popup {{
                    min-width: 150px;
                }}
                .course-popup h4 {{
                    margin: 0 0 5px 0;
                    padding-bottom: 5px;
                    border-bottom: 1px solid #eee;
                }}
                .course-popup p {{
                    margin: 5px 0;
                }}
            </style>
            
            <script>
                (function() {{
                    // マップIDの設定
                    var mapId = "{self.map_id}";
                    
                    // コースデータ
                    var courseData = {data_json};
                    
                    // コース設定
                    var courseConfig = {course_config_json};
                    
                    // マップ設定
                    var mapConfig = {map_config_json};
                    
                    // JavaScriptファイルの埋め込み
                    {self._load_js_file(js_path)}
                }})();
            </script>
        </div>
        '''
        
        return html_content

    def _load_js_file(self, js_path: pathlib.Path) -> str:
        """
        JavaScriptファイルを読み込む
        
        Parameters
        ----------
        js_path : pathlib.Path
            JavaScriptファイルのパス
            
        Returns
        -------
        str
            JavaScriptコード
        """
        try:
            if js_path.exists():
                with open(js_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                # ファイルが存在しない場合は警告ログを出力
                import logging
                logging.warning(f"JavaScript file not found: {js_path}")
                return "console.error('JavaScript file for course elements not found.');"
        except Exception as e:
            # エラーが発生した場合は警告ログを出力
            import logging
            logging.error(f"Error loading JavaScript file: {e}")
            return f"console.error('Error loading JavaScript file: {e}');"
