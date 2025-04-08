"""
ui.enhanced_import_demo

拡張インポートウィザードのデモアプリケーション
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import os
import sys

# プロジェクトのルートディレクトリをパスに追加
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

# 拡張インポートウィザードをインポート
from ui.components.forms.import_wizard.enhanced_wizard import EnhancedImportWizard

# ページ設定
st.set_page_config(
    page_title="拡張データインポートウィザード - セーリング戦略分析システム",
    page_icon="🚢",
    layout="wide",
)

# タイトル
st.title("拡張データインポートウィザード")
st.write("""
このデモアプリケーションでは、セーリング戦略分析システムの拡張インポート機能を試すことができます。
様々なGPSデータ形式（CSV, GPX, TCX, FIT）のインポートに対応しています。
""")

# セッション状態の初期化
if "imported_data" not in st.session_state:
    st.session_state["imported_data"] = None


def on_import_complete(container):
    """インポート完了時のコールバック"""
    st.session_state["imported_data"] = container
    st.success("データが正常にインポートされました！")


# タブによるレイアウト
tab1, tab2 = st.tabs(["データインポート", "インポートされたデータ"])

with tab1:
    # インポートウィザードを表示
    wizard = EnhancedImportWizard(
        key="demo_import_wizard",
        on_import_complete=on_import_complete
    )
    wizard.render()

with tab2:
    if st.session_state["imported_data"] is not None:
        # インポートされたデータの詳細表示
        container = st.session_state["imported_data"]
        
        # データ概要
        st.header("データ概要")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("#### 基本情報")
            st.write(f"**データポイント数:** {len(container.data)}")
            
            # 時間範囲
            time_range = container.get_time_range()
            st.write(f"**開始時刻:** {time_range['start']}")
            st.write(f"**終了時刻:** {time_range['end']}")
            st.write(f"**期間:** {time_range['duration_seconds'] / 60:.1f} 分")
        
        with col2:
            st.write("#### メタデータ")
            # メタデータを表示（一時的なキーを除外）
            filtered_metadata = {k: v for k, v in container.metadata.items() 
                               if k not in ["created_at", "updated_at", "time_range"]}
            
            for key, value in list(filtered_metadata.items())[:8]:  # 最初の8項目のみ表示
                st.write(f"**{key}:** {value}")
            
            if len(filtered_metadata) > 8:
                with st.expander("すべてのメタデータを表示"):
                    for key, value in filtered_metadata.items():
                        st.write(f"**{key}:** {value}")
        
        # データテーブル
        st.header("データテーブル")
        df = container.data
        
        # 表示するデータ量の選択
        num_rows = st.slider("表示する行数", min_value=5, max_value=100, value=10)
        display_all_cols = st.checkbox("すべての列を表示", value=False)
        
        if display_all_cols:
            st.dataframe(df.head(num_rows), use_container_width=True)
        else:
            # 主要列のみ表示
            main_cols = ['timestamp', 'latitude', 'longitude']
            # 他に存在する列を追加
            optional_cols = ['speed', 'course', 'elevation', 'heart_rate', 'cadence', 'power']
            display_cols = main_cols + [col for col in optional_cols if col in df.columns]
            
            st.dataframe(df[display_cols].head(num_rows), use_container_width=True)
            
            with st.expander("利用可能な列"):
                st.write(f"このデータセットには以下の列があります: {', '.join(df.columns)}")
        
        # データ可視化
        st.header("データ可視化")
        
        # 位置データを地図上に表示
        st.subheader("位置データマップ")
        map_data = df[["latitude", "longitude"]].copy()
        st.map(map_data)
        
        # 時系列データの表示
        st.subheader("時系列データ")
        # 表示する時系列データの選択
        time_series_cols = [col for col in df.columns 
                            if col not in ['timestamp', 'latitude', 'longitude'] 
                            and pd.api.types.is_numeric_dtype(df[col])]
        
        if time_series_cols:
            selected_col = st.selectbox("表示するデータを選択", time_series_cols)
            
            chart_data = pd.DataFrame({
                "時刻": df["timestamp"],
                selected_col: df[selected_col]
            })
            
            st.line_chart(chart_data.set_index("時刻"))
        else:
            st.info("時系列で表示できる数値データがありません。")
    else:
        st.info("まだデータがインポートされていません。「データインポート」タブでデータをインポートしてください。")


# サイドバー
st.sidebar.header("使い方ガイド")
st.sidebar.write("""
### 拡張インポートウィザードの使い方

1. **ファイルのアップロード**: GPSデータファイルをアップロードします
2. **形式検出**: ファイル形式が自動検出され、必要に応じて変更できます
3. **インポート設定**: 形式に応じた詳細設定を行います
4. **列マッピング**: CSVファイルの場合、列の対応付けを行います
5. **メタデータ**: データに関する追加情報を入力します
6. **プレビュー**: インポート前にデータを確認します
7. **インポート完了**: インポート処理が完了します

### サポートされるファイル形式

- **CSV**: カンマ区切りテキスト（またはその他の区切り文字）
- **GPX**: GPS Exchange Format (XML形式)
- **TCX**: Training Center XML (Garmin形式)
- **FIT**: Flexible and Interoperable Data Transfer (バイナリ形式)
""")

st.sidebar.write("---")
st.sidebar.write("セーリング戦略分析システム - 拡張インポートウィザードデモ")
