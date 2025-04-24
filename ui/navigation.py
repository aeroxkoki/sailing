# -*- coding: utf-8 -*-
"""
セーリング戦略分析システム - ナビゲーションコンポーネント

フェーズ2のUI/UX改善に合わせて拡張されたナビゲーションモジュール
"""

import streamlit as st
from typing import Optional, Dict, Any, List, Tuple

def create_navigation(logo_path: Optional[str] = None, mobile_responsive: bool = True):
    """
    サイドバーナビゲーションを作成（フェーズ2改良版）
    
    Parameters
    ----------
    logo_path : str, optional
        ロゴ画像のパス
    mobile_responsive : bool, optional
        モバイルレスポンシブ対応するか
        
    Returns
    -------
    str
        選択されたナビゲーション項目
    """
    # モバイル検出
    is_mobile = False
    if mobile_responsive:
        # ブラウザの幅でモバイルかどうかを推定
        # JavaScriptを使用して画面幅を取得
        screen_width_js = """
            <script>
                var width = window.innerWidth;
                localStorage.setItem('screenWidth', width);
            </script>
            <p id="screen_width" style="display:none;"></p>
        """
        st.markdown(screen_width_js, unsafe_allow_html=True)
        
        # セッション状態でモバイルモードを管理
        if 'is_mobile' not in st.session_state:
            st.session_state.is_mobile = False
        
        # モバイルモード切り替えボタン
        if st.sidebar.checkbox("モバイルモード", value=st.session_state.is_mobile, key="mobile_mode"):
            st.session_state.is_mobile = True
            is_mobile = True
        else:
            st.session_state.is_mobile = False
    
    with st.sidebar:
        # ロゴとタイトル
        col1, col2 = st.columns([1, 3])
        with col1:
            if logo_path:
                st.image(logo_path, width=60)
            else:
                st.markdown("""
                <div style="font-size: 40px; color: var(--main-color); text-align: center;">
                    <i class="fas fa-sailboat"></i>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            st.title("セーリング分析")
        
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        
        # ナビゲーション項目
        nav_items = {
            "マップビュー": {"icon": "map-marker-alt", "desc": "GPSデータの地図表示", "badge": None},
            "プロジェクト管理": {"icon": "project-diagram", "desc": "プロジェクトの作成・管理", "badge": None},
            "データ管理": {"icon": "database", "desc": "データのインポート・エクスポート", 
                      "badge": len(st.session_state.get('boats_data', {})) if st.session_state.get('boats_data') else None},
            "パフォーマンス分析": {"icon": "chart-line", "desc": "速度・風向の分析", "badge": None},
            "戦略評価": {"icon": "chess", "desc": "戦略的判断の評価", "badge": "New"},
            "設定": {"icon": "cog", "desc": "システム設定", "badge": None}
        }
        
        selected = None
        
        for nav_name, nav_info in nav_items.items():
            icon = nav_info["icon"]
            desc = nav_info["desc"]
            badge = nav_info["badge"]
            
            # アクティブ状態の判定
            is_active = "page" in st.session_state and st.session_state.page == nav_name
            active_class = "active" if is_active else ""
            
            # バッジの表示
            badge_html = ""
            if badge is not None:
                if badge == "New":
                    badge_html = f"""
                    <div style="display: inline-block; background-color: var(--accent-color); color: white; 
                            border-radius: 10px; padding: 2px 6px; font-size: 10px; margin-left: 8px;">
                        {badge}
                    </div>
                    """
                else:
                    badge_html = f"""
                    <div style="display: inline-block; background-color: var(--main-color); color: white; 
                            border-radius: 50%; width: 20px; height: 20px; font-size: 12px; text-align: center; 
                            line-height: 20px; margin-left: 8px;">
                        {badge}
                    </div>
                    """
            
            # 改良されたナビゲーション項目HTML
            item_html = f"""
            <div class="nav-item {active_class}" 
                 style="display: flex; justify-content: space-between; align-items: center;">
                <div style="display: flex; align-items: center;">
                    <i class="fas fa-{icon}" style="min-width: 24px; text-align: center;"></i>
                    <span style="margin-left: 12px;">{nav_name}</span>
                    {badge_html}
                </div>
                <i class="fas fa-chevron-right" style="font-size: 12px; opacity: 0.5;"></i>
            </div>
            <div style="font-size: 12px; color: var(--text-secondary); margin: -5px 0 12px 36px;">
                {desc}
            </div>
            """
            
            # クリックイベント
            if st.markdown(item_html, unsafe_allow_html=True):
                st.session_state.page = nav_name
                selected = nav_name
        
        # データサマリーセクション（強化版）
        st.markdown("---")
        
        if 'boats_data' in st.session_state and st.session_state.boats_data:
            boat_count = len(st.session_state.boats_data)
            total_points = sum(len(df) for df in st.session_state.boats_data.values())
            
            st.markdown(f"""
            <div style="background-color: rgba(21, 101, 192, 0.1); border-radius: 8px; padding: 12px; margin: 8px 0;">
                <p style="margin: 0; font-weight: 600; color: var(--main-color);">現在のデータセット</p>
                <div style="display: flex; justify-content: space-between; margin-top: 8px;">
                    <div>
                        <span style="font-weight: 600; font-size: 18px;">{boat_count}</span>
                        <span style="color: var(--text-secondary); font-size: 12px;"> 艇</span>
                    </div>
                    <div>
                        <span style="font-weight: 600; font-size: 18px;">{total_points:,}</span>
                        <span style="color: var(--text-secondary); font-size: 12px;"> データポイント</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # データ管理へのクイックリンク
            st.markdown("""
            <div style="text-align: center; margin-top: 8px;">
                <a href="#" onclick="Streamlit.setComponentValue('goto_data_management');" 
                   style="color: var(--accent-color); text-decoration: none; font-size: 14px;">
                    <i class="fas fa-external-link-alt"></i> データ管理ページへ
                </a>
            </div>
            """, unsafe_allow_html=True)
            
            clicked = st.markdown("", unsafe_allow_html=True)
            if clicked == 'goto_data_management':
                st.session_state.page = "データ管理"
                selected = "データ管理"
        else:
            st.markdown("""
            <div style="background-color: rgba(255, 167, 38, 0.1); border-radius: 8px; padding: 12px; margin: 8px 0;">
                <p style="margin: 0; color: var(--warning-color);">
                    <i class="fas fa-exclamation-triangle"></i> データがありません
                </p>
                <p style="margin: 4px 0 0 0; font-size: 12px; color: var(--text-secondary);">
                    「データ管理」ページからデータをアップロードしてください。
                </p>
            </div>
            """, unsafe_allow_html=True)
    
        # フッター
        st.sidebar.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
        st.sidebar.markdown("""
        <div style="position: absolute; bottom: 20px; left: 20px; right: 20px; text-align: center; 
                 font-size: 12px; color: var(--text-secondary);">
            セーリング戦略分析システム v1.5<br>
            <a href="#" style="color: var(--accent-color); text-decoration: none; font-size: 12px;">
                <i class="fas fa-question-circle"></i> ヘルプ
            </a> | 
            <a href="#" style="color: var(--accent-color); text-decoration: none; font-size: 12px;">
                <i class="fas fa-bug"></i> 問題を報告
            </a>
        </div>
        """, unsafe_allow_html=True)
    
    # モバイル向けナビゲーションバー（下部固定）
    if is_mobile:
        mobile_nav_html = """
        <div style="position: fixed; bottom: 0; left: 0; right: 0; background-color: white; 
                   box-shadow: 0 -2px 5px rgba(0,0,0,0.1); display: flex; z-index: 1000;">
        """
        
        mobile_nav_items = {
            "マップビュー": "map-marker-alt",
            "プロジェクト管理": "project-diagram",
            "データ管理": "database",
            "パフォーマンス分析": "chart-line",
            "設定": "cog"
        }
        
        for nav_name, icon in mobile_nav_items.items():
            is_active = "page" in st.session_state and st.session_state.page == nav_name
            active_style = "color: var(--main-color);" if is_active else "color: var(--text-secondary);"
            
            mobile_nav_html += f"""
            <a href="#" onclick="Streamlit.setComponentValue('mobile_{nav_name}');" 
               style="flex: 1; padding: 12px 4px; text-align: center; text-decoration: none; {active_style}">
                <div><i class="fas fa-{icon}" style="font-size: 18px;"></i></div>
                <div style="font-size: 10px; margin-top: 4px;">{nav_name}</div>
            </a>
            """
        
        mobile_nav_html += "</div>"
        
        # 底部のパディングを追加（モバイルナビゲーションバーのスペース確保）
        st.markdown("""
        <div style="height: 60px;"></div>
        """, unsafe_allow_html=True)
        
        # モバイルナビゲーションバーを表示
        clicked = st.markdown(mobile_nav_html, unsafe_allow_html=True)
        
        # モバイルナビゲーションのクリックイベント処理
        if clicked and clicked.startswith('mobile_'):
            nav_name = clicked[7:]  # 'mobile_' プレフィックスを取り除く
            st.session_state.page = nav_name
            selected = nav_name
    
    # デフォルト選択がない場合は最初の項目を返す
    if "page" not in st.session_state:
        st.session_state.page = "マップビュー"
    
    return selected or st.session_state.page
