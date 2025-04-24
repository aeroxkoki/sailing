# -*- coding: utf-8 -*-
"""
プロジェクトコレクションクラスのユニットテスト
"""

import pytest
from datetime import datetime
import uuid

from sailing_data_processor.project.project_collection import ProjectCollection
from sailing_data_processor.project.project_model import Project

class TestProjectCollection:
    
    def test_project_collection_init(self):
        """プロジェクトコレクションの初期化テスト"""
        collection = ProjectCollection()
        
        assert collection.version == "1.0"
        assert isinstance(collection.metadata, dict)
        assert "created_at" in collection.metadata
        assert "updated_at" in collection.metadata
        assert len(collection.projects) == 0
        assert len(collection.root_projects) == 0
    
    def test_add_project(self):
        """プロジェクト追加テスト"""
        collection = ProjectCollection()
        
        # ルートプロジェクトの追加
        root_project = Project("ルートプロジェクト")
        collection.add_project(root_project)
        
        assert root_project.project_id in collection.projects
        assert root_project.project_id in collection.root_projects
        assert len(collection.projects) == 1
        assert len(collection.root_projects) == 1
        
        # サブプロジェクトの追加
        sub_project = Project("サブプロジェクト", parent_id=root_project.project_id)
        collection.add_project(sub_project)
        
        assert sub_project.project_id in collection.projects
        assert sub_project.project_id not in collection.root_projects
        assert len(collection.projects) == 2
        assert len(collection.root_projects) == 1
    
    def test_remove_project_simple(self):
        """シンプルなプロジェクト削除テスト"""
        collection = ProjectCollection()
        
        # プロジェクトの追加
        project = Project("テストプロジェクト")
        collection.add_project(project)
        
        # 存在確認
        assert project.project_id in collection.projects
        assert project.project_id in collection.root_projects
        
        # プロジェクトの削除
        success = collection.remove_project(project.project_id)
        
        assert success is True
        assert project.project_id not in collection.projects
        assert project.project_id not in collection.root_projects
        assert len(collection.projects) == 0
        assert len(collection.root_projects) == 0
    
    def test_remove_project_with_sub_projects(self):
        """サブプロジェクトを持つプロジェクトの削除テスト"""
        collection = ProjectCollection()
        
        # ルートプロジェクトの追加
        root_project = Project("ルートプロジェクト")
        collection.add_project(root_project)
        
        # サブプロジェクトの追加
        sub_project1 = Project("サブプロジェクト1", parent_id=root_project.project_id)
        sub_project2 = Project("サブプロジェクト2", parent_id=root_project.project_id)
        collection.add_project(sub_project1)
        collection.add_project(sub_project2)
        
        # 親子関係の設定
        root_project.add_sub_project(sub_project1.project_id)
        root_project.add_sub_project(sub_project2.project_id)
        
        # 存在確認
        assert len(collection.projects) == 3
        assert len(collection.root_projects) == 1
        assert len(root_project.sub_projects) == 2
        
        # プロジェクトの削除（サブプロジェクトは残す）
        success = collection.remove_project(root_project.project_id, recursive=False)
        
        assert success is True
        assert root_project.project_id not in collection.projects
        assert root_project.project_id not in collection.root_projects
        
        # サブプロジェクトはルートプロジェクトになったはず
        assert sub_project1.project_id in collection.projects
        assert sub_project2.project_id in collection.projects
        assert sub_project1.project_id in collection.root_projects
        assert sub_project2.project_id in collection.root_projects
        
        # 残りのプロジェクト数の確認
        assert len(collection.projects) == 2
        assert len(collection.root_projects) == 2
    
    def test_remove_project_recursive(self):
        """サブプロジェクトを含めた再帰的削除テスト"""
        collection = ProjectCollection()
        
        # ルートプロジェクトの追加
        root_project = Project("ルートプロジェクト")
        collection.add_project(root_project)
        
        # サブプロジェクトの追加
        sub_project1 = Project("サブプロジェクト1", parent_id=root_project.project_id)
        sub_project2 = Project("サブプロジェクト2", parent_id=root_project.project_id)
        collection.add_project(sub_project1)
        collection.add_project(sub_project2)
        
        # 親子関係の設定
        root_project.add_sub_project(sub_project1.project_id)
        root_project.add_sub_project(sub_project2.project_id)
        
        # 存在確認
        assert len(collection.projects) == 3
        assert len(collection.root_projects) == 1
        
        # プロジェクトの再帰的削除
        success = collection.remove_project(root_project.project_id, recursive=True)
        
        assert success is True
        assert root_project.project_id not in collection.projects
        assert sub_project1.project_id not in collection.projects
        assert sub_project2.project_id not in collection.projects
        assert len(collection.projects) == 0
        assert len(collection.root_projects) == 0
    
    def test_get_root_projects(self):
        """ルートプロジェクト取得テスト"""
        collection = ProjectCollection()
        
        # ルートプロジェクトの追加
        root_project1 = Project("ルートプロジェクト1")
        root_project2 = Project("ルートプロジェクト2")
        collection.add_project(root_project1)
        collection.add_project(root_project2)
        
        # サブプロジェクトの追加
        sub_project = Project("サブプロジェクト", parent_id=root_project1.project_id)
        collection.add_project(sub_project)
        root_project1.add_sub_project(sub_project.project_id)
        
        # ルートプロジェクト取得
        root_projects = collection.get_root_projects()
        
        assert len(root_projects) == 2
        assert root_project1 in root_projects
        assert root_project2 in root_projects
        assert sub_project not in root_projects
    
    def test_get_sub_projects(self):
        """サブプロジェクト取得テスト"""
        collection = ProjectCollection()
        
        # ルートプロジェクトの追加
        root_project = Project("ルートプロジェクト")
        collection.add_project(root_project)
        
        # サブプロジェクトの追加
        sub_project1 = Project("サブプロジェクト1", parent_id=root_project.project_id)
        sub_project2 = Project("サブプロジェクト2", parent_id=root_project.project_id)
        collection.add_project(sub_project1)
        collection.add_project(sub_project2)
        
        # 親子関係の設定
        root_project.add_sub_project(sub_project1.project_id)
        root_project.add_sub_project(sub_project2.project_id)
        
        # サブプロジェクト取得
        sub_projects = collection.get_sub_projects(root_project.project_id)
        
        assert len(sub_projects) == 2
        assert sub_project1 in sub_projects
        assert sub_project2 in sub_projects
    
    def test_search_projects(self):
        """プロジェクト検索テスト"""
        collection = ProjectCollection()
        
        # プロジェクトの追加
        project1 = Project("テストプロジェクト1", description="これはテストです")
        project1.add_tag("テスト")
        project1.add_tag("重要")
        project1.category = "カテゴリA"
        
        project2 = Project("テストプロジェクト2", description="重要なプロジェクト")
        project2.add_tag("テスト")
        project2.category = "カテゴリB"
        
        project3 = Project("別のプロジェクト", description="これは別のものです")
        project3.add_tag("その他")
        project3.category = "カテゴリA"
        
        collection.add_project(project1)
        collection.add_project(project2)
        collection.add_project(project3)
        
        # クエリによる検索
        results = collection.search_projects("テスト")
        assert len(results) == 2
        assert project1 in results
        assert project2 in results
        
        # タグによる検索
        results = collection.search_projects(tags=["テスト"])
        assert len(results) == 2
        assert project1 in results
        assert project2 in results
        
        results = collection.search_projects(tags=["重要"])
        assert len(results) == 1
        assert project1 in results
        
        # カテゴリによる検索
        results = collection.search_projects(categories=["カテゴリA"])
        assert len(results) == 2
        assert project1 in results
        assert project3 in results
        
        # クエリ、タグ、カテゴリの組み合わせ
        results = collection.search_projects("テスト", tags=["テスト"], categories=["カテゴリA"])
        assert len(results) == 1
        assert project1 in results
    
    def test_move_project(self):
        """プロジェクト移動テスト"""
        collection = ProjectCollection()
        
        # ルートプロジェクトの追加
        root_project1 = Project("ルートプロジェクト1")
        root_project2 = Project("ルートプロジェクト2")
        collection.add_project(root_project1)
        collection.add_project(root_project2)
        
        # サブプロジェクトの追加
        sub_project = Project("サブプロジェクト", parent_id=root_project1.project_id)
        collection.add_project(sub_project)
        root_project1.add_sub_project(sub_project.project_id)
        
        # 別のルートプロジェクトに移動
        success = collection.move_project(sub_project.project_id, root_project2.project_id)
        
        assert success is True
        
        # 親子関係の確認
        assert sub_project.project_id not in root_project1.sub_projects
        assert sub_project.project_id in root_project2.sub_projects
        assert sub_project.parent_id == root_project2.project_id
        
        # ルートに移動
        success = collection.move_project(sub_project.project_id, None)
        
        assert success is True
        
        # 親子関係の確認
        assert sub_project.project_id not in root_project2.sub_projects
        assert sub_project.parent_id is None
        assert sub_project.project_id in collection.root_projects
    
    def test_is_descendant(self):
        """子孫判定テスト"""
        collection = ProjectCollection()
        
        # プロジェクト階層の作成
        root = Project("ルート")
        child = Project("子", parent_id=root.project_id)
        grandchild = Project("孫", parent_id=child.project_id)
        
        collection.add_project(root)
        collection.add_project(child)
        collection.add_project(grandchild)
        
        root.add_sub_project(child.project_id)
        child.add_sub_project(grandchild.project_id)
        
        # 子孫判定
        assert collection._is_descendant(child.project_id, root.project_id) is True
        assert collection._is_descendant(grandchild.project_id, root.project_id) is True
        assert collection._is_descendant(grandchild.project_id, child.project_id) is True
        
        # 非子孫判定
        assert collection._is_descendant(root.project_id, child.project_id) is False
        assert collection._is_descendant(child.project_id, grandchild.project_id) is False
        assert collection._is_descendant(root.project_id, grandchild.project_id) is False
    
    def test_to_dict(self):
        """辞書変換テスト"""
        collection = ProjectCollection(version="1.1", metadata={"test_key": "test_value"})
        
        # プロジェクトの追加
        project1 = Project("プロジェクト1")
        project2 = Project("プロジェクト2")
        collection.add_project(project1)
        collection.add_project(project2)
        
        # 辞書に変換
        data = collection.to_dict()
        
        assert data["version"] == "1.1"
        assert data["metadata"]["test_key"] == "test_value"
        assert len(data["root_projects"]) == 2
        assert project1.project_id in data["projects"]
        assert project2.project_id in data["projects"]
        assert data["projects"][project1.project_id]["name"] == "プロジェクト1"
    
    def test_from_dict(self):
        """辞書からの復元テスト"""
        # プロジェクト用のデータ作成
        project1_id = str(uuid.uuid4())
        project2_id = str(uuid.uuid4())
        
        project1_data = {
            "project_id": project1_id,
            "name": "プロジェクト1",
            "description": "説明1",
            "category": "カテゴリ1",
            "tags": ["タグ1", "タグ2"],
            "parent_id": None,
            "sub_projects": [],
            "sessions": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "metadata": {}
        }
        
        project2_data = {
            "project_id": project2_id,
            "name": "プロジェクト2",
            "description": "説明2",
            "category": "カテゴリ2",
            "tags": ["タグ3"],
            "parent_id": None,
            "sub_projects": [],
            "sessions": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "metadata": {}
        }
        
        # コレクションデータの作成
        collection_data = {
            "version": "1.1",
            "metadata": {"test_key": "test_value"},
            "root_projects": [project1_id, project2_id],
            "projects": {
                project1_id: project1_data,
                project2_id: project2_data
            }
        }
        
        # 辞書からコレクションを復元
        collection = ProjectCollection.from_dict(collection_data)
        
        assert collection.version == "1.1"
        assert collection.metadata["test_key"] == "test_value"
        assert len(collection.root_projects) == 2
        assert project1_id in collection.projects
        assert project2_id in collection.projects
        assert collection.projects[project1_id].name == "プロジェクト1"
        assert collection.projects[project2_id].name == "プロジェクト2"
        assert "タグ1" in collection.projects[project1_id].tags
