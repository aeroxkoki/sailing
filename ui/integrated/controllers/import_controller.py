# -*- coding: utf-8 -*-
"""
ui.integrated.controllers.import_controller

インポート処理のコントローラークラス
"""

import streamlit as st
import pandas as pd
import tempfile
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union

from sailing_data_processor.importers.importer_factory import ImporterFactory
from sailing_data_processor.data_model.container import GPSDataContainer
from sailing_data_processor.project.project_manager import ProjectManager
from sailing_data_processor.project.session_manager import SessionManager
from sailing_data_processor.validation.data_validator import DataValidator


class ImportController:
    """
    データインポート処理を管理するコントローラークラス
    
    インポートプロセスの状態管理、インポーターの選択、エラーハンドリングなどを担当
    """
    
    def __init__(self, key_prefix: str = "import_controller"):
        """
        コントローラーの初期化
        
        Parameters
        ----------
        key_prefix : str, optional
            セッション状態に保存する際のキープレフィックス, by default "import_controller"
        """
        self.key_prefix = key_prefix
        
        # セッション状態の初期化
        if f"{self.key_prefix}_state" not in st.session_state:
            st.session_state[f"{self.key_prefix}_state"] = {
                "current_step": "init",
                "file_format": None,
                "import_settings": {},
                "column_mapping": {},
                "metadata": {},
                "errors": [],
                "warnings": [],
                "import_history": [],
                "imported_container": None
            }
        
        # インポーターファクトリーの初期化
        self.importer_factory = ImporterFactory()
        
        # データ検証器の初期化
        self.validator = DataValidator()
        
        # プロジェクトマネージャーの初期化
        self.project_manager = None
    
    def get_state(self) -> Dict[str, Any]:
        """
        現在の状態を取得
        
        Returns
        -------
        Dict[str, Any]
            コントローラーの現在の状態
        """
        return st.session_state[f"{self.key_prefix}_state"]
    
    def set_state(self, state: Dict[str, Any]):
        """
        状態を設定
        
        Parameters
        ----------
        state : Dict[str, Any]
            設定する状態
        """
        st.session_state[f"{self.key_prefix}_state"] = state
    
    def update_state(self, **kwargs):
        """
        状態を部分更新
        
        Parameters
        ----------
        **kwargs
            更新する状態のキーと値
        """
        state = self.get_state()
        for key, value in kwargs.items():
            state[key] = value
        self.set_state(state)
    
    def reset_state(self):
        """状態をリセット"""
        st.session_state[f"{self.key_prefix}_state"] = {
            "current_step": "init",
            "file_format": None,
            "import_settings": {},
            "column_mapping": {},
            "metadata": {},
            "errors": [],
            "warnings": [],
            "import_history": [],
            "imported_container": None
        }
    
    def detect_file_format(self, file_obj) -> Optional[str]:
        """
        ファイル形式を検出
        
        Parameters
        ----------
        file_obj : UploadedFile
            アップロードされたファイルオブジェクト
            
        Returns
        -------
        Optional[str]
            検出されたファイル形式 (CSV, GPX, TCX, FIT など)
        """
        # 拡張子による検出
        filename = file_obj.name.lower()
        
        if filename.endswith('.csv'):
            return "CSV"
        elif filename.endswith('.gpx'):
            return "GPX"
        elif filename.endswith('.tcx'):
            return "TCX"
        elif filename.endswith('.fit'):
            return "FIT"
        
        # MIMEタイプによる検出
        mime_type = getattr(file_obj, 'type', '').lower()
        
        if mime_type in ['text/csv', 'application/csv']:
            return "CSV"
        elif mime_type in ['application/gpx+xml', 'application/xml'] and filename.endswith('.gpx'):
            return "GPX"
        elif mime_type in ['application/tcx+xml', 'application/xml'] and filename.endswith('.tcx'):
            return "TCX"
        elif mime_type in ['application/octet-stream'] and filename.endswith('.fit'):
            return "FIT"
        
        # ファイル内容による検出
        try:
            file_obj.seek(0)
            header = file_obj.read(128)
            file_obj.seek(0)
            
            if isinstance(header, bytes):
                header_str = header.decode('utf-8', errors='ignore')
            else:
                header_str = header
            
            # GPXファイルはXMLファイルで、通常「<gpx」で始まる
            if '<gpx' in header_str.lower():
                return "GPX"
            
            # TCXファイルはXMLファイルで、通常「<TrainingCenterDatabase」を含む
            if '<trainingcenterdatabase' in header_str.lower():
                return "TCX"
            
            # CSVファイルはテキストファイルで、通常は最初の行に列名がある
            if ',' in header_str and len(header_str.split(',')) > 1:
                return "CSV"
        
        except Exception as e:
            self.add_warning(f"ファイル形式の自動検出中にエラーが発生しました: {e}")
        
        return None
    
    def import_data(self, 
                   file_obj,
                   file_format: str, 
                   import_settings: Dict[str, Any], 
                   column_mapping: Dict[str, str] = None, 
                   metadata: Dict[str, Any] = None,
                   run_validation: bool = False
                   ) -> Optional[GPSDataContainer]:
        """
        データをインポート
        
        Parameters
        ----------
        file_obj : UploadedFile
            アップロードされたファイルオブジェクト
        file_format : str
            ファイル形式 (CSV, GPX, TCX, FIT など)
        import_settings : Dict[str, Any]
            インポート設定
        column_mapping : Dict[str, str], optional
            列マッピング (CSVの場合), by default None
        metadata : Dict[str, Any], optional
            メタデータ, by default None
        run_validation : bool, optional
            インポート後に検証を実行するかどうか, by default False
            
        Returns
        -------
        Optional[GPSDataContainer]
            インポートされたデータコンテナ (失敗した場合はNone)
        """
        # エラーと警告をクリア
        self.clear_errors_warnings()
        
        if file_obj is None:
            self.add_error("ファイルが指定されていません。")
            return None
        
        if file_format is None:
            self.add_error("ファイル形式が指定されていません。")
            return None
        
        # CSVの場合は列マッピングが必要
        if file_format == "CSV" and (column_mapping is None or not column_mapping):
            self.add_error("CSVファイルには列マッピングが必要です。")
            return None
        
        # アップロードされたファイルをテンポラリファイルに保存
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{Path(file_obj.name).suffix}") as tmp:
            tmp.write(file_obj.getvalue())
            tmp_path = tmp.name
        
        try:
            # インポーター設定
            config = import_settings.copy()
            if file_format == "CSV" and column_mapping:
                config["column_mapping"] = column_mapping
            
            # インポーターを取得
            importer = self.importer_factory.get_importer(file_format, config)
            
            if importer is None:
                self.add_error(f"サポートされていないファイル形式: {file_format}")
                return None
            
            # インポートを実行
            container = importer.import_data(tmp_path, metadata or {})
            
            # エラーと警告を保存
            for error in importer.get_errors():
                self.add_error(error)
            
            for warning in importer.get_warnings():
                self.add_warning(warning)
            
            # インポート履歴に追加
            if container:
                self.add_to_import_history(file_obj.name, file_format, container)
                
                # 検証フラグが設定されている場合、自動的に検証を実行
                if run_validation:
                    validation_results = self.run_validation_after_import(container)
                    # 検証結果をログに出力（デバッグ用）
                    validation_passed, _ = validation_results
                    if validation_passed:
                        self.add_warning("データ検証に成功しました。")
                    else:
                        self.add_warning("データ検証で問題が見つかりました。データ検証ページで詳細を確認してください。")
            
            return container
        
        except Exception as e:
            self.add_error(f"データのインポート中にエラーが発生しました: {str(e)}")
            return None
        
        finally:
            # テンポラリファイルを削除
            try:
                os.unlink(tmp_path)
            except:
                pass
    
    def add_error(self, error_message: str):
        """
        エラーメッセージを追加
        
        Parameters
        ----------
        error_message : str
            エラーメッセージ
        """
        state = self.get_state()
        state["errors"].append(error_message)
        self.set_state(state)
    
    def add_warning(self, warning_message: str):
        """
        警告メッセージを追加
        
        Parameters
        ----------
        warning_message : str
            警告メッセージ
        """
        state = self.get_state()
        state["warnings"].append(warning_message)
        self.set_state(state)
    
    def clear_errors_warnings(self):
        """エラーと警告をクリア"""
        state = self.get_state()
        state["errors"] = []
        state["warnings"] = []
        self.set_state(state)
    
    def get_errors(self) -> List[str]:
        """
        エラーメッセージを取得
        
        Returns
        -------
        List[str]
            エラーメッセージのリスト
        """
        return self.get_state()["errors"]
    
    def get_warnings(self) -> List[str]:
        """
        警告メッセージを取得
        
        Returns
        -------
        List[str]
            警告メッセージのリスト
        """
        return self.get_state()["warnings"]
    
    def validate_data(self, container: GPSDataContainer) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        データを検証
        
        Parameters
        ----------
        container : GPSDataContainer
            検証するデータコンテナ
            
        Returns
        -------
        Tuple[bool, List[Dict[str, Any]]]
            (検証結果, 詳細な検証結果のリスト)
        """
        if container is None:
            self.add_error("検証するデータがありません。")
            return False, []
        
        # データ検証を実行
        return self.validator.validate(container)
    
    def add_to_import_history(self, file_name: str, file_format: str, container: GPSDataContainer):
        """
        インポート履歴に追加
        
        Parameters
        ----------
        file_name : str
            ファイル名
        file_format : str
            ファイル形式
        container : GPSDataContainer
            インポートされたデータコンテナ
        """
        state = self.get_state()
        
        # インポート履歴エントリを作成
        history_entry = {
            "file_name": file_name,
            "file_format": file_format,
            "imported_at": pd.Timestamp.now().isoformat(),
            "data_points": len(container.data) if container.data is not None else 0,
            "container_id": container.container_id
        }
        
        # 履歴に追加
        state["import_history"].append(history_entry)
        
        # インポートされたコンテナを保存
        state["imported_container"] = container
        
        self.set_state(state)
    
    def get_import_history(self) -> List[Dict[str, Any]]:
        """
        インポート履歴を取得
        
        Returns
        -------
        List[Dict[str, Any]]
            インポート履歴のリスト
        """
        return self.get_state()["import_history"]
    
    def get_imported_container(self) -> Optional[GPSDataContainer]:
        """
        最後にインポートされたデータコンテナを取得
        
        Returns
        -------
        Optional[GPSDataContainer]
            最後にインポートされたデータコンテナ
        """
        return self.get_state()["imported_container"]
    
    def set_imported_container(self, container: GPSDataContainer):
        """
        インポートされたデータコンテナを設定
        
        Parameters
        ----------
        container : GPSDataContainer
            インポートされたデータコンテナ
        """
        state = self.get_state()
        state["imported_container"] = container
        self.set_state(state)
        
    def get_validation_results(self) -> Optional[Tuple[bool, List[Dict[str, Any]]]]:
        """
        最後の検証結果を取得
        
        Returns
        -------
        Optional[Tuple[bool, List[Dict[str, Any]]]]
            検証結果のタプル (成功フラグ, 検証結果リスト)
        """
        if "validation_results" not in st.session_state:
            # まだ検証が実行されていない場合
            container = self.get_imported_container()
            if container:
                # 検証を実行して結果を保存
                validation_results = self.validate_data(container)
                st.session_state["validation_results"] = validation_results
                return validation_results
            return None
        return st.session_state["validation_results"]
        
    def run_validation_after_import(self, container: GPSDataContainer) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        インポート後にデータ検証を実行
        
        Parameters
        ----------
        container : GPSDataContainer
            検証対象のデータコンテナ
            
        Returns
        -------
        Tuple[bool, List[Dict[str, Any]]]
            検証結果 (成功フラグ, 検証結果リスト)
        """
        # 検証を実行
        validation_results = self.validate_data(container)
        
        # 検証結果をセッションに保存
        st.session_state["validation_results"] = validation_results
        
        return validation_results
    
    def create_session_from_container(
            self, 
            project_id: str, 
            name: str, 
            description: str = "", 
            tags: List[str] = None
        ) -> bool:
        """
        インポートされたデータからセッションを作成
        
        Parameters
        ----------
        project_id : str
            プロジェクトID
        name : str
            セッション名
        description : str, optional
            セッションの説明, by default ""
        tags : List[str], optional
            タグのリスト, by default None
            
        Returns
        -------
        bool
            成功した場合はTrue、それ以外はFalse
        """
        container = self.get_imported_container()
        
        if container is None:
            self.add_error("セッション作成に必要なデータがありません。")
            return False
        
        if not project_id:
            self.add_error("プロジェクトIDが指定されていません。")
            return False
        
        # プロジェクトマネージャーが初期化されていない場合は初期化
        if self.project_manager is None:
            from ui.components.project.project_manager import initialize_project_manager
            self.project_manager = initialize_project_manager()
        
        try:
            # セッションを作成
            session = self.project_manager.create_session(
                project_id=project_id,
                name=name,
                description=description,
                tags=tags or [],
                data_container=container
            )
            
            return session is not None
        
        except Exception as e:
            self.add_error(f"セッションの作成中にエラーが発生しました: {str(e)}")
            return False
