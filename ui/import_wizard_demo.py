"""
ui.import_wizard_demo

インポートウィザードのデモページ
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any
import os
import sys

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ui.components.forms.import_wizard import ImportWizard

# ページ設定
st.set_page_config(
    page_title="データインポートウィザード - セーリング戦略分析システム",
    page_icon="🚢",
    layout="wide",
)

# タイトル
st.title("データインポートウィザード")
st.write("GPS位置データをインポートするためのウィザード")


def on_import_complete(container):
    """インポート完了時のコールバック"""
    st.session_state["imported_data"] = container
    st.session_state["show_analysis"] = True


# インポートウィザードの利用
wizard = ImportWizard(
    key="main_import_wizard",
    on_import_complete=on_import_complete
)

# セッション状態の初期化
if "imported_data" not in st.session_state:
    st.session_state["imported_data"] = None
if "show_analysis" not in st.session_state:
    st.session_state["show_analysis"] = False

# タブによるレイアウト
tab1, tab2 = st.tabs(["インポートウィザード", "インポートしたデータ"])

with tab1:
    # インポートウィザードを表示
    wizard.render()

with tab2:
    if st.session_state["imported_data"] is not None:
        # インポートされたデータの詳細表示
        container = st.session_state["imported_data"]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.header("メタデータ")
            metadata = container.metadata
            for key, value in metadata.items():
                st.write(f"**{key}:** {value}")
        
        with col2:
            st.header("時間範囲")
            time_range = container.get_time_range()
            st.write(f"**開始時刻:** {time_range['start']}")
            st.write(f"**終了時刻:** {time_range['end']}")
            st.write(f"**期間:** {time_range['duration_seconds'] / 60:.1f} 分")
        
        st.header("データ")
        df = container.data
        st.write(f"データポイント数: {len(df)}")
        st.dataframe(df)
        
        # データの可視化
        st.header("位置データの可視化")
        
        # マップ表示
        st.subheader("位置データマップ")
        # データをマップ用にフォーマット
        map_data = df[["latitude", "longitude"]].copy()
        st.map(map_data)
        
        # 時系列グラフ
        if "speed" in df.columns:
            st.subheader("速度の時系列推移")
            chart_data = pd.DataFrame({
                "時刻": df["timestamp"],
                "速度": df["speed"]
            })
            st.line_chart(chart_data.set_index("時刻"))
    else:
        st.info("まだデータがインポートされていません。左のタブでデータをインポートしてください。")


# サイドバー
st.sidebar.header("インポートウィザードについて")
st.sidebar.write("""
このページでは、GPSデータをインポートするためのウィザードを試すことができます。

サポートするファイル形式:
- CSV (カンマ区切りテキスト)
- GPX (GPS Exchange Format)
- TCX (Training Center XML)
- FIT (Flexible and Interoperable Data Transfer)

ウィザードでは以下のステップでデータをインポートします:
1. ファイルのアップロード
2. ファイル形式の検出
3. 列マッピング（CSVの場合）
4. メタデータの入力
5. データのプレビュー
6. インポート完了
""")

st.sidebar.info("注意: FITファイルのインポートにはfitparseライブラリが必要です。")

# フッター
st.sidebar.markdown("---")
st.sidebar.write("セーリング戦略分析システム - データインポートウィザードデモ")
