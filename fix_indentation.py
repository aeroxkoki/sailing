#!/usr/bin/env python3

# インデントエラーを修正
def fix_indentation():
    with open('sailing_data_processor/wind_estimator.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 235行目付近のインデントを修正
    fixed_lines = []
    for i, line in enumerate(lines):
        if i == 234 and line.strip().startswith('wind_data.append'):  # 0-indexed なので 234
            # インデントを調整
            fixed_lines.append('        wind_data.append({\n')
        elif i > 234 and i < 245 and line.startswith('                '):
            # 後続行のインデントも調整
            fixed_lines.append(line.replace('                ', '            '))
        else:
            fixed_lines.append(line)
    
    # ファイルに書き込む
    with open('sailing_data_processor/wind_estimator.py', 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)

if __name__ == '__main__':
    fix_indentation()
    print("インデントを修正しました！")
