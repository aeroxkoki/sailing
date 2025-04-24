# -*- coding: utf-8 -*-
"""
セッション参照クラスのユニットテスト
"""

import pytest
from datetime import datetime
import uuid

from sailing_data_processor.project.session_reference import SessionReference
from sailing_data_processor.project.project_model import Session

class TestSessionReference:
    
    def test_session_reference_init(self):
        """セッション参照の初期化テスト"""
        session_id = str(uuid.uuid4())
        reference = SessionReference(session_id)
        
        assert reference.session_id == session_id
        assert reference.display_name is None
        assert reference.description == ""
        assert isinstance(reference.metadata, dict)
        assert isinstance(reference.added_at, str)
        assert reference.order == 0
        assert isinstance(reference.view_settings, dict)
        assert isinstance(reference.cached_info, dict)
    
    def test_session_reference_with_display_name(self):
        """表示名を指定したセッション参照のテスト"""
        session_id = str(uuid.uuid4())
        display_name = "テスト表示名"
        reference = SessionReference(session_id, display_name=display_name)
        
        assert reference.session_id == session_id
        assert reference.display_name == display_name
    
    def test_update_cached_info(self):
        """セッション情報のキャッシュ更新テスト"""
        session_id = str(uuid.uuid4())
        session = Session(
            name="テストセッション",
            description="テスト説明",
            session_id=session_id,
            category="test",
            status="new"
        )
        
        reference = SessionReference(session_id)
        reference.update_cached_info(session)
        
        assert reference.cached_info["name"] == session.name
        assert reference.cached_info["description"] == session.description
        assert reference.cached_info["category"] == session.category
        assert reference.cached_info["status"] == session.status
        assert "updated_at" in reference.cached_info
        assert "created_at" in reference.cached_info
    
    def test_set_order(self):
        """表示順序設定テスト"""
        session_id = str(uuid.uuid4())
        reference = SessionReference(session_id)
        
        # 初期値
        assert reference.order == 0
        
        # 新しい順序を設定
        new_order = 5
        reference.set_order(new_order)
        assert reference.order == new_order
    
    def test_set_display_name(self):
        """表示名設定テスト"""
        session_id = str(uuid.uuid4())
        reference = SessionReference(session_id)
        
        # 初期値
        assert reference.display_name is None
        
        # 新しい表示名を設定
        new_display_name = "新しい表示名"
        reference.set_display_name(new_display_name)
        assert reference.display_name == new_display_name
    
    def test_update_view_settings(self):
        """表示設定更新テスト"""
        session_id = str(uuid.uuid4())
        reference = SessionReference(session_id)
        
        # 初期値
        assert reference.view_settings["visible"] is True
        assert reference.view_settings["highlight"] is False
        assert reference.view_settings["color_override"] is None
        
        # 設定を更新
        new_settings = {"visible": False, "highlight": True, "color_override": "#FF0000"}
        reference.update_view_settings(new_settings)
        
        assert reference.view_settings["visible"] is False
        assert reference.view_settings["highlight"] is True
        assert reference.view_settings["color_override"] == "#FF0000"
    
    def test_to_dict(self):
        """辞書変換テスト"""
        session_id = str(uuid.uuid4())
        display_name = "テスト表示名"
        description = "テスト説明"
        reference = SessionReference(
            session_id=session_id,
            display_name=display_name,
            description=description,
            order=3
        )
        
        data = reference.to_dict()
        
        assert data["session_id"] == session_id
        assert data["display_name"] == display_name
        assert data["description"] == description
        assert data["order"] == 3
        assert "added_at" in data
        assert "view_settings" in data
        assert "cached_info" in data
    
    def test_from_dict(self):
        """辞書からの復元テスト"""
        session_id = str(uuid.uuid4())
        display_name = "テスト表示名"
        description = "テスト説明"
        added_at = datetime.now().isoformat()
        order = 5
        
        data = {
            "session_id": session_id,
            "display_name": display_name,
            "description": description,
            "metadata": {"test_key": "test_value"},
            "added_at": added_at,
            "order": order,
            "view_settings": {"visible": False},
            "cached_info": {"name": "Cached Name"}
        }
        
        reference = SessionReference.from_dict(data)
        
        assert reference.session_id == session_id
        assert reference.display_name == display_name
        assert reference.description == description
        assert reference.metadata["test_key"] == "test_value"
        assert reference.added_at == added_at
        assert reference.order == order
        assert reference.view_settings["visible"] is False
        assert reference.cached_info["name"] == "Cached Name"
