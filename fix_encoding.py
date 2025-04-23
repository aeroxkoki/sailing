#\!/usr/bin/env python3
import os
import glob

def fix_file_encoding(file_path):
    try:
        # 元のファイルを読み込む
        with open(file_path, 'rb') as f:
            content = f.read()
        
        # 見えないヌルバイトを削除
        content_fixed = content.replace(b'\x00', b'')
        
        # 一時ファイルに保存
        temp_path = file_path + '.temp'
        with open(temp_path, 'wb') as f:
            f.write(content_fixed)
        
        # 元のファイルを置き換え
        os.replace(temp_path, file_path)
        
        print(f"修正完了: {file_path}")
        return True
    except Exception as e:
        print(f"エラー ({file_path}): {e}")
        return False

def main():
    # 対象ディレクトリ
    base_dir = os.path.dirname(os.path.abspath(__file__))
    endpoints_dir = os.path.join(base_dir, 'backend', 'app', 'api', 'endpoints')
    
    # 全Pythonファイルを処理
    py_files = glob.glob(os.path.join(endpoints_dir, '*.py'))
    
    success_count = 0
    for file_path in py_files:
        if fix_file_encoding(file_path):
            success_count += 1
    
    print(f"処理完了: {success_count}/{len(py_files)} ファイルを修正しました")

if __name__ == "__main__":
    main()
