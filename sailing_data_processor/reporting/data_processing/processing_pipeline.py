# -*- coding: utf-8 -*-
"""
sailing_data_processor.reporting.data_processing.processing_pipeline

データ処理パイプラインを提供するモジュールです。
変換、集計、計算の各処理を組み合わせたパイプラインを構築し、
一連のデータ処理を実行する機能を実装します。
"""

from typing import Dict, List, Any, Optional, Union, Tuple, Callable
import pandas as pd
import numpy as np

from sailing_data_processor.reporting.data_processing.transforms import (
    DataTransformer, SmoothingTransform, ResamplingTransform, NormalizationTransform
)
from sailing_data_processor.reporting.data_processing.aggregators import (
    DataAggregator, TimeAggregator, SpatialAggregator, CategoryAggregator
)
from sailing_data_processor.reporting.data_processing.calculators import (
    BaseCalculator, PerformanceCalculator, StatisticalCalculator, CustomFormulaCalculator
)


class ProcessingStep:
    """
    処理ステップの基底クラス
    
    データ処理パイプラインの個々のステップを表現します。
    """
    
    def __init__(self, step_type: str, processor: Union[DataTransformer, DataAggregator, BaseCalculator], name: str = None):
        """
        初期化
        
        Parameters
        ----------
        step_type : str
            ステップタイプ（'transform', 'aggregate', 'calculate'）
        processor : Union[DataTransformer, DataAggregator, BaseCalculator]
            処理を実行するプロセッサオブジェクト
        name : str, optional
            ステップの名前, by default None
        """
        self.step_type = step_type
        self.processor = processor
        self.name = name or f"{step_type}_{id(self)}"
    
    def execute(self, data: Any) -> Any:
        """
        処理ステップを実行
        
        Parameters
        ----------
        data : Any
            入力データ
            
        Returns
        -------
        Any
            処理結果データ
        """
        if self.step_type == 'transform':
            return self.processor.transform(data)
        elif self.step_type == 'aggregate':
            return self.processor.aggregate(data)
        elif self.step_type == 'calculate':
            return self.processor.calculate(data)
        else:
            # 不明なステップタイプの場合は何もしない
            return data
    
    def get_config(self) -> Dict[str, Any]:
        """
        ステップの設定を取得
        
        Returns
        -------
        Dict[str, Any]
            ステップの設定
        """
        return {
            'step_type': self.step_type,
            'name': self.name,
            'processor_type': type(self.processor).__name__,
            'params': self.processor.params
        }
    
    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> 'ProcessingStep':
        """
        設定からステップを作成
        
        Parameters
        ----------
        config : Dict[str, Any]
            ステップの設定
            
        Returns
        -------
        ProcessingStep
            作成されたステップ
        
        Raises
        ------
        ValueError
            不明なプロセッサタイプの場合
        """
        step_type = config['step_type']
        name = config.get('name')
        processor_type = config['processor_type']
        params = config.get('params', {})
        
        # プロセッサの作成
        processor = None
        
        if step_type == 'transform':
            if processor_type == 'SmoothingTransform':
                processor = SmoothingTransform(params)
            elif processor_type == 'ResamplingTransform':
                processor = ResamplingTransform(params)
            elif processor_type == 'NormalizationTransform':
                processor = NormalizationTransform(params)
            else:
                raise ValueError(f"不明な変換プロセッサタイプ: {processor_type}")
        
        elif step_type == 'aggregate':
            if processor_type == 'TimeAggregator':
                processor = TimeAggregator(params)
            elif processor_type == 'SpatialAggregator':
                processor = SpatialAggregator(params)
            elif processor_type == 'CategoryAggregator':
                processor = CategoryAggregator(params)
            else:
                raise ValueError(f"不明な集計プロセッサタイプ: {processor_type}")
        
        elif step_type == 'calculate':
            if processor_type == 'PerformanceCalculator':
                processor = PerformanceCalculator(params)
            elif processor_type == 'StatisticalCalculator':
                processor = StatisticalCalculator(params)
            elif processor_type == 'CustomFormulaCalculator':
                processor = CustomFormulaCalculator(params)
            else:
                raise ValueError(f"不明な計算プロセッサタイプ: {processor_type}")
        
        else:
            raise ValueError(f"不明なステップタイプ: {step_type}")
        
        return cls(step_type, processor, name)


class ProcessingPipeline:
    """
    データ処理パイプライン
    
    複数の処理ステップを順番に実行するパイプラインを提供します。
    """
    
    def __init__(self, steps: Optional[List[ProcessingStep]] = None, name: str = None):
        """
        初期化
        
        Parameters
        ----------
        steps : Optional[List[ProcessingStep]], optional
            処理ステップのリスト, by default None
        name : str, optional
            パイプラインの名前, by default None
        """
        self.steps = steps or []
        self.name = name or f"pipeline_{id(self)}"
        self.input_data = None
        self.result_data = None
        self.intermediate_results = {}
        self.execution_log = []
    
    def add_step(self, step: ProcessingStep) -> 'ProcessingPipeline':
        """
        ステップを追加
        
        Parameters
        ----------
        step : ProcessingStep
            追加する処理ステップ
            
        Returns
        -------
        ProcessingPipeline
            パイプラインオブジェクト（チェーン呼び出し用）
        """
        self.steps.append(step)
        return self
    
    def add_transform_step(self, transformer: DataTransformer, name: str = None) -> 'ProcessingPipeline':
        """
        変換ステップを追加
        
        Parameters
        ----------
        transformer : DataTransformer
            変換プロセッサ
        name : str, optional
            ステップ名, by default None
            
        Returns
        -------
        ProcessingPipeline
            パイプラインオブジェクト（チェーン呼び出し用）
        """
        step = ProcessingStep('transform', transformer, name)
        return self.add_step(step)
    
    def add_aggregate_step(self, aggregator: DataAggregator, name: str = None) -> 'ProcessingPipeline':
        """
        集計ステップを追加
        
        Parameters
        ----------
        aggregator : DataAggregator
            集計プロセッサ
        name : str, optional
            ステップ名, by default None
            
        Returns
        -------
        ProcessingPipeline
            パイプラインオブジェクト（チェーン呼び出し用）
        """
        step = ProcessingStep('aggregate', aggregator, name)
        return self.add_step(step)
    
    def add_calculate_step(self, calculator: BaseCalculator, name: str = None) -> 'ProcessingPipeline':
        """
        計算ステップを追加
        
        Parameters
        ----------
        calculator : BaseCalculator
            計算プロセッサ
        name : str, optional
            ステップ名, by default None
            
        Returns
        -------
        ProcessingPipeline
            パイプラインオブジェクト（チェーン呼び出し用）
        """
        step = ProcessingStep('calculate', calculator, name)
        return self.add_step(step)
    
    def execute(self, data: Any, store_intermediate: bool = False) -> Any:
        """
        パイプラインを実行
        
        Parameters
        ----------
        data : Any
            入力データ
        store_intermediate : bool, optional
            中間結果を保存するかどうか, by default False
            
        Returns
        -------
        Any
            処理結果データ
        """
        self.input_data = data
        self.intermediate_results = {}
        self.execution_log = []
        
        # 入力データを最初の中間結果として保存
        if store_intermediate:
            self.intermediate_results['input'] = data
        
        current_data = data
        
        # 各ステップを順番に実行
        for i, step in enumerate(self.steps):
            step_name = step.name
            step_type = step.step_type
            processor_type = type(step.processor).__name__
            
            try:
                # ステップを実行
                start_time = pd.Timestamp.now()
                current_data = step.execute(current_data)
                end_time = pd.Timestamp.now()
                duration = (end_time - start_time).total_seconds()
                
                # 実行ログに記録
                log_entry = {
                    'step_index': i,
                    'step_name': step_name,
                    'step_type': step_type,
                    'processor_type': processor_type,
                    'status': 'success',
                    'duration': duration
                }
                self.execution_log.append(log_entry)
                
                # 中間結果を保存
                if store_intermediate:
                    self.intermediate_results[step_name] = current_data
            
            except Exception as e:
                # エラーを記録
                log_entry = {
                    'step_index': i,
                    'step_name': step_name,
                    'step_type': step_type,
                    'processor_type': processor_type,
                    'status': 'error',
                    'error': str(e)
                }
                self.execution_log.append(log_entry)
                
                # エラーを再発生
                raise
        
        # 最終結果を保存
        self.result_data = current_data
        
        return current_data
    
    def get_config(self) -> Dict[str, Any]:
        """
        パイプラインの設定を取得
        
        Returns
        -------
        Dict[str, Any]
            パイプラインの設定
        """
        steps_config = [step.get_config() for step in self.steps]
        
        return {
            'name': self.name,
            'steps': steps_config
        }
    
    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> 'ProcessingPipeline':
        """
        設定からパイプラインを作成
        
        Parameters
        ----------
        config : Dict[str, Any]
            パイプラインの設定
            
        Returns
        -------
        ProcessingPipeline
            作成されたパイプライン
        """
        name = config.get('name')
        steps_config = config.get('steps', [])
        
        # パイプラインの作成
        pipeline = cls(name=name)
        
        # ステップの追加
        for step_config in steps_config:
            step = ProcessingStep.from_config(step_config)
            pipeline.add_step(step)
        
        return pipeline
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """
        実行の要約を取得
        
        Returns
        -------
        Dict[str, Any]
            実行の要約
        """
        total_duration = sum(log['duration'] for log in self.execution_log if 'duration' in log)
        success_steps = sum(1 for log in self.execution_log if log['status'] == 'success')
        error_steps = sum(1 for log in self.execution_log if log['status'] == 'error')
        
        return {
            'pipeline_name': self.name,
            'total_steps': len(self.steps),
            'executed_steps': len(self.execution_log),
            'success_steps': success_steps,
            'error_steps': error_steps,
            'total_duration': total_duration
        }


class ProcessingPipelineFactory:
    """
    処理パイプラインファクトリ
    
    一般的なデータ処理パイプラインを作成するためのファクトリクラスです。
    """
    
    @staticmethod
    def create_smoothing_pipeline(window_size: int = 5, method: str = 'moving_avg', columns: Optional[List[str]] = None) -> ProcessingPipeline:
        """
        スムージングパイプラインを作成
        
        Parameters
        ----------
        window_size : int, optional
            窓サイズ, by default 5
        method : str, optional
            平滑化方法, by default 'moving_avg'
        columns : Optional[List[str]], optional
            対象カラム, by default None
            
        Returns
        -------
        ProcessingPipeline
            作成されたパイプライン
        """
        params = {
            'window_size': window_size,
            'method': method
        }
        
        if columns is not None:
            params['columns'] = columns
        
        transformer = SmoothingTransform(params)
        pipeline = ProcessingPipeline(name='smoothing_pipeline')
        pipeline.add_transform_step(transformer, name='smoothing')
        
        return pipeline
    
    @staticmethod
    def create_time_aggregation_pipeline(time_column: str, time_unit: str = '1min', 
                                        aggregation_funcs: Optional[Dict[str, str]] = None) -> ProcessingPipeline:
        """
        時間集計パイプラインを作成
        
        Parameters
        ----------
        time_column : str
            時間カラム
        time_unit : str, optional
            時間単位, by default '1min'
        aggregation_funcs : Optional[Dict[str, str]], optional
            集計関数, by default None
            
        Returns
        -------
        ProcessingPipeline
            作成されたパイプライン
        """
        params = {
            'time_column': time_column,
            'time_unit': time_unit
        }
        
        if aggregation_funcs is not None:
            params['aggregation_funcs'] = aggregation_funcs
        
        aggregator = TimeAggregator(params)
        pipeline = ProcessingPipeline(name='time_aggregation_pipeline')
        pipeline.add_aggregate_step(aggregator, name='time_aggregation')
        
        return pipeline
    
    @staticmethod
    def create_performance_metrics_pipeline(speed_column: str, direction_column: str,
                                          wind_direction_column: str, wind_speed_column: str,
                                          metrics: Optional[List[str]] = None) -> ProcessingPipeline:
        """
        パフォーマンス指標計算パイプラインを作成
        
        Parameters
        ----------
        speed_column : str
            速度カラム
        direction_column : str
            方向カラム
        wind_direction_column : str
            風向カラム
        wind_speed_column : str
            風速カラム
        metrics : Optional[List[str]], optional
            計算する指標のリスト, by default None
            
        Returns
        -------
        ProcessingPipeline
            作成されたパイプライン
        """
        params = {
            'speed_column': speed_column,
            'direction_column': direction_column,
            'wind_direction_column': wind_direction_column,
            'wind_speed_column': wind_speed_column
        }
        
        if metrics is not None:
            params['metrics'] = metrics
        else:
            params['metrics'] = ['vmg', 'target_ratio']
        
        calculator = PerformanceCalculator(params)
        pipeline = ProcessingPipeline(name='performance_metrics_pipeline')
        pipeline.add_calculate_step(calculator, name='performance_metrics')
        
        return pipeline
    
    @staticmethod
    def create_statistical_analysis_pipeline(columns: Optional[List[str]] = None,
                                          metrics: Optional[List[str]] = None) -> ProcessingPipeline:
        """
        統計分析パイプラインを作成
        
        Parameters
        ----------
        columns : Optional[List[str]], optional
            対象カラム, by default None
        metrics : Optional[List[str]], optional
            計算する統計指標のリスト, by default None
            
        Returns
        -------
        ProcessingPipeline
            作成されたパイプライン
        """
        params = {}
        
        if columns is not None:
            params['columns'] = columns
        
        if metrics is not None:
            params['metrics'] = metrics
        else:
            params['metrics'] = ['mean', 'median', 'std', 'min', 'max']
        
        calculator = StatisticalCalculator(params)
        pipeline = ProcessingPipeline(name='statistical_analysis_pipeline')
        pipeline.add_calculate_step(calculator, name='statistical_analysis')
        
        return pipeline
    
    @staticmethod
    def create_data_transformation_pipeline(normalization: bool = True, smoothing: bool = True,
                                         columns: Optional[List[str]] = None) -> ProcessingPipeline:
        """
        データ変換パイプラインを作成
        
        Parameters
        ----------
        normalization : bool, optional
            正規化を行うかどうか, by default True
        smoothing : bool, optional
            平滑化を行うかどうか, by default True
        columns : Optional[List[str]], optional
            対象カラム, by default None
            
        Returns
        -------
        ProcessingPipeline
            作成されたパイプライン
        """
        pipeline = ProcessingPipeline(name='data_transformation_pipeline')
        
        # 正規化
        if normalization:
            norm_params = {
                'method': 'min_max',
                'target_min': 0.0,
                'target_max': 1.0
            }
            
            if columns is not None:
                norm_params['columns'] = columns
            
            normalizer = NormalizationTransform(norm_params)
            pipeline.add_transform_step(normalizer, name='normalization')
        
        # 平滑化
        if smoothing:
            smooth_params = {
                'method': 'moving_avg',
                'window_size': 5
            }
            
            if columns is not None:
                smooth_params['columns'] = columns
            
            smoother = SmoothingTransform(smooth_params)
            pipeline.add_transform_step(smoother, name='smoothing')
        
        return pipeline
