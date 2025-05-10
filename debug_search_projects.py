#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
デバッグスクリプト：プロジェクト検索の問題を調査
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sailing_data_processor.project.project_storage import ProjectStorage
from sailing_data_processor.project.project_model import Project

import tempfile
import shutil


def debug_search_projects():
    """プロジェクト検索のデバッグ"""
    
    # 一時ディレクトリを作成
    temp_dir = tempfile.mkdtemp()
    print(f"Temporary directory: {temp_dir}")
    
    try:
        # ProjectStorageインスタンスを作成
        storage = ProjectStorage(temp_dir)
        print(f"Storage initialized with base path: {storage.base_path}")
        
        # プロジェクトを作成
        print("\n=== Creating projects ===")
        project1 = storage.create_project(
            name="Sailing Competition",
            description="Race in Tokyo Bay",
            tags=["race", "tokyo"]
        )
        print(f"Project 1 created: {project1}")
        
        project2 = storage.create_project(
            name="Practice Session",
            description="Practice in Yokohama",
            tags=["practice", "yokohama"]
        )
        print(f"Project 2 created: {project2}")
        
        project3 = storage.create_project(
            name="Analysis Project",
            description="Wind direction analysis",
            tags=["analysis", "wind", "tokyo"]
        )
        print(f"Project 3 created: {project3}")
        
        # プロジェクトの一覧を取得
        print("\n=== All projects in cache ===")
        all_projects = list(storage.projects.values())
        for p in all_projects:
            print(f"  - {p.name}: {p.description} (tags: {p.tags})")
        
        # 検索を実行
        print("\n=== Searching for 'tokyo' ===")
        results = storage.search_projects(query="tokyo")
        print(f"Found {len(results)} results:")
        for p in results:
            print(f"  - {p.name}: {p.description}")
        
        # クエリで検索をデバッグ
        print("\n=== Debug query search ===")
        query = "tokyo"
        query_lower = query.lower()
        print(f"Query: '{query}' (lower: '{query_lower}')")
        
        for project in all_projects:
            print(f"\nChecking project: {project.name}")
            print(f"  Name: {project.name}")
            print(f"  Name lower: {project.name.lower()}")
            print(f"  Description: {project.description}")
            print(f"  Description lower: {project.description.lower()}")
            
            name_match = query_lower in project.name.lower()
            desc_match = query_lower in project.description.lower()
            
            print(f"  Query in name: {name_match}")
            print(f"  Query in description: {desc_match}")
            print(f"  Overall match: {name_match or desc_match}")
        
    finally:
        # 一時ディレクトリを削除
        shutil.rmtree(temp_dir)
        print(f"\nTemporary directory removed: {temp_dir}")


if __name__ == "__main__":
    debug_search_projects()
