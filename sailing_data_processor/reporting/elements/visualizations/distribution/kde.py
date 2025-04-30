# -*- coding: utf-8 -*-
"""
KDE (Kernel Density Estimation) implementation for distribution charts.
"""

from typing import Dict, List, Any, Optional
import numpy as np


def get_kde_data(chart, data: Any, value_key: str, category_key: Optional[str]) -> Dict[str, Any]:
    """
    カーネル密度推定(KDE)用のデータを準備
    
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
    # 解像度（点の数）を取得
    resolution = chart.get_property("kde_resolution", 100)
    
    # バンド幅係数
    bandwidth_factor = chart.get_property("kde_bandwidth_factor", 1.0)
    
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
        return {"type": "line", "data": {"labels": [], "datasets": []}}
    
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
        
        # 共通のx軸の範囲を決定
        min_val = min(values)
        max_val = max(values)
        range_vals = max_val - min_val
        
        # 範囲を少し広げる
        x_min = min_val - range_vals * 0.05
        x_max = max_val + range_vals * 0.05
        
        # x軸の値を生成
        x_vals = np.linspace(x_min, x_max, resolution)
        
        # カテゴリごとにKDEを計算
        datasets = []
        colors = chart._get_colors(len(unique_categories))
        
        for i, category in enumerate(unique_categories):
            cat_values = category_values[category]
            
            # 空のカテゴリはスキップ
            if not cat_values:
                continue
            
            # KDEを計算（ガウシアンカーネルを使用）
            kde_values = gaussian_kde(cat_values, x_vals, bandwidth_factor)
            
            datasets.append({
                "label": str(category),
                "data": kde_values,
                "borderColor": colors[i],
                "backgroundColor": colors[i].replace("1.0", "0.2"),
                "borderWidth": 2,
                "fill": True,
                "tension": 0.4,
                "pointRadius": 0
            })
        
        return {
            "type": "line",
            "data": {
                "labels": x_vals.tolist(),
                "datasets": datasets
            }
        }
    
    else:
        # カテゴリなしの場合、単一のKDEを計算
        min_val = min(values)
        max_val = max(values)
        range_vals = max_val - min_val
        
        # 範囲を少し広げる
        x_min = min_val - range_vals * 0.05
        x_max = max_val + range_vals * 0.05
        
        # x軸の値を生成
        x_vals = np.linspace(x_min, x_max, resolution)
        
        # KDEを計算
        kde_values = gaussian_kde(values, x_vals, bandwidth_factor)
        
        return {
            "type": "line",
            "data": {
                "labels": x_vals.tolist(),
                "datasets": [{
                    "label": chart.get_property("dataset_label", "密度"),
                    "data": kde_values,
                    "borderColor": "rgba(54, 162, 235, 1.0)",
                    "backgroundColor": "rgba(54, 162, 235, 0.2)",
                    "borderWidth": 2,
                    "fill": True,
                    "tension": 0.4,
                    "pointRadius": 0
                }]
            }
        }


def gaussian_kde(data: List[float], x_grid: np.ndarray, bandwidth_factor: float = 1.0) -> List[float]:
    """
    ガウシアンカーネル密度推定を計算
    
    Parameters
    ----------
    data : List[float]
        データ値
    x_grid : np.ndarray
        評価するx座標のグリッド
    bandwidth_factor : float, optional
        バンド幅係数, by default 1.0
        
    Returns
    -------
    List[float]
        KDE値
    """
    # データをNumPy配列に変換
    data_np = np.array(data)
    
    # シルバーマンの経験則に基づくバンド幅の推定
    n = len(data_np)
    sigma = np.std(data_np)
    
    # サンプル数が少ない場合、分散が0の場合の対策
    if n < 2 or sigma < 1e-6:
        sigma = 1.0
    
    # バンド幅の計算（シルバーマンの公式）
    bandwidth = 0.9 * sigma * n**(-0.2) * bandwidth_factor
    
    # KDEの計算
    kde_values = []
    for x in x_grid:
        # 各データポイントからの距離を計算
        distances = (x - data_np) / bandwidth
        
        # ガウシアンカーネルを適用
        kernel_values = np.exp(-0.5 * distances**2) / (np.sqrt(2 * np.pi) * bandwidth)
        
        # KDE値の計算
        kde_value = np.sum(kernel_values) / n
        kde_values.append(kde_value)
    
    return kde_values
