# -*- coding: utf-8 -*-
"""
タイムライン要素モジュール

このモジュールは、時系列データを視覚化するためのタイムライン要素を提供します。
"""

from typing import Dict, List, Any, Optional, Union
import json
import uuid
import html

from sailing_data_processor.reporting.elements.base_element import BaseElement
from sailing_data_processor.reporting.templates.template_model import ElementType

class EventTimelineElement(BaseElement):
    """
    イベントタイムライン要素
    
    時系列に沿ったイベントを表示するためのタイムライン要素です。
    """
    
    def __init__(self, element_id: str, title: str = "イベントタイムライン", **kwargs):
        """
        コンストラクタ
        
        Parameters
        ----------
        element_id : str
            要素ID
        title : str, optional
            タイトル, by default "イベントタイムライン"
        **kwargs : dict
            追加のプロパティ
        """
        super().__init__(element_id, title, **kwargs)
        self.element_type = ElementType.TIMELINE
        self.events = []
        
    def add_event(self, time: str, event_type: str, content: str, group: Optional[str] = None):
        """
        イベントを追加
        
        Parameters
        ----------
        time : str
            時間（ISO 8601形式推奨）
        event_type : str
            イベントタイプ（"tack", "gybe", "mark_rounding", "wind_shift"など）
        content : str
            イベント内容
        group : Optional[str], optional
            グループ名, by default None
        """
        self.events.append({
            "time": time,
            "event": event_type,
            "content": content,
            "group": group
        })
    
    def render(self, context: Dict[str, Any]) -> str:
        """
        要素をHTMLとしてレンダリング
        
        Parameters
        ----------
        context : Dict[str, Any]
            レンダリングコンテキスト
            
        Returns
        -------
        str
            HTML文字列
        """
        # スタイルの構成
        height = self.get_property("height", "400px")
        width = self.get_property("width", "100%")
        css_style = f"height: {height}; width: {width};"
        
        # データの準備
        data = self.events
        
        # データソースが指定されている場合はそちらを使用
        if self.data_source and self.data_source in context:
            data = context[self.data_source]
        
        # データがない場合は通知メッセージを表示
        if not data:
            return f'<div id="{self.element_id}" class="report-message warning">表示するデータがありません</div>'
        
        # タイムラインのキーマッピング
        time_key = self.get_property("time_key", "time")
        event_key = self.get_property("event_key", "event")
        group_key = self.get_property("group_key", "group")
        content_key = self.get_property("content_key", "content")
        
        # イベントタイプごとの色の設定
        event_colors = self.get_property("event_colors", {
            "tack": "blue",
            "gybe": "green",
            "mark_rounding": "red",
            "wind_shift": "purple",
            "default": "gray"
        })
        
        # 表示オプション
        show_groups = self.get_property("show_groups", True)
        show_tooltips = self.get_property("show_tooltips", True)
        cluster_events = self.get_property("cluster_events", True)
        
        # データをJSON文字列に変換
        data_json = json.dumps(data)
        
        # タイムライン設定をJSON文字列に変換
        timeline_config = {
            "time_key": time_key,
            "event_key": event_key,
            "group_key": group_key,
            "content_key": content_key,
            "event_colors": event_colors,
            "show_groups": show_groups,
            "show_tooltips": show_tooltips,
            "cluster_events": cluster_events
        }
        
        timeline_config_json = json.dumps(timeline_config)
        
        # タイムラインの一意なID
        timeline_id = f"timeline_{self.element_id}_{str(uuid.uuid4())[:8]}"
        
        # タイムライン要素のレンダリング
        html_content = f'''
        <div id="{self.element_id}" class="report-timeline-container" style="{css_style}">
            <!-- Timeline CSS -->
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/vis-timeline@7.7.0/dist/vis-timeline-graph2d.min.css" />
            
            <h3 class="report-element-title">{html.escape(self.title)}</h3>
            <div id="{timeline_id}" class="report-timeline"></div>
            
            <!-- Timeline JavaScript -->
            <script src="https://cdn.jsdelivr.net/npm/vis-timeline@7.7.0/dist/vis-timeline-graph2d.min.js"></script>
            <script>
                (function() {{
                    // データの取得
                    const timelineData = {data_json};
                    const config = {timeline_config_json};
                    
                    // タイムラインの設定
                    const container = document.getElementById('{timeline_id}');
                    
                    // アイテムの準備
                    const items = new vis.DataSet(
                        timelineData.map((item, index) => {{
                            const event_type = item[config.event_key] || 'default';
                            const color = config.event_colors[event_type] || config.event_colors.default;
                            
                            return {{
                                id: index,
                                content: item[config.content_key] || '',
                                start: item[config.time_key],
                                group: config.show_groups ? (item[config.group_key] || 'default') : undefined,
                                className: `event-${event_type}`,
                                style: `background-color: ${{color}}; color: white; padding: 5px; border-radius: 3px;`
                            }};
                        }})
                    );
                    
                    // グループの準備
                    let groups = null;
                    if (config.show_groups) {{
                        const groupSet = new Set();
                        timelineData.forEach(item => {{
                            const group = item[config.group_key] || 'default';
                            groupSet.add(group);
                        }});
                        
                        groups = Array.from(groupSet).map(group => ({{
                            id: group,
                            content: group
                        }}));
                    }}
                    
                    // オプションの設定
                    const options = {{
                        height: '100%',
                        maxHeight: '{height}',
                        stack: true,
                        showCurrentTime: false,
                        zoomMin: 1000 * 60, // 1分
                        zoomMax: 1000 * 60 * 60 * 24 * 30, // 30日
                        tooltip: {{
                            followMouse: true,
                            overflowMethod: 'cap'
                        }},
                        cluster: config.cluster_events ? {{
                            maxItems: 3,
                            clusterCriteria: (item1, item2) => {{
                                return item1.content === item2.content;
                            }}
                        }} : false
                    }};
                    
                    // タイムラインの作成
                    const timeline = new vis.Timeline(container, items, groups, options);
                    
                    // イベントハンドラの設定
                    timeline.on('click', (properties) => {{
                        const item = items.get(properties.item);
                        if (item) {{
                            console.log('Selected item:', item);
                            // ここに選択時の処理を追加
                        }}
                    }});
                }})();
            </script>
        </div>
        '''
        
        return html_content


class ParameterTimelineElement(BaseElement):
    """
    パラメータタイムライン要素
    
    時系列パラメータをグラフ形式で表示するためのタイムライン要素です。
    """
    
    def __init__(self, element_id: str, title: str = "パラメータタイムライン", **kwargs):
        """
        コンストラクタ
        
        Parameters
        ----------
        element_id : str
            要素ID
        title : str, optional
            タイトル, by default "パラメータタイムライン"
        **kwargs : dict
            追加のプロパティ
        """
        super().__init__(element_id, title, **kwargs)
        self.element_type = ElementType.TIMELINE
        self.data_points = []
        
    def add_data_point(self, time: str, value: float, label: Optional[str] = None):
        """
        データポイントを追加
        
        Parameters
        ----------
        time : str
            時間（ISO 8601形式推奨）
        value : float
            値
        label : Optional[str], optional
            ラベル, by default None
        """
        self.data_points.append({
            "time": time,
            "value": value,
            "label": label
        })
    
    def render(self, context: Dict[str, Any]) -> str:
        """
        要素をHTMLとしてレンダリング
        
        Parameters
        ----------
        context : Dict[str, Any]
            レンダリングコンテキスト
            
        Returns
        -------
        str
            HTML文字列
        """
        # スタイルの構成
        height = self.get_property("height", "300px")
        width = self.get_property("width", "100%")
        css_style = f"height: {height}; width: {width};"
        
        # データの準備
        data = self.data_points
        
        # データソースが指定されている場合はそちらを使用
        if self.data_source and self.data_source in context:
            data = context[self.data_source]
        
        # データがない場合は通知メッセージを表示
        if not data:
            return f'<div id="{self.element_id}" class="report-message warning">表示するデータがありません</div>'
        
        # パラメータのキーマッピング
        time_key = self.get_property("time_key", "time")
        value_key = self.get_property("value_key", "value")
        label_key = self.get_property("label_key", "label")
        
        # グラフの設定
        line_color = self.get_property("line_color", "#3366CC")
        fill_color = self.get_property("fill_color", "rgba(51, 102, 204, 0.2)")
        show_points = self.get_property("show_points", True)
        show_labels = self.get_property("show_labels", False)
        interpolation = self.get_property("interpolation", "linear")  # linear, step, none
        
        # データをJSON文字列に変換
        data_json = json.dumps(data)
        
        # グラフ設定をJSON文字列に変換
        graph_config = {
            "time_key": time_key,
            "value_key": value_key,
            "label_key": label_key,
            "line_color": line_color,
            "fill_color": fill_color,
            "show_points": show_points,
            "show_labels": show_labels,
            "interpolation": interpolation
        }
        
        graph_config_json = json.dumps(graph_config)
        
        # グラフの一意なID
        graph_id = f"graph_{self.element_id}_{str(uuid.uuid4())[:8]}"
        
        # グラフ要素のレンダリング
        html_content = f'''
        <div id="{self.element_id}" class="report-parameter-timeline" style="{css_style}">
            <!-- Graph CSS -->
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/vis-timeline@7.7.0/dist/vis-timeline-graph2d.min.css" />
            
            <h3 class="report-element-title">{html.escape(self.title)}</h3>
            <div id="{graph_id}" class="report-parameter-graph"></div>
            
            <!-- Graph JavaScript -->
            <script src="https://cdn.jsdelivr.net/npm/vis-timeline@7.7.0/dist/vis-timeline-graph2d.min.js"></script>
            <script>
                (function() {{
                    // データの取得
                    const graphData = {data_json};
                    const config = {graph_config_json};
                    
                    // グラフの設定
                    const container = document.getElementById('{graph_id}');
                    
                    // アイテムの準備
                    const items = new vis.DataSet(
                        graphData.map((item, index) => {{
                            return {{
                                x: new Date(item[config.time_key]),
                                y: item[config.value_key],
                                label: config.show_labels ? (item[config.label_key] || '') : undefined
                            }};
                        }})
                    );
                    
                    // グループの設定
                    const groups = new vis.DataSet([{{
                        id: 0,
                        content: '{html.escape(self.title)}',
                        style: `stroke: ${{config.line_color}}; fill: ${{config.fill_color}};`
                    }}]);
                    
                    // オプションの設定
                    const options = {{
                        height: '{height}',
                        style: config.show_points ? 'points' : 'line',
                        drawPoints: config.show_points,
                        shaded: {{
                            orientation: 'bottom'
                        }},
                        interpolation: {{
                            parametrization: config.interpolation
                        }},
                        legend: true,
                        dataAxis: {{
                            showMinorLabels: true
                        }},
                        tooltip: {{
                            followMouse: true
                        }}
                    }};
                    
                    // グラフの作成
                    const graph2d = new vis.Graph2d(container, items, groups, options);
                    
                    // ウィンドウリサイズ時の調整
                    window.addEventListener('resize', () => {{
                        graph2d.redraw();
                    }});
                }})();
            </script>
        </div>
        '''
        
        return html_content