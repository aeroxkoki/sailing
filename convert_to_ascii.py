#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日本語コメントをASCII化するスクリプト

テストファイルに含まれる日本語コメントを英語に変換し、
ASCII文字のみを使用するファイルを作成します。
"""

import os
import sys
from pathlib import Path

def convert_japanese_comments_to_english(file_path, output_path=None):
    """
    日本語コメントを英語に変換する
    
    Parameters
    ----------
    file_path : str
        変換するファイルのパス
    output_path : str, optional
        出力先ファイルパス（省略時は元ファイル名に .ascii.py を追加）
    
    Returns
    -------
    bool
        変換が成功したかどうか
    """
    if output_path is None:
        path = Path(file_path)
        output_path = str(path.parent / (path.stem + '.ascii' + path.suffix))
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 日本語のコメントを英語に変換
        # コメント行の置き換えマップ
        ja_to_en_map = {
            'インポート連携クラスのユニットテスト': 'Unit test for Import Integration class',
            'モックプロジェクトストレージ': 'Mock project storage',
            'インポート連携インスタンス': 'Import integration instance',
            'サンプルGPSデータコンテナ': 'Sample GPS data container',
            'プロジェクトへのセッション割り当てテスト': 'Test for assigning session to project',
            'カスタム表示名でのプロジェクトへのセッション割り当てテスト': 'Test for assigning session to project with custom display name',
            'セッション参照が正しく作成されたか確認': 'Verify the session reference is correctly created',
            '存在しないセッションの割り当てテスト': 'Test for assigning non-existent session',
            '存在しないプロジェクトへの割り当てテスト': 'Test for assigning to non-existent project',
            'プロジェクトからのセッション削除テスト': 'Test for removing session from project',
            'セッション参照更新テスト': 'Test for updating session reference',
            '存在しないセッション参照の更新テスト（自動作成）': 'Test for updating non-existent session reference (auto-creation)',
            'インポート結果処理テスト（特定プロジェクト）': 'Test for processing import result (specific project)',
            'タグによる自動プロジェクト割り当てテスト': 'Test for automatic project assignment by tag',
            '日付による自動プロジェクト割り当てテスト': 'Test for automatic project assignment by date',
            'プロジェクト設定の適用テスト': 'Test for applying project settings',
            'タグ継承のテスト': 'Test for tag inheritance',
            'バッチインポート処理テスト': 'Test for batch import processing',
            'インポート用プロジェクト作成テスト': 'Test for creating project for import',
            'テストモジュール: sailing_data_processor.project.project_storage': 'Test module: sailing_data_processor.project.project_storage',
            'テスト対象: ProjectStorageクラス': 'Test target: ProjectStorage class',
            'ProjectStorageクラスのテスト': 'Test for ProjectStorage class',
            'テスト用の一時ディレクトリを作成': 'Create temporary directory for testing',
            'テスト用のProjectStorageインスタンスを作成': 'Create ProjectStorage instance for testing',
            'サンプルプロジェクトの作成': 'Create sample project',
            'サンプルセッションの作成': 'Create sample session',
            'サンプル分析結果の作成': 'Create sample analysis result',
            'ディレクトリ作成のテスト': 'Test for directory creation',
            'プロジェクトの保存と読み込みのテスト': 'Test for saving and loading project',
            'セッションの保存と読み込みのテスト': 'Test for saving and loading session',
            '分析結果の保存と読み込みのテスト': 'Test for saving and loading analysis result',
            'プロジェクト作成のテスト': 'Test for creating project',
            'セッション作成のテスト': 'Test for creating session',
            '分析結果作成のテスト': 'Test for creating analysis result',
            'セッションをプロジェクトに追加するテスト': 'Test for adding session to project',
            '分析結果をセッションに追加するテスト': 'Test for adding analysis result to session',
            'プロジェクトに関連するセッションの取得テスト': 'Test for getting sessions related to project',
            'セッションに関連する分析結果の取得テスト': 'Test for getting analysis results related to session',
            'プロジェクト削除のテスト': 'Test for deleting project',
            'セッション削除のテスト': 'Test for deleting session',
            'プロジェクト検索のテスト': 'Test for searching projects',
            'すべてのタグ取得のテスト': 'Test for getting all tags',
            'ルートプロジェクト取得のテスト': 'Test for getting root projects',
            'サブプロジェクト取得のテスト': 'Test for getting sub-projects',
            'テストプロジェクト': 'Test Project',
            'テスト用のプロジェクト': 'Project for testing',
            'テストセッション': 'Test Session',
            'テスト用のセッション': 'Session for testing',
            'テスト結果': 'Test Result',
            'テスト用の分析結果': 'Analysis result for testing',
            '新規プロジェクト': 'New Project',
            '新しく作成したプロジェクト': 'Newly created project',
            '新規セッション': 'New Session',
            '新しく作成したセッション': 'Newly created session',
            '新規分析結果': 'New Analysis Result',
            '速度分析の結果': 'Result of speed analysis',
            'セーリング大会': 'Sailing Competition',
            '東京湾でのレース': 'Race in Tokyo Bay',
            '練習セッション': 'Practice Session',
            '横浜での練習': 'Practice in Yokohama',
            '分析プロジェクト': 'Analysis Project',
            '風向分析': 'Wind direction analysis',
            'プロジェクト1': 'Project 1',
            'プロジェクト2': 'Project 2',
            'セッション1': 'Session 1',
            '親プロジェクト': 'Parent Project',
            '子プロジェクト': 'Child Project',
            '子プロジェクト1': 'Child Project 1',
            '子プロジェクト2': 'Child Project 2',
            '別のルートプロジェクト': 'Another Root Project',
            '東京湾': 'Tokyo Bay',
            'テスト': 'test',
            'レース': 'race',
            '練習': 'practice',
            'カスタム表示名': 'Custom Display Name',
            '元の表示名': 'Original Display Name',
            '新しい表示名': 'New Display Name',
            '新しい説明': 'New Description',
            'インポートセッション': 'Import Session',
            'レースセッション': 'Race Session',
            '日付セッション': 'Date Session',
            'バッチセッション1': 'Batch Session 1',
            'バッチセッション2': 'Batch Session 2',
            '新規プロジェクトセッション': 'New Project Session',
            'インポート用に作成されたプロジェクト': 'Project created for import',
            'インポート': 'import',
            '4人乗り': '4-person crew',
        }
        
        # 内容を変換
        for ja, en in ja_to_en_map.items():
            content = content.replace(ja, en)
        
        # 出力ファイルに書き込み
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Converted file saved to: {output_path}")
        return True
    
    except Exception as e:
        print(f"Error converting file: {e}")
        return False

def main():
    # コマンドライン引数のチェック
    if len(sys.argv) < 2:
        print("Usage: python convert_to_ascii.py <file_path> [output_path]")
        return
    
    file_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    convert_japanese_comments_to_english(file_path, output_path)

if __name__ == "__main__":
    # デフォルト動作: テストプロジェクトのテストファイルを変換
    if len(sys.argv) == 1:
        # プロジェクトのテストディレクトリを指定
        project_dir = os.path.dirname(os.path.abspath(__file__))
        test_files = [
            os.path.join(project_dir, "tests", "test_project", "test_import_integration.py"),
            os.path.join(project_dir, "tests", "test_project", "test_project_storage.py")
        ]
        
        for file_path in test_files:
            convert_japanese_comments_to_english(file_path)
    else:
        main()
