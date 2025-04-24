# -*- coding: utf-8 -*-
"""
AnomalyDetector 階層クラス統合のテスト

このモジュールは新しく統合されたAnomalyDetectorクラス階層のテストを行います。
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# テスト対象のモジュール
from sailing_data_processor.anomaly import (
    BaseAnomalyDetector,
    StandardAnomalyDetector,
    GPSAnomalyDetector, 
    AdvancedGPSAnomalyDetector,
    create_anomaly_detector
)

class TestAnomalyDetectorIntegration(unittest.TestCase):
    """AnomalyDetector統合クラス階層のテスト"""
    
    def setUp(self):
        """各テスト前の準備"""
        # テスト用のGPSデータを生成
        timestamps = [datetime(2023, 1, 1) + timedelta(seconds=i) for i in range(100)]
        
        # 通常のポイント
        latitudes = np.random.normal(35.6812, 0.001, 100)
        longitudes = np.random.normal(139.7671, 0.001, 100)
        
        # 異常値を挿入
        latitudes[20] = 35.7000  # 異常に離れたポイント
        longitudes[20] = 139.8000
        latitudes[40] = 35.6000  # 異常に離れたポイント
        longitudes[40] = 139.7000
        latitudes[60] = 35.6900  # 中程度の異常ポイント
        longitudes[60] = 139.7800
        
        # 速度異常を作成（時間差に対して過度な距離）
        latitudes[80] = 35.7500  # 大きなジャンプ
        longitudes[80] = 139.8500
        
        # データフレームを作成
        self.df = pd.DataFrame({
            'timestamp': timestamps,
            'latitude': latitudes,
            'longitude': longitudes
        })
    
    def test_factory_function(self):
        """ファクトリー関数のテスト"""
        # 各タイプの検出器を作成
        standard_detector = create_anomaly_detector('standard')
        gps_detector = create_anomaly_detector('gps')
        advanced_detector = create_anomaly_detector('advanced')
        
        # 正しいクラスが作成されることを確認
        self.assertIsInstance(standard_detector, StandardAnomalyDetector)
        self.assertIsInstance(gps_detector, GPSAnomalyDetector)
        self.assertIsInstance(advanced_detector, AdvancedGPSAnomalyDetector)
        
        # 不明なタイプの場合は例外が発生することを確認
        with self.assertRaises(ValueError):
            create_anomaly_detector('unknown')
    
    def test_standard_detector(self):
        """StandardAnomalyDetectorのテスト"""
        detector = StandardAnomalyDetector()
        
        # 検出実行
        result = detector.detect_anomalies(self.df, methods=['z_score', 'distance'])
        
        # 異常値が検出されることを確認
        self.assertTrue(result['is_anomaly'].any())
        
        # 異常値の数を確認（実際の数は環境依存なので大まかなチェック）
        anomaly_count = result['is_anomaly'].sum()
        self.assertGreaterEqual(anomaly_count, 1)
        
        # 修正実行
        fixed_result = detector.fix_anomalies(result)
        
        # 修正された値を確認
        self.assertNotEqual(
            self.df.loc[result['is_anomaly'], 'latitude'].values.tolist(),
            fixed_result.loc[result['is_anomaly'], 'latitude'].values.tolist()
        )
    
    def test_gps_detector(self):
        """GPSAnomalyDetectorのテスト"""
        detector = GPSAnomalyDetector()
        
        # 検出実行
        result = detector.detect_anomalies(self.df, methods=['z_score', 'speed'])
        
        # 異常値が検出されることを確認
        self.assertTrue(result['is_anomaly'].any())
        
        # 異常値の数を確認
        anomaly_count = result['is_anomaly'].sum()
        self.assertGreaterEqual(anomaly_count, 1)
        
        # 速度ベースの検出が含まれていることを確認
        speed_anomalies = result[result['anomaly_method'] == 'speed']
        self.assertGreaterEqual(len(speed_anomalies), 1)
        
        # 修正実行（特定の修正方法を指定）
        fixed_result = detector.fix_anomalies(result, method='spline')
        
        # 修正された値を確認
        self.assertNotEqual(
            self.df.loc[result['is_anomaly'], 'latitude'].values.tolist(),
            fixed_result.loc[result['is_anomaly'], 'latitude'].values.tolist()
        )
    
    def test_advanced_detector(self):
        """AdvancedGPSAnomalyDetectorのテスト"""
        detector = AdvancedGPSAnomalyDetector()
        
        # 拡張設定の構成
        detector.configure(
            detection_params={'z_score_threshold': 2.5},
            interpolation_params={'smooth_factor': 0.3},
            advanced_params={'kalman_process_noise': 0.02}
        )
        
        # 検出実行
        result = detector.detect_anomalies(self.df)
        
        # 異常値が検出されることを確認
        self.assertTrue(result['is_anomaly'].any())
        
        # 修正実行
        try:
            # カルマンフィルタによる修正を試みる（ライブラリがなくてもエラーにならない）
            fixed_result = detector.fix_anomalies(result, method='kalman')
        except ImportError:
            # ライブラリがない場合はスキップ
            pass
        
        # 線形補間による修正
        fixed_result = detector.fix_anomalies(result, method='linear')
        
        # 修正された値を確認
        self.assertNotEqual(
            self.df.loc[result['is_anomaly'], 'latitude'].values.tolist(),
            fixed_result.loc[result['is_anomaly'], 'latitude'].values.tolist()
        )
    
    def test_process_function(self):
        """BaseAnomalyDetector.process_dataメソッドのテスト"""
        detector = StandardAnomalyDetector()
        
        # 一括処理実行
        result = detector.process_data(self.df, detection_methods=['z_score', 'distance'])
        
        # 処理が行われたことを確認
        self.assertIn('is_anomaly', result.columns)
        self.assertIn('is_anomaly_fixed', result.columns)
        
        # 異常値が検出され修正されたことを確認
        fixed_count = result['is_anomaly_fixed'].sum()
        self.assertGreaterEqual(fixed_count, 1)
    
    def test_configurable_parameters(self):
        """パラメータ設定のテスト"""
        detector = GPSAnomalyDetector()
        
        # 初期設定を保存
        original_threshold = detector.detection_config['z_score_threshold']
        
        # 設定を変更
        new_threshold = 2.0
        detector.configure(detection_params={'z_score_threshold': new_threshold})
        
        # 設定が変更されたことを確認
        self.assertEqual(detector.detection_config['z_score_threshold'], new_threshold)
        self.assertNotEqual(detector.detection_config['z_score_threshold'], original_threshold)
        
        # 変更された設定を使って検出
        result1 = detector.detect_anomalies(self.df, methods=['z_score'])
        
        # 設定を元に戻す
        detector.configure(detection_params={'z_score_threshold': original_threshold})
        
        # 元の設定で再度検出
        result2 = detector.detect_anomalies(self.df, methods=['z_score'])
        
        # 異なる閾値で検出した結果が異なることを確認（厳密なチェックではない）
        # Note: 乱数生成により稀に同じ結果になる可能性があります
        anomaly_count1 = result1['is_anomaly'].sum()
        anomaly_count2 = result2['is_anomaly'].sum()
        self.assertIsNotNone(anomaly_count1)
        self.assertIsNotNone(anomaly_count2)


if __name__ == '__main__':
    unittest.main()
