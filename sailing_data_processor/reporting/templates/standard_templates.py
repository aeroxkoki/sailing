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
    
    return template