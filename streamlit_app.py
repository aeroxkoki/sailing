"""
セーリング戦略分析システム - Streamlit Cloudエントリーポイント

このファイルはStreamlit Cloudでのデプロイ用エントリーポイントです。
アプリケーションのメインファイル（ui/app_v5.py）を実行します。
"""

import os
import sys
import streamlit as st

# プロジェクトのルートディレクトリをパスに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# デバッグモードを有効化
os.environ['STREAMLIT_DEBUG'] = 'true'

# メインアプリケーションのインポートと実行
try:
    from ui.app_v5 import *
    # app_v5.pyのコードが自動的に実行されます
except Exception as e:
    st.error(f"アプリケーションの読み込み中にエラーが発生しました: {e}")
    import traceback
    st.code(traceback.format_exc())
    
    # 詳細なシステム情報を表示（デバッグ用）
    st.subheader("システム情報")
    st.write(f"Python バージョン: {sys.version}")
    st.write(f"実行パス: {sys.executable}")
    st.write(f"作業ディレクトリ: {os.getcwd()}")
    st.write(f"ファイル一覧:")
    # 最大深度2までのファイル一覧を表示
    for root, dirs, files in os.walk(".", topdown=True):
        # ルートからの相対パスの深さを計算
        depth = root.count(os.sep)
        if depth > 1:  # 深さ2以上は除外
            dirs[:] = []  # サブディレクトリの探索をスキップ
            continue
        for name in files:
            st.write(os.path.join(root, name))
    
    # モジュールのインポートパスを表示
    st.write(f"Pythonパス: {sys.path}")
    st.info("開発者向け情報: このファイルはStreamlit Cloudデプロイ用のエントリーポイントです。")
    
    # 依存関係情報の表示（デバッグ用）
    if os.environ.get('STREAMLIT_DEBUG', '').lower() == 'true':
        st.write("システム情報:")
        st.write(f"Python バージョン: {sys.version}")
        st.write(f"実行パス: {sys.executable}")
        st.write(f"PYTHONPATH: {sys.path}")
        
        try:
            import pandas as pd
            import numpy as np
            st.success("主要ライブラリ (pandas, numpy) の読み込みに成功しました。")
        except ImportError as e:
            st.error(f"主要ライブラリの読み込みに失敗しました: {e}")
