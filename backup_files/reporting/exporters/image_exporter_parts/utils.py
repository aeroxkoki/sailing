# -*- coding: utf-8 -*-
"""
画像エクスポーター用ユーティリティ

画像生成に必要なライブラリのチェックや共通機能を提供します。
"""

import logging

# 画像処理ライブラリのインポートとフラグ設定
try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import matplotlib
    matplotlib.use('Agg')  # バックエンドの設定（GUIなし）
    import matplotlib.pyplot as plt
    from matplotlib.figure import Figure
    import matplotlib.dates as mdates
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

logger = logging.getLogger(__name__)

def check_image_libraries(options=None, exporter=None):
    """
    画像生成ライブラリのチェック
    
    Parameters
    ----------
    options : dict
        オプション設定
    exporter : BaseExporter
        エクスポーターオブジェクト
    
    Returns
    -------
    bool
        必要なライブラリが揃っているかどうか
    """
    all_available = True
    
    # 必要なライブラリのチェック
    if not MATPLOTLIB_AVAILABLE:
        if exporter:
            exporter.add_warning("Matplotlibがインストールされていないため、一部の画像生成機能が制限されます。pip install matplotlib を実行してください。")
        all_available = False
    
    if not PIL_AVAILABLE:
        if exporter:
            exporter.add_warning("PILがインストールされていないため、一部の画像処理機能が制限されます。pip install pillow を実行してください。")
        all_available = False
    
    if not NUMPY_AVAILABLE:
        if exporter:
            exporter.add_warning("NumPyがインストールされていないため、一部の機能が制限されます。pip install numpy を実行してください。")
        all_available = False
    
    if not PANDAS_AVAILABLE:
        if exporter:
            exporter.add_warning("pandasがインストールされていないため、一部の機能が制限されます。pip install pandas を実行してください。")
        all_available = False
    
    # スタイルの設定
    if MATPLOTLIB_AVAILABLE and options and 'style' in options:
        style = options.get("style", "default")
        if style != "default":
            try:
                plt.style.use(style)
            except:
                if exporter:
                    exporter.add_warning(f"指定されたスタイル '{style}' が見つかりません。デフォルトスタイルを使用します。")
                plt.style.use("default")
    
    return all_available
