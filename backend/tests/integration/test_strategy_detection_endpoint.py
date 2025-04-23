"""
戦略検出エンドポイントの統合テスト
"""

import pytest
from fastapi.testclient import TestClient
from uuid import uuid4

from app.main import app

client = TestClient(app)

def test_strategy_detection():
    """戦略検出テスト"""
    # テスト用パラメータ
    test_params = {
        "session_id": str(uuid4()),  # ランダムなセッションID
        "detection_sensitivity": 0.5,
        "min_tack_angle": 45.0,
        "min_jibe_angle": 45.0
    }
    
    # リクエスト送信
    response = client.post(
        "/api/v1/strategy-detection/detect",
        json=test_params
    )
    
    # レスポンスの検証
    assert response.status_code == 200, f"エラー: {response.text}"
    
    # レスポンス内容の検証
    data = response.json()
    assert "strategy_points" in data, "戦略ポイントが含まれていません"
    assert "created_at" in data, "作成日時が含まれていません"
    assert "session_id" in data, "セッションIDが含まれていません"
    
    # セッションIDの一致を確認
    assert data["session_id"] == test_params["session_id"], "セッションIDが一致しません"

def test_strategy_detection_invalid_uuid():
    """無効なUUIDでの戦略検出テスト（エラーケース）"""
    # 無効なUUIDを含むパラメータ
    test_params = {
        "session_id": "not-a-valid-uuid",
        "detection_sensitivity": 0.5,
        "min_tack_angle": 45.0,
        "min_jibe_angle": 45.0
    }
    
    # リクエスト送信
    response = client.post(
        "/api/v1/strategy-detection/detect",
        json=test_params
    )
    
    # エラーレスポンスの検証
    assert response.status_code != 200, "無効なUUIDがエラーになっていません"

def test_strategy_detection_missing_session_id():
    """セッションIDなしでの戦略検出テスト（エラーケース）"""
    # セッションIDを含まないパラメータ
    test_params = {
        "detection_sensitivity": 0.5,
        "min_tack_angle": 45.0,
        "min_jibe_angle": 45.0
    }
    
    # リクエスト送信
    response = client.post(
        "/api/v1/strategy-detection/detect",
        json=test_params
    )
    
    # エラーレスポンスの検証
    assert response.status_code != 200, "セッションID必須エラーが発生していません"

def test_strategy_detection_invalid_params():
    """無効なパラメータでの戦略検出テスト（エラーケース）"""
    # 無効な値を含むパラメータ
    test_params = {
        "session_id": str(uuid4()),
        "detection_sensitivity": 2.0,  # 0-1の範囲外
        "min_tack_angle": -10.0,  # 負の値
        "min_jibe_angle": 1000.0  # 極端に大きい値
    }
    
    # リクエスト送信
    response = client.post(
        "/api/v1/strategy-detection/detect",
        json=test_params
    )
    
    # エラーレスポンスの検証
    assert response.status_code != 200, "パラメータ検証エラーが発生していません"