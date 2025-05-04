            }
        
        # 風向風速の更新
        self.wind_estimates = final_result
        
        # 結果のデータフレーム作成
        wind_df = self._create_wind_time_series(df, final_result)
        
        return wind_df
    
    def _estimate_wind_from_tacks(self) -> Optional[Dict[str, Any]]:
        """
        タックデータから風向を推定
        
        Returns:
        --------
        Optional[Dict[str, Any]]
            風向推定結果
        """
        if len(self.detected_maneuvers) < 2:
            return None
        
        # タックのみを抽出
        tacks = [m for m in self.detected_maneuvers if m['type'] == 'tack']
        
        if len(tacks) < 2:
            return None
        
        # タック前後の方位から風向を推定
        wind_directions = []
        for tack in tacks:
            try:
                idx = tack['index']
                bearing_before = tack['bearing_change']
                
                # タック角度の半分が風向と推定
                wind_dir = (bearing_before + 180) % 360
                wind_directions.append(wind_dir)
                
            except (KeyError, IndexError):
                continue
        
        if not wind_directions:
            return None
        
        # 平均風向を計算（循環平均）
        mean_wind_dir = self._circular_mean(wind_directions)
        
        # 風速の推定（デフォルト）
        wind_speed = 10.0  # ノット
        
        return {
            "direction": float(mean_wind_dir),
            "speed": float(wind_speed),
            "confidence": 0.7,
            "method": "tack_analysis",
            "timestamp": self.detected_maneuvers[-1]['timestamp']
        }
    
    def _circular_mean(self, angles: List[float]) -> float:
        """
        循環平均を計算
        
        Parameters:
        -----------
        angles : List[float]
            角度のリスト（度）
            
        Returns:
        --------
        float
            循環平均（度）
        """
        if not angles:
            return 0.0
        
        # ラジアンに変換
        angles_rad = np.radians(angles)
        
        # sin/cosの平均
        sin_mean = np.mean(np.sin(angles_rad))
        cos_mean = np.mean(np.cos(angles_rad))
        
        # 平均角度
        mean_angle = np.arctan2(sin_mean, cos_mean)
        
        return float(np.degrees(mean_angle) % 360)
    
    def _bayesian_wind_estimate(self, estimates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        複数の風向推定をベイズ統合（最適化版）
        
        Parameters:
        -----------
        estimates : List[Dict[str, Any]]
            風向風速推定結果のリスト
            
        Returns:
        --------
        Dict[str, Any]
            統合された風向風速推定結果
        """
        # 早期リターンで冗長な処理を削減
        if not estimates:
            return None
        
        # 1つだけの場合はそのまま返す（処理スキップ）
        if len(estimates) == 1:
            return estimates[0]
        
        # 有効な推定結果を事前に絞り込み（高速フィルタリング）
        # リスト内包表記を1回のループで済ませる
        valid_estimates = []
        for est in estimates:
            if est and est.get("confidence", 0) > 0:
                valid_estimates.append(est)
        
        # 有効な推定が1つもなければ早期リターン
        if not valid_estimates:
            return None
        
        # 1つだけの場合は処理を簡略化
        if len(valid_estimates) == 1:
            return valid_estimates[0]
        
        # データを一度で抽出（繰り返し辞書アクセスを回避）
        directions = []
        confidences = []
        speeds = []
        timestamps = []
        
        for est in valid_estimates:
            directions.append(est["direction"])
            confidences.append(est["confidence"])
            speeds.append(est["speed"])
            if est["timestamp"] is not None:
                timestamps.append(est["timestamp"])
        
        # numpy配列変換（一括処理）
        directions = np.array(directions, dtype=np.float32)
        confidences = np.array(confidences, dtype=np.float32)
        speeds = np.array(speeds, dtype=np.float32)
        
        # 効率的な角度計算（ラジアン変換を一度に実行）
        rad_angles = np.radians(directions)
        sin_vals = np.sin(rad_angles)
        cos_vals = np.cos(rad_angles)
        
        # 重みつき平均の加速（事前計算した値を利用）
        # confidencesの合計が0になる可能性をチェック
        conf_sum = np.sum(confidences)
        if conf_sum > 0:
            weighted_sin = np.sum(sin_vals * confidences) / conf_sum
            weighted_cos = np.sum(cos_vals * confidences) / conf_sum
            avg_dir = np.degrees(np.arctan2(weighted_sin, weighted_cos)) % 360
            avg_speed = np.sum(speeds * confidences) / conf_sum
            avg_confidence = np.mean(confidences)
        else:
            # フォールバック：単純平均
            avg_dir = self._circular_mean(directions.tolist())
            avg_speed = np.mean(speeds)
            avg_confidence = 0.1
        
        # タイムスタンプの処理（存在する場合のみ）
        latest_timestamp = max(timestamps) if timestamps else None
        
        return {
            "direction": float(avg_dir),
            "speed": float(avg_speed),
            "confidence": float(avg_confidence),
            "method": "bayesian_integration",
            "timestamp": latest_timestamp
        }
    
    def _create_wind_result(self, direction: float, speed: float, confidence: float, 
                          method: str, timestamp: Optional[datetime] = None) -> Dict[str, Any]:
        """
        風向風速の結果を作成
        
        Parameters:
        -----------
        direction : float
            風向（度）
        speed : float
            風速（ノット）
        confidence : float
            信頼度（0-1）
        method : str
            推定方法
        timestamp : datetime or None
            タイムスタンプ
            
        Returns:
        --------
        Dict[str, Any]
            風向風速推定結果
        """
        return {
            "direction": direction,
            "speed": speed,
            "confidence": confidence,
            "method": method,
            "timestamp": timestamp
        }
    
    def _create_wind_time_series(self, gps_df: pd.DataFrame, 
                                wind_estimate: Dict[str, Any]) -> pd.DataFrame:
        """
        GPSデータに対応する風向風速の時系列データを作成
        
        Parameters:
        -----------
        gps_df : pd.DataFrame
            GPSデータフレーム
        wind_estimate : Dict[str, Any]
            風向風速推定結果
            
        Returns:
        --------
        pd.DataFrame
            風向風速の時系列データフレーム
        """
        if gps_df.empty:
            return pd.DataFrame(columns=[
                'timestamp', 'wind_direction', 'wind_speed', 'confidence', 'method'
            ])
            
        # タイムスタンプの取得
        timestamps = gps_df['timestamp'].copy()
        
        # 推定値の取得
        direction = wind_estimate["direction"]
        speed = wind_estimate["speed"]
        confidence = wind_estimate["confidence"]
        method = wind_estimate["method"]
        
        # 結果のデータフレーム作成
        wind_df = pd.DataFrame({
            'timestamp': timestamps,
            'wind_direction': direction,
            'wind_speed': speed,
            'confidence': confidence,
            'method': method
        })
        
        return wind_df
