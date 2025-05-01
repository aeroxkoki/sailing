# -*- coding: utf-8 -*-
"""
マップ生成用モジュール

GPSトラックやヒートマップなどのマップデータを可視化するための関数を提供します。
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

def create_track_map(df, ax, exporter=None, **kwargs):
    """
    トラックマップの作成
    
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
    
    Returns
    -------
    bool
        作成が成功したかどうか
    """
    if not MATPLOTLIB_AVAILABLE or not PANDAS_AVAILABLE:
        if exporter:
            exporter.add_error("マップ生成にはmatplotlibとpandasが必要です")
        return False
    
    options = kwargs.get("options", {})
    
    # トラックラインのプロット
    ax.plot(df['longitude'], df['latitude'], 'b-', linewidth=1.5, label='トラック')
    
    # 始点と終点のマーカー
    if len(df) > 0:
        ax.plot(df['longitude'].iloc[0], df['latitude'].iloc[0], 'go', markersize=8, label='開始点')
        ax.plot(df['longitude'].iloc[-1], df['latitude'].iloc[-1], 'ro', markersize=8, label='終了点')
    
    # 戦略ポイントの表示（あれば）
    if 'strategy_point' in df.columns:
        try:
            strategy_points = df[df['strategy_point'] == True]
            if not strategy_points.empty:
                ax.plot(strategy_points['longitude'], strategy_points['latitude'], 'y*', 
                       markersize=10, label='戦略ポイント')
        except:
            if exporter:
                exporter.add_warning("戦略ポイントの表示中にエラーが発生しました")
    
    # 風向の表示（あれば）
    show_wind = kwargs.get("show_wind", True)
    if show_wind and 'wind_direction' in df.columns and 'wind_speed' in df.columns and NUMPY_AVAILABLE:
        try:
            # 風ベクトルの表示（間引いて表示）
            sample_rate = max(1, len(df) // 20)  # 最大20本の矢印
            
            # 緯度/経度のスケールを取得（グリッドのサイズに合わせる）
            lon_range = df['longitude'].max() - df['longitude'].min()
            lat_range = df['latitude'].max() - df['latitude'].min()
            scale = min(lon_range, lat_range) / 30  # スケールの調整
            
            for i in range(0, len(df), sample_rate):
                # 風向をラジアンに変換
                wind_dir_rad = np.radians(90 - df['wind_direction'].iloc[i])  # 北を0度とする気象学的方向
                
                # 風速を使用してベクトルの長さを調整
                wind_speed = df['wind_speed'].iloc[i]
                dx = np.cos(wind_dir_rad) * wind_speed * scale
                dy = np.sin(wind_dir_rad) * wind_speed * scale
                
                ax.arrow(df['longitude'].iloc[i], df['latitude'].iloc[i], 
                        dx, dy, head_width=scale/2, head_length=scale, 
                        fc='red', ec='red', alpha=0.6)
        except Exception as e:
            if exporter:
                exporter.add_warning(f"風向表示でエラーが発生しました: {str(e)}")
    
    # カラーマッピング（速度など）
    color_by = kwargs.get("color_by", "speed" if "speed" in df.columns else None)
    if color_by and color_by in df.columns:
        try:
            # カラーマップの設定
            color_map = kwargs.get("color_map", options.get("color_scheme", "viridis"))
            
            # カラーでマッピングされたトラック
            points = ax.scatter(df['longitude'], df['latitude'], 
                               c=df[color_by], 
                               s=15, 
                               alpha=0.7,
                               cmap=color_map,
                               label=None)
            
            # カラーバーの追加
            cbar = plt.colorbar(points, ax=ax)
            cbar.set_label(color_by, rotation=270, labelpad=15)
            
            # カラートラックのため、元のトラックラインは非表示に
            ax.lines[0].set_alpha(0.3)
        except Exception as e:
            if exporter:
                exporter.add_warning(f"カラーマッピングでエラーが発生しました: {str(e)}")
    
    # 軸ラベルの設定
    ax.set_xlabel('経度', fontsize=options.get("axis_font_size", 12))
    ax.set_ylabel('緯度', fontsize=options.get("axis_font_size", 12))
    
    # 軸の目盛りサイズ設定
    ax.tick_params(axis='both', labelsize=options.get("tick_font_size", 10))
    
    # 等縮尺の設定
    ax.set_aspect('equal')
    
    return True

def create_heatmap(df, ax, exporter=None, **kwargs):
    """
    ヒートマップの作成
    
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
    
    Returns
    -------
    bool
        作成が成功したかどうか
    """
    if not MATPLOTLIB_AVAILABLE or not PANDAS_AVAILABLE:
        if exporter:
            exporter.add_error("ヒートマップ生成にはmatplotlibとpandasが必要です")
        return False
    
    options = kwargs.get("options", {})
    
    # ヒートマップの値列
    value_column = kwargs.get("value_column", "speed" if "speed" in df.columns else None)
    
    if not value_column or value_column not in df.columns:
        if exporter:
            exporter.add_error(f"ヒートマップ作成のための値列が指定されていません: {value_column}")
        return False
    
    # カラーマップの設定
    color_map = kwargs.get("color_map", options.get("color_scheme", "viridis"))
    
    # ヒートマップの作成
    points = ax.scatter(df['longitude'], df['latitude'], 
                       c=df[value_column], 
                       s=100,  # ポイントサイズを大きく
                       alpha=0.6,
                       cmap=color_map,
                       edgecolors='none')
    
    # カラーバーの追加
    cbar = plt.colorbar(points, ax=ax)
    cbar.set_label(value_column, rotation=270, labelpad=15)
    
    # トラックラインの追加（参考用）
    if kwargs.get("show_track", True):
        ax.plot(df['longitude'], df['latitude'], 'k-', linewidth=0.5, alpha=0.3)
    
    # 軸ラベルの設定
    ax.set_xlabel('経度', fontsize=options.get("axis_font_size", 12))
    ax.set_ylabel('緯度', fontsize=options.get("axis_font_size", 12))
    
    # 軸の目盛りサイズ設定
    ax.tick_params(axis='both', labelsize=options.get("tick_font_size", 10))
    
    # 等縮尺の設定
    ax.set_aspect('equal')
    
    return True
