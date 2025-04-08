"""
sailing_data_processor.project.session_manager

プロジェクト・セッション間の関連を管理するセッション管理クラスを提供するモジュール
"""

from typing import Dict, List, Any, Optional, Union, Set, Tuple, Callable
import os
import json
from datetime import datetime
import uuid
from pathlib import Path
import copy

from sailing_data_processor.project.project_manager import ProjectManager, Project, Session
from sailing_data_processor.project.session_model import SessionModel, SessionResult


class SessionManager:
    """
    セッション管理クラス（プロジェクト連携特化版）
    
    プロジェクト管理クラスと連携して、セッションの検索・取得・フィルタリング機能や
    セッションメタデータの管理、プロジェクト-セッション関連付け管理、
    セッションファイルの管理などを提供します。
    
    Parameters
    ----------
    project_manager : ProjectManager
        プロジェクト管理クラスのインスタンス
    """
    
    def __init__(self, project_manager: ProjectManager):
        """
        初期化
        
        Parameters
        ----------
        project_manager : ProjectManager
            プロジェクト管理クラスのインスタンス
        """
        self.project_manager = project_manager
        # セッションメタデータのキャッシュ
        self._session_metadata_cache = {}
        # セッションタグのキャッシュ (tag -> set of session_ids)
        self._session_tags_cache = {}
        # セッション検索インデックス (キーワード -> set of session_ids)
        self._search_index = {}
        # 結果管理
        self._results_cache = {}  # session_id -> Dict[result_id -> Dict[version -> SessionResult]]
        # 関連セッションキャッシュ
        self._related_sessions_cache = {}  # session_id -> Dict[relation_type -> List[session_id]]
        
        # セッション結果保存パス
        self.results_path = Path(project_manager.base_path) / "results"
        self.results_path.mkdir(parents=True, exist_ok=True)
        
        # キャッシュの初期化
        self._initialize_cache()
    
    def _initialize_cache(self) -> None:
        """
        メタデータとタグのキャッシュを初期化
        """
        self._session_metadata_cache = {}
        self._session_tags_cache = {}
        self._search_index = {}
        self._results_cache = {}
        self._related_sessions_cache = {}
        
        # すべてのセッションをロード
        all_sessions = self.get_all_sessions()
        
        for session in all_sessions:
            # メタデータをキャッシュ
            self._session_metadata_cache[session.session_id] = session.metadata
            
            # タグのインデックスを構築
            if session.tags:
                for tag in session.tags:
                    if tag not in self._session_tags_cache:
                        self._session_tags_cache[tag] = set()
                    self._session_tags_cache[tag].add(session.session_id)
            
            # 検索インデックスを構築
            self._add_to_search_index(session)
            
            # 結果のロード
            self._load_session_results(session.session_id)
            
            # 関連セッションのキャッシュ更新
            if hasattr(session, 'related_sessions') and session.related_sessions:
                self._related_sessions_cache[session.session_id] = session.related_sessions
    
    def _load_session_results(self, session_id: str) -> None:
        """
        セッション結果をロード
        
        Parameters
        ----------
        session_id : str
            セッションID
        """
        session_results_path = self.results_path / session_id
        if not session_results_path.exists():
            return
        
        self._results_cache[session_id] = {}
        
        # 結果タイプごとのディレクトリを検索
        for result_type_dir in session_results_path.glob("*"):
            if not result_type_dir.is_dir():
                continue
            
            # 各結果ファイルを読み込み
            for result_file in result_type_dir.glob("*.json"):
                try:
                    with open(result_file, 'r', encoding='utf-8') as f:
                        result_data = json.load(f)
                        result = SessionResult.from_dict(result_data)
                        
                        # 結果をキャッシュに追加
                        result_id = result.result_id
                        if result_id not in self._results_cache[session_id]:
                            self._results_cache[session_id][result_id] = {}
                        
                        self._results_cache[session_id][result_id][result.version] = result
                except Exception as e:
                    print(f"Failed to load result file {result_file}: {e}")
    
    def _add_to_search_index(self, session: Session) -> None:
        """
        セッションを検索インデックスに追加
        
        Parameters
        ----------
        session : Session
            インデックスに追加するセッション
        """
        # セッション名から検索キーワードを抽出
        keywords = set(self._extract_keywords(session.name))
        # 説明から検索キーワードを抽出
        if session.description:
            keywords.update(self._extract_keywords(session.description))
        
        # メタデータから検索キーワードを抽出
        for key, value in session.metadata.items():
            if isinstance(value, str):
                keywords.update(self._extract_keywords(value))
        
        # タグをキーワードとして追加
        if session.tags:
            keywords.update(session.tags)
        
        # インデックスに登録
        for keyword in keywords:
            if keyword not in self._search_index:
                self._search_index[keyword] = set()
            self._search_index[keyword].add(session.session_id)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        テキストから検索キーワードを抽出
        
        Parameters
        ----------
        text : str
            キーワードを抽出するテキスト
            
        Returns
        -------
        List[str]
            抽出されたキーワードのリスト
        """
        # 単純な分割と前処理
        words = text.lower().split()
        # 短すぎる単語を除外（オプション）
        return [word for word in words if len(word) > 2]
    
    def _update_search_index(self, session: Session) -> None:
        """
        セッションの検索インデックスを更新
        
        Parameters
        ----------
        session : Session
            更新するセッション
        """
        # セッションIDを含むエントリをすべてクリア
        for keyword_sessions in self._search_index.values():
            if session.session_id in keyword_sessions:
                keyword_sessions.remove(session.session_id)
        
        # 再インデックス
        self._add_to_search_index(session)
    
    def get_all_sessions(self) -> List[Session]:
        """
        システム内のすべてのセッションを取得
        
        Returns
        -------
        List[Session]
            すべてのセッションのリスト
        """
        return self.project_manager.get_all_sessions()
    
    def get_project_sessions(self, project_id: str) -> List[Session]:
        """
        特定プロジェクトのセッションを取得
        
        Parameters
        ----------
        project_id : str
            プロジェクトID
            
        Returns
        -------
        List[Session]
            プロジェクト内のセッションのリスト
        """
        return self.project_manager.get_project_sessions(project_id)
    
    def get_sessions_not_in_project(self, project_id: str) -> List[Session]:
        """
        指定したプロジェクトに含まれていないセッションを取得
        
        Parameters
        ----------
        project_id : str
            プロジェクトID
            
        Returns
        -------
        List[Session]
            プロジェクトに含まれていないセッションのリスト
        """
        project = self.project_manager.get_project(project_id)
        if not project:
            return []
        
        all_sessions = self.get_all_sessions()
        return [session for session in all_sessions if session.session_id not in project.sessions]
    
    def add_session_to_project(self, project_id: str, session_id: str) -> bool:
        """
        セッションをプロジェクトに追加
        
        Parameters
        ----------
        project_id : str
            プロジェクトID
        session_id : str
            セッションID
            
        Returns
        -------
        bool
            追加に成功した場合True
        """
        project = self.project_manager.get_project(project_id)
        if not project:
            return False
        
        if session_id in project.sessions:
            return True  # 既に追加済み
        
        try:
            project.add_session(session_id)
            self.project_manager.save_project(project)
            return True
        except Exception as e:
            print(f"Error adding session to project: {e}")
            return False
    
    def remove_session_from_project(self, project_id: str, session_id: str) -> bool:
        """
        セッションをプロジェクトから削除
        
        Parameters
        ----------
        project_id : str
            プロジェクトID
        session_id : str
            セッションID
            
        Returns
        -------
        bool
            削除に成功した場合True
        """
        project = self.project_manager.get_project(project_id)
        if not project:
            return False
        
        if session_id not in project.sessions:
            return True  # 既に削除済み
        
        try:
            project.remove_session(session_id)
            self.project_manager.save_project(project)
            return True
        except Exception as e:
            print(f"Error removing session from project: {e}")
            return False
    
    def move_session(self, session_id: str, source_project_id: str, target_project_id: str) -> bool:
        """
        セッションをプロジェクト間で移動
        
        Parameters
        ----------
        session_id : str
            セッションID
        source_project_id : str
            移動元プロジェクトID
        target_project_id : str
            移動先プロジェクトID
            
        Returns
        -------
        bool
            移動に成功した場合True
        """
        # 移動元と移動先のプロジェクトを取得
        source_project = self.project_manager.get_project(source_project_id)
        target_project = self.project_manager.get_project(target_project_id)
        
        if not source_project or not target_project:
            return False
        
        # セッションの存在確認
        if session_id not in source_project.sessions:
            return False
        
        # セッションを移動
        try:
            # 移動元から削除
            source_project.remove_session(session_id)
            self.project_manager.save_project(source_project)
            
            # 移動先に追加
            target_project.add_session(session_id)
            self.project_manager.save_project(target_project)
            
            return True
        except Exception as e:
            print(f"Error moving session between projects: {e}")
            # エラー時は元に戻す試み
            try:
                source_project.add_session(session_id)
                self.project_manager.save_project(source_project)
            except:
                pass
            return False
    
    def update_session_metadata(self, session_id: str, metadata: Dict[str, Any]) -> bool:
        """
        セッションメタデータを更新
        
        Parameters
        ----------
        session_id : str
            セッションID
        metadata : Dict[str, Any]
            更新するメタデータ
            
        Returns
        -------
        bool
            更新に成功した場合True
        """
        session = self.project_manager.get_session(session_id)
        if not session:
            return False
        
        try:
            # メタデータを更新
            for key, value in metadata.items():
                session.metadata[key] = value
            
            # キャッシュも更新
            if session_id in self._session_metadata_cache:
                self._session_metadata_cache[session_id].update(metadata)
            else:
                self._session_metadata_cache[session_id] = metadata.copy()
            
            # タグが更新された場合は、タグキャッシュも更新
            if "tags" in metadata and isinstance(metadata["tags"], list):
                self._update_session_tags(session_id, session.tags, metadata["tags"])
                session.tags = metadata["tags"]
            
            # イベント日時が更新された場合
            if "event_date" in metadata:
                event_date = None
                if metadata["event_date"]:
                    try:
                        # 文字列の場合はdatetimeに変換
                        if isinstance(metadata["event_date"], str):
                            event_date = datetime.fromisoformat(metadata["event_date"])
                        else:
                            event_date = metadata["event_date"]
                    except (ValueError, TypeError):
                        pass
                
                # 拡張バージョンのセッションモデルの場合
                if hasattr(session, 'update_event_date'):
                    session.update_event_date(event_date)
                elif hasattr(session, 'event_date'):
                    session.event_date = event_date.isoformat() if event_date else None
            
            # 位置情報が更新された場合
            if "location" in metadata:
                # 拡張バージョンのセッションモデルの場合
                if hasattr(session, 'update_location'):
                    session.update_location(metadata["location"])
                elif hasattr(session, 'location'):
                    session.location = metadata["location"]
            
            # 検索インデックスを更新
            self._update_search_index(session)
            
            # セッションを保存
            self.project_manager.save_session(session)
            
            return True
        except Exception as e:
            print(f"Error updating session metadata: {e}")
            return False
    
    def _update_session_tags(self, session_id: str, old_tags: List[str], new_tags: List[str]) -> None:
        """
        セッションのタグ情報を更新
        
        Parameters
        ----------
        session_id : str
            セッションID
        old_tags : List[str]
            古いタグのリスト
        new_tags : List[str]
            新しいタグのリスト
        """
        # 古いタグからセッションIDを削除
        for tag in old_tags:
            if tag in self._session_tags_cache and session_id in self._session_tags_cache[tag]:
                self._session_tags_cache[tag].remove(session_id)
                
                # タグに関連するセッションがなくなった場合、タグを削除
                if not self._session_tags_cache[tag]:
                    del self._session_tags_cache[tag]
        
        # 新しいタグにセッションIDを追加
        for tag in new_tags:
            if tag not in self._session_tags_cache:
                self._session_tags_cache[tag] = set()
            self._session_tags_cache[tag].add(session_id)
    
    def search_sessions(self, query: str = "", tags: List[str] = None, 
                        start_date: Optional[datetime] = None, 
                        end_date: Optional[datetime] = None,
                        location: Optional[str] = None,
                        updated_start_date: Optional[datetime] = None,
                        updated_end_date: Optional[datetime] = None,
                        **advanced_filters) -> List[str]:
        """
        セッションを検索
        
        Parameters
        ----------
        query : str, optional
            検索キーワード, by default ""
        tags : List[str], optional
            タグによるフィルタリング, by default None
        start_date : Optional[datetime], optional
            開始日による範囲指定, by default None
        end_date : Optional[datetime], optional
            終了日による範囲指定, by default None
        location : Optional[str], optional
            位置情報による検索, by default None
        updated_start_date : Optional[datetime], optional
            更新開始日による範囲指定, by default None
        updated_end_date : Optional[datetime], optional
            更新終了日による範囲指定, by default None
        **advanced_filters
            その他の高度なフィルタリング条件
            - status: セッションのステータス
            - category: セッションのカテゴリ
            - boat_type: 艇種
            - course_type: コース種類
            - created_by: 作成者
            - min_wind_speed: 風速下限
            - max_wind_speed: 風速上限
            - has_analysis: 分析結果の有無
            - has_validation: 検証済みかどうか
            - rating: 評価値
            - related_to: 関連するセッションID
            
        Returns
        -------
        List[str]
            条件に一致するセッションIDのリスト
        """
        # 初期状態ではすべてのセッションが対象
        all_sessions = self.get_all_sessions()
        result_ids = {session.session_id for session in all_sessions}
        
        # クエリによる検索
        if query:
            query_words = self._extract_keywords(query)
            matching_ids = set()
            
            # インデックスを使用して高速に検索
            for word in query_words:
                if word in self._search_index:
                    if not matching_ids:
                        matching_ids = self._search_index[word].copy()
                    else:
                        matching_ids &= self._search_index[word]
            
            # 検索結果がない場合は部分一致も試みる
            if not matching_ids:
                for keyword, ids in self._search_index.items():
                    if any(word in keyword for word in query_words):
                        matching_ids.update(ids)
            
            result_ids &= matching_ids
        
        # タグによるフィルタリング
        if tags and len(tags) > 0:
            tag_matching_ids = set()
            for tag in tags:
                if tag in self._session_tags_cache:
                    if not tag_matching_ids:
                        tag_matching_ids = self._session_tags_cache[tag].copy()
                    else:
                        # AND検索
                        tag_matching_ids &= self._session_tags_cache[tag]
            
            result_ids &= tag_matching_ids
        
        # フィルタリング条件を適用
        filtered_sessions = [s for s in all_sessions if s.session_id in result_ids]
        final_results = []
        
        for session in filtered_sessions:
            # 日付範囲によるフィルタリング
            if start_date or end_date:
                event_date_str = session.metadata.get("event_date", "")
                if event_date_str:
                    try:
                        event_date = datetime.fromisoformat(event_date_str)
                        if start_date and event_date < start_date:
                            continue
                        if end_date and event_date > end_date:
                            continue
                    except (ValueError, TypeError):
                        # 日付形式が無効な場合は作成日を使用
                        try:
                            created_date = datetime.fromisoformat(session.created_at)
                            if start_date and created_date < start_date:
                                continue
                            if end_date and created_date > end_date:
                                continue
                        except (ValueError, TypeError):
                            continue
            
            # 更新日範囲によるフィルタリング
            if updated_start_date or updated_end_date:
                try:
                    updated_date = datetime.fromisoformat(session.updated_at)
                    if updated_start_date and updated_date < updated_start_date:
                        continue
                    if updated_end_date and updated_date > updated_end_date:
                        continue
                except (ValueError, TypeError):
                    continue
            
            # 位置情報によるフィルタリング
            if location:
                session_location = session.metadata.get("location", "")
                if location.lower() not in session_location.lower():
                    continue
            
            # 高度なフィルタリング条件を適用
            skip = False
            
            for key, value in advanced_filters.items():
                if key == "status" and value and session.status != value:
                    skip = True
                    break
                
                elif key == "category" and value and session.category != value:
                    skip = True
                    break
                
                elif key == "boat_type" and value:
                    boat_type = session.metadata.get("boat_type", "")
                    if value.lower() not in boat_type.lower():
                        skip = True
                        break
                
                elif key == "course_type" and value:
                    course_type = session.metadata.get("course_type", "")
                    if value.lower() not in course_type.lower():
                        skip = True
                        break
                
                elif key == "created_by" and value:
                    created_by = session.metadata.get("created_by", "")
                    if value.lower() not in created_by.lower():
                        skip = True
                        break
                
                elif key == "min_wind_speed" and value is not None:
                    wind_speed = session.metadata.get("avg_wind_speed", 0)
                    try:
                        wind_speed = float(wind_speed)
                        if wind_speed < float(value):
                            skip = True
                            break
                    except (ValueError, TypeError):
                        skip = True
                        break
                
                elif key == "max_wind_speed" and value is not None:
                    wind_speed = session.metadata.get("avg_wind_speed", 0)
                    try:
                        wind_speed = float(wind_speed)
                        if wind_speed > float(value):
                            skip = True
                            break
                    except (ValueError, TypeError):
                        skip = True
                        break
                
                elif key == "has_analysis" and value:
                    if not session.analysis_results:
                        skip = True
                        break
                
                elif key == "has_validation" and value:
                    validation_score = session.metadata.get("validation_score", 0)
                    if validation_score <= 0:
                        skip = True
                        break
                
                elif key == "rating" and value is not None:
                    rating = getattr(session, 'rating', 0)
                    if rating < int(value):
                        skip = True
                        break
                
                elif key == "related_to" and value:
                    # 関連セッションによるフィルタリング
                    if session.session_id not in self._related_sessions_cache:
                        skip = True
                        break
                    
                    related_found = False
                    for relation_type, session_ids in self._related_sessions_cache[session.session_id].items():
                        if value in session_ids:
                            related_found = True
                            break
                    
                    if not related_found:
                        skip = True
                        break
            
            if not skip:
                final_results.append(session.session_id)
        
        return final_results
    
    def get_available_tags(self) -> List[str]:
        """
        利用可能なすべてのタグを取得
        
        Returns
        -------
        List[str]
            システム内のすべてのタグのリスト
        """
        return list(self._session_tags_cache.keys())
    
    def get_sessions_by_tag(self, tag: str) -> List[str]:
        """
        タグでセッションを検索
        
        Parameters
        ----------
        tag : str
            検索するタグ
            
        Returns
        -------
        List[str]
            タグに一致するセッションIDのリスト
        """
        if tag in self._session_tags_cache:
            return list(self._session_tags_cache[tag])
        return []
        
    def get_sessions_by_multiple_tags(self, tags: List[str], match_all: bool = True) -> List[str]:
        """
        複数のタグでセッションを検索
        
        Parameters
        ----------
        tags : List[str]
            検索するタグのリスト
        match_all : bool, optional
            すべてのタグに一致するセッションを返すかどうか, by default True
            Falseの場合はいずれかのタグに一致するセッションを返す
            
        Returns
        -------
        List[str]
            タグに一致するセッションIDのリスト
        """
        if not tags:
            return []
        
        if match_all:
            # すべてのタグに一致するセッションを検索（AND検索）
            result_set = None
            for tag in tags:
                if tag in self._session_tags_cache:
                    if result_set is None:
                        result_set = set(self._session_tags_cache[tag])
                    else:
                        result_set &= set(self._session_tags_cache[tag])
                else:
                    # 一つでも存在しないタグがあれば空の結果を返す
                    return []
            
            return list(result_set) if result_set else []
        else:
            # いずれかのタグに一致するセッションを検索（OR検索）
            result_set = set()
            for tag in tags:
                if tag in self._session_tags_cache:
                    result_set |= set(self._session_tags_cache[tag])
            
            return list(result_set)
    
    def get_sessions_by_category(self, category: str) -> List[SessionModel]:
        """
        カテゴリでセッションを検索
        
        Parameters
        ----------
        category : str
            検索するカテゴリ
            
        Returns
        -------
        List[SessionModel]
            カテゴリに一致するセッションのリスト
        """
        sessions = self.get_all_sessions()
        return [s for s in sessions if hasattr(s, 'category') and s.category == category]
    
    def get_related_sessions(self, session_id: str, relation_type: str = None) -> List[SessionModel]:
        """
        関連セッションを取得
        
        Parameters
        ----------
        session_id : str
            セッションID
        relation_type : str, optional
            関連タイプ, by default None (すべての関連タイプ)
            
        Returns
        -------
        List[SessionModel]
            関連セッションのリスト
        """
        if session_id not in self._related_sessions_cache:
            return []
        
        related_ids = []
        
        if relation_type:
            # 特定の関連タイプのみ取得
            if relation_type in self._related_sessions_cache[session_id]:
                related_ids = self._related_sessions_cache[session_id][relation_type]
        else:
            # すべての関連タイプを取得
            for ids in self._related_sessions_cache[session_id].values():
                related_ids.extend(ids)
        
        # セッションオブジェクトを取得
        related_sessions = []
        for related_id in related_ids:
            session = self.project_manager.get_session(related_id)
            if session:
                related_sessions.append(session)
        
        return related_sessions
    
    def bulk_add_sessions_to_project(self, project_id: str, session_ids: List[str]) -> int:
        """
        複数のセッションを一括でプロジェクトに追加
        
        Parameters
        ----------
        project_id : str
            プロジェクトID
        session_ids : List[str]
            追加するセッションIDのリスト
            
        Returns
        -------
        int
            追加に成功したセッション数
        """
        project = self.project_manager.get_project(project_id)
        if not project:
            return 0
        
        success_count = 0
        for session_id in session_ids:
            if self.add_session_to_project(project_id, session_id):
                success_count += 1
        
        return success_count
    
    def bulk_remove_sessions_from_project(self, project_id: str, session_ids: List[str]) -> int:
        """
        複数のセッションを一括でプロジェクトから削除
        
        Parameters
        ----------
        project_id : str
            プロジェクトID
        session_ids : List[str]
            削除するセッションIDのリスト
            
        Returns
        -------
        int
            削除に成功したセッション数
        """
        project = self.project_manager.get_project(project_id)
        if not project:
            return 0
        
        success_count = 0
        for session_id in session_ids:
            if self.remove_session_from_project(project_id, session_id):
                success_count += 1
        
        return success_count
    
    def get_projects_containing_session(self, session_id: str) -> List[Project]:
        """
        指定したセッションを含むプロジェクトのリストを取得
        
        Parameters
        ----------
        session_id : str
            セッションID
            
        Returns
        -------
        List[Project]
            セッションを含むプロジェクトのリスト
        """
        projects = self.project_manager.get_projects()
        return [project for project in projects if session_id in project.sessions]
    
    def update_session_status(self, session_id: str, status: str) -> bool:
        """
        セッションのステータスを更新
        
        Parameters
        ----------
        session_id : str
            セッションID
        status : str
            新しいステータス
            
        Returns
        -------
        bool
            更新に成功した場合True
        """
        session = self.project_manager.get_session(session_id)
        if not session:
            return False
        
        try:
            session.status = status
            self.project_manager.save_session(session)
            # 検索インデックスも更新
            self._update_search_index(session)
            return True
        except Exception as e:
            print(f"Error updating session status: {e}")
            return False
    
    def update_session_category(self, session_id: str, category: str) -> bool:
        """
        セッションのカテゴリを更新
        
        Parameters
        ----------
        session_id : str
            セッションID
        category : str
            新しいカテゴリ
            
        Returns
        -------
        bool
            更新に成功した場合True
        """
        session = self.project_manager.get_session(session_id)
        if not session:
            return False
        
        try:
            session.category = category
            self.project_manager.save_session(session)
            # 検索インデックスも更新
            self._update_search_index(session)
            return True
        except Exception as e:
            print(f"Error updating session category: {e}")
            return False
    
    def update_session_tags(self, session_id: str, tags: List[str]) -> bool:
        """
        セッションのタグを更新
        
        Parameters
        ----------
        session_id : str
            セッションID
        tags : List[str]
            新しいタグのリスト
            
        Returns
        -------
        bool
            更新に成功した場合True
        """
        session = self.project_manager.get_session(session_id)
        if not session:
            return False
        
        try:
            old_tags = session.tags.copy() if session.tags else []
            session.tags = tags
            self.project_manager.save_session(session)
            
            # タグキャッシュを更新
            self._update_session_tags(session_id, old_tags, tags)
            
            # 検索インデックスも更新
            self._update_search_index(session)
            
            return True
        except Exception as e:
            print(f"Error updating session tags: {e}")
            return False
    
    def update_session_rating(self, session_id: str, rating: int) -> bool:
        """
        セッションの評価を更新
        
        Parameters
        ----------
        session_id : str
            セッションID
        rating : int
            新しい評価値 (0-5)
            
        Returns
        -------
        bool
            更新に成功した場合True
        """
        session = self.project_manager.get_session(session_id)
        if not session:
            return False
        
        try:
            if hasattr(session, 'update_rating'):
                session.update_rating(rating)
            else:
                # 旧セッションモデルの場合は、直接属性を設定
                session.rating = rating if 0 <= rating <= 5 else 0
                session.updated_at = datetime.now().isoformat()
            
            self.project_manager.save_session(session)
            return True
        except Exception as e:
            print(f"Error updating session rating: {e}")
            return False
    
    def update_session_event_date(self, session_id: str, event_date: Optional[datetime]) -> bool:
        """
        セッションの日時を更新
        
        Parameters
        ----------
        session_id : str
            セッションID
        event_date : Optional[datetime]
            新しい日時、Noneの場合は日時をクリア
            
        Returns
        -------
        bool
            更新に成功した場合True
        """
        session = self.project_manager.get_session(session_id)
        if not session:
            return False
        
        try:
            if hasattr(session, 'update_event_date'):
                session.update_event_date(event_date)
            else:
                # 旧セッションモデルの場合は、メタデータを更新
                if event_date:
                    session.metadata['event_date'] = event_date.isoformat()
                elif 'event_date' in session.metadata:
                    del session.metadata['event_date']
                session.updated_at = datetime.now().isoformat()
            
            # セッションを保存
            self.project_manager.save_session(session)
            
            # 検索インデックスを更新
            self._update_search_index(session)
            
            return True
        except Exception as e:
            print(f"Error updating session event date: {e}")
            return False
    
    def update_session_location(self, session_id: str, location: str) -> bool:
        """
        セッションの位置情報を更新
        
        Parameters
        ----------
        session_id : str
            セッションID
        location : str
            新しい位置情報
            
        Returns
        -------
        bool
            更新に成功した場合True
        """
        session = self.project_manager.get_session(session_id)
        if not session:
            return False
        
        try:
            if hasattr(session, 'update_location'):
                session.update_location(location)
            else:
                # 旧セッションモデルの場合は、メタデータを更新
                if location:
                    session.metadata['location'] = location
                elif 'location' in session.metadata:
                    del session.metadata['location']
                session.updated_at = datetime.now().isoformat()
            
            # セッションを保存
            self.project_manager.save_session(session)
            
            # 検索インデックスを更新
            self._update_search_index(session)
            
            return True
        except Exception as e:
            print(f"Error updating session location: {e}")
            return False
    
    def add_related_session(self, session_id: str, related_session_id: str, relation_type: str = "related") -> bool:
        """
        関連セッションを追加
        
        Parameters
        ----------
        session_id : str
            セッションID
        related_session_id : str
            関連するセッションID
        relation_type : str, optional
            関連タイプ, by default "related"
            
        Returns
        -------
        bool
            追加に成功した場合True
        """
        session = self.project_manager.get_session(session_id)
        if not session or not self.project_manager.get_session(related_session_id):
            return False
        
        try:
            if hasattr(session, 'add_related_session'):
                session.add_related_session(related_session_id, relation_type)
            else:
                # 旧セッションモデルの場合は、メタデータに追加
                if 'related_sessions' not in session.metadata:
                    session.metadata['related_sessions'] = {}
                if relation_type not in session.metadata['related_sessions']:
                    session.metadata['related_sessions'][relation_type] = []
                if related_session_id not in session.metadata['related_sessions'][relation_type]:
                    session.metadata['related_sessions'][relation_type].append(related_session_id)
                    session.updated_at = datetime.now().isoformat()
            
            # キャッシュを更新
            if session_id not in self._related_sessions_cache:
                self._related_sessions_cache[session_id] = {}
            if relation_type not in self._related_sessions_cache[session_id]:
                self._related_sessions_cache[session_id][relation_type] = []
            if related_session_id not in self._related_sessions_cache[session_id][relation_type]:
                self._related_sessions_cache[session_id][relation_type].append(related_session_id)
            
            self.project_manager.save_session(session)
            return True
        except Exception as e:
            print(f"Error adding related session: {e}")
            return False
    
    def remove_related_session(self, session_id: str, related_session_id: str, relation_type: str = "related") -> bool:
        """
        関連セッションを削除
        
        Parameters
        ----------
        session_id : str
            セッションID
        related_session_id : str
            削除する関連セッションID
        relation_type : str, optional
            関連タイプ, by default "related"
            
        Returns
        -------
        bool
            削除に成功した場合True
        """
        session = self.project_manager.get_session(session_id)
        if not session:
            return False
        
        try:
            if hasattr(session, 'remove_related_session'):
                session.remove_related_session(related_session_id, relation_type)
            else:
                # 旧セッションモデルの場合は、メタデータから削除
                if 'related_sessions' in session.metadata and relation_type in session.metadata['related_sessions']:
                    if related_session_id in session.metadata['related_sessions'][relation_type]:
                        session.metadata['related_sessions'][relation_type].remove(related_session_id)
                        session.updated_at = datetime.now().isoformat()
            
            # キャッシュを更新
            if (session_id in self._related_sessions_cache and 
                relation_type in self._related_sessions_cache[session_id] and 
                related_session_id in self._related_sessions_cache[session_id][relation_type]):
                self._related_sessions_cache[session_id][relation_type].remove(related_session_id)
            
            self.project_manager.save_session(session)
            return True
        except Exception as e:
            print(f"Error removing related session: {e}")
            return False
    
    def get_session_results(self, session_id: str, result_type: str = None, 
                         include_all_versions: bool = False, 
                         tags: List[str] = None) -> List[SessionResult]:
        """
        セッション結果を取得
        
        Parameters
        ----------
        session_id : str
            セッションID
        result_type : str, optional
            結果タイプ, by default None (すべてのタイプ)
        include_all_versions : bool, optional
            すべてのバージョンを含めるかどうか, by default False
            Falseの場合は現在のバージョンのみを返す
        tags : List[str], optional
            タグによるフィルタリング, by default None
            
        Returns
        -------
        List[SessionResult]
            セッション結果のリスト
        """
        if session_id not in self._results_cache:
            return []
        
        results = []
        
        for result_id, versions in self._results_cache[session_id].items():
            for result in versions.values():
                # 結果タイプによるフィルタリング
                if result_type is not None and result.result_type != result_type:
                    continue
                
                # バージョンによるフィルタリング
                if not include_all_versions and not result.is_current:
                    continue
                
                # タグによるフィルタリング
                if tags:
                    if not result.tags or not any(tag in result.tags for tag in tags):
                        continue
                
                results.append(result)
        
        return results
        
    def get_session_results_by_tags(self, session_id: str, tags: List[str], 
                                  match_all: bool = True) -> List[SessionResult]:
        """
        タグに基づいてセッション結果を取得
        
        Parameters
        ----------
        session_id : str
            セッションID
        tags : List[str]
            検索するタグのリスト
        match_all : bool, optional
            すべてのタグに一致する結果を返すかどうか, by default True
            Falseの場合はいずれかのタグに一致する結果を返す
            
        Returns
        -------
        List[SessionResult]
            タグに一致するセッション結果のリスト
        """
        if session_id not in self._results_cache or not tags:
            return []
        
        results = []
        
        for result_id, versions in self._results_cache[session_id].items():
            for result in versions.values():
                # 現在のバージョンのみを対象とする
                if not result.is_current:
                    continue
                
                # タグによるフィルタリング
                if match_all:
                    # すべてのタグが含まれているか確認（AND検索）
                    if result.tags and all(tag in result.tags for tag in tags):
                        results.append(result)
                else:
                    # いずれかのタグが含まれているか確認（OR検索）
                    if result.tags and any(tag in result.tags for tag in tags):
                        results.append(result)
        
        return results
        
    def get_latest_session_results(self, session_id: str, max_results: int = 5) -> List[SessionResult]:
        """
        最新のセッション結果を取得
        
        Parameters
        ----------
        session_id : str
            セッションID
        max_results : int, optional
            取得する最大結果数, by default 5
            
        Returns
        -------
        List[SessionResult]
            最新のセッション結果のリスト（作成日時の降順）
        """
        if session_id not in self._results_cache:
            return []
        
        results = []
        
        # 現在のバージョンのみを集める
        for result_id, versions in self._results_cache[session_id].items():
            for result in versions.values():
                if result.is_current:
                    results.append(result)
                    break
        
        # 作成日時の降順でソート
        results.sort(key=lambda r: r.created_at if isinstance(r.created_at, str) else r.created_at.isoformat(), reverse=True)
        
        # 指定された数だけ返す
        return results[:max_results]
    
    def add_session_result(self, session_id: str, result_type: str, data: Dict[str, Any], 
                          metadata: Dict[str, Any] = None) -> SessionResult:
        """
        セッション結果を追加
        
        Parameters
        ----------
        session_id : str
            セッションID
        result_type : str
            結果タイプ
        data : Dict[str, Any]
            結果データ
        metadata : Dict[str, Any], optional
            結果メタデータ, by default None
            
        Returns
        -------
        SessionResult
            作成された結果
        """
        # セッションの存在確認
        session = self.project_manager.get_session(session_id)
        if not session:
            raise ValueError(f"Session with ID {session_id} does not exist")
        
        # 結果IDを生成
        result_id = str(uuid.uuid4())
        
        # 結果を作成
        result = SessionResult(
            result_id=result_id,
            session_id=session_id,
            result_type=result_type,
            data=data,
            metadata=metadata
        )
        
        # 結果の保存先ディレクトリを作成
        result_dir = self.results_path / session_id / result_type
        result_dir.mkdir(parents=True, exist_ok=True)
        
        # 結果をファイルに保存
        result_file = result_dir / f"{result_id}_v{result.version}.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)
        
        # キャッシュに追加
        if session_id not in self._results_cache:
            self._results_cache[session_id] = {}
        
        if result_id not in self._results_cache[session_id]:
            self._results_cache[session_id][result_id] = {}
        
        self._results_cache[session_id][result_id][result.version] = result
        
        # セッションに結果IDを追加
        if hasattr(session, 'add_result'):
            session.add_result(result_id)
        elif hasattr(session, 'add_analysis_result'):
            session.add_analysis_result(result_id)
        else:
            # 旧セッションモデルの場合は、直接属性を追加
            if not hasattr(session, 'results'):
                session.results = []
            session.results.append(result_id)
            session.updated_at = datetime.now().isoformat()
        
        self.project_manager.save_session(session)
        
        return result
    
    def update_session_result(self, session_id: str, result_id: str, data: Dict[str, Any], 
                             metadata: Dict[str, Any] = None) -> Optional[SessionResult]:
        """
        セッション結果を更新（新しいバージョンを作成）
        
        Parameters
        ----------
        session_id : str
            セッションID
        result_id : str
            結果ID
        data : Dict[str, Any]
            新しい結果データ
        metadata : Dict[str, Any], optional
            新しい結果メタデータ, by default None
            
        Returns
        -------
        Optional[SessionResult]
            更新された結果 (失敗した場合はNone)
        """
        # 既存の結果を確認
        if (session_id not in self._results_cache or 
            result_id not in self._results_cache[session_id]):
            return None
        
        # 現在のバージョンを取得
        current_version = None
        for version, result in self._results_cache[session_id][result_id].items():
            if result.is_current:
                current_version = result
                break
        
        if not current_version:
            return None
        
        # 新しいバージョンを作成
        new_version = current_version.create_new_version(data, metadata)
        
        # 結果タイプを取得
        result_type = new_version.result_type
        
        # 結果の保存先ディレクトリを確認
        result_dir = self.results_path / session_id / result_type
        result_dir.mkdir(parents=True, exist_ok=True)
        
        # 前のバージョンも保存（ステータスが更新されたため）
        prev_file = result_dir / f"{result_id}_v{current_version.version}.json"
        with open(prev_file, 'w', encoding='utf-8') as f:
            json.dump(current_version.to_dict(), f, ensure_ascii=False, indent=2)
        
        # 新しいバージョンを保存
        result_file = result_dir / f"{result_id}_v{new_version.version}.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(new_version.to_dict(), f, ensure_ascii=False, indent=2)
        
        # キャッシュを更新
        self._results_cache[session_id][result_id][new_version.version] = new_version
        
        return new_version
    
    def get_result_versions(self, session_id: str, result_id: str) -> List[SessionResult]:
        """
        結果のバージョンを取得
        
        Parameters
        ----------
        session_id : str
            セッションID
        result_id : str
            結果ID
            
        Returns
        -------
        List[SessionResult]
            結果のバージョンリスト（バージョン順にソート）
        """
        if (session_id not in self._results_cache or 
            result_id not in self._results_cache[session_id]):
            return []
        
        versions = list(self._results_cache[session_id][result_id].values())
        # バージョン番号で昇順ソート
        versions.sort(key=lambda x: x.version)
        
        return versions
        
    def get_result_version_history(self, session_id: str, result_id: str) -> Dict[str, Any]:
        """
        結果のバージョン履歴を取得
        
        Parameters
        ----------
        session_id : str
            セッションID
        result_id : str
            結果ID
            
        Returns
        -------
        Dict[str, Any]
            バージョン履歴情報（バージョン番号、作成日時、作成者、変更内容など）
        """
        if (session_id not in self._results_cache or 
            result_id not in self._results_cache[session_id]):
            return {"error": "Result not found"}
        
        versions = self.get_result_versions(session_id, result_id)
        
        # 最新バージョンを取得
        current_version = None
        for version in versions:
            if version.is_current:
                current_version = version
                break
        
        if not current_version:
            current_version = versions[-1] if versions else None
        
        # バージョン履歴を構築
        history = {
            "result_id": result_id,
            "session_id": session_id,
            "result_type": versions[0].result_type if versions else "",
            "current_version": current_version.version if current_version else None,
            "versions": []
        }
        
        # 各バージョンの情報を追加
        for version in versions:
            version_info = {
                "version": version.version,
                "created_at": version.created_at,
                "creator": version.creator,
                "is_current": version.is_current,
                "parent_version": version.parent_version,
                "last_modified_at": version.last_modified_at,
                "metadata": version.metadata
            }
            history["versions"].append(version_info)
        
        return history
        
    def compare_result_versions(self, session_id: str, result_id: str, 
                               version1: int, version2: int = None) -> Dict[str, Any]:
        """
        結果の2つのバージョンを比較
        
        Parameters
        ----------
        session_id : str
            セッションID
        result_id : str
            結果ID
        version1 : int
            比較する最初のバージョン番号
        version2 : int, optional
            比較する2番目のバージョン番号, by default None (最新バージョンと比較)
            
        Returns
        -------
        Dict[str, Any]
            比較結果の要約
        """
        if (session_id not in self._results_cache or 
            result_id not in self._results_cache[session_id]):
            return {"error": "Result not found"}
        
        # バージョンを取得
        version1_result = None
        version2_result = None
        
        for version, result in self._results_cache[session_id][result_id].items():
            if version == version1:
                version1_result = result
            elif version2 is not None and version == version2:
                version2_result = result
            elif version2 is None and result.is_current:
                version2_result = result
        
        if not version1_result:
            return {"error": f"Version {version1} not found"}
        
        if not version2_result:
            if version2 is not None:
                return {"error": f"Version {version2} not found"}
            else:
                return {"error": "Current version not found"}
        
        # 比較結果
        comparison = {
            "result_id": result_id,
            "session_id": session_id,
            "result_type": version1_result.result_type,
            "version1": version1,
            "version2": version2_result.version,
            "changes": {
                "metadata": self._compare_dicts(version1_result.metadata, version2_result.metadata),
                "tags": self._compare_lists(version1_result.tags, version2_result.tags),
                "result_category": version1_result.result_category != version2_result.result_category,
                "importance": version1_result.importance != version2_result.importance,
                "data_changes": self._compare_data_structures(version1_result.data, version2_result.data)
            }
        }
        
        return comparison
    
    def _compare_dicts(self, dict1: Dict, dict2: Dict) -> Dict[str, Any]:
        """辞書の違いを比較"""
        changes = {
            "added": [],
            "removed": [],
            "modified": []
        }
        
        # 追加されたキー
        for key in dict2:
            if key not in dict1:
                changes["added"].append(key)
        
        # 削除されたキー
        for key in dict1:
            if key not in dict2:
                changes["removed"].append(key)
        
        # 変更されたキー
        for key in dict1:
            if key in dict2 and dict1[key] != dict2[key]:
                changes["modified"].append(key)
        
        return changes
    
    def _compare_lists(self, list1: List, list2: List) -> Dict[str, Any]:
        """リストの違いを比較"""
        set1 = set(list1) if list1 else set()
        set2 = set(list2) if list2 else set()
        
        return {
            "added": list(set2 - set1),
            "removed": list(set1 - set2)
        }
    
    def _compare_data_structures(self, data1: Any, data2: Any) -> Any:
        """データ構造の違いを比較"""
        # ディクショナリの場合
        if isinstance(data1, dict) and isinstance(data2, dict):
            return self._compare_dicts(data1, data2)
        
        # リストの場合
        elif isinstance(data1, list) and isinstance(data2, list):
            # サイズの違い
            if len(data1) != len(data2):
                return {
                    "length_changed": True,
                    "old_length": len(data1),
                    "new_length": len(data2)
                }
            
            # 内容の違いを調査
            changes = []
            for i, (item1, item2) in enumerate(zip(data1, data2)):
                if item1 != item2:
                    changes.append({
                        "index": i,
                        "old_value": item1 if not isinstance(item1, (dict, list)) else "...",
                        "new_value": item2 if not isinstance(item2, (dict, list)) else "..."
                    })
            
            return {"changes": changes} if changes else {"changes": []}
        
        # その他の型の場合
        else:
            return {
                "changed": data1 != data2,
                "old_type": type(data1).__name__,
                "new_type": type(data2).__name__
            }
    
    def delete_session_result(self, session_id: str, result_id: str) -> bool:
        """
        セッション結果を削除
        
        Parameters
        ----------
        session_id : str
            セッションID
        result_id : str
            結果ID
            
        Returns
        -------
        bool
            削除に成功した場合True
        """
        # 結果の存在確認
        if (session_id not in self._results_cache or 
            result_id not in self._results_cache[session_id]):
            return False
        
        # セッションの存在確認
        session = self.project_manager.get_session(session_id)
        if not session:
            return False
        
        try:
            # 結果タイプを取得
            result_type = None
            for version, result in self._results_cache[session_id][result_id].items():
                result_type = result.result_type
                break
            
            if not result_type:
                return False
            
            # 結果ファイルを削除
            result_dir = self.results_path / session_id / result_type
            for version in self._results_cache[session_id][result_id].keys():
                result_file = result_dir / f"{result_id}_v{version}.json"
                if result_file.exists():
                    result_file.unlink()
            
            # キャッシュから削除
            del self._results_cache[session_id][result_id]
            
            # セッションから結果IDを削除
            if hasattr(session, 'remove_result'):
                session.remove_result(result_id)
            elif hasattr(session, 'remove_analysis_result'):
                session.remove_analysis_result(result_id)
            else:
                # 旧セッションモデルの場合は、直接属性から削除
                if hasattr(session, 'results') and result_id in session.results:
                    session.results.remove(result_id)
                    session.updated_at = datetime.now().isoformat()
            
            self.project_manager.save_session(session)
            
            return True
        except Exception as e:
            print(f"Error deleting session result: {e}")
            return False
    
    def get_session_summary(self, project_id: Optional[str] = None) -> Dict[str, Any]:
        """
        セッションの集計情報を取得
        
        Parameters
        ----------
        project_id : Optional[str], optional
            プロジェクトID (指定された場合はプロジェクト内のセッションのみ集計), by default None
            
        Returns
        -------
        Dict[str, Any]
            セッション集計情報
        """
        if project_id:
            sessions = self.get_project_sessions(project_id)
        else:
            sessions = self.get_all_sessions()
        
        # 集計情報の初期化
        summary = {
            "total_count": len(sessions),
            "by_status": {},
            "by_category": {},
            "by_tag": {},
            "by_boat_type": {},
            "by_rating": {},
            "recent_sessions": []
        }
        
        # ステータス、カテゴリ、タグ、艇種別の集計
        for session in sessions:
            # ステータス別集計
            status = session.status or "未設定"
            if status not in summary["by_status"]:
                summary["by_status"][status] = 0
            summary["by_status"][status] += 1
            
            # カテゴリ別集計
            category = session.category or "未設定"
            if category not in summary["by_category"]:
                summary["by_category"][category] = 0
            summary["by_category"][category] += 1
            
            # タグ別集計
            if session.tags:
                for tag in session.tags:
                    if tag not in summary["by_tag"]:
                        summary["by_tag"][tag] = 0
                    summary["by_tag"][tag] += 1
            
            # 艇種別集計
            boat_type = session.metadata.get("boat_type", "未設定")
            if boat_type not in summary["by_boat_type"]:
                summary["by_boat_type"][boat_type] = 0
            summary["by_boat_type"][boat_type] += 1
            
            # 評価別集計
            rating = getattr(session, 'rating', 0)
            if rating not in summary["by_rating"]:
                summary["by_rating"][rating] = 0
            summary["by_rating"][rating] += 1
        
        # 最近のセッションを取得（更新日時でソート）
        sorted_sessions = sorted(
            sessions, 
            key=lambda s: datetime.fromisoformat(s.updated_at) if s.updated_at else datetime.min,
            reverse=True
        )
        
        # 最新の5セッションを取得
        for session in sorted_sessions[:5]:
            summary["recent_sessions"].append({
                "session_id": session.session_id,
                "name": session.name,
                "updated_at": session.updated_at,
                "status": session.status
            })
        
        return summary
    
    def batch_process_sessions(self, session_ids: List[str], 
                               process_function: Callable[[Session], bool]) -> Dict[str, Any]:
        """
        複数のセッションに対して一括処理を行う
        
        Parameters
        ----------
        session_ids : List[str]
            処理対象のセッションIDリスト
        process_function : Callable[[Session], bool]
            各セッションに適用する処理関数
            
        Returns
        -------
        Dict[str, Any]
            処理結果サマリー
        """
        results = {
            "total": len(session_ids),
            "success": 0,
            "failed": 0,
            "failed_ids": []
        }
        
        for session_id in session_ids:
            session = self.project_manager.get_session(session_id)
            if not session:
                results["failed"] += 1
                results["failed_ids"].append(session_id)
                continue
            
            try:
                if process_function(session):
                    results["success"] += 1
                else:
                    results["failed"] += 1
                    results["failed_ids"].append(session_id)
            except Exception as e:
                print(f"Error processing session {session_id}: {e}")
                results["failed"] += 1
                results["failed_ids"].append(session_id)
        
        return results
