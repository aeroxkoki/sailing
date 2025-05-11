#!/usr/bin/env python3

# Wind estimator のエラーを修正する包括的なスクリプト

file_path = "sailing_data_processor/wind_estimator.py"

# ファイルの内容を読み込む
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# calculate_laylinesメソッドで混入したコードを修正
start_pos = content.find('def calculate_laylines(')
if start_pos > 0:
    # メソッドの終端を見つける
    next_method_pos = content.find('\n    def ', start_pos + 1)
    if next_method_pos > 0:
        laylines_method = content[start_pos:next_method_pos]
        
        # 混入したコードを削除
        laylines_method = laylines_method.replace("""        wind_data.append({
                'timestamp': row['timestamp'],
                'direction': row['wind_direction'],
                'speed': row['wind_speed'],
                'confidence': row['confidence']
            })
        
        # 艇データを作成
        boat_data = {}
        if not data.empty:
            latest = data.iloc[-1]
            boat_data = {
                'position': (latest.get('latitude', 0), latest.get('longitude', 0)),
                'speed': latest.get('sog', latest.get('speed', 0)),
                'course': latest.get('heading', latest.get('course', 0))""", "")
        
        # 正しいlaylinesメソッドのコードを追加
        laylines_method = laylines_method.replace("""        if isinstance(wind_speed, str):
            wind_speed = float(wind_speed)""", """        if isinstance(wind_speed, str):
            wind_speed = float(wind_speed)
        
        # 風上角度を使用
        upwind_angle = self.params["default_upwind_angle"]
        
        # マークへのベアリング
        bearing_to_mark = self._calculate_bearing(boat_position, mark_position)
        
        # レイラインの方向を計算
        port_layline_bearing = wind_direction + upwind_angle
        starboard_layline_bearing = wind_direction - upwind_angle
        
        # レイラインの長さを計算（適当な長さを設定）
        layline_length = self._calculate_distance(boat_position, mark_position) * 2
        
        # レイラインの終点を計算
        port_end = self._calculate_endpoint(boat_position, port_layline_bearing, layline_length)
        starboard_end = self._calculate_endpoint(boat_position, starboard_layline_bearing, layline_length)
        
        return {
            'port': port_end,
            'starboard': starboard_end
        }""")
        
        # 更新されたメソッドで置き換え
        content = content[:start_pos] + laylines_method + content[next_method_pos:]

# estimate_windメソッドも修正する必要があるかチェック
estimate_wind_pos = content.find('def estimate_wind(')
if estimate_wind_pos > 0:
    # estimate_windメソッドの中身を確認し、必要に応じて修正
    next_method_pos = content.find('\n    def ', estimate_wind_pos + 1)
    if next_method_pos > 0:
        estimate_wind_method = content[estimate_wind_pos:next_method_pos]
        
        # 正しいestimate_windメソッドを確保
        if 'wind_df = self.estimate_wind_from_single_boat(data)' in estimate_wind_method and 'wind_data.append({' not in estimate_wind_method:
            # メソッドが壊れている場合は修正
            correct_estimate_wind = '''    def estimate_wind(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        GPS データから風向風速を推定する
        
        テストが期待する形式に合わせたラッパーメソッド
        
        Parameters:
        -----------
        data : pd.DataFrame
            GPS データ
            
        Returns:
        --------
        Dict[str, Any]
            艇と風の情報を含む辞書
        """
        if data.empty:
            return {
                'boat': {},
                'wind': {
                    'wind_data': []
                }
            }
        
        # 従来のメソッドを呼び出す
        wind_df = self.estimate_wind_from_single_boat(data)
        
        # テストが期待する形式に変換
        wind_data = []
        if not wind_df.empty:
            for _, row in wind_df.iterrows():
                wind_data.append({
                    'timestamp': row['timestamp'],
                    'direction': row['wind_direction'],
                    'speed': row['wind_speed'],
                    'confidence': row['confidence']
                })
        
        # 艇データを作成
        boat_data = {}
        if not data.empty:
            latest = data.iloc[-1]
            boat_data = {
                'position': (latest.get('latitude', 0), latest.get('longitude', 0)),
                'speed': latest.get('sog', latest.get('speed', 0)),
                'course': latest.get('heading', latest.get('course', 0))
            }
        
        result = {
            'boat': boat_data,
            'wind': {
                'wind_data': wind_data
            }
        }
        
        return result
'''
            content = content[:estimate_wind_pos] + correct_estimate_wind + content[next_method_pos:]

# _calculate_bearingメソッドが正しく閉じられているか確認
bearing_pos = content.find('def _calculate_bearing(')
if bearing_pos > 0:
    next_method_pos = content.find('\n    def ', bearing_pos + 1)
    if next_method_pos > 0:
        bearing_method = content[bearing_pos:next_method_pos]
        # returnで終わっていることを確認
        if 'return bearing' not in bearing_method:
            # メソッドの最後にreturn文を追加
            bearing_method = bearing_method.rstrip() + '\n        return bearing\n'
            content = content[:bearing_pos] + bearing_method + content[next_method_pos:]

# _calculate_distanceメソッドが存在しない場合は追加
if '_calculate_distance(' not in content:
    distance_method = '''
    def _calculate_distance(self, point1: Tuple[float, float], 
                           point2: Tuple[float, float]) -> float:
        """
        2点間の距離を計算する（海里）
        
        Parameters:
        -----------
        point1, point2 : Tuple[float, float]
            位置（緯度、経度）
            
        Returns:
        --------
        float
            距離（海里）
        """
        lat1, lon1 = point1
        lat2, lon2 = point2
        
        # ラジアンに変換
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # 地球の半径（海里）
        r = 3440.065
        
        return c * r
'''
    # _calculate_endpointの前に追加
    endpoint_pos = content.find('def _calculate_endpoint(')
    if endpoint_pos > 0:
        content = content[:endpoint_pos] + distance_method + '\n    ' + content[endpoint_pos:]
    else:
        # クラスの最後に追加
        content = content.rstrip() + distance_method

# _calculate_endpointメソッドが存在しない場合は追加
if '_calculate_endpoint(' not in content:
    endpoint_method = '''
    def _calculate_endpoint(self, start_point: Tuple[float, float], 
                           bearing: float, distance: float) -> Tuple[float, float]:
        """
        始点からある方向と距離にある終点を計算する
        
        Parameters:
        -----------
        start_point : Tuple[float, float]
            始点（緯度、経度）
        bearing : float
            方位（度）
        distance : float
            距離（海里）
            
        Returns:
        --------
        Tuple[float, float]
            終点（緯度、経度）
        """
        lat1, lon1 = start_point
        
        # ラジアンに変換
        lat1 = math.radians(lat1)
        lon1 = math.radians(lon1)
        bearing = math.radians(bearing)
        
        # 地球の半径（海里）
        r = 3440.065
        
        # 角距離
        angular_distance = distance / r
        
        # 終点の計算
        lat2 = math.asin(math.sin(lat1) * math.cos(angular_distance) +
                        math.cos(lat1) * math.sin(angular_distance) * math.cos(bearing))
        
        lon2 = lon1 + math.atan2(math.sin(bearing) * math.sin(angular_distance) * math.cos(lat1),
                                math.cos(angular_distance) - math.sin(lat1) * math.sin(lat2))
        
        # 度に変換
        lat2 = math.degrees(lat2)
        lon2 = math.degrees(lon2)
        
        return (lat2, lon2)
'''
    # _create_wind_resultの前に追加
    wind_result_pos = content.find('def _create_wind_result(')
    if wind_result_pos > 0:
        content = content[:wind_result_pos] + endpoint_method + '\n    ' + content[wind_result_pos:]
    else:
        # クラスの最後に追加
        content = content.rstrip() + endpoint_method

# ファイルに書き込む
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Wind estimator を完全に修正しました！")
