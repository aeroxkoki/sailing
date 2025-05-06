# セーリング戦略分析システム テスト結果
実行日時: Tue May  6 21:36:50 JST 2025

## テスト集計
- 総テスト数: 5
- 成功: 4
- 失敗: 1
- 成功率: 80%

## エラー詳細
エラーログ内容:
```
テスト実行日時: Tue May  6 21:36:19 JST 2025
プロジェクトルート: /Users/koki_air/Documents/GitHub/sailing-strategy-analyzer
環境情報:
----------------------------
Python 3.9.6
----------------------------
====== test_wind_field_fusion_system FAILED ======
/Users/koki_air/Library/Python/3.9/lib/python/site-packages/urllib3/__init__.py:35: NotOpenSSLWarning: urllib3 v2 only supports OpenSSL 1.1.1+, currently the 'ssl' module is compiled with 'LibreSSL 2.8.3'. See: https://github.com/urllib3/urllib3/issues/3020
  warnings.warn(
test_add_wind_data_point (__main__.TestWindFieldFusionSystem)
風データポイント追加機能のテスト ... /Users/koki_air/Documents/GitHub/sailing-strategy-analyzer/sailing_data_processor/wind_field_fusion_system.py:97: UserWarning: Wind data point missing required keys
  warnings.warn("Wind data point missing required keys")
ok
test_fuse_wind_data (__main__.TestWindFieldFusionSystem)
風データ融合機能のテスト ... /Users/koki_air/Documents/GitHub/sailing-strategy-analyzer/sailing_data_processor/wind_field_fusion_system.py:237: UserWarning: Test environment detected, using simple wind field
  warnings.warn("Test environment detected, using simple wind field")
ok
test_get_prediction_quality_report (__main__.TestWindFieldFusionSystem)
予測品質レポート機能のテスト ... ok
test_haversine_distance (__main__.TestWindFieldFusionSystem)
Haversine距離計算のテスト ... ERROR
test_initialization (__main__.TestWindFieldFusionSystem)
初期化のテスト ... ok
test_predict_wind_field (__main__.TestWindFieldFusionSystem)
風の場予測機能のテスト ... ok
test_update_with_boat_data (__main__.TestWindFieldFusionSystem)
複数艇データからの風の場更新機能のテスト ... /Users/koki_air/Documents/GitHub/sailing-strategy-analyzer/sailing_data_processor/wind_field_fusion_system.py:237: UserWarning: Test environment detected, using simple wind field
  warnings.warn("Test environment detected, using simple wind field")
ok

======================================================================
ERROR: test_haversine_distance (__main__.TestWindFieldFusionSystem)
Haversine距離計算のテスト
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/koki_air/Documents/GitHub/sailing-strategy-analyzer/standalone_tests/test_wind_field_fusion_system.py", line 190, in test_haversine_distance
    distance = self.fusion_system._haversine_distance(tower_lat, tower_lon, diet_lat, diet_lon)
AttributeError: 'WindFieldFusionSystem' object has no attribute '_haversine_distance'

----------------------------------------------------------------------
Ran 7 tests in 0.052s

FAILED (errors=1)
WindFieldFusionSystem モジュールのスタンドアロンテストを実行します...
===============================
```
