# -*- coding: utf-8 -*-
"""
sailing_data_processor.reporting.elements.visualizations.timeline_elements

タイムライン要素を提供するモジュールです。
イベントタイムライン、パラメータタイムライン、セグメント比較、動的データビューアなどの
時間関連の可視化要素を実装します。
"""

from typing import Dict, List, Any, Optional, Union, Tuple
import json
import html
import uuid

from sailing_data_processor.reporting.elements.visualizations.base_chart import BaseChartElement
from sailing_data_processor.reporting.templates.template_model import ElementType, ElementModel


class EventTimelineElement(BaseChartElement):
    """
    イベントタイムライン要素
    
    タッキング、ジャイビングなどのイベントを時間軸上に表示するための要素です。
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
            kwargs['chart_type'] = "event_timeline"
        
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
            "https://cdn.jsdelivr.net/npm/vis-timeline@7.7.0/standalone/umd/vis-timeline-graph2d.min.js",
            "https://cdn.jsdelivr.net/npm/moment@2.29.1/moment.min.js"
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
            return f'<div id="{self.element_id}" class="report-timeline-empty">タイムラインデータがありません</div>'
        
        # CSSスタイルの取得
        css_style = self.get_css_styles()
        width, height = self.get_chart_dimensions()
        
        # タイムラインの設定
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
 {
            "tack": "blue",
            "gybe": "green",
            "mark_rounding": "red",
            "wind_shift": "purple",
            "default": "gray"}
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
 {
            "time_key": time_key,
            "event_key": event_key,
            "group_key": group_key,
            "content_key": content_key,
            "event_colors": event_colors,
            "show_groups": show_groups,
            "show_tooltips": show_tooltips,
            "cluster_events": cluster_events}
        
        timeline_config_json = json.dumps(timeline_config)
        
        # タイムラインの一意なID
        timeline_id = f"timeline_{self.element_id}_{str(uuid.uuid4())[:8]}"
        
        # タイムライン要素のレンダリング
        html_content = f'''
        <div id="{self.element_id}" class="report-timeline-container" style="{css_style}">
            <!-- Timeline CSS -->
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/vis-timeline@7.7.0/dist/vis-timeline-graph2d.min.css" />
            
            <style>
                .vis-item {{
                    border-color: #3498db;
                    background-color: #AED6F1;
                    font-size: 12px;
                }}
                
                .vis-timeline {{
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    background-color: #fafafa;
                }}
                
                .vis-panel.vis-center {{
                    border-left: 1px solid #ddd;
                    border-right: 1px solid #ddd;
                }}
                
                .vis-event-tooltip {{
                    background-color: rgba(255, 255, 255, 0.95);
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    padding: 8px;
                    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
                    font-size: 12px;
                    max-width: 300px;
                }}
                
                .vis-custom-time {{
                    background-color: #FF5722;
                }}
            </style>
            
            <div id="{timeline_id}" style="width: {width}; height: {height};"></div>
            
            <script>
                (function() {{
                    // タイムラインデータ
                    var timelineData = {data_json};
                    var timelineConfig = {timeline_config_json};
                    
                    // タイムライン初期化
                    window.addEventListener('load', function() {{
                        // グループとアイテムのデータを準備
                        var groups = new vis.DataSet();
                        var items = new vis.DataSet();
                        
                        // グループの追加（イベントタイプ別）
                        var groupIds = [];
                        var groupSets = new Set();
                        
                        // データ形式に応じて処理
                        if (Array.isArray(timelineData)) {{
                            // 配列形式の場合
                            for (var i = 0; i < timelineData.length; i++) {{
                                var event = timelineData[i];
                                var eventType = event[timelineConfig.event_key] || "default";
                                var group = timelineConfig.show_groups ? (event[timelineConfig.group_key] || eventType) : "events";
                                
                                // グループが未登録の場合は追加
                                if (!groupSets.has(group)) {{
                                    groupSets.add(group);
                                    groupIds.push(group);
                                    
                                    groups.add({{
                                        id: group,
                                        content: group,
                                        title: group
                                    }});
                                }}
                                
                                // イベント時間の取得
                                var eventTime = event[timelineConfig.time_key];
                                if (!eventTime) continue;
                                
                                // 日時形式に変換
                                var time = null;
                                if (typeof eventTime === 'string') {{
                                    time = moment(eventTime).toDate();
                                }} else if (typeof eventTime === 'number') {{
                                    // Unixタイムスタンプの場合（秒単位）
                                    time = moment.unix(eventTime).toDate();
                                }}
                                
                                if (!time) continue;
                                
                                // コンテンツの生成
                                var content = event[timelineConfig.content_key] || eventType;
                                
                                // イベントの色を決定
                                var eventColor = timelineConfig.event_colors[eventType] || timelineConfig.event_colors.default;
                                
                                // ツールチップの生成
                                var tooltip = '';
                                if (timelineConfig.show_tooltips) {{
                                    tooltip = '<div>';
                                    tooltip += '<div><strong>イベント:</strong> ' + eventType + '</div>';
                                    tooltip += '<div><strong>時間:</strong> ' + moment(time).format('YYYY-MM-DD HH:mm:ss') + '</div>';
                                    
                                    // その他の情報を追加
                                    for (var key in event) {{
                                        if (key !== timelineConfig.time_key && 
                                            key !== timelineConfig.event_key && 
                                            key !== timelineConfig.group_key && 
                                            key !== timelineConfig.content_key) {{
                                            tooltip += '<div><strong>' + key + ':</strong> ' + event[key] + '</div>';
                                        }}
                                    }}
                                    
                                    tooltip += '</div>';
                                }}
                                
                                // イベントアイテムを追加
                                items.add({{
                                    id: 'item_' + i,
                                    group: group,
                                    content: content,
                                    title: tooltip,
                                    start: time,
                                    type: 'box',
                                    style: 'background-color: ' + eventColor + '; border-color: ' + eventColor + ';'
                                }});
                            }}
                        }} else if (typeof timelineData === 'object' && timelineData.events) {{
                            // オブジェクト形式の場合
                            for (var i = 0; i < timelineData.events.length; i++) {{
                                var event = timelineData.events[i];
                                var eventType = event[timelineConfig.event_key] || "default";
                                var group = timelineConfig.show_groups ? (event[timelineConfig.group_key] || eventType) : "events";
                                
                                // グループが未登録の場合は追加
                                if (!groupSets.has(group)) {{
                                    groupSets.add(group);
                                    groupIds.push(group);
                                    
                                    groups.add({{
                                        id: group,
                                        content: group,
                                        title: group
                                    }});
                                }}
                                
                                // イベント時間の取得
                                var eventTime = event[timelineConfig.time_key];
                                if (!eventTime) continue;
                                
                                // 日時形式に変換
                                var time = null;
                                if (typeof eventTime === 'string') {{
                                    time = moment(eventTime).toDate();
                                }} else if (typeof eventTime === 'number') {{
                                    // Unixタイムスタンプの場合（秒単位）
                                    time = moment.unix(eventTime).toDate();
                                }}
                                
                                if (!time) continue;
                                
                                // コンテンツの生成
                                var content = event[timelineConfig.content_key] || eventType;
                                
                                // イベントの色を決定
                                var eventColor = timelineConfig.event_colors[eventType] || timelineConfig.event_colors.default;
                                
                                // ツールチップの生成
                                var tooltip = '';
                                if (timelineConfig.show_tooltips) {{
                                    tooltip = '<div>';
                                    tooltip += '<div><strong>イベント:</strong> ' + eventType + '</div>';
                                    tooltip += '<div><strong>時間:</strong> ' + moment(time).format('YYYY-MM-DD HH:mm:ss') + '</div>';
                                    
                                    // その他の情報を追加
                                    for (var key in event) {{
                                        if (key !== timelineConfig.time_key && 
                                            key !== timelineConfig.event_key && 
                                            key !== timelineConfig.group_key && 
                                            key !== timelineConfig.content_key) {{
                                            tooltip += '<div><strong>' + key + ':</strong> ' + event[key] + '</div>';
                                        }}
                                    }}
                                    
                                    tooltip += '</div>';
                                }}
                                
                                // イベントアイテムを追加
                                items.add({{
                                    id: 'item_' + i,
                                    group: group,
                                    content: content,
                                    title: tooltip,
                                    start: time,
                                    type: 'box',
                                    style: 'background-color: ' + eventColor + '; border-color: ' + eventColor + ';'
                                }});
                            }}
                        }}
                        
                        // グループが空の場合はデフォルトグループを追加
                        if (groups.length === 0) {{
                            groups.add({{
                                id: 'events',
                                content: 'イベント',
                                title: 'イベント'
                            }});
                        }}
                        
                        // タイムラインオプション
                        var options = {{
                            height: '100%',
                            margin: {{
                                item: 10,
                                axis: 5
                            }},
                            zoomMin: 1000 * 60,  // 1分
                            zoomMax: 1000 * 60 * 60 * 24 * 30,  // 30日
                            orientation: 'top',
                            showCurrentTime: false,
                            groupOrder: 'content',
                            groupHeightMode: 'auto',
                            cluster: timelineConfig.cluster_events ? {{
                                maxItems: 5,
                                clusterCriteria: function(item1, item2) {{
                                    return Math.abs(item1.start - item2.start) < 10000; // 10秒以内
                                }}
                            }} : false
                        }};
                        
                        // タイムラインを作成
                        var timeline = new vis.Timeline(document.getElementById('{timeline_id}'), items, groups, options);
                        
                        // タイムラインサイズの調整
                        window.addEventListener('resize', function() {{
                            timeline.redraw();
                        }});
                    }});
                }})();
            </script>
        </div>
        '''
        
        return html_content


class ParameterTimelineElement(BaseChartElement):
    """
    パラメータタイムライン要素
    
    速度、方向、風速などのパラメータの時系列変化を表示するための要素です。
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
            kwargs['chart_type'] = "parameter_timeline"
        
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
            "https://cdn.jsdelivr.net/npm/moment@2.29.1/moment.min.js",
            "https://cdn.jsdelivr.net/npm/chartjs-adapter-moment@1.0.0/dist/chartjs-adapter-moment.min.js",
            "https://cdn.jsdelivr.net/npm/hammerjs@2.0.8/hammer.min.js",
            "https://cdn.jsdelivr.net/npm/chartjs-plugin-zoom@1.2.1/dist/chartjs-plugin-zoom.min.js"
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
            return f'<div id="{self.element_id}" class="report-chart-empty">パラメータタイムラインデータがありません</div>'
        
        # CSSスタイルの取得
        css_style = self.get_css_styles()
        width, height = self.get_chart_dimensions()
        
        # パラメータと時間のキーを取得
        time_key = self.get_property("time_key", "time")
        parameters = self.get_property("parameters", [])
        
        # 自動パラメータ検出の設定
        auto_detect = self.get_property("auto_detect", True)
        excluded_keys = self.get_property("excluded_keys", [time_key, "lat", "lng", "latitude", "longitude"])
        
        # 表示オプション
        show_points = self.get_property("show_points", True)
        point_radius = self.get_property("point_radius", 2)
        brush_selection = self.get_property("brush_selection", True)
        
        # データをJSON文字列に変換
        data_json = json.dumps(data)
        
        # タイムライン設定をJSON文字列に変換
        timeline_config = {
            "time_key": time_key,
            "parameters": parameters,
            "auto_detect": auto_detect,
            "excluded_keys": excluded_keys,
            "show_points": show_points,
            "point_radius": point_radius,
            "brush_selection": brush_selection
 {
            "time_key": time_key,
            "parameters": parameters,
            "auto_detect": auto_detect,
            "excluded_keys": excluded_keys,
            "show_points": show_points,
            "point_radius": point_radius,
            "brush_selection": brush_selection}
        
        timeline_config_json = json.dumps(timeline_config)
        
        # チャートの一意なID
        chart_id = f"chart_{self.element_id}_{str(uuid.uuid4())[:8]}"
        
        # パラメータタイムライン要素のレンダリング
        html_content = f'''
        <div id="{self.element_id}" class="report-chart-container" style="{css_style}">
            <div class="report-chart-wrapper" style="width: {width}; height: {height}; position: relative;">
                <canvas id="{chart_id}" class="report-chart"></canvas>
            </div>
            
            <script>
                (function() {{
                    // タイムラインデータ
                    var timelineData = {data_json};
                    var timelineConfig = {timeline_config_json};
                    
                    // チャート初期化
                    window.addEventListener('load', function() {{
                        // Chart.jsのズームプラグインを登録
                        Chart.register(ChartZoom);
                        
                        // データの準備
                        var chartLabels = [];
                        var chartDatasets = [];
                        var colorPalette = [
                            'rgba(54, 162, 235, 1)',  // 青
                            'rgba(255, 99, 132, 1)',  // 赤
                            'rgba(75, 192, 192, 1)',  // 緑
                            'rgba(255, 159, 64, 1)',  // オレンジ
                            'rgba(153, 102, 255, 1)',  // 紫
                            'rgba(255, 205, 86, 1)',  // 黄
                            'rgba(201, 203, 207, 1)'  // グレー
                        ];
                        
                        // パラメータのセットを特定
                        var parameters = timelineConfig.parameters;
                        
                        if (timelineConfig.auto_detect && (!parameters || parameters.length === 0)) {{
                            parameters = [];
                            
                            // サンプルデータからパラメータを自動検出
                            var samplePoint = Array.isArray(timelineData) ? 
                                timelineData[0] : 
                                (timelineData.data ? timelineData.data[0] : null);
                            
                            if (samplePoint) {{
                                for (var key in samplePoint) {{
                                    // 除外キーに含まれていない数値パラメータを抽出
                                    if (!timelineConfig.excluded_keys.includes(key) && 
                                        typeof samplePoint[key] === 'number') {{
                                        parameters.push(key);
                                    }}
                                }}
                            }}
                        }}
                        
                        // 時間ラベルとパラメータ値を抽出
                        var timeValues = [];
                        var parameterValues = {{}};
                        
                        // 各パラメータの配列を初期化
                        parameters.forEach(function(param) {{
                            parameterValues[param] = [];
                        }});
                        
                        // データソースからデータを抽出
                        var dataArray = [];
                        if (Array.isArray(timelineData)) {{
                            dataArray = timelineData;
                        }} else if (timelineData.data && Array.isArray(timelineData.data)) {{
                            dataArray = timelineData.data;
                        }}
                        
                        // 時間シリーズを抽出
                        dataArray.forEach(function(point) {{
                            var timeValue = point[timelineConfig.time_key];
                            
                            if (timeValue) {{
                                // 時間値を変換
                                var time;
                                if (typeof timeValue === 'string') {{
                                    time = moment(timeValue);
                                }} else if (typeof timeValue === 'number') {{
                                    time = moment.unix(timeValue);
                                }}
                                
                                if (time && time.isValid()) {{
                                    timeValues.push(time);
                                    
                                    // 各パラメータの値を収集
                                    parameters.forEach(function(param) {{
                                        parameterValues[param].push({{
                                            x: time,
                                            y: point[param] || 0
                                        }});
                                    }});
                                }}
                            }}
                        }});
                        
                        // 時系列が空の場合は処理を終了
                        if (timeValues.length === 0) {{
                            document.getElementById('{self.element_id}').innerHTML = '<div class="report-chart-empty">パラメータタイムラインデータがありません</div>';
                            return;
                        }}
                        
                        // データセットを作成
                        parameters.forEach(function(param, index) {{
                            var colorIndex = index % colorPalette.length;
                            var color = colorPalette[colorIndex];
                            
                            chartDatasets.push({{
                                label: param,
                                data: parameterValues[param],
                                fill: false,
                                borderColor: color,
                                backgroundColor: color.replace('1)', '0.1)'),
                                borderWidth: 2,
                                pointRadius: timelineConfig.show_points ? timelineConfig.point_radius : 0,
                                tension: 0.1
                            }});
                        }});
                        
                        // チャートオプション
                        var options = {{
                            responsive: true,
                            maintainAspectRatio: false,
                            animation: {{
                                duration: 0
                            }},
                            scales: {{
                                x: {{
                                    type: 'time',
                                    time: {{
                                        unit: 'minute',
                                        tooltipFormat: 'YYYY-MM-DD HH:mm:ss',
                                        displayFormats: {{
                                            millisecond: 'HH:mm:ss.SSS',
                                            second: 'HH:mm:ss',
                                            minute: 'HH:mm',
                                            hour: 'HH:mm',
                                            day: 'MMM D',
                                            week: 'll',
                                            month: 'YYYY/MM',
                                            quarter: 'YYYY [Q]Q',
                                            year: 'YYYY'
                                        }}
                                    }},
                                    title: {{
                                        display: true,
                                        text: '時間'
                                    }}
                                }},
                                y: {{
                                    beginAtZero: false,
                                    title: {{
                                        display: true,
                                        text: 'パラメータ値'
                                    }}
                                }}
                            }},
                            plugins: {{
                                zoom: {{
                                    pan: {{
                                        enabled: true,
                                        mode: 'x'
                                    }},
                                    zoom: {{
                                        wheel: {{
                                            enabled: true
                                        }},
                                        pinch: {{
                                            enabled: true
                                        }},
                                        mode: 'x',
                                        speed: 0.1
                                    }}
                                }},
                                legend: {{
                                    position: 'top'
                                }},
                                tooltip: {{
                                    mode: 'index',
                                    intersect: false
                                }}
                            }},
                            interaction: {{
                                mode: 'nearest',
                                axis: 'x',
                                intersect: false
                            }}
                        }};
                        
                        // チャートを作成
                        var ctx = document.getElementById('{chart_id}').getContext('2d');
                        var chart = new Chart(ctx, {{
                            type: 'line',
                            data: {{
                                datasets: chartDatasets
                            }},
                            options: options
                        }});
                        
                        // ブラシ選択の追加（オプション）
                        if (timelineConfig.brush_selection) {{
                            // ブラシ選択機能はオプション
                        }}
                    }});
                }})();
            </script>
        </div>
        '''
        
        return html_content


class SegmentComparisonElement(BaseChartElement):
    """
    セグメント比較要素
    
    レグ（コースの区間）別の時間比較や同一レグの異なるセッション間比較を表示するための要素です。
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
            kwargs['chart_type'] = "segment_comparison"
        
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
            "https://cdn.jsdelivr.net/npm/chart.js@3.7.1/dist/chart.min.js"
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
            return f'<div id="{self.element_id}" class="report-chart-empty">セグメント比較データがありません</div>'
        
        # CSSスタイルの取得
        css_style = self.get_css_styles()
        width, height = self.get_chart_dimensions()
        
        # セグメント関連のキーを取得
        segment_key = self.get_property("segment_key", "segment")
        session_key = self.get_property("session_key", "session")
        value_key = self.get_property("value_key", "value")
        
        # 表示オプション
        chart_type = self.get_property("chart_type", "bar")  # 'bar', 'line', 'radar'
        stack_data = self.get_property("stack_data", False)
        show_average = self.get_property("show_average", True)
        normalize_values = self.get_property("normalize_values", False)
        
        # データをJSON文字列に変換
        data_json = json.dumps(data)
        
        # チャート設定をJSON文字列に変換
        chart_config = {
            "segment_key": segment_key,
            "session_key": session_key,
            "value_key": value_key,
            "chart_type": chart_type,
            "stack_data": stack_data,
            "show_average": show_average,
            "normalize_values": normalize_values
 {
            "segment_key": segment_key,
            "session_key": session_key,
            "value_key": value_key,
            "chart_type": chart_type,
            "stack_data": stack_data,
            "show_average": show_average,
            "normalize_values": normalize_values}
        
        chart_config_json = json.dumps(chart_config)
        
        # チャートの一意なID
        chart_id = f"chart_{self.element_id}_{str(uuid.uuid4())[:8]}"
        
        # セグメント比較要素のレンダリング
        html_content = f'''
        <div id="{self.element_id}" class="report-chart-container" style="{css_style}">
            <div class="report-chart-wrapper" style="width: {width}; height: {height};">
                <canvas id="{chart_id}" class="report-chart"></canvas>
            </div>
            
            <script>
                (function() {{
                    // セグメント比較データ
                    var segmentData = {data_json};
                    var chartConfig = {chart_config_json};
                    
                    // チャート初期化
                    window.addEventListener('load', function() {{
                        // データの準備
                        var labels = [];
                        var datasets = [];
                        var colorPalette = [
                            'rgba(54, 162, 235, 0.7)',  // 青
                            'rgba(255, 99, 132, 0.7)',  // 赤
                            'rgba(75, 192, 192, 0.7)',  // 緑
                            'rgba(255, 159, 64, 0.7)',  // オレンジ
                            'rgba(153, 102, 255, 0.7)',  // 紫
                            'rgba(255, 205, 86, 0.7)',  // 黄
                            'rgba(201, 203, 207, 0.7)'  // グレー
                        ];
                        
                        // データ形式に応じて処理
                        if (Array.isArray(segmentData)) {{
                            // セグメントとセッションの一覧を抽出
                            var segmentSet = new Set();
                            var sessionSet = new Set();
                            
                            segmentData.forEach(function(item) {{
                                if (item[chartConfig.segment_key]) {{
                                    segmentSet.add(item[chartConfig.segment_key]);
                                }}
                                if (item[chartConfig.session_key]) {{
                                    sessionSet.add(item[chartConfig.session_key]);
                                }}
                            }});
                            
                            // セグメントラベルとセッション一覧
                            var segments = Array.from(segmentSet).sort();
                            var sessions = Array.from(sessionSet).sort();
                            
                            // セグメントがない場合は処理を終了
                            if (segments.length === 0) {{
                                document.getElementById('{self.element_id}').innerHTML = '<div class="report-chart-empty">セグメントデータがありません</div>';
                                return;
                            }}
                            
                            // ラベルを設定
                            labels = segments;
                            
                            // セッションごとにデータセットを作成
                            sessions.forEach(function(session, index) {{
                                var sessionData = [];
                                
                                // 各セグメントの値を取得
                                segments.forEach(function(segment) {{
                                    var found = segmentData.find(function(item) {{
                                        return item[chartConfig.segment_key] === segment && 
                                               item[chartConfig.session_key] === session;
                                    }});
                                    
                                    var value = found ? (found[chartConfig.value_key] || 0) : 0;
                                    sessionData.push(value);
                                }});
                                
                                // データセットを作成
                                var colorIndex = index % colorPalette.length;
                                var color = colorPalette[colorIndex];
                                
                                datasets.push({{
                                    label: session,
                                    data: sessionData,
                                    backgroundColor: color,
                                    borderColor: color.replace('0.7', '1'),
                                    borderWidth: 1
                                }});
                            }});
                            
                            // 平均値の追加（オプション）
                            if (chartConfig.show_average && sessions.length > 1) {{
                                var avgData = [];
                                
                                // 各セグメントの平均値を計算
                                segments.forEach(function(segment, idx) {{
                                    var total = 0;
                                    var count = 0;
                                    
                                    datasets.forEach(function(dataset) {{
                                        total += dataset.data[idx];
                                        count++;
                                    }});
                                    
                                    avgData.push(count > 0 ? total / count : 0);
                                }});
                                
                                // 平均値のデータセットを追加
                                datasets.push({{
                                    label: '平均',
                                    data: avgData,
                                    backgroundColor: 'rgba(255, 255, 255, 0.2)',
                                    borderColor: 'rgba(0, 0, 0, 0.7)',
                                    borderWidth: 2,
                                    type: 'line',
                                    fill: false
                                }});
                            }}
                        }} else if (typeof segmentData === 'object') {{
                            // オブジェクト形式の場合
                            if (segmentData.segments && Array.isArray(segmentData.segments)) {{
                                labels = segmentData.segments;
                            }} else if (segmentData.labels && Array.isArray(segmentData.labels)) {{
                                labels = segmentData.labels;
                            }}
                            
                            if (segmentData.datasets && Array.isArray(segmentData.datasets)) {{
                                datasets = segmentData.datasets;
                            }}
                        }}
                        
                        // ラベルがない場合は処理を終了
                        if (labels.length === 0) {{
                            document.getElementById('{self.element_id}').innerHTML = '<div class="report-chart-empty">セグメントラベルがありません</div>';
                            return;
                        }}
                        
                        // データセットがない場合は処理を終了
                        if (datasets.length === 0) {{
                            document.getElementById('{self.element_id}').innerHTML = '<div class="report-chart-empty">セグメントデータセットがありません</div>';
                            return;
                        }}
                        
                        // 正規化処理（オプション）
                        if (chartConfig.normalize_values) {{
                            datasets.forEach(function(dataset) {{
                                var maxValue = Math.max(...dataset.data);
                                if (maxValue > 0) {{
                                    dataset.data = dataset.data.map(function(value) {{
                                        return value / maxValue;
                                    }});
                                }}
                            }});
                        }}
                        
                        // チャートオプション
                        var options = {{
                            responsive: true,
                            maintainAspectRatio: false,
                            scales: {{
                                y: {{
                                    beginAtZero: true,
                                    stacked: chartConfig.stack_data,
                                    title: {{
                                        display: true,
                                        text: chartConfig.value_key
                                    }}
                                }},
                                x: {{
                                    stacked: chartConfig.stack_data,
                                    title: {{
                                        display: true,
                                        text: chartConfig.segment_key
                                    }}
                                }}
                            }},
                            plugins: {{
                                legend: {{
                                    position: 'top'
                                }},
                                tooltip: {{
                                    mode: 'index',
                                    intersect: false
                                }}
                            }}
                        }};
                        
                        // レーダーチャートの場合は特別な設定
                        if (chartConfig.chart_type === 'radar') {{
                            options.scales = null;  // レーダーチャートはscalesを使用しない
                            options.elements = {{
                                line: {{
                                    tension: 0
                                }}
                            }};
                        }}
                        
                        // チャートを作成
                        var ctx = document.getElementById('{chart_id}').getContext('2d');
                        var chart = new Chart(ctx, {{
                            type: chartConfig.chart_type,
                            data: {{
                                labels: labels,
                                datasets: datasets
                            }},
                            options: options
                        }});
                    }});
                }})();
            </script>
        </div>
        '''
        
        return html_content


class DataViewerElement(BaseChartElement):
    """
    動的なデータビューア要素
    
    スクラブバー（動画のシークバーのような機能）を使用してデータの時間による変化を
    表示するための要素です。
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
            kwargs['chart_type'] = "data_viewer"
        
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
            "https://cdn.jsdelivr.net/npm/moment@2.29.1/moment.min.js",
            "https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"
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
            return f'<div id="{self.element_id}" class="report-chart-empty">データビューアデータがありません</div>'
        
        # CSSスタイルの取得
        css_style = self.get_css_styles()
        width, height = self.get_chart_dimensions()
        
        # データビューアの設定
        time_key = self.get_property("time_key", "time")
        parameters = self.get_property("parameters", [])
        map_view = self.get_property("map_view", True)
        chart_view = self.get_property("chart_view", True)
        data_table = self.get_property("data_table", True)
        
        # データをJSON文字列に変換
        data_json = json.dumps(data)
        
        # ビューア設定をJSON文字列に変換
        viewer_config = {
            "time_key": time_key,
            "parameters": parameters,
            "map_view": map_view,
            "chart_view": chart_view,
            "data_table": data_table
 {
            "time_key": time_key,
            "parameters": parameters,
            "map_view": map_view,
            "chart_view": chart_view,
            "data_table": data_table}
        
        viewer_config_json = json.dumps(viewer_config)
        
        # 要素の一意なID
        viewer_id = f"viewer_{self.element_id}_{str(uuid.uuid4())[:8]}"
        map_id = f"map_{self.element_id}_{str(uuid.uuid4())[:8]}"
        chart_id = f"chart_{self.element_id}_{str(uuid.uuid4())[:8]}"
        table_id = f"table_{self.element_id}_{str(uuid.uuid4())[:8]}"
        slider_id = f"slider_{self.element_id}_{str(uuid.uuid4())[:8]}"
        
        # データビューア要素のレンダリング
        html_content = f'''
        <div id="{self.element_id}" class="report-data-viewer-container" style="{css_style}">
            <!-- Leaflet CSS -->
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
            
            <style>
                .data-viewer-container {{
                    display: flex;
                    flex-direction: column;
                    width: 100%;
                    height: 100%;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    overflow: hidden;
                }}
                
                .data-viewer-panels {{
                    display: flex;
                    flex: 1;
                    overflow: hidden;
                }}
                
                .data-viewer-panel {{
                    flex: 1;
                    padding: 10px;
                    border-right: 1px solid #ddd;
                    overflow: auto;
                }}
                
                .data-viewer-panel:last-child {{
                    border-right: none;
                }}
                
                .data-viewer-controls {{
                    padding: 10px;
                    border-top: 1px solid #ddd;
                    background-color: #f9f9f9;
                }}
                
                .data-viewer-slider {{
                    width: 100%;
                    margin-top: 5px;
                }}
                
                .data-viewer-time-display {{
                    text-align: center;
                    font-weight: bold;
                    margin-top: 5px;
                }}
                
                .data-viewer-table {{
                    width: 100%;
                    border-collapse: collapse;
                }}
                
                .data-viewer-table th, .data-viewer-table td {{
                    padding: 5px;
                    border: 1px solid #ddd;
                    text-align: left;
                }}
                
                .data-viewer-table th {{
                    background-color: #f2f2f2;
                }}
                
                .data-viewer-table tr.current-row {{
                    background-color: #e2f3fe;
                }}
            </style>
            
            <div id="{viewer_id}" class="data-viewer-container" style="width: {width}; height: {height};">
                <div class="data-viewer-panels">
                    <!-- マップビュー（表示設定がオンの場合） -->
                    {f'<div class="data-viewer-panel" id="{map_id}" style="flex: 2;"></div>' if viewer_config["map_view"] else ''}
                    
                    <!-- チャートビュー（表示設定がオンの場合） -->
                    {f'<div class="data-viewer-panel" style="flex: 2;"><canvas id="{chart_id}"></canvas></div>' if viewer_config["chart_view"] else ''}
                    
                    <!-- データテーブル（表示設定がオンの場合） -->
                    {f'<div class="data-viewer-panel" style="flex: 1; max-height: 100%; overflow-y: auto;"><table id="{table_id}" class="data-viewer-table"></table></div>' if viewer_config["data_table"] else ''}
                </div>
                
                <!-- コントロールパネル -->
                <div class="data-viewer-controls">
                    <input type="range" id="{slider_id}" class="data-viewer-slider" min="0" max="100" value="0">
                    <div id="{slider_id}-display" class="data-viewer-time-display">-</div>
                </div>
            </div>
            
            <script>
                (function() {{
                    // データビューアデータ
                    var viewerData = {data_json};
                    var viewerConfig = {viewer_config_json};
                    
                    // データビューア初期化
                    window.addEventListener('load', function() {{
                        // データの準備
                        var timeKey = viewerConfig.time_key;
                        var data = [];
                        
                        // データの形式によって処理を分岐
                        if (Array.isArray(viewerData)) {{
                            data = viewerData;
                        }} else if (viewerData.data && Array.isArray(viewerData.data)) {{
                            data = viewerData.data;
                        }}
                        
                        // データが空の場合は処理を終了
                        if (data.length === 0) {{
                            document.getElementById('{self.element_id}').innerHTML = '<div class="report-chart-empty">データビューアデータがありません</div>';
                            return;
                        }}
                        
                        // 時間値とパラメータを準備
                        var timeValues = [];
                        var parameterData = {{}};
                        
                        // パラメータが指定されていない場合は自動検出
                        var parameters = viewerConfig.parameters;
                        if (!parameters || parameters.length === 0) {{
                            parameters = [];
                            var excludedKeys = [timeKey, 'lat', 'lng', 'latitude', 'longitude'];
                            
                            // 最初のデータポイントからパラメータを抽出
                            if (data.length > 0) {{
                                for (var key in data[0]) {{
                                    // 除外キーでなく、数値型のパラメータを抽出
                                    if (!excludedKeys.includes(key) && typeof data[0][key] === 'number') {{
                                        parameters.push(key);
                                    }}
                                }}
                            }}
                        }}
                        
                        // 各パラメータの配列を初期化
                        parameters.forEach(function(param) {{
                            parameterData[param] = [];
                        }});
                        
                        // 時間とパラメータデータを抽出
                        data.forEach(function(point, index) {{
                            var timeValue = point[timeKey];
                            
                            // 時間値を変換して追加
                            var time = null;
                            if (typeof timeValue === 'string') {{
                                time = moment(timeValue);
                                timeValues.push(time);
                            }} else if (typeof timeValue === 'number') {{
                                time = moment.unix(timeValue);
                                timeValues.push(time);
                            }} else {{
                                // 時間値がない場合はインデックスを使用
                                timeValues.push(index);
                            }}
                            
                            // 各パラメータの値を収集
                            parameters.forEach(function(param) {{
                                parameterData[param].push({{
                                    x: timeValues[timeValues.length - 1],
                                    y: point[param] || 0
                                }});
                            }});
                        }});
                        
                        // スクラブバーの設定
                        var slider = document.getElementById('{slider_id}');
                        var timeDisplay = document.getElementById('{slider_id}-display');
                        
                        // スライダーの最大値を設定
                        slider.max = data.length - 1;
                        
                        // 現在の表示インデックス
                        var currentIndex = 0;
                        
                        // マップビューの初期化（表示設定がオンの場合）
                        var map = null;
                        var marker = null;
                        var trackLine = null;
                        
                        if (viewerConfig.map_view) {{
                            map = L.map('{map_id}');
                            
                            // 地図タイルの追加
                            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                            }}).addTo(map);
                            
                            // トラックラインの作成
                            var trackPoints = [];
                            var latKey = 'lat';
                            var lngKey = 'lng';
                            
                            // 座標キーを特定
                            if (data.length > 0) {{
                                if ('latitude' in data[0] && 'longitude' in data[0]) {{
                                    latKey = 'latitude';
                                    lngKey = 'longitude';
                                }} else if ('lat' in data[0] && 'lon' in data[0]) {{
                                    lngKey = 'lon';
                                }}
                            }}
                            
                            // トラックポイントを抽出
                            data.forEach(function(point) {{
                                if (point[latKey] && point[lngKey]) {{
                                    trackPoints.push([point[latKey], point[lngKey]]);
                                }}
                            }});
                            
                            // トラックポイントがある場合
                            if (trackPoints.length > 0) {{
                                trackLine = L.polyline(trackPoints, {{
                                    color: 'rgba(54, 162, 235, 0.8)',
                                    weight: 3,
                                    opacity: 0.7
                                }}).addTo(map);
                                
                                // 初期マーカーの設定
                                var startPoint = trackPoints[0];
                                marker = L.marker(startPoint).addTo(map);
                                
                                // 自動的にトラック全体が表示されるようにズーム
                                map.fitBounds(trackLine.getBounds());
                            }}
                        }}
                        
                        // チャートビューの初期化（表示設定がオンの場合）
                        var chart = null;
                        var currentLine = null;
                        
                        if (viewerConfig.chart_view) {{
                            // データセットの準備
                            var colorPalette = [
                                'rgba(54, 162, 235, 1)',  // 青
                                'rgba(255, 99, 132, 1)',  // 赤
                                'rgba(75, 192, 192, 1)',  // 緑
                                'rgba(255, 159, 64, 1)',  // オレンジ
                                'rgba(153, 102, 255, 1)',  // 紫
                                'rgba(255, 205, 86, 1)',  // 黄
                                'rgba(201, 203, 207, 1)'  // グレー
                            ];
                            
                            var datasets = [];
                            
                            // 各パラメータのデータセットを作成
                            parameters.forEach(function(param, index) {{
                                var colorIndex = index % colorPalette.length;
                                var color = colorPalette[colorIndex];
                                
                                datasets.push({{
                                    label: param,
                                    data: parameterData[param],
                                    fill: false,
                                    borderColor: color,
                                    backgroundColor: color.replace('1)', '0.1)'),
                                    borderWidth: 2,
                                    pointRadius: 0,
                                    tension: 0.1
                                }});
                            }});
                            
                            // チャートオプション
                            var options = {{
                                responsive: true,
                                maintainAspectRatio: false,
                                animation: {{
                                    duration: 0
                                }},
                                scales: {{
                                    x: {{
                                        type: typeof timeValues[0] === 'object' ? 'time' : 'linear',
                                        time: typeof timeValues[0] === 'object' ? {{
                                            unit: 'minute',
                                            tooltipFormat: 'YYYY-MM-DD HH:mm:ss',
                                            displayFormats: {{
                                                millisecond: 'HH:mm:ss.SSS',
                                                second: 'HH:mm:ss',
                                                minute: 'HH:mm',
                                                hour: 'HH:mm',
                                                day: 'MMM D'
                                            }}
                                        }} : undefined,
                                        title: {{
                                            display: true,
                                            text: '時間'
                                        }}
                                    }},
                                    y: {{
                                        beginAtZero: false,
                                        title: {{
                                            display: true,
                                            text: 'パラメータ値'
                                        }}
                                    }}
                                }},
                                plugins: {{
                                    legend: {{
                                        position: 'top'
                                    }},
                                    tooltip: {{
                                        mode: 'index',
                                        intersect: false
                                    }}
                                }},
                                interaction: {{
                                    mode: 'nearest',
                                    axis: 'x',
                                    intersect: false
                                }}
                            }};
                            
                            // チャートを作成
                            var ctx = document.getElementById('{chart_id}').getContext('2d');
                            chart = new Chart(ctx, {{
                                type: 'line',
                                data: {{
                                    datasets: datasets
                                }},
                                options: options
                            }});
                            
                            // 現在位置を示す垂直線を追加
                            var originalDraw = chart.draw;
                            chart.draw = function() {{
                                originalDraw.apply(this, arguments);
                                
                                if (this.chart && this.chart.config && this.chart.config.data && this.chart.config.data.datasets.length > 0) {{
                                    var chartArea = this.chartArea;
                                    var ctx = this.ctx;
                                    
                                    if (!chartArea) {{
                                        return;
                                    }}
                                    
                                    // 現在位置のX座標を計算
                                    var dataset = this.chart.config.data.datasets[0];
                                    if (dataset && dataset.data.length > currentIndex) {{
                                        var xScale = this.scales.x;
                                        var xValue = dataset.data[currentIndex].x;
                                        var xPixel = xScale.getPixelForValue(xValue);
                                        
                                        // 垂直線を描画
                                        ctx.save();
                                        ctx.beginPath();
                                        ctx.moveTo(xPixel, chartArea.top);
                                        ctx.lineTo(xPixel, chartArea.bottom);
                                        ctx.lineWidth = 2;
                                        ctx.strokeStyle = 'rgba(255, 0, 0, 0.8)';
                                        ctx.stroke();
                                        
                                        // 現在インデックスを表示
                                        ctx.fillStyle = 'rgba(255, 0, 0, 0.8)';
                                        ctx.font = '12px Arial';
                                        ctx.textAlign = 'center';
                                        ctx.fillText('現在位置', xPixel, chartArea.top - 5);
                                        
                                        ctx.restore();
                                    }}
                                }}
                            }};
                        }}
                        
                        // データテーブルの初期化（表示設定がオンの場合）
                        var tableElement = document.getElementById('{table_id}');
                        
                        if (viewerConfig.data_table && tableElement) {{
                            // テーブルヘッダーの生成
                            var headers = ['インデックス', '時間'];
                            parameters.forEach(function(param) {{
                                headers.push(param);
                            }});
                            
                            var headerRow = document.createElement('tr');
                            headers.forEach(function(header) {{
                                var th = document.createElement('th');
                                th.textContent = header;
                                headerRow.appendChild(th);
                            }});
                            tableElement.appendChild(headerRow);
                            
                            // テーブルデータの生成
                            for (var i = 0; i < data.length; i++) {{
                                var row = document.createElement('tr');
                                row.id = 'data-row-' + i;
                                
                                // インデックスと時間を追加
                                var indexCell = document.createElement('td');
                                indexCell.textContent = i;
                                row.appendChild(indexCell);
                                
                                var timeCell = document.createElement('td');
                                var timeValue = data[i][timeKey];
                                if (typeof timeValue === 'string') {{
                                    timeCell.textContent = moment(timeValue).format('YYYY-MM-DD HH:mm:ss');
                                }} else if (typeof timeValue === 'number') {{
                                    timeCell.textContent = moment.unix(timeValue).format('YYYY-MM-DD HH:mm:ss');
                                }} else {{
                                    timeCell.textContent = i;
                                }}
                                row.appendChild(timeCell);
                                
                                // 各パラメータの値を追加
                                parameters.forEach(function(param) {{
                                    var cell = document.createElement('td');
                                    var value = data[i][param];
                                    cell.textContent = typeof value === 'number' ? value.toFixed(2) : (value || '-');
                                    row.appendChild(cell);
                                }});
                                
                                tableElement.appendChild(row);
                            }}
                        }}
                        
                        // スクラブバーの変更イベント
                        slider.addEventListener('input', function(e) {{
                            updateViewer(parseInt(e.target.value));
                        }});
                        
                        // ビューアの更新
                        function updateViewer(index) {{
                            currentIndex = index;
                            var currentData = data[index];
                            
                            // 時間表示の更新
                            var timeValue = currentData[timeKey];
                            if (typeof timeValue === 'string') {{
                                timeDisplay.textContent = moment(timeValue).format('YYYY-MM-DD HH:mm:ss');
                            }} else if (typeof timeValue === 'number') {{
                                timeDisplay.textContent = moment.unix(timeValue).format('YYYY-MM-DD HH:mm:ss');
                            }} else {{
                                timeDisplay.textContent = 'インデックス: ' + index;
                            }}
                            
                            // マップの更新（表示設定がオンの場合）
                            if (map && marker && currentData.lat && currentData.lng) {{
                                marker.setLatLng([currentData.lat, currentData.lng]);
                            }} else if (map && marker && currentData.latitude && currentData.longitude) {{
                                marker.setLatLng([currentData.latitude, currentData.longitude]);
                            }}
                            
                            // チャートの更新（表示設定がオンの場合）
                            if (chart) {{
                                chart.update();
                            }}
                            
                            // テーブルの更新（表示設定がオンの場合）
                            if (viewerConfig.data_table) {{
                                // 前の選択行のハイライトを解除
                                var oldSelectedRow = tableElement.querySelector('.current-row');
                                if (oldSelectedRow) {{
                                    oldSelectedRow.classList.remove('current-row');
                                }}
                                
                                // 現在の行をハイライト
                                var currentRow = document.getElementById('data-row-' + index);
                                if (currentRow) {{
                                    currentRow.classList.add('current-row');
                                    
                                    // 表示範囲内にスクロール
                                    currentRow.scrollIntoView({{
                                        behavior: 'smooth',
                                        block: 'center'
                                    }});
                                }}
                            }}
                        }}
                        
                        // 初期表示
                        updateViewer(0);
                    }});
                }})();
            </script>
        </div>
        '''
        
        return html_content
