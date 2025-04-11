"""
sailing_data_processor.validation.quality_metrics_improvements

データ品質メトリクスの計算機能の追加実装
"""

from typing import Dict, List, Any, Optional, Tuple, Set
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from sailing_data_processor.data_model.container import GPSDataContainer

class QualityMetricsCalculatorExtension:
    """
    データ品質メトリクスの計算クラスの拡張部分
    これは既存のQualityMetricsCalculatorに追加される新しいメソッドを含む
    """
    
    def __init__(self, validation_results=None, data=None):
        """
        初期化メソッド
        元のクラスに対応するダミーの初期化メソッド
        
        Parameters
        ----------
        validation_results : List[Dict[str, Any]], optional
            DataValidatorから得られた検証結果
        data : pd.DataFrame, optional
            検証されたデータフレーム
        """
        # これは継承用のプレースホルダーで、直接インスタンス化して使用するためのものではありません
        self.validation_results = validation_results if validation_results else []
        self.data = data if data is not None else pd.DataFrame()
        self.problematic_indices = {"all": set()}
        
        # ルールカテゴリーの定義
        self.rule_categories = {
            "completeness": ["Required Columns Check", "No Null Values Check"],
            "accuracy": ["Value Range Check", "Spatial Consistency Check"],
            "consistency": ["No Duplicate Timestamps", "Temporal Consistency Check"]
        }
    
    def calculate_quality_scores(self) -> Dict[str, float]:
        """
        データ品質スコアを計算。
        
        0〜100の範囲で全体的なデータ品質を評価し、
        問題の重要度に基づく重み付け計算を行います。
        
        Returns
        -------
        Dict[str, float]
            各種品質スコア (total, completeness, accuracy, consistency)
        """
        # レコード総数を取得
        total_records = len(self.data)
        if total_records == 0:
            return {
                "total": 100.0,
                "completeness": 100.0,
                "accuracy": 100.0,
                "consistency": 100.0
            }
        
        # 問題のあるレコード数とその重み付け
        error_count = len(self.problematic_indices.get("all", set()))
        
        # 問題タイプごとの重み
        weights = {
            "missing_data": 1.0,  # エラー
            "out_of_range": 1.0,  # エラー
            "duplicates": 0.5,    # 警告
            "spatial_anomalies": 0.5,  # 警告
            "temporal_anomalies": 0.5  # 警告
        }
        
        # 重み付けされた問題スコアの計算
        weighted_sum = 0
        for problem_type, indices in self.problematic_indices.items():
            if problem_type != "all":
                weighted_sum += len(indices) * weights.get(problem_type, 0.1)
        
        # 総合スコアの計算（100点満点）
        total_score = max(0, 100 - (weighted_sum * 100 / total_records))
        
        # カテゴリ別スコアを計算
        category_scores = self.calculate_category_quality_scores()
        
        return {
            "total": round(total_score, 1),
            "completeness": category_scores["completeness"],
            "accuracy": category_scores["accuracy"],
            "consistency": category_scores["consistency"]
        }
    
    def calculate_category_quality_scores(self) -> Dict[str, float]:
        """
        カテゴリ別の品質スコアを計算。
        
        完全性（Completeness）: 欠損値や必須項目の充足度
        正確性（Accuracy）: 値の範囲や形式の正確さ
        一貫性（Consistency）: 時間的・空間的な整合性
        
        Returns
        -------
        Dict[str, Dict[str, float]]
            カテゴリ別の詳細スコア
        """
        total_records = len(self.data)
        if total_records == 0:
            return {
                "completeness": 100.0,
                "accuracy": 100.0,
                "consistency": 100.0
            }
        
        # カテゴリごとの問題数をカウント
        completeness_issues = len(self.problematic_indices.get("missing_data", []))
        accuracy_issues = len(self.problematic_indices.get("out_of_range", []))
        consistency_issues = len(self.problematic_indices.get("duplicates", [])) + \
                             len(self.problematic_indices.get("spatial_anomalies", [])) + \
                             len(self.problematic_indices.get("temporal_anomalies", []))
        
        # カラム数（欠損値チェック用）
        total_fields = len(self.data.columns) * total_records
        
        # スコアの計算
        completeness_score = max(0, 100 - (completeness_issues * 100 / total_fields))
        accuracy_score = max(0, 100 - (accuracy_issues * 100 / total_records))
        consistency_score = max(0, 100 - (consistency_issues * 100 / total_records))
        
        return {
            "completeness": round(completeness_score, 1),
            "accuracy": round(accuracy_score, 1),
            "consistency": round(consistency_score, 1)
        }
    
    def calculate_temporal_quality_scores(self) -> List[Dict[str, Any]]:
        """
        時間帯別の品質スコアを計算。
        
        1日を複数の時間帯に分割し、各時間帯の品質スコアを計算します。
        
        Returns
        -------
        List[Dict[str, Any]]
            各時間帯の品質情報
        """
        if "timestamp" not in self.data.columns or len(self.data) == 0:
            return []
        
        # タイムスタンプがdatetime型でない場合は変換
        if not pd.api.types.is_datetime64_any_dtype(self.data["timestamp"]):
            try:
                timestamps = pd.to_datetime(self.data["timestamp"])
            except:
                return []
        else:
            timestamps = self.data["timestamp"]
        
        # 時間帯の定義（4時間ごと）
        time_periods = [
            {"period": "早朝", "start_time": "04:00:00", "end_time": "08:00:00"},
            {"period": "午前", "start_time": "08:00:00", "end_time": "12:00:00"},
            {"period": "午後", "start_time": "12:00:00", "end_time": "16:00:00"},
            {"period": "夕方", "start_time": "16:00:00", "end_time": "20:00:00"},
            {"period": "夜間", "start_time": "20:00:00", "end_time": "00:00:00"},
            {"period": "深夜", "start_time": "00:00:00", "end_time": "04:00:00"}
        ]
        
        results = []
        
        for period in time_periods:
            # 時間範囲の開始と終了を解析
            start_hour, start_minute, start_second = map(int, period["start_time"].split(":"))
            end_hour, end_minute, end_second = map(int, period["end_time"].split(":"))
            
            # 時間帯に対応するインデックスを取得
            period_indices = []
            for i, ts in enumerate(timestamps):
                hour = ts.hour
                if start_hour <= end_hour:
                    if start_hour <= hour < end_hour:
                        period_indices.append(i)
                else:  # 夜間など、日付をまたぐ場合
                    if hour >= start_hour or hour < end_hour:
                        period_indices.append(i)
            
            # 該当時間帯のレコード数
            total_count = len(period_indices)
            
            if total_count == 0:
                continue  # この時間帯のデータがなければスキップ
            
            # 問題のあるレコード数
            problem_count = len(set(period_indices).intersection(self.problematic_indices.get("all", set())))
            
            # 品質スコアの計算
            quality_score = 100.0 if total_count == 0 else max(0, 100 - (problem_count * 100 / total_count))
            
            # 問題タイプの分布を計算
            problem_type_distribution = self._calculate_problem_type_distribution_for_period(period_indices)
            
            results.append({
                "period": period["period"],
                "start_time": period["start_time"],
                "end_time": period["end_time"],
                "quality_score": round(quality_score, 1),
                "problem_count": problem_count,
                "total_count": total_count,
                "problem_distribution": problem_type_distribution
            })
        
        return results
    
    def calculate_spatial_quality_scores(self) -> List[Dict[str, Any]]:
        """
        空間グリッド別の品質スコアを計算。
        
        地図を格子状に分割し、各グリッドの品質スコアを計算します。
        
        Returns
        -------
        List[Dict[str, Any]]
            各グリッドの品質情報
        """
        if "latitude" not in self.data.columns or "longitude" not in self.data.columns or len(self.data) == 0:
            return []
        
        # 緯度と経度の範囲を確認
        lat_min = self.data["latitude"].min()
        lat_max = self.data["latitude"].max()
        lon_min = self.data["longitude"].min()
        lon_max = self.data["longitude"].max()
        
        # グリッドのサイズを計算（エリアを5x5に分割）
        grid_rows = 5
        grid_cols = 5
        lat_step = (lat_max - lat_min) / grid_rows if lat_max > lat_min else 0.01
        lon_step = (lon_max - lon_min) / grid_cols if lon_max > lon_min else 0.01
        
        # 小さすぎるステップを防止
        lat_step = max(lat_step, 0.01)
        lon_step = max(lon_step, 0.01)
        
        results = []
        
        for row in range(grid_rows):
            for col in range(grid_cols):
                # グリッドの境界を計算
                min_lat = lat_min + row * lat_step
                max_lat = min_lat + lat_step
                min_lon = lon_min + col * lon_step
                max_lon = min_lon + lon_step
                
                # グリッドIDを作成（例：A1, B2など）
                grid_id = f"{chr(65 + row)}{col + 1}"
                
                # グリッド内のレコードのインデックスを特定
                grid_indices = []
                for i, (lat, lon) in enumerate(zip(self.data["latitude"], self.data["longitude"])):
                    if min_lat <= lat < max_lat and min_lon <= lon < max_lon:
                        grid_indices.append(i)
                
                # 該当グリッドのレコード数
                total_count = len(grid_indices)
                
                if total_count == 0:
                    continue  # このグリッドにデータがなければスキップ
                
                # 問題のあるレコード数
                problem_count = len(set(grid_indices).intersection(self.problematic_indices.get("all", set())))
                
                # 品質スコアの計算
                quality_score = 100.0 if total_count == 0 else max(0, 100 - (problem_count * 100 / total_count))
                
                # 問題タイプの分布を計算
                problem_type_distribution = self._calculate_problem_type_distribution_for_period(grid_indices)
                
                results.append({
                    "grid_id": grid_id,
                    "center": [(min_lat + max_lat) / 2, (min_lon + max_lon) / 2],
                    "bounds": {
                        "min_lat": min_lat,
                        "max_lat": max_lat,
                        "min_lon": min_lon,
                        "max_lon": max_lon
                    },
                    "quality_score": round(quality_score, 1),
                    "problem_count": problem_count,
                    "total_count": total_count,
                    "problem_distribution": problem_type_distribution
                })
        
        return results
    
    def _calculate_problem_type_distribution_for_period(self, period_indices: List[int]) -> Dict[str, int]:
        """
        特定の期間における問題タイプの分布を計算

        Parameters
        ----------
        period_indices : List[int]
            期間内のレコードインデックス

        Returns
        -------
        Dict[str, int]
            問題タイプ別のカウント
        """
        problem_type_counts = {
            "missing_data": 0,
            "out_of_range": 0,
            "duplicates": 0,
            "spatial_anomalies": 0,
            "temporal_anomalies": 0
        }
        
        # 期間内の各問題タイプのカウントを計算
        for problem_type, indices in self.problematic_indices.items():
            if problem_type != "all":
                # 期間内のインデックスと問題タイプのインデックスの交差を計算
                intersection = set(period_indices).intersection(set(indices))
                problem_type_counts[problem_type] = len(intersection)
        
        return problem_type_counts
    
    def calculate_temporal_quality_scores(self) -> List[Dict[str, Any]]:
        """
        時間帯別の品質スコアを計算。
        
        データを時間帯ごとに分析し、それぞれの時間帯の品質スコアと問題情報を計算します。
        これにより、時間的な品質変動を特定できます。
        
        Returns
        -------
        List[Dict[str, Any]]
            各時間帯の品質情報
        """
        # タイムスタンプカラムがない場合
        if "timestamp" not in self.data.columns:
            return []
        
        try:
            # 有効なタイムスタンプのみを抽出
            valid_data = self.data.dropna(subset=["timestamp"])
            
            if len(valid_data) < 2:
                return []
            
            # 問題のあるすべてのレコードのインデックス
            all_problem_indices = self.problematic_indices["all"]
            
            # 時間範囲を決定
            min_time = valid_data["timestamp"].min()
            max_time = valid_data["timestamp"].max()
            time_range = max_time - min_time
            
            # 時間を12個の区間に分割
            hours_bins = 12
            time_step = time_range / hours_bins
            
            # 時間帯ごとのスコアを計算
            temporal_scores = []
            
            for i in range(hours_bins):
                bin_start = min_time + time_step * i
                bin_end = min_time + time_step * (i + 1)
                
                # 時間帯内のレコードを抽出
                bin_mask = (valid_data["timestamp"] >= bin_start) & (valid_data["timestamp"] < bin_end)
                bin_indices = valid_data.index[bin_mask].tolist()
                
                if bin_indices:
                    # 時間帯内の問題レコード数
                    problem_indices_in_bin = set(bin_indices).intersection(set(all_problem_indices))
                    problem_count = len(problem_indices_in_bin)
                    total_count = len(bin_indices)
                    
                    # 問題の割合に基づく品質スコア
                    problem_percentage = problem_count / total_count * 100 if total_count > 0 else 0
                    quality_score = max(0, 100 - problem_percentage)
                    
                    # 人間が読みやすい時間帯ラベルを作成
                    label = f"{bin_start.strftime('%H:%M')}-{bin_end.strftime('%H:%M')}"
                    
                    # 問題タイプごとの分布も計算
                    problem_type_distribution = self._calculate_problem_type_distribution_for_period(bin_indices)
                    
                    # 品質スコアを保存
                    temporal_scores.append({
                        "period": f"期間{i+1}",
                        "start_time": bin_start.isoformat(),
                        "end_time": bin_end.isoformat(),
                        "label": label,
                        "quality_score": quality_score,
                        "problem_count": problem_count,
                        "total_count": total_count,
                        "problem_percentage": problem_percentage,
                        "impact_level": self._determine_impact_level(quality_score),
                        "problem_types": problem_type_distribution
                    })
            
            return temporal_scores
            
        except Exception as e:
            # エラーが発生した場合は空のリストを返す
            print(f"時間帯別の品質スコア計算中にエラー: {e}")
            return []
            
    def calculate_spatial_quality_scores(self) -> List[Dict[str, Any]]:
        """
        空間グリッド別の品質スコアを計算。
        
        データを空間的なグリッドに分割し、各グリッドの品質スコアと問題情報を計算します。
        これにより、空間的な品質変動を視覚的に把握できます。
        
        Returns
        -------
        List[Dict[str, Any]]
            各グリッドの品質情報
        """
        # 位置情報カラムがない場合
        if "latitude" not in self.data.columns or "longitude" not in self.data.columns:
            return []
            
        try:
            # 有効な位置情報を持つレコードのみを抽出
            valid_data = self.data.dropna(subset=["latitude", "longitude"])
            
            if len(valid_data) < 5:  # 最低5ポイント必要
                return []
                
            # 問題のあるすべてのレコードのインデックス
            all_problem_indices = self.problematic_indices["all"]
            
            # 位置の範囲を取得
            min_lat = valid_data["latitude"].min()
            max_lat = valid_data["latitude"].max()
            min_lon = valid_data["longitude"].min()
            max_lon = valid_data["longitude"].max()
            
            # 適切なグリッドサイズを決定（5x5グリッド）
            lat_bins = 5
            lon_bins = 5
            
            # 範囲が狭すぎる場合は調整
            if max_lat - min_lat < 0.001:
                center_lat = (max_lat + min_lat) / 2
                min_lat = center_lat - 0.005
                max_lat = center_lat + 0.005
                
            if max_lon - min_lon < 0.001:
                center_lon = (max_lon + min_lon) / 2
                min_lon = center_lon - 0.005
                max_lon = center_lon + 0.005
                
            lat_step = (max_lat - min_lat) / lat_bins
            lon_step = (max_lon - min_lon) / lon_bins
            
            # グリッドごとの品質スコアを計算
            spatial_scores = []
            
            for i in range(lat_bins):
                lat_start = min_lat + lat_step * i
                lat_end = min_lat + lat_step * (i + 1)
                
                for j in range(lon_bins):
                    lon_start = min_lon + lon_step * j
                    lon_end = min_lon + lon_step * (j + 1)
                    
                    # グリッド内のレコードを抽出
                    grid_mask = ((valid_data["latitude"] >= lat_start) & 
                                (valid_data["latitude"] < lat_end) & 
                                (valid_data["longitude"] >= lon_start) & 
                                (valid_data["longitude"] < lon_end))
                    grid_indices = valid_data.index[grid_mask].tolist()
                    
                    if grid_indices:  # グリッド内にデータがある場合
                        # グリッド内の問題レコード数
                        problem_indices_in_grid = set(grid_indices).intersection(set(all_problem_indices))
                        problem_count = len(problem_indices_in_grid)
                        total_count = len(grid_indices)
                        
                        # 問題の割合に基づく品質スコア
                        problem_percentage = problem_count / total_count * 100 if total_count > 0 else 0
                        quality_score = max(0, 100 - problem_percentage)
                        
                        # グリッドの中心座標
                        center_lat = (lat_start + lat_end) / 2
                        center_lon = (lon_start + lon_end) / 2
                        
                        # グリッドIDを生成
                        grid_id = f"grid_{i}_{j}"
                        
                        # 問題タイプごとの分布も計算
                        problem_type_distribution = self._calculate_problem_type_distribution_for_period(grid_indices)
                        
                        # 品質スコアを保存
                        spatial_scores.append({
                            "grid_id": grid_id,
                            "lat_range": (lat_start, lat_end),
                            "lon_range": (lon_start, lon_end),
                            "center": (center_lat, center_lon),
                            "quality_score": quality_score,
                            "problem_count": problem_count,
                            "total_count": total_count,
                            "problem_percentage": problem_percentage,
                            "impact_level": self._determine_impact_level(quality_score),
                            "problem_types": problem_type_distribution
                        })
            
            return spatial_scores
            
        except Exception as e:
            # エラーが発生した場合は空のリストを返す
            print(f"空間的な品質スコア計算中にエラー: {e}")
            return []
            
    def calculate_category_quality_scores(self) -> Dict[str, Dict[str, float]]:
        """
        カテゴリ別の品質スコアを計算。
        
        各品質カテゴリ（完全性、正確性、一貫性）の詳細なスコアと問題情報を計算します。
        カテゴリごとの細分化された問題タイプやその影響範囲も含みます。
        
        Returns
        -------
        Dict[str, Dict[str, float]]
            カテゴリ別の詳細スコア
        """
        category_scores = {}
        
        # 品質スコアを取得
        quality_scores = self.calculate_quality_scores()
        
        # 各カテゴリの詳細スコアを計算
        for category, rules in self.rule_categories.items():
            category_scores[category] = {
                "score": quality_scores[category],
                "issues": 0,
                "details": {},
                "impact_level": self._determine_impact_level(quality_scores[category])
            }
            
            # 各ルールの結果を集計
            for result in self.validation_results:
                rule_name = result["rule_name"]
                
                if any(rule in rule_name for rule in rules):
                    if not result["is_valid"]:
                        # 問題カウントを増加
                        category_scores[category]["issues"] += 1
                        
                        # 詳細情報を追加
                        details = result["details"]
                        rule_key = rule_name.replace(" ", "_").lower()
                        
                        if "out_of_range_count" in details:
                            category_scores[category]["details"][rule_key] = {
                                "count": details["out_of_range_count"],
                                "percentage": round(details["out_of_range_count"] / len(self.data) * 100, 2),
                                "severity": result["severity"],
                                "description": f"{details.get('column', '値')}の{details['out_of_range_count']}件が範囲外"
                            }
                        elif "duplicate_count" in details:
                            category_scores[category]["details"][rule_key] = {
                                "count": details["duplicate_count"],
                                "percentage": round(details["duplicate_count"] / len(self.data) * 100, 2),
                                "severity": result["severity"],
                                "description": f"{details['duplicate_count']}件の重複タイムスタンプ"
                            }
                        elif "total_null_count" in details:
                            total_fields = len(self.data) * len(details.get("columns", []))
                            percentage = 0 if total_fields == 0 else round(details["total_null_count"] / total_fields * 100, 2)
                            
                            category_scores[category]["details"][rule_key] = {
                                "count": details["total_null_count"],
                                "percentage": percentage,
                                "severity": result["severity"],
                                "affected_columns": list(details.get("null_counts", {}).keys()),
                                "description": f"{details['total_null_count']}件の欠損値"
                            }
                        elif "gap_count" in details:
                            category_scores[category]["details"][rule_key] = {
                                "gap_count": details["gap_count"],
                                "reverse_count": details.get("reverse_count", 0),
                                "max_gap": details.get("max_actual_gap", 0),
                                "percentage": round((details["gap_count"] + details.get("reverse_count", 0)) / len(self.data) * 100, 2),
                                "severity": result["severity"],
                                "description": f"{details['gap_count']}件のギャップ、{details.get('reverse_count', 0)}件の逆行"
                            }
                        elif "missing_columns" in details:
                            category_scores[category]["details"][rule_key] = {
                                "missing_columns": details["missing_columns"],
                                "count": len(details["missing_columns"]),
                                "severity": result["severity"],
                                "description": f"{len(details['missing_columns'])}個の必須カラムが欠落"
                            }
                        elif "anomaly_count" in details:
                            category_scores[category]["details"][rule_key] = {
                                "count": details["anomaly_count"],
                                "percentage": round(details["anomaly_count"] / len(self.data) * 100, 2),
                                "max_speed": details.get("max_calculated_speed", 0),
                                "severity": result["severity"],
                                "description": f"{details['anomaly_count']}件の空間的異常"
                            }
        
        return category_scores
            
    def generate_quality_score_visualization(self) -> Tuple[go.Figure, go.Figure]:
        """
        品質スコアのゲージチャートとカテゴリ別バーチャートを生成。
        
        品質スコアの視覚的表現として、総合スコアを円形ゲージで、
        カテゴリ別スコア（完全性、正確性、一貫性）を棒グラフで表示します。
        
        Returns
        -------
        Tuple[go.Figure, go.Figure]
            ゲージチャートとバーチャート
        """
        import plotly.graph_objects as go
        
        # 品質スコアを取得
        quality_scores = self.calculate_quality_scores()
        
        # ゲージチャートを生成（総合スコア用）
        gauge_chart = go.Figure(go.Indicator(
            mode="gauge+number",
            value=quality_scores["total"],
            title={"text": "データ品質スコア", "font": {"size": 24}},
            number={"font": {"size": 32, "color": self._get_score_color(quality_scores["total"])}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "darkblue"},
                "bar": {"color": self._get_score_color(quality_scores["total"])},
                "bgcolor": "white",
                "borderwidth": 2,
                "bordercolor": "gray",
                "steps": [
                    {"range": [0, 50], "color": "#FFCCCC"},  # 赤系 - 低品質
                    {"range": [50, 75], "color": "#FFEEAA"},  # 黄系 - 中品質
                    {"range": [75, 90], "color": "#CCFFCC"},  # 緑系 - 高品質
                    {"range": [90, 100], "color": "#AAFFAA"}  # 濃い緑系 - 非常に高品質
                ],
                "threshold": {
                    "line": {"color": "black", "width": 4},
                    "thickness": 0.75,
                    "value": quality_scores["total"]
                }
            }
        ))
        
        # レイアウト設定
        gauge_chart.update_layout(
            height=300,
            margin=dict(t=40, b=0, l=40, r=40),
            paper_bgcolor="white",
            font={"family": "Arial", "size": 12}
        )
        
        # ベストプラクティスの追加
        if quality_scores["total"] >= 90:
            gauge_chart.add_annotation(
                x=0.5, y=0.7,
                text="高品質",
                showarrow=False,
                font={"size": 16, "color": "green"},
                align="center"
            )
        elif quality_scores["total"] < 50:
            gauge_chart.add_annotation(
                x=0.5, y=0.7,
                text="要改善",
                showarrow=False,
                font={"size": 16, "color": "red"},
                align="center"
            )
        
        # カテゴリ別バーチャートを生成
        categories = ["completeness", "accuracy", "consistency"]
        values = [quality_scores[cat] for cat in categories]
        
        # カテゴリ名の日本語対応
        category_names = {
            "completeness": "完全性",
            "accuracy": "正確性",
            "consistency": "一貫性"
        }
        
        # カテゴリ別の色設定
        bar_colors = [
            self._get_score_color(values[0]),
            self._get_score_color(values[1]),
            self._get_score_color(values[2])
        ]
        
        display_categories = [category_names[cat] for cat in categories]
        
        bar_chart = go.Figure(data=[
            go.Bar(
                x=display_categories,
                y=values,
                marker_color=bar_colors,
                text=[f"{v:.1f}" for v in values],
                textposition="auto",
                hoverinfo="text",
                hovertext=[
                    f"完全性スコア: {values[0]:.1f}<br>欠損値や必須項目の充足度",
                    f"正確性スコア: {values[1]:.1f}<br>値の範囲や形式の正確さ",
                    f"一貫性スコア: {values[2]:.1f}<br>時間的・空間的な整合性"
                ]
            )
        ])
        
        # 目標ラインの追加（品質目標：90点）
        bar_chart.add_shape(
            type="line",
            x0=-0.5, y0=90, x1=2.5, y1=90,
            line=dict(color="green", width=2, dash="dash"),
            name="品質目標"
        )
        
        bar_chart.update_layout(
            title={
                "text": "カテゴリ別品質スコア",
                "y": 0.9,
                "x": 0.5,
                "xanchor": "center",
                "yanchor": "top"
            },
            yaxis={
                "title": "品質スコア",
                "range": [0, 105],
                "tickvals": [0, 25, 50, 75, 90, 100],
                "ticktext": ["0", "25", "50", "75", "90", "100"],
                "gridcolor": "lightgray"
            },
            height=350,
            margin=dict(t=60, b=30, l=40, r=40),
            paper_bgcolor="white",
            plot_bgcolor="white",
            font={"family": "Arial", "size": 12},
            showlegend=False
        )
        
        return gauge_chart, bar_chart
    
    def _get_score_color(self, score: float) -> str:
        """
        スコアに応じた色を返す
        
        Parameters
        ----------
        score : float
            品質スコア（0-100）
            
        Returns
        -------
        str
            対応する色のHEXコード
        """
        if score >= 90:
            return "#27AE60"  # 濃い緑
        elif score >= 75:
            return "#2ECC71"  # 緑
        elif score >= 50:
            return "#F1C40F"  # 黄色
        elif score >= 25:
            return "#E67E22"  # オレンジ
        else:
            return "#E74C3C"  # 赤
            
    def _determine_impact_level(self, score: float) -> str:
        """
        品質スコアから影響レベルを決定する
        
        Parameters
        ----------
        score : float
            品質スコア (0-100)
            
        Returns
        -------
        str
            影響レベル
        """
        if score >= 90:
            return "low"       # 低影響
        elif score >= 75:
            return "medium"    # 中程度の影響
        elif score >= 50:
            return "high"      # 高影響
        else:
            return "critical"  # 重大な影響
            
    def generate_spatial_quality_map(self) -> go.Figure:
        """
        空間的な品質分布のマップを生成。
        
        GPSデータの空間的な品質分布を地図上に視覚化します。
        各エリアは品質スコアによって色分けされ、品質の空間的な変動を把握できます。
        
        Returns
        -------
        go.Figure
            品質マップの図
        """
        import plotly.graph_objects as go
        
        # 空間品質スコアを取得
        spatial_scores = self.calculate_spatial_quality_scores()
        
        if not spatial_scores:
            # データがない場合は空のマップを返す
            fig = go.Figure()
            fig.update_layout(
                title="空間的な品質分布マップ (データなし)",
                height=500,
                margin=dict(t=50, b=0, l=0, r=0)
            )
            return fig
        
        # マップの中心座標を計算
        all_lats = []
        all_lons = []
        for grid in spatial_scores:
            center = grid["center"]
            all_lats.append(center[0])
            all_lons.append(center[1])
        
        center_lat = sum(all_lats) / len(all_lats) if all_lats else 0
        center_lon = sum(all_lons) / len(all_lons) if all_lons else 0
        
        # マップの作成
        fig = go.Figure()
        
        # 各グリッドのポリゴンを追加
        for grid in spatial_scores:
            lat_range = grid["lat_range"]
            lon_range = grid["lon_range"]
            quality_score = grid["quality_score"]
            
            # グリッドの四隅の座標
            lats = [lat_range[0], lat_range[1], lat_range[1], lat_range[0]]
            lons = [lon_range[0], lon_range[0], lon_range[1], lon_range[1]]
            
            # ポリゴンの色を品質スコアから決定
            color = self._get_score_color(quality_score)
            
            # ホバーテキストを作成
            hover_text = (
                f"品質スコア: {quality_score:.1f}<br>" +
                f"問題数: {grid['problem_count']}<br>" +
                f"総レコード数: {grid['total_count']}<br>" +
                f"問題率: {(grid['problem_count'] / grid['total_count'] * 100):.1f}%"
            )
            
            # 問題タイプの内訳があれば追加
            if "problem_types" in grid:
                problem_type_text = "<br>問題タイプ内訳:<br>"
                for problem_type, count in grid["problem_types"].items():
                    if count > 0:
                        type_name = {
                            "missing_data": "欠損値",
                            "out_of_range": "範囲外の値",
                            "duplicates": "重複データ",
                            "spatial_anomalies": "空間的異常",
                            "temporal_anomalies": "時間的異常"
                        }.get(problem_type, problem_type)
                        problem_type_text += f" - {type_name}: {count}件<br>"
                hover_text += problem_type_text
            
            # 各グリッドのポリゴンを追加
            fig.add_trace(go.Scattermapbox(
                lat=lats + [lats[0]],  # 閉じたポリゴンにするため最初の点を追加
                lon=lons + [lons[0]],
                mode="lines",
                line=dict(width=1, color=color),
                fill="toself",
                fillcolor=color,
                opacity=0.6,
                text=hover_text,
                hoverinfo="text",
                name=f"グリッド（スコア: {quality_score:.1f}）"
            ))
            
            # グリッドの中心にスコアを表示するマーカーを追加
            fig.add_trace(go.Scattermapbox(
                lat=[grid["center"][0]],
                lon=[grid["center"][1]],
                mode="markers+text",
                marker=dict(size=10, color="white", opacity=0.7),
                text=[f"{quality_score:.0f}"],
                textfont=dict(size=10, color="black"),
                hoverinfo="none"
            ))
        
        # マップレイアウトの設定
        fig.update_layout(
            title="空間的な品質分布マップ",
            mapbox=dict(
                style="open-street-map",
                center=dict(lat=center_lat, lon=center_lon),
                zoom=12
            ),
            height=500,
            margin=dict(t=50, b=0, l=0, r=0),
            showlegend=False
        )
        
        # 凡例として、品質スコアレンジの説明をアノテーションとして追加
        fig.add_annotation(
            x=0.02, y=0.02,
            xref="paper", yref="paper",
            text=(
                "品質スコア<br>" +
                "<span style='color:#E74C3C'>■</span> 0-25: 重大な問題<br>" +
                "<span style='color:#E67E22'>■</span> 25-50: 多数の問題<br>" +
                "<span style='color:#F1C40F'>■</span> 50-75: 一部に問題<br>" +
                "<span style='color:#2ECC71'>■</span> 75-90: 良好<br>" +
                "<span style='color:#27AE60'>■</span> 90-100: 優良"
            ),
            showarrow=False,
            align="left",
            bgcolor="rgba(255, 255, 255, 0.8)",
            bordercolor="gray",
            borderwidth=1,
            borderpad=4,
            font=dict(size=10)
        )
        
        return fig
        
    def generate_temporal_quality_chart(self) -> go.Figure:
        """
        時間帯別の品質分布チャートを生成。
        
        時間帯ごとの品質スコアをグラフ化し、時間的な品質の変動を視覚化します。
        各時間帯のデータ量と問題発生率も表示します。
        
        Returns
        -------
        go.Figure
            時間帯別品質チャート
        """
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        
        # 時間的品質スコアを取得
        temporal_scores = self.calculate_temporal_quality_scores()
        
        if not temporal_scores:
            # データがない場合は空のチャートを返す
            fig = go.Figure()
            fig.update_layout(
                title="時間帯別の品質スコア (データなし)",
                height=400,
                margin=dict(t=50, b=50, l=40, r=40)
            )
            return fig
        
        # 時間順にソート
        temporal_scores.sort(key=lambda x: x["start_time"])
        
        # チャートデータの準備
        labels = [score["label"] for score in temporal_scores]
        quality_scores = [score["quality_score"] for score in temporal_scores]
        problem_counts = [score["problem_count"] for score in temporal_scores]
        total_counts = [score["total_count"] for score in temporal_scores]
        problem_percentages = [score["problem_percentage"] for score in temporal_scores]
        
        # 問題タイプごとのデータを抽出（存在する場合）
        problem_types_data = {}
        if "problem_types" in temporal_scores[0]:
            # 問題タイプのキーを取得
            problem_type_keys = temporal_scores[0]["problem_types"].keys()
            
            for key in problem_type_keys:
                problem_types_data[key] = [score["problem_types"].get(key, 0) for score in temporal_scores]
        
        # サブプロットの数を決定
        if problem_types_data:
            subplot_rows = 3  # 品質スコア、データ量と問題率、問題タイプ分布
        else:
            subplot_rows = 2  # 品質スコア、データ量と問題率のみ
        
        # グラフの作成（サブプロット）
        fig = make_subplots(
            rows=subplot_rows, 
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.1,
            subplot_titles=(
                ["時間帯別品質スコア", "時間帯別データ量と問題率"] + 
                (["問題タイプ別分布"] if problem_types_data else [])
            ),
            specs=[
                [{"type": "bar"}],
                [{"type": "scatter"}]
            ] + ([{"type": "bar"}] if problem_types_data else [])
        )
        
        # 品質スコアのバーチャート
        bar_colors = [self._get_score_color(score) for score in quality_scores]
        
        # 品質スコアのバーチャート（上の図）
        fig.add_trace(
            go.Bar(
                x=labels,
                y=quality_scores,
                marker_color=bar_colors,
                text=[f"{score:.1f}" for score in quality_scores],
                textposition="auto",
                hoverinfo="text",
                hovertext=[
                    (f"時間帯: {labels[i]}<br>" +
                     f"品質スコア: {quality_scores[i]:.1f}<br>" +
                     f"データ量: {total_counts[i]}<br>" +
                     f"問題数: {problem_counts[i]}")
                    for i in range(len(labels))
                ],
                name="品質スコア"
            ),
            row=1, col=1
        )
        
        # 目標ラインの追加（品質目標：90点）
        fig.add_shape(
            type="line",
            x0=-0.5, y0=90, 
            x1=len(labels) - 0.5, y1=90,
            line=dict(color="green", width=2, dash="dash"),
            row=1, col=1
        )
        
        # データ量のラインチャート（下の図）
        fig.add_trace(
            go.Scatter(
                x=labels,
                y=total_counts,
                mode="lines+markers",
                name="データ量",
                line=dict(color="blue", width=2),
                marker=dict(size=8, color="blue"),
                hoverinfo="text",
                hovertext=[f"時間帯: {labels[i]}<br>データ量: {total_counts[i]}" for i in range(len(labels))]
            ),
            row=2, col=1
        )
        
        # 問題率のラインチャート（2次Y軸）
        fig.add_trace(
            go.Scatter(
                x=labels,
                y=problem_percentages,
                mode="lines+markers",
                name="問題率 (%)",
                line=dict(color="red", width=2, dash="dot"),
                marker=dict(size=8, color="red"),
                hoverinfo="text",
                hovertext=[f"時間帯: {labels[i]}<br>問題率: {problem_percentages[i]:.1f}%" for i in range(len(labels))],
                yaxis="y3"
            ),
            row=2, col=1
        )
        
        # 問題タイプの内訳がある場合、それも表示
        if problem_types_data:
            # 問題タイプごとの色を設定
            type_colors = {
                "missing_data": "blue",
                "out_of_range": "red",
                "duplicates": "green",
                "spatial_anomalies": "purple",
                "temporal_anomalies": "orange"
            }
            
            # 問題タイプごとの表示名
            type_names = {
                "missing_data": "欠損値",
                "out_of_range": "範囲外の値",
                "duplicates": "重複データ",
                "spatial_anomalies": "空間的異常",
                "temporal_anomalies": "時間的異常"
            }
            
            # 積み上げバーチャートのデータ準備
            bar_data = []
            for key in problem_types_data:
                if sum(problem_types_data[key]) > 0:
                    bar_data.append({
                        "name": type_names.get(key, key),
                        "values": problem_types_data[key],
                        "color": type_colors.get(key, "gray")
                    })
            
            # 積み上げバーチャートを追加
            for data in bar_data:
                fig.add_trace(
                    go.Bar(
                        x=labels,
                        y=data["values"],
                        name=data["name"],
                        marker_color=data["color"],
                        hoverinfo="text",
                        hovertext=[
                            f"時間帯: {labels[i]}<br>{data['name']}: {data['values'][i]}件"
                            for i in range(len(labels))
                        ]
                    ),
                    row=3, col=1
                )
        
        # レイアウト設定
        fig.update_layout(
            height=600 if problem_types_data else 500,
            margin=dict(t=70, b=50, l=50, r=50),
            paper_bgcolor="white",
            plot_bgcolor="white",
            font=dict(family="Arial", size=12),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            hovermode="closest",
            barmode="stack" if problem_types_data else None
        )
        
        # Y軸の設定
        fig.update_yaxes(
            title_text="品質スコア",
            range=[0, 105],
            tickvals=[0, 25, 50, 75, 90, 100],
            gridcolor="lightgray",
            row=1, col=1
        )
        
        fig.update_yaxes(
            title_text="データ量",
            range=[0, max(total_counts) * 1.1],
            gridcolor="lightgray",
            row=2, col=1,
            title_standoff=0
        )
        
        # 2次Y軸（問題率）の追加
        fig.update_layout(
            yaxis3=dict(
                title="問題率 (%)",
                titlefont=dict(color="red"),
                tickfont=dict(color="red"),
                anchor="x",
                overlaying="y2",
                side="right",
                range=[0, max(problem_percentages) * 1.1 if problem_percentages else 10],
                showgrid=False
            )
        )
        
        # 問題タイプの内訳グラフのY軸設定
        if problem_types_data:
            fig.update_yaxes(
                title_text="問題数",
                gridcolor="lightgray",
                row=3, col=1
            )
        
        # X軸の設定（斜めに表示）
        fig.update_xaxes(
            tickangle=-45,
            row=subplot_rows, col=1
        )
        
        return fig