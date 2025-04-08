"""
sailing_data_processor.reporting.templates.template_manager

レポートテンプレート管理のためのモジュールです。
テンプレートのロード、保存、検索、タグ付け、カテゴリ分類など、
テンプレート管理に関する機能を提供します。
"""

from typing import Dict, List, Any, Optional, Union, Set, Tuple
from pathlib import Path
import os
import json
import shutil
import datetime
import uuid

from sailing_data_processor.reporting.templates.template_model import (
    Template, Section, Element, TemplateOutputFormat
)


class TemplateManager:
    """
    レポートテンプレート管理クラス
    
    テンプレートの作成、保存、ロード、検索など、テンプレート管理に関する
    機能を提供します。
    """
    
    def __init__(self, template_dir: Optional[Union[str, Path]] = None):
        """
        初期化
        
        Parameters
        ----------
        template_dir : Optional[Union[str, Path]], optional
            テンプレートディレクトリのパス, by default None
            Noneの場合は、デフォルトのディレクトリを使用
        """
        if template_dir is None:
            # デフォルトのテンプレートディレクトリを設定
            module_dir = Path(__file__).parent
            template_dir = module_dir / "data"
        
        self.template_dir = Path(template_dir)
        self.template_dir.mkdir(parents=True, exist_ok=True)
        
        # 出力形式ごとのディレクトリを作成
        for fmt in [e.value for e in TemplateOutputFormat]:
            fmt_dir = self.template_dir / fmt
            fmt_dir.mkdir(exist_ok=True)
        
        # メタデータの保存場所
        self.metadata_file = self.template_dir / "metadata.json"
        self._load_metadata()
    
    def _load_metadata(self) -> None:
        """
        テンプレートのメタデータをロード
        """
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, "r", encoding="utf-8") as f:
                    self.metadata = json.load(f)
            except (json.JSONDecodeError, Exception):
                self.metadata = {"templates": {}, "categories": [], "tags": []}
        else:
            self.metadata = {"templates": {}, "categories": [], "tags": []}
    
    def _save_metadata(self) -> None:
        """
        テンプレートのメタデータを保存
        """
        try:
            with open(self.metadata_file, "w", encoding="utf-8") as f:
                json.dump(self.metadata, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"メタデータの保存中にエラーが発生しました: {str(e)}")
    
    def _update_template_metadata(self, template: Template) -> None:
        """
        テンプレートのメタデータを更新
        
        Parameters
        ----------
        template : Template
            更新するテンプレート
        """
        template_meta = {
            "template_id": template.template_id,
            "name": template.name,
            "description": template.description,
            "author": template.author,
            "created_at": template.created_at.isoformat(),
            "updated_at": template.updated_at.isoformat(),
            "version": template.version,
            "tags": template.tags,
            "category": template.category,
            "output_format": template.output_format.value,
            "file_path": self._get_template_path(template.template_id, template.output_format.value)
        }
        
        self.metadata["templates"][template.template_id] = template_meta
        
        # カテゴリとタグの更新
        if template.category and template.category not in self.metadata["categories"]:
            self.metadata["categories"].append(template.category)
        
        for tag in template.tags:
            if tag not in self.metadata["tags"]:
                self.metadata["tags"].append(tag)
        
        self._save_metadata()
    
    def _get_template_path(self, template_id: str, output_format: str) -> str:
        """
        テンプレートのファイルパスを取得
        
        Parameters
        ----------
        template_id : str
            テンプレートID
        output_format : str
            出力形式
            
        Returns
        -------
        str
            テンプレートのファイルパス
        """
        return str(self.template_dir / output_format / f"{template_id}.json")
    
    def _get_all_template_files(self) -> List[Path]:
        """
        すべてのテンプレートファイルを取得
        
        Returns
        -------
        List[Path]
            テンプレートファイルのリスト
        """
        template_files = []
        
        for fmt in [e.value for e in TemplateOutputFormat]:
            fmt_dir = self.template_dir / fmt
            if fmt_dir.exists():
                template_files.extend(fmt_dir.glob("*.json"))
        
        return template_files
    
    def create_template(self, 
                       name: str,
                       description: str = "",
                       author: str = "",
                       output_format: Union[TemplateOutputFormat, str] = TemplateOutputFormat.HTML,
                       category: str = "",
                       tags: Optional[List[str]] = None) -> Template:
        """
        新しいテンプレートを作成
        
        Parameters
        ----------
        name : str
            テンプレート名
        description : str, optional
            テンプレートの説明, by default ""
        author : str, optional
            作成者, by default ""
        output_format : Union[TemplateOutputFormat, str], optional
            出力形式, by default TemplateOutputFormat.HTML
        category : str, optional
            カテゴリ, by default ""
        tags : Optional[List[str]], optional
            タグリスト, by default None
        
        Returns
        -------
        Template
            作成されたテンプレート
        """
        template = Template(
            name=name,
            description=description,
            author=author,
            output_format=output_format,
            category=category,
            tags=tags or []
        )
        
        # テンプレートを保存
        self.save_template(template)
        
        return template
    
    def save_template(self, template: Template) -> str:
        """
        テンプレートを保存
        
        Parameters
        ----------
        template : Template
            保存するテンプレート
        
        Returns
        -------
        str
            保存されたテンプレートのファイルパス
        """
        # 保存先のパスを取得
        file_path = Path(self._get_template_path(template.template_id, template.output_format.value))
        
        # テンプレートを保存
        template.save_to_file(file_path)
        
        # メタデータを更新
        self._update_template_metadata(template)
        
        return str(file_path)
    
    def get_template(self, template_id: str) -> Optional[Template]:
        """
        テンプレートをロード
        
        Parameters
        ----------
        template_id : str
            テンプレートID
        
        Returns
        -------
        Optional[Template]
            ロードされたテンプレート、見つからない場合はNone
        """
        # メタデータからテンプレート情報を取得
        template_meta = self.metadata["templates"].get(template_id)
        
        if not template_meta:
            return None
        
        file_path = template_meta.get("file_path")
        
        if not file_path or not Path(file_path).exists():
            return None
        
        try:
            return Template.load_from_file(file_path)
        except Exception as e:
            print(f"テンプレートのロード中にエラーが発生しました: {str(e)}")
            return None
    
    def delete_template(self, template_id: str) -> bool:
        """
        テンプレートを削除
        
        Parameters
        ----------
        template_id : str
            削除するテンプレートID
        
        Returns
        -------
        bool
            削除に成功した場合はTrue、失敗した場合はFalse
        """
        # メタデータからテンプレート情報を取得
        template_meta = self.metadata["templates"].get(template_id)
        
        if not template_meta:
            return False
        
        file_path = template_meta.get("file_path")
        
        if not file_path or not Path(file_path).exists():
            # ファイルが存在しない場合はメタデータからのみ削除
            self.metadata["templates"].pop(template_id, None)
            self._save_metadata()
            return True
        
        try:
            # ファイルを削除
            Path(file_path).unlink()
            
            # メタデータから削除
            self.metadata["templates"].pop(template_id, None)
            self._save_metadata()
            
            return True
        except Exception as e:
            print(f"テンプレートの削除中にエラーが発生しました: {str(e)}")
            return False
    
    def list_templates(self, 
                       output_format: Optional[Union[TemplateOutputFormat, str]] = None,
                       category: Optional[str] = None,
                       tags: Optional[List[str]] = None,
                       search_term: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        テンプレートのリストを取得
        
        Parameters
        ----------
        output_format : Optional[Union[TemplateOutputFormat, str]], optional
            フィルタする出力形式, by default None
        category : Optional[str], optional
            フィルタするカテゴリ, by default None
        tags : Optional[List[str]], optional
            フィルタするタグリスト, by default None
        search_term : Optional[str], optional
            検索キーワード, by default None
        
        Returns
        -------
        List[Dict[str, Any]]
            テンプレート情報のリスト
        """
        templates = []
        
        for template_id, template_meta in self.metadata["templates"].items():
            # フィルタ条件に合致するか確認
            if output_format:
                fmt_value = output_format.value if isinstance(output_format, TemplateOutputFormat) else output_format
                if template_meta.get("output_format") != fmt_value:
                    continue
            
            if category and template_meta.get("category") != category:
                continue
            
            if tags:
                template_tags = template_meta.get("tags", [])
                if not all(tag in template_tags for tag in tags):
                    continue
            
            if search_term:
                search_term = search_term.lower()
                name = template_meta.get("name", "").lower()
                description = template_meta.get("description", "").lower()
                
                if (search_term not in name and
                    search_term not in description):
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
    
    def duplicate_template(self, template_id: str, new_name: Optional[str] = None) -> Optional[Template]:
        """
        テンプレートを複製
        
        Parameters
        ----------
        template_id : str
            複製元のテンプレートID
        new_name : Optional[str], optional
            新しいテンプレート名, by default None
            Noneの場合は「[元の名前]のコピー」を使用
        
        Returns
        -------
        Optional[Template]
            複製されたテンプレート、失敗した場合はNone
        """
        # 元のテンプレートをロード
        template = self.get_template(template_id)
        
        if not template:
            return None
        
        # 新しいテンプレート名を設定
        if new_name is None:
            new_name = f"{template.name}のコピー"
        
        # 新しいテンプレートを作成
        new_template = Template(
            name=new_name,
            description=template.description,
            author=template.author,
            output_format=template.output_format,
            category=template.category,
            tags=template.tags.copy(),
            metadata=template.metadata.copy(),
            global_styles=template.global_styles.copy()
        )
        
        # セクションを複製
        for section in template.sections:
            new_template.add_section_from_dict(section.to_dict())
        
        # 新しいテンプレートを保存
        self.save_template(new_template)
        
        return new_template
    
    def import_template(self, file_path: Union[str, Path]) -> Optional[Template]:
        """
        テンプレートファイルをインポート
        
        Parameters
        ----------
        file_path : Union[str, Path]
            インポートするテンプレートファイルのパス
        
        Returns
        -------
        Optional[Template]
            インポートされたテンプレート、失敗した場合はNone
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            print(f"ファイルが見つかりません: {file_path}")
            return None
        
        try:
            # テンプレートをロード
            template = Template.load_from_file(file_path)
            
            # テンプレートを保存
            self.save_template(template)
            
            return template
        except Exception as e:
            print(f"テンプレートのインポート中にエラーが発生しました: {str(e)}")
            return None
    
    def export_template(self, template_id: str, export_path: Union[str, Path]) -> bool:
        """
        テンプレートをエクスポート
        
        Parameters
        ----------
        template_id : str
            エクスポートするテンプレートID
        export_path : Union[str, Path]
            エクスポート先のパス
        
        Returns
        -------
        bool
            エクスポートに成功した場合はTrue、失敗した場合はFalse
        """
        # テンプレートをロード
        template = self.get_template(template_id)
        
        if not template:
            return False
        
        export_path = Path(export_path)
        
        # ディレクトリの場合は、テンプレート名をファイル名として使用
        if export_path.is_dir():
            sanitized_name = template.name.replace(" ", "_").replace("/", "_").replace("\\", "_")
            export_path = export_path / f"{sanitized_name}_{template.template_id}.json"
        
        try:
            # テンプレートを保存
            template.save_to_file(export_path)
            return True
        except Exception as e:
            print(f"テンプレートのエクスポート中にエラーが発生しました: {str(e)}")
            return False
    
    def create_standard_templates(self) -> List[str]:
        """
        標準テンプレートを作成
        
        Returns
        -------
        List[str]
            作成されたテンプレートのIDリスト
        """
        created_template_ids = []
        
        # 基本テンプレート
        basic_template = self.create_template(
            name="基本レポート",
            description="セッションの基本情報と主要指標を表示する標準テンプレート",
            author="System",
            category="基本",
            tags=["標準", "基本"]
        )
        
        # 基本レイアウトの作成（ヘッダー、コンテンツ、フッター）
        header_section = Section(
            section_type="header",
            name="header",
            title="ヘッダー",
            description="レポートのヘッダーセクション",
            order=0
        )
        
        summary_section = Section(
            section_type="content",
            name="summary",
            title="セッションサマリー",
            description="セッションの基本情報と主要指標",
            order=1
        )
        
        wind_section = Section(
            section_type="content",
            name="wind_analysis",
            title="風向風速分析",
            description="風向風速の分析結果",
            order=2
        )
        
        strategy_section = Section(
            section_type="content",
            name="strategy_points",
            title="戦略ポイント",
            description="重要な戦略的決断ポイント",
            order=3
        )
        
        footer_section = Section(
            section_type="footer",
            name="footer",
            title="フッター",
            description="レポートのフッターセクション",
            order=4
        )
        
        # セクションをテンプレートに追加
        basic_template.add_section(header_section)
        basic_template.add_section(summary_section)
        basic_template.add_section(wind_section)
        basic_template.add_section(strategy_section)
        basic_template.add_section(footer_section)
        
        # テンプレートを保存
        self.save_template(basic_template)
        created_template_ids.append(basic_template.template_id)
        
        # 詳細分析テンプレート
        detailed_template = self.create_template(
            name="詳細分析レポート",
            description="詳細な分析結果とグラフを含む高度なレポートテンプレート",
            author="System",
            category="詳細",
            tags=["標準", "詳細", "分析"]
        )
        
        # 詳細テンプレートにセクションを追加
        detailed_template.add_section(header_section)
        detailed_template.add_section(summary_section)
        detailed_template.add_section(wind_section)
        detailed_template.add_section(strategy_section)
        
        # パフォーマンス分析セクション
        performance_section = Section(
            section_type="content",
            name="performance",
            title="パフォーマンス分析",
            description="詳細なパフォーマンス分析結果",
            order=4
        )
        
        # 比較分析セクション
        comparison_section = Section(
            section_type="content",
            name="comparison",
            title="比較分析",
            description="過去のセッションとの比較分析",
            order=5
        )
        
        detailed_template.add_section(performance_section)
        detailed_template.add_section(comparison_section)
        detailed_template.add_section(footer_section)
        
        # テンプレートを保存
        self.save_template(detailed_template)
        created_template_ids.append(detailed_template.template_id)
        
        # プレゼンテーションテンプレート
        presentation_template = self.create_template(
            name="プレゼンテーションレポート",
            description="視覚的な要素を重視したプレゼンテーション用テンプレート",
            author="System",
            output_format=TemplateOutputFormat.HTML,
            category="プレゼンテーション",
            tags=["標準", "プレゼンテーション", "視覚化"]
        )
        
        # カバーページセクション
        cover_section = Section(
            section_type="cover",
            name="cover",
            title="カバーページ",
            description="レポートの表紙",
            order=0
        )
        
        # 主要グラフセクション
        charts_section = Section(
            section_type="content",
            name="key_charts",
            title="主要グラフ",
            description="重要なデータを視覚化したグラフ",
            order=1,
            layout={"columns": 2}
        )
        
        # ハイライトセクション
        highlights_section = Section(
            section_type="content",
            name="highlights",
            title="ハイライト",
            description="セッションの重要なポイント",
            order=2
        )
        
        presentation_template.add_section(cover_section)
        presentation_template.add_section(charts_section)
        presentation_template.add_section(highlights_section)
        presentation_template.add_section(wind_section)
        presentation_template.add_section(strategy_section)
        presentation_template.add_section(footer_section)
        
        # テンプレートを保存
        self.save_template(presentation_template)
        created_template_ids.append(presentation_template.template_id)
        
        # コーチング用テンプレート
        coaching_template = self.create_template(
            name="コーチング用レポート",
            description="改善点と次のステップにフォーカスしたコーチング用テンプレート",
            author="System",
            category="コーチング",
            tags=["専門", "コーチング", "改善"]
        )
        
        # 強みと弱みセクション
        strengths_weaknesses_section = Section(
            section_type="content",
            name="strengths_weaknesses",
            title="強みと弱み",
            description="セッションで示された強みと改善が必要な点",
            order=2
        )
        
        # 改善計画セクション
        improvement_section = Section(
            section_type="content",
            name="improvement_plan",
            title="改善計画",
            description="具体的な改善ポイントと次のステップ",
            order=3
        )
        
        coaching_template.add_section(header_section)
        coaching_template.add_section(summary_section)
        coaching_template.add_section(strengths_weaknesses_section)
        coaching_template.add_section(improvement_section)
        coaching_template.add_section(footer_section)
        
        # テンプレートを保存
        self.save_template(coaching_template)
        created_template_ids.append(coaching_template.template_id)
        
        return created_template_ids
    
    def rebuild_metadata(self) -> None:
        """
        メタデータを再構築
        
        テンプレートファイルからメタデータを再構築します。
        """
        self.metadata = {"templates": {}, "categories": [], "tags": []}
        
        # すべてのテンプレートファイルを取得
        template_files = self._get_all_template_files()
        
        for file_path in template_files:
            try:
                # テンプレートをロード
                template = Template.load_from_file(file_path)
                
                # メタデータを更新
                self._update_template_metadata(template)
            except Exception as e:
                print(f"テンプレートのロード中にエラーが発生しました: {file_path} - {str(e)}")
        
        # メタデータを保存
        self._save_metadata()
