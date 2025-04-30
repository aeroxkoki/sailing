# -*- coding: utf-8 -*-
"""
Violin plot implementation for distribution charts.
"""

from typing import Dict, List, Any, Optional
import numpy as np


def get_violin_data(chart, data: Any, value_key: str, category_key: Optional[str]) -> Dict[str, Any]:
    """
    バイオリンプロット用のデータを準備
    
    Parameters
    ----------
    chart : BaseChartElement
        チャート要素
    data : Any
        元データ
    value_key : str
        値キー
    category_key : Optional[str]
        カテゴリ/グループキー
        
    Returns
    -------
    Dict[str, Any]
        チャートデータ
    """
    # データ型に応じた処理
    values = []
    categories = []
    
    if isinstance(data, list):
        if len(data) > 0 and isinstance(data[0], dict):
            # 辞書のリストの場合
            for item in data:
                if value_key in item:
                    value = item[value_key]
                    if isinstance(value, (int, float)):
                        values.append(value)
                        if category_key and category_key in item:
                            categories.append(item[category_key])
        else:
            # 単純なリストの場合
            values = [v for v in data if isinstance(v, (int, float))]
    
    # 値がない場合は空のデータを返す
    if not values:
        return {"type": "violin", "data": {"labels": [], "datasets": []}}
    
    # カテゴリがある場合はカテゴリごとに処理
    if category_key and categories:
        # カテゴリのユニーク値を取得
        unique_categories = sorted(list(set(categories)))
        
        # カテゴリごとに値をグループ化
        category_values = {cat: [] for cat in unique_categories}
        for i, value in enumerate(values):
            if i < len(categories):
                cat = categories[i]
                if cat in category_values:
                    category_values[cat].append(value)
        
        # ラベルを設定
        labels = unique_categories
        
        # データを準備
        violin_data = []
        for category in unique_categories:
            violin_data.append(category_values[category])
        
        return {
            "type": "violin",
            "data": {
                "labels": labels,
                "datasets": [{
                    "label": chart.get_property("dataset_label", "分布"),
                    "data": violin_data,
                    "backgroundColor": "rgba(54, 162, 235, 0.6)",
                    "borderColor": "rgba(54, 162, 235, 1.0)",
                    "borderWidth": 1,
                    "outlierColor": "rgba(255, 99, 132, 0.8)",
                    "outlierRadius": 5
                }]
            }
        }
    
    else:
        # カテゴリなしの場合、単一のバイオリンプロット
        return {
            "type": "violin",
            "data": {
                "labels": ["全データ"],
                "datasets": [{
                    "label": chart.get_property("dataset_label", "分布"),
                    "data": [values],
                    "backgroundColor": "rgba(54, 162, 235, 0.6)",
                    "borderColor": "rgba(54, 162, 235, 1.0)",
                    "borderWidth": 1,
                    "outlierColor": "rgba(255, 99, 132, 0.8)",
                    "outlierRadius": 5
                }]
            }
        }
