# -*- coding: utf-8 -*-
"""
sailing_data_processor.reporting.exporters.image_exporter

高品質な画像を生成するエクスポーターモジュール
"""

import os
import logging
from pathlib import Path
import datetime
import tempfile
from typing import Dict, List, Any, Optional, Union, BinaryIO, TextIO
import io
import base64

# ベースクラスのインポート
from sailing_data_processor.reporting.exporters.base_exporter import BaseExporter

# 画像処理ライブラリ
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

class ImageExporter(BaseExporter):
    """
    画像エクスポーター
    
    セーリングデータ分析結果を高品質な画像として出力します。
    """
    
    def __init__(self, **options):
        """初期化"""
        super().__init__(**options)
        
        # 画像デフォルトオプション
        image_defaults = {
            "format": "png",  # 'png', 'jpeg', 'svg'
            "dpi": 300,
            "width": 1200,
            "height": 800,
            "background_color": "white",
            "transparent": False,
            "quality": 95,  # JPEGの場合の品質
            "content_type": "chart",  # 'chart', 'map', 'combined'
            "chart_type": "line",  # 'line', 'bar', 'scatter', 'pie'
            "map_type": "track",  # 'track', 'heatmap'
            "include_title": True,
            "include_legend": True,
            "include_grid": True,
            "include_timestamp": True,
            "font_family": "sans-serif",
            "title_font_size": 16,
            "axis_font_size": 12,
            "tick_font_size": 10,
            "legend_font_size": 10,
            "color_scheme": "default",  # 'default', 'viridis', 'plasma', 'inferno', 'magma', 'cividis'
            "style": "default",  # 'default', 'seaborn', 'ggplot', 'bmh', 'dark_background', 'fivethirtyeight'
        }
        
        self.options.update(image_defaults)
        self.options.update(options)
        
        # 画像生成機能のチェック
        self._check_image_libraries()
    
    def _check_image_libraries(self):
        """画像生成ライブラリのチェック"""
        # 必要なライブラリのチェック
        if not MATPLOTLIB_AVAILABLE:
            self.add_warning("Matplotlibがインストールされていないため、一部の画像生成機能が制限されます。pip install matplotlib を実行してください。")
        
        if not PIL_AVAILABLE:
            self.add_warning("PILがインストールされていないため、一部の画像処理機能が制限されます。pip install pillow を実行してください。")
        
        if not NUMPY_AVAILABLE:
            self.add_warning("NumPyがインストールされていないため、一部の機能が制限されます。pip install numpy を実行してください。")
        
        if not PANDAS_AVAILABLE:
            self.add_warning("pandasがインストールされていないため、一部の機能が制限されます。pip install pandas を実行してください。")
        
        # スタイルの設定
        style = self.options.get("style", "default")
        if MATPLOTLIB_AVAILABLE and style != "default":
            try:
                plt.style.use(style)
            except:
                self.add_warning(f"指定されたスタイル '{style}' が見つかりません。デフォルトスタイルを使用します。")
                plt.style.use("default")
    
    def export(self, data, template=None, **kwargs):
        """
        データを画像としてエクスポート
        
        Parameters
        ----------
        data : Any
            エクスポートするデータ
        template : Optional[str]
            使用するテンプレート名または画像テンプレートのパス
        **kwargs : dict
            追加のパラメータ
            
        Returns
        -------
        str
            出力ファイルのパス
        """
        if not self.validate_options():
            self.add_error("無効なオプションが指定されています。")
            return None
        
        # 必要なライブラリのチェック
        if not MATPLOTLIB_AVAILABLE and not PIL_AVAILABLE:
            self.add_error("画像生成に必要なライブラリがインストールされていません。pip install matplotlib pillow のいずれかを実行してください。")
            return None
        
        # 出力パスの処理
        output_path = kwargs.get("output_path", self.options.get("output_path", ""))
        if not output_path:
            # パスが指定されていない場合は一時ファイルを作成
            output_format = self.options.get("format", "png")
            output_path = os.path.join(
                tempfile.mkdtemp(),
                self.generate_filename(data, output_format)
            )
        
        # ディレクトリの存在確認と作成
        self.ensure_directory(output_path)
        
        try:
            # コンテンツタイプに応じた画像生成
            content_type = self.options.get("content_type", "chart")
            
            if content_type == "chart":
                # チャート画像の生成
                image_data = self._generate_chart_image(data, **kwargs)
            elif content_type == "map":
                # マップ画像の生成
                image_data = self._generate_map_image(data, **kwargs)
            elif content_type == "combined":
                # 複合画像の生成
                image_data = self._generate_combined_image(data, **kwargs)
            else:
                self.add_error(f"未対応のコンテンツタイプ: {content_type}")
                return None
            
            if image_data is None:
                return None
            
            # 画像の保存
            if isinstance(output_path, (str, Path)):
                # ファイルへの保存
                with open(output_path, 'wb') as f:
                    f.write(image_data)
                return str(output_path)
            elif hasattr(output_path, "write"):
                # ファイルオブジェクトへの書き込み
                output_path.write(image_data)
                return None
            
        except Exception as e:
            self.add_error(f"画像生成中にエラーが発生しました: {str(e)}")
            logger.error(f"Image generation failed: {str(e)}", exc_info=True)
            return None
    
    def _generate_chart_image(self, data, **kwargs):
        """
        チャート画像を生成
        
        Parameters
        ----------
        data : Any
            エクスポートするデータ
        **kwargs : dict
            追加のパラメータ
            
        Returns
        -------
        bytes
            画像データ
        """
        if not MATPLOTLIB_AVAILABLE:
            self.add_error("チャート生成にはmatplotlibライブラリが必要です。pip install matplotlib を実行してください。")
            return None
        
        if not hasattr(data, 'data') or not PANDAS_AVAILABLE:
            self.add_error("チャート生成にはpandasのDataFrameが必要です。")
            return None
        
        df = data.data
        
        # 図のサイズと解像度の設定
        width = self.options.get("width", 1200) / 100
        height = self.options.get("height", 800) / 100
        dpi = self.options.get("dpi", 300)
        
        # 図の作成
        fig, ax = plt.subplots(figsize=(width, height), dpi=dpi)
        
        # チャートタイプの取得
        chart_type = self.options.get("chart_type", "line")
        
        # タイトルの設定
        if self.options.get("include_title", True):
            title = kwargs.get("title", self.options.get("title", ""))
            
            # データのメタデータからタイトルを設定（タイトルが指定されていない場合）
            if not title and hasattr(data, 'metadata') and isinstance(data.metadata, dict):
                if 'name' in data.metadata:
                    title = f"セーリングデータ: {data.metadata['name']}"
                elif 'date' in data.metadata:
                    title = f"セーリングデータ: {data.metadata['date']}"
            
            # デフォルトタイトル
            if not title:
                title = "セーリングデータ分析チャート"
            
            plt.title(title, fontsize=self.options.get("title_font_size", 16))
        
        # グリッドの設定
        if self.options.get("include_grid", True):
            plt.grid(True, alpha=0.3)
        
        # チャートの作成（チャートタイプに応じた処理）
        if chart_type == "line":
            # 線グラフ
            self._create_line_chart(df, ax, **kwargs)
        elif chart_type == "bar":
            # 棒グラフ
            self._create_bar_chart(df, ax, **kwargs)
        elif chart_type == "scatter":
            # 散布図
            self._create_scatter_chart(df, ax, **kwargs)
        elif chart_type == "pie":
            # 円グラフ
            self._create_pie_chart(df, ax, **kwargs)
        else:
            self.add_error(f"未対応のチャートタイプ: {chart_type}")
            plt.close(fig)
            return None
        
        # 凡例の設定
        if self.options.get("include_legend", True):
            plt.legend(fontsize=self.options.get("legend_font_size", 10))
        
        # タイムスタンプの追加
        if self.options.get("include_timestamp", True):
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            plt.figtext(0.01, 0.01, f"生成日時: {timestamp}", fontsize=8, alpha=0.7)
        
        # 背景の設定
        if self.options.get("transparent", False):
            fig.patch.set_alpha(0)
        else:
            fig.patch.set_facecolor(self.options.get("background_color", "white"))
        
        # レイアウトの調整
        plt.tight_layout()
        
        # 画像形式の設定
        output_format = self.options.get("format", "png")
        
        # 画像の保存（バイトストリームに）
        buffer = io.BytesIO()
        
        if output_format.lower() == "svg":
            plt.savefig(buffer, format="svg", transparent=self.options.get("transparent", False))
        else:
            plt.savefig(buffer, format=output_format, 
                      dpi=dpi, 
                      transparent=self.options.get("transparent", False),
                      bbox_inches="tight")
        
        plt.close(fig)
        
        # バッファから画像データを取得
        buffer.seek(0)
        image_data = buffer.getvalue()
        buffer.close()
        
        return image_data
    
    def _create_line_chart(self, df, ax, **kwargs):
        """
        線グラフの作成
        
        Parameters
        ----------
        df : pandas.DataFrame
            データフレーム
        ax : matplotlib.axes.Axes
            軸オブジェクト
        **kwargs : dict
            追加のパラメータ
        """
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
                    if col != x_column and pd.api.types.is_numeric_dtype(df[col]):
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
        
        ax.set_xlabel(x_label, fontsize=self.options.get("axis_font_size", 12))
        ax.set_ylabel(y_label, fontsize=self.options.get("axis_font_size", 12))
        
        # 軸の目盛りサイズ設定
        ax.tick_params(axis='both', labelsize=self.options.get("tick_font_size", 10))
    
    def _create_bar_chart(self, df, ax, **kwargs):
        """
        棒グラフの作成
        
        Parameters
        ----------
        df : pandas.DataFrame
            データフレーム
        ax : matplotlib.axes.Axes
            軸オブジェクト
        **kwargs : dict
            追加のパラメータ
        """
        # X軸データの設定
        x_column = kwargs.get("x_column", "timestamp" if "timestamp" in df.columns else df.columns[0])
        
        # Y軸データの設定
        y_column = kwargs.get("y_column", "speed" if "speed" in df.columns else df.columns[1] if len(df.columns) > 1 else None)
        
        if y_column is None or y_column not in df.columns:
            self.add_error(f"棒グラフ作成のためのY軸データが見つかりません: {y_column}")
            return
        
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
        
        ax.set_xlabel(x_label, fontsize=self.options.get("axis_font_size", 12))
        ax.set_ylabel(y_label, fontsize=self.options.get("axis_font_size", 12))
        
        # 軸の目盛りサイズ設定
        ax.tick_params(axis='both', labelsize=self.options.get("tick_font_size", 10))
    
    def _create_scatter_chart(self, df, ax, **kwargs):
        """
        散布図の作成
        
        Parameters
        ----------
        df : pandas.DataFrame
            データフレーム
        ax : matplotlib.axes.Axes
            軸オブジェクト
        **kwargs : dict
            追加のパラメータ
        """
        # X軸データの設定
        x_column = kwargs.get("x_column", "latitude" if "latitude" in df.columns else df.columns[0])
        
        # Y軸データの設定
        y_column = kwargs.get("y_column", "longitude" if "longitude" in df.columns else df.columns[1] if len(df.columns) > 1 else None)
        
        # カラー/サイズデータの設定
        color_column = kwargs.get("color_column", "speed" if "speed" in df.columns else None)
        size_column = kwargs.get("size_column", None)
        
        if y_column is None or y_column not in df.columns:
            self.add_error(f"散布図作成のためのY軸データが見つかりません: {y_column}")
            return
        
        # 散布図の作成
        if color_column and color_column in df.columns:
            scatter = ax.scatter(df[x_column], df[y_column], 
                                c=df[color_column], 
                                s=df[size_column] if size_column and size_column in df.columns else 30,
                                alpha=0.7,
                                cmap=self.options.get("color_scheme", "viridis"))
            
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
        
        ax.set_xlabel(x_label, fontsize=self.options.get("axis_font_size", 12))
        ax.set_ylabel(y_label, fontsize=self.options.get("axis_font_size", 12))
        
        # 軸の目盛りサイズ設定
        ax.tick_params(axis='both', labelsize=self.options.get("tick_font_size", 10))
        
        # 等縮尺の設定（緯度/経度の場合）
        if (x_column == "latitude" and y_column == "longitude") or kwargs.get("equal_aspect", False):
            ax.set_aspect('equal')
    
    def _create_pie_chart(self, df, ax, **kwargs):
        """
        円グラフの作成
        
        Parameters
        ----------
        df : pandas.DataFrame
            データフレーム
        ax : matplotlib.axes.Axes
            軸オブジェクト
        **kwargs : dict
            追加のパラメータ
        """
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
            ax.set_title('風向の分布', fontsize=self.options.get("title_font_size", 16))
        
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
                self.add_warning(f"カテゴリが多いため、上位10個のみ表示します。")
            
            labels = grouped.index.tolist()
            sizes = grouped.values.tolist()
            
            ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
            title = f"{category_column}の分布"
            if value_column:
                title += f" (by {value_column})"
            ax.set_title(title, fontsize=self.options.get("title_font_size", 16))
        
        else:
            self.add_error("円グラフ作成のためのカテゴリデータが指定されていません。")
            return
        
        # 円グラフを真円に
        ax.axis('equal')
    
    def _generate_map_image(self, data, **kwargs):
        """
        マップ画像を生成
        
        Parameters
        ----------
        data : Any
            エクスポートするデータ
        **kwargs : dict
            追加のパラメータ
            
        Returns
        -------
        bytes
            画像データ
        """
        if not MATPLOTLIB_AVAILABLE:
            self.add_error("マップ生成にはmatplotlibライブラリが必要です。pip install matplotlib を実行してください。")
            return None
        
        if not hasattr(data, 'data') or not PANDAS_AVAILABLE:
            self.add_error("マップ生成にはpandasのDataFrameが必要です。")
            return None
        
        df = data.data
        
        # 緯度・経度の確認
        if 'latitude' not in df.columns or 'longitude' not in df.columns:
            self.add_error("マップ生成には緯度(latitude)と経度(longitude)のデータが必要です。")
            return None
        
        # 図のサイズと解像度の設定
        width = self.options.get("width", 1200) / 100
        height = self.options.get("height", 800) / 100
        dpi = self.options.get("dpi", 300)
        
        # 図の作成
        fig, ax = plt.subplots(figsize=(width, height), dpi=dpi)
        
        # マップタイプの取得
        map_type = self.options.get("map_type", "track")
        
        # タイトルの設定
        if self.options.get("include_title", True):
            title = kwargs.get("title", self.options.get("title", ""))
            
            # データのメタデータからタイトルを設定（タイトルが指定されていない場合）
            if not title and hasattr(data, 'metadata') and isinstance(data.metadata, dict):
                if 'name' in data.metadata:
                    title = f"セーリングトラック: {data.metadata['name']}"
                elif 'date' in data.metadata:
                    title = f"セーリングトラック: {data.metadata['date']}"
            
            # デフォルトタイトル
            if not title:
                title = "セーリングトラックマップ"
            
            plt.title(title, fontsize=self.options.get("title_font_size", 16))
        
        # グリッドの設定
        if self.options.get("include_grid", True):
            plt.grid(True, alpha=0.3)
        
        # マップの作成（マップタイプに応じた処理）
        if map_type == "track":
            # トラックマップ
            self._create_track_map(df, ax, **kwargs)
        elif map_type == "heatmap":
            # ヒートマップ
            self._create_heatmap(df, ax, **kwargs)
        else:
            self.add_error(f"未対応のマップタイプ: {map_type}")
            plt.close(fig)
            return None
        
        # 凡例の設定
        if self.options.get("include_legend", True) and kwargs.get("add_legend", True):
            plt.legend(fontsize=self.options.get("legend_font_size", 10))
        
        # タイムスタンプの追加
        if self.options.get("include_timestamp", True):
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            plt.figtext(0.01, 0.01, f"生成日時: {timestamp}", fontsize=8, alpha=0.7)
        
        # 背景の設定
        if self.options.get("transparent", False):
            fig.patch.set_alpha(0)
        else:
            fig.patch.set_facecolor(self.options.get("background_color", "white"))
        
        # レイアウトの調整
        plt.tight_layout()
        
        # 画像形式の設定
        output_format = self.options.get("format", "png")
        
        # 画像の保存（バイトストリームに）
        buffer = io.BytesIO()
        
        if output_format.lower() == "svg":
            plt.savefig(buffer, format="svg", transparent=self.options.get("transparent", False))
        else:
            plt.savefig(buffer, format=output_format, 
                      dpi=dpi, 
                      transparent=self.options.get("transparent", False),
                      bbox_inches="tight")
        
        plt.close(fig)
        
        # バッファから画像データを取得
        buffer.seek(0)
        image_data = buffer.getvalue()
        buffer.close()
        
        return image_data
    
    def _create_track_map(self, df, ax, **kwargs):
        """
        トラックマップの作成
        
        Parameters
        ----------
        df : pandas.DataFrame
            データフレーム
        ax : matplotlib.axes.Axes
            軸オブジェクト
        **kwargs : dict
            追加のパラメータ
        """
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
                pass
        
        # 風向の表示（あれば）
        show_wind = kwargs.get("show_wind", True)
        if show_wind and 'wind_direction' in df.columns and 'wind_speed' in df.columns:
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
                self.add_warning(f"風向表示でエラーが発生しました: {str(e)}")
        
        # カラーマッピング（速度など）
        color_by = kwargs.get("color_by", "speed" if "speed" in df.columns else None)
        if color_by and color_by in df.columns:
            try:
                # カラーマップの設定
                color_map = kwargs.get("color_map", self.options.get("color_scheme", "viridis"))
                
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
                self.add_warning(f"カラーマッピングでエラーが発生しました: {str(e)}")
        
        # 軸ラベルの設定
        ax.set_xlabel('経度', fontsize=self.options.get("axis_font_size", 12))
        ax.set_ylabel('緯度', fontsize=self.options.get("axis_font_size", 12))
        
        # 軸の目盛りサイズ設定
        ax.tick_params(axis='both', labelsize=self.options.get("tick_font_size", 10))
        
        # 等縮尺の設定
        ax.set_aspect('equal')
    
    def _create_heatmap(self, df, ax, **kwargs):
        """
        ヒートマップの作成
        
        Parameters
        ----------
        df : pandas.DataFrame
            データフレーム
        ax : matplotlib.axes.Axes
            軸オブジェクト
        **kwargs : dict
            追加のパラメータ
        """
        # ヒートマップの値列
        value_column = kwargs.get("value_column", "speed" if "speed" in df.columns else None)
        
        if not value_column or value_column not in df.columns:
            self.add_error(f"ヒートマップ作成のための値列が指定されていません: {value_column}")
            return
        
        # カラーマップの設定
        color_map = kwargs.get("color_map", self.options.get("color_scheme", "viridis"))
        
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
        ax.set_xlabel('経度', fontsize=self.options.get("axis_font_size", 12))
        ax.set_ylabel('緯度', fontsize=self.options.get("axis_font_size", 12))
        
        # 軸の目盛りサイズ設定
        ax.tick_params(axis='both', labelsize=self.options.get("tick_font_size", 10))
        
        # 等縮尺の設定
        ax.set_aspect('equal')
    
    def _generate_combined_image(self, data, **kwargs):
        """
        複合画像を生成（チャートとマップの組み合わせ）
        
        Parameters
        ----------
        data : Any
            エクスポートするデータ
        **kwargs : dict
            追加のパラメータ
            
        Returns
        -------
        bytes
            画像データ
        """
        if not MATPLOTLIB_AVAILABLE:
            self.add_error("複合画像生成にはmatplotlibライブラリが必要です。pip install matplotlib を実行してください。")
            return None
        
        if not hasattr(data, 'data') or not PANDAS_AVAILABLE:
            self.add_error("複合画像生成にはpandasのDataFrameが必要です。")
            return None
        
        df = data.data
        
        # 緯度・経度の確認
        if 'latitude' not in df.columns or 'longitude' not in df.columns:
            self.add_error("マップ部分の生成には緯度(latitude)と経度(longitude)のデータが必要です。")
            return None
        
        # 図のサイズと解像度の設定
        width = self.options.get("width", 1200) / 100
        height = self.options.get("height", 800) / 100
        dpi = self.options.get("dpi", 300)
        
        # サブプロットの構成
        layout = kwargs.get("layout", "2x1")  # デフォルトは2行1列
        
        if layout == "2x1":
            # 2行1列のレイアウト
            fig, axs = plt.subplots(2, 1, figsize=(width, height), dpi=dpi)
            
            # チャート（上段）
            chart_type = kwargs.get("chart_type", self.options.get("chart_type", "line"))
            if chart_type == "line":
                self._create_line_chart(df, axs[0], **kwargs)
            elif chart_type == "bar":
                self._create_bar_chart(df, axs[0], **kwargs)
            else:
                self._create_line_chart(df, axs[0], **kwargs)  # デフォルトは線グラフ
            
            # マップ（下段）
            map_type = kwargs.get("map_type", self.options.get("map_type", "track"))
            if map_type == "track":
                self._create_track_map(df, axs[1], add_legend=False, **kwargs)
            elif map_type == "heatmap":
                self._create_heatmap(df, axs[1], **kwargs)
            else:
                self._create_track_map(df, axs[1], add_legend=False, **kwargs)  # デフォルトはトラック
            
        elif layout == "1x2":
            # 1行2列のレイアウト
            fig, axs = plt.subplots(1, 2, figsize=(width, height), dpi=dpi)
            
            # マップ（左）
            map_type = kwargs.get("map_type", self.options.get("map_type", "track"))
            if map_type == "track":
                self._create_track_map(df, axs[0], add_legend=False, **kwargs)
            elif map_type == "heatmap":
                self._create_heatmap(df, axs[0], **kwargs)
            else:
                self._create_track_map(df, axs[0], add_legend=False, **kwargs)
            
            # チャート（右）
            chart_type = kwargs.get("chart_type", self.options.get("chart_type", "line"))
            if chart_type == "line":
                self._create_line_chart(df, axs[1], **kwargs)
            elif chart_type == "bar":
                self._create_bar_chart(df, axs[1], **kwargs)
            else:
                self._create_line_chart(df, axs[1], **kwargs)
            
        else:
            # 1行1列のレイアウト（グリッド）
            fig = plt.figure(figsize=(width, height), dpi=dpi)
            
            # グリッド定義
            gs = fig.add_gridspec(2, 2)
            
            # マップ（左上）
            ax1 = fig.add_subplot(gs[0, 0])
            self._create_track_map(df, ax1, add_legend=False, **kwargs)
            
            # 速度チャート（右上）
            ax2 = fig.add_subplot(gs[0, 1])
            self._create_line_chart(df, ax2, y_columns=["speed"] if "speed" in df.columns else None, **kwargs)
            
            # 風向チャート（左下）
            if 'wind_direction' in df.columns:
                ax3 = fig.add_subplot(gs[1, 0])
                self._create_pie_chart(df, ax3, **kwargs)
            
            # 風速チャート（右下）
            if 'wind_speed' in df.columns:
                ax4 = fig.add_subplot(gs[1, 1])
                self._create_line_chart(df, ax4, y_columns=["wind_speed"], **kwargs)
        
        # タイトルの設定
        if self.options.get("include_title", True):
            title = kwargs.get("title", self.options.get("title", ""))
            
            # データのメタデータからタイトルを設定（タイトルが指定されていない場合）
            if not title and hasattr(data, 'metadata') and isinstance(data.metadata, dict):
                if 'name' in data.metadata:
                    title = f"セーリングデータ分析: {data.metadata['name']}"
                elif 'date' in data.metadata:
                    title = f"セーリングデータ分析: {data.metadata['date']}"
            
            # デフォルトタイトル
            if not title:
                title = "セーリングデータ総合分析"
            
            fig.suptitle(title, fontsize=self.options.get("title_font_size", 16))
        
        # タイムスタンプの追加
        if self.options.get("include_timestamp", True):
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            plt.figtext(0.01, 0.01, f"生成日時: {timestamp}", fontsize=8, alpha=0.7)
        
        # 背景の設定
        if self.options.get("transparent", False):
            fig.patch.set_alpha(0)
        else:
            fig.patch.set_facecolor(self.options.get("background_color", "white"))
        
        # レイアウトの調整
        plt.tight_layout()
        if self.options.get("include_title", True):
            plt.subplots_adjust(top=0.9)  # タイトル用のスペース
        
        # 画像形式の設定
        output_format = self.options.get("format", "png")
        
        # 画像の保存（バイトストリームに）
        buffer = io.BytesIO()
        
        if output_format.lower() == "svg":
            plt.savefig(buffer, format="svg", transparent=self.options.get("transparent", False))
        else:
            plt.savefig(buffer, format=output_format, 
                      dpi=dpi, 
                      transparent=self.options.get("transparent", False),
                      bbox_inches="tight")
        
        plt.close(fig)
        
        # バッファから画像データを取得
        buffer.seek(0)
        image_data = buffer.getvalue()
        buffer.close()
        
        return image_data
    
    def validate_options(self):
        """
        オプションの検証
        
        Returns
        -------
        bool
            検証結果
        """
        # フォーマットの検証
        output_format = self.options.get("format", "png")
        if output_format.lower() not in ["png", "jpeg", "jpg", "svg", "pdf"]:
            self.add_warning(f"未対応の画像形式: {output_format}, 'png'を使用します。")
            self.options["format"] = "png"
        
        # コンテンツタイプの検証
        content_type = self.options.get("content_type", "chart")
        if content_type not in ["chart", "map", "combined"]:
            self.add_warning(f"未対応のコンテンツタイプ: {content_type}, 'chart'を使用します。")
            self.options["content_type"] = "chart"
        
        # チャートタイプの検証
        chart_type = self.options.get("chart_type", "line")
        if chart_type not in ["line", "bar", "scatter", "pie"]:
            self.add_warning(f"未対応のチャートタイプ: {chart_type}, 'line'を使用します。")
            self.options["chart_type"] = "line"
        
        # マップタイプの検証
        map_type = self.options.get("map_type", "track")
        if map_type not in ["track", "heatmap"]:
            self.add_warning(f"未対応のマップタイプ: {map_type}, 'track'を使用します。")
            self.options["map_type"] = "track"
        
        # スタイルの検証
        if MATPLOTLIB_AVAILABLE:
            style = self.options.get("style", "default")
            available_styles = plt.style.available
            if style != "default" and style not in available_styles:
                self.add_warning(f"未対応のスタイル: {style}, 'default'を使用します。")
                self.options["style"] = "default"
        
        return True
    
    def get_supported_formats(self):
        """
        サポートするフォーマットのリストを取得
        
        Returns
        -------
        List[str]
            サポートするフォーマットのリスト
        """
        return ["image", "png", "jpeg", "svg", "chart", "map"]
