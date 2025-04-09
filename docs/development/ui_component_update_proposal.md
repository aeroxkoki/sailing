# UIコンポーネント更新提案

## 概要

拡張されたデータ品質メトリクス計算と視覚化機能を既存のUIコンポーネントに統合するための提案です。

## 対象ファイル

- `ui/components/validation/validation_summary.py` - 検証結果のサマリーを表示するコンポーネント
- `ui/components/validation/validation_dashboard.py` - 検証結果のダッシュボードを表示するコンポーネント

## 更新案

### 1. validation_summary.py の更新

#### 変更点:

1. `EnhancedQualityMetricsCalculator` と `EnhancedValidationVisualizer` のインポートを追加
2. カテゴリ別の詳細スコア表示を追加
3. 時間帯別・空間グリッド別の品質表示を追加
4. カードスタイルの品質スコア表示を追加

#### コード例:

```python
from sailing_data_processor.validation.quality_metrics_integration import EnhancedQualityMetricsCalculator
from sailing_data_processor.validation.visualization_integration import EnhancedValidationVisualizer, create_validation_visualizer

class ValidationSummary:
    # 既存の初期化コードは維持
    def __init__(self, metrics_calculator, container=None, key_prefix="validation_summary", on_fix_button_click=None):
        # 親クラスの初期化
        self.metrics_calculator = metrics_calculator
        self.container = container
        self.key_prefix = key_prefix
        self.on_fix_button_click = on_fix_button_click
        
        # 拡張されたメトリクス計算と視覚化クラスを使用
        if not isinstance(metrics_calculator, EnhancedQualityMetricsCalculator):
            self.enhanced_metrics = EnhancedQualityMetricsCalculator(
                metrics_calculator.validation_results, metrics_calculator.data)
        else:
            self.enhanced_metrics = metrics_calculator
            
        # 視覚化クラスの作成
        if container and container.data is not None:
            self.visualizer = EnhancedValidationVisualizer(self.enhanced_metrics, container.data)
        else:
            self.visualizer = EnhancedValidationVisualizer(self.enhanced_metrics, self.enhanced_metrics.data)
            
        # 品質サマリーを取得
        self.quality_summary = self.enhanced_metrics.get_quality_summary()
        
        # 品質スコアを取得
        self.quality_scores = self.enhanced_metrics.quality_scores
        
        # カテゴリ別スコアを取得
        self.category_scores = self.enhanced_metrics.calculate_category_quality_scores()
        
        # セッション状態の初期化
        if f"{self.key_prefix}_selected_tab" not in st.session_state:
            st.session_state[f"{self.key_prefix}_selected_tab"] = "概要"
    
    # 既存のrenderメソッドを拡張
    def render(self):
        with st.container():
            self._render_summary_header()
            
            # タブでセクションを分ける
            tabs = st.tabs(["概要", "カテゴリ別", "時間分布", "空間分布", "修正可能性"])
            
            with tabs[0]:
                self._render_overall_summary()
            
            with tabs[1]:
                self._render_category_summary()
            
            with tabs[2]:
                self._render_temporal_distribution()
            
            with tabs[3]:
                self._render_spatial_distribution()
            
            with tabs[4]:
                self._render_fixability_summary()
    
    # 新しい時間分布表示メソッド
    def _render_temporal_distribution(self):
        st.markdown("### 時間帯別の品質分布")
        
        # 時間的品質スコアの取得
        temporal_scores = self.enhanced_metrics.calculate_temporal_quality_scores()
        
        if temporal_scores:
            # 時間的品質チャートの表示
            temporal_chart = self.visualizer.generate_temporal_quality_chart()
            st.plotly_chart(temporal_chart, use_container_width=True)
            
            # 問題タイプの分布
            dashboard = self.visualizer.generate_problem_distribution_visualization()
            st.plotly_chart(dashboard["problem_type_stacked"], use_container_width=True)
        else:
            st.info("時間的な品質分布データがありません。タイムスタンプデータが不足している可能性があります。")
    
    # 新しい空間分布表示メソッド
    def _render_spatial_distribution(self):
        st.markdown("### 空間的な品質分布")
        
        # 空間的品質スコアの取得
        spatial_scores = self.enhanced_metrics.calculate_spatial_quality_scores()
        
        if spatial_scores:
            # 空間的品質マップの表示
            spatial_map = self.visualizer.generate_spatial_quality_map()
            st.plotly_chart(spatial_map, use_container_width=True)
            
            # 問題の密度ヒートマップ
            dashboard = self.visualizer.generate_problem_distribution_visualization()
            st.plotly_chart(dashboard["spatial_heatmap"], use_container_width=True)
        else:
            st.info("空間的な品質分布データがありません。位置情報データが不足している可能性があります。")
```

### 2. validation_dashboard.py の更新

#### 変更点:

1. `EnhancedQualityMetricsCalculator` と `EnhancedValidationVisualizer` のインポートを追加
2. 拡張されたダッシュボード表示機能を追加
3. インタラクティブな問題分布表示を追加
4. フィルタリング機能を追加して、問題タイプや重要度別にデータを絞り込めるようにする

#### コード例:

```python
from sailing_data_processor.validation.quality_metrics_integration import EnhancedQualityMetricsCalculator
from sailing_data_processor.validation.visualization_integration import EnhancedValidationVisualizer, create_validation_visualizer

class ValidationDashboard:
    # 既存の初期化コードは維持しつつ拡張
    def __init__(self, validation_results, data, key_prefix="validation_dashboard"):
        # 拡張されたメトリクス計算と視覚化クラスを使用
        self.metrics_calculator = EnhancedQualityMetricsCalculator(validation_results, data)
        self.data = data
        self.key_prefix = key_prefix
        
        # 視覚化クラスの作成
        self.visualizer = EnhancedValidationVisualizer(self.metrics_calculator, data)
        
        # フィルタリング状態を初期化
        self.active_filters = {
            "problem_types": ["missing_data", "out_of_range", "duplicates", 
                           "spatial_anomalies", "temporal_anomalies"],
            "severity": ["error", "warning", "info"],
            "time_range": None,
            "position": None
        }
        
        # セッション状態の初期化
        if f"{self.key_prefix}_view_mode" not in st.session_state:
            st.session_state[f"{self.key_prefix}_view_mode"] = "標準"
    
    # 拡張されたダッシュボード表示
    def render_dashboard(self):
        st.title("データ品質ダッシュボード")
        
        # ダッシュボード表示モードの選択
        view_mode = st.radio(
            "表示モード",
            ["標準", "詳細"],
            horizontal=True,
            key=f"{self.key_prefix}_view_mode"
        )
        
        # フィルター設定のエクスパンダー
        with st.expander("フィルター設定", expanded=False):
            self._render_filters()
        
        # ダッシュボード表示
        if view_mode == "標準":
            self._render_standard_dashboard()
        else:
            self._render_detailed_dashboard()
    
    # フィルター設定UI
    def _render_filters(self):
        col1, col2 = st.columns(2)
        
        with col1:
            # 問題タイプフィルター
            problem_types = st.multiselect(
                "問題タイプ",
                ["欠損値", "範囲外の値", "重複データ", "空間的異常", "時間的異常"],
                ["欠損値", "範囲外の値", "重複データ", "空間的異常", "時間的異常"],
                key=f"{self.key_prefix}_problem_types"
            )
            
            # 日本語名を英語キーに変換
            type_keys = {
                "欠損値": "missing_data",
                "範囲外の値": "out_of_range",
                "重複データ": "duplicates",
                "空間的異常": "spatial_anomalies",
                "時間的異常": "temporal_anomalies"
            }
            self.active_filters["problem_types"] = [type_keys[t] for t in problem_types]
        
        with col2:
            # 重要度フィルター
            severity = st.multiselect(
                "重要度",
                ["エラー", "警告", "情報"],
                ["エラー", "警告", "情報"],
                key=f"{self.key_prefix}_severity"
            )
            
            # 日本語名を英語キーに変換
            severity_keys = {
                "エラー": "error",
                "警告": "warning",
                "情報": "info"
            }
            self.active_filters["severity"] = [severity_keys[s] for s in severity]
    
    # 標準ダッシュボード表示
    def _render_standard_dashboard(self):
        # 品質スコアカード
        quality_cards = self.visualizer.generate_quality_score_card()
        
        # 総合スコアを大きく表示
        col1, col2 = st.columns([1, 3])
        with col1:
            total_score = quality_cards["total_score"]
            st.metric("総合品質スコア", f"{total_score:.1f} / 100")
        
        with col2:
            # カテゴリ別スコアを横並びで表示
            subcols = st.columns(3)
            for i, card in enumerate(quality_cards["cards"][1:]):  # 総合スコア以外を表示
                with subcols[i]:
                    st.metric(
                        card["title"], 
                        f"{card['value']:.1f}", 
                        delta=card["impact_level"], 
                        help=card["description"]
                    )
        
        # データ品質の分布
        st.subheader("データ品質の分布")
        
        # タブで分割
        quality_tabs = st.tabs(["時間的品質", "空間的品質", "問題タイプ"])
        
        with quality_tabs[0]:
            # 時間的品質チャート
            temporal_chart = self.visualizer.generate_temporal_quality_chart()
            st.plotly_chart(temporal_chart, use_container_width=True)
        
        with quality_tabs[1]:
            # 空間的品質マップ
            spatial_map = self.visualizer.generate_spatial_quality_map()
            st.plotly_chart(spatial_map, use_container_width=True)
        
        with quality_tabs[2]:
            # 問題分布の視覚化
            distribution = self.visualizer.generate_problem_distribution_visualization()
            col1, col2 = st.columns(2)
            
            with col1:
                st.plotly_chart(distribution["problem_type_pie"], use_container_width=True)
            
            with col2:
                st.plotly_chart(distribution["temporal_distribution"], use_container_width=True)
    
    # 詳細ダッシュボード表示
    def _render_detailed_dashboard(self):
        # 品質スコアダッシュボード
        dashboard = self.visualizer.generate_quality_score_dashboard()
        
        # ゲージとバーチャート
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(dashboard["gauge_chart"], use_container_width=True)
        with col2:
            st.plotly_chart(dashboard["category_bar_chart"], use_container_width=True)
        
        # 詳細タブ
        detail_tabs = st.tabs(["時間分布", "空間分布", "問題の詳細"])
        
        with detail_tabs[0]:
            st.plotly_chart(dashboard["temporal_quality_chart"], use_container_width=True)
            
            # 問題分布の視覚化
            distribution = self.visualizer.generate_problem_distribution_visualization()
            st.plotly_chart(distribution["problem_type_stacked"], use_container_width=True)
        
        with detail_tabs[1]:
            st.plotly_chart(dashboard["spatial_quality_map"], use_container_width=True)
            st.plotly_chart(distribution["spatial_heatmap"], use_container_width=True)
        
        with detail_tabs[2]:
            # 問題のあるレコードを表示
            self._render_problem_records()
    
    # 問題レコードの表示
    def _render_problem_records(self):
        # 問題サマリーの表示
        issues_summary = {
            "総レコード数": len(self.data),
            "問題のあるレコード数": len(self.metrics_calculator.problematic_indices["all"]),
            "問題率": f"{len(self.metrics_calculator.problematic_indices['all']) / len(self.data) * 100:.2f}%",
            "欠損値のあるレコード": len(self.metrics_calculator.problematic_indices["missing_data"]),
            "範囲外の値のあるレコード": len(self.metrics_calculator.problematic_indices["out_of_range"]),
            "重複のあるレコード": len(self.metrics_calculator.problematic_indices["duplicates"]),
            "空間的異常のあるレコード": len(self.metrics_calculator.problematic_indices["spatial_anomalies"]),
            "時間的異常のあるレコード": len(self.metrics_calculator.problematic_indices["temporal_anomalies"])
        }
        
        st.json(issues_summary)
        
        # 問題レコードの表示（フィルタリング対応）
        filtered_indices = self._filter_problem_indices()
        
        if filtered_indices:
            st.subheader(f"問題のあるレコード ({len(filtered_indices)} 件)")
            
            # ページネーションの設定
            page_size = 20
            total_pages = (len(filtered_indices) + page_size - 1) // page_size
            
            page = st.number_input(
                "ページ",
                min_value=1,
                max_value=max(1, total_pages),
                value=1,
                key=f"{self.key_prefix}_page"
            )
            
            # 現在のページのインデックスを取得
            start_idx = (page - 1) * page_size
            end_idx = min(start_idx + page_size, len(filtered_indices))
            current_indices = filtered_indices[start_idx:end_idx]
            
            # 問題レコードの表示
            problem_data = self.data.iloc[current_indices].copy()
            
            # 問題タイプの追加
            problem_data["問題タイプ"] = ""
            for idx in current_indices:
                problem_types = []
                for type_name, indices in self.metrics_calculator.problematic_indices.items():
                    if type_name != "all" and idx in indices:
                        problem_types.append(type_name)
                problem_data.loc[idx, "問題タイプ"] = ", ".join(problem_types)
            
            st.dataframe(problem_data)
            
            if total_pages > 1:
                st.write(f"ページ {page} / {total_pages}")
        else:
            st.info("フィルター条件に合致する問題レコードはありません。")
    
    # フィルター条件に基づいて問題インデックスをフィルタリング
    def _filter_problem_indices(self):
        # フィルタリングのロジック
        filtered_indices = []
        all_indices = self.metrics_calculator.problematic_indices["all"]
        
        # 問題タイプによるフィルタリング
        type_indices = set()
        for problem_type in self.active_filters["problem_types"]:
            type_indices.update(self.metrics_calculator.problematic_indices[problem_type])
        
        # 結果を重複なしのリストとして返す
        filtered_indices = sorted(list(type_indices.intersection(all_indices)))
        return filtered_indices
```

## 新しいUIコンポーネントの提案

新しい検証ダッシュボードコンポーネントとして、`ui/components/validation/enhanced_validation_dashboard.py` を作成することをお勧めします。これは上記の提案を元にした新しいコンポーネントで、既存のコードを大幅に変更せずに新機能を導入できます。

## 推奨ドキュメントの更新

実装が完了したら、以下のドキュメントの更新も推奨します：

1. `docs/ui_component_library.md` - 新しいコンポーネントの説明を追加
2. `README.md` - 拡張データ品質機能についての説明を追加
3. ユーザーマニュアル - 新しい視覚化機能の使い方を説明

## 拡張機能の影響範囲

この拡張機能の実装により、以下の点が改善されます：

1. データ品質の定量的な評価がより詳細に
2. 時間的・空間的な品質変動の可視化
3. 問題タイプごとの分布を視覚的に理解
4. インタラクティブなダッシュボードによる柔軟な分析
5. より直感的なデータ検証結果の表示

これらの改善により、ユーザーはデータの問題をより迅速に特定し、効率的に修正できるようになります。
