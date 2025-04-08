"""
sailing_data_processor.sharing.team_manager

チーム管理機能を提供するモジュール
"""

import json
import os
import uuid
import datetime
from typing import Dict, List, Any, Optional, Set
from pathlib import Path


class TeamMember:
    """
    チームメンバーを表すクラス
    
    Parameters
    ----------
    user_id : str
        ユーザーID
    name : str
        表示名
    email : Optional[str], optional
        メールアドレス, by default None
    role : str, optional
        役割（"owner", "editor", "viewer"）, by default "viewer"
    """
    
    def __init__(self, user_id: str, name: str, email: Optional[str] = None, role: str = "viewer"):
        """初期化"""
        self.user_id = user_id
        self.name = name
        self.email = email
        self.role = role
        self.added_at = datetime.datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書に変換"""
        return {
            'user_id': self.user_id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'added_at': self.added_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TeamMember':
        """辞書からインスタンスを作成"""
        member = cls(
            user_id=data['user_id'],
            name=data['name'],
            email=data.get('email'),
            role=data.get('role', 'viewer')
        )
        member.added_at = data.get('added_at', datetime.datetime.now().isoformat())
        return member


class Team:
    """
    チームを表すクラス
    
    Parameters
    ----------
    team_id : str
        チームID
    name : str
        チーム名
    description : str, optional
        説明, by default ""
    owner_id : str, optional
        オーナーのユーザーID, by default ""
    """
    
    def __init__(self, team_id: str, name: str, description: str = "", owner_id: str = ""):
        """初期化"""
        self.team_id = team_id
        self.name = name
        self.description = description
        self.owner_id = owner_id
        self.members: Dict[str, TeamMember] = {}  # user_id -> TeamMember
        self.created_at = datetime.datetime.now().isoformat()
        self.updated_at = self.created_at
        self.projects: Set[str] = set()  # プロジェクトIDのセット
        self.sessions: Set[str] = set()  # セッションIDのセット
    
    def add_member(self, member: TeamMember) -> bool:
        """
        メンバーを追加
        
        Parameters
        ----------
        member : TeamMember
            追加するメンバー
            
        Returns
        -------
        bool
            追加されたかどうか (既に存在する場合はFalse)
        """
        if member.user_id in self.members:
            return False
        
        self.members[member.user_id] = member
        self.updated_at = datetime.datetime.now().isoformat()
        return True
    
    def update_member(self, user_id: str, name: Optional[str] = None, 
                     email: Optional[str] = None, role: Optional[str] = None) -> bool:
        """
        メンバー情報を更新
        
        Parameters
        ----------
        user_id : str
            ユーザーID
        name : Optional[str], optional
            名前, by default None (変更なし)
        email : Optional[str], optional
            メールアドレス, by default None (変更なし)
        role : Optional[str], optional
            役割, by default None (変更なし)
            
        Returns
        -------
        bool
            更新されたかどうか
        """
        if user_id not in self.members:
            return False
        
        if name is not None:
            self.members[user_id].name = name
        
        if email is not None:
            self.members[user_id].email = email
        
        if role is not None:
            self.members[user_id].role = role
        
        self.updated_at = datetime.datetime.now().isoformat()
        return True
    
    def remove_member(self, user_id: str) -> bool:
        """
        メンバーを削除
        
        Parameters
        ----------
        user_id : str
            削除するメンバーのユーザーID
            
        Returns
        -------
        bool
            削除されたかどうか
        """
        if user_id not in self.members:
            return False
        
        # オーナーは削除できない
        if user_id == self.owner_id:
            return False
        
        del self.members[user_id]
        self.updated_at = datetime.datetime.now().isoformat()
        return True
    
    def add_project(self, project_id: str) -> bool:
        """
        プロジェクトを追加
        
        Parameters
        ----------
        project_id : str
            プロジェクトID
            
        Returns
        -------
        bool
            追加されたかどうか
        """
        if project_id in self.projects:
            return False
        
        self.projects.add(project_id)
        self.updated_at = datetime.datetime.now().isoformat()
        return True
    
    def remove_project(self, project_id: str) -> bool:
        """
        プロジェクトを削除
        
        Parameters
        ----------
        project_id : str
            プロジェクトID
            
        Returns
        -------
        bool
            削除されたかどうか
        """
        if project_id not in self.projects:
            return False
        
        self.projects.remove(project_id)
        self.updated_at = datetime.datetime.now().isoformat()
        return True
    
    def add_session(self, session_id: str) -> bool:
        """
        セッションを追加
        
        Parameters
        ----------
        session_id : str
            セッションID
            
        Returns
        -------
        bool
            追加されたかどうか
        """
        if session_id in self.sessions:
            return False
        
        self.sessions.add(session_id)
        self.updated_at = datetime.datetime.now().isoformat()
        return True
    
    def remove_session(self, session_id: str) -> bool:
        """
        セッションを削除
        
        Parameters
        ----------
        session_id : str
            セッションID
            
        Returns
        -------
        bool
            削除されたかどうか
        """
        if session_id not in self.sessions:
            return False
        
        self.sessions.remove(session_id)
        self.updated_at = datetime.datetime.now().isoformat()
        return True
    
    def get_member_roles(self) -> Dict[str, str]:
        """
        メンバーの役割の辞書を取得
        
        Returns
        -------
        Dict[str, str]
            user_id -> roleの辞書
        """
        return {user_id: member.role for user_id, member in self.members.items()}
    
    def has_access(self, user_id: str, min_role: str = "viewer") -> bool:
        """
        ユーザーがチームへのアクセス権を持っているかチェック
        
        Parameters
        ----------
        user_id : str
            ユーザーID
        min_role : str, optional
            必要な最低の役割, by default "viewer"
            
        Returns
        -------
        bool
            アクセス権があるかどうか
        """
        if user_id not in self.members:
            return False
        
        role = self.members[user_id].role
        
        # 権限チェック
        if min_role == "viewer":
            return role in ["viewer", "editor", "owner"]
        elif min_role == "editor":
            return role in ["editor", "owner"]
        elif min_role == "owner":
            return role == "owner"
        
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """
        辞書に変換
        
        Returns
        -------
        Dict[str, Any]
            チーム情報の辞書
        """
        return {
            'team_id': self.team_id,
            'name': self.name,
            'description': self.description,
            'owner_id': self.owner_id,
            'members': {user_id: member.to_dict() for user_id, member in self.members.items()},
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'projects': list(self.projects),
            'sessions': list(self.sessions)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Team':
        """
        辞書からインスタンスを作成
        
        Parameters
        ----------
        data : Dict[str, Any]
            チーム情報の辞書
            
        Returns
        -------
        Team
            作成されたインスタンス
        """
        team = cls(
            team_id=data['team_id'],
            name=data['name'],
            description=data.get('description', ''),
            owner_id=data.get('owner_id', '')
        )
        
        # メンバーの追加
        members_data = data.get('members', {})
        for user_id, member_data in members_data.items():
            team.members[user_id] = TeamMember.from_dict(member_data)
        
        # 日時情報
        team.created_at = data.get('created_at', team.created_at)
        team.updated_at = data.get('updated_at', team.updated_at)
        
        # プロジェクト情報
        team.projects = set(data.get('projects', []))
        
        # セッション情報
        team.sessions = set(data.get('sessions', []))
        
        return team


class TeamManager:
    """
    チーム管理クラス
    
    チームの作成、更新、削除、メンバー管理などの機能を提供します。
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        初期化
        
        Parameters
        ----------
        storage_path : Optional[str], optional
            チーム情報を保存するディレクトリパス, by default None
            Noneの場合はデフォルトの保存先を使用
        """
        if storage_path:
            self.storage_path = Path(storage_path)
        else:
            # デフォルトの保存先
            self.storage_path = Path.home() / ".sailing_analyzer" / "teams"
        
        # 保存先ディレクトリの作成
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # チームの辞書 (team_id -> Team)
        self.teams: Dict[str, Team] = {}
        
        # チーム情報の読み込み
        self._load_teams()
    
    def _load_teams(self) -> None:
        """チーム情報を読み込む"""
        teams_dir = self.storage_path
        
        # チームファイル（.json）を検索
        for team_file in teams_dir.glob("*.json"):
            try:
                with open(team_file, 'r', encoding='utf-8') as f:
                    team_data = json.load(f)
                    team = Team.from_dict(team_data)
                    self.teams[team.team_id] = team
            except Exception as e:
                print(f"チーム情報の読み込みに失敗しました: {str(e)}")
    
    def _save_team(self, team: Team) -> bool:
        """
        チーム情報を保存
        
        Parameters
        ----------
        team : Team
            保存するチーム
            
        Returns
        -------
        bool
            保存に成功したかどうか
        """
        team_file = self.storage_path / f"{team.team_id}.json"
        
        try:
            with open(team_file, 'w', encoding='utf-8') as f:
                json.dump(team.to_dict(), f, ensure_ascii=False, indent=2, default=str)
            return True
        except Exception as e:
            print(f"チーム情報の保存に失敗しました: {str(e)}")
            return False
    
    def create_team(self, name: str, description: str = "", owner_id: str = "") -> Optional[Team]:
        """
        新しいチームを作成
        
        Parameters
        ----------
        name : str
            チーム名
        description : str, optional
            説明, by default ""
        owner_id : str, optional
            オーナーのユーザーID, by default ""
            
        Returns
        -------
        Optional[Team]
            作成されたチーム（失敗時はNone）
        """
        team_id = str(uuid.uuid4())
        team = Team(team_id, name, description, owner_id)
        
        # オーナーをメンバーとして追加
        if owner_id:
            owner = TeamMember(owner_id, owner_id, role="owner")
            team.add_member(owner)
        
        # チームを保存
        if self._save_team(team):
            self.teams[team_id] = team
            return team
        
        return None
    
    def get_team(self, team_id: str) -> Optional[Team]:
        """
        チームを取得
        
        Parameters
        ----------
        team_id : str
            チームID
            
        Returns
        -------
        Optional[Team]
            チーム（存在しない場合はNone）
        """
        return self.teams.get(team_id)
    
    def update_team(self, team_id: str, name: Optional[str] = None, 
                   description: Optional[str] = None) -> bool:
        """
        チーム情報を更新
        
        Parameters
        ----------
        team_id : str
            チームID
        name : Optional[str], optional
            新しいチーム名, by default None (変更なし)
        description : Optional[str], optional
            新しい説明, by default None (変更なし)
            
        Returns
        -------
        bool
            更新に成功したかどうか
        """
        team = self.get_team(team_id)
        if not team:
            return False
        
        if name is not None:
            team.name = name
        
        if description is not None:
            team.description = description
        
        team.updated_at = datetime.datetime.now().isoformat()
        
        return self._save_team(team)
    
    def delete_team(self, team_id: str) -> bool:
        """
        チームを削除
        
        Parameters
        ----------
        team_id : str
            チームID
            
        Returns
        -------
        bool
            削除に成功したかどうか
        """
        if team_id not in self.teams:
            return False
        
        team_file = self.storage_path / f"{team_id}.json"
        
        try:
            if team_file.exists():
                team_file.unlink()
            
            del self.teams[team_id]
            return True
        except Exception as e:
            print(f"チームの削除に失敗しました: {str(e)}")
            return False
    
    def add_member_to_team(self, team_id: str, user_id: str, name: str,
                          email: Optional[str] = None, role: str = "viewer") -> bool:
        """
        チームにメンバーを追加
        
        Parameters
        ----------
        team_id : str
            チームID
        user_id : str
            ユーザーID
        name : str
            表示名
        email : Optional[str], optional
            メールアドレス, by default None
        role : str, optional
            役割, by default "viewer"
            
        Returns
        -------
        bool
            追加に成功したかどうか
        """
        team = self.get_team(team_id)
        if not team:
            return False
        
        member = TeamMember(user_id, name, email, role)
        if team.add_member(member):
            return self._save_team(team)
        
        return False
    
    def update_team_member(self, team_id: str, user_id: str, name: Optional[str] = None,
                          email: Optional[str] = None, role: Optional[str] = None) -> bool:
        """
        チームメンバー情報を更新
        
        Parameters
        ----------
        team_id : str
            チームID
        user_id : str
            ユーザーID
        name : Optional[str], optional
            新しい表示名, by default None (変更なし)
        email : Optional[str], optional
            新しいメールアドレス, by default None (変更なし)
        role : Optional[str], optional
            新しい役割, by default None (変更なし)
            
        Returns
        -------
        bool
            更新に成功したかどうか
        """
        team = self.get_team(team_id)
        if not team:
            return False
        
        if team.update_member(user_id, name, email, role):
            return self._save_team(team)
        
        return False
    
    def remove_member_from_team(self, team_id: str, user_id: str) -> bool:
        """
        チームからメンバーを削除
        
        Parameters
        ----------
        team_id : str
            チームID
        user_id : str
            ユーザーID
            
        Returns
        -------
        bool
            削除に成功したかどうか
        """
        team = self.get_team(team_id)
        if not team:
            return False
        
        if team.remove_member(user_id):
            return self._save_team(team)
        
        return False
    
    def get_user_teams(self, user_id: str) -> List[Team]:
        """
        ユーザーが所属するチームのリストを取得
        
        Parameters
        ----------
        user_id : str
            ユーザーID
            
        Returns
        -------
        List[Team]
            ユーザーが所属するチームのリスト
        """
        return [team for team in self.teams.values() if user_id in team.members]
    
    def add_project_to_team(self, team_id: str, project_id: str) -> bool:
        """
        チームにプロジェクトを追加
        
        Parameters
        ----------
        team_id : str
            チームID
        project_id : str
            プロジェクトID
            
        Returns
        -------
        bool
            追加に成功したかどうか
        """
        team = self.get_team(team_id)
        if not team:
            return False
        
        if team.add_project(project_id):
            return self._save_team(team)
        
        return False
    
    def remove_project_from_team(self, team_id: str, project_id: str) -> bool:
        """
        チームからプロジェクトを削除
        
        Parameters
        ----------
        team_id : str
            チームID
        project_id : str
            プロジェクトID
            
        Returns
        -------
        bool
            削除に成功したかどうか
        """
        team = self.get_team(team_id)
        if not team:
            return False
        
        if team.remove_project(project_id):
            return self._save_team(team)
        
        return False
    
    def add_session_to_team(self, team_id: str, session_id: str) -> bool:
        """
        チームにセッションを追加
        
        Parameters
        ----------
        team_id : str
            チームID
        session_id : str
            セッションID
            
        Returns
        -------
        bool
            追加に成功したかどうか
        """
        team = self.get_team(team_id)
        if not team:
            return False
        
        if team.add_session(session_id):
            return self._save_team(team)
        
        return False
    
    def remove_session_from_team(self, team_id: str, session_id: str) -> bool:
        """
        チームからセッションを削除
        
        Parameters
        ----------
        team_id : str
            チームID
        session_id : str
            セッションID
            
        Returns
        -------
        bool
            削除に成功したかどうか
        """
        team = self.get_team(team_id)
        if not team:
            return False
        
        if team.remove_session(session_id):
            return self._save_team(team)
        
        return False
    
    def get_teams_for_project(self, project_id: str) -> List[Team]:
        """
        プロジェクトが所属するチームのリストを取得
        
        Parameters
        ----------
        project_id : str
            プロジェクトID
            
        Returns
        -------
        List[Team]
            プロジェクトが所属するチームのリスト
        """
        return [team for team in self.teams.values() if project_id in team.projects]
    
    def get_teams_for_session(self, session_id: str) -> List[Team]:
        """
        セッションが所属するチームのリストを取得
        
        Parameters
        ----------
        session_id : str
            セッションID
            
        Returns
        -------
        List[Team]
            セッションが所属するチームのリスト
        """
        return [team for team in self.teams.values() if session_id in team.sessions]
    
    def get_all_teams(self) -> List[Team]:
        """
        すべてのチームのリストを取得
        
        Returns
        -------
        List[Team]
            すべてのチームのリスト
        """
        return list(self.teams.values())
    
    def check_user_access(self, user_id: str, item_id: str, item_type: str, 
                        required_role: str = "viewer") -> bool:
        """
        ユーザーがアイテムへのアクセス権を持っているかチェック
        
        Parameters
        ----------
        user_id : str
            ユーザーID
        item_id : str
            アイテムID
        item_type : str
            アイテムの種類 ("project" または "session")
        required_role : str, optional
            必要な最低の役割, by default "viewer"
            
        Returns
        -------
        bool
            アクセス権があるかどうか
        """
        if item_type == "project":
            teams = self.get_teams_for_project(item_id)
        elif item_type == "session":
            teams = self.get_teams_for_session(item_id)
        else:
            return False
        
        # いずれかのチームでアクセス権があればTrue
        for team in teams:
            if team.has_access(user_id, required_role):
                return True
        
        return False
