"""
ui.integrated.components.help.help_component

ヘルプコンポーネント
アプリケーションの使い方に関するヘルプとガイダンスを提供します。
"""

import streamlit as st
import os
import sys
import base64
from typing import Dict, List, Any, Optional

class HelpComponent:
    """ヘルプとガイダンスコンポーネント"""
    
    def __init__(self, key_prefix: str = "help"):
        """
        初期化
        
        Parameters
        ----------
        key_prefix : str, optional
            Streamlitコンポーネントキーのプレフィックス, by default "help"
        """
        self.key_prefix = key_prefix
        
        # ヘルプコンテンツの定義
        self.help_topics = {
            "import": {
                "title": "データインポート",
                "description": "GPSデータや他の測定データをインポートする方法",
                "icon": "upload",
                "content": self._get_import_help()
            },
            "analysis": {
                "title": "データ分析",
                "description": "風推定や戦略検出などの分析機能の使い方",
                "icon": "activity",
                "content": self._get_analysis_help()
            },
            "visualization": {
                "title": "データ可視化",
                "description": "マップ、チャートなどの可視化機能の使い方",
                "icon": "bar-chart-2",
                "content": self._get_visualization_help()
            },
            "export": {
                "title": "エクスポート",
                "description": "データ、可視化、レポートをエクスポートする方法",
                "icon": "download",
                "content": self._get_export_help()
            },
            "storage": {
                "title": "データストレージ",
                "description": "セッションやプロジェクトの保存と管理",
                "icon": "save",
                "content": self._get_storage_help()
            }
        }
    
    def render_help_button(self, topic: str):
        """
        ヘルプボタンを表示
        
        Parameters
        ----------
        topic : str
            ヘルプトピックのID
        """
        if topic in self.help_topics:
            topic_data = self.help_topics[topic]
            # ヘルプアイコンボタン
            help_html = f"""
            <div style="display: inline-block; position: relative;">
                <button 
                    onclick="document.getElementById('{self.key_prefix}_{topic}_popup').style.display='block';"
                    style="background: none; border: none; color: #0066cc; cursor: pointer;"
                    title="{topic_data['description']}"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" 
                         stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="12" cy="12" r="10"></circle>
                        <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path>
                        <line x1="12" y1="17" x2="12.01" y2="17"></line>
                    </svg>
                </button>
                
                <div id="{self.key_prefix}_{topic}_popup" 
                     style="display: none; position: absolute; right: 0; top: 100%; width: 300px; 
                            background-color: white; border: 1px solid #ddd; border-radius: 4px; 
                            padding: 10px; z-index: 1000; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
                        <h4 style="margin: 0;">{topic_data['title']}</h4>
                        <button 
                            onclick="document.getElementById('{self.key_prefix}_{topic}_popup').style.display='none';"
                            style="background: none; border: none; color: #666; cursor: pointer; font-size: 18px; line-height: 1;"
                        >&times;</button>
                    </div>
                    <hr style="margin: 5px 0;">
                    <div style="max-height: 300px; overflow-y: auto; font-size: 14px;">
                        {topic_data['content']}
                    </div>
                    <hr style="margin: 5px 0;">
                    <div style="text-align: center; margin-top: 5px;">
                        <a href="#{topic}" onclick="document.getElementById('{self.key_prefix}_{topic}_popup').style.display='none'; 
                                                  document.getElementById('{self.key_prefix}_full_help').scrollIntoView();"
                           style="color: #0066cc; text-decoration: none; font-size: 12px;"
                        >詳細ヘルプを表示</a>
                    </div>
                </div>
            </div>
            """
            st.markdown(help_html, unsafe_allow_html=True)
    
    def render_help_tooltip(self, text: str, tooltip: str, placement: str = "top"):
        """
        ツールチップ付きテキストを表示
        
        Parameters
        ----------
        text : str
            表示するテキスト
        tooltip : str
            ツールチップに表示する説明テキスト
        placement : str, optional
            ツールチップの表示位置, by default "top"
        """
        # ランダムIDを生成（複数のツールチップ用）
        import random
        tooltip_id = f"tooltip_{random.randint(10000, 99999)}"
        
        tooltip_html = f"""
        <div style="display: inline-block; position: relative;">
            <span id="{tooltip_id}_trigger" style="border-bottom: 1px dashed #666; cursor: help;">{text}</span>
            <div id="{tooltip_id}" 
                 style="display: none; position: absolute; {placement}: -40px; left: 50%; transform: translateX(-50%);
                        width: 200px; background-color: #333; color: white; text-align: center;
                        border-radius: 4px; padding: 5px; font-size: 12px; z-index: 1000;">
                {tooltip}
                <div style="position: absolute; {placement}: 100%; left: 50%; transform: translateX(-50%);
                            width: 0; height: 0; border-left: 5px solid transparent;
                            border-right: 5px solid transparent; border-top: 5px solid #333;"></div>
            </div>
        </div>
        
        <script>
            document.getElementById("{tooltip_id}_trigger").onmouseover = function() {{
                document.getElementById("{tooltip_id}").style.display = "block";
            }};
            document.getElementById("{tooltip_id}_trigger").onmouseout = function() {{
                document.getElementById("{tooltip_id}").style.display = "none";
            }};
        </script>
        """
        
        st.markdown(tooltip_html, unsafe_allow_html=True)
    
    def render_help_page(self, topic: Optional[str] = None):
        """
        ヘルプページ全体を表示
        
        Parameters
        ----------
        topic : Optional[str], optional
            初期選択するトピック, by default None
        """
        st.markdown("<h1 id='help_full_help'>セーリング戦略分析システム ヘルプ</h1>", unsafe_allow_html=True)
        
        # 概要
        st.markdown("""
        このヘルプページでは、セーリング戦略分析システムの使い方について説明します。
        左側のメニューからトピックを選択するか、以下のクイックガイドからお探しの情報を見つけることができます。
        """)
        
        # トピック選択
        selected_topic = st.selectbox(
            "トピックを選択",
            options=list(self.help_topics.keys()),
            format_func=lambda x: self.help_topics[x]["title"],
            index=list(self.help_topics.keys()).index(topic) if topic in self.help_topics else 0,
            key=f"{self.key_prefix}_topic_selector"
        )
        
        # 選択したトピックの表示
        if selected_topic in self.help_topics:
            topic_data = self.help_topics[selected_topic]
            
            st.markdown(f"## {topic_data['title']}")
            st.markdown(topic_data['description'])
            
            # トピックの詳細コンテンツをMarkdownで表示（HTMLも可）
            st.markdown(topic_data['content'], unsafe_allow_html=True)
            
            # 関連トピック
            st.markdown("### 関連トピック")
            cols = st.columns(min(3, len(self.help_topics) - 1))
            
            i = 0
            for topic_id, topic_info in self.help_topics.items():
                if topic_id != selected_topic:
                    with cols[i % len(cols)]:
                        st.markdown(f"**[{topic_info['title']}](#)**")
                        st.markdown(topic_info['description'])
                    i += 1
    
    def render_walkthrough(self, section: str):
        """
        対話型ウォークスルーを表示
        
        Parameters
        ----------
        section : str
            ウォークスルーのセクション
        """
        # サンプルウォークスルー
        if section == "welcome":
            st.success("""
            👋 **ようこそ！** セーリング戦略分析システムへ
            
            このシステムでは、セーリングデータの分析と視覚化が簡単に行えます。
            まずはデータのインポートから始めましょう。
            
            ▶️ 左のサイドバーから「データインポート」を選択してください。
            """)
            
        elif section == "import":
            st.info("""
            📥 **データインポート**
            
            CSVファイルやGPXファイルなどをアップロードして、セーリングセッションデータを読み込みます。
            サンプルデータを使用することもできます。
            
            ▶️ インポートが完了したら「データ検証」へ進みましょう。
            """)
            
        elif section == "validation":
            st.info("""
            ✅ **データ検証**
            
            インポートしたデータの品質を確認します。
            問題がある場合は修正オプションが表示されます。
            
            ▶️ 検証が完了したら「分析」へ進みましょう。
            """)
    
    def render_quick_tips(self):
        """
        クイックヒントを表示
        """
        with st.expander("📌 クイックヒント"):
            tips = [
                "**データバックアップ**: 分析セッションは定期的にエクスポートすることをお勧めします。",
                "**キーボードショートカット**: Ctrl+S（またはCmd+S）で現在のセッションを保存できます。",
                "**大きなファイル**: 大容量のGPSファイルは、処理に時間がかかることがあります。辛抱強くお待ちください。",
                "**最適表示**: このアプリケーションは1280x800以上の解像度で最適に表示されます。",
                "**メモリ使用量**: 多数の可視化を開くとブラウザのメモリ使用量が増加することがあります。定期的に更新することをお勧めします。"
            ]
            
            for tip in tips:
                st.markdown(f"- {tip}")
    
    def _get_import_help(self) -> str:
        """
        データインポートのヘルプコンテンツを取得
        """
        return """
        <h3>データのインポート方法</h3>
        <p>以下の手順でデータをインポートできます：</p>
        <ol>
            <li>「データインポート」ページを開く</li>
            <li>「ファイルをアップロード」ボタンをクリックし、GPSデータファイル（CSV, GPX, FITなど）を選択</li>
            <li>必要な場合は、ファイルの形式と列のマッピングを設定</li>
            <li>「インポート実行」ボタンをクリック</li>
        </ol>
        
        <h4>サポートされているファイル形式</h4>
        <ul>
            <li><strong>CSV</strong>: カンマ区切りのテキストファイル</li>
            <li><strong>GPX</strong>: GPS Exchange Format（GPSデバイスの標準形式）</li>
            <li><strong>FIT</strong>: Flexible and Interoperable Data Transfer（Garminなどで使用）</li>
            <li><strong>TCX</strong>: Training Center XML（トレーニングデータ形式）</li>
        </ul>
        
        <h4>トラブルシューティング</h4>
        <p>インポートに問題がある場合：</p>
        <ul>
            <li>ファイルが正しい形式であることを確認</li>
            <li>ファイルが破損していないことを確認</li>
            <li>必要な列（時刻、緯度、経度）が含まれていることを確認</li>
            <li>大きなファイルの場合、処理に時間がかかることがあります</li>
        </ul>
        """
    
    def _get_analysis_help(self) -> str:
        """
        データ分析のヘルプコンテンツを取得
        """
        return """
        <h3>データ分析機能について</h3>
        <p>以下の分析機能が利用できます：</p>
        
        <h4>風推定</h4>
        <p>GPSデータから風向と風速を推定します。次の手順で実行できます：</p>
        <ol>
            <li>「風推定」ページを開く</li>
            <li>使用するモデルとパラメータを選択</li>
            <li>「推定実行」ボタンをクリック</li>
            <li>結果は視覚的にマップとグラフで表示されます</li>
        </ol>
        
        <h4>戦略検出</h4>
        <p>セーリング中の重要な戦略的決断ポイントを検出します：</p>
        <ol>
            <li>「戦略検出」ページを開く</li>
            <li>検出感度と対象とする動作タイプを設定</li>
            <li>「検出実行」ボタンをクリック</li>
            <li>検出された戦略ポイントがマップとタイムラインに表示されます</li>
        </ol>
        
        <h4>パフォーマンス分析</h4>
        <p>セーリングのパフォーマンスを分析し、改善点を特定します：</p>
        <ol>
            <li>「パフォーマンス分析」ページを開く</li>
            <li>分析する側面（速度、角度など）を選択</li>
            <li>「分析実行」ボタンをクリック</li>
            <li>パフォーマンス指標と比較グラフが表示されます</li>
        </ol>
        """
    
    def _get_visualization_help(self) -> str:
        """
        データ可視化のヘルプコンテンツを取得
        """
        return """
        <h3>データ可視化機能について</h3>
        <p>以下の可視化機能が利用できます：</p>
        
        <h4>マップビュー</h4>
        <p>GPSトラックとその他のデータをマップ上に表示します：</p>
        <ul>
            <li><strong>ベースマップ</strong>: 異なる地図スタイルを選択できます</li>
            <li><strong>レイヤー</strong>: GPS軌跡、風向、戦略ポイントなどの表示/非表示を切り替え</li>
            <li><strong>時間フィルター</strong>: 特定の時間範囲のデータのみを表示</li>
            <li><strong>インタラクション</strong>: ポイントクリックで詳細情報を表示</li>
        </ul>
        
        <h4>チャートビュー</h4>
        <p>様々なデータをグラフとして可視化します：</p>
        <ul>
            <li><strong>時系列チャート</strong>: 速度、方向、風などの時間変化を表示</li>
            <li><strong>散布図</strong>: 2つの変数間の関係を表示</li>
            <li><strong>ヒストグラム</strong>: データの分布を表示</li>
            <li><strong>極座標チャート</strong>: 方向データの分析に有用</li>
        </ul>
        
        <h4>タイムラインビュー</h4>
        <p>セッション全体を時間軸で可視化します：</p>
        <ul>
            <li><strong>イベントマーカー</strong>: タック、ジャイブ、戦略ポイントなどを表示</li>
            <li><strong>時間セグメント</strong>: レース中の異なるフェーズを区分</li>
            <li><strong>タイムスクラバー</strong>: 特定の時点のデータにフォーカス</li>
        </ul>
        
        <h4>インタラクション機能</h4>
        <ul>
            <li><strong>ズーム</strong>: ホイールまたはピンチジェスチャーでズーム</li>
            <li><strong>パン</strong>: ドラッグして表示位置を移動</li>
            <li><strong>フィルタリング</strong>: 特定の条件に合うデータのみを表示</li>
            <li><strong>リンク表示</strong>: 複数の可視化間でデータをリンク</li>
        </ul>
        """
    
    def _get_export_help(self) -> str:
        """
        エクスポート機能のヘルプコンテンツを取得
        """
        return """
        <h3>エクスポート機能について</h3>
        <p>データ、可視化、レポートをさまざまな形式でエクスポートできます：</p>
        
        <h4>データエクスポート</h4>
        <p>セッションデータや分析結果をエクスポートします：</p>
        <ul>
            <li><strong>CSV</strong>: 表形式データを標準的なCSV形式で保存（Excel等で開くことが可能）</li>
            <li><strong>JSON</strong>: 構造化データをJSON形式で保存（プログラムでの処理に最適）</li>
            <li><strong>GPX</strong>: GPS軌跡データをGPX形式で保存（他のGPSアプリで使用可能）</li>
            <li><strong>Excel</strong>: 複数シートを含むExcelファイルとして保存（詳細な分析に便利）</li>
        </ul>
        
        <h4>可視化エクスポート</h4>
        <p>チャート、グラフ、マップを画像形式で保存：</p>
        <ul>
            <li><strong>PNG</strong>: 高品質のラスター画像（透過背景をサポート、プレゼンテーションに最適）</li>
            <li><strong>JPG</strong>: 写真向けのラスター画像（ファイルサイズが小さい、ウェブ公開に適する）</li>
            <li><strong>SVG</strong>: ベクター画像形式（拡大しても鮮明、印刷物に最適）</li>
            <li><strong>PDF</strong>: 印刷に適したドキュメント形式（高品質な印刷用資料作成に）</li>
            <li><strong>HTML</strong>: インタラクティブな可視化をウェブページとして保存（データ探索向け）</li>
        </ul>
        
        <h4>レポートエクスポート</h4>
        <p>分析結果をまとめたレポートを生成します：</p>
        <ul>
            <li><strong>PDF</strong>: 読みやすいPDFレポート（印刷や共有に最適）</li>
            <li><strong>HTML</strong>: ウェブブラウザで閲覧可能なレポート（インタラクティブ要素を含める場合に便利）</li>
            <li><strong>Markdown</strong>: テキストベースのレポート（GitHub等での共有に適する）</li>
        </ul>
        
        <h4>バッチエクスポート</h4>
        <p>複数のセッションやプロジェクトを一括でエクスポートできます：</p>
        <ul>
            <li><strong>個別ファイル</strong>: 各アイテムを個別のファイルとして保存</li>
            <li><strong>結合ファイル</strong>: すべてのデータを1つのファイルにまとめる</li>
            <li><strong>ZIP圧縮</strong>: 複数のファイルをZIPアーカイブにまとめる</li>
        </ul>
        
        <h4>エクスポート設定</h4>
        <p>各エクスポート形式で詳細な設定が可能です：</p>
        <ul>
            <li><strong>解像度</strong>: 画像の品質とサイズを調整</li>
            <li><strong>サイズ</strong>: 画像の幅と高さを指定</li>
            <li><strong>メタデータ</strong>: 説明情報を含めるかどうか</li>
            <li><strong>時間範囲</strong>: 特定の期間のデータのみをエクスポート</li>
            <li><strong>データフィールド</strong>: エクスポートに含める項目を選択</li>
            <li><strong>ファイル形式設定</strong>: 各形式固有の詳細設定（エンコーディング、圧縮率など）</li>
        </ul>
        
        <h4>エクスポート履歴</h4>
        <p>過去のエクスポート記録を閲覧し、同じ設定で再エクスポートしたり、以前のエクスポートファイルを再ダウンロードしたりできます。</p>
        """
    
    def _get_storage_help(self) -> str:
        """
        データストレージのヘルプコンテンツを取得
        """
        return """
        <h3>データストレージ機能について</h3>
        <p>セッションやプロジェクトを保存・管理する方法：</p>
        
        <h4>ブラウザストレージ</h4>
        <p>データはブラウザのローカルストレージに保存されます：</p>
        <ul>
            <li><strong>メリット</strong>: インターネット接続なしで利用可能、プライバシー保護</li>
            <li><strong>制限</strong>: ブラウザや端末間で共有できない、容量制限あり</li>
            <li><strong>推奨</strong>: 定期的にデータをファイルにエクスポートしてバックアップしてください</li>
        </ul>
        
        <h4>プロジェクト管理</h4>
        <p>複数のセッションをプロジェクトとして管理できます：</p>
        <ol>
            <li>「プロジェクト」ページを開く</li>
            <li>「新規プロジェクト作成」ボタンをクリック</li>
            <li>プロジェクト名と説明を入力</li>
            <li>プロジェクトに含めるセッションを選択</li>
            <li>「保存」ボタンをクリック</li>
        </ol>
        
        <h4>セッション管理</h4>
        <p>個別のセーリングセッションを管理できます：</p>
        <ul>
            <li><strong>保存</strong>: 「セッションを保存」ボタンをクリックして現在のセッションを保存</li>
            <li><strong>読み込み</strong>: 「セッションを読み込む」から保存済みセッションを選択</li>
            <li><strong>削除</strong>: 不要になったセッションを削除</li>
        </ul>
        
        <h4>データのバックアップと復元</h4>
        <p>重要なデータを保護するには：</p>
        <ol>
            <li>「エクスポート」ページを開く</li>
            <li>「アプリケーションデータ」タブを選択</li>
            <li>「すべてのデータをエクスポート」または特定のデータを選択</li>
            <li>「エクスポート実行」ボタンをクリック</li>
            <li>生成されたファイルを安全な場所に保存</li>
        </ol>
        <p>復元するには「データインポート」ページの「バックアップから復元」機能を使用します。</p>
        """


def create_icon_button(icon: str, label: str = None, tooltip: str = None, on_click: str = None) -> str:
    """
    アイコン付きのボタンHTMLを生成する
    
    Parameters
    ----------
    icon : str
        Featherアイコン名
    label : str, optional
        ボタンのラベル, by default None
    tooltip : str, optional
        ホバー時のツールチップ, by default None
    on_click : str, optional
        クリック時のJavaScriptコード, by default None
    
    Returns
    -------
    str
        ボタンのHTML
    """
    # ランダムIDを生成
    import random
    button_id = f"btn_{random.randint(10000, 99999)}"
    
    # SVGアイコンのパス定義
    icon_paths = {
        "help-circle": '<circle cx="12" cy="12" r="10"></circle><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path><line x1="12" y1="17" x2="12.01" y2="17"></line>',
        "info": '<circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line>',
        "alert-circle": '<circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line>',
        "upload": '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line>',
        "download": '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line>',
        "activity": '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>',
        "bar-chart-2": '<line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line>',
        "save": '<path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path><polyline points="17 21 17 13 7 13 7 21"></polyline><polyline points="7 3 7 8 15 8"></polyline>'
    }
    
    # アイコンのパスが見つからない場合はデフォルトのヘルプアイコンを使用
    icon_path = icon_paths.get(icon, icon_paths["help-circle"])
    
    # ボタンHTML
    button_html = f"""
    <button id="{button_id}" 
            style="background: none; border: none; color: #0066cc; cursor: pointer; padding: 5px; 
                   display: inline-flex; align-items: center; justify-content: center;"
            title="{tooltip if tooltip else ''}"
            {f'onclick="{on_click}"' if on_click else ''}>
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" 
             fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" 
             stroke-linejoin="round" style="margin-right: {5 if label else 0}px;">
            {icon_path}
        </svg>
        {f'<span style="font-size: 14px;">{label}</span>' if label else ''}
    </button>
    """
    
    return button_html
