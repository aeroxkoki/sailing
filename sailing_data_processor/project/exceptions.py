# -*- coding: utf-8 -*-
"""
sailing_data_processor.project.exceptions

プロジェクト関連の例外を定義するモジュール
"""

class ProjectError(Exception):
    """
    プロジェクト関連エラーの基底クラス
    
    すべてのプロジェクト関連例外の基底となる例外クラス。
    """
    pass


class ProjectNotFoundError(ProjectError):
    """
    プロジェクトが見つからない場合のエラー
    
    プロジェクトの読み込みや参照時に、指定されたプロジェクトが
    存在しない場合に発生します。
    """
    pass


class ProjectStorageError(ProjectError):
    """
    プロジェクトの保存/読み込み時のエラー
    
    プロジェクトデータの保存や読み込み操作中に問題が
    発生した場合に使用される例外です。
    """
    pass


class InvalidProjectData(ProjectError):
    """
    プロジェクトデータが不正な場合のエラー
    
    プロジェクトデータの形式が不正であったり、必須フィールドが
    欠けている場合などに発生します。
    """
    pass

