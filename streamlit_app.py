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
sys.path.insert(0, str(current_dir / 'ui' / 'pages'))  # pagesディレクトリを明示的に追加

# 依存パッケージのバージョン確認（デプロイ環境のデバッグ用）
try:
    import streamlit
    import pandas
    import numpy
    import folium
    logging.info(f"Streamlit version: {streamlit.__version__}")
    logging.info(f"Pandas version: {pandas.__version__}")
    logging.info(f"NumPy version: {numpy.__version__}")
    logging.info(f"Folium version: {folium.__version__}")
except ImportError as e:
    logging.error(f"依存パッケージの確認中にエラー: {e}")

# 環境変数を設定してクラウド環境を識別
os.environ['SAILING_ANALYZER_ENV'] = os.environ.get('STREAMLIT_SERVER_HEADLESS', 'false')

# ロギングの設定（環境に応じて適切なハンドラを使用）
is_cloud = os.environ.get('SAILING_ANALYZER_ENV') == 'true'

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

# ページ設定（app_v5.pyとの重複を避けるためここで一度だけ設定）
st.set_page_config(
    page_title="セーリング戦略分析システム",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# デバッグモードを有効化
os.environ['STREAMLIT_DEBUG'] = 'true'

# ディレクトリの存在確認（pathlib使用でプラットフォーム互換性向上）
ui_dir = current_dir / 'ui'
ui_pages_dir = ui_dir / 'pages'
ui_components_dir = ui_dir / 'components'
validation_dir = current_dir / 'sailing_data_processor' / 'validation'

# ディレクトリ構造の確認
st.header("ディレクトリ構造の確認")
st.write(f"ui ディレクトリ: {ui_dir.exists()}")
st.write(f"ui/pages ディレクトリ: {ui_pages_dir.exists()}")
st.write(f"ui/components ディレクトリ: {ui_components_dir.exists()}")
st.write(f"sailing_data_processor/validation ディレクトリ: {validation_dir.exists()}")

# ui/pages ディレクトリの内容を確認
if ui_pages_dir.exists():
    pages_files = list(ui_pages_dir.glob("*.py"))  # Pythonファイルのみリスト
    st.write("pages ディレクトリの内容:")
    for file in pages_files:
        st.write(f"- {file.name}")  # ファイル名のみ表示
else:
    st.error(f"ui/pages ディレクトリが見つかりません: {ui_pages_dir}")

# 必須モジュールファイルの存在確認（pathlib使用）
required_files = [
    current_dir / 'sailing_data_processor' / 'validation' / 'quality_metrics.py',
    current_dir / 'sailing_data_processor' / 'validation' / 'quality_metrics_improvements.py',
    current_dir / 'sailing_data_processor' / 'validation' / 'quality_metrics_integration.py',
    current_dir / 'ui' / 'pages' / 'basic_project_management.py'
]

missing_files = []
for file_path in required_files:
    if not file_path.exists():
        # Pathlibオブジェクトを相対パスの文字列に変換して表示
        relative_path = file_path.relative_to(current_dir)
        missing_files.append(str(relative_path))

if missing_files:
    st.error("必須ファイルが見つかりません。")
    st.write("見つからないファイル:")
    for file in missing_files:
        st.write(f"- {file}")
    st.info("モジュール構造を修正してください。")
    st.stop()

# モジュールインポートのヘルパー関数
def try_import_with_feedback(import_statement, name, fallback=None):
    """
    モジュールのインポートを試し、成功・失敗を表示する
    失敗時にはフォールバックを返す
    """
    try:
        exec(import_statement)
        module_name = import_statement.split()[1].split(' as ')[0]
        globals()[module_name] = eval(module_name)
        st.success(f"{name}モジュールが正常にインポートされました。")
        return True
    except ImportError as e:
        st.error(f"{name}モジュールのインポートに失敗しました: {e}")
        if fallback:
            try:
                exec(fallback)
                module_name = fallback.split()[1].split(' as ')[0]
                globals()[module_name] = eval(module_name)
                st.warning(f"{name}モジュールの代替インポートが成功しました。")
                return True
            except Exception as e2:
                st.error(f"{name}の代替インポートも失敗しました: {e2}")
        return False
    except Exception as e:
        st.error(f"{name}のインポート中に予期せぬエラーが発生しました: {e}")
        return False

# メインアプリケーションのインポートと実行
try:
    # パッケージ構造チェック
    st.subheader("パッケージ構造の診断")
    # モジュールが存在するかの簡易テスト
    module_checks = [
        ("import sailing_data_processor.validation", "sailing_data_processor.validation"),
        ("from sailing_data_processor.validation.quality_metrics import QualityMetricsCalculator", "QualityMetricsCalculator"),
        # ProjectManagerのget_all_sessionsメソッドが存在するか確認を追加
        ("from sailing_data_processor.project.project_manager import ProjectManager", "ProjectManager")
    ]
    
    all_imports_ok = True
    for import_stmt, module_name in module_checks:
        if not try_import_with_feedback(import_stmt, module_name):
            all_imports_ok = False
    
    if not all_imports_ok:
        st.warning("⚠️ 一部のモジュールのインポートに問題がありますが、続行を試みます。")
    else:
        st.success("✅ すべての必須モジュールのインポートに成功しました。")
    
    # メインアプリケーションをロードする前に状態を表示
    st.info("メインアプリケーションを読み込んでいます...")
    
    # app_v5.pyファイルの存在確認（pathlib使用）
    app_v5_path = ui_path / 'app_v5.py'
    if app_v5_path.exists():
        st.success(f"app_v5.py ファイルが見つかりました")
        # ファイルの先頭部分を表示して確認（pathlib使用）
        content = app_v5_path.read_text(encoding='utf-8')[:500]  # 先頭500文字だけを読み込む
        st.write("app_v5.py の先頭部分")
        st.code(content, language="python")
    else:
        st.error(f"app_v5.py ファイルが見つかりません: {app_v5_path}")
        st.stop()
    
    # インポート前の設定確認
    st.write("インポート前の設定確認:")
    st.write(f"ui ディレクトリパス: {ui_path}")
    st.write(f"sys.path 内の ui 関連パス: {[p for p in sys.path if 'ui' in p]}")
    
    # app_v5モジュールのインポートをより詳細に
    logger.info("ui.app_v5 モジュールのインポートを試行中...")
    try:
        # importlib.util で詳細な情報を得ながらインポート
        import importlib.util
        
        # モジュールの仕様を取得
        spec = importlib.util.find_spec("ui.app_v5")
        if spec is None:
            raise ImportError("モジュール仕様が取得できませんでした")
        
        # モジュールをロード
        module = importlib.util.module_from_spec(spec)
        
        # グローバル名前空間にモジュールを追加
        import sys
        sys.modules["ui.app_v5"] = module
        
        try:
            spec.loader.exec_module(module)
            # 通常のimportでも参照できるようにする
            import ui.app_v5
        except SyntaxError as e:
            st.error(f"ui.app_v5に構文エラーがあります: {e}")
            st.code(traceback.format_exc())
            
            # エラー位置のコードを表示（pathlib使用）
            lineno = e.lineno
            if lineno:
                # 全体のコンテンツを読み込む
                lines = app_v5_path.read_text(encoding='utf-8').splitlines(True)
                start_line = max(0, lineno - 5)
                end_line = min(len(lines), lineno + 5)
                # 該当部分のみ抽出
                context = ''.join(lines[start_line:end_line])
                st.subheader(f"エラー箇所周辺のコード (行 {start_line+1} - {end_line}):")
                st.code(context, language="python")
            raise
        
        logger.info("app_v5 モジュールのインポートに成功")
        st.success("app_v5 モジュールのインポートに成功しました")
        
        # モジュールの内容を確認
        st.write("UIモジュール内容確認")
        # 直接moduleを参照する（ui.app_v5ではなく）
        logger.info(f"app_v5 モジュールの内容: {dir(module)}")
    except Exception as app_import_error:
        logger.error(f"app_v5 モジュールのインポート中にエラー: {app_import_error}")
        logger.error(traceback.format_exc())
        st.error(f"app_v5 モジュールのインポート中にエラーが発生しました: {app_import_error}")
        st.code(traceback.format_exc())
        
except Exception as e:
    st.error(f"アプリケーションの読み込み中にエラーが発生しました: {e}")
    st.code(traceback.format_exc())
    
    # 詳細なシステム情報を表示（デバッグ用）
    st.subheader("システム情報")
    st.write(f"Python バージョン: {sys.version}")
    st.write(f"実行パス: {sys.executable}")
    st.write(f"作業ディレクトリ: {os.getcwd()}")
    st.write(f"ファイル一覧:")
    # 最大深度2までのファイル一覧を表示（pathlib使用で改善）
    base_path = pathlib.Path('.')
    st.write("最上位ディレクトリ:")
    for file_path in base_path.glob('*'):
        if file_path.is_file():
            st.write(f"- {file_path}")
    
    # 1段階下のサブディレクトリ内のファイルも表示
    for dir_path in [p for p in base_path.glob('*') if p.is_dir()]:
        st.write(f"ディレクトリ {dir_path}:")
        for file_path in dir_path.glob('*'):
            if file_path.is_file():
                st.write(f"- {file_path}")
    
    # モジュールのインポートパスを表示
    st.write(f"Pythonパス: {sys.path}")
    st.info("開発者向け情報: このファイルはStreamlit Cloudデプロイ用のエントリーポイントです。")
