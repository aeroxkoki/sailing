# -*- coding: utf-8 -*-
"""
ui.demo_export

高度なエクスポート機能のデモアプリケーション
"""

import streamlit as st
import os
import sys
import datetime
import pandas as pd
import numpy as np
import uuid
import tempfile
from pathlib import Path
import random
import io

# ライブラリのパスを追加
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 必要なモジュールのインポート
try:
    from sailing_data_processor.reporting.exporters.base_exporter import BaseExporter
    from sailing_data_processor.reporting.exporters.pdf_exporter import PDFExporter
    from sailing_data_processor.reporting.exporters.html_exporter import HTMLExporter
    from sailing_data_processor.reporting.exporters.excel_exporter import ExcelExporter
    from sailing_data_processor.reporting.exporters.image_exporter import ImageExporter
    from sailing_data_processor.reporting.exporters.data_exporter import DataExporter
    
    EXPORTERS_AVAILABLE = True
except ImportError:
    EXPORTERS_AVAILABLE = False
    
try:
    from ui.components.reporting.export_panel import ExportPanel
    EXPORT_PANEL_AVAILABLE = True
except ImportError:
    EXPORT_PANEL_AVAILABLE = False

# ページ設定
st.set_page_config(
    page_title="高度なエクスポート機能デモ",
    page_icon="🚢",
    layout="wide"
)

# タイトル表示
st.title("高度なエクスポート機能デモ")

# デモデータの生成
@st.cache_data
def generate_demo_data():
    """デモ用のセーリングデータを生成"""
    # 時間範囲の設定
    start_time = datetime.datetime(2023, 6, 1, 10, 0, 0)
    end_time = start_time + datetime.timedelta(hours=2)
    timestamps = pd.date_range(start=start_time, end=end_time, freq='10s')
    
    # 基本データの作成
    data = pd.DataFrame({
        'timestamp': timestamps,
        'latitude': np.linspace(35.6000, 35.6300, len(timestamps)) + np.random.normal(0, 0.0003, len(timestamps)),
        'longitude': np.linspace(139.7600, 139.8000, len(timestamps)) + np.random.normal(0, 0.0003, len(timestamps)),
        'speed': np.random.uniform(4, 10, len(timestamps)),
        'heading': np.random.uniform(0, 360, len(timestamps)),
    })
    
    # 風向風速データの追加
    wind_direction_base = 270  # 西風をベースにする
    wind_variations = np.cumsum(np.random.normal(0, 2, len(timestamps)))  # 風向の変動
    data['wind_direction'] = (wind_direction_base + wind_variations) % 360
    data['wind_speed'] = np.random.uniform(10, 20, len(timestamps))  # 風速
    
    # 戦略ポイントの追加（約5分ごとに1つ）
    strategy_points = []
    for i in range(0, len(timestamps), 30):
        if random.random() < 0.2:  # 20%の確率で戦略ポイントとする
            strategy_points.append(i)
    
    data['strategy_point'] = False
    data.loc[strategy_points, 'strategy_point'] = True
    
    # 戦略ポイントの詳細を追加
    data['strategy_type'] = None
    data['strategy_description'] = None
    
    strategy_types = ['tack', 'gybe', 'mark_rounding', 'start', 'finish', 'layline']
    
    for idx in strategy_points:
        strategy_type = random.choice(strategy_types)
        data.loc[idx, 'strategy_type'] = strategy_type
        
        if strategy_type == 'tack':
            data.loc[idx, 'strategy_description'] = 'タックによる方向転換'
        elif strategy_type == 'gybe':
            data.loc[idx, 'strategy_description'] = 'ジャイブによる方向転換'
        elif strategy_type == 'mark_rounding':
            data.loc[idx, 'strategy_description'] = 'マークの回航'
        elif strategy_type == 'start':
            data.loc[idx, 'strategy_description'] = 'スタートライン通過'
        elif strategy_type == 'finish':
            data.loc[idx, 'strategy_description'] = 'フィニッシュライン通過'
        elif strategy_type == 'layline':
            data.loc[idx, 'strategy_description'] = 'レイラインへの接近'
    
    # メタデータの追加
    metadata = {
        'name': '東京湾トレーニングセッション',
        'date': '2023-06-01',
        'location': '東京湾',
        'boat_type': 'レーザー',
        'sailor_name': '山田太郎',
        'weather': '晴れ',
        'wind_condition': '中風（10-20ノット）',
        'water_temperature': 22.5,
        'air_temperature': 26.0,
        'course_type': '三角コース',
        'session_purpose': '風向変化への対応訓練',
        'coach': '鈴木コーチ',
        'notes': '風向が西からやや北寄りに変化。第2マーク回航後の風速増加に対応できず。',
    }
    
    # データと一緒にメタデータも渡す
    class SailingSessionData:
        def __init__(self, data, metadata):
            self.data = data
            self.metadata = metadata
    
    session_data = SailingSessionData(data, metadata)
    
    return session_data

# デモデータの生成
demo_data = generate_demo_data()

# サイドバー
with st.sidebar:
    st.subheader("セッション情報")
    
    # メタデータの表示
    for key, value in demo_data.metadata.items():
        if key in ['name', 'date', 'location', 'boat_type', 'sailor_name', 'weather', 'course_type']:
            st.write(f"**{key.capitalize()}:** {value}")
    
    # データの概要を表示
    st.subheader("データ概要")
    
    st.write(f"**データポイント数:** {len(demo_data.data)}")
    
    # 時間範囲表示
    time_range = demo_data.data['timestamp'].agg(['min', 'max'])
    start_time = time_range['min'].strftime("%Y-%m-%d %H:%M:%S")
    end_time = time_range['max'].strftime("%Y-%m-%d %H:%M:%S")
    duration = time_range['max'] - time_range['min']
    
    st.write(f"**時間範囲:** {start_time} ~ {end_time}")
    st.write(f"**所要時間:** {duration}")
    
    # 速度統計
    speed_stats = demo_data.data['speed'].agg(['mean', 'min', 'max'])
    st.write(f"**平均速度:** {speed_stats['mean']:.2f} ノット")
    st.write(f"**最大速度:** {speed_stats['max']:.2f} ノット")
    
    # 風統計
    wind_stats = demo_data.data['wind_speed'].agg(['mean', 'min', 'max'])
    st.write(f"**平均風速:** {wind_stats['mean']:.2f} ノット")
    st.write(f"**最大風速:** {wind_stats['max']:.2f} ノット")
    
    # 戦略ポイント数
    strategy_count = demo_data.data['strategy_point'].sum()
    st.write(f"**戦略ポイント数:** {int(strategy_count)}")

# メインコンテンツ
st.markdown("## データ可視化")

# データの可視化（簡易表示）
tab1, tab2, tab3 = st.tabs(["地図", "速度チャート", "風向風速"])

# 地図タブ
with tab1:
    try:
        # 地図の表示（簡易版）
        import folium
        from streamlit_folium import folium_static
        
        # 地図の中心を計算
        center_lat = demo_data.data['latitude'].mean()
        center_lon = demo_data.data['longitude'].mean()
        
        # 地図の作成
        m = folium.Map(location=[center_lat, center_lon], zoom_start=14)
        
        # トラックの追加
        track_coords = [[row['latitude'], row['longitude']] for _, row in demo_data.data.iterrows()]
        folium.PolyLine(track_coords, color="blue", weight=2.5, opacity=0.8).add_to(m)
        
        # 戦略ポイントの追加
        strategy_data = demo_data.data[demo_data.data['strategy_point'] == True]
        for _, row in strategy_data.iterrows():
            popup_text = f"""
            <b>タイプ:</b> {row['strategy_type']}<br>
            <b>説明:</b> {row['strategy_description']}<br>
            <b>時間:</b> {row['timestamp'].strftime('%H:%M:%S')}<br>
            <b>速度:</b> {row['speed']:.2f} ノット<br>
            <b>風向:</b> {row['wind_direction']:.1f}°<br>
            <b>風速:</b> {row['wind_speed']:.1f} ノット<br>
            """
            
            folium.Marker(
                [row['latitude'], row['longitude']],
                popup=folium.Popup(popup_text, max_width=300),
                icon=folium.Icon(color="red", icon="info-sign"),
            ).add_to(m)
        
        # 開始点と終了点のマーカー
        folium.Marker(
            [demo_data.data['latitude'].iloc[0], demo_data.data['longitude'].iloc[0]],
            popup="開始点",
            icon=folium.Icon(color="green"),
        ).add_to(m)
        
        folium.Marker(
            [demo_data.data['latitude'].iloc[-1], demo_data.data['longitude'].iloc[-1]],
            popup="終了点",
            icon=folium.Icon(color="red"),
        ).add_to(m)
        
        # 地図の表示
        folium_static(m)
        
    except Exception as e:
        st.error(f"地図の表示中にエラーが発生しました: {str(e)}")
        st.info("foliumとstreamlit_foliumをインストールすると地図が表示されます。")

# 速度チャートタブ
with tab2:
    # 速度と時間のグラフ
    st.subheader("速度の推移")
    
    chart_data = pd.DataFrame({
        "時間": demo_data.data['timestamp'],
        "速度 (ノット)": demo_data.data['speed']
    })
    
    st.line_chart(chart_data.set_index("時間"))

# 風向風速タブ
with tab3:
    # 風向風速の時系列表示
    st.subheader("風速の推移")
    
    wind_data = pd.DataFrame({
        "時間": demo_data.data['timestamp'],
        "風速 (ノット)": demo_data.data['wind_speed']
    })
    
    st.line_chart(wind_data.set_index("時間"))
    
    # 風向の変化
    st.subheader("風向の分布")
    
    # 風向データを30度ごとのビンに分割
    bins = list(range(0, 391, 30))
    labels = [f"{b}-{b+30}" for b in bins[:-1]]
    
    wind_dir_data = pd.cut(demo_data.data['wind_direction'], bins=bins, labels=labels, include_lowest=True)
    wind_dir_counts = wind_dir_data.value_counts().reset_index()
    wind_dir_counts.columns = ['風向', '頻度']
    
    st.bar_chart(wind_dir_counts.set_index('風向'))

# エクスポート機能
st.markdown("## 高度なエクスポート機能")

# エクスポート機能が使用可能か確認
if not EXPORTERS_AVAILABLE:
    st.warning("エクスポーターモジュールがインストールされていません。機能が制限されます。")

if not EXPORT_PANEL_AVAILABLE:
    st.warning("エクスポートパネルコンポーネントがインストールされていません。機能が制限されます。")

# エクスポートパネルの表示
if EXPORT_PANEL_AVAILABLE:
    # エクスポート完了時のコールバック
    def on_export_complete(path, format_type, options):
        st.session_state['last_export'] = {
            'path': path,
            'format': format_type,
            'options': options,
            'time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    # エクスポートパネルを表示
    export_panel = ExportPanel(key="demo_export", on_export=on_export_complete)
    export_settings = export_panel.render(data=demo_data)
    
    # 最近のエクスポート情報を表示
    if 'last_export' in st.session_state:
        last_export = st.session_state['last_export']
        with st.expander("最近のエクスポート"):
            st.write(f"**実行時間:** {last_export['time']}")
            st.write(f"**形式:** {last_export['format'].upper()}")
            st.write(f"**保存先:** {last_export['path']}")
else:
    # エクスポートパネルが利用できない場合、簡易エクスポート機能を表示
    st.info("カスタムエクスポートパネルが利用できないため、簡易機能を表示します。")
    
    # 簡易エクスポート設定UI
    export_format = st.selectbox(
        "エクスポート形式",
        options=["csv", "json", "excel"],
        format_func=lambda x: "CSV (カンマ区切りテキスト)" if x == "csv" else "JSON" if x == "json" else "Excel"
    )
    
    # 単純なエクスポートボタン
    if st.button("エクスポート", key="simple_export"):
        try:
            if export_format == "csv":
                # CSVダウンロード用のバッファを準備
                csv_buffer = io.StringIO()
                demo_data.data.to_csv(csv_buffer, index=False)
                
                st.download_button(
                    label="CSVをダウンロード",
                    data=csv_buffer.getvalue(),
                    file_name="sailing_data.csv",
                    mime="text/csv"
                )
            
            elif export_format == "json":
                # JSONダウンロード用のバッファを準備
                json_str = demo_data.data.to_json(orient="records", date_format="iso")
                
                st.download_button(
                    label="JSONをダウンロード",
                    data=json_str,
                    file_name="sailing_data.json",
                    mime="application/json"
                )
            
            elif export_format == "excel":
                # Excelダウンロード用のバッファを準備
                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer) as writer:
                    demo_data.data.to_excel(writer, sheet_name="Data", index=False)
                    
                    # メタデータシートの追加
                    metadata_df = pd.DataFrame({
                        "Key": list(demo_data.metadata.keys()),
                        "Value": list(demo_data.metadata.values())
                    })
                    metadata_df.to_excel(writer, sheet_name="Metadata", index=False)
                
                excel_buffer.seek(0)
                
                st.download_button(
                    label="Excelをダウンロード",
                    data=excel_buffer,
                    file_name="sailing_data.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        
        except Exception as e:
            st.error(f"エクスポート中にエラーが発生しました: {str(e)}")

# データテーブル
st.markdown("## データテーブル")

with st.expander("データテーブル", expanded=False):
    # データの表示（最初の100行）
    st.dataframe(demo_data.data.head(100), use_container_width=True)

# 使用方法説明
with st.expander("このデモの使い方"):
    st.write("""
    ## 高度なエクスポート機能デモの使用方法
    
    このデモアプリでは、セーリングデータの様々な形式でのエクスポート機能を試すことができます。
    
    ### 機能概要
    
    1. **データ可視化**
        - 地図: トラック（航跡）と戦略ポイントの表示
        - 速度チャート: 時間に対する速度の変化
        - 風向風速: 風速の時間変化と風向の分布
    
    2. **高度なエクスポート機能**
        - PDF: 印刷用の高品質レポート
        - HTML: インタラクティブなWebレポート
        - Excel: 詳細なデータと複数シート
        - 画像: チャートとマップの画像エクスポート
        - データ: CSV、JSON、XMLなどの生データ
    
    ### 使用方法
    
    1. エクスポートしたい形式を選択します
    2. 詳細オプションを設定します
    3. プレビューボタンでエクスポート結果を確認できます
    4. エクスポートボタンで実際にファイルを生成します
    
    ### 注意点
    
    - このデモでは一時ファイルを使用しているため、実際の利用時とは動作が異なる場合があります
    - エクスポート先のパスは適切に設定してください
    - 大きなデータセットの場合、処理に時間がかかることがあります
    """)

# フッター
st.markdown("---")
st.caption("セーリング戦略分析システム - 高度なエクスポート機能デモ")
st.caption("バージョン: 1.0.0")
