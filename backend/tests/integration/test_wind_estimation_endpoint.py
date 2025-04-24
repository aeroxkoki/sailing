# -*- coding: utf-8 -*-
"""
風向風速推定エンドポイントの統合テスト
"""

import os
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

# テスト用のデータファイルパス
TEST_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "test_data")
CSV_FILE_PATH = os.path.join(TEST_DATA_DIR, "sample.csv")
GPX_FILE_PATH = os.path.join(TEST_DATA_DIR, "sample.gpx")

def test_wind_estimation_with_csv():
    """CSVファイルを使った風向風速推定テスト"""
    # ファイルの存在を確認
    assert os.path.exists(CSV_FILE_PATH), f"テストファイルが見つかりません: {CSV_FILE_PATH}"
    
    # テスト用リクエストの準備
    with open(CSV_FILE_PATH, "rb") as f:
        file_content = f.read()
    
    # リクエスト送信
    response = client.post(
        "/api/v1/wind-estimation/estimate",
        files={"gps_data": ("sample.csv", file_content, "text/csv")},
        data={
            "boat_type": "default",
            "min_tack_angle": "30",
            "use_bayesian": "true",
            "file_format": "csv"
        }
    )
    
    # レスポンスの検証
    assert response.status_code == 200, f"エラー: {response.text}"
    
    # レスポンス内容の検証
    data = response.json()
    assert "wind_data" in data, "風データが含まれていません"
    assert "average_speed" in data, "平均風速が含まれていません"
    assert "average_direction" in data, "平均風向が含まれていません"
    assert "created_at" in data, "作成日時が含まれていません"
    
    # 値の妥当性検証
    assert isinstance(data["average_speed"], (int, float)), "平均風速が数値ではありません"
    assert 0 <= data["average_direction"] <= 360, "平均風向が0-360度の範囲外です"
    assert len(data["wind_data"]) > 0, "風データが空です"

def test_wind_estimation_with_gpx():
    """GPXファイルを使った風向風速推定テスト"""
    # ファイルの存在を確認
    if not os.path.exists(GPX_FILE_PATH):
        pytest.skip("GPXテストファイルが見つかりません")
    
    # テスト用リクエストの準備
    with open(GPX_FILE_PATH, "rb") as f:
        file_content = f.read()
    
    # リクエスト送信
    response = client.post(
        "/api/v1/wind-estimation/estimate",
        files={"gps_data": ("sample.gpx", file_content, "application/gpx+xml")},
        data={
            "boat_type": "laser",
            "min_tack_angle": "30",
            "use_bayesian": "true",
            "file_format": "gpx"
        }
    )
    
    # レスポンスの検証
    assert response.status_code == 200, f"エラー: {response.text}"
    
    # レスポンス内容の検証
    data = response.json()
    assert "wind_data" in data, "風データが含まれていません"
    assert "average_speed" in data, "平均風速が含まれていません"
    assert "average_direction" in data, "平均風向が含まれていません"

def test_wind_estimation_with_invalid_file():
    """無効なファイルを使った風向風速推定テスト（エラーケース）"""
    # 無効なファイル内容を作成
    invalid_content = b"This is not a valid CSV or GPX file"
    
    # リクエスト送信
    response = client.post(
        "/api/v1/wind-estimation/estimate",
        files={"gps_data": ("invalid.csv", invalid_content, "text/csv")},
        data={
            "boat_type": "default",
            "min_tack_angle": "30",
            "use_bayesian": "true",
            "file_format": "csv"
        }
    )
    
    # エラーレスポンスの検証
    assert response.status_code != 200, "無効なファイルがエラーになっていません"

def test_wind_estimation_missing_file():
    """ファイルなしでの風向風速推定テスト（エラーケース）"""
    # ファイルなしでリクエスト送信
    response = client.post(
        "/api/v1/wind-estimation/estimate",
        data={
            "boat_type": "default",
            "min_tack_angle": "30",
            "use_bayesian": "true",
            "file_format": "csv"
        }
    )
    
    # エラーレスポンスの検証
    assert response.status_code != 200, "ファイル必須エラーが発生していません"