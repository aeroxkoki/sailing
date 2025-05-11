#!/usr/bin/env python3

import fileinput
import re

# ファイルを修正
file_path = "sailing_data_processor/wind_estimator.py"

# 修正1: タック検出の条件を修正
def fix_tack_detection():
    with fileinput.FileInput(file_path, inplace=True, backup='.bak') as file:
        for line in file:
            if 'if angle_change < -self.params["min_tack_angle_change"]:' in line:
                print('            if abs(angle_change) > self.params["min_tack_angle_change"]:')
            else:
                print(line, end='')

# 修正2: detect_maneuversメソッドの実装
detect_maneuvers_method = '''
    def detect_maneuvers(self, data: pd.DataFrame, **kwargs) -> List[Dict]:
        """
        マニューバー（タック/ジャイブ）を検出する
        
        Parameters:
        -----------
        data : pd.DataFrame
            GPSデータ
        **kwargs : dict
            追加パラメータ
            
        Returns:
        --------
        List[Dict]
            検出されたマニューバーのリスト
        """
        tacks = self.detect_tacks(data)
        gybes = self.detect_gybes(data)
        
        maneuvers = []
        
        # タックのデータを追加
        if not tacks.empty:
            for _, tack in tacks.iterrows():
                maneuvers.append({
                    'timestamp': tack['timestamp'],
                    'type': 'tack',
                    'angle_change': tack['angle_change'],
                    'heading_before': tack['heading_before'],
                    'heading_after': tack['heading_after'],
                    'index': tack['index']
                })
        
        # ジャイブのデータを追加
        if not gybes.empty:
            for _, gybe in gybes.iterrows():
                maneuvers.append({
                    'timestamp': gybe['timestamp'],
                    'type': 'gybe',
                    'angle_change': gybe['angle_change'],
                    'heading_before': gybe['heading_before'],
                    'heading_after': gybe['heading_after'],
                    'index': gybe['index']
                })
        
        # タイムスタンプで���������
        maneuvers.sort(key=lambda x: x.get('timestamp', x.get('index', 0)))
        
        return maneuvers
'''

# 修正3: _normalize_angleメソッドの実装
normalize_angle_method = '''
    def _normalize_angle(self, angle: float) -> float:
        """
        角度を0-360度の範囲に正規化する
        
        Parameters:
        -----------
        angle : float
            角度（度）
            
        Returns:
        --------
        float
            正規化された角度（0-360度）
        """
        # まず360で割った余りを計算
        normalized = angle % 360
        
        # 負の値の場合は360を足す
        if normalized < 0:
            normalized += 360
            
        return normalized
'''

# 修正4: calculate_laylinesメソッドの引数を修正
def fix_calculate_laylines():
    # パラメータを統一し、型変換を追加
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # calculate_laylines メソッドを修正
    pattern = r'def calculate_laylines\(self, wind_direction: float, wind_speed: float,.*?\):'
    replacement = '''def calculate_laylines(self, wind_direction: Union[float, str], wind_speed: Union[float, str], 
                         mark_position: Tuple[float, float], 
                         boat_position: Tuple[float, float], 
                         **kwargs) -> Dict[str, Tuple[float, float]]:
        """
        レイラインを計算する
        
        Parameters:
        -----------
        wind_direction : Union[float, str]
            風向（度）
        wind_speed : Union[float, str]
            風速（ノット）
        mark_position : Tuple[float, float]
            マークの位置（緯度、経度）
        boat_position : Tuple[float, float]
            艇の位置（緯度、経度）
        **kwargs : dict
            追加パラメータ
            
        Returns:
        --------
        Dict[str, Tuple[float, float]]
            レイラインのポートタックとスターボードタックの終点
        """
        # 型変換
        if isinstance(wind_direction, str):
            wind_direction = float(wind_direction)
        if isinstance(wind_speed, str):
            wind_speed = float(wind_speed)'''
    
    content = re.sub(pattern, replacement, content, count=1, flags=re.DOTALL)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

# 修正5: プライベートメソッドの引数補正
private_methods_fix = '''
    def _convert_angle_to_wind_vector(self, angle: float) -> Tuple[float, float]:
        """
        風向角度を風向ベクトルに変換する
        
        Parameters:
        -----------
        angle : float
            風向（度）
            
        Returns:
        --------
        Tuple[float, float]
            風向ベクトル（x, y成分）
        """
        # 北を0度として時計回りの角度から、数学的な角度（東が0度、反時計回り）に変換
        math_angle = 90 - angle
        
        x = math.cos(math.radians(math_angle))
        y = math.sin(math.radians(math_angle))
        
        return (x, y)
    
    def _convert_wind_vector_to_angle(self, vector: Tuple[float, float]) -> float:
        """
        風向ベクトルを風向角度に変換する
        
        Parameters:
        -----------
        vector : Tuple[float, float]
            風向ベクトル（x, y成分）
            
        Returns:
        --------
        float
            風向（度）
        """
        x, y = vector
        
        # 数学的な角度（東が0度、反時計回り）を計算
        math_angle = math.degrees(math.atan2(y, x))
        
        # 北を0度として時計回りの角度に変換
        wind_angle = 90 - math_angle
        
        # 0-360度の範囲に正規化
        return self._normalize_angle(wind_angle)
    
    def _get_conversion_functions(self) -> Tuple[callable, callable]:
        """
        風向変換関数のペアを取得
        
        Returns:
        --------
        Tuple[callable, callable]
            (angle_to_vector, vector_to_angle) 関数のペア
        """
        return self._convert_angle_to_wind_vector, self._convert_wind_vector_to_angle
'''

# 修正6: _categorize_maneuverと_determine_point_stateメソッドの実装
state_methods = '''
    def _categorize_maneuver(self, angle_change: float) -> str:
        """
        マニューバーの種類を分類する
        
        Parameters:
        -----------
        angle_change : float
            角度変化（度）
            
        Returns:
        --------
        str
            マニューバーの種類（'tack' または 'gybe'）
        """
        # 簡単な実装：角度変化の方向で判定
        if angle_change > 0:
            return 'gybe'
        else:
            return 'tack'
    
    def _determine_point_state(self, heading: float, wind_direction: float) -> str:
        """
        ポイントの状態を判定する
        
        Parameters:
        -----------
        heading : float
            艇の向き（度）
        wind_direction : float
            風向（度）
            
        Returns:
        --------
        str
            状態（'upwind', 'downwind', 'reaching'）
        """
        # 風に対する相対角度を計算
        relative_angle = abs(self._normalize_angle(heading - wind_direction))
        if relative_angle > 180:
            relative_angle = 360 - relative_angle
        
        # 状態を判定
        if relative_angle < self.params["upwind_threshold"]:
            return 'upwind'
        elif relative_angle > self.params["downwind_threshold"]:
            return 'downwind'
        else:
            return 'reaching'
'''

# 修正7: estimate_wind_from_course_speedを追加
course_speed_method = '''
    def estimate_wind_from_course_speed(self, data: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """
        コースと速度の変化から風向風速を推定する
        
        Parameters:
        -----------
        data : pd.DataFrame
            GPSデータ
            
        Returns:
        --------
        Optional[Dict[str, Any]]
            推定結果
        """
        if data.empty or len(data) < 10:
            return None
        
        # 簡単な実装：平均的な方向から推定
        heading_col = 'heading' if 'heading' in data.columns else 'course'
        if heading_col not in data.columns:
            return None
        
        # 平均的な向きから風向を推定（簡略化）
        mean_heading = data[heading_col].mean()
        wind_direction = self._normalize_angle(mean_heading + 180)
        
        # 速度から風速を推定（簡略化）
        speed_col = 'sog' if 'sog' in data.columns else 'speed'
        if speed_col in data.columns:
            mean_speed = data[speed_col].mean()
            wind_speed = mean_speed * 0.7  # 簡単な推定
        else:
            wind_speed = 10.0  # デフォルト値
        
        return self._create_wind_result(
            direction=wind_direction,
            speed=wind_speed,
            confidence=0.5,
            method='course_speed',
            timestamp=data.iloc[-1]['timestamp'] if 'timestamp' in data.columns else None
        )
'''

# 修正8: _estimate_wind_from_maneuversを追加
maneuvers_method = '''
    def _estimate_wind_from_maneuvers(self, maneuvers: List[Dict], data: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """
        マニューバーから風向風速を推定する
        
        Parameters:
        -----------
        maneuvers : List[Dict]
            検出されたマニューバー
        data : pd.DataFrame
            GPSデータ
            
        Returns:
        --------
        Optional[Dict[str, Any]]
            推定結果
        """
        if not maneuvers or len(maneuvers) < 2:
            return None
        
        # タックを抽出
        tacks = [m for m in maneuvers if m['type'] == 'tack']
        
        if not tacks:
            return None
        
        # タックの前後の方向から風向を推定
        wind_directions = []
        for tack in tacks:
            before = tack['heading_before']
            after = tack['heading_after']
            
            # タックの前後の方向の平均が風向に対して約90度
            avg_heading = (before + after) / 2
            wind_dir = self._normalize_angle(avg_heading + 90)
            wind_directions.append(wind_dir)
        
        # 平均風向
        mean_wind_direction = np.mean(wind_directions)
        
        # 風速は速度から推定（簡略化）
        speed_col = 'sog' if 'sog' in data.columns else 'speed'
        if speed_col in data.columns:
            wind_speed = data[speed_col].mean() * 0.8
        else:
            wind_speed = 12.0  # デフォルト値
        
        return self._create_wind_result(
            direction=mean_wind_direction,
            speed=wind_speed,
            confidence=0.7,
            method='maneuvers',
            timestamp=data.iloc[-1]['timestamp'] if 'timestamp' in data.columns else None
        )
'''

# 修正9: _preprocess_dataを追加
preprocess_method = '''
    def _preprocess_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        データの前処理を行う
        
        Parameters:
        -----------
        data : pd.DataFrame
            生のGPSデータ
            
        Returns:
        --------
        pd.DataFrame
            前処理されたデータ
        """
        df = data.copy()
        
        # タイムスタンプの確認
        if 'timestamp' not in df.columns:
            df['timestamp'] = pd.to_datetime(df.index)
        
        # 速度の確認
        if 'sog' not in df.columns and 'speed' not in df.columns:
            # 位置から速度を計算する必要がある場合
            pass
        
        # ヘディングの確認
        if 'heading' not in df.columns and 'course' not in df.columns:
            # コースから計算する必要がある場合
            pass
        
        return df
'''

# ファイルを実際に修正
def main():
    print("Wind estimator の修正を開始します...")
    
    # まず元のファイルを読み込む
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修正1: タック検出の条件
    fix_tack_detection()
    
    # 読み直し
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # detect_maneuversメソッドを追加
    if 'def detect_maneuvers(' not in content:
        # calculate_laylinesの前に追加
        calc_pos = content.find('def calculate_laylines(')
        if calc_pos > 0:
            content = content[:calc_pos] + detect_maneuvers_method + '\n' + content[calc_pos:]
    
    # _normalize_angleメソッドを追加  
    if 'def _normalize_angle(' not in content:
        # _calculate_angle_changeの後に追加
        change_pos = content.find('def _calculate_angle_change(')
        if change_pos > 0:
            next_method_pos = content.find('\n    def ', change_pos + 1)
            if next_method_pos > 0:
                content = content[:next_method_pos] + normalize_angle_method + '\n' + content[next_method_pos:]
    
    # _categorize_maneuverと_determine_point_stateを追加
    if '_categorize_maneuver' not in content:
        # クラスの最後に追加
        content = content.rstrip() + '\n' + state_methods
    
    # プライベートメソッドを修正
    # _convert_angle_to_wind_vectorを正しく定義
    convert_pos = content.find('def _convert_angle_to_wind_vector(')
    if convert_pos > 0:
        # 既存のメソッドを置き換え
        next_method_pos = content.find('\n    def ', convert_pos + 1)
        if next_method_pos > 0:
            content = content[:convert_pos] + private_methods_fix.strip()[4:] + '\n' + content[next_method_pos:]
    else:
        # メソッドがない場合は追加
        content = content.rstrip() + '\n' + private_methods_fix
    
    # estimate_wind_from_course_speedを追加
    if 'def estimate_wind_from_course_speed(' not in content:
        # estimate_wind_from_single_boatの後に追加
        single_pos = content.find('def estimate_wind_from_single_boat(')
        if single_pos > 0:
            next_method_pos = content.find('\n    def ', single_pos + 1)
            while next_method_pos > 0:
                if content[next_method_pos:next_method_pos+50].find('def _') == -1:  # プライベートメソッドでない
                    break
                next_method_pos = content.find('\n    def ', next_method_pos + 1)
            
            if next_method_pos > 0:
                content = content[:next_method_pos] + course_speed_method + '\n' + content[next_method_pos:]
            else:
                content = content.rstrip() + '\n' + course_speed_method
    
    # _estimate_wind_from_maneuversを追加
    if '_estimate_wind_from_maneuvers' not in content:
        content = content.rstrip() + '\n' + maneuvers_method
    
    # _preprocess_dataを追加
    if '_preprocess_data' not in content:
        content = content.rstrip() + '\n' + preprocess_method
    
    # ファイルに書き込む
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # calculate_laylinesの修正
    fix_calculate_laylines()
    
    print("Wind estimator の修正が完了しました！")

if __name__ == '__main__':
    main()
