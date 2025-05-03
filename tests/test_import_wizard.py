#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
インポートウィザードのテスト
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
import pytest

# プロジェクトのルートディレクトリを追加
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

def generate_sample_gps_csv(file_path, num_points=100):
    """
    サンプルのGPSデータを生成してCSVに保存
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
    
    return df

def generate_sample_gpx(file_path, num_points=100):
    """
    サンプルのGPSデータをGPXに保存
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
    
    # 一時ファイルの削除
    if os.path.exists(file_path + ".temp.csv"):
        os.remove(file_path + ".temp.csv")
    
    return df

@pytest.fixture
def sample_files():
    """サンプルファイルのフィクスチャ"""
    files = {}
    
    # CSVファイル生成
    with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp:
        csv_path = tmp.name
        generate_sample_gps_csv(csv_path, 200)
        files['csv'] = csv_path
    
    # GPXファイル生成
    with tempfile.NamedTemporaryFile(delete=False, suffix='.gpx') as tmp:
        gpx_path = tmp.name
        generate_sample_gpx(gpx_path, 200)
        files['gpx'] = gpx_path
    
    yield files
    
    # クリーンアップ
    for filepath in files.values():
        if os.path.exists(filepath):
            os.remove(filepath)

def test_sample_csv_generation(sample_files):
    """CSVサンプルデータ生成のテスト"""
    csv_path = sample_files.get('csv')
    
    assert csv_path is not None, "CSVファイルパスが存在しません"
    assert os.path.exists(csv_path), "CSVファイルが生成されていません"
    
    # CSVファイルの読み込み
    df = pd.read_csv(csv_path)
    
    assert len(df) == 200, "生成されたデータポイントの数が正しくありません"
    assert 'timestamp' in df.columns, "timestamp列が存在しません"
    assert 'latitude' in df.columns, "latitude列が存在しません"
    assert 'longitude' in df.columns, "longitude列が存在しません"
    assert 'speed' in df.columns, "speed列が存在しません"
    assert 'course' in df.columns, "course列が存在しません"

def test_sample_gpx_generation(sample_files):
    """GPXサンプルデータ生成のテスト"""
    gpx_path = sample_files.get('gpx')
    
    assert gpx_path is not None, "GPXファイルパスが存在しません"
    assert os.path.exists(gpx_path), "GPXファイルが生成されていません"
    
    # GPXファイルのXML解析
    tree = ET.parse(gpx_path)
    root = tree.getroot()
    
    assert root.tag.endswith('gpx'), "ルート要素がgpxではありません"
    
    # メタデータの確認
    metadata = root.find('.//{http://www.topografix.com/GPX/1/1}metadata')
    assert metadata is not None, "メタデータ要素が見つかりません"
    
    # トラックの確認
    trk = root.find('.//{http://www.topografix.com/GPX/1/1}trk')
    assert trk is not None, "トラック要素が見つかりません"
    
    # トラックポイントの数を確認
    trkpts = root.findall('.//{http://www.topografix.com/GPX/1/1}trkpt')
    assert len(trkpts) == 200, "トラックポイントの数が正しくありません"

def test_import_wizard_components():
    """インポートウィザードコンポーネントのテスト"""
    try:
        from ui.components.forms.import_wizard import ImportWizard, EnhancedImportWizard, BatchImportUI
        from sailing_data_processor.data_model.container import GPSDataContainer
        
        assert ImportWizard is not None, "ImportWizardクラスがインポートできません"
        assert EnhancedImportWizard is not None, "EnhancedImportWizardクラスがインポートできません"
        assert BatchImportUI is not None, "BatchImportUIクラスがインポートできません"
        assert GPSDataContainer is not None, "GPSDataContainerクラスがインポートできません"
    except ImportError as e:
        pytest.fail(f"インポートウィザードコンポーネントのインポートに失敗: {e}")

@pytest.mark.parametrize("wizard_class", [
    "ImportWizard",
    "EnhancedImportWizard",
    "BatchImportUI"
])
def test_wizard_initialization(wizard_class):
    """各ウィザードクラスの初期化テスト"""
    try:
        # モジュールのインポート
        from ui.components.forms.import_wizard import ImportWizard, EnhancedImportWizard, BatchImportUI
        
        # クラスの動的取得
        wizard_cls = eval(wizard_class)
        
        # ダミーのコールバック関数
        def dummy_callback(container):
            pass
        
        # インスタンス化（Streamlitがない環境でもテスト可能なようにtry-catch）
        try:
            wizard = wizard_cls(
                key=f"test_{wizard_class.lower()}",
                on_import_complete=dummy_callback
            )
            assert wizard is not None, f"{wizard_class}のインスタンス化に失敗しました"
        except ImportError:
            # Streamlitが必要な場合はスキップ
            pytest.skip(f"{wizard_class}はStreamlitが必要です")
    except ImportError as e:
        pytest.fail(f"{wizard_class}のインポートに失敗: {e}")
