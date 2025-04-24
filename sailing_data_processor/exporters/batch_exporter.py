# -*- coding: utf-8 -*-
"""
sailing_data_processor.exporters.batch_exporter

バッチエクスポート処理を管理するモジュール
"""

import os
import threading
import time
import queue
import concurrent.futures
from typing import Dict, Any, List, Optional, Callable, Tuple
import uuid

from sailing_data_processor.exporters.base_exporter import BaseExporter
from sailing_data_processor.exporters.export_job import ExportJob
from sailing_data_processor.exporters.exporter_factory import ExporterFactory


class BatchExporter:
    """
    バッチエクスポート処理クラス
    
    複数セッションのエクスポートを管理する。
    並列処理によるバッチエクスポートと進行状況の追跡をサポートする。
    """
    
    def __init__(self, exporter_factory: Optional[ExporterFactory] = None, max_workers: int = 4):
        """
        初期化
        
        Parameters
        ----------
        exporter_factory : Optional[ExporterFactory], optional
            エクスポーターファクトリー, by default None
        max_workers : int, optional
            同時実行するワーカー数, by default 4
        """
        self.exporter_factory = exporter_factory
        self.max_workers = max_workers
        self.jobs = {}  # {job_id: ExportJob}
        self.job_lock = threading.Lock()
    
    def start_batch_export(self, sessions, exporter_id, output_dir=None, 
                          filename_template="{session_name}_{timestamp}", 
                          template_name="default", options=None,
                          progress_callback=None) -> str:
        """
        バッチエクスポートの開始
        
        Parameters
        ----------
        sessions : List
            エクスポート対象のセッションリスト
        exporter_id : str
            使用するエクスポーターID
        output_dir : str, optional
            出力先ディレクトリ
        filename_template : str, optional
            ファイル名テンプレート
        template_name : str, optional
            使用するテンプレート名
        options : Dict[str, Any], optional
            エクスポートオプション
        progress_callback : Callable, optional
            進行状況コールバック
            
        Returns
        -------
        str
            ジョブID
        """
        # 出力ディレクトリの設定
        if not output_dir:
            output_dir = os.path.join("exports", f"batch_{uuid.uuid4().hex[:8]}")
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # ジョブID生成
        job_id = str(uuid.uuid4())
        
        # エクスポートジョブの作成
        job = ExportJob(
            job_id=job_id,
            sessions=sessions,
            exporter_id=exporter_id,
            output_dir=output_dir,
            filename_template=filename_template,
            template_name=template_name,
            options=options,
            progress_callback=progress_callback
        )
        
        # ジョブの登録
        with self.job_lock:
            self.jobs[job_id] = job
        
        # バックグラウンドでジョブを実行
        thread = threading.Thread(
            target=self._run_batch_job,
            args=(job,),
            daemon=True
        )
        thread.start()
        
        return job_id
    
    def get_job_status(self, job_id) -> Optional[Dict[str, Any]]:
        """
        ジョブのステータスを取得
        
        Parameters
        ----------
        job_id : str
            ジョブID
            
        Returns
        -------
        Optional[Dict[str, Any]]
            ジョブステータス情報
        """
        with self.job_lock:
            job = self.jobs.get(job_id)
            
        if not job:
            return None
            
        return job.get_status()
    
    def cancel_job(self, job_id) -> bool:
        """
        ジョブのキャンセル
        
        Parameters
        ----------
        job_id : str
            ジョブID
            
        Returns
        -------
        bool
            キャンセル成功かどうか
        """
        with self.job_lock:
            job = self.jobs.get(job_id)
            
        if not job:
            return False
            
        return job.cancel()
    
    def cleanup_completed_jobs(self, max_age_seconds=3600) -> int:
        """
        完了したジョブを削除
        
        Parameters
        ----------
        max_age_seconds : int, optional
            保持する最大経過時間（秒）, by default 3600 (1時間)
            
        Returns
        -------
        int
            削除されたジョブ数
        """
        current_time = time.time()
        jobs_to_remove = []
        
        with self.job_lock:
            for job_id, job in self.jobs.items():
                status = job.get_status()
                
                # 完了したジョブが古い場合は削除対象
                if status["status"] in ["completed", "failed", "cancelled"]:
                    if status["end_time"] and current_time - status["end_time"] > max_age_seconds:
                        jobs_to_remove.append(job_id)
            
            # 削除実行
            for job_id in jobs_to_remove:
                del self.jobs[job_id]
        
        return len(jobs_to_remove)
    
    def _run_batch_job(self, job):
        """
        バッチジョブの実行
        
        Parameters
        ----------
        job : ExportJob
            実行するジョブ
        """
        # ジョブの準備と開始
        job.start()
        
        sessions = job.sessions
        exporter_id = job.exporter_id
        output_dir = job.output_dir
        filename_template = job.filename_template
        template_name = job.template_name
        options = job.options
        
        # エクスポーターの取得
        if not self.exporter_factory:
            job.complete(success=False, error="エクスポーターファクトリーが設定されていません")
            return
            
        exporter = self.exporter_factory.get_exporter(exporter_id)
        if not exporter:
            job.complete(success=False, error=f"エクスポーター '{exporter_id}' が見つかりません")
            return
        
        # スレッドプールを使用して並列処理
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # セッションごとの処理をSubmit
            future_to_session = {}
            for i, session in enumerate(sessions):
                # キャンセルされていたら中断
                if job.is_cancelled():
                    break
                
                # 出力ファイル名の生成
                timestamp = time.strftime("%Y%m%d%H%M%S")
                filename = filename_template.format(
                    session_name=session.name.replace(" ", "_"),
                    session_id=session.session_id,
                    timestamp=timestamp,
                    index=i
                )
                
                # 拡張子がなければ追加
                if not filename.endswith(f".{exporter.file_extension}"):
                    filename = f"{filename}.{exporter.file_extension}"
                
                output_path = os.path.join(output_dir, filename)
                
                # プログレスコールバックの作成
                session_index = i
                total_sessions = len(sessions)
                
                def session_progress_callback(progress, message):
                    # セッションの進捗をジョブ全体の進捗に変換
                    overall_progress = (session_index + progress) / total_sessions
                    job.update_progress(overall_progress, message)
                
                # エクスポートタスクの投入
                future = executor.submit(
                    self._export_single_session,
                    exporter=exporter,
                    session=session,
                    output_path=output_path,
                    template_name=template_name,
                    options=options,
                    progress_callback=session_progress_callback
                )
                
                future_to_session[future] = (session.session_id, session.name)
            
            # 完了したタスクを処理
            for future in concurrent.futures.as_completed(future_to_session):
                # キャンセルされていたら中断
                if job.is_cancelled():
                    executor.shutdown(wait=False)
                    job.complete(success=False, error="ジョブがキャンセルされました")
                    return
                
                session_id, session_name = future_to_session[future]
                try:
                    output_path = future.result()
                    results.append({
                        "session_id": session_id,
                        "session_name": session_name,
                        "success": True,
                        "output_path": output_path
                    })
                except Exception as e:
                    results.append({
                        "session_id": session_id,
                        "session_name": session_name,
                        "success": False,
                        "error": str(e)
                    })
        
        # 処理完了
        if job.is_cancelled():
            job.complete(success=False, error="ジョブがキャンセルされました", results=results)
            return
            
        all_success = all(result["success"] for result in results)
        if all_success:
            job.complete(success=True, results=results)
        else:
            job.complete(
                success=False, 
                error="一部のエクスポートが失敗しました",
                results=results
            )
    
    def _export_single_session(self, exporter, session, output_path, 
                             template_name, options, progress_callback):
        """
        単一セッションのエクスポート処理
        
        Parameters
        ----------
        exporter : BaseExporter
            使用するエクスポーター
        session : SessionModel
            エクスポートするセッション
        output_path : str
            出力先パス
        template_name : str
            使用するテンプレート名
        options : Dict[str, Any]
            エクスポートオプション
        progress_callback : Callable
            進行状況コールバック
            
        Returns
        -------
        str
            エクスポートされたファイルのパス
        """
        try:
            # エクスポーター固有の処理
            # SessionExporterとBaseExporterの両方に対応するための処理分岐
            if hasattr(exporter, 'set_progress_callback'):
                exporter.set_progress_callback(progress_callback)
            
            if hasattr(exporter, 'export_session'):
                # SessionExporterの場合
                output_path = exporter.export_session(
                    session=session,
                    output_path=output_path,
                    template=template_name,
                    options=options
                )
            elif hasattr(exporter, 'export_data'):
                # BaseExporterの場合
                # セッションからデータコンテナを取得する必要がある
                container = self._get_data_container_from_session(session)
                if container:
                    output_path = exporter.export_data(
                        container=container,
                        output_path=output_path,
                        metadata=session.metadata
                    )
                else:
                    raise ValueError("セッションからデータコンテナを取得できませんでした")
            else:
                raise ValueError(f"サポートされていないエクスポーター形式です: {type(exporter)}")
                
            return output_path
            
        except Exception as e:
            # エラーをリレー
            raise Exception(f"セッション '{session.name}' のエクスポート中にエラーが発生しました: {str(e)}")
    
    def _get_data_container_from_session(self, session):
        """
        セッションからデータコンテナを取得
        
        Parameters
        ----------
        session : SessionModel
            セッション
            
        Returns
        -------
        Optional[GPSDataContainer]
            データコンテナ、または取得できない場合はNone
        """
        # ここは実際の実装に合わせて調整が必要
        # セッションからデータコンテナを取得する方法は
        # プロジェクトの構造によって異なる
        
        # 例: セッションのresultから最新のデータを取得
        if hasattr(session, 'results') and session.results:
            # 最新の結果を検索
            latest_result = None
            for result in session.results:
                if result.get('is_current', False):
                    latest_result = result
                    break
            
            if latest_result and hasattr(latest_result, 'data'):
                return latest_result.data
        
        # データが見つからない場合はNone
        return None
