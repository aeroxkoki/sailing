#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
テストケースのデバッグスクリプト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pytest
import tempfile
import shutil
from sailing_data_processor.project.project_storage import ProjectStorage


def test_search_projects_debug():
    """Test for searching projects with debug output"""
    temp_dir = tempfile.mkdtemp()
    storage = ProjectStorage(temp_dir)
    
    try:
        print("\n=== Creating projects ===")
        # 複数のプロジェクトを作成
        project1 = storage.create_project(
            name="Sailing Competition",
            description="Race in Tokyo Bay",
            tags=["race", "tokyo"]
        )
        print(f"Project1: {project1}")
        
        project2 = storage.create_project(
            name="Practice Session",
            description="Practice in Yokohama",
            tags=["practice", "yokohama"]
        )
        print(f"Project2: {project2}")
        
        project3 = storage.create_project(
            name="Analysis Project",
            description="Wind direction analysis",
            tags=["analysis", "wind", "tokyo"]
        )
        print(f"Project3: {project3}")
        
        print("\n=== All projects in cache ===")
        all_projects = list(storage.projects.values())
        print(f"Number of projects: {len(all_projects)}")
        for p in all_projects:
            print(f"  - {p.name}: {p.description} (tags: {p.tags})")
        
        print("\n=== Searching for 'tokyo' ===")
        # 名前・説明による検索
        results = storage.search_projects(query="tokyo")
        print(f"Found {len(results)} results:")
        for p in results:
            print(f"  - {p.name}: {p.description}")
        
        assert len(results) == 1
        assert results[0].project_id == project1.project_id
        
        print("\n=== Searching by tags ['tokyo'] ===")
        # タグによる検索
        results = storage.search_projects(tags=["tokyo"])
        print(f"Found {len(results)} results:")
        for p in results:
            print(f"  - {p.name}: {p.description} (tags: {p.tags})")
        
        assert len(results) == 2
        project_ids = [p.project_id for p in results]
        assert project1.project_id in project_ids
        assert project3.project_id in project_ids
        
        print("\n=== Complex search: query='分析', tags=['wind'] ===")
        # 複合検索
        results = storage.search_projects(query="分析", tags=["wind"])
        print(f"Found {len(results)} results:")
        for p in results:
            print(f"  - {p.name}: {p.description} (tags: {p.tags})")
        
        assert len(results) == 1
        assert results[0].project_id == project3.project_id
        
        print("\nAll tests passed!")
        
    finally:
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    test_search_projects_debug()
