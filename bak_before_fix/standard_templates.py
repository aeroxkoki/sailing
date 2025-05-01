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
                {"field": "timestamp", "header": "時刻"},
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
            "content": "このレポートはSailing Strategy Analyzerによって生成されました。生成日時: {generation_date}",
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
                {"y_axis": "speed", "label": "速度", "color": "#E91E63"},
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
                {"y_axis": "vmg", "label": "VMG", "color": "#FF9800"},
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
                {"y_axis": "current_value", "label": "現在のセッション", "color": "#3F51B5"},
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
    
    return template    # パフォーマンスサマリー要素
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
                {"y_axis": "current_value", "label": "現在のセッション", "color": "#3F51B5"},
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
    プレゼンテーション用テンプレートを作成
    
    視覚的な要素を重視したプレゼンテーション用テンプレートです。
    
    Returns
    -------
    Template
        プレゼンテーション用テンプレート
    """
    template = Template(
        name="プレゼンテーションレポート",
        description="視覚的な要素を重視したプレゼンテーション用テンプレート",
        author="System",
        output_format=TemplateOutputFormat.HTML,
        category="プレゼンテーション",
        tags=["標準", "プレゼンテーション", "視覚化"]
    )
    
    # カバーページセクション
    cover_section = Section(
        section_type=SectionType.HEADER,
        name="cover",
        title="カバーページ",
        description="レポートの表紙",
        order=0
    )
    
    # カバータイトル要素
    cover_title_element = Element(
        element_type=ElementType.TEXT,
        name="cover_title",
        properties={
            "content": "セーリング分析レポート",
            "content_type": "static"
        },
        styles={
            "font_size": "36px",
            "font_weight": "bold",
            "text_align": "center",
            "margin_top": "100px",
            "margin_bottom": "20px"
        }
    )
    
    # カバーサブタイトル要素
    cover_subtitle_element = Element(
        element_type=ElementType.TEXT,
        name="cover_subtitle",
        properties={
            "content": "{session_name}",
            "content_type": "dynamic"
        },
        styles={
            "font_size": "24px",
            "text_align": "center",
            "margin_bottom": "10px"
        }
    )
    
    # カバー日付要素
    cover_date_element = Element(
        element_type=ElementType.TEXT,
        name="cover_date",
        properties={
            "content": "{session_date}",
            "content_type": "dynamic"
        },
        styles={
            "font_size": "18px",
            "text_align": "center",
            "margin_bottom": "100px"
        }
    )
    
    # カバーセクションに要素を追加
    cover_section.elements.append(cover_title_element)
    cover_section.elements.append(cover_subtitle_element)
    cover_section.elements.append(cover_date_element)
    
    # 主要グラフセクション
    charts_section = Section(
        section_type=SectionType.CONTENT,
        name="key_charts",
        title="主要グラフ",
        description="重要なデータを視覚化したグラフ",
        order=1,
        layout={"columns": 2}
    )
    
    # トラックマップ要素
    track_map_element = Element(
        element_type=ElementType.MAP,
        name="track_map",
        properties={
            "map_type": "track",
            "center": {"latitude": "{map_center_lat}", "longitude": "{map_center_lon}"},
            "zoom": 15,
            "data_source": "track_data",
            "color_by": "speed"
        },
        styles={
            "width": "100%",
            "height": "400px",
            "margin_bottom": "20px"
        }
    )
    
    # 風向風速マップ要素
    wind_map_element = Element(
        element_type=ElementType.MAP,
        name="wind_map",
        properties={
            "map_type": "wind_field",
            "center": {"latitude": "{map_center_lat}", "longitude": "{map_center_lon}"},
            "zoom": 15,
            "data_source": "wind_field_data"
        },
        styles={
            "width": "100%",
            "height": "400px",
            "margin_bottom": "20px"
        }
    )
    
    # 速度グラフ要素
    speed_chart_element = Element(
        element_type=ElementType.CHART,
        name="speed_chart",
        properties={
            "chart_type": "line",
            "data_source": "track_data",
            "x_axis": "timestamp",
            "series": [
                {"y_axis": "speed", "label": "速度", "color": "#2196F3"}
            ],
            "title": "速度の時間変化"
        },
        styles={
            "width": "100%",
            "height": "300px",
            "margin_bottom": "20px"
        }
    )
    
    # 風向ローズチャート要素
    wind_rose_element = Element(
        element_type=ElementType.CHART,
        name="wind_rose",
        properties={
            "chart_type": "wind_rose",
            "data_source": "wind_direction_data",
            "title": "風向の分布"
        },
        styles={
            "width": "100%",
            "height": "300px",
            "margin_bottom": "20px"
        }
    )
    
    # 主要グラフセクションに要素を追加
    charts_section.elements.append(track_map_element)
    charts_section.elements.append(wind_map_element)
    charts_section.elements.append(speed_chart_element)
    charts_section.elements.append(wind_rose_element)
    
    # ハイライトセクション
    highlights_section = Section(
        section_type=SectionType.CONTENT,
        name="highlights",
        title="ハイライト",
        description="セッションの重要なポイント",
        order=2
    )
    
    # ハイライトテキスト要素
    highlights_element = Element(
        element_type=ElementType.KEY_VALUE,
        name="highlights_list",
        properties={
            "data_source": "session_highlights",
            "title": "セッションハイライト"
        },
        styles={
            "width": "100%",
            "margin_bottom": "20px"
        }
    )
    
    # ハイライトセクションに要素を追加
    highlights_section.elements.append(highlights_element)
    
    # 戦略ポイントセクション
    strategy_section = Section(
        section_type=SectionType.CONTENT,
        name="strategy_points",
        title="戦略ポイント",
        description="重要な戦略的決断ポイント",
        order=3
    )
    
    # 戦略ポイントテーブル要素
    strategy_table_element = Element(
        element_type=ElementType.TABLE,
        name="strategy_points_table",
        properties={
            "data_source": "strategy_points",
            "columns": [
                {"field": "timestamp", "header": "時刻"},
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
        order=4
    )
    
    # フッターテキスト要素
    footer_element = Element(
        element_type=ElementType.TEXT,
        name="footer_text",
        properties={
            "content": "このレポートはSailing Strategy Analyzerによって生成されました。生成日時: {generation_date}",
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
    template.add_section(cover_section)
    template.add_section(charts_section)
    template.add_section(highlights_section)
    template.add_section(strategy_section)
    template.add_section(footer_section)
    
    return template


def create_coaching_template() -> Template:
    """
    コーチング用テンプレートを作成
    
    改善点と次のステップにフォーカスしたコーチング用テンプレートです。
    
    Returns
    -------
    Template
        コーチング用テンプレート
    """
    template = Template(
        name="コーチング用レポート",
        description="改善点と次のステップにフォーカスしたコーチング用テンプレート",
        author="System",
        output_format=TemplateOutputFormat.HTML,
        category="コーチング",
        tags=["専門", "コーチング", "改善"]
    )
    
    # ヘッダーセクション
    header_section = Section(
        section_type=SectionType.HEADER,
        name="header",
        title="ヘッダー",
        description="レポートのヘッダーセクション",
        order=0
    )
    
    # ヘッダータイトル要素
    header_title_element = Element(
        element_type=ElementType.TEXT,
        name="header_title",
        properties={
            "content": "セーリングパフォーマンス評価: {session_name}",
            "content_type": "dynamic"
        },
        styles={
            "font_size": "24px",
            "font_weight": "bold",
            "text_align": "center",
            "margin_bottom": "10px"
        }
    )
    
    # ヘッダーサブタイトル要素
    header_subtitle_element = Element(
        element_type=ElementType.TEXT,
        name="header_subtitle",
        properties={
            "content": "{session_date}",
            "content_type": "dynamic"
        },
        styles={
            "font_size": "16px",
            "text_align": "center",
            "margin_bottom": "20px"
        }
    )
    
    # ヘッダーセクションに要素を追加
    header_section.elements.append(header_title_element)
    header_section.elements.append(header_subtitle_element)
    
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
                {"field": "key", "header": "項目"},
                {"field": "value", "header": "値"}
            ]
        },
        styles={
            "width": "100%",
            "border_collapse": "collapse",
            "margin_bottom": "20px"
        }
    )
    
    # パフォーマンススコア要素
    performance_score_element = Element(
        element_type=ElementType.CHART,
        name="performance_score",
        properties={
            "chart_type": "gauge",
            "data_source": "performance_score",
            "min": 0,
            "max": 100,
            "title": "総合パフォーマンススコア"
        },
        styles={
            "width": "100%",
            "height": "200px",
            "margin_bottom": "20px"
        }
    )
    
    # サマリーセクションに要素を追加
    summary_section.elements.append(summary_table_element)
    summary_section.elements.append(performance_score_element)
    
    # 強みと弱みセクション
    strengths_weaknesses_section = Section(
        section_type=SectionType.CONTENT,
        name="strengths_weaknesses",
        title="強みと弱み",
        description="セッションで示された強みと改善が必要な点",
        order=2
    )
    
    # 強みリスト要素
    strengths_element = Element(
        element_type=ElementType.LIST,
        name="strengths_list",
        properties={
            "data_source": "strengths",
            "title": "強み",
            "list_type": "unordered",
            "icon": "checkmark"
        },
        styles={
            "margin_bottom": "20px",
            "color": "#4CAF50"
        }
    )
    
    # 弱みリスト要素
    weaknesses_element = Element(
        element_type=ElementType.LIST,
        name="weaknesses_list",
        properties={
            "data_source": "weaknesses",
            "title": "改善点",
            "list_type": "unordered",
            "icon": "warning"
        },
        styles={
            "margin_bottom": "20px",
            "color": "#F44336"
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
    
    # 改善ステップ要素
    improvement_steps_element = Element(
        element_type=ElementType.LIST,
        name="improvement_steps",
        properties={
            "data_source": "improvement_steps",
            "title": "改善ステップ",
            "list_type": "ordered"
        },
        styles={
            "margin_bottom": "20px"
        }
    )
    
    # 練習提案要素
    practice_suggestions_element = Element(
        element_type=ElementType.KEY_VALUE,
        name="practice_suggestions",
        properties={
            "data_source": "practice_suggestions",
            "title": "練習提案"
        },
        styles={
            "width": "100%",
            "margin_bottom": "20px"
        }
    )
    
    # 改善計画セクションに要素を追加
    improvement_section.elements.append(improvement_steps_element)
    improvement_section.elements.append(practice_suggestions_element)
    
    # フッターセクション
    footer_section = Section(
        section_type=SectionType.FOOTER,
        name="footer",
        title="フッター",
        description="レポートのフッターセクション",
        order=4
    )
    
    # フッターテキスト要素
    footer_element = Element(
        element_type=ElementType.TEXT,
        name="footer_text",
        properties={
            "content": "このレポートはSailing Strategy Analyzerによって生成されました。生成日時: {generation_date}",
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
    template.add_section(strengths_weaknesses_section)
    template.add_section(improvement_section)
    template.add_section(footer_section)
    
    return template


def get_all_standard_templates() -> Dict[str, Template]:
    """
    すべての標準テンプレートを取得
    
    Returns
    -------
    Dict[str, Template]
        テンプレート名をキーとした標準テンプレートの辞書
    """
    return {
        "basic": create_basic_template(),
        "detailed": create_detailed_template(),
        "presentation": create_presentation_template(),
        "coaching": create_coaching_template()
    }
