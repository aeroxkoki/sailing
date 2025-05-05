# セーリング戦略分析システム改善計画

## 1. 修正済みの問題
- ✅ GPSAnomalyDetector インターフェースの互換性問題
- ✅ CSVファイル読み込みエラー
- ✅ 時間同期処理エラー

## 2. 今後の改善計画

### 2.1 データモデル関連
- [ ] キャッシュ関数のテスト修正（tests/test_data_model.py::TestCacheFunctions::test_cached_decorator）
- [ ] プロジェクト統合テストの修正

### 2.2 解析エンジン関連
- [ ] DecisionPointsAnalyzer クラスの修正（_remove_duplicate_points メソッドの追加）
- [ ] wind_data 引数に関するエラーの修正（_extract_performance_metrics メソッド）

### 2.3 風推定エンジン関連
- [ ] WindEstimator インターフェースの改善（_categorize_maneuver, _determine_point_state メソッドの追加）
- [ ] detect_maneuvers メソッドの引数修正（3つの引数を期待するよう修正）
- [ ] estimate_wind メソッドの実装

### 2.4 最適化計算関連
- [ ] OptimalVMGCalculator の風上最適角度計算の修正（負の値や0を返さないよう修正）
- [ ] ポーラーデータ読み込み処理の改善（風速値の範囲を適切に扱う）

### 2.5 データ品質メトリクス関連
- [ ] EnhancedQualityMetricsCalculator クラスの calculate_category_quality_scores メソッド実装
- [ ] 可視化コンポーネントの改善（無効なプロパティエラーの修正）

## 3. リファクタリング計画
- [ ] ファイルサイズが大きいモジュールの分割（500行以上のファイル）
- [ ] テストコードの整理と簡素化
- [ ] エラーハンドリングの統一と改善
- [ ] デバッグログの整理

