"""
ui.app_v5

セーリング戦略分析システムの最新バージョンのアプリケーション
このファイルはアプリケーションのメインエントリーポイントです。
"""

import streamlit as st
import pandas as pd
import numpy as np
import os
import sys
import logging
import traceback
from streamlit_folium import folium_static
import folium

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 先に依存モジュールが正しくロードされているか確認
try:
    # 明示的に依存モジュールをインポート
    import sailing_data_processor.validation.quality_metrics_integration as quality_metrics_integration
    logger.info("Quality metrics integration モジュールのロードに成功")
    
    # MetricsCalculator のインポート問題を診断
    try:
        from sailing_data_processor.validation.quality_metrics import QualityMetricsCalculator
        logger.info("QualityMetricsCalculator クラスのロードに成功")
    except ImportError as e:
        logger.error(f"QualityMetricsCalculator ロードエラー: {e}")
        st.warning("QualityMetricsCalculator クラスのロードに失敗しました")
    
    # 各モジュールの存在を確認
    import os
    required_files = [
        'sailing_data_processor/validation/quality_metrics.py',
        'sailing_data_processor/validation/quality_metrics_improvements.py',
        'sailing_data_processor/validation/quality_metrics_integration.py',
        'ui/pages/basic_project_management.py'
    ]
    
    for file_path in required_files:
        full_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), file_path)
        if os.path.exists(full_path):
            logger.info(f"ファイル存在確認: {file_path} ✓")
        else:
            logger.error(f"ファイル存在確認: {file_path} ✗ (見つかりません)")
except Exception as diag_error:
    logger.error(f"依存モジュール診断エラー: {diag_error}")
    logger.error(traceback.format_exc())

# UI ページのインポート
try:
    # インポート順序を変更して問題を回避
    logger.info("UIページのインポートを開始...")
    
    # 明示的に基本モジュールをインポート
    import ui.pages.basic_project_management
    import ui.pages.data_validation
    import ui.pages.session_management
    
    # 実際の関数をインポート
    from ui.pages.basic_project_management import render_page as render_project_management
    from ui.pages.data_validation import render_page as render_data_validation
    from ui.pages.session_management import render_page as render_session_management
    
    # 追加のインポートを必要に応じて行う
    logger.info("UI モジュールの読み込みに成功しました。")
    UI_MODULES_LOADED = True
except ImportError as e:
    logger.error(f"モジュールの読み込みに失敗しました: {e}")
    traceback.print_exc()
    UI_MODULES_LOADED = False
    
    # インポートが失敗した場合のダミー関数を定義
    def dummy_render():
        st.error("モジュールの読み込みに失敗しました。")
        st.info("詳細なエラー情報については、ログをご確認ください。")
        st.code(traceback.format_exc())
        
    # ダミー関数で置き換え
    render_project_management = dummy_render
    render_data_validation = dummy_render
    render_session_management = dummy_render

# ページ設定
st.set_page_config(
    page_title="セーリング戦略分析システム",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# アプリケーションのタイトル
st.title('セーリング戦略分析システム')

# ページ選択
page = st.sidebar.selectbox(
    'ナビゲーション',
    ['プロジェクト管理', 'セッション管理', 'マップビュー', 'データ管理', 'データ検証', 'パフォーマンス分析', 'ヘルプ']
)

# 選択したページの表示
try:
    # モジュールのロードに失敗した場合、診断モードを表示
    if not UI_MODULES_LOADED:
        st.error("アプリケーションモジュールの読み込みに失敗しました。")
        st.info("診断モード: ロード中に発生したエラーのトレースを表示します。")
        st.warning("解決策: MetricsCalculatorのインポートエラーが発生しています。モジュールパス設定を確認してください。")
        
        # エラーの詳細を表示
        with st.expander("エラーの詳細", expanded=True):
            st.code(traceback.format_exc())
            
        # トラブルシューティング情報
        with st.expander("トラブルシューティング", expanded=True):
            st.markdown("""
            ### トラブルシューティング手順
            
            1. **モジュールのパス確認**：
               - `sailing_data_processor.validation.quality_metrics` モジュールの存在を確認
               - `MetricsCalculator` クラスの存在を確認
            
            2. **依存関係の確認**：
               - `requirements.txt` のインストール状況を確認
               - Python環境のバージョンを確認
            
            3. **ファイル修正の確認**：
               - quality_metrics_integration.py のインポート方法を確認
               - quality_metrics_improvements.py の初期化メソッドを確認
            """)
        
        # システム情報を表示
        with st.expander("システム情報", expanded=False):
            st.write(f"Python バージョン: {sys.version}")
            st.write(f"実行パス: {sys.executable}")
            st.write(f"作業ディレクトリ: {os.getcwd()}")
            st.write(f"PYTHONPATH: {sys.path}")
    elif page == 'プロジェクト管理':
        render_project_management()
    elif page == 'セッション管理':
        try:
            render_session_management()
        except NameError:
            st.error("セッション管理モジュールが読み込めませんでした。開発中の機能です。")
            st.info("プロジェクト管理からセッションにアクセスすることができます。")
    elif page == 'データ検証':
        render_data_validation()
    elif page == 'マップビュー':
        st.info("マップビュー機能は開発中です。")
        # マップの例を表示
        m = folium.Map(location=[35.45, 139.65], zoom_start=12)
        folium_static(m, width=800, height=600)
    elif page == 'データ管理':
        st.info("データ管理機能は開発中です。")
    elif page == 'パフォーマンス分析':
        st.info("パフォーマンス分析機能は開発中です。")
    elif page == 'ヘルプ':
        st.header("ヘルプとドキュメント")
        st.markdown("""
        ## セーリング戦略分析システムへようこそ
        
        このアプリケーションは、セーリング競技のデータ分析と戦略評価を支援するツールです。
        
        ### 主な機能
        
        1. **プロジェクト管理**: セーリングセッションをプロジェクトとしてグループ化
        2. **データインポート**: GPSデータをインポートして分析
        3. **データ検証**: インポートされたデータの問題を検出して修正
        4. **風の推定**: GPSデータから風向と風速を推定
        5. **戦略分析**: 戦略的判断ポイントを検出して評価
        
        ### 使い方のガイド
        
        詳細なドキュメントは`/docs/user_guide.md`を参照してください。
        """)
        
        # ヘルプページにバージョン情報とリリースノートを追加
        st.subheader("バージョン情報")
        st.info("セーリング戦略分析システム v1.0.0 (2023年4月)")
        
        with st.expander("リリースノート"):
            st.markdown("""
            ### v1.0.0 (2023年4月9日)
            
            - 初期リリース
            - 基本的なプロジェクト管理機能
            - データインポートとバリデーション
            - 風推定の基本機能
            - 基本的な可視化機能
            """)
except Exception as e:
    st.error(f"ページの表示中にエラーが発生しました: {e}")
    logger.error(f"ページレンダリングエラー: {e}")
    logger.error(traceback.format_exc())

# フッター
st.sidebar.markdown('---')
st.sidebar.info('セーリング戦略分析システム v1.0.0')

# フィードバックセクション
with st.sidebar.expander("フィードバック"):
    st.write("アプリケーションの改善にご協力ください。")
    feedback_type = st.selectbox("フィードバックの種類", 
                                ["選択してください", "バグ報告", "機能リクエスト", "その他"])
    feedback_text = st.text_area("フィードバック内容")
    if st.button("送信", key="feedback_submit"):
        if feedback_type == "選択してください":
            st.error("フィードバックの種類を選択してください。")
        elif not feedback_text:
            st.error("フィードバック内容を入力してください。")
        else:
            # フィードバックの保存処理（本番環境では実装必要）
            logger.info(f"フィードバック受信: {feedback_type} - {feedback_text[:50]}...")
            st.success("フィードバックを受け付けました。ありがとうございます！")

# デバッグモード（開発中のみ）
if os.environ.get('STREAMLIT_DEBUG', '').lower() == 'true':
    with st.sidebar.expander("デバッグ情報", expanded=False):
        st.write(f"システム情報: {sys.version}")
        st.write(f"ページ: {page}")
        if st.button("キャッシュクリア"):
            st.experimental_rerun()
