# -*- coding: utf-8 -*-
"""
セーリング戦略分析システム - リダイレクトスクリプト

このファイルは、最新バージョンのアプリケーションにリダイレクトするためのラッパーです。
"""

import os
import sys
import streamlit as st

# メッセージを表示して新しいバージョンにリダイレクト
st.set_page_config(
    page_title="セーリング戦略分析システム - リダイレクト",
    page_icon="🌊",
    layout="wide"
)

st.title("セーリング戦略分析システム")
st.info("最新バージョンのアプリケーションにリダイレクトしています...")

# 現在のディレクトリと実行パスを取得
current_dir = os.path.dirname(os.path.abspath(__file__))
main_app_path = os.path.join(current_dir, "app_v5.py")

# app_v5.pyへのインポートと実行
sys.path.insert(0, os.path.abspath(os.path.join(current_dir, '..')))

try:
    # 別プロセスとしてapp_v5.pyを起動（Streamlit環境では直接インポートして実行することは難しい）
    st.info(f"新しいバージョンを起動しています: {main_app_path}")
    st.write("このページを閉じて、新しく開いたアプリケーションをご利用ください。")
    
    # 起動コマンドを表示
    st.code(f"streamlit run {main_app_path}", language="bash")
    
    # ボタンクリックで新しいバージョンを起動
    if st.button("最新バージョンを起動", type="primary"):
        import subprocess
        try:
            subprocess.Popen(["streamlit", "run", main_app_path])
            st.success("新しいウィンドウでアプリケーションを起動しました")
        except Exception as e:
            st.error(f"起動エラー: {e}")

except Exception as e:
    st.error(f"エラーが発生しました: {e}")
    st.error("コマンドラインから以下のコマンドを実行してください:")
    st.code(f"streamlit run {main_app_path}", language="bash")
