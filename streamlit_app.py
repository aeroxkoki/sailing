"""
セーリング戦略分析システム - Streamlit Cloudエントリーポイント

このファイルはStreamlit Cloudでのデプロイ用エントリーポイントです。
UI/UXが改善された風向風速可視化デモを表示します。
"""

import os
import sys
import streamlit as st
import traceback
import importlib
import logging
import pathlib

# プロジェクトのルートディレクトリをパスに追加（pathlib使用でプラットフォーム互換性向上）
current_dir = pathlib.Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

# 明示的にsailing_data_processorとuiモジュールをインポート可能にする
# Streamlit Cloud環境でのモジュール解決を確実にするため
sailing_processor_path = current_dir / 'sailing_data_processor'
ui_path = current_dir / 'ui'
sys.path.insert(0, str(sailing_processor_path))
sys.path.insert(0, str(ui_path))

# ロギングの設定（環境に応じて適切なハンドラを使用）
is_cloud = os.environ.get('STREAMLIT_SERVER_HEADLESS', 'false') == 'true'

if is_cloud:
    # クラウド環境ではファイル書き込みができないためStreamHandlerのみ使用
    handlers = [logging.StreamHandler()]
    log_message = "クラウド環境用ロギング設定を使用（ファイル書き込みなし）"
else:
    # ローカル環境ではファイルとコンソールの両方にログを出力
    log_file = str(current_dir / "streamlit_cloud.log")
    handlers = [
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
    log_message = f"ローカル環境用ロギング設定を使用（ログファイル: {log_file}）"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=handlers
)
logger = logging.getLogger(__name__)
logger.info(log_message)

# システム環境の記録（デバッグ用）
logger.info(f"Python バージョン: {sys.version}")
logger.info(f"実行パス: {sys.executable}")
logger.info(f"作業ディレクトリ: {os.getcwd()}")
logger.info(f"Python パス: {sys.path}")

# ページ設定（app_v6.pyとの重複を避けるためここで一度だけ設定）
st.set_page_config(
    page_title="セーリング戦略分析システム",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 依存モジュールが正しく解決できるかチェック
try:
    # モジュールの存在チェック
    required_modules = [
        'streamlit',
        'pandas',
        'numpy',
        'folium',
        'ui.components.navigation.top_bar',
        'ui.components.navigation.context_bar',
        'ui.components.visualizations.wind_flow_map',
        'ui.components.visualizations.boat_marker',
        'ui.components.controls.timeline_control',
        'sailing_data_processor.utilities.wind_field_generator'
    ]
    
    missing_modules = []
    for module_name in required_modules:
        try:
            importlib.import_module(module_name)
            logger.info(f"モジュールをインポートできました: {module_name}")
        except ImportError as e:
            missing_modules.append((module_name, str(e)))
            logger.error(f"モジュールのインポートに失敗: {module_name} - {e}")
    
    if missing_modules:
        st.error("以下のモジュールが見つかりませんでした：")
        for module, error in missing_modules:
            st.write(f"- {module}: {error}")
        st.info("モジュール構造を確認してください。")
    else:
        # 全てのモジュールが正常に解決できる場合、風向風速デモを実行
        from ui.demo.wind_flow_demo import run_demo
        
        # デモのUI非表示化設定
        if is_cloud:
            st.sidebar.info("このアプリはStreamlit Cloud上でホストされています。")
            st.sidebar.markdown("---")
            st.sidebar.markdown("### セーリング戦略分析システム")
            st.sidebar.markdown("UI/UX改善版 - 風向風速可視化デモ")
            
        # デモアプリの実行
        run_demo()
        
except Exception as e:
    st.error(f"アプリケーションの読み込み中にエラーが発生しました: {e}")
    st.code(traceback.format_exc())
    
    # 詳細なシステム情報を表示（デバッグ用）
    st.subheader("システム情報")
    st.write(f"Python バージョン: {sys.version}")
    st.write(f"実行パス: {sys.executable}")
    st.write(f"作業ディレクトリ: {os.getcwd()}")
    
    # モジュールのインポートパスを表示
    st.write(f"Pythonパス: {sys.path}")
    st.info("開発者向け情報: このファイルはStreamlit Cloudデプロイ用のエントリーポイントです。")
