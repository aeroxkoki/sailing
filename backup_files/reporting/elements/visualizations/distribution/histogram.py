# -*- coding: utf-8 -*-
"""
Histogram implementation for distribution charts.
"""

from typing import Dict, List, Any, Optional
import numpy as np


def get_histogram_data(chart, data: Any, value_key: str, category_key: Optional[str]) -> Dict[str, Any]:
    """
    ヒストグラム用のデータを準備
    
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
    # ビンの数を取得
    bin_count = chart.get_property("bin_count", 10)
    
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
        return {"type": "bar", "data": {"labels": [], "datasets": []}}
    
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
        
        # 共通のビン範囲を決定
        min_val = min(values)
        max_val = max(values)
        bin_width = (max_val - min_val) / bin_count
        
        # ビンの境界を計算
        bin_edges = [min_val + i * bin_width for i in range(bin_count + 1)]
        
        # ラベルを設定（ビンの中央値）
        labels = [(bin_edges[i] + bin_edges[i + 1]) / 2 for i in range(len(bin_edges) - 1)]
        labels = [f"{label:.2f}" for label in labels]
        
        # カテゴリごとにヒストグラムを計算
        datasets = []
        colors = chart._get_colors(len(unique_categories))
        
        for i, category in enumerate(unique_categories):
            cat_values = category_values[category]
            
            # 空のカテゴリはスキップ
            if not cat_values:
                continue
            
            # ヒストグラムのカウントを計算
            counts, _ = np.histogram(cat_values, bins=bin_edges)
            
            datasets.append({
                "label": str(category),
                "data": counts.tolist(),
                "backgroundColor": colors[i],
                "borderColor": colors[i].replace("0.6", "1.0"),
                "borderWidth": 1
            })
        
        return {
            "type": "bar",
            "data": {
                "labels": labels,
                "datasets": datasets
            }
        }
    
    else:
        # カテゴリなしの場合、単一のヒストグラムを計算
        min_val = min(values)
        max_val = max(values)
        bin_width = (max_val - min_val) / bin_count
        
        # ビンの境界を計算
        bin_edges = [min_val + i * bin_width for i in range(bin_count + 1)]
        
        # ラベルを設定（ビンの中央値）
        labels = [(bin_edges[i] + bin_edges[i + 1]) / 2 for i in range(len(bin_edges) - 1)]
        labels = [f"{label:.2f}" for label in labels]
        
        # ヒストグラムのカウントを計算
        counts, _ = np.histogram(values, bins=bin_edges)
        
        return {
            "type": "bar",
            "data": {
                "labels": labels,
                "datasets": [{
                    "label": chart.get_property("dataset_label", "頻度"),
                    "data": counts.tolist(),
                    "backgroundColor": "rgba(54, 162, 235, 0.6)",
                    "borderColor": "rgba(54, 162, 235, 1.0)",
                    "borderWidth": 1
                }]
            }
        }
