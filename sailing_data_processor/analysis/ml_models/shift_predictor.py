    def _normalize_weights(self) -> None:
        """モデルの重みを正規化"""
        # 重みの合計
        total_weight = sum(self.model_weights.values())
        
        # 重みの合計がゼロでない場合は正規化
        if total_weight > 0:
            for model_name in self.model_weights:
                self.model_weights[model_name] /= total_weight
        # 重みの合計がゼロの場合は均等配分
        else:
            n_models = len(self.model_weights)
            if n_models > 0:
                for model_name in self.model_weights:
                    self.model_weights[model_name] = 1.0 / n_models
    
    def _calculate_weighted_metrics(self, training_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        重み付き平均でメトリクスを計算
        
        Parameters
        ----------
        training_results : Dict[str, Dict[str, Any]]
            各モデルのトレーニング結果
            
        Returns
        -------
        Dict[str, Any]
            重み付き平均のメトリクス
        """
        # 各モデルのメトリクス
        metrics = {}
        
        # バリデーションメトリクス
        validation_maes = []
        validation_weights = []
        
        for model_name, result in training_results.items():
            if result.get('status') == 'success' and 'metrics' in result:
                model_metrics = result['metrics']
                
                # バリデーションメトリクス
                if 'validation' in model_metrics:
                    mae = model_metrics['validation'].get('mae', float('inf'))
                    
                    # 有効な値の場合のみ追加
                    if isinstance(mae, (int, float)) and mae < float('inf'):
                        validation_maes.append(mae)
                        # モデルの重みを使用
                        validation_weights.append(self.model_weights[model_name])
        
        # バリデーションMAEの重み付き平均
        if validation_maes and validation_weights and sum(validation_weights) > 0:
            metrics['validation'] = {
                'mae': sum(m * w for m, w in zip(validation_maes, validation_weights)) / sum(validation_weights),
                'models_used': len(validation_maes)
            }
        
        # トレーニングサイズの合計
        total_training_size = sum(
            result.get('training_size', 0) 
            for result in training_results.values() 
            if result.get('status') == 'success'
        )
        
        metrics['total_training_size'] = total_training_size
        
        return metrics
    
    def _simple_prediction(self, current_data: pd.DataFrame, horizon: int) -> pd.DataFrame:
        """
        単純な予測（フォールバック手段）
        
        Parameters
        ----------
        current_data : DataFrame
            現在のデータ
        horizon : int
            予測時間（分）
            
        Returns
        -------
        DataFrame
            予測結果
        """
        if current_data.empty:
            # データがない場合は仮の値を返す
            return pd.DataFrame({
                'timestamp': [datetime.now() + timedelta(minutes=i) for i in range(horizon)],
                'predicted_direction': [0] * horizon,
                'confidence': [0.1] * horizon,
                'shift_point': [False] * horizon
            })
        
        # データの前処理
        df = current_data.copy()
        if 'timestamp' not in df.columns or 'wind_direction' not in df.columns:
            # 必要なカラムがない場合は仮の値を返す
            return pd.DataFrame({
                'timestamp': [datetime.now() + timedelta(minutes=i) for i in range(horizon)],
                'predicted_direction': [0] * horizon,
                'confidence': [0.1] * horizon,
                'shift_point': [False] * horizon
            })
        
        # 最新の風向と時刻
        latest_dir = df['wind_direction'].iloc[-1] if len(df) > 0 else 0
        latest_time = df['timestamp'].max() if len(df) > 0 else datetime.now()
        
        # 風向の変化率
        if len(df) >= 10:
            # 最近の変化傾向を計算
            recent_data = df.iloc[-10:]
            diffs = []
            for i in range(1, len(recent_data)):
                diff = self._calculate_angle_difference(
                    recent_data['wind_direction'].iloc[i],
                    recent_data['wind_direction'].iloc[i-1]
                )
                diffs.append(diff)
            
            # 平均変化率
            avg_diff = sum(diffs) / len(diffs) if diffs else 0
            
            # 単純な線形予測
            predicted_dirs = []
            current_dir = latest_dir
            
            for _ in range(horizon):
                # 小さなランダム変動を加える
                noise = np.random.normal(0, 1) * min(3.0, abs(avg_diff) + 0.5)
                next_dir = (current_dir + avg_diff + noise) % 360
                predicted_dirs.append(next_dir)
                current_dir = next_dir
            
            # 信頼度は遠い将来ほど低下
            confidence = np.linspace(0.4, 0.2, horizon)
        else:
            # データが少ない場合は定常予測
            predicted_dirs = [latest_dir] * horizon
            confidence = np.linspace(0.3, 0.1, horizon)
        
        # 予測時間の作成
        future_times = [latest_time + timedelta(minutes=i+1) for i in range(horizon)]
        
        # 風速予測（利用可能であれば）
        predicted_speeds = None
        if 'wind_speed' in df.columns:
            latest_speed = df['wind_speed'].iloc[-1] if len(df) > 0 else 0
            predicted_speeds = [max(0, latest_speed + np.random.normal(0, 0.5)) for _ in range(horizon)]
        
        # 結果のデータフレーム作成
        result = pd.DataFrame({
            'timestamp': future_times,
            'predicted_direction': predicted_dirs,
            'confidence': confidence
        })
        
        if predicted_speeds is not None:
            result['predicted_speed'] = predicted_speeds
        
        # 予測シフトポイントの検出
        result['shift_point'] = False
        for i in range(1, len(result)):
            direction_change = self._calculate_angle_difference(
                result['predicted_direction'].iloc[i],
                result['predicted_direction'].iloc[i-1]
            )
            # 5度以上の変化があればシフトポイントと判定
            if abs(direction_change) >= 5.0:
                result.at[result.index[i], 'shift_point'] = True
                result.at[result.index[i], 'shift_magnitude'] = direction_change
        
        return result
    
    def _calculate_angle_difference(self, angle1: float, angle2: float) -> float:
        """
        2つの角度の差を計算（-180〜180度の範囲で返す）
        
        Parameters
        ----------
        angle1 : float
            1つ目の角度（度、0-360）
        angle2 : float
            2つ目の角度（度、0-360）
            
        Returns
        -------
        float
            角度差（度、-180〜180）
        """
        # 角度が無効な場合は0を返す
        if not isinstance(angle1, (int, float)) or not isinstance(angle2, (int, float)):
            return 0
        
        # 角度を0-360の範囲に正規化
        a1 = angle1 % 360
        a2 = angle2 % 360
        
        # 角度差を計算（-180〜180度の範囲）
        diff = ((a1 - a2 + 180) % 360) - 180
        
        return diff
    
    def _get_model_state(self) -> Dict[str, Any]:
        """
        モデル固有の状態を取得
        
        Returns
        -------
        Dict[str, Any]
            モデル状態
        """
        state = {
            'model_weights': self.model_weights,
            'sub_models': {}
        }
        
        # サブモデルの状態を保存
        for model_name, model in self.sub_models.items():
            # モデルの重みがゼロでない場合のみ保存
            if self.model_weights.get(model_name, 0) > 0:
                state['sub_models'][model_name] = {
                    'is_trained': model.is_trained,
                    'last_update': model.last_update,
                    'model_class': model.__class__.__name__,
                    'model_state': model._get_model_state()
                }
        
        return state
    
    def _set_model_state(self, state: Dict[str, Any]) -> None:
        """
        モデル固有の状態を設定
        
        Parameters
        ----------
        state : Dict[str, Any]
            モデル状態
        """
        # 重みの復元
        self.model_weights = state.get('model_weights', self.model_weights)
        
        # サブモデルの状態を復元
        sub_models_state = state.get('sub_models', {})
        
        for model_name, model_state in sub_models_state.items():
            if model_name in self.sub_models:
                model = self.sub_models[model_name]
                
                # モデルクラスの確認
                if model_state.get('model_class') == model.__class__.__name__:
                    model.is_trained = model_state.get('is_trained', False)
                    model.last_update = model_state.get('last_update')
                    
                    # モデル固有の状態を復元
                    model._set_model_state(model_state.get('model_state', {}))
                else:
                    warnings.warn(f"Model class mismatch for {model_name}: expected {model.__class__.__name__}, got {model_state.get('model_class')}")


class WindShiftPredictor:
    """
    風向シフト予測クラス
    
    過去のデータパターンから将来の風向シフトを予測する機械学習モデルを提供します。
    """
    
    def __init__(self, model_type="ensemble", prediction_horizon=30, confidence_interval=0.9, **kwargs):
        """
        初期化
        
        Parameters
        ----------
        model_type : str, optional
            モデルタイプ ("arima", "prophet", "lstm", "ensemble"), by default "ensemble"
        prediction_horizon : int, optional
            予測時間（分）, by default 30
        confidence_interval : float, optional
            信頼区間 (0.0-1.0), by default 0.9
        **kwargs : dict
            追加のパラメータ
        """
        self.model_type = model_type
        self.prediction_horizon = prediction_horizon
        self.confidence_interval = confidence_interval
        
        # 追加パラメータ
        self.params = {
            "training_window": kwargs.get("training_window", 180),  # 学習ウィンドウ（分）
            "update_frequency": kwargs.get("update_frequency", 5),  # 更新頻度（分）
            "features": kwargs.get("features", ["wind_direction", "wind_speed", "time_of_day"]),
            "use_external_data": kwargs.get("use_external_data", False),  # 外部データの使用
            "regularization": kwargs.get("regularization", 0.01),  # 正則化パラメータ
        }
        
        # 共通パラメータの設定
        common_params = {
            "prediction_horizon": prediction_horizon,
            "confidence_interval": confidence_interval,
            **self.params
        }
        
        # モデルの初期化
        self._init_model(common_params)
        
        # モデル状態
        self.is_trained = False
        self.last_update = None
        self.performance_metrics = {}
    
    def _init_model(self, params):
        """モデルの初期化"""
        if self.model_type == "arima":
            self._model = ARIMAModel(params)
        elif self.model_type == "prophet":
            self._model = ProphetModel(params)
        elif self.model_type == "lstm":
            self._model = LSTMModel(params)
        elif self.model_type == "ensemble":
            # アンサンブルモデルの場合は使用するモデルタイプを指定
            ensemble_params = params.copy()
            ensemble_params["model_types"] = ["arima", "prophet"]
            # LSTMは計算コストが高いため必要時のみ追加
            if params.get("use_lstm", False):
                ensemble_params["model_types"].append("lstm")
            self._model = EnsembleModel(ensemble_params)
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")
    
    def train(self, historical_data, validation_ratio=0.2):
        """
        モデルの学習
        
        Parameters
        ----------
        historical_data : DataFrame
            過去の風向・風速データ
        validation_ratio : float, optional
            検証データの割合, by default 0.2
            
        Returns
        -------
        dict
            トレーニング結果と評価指標
        """
        # データの検証
        if not isinstance(historical_data, pd.DataFrame):
            raise ValueError("Historical data must be a pandas DataFrame")
        
        if historical_data.empty:
            raise ValueError("Historical data is empty")
        
        # 必要なカラムの確認
        required_columns = ['timestamp', 'wind_direction']
        missing_columns = [col for col in required_columns if col not in historical_data.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # モデルのトレーニング
        training_result = self._model.train(historical_data, validation_ratio)
        
        # 結果の処理
        if training_result.get('status') == 'success' or ('metrics' in training_result and training_result['metrics']):
            self.is_trained = True
            self.last_update = datetime.now()
            
            # パフォーマンスメトリクスの更新
            if 'metrics' in training_result:
                self.performance_metrics = training_result['metrics']
        else:
            warnings.warn("Training was not fully successful")
        
        return training_result
    
    def predict(self, current_data, horizon=None):
        """
        風向シフトを予測
        
        Parameters
        ----------
        current_data : DataFrame
            現在の風向・風速データ
        horizon : int, optional
            予測時間（分）, by default None (インスタンス設定値を使用)
            
        Returns
        -------
        DataFrame
            予測結果
        """
        if not self.is_trained:
            warnings.warn("Model is not trained yet. Call train() first.")
        
        # モデルによる予測
        forecast = self._model.predict(current_data, horizon or self.prediction_horizon)
        
        # 予測結果からシフトポイントを抽出
        shift_points = self._extract_shift_points(forecast)
        
        # 結果の拡張
        forecast = self._enhance_forecast(forecast, shift_points)
        
        return forecast
    
    def _extract_shift_points(self, forecast):
        """
        予測結果からシフトポイントを抽出
        
        Parameters
        ----------
        forecast : DataFrame
            予測結果
            
        Returns
        -------
        list
            シフトポイントのリスト
        """
        shift_points = []
        
        # 'shift_point'フラグが立っている行を抽出
        if 'shift_point' in forecast.columns:
            for idx, row in forecast[forecast['shift_point'] == True].iterrows():
                shift_point = {
                    'timestamp': row['timestamp'],
                    'direction': row['predicted_direction'],
                    'confidence': row['confidence'],
                    'magnitude': row.get('shift_magnitude', 0)
                }
                
                # 風速があれば追加
                if 'predicted_speed' in row:
                    shift_point['speed'] = row['predicted_speed']
                
                shift_points.append(shift_point)
        
        return shift_points
    
    def _enhance_forecast(self, forecast, shift_points):
        """
        予測結果に追加情報を付与
        
        Parameters
        ----------
        forecast : DataFrame
            予測結果
        shift_points : list
            シフトポイントのリスト
            
        Returns
        -------
        DataFrame
            拡張された予測結果
        """
        # 結果のコピーを作成
        result = forecast.copy()
        
        # シフトポイントの性質を分析
        if shift_points:
            # シフトの方向（正/負）をカウント
            positive_shifts = sum(1 for p in shift_points if p.get('magnitude', 0) > 0)
            negative_shifts = sum(1 for p in shift_points if p.get('magnitude', 0) < 0)
            
            # 主要なシフト方向
            if positive_shifts > negative_shifts:
                dominant_direction = "positive"  # 右シフト優勢
            elif negative_shifts > positive_shifts:
                dominant_direction = "negative"  # 左シフト優勢
            else:
                dominant_direction = "mixed"     # 混合
            
            # シフトの大きさ
            magnitudes = [abs(p.get('magnitude', 0)) for p in shift_points]
            avg_magnitude = sum(magnitudes) / len(magnitudes) if magnitudes else 0
            
            # 予測全体に情報を追加
            result.attrs['shift_points_count'] = len(shift_points)
            result.attrs['dominant_shift_direction'] = dominant_direction
            result.attrs['average_shift_magnitude'] = avg_magnitude
            result.attrs['next_shift_time'] = shift_points[0]['timestamp'] if shift_points else None
        else:
            # シフトポイントがない場合
            result.attrs['shift_points_count'] = 0
            result.attrs['dominant_shift_direction'] = "none"
            result.attrs['average_shift_magnitude'] = 0
            result.attrs['next_shift_time'] = None
        
        return result
    
    def update(self, new_data):
        """
        モデルをオンライン更新
        
        Parameters
        ----------
        new_data : DataFrame
            新しいデータ
            
        Returns
        -------
        bool
            更新が成功したかどうか
        """
        # モデルの更新
        update_success = self._model.update(new_data)
        
        if update_success:
            self.last_update = datetime.now()
        
        return update_success
    
    def evaluate_performance(self, test_data):
        """
        モデルの性能評価
        
        Parameters
        ----------
        test_data : DataFrame
            テストデータ
            
        Returns
        -------
        dict
            性能評価指標
        """
        if not self.is_trained:
            warnings.warn("Model is not trained yet. Call train() first.")
            return {}
        
        # テストデータの準備
        if len(test_data) < self.prediction_horizon + 1:
            warnings.warn(f"Test data too short for proper evaluation. Need at least {self.prediction_horizon + 1} data points.")
            return {}
        
        # 評価結果
        evaluation = {}
        
        # ホライズンごとの精度を評価
        horizons = [5, 10, 15, 30]
        horizons = [h for h in horizons if h <= self.prediction_horizon]
        
        for horizon in horizons:
            # 予測結果の収集
            predictions = []
            actuals = []
            
            # 複数の時点から予測して評価
            test_points = max(3, len(test_data) // 10)  # テストポイント数（最低3、最大はデータ長の1/10）
            step = max(1, (len(test_data) - horizon) // test_points)
            
            for i in range(0, len(test_data) - horizon, step):
                # 現在の時点までのデータ
                current_data = test_data.iloc[:i+1]
                
                # 予測を実行
                try:
                    forecast = self.predict(current_data, horizon)
                    
                    # 予測値と実測値の比較
                    for j in range(min(horizon, len(forecast))):
                        if i + 1 + j < len(test_data):
                            predicted = forecast['predicted_direction'].iloc[j]
                            actual = test_data['wind_direction'].iloc[i + 1 + j]
                            
                            predictions.append(predicted)
                            actuals.append(actual)
                except Exception as e:
                    warnings.warn(f"Prediction failed at index {i}: {str(e)}")
                    continue
            
            # 精度評価
            if predictions and actuals:
                metrics = self._calculate_error_metrics(predictions, actuals)
                evaluation[f'horizon_{horizon}'] = metrics
        
        # シフトポイントの検出精度
        if 'wind_direction' in test_data.columns:
            try:
                # シフトポイントの検出（過去データから）
                from sailing_data_processor.analysis.wind_shift_detector import WindShiftDetector
                detector = WindShiftDetector()
                actual_shifts = detector.detect_shifts(test_data)
                
                # 過去の変化点ベースでシフト検出精度を評価
                shift_accuracy = self._evaluate_shift_detection(actual_shifts, test_data)
                
                evaluation['shift_detection'] = shift_accuracy
            except:
                pass  # WindShiftDetectorが利用できない場合はスキップ
        
        # パフォーマンスメトリクスに保存
        self.performance_metrics['evaluation'] = evaluation
        
        return evaluation
    
    def _calculate_error_metrics(self, predictions, actuals):
        """
        予測誤差メトリクスを計算
        
        Parameters
        ----------
        predictions : list
            予測値のリスト
        actuals : list
            実測値のリスト
            
        Returns
        -------
        dict
            誤差メトリクス
        """
        # 角度の差を計算
        angle_diffs = []
        for pred, act in zip(predictions, actuals):
            # 角度の差を-180〜180度の範囲で計算
            diff = ((pred - act + 180) % 360) - 180
            angle_diffs.append(abs(diff))
        
        # 平均絶対誤差（MAE）
        mae = sum(angle_diffs) / len(angle_diffs)
        
        # 平均二乗誤差（MSE）
        mse = sum(d * d for d in angle_diffs) / len(angle_diffs)
        
        # 二乗平均平方根誤差（RMSE）
        rmse = math.sqrt(mse)
        
        # 90%分位点
        percentile_90 = sorted(angle_diffs)[int(len(angle_diffs) * 0.9)]
        
        return {
            'mae': mae,
            'mse': mse,
            'rmse': rmse,
            'percentile_90': percentile_90,
            'max_error': max(angle_diffs),
            'min_error': min(angle_diffs),
            'count': len(angle_diffs)
        }
    
    def _evaluate_shift_detection(self, actual_shifts, test_data):
        """
        シフト検出精度の評価
        
        Parameters
        ----------
        actual_shifts : list
            実際のシフトポイントのリスト
        test_data : DataFrame
            テストデータ
            
        Returns
        -------
        dict
            シフト検出精度の評価指標
        """
        # TODO: シフト検出の精度評価ロジックを実装
        # 実際のシフトと予測シフトの時間差、方向の一致度などを評価
        
        return {
            'precision': 0.0,
            'recall': 0.0,
            'f1_score': 0.0
        }
    
    def get_model_params(self):
        """
        現在のモデルパラメータを取得
        
        Returns
        -------
        dict
            モデルパラメータ
        """
        return {
            "model_type": self.model_type,
            "prediction_horizon": self.prediction_horizon,
            "confidence_interval": self.confidence_interval,
            "is_trained": self.is_trained,
            "last_update": self.last_update,
            **self.params
        }
    
    def save(self, file_path):
        """
        モデルを保存
        
        Parameters
        ----------
        file_path : str
            保存先ファイルパス
            
        Returns
        -------
        bool
            保存が成功したかどうか
        """
        try:
            # モデル情報の辞書を作成
            model_data = {
                'model_type': self.model_type,
                'prediction_horizon': self.prediction_horizon,
                'confidence_interval': self.confidence_interval,
                'params': self.params,
                'is_trained': self.is_trained,
                'last_update': self.last_update,
                'performance_metrics': self.performance_metrics
            }
            
            # 内部モデルの状態を保存
            if hasattr(self._model, '_get_model_state'):
                model_data['model_state'] = self._model._get_model_state()
            
            # ディレクトリが存在しない場合は作成
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            
            # 保存
            joblib.dump(model_data, file_path)
            return True
        except Exception as e:
            warnings.warn(f"Failed to save model: {str(e)}")
            return False
    
    def load(self, file_path):
        """
        モデルをロード
        
        Parameters
        ----------
        file_path : str
            ロード元ファイルパス
            
        Returns
        -------
        bool
            ロードが成功したかどうか
        """
        try:
            # モデルデータをロード
            model_data = joblib.load(file_path)
            
            # モデル情報の復元
            self.model_type = model_data.get('model_type', self.model_type)
            self.prediction_horizon = model_data.get('prediction_horizon', self.prediction_horizon)
            self.confidence_interval = model_data.get('confidence_interval', self.confidence_interval)
            self.params = model_data.get('params', self.params)
            self.is_trained = model_data.get('is_trained', False)
            self.last_update = model_data.get('last_update')
            self.performance_metrics = model_data.get('performance_metrics', {})
            
            # モデルの再初期化（必要パラメータで）
            common_params = {
                "prediction_horizon": self.prediction_horizon,
                "confidence_interval": self.confidence_interval,
                **self.params
            }
            self._init_model(common_params)
            
            # モデル状態の復元
            if 'model_state' in model_data and hasattr(self._model, '_set_model_state'):
                self._model._set_model_state(model_data['model_state'])
            
            return True
        except Exception as e:
            warnings.warn(f"Failed to load model: {str(e)}")
            return False