# -*- coding: utf-8 -*-
"""
Module for data connector between map layers and data sources.
This module provides functions for binding and data transformation between layers and data sources.
"""

from typing import Dict, List, Any, Optional, Union, Tuple, Set, Callable
import json
import uuid
import math
from datetime import datetime

from sailing_data_processor.reporting.elements.map.layers.base_layer import BaseMapLayer


class CourseElementsLayer(BaseMapLayer):
    """
    コース要素表示レイヤー
    
    セーリングコースの要素（マーク、ゲート、レイラインなど）を地図上に可視化するためのレイヤーを提供します。
    """
    
    def __init__(self, layer_id: Optional[str] = None, name: str = "コース", 
                description: str = "セーリングコース要素を表示", **kwargs):
        """
        初期化
        
        Parameters
        ----------
        layer_id : Optional[str], optional
            レイヤーID, by default None
        name : str, optional
            レイヤー名, by default "コース"
        description : str, optional
            レイヤーの説明, by default "セーリングコース要素を表示"
        **kwargs : dict
            追加のプロパティ
        """
        super().__init__(layer_id, name, description, **kwargs)
        
        # デフォルト設定
        self.set_property("course_type", kwargs.get("course_type", "windward_leeward"))  # windward_leeward, triangle, trapezoid, custom
        self.set_property("mark_size", kwargs.get("mark_size", 15))  # マークのサイズ
        self.set_property("mark_color", kwargs.get("mark_color", "#FF4500"))  # マークの色
        self.set_property("gate_color", kwargs.get("gate_color", "#4169E1"))  # ゲートの色
        self.set_property("start_color", kwargs.get("start_color", "#32CD32"))  # スタートラインの色
        self.set_property("finish_color", kwargs.get("finish_color", "#FF6347"))  # フィニッシュラインの色
        self.set_property("course_color", kwargs.get("course_color", "#808080"))  # コース線の色
        self.set_property("layline_color", kwargs.get("layline_color", "#FF8C00"))  # レイラインの色
        self.set_property("restricted_color", kwargs.get("restricted_color", "#FF0000"))  # 制限エリアの色
        
        # 表示設定
        self.set_property("show_marks", kwargs.get("show_marks", True))  # マークの表示
        self.set_property("show_gates", kwargs.get("show_gates", True))  # ゲートの表示
        self.set_property("show_start_finish", kwargs.get("show_start_finish", True))  # スタート/フィニッシュの表示
        self.set_property("show_course_lines", kwargs.get("show_course_lines", True))  # コース線の表示
        self.set_property("show_laylines", kwargs.get("show_laylines", False))  # レイラインの表示
        self.set_property("show_restricted", kwargs.get("show_restricted", False))  # 制限エリアの表示
        
        # マーク設定
        self.set_property("marks", kwargs.get("marks", []))  # マークの位置
        
        # レイライン設定
        self.set_property("wind_direction", kwargs.get("wind_direction", 0))  # 風向（度）
        self.set_property("twa_upwind", kwargs.get("twa_upwind", 45))  # 風上の艇の風に対する角度（度）
        self.set_property("twa_downwind", kwargs.get("twa_downwind", 150))  # 風下の艇の風に対する角度（度）
        
        # レイライン長さ
        self.set_property("layline_length", kwargs.get("layline_length", 0.5))  # レイラインの長さ（km）
        
        # 制限エリア
        self.set_property("restricted_areas", kwargs.get("restricted_areas", []))  # 制限エリア
    
    def set_course_type(self, course_type: str) -> None:
        """
        コースタイプを設定
        
        Parameters
        ----------
        course_type : str
            コースタイプ ("windward_leeward", "triangle", "trapezoid", "custom")
        """
        valid_types = ["windward_leeward", "triangle", "trapezoid", "custom"]
        if course_type in valid_types:
            self.set_property("course_type", course_type)
    
    def add_mark(self, lat: float, lng: float, name: str = "", color: str = None, 
                size: int = None, is_gate: bool = False, properties: Dict[str, Any] = None) -> int:
        """
        マークを追加
        
        Parameters
        ----------
        lat : float
            緯度
        lng : float
            経度
        name : str, optional
            マーク名, by default ""
        color : str, optional
            マーク色, by default None（レイヤーデフォルト）
        size : int, optional
            マークサイズ, by default None（レイヤーデフォルト）
        is_gate : bool, optional
            ゲートフラグ, by default False
        properties : Dict[str, Any], optional
            追加プロパティ, by default None
            
        Returns
        -------
        int
            追加されたマークのインデックス
        """
        marks = self.get_property("marks", [])
        
        # マークプロパティ
        mark = {
            "lat": lat,
            "lng": lng,
            "name": name,
            "color": color if color else self.get_property("mark_color" if not is_gate else "gate_color"),
            "size": size if size else self.get_property("mark_size"),
            "is_gate": is_gate
        }
        
        # 追加プロパティ
        if properties:
            mark.update(properties)
        
        # マークの追加
        marks.append(mark)
        self.set_property("marks", marks)
        
        return len(marks) - 1
    
    def add_gate(self, lat1: float, lng1: float, lat2: float, lng2: float, 
                name: str = "", color: str = None, properties: Dict[str, Any] = None) -> int:
        """
        ゲートを追加
        
        Parameters
        ----------
        lat1 : float
            左マーク緯度
        lng1 : float
            左マーク経度
        lat2 : float
            右マーク緯度
        lng2 : float
            右マーク経度
        name : str, optional
            ゲート名, by default ""
        color : str, optional
            ゲート色, by default None（レイヤーデフォルト）
        properties : Dict[str, Any], optional
            追加プロパティ, by default None
            
        Returns
        -------
        int
            追加されたゲートのインデックス（最初のマークのインデックス）
        """
        marks = self.get_property("marks", [])
        index = len(marks)
        
        gate_color = color if color else self.get_property("gate_color")
        
        # 左マーク
        left_mark = {
            "lat": lat1,
            "lng": lng1,
            "name": f"{name} (L)",
            "color": gate_color,
            "size": self.get_property("mark_size"),
            "is_gate": True,
            "gate_pair": index + 1
        }
        
        # 右マーク
        right_mark = {
            "lat": lat2,
            "lng": lng2,
            "name": f"{name} (R)",
            "color": gate_color,
            "size": self.get_property("mark_size"),
            "is_gate": True,
            "gate_pair": index
        }
        
        # 追加プロパティ
        if properties:
            left_mark.update(properties)
            right_mark.update(properties)
        
        # ゲートの追加
        marks.append(left_mark)
        marks.append(right_mark)
        self.set_property("marks", marks)
        
        return index
    
    def add_start_line(self, lat1: float, lng1: float, lat2: float, lng2: float, 
                      name: str = "スタート", color: str = None, properties: Dict[str, Any] = None) -> int:
        """
        スタートラインを追加
        
        Parameters
        ----------
        lat1 : float
            ピン側緯度
        lng1 : float
            ピン側経度
        lat2 : float
            コミッティ側緯度
        lng2 : float
            コミッティ側経度
        name : str, optional
            スタートライン名, by default "スタート"
        color : str, optional
            スタートライン色, by default None（レイヤーデフォルト）
        properties : Dict[str, Any], optional
            追加プロパティ, by default None
            
        Returns
        -------
        int
            追加されたスタートラインのインデックス（最初のマークのインデックス）
        """
        marks = self.get_property("marks", [])
        index = len(marks)
        
        start_color = color if color else self.get_property("start_color")
        
        # ピン側
        pin_mark = {
            "lat": lat1,
            "lng": lng1,
            "name": f"{name} (Pin)",
            "color": start_color,
            "size": self.get_property("mark_size"),
            "is_start": True,
            "start_pair": index + 1
        }
        
        # コミッティ側
        committee_mark = {
            "lat": lat2,
            "lng": lng2,
            "name": f"{name} (Committee)",
            "color": start_color,
            "size": self.get_property("mark_size"),
            "is_start": True,
            "start_pair": index
        }
        
        # 追加プロパティ
        if properties:
            pin_mark.update(properties)
            committee_mark.update(properties)
        
        # スタートラインの追加
        marks.append(pin_mark)
        marks.append(committee_mark)
        self.set_property("marks", marks)
        
        return index
    
    def add_finish_line(self, lat1: float, lng1: float, lat2: float, lng2: float, 
                       name: str = "フィニッシュ", color: str = None, properties: Dict[str, Any] = None) -> int:
        """
        フィニッシュラインを追加
        
        Parameters
        ----------
        lat1 : float
            ピン側緯度
        lng1 : float
            ピン側経度
        lat2 : float
            コミッティ側緯度
        lng2 : float
            コミッティ側経度
        name : str, optional
            フィニッシュライン名, by default "フィニッシュ"
        color : str, optional
            フィニッシュライン色, by default None（レイヤーデフォルト）
        properties : Dict[str, Any], optional
            追加プロパティ, by default None
            
        Returns
        -------
        int
            追加されたフィニッシュラインのインデックス（最初のマークのインデックス）
        """
        marks = self.get_property("marks", [])
        index = len(marks)
        
        finish_color = color if color else self.get_property("finish_color")
        
        # ピン側
        pin_mark = {
            "lat": lat1,
            "lng": lng1,
            "name": f"{name} (Pin)",
            "color": finish_color,
            "size": self.get_property("mark_size"),
            "is_finish": True,
            "finish_pair": index + 1
        }
        
        # コミッティ側
        committee_mark = {
            "lat": lat2,
            "lng": lng2,
            "name": f"{name} (Committee)",
            "color": finish_color,
            "size": self.get_property("mark_size"),
            "is_finish": True,
            "finish_pair": index
        }
        
        # 追加プロパティ
        if properties:
            pin_mark.update(properties)
            committee_mark.update(properties)
        
        # フィニッシュラインの追加
        marks.append(pin_mark)
        marks.append(committee_mark)
        self.set_property("marks", marks)
        
        return index
    
    def add_restricted_area(self, coordinates: List[Tuple[float, float]], name: str = "制限エリア", 
                           color: str = None, properties: Dict[str, Any] = None) -> int:
        """
        制限エリアを追加
        
        Parameters
        ----------
        coordinates : List[Tuple[float, float]]
            座標リスト [(lat1, lng1), (lat2, lng2), ...]
        name : str, optional
            エリア名, by default "制限エリア"
        color : str, optional
            エリア色, by default None（レイヤーデフォルト）
        properties : Dict[str, Any], optional
            追加プロパティ, by default None
            
        Returns
        -------
        int
            追加された制限エリアのインデックス
        """
        restricted_areas = self.get_property("restricted_areas", [])
        
        # エリアプロパティ
        area = {
            "coordinates": coordinates,
            "name": name,
            "color": color if color else self.get_property("restricted_color")
        }
        
        # 追加プロパティ
        if properties:
            area.update(properties)
        
        # 制限エリアの追加
        restricted_areas.append(area)
        self.set_property("restricted_areas", restricted_areas)
        
        return len(restricted_areas) - 1
    
    def set_wind_direction(self, direction: float) -> None:
        """
        風向を設定
        
        Parameters
        ----------
        direction : float
            風向（度）
        """
        self.set_property("wind_direction", float(direction) % 360)
    
    def set_twa(self, upwind: float = None, downwind: float = None) -> None:
        """
        風に対する角度を設定
        
        Parameters
        ----------
        upwind : float, optional
            風上の艇の風に対する角度（度）, by default None
        downwind : float, optional
            風下の艇の風に対する角度（度）, by default None
        """
        if upwind is not None:
            self.set_property("twa_upwind", max(0, min(90, float(upwind))))
        if downwind is not None:
            self.set_property("twa_downwind", max(90, min(180, float(downwind))))
    
    def clear_marks(self) -> None:
        """マークをすべて削除"""
        self.set_property("marks", [])
    
    def clear_restricted_areas(self) -> None:
        """制限エリアをすべて削除"""
        self.set_property("restricted_areas", [])
    
    def get_bounds(self) -> Optional[Tuple[Tuple[float, float], Tuple[float, float]]]:
        """
        レイヤーの境界ボックスを取得
        
        Returns
        -------
        Optional[Tuple[Tuple[float, float], Tuple[float, float]]]
            ((min_lat, min_lng), (max_lat, max_lng))の形式の境界ボックス
            または境界が定義できない場合はNone
        """
        marks = self.get_property("marks", [])
        restricted_areas = self.get_property("restricted_areas", [])
        
        if not marks and not restricted_areas:
            return None
        
        # 初期値
        min_lat = min_lng = float('inf')
        max_lat = max_lng = float('-inf')
        
        # マークの座標範囲を計算
        for mark in marks:
            if 'lat' in mark and 'lng' in mark:
                min_lat = min(min_lat, mark['lat'])
                min_lng = min(min_lng, mark['lng'])
                max_lat = max(max_lat, mark['lat'])
                max_lng = max(max_lng, mark['lng'])
        
        # 制限エリアの座標範囲を計算
        for area in restricted_areas:
            if 'coordinates' in area:
                for lat, lng in area['coordinates']:
                    min_lat = min(min_lat, lat)
                    min_lng = min(min_lng, lng)
                    max_lat = max(max_lat, lat)
                    max_lng = max(max_lng, lng)
        
        if min_lat == float('inf'):
            return None
        
        return ((min_lat, min_lng), (max_lat, max_lng))
    
    def render_layer(self, map_var: str = "map") -> str:
        """
        レイヤーのレンダリングコードを生成
        
        Parameters
        ----------
        map_var : str, optional
            マップ変数名, by default "map"
            
        Returns
        -------
        str
            レイヤーをレンダリングするJavaScriptコード
        """
        # レイヤー設定
        layer_id = self.layer_id
        layer_var = f"layer_{layer_id}"
        
        # レイヤープロパティ
        mark_size = self.get_property("mark_size", 15)
        mark_color = self.get_property("mark_color", "#FF4500")
        gate_color = self.get_property("gate_color", "#4169E1")
        start_color = self.get_property("start_color", "#32CD32")
        finish_color = self.get_property("finish_color", "#FF6347")
        course_color = self.get_property("course_color", "#808080")
        layline_color = self.get_property("layline_color", "#FF8C00")
        restricted_color = self.get_property("restricted_color", "#FF0000")
        
        # 表示設定
        show_marks = self.get_property("show_marks", True)
        show_gates = self.get_property("show_gates", True)
        show_start_finish = self.get_property("show_start_finish", True)
        show_course_lines = self.get_property("show_course_lines", True)
        show_laylines = self.get_property("show_laylines", False)
        show_restricted = self.get_property("show_restricted", False)
        
        # 風向設定
        wind_direction = self.get_property("wind_direction", 0)
        twa_upwind = self.get_property("twa_upwind", 45)
        twa_downwind = self.get_property("twa_downwind", 150)
        layline_length = self.get_property("layline_length", 0.5)
        
        # マークと制限エリアのJSON
        marks = self.get_property("marks", [])
        restricted_areas = self.get_property("restricted_areas", [])
        
        marks_json = json.dumps(marks)
        restricted_json = json.dumps(restricted_areas)
        
        # JavaScript コード - 構文エラーを避けるため簡略化
        code = f"""
            // コース要素レイヤーの作成 {layer_id}
            {layer_var} = (function() {{
                // コース設定
                var courseConfig = {{
                    markSize: {mark_size},
                    markColor: '{mark_color}',
                    gateColor: '{gate_color}',
                    startColor: '{start_color}',
                    finishColor: '{finish_color}',
                    courseColor: '{course_color}',
                    laylineColor: '{layline_color}',
                    restrictedColor: '{restricted_color}',
                    showMarks: {str(show_marks).lower()},
                    showGates: {str(show_gates).lower()},
                    showStartFinish: {str(show_start_finish).lower()},
                    showCourseLines: {str(show_course_lines).lower()},
                    showLaylines: {str(show_laylines).lower()},
                    showRestricted: {str(show_restricted).lower()},
                    windDirection: {wind_direction},
                    twaUpwind: {twa_upwind},
                    twaDownwind: {twa_downwind},
                    laylineLength: {layline_length}
                }};
                
                // マークデータ
                var marksData = {marks_json};
                var restrictedAreas = {restricted_json};
                
                // レイヤーグループの作成
                var layerGroup = L.layerGroup();
                
                // レイヤー情報を保存
                layerGroup.id = '{layer_id}';
                layerGroup.name = '{self.name}';
                layerGroup.type = 'course_elements';
                
                // マップに追加
                layerGroup.addTo({map_var});
                
                return layerGroup;
            }})();
        """
        
        return code
