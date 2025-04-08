"""
ui.demo_batch_export

バッチエクスポート機能のデモアプリケーション
"""

import streamlit as st
import os
import time
import datetime
import uuid
import sys
import pandas as pd
import json

# モジュールのインポートパスを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sailing_data_processor.exporters.export_job import ExportJob
from sailing_data_processor.exporters.batch_exporter import BatchExporter
from sailing_data_processor.exporters.csv_exporter import CSVExporter
from sailing_data_processor.exporters.json_exporter import JSONExporter
from sailing_data_processor.exporters.exporter_factory import ExporterFactory
from sailing_data_processor.exporters.template_manager import TemplateManager

from ui.components.export.batch_export_panel import BatchExportPanel
from ui.components.export.csv_preview import CSVPreviewComponent
from ui.components.export.json_preview import JSONPreviewComponent
from ui.components.export.export_result_panel import ExportResultPanel

# ダミーセッションモデルクラス
class DummySessionModel:
    def __init__(self, session_id, name, description="", category="", tags=None, status="active"):
        self.session_id = session_id
        self.name = name
        self.description = description
        self.category = category
        self.tags = tags or []
        self.status = status
        self.purpose = ""
        self.event_date = datetime.datetime.now().isoformat()
        self.location = ""
        self.importance = 1
        self.rating = 3
        self.created_at = datetime.datetime.now().isoformat()
        self.updated_at = datetime.datetime.now().isoformat()
        self.metadata = {
            "boat_type": "470",
            "wind_strength": "medium",
            "race_type": "training",
        }
        self.results = []
        self.completion_percentage = 100

# ダミーエクスポーターファクトリ
class DummyExporterFactory:
    def __init__(self):
        self.exporters = {
            "csv": CSVExporter(),
            "json": JSONExporter()
        }
        
    def get_exporter(self, exporter_id):
        return self.exporters.get(exporter_id)
        
    def get_supported_formats(self):
        return {
            "csv": "CSV (カンマ区切りテキスト)",
            "json": "JSON (JavaScriptオブジェクト表記)"
        }

# ダミーバッチエクスポーター
class DummyBatchExporter(BatchExporter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    # 擬似的なエクスポート処理
    def _export_single_session(self, exporter, session, output_path, 
                             template_name, options, progress_callback):
        """オーバーライドしたエクスポート処理（実際にはダミーデータを生成）"""
        # 実際にはファイルを作成しない擬似エクスポート
        time.sleep(0.5)  # エクスポートに時間がかかる様子をシミュレート
        
        # エクスポートの種類によって異なる処理
        if hasattr(exporter, 'file_extension'):
            ext = exporter.file_extension
        else:
            ext = "txt"
            
        # 出力ディレクトリがなければ作成
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # ダミーデータを出力
        if ext == "csv":
            # CSVダミーデータ
            df = pd.DataFrame({
                "timestamp": pd.date_range(start="2025-01-01", periods=10, freq="1H"),
                "latitude": [35.123456 + i * 0.001 for i in range(10)],
                "longitude": [139.123456 + i * 0.001 for i in range(10)],
                "speed": [10 + i * 0.5 for i in range(10)],
                "course": [45 + i for i in range(10)]
            })
            df.to_csv(output_path, index=False)
        elif ext == "json":
            # JSONダミーデータ
            data = {
                "session_id": session.session_id,
                "name": session.name,
                "metadata": session.metadata,
                "data_points": [
                    {
                        "timestamp": (datetime.datetime.now() + datetime.timedelta(minutes=i)).isoformat(),
                        "latitude": 35.123456 + i * 0.001,
                        "longitude": 139.123456 + i * 0.001,
                        "speed": 10 + i * 0.5,
                        "course": 45 + i
                    } for i in range(10)
                ]
            }
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        else:
            # その他のフォーマット
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(f"Session: {session.name}\nExported at: {datetime.datetime.now().isoformat()}")
        
        # 進捗コールバック
        if progress_callback:
            progress_callback(1.0, f"{session.name} のエクスポートが完了しました")
        
        return output_path

def main():
    st.set_page_config(
        page_title="バッチエクスポートデモ",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("バッチエクスポート機能 デモ")
    
    st.markdown("""
    このデモでは、複数のセッションを一括でエクスポートする機能を試すことができます。
    左側のサイドバーから機能を選択してください。
    """)
    
    # サイドバーでのナビゲーション
    nav_selection = st.sidebar.radio(
        "機能選択",
        ["バッチエクスポートウィザード", "CSVプレビュー", "JSONプレビュー", "エクスポート結果"]
    )
    
    # ダミーセッションデータの生成
    if "dummy_sessions" not in st.session_state:
        st.session_state.dummy_sessions = []
        categories = ["レース", "練習", "アナリティクス", "その他"]
        tags = ["風強", "風弱", "北風", "東風", "南風", "西風", "晴れ", "雨", "波あり", "波なし"]
        
        for i in range(20):
            session_id = str(uuid.uuid4())
            category = categories[i % len(categories)]
            name = f"セッション {i+1:02d} - {category}"
            description = f"{category}のサンプルセッション #{i+1}"
            
            # タグの割り当て（ランダム）
            session_tags = []
            for j, tag in enumerate(tags):
                if (i + j) % 3 == 0:  # 適当な条件でタグを付与
                    session_tags.append(tag)
            
            status = "完了" if i % 4 != 0 else "進行中" if i % 4 == 0 else "未開始"
            
            # セッションオブジェクトの作成
            session = DummySessionModel(
                session_id=session_id,
                name=name,
                description=description,
                category=category,
                tags=session_tags,
                status=status
            )
            st.session_state.dummy_sessions.append(session)
    
    # エクスポーターとバッチエクスポーターの初期化
    factory = DummyExporterFactory()
    batch_exporter = DummyBatchExporter(factory)
    
    # 選択した機能を表示
    if nav_selection == "バッチエクスポートウィザード":
        st.header("バッチエクスポートウィザード")
        
        # バッチエクスポートパネルの表示
        batch_panel = BatchExportPanel(
            key="demo_batch",
            export_manager=factory,
            batch_exporter=batch_exporter
        )
        batch_panel.render(st.session_state.dummy_sessions)
        
    elif nav_selection == "CSVプレビュー":
        st.header("CSVプレビュー")
        
        # サンプルCSVデータの作成
        if "csv_sample" not in st.session_state:
            df = pd.DataFrame({
                "日付": pd.date_range(start="2025-01-01", periods=50, freq="1D"),
                "セッション名": [f"セッション {i+1:02d}" for i in range(50)],
                "カテゴリ": [categories[i % len(categories)] for i in range(50)],
                "風速": [5 + (i % 15) for i in range(50)],
                "風向": [45 * (i % 8) for i in range(50)],
                "戦略スコア": [(i % 10) / 2 for i in range(50)],
                "完了率": [min(100, 50 + (i * 2)) for i in range(50)],
                "評価": [(i % 5) + 1 for i in range(50)]
            })
            st.session_state.csv_sample = df
        
        # CSVプレビューコンポーネントの表示
        csv_preview = CSVPreviewComponent(key="demo_csv_preview")
        
        # アップロードかサンプルデータの選択
        data_source = st.radio("データソース", ["サンプルデータ", "ファイルアップロード"], horizontal=True)
        
        if data_source == "サンプルデータ":
            csv_preview.load_data(st.session_state.csv_sample)
            csv_preview.render()
        else:
            uploaded_file = st.file_uploader("CSVファイルをアップロード", type="csv")
            if uploaded_file:
                try:
                    delimiter = st.selectbox("区切り文字", options=[",", ";", "\\t"], 
                                          format_func=lambda x: "カンマ (,)" if x == "," else "セミコロン (;)" if x == ";" else "タブ (\\t)")
                    encoding = st.selectbox("エンコーディング", options=["utf-8", "shift-jis", "euc-jp"])
                    
                    # CSVファイルを読み込み
                    csv_preview.load_data(uploaded_file, delimiter=delimiter, encoding=encoding)
                    csv_preview.render()
                except Exception as e:
                    st.error(f"CSVファイルの読み込みに失敗しました: {str(e)}")
            else:
                st.info("CSVファイルをアップロードしてください")
        
    elif nav_selection == "JSONプレビュー":
        st.header("JSONプレビュー")
        
        # サンプルJSONデータの作成
        if "json_sample" not in st.session_state:
            sample_data = {
                "metadata": {
                    "app_version": "1.0.0",
                    "export_date": datetime.datetime.now().isoformat(),
                    "user": "demo_user"
                },
                "sessions": [
                    {
                        "session_id": str(uuid.uuid4()),
                        "name": f"サンプルセッション {i+1}",
                        "category": categories[i % len(categories)],
                        "created_at": (datetime.datetime.now() - datetime.timedelta(days=10-i)).isoformat(),
                        "data_points": [
                            {
                                "timestamp": (datetime.datetime.now() - datetime.timedelta(days=10-i, minutes=j*10)).isoformat(),
                                "latitude": 35.123456 + j * 0.001,
                                "longitude": 139.123456 + j * 0.001,
                                "speed": 10 + j * 0.5,
                                "course": 45 + j * 10,
                                "wind_speed": 15 + (j % 5),
                                "wind_direction": 90 + (j * 15) % 360
                            }
                            for j in range(5)
                        ],
                        "analysis_results": {
                            "avg_speed": 12.5 + i * 0.3,
                            "max_speed": 15.0 + i * 0.5,
                            "distance": 5.2 + i * 0.2,
                            "tack_count": 12 + i,
                            "strategy_score": 85 + (i % 15)
                        }
                    }
                    for i in range(3)
                ]
            }
            st.session_state.json_sample = sample_data
        
        # JSONプレビューコンポーネントの表示
        json_preview = JSONPreviewComponent(key="demo_json_preview")
        
        # アップロードかサンプルデータの選択
        data_source = st.radio("データソース", ["サンプルデータ", "ファイルアップロード"], horizontal=True)
        
        if data_source == "サンプルデータ":
            json_preview.load_data(st.session_state.json_sample)
            json_preview.render()
        else:
            uploaded_file = st.file_uploader("JSONファイルをアップロード", type="json")
            if uploaded_file:
                try:
                    json_preview.load_data(uploaded_file)
                    json_preview.render()
                except Exception as e:
                    st.error(f"JSONファイルの読み込みに失敗しました: {str(e)}")
            else:
                st.info("JSONファイルをアップロードしてください")
        
    elif nav_selection == "エクスポート結果":
        st.header("エクスポート結果表示")
        
        # サンプル結果の生成
        if "result_samples" not in st.session_state:
            sample_results = []
            for i in range(15):
                success = i % 4 != 0  # 75%の確率で成功
                result = {
                    "session_id": f"session_{i}",
                    "session_name": f"サンプルセッション {i+1}",
                    "success": success,
                    "output_path": f"/path/to/exports/session_{i}.{'csv' if i % 2 == 0 else 'json'}" if success else "",
                    "error": "" if success else "エクスポート中にエラーが発生しました: ファイルの書き込み権限がありません" if i % 8 == 0 else "無効なデータ形式です" if i % 8 == 4 else "接続エラー",
                    "timestamp": (datetime.datetime.now() - datetime.timedelta(minutes=i*5)).isoformat()
                }
                sample_results.append(result)
            st.session_state.result_samples = sample_results
        
        # 結果パネルの表示
        result_panel = ExportResultPanel(key="demo_result")
        
        # 結果数の選択
        result_count = st.slider("結果数", min_value=1, max_value=len(st.session_state.result_samples), value=5)
        results = st.session_state.result_samples[:result_count]
        
        # 結果の設定と表示
        result_panel.set_results(results)
        result_panel.render()
    
if __name__ == "__main__":
    main()
