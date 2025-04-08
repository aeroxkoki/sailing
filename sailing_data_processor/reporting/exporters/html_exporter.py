"""
sailing_data_processor.reporting.exporters.html_exporter

インタラクティブなHTMLレポートを生成するエクスポーターモジュール
"""

import os
import logging
import json
from pathlib import Path
import datetime
import tempfile
import shutil
import pkg_resources
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
    
    def _prepare_map_data(self, df):
        """
        マップデータの準備
        
        Parameters
        ----------
        df : pandas.DataFrame
            データフレーム
            
        Returns
        -------
        dict
            マップデータ
        """
        map_data = {
            'has_gps_data': False,
            'center': [0, 0],
            'track_points': [],
            'strategy_points': [],
        }
        
        # GPS座標の確認
        if 'latitude' in df.columns and 'longitude' in df.columns:
            map_data['has_gps_data'] = True
            
            # 地図の中心座標
            map_data['center'] = [
                df['latitude'].mean(),
                df['longitude'].mean()
            ]
            
            # トラックポイント（一定間隔でサンプリング）
            sample_rate = max(1, len(df) // 1000)  # 最大1000ポイント程度に制限
            
            track_points = []
            for idx, row in df.iloc[::sample_rate].iterrows():
                point = {
                    'lat': float(row['latitude']),
                    'lng': float(row['longitude']),
                }
                
                # 追加データがあれば追加
                if 'speed' in df.columns:
                    point['speed'] = float(row['speed'])
                
                if 'timestamp' in df.columns:
                    point['time'] = row['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                
                if 'wind_speed' in df.columns and 'wind_direction' in df.columns:
                    point['wind_speed'] = float(row['wind_speed'])
                    point['wind_direction'] = float(row['wind_direction'])
                
                track_points.append(point)
            
            map_data['track_points'] = track_points
            
            # 戦略ポイント（あれば）
            if 'strategy_point' in df.columns:
                strategy_points = []
                strategy_df = df[df['strategy_point'] == True].copy()
                
                for idx, row in strategy_df.iterrows():
                    point = {
                        'lat': float(row['latitude']),
                        'lng': float(row['longitude']),
                    }
                    
                    # 追加データがあれば追加
                    if 'speed' in df.columns:
                        point['speed'] = float(row['speed'])
                    
                    if 'timestamp' in df.columns:
                        point['time'] = row['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                    
                    if 'strategy_type' in df.columns:
                        point['type'] = row['strategy_type']
                    
                    if 'strategy_description' in df.columns:
                        point['description'] = row['strategy_description']
                    
                    strategy_points.append(point)
                
                map_data['strategy_points'] = strategy_points
        
        return map_data
    
    def _render_simple_template(self, template_path, context):
        """
        シンプルなテンプレート処理（Jinja2を使用しない場合）
        
        Parameters
        ----------
        template_path : str
            テンプレートファイルのパス
        context : dict
            テンプレートコンテキスト
            
        Returns
        -------
        str
            レンダリングされたHTML
        """
        # テンプレートの読み込み
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # シンプルな置換
        for key, value in context.items():
            if isinstance(value, str):
                template_content = template_content.replace(f"{{{{ {key} }}}}", value)
        
        # タイトルの置換
        template_content = template_content.replace("{{title}}", context.get('title', 'セーリングデータ分析レポート'))
        
        # 生成日時の置換
        template_content = template_content.replace("{{generated_date}}", context.get('generated_date', datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        
        return template_content
    
    def _render_default_template(self, context):
        """
        デフォルトテンプレートのレンダリング
        
        Parameters
        ----------
        context : dict
            テンプレートコンテキスト
            
        Returns
        -------
        str
            レンダリングされたHTML
        """
        title = context.get('title', 'セーリングデータ分析レポート')
        generated_date = context.get('generated_date', datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        # メタデータ
        metadata_html = "<table class='table table-bordered'><tr><th>項目</th><th>値</th></tr>"
        for key, value in context.get('metadata', {}).items():
            metadata_html += f"<tr><td>{key}</td><td>{value}</td></tr>"
        metadata_html += "</table>"
        
        # サマリー統計
        summary_stats = context.get('summary_stats', {})
        stats_html = "<table class='table table-bordered'><tr><th>項目</th><th>値</th></tr>"
        
        # データ数
        stats_html += f"<tr><td>データポイント数</td><td>{summary_stats.get('count', 'N/A')}</td></tr>"
        
        # 時間範囲
        if 'time_range' in summary_stats:
            time_range = summary_stats['time_range']
            stats_html += f"<tr><td>開始時刻</td><td>{time_range.get('start', 'N/A')}</td></tr>"
            stats_html += f"<tr><td>終了時刻</td><td>{time_range.get('end', 'N/A')}</td></tr>"
            stats_html += f"<tr><td>所要時間</td><td>{time_range.get('duration', 'N/A')}</td></tr>"
        
        # 位置範囲
        if 'position_range' in summary_stats:
            pos_range = summary_stats['position_range']
            stats_html += f"<tr><td>緯度範囲</td><td>{pos_range.get('lat_min', 'N/A'):.6f} - {pos_range.get('lat_max', 'N/A'):.6f}</td></tr>"
            stats_html += f"<tr><td>経度範囲</td><td>{pos_range.get('lon_min', 'N/A'):.6f} - {pos_range.get('lon_max', 'N/A'):.6f}</td></tr>"
        
        # 速度統計
        if 'speed_stats' in summary_stats:
            speed_stats = summary_stats['speed_stats']
            stats_html += f"<tr><td>平均速度</td><td>{speed_stats.get('mean', 'N/A'):.2f}</td></tr>"
            stats_html += f"<tr><td>最大速度</td><td>{speed_stats.get('max', 'N/A'):.2f}</td></tr>"
        
        stats_html += "</table>"
        
        # データテーブル
        data_table_html = ""
        data_info = context.get('data')
        if data_info and 'columns' in data_info and 'rows' in data_info:
            columns = data_info['columns']
            rows = data_info['rows']
            
            data_table_html = "<table class='table table-striped table-bordered'><thead><tr>"
            for col in columns:
                data_table_html += f"<th>{col}</th>"
            data_table_html += "</tr></thead><tbody>"
            
            for row in rows:
                data_table_html += "<tr>"
                for col in columns:
                    value = row.get(col, "")
                    # 日時データのフォーマット
                    if isinstance(value, datetime.datetime):
                        value = value.strftime('%Y-%m-%d %H:%M:%S')
                    data_table_html += f"<td>{value}</td>"
                data_table_html += "</tr>"
            
            data_table_html += "</tbody></table>"
        
        # チャートスクリプト
        charts_scripts = ""
        if context.get('options', {}).get('include_charts', True):
            charts_data = context.get('charts_data', [])
            
            if charts_data:
                # Chart.jsの読み込み
                charts_scripts += """
                <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
                <script>
                document.addEventListener('DOMContentLoaded', function() {
                """
                
                for chart in charts_data:
                    chart_id = chart.get('id', f"chart_{len(charts_scripts)}")
                    chart_type = chart.get('type', 'line')
                    chart_data = json.dumps(chart.get('data', {}))
                    
                    charts_scripts += f"""
                    // {chart.get('title', 'チャート')}
                    (function() {{
                        const ctx = document.getElementById('{chart_id}');
                        if (ctx) {{
                            new Chart(ctx, {{
                                type: '{chart_type}',
                                data: {chart_data},
                                options: {{
                                    responsive: true,
                                    plugins: {{
                                        title: {{
                                            display: true,
                                            text: '{chart.get('title', '')}'
                                        }}
                                    }},
                                    scales: {{
                                        x: {{
                                            title: {{
                                                display: true,
                                                text: '{chart.get('x_label', '')}'
                                            }}
                                        }},
                                        y: {{
                                            title: {{
                                                display: true,
                                                text: '{chart.get('y_label', '')}'
                                            }}
                                        }}
                                    }}
                                }}
                            }});
                        }}
                    }})();
                    """
                
                charts_scripts += """
                });
                </script>
                """
        
        # マップスクリプト
        map_script = ""
        if context.get('options', {}).get('include_map', True):
            map_data = context.get('map_data', {})
            
            if map_data.get('has_gps_data', False):
                # Leafletの読み込みとマップの初期化
                map_script += """
                <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
                <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
                <script>
                document.addEventListener('DOMContentLoaded', function() {
                    // マップの初期化
                    const map = L.map('map').setView([{center_lat}, {center_lng}], 13);
                    
                    // タイルレイヤーの追加
                    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    }).addTo(map);
                    
                    // トラックラインの描画
                    const trackPoints = {track_points};
                    const trackLine = L.polyline(trackPoints.map(p => [p.lat, p.lng]), {color: 'blue', weight: 3}).addTo(map);
                    
                    // マップをトラックに合わせる
                    map.fitBounds(trackLine.getBounds());
                    
                    // トラックポイントにポップアップを追加
                    trackPoints.forEach(function(point, index) {
                        if (index % 10 === 0) { // 間引いてマーカーを表示
                            let popupContent = `時刻: ${point.time || 'N/A'}<br>速度: ${point.speed || 'N/A'}`;
                            
                            if (point.wind_speed) {
                                popupContent += `<br>風速: ${point.wind_speed}<br>風向: ${point.wind_direction}°`;
                            }
                            
                            L.circleMarker([point.lat, point.lng], {radius: 3, color: 'blue', fillOpacity: 0.5})
                                .bindPopup(popupContent)
                                .addTo(map);
                        }
                    });
                    
                    // 戦略ポイントのマーカー追加
                    const strategyPoints = {strategy_points};
                    strategyPoints.forEach(function(point) {
                        let popupContent = `<strong>${point.type || '戦略ポイント'}</strong><br>
                                           時刻: ${point.time || 'N/A'}<br>
                                           速度: ${point.speed || 'N/A'}`;
                        
                        if (point.description) {
                            popupContent += `<br>${point.description}`;
                        }
                        
                        L.marker([point.lat, point.lng])
                            .bindPopup(popupContent)
                            .addTo(map);
                    });
                });
                </script>
                """.format(
                    center_lat=map_data.get('center', [0, 0])[0],
                    center_lng=map_data.get('center', [0, 0])[1],
                    track_points=json.dumps(map_data.get('track_points', [])),
                    strategy_points=json.dumps(map_data.get('strategy_points', []))
                )
        
        # チャートHTML
        charts_html = ""
        if context.get('options', {}).get('include_charts', True):
            charts_data = context.get('charts_data', [])
            
            if charts_data:
                for chart in charts_data:
                    chart_id = chart.get('id', f"chart_{len(charts_html)}")
                    charts_html += f"""
                    <div class="chart-container" style="position: relative; height:40vh; width:100%">
                        <canvas id="{chart_id}"></canvas>
                    </div>
                    """
        
        # マップHTML
        map_html = ""
        if context.get('options', {}).get('include_map', True):
            map_data = context.get('map_data', {})
            
            if map_data.get('has_gps_data', False):
                map_html = """
                <div id="map" style="height: 500px; width: 100%;"></div>
                """
        
        # 最終的なHTML
        html_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1, h2, h3 {{ color: #2c3e50; }}
        h1 {{ border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
        h2 {{ border-bottom: 1px solid #ddd; padding-bottom: 5px; margin-top: 30px; }}
        
        @media print {{
            body {{ font-size: 10pt; }}
            .page-break {{ page-break-before: always; }}
            table {{ page-break-inside: avoid; }}
            .no-print {{ display: none; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        <p>生成日時: {generated_date}</p>
        
        <div class="row">
            <div class="col-md-6">
                <h2>メタデータ</h2>
                {metadata_html}
            </div>
            <div class="col-md-6">
                <h2>データサマリー</h2>
                {stats_html}
            </div>
        </div>
        
        {map_html}
        
        <h2>チャート</h2>
        {charts_html}
        
        <div class="page-break"></div>
        
        <h2>データテーブル</h2>
        <p>以下は記録されたデータの最初の行です。</p>
        <div style="overflow-x: auto;">
            {data_table_html}
        </div>
        
        <h2>エクスポート情報</h2>
        <p>このレポートはセーリング戦略分析システムによって生成されました。</p>
        <p>生成日時: {generated_date}</p>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    {charts_scripts}
    {map_script}
</body>
</html>
""".format(
            title=title,
            generated_date=generated_date,
            metadata_html=metadata_html,
            stats_html=stats_html,
            data_table_html=data_table_html,
            charts_html=charts_html,
            charts_scripts=charts_scripts,
            map_html=map_html,
            map_script=map_script
        )
        
        return html_template
    
    def _copy_resources(self, resources_dir):
        """
        必要なリソースファイルをリソースディレクトリにコピー
        
        Parameters
        ----------
        resources_dir : str
            リソースディレクトリのパス
        """
        # CSSフレームワークの選択
        css_framework = self.options.get("css_framework", "bootstrap")
        
        # CSSファイルの作成
        css_dir = os.path.join(resources_dir, "css")
        os.makedirs(css_dir, exist_ok=True)
        
        # JavaScriptファイルの作成
        js_dir = os.path.join(resources_dir, "js")
        os.makedirs(js_dir, exist_ok=True)
        
        # 現在は処理なし（今後必要に応じて追加）
    
    def _update_resource_links(self, html_content, resource_root):
        """
        HTML内のリソースリンクを更新
        
        Parameters
        ----------
        html_content : str
            HTML内容
        resource_root : str
            リソースルートディレクトリ
            
        Returns
        -------
        str
            更新されたHTML内容
        """
        # CDNリンクをローカルリソースに置き換える場合はここで実装
        # 現在は処理なし（今後必要に応じて追加）
        return html_content
    
    def export_batch(self, data_items, output_dir=None, template=None, **kwargs):
        """
        複数のデータをバッチエクスポート
        
        Parameters
        ----------
        data_items : List[Any]
            エクスポートするデータのリスト
        output_dir : Optional[str]
            出力先ディレクトリ
        template : Optional[str]
            使用するテンプレート名
        **kwargs : dict
            追加のパラメータ
            
        Returns
        -------
        List[str]
            出力ファイルのパスリスト
        """
        if output_dir is None:
            output_dir = tempfile.mkdtemp()
        
        output_paths = []
        
        # 各データのエクスポート
        for i, data in enumerate(data_items):
            try:
                # ファイル名の生成
                filename = self.generate_filename(data, "html")
                
                # 出力パス
                output_path = os.path.join(output_dir, filename)
                
                # エクスポート実行
                result_path = self.export(data, template, output_path=output_path, **kwargs)
                
                if result_path:
                    output_paths.append(result_path)
            except Exception as e:
                self.add_error(f"データ {i+1} のエクスポート中にエラーが発生しました: {str(e)}")
                logger.error(f"Export failed for data {i+1}: {str(e)}", exc_info=True)
        
        # インデックスページの作成
        if self.options.get("create_index", True) and len(output_paths) > 1:
            try:
                index_path = os.path.join(output_dir, "index.html")
                self._create_index_page(output_paths, index_path)
                output_paths.insert(0, index_path)  # インデックスを先頭に追加
            except Exception as e:
                self.add_error(f"インデックスページの作成中にエラーが発生しました: {str(e)}")
                logger.error(f"Index page creation failed: {str(e)}", exc_info=True)
        
        return output_paths
    
    def _create_index_page(self, file_paths, index_path):
        """
        インデックスページの作成
        
        Parameters
        ----------
        file_paths : List[str]
            エクスポートされたファイルのパスリスト
        index_path : str
            インデックスファイルの出力パス
        """
        files = []
        
        for path in file_paths:
            # ファイル名の取得
            filename = os.path.basename(path)
            
            # メタデータの取得（可能であれば）
            title = filename
            description = ""
            
            # ファイルをHTMLとして読み込んでタイトルを抽出
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    
                    # タイトルタグから抽出
                    import re
                    title_match = re.search(r"<title>(.*?)</title>", content, re.IGNORECASE)
                    if title_match:
                        title = title_match.group(1)
                    
                    # h1タグから抽出
                    h1_match = re.search(r"<h1>(.*?)</h1>", content, re.IGNORECASE)
                    if h1_match:
                        description = h1_match.group(1)
            except:
                # エラーが発生した場合はファイル名をそのまま使用
                pass
            
            files.append({
                "filename": filename,
                "title": title,
                "description": description,
                "path": os.path.relpath(path, os.path.dirname(index_path))
            })
        
        # インデックスHTMLの生成
        title = "セーリング分析レポート一覧"
        
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1, h2, h3 {{ color: #2c3e50; }}
        h1 {{ border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
        .card {{ margin-bottom: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        <p>生成日時: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        
        <div class="row">
"""
        
        # ファイルリスト
        for file in files:
            html_content += f"""
            <div class="col-md-6 col-lg-4">
                <div class="card">
                    <div class="card-body">
                        <h5 class="card-title">{file["title"]}</h5>
                        <p class="card-text">{file["description"]}</p>
                        <a href="{file["path"]}" class="btn btn-primary">レポートを開く</a>
                    </div>
                </div>
            </div>
"""
        
        html_content += """
        </div>
        
        <hr>
        <p>このインデックスページはセーリング戦略分析システムによって生成されました。</p>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""
        
        # ファイルに書き込み
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(html_content)
    
    def validate_options(self):
        """
        オプションの検証
        
        Returns
        -------
        bool
            検証結果
        """
        # テーマの検証
        theme = self.options.get("theme", "default")
        theme_path = os.path.join(self.template_search_path, f"{theme}.html")
        
        if theme != "default" and not os.path.exists(theme_path) and JINJA2_AVAILABLE and self.jinja_env:
            try:
                self.jinja_env.get_template(f"{theme}.html")
            except jinja2.exceptions.TemplateNotFound:
                self.add_warning(f"テーマ '{theme}' が見つかりません。デフォルトテーマを使用します。")
                self.options["theme"] = "default"
        
        # CSSフレームワークの検証
        css_framework = self.options.get("css_framework", "bootstrap")
        if css_framework not in ["bootstrap", "bulma", "tailwind", "none"]:
            self.add_warning(f"未対応のCSSフレームワーク: {css_framework}, 'bootstrap'を使用します。")
            self.options["css_framework"] = "bootstrap"
        
        return True
    
    def get_supported_formats(self):
        """
        サポートするフォーマットのリストを取得
        
        Returns
        -------
        List[str]
            サポートするフォーマットのリスト
        """
        return ["html", "html_report", "html_interactive", "html_static"]
