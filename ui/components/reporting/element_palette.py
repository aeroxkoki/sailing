"""
ui.components.reporting.element_palette

要素パレットコンポーネントを提供するモジュールです。
"""

import streamlit as st
from typing import Dict, List, Any, Optional, Callable

from sailing_data_processor.reporting.templates.template_model import ElementType


def render_element_palette(on_element_select: Callable[[ElementType, str], None]) -> None:
    """
    要素パレットを描画
    
    Parameters
    ----------
    on_element_select : Callable[[ElementType, str], None]
        要素が選択された時のコールバック関数
        引数はElementTypeと要素名
    """
    st.sidebar.header("要素パレット")
    
    # 要素カテゴリの定義
    element_categories = {
        "コンテンツ要素": [
            {"type": ElementType.TEXT, "name": "テキスト", "icon": "📝", "description": "静的または動的テキストを表示"},
            {"type": ElementType.TABLE, "name": "テーブル", "icon": "🗃️", "description": "データをテーブル形式で表示"},
            {"type": ElementType.LIST, "name": "リスト", "icon": "📋", "description": "データをリスト形式で表示"},
            {"type": ElementType.KEY_VALUE, "name": "キーバリュー", "icon": "🔑", "description": "キーと値のペアを表示"}
        ],
        "視覚化要素": [
            {"type": ElementType.CHART, "name": "チャート", "icon": "📊", "description": "データをチャートとして表示"},
            {"type": ElementType.MAP, "name": "マップ", "icon": "🗺️", "description": "地理データをマップとして表示"},
            {"type": ElementType.DIAGRAM, "name": "ダイアグラム", "icon": "📈", "description": "データをダイアグラムとして表示"}
        ],
        "メディア要素": [
            {"type": ElementType.IMAGE, "name": "画像", "icon": "🖼️", "description": "画像を表示"}
        ],
        "レイアウト要素": [
            {"type": ElementType.SECTION, "name": "セクション", "icon": "📑", "description": "コンテンツのグループ化"},
            {"type": ElementType.COLUMN, "name": "カラム", "icon": "🧱", "description": "垂直方向のレイアウト"},
            {"type": ElementType.GRID, "name": "グリッド", "icon": "🔲", "description": "グリッドレイアウト"},
            {"type": ElementType.TAB, "name": "タブ", "icon": "🔖", "description": "タブ形式でコンテンツを表示"}
        ],
        "装飾要素": [
            {"type": ElementType.DIVIDER, "name": "区切り線", "icon": "➖", "description": "コンテンツの視覚的な区切り"},
            {"type": ElementType.BOX, "name": "ボックス", "icon": "📦", "description": "コンテンツをボックスで囲む"},
            {"type": ElementType.BACKGROUND, "name": "背景", "icon": "🎨", "description": "子要素に背景を提供"}
        ]
    }
    
    # 各カテゴリの要素を表示
    for category, elements in element_categories.items():
        with st.sidebar.expander(category, expanded=True):
            for element in elements:
                col1, col2 = st.columns([1, 4])
                
                with col1:
                    st.write(element["icon"])
                
                with col2:
                    if st.button(element["name"], key=f"element_{element['type'].value}", help=element["description"]):
                        on_element_select(element["type"], element["name"])


def render_element_palette_drag_drop(on_element_drag: Callable[[ElementType, str], None]) -> None:
    """
    ドラッグ＆ドロップ対応の要素パレットを描画
    
    注: 実際のドラッグ＆ドロップ実装にはJavaScriptとの連携が必要になるため、
    このサンプル実装ではクリックベースのインタフェースを提供します。
    
    Parameters
    ----------
    on_element_drag : Callable[[ElementType, str], None]
        要素がドラッグされた時のコールバック関数
        引数はElementTypeと要素名
    """
    # 簡易版のパレットで代用
    render_element_palette(on_element_drag)
    
    # 実際のドラッグ＆ドロップは将来的に実装する注記
    st.sidebar.info("注: ドラッグ＆ドロップ機能はクリックで代用しています。将来的には実際のドラッグ＆ドロップインタフェースを実装予定です。")
