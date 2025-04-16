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
import pathlib
from streamlit_folium import folium_static
import folium

# プロジェクトのルートディレクトリをパスに追加（pathlib使用でプラットフォーム互換性向上）
current_dir = pathlib.Path(__file__).parent
project_root = current_dir.parent.absolute()
sys.path.insert(0, str(project_root))

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

# エラー追跡用のグローバル変数（宣言のみ）
last_error_trace = None

# 先に依存モジュールが正しくロードされているか確認
try:
    # システムパスを出力（デバッグ用）
    logger.info(f"システムパス: {sys.path}")
    
    # 明示的にsailing_data_processorディレクトリをパスに追加（デプロイ環境対応）
    # project_rootはすでに設定済み（pathlib使用でプラットフォーム互換性向上）
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
        logger.info(f"プロジェクトルートをパスに追加: {project_root}")
    
    # 明示的に依存モジュールの存在をチェック
    import importlib.util
    
    # quality_metrics モジュールの存在確認（pathlib使用）
    qm_path = project_root / 'sailing_data_processor' / 'validation' / 'quality_metrics.py'
    logger.info(f"quality_metrics.py パス: {qm_path}")
    logger.info(f"ファイルは存在するか: {qm_path.exists()}")
    
    if qm_path.exists():
        content = qm_path.read_text(encoding='utf-8')[:50]
        logger.info(f"quality_metrics.py 先頭50文字: {content}")
    
    # モジュールをインポート
    try:
        # まず直接インポートを試す
        try:
            import sailing_data_processor.validation.quality_metrics_integration as quality_metrics_integration
            logger.info("Quality metrics integration モジュールのロードに成功")
            logger.info(f"モジュール内容: {dir(quality_metrics_integration)}")
        except ImportError as e1:
            logger.warning(f"標準的なインポートに失敗: {e1}")
            
            # 代替インポート方法を試す
            try:
                import importlib.util
                integration_path = project_root / 'sailing_data_processor' / 'validation' / 'quality_metrics_integration.py'
                spec = importlib.util.spec_from_file_location("quality_metrics_integration", str(integration_path))
                quality_metrics_integration = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(quality_metrics_integration)
                logger.info("代替方法でのQuality metrics integrationモジュールのロードに成功")
            except Exception as e2:
                logger.error(f"代替インポート方法でも失敗: {e2}")
                raise ImportError(f"両方のインポート方法に失敗: {e1}, {e2}")
    except Exception as e:
        logger.error(f"Quality metrics モジュールロードエラー: {e}")
        logger.error(traceback.format_exc())
        st.error(f"Quality metrics モジュールのロードに失敗: {e}")
    
    # MetricsCalculator のインポート問題を診断
    try:
        # 直接インポートしてみる
        try:
            from sailing_data_processor.validation.quality_metrics import QualityMetricsCalculator
            logger.info("QualityMetricsCalculator クラスのロードに成功")
            logger.info(f"QualityMetricsCalculator クラスの内容: {dir(QualityMetricsCalculator)}")
            logger.info(f"クラスタイプ: {type(QualityMetricsCalculator)}")
        except ImportError as e1:
            logger.warning(f"標準的なQualityMetricsCalculatorインポートに失敗: {e1}")
            
            # 代替インポート方法を試す
            try:
                import importlib.util
                metrics_path = project_root / 'sailing_data_processor' / 'validation' / 'quality_metrics.py'
                spec = importlib.util.spec_from_file_location("quality_metrics", str(metrics_path))
                quality_metrics = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(quality_metrics)
                
                QualityMetricsCalculator = quality_metrics.QualityMetricsCalculator
                logger.info("代替方法でのQualityMetricsCalculatorクラスのロードに成功")
            except Exception as e2:
                logger.error(f"代替インポート方法でも失敗: {e2}")
                raise ImportError(f"両方のインポート方法に失敗: {e1}, {e2}")
    except Exception as e:
        logger.error(f"QualityMetricsCalculator ロードエラー: {e}")
        logger.error(traceback.format_exc())
        st.warning(f"QualityMetricsCalculator クラスのロードに失敗しました: {e}")
    
    # 各モジュールの存在を確認（pathlib使用）
    required_files = [
        project_root / 'sailing_data_processor' / 'validation' / 'quality_metrics.py',
        project_root / 'sailing_data_processor' / 'validation' / 'quality_metrics_improvements.py',
        project_root / 'sailing_data_processor' / 'validation' / 'quality_metrics_integration.py',
        project_root / 'ui' / 'pages' / 'basic_project_management.py'
    ]
    
    for file_path in required_files:
        relative_path = file_path.relative_to(project_root)
        if file_path.exists():
            logger.info(f"ファイル存在確認: {relative_path} ✓")
        else:
            logger.error(f"ファイル存在確認: {relative_path} ✗ (見つかりません)")
except Exception as diag_error:
    logger.error(f"依存モジュール診断エラー: {diag_error}")
    logger.error(traceback.format_exc())

# UI ページのインポート
try:
    # インポート順序を変更して問題を回避
    logger.info("UIページのインポートを開始...")
    
    # パス情報を記録（デバッグ用、pathlib使用）
    pages_dir = current_dir / 'pages'
    basic_pm_path = pages_dir / 'basic_project_management.py'
    logger.info(f"UI pages パス: {pages_dir}")
    logger.info(f"基本プロジェクト管理ファイルパス: {basic_pm_path}")
    logger.info(f"ファイルは存在するか: {basic_pm_path.exists()}")
    
    # スタックトレースを取得するためのヘルパー関数
    def import_with_detailed_error(module_path, module_name):
        global last_error_trace  # 最初にグローバル変数宣言
        try:
            logger.info(f"{module_name}のインポートを試みます...")
            module = __import__(module_path, fromlist=[''])
            logger.info(f"{module_name}のインポートに成功しました。")
            return module
        except Exception as e:
            error_msg = f"{module_name}のインポートに失敗: {e}"
            error_trace = traceback.format_exc()
            # グローバル変数に保存
            last_error_trace = error_trace
            # 関数内でログ記録する
            logger.error(error_msg)
            logger.error(error_trace)
            st.error(error_msg)
            return None
    
    # デバッグ用に直接インポートも試行
    try:
        # 直接インポートを試す（モジュール検索パスとのトラブルシューティング用）
        import importlib.util
        sys.path.append(str(current_dir / 'pages'))
        logger.info(f"pages直接アクセス用にパスを追加: {current_dir / 'pages'}")
        
        # モジュールファイルの存在を確認してからインポート
        page_files = {
            "basic_project_management": str(current_dir / 'pages' / 'basic_project_management.py'),
            "data_validation": str(current_dir / 'pages' / 'data_validation.py'),
            "session_management": str(current_dir / 'pages' / 'session_management.py')
        }
        
        # ファイルの存在確認
        for name, path in page_files.items():
            if os.path.exists(path):
                logger.info(f"ファイル {name} が見つかりました: {path}")
            else:
                logger.error(f"ファイル {name} が見つかりません: {path}")
    except Exception as direct_import_error:
        logger.warning(f"直接インポート確認中のエラー: {direct_import_error}")

    # 段階的にモジュールをインポート - より堅牢なアプローチ
    basic_project_management = import_with_detailed_error('ui.pages.basic_project_management', '基本プロジェクト管理')
    data_validation = import_with_detailed_error('ui.pages.data_validation', 'データ検証')
    session_management = import_with_detailed_error('ui.pages.session_management', 'セッション管理')
    
    # インポートが成功したかチェック
    UI_MODULES_LOADED = False
    module_import_errors = {}
    
    # 各モジュールが存在するかと必要な属性を持っているか確認
    if basic_project_management:
        try:
            render_project_management = basic_project_management.render_page
            logger.info("プロジェクト管理の render_page 関数が正常にロードされました。")
        except AttributeError as e:
            module_import_errors["basic_project_management"] = f"render_page属性がありません: {e}"
            logger.error(f"プロジェクト管理の render_page 属性エラー: {e}")
    else:
        module_import_errors["basic_project_management"] = "モジュールのロードに失敗しました"
    
    if data_validation:
        try:
            render_data_validation = data_validation.render_page
            logger.info("データ検証の render_page 関数が正常にロードされました。")
        except AttributeError as e:
            module_import_errors["data_validation"] = f"render_page属性がありません: {e}"
            logger.error(f"データ検証の render_page 属性エラー: {e}")
    else:
        module_import_errors["data_validation"] = "モジュールのロードに失敗しました"
    
    # セッション管理の処理 - render_page関数が標準化されたことを前提
    if session_management:
        try:
            # セッション管理モジュールには標準でrender_page関数が実装されているはず
            if hasattr(session_management, 'render_page'):
                render_session_management = session_management.render_page
                logger.info("セッション管理の render_page 関数が正常にロードされました。")
            else:
                # 念のためfallback - 旧バージョンの互換性のため
                logger.warning("セッション管理にrender_page関数が見つかりません。互換性モードを試行します。")
                if hasattr(session_management, 'session_management_page'):
                    logger.info("代替方法：session_management_pageを直接使用します")
                    render_session_management = session_management.session_management_page
                else:
                    raise AttributeError("必要な関数が見つかりません")
        except AttributeError as e:
            module_import_errors["session_management"] = f"必要な属性がありません: {e}"
            logger.error(f"セッション管理の 属性エラー: {e}")
            # モジュールの内容を詳細にロギング
            logger.info(f"セッション管理モジュールの内容: {dir(session_management)}")
    else:
        module_import_errors["session_management"] = "モジュールのロードに失敗しました"
    
    # すべてのモジュールが正常にロードされたかチェック
    if not module_import_errors:
        logger.info("すべてのUI モジュールの読み込みに成功しました。")
        UI_MODULES_LOADED = True
    else:
        # エラーが発生したが、ロードできたモジュールがあればそれを使う
        logger.error(f"一部モジュールのロードに問題がありました: {module_import_errors}")
        
        # ダミー関数を定義（未定義のrender_*関数を置き換え）
        def create_dummy_render(module_name, error_detail):
            def dummy():
                st.error(f"{module_name}モジュールの読み込みに失敗しました。")
                st.info(f"エラー詳細: {error_detail}")
            return dummy
        
        # エラーが発生したモジュールにダミー関数を設定
        if "basic_project_management" in module_import_errors:
            render_project_management = create_dummy_render("プロジェクト管理", module_import_errors["basic_project_management"])
        
        if "data_validation" in module_import_errors:
            render_data_validation = create_dummy_render("データ検証", module_import_errors["data_validation"])
        
        if "session_management" in module_import_errors:
            render_session_management = create_dummy_render("セッション管理", module_import_errors["session_management"])
        
        # 一部でもモジュールがロードできていれば部分的に動作させる
        if basic_project_management or data_validation or session_management:
            UI_MODULES_LOADED = True
            logger.info("一部のモジュールがロードされています。部分的な機能で動作します。")
        else:
            UI_MODULES_LOADED = False
            logger.error("すべてのモジュールのロードに失敗しました。")
        
except Exception as e:
    # エラートレースをグローバル変数に保存
    error_trace = traceback.format_exc()
    # グローバル変数への代入
    last_error_trace = error_trace
    logger.error(f"モジュールの読み込みに失敗しました: {e}")
    logger.error(error_trace)
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

# ページ設定の確認（既に設定されている場合はスキップ）
try:
    # ページ設定を試みる（既に設定されていると例外が発生する）
    st.set_page_config(
        page_title="セーリング戦略分析システム",
        page_icon="🌊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
except Exception as e:
    # 既にページ設定されているなど、エラーは無視する
    logger.info(f"ページ設定スキップ: {e}")

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
            if 'last_error_trace' in globals():
                st.code(last_error_trace)
            else:
                st.code(traceback.format_exc())
            
            # ファイルの存在確認結果を表示（pathlib使用でクロスプラットフォーム互換性向上）
            st.subheader("モジュールパス確認")
            pages_dir = current_dir / 'pages'
            files_to_check = [
                'basic_project_management.py',
                'data_validation.py',
                'session_management.py'
            ]
            
            st.write(f"UIページディレクトリ: {pages_dir}")
            st.write("ファイル存在確認:")
            
            for file in files_to_check:
                file_path = pages_dir / file
                exists = file_path.exists()
                status = "✅ 存在します" if exists else "❌ 見つかりません"
                st.write(f" - {file}: {status}")
                
            # プロジェクトマネージャーのインポートを試みる
            try:
                from ui.components.project.project_manager import initialize_project_manager
                st.success("プロジェクトマネージャーコンポーネントのインポートに成功しました")
            except Exception as e:
                st.error(f"プロジェクトマネージャーコンポーネントのインポートに失敗: {e}")
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