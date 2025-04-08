"""
sailing_data_processor.search.search_engine

プロジェクトやセッションの検索エンジンを提供するモジュール
"""

from typing import Dict, List, Any, Optional, Union, Set, Callable
import re
from datetime import datetime, timedelta

from sailing_data_processor.project.project_model import Project, Session, AnalysisResult


class SearchEngine:
    """
    検索エンジンクラス
    
    プロジェクト、セッション、分析結果などのデータを検索するための機能を提供します。
    """
    
    def __init__(self):
        """初期化"""
        self.stopwords = {'の', 'に', 'は', 'を', 'が', 'と', 'で', 'た', 'から'}
        
    def tokenize(self, text: str) -> List[str]:
        """
        テキストをトークン化
        
        Parameters
        ----------
        text : str
            トークン化するテキスト
            
        Returns
        -------
        List[str]
            トークンのリスト
        """
        # 簡易的なトークン化（空白と記号で分割）
        if not text:
            return []
        
        # 小文字化と記号の置換
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # トークン化と空トークンの除去
        tokens = [token for token in text.split() if token and token not in self.stopwords]
        return tokens
    
    def _calc_relevance(self, tokens: List[str], target: str) -> float:
        """
        検索語とターゲットの関連性スコアを計算
        
        Parameters
        ----------
        tokens : List[str]
            検索トークンのリスト
        target : str
            検索対象のテキスト
            
        Returns
        -------
        float
            関連性スコア
        """
        if not tokens or not target:
            return 0.0
        
        target = target.lower()
        score = 0.0
        
        for token in tokens:
            # 完全一致は高いスコア
            if token in target.split():
                score += 1.0
            # 部分一致はより低いスコア
            elif token in target:
                score += 0.5
        
        return score
    
    def search_projects(self, 
                       projects: List[Project], 
                       query: str, 
                       tags: Optional[List[str]] = None,
                       date_range: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """
        プロジェクトを検索
        
        Parameters
        ----------
        projects : List[Project]
            検索対象のプロジェクトリスト
        query : str
            検索クエリ
        tags : Optional[List[str]], optional
            フィルタするタグのリスト, by default None
        date_range : Optional[Dict[str, str]], optional
            日付範囲（'start'と'end'のキーを持つ辞書）, by default None
            
        Returns
        -------
        List[Dict[str, Any]]
            マッチしたプロジェクトの情報を含む辞書のリスト
        """
        results = []
        
        # クエリをトークン化
        tokens = self.tokenize(query)
        
        for project in projects:
            # 初期スコアは0
            relevance = 0.0
            
            # 名前の検索スコア（重み付け）
            name_score = self._calc_relevance(tokens, project.name)
            relevance += name_score * 2.0  # 名前は重み付けを高く
            
            # 説明の検索スコア
            desc_score = self._calc_relevance(tokens, project.description)
            relevance += desc_score
            
            # メタデータの検索スコア
            meta_score = 0.0
            for key, value in project.metadata.items():
                if isinstance(value, str):
                    meta_score += self._calc_relevance(tokens, value) * 0.5  # メタデータは重み付けを低く
            relevance += meta_score
            
            # タグフィルタリング
            if tags and not all(tag in project.tags for tag in tags):
                continue
            
            # 日付範囲フィルタリング
            if date_range:
                project_date = datetime.fromisoformat(project.created_at)
                
                if date_range.get('start'):
                    start_date = datetime.fromisoformat(date_range['start'])
                    if project_date < start_date:
                        continue
                
                if date_range.get('end'):
                    end_date = datetime.fromisoformat(date_range['end'])
                    if project_date > end_date:
                        continue
            
            # 検索クエリが空の場合や関連性スコアが0より大きい場合に結果に追加
            if not tokens or relevance > 0:
                results.append({
                    'project': project,
                    'relevance': relevance,
                    'matched_in': {
                        'name': name_score > 0,
                        'description': desc_score > 0,
                        'metadata': meta_score > 0
                    }
                })
        
        # 関連性スコアでソート
        results.sort(key=lambda x: x['relevance'], reverse=True)
        return results
    
    def search_sessions(self, 
                       sessions: List[Session], 
                       query: str, 
                       tags: Optional[List[str]] = None,
                       date_range: Optional[Dict[str, str]] = None,
                       categories: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        セッションを検索
        
        Parameters
        ----------
        sessions : List[Session]
            検索対象のセッションリスト
        query : str
            検索クエリ
        tags : Optional[List[str]], optional
            フィルタするタグのリスト, by default None
        date_range : Optional[Dict[str, str]], optional
            日付範囲（'start'と'end'のキーを持つ辞書）, by default None
        categories : Optional[List[str]], optional
            フィルタするカテゴリのリスト, by default None
            
        Returns
        -------
        List[Dict[str, Any]]
            マッチしたセッションの情報を含む辞書のリスト
        """
        results = []
        
        # クエリをトークン化
        tokens = self.tokenize(query)
        
        for session in sessions:
            # 初期スコアは0
            relevance = 0.0
            
            # 名前の検索スコア（重み付け）
            name_score = self._calc_relevance(tokens, session.name)
            relevance += name_score * 2.0  # 名前は重み付けを高く
            
            # 説明の検索スコア
            desc_score = self._calc_relevance(tokens, session.description)
            relevance += desc_score
            
            # メタデータの検索スコア
            meta_score = 0.0
            for key, value in session.metadata.items():
                if isinstance(value, str):
                    meta_score += self._calc_relevance(tokens, value) * 0.5  # メタデータは重み付けを低く
            relevance += meta_score
            
            # タグフィルタリング
            if tags and not all(tag in session.tags for tag in tags):
                continue
            
            # カテゴリフィルタリング
            if categories and hasattr(session, 'category') and session.category not in categories:
                continue
            
            # 日付範囲フィルタリング
            if date_range:
                session_date = datetime.fromisoformat(session.created_at)
                
                if date_range.get('start'):
                    start_date = datetime.fromisoformat(date_range['start'])
                    if session_date < start_date:
                        continue
                
                if date_range.get('end'):
                    end_date = datetime.fromisoformat(date_range['end'])
                    if session_date > end_date:
                        continue
            
            # 検索クエリが空の場合や関連性スコアが0より大きい場合に結果に追加
            if not tokens or relevance > 0:
                results.append({
                    'session': session,
                    'relevance': relevance,
                    'matched_in': {
                        'name': name_score > 0,
                        'description': desc_score > 0,
                        'metadata': meta_score > 0
                    }
                })
        
        # 関連性スコアでソート
        results.sort(key=lambda x: x['relevance'], reverse=True)
        return results
    
    def search_analysis_results(self, 
                               results: List[AnalysisResult], 
                               query: str,
                               result_types: Optional[List[str]] = None,
                               date_range: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """
        分析結果を検索
        
        Parameters
        ----------
        results : List[AnalysisResult]
            検索対象の分析結果リスト
        query : str
            検索クエリ
        result_types : Optional[List[str]], optional
            フィルタする結果タイプのリスト, by default None
        date_range : Optional[Dict[str, str]], optional
            日付範囲（'start'と'end'のキーを持つ辞書）, by default None
            
        Returns
        -------
        List[Dict[str, Any]]
            マッチした分析結果の情報を含む辞書のリスト
        """
        search_results = []
        
        # クエリをトークン化
        tokens = self.tokenize(query)
        
        for result in results:
            # 初期スコアは0
            relevance = 0.0
            
            # 名前の検索スコア（重み付け）
            name_score = self._calc_relevance(tokens, result.name)
            relevance += name_score * 2.0  # 名前は重み付けを高く
            
            # 説明の検索スコア
            desc_score = self._calc_relevance(tokens, result.description)
            relevance += desc_score
            
            # 結果タイプの検索スコア
            type_score = self._calc_relevance(tokens, result.result_type)
            relevance += type_score * 1.5  # タイプも重み付けを高く
            
            # メタデータの検索スコア
            meta_score = 0.0
            for key, value in result.metadata.items():
                if isinstance(value, str):
                    meta_score += self._calc_relevance(tokens, value) * 0.5  # メタデータは重み付けを低く
            relevance += meta_score
            
            # 結果タイプフィルタリング
            if result_types and result.result_type not in result_types:
                continue
            
            # 日付範囲フィルタリング
            if date_range:
                result_date = datetime.fromisoformat(result.created_at)
                
                if date_range.get('start'):
                    start_date = datetime.fromisoformat(date_range['start'])
                    if result_date < start_date:
                        continue
                
                if date_range.get('end'):
                    end_date = datetime.fromisoformat(date_range['end'])
                    if result_date > end_date:
                        continue
            
            # 検索クエリが空の場合や関連性スコアが0より大きい場合に結果に追加
            if not tokens or relevance > 0:
                search_results.append({
                    'result': result,
                    'relevance': relevance,
                    'matched_in': {
                        'name': name_score > 0,
                        'description': desc_score > 0,
                        'result_type': type_score > 0,
                        'metadata': meta_score > 0
                    }
                })
        
        # 関連性スコアでソート
        search_results.sort(key=lambda x: x['relevance'], reverse=True)
        return search_results
