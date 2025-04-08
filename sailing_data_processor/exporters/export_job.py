"""
sailing_data_processor.exporters.export_job

エクスポートジョブを管理するモジュール
"""

import time
import threading
from typing import Dict, List, Any, Optional, Callable
import uuid


class ExportJob:
    """
    エクスポートジョブクラス
    
    バッチエクスポート処理のジョブを管理するためのクラスです。
    ジョブの進行状況や結果を追跡します。
    """
    
    def __init__(self, job_id: str, sessions: List, exporter_id: str,
                output_dir: str, filename_template: str = "{session_name}_{timestamp}",
                template_name: str = "default", options: Optional[Dict[str, Any]] = None,
                progress_callback: Optional[Callable[[float, str], None]] = None):
        """
        初期化
        
        Parameters
        ----------
        job_id : str
            ジョブID
        sessions : List
            エクスポート対象のセッションリスト
        exporter_id : str
            使用するエクスポーターID
        output_dir : str
            出力先ディレクトリ
        filename_template : str, optional
            ファイル名テンプレート
        template_name : str, optional
            使用するテンプレート名
        options : Optional[Dict[str, Any]], optional
            エクスポートオプション
        progress_callback : Optional[Callable[[float, str], None]], optional
            進行状況コールバック
        """
        self.job_id = job_id
        self.sessions = sessions
        self.exporter_id = exporter_id
        self.output_dir = output_dir
        self.filename_template = filename_template
        self.template_name = template_name
        self.options = options or {}
        self.progress_callback = progress_callback
        
        # ジョブ状態
        self.start_time = None
        self.end_time = None
        self.status = "created"  # created, running, completed, failed, cancelled
        self.progress = 0.0  # 0.0 ~ 1.0
        self.message = ""
        self.error = None
        self.results = []
        
        # 制御用
        self._cancelled = False
        self._lock = threading.Lock()
    
    def start(self) -> None:
        """ジョブを開始"""
        with self._lock:
            if self.status != "created":
                return
            
            self.start_time = time.time()
            self.status = "running"
            self.progress = 0.0
            self.message = "ジョブを開始しています..."
    
    def update_progress(self, progress: float, message: str) -> None:
        """
        進行状況を更新
        
        Parameters
        ----------
        progress : float
            進行状況（0.0 ~ 1.0）
        message : str
            ステータスメッセージ
        """
        with self._lock:
            self.progress = progress
            self.message = message
            
            # コールバックがあれば呼び出し
            if self.progress_callback:
                try:
                    self.progress_callback(progress, message)
                except Exception:
                    pass
    
    def complete(self, success: bool = True, error: Optional[str] = None, 
               results: Optional[List[Dict[str, Any]]] = None) -> None:
        """
        ジョブを完了
        
        Parameters
        ----------
        success : bool, optional
            成功したかどうか
        error : Optional[str], optional
            エラーメッセージ
        results : Optional[List[Dict[str, Any]]], optional
            処理結果
        """
        with self._lock:
            self.end_time = time.time()
            
            if success:
                self.status = "completed"
                self.progress = 1.0
                self.message = "ジョブが完了しました"
            else:
                self.status = "failed"
                self.error = error
                self.message = f"ジョブが失敗しました: {error}"
            
            if results:
                self.results = results
    
    def cancel(self) -> bool:
        """
        ジョブをキャンセル
        
        Returns
        -------
        bool
            キャンセルに成功したかどうか
        """
        with self._lock:
            # 既に完了している場合はキャンセル不可
            if self.status in ["completed", "failed", "cancelled"]:
                return False
            
            self._cancelled = True
            self.status = "cancelled"
            self.end_time = time.time()
            self.message = "ジョブがキャンセルされました"
            return True
    
    def is_cancelled(self) -> bool:
        """
        キャンセルされたかどうかを確認
        
        Returns
        -------
        bool
            キャンセルされた場合はTrue
        """
        with self._lock:
            return self._cancelled
    
    def get_status(self) -> Dict[str, Any]:
        """
        現在のジョブ状態を取得
        
        Returns
        -------
        Dict[str, Any]
            ジョブ状態の辞書
        """
        with self._lock:
            return {
                "job_id": self.job_id,
                "status": self.status,
                "progress": self.progress,
                "message": self.message,
                "start_time": self.start_time,
                "end_time": self.end_time,
                "error": self.error,
                "exporter_id": self.exporter_id,
                "template_name": self.template_name,
                "output_dir": self.output_dir,
                "results": self.results,
                "session_count": len(self.sessions)
            }
