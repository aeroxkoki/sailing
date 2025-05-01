# -*- coding: utf-8 -*-
"""
Module for HTML export functionality for the sailing data processor.
This module provides tools for generating HTML reports and visualizations.
"""

import os
import logging
import json
from pathlib import Path
import datetime
import tempfile
import shutil
import re
from typing import Dict, List, Any, Optional, Union, BinaryIO, TextIO

# ベースクラスのインポート
from sailing_data_processor.reporting.exporters.base_exporter import BaseExporter

# HTMLテンプレートエンジン
try:
    import jinja2
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False

logger = logging.getLogger(__name__)

class HTMLExporter(BaseExporter):
    """
    HTMLエクスポーター
    
    セーリングデータ分析結果をインタラクティブなHTMLレポートとして出力します。
    """
    
    def __init__(self, **options):
        """初期化"""
        super().__init__(**options)
        
        # HTMLデフォルトオプション
        html_defaults = {
            "theme": "default",
            "include_interactive": True,
            "include_print_css": True,
            "include_charts": True,
            "include_map": True,
            "include_summary": True,
            "include_data_table": True,
            "include_metadata": True,
            "include_navbar": True,
            "include_search": True,
            "include_filters": True,
            "css_framework": "bootstrap",  # bootstrap, bulma, tailwind, ...
            "self_contained": True,  # 全て1ファイルに含める
            "additional_scripts": [],
            "additional_styles": [],
            "template_search_path": None,
            "create_index": True,  # 複数ファイル作成時にインデックスページを作成
        }
        
        self.options.update(html_defaults)
        self.options.update(options)
        
        # テンプレートエンジンの設定
        self._setup_template_engine()
    
    def _setup_template_engine(self):
        """テンプレートエンジンのセットアップ"""
        # Jinja2が利用可能か確認
        if not JINJA2_AVAILABLE:
            self.add_warning("Jinja2テンプレートエンジンが利用できません。一部の機能が制限されます。pip install jinja2 を実行してください。")
        
        # テンプレート検索パスの設定
        self.template_search_path = self.options.get("template_search_path")
        
        # テンプレート検索パスが設定されていない場合、デフォルト場所を使用
        if not self.template_search_path:
            # パッケージのテンプレートディレクトリを使用
            package_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            template_dir = os.path.join(package_dir, "templates", "html")
            
            # ディレクトリが存在しない場合は作成
            if not os.path.exists(template_dir):
                os.makedirs(template_dir, exist_ok=True)
            
            self.template_search_path = template_dir
        
        # Jinja2環境のセットアップ
        if JINJA2_AVAILABLE:
            try:
                # ファイルシステムローダー
                file_loader = jinja2.FileSystemLoader(self.template_search_path)
                
                # パッケージローダー（デフォルトテンプレート用）
                try:
                    package_loader = jinja2.PackageLoader('sailing_data_processor.reporting', 'templates/html')
                    # 複数のローダーを組み合わせる
                    loader = jinja2.ChoiceLoader([file_loader, package_loader])
                except:
                    loader = file_loader
                
                # Jinja2環境の作成
                self.jinja_env = jinja2.Environment(
                    loader=loader,
                    autoescape=jinja2.select_autoescape(['html', 'xml']),
                    trim_blocks=True,
                    lstrip_blocks=True
                )
                
                # カスタムフィルターの登録
                self.jinja_env.filters['json'] = lambda obj: json.dumps(obj)
                
            except Exception as e:
                self.add_error(f"テンプレートエンジンの初期化中にエラーが発生しました: {str(e)}")
                logger.error(f"Template engine initialization failed: {str(e)}", exc_info=True)
                self.jinja_env = None
        else:
            self.jinja_env = None
    
    def export(self, data, template=None, **kwargs):
        """
        データをHTMLとしてエクスポート
        
        Parameters
        ----------
        data : Any
            エクスポートするデータ
        template : Optional[str]
            使用するテンプレート名またはパス
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
        
        # 出力パスの処理
        output_path = kwargs.get("output_path", self.options.get("output_path", ""))
        if not output_path:
            # パスが指定されていない場合は一時ファイルを作成
            output_path = os.path.join(
                tempfile.mkdtemp(),
                self.generate_filename(data, 'html')
            )
        
        try:
            # HTMLコンテンツの生成
            html_content = self._generate_html_content(data, template, **kwargs)
            
            # 出力ディレクトリの作成
            self.ensure_directory(output_path)
            
            # 自己完結型HTMLの場合
            if self.options.get("self_contained", True):
                # 単一ファイルとして出力
                if isinstance(output_path, (str, Path)):
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(html_content)
                elif hasattr(output_path, "write"):
                    # ファイルオブジェクトに直接書き込む
                    if hasattr(output_path, "encoding"):
                        output_path.write(html_content)
                    else:
                        output_path.write(html_content.encode('utf-8'))
            else:
                # 関連ファイルを含むディレクトリ構造を作成
                if isinstance(output_path, (str, Path)):
                    # 出力先ディレクトリ
                    output_dir = os.path.dirname(output_path)
                    
                    # リソースディレクトリの作成
                    resources_dir = os.path.join(output_dir, 'resources')
                    os.makedirs(resources_dir, exist_ok=True)
                    
                    # 必要なリソースファイルをコピー
                    self._copy_resources(resources_dir)
                    
                    # HTML内のリンクをリソースディレクトリに合わせて更新
                    html_content = self._update_resource_links(html_content, 'resources')
                    
                    # メインHTMLファイルの出力
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(html_content)
                else:
                    # ファイルオブジェクトの場合、自己完結型HTMLのみサポート
                    self.add_warning("ファイルオブジェクトへの出力では、自己完結型HTMLのみサポートされます。")
                    if hasattr(output_path, "encoding"):
                        output_path.write(html_content)
                    else:
                        output_path.write(html_content.encode('utf-8'))
            
            return str(output_path) if isinstance(output_path, (str, Path)) else None
            
        except Exception as e:
            self.add_error(f"HTML生成中にエラーが発生しました: {str(e)}")
            logger.error(f"HTML generation failed: {str(e)}", exc_info=True)
            return None
    
    def _generate_html_content(self, data, template=None, **kwargs):
        """
        HTML内容を生成
        
        Parameters
        ----------
        data : Any
            エクスポートするデータ
        template : Optional[str]
            テンプレート名またはパス
        **kwargs : dict
            追加のパラメータ
            
        Returns
        -------
        str
            HTML内容
        """
        # テンプレートの選択
        if template:
            template_path = template
        else:
            # デフォルトテンプレート
            template_name = self.options.get("theme", "default")
            template_path = f"{template_name}.html"
        
        # コンテキストデータの準備
        context = self._prepare_template_context(data, **kwargs)
        
        # テンプレートがパスで、Jinja2を使用しない場合
        if os.path.exists(template_path) and not JINJA2_AVAILABLE:
            # テンプレートファイルを読み込み、シンプルな文字列置換を実行
            return self._render_simple_template(template_path, context)
        
        # Jinja2が利用可能でテンプレートエンジンが初期化されている場合
        if JINJA2_AVAILABLE and self.jinja_env:
            try:
                # テンプレートの読み込み
                template = self.jinja_env.get_template(template_path)
                
                # テンプレートのレンダリング
                return template.render(**context)
            except jinja2.exceptions.TemplateNotFound:
                # テンプレートが見つからない場合はデフォルトテンプレートを使用
                self.add_warning(f"テンプレート '{template_path}' が見つかりません。デフォルトテンプレートを使用します。")
                return self._render_default_template(context)
            except Exception as e:
                # その他のエラー
                self.add_error(f"テンプレートのレンダリング中にエラーが発生しました: {str(e)}")
                logger.error(f"Template rendering failed: {str(e)}", exc_info=True)
                return self._render_default_template(context)
        else:
            # Jinja2が利用できない場合はデフォルトテンプレートを使用
            return self._render_default_template(context)
            
    def _prepare_template_context(self, data, **kwargs):
        """
        テンプレート用のコンテキストデータを準備
        
        Parameters
        ----------
        data : Any
            元データ
        **kwargs : dict
            追加のパラメータ
            
        Returns
        -------
        dict
            テンプレートコンテキスト
        """
        context = {
            'title': 'セーリングデータ分析レポート',
            'generated_date': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'options': self.options,
            'metadata': {},
            'data': None,
            'summary_stats': {},
            'charts_data': [],
            'map_data': {},
            'has_wind_data': False,
            'has_strategy_data': False,
            'additional_data': {},
        }
        
        # タイトルの設定
        if 'title' in kwargs:
            context['title'] = kwargs['title']
        elif 'title' in self.options:
            context['title'] = self.options['title']
        
        # データの処理
        if hasattr(data, 'metadata') and isinstance(data.metadata, dict):
            context['metadata'] = data.metadata
            
            # タイトルの更新（メタデータに名前があれば）
            if 'name' in data.metadata and not 'title' in kwargs:
                context['title'] = f"{context['title']} - {data.metadata['name']}"
        
        # データフレームの処理
        if hasattr(data, 'data'):
            # DataFrameの有無確認
            try:
                import pandas as pd
                if isinstance(data.data, pd.DataFrame):
                    # 基本的なデータ情報の提供
                    df = data.data
                    context['data'] = {
                        'columns': df.columns.tolist(),
                        'rows': df.head(100).to_dict('records'),
                        'total_rows': len(df),
                    }
                    
                    # サマリー統計の計算
                    context['summary_stats'] = self._calculate_summary_stats(df)
                    
                    # チャート・マップデータの準備（必要に応じて）
                    if self.options.get('include_charts', True):
                        context['charts_data'] = self._prepare_charts_data(df)
                    
                    if self.options.get('include_map', True):
                        context['map_data'] = self._prepare_map_data(df)
                    
                    # 風データの有無確認
                    context['has_wind_data'] = 'wind_speed' in df.columns and 'wind_direction' in df.columns
                    
                    # 戦略データの有無確認
                    context['has_strategy_data'] = 'strategy_point' in df.columns or 'tack' in df.columns
            except ImportError:
                self.add_warning("pandasがインストールされていないため、データ処理が制限されています。")
            except Exception as e:
                self.add_warning(f"データの処理中にエラーが発生しました: {str(e)}")
        
        # 追加データの処理
        if 'additional_data' in kwargs:
            context['additional_data'] = kwargs['additional_data']
        
        return context
        
    def _calculate_summary_stats(self, df):
        """
        基本的な統計情報を計算
        
        Parameters
        ----------
        df : pandas.DataFrame
            データフレーム
            
        Returns
        -------
        dict
            統計情報
        """
        import pandas as pd
        
        summary = {
            'count': len(df),
        }
        
        # 時間範囲（あれば）
        if 'timestamp' in df.columns:
            try:
                start_time = pd.to_datetime(df['timestamp'].min())
                end_time = pd.to_datetime(df['timestamp'].max())
                duration = end_time - start_time
                
                summary['time_range'] = {
                    'start': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'end': end_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'duration': str(duration),
                    'duration_seconds': duration.total_seconds(),
                }
            except:
                pass
        
        # 位置範囲（あれば）
        if 'latitude' in df.columns and 'longitude' in df.columns:
            summary['position_range'] = {
                'lat_min': float(df['latitude'].min()),
                'lat_max': float(df['latitude'].max()),
                'lon_min': float(df['longitude'].min()),
                'lon_max': float(df['longitude'].max()),
            }
        
        # 速度統計（あれば）
        if 'speed' in df.columns:
            summary['speed_stats'] = {
                'mean': float(df['speed'].mean()),
                'max': float(df['speed'].max()),
                'min': float(df['speed'].min()),
            }
        
        # 風統計（あれば）
        if 'wind_speed' in df.columns:
            summary['wind_stats'] = {
                'mean_speed': float(df['wind_speed'].mean()),
                'max_speed': float(df['wind_speed'].max()),
                'min_speed': float(df['wind_speed'].min()),
            }
        
        return summary
        
    def _prepare_charts_data(self, df):
        """
        チャートデータの準備
        
        Parameters
        ----------
        df : pandas.DataFrame
            データフレーム
            
        Returns
        -------
        list
            チャートデータのリスト
        """
        import pandas as pd
        charts = []
        
        # 時系列チャート（速度など）
        if 'timestamp' in df.columns and 'speed' in df.columns:
            charts.append({
                'id': 'speed_chart',
                'title': '速度の推移',
                'type': 'line',
                'x_label': '時間',
                'y_label': '速度',
                'data': {
                    'labels': df['timestamp'].dt.strftime('%H:%M:%S').tolist(),
                    'datasets': [{
                        'label': '速度',
                        'data': df['speed'].tolist(),
                        'borderColor': 'rgb(75, 192, 192)',
                        'tension': 0.1
                    }]
                }
            })
        
        # 風速チャート
        if 'timestamp' in df.columns and 'wind_speed' in df.columns:
            charts.append({
                'id': 'wind_chart',
                'title': '風速の推移',
                'type': 'line',
                'x_label': '時間',
                'y_label': '風速',
                'data': {
                    'labels': df['timestamp'].dt.strftime('%H:%M:%S').tolist(),
                    'datasets': [{
                        'label': '風速',
                        'data': df['wind_speed'].tolist(),
                        'borderColor': 'rgb(255, 99, 132)',
                        'tension': 0.1
                    }]
                }
            })
        
        # 風向チャート（扇形）
        if 'wind_direction' in df.columns:
            # 風向を30度ごとに集計
            bins = list(range(0, 361, 30))
            labels = [f"{b}-{b+30}" for b in bins[:-1]]
            
            wind_dir_counts = pd.cut(df['wind_direction'], bins=bins, labels=labels).value_counts()
            
            charts.append({
                'id': 'wind_direction_chart',
                'title': '風向の分布',
                'type': 'pie',
                'data': {
                    'labels': wind_dir_counts.index.tolist(),
                    'datasets': [{
                        'data': wind_dir_counts.values.tolist(),
                        'backgroundColor': [
                            'rgb(255, 99, 132)',
                            'rgb(255, 159, 64)',
                            'rgb(255, 205, 86)',
                            'rgb(75, 192, 192)',
                            'rgb(54, 162, 235)',
                            'rgb(153, 102, 255)',
                            'rgb(201, 203, 207)',
                            'rgb(255, 99, 132)',
                            'rgb(255, 159, 64)',
                            'rgb(255, 205, 86)',
                            'rgb(75, 192, 192)',
                            'rgb(54, 162, 235)',
                        ]
                    }]
                }
            })
        
        return charts
        