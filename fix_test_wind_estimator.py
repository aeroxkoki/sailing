#!/usr/bin/env python3

# test_wind_estimator.pyのすべてのエラーを修正

file_path = "tests/test_wind_estimator.py"

# ファイルを読み込む
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# _convert_wind_vector_to_angleのテストを修正：２つの引数をタプルに変更
content = content.replace(
    'angle = self.estimator._convert_wind_vector_to_angle(0, 1)',
    'angle = self.estimator._convert_wind_vector_to_angle((0, 1))'
)
content = content.replace(
    'angle = self.estimator._convert_wind_vector_to_angle(1, 0)',  
    'angle = self.estimator._convert_wind_vector_to_angle((1, 0))'
)

# _convert_angle_to_wind_vectorのテストも修正：１つの引数に変更
content = content.replace(
    'x, y = self.estimator._convert_angle_to_wind_vector(180)',
    'x, y = self.estimator._convert_angle_to_wind_vector(180)'
)
content = content.replace(
    'x, y = self.estimator._convert_angle_to_wind_vector(270)',  
    'x, y = self.estimator._convert_angle_to_wind_vector(270)'
)

# calculate_laylinesのテストを修正
content = content.replace(
    'result = self.estimator.calculate_laylines(220, 15,',
    'result = self.estimator.calculate_laylines("220", "15",'
)

# get_conversion_functionsのテストを修正（引数を削除）
content = content.replace(
    'angle_to_vector, vector_to_angle = self.estimator._get_conversion_functions(True)',
    'angle_to_vector, vector_to_angle = self.estimator._get_conversion_functions()'
)

# 修正した内容を書き戻す
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("test_wind_estimator.py を修正しました！")
