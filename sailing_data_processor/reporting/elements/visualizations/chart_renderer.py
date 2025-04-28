# -*- coding: utf-8 -*-
"""
Module for data connector between map layers and data sources.
This module provides functions for binding and data transformation between layers and data sources.
"""

from typing import Dict, List, Any, Optional, Union, Tuple
import json
import html
import base64
from abc import ABC, abstractmethod
from io import BytesIO
import uuid

class BaseChartRenderer(ABC):
    """
    チャートレンダラーの基底クラス
    
    異なるグラフライブラリに対応する抽象化レイヤーを提供します。
    すべてのレンダラーは、この基底クラスを継承して実装します。
    """
    
    def __init__(self, chart_id: str, options: Dict[str, Any] = None):
        """
        初期化
        
        Parameters
        ----------
        chart_id : str
            チャートID
        options : Dict[str, Any], optional
            レンダラーオプション, by default None
        """
        self.chart_id = chart_id
        self.options = options or {}
    
    @abstractmethod
    def render(self, data: Dict[str, Any], width: str = "100%", height: str = "400px") -> str:
        """
        チャートをレンダリング
        
        Parameters
        ----------
        data : Dict[str, Any]
            チャートデータ
        width : str, optional
            幅, by default "100%"
        height : str, optional
            高さ, by default "400px"
            
        Returns
        -------
        str
            レンダリングされたHTML
        """
        pass
    
    @abstractmethod
    def get_required_libraries(self) -> List[str]:
        """
        必要なライブラリのURLリストを取得
        
        Returns
        -------
        List[str]
            ライブラリのURLリスト
        """
        pass
    
    def get_initialization_code(self, config_var: str = "config") -> str:
        """
        初期化用のJavaScriptコードを取得
        
        Parameters
        ----------
        config_var : str, optional
            設定変数名, by default "config"
            
        Returns
        -------
        str
            初期化コード
        """
        return ""


class PlotlyRenderer(BaseChartRenderer):
    """
    Plotlyを使用したチャートレンダラー
    
    インタラクティブなグラフの描画に適しています。
    """
    
    def __init__(self, chart_id: str, options: Dict[str, Any] = None):
        """
        初期化
        
        Parameters
        ----------
        chart_id : str
            チャートID
        options : Dict[str, Any], optional
            レンダラーオプション, by default None
        """
        super().__init__(chart_id, options)
    
    def render(self, data: Dict[str, Any], width: str = "100%", height: str = "400px") -> str:
        """
        チャートをレンダリング
        
        Parameters
        ----------
        data : Dict[str, Any]
            チャートデータ
        width : str, optional
            幅, by default "100%"
        height : str, optional
            高さ, by default "400px"
            
        Returns
        -------
        str
            レンダリングされたHTML
        """
        # Plotlyデータのフォーマットをチェック
        if "data" not in data:
            data = {"data": data}
        
        # configを取得（または作成）
        config = data.get("config", {})
        if "responsive" not in config:
            config["responsive"] = True
        
        # Plotlyデータとレイアウトを設定
        plotly_config = json.dumps(config)
        plotly_data = json.dumps(data["data"])
        plotly_layout = json.dumps(data.get("layout", {}))
        
        # スタイルを設定
        if width and not width.endswith(';'):
            width += ';'
        if height and not height.endswith(';'):
            height += ';'
        
        style = f"width:{width} height:{height} {self.options.get('style', '')}"
        
        # HTMLを生成
        html_content = f"""
        <div id="{self.chart_id}_container" style="{style}">
            <div id="{self.chart_id}" class="plotly-chart"></div>
            
            <script>
                (function() {{
                    function render() {{
                        var data = {plotly_data};
                        var layout = {plotly_layout};
                        var config = {plotly_config};
                        
                        Plotly.newPlot('{self.chart_id}', data, layout, config);
                    }}
                    
                    if (typeof Plotly !== 'undefined') {{
                        render();
                    }} else {{
                        window.addEventListener('load', function() {{
                            if (document.querySelector('script[src*="plotly"]')) {{
                                // Plotlyライブラリがロード済みの場合
                                render();
                            }} else {{
                                // Plotlyライブラリをロード
                                var script = document.createElement('script');
                                script.src = 'https://cdn.jsdelivr.net/npm/plotly.js@2.27.1/dist/plotly.min.js';
                                script.onload = render;
                                document.head.appendChild(script);
                            }}
                        }});
                    }}
                }})();
            </script>
        </div>
        """
        
        return html_content
    
    def get_required_libraries(self) -> List[str]:
        """
        必要なライブラリのURLリストを取得
        
        Returns
        -------
        List[str]
            ライブラリのURLリスト
        """
        return ["https://cdn.jsdelivr.net/npm/plotly.js@2.27.1/dist/plotly.min.js"]


class ChartJSRenderer(BaseChartRenderer):
    """
    Chart.jsを使用したチャートレンダラー
    
    軽量でレスポンシブなグラフの描画に適しています。
    """
    
    def __init__(self, chart_id: str, options: Dict[str, Any] = None):
        """
        初期化
        
        Parameters
        ----------
        chart_id : str
            チャートID
        options : Dict[str, Any], optional
            レンダラーオプション, by default None
        """
        super().__init__(chart_id, options)
    
    def render(self, data: Dict[str, Any], width: str = "100%", height: str = "400px") -> str:
        """
        チャートをレンダリング
        
        Parameters
        ----------
        data : Dict[str, Any]
            チャートデータ
        width : str, optional
            幅, by default "100%"
        height : str, optional
            高さ, by default "400px"
            
        Returns
        -------
        str
            レンダリングされたHTML
        """
        # Chart.jsのconfig形式にデータを変換
        chart_type = data.get("type", "line")
        chart_data = data.get("data", {})
        chart_options = data.get("options", {})
        
        # 設定をJSON形式に変換
        config_json = json.dumps({
            "type": chart_type,
            "data": chart_data,
            "options": chart_options
        })
        
        # スタイルを設定
        if width and not width.endswith(';'):
            width += ';'
        if height and not height.endswith(';'):
            height += ';'
        
        style = f"width:{width} height:{height} {self.options.get('style', '')}"
        
        # HTMLを生成
        html_content = f"""
        <div id="{self.chart_id}_container" style="{style}">
            <canvas id="{self.chart_id}" class="chartjs-chart"></canvas>
            
            <script>
                (function() {{
                    function render() {{
                        var ctx = document.getElementById('{self.chart_id}').getContext('2d');
                        var config = {config_json};
                        new Chart(ctx, config);
                    }}
                    
                    if (typeof Chart !== 'undefined') {{
                        render();
                    }} else {{
                        window.addEventListener('load', function() {{
                            if (document.querySelector('script[src*="chart.js"]')) {{
                                // Chart.jsライブラリがロード済みの場合
                                render();
                            }} else {{
                                // Chart.jsライブラリをロード
                                var script = document.createElement('script');
                                script.src = 'https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js';
                                script.onload = render;
                                document.head.appendChild(script);
                            }}
                        }});
                    }}
                }})();
            </script>
        </div>
        """
        
        return html_content
    
    def get_required_libraries(self) -> List[str]:
        """
        必要なライブラリのURLリストを取得
        
        Returns
        -------
        List[str]
            ライブラリのURLリスト
        """
        libraries = ["https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"]
        
        # 追加プラグインが必要な場合
        if self.options.get("plugins", {}).get("annotation", False):
            libraries.append("https://cdn.jsdelivr.net/npm/chartjs-plugin-annotation@2.1.0/dist/chartjs-plugin-annotation.min.js")
        
        if self.options.get("plugins", {}).get("datalabels", False):
            libraries.append("https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2.2.0/dist/chartjs-plugin-datalabels.min.js")
        
        return libraries
    
    def get_initialization_code(self, config_var: str = "config") -> str:
        """
        初期化用のJavaScriptコードを取得
        
        Parameters
        ----------
        config_var : str, optional
            設定変数名, by default "config"
            
        Returns
        -------
        str
            初期化コード
        """
        return f"""
            var ctx = document.getElementById('{self.chart_id}').getContext('2d');
            new Chart(ctx, {config_var});
        """


class MatplotlibRenderer(BaseChartRenderer):
    """
    Matplotlibを使用したチャートレンダラー
    
    静的なグラフの描画や細かいカスタマイズに適しています。
    """
    
    def __init__(self, chart_id: str, options: Dict[str, Any] = None):
        """
        初期化
        
        Parameters
        ----------
        chart_id : str
            チャートID
        options : Dict[str, Any], optional
            レンダラーオプション, by default None
        """
        super().__init__(chart_id, options)
    
    def render(self, data: Dict[str, Any], width: str = "100%", height: str = "400px") -> str:
        """
        チャートをレンダリング
        
        Parameters
        ----------
        data : Dict[str, Any]
            チャートデータとプロットコマンド
        width : str, optional
            幅, by default "100%"
        height : str, optional
            高さ, by default "400px"
            
        Returns
        -------
        str
            レンダリングされたHTML
        """
        # データからMatplotlibのfigureオブジェクトを取得
        fig = data.get("figure")
        if fig is None:
            return f'<div id="{self.chart_id}" class="error">Matplotlibのfigureが提供されていません。</div>'
        
        # 図をBase64エンコードされた画像に変換
        img_bytes = BytesIO()
        fig.savefig(img_bytes, format='png', bbox_inches='tight', dpi=self.options.get("dpi", 100))
        img_bytes.seek(0)
        img_base64 = base64.b64encode(img_bytes.read()).decode('utf-8')
        
        # スタイルを設定
        if width and width.endswith('%'):
            # パーセンテージ指定の場合は最大幅を設定
            width_style = f"max-width:{width};"
        else:
            width_style = f"width:{width};"
        
        if height and height.endswith('%'):
            # パーセンテージ指定の場合は最大高さを設定
            height_style = f"max-height:{height};"
        else:
            height_style = f"height:{height};"
        
        style = f"{width_style} {height_style} {self.options.get('style', '')}"
        
        # HTMLを生成
        html_content = f"""
        <div id="{self.chart_id}_container" style="{style}">
            <img id="{self.chart_id}" src="data:image/png;base64,{img_base64}" 
                 style="width:100%; height:auto;" alt="Matplotlib chart" />
        </div>
        """
        
        return html_content
    
    def get_required_libraries(self) -> List[str]:
        """
        必要なライブラリのURLリストを取得
        
        Returns
        -------
        List[str]
            ライブラリのURLリスト
        """
        # Matplotlibは画像として出力されるため、クライアント側ライブラリは不要
        return []


class RendererFactory:
    """
    チャートレンダラーのファクトリークラス
    
    適切なレンダラーを作成するためのファクトリーメソッドを提供します。
    """
    
    @staticmethod
    def create_renderer(renderer_type: str, chart_id: str = None, options: Dict[str, Any] = None) -> BaseChartRenderer:
        """
        指定されたタイプのレンダラーを作成
        
        Parameters
        ----------
        renderer_type : str
            レンダラータイプ（"plotly", "chartjs", "matplotlib"）
        chart_id : str, optional
            チャートID, by default None（指定されない場合は自動生成）
        options : Dict[str, Any], optional
            レンダラーオプション, by default None
            
        Returns
        -------
        BaseChartRenderer
            作成されたレンダラー
            
        Raises
        ------
        ValueError
            サポートされていないレンダラータイプの場合
        """
        # チャートIDがない場合は生成
        if chart_id is None:
            chart_id = f"chart_{str(uuid.uuid4())[:8]}"
        
        # オプションがない場合は空の辞書を作成
        options = options or {}
        
        # レンダラータイプに応じてレンダラーを作成
        if renderer_type.lower() == "plotly":
            return PlotlyRenderer(chart_id, options)
        elif renderer_type.lower() == "chartjs":
            return ChartJSRenderer(chart_id, options)
        elif renderer_type.lower() == "matplotlib":
            return MatplotlibRenderer(chart_id, options)
        else:
            raise ValueError(f"サポートされていないレンダラータイプ: {renderer_type}")
