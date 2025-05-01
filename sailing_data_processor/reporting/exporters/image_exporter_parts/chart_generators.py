# -*- coding: utf-8 -*-
"""
グラフ・チャート生成用モジュール

各種グラフやチャートを生成するための関数を提供します。
"""

import logging
from typing import Dict, List, Any, Optional, Union
import datetime

try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

logger = logging.getLogger(__name__)

def create_line_chart(df, ax, exporter=None, **kwargs):
    """
    線グラフの作成
    
    Parameters
    ----------
    df : pandas.DataFrame
        データフレーム
    ax : matplotlib.axes.Axes
        軸オブジェクト
    exporter : BaseExporter, optional
        エクスポーターインスタンス
    **kwargs : dict
        追加のパラメータ
    """
    if not MATPLOTLIB_AVAILABLE or not PANDAS_AVAILABLE:
        if exporter:
            exporter.add_error("線グラフ作成にはmatplotlibとpandasが必要です")
        return False
    
    options = kwargs.get("options", {})
    
    # X軸データの設定
    x_column = kwargs.get("x_column", "timestamp" if "timestamp" in df.columns else df.columns[0])
    
    # Y軸データの設定（複数列指定可能）
    y_columns = kwargs.get("y_columns", None)
    if y_columns is None:
        # 速度列があれば優先的に使用
        if "speed" in df.columns:
            y_columns = ["speed"]
        # 風速列があれば追加
        if "wind_speed" in df.columns and "speed" in df.columns:
            y_columns = ["speed", "wind_speed"]
        # それ以外の場合は数値列を探す
        else:
            y_columns = []
            for col in df.columns:
                if col \!= x_column and pd.api.types.is_numeric_dtype(df[col]):
                    y_columns.append(col)
            if not y_columns and len(df.columns) > 1:
                y_columns = [df.columns[1]]  # 少なくとも1つの列を使用
    
    # X軸がタイムスタンプの場合の処理
    if x_column == "timestamp" and pd.api.types.is_datetime64_any_dtype(df[x_column]):
        for y_column in y_columns:
            if y_column in df.columns:
                ax.plot(df[x_column], df[y_column], label=y_column)
        
        # X軸の日付フォーマット設定
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.gcf().autofmt_xdate()
    else:
        # 通常のX-Y軸データ
        for y_column in y_columns:
            if y_column in df.columns:
                ax.plot(df[x_column], df[y_column], label=y_column)
    
    # 軸ラベルの設定
    x_label = kwargs.get("x_label", x_column)
    y_label = kwargs.get("y_label", ", ".join(y_columns) if len(y_columns) <= 2 else "値")
    
    ax.set_xlabel(x_label, fontsize=options.get("axis_font_size", 12))
    ax.set_ylabel(y_label, fontsize=options.get("axis_font_size", 12))
    
    # 軸の目盛りサイズ設定
    ax.tick_params(axis='both', labelsize=options.get("tick_font_size", 10))
    
    return True

def create_bar_chart(df, ax, exporter=None, **kwargs):
    """
    棒グラフの作成
    
    Parameters
    ----------
    df : pandas.DataFrame
        データフレーム
    ax : matplotlib.axes.Axes
        軸オブジェクト
    exporter : BaseExporter, optional
        エクスポーターインスタンス
    **kwargs : dict
        追加のパラメータ
    """
    if not MATPLOTLIB_AVAILABLE or not PANDAS_AVAILABLE:
        if exporter:
            exporter.add_error("棒グラフ作成にはmatplotlibとpandasが必要です")
        return False
    
    options = kwargs.get("options", {})
    
    # X軸データの設定
    x_column = kwargs.get("x_column", "timestamp" if "timestamp" in df.columns else df.columns[0])
    
    # Y軸データの設定
    y_column = kwargs.get("y_column", "speed" if "speed" in df.columns else df.columns[1] if len(df.columns) > 1 else None)
    
    if y_column is None or y_column not in df.columns:
        if exporter:
            exporter.add_error(f"棒グラフ作成のためのY軸データが見つかりません: {y_column}")
        return False
    
    # 棒グラフの作成
    if pd.api.types.is_datetime64_any_dtype(df[x_column]):
        # 日時データの場合は日付でビニングする
        df_binned = df.copy()
        df_binned['date'] = df_binned[x_column].dt.date
        grouped = df_binned.groupby('date')[y_column].mean().reset_index()
        ax.bar(grouped['date'], grouped[y_column])
        
        # X軸の日付フォーマット設定
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.gcf().autofmt_xdate()
    else:
        # 数値/カテゴリデータの場合
        if len(df) > 30:
            # データポイントが多い場合は、ビニングまたはサンプリングする
            sample_rate = max(1, len(df) // 30)
            ax.bar(df[x_column][::sample_rate], df[y_column][::sample_rate])
        else:
            ax.bar(df[x_column], df[y_column])
    
    # 軸ラベルの設定
    x_label = kwargs.get("x_label", x_column)
    y_label = kwargs.get("y_label", y_column)
    
    ax.set_xlabel(x_label, fontsize=options.get("axis_font_size", 12))
    ax.set_ylabel(y_label, fontsize=options.get("axis_font_size", 12))
    
    # 軸の目盛りサイズ設定
    ax.tick_params(axis='both', labelsize=options.get("tick_font_size", 10))
    
    return True

def create_scatter_chart(df, ax, exporter=None, **kwargs):
    """
    散布図の作成
    
    Parameters
    ----------
    df : pandas.DataFrame
        データフレーム
    ax : matplotlib.axes.Axes
        軸オブジェクト
    exporter : BaseExporter, optional
        エクスポーターインスタンス
    **kwargs : dict
        追加のパラメータ
    """
    if not MATPLOTLIB_AVAILABLE or not PANDAS_AVAILABLE:
        if exporter:
            exporter.add_error("散布図作成にはmatplotlibとpandasが必要です")
        return False
    
    options = kwargs.get("options", {})
    
    # X軸データの設定
    x_column = kwargs.get("x_column", "latitude" if "latitude" in df.columns else df.columns[0])
    
    # Y軸データの設定
    y_column = kwargs.get("y_column", "longitude" if "longitude" in df.columns else df.columns[1] if len(df.columns) > 1 else None)
    
    # カラー/サイズデータの設定
    color_column = kwargs.get("color_column", "speed" if "speed" in df.columns else None)
    size_column = kwargs.get("size_column", None)
    
    if y_column is None or y_column not in df.columns:
        if exporter:
            exporter.add_error(f"散布図作成のためのY軸データが見つかりません: {y_column}")
        return False
    
    # 散布図の作成
    if color_column and color_column in df.columns:
        scatter = ax.scatter(df[x_column], df[y_column], 
                           c=df[color_column], 
                           s=df[size_column] if size_column and size_column in df.columns else 30,
                           alpha=0.7,
                           cmap=options.get("color_scheme", "viridis"))
        
        # カラーバーの追加
        cbar = plt.colorbar(scatter, ax=ax)
        cbar.set_label(color_column, rotation=270, labelpad=15)
    else:
        ax.scatter(df[x_column], df[y_column], 
                 s=df[size_column] if size_column and size_column in df.columns else 30,
                 alpha=0.7)
    
    # 軸ラベルの設定
    x_label = kwargs.get("x_label", x_column)
    y_label = kwargs.get("y_label", y_column)
    
    ax.set_xlabel(x_label, fontsize=options.get("axis_font_size", 12))
    ax.set_ylabel(y_label, fontsize=options.get("axis_font_size", 12))
    
    # 軸の目盛りサイズ設定
    ax.tick_params(axis='both', labelsize=options.get("tick_font_size", 10))
    
    # 等縮尺の設定（緯度/経度の場合）
    if (x_column == "latitude" and y_column == "longitude") or kwargs.get("equal_aspect", False):
        ax.set_aspect('equal')
    
    return True

def create_pie_chart(df, ax, exporter=None, **kwargs):
    """
    円グラフの作成
    
    Parameters
    ----------
    df : pandas.DataFrame
        データフレーム
    ax : matplotlib.axes.Axes
        軸オブジェクト
    exporter : BaseExporter, optional
        エクスポーターインスタンス
    **kwargs : dict
        追加のパラメータ
    """
    if not MATPLOTLIB_AVAILABLE or not PANDAS_AVAILABLE:
        if exporter:
            exporter.add_error("円グラフ作成にはmatplotlibとpandasが必要です")
        return False
    
    options = kwargs.get("options", {})
    
    # カテゴリ列と値列の設定
    category_column = kwargs.get("category_column", None)
    value_column = kwargs.get("value_column", None)
    
    # 風向データの特別処理
    if "wind_direction" in df.columns and category_column is None:
        # 風向をカテゴリ化
        direction_labels = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        df['direction_cat'] = pd.cut(
            df['wind_direction'] % 360, 
            bins=[0, 45, 90, 135, 180, 225, 270, 315, 360],
            labels=direction_labels,
            include_lowest=True
        )
        direction_counts = df['direction_cat'].value_counts()
        labels = direction_counts.index.tolist()
        sizes = direction_counts.values.tolist()
        
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
        ax.set_title('風向の分布', fontsize=options.get("title_font_size", 16))
    
    # 指定されたカテゴリと値でグラフ作成
    elif category_column and category_column in df.columns:
        if value_column and value_column in df.columns:
            # 値の合計をカテゴリごとに計算
            grouped = df.groupby(category_column)[value_column].sum()
        else:
            # カテゴリの出現回数をカウント
            grouped = df[category_column].value_counts()
        
        if len(grouped) > 10:
            # カテゴリが多すぎる場合は上位のみ表示
            grouped = grouped.sort_values(ascending=False).head(10)
            if exporter:
                exporter.add_warning(f"カテゴリが多いため、上位10個のみ表示します。")
        
        labels = grouped.index.tolist()
        sizes = grouped.values.tolist()
        
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
        title = f"{category_column}の分布"
        if value_column:
            title += f" (by {value_column})"
        ax.set_title(title, fontsize=options.get("title_font_size", 16))
    
    else:
        if exporter:
            exporter.add_error("円グラフ作成のためのカテゴリデータが指定されていません。")
        return False
    
    # 円グラフを真円に
    ax.axis('equal')
    
    return True
