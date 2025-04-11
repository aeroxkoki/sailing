"""
セーリング戦略分析システム - Streamlit Cloudエントリーポイント

このファイルはStreamlit Cloudでのデプロイ用エントリーポイントです。
アプリケーションのメインファイル（ui/app_v5.py）を実行します。
"""

import os
import sys
import streamlit as st
import traceback
import importlib
import logging

# プロジェクトのルートディレクトリをパスに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# 明示的にsailing_data_processorとuiモジュールをインポート可能にする
# Streamlit Cloud環境でのモジュール解決を確実にするため
sailing_processor_path = os.path.join(current_dir, 'sailing_data_processor')
ui_path = os.path.join(current_dir, 'ui')
sys.path.insert(0, sailing_processor_path)
sys.path.insert(0, ui_path)

# ロギングの設定（ファイルに書き込まれてデバッグに役立つ）
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(current_dir, "streamlit_cloud.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# システム環境の記録（デバッグ用）
logger.info(f"Python バージョン: {sys.version}")
logger.info(f"実行パス: {sys.executable}")
logger.info(f"作業ディレクトリ: {os.getcwd()}")
logger.info(f"Python パス: {sys.path}")

# ページ設定（app_v5.pyとの重複を避けるためここで一度だけ設定）
st.set_page_config(
    page_title="セーリング戦略分析システム",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# デバッグモードを有効化
os.environ['STREAMLIT_DEBUG'] = 'true'

# validation ディレクトリの存在確認（デバッグ用）
validation_dir = os.path.join(current_dir, 'sailing_data_processor', 'validation')
if not os.path.exists(validation_dir):
    try:
        os.makedirs(validation_dir)
        st.warning(f"validation ディレクトリが存在しなかったため作成しました: {validation_dir}")
    except Exception as e:
        st.error(f"validation ディレクトリの作成に失敗しました: {e}")

# 必須モジュールファイルの存在確認
required_files = [
    os.path.join('sailing_data_processor', 'validation', 'quality_metrics.py'),
    os.path.join('sailing_data_processor', 'validation', 'quality_metrics_improvements.py'),
    os.path.join('sailing_data_processor', 'validation', 'quality_metrics_integration.py'),
    os.path.join('ui', 'pages', 'basic_project_management.py')
]

missing_files = []
for file_path in required_files:
    full_path = os.path.join(current_dir, file_path)
    if not os.path.exists(full_path):
        missing_files.append(file_path)

if missing_files:
    st.error("必須ファイルが見つかりません。")
    st.write("見つからないファイル:")
    for file in missing_files:
        st.write(f"- {file}")
    st.info("モジュール構造を修正してください。")
    st.stop()

# メインアプリケーションのインポートと実行
try:
    # 明示的に sailing_data_processor.validation モジュールが利用可能か確認
    try:
        import sailing_data_processor.validation
        st.success("sailing_data_processor.validation モジュールが正常にインポートされました。")
    except ImportError as e:
        st.error(f"sailing_data_processor.validation モジュールのインポートに失敗しました: {e}")
        
    # QualityMetricsCalculator クラスが利用可能か確認
    try:
        from sailing_data_processor.validation.quality_metrics import QualityMetricsCalculator
        st.success("QualityMetricsCalculator クラスが正常にインポートされました。")
    except ImportError as e:
        st.error(f"QualityMetricsCalculator クラスのインポートに失敗しました: {e}")
        
    # メインアプリを実行（ページ設定は既に行われているため直接インポート）
    import ui.app_v5
    
except Exception as e:
    st.error(f"アプリケーションの読み込み中にエラーが発生しました: {e}")
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
        try:
            import pandas as pd
            import numpy as np
            st.success("主要ライブラリ (pandas, numpy) の読み込みに成功しました。")
        except ImportError as e:
            st.error(f"主要ライブラリの読み込みに失敗しました: {e}")
        
        # ディレクトリ構造を表示
        st.write("ディレクトリ構造:")
        for root, dirs, files in os.walk(".", topdown=True, maxdepth=3):
            level = root.count(os.sep)
            indent = ' ' * 4 * level
            st.write(f"{indent}{os.path.basename(root)}/")
            sub_indent = ' ' * 4 * (level + 1)
            for f in files:
                st.write(f"{sub_indent}{f}")
