# -*- coding: utf-8 -*-
"""
セーリング戦略分析システム - サイドバーナビゲーションコンポーネント

サイドバーメニューのコンポーネントを提供します。
"""

import streamlit as st
from ..styles import Colors, Spacing, BorderRadius, FontSizes, FontWeights, Transitions

def create_sidebar_menu(
    items,
    title=None,
    active_item=None,
    key_prefix="sidebar",
    callback=None
):
    """
    サイドバーメニューを作成します。
    
    Parameters:
    -----------
    items : list of dict
        メニュー項目のリスト。各辞書は以下のキーを持つことができます：
        - label: 表示テキスト（必須）
        - id: 項目の識別子（任意、指定がない場合はlabelが使用される）
        - icon: 項目のアイコン（任意、Font Awesomeクラス）
        - items: サブメニュー項目のリスト（任意、ネストされたメニュー用）
    title : str, optional
        メニュータイトル
    active_item : str, optional
        現在アクティブな項目のID
    key_prefix : str, optional
        キー生成時のプレフィックス
    callback : callable, optional
        メニュー項目選択時に呼び出すコールバック関数
        
    Returns:
    --------
    str
        選択されたメニュー項目のID
    """
    # セッション状態にアクティブなメニュー項目を保存
    if 'sidebar_active_item' not in st.session_state:
        st.session_state.sidebar_active_item = active_item
    
    # サイドバースタイルの定義
    sidebar_style = f"""
    <style>
    section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] {{
        padding: 0;
    }}
    
    .sidebar-menu {{
        padding: {Spacing.XS} 0;
    }}
    
    .sidebar-title {{
        color: {Colors.DARK_2};
        font-size: {FontSizes.SUBTITLE};
        font-weight: {FontWeights.SEMIBOLD};
        padding: {Spacing.M} {Spacing.M} {Spacing.S};
        margin: 0;
    }}
    
    .sidebar-menu-item {{
        display: flex;
        align-items: center;
        padding: {Spacing.S} {Spacing.M};
        margin-bottom: {Spacing.XS};
        color: {Colors.DARK_1};
        text-decoration: none;
        font-size: {FontSizes.BODY};
        border-left: 3px solid transparent;
        transition: all {Transitions.FAST} ease-out;
        cursor: pointer;
    }}
    
    .sidebar-menu-item:hover {{
        background-color: {Colors.GRAY_1};
        border-left-color: {Colors.GRAY_MID};
        color: {Colors.DARK_2};
    }}
    
    .sidebar-menu-item.active {{
        background-color: {Colors.PRIMARY}10;
        border-left-color: {Colors.PRIMARY};
        color: {Colors.PRIMARY};
        font-weight: {FontWeights.MEDIUM};
    }}
    
    .sidebar-menu-item i {{
        margin-right: {Spacing.S};
        width: 16px;
        text-align: center;
    }}
    
    .sidebar-submenu {{
        padding-left: {Spacing.L};
    }}
    
    .sidebar-menu-divider {{
        height: 1px;
        background-color: {Colors.GRAY_2};
        margin: {Spacing.S} {Spacing.M};
    }}
    </style>
    """
    
    st.markdown(sidebar_style, unsafe_allow_html=True)
    
    # サイドバータイトル
    if title:
        st.sidebar.markdown(f'<h3 class="sidebar-title">{title}</h3>', unsafe_allow_html=True)
    
    # メニューHTMLの生成
    menu_html = '<div class="sidebar-menu">'
    
    # 選択された項目をトラッキングするための辞書
    selected_item = None
    
    # メニュー項目の生成（再帰的）
    def generate_menu_items(items, level=0, parent_id=None):
        nonlocal menu_html, selected_item
        
        for i, item in enumerate(items):
            item_label = item.get('label', f'Item {i}')
            item_id = item.get('id', item_label)
            item_icon = item.get('icon', None)
            item_subitems = item.get('items', None)
            
            # 完全な項目IDの生成（親IDを含む）
            full_item_id = f"{parent_id}_{item_id}" if parent_id else item_id
            key = f"{key_prefix}_{full_item_id}"
            
            # アクティブ状態の判定
            is_active = st.session_state.sidebar_active_item == full_item_id
            active_class = "active" if is_active else ""
            
            # アイコンの追加
            icon_html = f'<i class="{item_icon}"></i>' if item_icon else ''
            
            # メニュー項目のHTML
            menu_html += f"""
            <div class="sidebar-menu-item {active_class}" 
                 onclick="
                    (function() {{
                        const data = {{key: '{key}', value: true}};
                        fetch('/_stcore/component_communication', {{
                            method: 'POST',
                            headers: {{'Content-Type': 'application/json'}},
                            body: JSON.stringify(data)
                        }});
                    }})();
                    return false;"
            >
                {icon_html} {item_label}
            </div>
            """
            
            # クリック検出（セッション状態経由）
            if key not in st.session_state:
                st.session_state[key] = False
            elif st.session_state[key]:
                st.session_state[key] = False
                st.session_state.sidebar_active_item = full_item_id
                selected_item = full_item_id
                
                # コールバック関数がある場合は呼び出し
                if callback:
                    callback(full_item_id)
            
            # サブメニューがある場合は再帰的に処理
            if item_subitems:
                menu_html += '<div class="sidebar-submenu">'
                generate_menu_items(item_subitems, level + 1, full_item_id)
                menu_html += '</div>'
        
        # 区切り線（最後の項目以外）
        if level == 0 and items:
            menu_html += '<div class="sidebar-menu-divider"></div>'
    
    # メニュー項目の生成
    generate_menu_items(items)
    menu_html += '</div>'
    
    # メニューの表示
    st.sidebar.markdown(menu_html, unsafe_allow_html=True)
    
    # 選択された項目のIDを返す
    return selected_item or st.session_state.sidebar_active_item

def create_sidebar_collapse(label="メニューを閉じる", icon="fas fa-chevron-left"):
    """
    サイドバーを折りたたむためのボタンを作成します。
    
    Parameters:
    -----------
    label : str, optional
        ボタンのラベル
    icon : str, optional
        ボタンのアイコン（Font Awesomeクラス）
        
    Returns:
    --------
    bool
        ボタンがクリックされたかどうか
    """
    # サイドバー折りたたみボタンのスタイル
    collapse_style = f"""
    <style>
    .sidebar-collapse-button {{
        display: flex;
        align-items: center;
        justify-content: center;
        padding: {Spacing.S} {Spacing.M};
        margin: {Spacing.M} {Spacing.M};
        background-color: {Colors.GRAY_1};
        color: {Colors.DARK_1};
        border-radius: {BorderRadius.SMALL};
        cursor: pointer;
        transition: all {Transitions.FAST} ease-out;
        font-size: {FontSizes.BODY};
    }}
    
    .sidebar-collapse-button:hover {{
        background-color: {Colors.GRAY_2};
        color: {Colors.DARK_2};
    }}
    
    .sidebar-collapse-button i {{
        margin-right: {Spacing.S};
    }}
    </style>
    """
    
    st.sidebar.markdown(collapse_style, unsafe_allow_html=True)
    
    # ボタンのHTML
    button_key = "sidebar_collapse_button"
    button_html = f"""
    <div class="sidebar-collapse-button"
         onclick="
            (function() {{
                const data = {{key: '{button_key}', value: true}};
                fetch('/_stcore/component_communication', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify(data)
                }});
            }})();
            return false;">
        <i class="{icon}"></i> {label}
    </div>
    """
    
    st.sidebar.markdown(button_html, unsafe_allow_html=True)
    
    # クリック検出（セッション状態経由）
    if button_key not in st.session_state:
        st.session_state[button_key] = False
    
    clicked = False
    if st.session_state[button_key]:
        st.session_state[button_key] = False
        clicked = True
    
    return clicked
