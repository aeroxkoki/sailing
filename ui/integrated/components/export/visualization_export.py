# -*- coding: utf-8 -*-
"""
ui.integrated.components.export.visualization_export

可視化エクスポートコンポーネント
チャート、マップ、タイムラインなどの可視化をエクスポートするためのコンポーネント
"""

import streamlit as st
import pandas as pd
import numpy as np
import io
import base64
import os
import sys
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..')))

# 仮想的なMatplotlibインポート
try:
    import matplotlib.pyplot as plt
    import matplotlib
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

# 仮想的なPlotlyインポート
try:
    import plotly.graph_objects as go
    import plotly.io as pio
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False


class VisualizationExportComponent:
    """可視化エクスポートコンポーネント"""
    
    def __init__(self, key_prefix: str = "viz_export"):
        """
        初期化
        
        Parameters
        ----------
        key_prefix : str, optional
            Streamlitコンポーネントキーのプレフィックス, by default "viz_export"
        """
        self.key_prefix = key_prefix
        
        # サポートする可視化タイプ
        self.viz_types = {
            "chart": "チャート・グラフ",
            "map": "マップ・航跡",
            "timeline": "タイムライン",
            "dashboard": "ダッシュボード"
        }
        
        # サポートする出力形式
        self.output_formats = {
            "png": "PNG画像 (.png)",
            "jpg": "JPEG画像 (.jpg)",
            "svg": "SVGベクター画像 (.svg)",
            "pdf": "PDFドキュメント (.pdf)",
            "html": "HTML (インタラクティブ) (.html)"
        }
    
    def render(self, visualization=None, viz_type: str = "chart") -> Optional[Dict[str, Any]]:
        """
        可視化エクスポートUIの表示
        
        Parameters
        ----------
        visualization : matplotlib.figure.Figure or plotly.graph_objects.Figure, optional
            エクスポートする可視化オブジェクト, by default None
        viz_type : str, optional
            可視化のタイプ ("chart", "map", "timeline", "dashboard"), by default "chart"
            
        Returns
        -------
        Optional[Dict[str, Any]]
            エクスポート結果情報（実行された場合）
        """
        st.subheader("可視化エクスポート")
        
        # 可視化のサンプル（実際の実装では引数から受け取る）
        if visualization is None:
            # サンプル可視化の生成（表示用）
            visualization = self._generate_sample_visualization(viz_type)
            
            # サンプル可視化の表示
            st.markdown("### プレビュー")
            
            if viz_type == "chart":
                # チャートの場合
                if MATPLOTLIB_AVAILABLE:
                    st.pyplot(visualization)
                else:
                    st.info("注: プレビューを表示するにはMatplotlibが必要です")
                    
            elif viz_type == "map":
                # マップの場合
                st.markdown("#### マッププレビュー")
                st.info("注: このコンポーネントではマップのプレビューを表示しています。実際の実装では、セッションから生成されたマップを表示します。")
                
                # サンプルマップデータ
                map_data = pd.DataFrame({
                    'lat': [35.6580, 35.6585, 35.6590, 35.6595, 35.6600],
                    'lon': [139.7515, 139.7520, 139.7525, 139.7530, 139.7535]
                })
                st.map(map_data)
                
            elif viz_type == "timeline":
                # タイムラインの場合
                st.markdown("#### タイムラインプレビュー")
                st.info("注: このコンポーネントではタイムラインのプレビューを表示しています。実際の実装では、セッションから生成されたタイムラインを表示します。")
                
                # サンプルタイムラインデータ
                chart_data = pd.DataFrame({
                    'time': pd.date_range(start='2025-03-27 13:00:00', periods=100, freq='1min'),
                    'speed': np.cumsum(np.random.randn(100)) + 10
                }).set_index('time')
                
                st.line_chart(chart_data)
                
            elif viz_type == "dashboard":
                # ダッシュボードの場合
                st.markdown("#### ダッシュボードプレビュー")
                st.info("注: このコンポーネントではダッシュボードのプレビューを表示しています。実際の実装では、セッションから生成されたダッシュボードを表示します。")
                
                # サンプルダッシュボードレイアウト
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("##### 速度プロファイル")
                    chart_data = pd.DataFrame({
                        'speed': np.cumsum(np.random.randn(20)) + 10
                    })
                    st.line_chart(chart_data)
                
                with col2:
                    st.markdown("##### 風向分布")
                    chart_data = pd.DataFrame({
                        'wind_dir': np.random.randint(0, 360, 50)
                    })
                    st.bar_chart(chart_data)
        
        # エクスポート設定
        st.markdown("### エクスポート設定")
        
        # 2列レイアウト
        col1, col2 = st.columns(2)
        
        with col1:
            # 可視化タイプの選択
            export_viz_type = st.selectbox(
                "可視化タイプ",
                options=list(self.viz_types.keys()),
                format_func=lambda x: self.viz_types.get(x, x),
                index=list(self.viz_types.keys()).index(viz_type) if viz_type in self.viz_types else 0,
                key=f"{self.key_prefix}_viz_type"
            )
            
            # 出力形式の選択
            export_format = st.selectbox(
                "出力形式",
                options=list(self.output_formats.keys()),
                format_func=lambda x: self.output_formats.get(x, x),
                key=f"{self.key_prefix}_format"
            )
            
            # 出力ファイル名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"sailing_{export_viz_type}_{timestamp}"
            
            filename = st.text_input(
                "ファイル名",
                value=default_filename,
                key=f"{self.key_prefix}_filename"
            )
        
        with col2:
            # 画像品質設定
            if export_format in ["png", "jpg", "pdf"]:
                dpi = st.slider(
                    "解像度 (DPI)",
                    min_value=72,
                    max_value=300,
                    value=150,
                    step=1,
                    help="高いほど高品質ですが、ファイルサイズも大きくなります",
                    key=f"{self.key_prefix}_dpi"
                )
            
            # 画像サイズ設定
            width = st.slider(
                "幅 (ピクセル)",
                min_value=640,
                max_value=3840,
                value=1200,
                step=10,
                key=f"{self.key_prefix}_width"
            )
            
            height = st.slider(
                "高さ (ピクセル)",
                min_value=480,
                max_value=2160,
                value=800,
                step=10,
                key=f"{self.key_prefix}_height"
            )
            
            # 透過背景（PNG、SVGの場合）
            if export_format in ["png", "svg"]:
                transparent = st.checkbox(
                    "透過背景",
                    value=True,
                    help="背景を透明にします（PNG、SVGのみ）",
                    key=f"{self.key_prefix}_transparent"
                )
        
        # 詳細設定
        with st.expander("詳細設定", expanded=False):
            # 出力形式ごとの詳細設定
            if export_format == "png":
                compression = st.slider(
                    "PNG圧縮レベル",
                    min_value=0,
                    max_value=9,
                    value=6,
                    step=1,
                    help="高いほど圧縮率が高くなりますが、処理に時間がかかります",
                    key=f"{self.key_prefix}_compression"
                )
                
                optimize = st.checkbox(
                    "最適化",
                    value=True,
                    help="ファイルサイズを最適化します",
                    key=f"{self.key_prefix}_optimize"
                )
            
            elif export_format == "jpg":
                quality = st.slider(
                    "JPEG品質",
                    min_value=10,
                    max_value=100,
                    value=85,
                    step=5,
                    help="高いほど高品質ですが、ファイルサイズも大きくなります",
                    key=f"{self.key_prefix}_quality"
                )
                
                progressive = st.checkbox(
                    "プログレッシブ表示",
                    value=True,
                    help="読み込み中に徐々に表示されるようにします",
                    key=f"{self.key_prefix}_progressive"
                )
            
            elif export_format == "svg":
                include_fonts = st.checkbox(
                    "フォントを埋め込む",
                    value=False,
                    help="フォントを埋め込みますが、ファイルサイズが大きくなります",
                    key=f"{self.key_prefix}_include_fonts"
                )
            
            elif export_format == "pdf":
                paper_size = st.selectbox(
                    "用紙サイズ",
                    options=["A4", "A3", "レター", "リーガル", "カスタム"],
                    index=0,
                    key=f"{self.key_prefix}_paper_size"
                )
                
                orientation = st.radio(
                    "向き",
                    options=["縦向き", "横向き"],
                    index=1,
                    horizontal=True,
                    key=f"{self.key_prefix}_orientation"
                )
            
            elif export_format == "html":
                include_plotlyjs = st.radio(
                    "Plotly.jsの埋め込み",
                    options=["埋め込む (スタンドアロン)", "CDNから読み込む (小さいファイルサイズ)"],
                    index=0,
                    horizontal=True,
                    key=f"{self.key_prefix}_include_plotlyjs"
                )
                
                include_mathjax = st.checkbox(
                    "MathJaxを含める",
                    value=False,
                    help="数式の表示に必要ですが、ファイルサイズが大きくなります",
                    key=f"{self.key_prefix}_include_mathjax"
                )
                
                responsive = st.checkbox(
                    "レスポンシブデザイン",
                    value=True,
                    help="ブラウザのサイズに合わせて表示サイズを調整します",
                    key=f"{self.key_prefix}_responsive"
                )
            
            # その他の設定（共通）
            include_title = st.checkbox(
                "タイトルを含める",
                value=True,
                key=f"{self.key_prefix}_include_title"
            )
            
            if include_title:
                title = st.text_input(
                    "タイトル",
                    value=f"Sailing Analysis - {self.viz_types.get(export_viz_type, export_viz_type)}",
                    key=f"{self.key_prefix}_title"
                )
            
            include_timestamp = st.checkbox(
                "タイムスタンプを含める",
                value=True,
                key=f"{self.key_prefix}_include_timestamp"
            )
            
            include_logo = st.checkbox(
                "ロゴを含める",
                value=False,
                key=f"{self.key_prefix}_include_logo"
            )
        
        # エクスポート実行ボタン
        if st.button("エクスポート実行", key=f"{self.key_prefix}_export_btn", use_container_width=True):
            # エクスポート処理（実際の実装では可視化オブジェクトをエクスポート）
            export_data, exported_filename = self._export_visualization(
                visualization=visualization,
                viz_type=export_viz_type,
                export_format=export_format,
                filename=filename,
                width=width,
                height=height,
                dpi=locals().get("dpi", 150),
                transparent=locals().get("transparent", False),
                title=locals().get("title", "")
            )
            
            if export_data:
                # ダウンロードリンクの作成
                download_link = self._create_download_link(export_data, exported_filename, export_format)
                st.success(f"可視化のエクスポートが完了しました。")
                st.markdown(download_link, unsafe_allow_html=True)
                
                # エクスポート結果情報の返却
                return {
                    "type": "visualization",
                    "viz_type": export_viz_type,
                    "format": export_format,
                    "filename": exported_filename,
                    "timestamp": datetime.now().isoformat(),
                    "download_link": download_link,
                    "size": self._get_file_size_str(len(export_data))
                }
        
        return None
    
    def _generate_sample_visualization(self, viz_type: str):
        """
        サンプル可視化の生成（デモ用）
        
        Parameters
        ----------
        viz_type : str
            可視化のタイプ
            
        Returns
        -------
        matplotlib.figure.Figure or plotly.graph_objects.Figure or None
            サンプル可視化オブジェクト
        """
        if viz_type == "chart" and MATPLOTLIB_AVAILABLE:
            # Matplotlibのサンプルチャート
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # データ生成
            np.random.seed(42)
            x = np.linspace(0, 10, 100)
            y1 = np.sin(x) + np.random.normal(0, 0.1, 100)
            y2 = np.cos(x) + np.random.normal(0, 0.1, 100)
            
            # プロット
            ax.plot(x, y1, label='風速', linewidth=2, color='#1f77b4')
            ax.plot(x, y2, label='艇速', linewidth=2, color='#ff7f0e')
            
            # グラフ装飾
            ax.set_title('風速と艇速の関係', fontsize=16)
            ax.set_xlabel('時間 (分)', fontsize=12)
            ax.set_ylabel('速度 (ノット)', fontsize=12)
            ax.grid(True, linestyle='--', alpha=0.7)
            ax.legend(fontsize=12)
            
            # スタイル設定
            plt.tight_layout()
            
            return fig
        
        elif viz_type == "chart" and PLOTLY_AVAILABLE:
            # Plotlyのサンプルチャート
            # データ生成
            np.random.seed(42)
            x = np.linspace(0, 10, 100)
            y1 = np.sin(x) + np.random.normal(0, 0.1, 100)
            y2 = np.cos(x) + np.random.normal(0, 0.1, 100)
            
            # プロット
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=x, y=y1, name='風速', line=dict(width=2, color='#1f77b4')))
            fig.add_trace(go.Scatter(x=x, y=y2, name='艇速', line=dict(width=2, color='#ff7f0e')))
            
            # グラフ装飾
            fig.update_layout(
                title='風速と艇速の関係',
                xaxis_title='時間 (分)',
                yaxis_title='速度 (ノット)',
                template='plotly_white',
                legend=dict(
                    x=0.01,
                    y=0.99,
                    bordercolor='Gray',
                    borderwidth=1
                )
            )
            
            return fig
        
        return None
    
    def _export_visualization(self, visualization, viz_type: str, export_format: str, 
                             filename: str, width: int, height: int, dpi: int = 150,
                             transparent: bool = False, title: str = "") -> Tuple[bytes, str]:
        """
        可視化をエクスポート
        
        Parameters
        ----------
        visualization : matplotlib.figure.Figure or plotly.graph_objects.Figure
            エクスポートする可視化オブジェクト
        viz_type : str
            可視化のタイプ
        export_format : str
            エクスポート形式
        filename : str
            出力ファイル名
        width : int
            画像の幅（ピクセル）
        height : int
            画像の高さ（ピクセル）
        dpi : int, optional
            画像の解像度（DPI）, by default 150
        transparent : bool, optional
            透過背景の使用, by default False
        title : str, optional
            タイトル, by default ""
            
        Returns
        -------
        Tuple[bytes, str]
            エクスポートデータのバイト列とファイル名
        """
        # 実際の実装では可視化オブジェクトから適切な形式でエクスポート
        # ここではサンプルデータを返す
        
        # ファイル拡張子の設定
        file_ext = export_format
        
        # 完全なファイル名
        full_filename = f"{filename}.{file_ext}"
        
        # バッファの作成
        buffer = io.BytesIO()
        
        # 可視化タイプとエクスポート形式に応じたエクスポート処理
        # ここではダミーのエクスポート処理
        if viz_type == "chart":
            if export_format == "html" and PLOTLY_AVAILABLE and isinstance(visualization, go.Figure):
                # Plotlyのインタラクティブなエクスポート
                html_str = pio.to_html(
                    visualization,
                    include_plotlyjs=True,
                    full_html=True
                )
                buffer.write(html_str.encode("utf-8"))
                
            elif MATPLOTLIB_AVAILABLE and hasattr(visualization, "savefig"):
                # Matplotlibの静的なエクスポート
                visualization.savefig(
                    buffer,
                    format=export_format,
                    dpi=dpi,
                    transparent=transparent,
                    bbox_inches="tight"
                )
                
            else:
                # ダミーデータ
                buffer.write(f"Chart export placeholder for {viz_type} in {export_format} format".encode("utf-8"))
                
        elif viz_type == "map":
            # マップのエクスポート（ダミー）
            buffer.write(f"Map export placeholder for {viz_type} in {export_format} format".encode("utf-8"))
            
        elif viz_type == "timeline":
            # タイムラインのエクスポート（ダミー）
            buffer.write(f"Timeline export placeholder for {viz_type} in {export_format} format".encode("utf-8"))
            
        elif viz_type == "dashboard":
            # ダッシュボードのエクスポート（ダミー）
            buffer.write(f"Dashboard export placeholder for {viz_type} in {export_format} format".encode("utf-8"))
        
        # バッファを先頭に戻す
        buffer.seek(0)
        
        # バイト列として返す
        return buffer.read(), full_filename
    
    def _create_download_link(self, data: bytes, filename: str, format_type: str) -> str:
        """
        ダウンロードリンクの生成
        
        Parameters
        ----------
        data : bytes
            ダウンロードするデータ
        filename : str
            ファイル名
        format_type : str
            ファイル形式
            
        Returns
        -------
        str
            HTMLダウンロードリンク
        """
        b64 = base64.b64encode(data).decode()
        
        # MIMEタイプの設定
        mime_types = {
            "png": "image/png",
            "jpg": "image/jpeg",
            "svg": "image/svg+xml",
            "pdf": "application/pdf",
            "html": "text/html"
        }
        
        mime_type = mime_types.get(format_type, "application/octet-stream")
        
        # スタイル付きのダウンロードボタン
        styled_link = f"""
        <div style="text-align: center; margin: 10px 0;">
            <a href="data:{mime_type};base64,{b64}" 
               download="{filename}" 
               style="display: inline-block; 
                      background-color: #4CAF50; 
                      color: white; 
                      padding: 10px 20px; 
                      text-align: center; 
                      text-decoration: none; 
                      font-size: 16px; 
                      margin: 4px 2px; 
                      cursor: pointer; 
                      border-radius: 4px;">
                <span>可視化をダウンロード ({format_type.upper()})</span>
            </a>
        </div>
        """
        
        return styled_link
    
    def _get_file_size_str(self, size_bytes: int) -> str:
        """
        ファイルサイズの文字列表現を取得
        
        Parameters
        ----------
        size_bytes : int
            バイト単位のサイズ
            
        Returns
        -------
        str
            人間が読みやすい形式のサイズ表現
        """
        # サイズの単位変換
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
