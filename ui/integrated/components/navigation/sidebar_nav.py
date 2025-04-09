"""
ui.integrated.components.navigation.sidebar_nav

サイドバーナビゲーションコンポーネント
アプリケーションの主要機能にアクセスするためのサイドバーナビゲーションを提供します。
"""

import streamlit as st
from typing import Dict, List, Optional, Any, Callable

class SidebarNavComponent:
    """サイドバーナビゲーションコンポーネント"""
    
    def __init__(self, key_prefix: str = "sidebar_nav"):
        """
        初期化
        
        Parameters
        ----------
        key_prefix : str, optional
            Streamlitコンポーネントキーのプレフィックス, by default "sidebar_nav"
        """
        self.key_prefix = key_prefix
        
        # ナビゲーション項目の定義
        self.nav_items = {
            "main": [
                {
                    "id": "welcome",
                    "label": "ホーム",
                    "icon": "home",
                    "url": "?page=welcome"
                },
                {
                    "id": "project_list",
                    "label": "プロジェクト",
                    "icon": "folder",
                    "url": "?page=project_list"
                },
                {
                    "id": "data_import",
                    "label": "データインポート",
                    "icon": "upload",
                    "url": "?page=data_import"
                }
            ],
            "analysis": [
                {
                    "id": "dashboard",
                    "label": "ダッシュボード",
                    "icon": "grid",
                    "url": "?page=dashboard"
                },
                {
                    "id": "wind_estimation",
                    "label": "風推定",
                    "icon": "wind",
                    "url": "?page=wind_estimation"
                },
                {
                    "id": "strategy_detection",
                    "label": "戦略検出",
                    "icon": "target",
                    "url": "?page=strategy_detection"
                },
                {
                    "id": "performance_analysis",
                    "label": "パフォーマンス分析",
                    "icon": "activity",
                    "url": "?page=performance_analysis"
                }
            ],
            "visualization": [
                {
                    "id": "map_view",
                    "label": "マップビュー",
                    "icon": "map",
                    "url": "?page=map_view"
                },
                {
                    "id": "chart_view",
                    "label": "チャートビュー",
                    "icon": "bar-chart-2",
                    "url": "?page=chart_view"
                },
                {
                    "id": "timeline_view",
                    "label": "タイムラインビュー",
                    "icon": "clock",
                    "url": "?page=timeline_view"
                },
                {
                    "id": "statistical_view",
                    "label": "統計ビュー",
                    "icon": "pie-chart",
                    "url": "?page=statistical_view"
                }
            ],
            "output": [
                {
                    "id": "export",
                    "label": "エクスポート",
                    "icon": "download",
                    "url": "?page=export"
                },
                {
                    "id": "report_builder",
                    "label": "レポート作成",
                    "icon": "file-text",
                    "url": "?page=report_builder"
                }
            ]
        }
        
        # アイコンの定義
        self.icons = {
            "home": '<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline>',
            "folder": '<path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>',
            "upload": '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line>',
            "download": '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line>',
            "grid": '<rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect>',
            "wind": '<path d="M9.59 4.59A2 2 0 1 1 11 8H2m10.59 11.41A2 2 0 1 0 14 16H2m15.73-8.27A2.5 2.5 0 1 1 19.5 12H2"></path>',
            "target": '<circle cx="12" cy="12" r="10"></circle><circle cx="12" cy="12" r="6"></circle><circle cx="12" cy="12" r="2"></circle>',
            "activity": '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>',
            "map": '<polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6"></polygon><line x1="8" y1="2" x2="8" y2="18"></line><line x1="16" y1="6" x2="16" y2="22"></line>',
            "bar-chart-2": '<line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line>',
            "clock": '<circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline>',
            "pie-chart": '<path d="M21.21 15.89A10 10 0 1 1 8 2.83"></path><path d="M22 12A10 10 0 0 0 12 2v10z"></path>',
            "file-text": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline>',
            "settings": '<circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>',
            "help-circle": '<circle cx="12" cy="12" r="10"></circle><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path><line x1="12" y1="17" x2="12.01" y2="17"></line>'
        }
    
    def render(self, current_page: str = None, session_status: Dict[str, Any] = None, on_change: Optional[Callable] = None):
        """
        サイドバーナビゲーションを表示
        
        Parameters
        ----------
        current_page : str, optional
            現在のページID, by default None
        session_status : Dict[str, Any], optional
            セッションの状態(データの有無など), by default None
        on_change : Optional[Callable], optional
            ページ変更時のコールバック, by default None
            
        Returns
        -------
        str
            選択されたページID
        """
        with st.sidebar:
            # ロゴとタイトル
            st.markdown(
                """
                <div style="text-align: center; margin-bottom: 20px;">
                    <h3 style="margin-bottom: 0;">セーリング戦略分析</h3>
                    <p style="margin-top: 0; font-size: 0.9rem; color: #666;">データ分析・可視化システム</p>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # セッション情報
            if session_status:
                self._render_session_status(session_status)
            
            # 各セクションのレンダリング
            st.markdown("### メイン")
            selected_page = self._render_nav_section("main", current_page)
            
            # セッションが必要な機能はデータがある場合のみ表示
            is_data_available = session_status and session_status.get("has_data", False)
            
            if is_data_available:
                st.markdown("### 分析")
                selected_analysis = self._render_nav_section("analysis", current_page)
                if selected_analysis != current_page:
                    selected_page = selected_analysis
                
                st.markdown("### 可視化")
                selected_viz = self._render_nav_section("visualization", current_page)
                if selected_viz != current_page:
                    selected_page = selected_viz
                
                st.markdown("### 出力")
                selected_output = self._render_nav_section("output", current_page)
                if selected_output != current_page:
                    selected_page = selected_output
            else:
                # データが無い場合はグレーアウト表示
                st.markdown("### 分析")
                self._render_disabled_section("analysis")
                
                st.markdown("### 可視化")
                self._render_disabled_section("visualization")
                
                st.markdown("### 出力")
                self._render_disabled_section("output")
            
            # ヘルプセクション
            with st.expander("ヘルプ", expanded=False):
                st.markdown("""
                - [使い方ガイド](#)
                - [チュートリアル](#)
                - [よくある質問](#)
                """)
            
            # フッター
            st.markdown(
                """
                <div style="position: fixed; bottom: 20px; left: 20px; right: 20px; 
                            font-size: 0.8rem; color: #666; text-align: center;">
                    <p>セーリング戦略分析システム v0.5.0</p>
                    <p>© 2025 Sailing Analytics Team</p>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # コールバック実行
            if on_change and selected_page != current_page:
                on_change(selected_page)
            
            return selected_page
    
    def _render_nav_section(self, section: str, current_page: str = None) -> str:
        """
        ナビゲーションセクションを表示
        
        Parameters
        ----------
        section : str
            セクション名
        current_page : str, optional
            現在のページID, by default None
            
        Returns
        -------
        str
            選択されたページID
        """
        selected_page = current_page
        
        # ナビゲーション項目のレンダリング
        for item in self.nav_items.get(section, []):
            is_active = item["id"] == current_page
            
            # アイコンの取得
            icon_svg = self.icons.get(item.get("icon", "help-circle"), self.icons["help-circle"])
            
            # アクティブ状態のスタイル
            active_style = "background-color: #e6f2ff; color: #0366d6; font-weight: 500;" if is_active else ""
            
            # ナビゲーション項目のHTML
            nav_item_html = f"""
            <a href="{item['url']}" 
               style="display: flex; align-items: center; padding: 8px 12px; 
                      text-decoration: none; color: #333; border-radius: 4px; 
                      margin-bottom: 4px; {active_style}"
               onmouseover="this.style.backgroundColor='#f5f5f5';" 
               onmouseout="this.style.backgroundColor='{('#e6f2ff' if is_active else '')}'"
               onclick="return false;" id="nav_item_{item['id']}">
                <span style="margin-right: 10px;">
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" 
                         fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" 
                         stroke-linejoin="round">
                        {icon_svg}
                    </svg>
                </span>
                <span>{item['label']}</span>
            </a>
            """
            
            # HTML表示とクリックイベントハンドリング
            st.markdown(nav_item_html, unsafe_allow_html=True)
            
            # JavaScriptでクリックイベントを取得
            js_code = f"""
            <script>
                document.getElementById("nav_item_{item['id']}").addEventListener('click', function() {{
                    window.location.href = "{item['url']}";
                }});
            </script>
            """
            st.markdown(js_code, unsafe_allow_html=True)
            
            # Streamlitのリンク（JavaScript無効時のフォールバック）
            if st.button(
                item["label"], 
                key=f"{self.key_prefix}_{item['id']}", 
                help=item.get("description", ""),
                use_container_width=True,
                type="secondary" if not is_active else "primary"
            ):
                selected_page = item["id"]
        
        return selected_page
    
    def _render_disabled_section(self, section: str):
        """
        無効化されたナビゲーションセクションを表示
        
        Parameters
        ----------
        section : str
            セクション名
        """
        for item in self.nav_items.get(section, []):
            # アイコンの取得
            icon_svg = self.icons.get(item.get("icon", "help-circle"), self.icons["help-circle"])
            
            # 無効化されたスタイル
            disabled_style = "color: #aaa; cursor: not-allowed;"
            
            # ナビゲーション項目のHTML
            nav_item_html = f"""
            <div style="display: flex; align-items: center; padding: 8px 12px; 
                        border-radius: 4px; margin-bottom: 4px; {disabled_style}">
                <span style="margin-right: 10px;">
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" 
                         fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" 
                         stroke-linejoin="round">
                        {icon_svg}
                    </svg>
                </span>
                <span>{item['label']}</span>
            </div>
            """
            
            st.markdown(nav_item_html, unsafe_allow_html=True)
    
    def _render_session_status(self, session_status: Dict[str, Any]):
        """
        セッション状態を表示
        
        Parameters
        ----------
        session_status : Dict[str, Any]
            セッションの状態情報
        """
        # セッション情報がある場合
        with st.expander("セッション情報", expanded=False):
            if session_status.get("has_data", False):
                # データが読み込まれている場合
                st.markdown(f"**セッション名**: {session_status.get('session_name', '未設定')}")
                
                # データ情報
                data_info = session_status.get("data_info", {})
                if data_info:
                    st.markdown(f"**データポイント**: {data_info.get('point_count', 0):,}点")
                    st.markdown(f"**時間範囲**: {data_info.get('time_range', '不明')}")
                    st.markdown(f"**最終更新**: {data_info.get('last_updated', '不明')}")
                
                # アクションボタン
                col1, col2 = st.columns(2)
                with col1:
                    st.button("保存", key="save_session_btn", use_container_width=True)
                with col2:
                    st.button("クリア", key="clear_session_btn", use_container_width=True)
            else:
                # データが読み込まれていない場合
                st.markdown("データが読み込まれていません。")
                st.markdown("「データインポート」からデータを読み込んでください。")
                
                # インポートに直接移動するボタン
                if st.button("データインポートへ", key="goto_import_btn", use_container_width=True):
                    return "data_import"
        
        return None
