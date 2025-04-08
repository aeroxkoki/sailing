# 開発指示書：データ検証フィードバック最終統合（Phase 2 - Week 7）

## 1. タスク概要

データ検証フィードバック機能の最終統合作業を行い、パフォーマンス最適化とユーザビリティの向上を図る。

**タスク名**: データ検証フィードバック機能の最終統合・最適化  
**担当モジュール**: `ui/components/visualizations`, `sailing_data_processor/validation`  
**優先度**: 高  
**推定工数**: 1人日  

## 2. 背景と目的

サブステップ2.2のユーザーエクスペリエンス向上の一環として、データ検証フィードバック機能の基本実装は完了しています。現在、各コンポーネント（ValidationDashboard, CorrectionProcessor, ValidationVisualizer）は個別に機能していますが、ユーザーにとってより直感的で使いやすい統合体験を提供するために、これらのコンポーネント間の連携を強化し、パフォーマンスを最適化する必要があります。

このタスクの目的は、個別に実装された機能を統合し、大規模データセットの処理を最適化し、ユーザーが自信を持ってデータ品質を確認・改善できるシームレスな体験を実現することです。

## 3. 機能要件

### 3.1 コンポーネント統合

1. **ValidationDashboardの機能強化**
   - 問題箇所の視覚的ハイライト機能とフィードバック連携の強化
   - メトリクス計算、可視化、修正適用間のシームレスなデータフローの確立
   - レポート表示時の空間的問題の視覚化の改善

2. **修正提案の自動適用フローの改善**
   - 推奨修正適用時のフィードバックと履歴機能の実装
   - バッチ修正機能の強化（特に空間的・時間的異常の一括処理）
   - 修正適用前後の比較機能

3. **UI応答性の向上**
   - 進行状況表示の実装（特に大規模データセット処理時）
   - 非同期処理の安定化
   - ユーザー操作のキャッシュと遅延読み込み

### 3.2 パフォーマンス最適化

1. **大規模データセット処理の改善**
   - サンプリングロジックの改良（重要データポイントの保持を確実に）
   - 計算負荷の高い処理の効率化
   - メモリ使用量の削減

2. **計算結果のキャッシング強化**
   - キャッシュポリシーの最適化
   - キャッシュの無効化条件の明確化
   - セッション間でのキャッシュ共有メカニズムの検討

3. **レンダリング最適化**
   - グラフと可視化要素の描画最適化
   - 表形式データの効率的な表示
   - データ量に応じた表示調整

### 3.3 エラー処理とエッジケース対応

1. **異常データへの対応強化**
   - 極端に不正なデータセットでもクラッシュしない堅牢性
   - エラーメッセージの改善とユーザーガイダンスの強化
   - 部分的な問題でも可能な限り機能を提供

2. **エッジケースのサポート**
   - 大量のエラーを含むデータセットへの対応
   - GPS特有の問題パターンの検出と対応
   - 特殊なデータ形式や構造への柔軟な対応

3. **データ検証失敗時のフォールバック**
   - 検証失敗時の代替表示オプション
   - 部分的な検証結果の活用
   - ユーザーへの改善提案の提示

## 4. 技術仕様

### 4.1 ValidationDashboardの統合改善

```python
class ValidationDashboard:
    """
    データ検証ダッシュボードコンポーネント（改良版）
    """
    
    def __init__(self, 
                container: GPSDataContainer, 
                validator: Optional[DataValidator] = None,
                key_prefix: str = "validation_dashboard",
                on_fix_proposal: Optional[Callable[[str, str], Dict[str, Any]]] = None,
                on_export: Optional[Callable[[str], None]] = None,
                on_data_update: Optional[Callable[[GPSDataContainer], None]] = None,
                enable_advanced_features: bool = True):
        """
        拡張初期化メソッド
        """
        # 既存の初期化
        super().__init__(container, validator, key_prefix)
        
        # 拡張機能フラグ
        self.enable_advanced_features = enable_advanced_features
        
        # コールバック設定
        self.on_fix_proposal = on_fix_proposal
        self.on_export = on_export
        self.on_data_update = on_data_update
        
        # 進行状況管理
        self._processing_state = {}
        self._last_processed_data_hash = None
        
    def _render_report_tab(self) -> None:
        """改良されたレポートタブ表示"""
        # 実装内容
        
    def _render_spatial_problem_visualization(self, problem_indices: List[int]) -> None:
        """
        空間的問題を地図上に視覚化
        
        Parameters
        ----------
        problem_indices : List[int]
            問題のあるデータポイントのインデックスリスト
        """
        # 実装内容
        
    def _handle_fix_application(self, fix_result: Dict[str, Any]) -> None:
        """
        修正適用後の状態更新処理の改良
        
        Parameters
        ----------
        fix_result : Dict[str, Any]
            修正適用結果
        """
        # 実装内容
        
    def _render_progress_indicator(self, operation: str, progress: float = None) -> None:
        """
        処理進行状況の表示
        
        Parameters
        ----------
        operation : str
            実行中の操作名
        progress : float, optional
            進行状況（0.0～1.0）, by default None
        """
        # 実装内容
```

### 4.2 パフォーマンス最適化の実装

```python
def _optimize_data_processing(self, data: pd.DataFrame) -> pd.DataFrame:
    """
    大規模データセット処理の最適化（改良版）
    
    Parameters
    ----------
    data : pd.DataFrame
        処理対象のデータ
        
    Returns
    -------
    pd.DataFrame
        最適化されたデータ
    """
    # データが少なければ、そのまま返す（10,000行未満）
    if data is None or data.empty or len(data) < 10000:
        return data
        
    # データハッシュの計算（処理済みデータの再利用のため）
    data_hash = hash(tuple(data.shape) + tuple(data.columns))
    
    # 処理済みデータがあれば再利用
    cache_key = f"{self.key_prefix}_optimized_data_{data_hash}"
    if cache_key in st.session_state:
        return st.session_state[cache_key]
    
    # 処理進行状況表示
    self._render_progress_indicator("データ最適化", 0.1)
    
    # 基本サンプリング（均等に抽出）
    sample_size = min(5000, len(data) // 2)  # データ量に応じて調整
    step_size = max(1, len(data) // sample_size)
    base_sample = data.iloc[::step_size].copy()
    
    self._render_progress_indicator("データ最適化", 0.4)
    
    # 問題のある箇所を特定して追加
    problem_indices = self._get_problem_indices()
    
    # 問題のある行をサンプルに追加
    problem_rows = pd.DataFrame()
    if problem_indices:
        # インデックスの有効性を確認（範囲内のもののみ使用）
        valid_indices = [idx for idx in problem_indices if 0 <= idx < len(data)]
        if valid_indices:
            problem_rows = data.loc[valid_indices].copy()
    
    self._render_progress_indicator("データ最適化", 0.7)
    
    # 重要なデータポイントを特定して追加（例: 極値、変化の大きい点など）
    important_points = self._identify_important_points(data)
    important_rows = data.loc[important_points].copy() if important_points else pd.DataFrame()
    
    # 全てのサンプルを結合して重複を除去
    optimized_data = pd.concat([base_sample, problem_rows, important_rows]).drop_duplicates()
    
    # タイムスタンプでソート（あれば）
    if 'timestamp' in optimized_data.columns:
        optimized_data = optimized_data.sort_values('timestamp')
    
    self._render_progress_indicator("データ最適化", 1.0)
    
    # 結果をキャッシュに保存
    st.session_state[cache_key] = optimized_data
    
    return optimized_data

def _identify_important_points(self, data: pd.DataFrame) -> List[int]:
    """
    データ内の重要なポイントを特定
    
    Parameters
    ----------
    data : pd.DataFrame
        対象データ
        
    Returns
    -------
    List[int]
        重要なポイントのインデックスリスト
    """
    important_indices = []
    
    # データが少なすぎる場合は空リストを返す
    if len(data) < 10:
        return important_indices
    
    try:
        # 数値カラムに対して処理
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            if col in ['latitude', 'longitude', 'speed', 'course']:
                # NaNを無視
                series = data[col].dropna()
                
                if len(series) < 10:
                    continue
                
                # 極値（最大・最小）のインデックスを追加
                important_indices.extend(series.nlargest(3).index.tolist())
                important_indices.extend(series.nsmallest(3).index.tolist())
                
                # 変化率の大きいポイントを特定
                diff_series = series.diff().abs()
                if not diff_series.empty:
                    important_indices.extend(diff_series.nlargest(5).index.tolist())
    
    except Exception as e:
        # エラーが発生しても処理を継続
        print(f"重要ポイント特定中のエラー: {e}")
    
    # 重複を除去して返す
    return list(set(important_indices))
```

### 4.3 エラー処理の強化

```python
def _safely_render_visualization(self, render_func: Callable, fallback_message: str) -> None:
    """
    可視化の安全なレンダリング
    
    Parameters
    ----------
    render_func : Callable
        レンダリング関数
    fallback_message : str
        失敗時のフォールバックメッセージ
    """
    try:
        # 進行状況表示の準備
        progress_placeholder = st.empty()
        
        # プログレスバーの表示（必要に応じて）
        if hasattr(self, '_render_progress_indicator'):
            with progress_placeholder:
                self._render_progress_indicator("可視化処理", 0.5)
        
        # レンダリング関数を実行
        render_func()
        
        # プログレスバーのクリア
        progress_placeholder.empty()
        
    except Exception as e:
        # エラーメッセージと対処法の表示
        st.error(f"{fallback_message}: {str(e)}")
        st.info("データの検証と前処理を確認してください。問題が解決しない場合は、サンプル数を減らすか、データをクリーニングしてください。")
        
        # 詳細なエラー情報（開発用）
        if st.checkbox("詳細なエラー情報を表示", key=f"{self.key_prefix}_show_error_details"):
            st.code(traceback.format_exc())

def render(self) -> None:
    """
    ダッシュボード全体の強化されたレンダリング
    """
    try:
        # データの検証
        if self.container is None or self.container.data is None or self.container.data.empty:
            st.warning("データがありません。まずデータをインポートしてください。")
            return
            
        # タブの設定
        tabs = ["概要", "詳細分析", "問題箇所", "修正提案", "レポート"]
        
        # 高度な機能が無効の場合はタブを減らす
        if not self.enable_advanced_features:
            tabs = ["概要", "問題箇所", "レポート"]
        
        selected_tab = st.tabs(tabs)
        
        # タブごとのレンダリング（安全に実行）
        with selected_tab[0]:
            self._safely_render_visualization(
                self._render_overview_section,
                "概要の表示中にエラーが発生しました"
            )
            
        # 残りのタブも同様に実装...
            
    except Exception as e:
        # 致命的なエラーの場合
        st.error(f"ダッシュボードの表示中に予期しないエラーが発生しました: {str(e)}")
        st.info("サポートチームに問い合わせるか、データの形式を確認してください。")
        
        # 詳細なエラー情報
        if st.checkbox("詳細なエラー情報を表示", key=f"{self.key_prefix}_fatal_error_details"):
            st.code(traceback.format_exc())
```

### 4.4 修正提案の改良

```python
def _render_fix_proposals(self, report_data: Dict[str, Any]) -> None:
    """
    修正提案のレンダリング改良
    
    Parameters
    ----------
    report_data : Dict[str, Any]
        レポートデータ
    """
    st.subheader("修正提案")
    
    if "fix_proposals" not in report_data or not report_data["fix_proposals"]:
        st.info("自動修正提案はありません。データの品質が高いか、サポートされていない問題タイプです。")
        return
    
    proposals = report_data["fix_proposals"]
    
    # カテゴリ別に提案を整理
    categorized_proposals = {}
    for proposal in proposals:
        category = proposal.get("issue_type", "その他")
        if category not in categorized_proposals:
            categorized_proposals[category] = []
        categorized_proposals[category].append(proposal)
    
    # カテゴリタブを作成
    if categorized_proposals:
        category_tabs = st.tabs(list(categorized_proposals.keys()))
        
        # カテゴリごとに提案を表示
        for i, (category, category_proposals) in enumerate(categorized_proposals.items()):
            with category_tabs[i]:
                # 提案リストを表形式で表示
                proposal_data = []
                for j, proposal in enumerate(category_proposals):
                    proposal_data.append({
                        "No.": j+1,
                        "説明": proposal.get("description", ""),
                        "影響レコード数": len(proposal.get("affected_indices", [])),
                        "推奨方法": proposal.get("recommended_method", ""),
                        "品質向上見込み": self._format_quality_impact(proposal)
                    })
                
                proposal_df = pd.DataFrame(proposal_data)
                st.dataframe(proposal_df, use_container_width=True)
                
                # 提案選択と適用UI
                selected_proposal = st.selectbox(
                    "適用する提案を選択:",
                    options=range(len(category_proposals)),
                    format_func=lambda i: f"{proposal_data[i]['No']}. {proposal_data[i]['説明']}",
                    key=f"{self.key_prefix}_{category}_selected_proposal"
                )
                
                # 選択された提案の詳細を表示
                if 0 <= selected_proposal < len(category_proposals):
                    proposal = category_proposals[selected_proposal]
                    
                    # 提案詳細の表示
                    with st.expander("提案の詳細", expanded=True):
                        self._render_proposal_details(proposal, selected_proposal)
                    
                    # 適用ボタン
                    if self.on_fix_proposal and st.button("この提案を適用", key=f"{self.key_prefix}_{category}_apply_proposal"):
                        self._apply_selected_proposal(proposal)

def _render_proposal_details(self, proposal: Dict[str, Any], index: int) -> None:
    """
    提案詳細の表示
    
    Parameters
    ----------
    proposal : Dict[str, Any]
        修正提案データ
    index : int
        提案インデックス
    """
    # 提案の主要情報を表示
    cols = st.columns(2)
    with cols[0]:
        st.write("**影響範囲:**")
        st.write(f"- 対象レコード数: {len(proposal.get('affected_indices', []))}")
        st.write(f"- 対象カラム: {proposal.get('affected_column', '全カラム')}")
        
        # 重要度に基づいた色付きバッジの表示
        severity = proposal.get("severity", "info")
        severity_color = {
            "error": "red",
            "warning": "orange",
            "info": "blue",
            "batch": "green"
        }.get(severity, "gray")
        
        st.markdown(f"""
        <div style="display: inline-block; padding: 4px 8px; 
        background-color: {severity_color}; color: white; 
        border-radius: 4px; font-size: 0.8em;">
        {severity.upper()}
        </div