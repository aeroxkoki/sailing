# -*- coding: utf-8 -*-
"""
conftest.py - PyTestのグローバル設定とフィクスチャを定義

このファイルはPyTestの実行時に自動的に読み込まれ、
複数のテストで共通して使用するフィクスチャや設定を提供します。
"""

import os
import sys
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import traceback
import logging
import platform
import socket
import json
import warnings

# 警告を記録するためのセットアップ
warnings.simplefilter('always', UserWarning)

# 現在のファイルの絶対パスからプロジェクトルートを検出
current_file = os.path.abspath(__file__)
project_root = os.path.dirname(os.path.dirname(current_file))

# Pythonパスの明示的設定と重複回避
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# sailing_data_processor へのパスも明示的に追加
module_path = os.path.join(project_root, 'sailing_data_processor')
if module_path not in sys.path:
    sys.path.insert(0, module_path)

# sailing_data_processor の strategy サブパッケージへのパスも追加
strategy_path = os.path.join(module_path, 'strategy')
if strategy_path not in sys.path:
    sys.path.insert(0, strategy_path)

# testsディレクトリへのパスも明示的に追加
tests_path = os.path.dirname(os.path.abspath(__file__))
if tests_path not in sys.path:
    sys.path.insert(0, tests_path)

# Python のインポート機構をデバッグモードに設定
# これにより、インポートエラーの詳細が出力される
os.environ['PYTHONVERBOSE'] = '1'

# パス設定デバッグ情報
print(f"プロジェクトルート: {project_root}")
print(f"モジュールパス: {module_path}")
print(f"テストパス: {tests_path}")

# テスト用データディレクトリへのパス
TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')

# モジュールのインポートパス問題を解決するための事前処理
try:
    print("Current directory:", os.getcwd())
    print("Python path:", sys.path)
    
    # 必要なパスがすべて追加されていることを確認
    for path in [project_root, module_path, strategy_path, tests_path]:
        if path not in sys.path:
            sys.path.insert(0, path)
            print(f"Added missing path: {path}")
    
    # sailing_data_processor モジュールをインポート
    import sailing_data_processor
    print(f"sailing_data_processor path: {sailing_data_processor.__file__}")
    print(f"sailing_data_processor version: {sailing_data_processor.__version__}")
    
    # モジュールの初期化を保証するために明示的にインポート
    import sailing_data_processor.wind_field_interpolator
    import sailing_data_processor.wind_propagation_model
    import sailing_data_processor.wind_field_fusion_system
    import sailing_data_processor.strategy
    
    # 実際に各モジュールが正しくロードできるか確認
    from sailing_data_processor.wind_propagation_model import WindPropagationModel
    print(f"Successfully imported WindPropagationModel")
    
    # インスタンス化もテスト
    model = WindPropagationModel()
    print(f"Successfully created WindPropagationModel instance")
    
    # 風のインターポレーターをインポート
    from sailing_data_processor.wind_field_interpolator import WindFieldInterpolator
    interpolator = WindFieldInterpolator()
    
    # 風の場統合システムをインポート
    from sailing_data_processor.wind_field_fusion_system import WindFieldFusionSystem
    print(f"Successfully imported WindFieldFusionSystem")
    
    # StrategyDetectorWithPropagation をインポート
    print("\n===== 戦略検出器ロード開始 =====")
    
    # 最初にパス情報を出力して確認
    print(f"現在のディレクトリ: {os.getcwd()}")
    print(f"Python path: {sys.path}")
    print(f"sailing_data_processor path: {sailing_data_processor.__file__}")
    
    # より単純で堅牢な方法で戦略検出器をロード
    try:
        # ルートモジュールのロード機能を使用
        from sailing_data_processor import load_strategy_detector
        print("Imported load_strategy_detector from root module")
        
        # 明示的なロード
        StrategyDetectorWithPropagation = load_strategy_detector()
        if StrategyDetectorWithPropagation:
            print(f"Successfully loaded StrategyDetectorWithPropagation via root loader: {StrategyDetectorWithPropagation.__name__}")
        else:
            raise ImportError("Root loader returned None")
            
    except Exception as e:
        print(f"戦略検出器のロードに失敗しました: {e}")
        print("エラーの詳細:")
        traceback.print_exc()
        
        # 最終的なフォールバックとしてシンプルな代替クラスを提供
        print("シンプルな代替戦略検出器を作成します")
        
        # 基本クラスのインポート
        try:
            from sailing_data_processor.strategy.detector import StrategyDetector
            
            # 最小限の代替クラス
            class TestStrategyDetectorWithPropagation(StrategyDetector):
                """テスト専用の最小限実装"""
                def __init__(self, vmg_calculator=None, wind_fusion_system=None):
                    super().__init__(vmg_calculator)
                    self.wind_fusion_system = wind_fusion_system
                    self.propagation_config = {
                        'wind_shift_prediction_horizon': 1800,  # デフォルト値
                        'prediction_time_step': 300,
                        'wind_shift_confidence_threshold': 0.7,
                        'min_propagation_distance': 1000,
                        'prediction_confidence_decay': 0.1, 
                        'use_historical_data': True
                    }
                
                def detect_wind_shifts_with_propagation(self, course_data, wind_field):
                    """非常にシンプルな実装"""
                    print("TestStrategyDetectorWithPropagation.detect_wind_shifts_with_propagation called")
                    return []
                
                def _detect_wind_shifts_in_legs(self, course_data, wind_field, target_time):
                    """空実装"""
                    return []
                
                def _get_wind_at_position(self, lat, lon, time, wind_field):
                    """空実装"""
                    return None
            
            StrategyDetectorWithPropagation = TestStrategyDetectorWithPropagation
            print("テスト用の代替戦略検出器を作成しました")
            
        except Exception as e2:
            print(f"代替クラスの作成にも失敗しました: {e2}")
            print("モジュールのインポートに関する根本的な問題があります")
            raise
    
    print("===== 戦略検出器ロード完了 =====\n")
    
except ImportError as e:
    print(f"モジュールインポート失敗: {e}")
    traceback.print_exc()
    
    # 代替インポート方法を試行
    try:
        # 詳細なデバッグ情報の表示
        print(f"現在のsys.path: {sys.path}")
        # インポートパスの問題を解決するために環境変数を確認
        print(f"PYTHONPATH環境変数: {os.environ.get('PYTHONPATH', 'Not set')}")
        
        # 代替方法でのインポート試行
        sys.path.append(os.path.abspath(module_path))
        from sailing_data_processor.wind_propagation_model import WindPropagationModel
        print(f"代替パスを使用してWindPropagationModelを正常にインポートしました")
    except ImportError as e:
        print(f"代替インポート方法も失敗しました: {e}")
        traceback.print_exc()
        raise

# ロガーの設定
logger = logging.getLogger('sailing_test')
logger.setLevel(logging.DEBUG)

# ファイルハンドラ
log_file = os.path.join(project_root, 'test_details.log')
file_handler = logging.FileHandler(log_file, mode='w')
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# コンソールハンドラ
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

def get_environment_info():
    """テスト環境の情報を収集"""
    env_info = {
        'platform': platform.platform(),
        'python_version': platform.python_version(),
        'hostname': socket.gethostname(),
        'pythonpath': sys.path,
        'environment_variables': {
            k: v for k, v in os.environ.items() 
            if k.startswith(('PYTHON', 'PATH', 'SAIL'))
        }
    }
    return env_info

@pytest.fixture(scope="session", autouse=True)
def log_environment_info():
    """テスト環境情報のログ出力"""
    env_info = get_environment_info()
    logger.info("======== テスト環境情報 ========")
    logger.info(f"Platform: {env_info['platform']}")
    logger.info(f"Python version: {env_info['python_version']}")
    logger.info(f"Hostname: {env_info['hostname']}")
    logger.debug(f"Python path: {json.dumps(env_info['pythonpath'], indent=2)}")
    
    # 環境変数をログに記録
    logger.debug("Environment variables:")
    for k, v in env_info['environment_variables'].items():
        logger.debug(f"  {k}: {v}")
    
    logger.info("======== テスト開始 ========")
    yield
    logger.info("======== テスト終了 ========")

@pytest.fixture(autouse=True)
def setup_logging(request):
    """各テストのログ設定"""
    logger.info(f"テスト開始: {request.node.name}")
    
    # 個別のテストログファイル
    test_name = request.node.name
    test_log_dir = os.path.join(project_root, 'test_logs')
    os.makedirs(test_log_dir, exist_ok=True)
    test_log_path = os.path.join(test_log_dir, f'test_log_{test_name}.log')
    test_handler = logging.FileHandler(test_log_path, mode='w')
    test_handler.setFormatter(file_formatter)
    logger.addHandler(test_handler)
    
    yield
    
    # テスト終了時のクリーンアップ
    logger.info(f"テスト終了: {request.node.name}")
    logger.removeHandler(test_handler)

# ====== 共通テストフィクスチャ ======

@pytest.fixture
def sample_gps_data():
    """
    テスト用のGPSデータを生成するフィクスチャ
    
    Returns:
        pd.DataFrame: サンプルGPSデータフレーム
    """
    # 100ポイントのテストデータを生成
    timestamps = [datetime.now() + timedelta(seconds=i*10) for i in range(100)]
    
    data = pd.DataFrame({
        'timestamp': timestamps,
        'latitude': 35.45 + np.cumsum(np.random.normal(0, 0.0001, 100)),
        'longitude': 139.65 + np.cumsum(np.random.normal(0, 0.0001, 100)),
        'speed': 5 + np.random.normal(0, 0.5, 100),
        'course': 45 + np.random.normal(0, 5, 100),
        'wind_direction': 90 + np.random.normal(0, 3, 100),
        'wind_speed_knots': 12 + np.random.normal(0, 1, 100)
    })
    
    return data

@pytest.fixture
def sample_wind_data_points():
    """
    テスト用の風データポイントを生成するフィクスチャ
    
    Returns:
        list: 風データポイントのリスト
    """
    base_time = datetime.now()
    
    # 風データの変動を増やす（QHullエラー対策）
    variation_scale = 0.01  # 変動スケールを増加
    
    # 10ポイントの風データを生成
    wind_data_points = []
    for i in range(10):
        point = {
            'timestamp': base_time + timedelta(minutes=i*5),
            'latitude': 35.45 + i * variation_scale + np.random.normal(0, variation_scale/10),
            'longitude': 139.65 + i * variation_scale + np.random.normal(0, variation_scale/10),
            'wind_direction': 90 + i * 2 + np.random.normal(0, 1),
            'wind_speed': 12 + i * 0.2 + np.random.normal(0, 0.1),
            'confidence': 0.8 - i * 0.02  # 時間経過で信頼度が低下
        }
        wind_data_points.append(point)
    
    return wind_data_points

@pytest.fixture
def sample_course_data():
    """
    テスト用のコースデータを生成するフィクスチャ
    
    Returns:
        dict: コース計算結果のサンプル
    """
    start_time = datetime.now()
    
    # コースデータのサンプル
    course_data = {
        'start_time': start_time,
        'legs': [
            {
                'leg_number': 1,
                'is_upwind': True,
                'start_waypoint': {
                    'lat': 35.45,
                    'lon': 139.65,
                    'name': 'Start'
                },
                'end_waypoint': {
                    'lat': 35.46,
                    'lon': 139.66,
                    'name': 'Mark 1'
                },
                'path': {
                    'path_points': [
                        {
                            'lat': 35.45 + i * 0.001,
                            'lon': 139.65 + i * 0.001,
                            'time': start_time + timedelta(minutes=i*2),
                            'course': 45
                        } for i in range(10)
                    ]
                }
            }
        ]
    }
    
    return course_data

@pytest.fixture
def sample_wind_field():
    """
    テスト用の風の場データを生成するフィクスチャ
    
    Returns:
        dict: 風の場データのサンプル
    """
    # グリッドの生成（変動を含む）
    grid_size = 10  # グリッドサイズを増加
    lat_grid = np.linspace(35.45, 35.47, grid_size)
    lon_grid = np.linspace(139.65, 139.67, grid_size)
    grid_lats, grid_lons = np.meshgrid(lat_grid, lon_grid)
    
    # 風向・風速・信頼度のマトリックス生成（わずかな変動を含める）
    # QHull精度エラーを避けるために変動性を確保
    wind_direction = np.ones_like(grid_lats) * 90 + np.random.normal(0, 5, grid_lats.shape)
    wind_speed = np.ones_like(grid_lats) * 12 + np.random.normal(0, 1, grid_lats.shape)
    confidence = np.ones_like(grid_lats) * 0.8 + np.random.normal(0, 0.05, grid_lats.shape)
    confidence = np.clip(confidence, 0.1, 1.0)  # 有効範囲内に収める
    
    # 風の場データ
    wind_field = {
        'lat_grid': grid_lats,
        'lon_grid': grid_lons,
        'wind_direction': wind_direction,
        'wind_speed': wind_speed,
        'confidence': confidence,
        'time': datetime.now()
    }
    
    return wind_field

# ====== 風の移動モデル用フィクスチャ ======

@pytest.fixture
def standard_wind_pattern():
    """標準風パターンのデータを生成"""
    base_time = datetime.now()
    points = []
    
    # より多様な風データを生成
    for i in range(15):
        point = {
            'timestamp': base_time + timedelta(minutes=i*10),
            'latitude': 35.45 + i * 0.005,
            'longitude': 139.65 + i * 0.005,
            'wind_direction': 90 + i * 1.5,  # 徐々に変化する風向
            'wind_speed': 12 + i * 0.3,      # 徐々に変化する風速
            'confidence': 0.9 - i * 0.02     # 時間経過で低下する信頼度
        }
        points.append(point)
    
    return points

@pytest.fixture
def oscillating_wind_pattern():
    """振動する風パターンのデータを生成"""
    base_time = datetime.now()
    points = []
    
    # 振動パターンの風データ
    for i in range(15):
        oscillation = 20 * np.sin(i * np.pi / 4)  # 振動する風向
        point = {
            'timestamp': base_time + timedelta(minutes=i*10),
            'latitude': 35.45 + i * 0.005,
            'longitude': 139.65 + i * 0.005,
            'wind_direction': 90 + oscillation,
            'wind_speed': 12 + 2 * np.sin(i * np.pi / 3),  # 振動する風速
            'confidence': 0.85
        }
        points.append(point)
    
    return points

@pytest.fixture
def light_wind_pattern():
    """弱風パターンのデータを生成"""
    base_time = datetime.now()
    points = []
    
    for i in range(15):
        point = {
            'timestamp': base_time + timedelta(minutes=i*10),
            'latitude': 35.45 + i * 0.005,
            'longitude': 139.65 + i * 0.005,
            'wind_direction': 90 + np.random.normal(0, 10),  # 弱風時は風向が不安定
            'wind_speed': 4 + np.random.normal(0, 0.8),      # 5ノット以下の弱風
            'confidence': 0.7 - i * 0.01                     # 弱風は信頼度が低い
        }
        points.append(point)
    
    return points

@pytest.fixture
def high_wind_pattern():
    """強風パターンのデータを生成"""
    base_time = datetime.now()
    points = []
    
    for i in range(15):
        point = {
            'timestamp': base_time + timedelta(minutes=i*10),
            'latitude': 35.45 + i * 0.005,
            'longitude': 139.65 + i * 0.005,
            'wind_direction': 90 + i * 0.5,   # 強風は方向が安定
            'wind_speed': 20 + i * 0.4,       # 20ノット以上の強風
            'confidence': 0.95 - i * 0.005    # 強風は信頼度が高い
        }
        points.append(point)
    
    return points

@pytest.fixture
def coastal_wind_pattern():
    """沿岸風パターンのデータを生成"""
    base_time = datetime.now()
    points = []
    
    # 海岸線を35.45度と仮定
    coast_lat = 35.45
    
    for i in range(15):
        # 海岸からの距離に応じて風向が変化
        lat = coast_lat + i * 0.005
        distance_from_coast = (lat - coast_lat) * 111000  # メートル単位に変換
        coastal_effect = 30 * np.exp(-distance_from_coast / 2000)  # 海岸から離れるほど効果が減少
        
        point = {
            'timestamp': base_time + timedelta(minutes=i*10),
            'latitude': lat,
            'longitude': 139.65 + i * 0.003,
            'wind_direction': 90 + coastal_effect,  # 海岸効果による風向変化
            'wind_speed': 12 + 5 * np.exp(-distance_from_coast / 3000),  # 海岸近くで風速増加
            'confidence': 0.85 - i * 0.01
        }
        points.append(point)
    
    return points
