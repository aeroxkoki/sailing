# -*- coding: utf-8 -*-
"""
レポートテンプレートマネージャー

レポートテンプレートの管理・更新・適用を行うモジュール
"""

import os
import json
import uuid
import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

class TemplateManager:
    """
    テンプレート管理クラス
    """
    
    def __init__(self, templates_dir: Union[str, Path] = None):
        """
        初期化
        
        Parameters
        ----------
        templates_dir : Union[str, Path], optional
            テンプレートディレクトリ, by default None
        """
        self.templates_dir = Path(templates_dir) if templates_dir else Path.cwd() / "templates"
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        
        self.metadata_path = self.templates_dir / "metadata.json"
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict[str, Any]:
        """
        メタデータをロード
        
        Returns
        -------
        Dict[str, Any]
            メタデータ辞書
        """
        if not self.metadata_path.exists():
            metadata = {
                "templates": {},
                "categories": ["基本", "詳細", "プレゼンテーション", "コーチング"],
                "tags": ["標準", "基本", "詳細", "分析", "プレゼンテーション", "視覚化"]
            }
            self._save_metadata(metadata)
            return metadata
        
        try:
            with open(self.metadata_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"メタデータのロード中にエラーが発生しました: {str(e)}")
            return {
                "templates": {},
                "categories": ["基本", "詳細", "プレゼンテーション", "コーチング"],
                "tags": ["標準", "基本", "詳細", "分析", "プレゼンテーション", "視覚化"]
            }
    
    def _save_metadata(self, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        メタデータを保存
        
        Parameters
        ----------
        metadata : Optional[Dict[str, Any]], optional
            保存するメタデータ, by default None
            
        Returns
        -------
        bool
            保存に成功した場合はTrue、失敗した場合はFalse
        """
        if metadata is None:
            metadata = self.metadata
        
        try:
            with open(self.metadata_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"メタデータの保存中にエラーが発生しました: {str(e)}")
            return False
    
    def list_templates(self, category: Optional[str] = None, tags: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        テンプレートのリストを取得
        
        Parameters
        ----------
        category : Optional[str], optional
            フィルタするカテゴリ, by default None
        tags : Optional[List[str]], optional
            フィルタするタグリスト, by default None
        
        Returns
        -------
        List[Dict[str, Any]]
            テンプレート情報のリスト
        """
        templates = []
        
        for template_id, template_meta in self.metadata["templates"].items():
            # フィルタ条件に合致するか確認
            if category and template_meta.get("category") != category:
                continue
            
            if tags:
                template_tags = template_meta.get("tags", [])
                if not all(tag in template_tags for tag in tags):
                    continue
            
            templates.append(template_meta)
        
        # 更新日時の降順で並べ替え
        templates.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        
        return templates
        
    def get_categories(self) -> List[str]:
        """
        すべてのカテゴリを取得
        
        Returns
        -------
        List[str]
            カテゴリのリスト
        """
        return self.metadata["categories"]
    
    def get_tags(self) -> List[str]:
        """
        すべてのタグを取得
        
        Returns
        -------
        List[str]
            タグのリスト
        """
        return self.metadata["tags"]
