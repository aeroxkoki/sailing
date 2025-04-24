# -*- coding: utf-8 -*-
"""
sailing_data_processor.exporters.json_exporter

セッション結果をJSON形式でエクスポートするモジュール
"""

import os
import json
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import datetime

from sailing_data_processor.project.session_model import SessionModel, SessionResult
from sailing_data_processor.exporters.session_exporter import SessionExporter


class JSONExporter(SessionExporter):
    """
    JSON形式でセッション結果をエクスポートするクラス
    """
    
    def __init__(self, template_manager=None, config: Optional[Dict[str, Any]] = None):
        """
        初期化
        
        Parameters
        ----------
        template_manager : Optional, default=None
            テンプレート管理クラスのインスタンス
        config : Optional[Dict[str, Any]], default=None
            エクスポーター設定
        """
        super().__init__(template_manager, config)
    
    def export_session(self, session: SessionModel, output_path: str, 
                       template: str = "default", options: Dict[str, Any] = None) -> str:
        """
        単一セッションをJSONでエクスポート
        
        Parameters
        ----------
        session : SessionModel
            エクスポートするセッション
        output_path : str
            出力先パス
        template : str, optional
            使用するテンプレート名, by default "default"
        options : Dict[str, Any], optional
            エクスポートオプション, by default None
            
        Returns
        -------
        str
            エクスポートされたファイルのパス
        """
        options = options or {}
        
        # テンプレートの取得
        template_data = {}
        if self.template_manager:
            try:
                template_data = self.template_manager.get_template(template, "json")
            except Exception as e:
                self.warnings.append(f"テンプレートの読み込みに失敗しました: {e}")
                # デフォルト設定で続行
        
        # 出力先ディレクトリの確認
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # JSONデータの生成
        json_data = self._generate_json_data(session, template_data, options)
        
        # エクスポートオプションの設定
        indent = template_data.get("metadata", {}).get("indent", 2)
        ensure_ascii = False
        
        # JSONファイルの保存
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=indent, ensure_ascii=ensure_ascii)
        except Exception as e:
            self.errors.append(f"JSONファイルの保存に失敗しました: {e}")
            raise
        
        return output_path
    
    def export_multiple_sessions(self, sessions: List[SessionModel], output_dir: str,
                                template: str = "default", options: Dict[str, Any] = None) -> List[str]:
        """
        複数セッションをJSONでエクスポート
        
        Parameters
        ----------
        sessions : List[SessionModel]
            エクスポートするセッションのリスト
        output_dir : str
            出力先ディレクトリ
        template : str, optional
            使用するテンプレート名, by default "default"
        options : Dict[str, Any], optional
            エクスポートオプション, by default None
            
        Returns
        -------
        List[str]
            エクスポートされたファイルのパスのリスト
        """
        options = options or {}
        export_files = []
        
        # 出力ディレクトリの確認
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # 単一ファイルとしてエクスポートする場合
        if "export_as_single_file" in options and options["export_as_single_file"]:
            # すべてのセッションのデータを収集
            all_sessions_data = []
            for session in sessions:
                # テンプレートの取得（各セッションで同じテンプレートを使用）
                template_data = {}
                if self.template_manager:
                    try:
                        template_data = self.template_manager.get_template(template, "json")
                    except Exception:
                        pass
                
                # JSONデータの生成
                session_data = self._generate_json_data(session, template_data, options)
                all_sessions_data.append(session_data)
            
            # タイムスタンプを含むファイル名を生成
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"sessions_export_{timestamp}.json"
            output_path = os.path.join(output_dir, filename)
            
            # JSONファイルの保存
            try:
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(all_sessions_data, f, indent=2, ensure_ascii=False)
                export_files.append(output_path)
            except Exception as e:
                self.errors.append(f"複数セッションの一括エクスポートに失敗しました: {e}")
        else:
            # 各セッションを個別にエクスポート
            for session in sessions:
                try:
                    # ファイル名の生成
                    filename = self.generate_export_filename(session, "json")
                    output_path = os.path.join(output_dir, filename)
                    
                    # エクスポート実行
                    exported_file = self.export_session(session, output_path, template, options)
                    export_files.append(exported_file)
                except Exception as e:
                    self.errors.append(f"セッション '{session.name}' のエクスポートに失敗しました: {e}")
        
        return export_files
    
    def _generate_json_data(self, session: SessionModel, template_data: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        """
        セッションをJSONデータに変換
        
        Parameters
        ----------
        session : SessionModel
            セッション
        template_data : Dict[str, Any]
            テンプレートデータ
        options : Dict[str, Any]
            エクスポートオプション
            
        Returns
        -------
        Dict[str, Any]
            JSON用のデータ辞書
        """
        # テンプレートからセクション設定を取得
        sections = template_data.get("sections", [])
        
        # エクスポートするセクションを決定
        export_metadata = True
        export_session_data = True
        export_results = True
        include_all_versions = False
        
        for section in sections:
            name = section.get("name", "")
            enabled = section.get("enabled", True)
            
            if name == "metadata":
                export_metadata = enabled
            elif name == "session_data":
                export_session_data = enabled
            elif name == "results":
                export_results = enabled
                include_all_versions = section.get("include_all_versions", False)
        
        # オプションで上書き
        if "include_metadata" in options:
            export_metadata = options["include_metadata"]
        if "include_session_data" in options:
            export_session_data = options["include_session_data"]
        if "include_results" in options:
            export_results = options["include_results"]
        if "include_all_versions" in options:
            include_all_versions = options["include_all_versions"]
        
        # 基本データ構造
        json_data = {}
        
        # エクスポート情報
        json_data["export_info"] = {
            "timestamp": datetime.datetime.now().isoformat(),
            "exporter": "JSONExporter",
            "version": "1.0"
        }
        
        # セッションのメタデータ
        if export_metadata:
            json_data["metadata"] = {
                "session_id": session.session_id,
                "name": session.name,
                "description": session.description,
                "purpose": session.purpose,
                "category": session.category,
                "status": session.status,
                "tags": session.tags,
                "rating": session.rating,
                "event_date": session.event_date,
                "location": session.location,
                "importance": session.importance,
                "created_at": session.created_at,
                "updated_at": session.updated_at
            }
            
            # その他のメタデータ（MetaDataセクションが部分的にエクスポート対象の場合も必要）
            if hasattr(session, "completion_percentage"):
                json_data["metadata"]["completion_percentage"] = session.completion_percentage
            
            # 追加のメタデータ
            additional_metadata = {}
            for key, value in session.metadata.items():
                if key not in json_data["metadata"]:
                    additional_metadata[key] = value
            
            if additional_metadata:
                json_data["metadata"]["additional_metadata"] = additional_metadata
        
        # セッションデータ
        if export_session_data:
            json_data["session_data"] = session.to_dict()
        
        # 結果データ（セッション結果マネージャーなどがあればそこから結果を取得し追加）
        if export_results and hasattr(session, "results") and session.results:
            json_data["results"] = session.results
            
            # 結果の詳細データは現在アクセスできないため、セッションの結果IDのリストのみを含める
            json_data["results_info"] = {
                "count": len(session.results),
                "ids": session.results,
                "note": "詳細な結果データを取得するには、セッション結果マネージャーを使用してください。"
            }
        
        return json_data