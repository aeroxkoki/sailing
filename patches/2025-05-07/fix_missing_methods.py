#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EnhancedQualityMetricsCalculator に不足しているメソッドを追加するパッチ

テストで見つかったエラー：
- test_quality_metrics - AttributeError: 'EnhancedQualityMetricsCalculator' object has no attribute 'calculate_category_quality_scores'
- test_visualization - AttributeError: 'EnhancedQualityMetricsCalculator' object has no attribute 'generate_quality_score_visualization'
"""

import sys
import os
import re

def fix_enhanced_quality_metrics_calculator(file_path):
    """EnhancedQualityMetricsCalculator に不足しているメソッドを追加します"""
    
    # ファイルの存在確認
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return False
    
    print(f"Fixing {file_path}")
    
    # ファイルを読み込む
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # バックアップファイルの作成
    backup_path = f"{file_path}.bak"
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Backup created: {backup_path}")
    
    # calculate_category_quality_scores メソッドの追加
    if "def calculate_category_quality_scores" not in content:
        # クラスの最後を見つける
        class_end = content.rfind("}")
        if class_end == -1:
            # } が見つからない場合は、クラスの最後の行を見つける
            lines = content.split('\n')
            for i in range(len(lines) - 1, -1, -1):
                if "def get_quality_summary" in lines[i]:
                    # get_quality_summary メソッドの終わりを見つける
                    for j in range(i, len(lines)):
                        if lines[j].strip().startswith("return {"):
                            # return ステートメントの終わりを見つける
                            for k in range(j, len(lines)):
                                if lines[k].strip() == "}":
                                    class_end = k + 1
                                    break
                            break
                    break
        
        if class_end == -1:
            print("Error: Could not find the end of the EnhancedQualityMetricsCalculator class")
            return False
        
        # インデントを見つける
        lines = content.split('\n')
        indent = ""
        for line in lines:
            if line.strip().startswith("def ") and "self" in line:
                indent = " " * (len(line) - len(line.lstrip()))
                break
        
        # 追加するメソッド
        methods_to_add = f"""
{indent}def calculate_category_quality_scores(self) -> Dict[str, float]:
{indent}    \"\"\"
{indent}    カテゴリ別の品質スコアを計算。
{indent}    
{indent}    完全性（Completeness）: 欠損値や必須項目の充足度
{indent}    正確性（Accuracy）: 値の範囲や形式の正確さ
{indent}    一貫性（Consistency）: 時間的・空間的な整合性
{indent}    
{indent}    Returns
{indent}    -------
{indent}    Dict[str, float]
{indent}        カテゴリ別のスコア
{indent}    \"\"\"
{indent}    total_records = len(self.data)
{indent}    if total_records == 0:
{indent}        return {{
{indent}            "completeness": 100.0,
{indent}            "accuracy": 100.0,
{indent}            "consistency": 100.0
{indent}        }}
{indent}    
{indent}    # カテゴリごとの問題数をカウント
{indent}    completeness_issues = len(self.problematic_indices.get("missing_data", []))
{indent}    accuracy_issues = len(self.problematic_indices.get("out_of_range", []))
{indent}    consistency_issues = len(self.problematic_indices.get("duplicates", [])) + \\
{indent}                         len(self.problematic_indices.get("spatial_anomalies", [])) + \\
{indent}                         len(self.problematic_indices.get("temporal_anomalies", []))
{indent}    
{indent}    # カラム数（欠損値チェック用）
{indent}    total_fields = len(self.data.columns) * total_records
{indent}    
{indent}    # スコアの計算
{indent}    completeness_score = max(0, 100 - (completeness_issues * 100 / total_fields))
{indent}    accuracy_score = max(0, 100 - (accuracy_issues * 100 / total_records))
{indent}    consistency_score = max(0, 100 - (consistency_issues * 100 / total_records))
{indent}    
{indent}    return {{
{indent}        "completeness": round(completeness_score, 1),
{indent}        "accuracy": round(accuracy_score, 1),
{indent}        "consistency": round(consistency_score, 1)
{indent}    }}

{indent}def generate_quality_score_visualization(self):
{indent}    \"\"\"
{indent}    品質スコアのゲージチャートとカテゴリ別バーチャートを生成
{indent}    
{indent}    この機能を使用するにはplotlyが必要です。
{indent}    
{indent}    Returns
{indent}    -------
{indent}    Tuple
{indent}        ゲージチャートとバーチャート
{indent}    \"\"\"
{indent}    try:
{indent}        import plotly.graph_objects as go
{indent}        from plotly.subplots import make_subplots
{indent}    except ImportError:
{indent}        print("plotly モジュールをインポートできませんでした。視覚化機能は利用できません。")
{indent}        # ダミーオブジェクトを返す（エラー防止用）
{indent}        class DummyFigure:
{indent}            def update_layout(self, *args, **kwargs): pass
{indent}            def add_annotation(self, *args, **kwargs): pass
{indent}            def add_shape(self, *args, **kwargs): pass
{indent}        return DummyFigure(), DummyFigure()
{indent}    
{indent}    # 品質スコアを取得
{indent}    quality_scores = self.calculate_quality_scores()
{indent}    
{indent}    # ゲージチャートを生成（総合スコア用）
{indent}    gauge_chart = go.Figure(go.Indicator(
{indent}        mode="gauge+number",
{indent}        value=quality_scores["total"],
{indent}        title={{"text": "データ品質スコア", "font": {{"size": 24}}}},
{indent}        number={{"font": {{"size": 32}}, "color": self._get_score_color(quality_scores["total"])}},
{indent}        gauge={{
{indent}            "axis": {{"range": [0, 100], "tickwidth": 1, "tickcolor": "darkblue"}},
{indent}            "bar": {{"color": self._get_score_color(quality_scores["total"])}},
{indent}            "bgcolor": "white",
{indent}            "borderwidth": 2,
{indent}            "bordercolor": "gray",
{indent}            "steps": [
{indent}                {{"range": [0, 50], "color": "#FFCCCC"}},  # 赤系 - 低品質
{indent}                {{"range": [50, 75], "color": "#FFEEAA"}},  # 黄系 - 中品質
{indent}                {{"range": [75, 90], "color": "#CCFFCC"}},  # 緑系 - 高品質
{indent}                {{"range": [90, 100], "color": "#AAFFAA"}}  # 濃い緑系 - 非常に高品質
{indent}            ],
{indent}            "threshold": {{
{indent}                "line": {{"color": "black", "width": 4}},
{indent}                "thickness": 0.75,
{indent}                "value": quality_scores["total"]
{indent}            }}
{indent}        }}
{indent}    ))
{indent}    
{indent}    # レイアウト設定
{indent}    gauge_chart.update_layout(
{indent}        height=300,
{indent}        margin=dict(t=40, b=0, l=40, r=40),
{indent}        paper_bgcolor="white",
{indent}        font={{"family": "Arial", "size": 12}}
{indent}    )
{indent}    
{indent}    # ベストプラクティスの追加
{indent}    if quality_scores["total"] >= 90:
{indent}        gauge_chart.add_annotation(
{indent}            x=0.5, y=0.7,
{indent}            text="高品質",
{indent}            showarrow=False,
{indent}            font={{"size": 16, "color": "green"}},
{indent}            align="center"
{indent}        )
{indent}    elif quality_scores["total"] < 50:
{indent}        gauge_chart.add_annotation(
{indent}            x=0.5, y=0.7,
{indent}            text="要改善",
{indent}            showarrow=False,
{indent}            font={{"size": 16, "color": "red"}},
{indent}            align="center"
{indent}        )
{indent}    
{indent}    # カテゴリ別バーチャートを生成
{indent}    categories = ["completeness", "accuracy", "consistency"]
{indent}    values = [quality_scores[cat] for cat in categories]
{indent}    
{indent}    # カテゴリ名の日本語対応
{indent}    category_names = {{
{indent}        "completeness": "完全性",
{indent}        "accuracy": "正確性",
{indent}        "consistency": "一貫性"
{indent}    }}
{indent}    # カテゴリ別の色設定
{indent}    bar_colors = [
{indent}        self._get_score_color(values[0]),
{indent}        self._get_score_color(values[1]),
{indent}        self._get_score_color(values[2])
{indent}    ]
{indent}    
{indent}    display_categories = [category_names[cat] for cat in categories]
{indent}    
{indent}    bar_chart = go.Figure(data=[
{indent}        go.Bar(
{indent}            x=display_categories,
{indent}            y=values,
{indent}            marker_color=bar_colors,
{indent}            text=[f"{{v:.1f}}" for v in values],
{indent}            textposition="auto",
{indent}            hoverinfo="text",
{indent}            hovertext=[
{indent}                f"完全性スコア: {{values[0]:.1f}}<br>欠損値や必須項目の充足度",
{indent}                f"正確性スコア: {{values[1]:.1f}}<br>値の範囲や形式の正確さ",
{indent}                f"一貫性スコア: {{values[2]:.1f}}<br>時間的・空間的な整合性"
{indent}            ]
{indent}        )
{indent}    ])
{indent}    
{indent}    # 目標ラインの追加（品質目標：90点）
{indent}    bar_chart.add_shape(
{indent}        type="line",
{indent}        x0=-0.5, y0=90, x1=2.5, y1=90,
{indent}        line=dict(color="green", width=2, dash="dash"),
{indent}        name="品質目標"
{indent}    )
{indent}    
{indent}    bar_chart.update_layout(
{indent}        title={{
{indent}            "text": "カテゴリ別品質スコア",
{indent}            "y": 0.9,
{indent}            "x": 0.5,
{indent}            "xanchor": "center",
{indent}            "yanchor": "top"
{indent}        }},
{indent}        yaxis={{
{indent}            "title": "品質スコア",
{indent}            "range": [0, 105],
{indent}            "tickvals": [0, 25, 50, 75, 90, 100],
{indent}            "ticktext": ["0", "25", "50", "75", "90", "100"],
{indent}            "gridcolor": "lightgray"
{indent}        }},
{indent}        height=350,
{indent}        margin=dict(t=60, b=30, l=40, r=40),
{indent}        paper_bgcolor="white",
{indent}        plot_bgcolor="white",
{indent}        font={{"family": "Arial", "size": 12}},
{indent}        showlegend=False
{indent}    )
{indent}    
{indent}    return gauge_chart, bar_chart
"""
        
        # 修正内容を適用
        if class_end != -1:
            content_lines = content.split('\n')
            content_lines.insert(class_end, methods_to_add)
            content = '\n'.join(content_lines)
        else:
            # クラスの終わりが見つからなかった場合はファイルの末尾に追加
            content += methods_to_add
    
        # 修正したファイルを保存
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    print(f"Enhanced quality metrics calculator fixed successfully")
    return True

if __name__ == "__main__":
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    file_path = os.path.join(root_dir, "sailing_data_processor", "validation", "quality_metrics_integration.py")
    
    if fix_enhanced_quality_metrics_calculator(file_path):
        print("Success!")
    else:
        print("Failed to fix enhanced quality metrics calculator.")
        sys.exit(1)
