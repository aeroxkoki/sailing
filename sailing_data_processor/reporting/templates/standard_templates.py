# -*- coding: utf-8 -*-
"""
sailing_data_processor.reporting.templates.standard_templates

標準テンプレート定義モジュールです。
システムが提供する標準テンプレートの定義を含みます。
"""

from typing import Dict, List, Any, Optional, Union
from sailing_data_processor.reporting.templates.template_model import (
    Template, Section, Element, ElementType, TemplateOutputFormat, SectionType
)


def create_basic_template() -> Template:
    """
    基本レポートテンプレートを作成
    
    シンプルな基本情報を含む標準テンプレートです。
    
    Returns
    -------
    Template
        基本レポートテンプレート
    """
    template = Template(
        name="基本レポート",
        description="セッションの基本情報と主要指標を表示する標準テンプレート",
        author="System",
        output_format=TemplateOutputFormat.HTML,
        category="基本",
        tags=["標準", "基本"]
    )
    
    # ヘッダーセクション
    header_section = Section(
        section_type=SectionType.HEADER,
        name="header",
        title="ヘッダー",
        description="レポートのヘッダーセクション",
        order=0
    )
    
    # タイトル要素
    title_element = Element(
        element_type=ElementType.TEXT,
        name="report_title",
        properties={}
            "content": "{session_name}} - セーリングセッションレポート",
            "content_type": "dynamic"
        },
        styles={
            "font_size": "24px",
            "font_weight": "bold",
            "margin_bottom": "10px"
        }
    )
    
    # 日時要素
    date_element = Element(
        element_type=ElementType.TEXT,
        name="report_date",
        properties={
            "content": "セッション日時: {session_date}}",
            }
            "content_type": "dynamic"
        },
        styles={
            "font_size": "14px",
            "margin_bottom": "5px"
        }
    )
    
    # ロケーション要素
    location_element = Element(
        element_type=ElementType.TEXT,
        name="report_location",
        properties={
            "content": "場所: {session_location}}",
            }
            "content_type": "dynamic"
        },
        styles={
            "font_size": "14px",
            "margin_bottom": "15px"
        }
    )
    
    # 要素をヘッダーセクションに追加
    header_section.elements.append(title_element)
    header_section.elements.append(date_element)
    header_section.elements.append(location_element)
    
    # サマリーセクション
    summary_section = Section(
        section_type=SectionType.CONTENT,
        name="summary",
        title="セッションサマリー",
        description="セッションの基本情報と主要指標",
        order=1
    )
    
    # サマリーテーブル要素
    summary_table_element = Element(
        element_type=ElementType.TABLE,
        name="summary_table",
        properties={
            "data_source": "session_summary",
            "columns": [
                "field": "metric", "header": "指標"},
                {"field": "value", "header": "値"}
            ]
        },
        styles={
            "width": "100%",
            "border_collapse": "collapse",
            "margin_bottom": "20px"
        }
    )
    
    # サマリーセクションに要素を追加
    summary_section.elements.append(summary_table_element)
    
    # 風向風速分析セクション
    wind_section = Section(
        section_type=SectionType.CONTENT,
        name="wind_analysis",
        title="風向風速分析",
        description="風向風速の分析結果",
        order=2
    )
    
    # 風向風速グラフ要素
    wind_chart_element = Element(
        element_type=ElementType.CHART,
        name="wind_direction_speed_chart",
        properties={
            "chart_type": "line",
            "data_source": "wind_data",
            "x_axis": "timestamp",
            "series": [
                "y_axis": "wind_speed", "label": "風速", "color": "#4CAF50"},
                {"y_axis": "wind_direction", "label": "風向", "color": "#2196F3"}
            ],
            "title": "風向風速の変化"
        },
        styles={
            "height": "400px",
            "width": "100%",
            "margin_bottom": "20px"
        }
    )
    
    # 風配図要素
    wind_rose_element = Element(
        element_type=ElementType.DIAGRAM,
        name="wind_rose",
        properties={
            "diagram_type": "windrose",
            "data_source": "wind_data",
            "title": "風配図"
        },
        styles={
            "height": "400px",
            "width": "100%"
        }
    )
    
    # 風向風速セクションに要素を追加
    wind_section.elements.append(wind_chart_element)
    wind_section.elements.append(wind_rose_element)
    
    # 航跡セクション
    track_section = Section(
        section_type=SectionType.CONTENT,
        name="track",
        title="航跡",
        description="GPSトラック",
        order=3
    )
    
    # マップ要素
    map_element = Element(
        element_type=ElementType.MAP,
        name="gps_track_map",
        properties={
            "map_type": "track",
            "data_source": "gps_data",
            "track_color": "#FF5722",
            "center_auto": True,
            "zoom_level": 13
        },
        styles={
            "height": "500px",
            "width": "100%",
            "margin_bottom": "20px"
        }
    )
    
    # マップセクションに要素を追加
    track_section.elements.append(map_element)
    
    # 戦略ポイントセクション
    strategy_section = Section(
        section_type=SectionType.CONTENT,
        name="strategy_points",
        title="戦略ポイント",
        description="重要な戦略的決断ポイント",
        order=4
    )
    
    # 戦略ポイントテーブル要素
    strategy_table_element = Element(
        element_type=ElementType.TABLE,
        name="strategy_points_table",
        properties={
            "data_source": "strategy_points",
            "columns": [
                "field": "timestamp", "header": "時刻"},
                {"field": "type", "header": "タイプ"},
                {"field": "score", "header": "スコア"},
                {"field": "description", "header": "説明"}
            ]
        },
        styles={
            "width": "100%",
            "border_collapse": "collapse",
            "margin_bottom": "20px"
        }
    )
    
    # 戦略ポイントセクションに要素を追加
    strategy_section.elements.append(strategy_table_element)
    
    # フッターセクション
    footer_section = Section(
        section_type=SectionType.FOOTER,
        name="footer",
        title="フッター",
        description="レポートのフッターセクション",
        order=5
    )
    
    # フッターテキスト要素
    footer_element = Element(
        element_type=ElementType.TEXT,
        name="footer_text",
        properties={
            "content": "このレポートはSailing Strategy Analyzerによって生成されました。生成日時: {generation_date}}",
            }
            "content_type": "dynamic"
        },
        styles={
            "font_size": "12px",
            "text_align": "center",
            "margin_top": "20px",
            "color": "#666666"
        }
    )
    
    # フッターセクションに要素を追加
    footer_section.elements.append(footer_element)
    
    # セクションをテンプレートに追加
    template.add_section(header_section)
    template.add_section(summary_section)
    template.add_section(wind_section)
    template.add_section(track_section)
    template.add_section(strategy_section)
    template.add_section(footer_section)
    
    return template


def create_detailed_template() -> Template:
    """
    詳細分析レポートテンプレートを作成
    
    詳細な分析結果とグラフを含む高度なレポートテンプレートです。
    
    Returns
    -------
    Template
        詳細分析レポートテンプレート
    """
    template = Template(
        name="詳細分析レポート",
        description="詳細な分析結果とグラフを含む高度なレポートテンプレート",
        author="System",
        output_format=TemplateOutputFormat.HTML,
        category="詳細",
        tags=["標準", "詳細", "分析"]
    )
    
    # 基本テンプレートからセクションを取得
    basic_template = create_basic_template()
    
    # 基本テンプレートのセクションをコピー
    for section in basic_template.sections:
        template.add_section_from_dict(section.to_dict())
    
    # パフォーマンス分析セクション
    performance_section = Section(
        section_type=SectionType.CONTENT,
        name="performance",
        title="パフォーマンス分析",
        description="詳細なパフォーマンス分析結果",
        order=5  # 戦略ポイントセクションの後
    )
    
    # 速度グラフ要素
    speed_chart_element = Element(
        element_type=ElementType.CHART,
        name="speed_chart",
        properties={
            "chart_type": "line",
            "data_source": "performance_data",
            "x_axis": "timestamp",
            "series": [
                "y_axis": "speed", "label": "速度", "color": "#E91E63"},
                {"y_axis": "optimal_speed", "label": "最適速度", "color": "#9C27B0", "line_style": "dashed"}
            ],
            "title": "速度分析"
        },
        styles={
            "height": "300px",
            "width": "100%",
            "margin_bottom": "20px"
        }
    )
    
    # VMG分析グラフ要素
    vmg_chart_element = Element(
        element_type=ElementType.CHART,
        name="vmg_chart",
        properties={
            "chart_type": "line",
            "data_source": "performance_data",
            "x_axis": "timestamp",
            "series": [
                "y_axis": "vmg", "label": "VMG", "color": "#FF9800"},
                {"y_axis": "optimal_vmg", "label": "最適VMG", "color": "#FF5722", "line_style": "dashed"}
            ],
            "title": "VMG分析"
        },
        styles={
            "height": "300px",
            "width": "100%",
            "margin_bottom": "20px"
        }
    )
    
    # ヒートマップ要素
    heatmap_element = Element(
        element_type=ElementType.CHART,
        name="performance_heatmap",
        properties={
            "chart_type": "heatmap",
            "data_source": "performance_heatmap",
            "x_axis": "wind_speed",
            "y_axis": "wind_angle",
            "value": "performance_ratio",
            "title": "風向風速別パフォーマンス"
        },
        styles={
            "height": "400px",
            "width": "100%",
            "margin_bottom": "20px"
        }
    )
    
    # パフォーマンスサマリー要素
    performance_summary_element = Element(
        element_type=ElementType.KEY_VALUE,
        name="performance_summary",
        properties={
            "data_source": "performance_summary",
            "title": "パフォーマンスサマリー"
        },
        styles={
            "width": "100%",
            "margin_bottom": "20px"
        }
    )
    
    # パフォーマンスセクションに要素を追加
    performance_section.elements.append(performance_summary_element)
    performance_section.elements.append(speed_chart_element)
    performance_section.elements.append(vmg_chart_element)
    performance_section.elements.append(heatmap_element)
    
    # 比較分析セクション
    comparison_section = Section(
        section_type=SectionType.CONTENT,
        name="comparison",
        title="比較分析",
        description="過去のセッションとの比較分析",
        order=6  # パフォーマンス分析セクションの後
    )
    
    # 比較グラフ要素
    comparison_chart_element = Element(
        element_type=ElementType.CHART,
        name="comparison_chart",
        properties={
            "chart_type": "bar",
            "data_source": "comparison_data",
            "x_axis": "metric",
            "series": [
                "y_axis": "current_value", "label": "現在のセッション", "color": "#3F51B5"},
                {"y_axis": "average_value", "label": "過去の平均", "color": "#607D8B"}
            ],
            "title": "過去のセッションとの比較"
        },
        styles={
            "height": "400px",
            "width": "100%",
            "margin_bottom": "20px"
        }
    )
    
    # 比較セクションに要素を追加
    comparison_section.elements.append(comparison_chart_element)
    
    # セクションをテンプレートに追加
    template.add_section(performance_section)
    template.add_section(comparison_section)
    
    # フッターを最後に持ってくるように再ソート
    footer_section = None
    for section in template.sections:
        if section.section_type == SectionType.FOOTER:
            footer_section = section
            break
    
    if footer_section:
        template.remove_section(footer_section.section_id)
        footer_section.order = 100  # 高い順序値を設定
        template.add_section(footer_section)
    
    template.sort_sections()
    
    return template


def create_presentation_template() -> Template:
    """
    プレゼンテーションレポートテンプレートを作成
    
    視覚的な要素を重視したプレゼンテーション用テンプレートです。
    
    Returns
    -------
    Template
        プレゼンテーションレポートテンプレート
    """
    template = Template(
        name="プレゼンテーションレポート",
        description="視覚的な要素を重視したプレゼンテーション用テンプレート",
        author="System",
        output_format=TemplateOutputFormat.HTML,
        category="プレゼンテーション",
        tags=["標準", "プレゼンテーション", "視覚化"],
        global_styles={
            "font_family": "'Segoe UI', Roboto, Arial, sans-serif",
            "base_font_size": 16,
            "color_primary": "#2196F3",
            "color_secondary": "#1976D2",
            "color_accent": "#FF4081",
            "color_background": "#FFFFFF",
            "color_text": "#212121"
        }
    )
    
    # カバーセクション
    cover_section = Section(
        section_type=SectionType.COVER,
        name="cover",
        title="カバーページ",
        description="レポートの表紙",
        order=0,
        styles={
            "background_color": "#1976D2",
            "color": "#FFFFFF",
            "text_align": "center",
            "padding": "50px"
        }
    )
    
    # カバータイトル要素
    cover_title_element = Element(
        element_type=ElementType.TEXT,
        name="cover_title",
        properties={
            "content": "{session_name}}",
            "content_type": "dynamic"
        },
        styles={
            "font_size": "36px",
            "font_weight": "bold",
            "margin_bottom": "20px"
        }
    )
    
    # カバーサブタイトル要素
    cover_subtitle_element = Element(
        element_type=ElementType.TEXT,
        name="cover_subtitle",
        properties={
            "content": "セーリングセッション分析レポート",
            "content_type": "static"
        },
        styles={
            "font_size": "24px",
            "margin_bottom": "40px"
        }
    )
    
    # カバー日付要素
    cover_date_element = Element(
        element_type=ElementType.TEXT,
        name="cover_date",
        properties={
            "content": "{session_date}}",
            "content_type": "dynamic"
        },
        styles={
            "font_size": "18px",
            "margin_bottom": "10px"
        }
    )
    
    # カバー場所要素
    cover_location_element = Element(
        element_type=ElementType.TEXT,
        name="cover_location",
        properties={
            "content": "{session_location}}",
            "content_type": "dynamic"
        },
        styles={
            "font_size": "18px",
            "margin_bottom": "40px"
        }
    )
    
    # カバーセクションに要素を追加
    cover_section.elements.append(cover_title_element)
    cover_section.elements.append(cover_subtitle_element)
    cover_section.elements.append(cover_date_element)
    cover_section.elements.append(cover_location_element)
    
    # 主要指標セクション
    metrics_section = Section(
        section_type=SectionType.CONTENT,
        name="key_metrics",
        title="主要指標",
        description="セッションの主要指標",
        order=1,
        layout={"columns": 2, "margin": "top": 30, "right": 30, "bottom": 30, "left": 30}}
    )
    
    # 速度指標要素
    speed_metric_element = Element(
        element_type=ElementType.BOX,
        name="speed_metric",
        properties={
            "title": "平均速度",
            "value": "{avg_speed}} ノット",
            "icon": "speedometer"
        },
        styles={
            "background_color": "#E3F2FD",
            "border_radius": "10px",
            "padding": "20px",
            "text_align": "center",
            "height": "150px"
        }
    )
    
    # 風速指標要素
    wind_metric_element = Element(
        element_type=ElementType.BOX,
        name="wind_metric",
        properties={
            "title": "平均風速",
            "value": "{avg_wind_speed}} ノット",
            "icon": "air"
        },
        styles={
            "background_color": "#E8F5E9",
            "border_radius": "10px",
            "padding": "20px",
            "text_align": "center",
            "height": "150px"
        }
    )
    
    # 距離指標要素
    distance_metric_element = Element(
        element_type=ElementType.BOX,
        name="distance_metric",
        properties={
            "title": "セーリング距離",
            "value": "{total_distance}} 海里",
            "icon": "straighten"
        },
        styles={
            "background_color": "#FFF3E0",
            "border_radius": "10px",
            "padding": "20px",
            "text_align": "center",
            "height": "150px"
        }
    )
    
    # 時間指標要素
    time_metric_element = Element(
        element_type=ElementType.BOX,
        name="time_metric",
        properties={
            "title": "セーリング時間",
            "value": "{total_time}}",
            "icon": "access_time"
        },
        styles={
            "background_color": "#F3E5F5",
            "border_radius": "10px",
            "padding": "20px",
            "text_align": "center",
            "height": "150px"
        }
    )
    
    # 指標セクションに要素を追加
    metrics_section.elements.append(speed_metric_element)
    metrics_section.elements.append(wind_metric_element)
    metrics_section.elements.append(distance_metric_element)
    metrics_section.elements.append(time_metric_element)
    
    # 主要グラフセクション
    charts_section = Section(
        section_type=SectionType.CONTENT,
        name="key_charts",
        title="パフォーマンス概要",
        description="重要なデータを視覚化したグラフ",
        order=2,
        layout={"columns": 1, "margin": "top": 30, "right": 30, "bottom": 30, "left": 30}}
    )
    
    # 航跡マップ要素
    track_map_element = Element(
        element_type=ElementType.MAP,
        name="track_map",
        properties={
            "map_type": "track",
            "data_source": "gps_data",
            "track_color": "#1976D2",
            "center_auto": True,
            "zoom_level": 13,
            "show_wind": True,
            "show_strategy_points": True
        },
        styles={
            "height": "500px",
            "width": "100%",
            "margin_bottom": "30px",
            "border_radius": "10px",
            "box_shadow": "0 4px 6px rgba(0,0,0,0.1)"
        }
    )
    
    # 速度風速グラフ要素
    speed_wind_chart_element = Element(
        element_type=ElementType.CHART,
        name="speed_wind_chart",
        properties={
            "chart_type": "line",
            "data_source": "performance_data",
            "x_axis": "timestamp",
            "series": [
                "y_axis": "speed", "label": "速度", "color": "#1976D2"},
                {"y_axis": "wind_speed", "label": "風速", "color": "#4CAF50"}
            ],
            "title": "速度と風速の関係",
            "legend_position": "top"
        },
        styles={
            "height": "400px",
            "width": "100%",
            "margin_bottom": "30px",
            "border_radius": "10px",
            "box_shadow": "0 4px 6px rgba(0,0,0,0.1)",
            "padding": "20px",
            "background_color": "#FFFFFF"
        }
    )
    
    # チャートセクションに要素を追加
    charts_section.elements.append(track_map_element)
    charts_section.elements.append(speed_wind_chart_element)
    
    # ハイライトセクション
    highlights_section = Section(
        section_type=SectionType.CONTENT,
        name="highlights",
        title="セッションハイライト",
        description="セッションの重要なポイント",
        order=3,
        layout={"columns": 1, "margin": "top": 30, "right": 30, "bottom": 30, "left": 30}}
    )
    
    # ハイライトテキスト要素
    highlights_text_element = Element(
        element_type=ElementType.TEXT,
        name="highlights_text",
        properties={
            "content": "{session_highlights}}",
            "content_type": "dynamic"
        },
        styles={
            "font_size": "18px",
            "line_height": "1.6",
            "margin_bottom": "20px"
        }
    )
    
    # 戦略ポイントリスト要素
    strategy_list_element = Element(
        element_type=ElementType.LIST,
        name="strategy_list",
        properties={
            "data_source": "strategy_highlights",
            "item_template": "<strong>{timestamp}}</strong>: {description}} (スコア: {score}})",
            }
            "list_type": "ordered"
        },
        styles={
            "font_size": "16px",
            "line_height": "1.6",
            "margin_left": "20px"
        }
    )
    
    # ハイライトセクションに要素を追加
    highlights_section.elements.append(highlights_text_element)
    highlights_section.elements.append(strategy_list_element)
    
    # フッターセクション
    footer_section = Section(
        section_type=SectionType.FOOTER,
        name="footer",
        title="フッター",
        description="レポートのフッターセクション",
        order=100,
        styles={
            "background_color": "#F5F5F5",
            "padding": "20px",
            "text_align": "center"
        }
    )
    
    # フッターテキスト要素
    footer_element = Element(
        element_type=ElementType.TEXT,
        name="footer_text",
        properties={
            "content": "このレポートはSailing Strategy Analyzerによって生成されました。生成日時: {generation_date}}",
            }
            "content_type": "dynamic"
        },
        styles={
            "font_size": "14px",
            "color": "#757575"
        }
    )
    
    # フッターセクションに要素を追加
    footer_section.elements.append(footer_element)
    
    # セクションをテンプレートに追加
    template.add_section(cover_section)
    template.add_section(metrics_section)
    template.add_section(charts_section)
    template.add_section(highlights_section)
    template.add_section(footer_section)
    
    return template


def create_coaching_template() -> Template:
    """
    コーチング用レポートテンプレートを作成
    
    改善点と次のステップにフォーカスしたコーチング用テンプレートです。
    
    Returns
    -------
    Template
        コーチング用レポートテンプレート
    """
    template = Template(
        name="コーチング用レポート",
        description="改善点と次のステップにフォーカスしたコーチング用テンプレート",
        author="System",
        output_format=TemplateOutputFormat.HTML,
        category="コーチング",
        tags=["専門", "コーチング", "改善"],
        global_styles={
            "font_family": "Arial, sans-serif",
            "base_font_size": 14,
            "color_primary": "#009688",
            "color_secondary": "#00796B",
            "color_accent": "#FF5722",
            "color_background": "#FFFFFF",
            "color_text": "#212121"
        }
    )
    
    # ヘッダーセクション
    header_section = Section(
        section_type=SectionType.HEADER,
        name="header",
        title="ヘッダー",
        description="レポートのヘッダーセクション",
        order=0
    )
    
    # タイトル要素
    title_element = Element(
        element_type=ElementType.TEXT,
        name="report_title",
        properties={
            "content": "{sailor_name}} - コーチングレポート",
            "content_type": "dynamic"
        },
        styles={
            "font_size": "24px",
            "font_weight": "bold",
            "margin_bottom": "10px",
            "color": "#009688"
        }
    )
    
    # 日時要素
    date_element = Element(
        element_type=ElementType.TEXT,
        name="report_date",
        properties={
            "content": "セッション日時: {session_date}}",
            }
            "content_type": "dynamic"
        },
        styles={
            "font_size": "14px",
            "margin_bottom": "5px"
        }
    )
    
    # ロケーション要素
    location_element = Element(
        element_type=ElementType.TEXT,
        name="report_location",
        properties={
            "content": "場所: {session_location}}",
            }
            "content_type": "dynamic"
        },
        styles={
            "font_size": "14px",
            "margin_bottom": "15px"
        }
    )
    
    # コーチ情報要素
    coach_element = Element(
        element_type=ElementType.TEXT,
        name="coach_info",
        properties={
            "content": "コーチ: {coach_name}}",
            }
            "content_type": "dynamic"
        },
        styles={
            "font_size": "14px",
            "margin_bottom": "5px",
            "font_weight": "bold"
        }
    )
    
    # 要素をヘッダーセクションに追加
    header_section.elements.append(title_element)
    header_section.elements.append(date_element)
    header_section.elements.append(location_element)
    header_section.elements.append(coach_element)
    
    # サマリーセクション
    summary_section = Section(
        section_type=SectionType.CONTENT,
        name="summary",
        title="セッションサマリー",
        description="セッションの基本情報と主要指標",
        order=1
    )
    
    # サマリーテキスト要素
    summary_text_element = Element(
        element_type=ElementType.TEXT,
        name="summary_text",
        properties={
            "content": "{session_summary}}",
            "content_type": "dynamic"
        },
        styles={
            "font_size": "16px",
            "line_height": "1.6",
            "margin_bottom": "20px"
        }
    )
    
    # サマリーセクションに要素を追加
    summary_section.elements.append(summary_text_element)
    
    # 強みと弱みセクション
    strengths_weaknesses_section = Section(
        section_type=SectionType.CONTENT,
        name="strengths_weaknesses",
        title="強みと改善点",
        description="セッションで示された強みと改善が必要な点",
        order=2,
        layout={"columns": 2, "margin": "top": 20, "right": 20, "bottom": 20, "left": 20}}
    )
    
    # 強み要素
    strengths_element = Element(
        element_type=ElementType.BOX,
        name="strengths",
        properties={
            "title": "強み",
            "content_source": "strengths_list",
            "icon": "thumb_up"
        },
        styles={
            "background_color": "#E8F5E9",
            "border_radius": "10px",
            "padding": "20px",
            "margin_right": "10px"
        }
    )
    
    # 弱み要素
    weaknesses_element = Element(
        element_type=ElementType.BOX,
        name="weaknesses",
        properties={
            "title": "改善点",
            "content_source": "weaknesses_list",
            "icon": "trending_up"
        },
        styles={
            "background_color": "#FFF3E0",
            "border_radius": "10px",
            "padding": "20px",
            "margin_left": "10px"
        }
    )
    
    # 強みと弱みセクションに要素を追加
    strengths_weaknesses_section.elements.append(strengths_element)
    strengths_weaknesses_section.elements.append(weaknesses_element)
    
    # 改善計画セクション
    improvement_section = Section(
        section_type=SectionType.CONTENT,
        name="improvement_plan",
        title="改善計画",
        description="具体的な改善ポイントと次のステップ",
        order=3
    )
    
    # 改善計画テキスト要素
    improvement_text_element = Element(
        element_type=ElementType.TEXT,
        name="improvement_text",
        properties={
            "content": "{improvement_intro}}",
            "content_type": "dynamic"
        },
        styles={
            "font_size": "16px",
            "line_height": "1.6",
            "margin_bottom": "20px"
        }
    )
    
    # 改善計画リスト要素
    improvement_list_element = Element(
        element_type=ElementType.LIST,
        name="improvement_list",
        properties={
            "data_source": "improvement_items",
            "item_template": "<strong>{title}}</strong>: {description}}",
            }
            "list_type": "unordered"
        },
        styles={
            "font_size": "16px",
            "line_height": "1.6",
            "margin_left": "20px",
            "margin_bottom": "20px"
        }
    )
    
    # 練習計画要素
    practice_plan_element = Element(
        element_type=ElementType.TABLE,
        name="practice_plan",
        properties={
            "data_source": "practice_plan",
            "columns": [
                "field": "day", "header": "日付"},
                {"field": "focus", "header": "フォーカス"},
                {"field": "exercises", "header": "エクササイズ"},
                {"field": "goals", "header": "ゴール"}
            ],
            "title": "練習計画"
        },
        styles={
            "width": "100%",
            "border_collapse": "collapse",
            "margin_top": "20px",
            "margin_bottom": "20px"
        }
    )
    
    # 改善計画セクションに要素を追加
    improvement_section.elements.append(improvement_text_element)
    improvement_section.elements.append(improvement_list_element)
    improvement_section.elements.append(practice_plan_element)
    
    # フィードバックセクション
    feedback_section = Section(
        section_type=SectionType.CONTENT,
        name="feedback",
        title="フィードバック記入欄",
        description="セーラーからのフィードバック",
        order=4
    )
    
    # フィードバック説明要素
    feedback_intro_element = Element(
        element_type=ElementType.TEXT,
        name="feedback_intro",
        properties={
            "content": "このレポートに関する質問やコメントがあれば、以下に記入してください。",
            "content_type": "static"
        },
        styles={
            "font_size": "16px",
            "margin_bottom": "10px"
        }
    )
    
    # フィードバック入力要素（HTMLのみで有効）
    feedback_input_element = Element(
        element_type=ElementType.TEXT,
        name="feedback_input",
        properties={
            "content": "<textarea rows='5' style='width: 100%; padding: 10px; border-radius: 5px; border: 1px solid #ddd;' placeholder='ここにフィードバックを入力してください...'></textarea>",
            "content_type": "html"
        },
        styles={
            "margin_top": "10px",
            "margin_bottom": "20px"
        }
    )
    
    # フィードバックセクションに要素を追加
    feedback_section.elements.append(feedback_intro_element)
    feedback_section.elements.append(feedback_input_element)
    
    # フッターセクション
    footer_section = Section(
        section_type=SectionType.FOOTER,
        name="footer",
        title="フッター",
        description="レポートのフッターセクション",
        order=100,
        styles={
            "background_color": "#F5F5F5",
            "padding": "20px",
            "text_align": "center"
        }
    )
    
    # フッターテキスト要素
    footer_element = Element(
        element_type=ElementType.TEXT,
        name="footer_text",
        properties={
            "content": "このレポートはSailing Strategy Analyzerによって生成されました。生成日時: {generation_date}}",
            }
            "content_type": "dynamic"
        },
        styles={
            "font_size": "14px",
            "color": "#757575"
        }
    )
    
    # フッターセクションに要素を追加
    footer_section.elements.append(footer_element)
    
    # セクションをテンプレートに追加
    template.add_section(header_section)
    template.add_section(summary_section)
    template.add_section(strengths_weaknesses_section)
    template.add_section(improvement_section)
    template.add_section(feedback_section)
    template.add_section(footer_section)
    
    return template


def get_all_standard_templates() -> List[Template]:
    """
    すべての標準テンプレートを取得
    
    Returns
    -------
    List[Template]
        標準テンプレートのリスト
    """
    templates = [
        create_basic_template(),
        create_detailed_template(),
        create_presentation_template(),
        create_coaching_template()
    ]
    
    return templates
