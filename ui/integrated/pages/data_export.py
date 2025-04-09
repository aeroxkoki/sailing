"""
ui.integrated.pages.data_export

データエクスポート機能ページ
セッションデータや分析結果のエクスポートを提供します。
このページは export.py に統合されました。
"""

import streamlit as st
import os
import sys

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

# リダイレクト用
from ui.integrated.pages.export import render_page as render_export_page


def render_page():
    """データエクスポートページをレンダリングする関数（リダイレクト）"""
    st.info("このページは統合エクスポートページに移行しました。新しいエクスポート機能をご利用ください。")
    # 新しいエクスポートページにリダイレクト
    render_export_page()


if __name__ == "__main__":
    render_page()
