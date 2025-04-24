# -*- coding: utf-8 -*-
"""
sailing_data_processor.reporting.elements.timeline.event_timeline

イベントタイムラインクラスを提供するモジュールです。
セーリング中のイベント（タック、ジャイブ、マーク回航など）を時間軸上に表示します。
"""

from typing import Dict, List, Any, Optional, Union, Tuple
import json
import uuid
from datetime import datetime, timedelta

from sailing_data_processor.reporting.elements.base_element import BaseElement
from sailing_data_processor.reporting.templates.template_model import ElementType, ElementModel


class EventTimeline(BaseElement):
    """
    イベントタイムラインクラス
    
    セーリング中のイベント（タック、ジャイブ、マーク回航など）を
    時間軸上に表示するタイムラインを提供します。
    """
    
    def __init__(self, model: Optional[ElementModel] = None, element_id=None, name="イベントタイムライン", **kwargs):
        """
        初期化
        
        Parameters
        ----------
        model : Optional[ElementModel], optional
            要素モデル, by default None
        element_id : str, optional
            要素ID, by default None (自動生成)
        name : str, optional
            要素名, by default "イベントタイムライン"
        **kwargs : dict
            その他のプロパティ
        """
        # デフォルトでタイムライン要素タイプを設定
        if model is None and 'element_type' not in kwargs:
            kwargs['element_type'] = ElementType.TIMELINE
        
        if element_id is None:
            element_id = f"event_timeline_{uuid.uuid4().hex[:8]}"
        
        super().__init__(model, element_id=element_id, name=name, **kwargs)
        
        # イベントデータ
        self._events = []
        
        # 表示オプション
        self._options = {
            "show_tacks": kwargs.get("show_tacks", True),
            "show_jibes": kwargs.get("show_jibes", True),
            "show_marks": kwargs.get("show_marks", True),
            "show_custom": kwargs.get("show_custom", True),
            "event_height": kwargs.get("event_height", 20),
            "group_events": kwargs.get("group_events", True),
            "timeline_height": kwargs.get("timeline_height", 150),
            "handle_overflow": kwargs.get("handle_overflow", True),
            "tooltip_placement": kwargs.get("tooltip_placement", "top"),
            "time_format": kwargs.get("time_format", "HH:mm:ss"),
        
        # オプションをプロパティに設定
        for key, value in self._options.items():
            self.set_property(key, value)
        
        # イベントタイプの定義と色
        self._event_types = {
            "tack": {"color": "#FF5722", "symbol": "⟲", "label": "タック"},
            "jibe": {"color": "#2196F3", "symbol": "⟳", "label": "ジャイブ"},
            "mark_rounding": {"color": "#4CAF50", "symbol": "◎", "label": "マーク回航"},
            "start": {"color": "#FFC107", "symbol": "▶", "label": "スタート"},
            "finish": {"color": "#9C27B0", "symbol": "■", "label": "フィニッシュ"},
            "custom": {"color": "#607D8B", "symbol": "★", "label": "カスタム"}
        
        # イベントタイプとフィールドの対応
        self.set_property("event_type_fields", {
            "tack": "is_tack",
            "jibe": "is_jibe",
            "mark_rounding": "is_mark_rounding",
            "start": "is_start",
            "finish": "is_finish"
        })
        
        # 詳細情報のフィールド
        self.set_property("detail_fields", [
            "speed", "wind_speed", "wind_direction", "heading"
        ])
        
        # データソース
        self.set_property("data_source", kwargs.get("data_source", ""))
    
    def add_event(self, timestamp, event_type, label=None, details=None, **kwargs):
        """
        イベントを追加
        
        Parameters
        ----------
        timestamp : str or datetime
            イベントの発生時刻
        event_type : str
            イベントタイプ ("tack", "jibe", "mark_rounding", "start", "finish", "custom")
        label : str, optional
            イベントのラベル, by default None
        details : dict, optional
            イベントの詳細情報, by default None
        **kwargs : dict
            その他のイベント属性
            
        Returns
        -------
        dict
            追加されたイベント情報
        """
        # タイムスタンプの形式をチェック
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp)
            except (ValueError, TypeError):
                try:
                    timestamp = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S")
                except (ValueError, TypeError):
                    raise ValueError(f"無効なタイムスタンプ形式: {timestamp}")
        
        if not isinstance(timestamp, datetime):
            raise TypeError("タイムスタンプはdatetimeオブジェクトまたはISO形式の文字列である必要があります")
        
        # イベントタイプの検証
        if event_type not in self._event_types and event_type != "custom":
            raise ValueError(f"無効なイベントタイプ: {event_type}")
        
        # イベント情報を作成
        event = {
            "id": str(uuid.uuid4()),
            "timestamp": timestamp.isoformat(),
            "type": event_type,
            "label": label or self._event_types[event_type]["label"],
            "symbol": self._event_types[event_type]["symbol"],
            "color": self._event_types[event_type]["color"],
            "details": details or {}
        
        # その他の属性を追加
        for key, value in kwargs.items():
            if key not in event:
                event[key] = value
        
        # イベントを追加
        self._events.append(event)
        
        return event
    
    def clear_events(self):
        """イベントをクリア"""
        self._events = []
    
    def set_property(self, key: str, value: Any) -> None:
        """
        プロパティを設定
        
        Parameters
        ----------
        key : str
            プロパティ名
        value : Any
            プロパティ値
        """
        super().set_property(key, value)
        
        # _optionsも更新
        if key in self._options:
            self._options[key] = value
    
    def get_property(self, key: str, default: Any = None) -> Any:
        """
        プロパティを取得
        
        Parameters
        ----------
        key : str
            プロパティ名
        default : Any, optional
            デフォルト値, by default None
            
        Returns
        -------
        Any
            プロパティ値
        """
        return super().get_property(key, default)
    
    def _extract_events_from_data(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        データからイベントを抽出
        
        Parameters
        ----------
        data : Dict[str, Any]
            データソース
            
        Returns
        -------
        List[Dict[str, Any]]
            抽出されたイベントのリスト
        """
        events = []
        
        # データが存在しない場合は空リストを返す
        if not data or "timestamp" not in data:
            return events
        
        # タイムスタンプのリスト
        timestamps = data["timestamp"]
        
        # イベントタイプとフィールドの対応
        event_type_fields = self.get_property("event_type_fields", {})
        
        # 詳細情報のフィールド
        detail_fields = self.get_property("detail_fields", [])
        
        # イベントを抽出
        for i, ts in enumerate(timestamps):
            # 各イベントタイプについてチェック
            for event_type, field in event_type_fields.items():
                if field in data and i < len(data[field]) and data[field][i]:
                    # 詳細情報を収集
                    details = {}
                    for detail_field in detail_fields:
                        if detail_field in data and i < len(data[detail_field]):
                            details[detail_field] = data[detail_field][i]
                    
                    # イベントを追加
                    event = {
                        "id": f"{event_type}_{i}",
                        "timestamp": ts,
                        "type": event_type,
                        "label": self._event_types[event_type]["label"],
                        "symbol": self._event_types[event_type]["symbol"],
                        "color": self._event_types[event_type]["color"],
                        "details": details,
                        "index": i  # データ内のインデックスを保存
                    events.append(event)
        
        return events
    
    def get_required_libraries(self) -> List[str]:
        """
        必要なライブラリのURLリストを取得
        
        Returns
        -------
        List[str]
            ライブラリのURLリスト
        """
        return [
            "https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js",
            "https://cdn.jsdelivr.net/npm/luxon@2.0.2/build/global/luxon.min.js",
            "https://cdn.jsdelivr.net/npm/chartjs-adapter-luxon@1.1.0/dist/chartjs-adapter-luxon.min.js"
        ]
    
    def get_required_styles(self) -> List[str]:
        """
        必要なスタイルシートのURLリストを取得
        
        Returns
        -------
        List[str]
            スタイルシートのURLリスト
        """
        return []
    
    def render(self, context: Dict[str, Any] = None) -> str:
        """
        タイムラインのHTMLを生成
        
        Parameters
        ----------
        context : Dict[str, Any], optional
            レンダリングコンテキスト, by default None
            
        Returns
        -------
        str
            生成されたHTML
        """
        if context is None:
            context = {}
        
        # 条件チェック
        if not self.evaluate_conditions(context):
            return ""
        
        # データソースからイベントを抽出
        data_source = self.get_property("data_source", "")
        events = self._events.copy()  # 直接追加されたイベント
        
        if data_source and data_source in context:
            data = context[data_source]
            extracted_events = self._extract_events_from_data(data)
            events.extend(extracted_events)
        
        # イベントが空の場合はプレースホルダを表示
        if not events:
            return f'<div id="{self.element_id}" class="event-timeline-container"><p>イベントがありません</p></div>'
        
        # CSSスタイルの取得
        css_style = self.get_css_styles()
        
        # タイムラインの高さ
        timeline_height = self.get_property("timeline_height", 150)
        
        # イベント表示の設定
        show_tacks = str(self.get_property("show_tacks", True)).lower()
        show_jibes = str(self.get_property("show_jibes", True)).lower()
        show_marks = str(self.get_property("show_marks", True)).lower()
        show_custom = str(self.get_property("show_custom", True)).lower()
        
        # イベントのグループ化設定
        group_events = str(self.get_property("group_events", True)).lower()
        
        # イベントの高さ
        event_height = self.get_property("event_height", 20)
        
        # オーバーフロー処理
        handle_overflow = str(self.get_property("handle_overflow", True)).lower()
        
        # ツールチップの配置
        tooltip_placement = self.get_property("tooltip_placement", "top")
        
        # 時間フォーマット
        time_format = self.get_property("time_format", "HH:mm:ss")
        
        # イベントをJSON形式に変換
        events_json = json.dumps(events, ensure_ascii=False)
        
        # 必要なライブラリを取得
        libraries = self.get_required_libraries()
        library_tags = "\n".join([f'<script src="{lib}"></script>' for lib in libraries])
        
        # 必要なスタイルを取得
        styles = self.get_required_styles()
        style_tags = "\n".join([f'<link rel="stylesheet" href="{style}" />' for style in styles])
        
        # HTMLを生成
        html = f'''
        <div id="{self.element_id}_container" class="event-timeline-container" style="{css_style}">
            {style_tags}
            
            <style>
                #{self.element_id}_container {{
                    width: 100%;
                    position: relative;
                }}
                
                #{self.element_id}_timeline {{
                    width: 100%;
                    height: {timeline_height}px;
                    position: relative;
                    overflow-x: auto;
                    overflow-y: hidden;
                }}
                
                .event-marker {{
                    position: absolute;
                    cursor: pointer;
                    transition: transform 0.2s;
                    text-align: center;
                    user-select: none;
                }}
                
                .event-marker:hover {{
                    transform: scale(1.2);
                    z-index: 1000;
                }}
                
                .event-tooltip {{
                    position: absolute;
                    background-color: rgba(255, 255, 255, 0.95);
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    padding: 8px;
                    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
                    z-index: 1001;
                    display: none;
                    pointer-events: none;
                    max-width: 300px;
                }}
                
                .event-tooltip-header {{
                    font-weight: bold;
                    margin-bottom: 5px;
                    border-bottom: 1px solid #eee;
                    padding-bottom: 3px;
                }}
                
                .event-tooltip-content {{
                    font-size: 0.9em;
                }}
                
                .event-tooltip-detail {{
                    display: flex;
                    justify-content: space-between;
                    margin: 2px 0;
                }}
            </style>
            
            <div id="{self.element_id}_timeline" class="timeline-container"></div>
            <div id="{self.element_id}_tooltip" class="event-tooltip"></div>
            
            {library_tags}
            
            <script>
                (function() {{
                    // イベントデータ
                    const events = {events_json};
                    
                    // 表示設定
                    const config = {{
                        showTacks: {show_tacks},
                        showJibes: {show_jibes},
                        showMarks: {show_marks},
                        showCustom: {show_custom},
                        groupEvents: {group_events},
                        eventHeight: {event_height},
                        handleOverflow: {handle_overflow},
                        tooltipPlacement: "{tooltip_placement}",
                        timeFormat: "{time_format}"
                    }};
                    
                    // イベントタイプの定義
                    const eventTypes = {{
                        "tack": {{ color: "#FF5722", symbol: "⟲", label: "タック" }},
                        "jibe": {{ color: "#2196F3", symbol: "⟳", label: "ジャイブ" }},
                        "mark_rounding": {{ color: "#4CAF50", symbol: "◎", label: "マーク回航" }},
                        "start": {{ color: "#FFC107", symbol: "▶", label: "スタート" }},
                        "finish": {{ color: "#9C27B0", symbol: "■", label: "フィニッシュ" }},
                        "custom": {{ color: "#607D8B", symbol: "★", label: "カスタム" }}
                    }};
                    
                    // タイムライン要素
                    const timelineContainer = document.getElementById("{self.element_id}_timeline");
                    const tooltipElement = document.getElementById("{self.element_id}_tooltip");
                    
                    // イベントのフィルタリング
                    let filteredEvents = events.filter(event => {{
                        switch(event.type) {{
                            case "tack": return config.showTacks;
                            case "jibe": return config.showJibes;
                            case "mark_rounding": return config.showMarks;
                            case "custom": return config.showCustom;
                            default: return true;
                        }}
                    }});
                    
                    // イベントを時間順にソート
                    filteredEvents.sort((a, b) => {{
                        return new Date(a.timestamp) - new Date(b.timestamp);
                    }});
                    
                    if (filteredEvents.length === 0) {{
                        timelineContainer.innerHTML = "<p>表示するイベントがありません</p>";
                        return;
                    }}
                    
                    // タイムラインの時間範囲を計算
                    const startTime = new Date(filteredEvents[0].timestamp);
                    const endTime = new Date(filteredEvents[filteredEvents.length - 1].timestamp);
                    const timeRange = endTime - startTime;
                    
                    // タイムラインの幅を計算
                    const timelineWidth = Math.max(timelineContainer.clientWidth, timeRange / 1000 * 10); // 最低でも表示幅、最大で1秒あたり10px
                    
                    // タイムライン背景の作成
                    const timelineBackground = document.createElement("div");
                    timelineBackground.style.position = "absolute";
                    timelineBackground.style.top = "0";
                    timelineBackground.style.left = "0";
                    timelineBackground.style.width = timelineWidth + "px";
                    timelineBackground.style.height = "100%";
                    timelineBackground.style.background = "linear-gradient(to bottom, #f8f8f8, #e8e8e8)";
                    timelineContainer.appendChild(timelineBackground);
                    
                    // 時間目盛りの作成
                    const timeMarkerCount = Math.min(10, Math.max(5, Math.floor(timelineWidth / 100)));
                    const timeInterval = timeRange / (timeMarkerCount - 1);
                    
                    for (let i = 0; i < timeMarkerCount; i++) {{
                        const markerTime = new Date(startTime.getTime() + i * timeInterval);
                        const position = (markerTime - startTime) / timeRange * timelineWidth;
                        
                        // 目盛り線
                        const tickMark = document.createElement("div");
                        tickMark.style.position = "absolute";
                        tickMark.style.top = "0";
                        tickMark.style.left = position + "px";
                        tickMark.style.width = "1px";
                        tickMark.style.height = "100%";
                        tickMark.style.background = "rgba(0, 0, 0, 0.1)";
                        timelineBackground.appendChild(tickMark);
                        
                        // 時間ラベル
                        const timeLabel = document.createElement("div");
                        timeLabel.style.position = "absolute";
                        timeLabel.style.top = "5px";
                        timeLabel.style.left = position + "px";
                        timeLabel.style.transform = "translateX(-50%)";
                        timeLabel.style.fontSize = "0.8em";
                        timeLabel.style.color = "#666";
                        
                        // 時間フォーマット
                        const formatter = new Intl.DateTimeFormat('ja-JP', {{
                            hour: '2-digit',
                            minute: '2-digit',
                            second: '2-digit',
                            hour12: false
                        }});
                        timeLabel.textContent = formatter.format(markerTime);
                        timelineBackground.appendChild(timeLabel);
                    }}
                    
                    // イベントのグループ化
                    let groupedEvents = filteredEvents;
                    if (config.groupEvents) {{
                        // 時間的に近いイベントをグループ化
                        const groupThreshold = timeRange * 0.01; // 全体の1%以内のイベントをグループ化
                        
                        // グループの初期化
                        const groups = [];
                        let currentGroup = [filteredEvents[0]];
                        
                        for (let i = 1; i < filteredEvents.length; i++) {{
                            const prevTime = new Date(filteredEvents[i-1].timestamp);
                            const currentTime = new Date(filteredEvents[i].timestamp);
                            
                            if (currentTime - prevTime < groupThreshold) {{
                                // 現在のグループに追加
                                currentGroup.push(filteredEvents[i]);
                            }} else {{
                                // 新しいグループを開始
                                groups.push(currentGroup);
                                currentGroup = [filteredEvents[i]];
                            }}
                        }}
                        
                        // 最後のグループを追加
                        groups.push(currentGroup);
                        
                        // グループ代表のイベントのみを選択
                        groupedEvents = groups.map(group => {{
                            if (group.length === 1) {{
                                return group[0];
                            }}
                            
                            // グループの代表（最も重要なイベント）を選択
                            const priorityOrder = {{"start": 0, "finish": 1, "mark_rounding": 2, "tack": 3, "jibe": 4, "custom": 5}};
                            group.sort((a, b) => priorityOrder[a.type] - priorityOrder[b.type]);
                            
                            const representative = group[0];
                            representative.groupSize = group.length;
                            representative.groupedEvents = group;
                            
                            return representative;
                        }});
                    }}
                    
                    // イベントマーカーの表示
                    groupedEvents.forEach((event, index) => {{
                        const eventTime = new Date(event.timestamp);
                        const position = (eventTime - startTime) / timeRange * timelineWidth;
                        
                        // 位置が範囲外の場合は調整
                        let adjustedPosition = position;
                        if (config.handleOverflow) {{
                            adjustedPosition = Math.max(10, Math.min(timelineWidth - 10, position));
                        }}
                        
                        // イベントタイプに基づく情報を取得
                        const eventInfo = eventTypes[event.type] || eventTypes.custom;
                        
                        // イベントマーカーの作成
                        const eventMarker = document.createElement("div");
                        eventMarker.className = "event-marker";
                        eventMarker.id = `{self.element_id}_event_${{event.id}}`;
                        eventMarker.dataset.eventId = event.id;
                        eventMarker.dataset.eventType = event.type;
                        eventMarker.dataset.timestamp = event.timestamp;
                        
                        // グループサイズの設定
                        if (event.groupSize > 1) {{
                            eventMarker.dataset.groupSize = event.groupSize;
                        }}
                        
                        // スタイルの設定
                        eventMarker.style.left = adjustedPosition + "px";
                        eventMarker.style.top = "30px";
                        eventMarker.style.width = `${{config.eventHeight}}px`;
                        eventMarker.style.height = `${{config.eventHeight}}px`;
                        eventMarker.style.lineHeight = `${{config.eventHeight}}px`;
                        eventMarker.style.backgroundColor = event.color || eventInfo.color;
                        eventMarker.style.color = "#fff";
                        eventMarker.style.borderRadius = "50%";
                        eventMarker.style.fontSize = `${{Math.max(10, config.eventHeight * 0.6)}}px`;
                        
                        // グループサイズの表現（サイズを大きくする）
                        if (event.groupSize > 1) {{
                            const scale = 1 + Math.min(1, event.groupSize * 0.1);
                            eventMarker.style.transform = `scale(${{scale}})`;
                            eventMarker.style.zIndex = 10 + event.groupSize;
                            eventMarker.title = `${{event.label}} (${{event.groupSize}}件のイベント)`;
                        }} else {{
                            eventMarker.title = event.label;
                        }}
                        
                        // シンボルを表示
                        eventMarker.innerHTML = event.symbol || eventInfo.symbol;
                        
                        // イベントリスナー
                        eventMarker.addEventListener("mouseenter", (e) => {{
                            showTooltip(event, eventMarker);
                        }});
                        
                        eventMarker.addEventListener("mouseleave", (e) => {{
                            hideTooltip();
                        }});
                        
                        eventMarker.addEventListener("click", (e) => {{
                            // カスタムイベントを発火
                            const selectEvent = new CustomEvent("timelineEventSelect", {{
                                detail: {{
                                    event: event,
                                    element: eventMarker,
                                    groupedEvents: event.groupedEvents || [event]
                                }},
                                bubbles: true
                            }});
                            timelineContainer.dispatchEvent(selectEvent);
                        }});
                        
                        timelineContainer.appendChild(eventMarker);
                    }});
                    
                    // ツールチップの表示
                    function showTooltip(event, markerElement) {{
                        const tooltip = tooltipElement;
                        
                        // ツールチップの内容を設定
                        let tooltipContent = `
                            <div class="event-tooltip-header">
                                ${{event.label || eventTypes[event.type].label}}
                            </div>
                            <div class="event-tooltip-content">
                        `;
                        
                        // タイムスタンプの表示
                        const eventTime = new Date(event.timestamp);
                        const timeFormatter = new Intl.DateTimeFormat('ja-JP', {{
                            hour: '2-digit',
                            minute: '2-digit',
                            second: '2-digit',
                            hour12: false
                        }});
                        
                        tooltipContent += `
                            <div class="event-tooltip-detail">
                                <span>時刻:</span>
                                <span>${{timeFormatter.format(eventTime)}}</span>
                            </div>
                        `;
                        
                        // グループサイズの表示
                        if (event.groupSize > 1) {{
                            tooltipContent += `
                                <div class="event-tooltip-detail">
                                    <span>イベント数:</span>
                                    <span>${{event.groupSize}}</span>
                                </div>
                            `;
                        }}
                        
                        // 詳細情報の表示
                        if (event.details) {{
                            for (const [key, value] of Object.entries(event.details)) {{
                                let formattedValue = value;
                                let label = key;
                                
                                // フィールドの表示名を設定
                                switch(key) {{
                                    case "speed": 
                                        label = "速度"; 
                                        formattedValue = value + " kt";
                                        break;
                                    case "wind_speed": 
                                        label = "風速"; 
                                        formattedValue = value + " kt";
                                        break;
                                    case "wind_direction": 
                                        label = "風向"; 
                                        formattedValue = value + "°";
                                        break;
                                    case "heading": 
                                        label = "艇首方位"; 
                                        formattedValue = value + "°";
                                        break;
                                }}
                                
                                tooltipContent += `
                                    <div class="event-tooltip-detail">
                                        <span>${{label}}:</span>
                                        <span>${{formattedValue}}</span>
                                    </div>
                                `;
                            }}
                        }}
                        
                        tooltipContent += `</div>`;
                        tooltip.innerHTML = tooltipContent;
                        
                        // ツールチップの位置を設定
                        const markerRect = markerElement.getBoundingClientRect();
                        const containerRect = timelineContainer.getBoundingClientRect();
                        
                        tooltip.style.display = "block";
                        
                        const tooltipRect = tooltip.getBoundingClientRect();
                        
                        // 配置位置の決定
                        let top, left;
                        
                        if (config.tooltipPlacement === "top") {{
                            top = markerRect.top - containerRect.top - tooltipRect.height - 10;
                            left = markerRect.left - containerRect.left + markerRect.width / 2 - tooltipRect.width / 2;
                        }} else if (config.tooltipPlacement === "bottom") {{
                            top = markerRect.bottom - containerRect.top + 10;
                            left = markerRect.left - containerRect.left + markerRect.width / 2 - tooltipRect.width / 2;
                        }} else if (config.tooltipPlacement === "left") {{
                            top = markerRect.top - containerRect.top + markerRect.height / 2 - tooltipRect.height / 2;
                            left = markerRect.left - containerRect.left - tooltipRect.width - 10;
                        }} else {{ // right
                            top = markerRect.top - containerRect.top + markerRect.height / 2 - tooltipRect.height / 2;
                            left = markerRect.right - containerRect.left + 10;
                        }}
                        
                        // 画面からはみ出さないように調整
                        top = Math.max(5, Math.min(containerRect.height - tooltipRect.height - 5, top));
                        left = Math.max(5, Math.min(containerRect.width - tooltipRect.width - 5, left));
                        
                        tooltip.style.top = `${{top}}px`;
                        tooltip.style.left = `${{left}}px`;
                    }}
                    
                    // ツールチップの非表示
                    function hideTooltip() {{
                        tooltipElement.style.display = "none";
                    }}
                    
                    // グローバル変数として保存（外部からアクセス用）
                    window["{self.element_id}_timeline"] = {{
                        events: events,
                        filteredEvents: filteredEvents,
                        groupedEvents: groupedEvents,
                        config: config
                    }};
                }})();
            </script>
        </div>
        '''
        
        return html
"""
"""