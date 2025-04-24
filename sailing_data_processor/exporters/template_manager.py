# -*- coding: utf-8 -*-
"""
sailing_data_processor.exporters.template_manager

レポートテンプレート管理のためのモジュール
"""

from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import os
import json
import datetime
import shutil


class TemplateManager:
    """
    レポートテンプレート管理クラス
    
    レポートテンプレートのロード、保存、管理を行います。
    """
    
    def __init__(self, template_dir: Union[str, Path] = None):
        """
        初期化
        
        Parameters
        ----------
        template_dir : Union[str, Path], optional
            テンプレートディレクトリ、by default None
            Noneの場合はデフォルトディレクトリを使用
        """
        if template_dir is None:
            # デフォルトのテンプレートディレクトリを設定
            module_dir = Path(__file__).parent
            template_dir = module_dir / "templates"
        
        self.template_dir = Path(template_dir)
        self.template_dir.mkdir(parents=True, exist_ok=True)
        
        # テンプレートフォーマットごとのディレクトリを作成
        self.formats = ["pdf", "html", "csv", "json"]
        for fmt in self.formats:
            fmt_dir = self.template_dir / fmt
            fmt_dir.mkdir(exist_ok=True)
            
            # デフォルトテンプレートが存在しない場合は作成
            default_template = fmt_dir / "default.json"
            if not default_template.exists():
                self._create_default_template(fmt, default_template)
    
    def _create_default_template(self, format_name: str, template_path: Path) -> None:
        """
        デフォルトテンプレートを作成
        
        Parameters
        ----------
        format_name : str
            テンプレートフォーマット
        template_path : Path
            テンプレートファイルパス
        """
        # 各フォーマットに適したデフォルトテンプレート
        default_template_data = {
            "pdf": {
                "name": "デフォルトPDFテンプレート",
                "description": "標準的なPDFレポートテンプレート",
                "created_at": datetime.datetime.now().isoformat(),
                "updated_at": datetime.datetime.now().isoformat(),
                "format": "pdf",
                "version": "1.0",
                "metadata": {
                    "header": {
                        "include_logo": True,
                        "include_title": True,
                        "include_date": True
                    },
                    "footer": {
                        "include_page_number": True,
                        "include_timestamp": True
                    }
                },
                "sections": [
                    {
                        "name": "summary",
                        "title": "セッションサマリー",
                        "enabled": True,
                        "order": 1
                    },
                    {
                        "name": "metadata",
                        "title": "メタデータ",
                        "enabled": True,
                        "order": 2
                    },
                    {
                        "name": "wind_analysis",
                        "title": "風向風速分析",
                        "enabled": True,
                        "order": 3
                    },
                    {
                        "name": "strategy_points",
                        "title": "戦略ポイント",
                        "enabled": True,
                        "order": 4
                    },
                    {
                        "name": "performance",
                        "title": "パフォーマンス分析",
                        "enabled": True,
                        "order": 5
                    }
                ],
                "styles": {
                    "font_family": "Arial, Helvetica, sans-serif",
                    "base_font_size": 10,
                    "h1_font_size": 18,
                    "h2_font_size": 16,
                    "h3_font_size": 14,
                    "colors": {
                        "primary": "#1565C0",
                        "secondary": "#0D47A1",
                        "text": "#212121",
                        "background": "#FFFFFF",
                        "accent": "#4CAF50"
                    }
                }
            },
            "html": {
                "name": "デフォルトHTMLテンプレート",
                "description": "標準的なHTMLレポートテンプレート",
                "created_at": datetime.datetime.now().isoformat(),
                "updated_at": datetime.datetime.now().isoformat(),
                "format": "html",
                "version": "1.0",
                "metadata": {
                    "include_interactive": True,
                    "include_navigation": True,
                    "include_print_css": True
                },
                "sections": [
                    {
                        "name": "summary",
                        "title": "セッションサマリー",
                        "enabled": True,
                        "order": 1
                    },
                    {
                        "name": "metadata",
                        "title": "メタデータ",
                        "enabled": True,
                        "order": 2
                    },
                    {
                        "name": "wind_analysis",
                        "title": "風向風速分析",
                        "enabled": True,
                        "order": 3,
                        "interactive": True
                    },
                    {
                        "name": "strategy_points",
                        "title": "戦略ポイント",
                        "enabled": True,
                        "order": 4,
                        "interactive": True
                    },
                    {
                        "name": "performance",
                        "title": "パフォーマンス分析",
                        "enabled": True,
                        "order": 5,
                        "interactive": True
                    }
                ],
                "styles": {
                    "css_framework": "bootstrap",
                    "theme": "light",
                    "custom_css": ""
                }
            },
            "csv": {
                "name": "デフォルトCSVテンプレート",
                "description": "標準的なCSVエクスポートテンプレート",
                "created_at": datetime.datetime.now().isoformat(),
                "updated_at": datetime.datetime.now().isoformat(),
                "format": "csv",
                "version": "1.0",
                "metadata": {
                    "include_headers": True,
                    "delimiter": ",",
                    "quotechar": "\"",
                    "encoding": "utf-8",
                    "include_bom": True
                },
                "sections": [
                    {
                        "name": "metadata",
                        "enabled": True,
                        "fields": ["name", "description", "category", "tags", "status", "rating", "created_at", "updated_at", "event_date", "location"]
                    },
                    {
                        "name": "wind_data",
                        "enabled": True,
                        "fields": ["timestamp", "lat", "lon", "wind_speed", "wind_direction"]
                    },
                    {
                        "name": "strategy_points",
                        "enabled": True,
                        "fields": ["timestamp", "lat", "lon", "type", "score", "description"]
                    }
                ]
            },
            "json": {
                "name": "デフォルトJSONテンプレート",
                "description": "標準的なJSONエクスポートテンプレート",
                "created_at": datetime.datetime.now().isoformat(),
                "updated_at": datetime.datetime.now().isoformat(),
                "format": "json",
                "version": "1.0",
                "metadata": {
                    "pretty_print": True,
                    "indent": 2,
                    "encoding": "utf-8"
                },
                "sections": [
                    {
                        "name": "metadata",
                        "enabled": True
                    },
                    {
                        "name": "session_data",
                        "enabled": True
                    },
                    {
                        "name": "results",
                        "enabled": True,
                        "include_all_versions": False
                    }
                ]
            }
        }
        
        # 該当するフォーマットのデフォルトテンプレートを作成
        if format_name in default_template_data:
            with open(template_path, "w", encoding="utf-8") as f:
                json.dump(default_template_data[format_name], f, ensure_ascii=False, indent=2)
    
    def get_template(self, template_name: str, format_name: str) -> Dict[str, Any]:
        """
        テンプレートを取得
        
        Parameters
        ----------
        template_name : str
            テンプレート名
        format_name : str
            テンプレートフォーマット
            
        Returns
        -------
        Dict[str, Any]
            テンプレートデータ
        
        Raises
        ------
        FileNotFoundError
            テンプレートが見つからない場合
        """
        if format_name not in self.formats:
            raise ValueError(f"Unsupported format: {format_name}. Available formats: {', '.join(self.formats)}")
        
        template_path = self.template_dir / format_name / f"{template_name}.json"
        
        if not template_path.exists():
            # テンプレートが見つからない場合はデフォルトを使用
            template_path = self.template_dir / format_name / "default.json"
            if not template_path.exists():
                raise FileNotFoundError(f"Template not found: {template_name}.json and default.json for format {format_name}")
        
        with open(template_path, "r", encoding="utf-8") as f:
            template_data = json.load(f)
        
        return template_data
    
    def save_template(self, template_data: Dict[str, Any], template_name: str = None) -> str:
        """
        テンプレートを保存
        
        Parameters
        ----------
        template_data : Dict[str, Any]
            テンプレートデータ
        template_name : str, optional
            テンプレート名, by default None
            Noneの場合はテンプレートデータ内の名前を使用
            
        Returns
        -------
        str
            保存されたテンプレートのパス
        
        Raises
        ------
        ValueError
            テンプレートデータにフォーマットが含まれていない場合
        """
        if "format" not in template_data:
            raise ValueError("Template data must include 'format' field")
        
        format_name = template_data["format"]
        if format_name not in self.formats:
            raise ValueError(f"Unsupported format: {format_name}. Available formats: {', '.join(self.formats)}")
        
        if template_name is None:
            if "name" in template_data:
                # 名前からファイル名を生成
                template_name = template_data["name"].lower().replace(" ", "_")
            else:
                # 一意のファイル名を生成
                template_name = f"template_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        template_path = self.template_dir / format_name / f"{template_name}.json"
        
        # 更新日時を設定
        template_data["updated_at"] = datetime.datetime.now().isoformat()
        if "created_at" not in template_data:
            template_data["created_at"] = template_data["updated_at"]
        
        with open(template_path, "w", encoding="utf-8") as f:
            json.dump(template_data, f, ensure_ascii=False, indent=2)
        
        return str(template_path)
    
    def list_templates(self, format_name: str = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        テンプレート一覧を取得
        
        Parameters
        ----------
        format_name : str, optional
            テンプレートフォーマット, by default None
            Noneの場合はすべてのフォーマットのテンプレートを取得
            
        Returns
        -------
        Dict[str, List[Dict[str, Any]]]
            フォーマットごとのテンプレート情報リスト
        """
        result = {}
        
        formats_to_check = [format_name] if format_name else self.formats
        
        for fmt in formats_to_check:
            if fmt not in self.formats:
                continue
                
            format_dir = self.template_dir / fmt
            result[fmt] = []
            
            # フォーマットディレクトリ内のJSONファイルをチェック
            if format_dir.exists():
                for template_file in format_dir.glob("*.json"):
                    try:
                        with open(template_file, "r", encoding="utf-8") as f:
                            template_data = json.load(f)
                            
                            # 基本情報のみ含める
                            template_info = {
                                "name": template_data.get("name", template_file.stem),
                                "description": template_data.get("description", ""),
                                "filename": template_file.name,
                                "created_at": template_data.get("created_at", ""),
                                "updated_at": template_data.get("updated_at", ""),
                                "version": template_data.get("version", "1.0")
                            }
                            result[fmt].append(template_info)
                    except (json.JSONDecodeError, Exception) as e:
                        # 読み込みエラーの場合はスキップ
                        pass
        
        return result
    
    def delete_template(self, template_name: str, format_name: str) -> bool:
        """
        テンプレートを削除
        
        Parameters
        ----------
        template_name : str
            テンプレート名
        format_name : str
            テンプレートフォーマット
            
        Returns
        -------
        bool
            削除に成功した場合True
        """
        if format_name not in self.formats:
            return False
        
        template_path = self.template_dir / format_name / f"{template_name}.json"
        
        if not template_path.exists():
            return False
        
        # デフォルトテンプレートは削除できない
        if template_name == "default":
            return False
        
        try:
            template_path.unlink()
            return True
        except Exception:
            return False
    
    def duplicate_template(self, template_name: str, format_name: str, new_template_name: str = None) -> Optional[str]:
        """
        テンプレートを複製
        
        Parameters
        ----------
        template_name : str
            複製元テンプレート名
        format_name : str
            テンプレートフォーマット
        new_template_name : str, optional
            新しいテンプレート名, by default None
            Noneの場合は「コピー_(元の名前)」を使用
            
        Returns
        -------
        Optional[str]
            複製されたテンプレートのパス、失敗した場合はNone
        """
        try:
            # 元のテンプレートを取得
            template_data = self.get_template(template_name, format_name)
            
            # 新しい名前を設定
            if new_template_name is None:
                template_display_name = template_data.get("name", template_name)
                new_template_display_name = f"コピー_{template_display_name}"
                new_template_name = new_template_display_name.lower().replace(" ", "_")
            else:
                new_template_display_name = new_template_name
            
            # テンプレートデータを更新
            template_data["name"] = new_template_display_name
            template_data["created_at"] = datetime.datetime.now().isoformat()
            template_data["updated_at"] = template_data["created_at"]
            
            # 新しいテンプレートとして保存
            return self.save_template(template_data, new_template_name)
        except Exception as e:
            print(f"Error duplicating template: {e}")
            return None
    
    def import_template(self, template_file_path: Union[str, Path], format_name: str = None) -> Optional[str]:
        """
        外部ファイルからテンプレートをインポート
        
        Parameters
        ----------
        template_file_path : Union[str, Path]
            インポートするテンプレートファイルのパス
        format_name : str, optional
            テンプレートフォーマット, by default None
            Noneの場合はテンプレートデータから推測
            
        Returns
        -------
        Optional[str]
            インポートされたテンプレートのパス、失敗した場合はNone
        """
        template_file_path = Path(template_file_path)
        
        if not template_file_path.exists():
            print(f"Template file not found: {template_file_path}")
            return None
        
        try:
            # テンプレートファイルを読み込み
            with open(template_file_path, "r", encoding="utf-8") as f:
                template_data = json.load(f)
            
            # フォーマットを確認/推測
            if format_name is None:
                if "format" in template_data:
                    format_name = template_data["format"]
                else:
                    # ファイル名からフォーマットを推測
                    for fmt in self.formats:
                        if fmt in template_file_path.stem.lower():
                            format_name = fmt
                            break
            
            if format_name not in self.formats:
                print(f"Unsupported format: {format_name}. Available formats: {', '.join(self.formats)}")
                return None
            
            # テンプレートデータにフォーマットを設定
            template_data["format"] = format_name
            
            # テンプレート名を設定
            template_name = template_data.get("name", "").lower().replace(" ", "_")
            if not template_name:
                template_name = template_file_path.stem.lower().replace(" ", "_")
            
            # 重複を避けるためにタイムスタンプを追加
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            template_name = f"{template_name}_{timestamp}"
            
            # テンプレートを保存
            return self.save_template(template_data, template_name)
        except Exception as e:
            print(f"Error importing template: {e}")
            return None
    
    def export_template(self, template_name: str, format_name: str, output_path: Union[str, Path]) -> bool:
        """
        テンプレートを外部ファイルにエクスポート
        
        Parameters
        ----------
        template_name : str
            エクスポートするテンプレート名
        format_name : str
            テンプレートフォーマット
        output_path : Union[str, Path]
            出力先パス
            
        Returns
        -------
        bool
            エクスポートに成功した場合True
        """
        if format_name not in self.formats:
            print(f"Unsupported format: {format_name}. Available formats: {', '.join(self.formats)}")
            return False
        
        template_path = self.template_dir / format_name / f"{template_name}.json"
        
        if not template_path.exists():
            print(f"Template not found: {template_name}.json for format {format_name}")
            return False
        
        try:
            output_path = Path(output_path)
            
            # ディレクトリが指定された場合、テンプレート名をファイル名として使用
            if output_path.is_dir():
                output_path = output_path / f"{template_name}_{format_name}.json"
            
            # テンプレートファイルをコピー
            shutil.copy2(template_path, output_path)
            return True
        except Exception as e:
            print(f"Error exporting template: {e}")
            return False
