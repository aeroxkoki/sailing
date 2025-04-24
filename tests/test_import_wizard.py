#!/usr/bin/env python3
"""
インポートウィザードのテスト用モジュール

このモジュールでは：
1. サンプルのGPSデータを生成してCSVとGPXに保存
2. インポートウィザードでデータをインポート
3. インポート結果を表示
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import streamlit as st
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

# プロジェクトのルートディレクトリを追加
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from ui.components.forms.import_wizard import ImportWizard, EnhancedImportWizard, BatchImportUI
from sailing_data_processor.data_model.container import GPSDataContainer


def generate_sample_gps_csv(file_path, num_points=100):
    """
    サンプルのGPSデータを生成してCSVに保存
    
    Parameters
    ----------
    file_path : str
        保存先のファイルパス
    num_points : int, optional
        生成するデータポイント数, by default 100
        
    Returns
    -------
    pd.DataFrame
        生成したGPSデータのDataFrame
    """
    # 基準位置
    base_lat = 35.6234
    base_lon = 139.7732
    
    # 時間軸
    start_time = datetime.now() - timedelta(hours=2)
    times = [start_time + timedelta(seconds=i*30) for i in range(num_points)]
    
    # 位置データの生成（徐々に移動）
    lats = [base_lat + np.random.normal(0, 0.001) + i * 0.0001 for i in range(num_points)]
    lons = [base_lon + np.random.normal(0, 0.001) + i * 0.0001 for i in range(num_points)]
    
    # 速度データの生成（サイン波に乱数ノイズを加える）
    speeds = [5 + np.sin(i/10) * 2 + np.random.normal(0, 0.5) for i in range(num_points)]
    
    # 進行方向の生成（0〜360度）
    courses = [(45 + np.sin(i/15) * 30 + np.random.normal(0, 5)) % 360 for i in range(num_points)]
    
    # DataFrameの作成
    df = pd.DataFrame({
        'timestamp': times,
        'latitude': lats,
        'longitude': lons,
        'speed': speeds,
        'course': courses,
        'elevation': [0 for _ in range(num_points)]  # 高度は0
    })
    
    # CSVに保存
    df.to_csv(file_path, index=False)
    print(f"サンプル用{file_path}に保存しました（{num_points}ポイント）")
    
    return df


def generate_sample_gpx(file_path, num_points=100):
    """
    サンプルのGPSデータをGPXに保存
    
    Parameters
    ----------
    file_path : str
        保存先のファイルパス
    num_points : int, optional
        生成するデータポイント数, by default 100
        
    Returns
    -------
    pd.DataFrame
        生成したGPSデータのDataFrame
    """
    # DataFrame生成
    df = generate_sample_gps_csv(file_path + ".temp.csv", num_points)
    
    # GPXファイルの作成
    gpx = ET.Element('gpx', version="1.1", 
                     attrib={'creator': 'Sailing Strategy Analyzer Test Script',
                             'xmlns': 'http://www.topografix.com/GPX/1/1'})
    
    # メタデータ
    metadata = ET.SubElement(gpx, 'metadata')
    ET.SubElement(metadata, 'name').text = 'Sample GPX Track'
    ET.SubElement(metadata, 'desc').text = 'Generated for testing purposes'
    ET.SubElement(metadata, 'time').text = datetime.now().isoformat()
    
    # トラックの作成
    trk = ET.SubElement(gpx, 'trk')
    ET.SubElement(trk, 'name').text = 'Sample Track'
    trkseg = ET.SubElement(trk, 'trkseg')
    
    # トラックポイントの追加
    for _, row in df.iterrows():
        trkpt = ET.SubElement(trkseg, 'trkpt', lat=str(row['latitude']), lon=str(row['longitude']))
        ET.SubElement(trkpt, 'ele').text = str(row['elevation'])
        ET.SubElement(trkpt, 'time').text = row['timestamp'].isoformat()
        
        # 拡張データ
        extensions = ET.SubElement(trkpt, 'extensions')
        speed_element = ET.SubElement(extensions, 'speed')
        speed_element.text = str(row['speed'])
        course_element = ET.SubElement(extensions, 'course')
        course_element.text = str(row['course'])
    
    # XMLツリーの作成と保存
    tree = ET.ElementTree(gpx)
    tree.write(file_path, encoding='utf-8', xml_declaration=True)
    print(f"GPXファイル{file_path}に保存しました（{num_points}ポイント）")
    
    # 一時ファイルの削除
    if os.path.exists(file_path + ".temp.csv"):
        os.remove(file_path + ".temp.csv")
    
    return df


def import_wizard_test_app():
    """
    インポートウィザードのテスト用Streamlitアプリ
    """
    # アプリ設定
    st.set_page_config(
        page_title="インポートウィザードテスト",
        page_icon="⛵",
        layout="wide",
    )
    
    # タイトル
    st.title("インポートウィザードテスト")
    
    # サンプルデータ生成
    if 'sample_files' not in st.session_state:
        st.session_state['sample_files'] = {}
        
        # CSVファイル生成
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp:
            csv_path = tmp.name
            generate_sample_gps_csv(csv_path, 200)
            st.session_state['sample_files']['csv'] = csv_path
        
        # GPXファイル生成
        with tempfile.NamedTemporaryFile(delete=False, suffix='.gpx') as tmp:
            gpx_path = tmp.name
            generate_sample_gpx(gpx_path, 200)
            st.session_state['sample_files']['gpx'] = gpx_path
    
    # サンプルデータ表示
    st.write("### サンプルデータの生成")
    
    csv_path = st.session_state['sample_files'].get('csv')
    gpx_path = st.session_state['sample_files'].get('gpx')
    
    col1, col2 = st.columns(2)
    
    with col1:
        if csv_path and os.path.exists(csv_path):
            st.success(f"CSVサンプルデータを生成しました: {csv_path}")
            
            # サンプルデータの中身を表示
            try:
                sample_df = pd.read_csv(csv_path)
                st.write("CSVプレビュー")
                st.dataframe(sample_df.head())
            except Exception as e:
                st.error(f"CSVの読み込みに失敗しました: {e}")
        else:
            st.error("CSVサンプルデータの生成に失敗しました。")
    
    with col2:
        if gpx_path and os.path.exists(gpx_path):
            st.success(f"GPXサンプルデータを生成しました: {gpx_path}")
            
            # GPXファイルの中身を表示
            try:
                with open(gpx_path, 'r') as f:
                    gpx_content = f.read(1000)  # 最初の1000文字だけ表示
                
                st.write("GPXプレビュー")
                st.code(gpx_content + "...", language="xml")
            except Exception as e:
                st.error(f"GPXの読み込みに失敗しました: {e}")
        else:
            st.error("GPXサンプルデータの生成に失敗しました。")
    
    # 各種インポートウィザード表示
    tab1, tab2, tab3 = st.tabs(["基本インポートウィザード", "拡張インポートウィザード", "バッチインポート"])
    
    def on_import_complete(container):
        """インポート完了時のコールバック"""
        st.session_state["imported_data"] = container
        st.success("データのインポートが完了しました！")
    
    with tab1:
        st.header("基本インポートウィザード")
        wizard = ImportWizard(
            key="test_import_wizard",
            on_import_complete=on_import_complete
        )
        wizard.render()
    
    with tab2:
        st.header("拡張インポートウィザード")
        enhanced_wizard = EnhancedImportWizard(
            key="test_enhanced_wizard",
            on_import_complete=on_import_complete
        )
        enhanced_wizard.render()
    
    with tab3:
        st.header("バッチインポート")
        batch_import = BatchImportUI(
            key="test_batch_import",
            on_import_complete=on_import_complete
        )
        batch_import.render()
    
    # インポート結果データの表示
    if "imported_data" in st.session_state and st.session_state["imported_data"]:
        st.write("---")
        st.header("インポート結果データ")
        
        container = st.session_state["imported_data"]
        
        if isinstance(container, GPSDataContainer):
            # メタデータ表示
            st.write("### メタデータ")
            st.json(container.metadata)
            
            # データ表示
            st.write("### データ")
            st.dataframe(container.data)
            
            # 地図表示
            st.write("### 位置データマップ")
            map_data = container.data[["latitude", "longitude"]]
            st.map(map_data)
        else:
            st.write("インポート結果データの型が不明です。")


if __name__ == "__main__":
    import_wizard_test_app()
