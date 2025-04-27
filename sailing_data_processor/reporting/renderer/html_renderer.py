# -*- coding: utf-8 -*-
"""
sailing_data_processor.reporting.renderer.html_renderer

テンプレートをHTML形式でレンダリングするためのモジュールです。
"""

from typing import Dict, List, Any, Optional, Union, BinaryIO, TextIO
from pathlib import Path
import os
import json
import datetime
import html

from sailing_data_processor.reporting.renderer.base_renderer import BaseRenderer
from sailing_data_processor.reporting.templates.template_model import (
    Template, Section, Element, SectionType
)
from sailing_data_processor.reporting.elements.element_factory import create_element


class HTMLRenderer(BaseRenderer):
    """
    HTML形式のレンダラークラス
    
    テンプレートをHTML形式にレンダリングします。
    """
    
    def __init__(self, template: Template, config: Optional[Dict[str, Any]] = None):
        """
        初期化
        
        Parameters
        ----------
        template : Template
            レンダリング対象のテンプレート
        config : Optional[Dict[str, Any]], optional
            レンダラーの設定, by default None
            
            - include_css: CSSを含めるかどうか (デフォルト: True)
            - include_js: JavaScriptを含めるかどうか (デフォルト: True)
            - minify: HTML出力を最小化するかどうか (デフォルト: False)
            - encoding: 出力エンコーディング (デフォルト: utf-8)
        """
        super().__init__(template, config)
        
        # デフォルト設定
        self.include_css = self.config.get('include_css', True)
        self.include_js = self.config.get('include_js', True)
        self.minify = self.config.get('minify', False)
        self.encoding = self.config.get('encoding', 'utf-8')
        
        # レンダリング結果
        self.rendered_html = None
    
    def render(self) -> str:
        """
        テンプレートをHTMLにレンダリング
        
        Returns
        -------
        str
            レンダリングされたHTML
        """
        try:
            # テンプレートをソート
            self.template.sort_sections()
            
            # HTMLドキュメントの開始
            html_parts = [
                '<!DOCTYPE html>',
                '<html lang="ja">',
                '<head>',
                f'<meta charset="{self.encoding}">',
                '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
                f'<title>{html.escape(self.template.name)}</title>'
            ]
            
            # CSSの追加
            if self.include_css:
                html_parts.append(self._get_css())
            
            # 外部リソースの追加
            html_parts.extend([
                '<link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">',
                '<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>'
            ])
            
            html_parts.append('</head><body>')
            
            # テンプレートの各セクションをレンダリング
            html_parts.append('<div class="report-container">')
            
            # ヘッダーセクション
            header_sections = [s for s in self.template.sections if s.section_type == SectionType.HEADER]
            for section in header_sections:
                html_parts.append(self._render_section(section))
            
            # カバーセクション
            cover_sections = [s for s in self.template.sections if s.section_type == SectionType.COVER]
            for section in cover_sections:
                html_parts.append(self._render_section(section))
            
            # コンテンツセクション（カバーとヘッダー、フッター以外）
            content_sections = [s for s in self.template.sections 
                               if s.section_type not in (SectionType.HEADER, SectionType.FOOTER, SectionType.COVER)]
            
            # コンテンツ部分のラッパー
            html_parts.append('<div class="report-content">')
            for section in content_sections:
                html_parts.append(self._render_section(section))
            html_parts.append('</div>')
            
            # フッターセクション
            footer_sections = [s for s in self.template.sections if s.section_type == SectionType.FOOTER]
            for section in footer_sections:
                html_parts.append(self._render_section(section))
            
            html_parts.append('</div>')
            
            # JavaScriptの追加
            if self.include_js:
                html_parts.append(self._get_js())
            
            # HTMLドキュメントの終了
            html_parts.append('</body></html>')
            
            # HTMLの結合
            html_content = '\n'.join(html_parts)
            
            # HTML最小化（オプション）
            if self.minify:
                html_content = self._minify_html(html_content)
            
            # レンダリング結果を保存
            self.rendered_html = html_content
            
            return html_content
            
        except Exception as e:
            self.errors.append(f"HTMLのレンダリング中にエラーが発生しました: {str(e)}")
            }
            import traceback
            self.errors.append(traceback.format_exc())
            return ""
    
    def save(self, output_path: Union[str, Path, BinaryIO, TextIO]) -> bool:
        """
        レンダリング結果を保存
        
        Parameters
        ----------
        output_path : Union[str, Path, BinaryIO, TextIO]
            出力先
        
        Returns
        -------
        bool
            保存成功の場合はTrue
        """
        # レンダリング結果がない場合は先にレンダリング
        if self.rendered_html is None:
            self.render()
        
        if not self.rendered_html:
            return False
        
        try:
            # ファイルパスまたはファイルオブジェクトに書き込み
            if isinstance(output_path, (str, Path)):
                output_path = Path(output_path)
                # 親ディレクトリがない場合は作成
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_path, 'w', encoding=self.encoding) as f:
                    f.write(self.rendered_html)
            else:
                # ファイルオブジェクト
                if hasattr(output_path, 'write'):
                    output_path.write(self.rendered_html)
                else:
                    self.errors.append("無効な出力先が指定されました")
                    return False
            
            return True
        except Exception as e:
            self.errors.append(f"HTMLの保存中にエラーが発生しました: {str(e)}")
            }
            import traceback
            self.errors.append(traceback.format_exc())
            return False
    
    def _render_section(self, section: Section) -> str:
        """
        セクションをHTMLにレンダリング
        
        Parameters
        ----------
        section : Section
            レンダリング対象のセクション
        
        Returns
        -------
        str
            レンダリングされたHTML
        """
        # セクション要素を作成
        section_element = create_element(
            ElementType.SECTION,
            name=section.name,
            properties={}
                "title": section.title,
                "description": section.description,
                "title_level": 2
            },
            styles=section.styles
        )
        
        # セクション要素に子要素を追加
        for element_model in section.elements:
            section_element.add_child(element_model)
        
        # セクション要素をレンダリング
        return section_element.render(self.context)
    
    def _get_css(self) -> str:
        """
        レポート用のCSSスタイルを取得
        
        Returns
        -------
        str
            CSSスタイルを含むHTMLタグ
        """
        # テンプレートのグローバルスタイルを取得
        global_styles = self.template.global_styles
        
        # 基本スタイル設定
        font_family = global_styles.get('font_family', 'Arial, sans-serif')
        base_font_size = global_styles.get('base_font_size', 14)
        color_primary = global_styles.get('color_primary', '#3498db')
        color_secondary = global_styles.get('color_secondary', '#2c3e50')
        color_accent = global_styles.get('color_accent', '#e74c3c')
        color_background = global_styles.get('color_background', '#ffffff')
        color_text = global_styles.get('color_text', '#333333')
        
        # CSSスタイル
        css = f"""
        <style>
            /* グローバルスタイル */
            :root {{
                --color-primary: color_primary};
                --color-secondary: {color_secondary};
                --color-accent: {color_accent};
                --color-background: {color_background};
                --color-text: {color_text};
                --font-family: {font_family};
                --base-font-size: {base_font_size}px;
            }}
                }
                }
                }
                }
                }
            
            body {font-family: var(--font-family);
                font-size: var(--base-font-size);
                line-height: 1.6;
                color: var(--color-text);
                background-color: var(--color-background);
                margin: 0;
                padding: 0;
            }}
            
            /* レポートコンテナ */
            .report-container {max-width: 1200px;
                margin: 0 auto;
                background-color: #fff;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            
            /* レポートコンテンツ */
            .report-content {padding: 20px;
            }}
            
            /* セクション */
            .report-section {margin-bottom: 30px;
                padding: 20px;
                border-radius: 5px;
                background-color: #fff;
            }}
            
            .report-section-title {color: var(--color-primary);
                margin-top: 0;
                margin-bottom: 15px;
                border-bottom: 1px solid #eee;
                padding-bottom: 10px;
            }}
            
            .report-section-description {color: #666;
                margin-bottom: 20px;
            }}
            
            .report-section-content {/* セクションコンテンツのスタイル */
            }}
            
            /* テキスト要素 */
            .report-text {margin-bottom: 15px;
                line-height: 1.6;
            }}
            
            /* テーブル要素 */
            .report-table-container {overflow-x: auto;
                margin-bottom: 20px;
            }}
            
            .report-table {width: 100%;
                border-collapse: collapse;
                border-spacing: 0;
            }}
            
            .report-table th {background-color: var(--color-primary);
                color: white;
                font-weight: bold;
                text-align: left;
                padding: 12px;
                border: 1px solid #ddd;
            }}
            
            .report-table td {padding: 10px;
                border: 1px solid #ddd;
            }}
            
            .report-table tr:nth-child(even) {background-color: #f9f9f9;
            }}
            
            .report-table tr:hover {background-color: #f1f1f1;
            }}
            
            /* リスト要素 */
            .report-list-container {margin-bottom: 20px;
            }}
            
            .report-list {margin-left: 20px;
                padding-left: 0;
            }}
            
            .report-list li {margin-bottom: 8px;
            }}
            
            /* キー・バリュー要素 */
            .report-key-value-container {margin-bottom: 20px;
            }}
            
            .report-key-value-title {color: var(--color-primary);
                margin-top: 0;
                margin-bottom: 10px;
            }}
            
            .report-key-value-table {width: 100%;
                border-collapse: collapse;
            }}
            
            .report-key-value-key {width: 30%;
                font-weight: bold;
                padding: 8px;
                border-bottom: 1px solid #ddd;
                text-align: left;
                color: var(--color-secondary);
            }}
            
            .report-key-value-value {padding: 8px;
                border-bottom: 1px solid #ddd;
            }}
            
            /* チャート要素 */
            .report-chart-container {margin-bottom: 20px;
                border: 1px solid #eee;
                border-radius: 5px;
                padding: 10px;
            }}
            
            .report-chart {width: 100%;
                height: 100%;
            }}
            
            /* マップ要素 */
            .report-map-container {margin-bottom: 20px;
                border: 1px solid #eee;
                border-radius: 5px;
                padding: 10px;
            }}
            
            .report-map {width: 100%;
                height: 400px;
                background-color: #f5f5f5;
            }}
            
            /* ダイアグラム要素 */
            .report-diagram-container {margin-bottom: 20px;
                border: 1px solid #eee;
                border-radius: 5px;
                padding: 10px;
            }}
            
            .report-diagram {width: 100%;
                height: 400px;
                background-color: #f5f5f5;
            }}
            
            /* 画像要素 */
            .report-image-container {margin-bottom: 20px;
                text-align: center;
            }}
            
            .report-image {max-width: 100%;
                height: auto;
                border-radius: 5px;
            }}
            
            /* カラム要素 */
            .report-column {margin-bottom: 20px;
            }}
            
            /* グリッド要素 */
            .report-grid {margin-bottom: 20px;
            }}
            
            .report-grid-item {padding: 10px;
            }}
            
            /* タブ要素 */
            .report-tab-container {margin-bottom: 20px;
            }}
            
            .report-tab-nav {display: flex;
                border-bottom: 1px solid #ddd;
                margin-bottom: 15px;
            }}
            
            .report-tab-button {padding: 10px 15px;
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-bottom: none;
                border-radius: 5px 5px 0 0;
                margin-right: 5px;
                cursor: pointer;
                font-size: 16px;
            }}
            
            .report-tab-active {background-color: #fff;
                border-bottom: 2px solid var(--color-primary);
                color: var(--color-primary);
            }}
            
            .report-tab-panel {padding: 15px;
                border: 1px solid #ddd;
                border-top: none;
                border-radius: 0 0 5px 5px;
            }}
            
            /* 区切り線要素 */
            .report-divider {margin: 20px 0;
                border: none;
                border-top: 1px solid #ddd;
            }}
            
            /* ボックス要素 */
            .report-box {padding: 15px;
                margin-bottom: 20px;
                border-radius: 5px;
                background-color: #f9f9f9;
                border: 1px solid #ddd;
            }}
            
            .report-box-icon {margin-bottom: 10px;
                text-align: center;
            }}
            
            .report-box-icon i {font-size: 36px;
                color: var(--color-primary);
            }}
            
            .report-box-title {font-size: 18px;
                font-weight: bold;
                margin-bottom: 10px;
                color: var(--color-secondary);
                text-align: center;
            }}
            
            .report-box-value {font-size: 24px;
                font-weight: bold;
                margin-bottom: 10px;
                text-align: center;
                color: var(--color-accent);
            }}
            
            .report-box-content {margin-bottom: 10px;
            }}
            
            .report-box-children {/* ボックス子要素のスタイル */
            }}
            
            /* 背景要素 */
            .report-background {padding: 20px;
                margin-bottom: 20px;
                border-radius: 5px;
            }}
            
            /* 空の要素 */
            .report-table-empty,
            .report-list-empty,
            .report-key-value-empty,
            .report-chart-empty,
            .report-map-empty,
            .report-diagram-empty,
            .report-image-empty,
            .report-tab-empty {padding: 15px;
                margin-bottom: 20px;
                background-color: #f5f5f5;
                border: 1px dashed #ddd;
                border-radius: 5px;
                color: #888;
                text-align: center;
            }}
            
            /* レスポンシブデザイン */
            @media (max-width: 768px) {{
                .report-container {max-width: 100%;
                    margin: 0;
                }}
                
                .report-content {padding: 10px;
                }}
                
                .report-section {padding: 15px;
                }}
                
                .report-tab-button {padding: 8px 12px;
                    font-size: 14px;
                }}
            }}
            
            @media print {{
                body {background-color: #fff;
                }}
                
                .report-container {max-width: 100%;
                    margin: 0;
                    box-shadow: none;
                }}
                
                /* 印刷時のページ区切り */
                .report-section {page-break-inside: avoid;
                }}
            }}
        </style>
        """
        
        return css
    
    def _get_js(self) -> str:
        """
        レポート用のJavaScriptを取得
        
        Returns
        -------
        str
            JavaScriptを含むHTMLタグ
        """
        js = """
        <script>
            // マップの初期化関数
            function initMap(mapId, config) {
                // レポート内のマップ初期化
                // 注: 実際の実装ではリアルなマップライブラリを使用する
                console.log('Initializing map:', mapId, config);
                
                // マップコンテナを取得
                const mapContainer = document.getElementById(mapId);
                if (!mapContainer) return;
                
                // 簡易的なマップ表示（実装用のプレースホルダ）
                mapContainer.innerHTML = '<div style="width:100%;height:100%;display:flex;justify-content:center;align-items:center;"><p>マップデータが読み込まれました。<br>マップのレンダリングには実際のマップライブラリが必要です。</p></div>';
            }
            
            // ダイアグラムの初期化関数
            function initDiagram(diagramId, config) {
                // レポート内のダイアグラム初期化
                console.log('Initializing diagram:', diagramId, config);
                
                // ダイアグラムコンテナを取得
                const diagramContainer = document.getElementById(diagramId);
                if (!diagramContainer) return;
                
                // 簡易的なダイアグラム表示（実装用のプレースホルダ）
                diagramContainer.innerHTML = '<div style="width:100%;height:100%;display:flex;justify-content:center;align-items:center;"><p>ダイアグラムデータが読み込まれました。<br>ダイアグラムのレンダリングには実際のライブラリが必要です。</p></div>';
            }
            
            // ページ読み込み完了時の処理
            document.addEventListener('DOMContentLoaded', function() {
                console.log('Report rendered successfully');
            });
        </script>
        """
        
        return js
    
    def _minify_html(self, html_content: str) -> str:
        """
        HTMLを最小化
        
        Parameters
        ----------
        html_content : str
            最小化するHTML
        
        Returns
        -------
        str
            最小化されたHTML
        """
        # 非常に単純な最小化（空白の削減と改行の削除）
        # 注: 本格的な最小化にはHTMLMinifier等のライブラリを使用することを推奨
        
        # コメントの削除
        import re
        html_content = re.sub(r'<!--.*?-->', '', html_content, flags=re.DOTALL)
        
        # 無駄な空白の削除
        html_content = re.sub(r'\s+', ' ', html_content)
        
        # 特定のタグ周りの空白を調整
        for tag in ['html', 'head', 'body', 'div', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'section']:
            html_content = re.sub(fr'<{tag}>\s+', f'<{tag}>', html_content)
            html_content = re.sub(fr'\s+</{tag}>', f'</{tag}>', html_content)
        
        return html_content