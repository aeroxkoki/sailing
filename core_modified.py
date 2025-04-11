# sailing_data_processor/core.py
"""
セーリング戦略分析システム - コアモジュール

SailingDataProcessorクラスを提供し、データ処理の中心的な役割を担う
"""

import pandas as pd
import numpy as np
import gpxpy
import io
import math
from geopy.distance import geodesic
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Union, Any
import warnings
import gc
import os
import time
from concurrent.futures import ThreadPoolExecutor
from functools import partial

# 内部モジュールのインポート
from sailing_data_processor.wind_estimator import WindEstimator
from sailing_data_processor.performance_optimizer import PerformanceOptimizer
from sailing_data_processor.boat_data_fusion import BoatDataFusionModel
from sailing_data_processor.wind_field_interpolator import WindFieldInterpolator

class SailingDataProcessor:
    """セーリングデータ処理クラス - GPSデータの読み込み、前処理、分析を担当"""
    
    def __init__(self):
        """初期化"""
        self.boat_data = {}  # 艇ID: DataFrameの辞書
        self.processed_data = {}  # 処理済みデータ
        self.synced_data = {}  # 時間同期済みデータ
        self.max_boats = 100  # 最大処理可能艇数
        
        # 風推定器と最適化ユーティリティを初期化
        self._wind_estimator = WindEstimator()
        self._optimizer = PerformanceOptimizer()
        
        # 必要に応じて融合モデルと補間器を初期化（遅延初期化）
        self._fusion_model = None
        self._interpolator = None
        
        # 推定された風向風速データ
        self.wind_estimates = {}  # 艇ID: 風推定DataFrameの辞書
        self.wind_field_data = {}  # 時間: 風の場データの辞書
        
        # パフォーマンス統計情報
        self.performance_stats = {
            'load_time': 0,  # データ読み込み時間
            'process_time': 0,  # 処理時間
            'sync_time': 0,  # 同期時間
            'wind_estimation_time': 0,  # 風推定時間
            'total_points_processed': 0,  # 処理されたデータポイント総数
            'memory_usage': []  # メモリ使用量の履歴
        }
        
        # コンフィグ
        self.config = {
            'auto_optimize': True,  # 自動最適化の有効/無効
            'use_parallel': True,  # 並列処理の有効/無効
            'downsample_threshold': 1000000,  # ダウンサンプリングの閾値（ポイント数）
            'downsample_target': 0.5,  # ダウンサンプリング目標（元のサイズに対する比率）
            'chunking_threshold': 50000,  # チャンク分割の閾値（ポイント数）
            'log_performance': False,  # パフォーマンスログの有効/無効
            'auto_gc': True,  # 自動ガベージコレクションの有効/無効
            'default_tack_angle': 30.0,  # デフォルトのタック検出角度
            'wind_estimate_confidence_threshold': 0.6,  # 風推定の信頼度閾値
            'memory_threshold': 1000,  # メモリ自動クリーンアップの閾値（MB）
            'chunk_processing': True,  # 大規模データの分割処理
            'chunk_size': 10000  # 1チャンクあたりの最大データポイント数
        }
        
        # メモリモニタリング
        self._last_gc_time = time.time()
        self._mem_check_interval = 30  # メモリチェック間隔（秒）
        
    # メモリ管理メソッドを追加
    def _check_memory_usage(self):
        """メモリ使用量をチェックし、必要に応じてガベージコレクションを実行"""
        if not self.config['auto_gc']:
            return
            
        current_time = time.time()
        # 定期的なチェック（_mem_check_interval秒ごと）
        if current_time - self._last_gc_time > self._mem_check_interval:
            memory_usage = self._optimizer.get_memory_usage() 
            
            # メモリ使用量が閾値を超えたらガベージコレクション
            if memory_usage > self.config['memory_threshold']:
                self.cleanup_memory()
                
            self._last_gc_time = current_time
            
    def cleanup_memory(self):
        """明示的にメモリをクリーンアップ"""
        # 参照を解除して大きなオブジェクトを開放
        temp_data = {}
        
        # 一時変数を解放
        temp_vars = [v for v in dir(self) if v.startswith('_temp_')]
        for var in temp_vars:
            if hasattr(self, var):
                delattr(self, var)
        
        # 明示的なガベージコレクション
        gc.collect()
        
        if self.config['log_performance']:
            memory_usage = self._optimizer.get_memory_usage()
            self.performance_stats['memory_usage'].append({
                'timestamp': datetime.now().isoformat(),
                'memory_mb': memory_usage,
                'operation': 'cleanup'
            })
            
    def _log_performance_step(self, step_name):
        """パフォーマンスログのステップを記録"""
        if self.config['log_performance']:
            memory_usage = self._optimizer.get_memory_usage()
            self.performance_stats['memory_usage'].append({
                'timestamp': datetime.now().isoformat(),
                'memory_mb': memory_usage,
                'operation': step_name
            })
            
        # 定期的なメモリチェック
        self._check_memory_usage()
            
    # データロード処理の最適化
    def load_multiple_files(self, file_list: List[Tuple[str, bytes, str]]) -> Dict[str, pd.DataFrame]:
        """
        複数のファイルを読み込み、艇IDとデータフレームの辞書を返す
        
        Parameters:
        -----------
        file_list : List[Tuple[str, bytes, str]]
            読み込むファイルのリスト（ファイル名, ファイル内容, ファイル形式）
            
        Returns:
        --------
        Dict[str, pd.DataFrame]
            艇ID: DataFrameの辞書
        """
        # パフォーマンス計測開始
        start_time = time.time()
        self._log_performance_step("load_start")
        
        # 結果格納用の辞書
        result_data = {}
        
        # 並列処理
        if self.config['use_parallel'] and len(file_list) > 1:
            # ThreadPoolExecutorで並列処理
            with ThreadPoolExecutor() as executor:
                # 各ファイルの処理を並列化
                futures = []
                for filename, content, file_format in file_list:
                    future = executor.submit(self._load_single_file, filename, content, file_format)
                    futures.append(future)
                
                # 結果を収集
                for future in futures:
                    if future.result() is not None:
                        boat_id, df = future.result()
                        if boat_id is not None:
                            result_data[boat_id] = df
        else:
            # 逐次処理
            for filename, content, file_format in file_list:
                result = self._load_single_file(filename, content, file_format)
                if result is not None:
                    boat_id, df = result
                    if boat_id is not None:
                        result_data[boat_id] = df
        
        # 結果をインスタンス変数に保存
        self.boat_data.update(result_data)
        
        # パフォーマンス計測終了
        load_time = time.time() - start_time
        self.performance_stats['load_time'] += load_time
        
        # 処理されたデータポイント数を記録
        total_points = sum(len(df) for df in result_data.values())
        self.performance_stats['total_points_processed'] += total_points
        
        self._log_performance_step("load_complete")
        
        return result_data
        
    def _load_single_file(self, filename: str, content: bytes, file_format: str) -> Optional[Tuple[str, pd.DataFrame]]:
        """
        単一ファイルを読み込む（並列処理用）
        
        Parameters:
        -----------
        filename : str
            ファイル名
        content : bytes
            ファイル内容
        file_format : str
            ファイル形式 (csv, gpx, tcx, fit)
            
        Returns:
        --------
        Optional[Tuple[str, pd.DataFrame]]
            (艇ID, DataFrame)のタプル、エラー時はNone
        """
        try:
            # ファイル形式に応じた処理
            df = None
            if file_format.lower() == 'csv':
                # CSVファイルの読み込み
                try:
                    # 最初はUTF-8で試す
                    df = pd.read_csv(io.BytesIO(content), parse_dates=['timestamp'])
                except (UnicodeDecodeError, pd.errors.ParserError):
                    # UTF-8で失敗したらShift-JISで試す
                    try:
                        df = pd.read_csv(io.BytesIO(content), encoding='shift-jis', parse_dates=['timestamp'])
                    except Exception:
                        # それでも失敗したら検出を試みる
                        df = pd.read_csv(io.BytesIO(content), encoding='latin1', parse_dates=['timestamp'])
            
            elif file_format.lower() == 'gpx':
                # GPXファイルの読み込み
                gpx = gpxpy.parse(io.BytesIO(content))
                points = []
                
                for track in gpx.tracks:
                    for segment in track.segments:
                        for point in segment.points:
                            points.append({
                                'timestamp': point.time,
                                'latitude': point.latitude,
                                'longitude': point.longitude,
                                'elevation': point.elevation
                            })
                
                df = pd.DataFrame(points)
            
            elif file_format.lower() in ['tcx', 'fit']:
                # TCX/FITファイルはカスタム処理が必要（簡略化）
                raise NotImplementedError(f"{file_format}形式はまだ実装されていません")
            
            else:
                raise ValueError(f"不明なファイル形式: {file_format}")
            
            # データの基本検証
            if df is None or len(df) == 0:
                warnings.warn(f"ファイル {filename} にデータがありません")
                return None
            
            # 必須カラムの確認
            required_columns = ['timestamp', 'latitude', 'longitude']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                warnings.warn(f"ファイル {filename} に必須カラム {missing_columns} がありません")
                return None
            
            # タイムスタンプを datetime 型に変換（すでに変換済みの場合はスキップ）
            if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # 名前からボートIDを抽出
            boat_id = os.path.splitext(os.path.basename(filename))[0]
            
            # boat_id列を追加
            df['boat_id'] = boat_id
            
            # 大規模データセットの場合はダウンサンプリング
            if len(df) > self.config['downsample_threshold'] and self.config['auto_optimize']:
                # ダウンサンプリング率を計算
                target_size = int(len(df) * self.config['downsample_target'])
                
                # ダウンサンプリング（時間的な一貫性を保持）
                df = df.sort_values('timestamp')
                step = max(1, len(df) // target_size)
                df = df.iloc[::step].copy()
                
                warnings.warn(f"ファイル {filename} は大きすぎるためダウンサンプリングされました（{len(df)}ポイント）")
            
            # チャンク処理の場合はデータを分割
            if self.config['chunk_processing'] and len(df) > self.config['chunk_size']:
                # データをチャンクに分割して処理
                chunk_size = self.config['chunk_size']
                chunks = [df[i:i+chunk_size] for i in range(0, len(df), chunk_size)]
                
                # 各チャンクを処理して結合
                processed_chunks = []
                for i, chunk in enumerate(chunks):
                    # メモリリークを防ぐために各チャンクを個別にコピー
                    chunk_copy = chunk.copy()
                    # 必要な処理をここで実行
                    processed_chunks.append(chunk_copy)
                    # 明示的に不要なオブジェクトを削除
                    del chunk_copy
                    
                    # 定期的なガベージコレクション
                    if i % 5 == 0:
                        gc.collect()
                
                # チャンクを結合
                df = pd.concat(processed_chunks, ignore_index=True)
                del processed_chunks
                
            return boat_id, df
            
        except Exception as e:
            warnings.warn(f"ファイル {filename} の読み込み中にエラーが発生しました: {str(e)}")
            return None

    def estimate_wind_from_boat(self, boat_id: str, **kwargs) -> Optional[pd.DataFrame]:
        """
        指定した艇のGPSデータから風向風速を推定
        
        Parameters:
        -----------
        boat_id : str
            風向風速を推定する艇のID
        **kwargs
            WindEstimatorに渡す追加パラメータ
            
        Returns:
        --------
        Optional[pd.DataFrame]
            風向風速の推定結果を含むDataFrame、失敗時はNone
        """
        # パフォーマンス計測開始
        start_time = time.time()
        self._log_performance_step(f"wind_estimation_start_{boat_id}")
        
        # 前処理済みデータがあればそれを使用、なければ生データを使用
        if boat_id in self.processed_data:
            gps_data = self.processed_data[boat_id]
        elif boat_id in self.boat_data:
            gps_data = self.boat_data[boat_id]
        else:
            warnings.warn(f"艇 {boat_id} のデータが見つかりません")
            return None
        
        try:
            # 風推定のパラメータ
            min_tack_angle = kwargs.get('min_tack_angle', self.config['default_tack_angle'])
            boat_type = kwargs.get('boat_type', 'default')
            use_bayesian = kwargs.get('use_bayesian', True)
            
            # チャンク処理の場合はデータを分割
            if self.config['chunk_processing'] and len(gps_data) > self.config['chunk_size']:
                # データをチャンクに分割して処理
                chunk_size = self.config['chunk_size']
                chunks = [gps_data[i:i+chunk_size] for i in range(0, len(gps_data), chunk_size)]
                
                # 各チャンクを処理して結合
                wind_chunks = []
                for i, chunk in enumerate(chunks):
                    # 各チャンクのコピーを作成
                    chunk_copy = chunk.copy()
                    
                    # 風推定実行
                    wind_result = self.wind_estimator.estimate_wind_from_single_boat(
                        gps_data=chunk_copy,
                        min_tack_angle=min_tack_angle,
                        boat_type=boat_type,
                        use_bayesian=use_bayesian
                    )
                    
                    wind_chunks.append(wind_result)
                    
                    # 明示的に不要なオブジェクトを削除
                    del chunk_copy
                    
                    # 定期的なガベージコレクション
                    if i % 5 == 0:
                        gc.collect()
                
                # チャンクを結合
                wind_data = pd.concat(wind_chunks, ignore_index=True)
                del wind_chunks
                
            else:
                # チャンク処理なしの場合は一括処理
                wind_data = self.wind_estimator.estimate_wind_from_single_boat(
                    gps_data=gps_data,
                    min_tack_angle=min_tack_angle,
                    boat_type=boat_type,
                    use_bayesian=use_bayesian
                )
            
            # 結果をインスタンス変数に保存
            self.wind_estimates[boat_id] = wind_data
            
            # パフォーマンス計測終了
            wind_time = time.time() - start_time
            self.performance_stats['wind_estimation_time'] += wind_time
            
            self._log_performance_step(f"wind_estimation_complete_{boat_id}")
            
            return wind_data
            
        except Exception as e:
            warnings.warn(f"艇 {boat_id} の風推定中にエラーが発生しました: {str(e)}")
            import traceback
            traceback.print_exc()
            
            self._log_performance_step(f"wind_estimation_error_{boat_id}")
            
            return None
