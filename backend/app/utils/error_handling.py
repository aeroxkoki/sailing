"""
エラーハンドリングユーティリティ

アプリケーション全体で一貫したエラーハンドリングを提供するためのユーティリティモジュール
"""

import logging
import traceback
import functools
from typing import Any, Callable, Dict, Optional, Type, TypeVar, Union, cast
from fastapi import HTTPException, status
from pydantic import BaseModel, Field

# ロガーの設定
logger = logging.getLogger(__name__)

# 型変数の定義
T = TypeVar('T')


class ErrorResponse(BaseModel):
    """標準エラーレスポンスモデル"""
    status: str = Field(default="error")
    code: str = Field(default="unknown_error")
    message: str
    details: Optional[Dict[str, Any]] = None


class ServiceError(Exception):
    """サービス層でのエラーを表す基本例外クラス"""
    def __init__(
        self, 
        message: str, 
        code: str = "service_error",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class DatabaseError(ServiceError):
    """データベース操作に関連するエラー"""
    def __init__(
        self, 
        message: str, 
        code: str = "database_error",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, code, status_code, details)


class ExternalServiceError(ServiceError):
    """外部サービス（Supabaseなど）に関連するエラー"""
    def __init__(
        self, 
        message: str, 
        service_name: str = "external_service",
        code: str = "external_service_error",
        status_code: int = status.HTTP_503_SERVICE_UNAVAILABLE,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        details["service_name"] = service_name
        super().__init__(message, code, status_code, details)


class SupabaseError(ExternalServiceError):
    """Supabase特有のエラー"""
    def __init__(
        self, 
        message: str, 
        code: str = "supabase_error",
        status_code: int = status.HTTP_503_SERVICE_UNAVAILABLE,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, "supabase", code, status_code, details)


class ValidationError(ServiceError):
    """データバリデーションエラー"""
    def __init__(
        self, 
        message: str, 
        code: str = "validation_error",
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, code, status_code, details)


class NotFoundError(ServiceError):
    """リソースが見つからないエラー"""
    def __init__(
        self, 
        message: str, 
        resource_type: Optional[str] = None,
        code: str = "not_found",
        status_code: int = status.HTTP_404_NOT_FOUND,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if resource_type:
            details["resource_type"] = resource_type
        super().__init__(message, code, status_code, details)


class AuthenticationError(ServiceError):
    """認証関連のエラー"""
    def __init__(
        self, 
        message: str, 
        code: str = "authentication_error",
        status_code: int = status.HTTP_401_UNAUTHORIZED,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, code, status_code, details)


class AuthorizationError(ServiceError):
    """権限関連のエラー"""
    def __init__(
        self, 
        message: str, 
        code: str = "authorization_error",
        status_code: int = status.HTTP_403_FORBIDDEN,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, code, status_code, details)


def handle_service_error(error: Exception) -> HTTPException:
    """
    サービスエラーをHTTP例外に変換するヘルパー関数
    
    Args:
        error: 発生したエラー
        
    Returns:
        HTTPException: FastAPIで処理可能なHTTP例外
    """
    if isinstance(error, ServiceError):
        # すでにServiceErrorの場合はそのままHTTPExceptionに変換
        return HTTPException(
            status_code=error.status_code,
            detail=ErrorResponse(
                code=error.code,
                message=error.message,
                details=error.details
            ).dict()
        )
    else:
        # その他の例外は汎用的なサーバーエラーとして処理
        logger.error(f"Unhandled exception: {str(error)}")
        logger.error(traceback.format_exc())
        
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                code="internal_server_error",
                message="内部サーバーエラーが発生しました",
                details={"error_type": error.__class__.__name__}
            ).dict()
        )


def safe_external_call(
    func: Optional[Callable[..., T]] = None,
    *,
    error_message: str = "外部サービスとの通信中にエラーが発生しました",
    service_name: str = "external_service",
    fallback_value: Optional[T] = None,
    raise_error: bool = True
) -> Union[Callable[..., T], Callable[[Callable[..., T]], Callable[..., T]]]:
    """
    外部サービス呼び出しを安全に行うためのデコレータ
    
    デコレータとして2つの使い方があります：
    1. パラメータなし: @safe_external_call
    2. パラメータあり: @safe_external_call(error_message="エラー", service_name="サービス名")
    
    Args:
        func: デコレートする関数（オプション）
        error_message: エラー発生時のメッセージ
        service_name: 外部サービス名
        fallback_value: エラー時の代替戻り値
        raise_error: エラーを発生させるかどうか
        
    Returns:
        デコレートされた関数またはデコレータ
    """
    def decorator(func_to_decorate: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func_to_decorate)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return func_to_decorate(*args, **kwargs)
            except Exception as e:
                logger.error(f"{service_name} error in {func_to_decorate.__name__}: {str(e)}")
                logger.error(traceback.format_exc())
                
                if raise_error:
                    raise ExternalServiceError(
                        message=error_message,
                        service_name=service_name,
                        details={"original_error": str(e)}
                    )
                else:
                    if fallback_value is not None:
                        return fallback_value
                    # 型チェックを満たすためにcastを使用
                    return cast(T, None)
        
        return wrapper
    
    # funcが指定されている場合は直接デコレータを適用
    if func is not None:
        return decorator(func)
    
    # funcが指定されていない場合はデコレータを返す
    return decorator


def safe_db_operation(
    func: Optional[Callable[..., T]] = None,
    *,
    error_message: str = "データベース操作中にエラーが発生しました",
    fallback_value: Optional[T] = None,
    raise_error: bool = True
) -> Union[Callable[..., T], Callable[[Callable[..., T]], Callable[..., T]]]:
    """
    データベース操作を安全に行うためのデコレータ
    
    デコレータとして2つの使い方があります：
    1. パラメータなし: @safe_db_operation
    2. パラメータあり: @safe_db_operation(error_message="エラー")
    
    Args:
        func: デコレートする関数（オプション）
        error_message: エラー発生時のメッセージ
        fallback_value: エラー時の代替戻り値
        raise_error: エラーを発生させるかどうか
        
    Returns:
        デコレートされた関数またはデコレータ
    """
    def decorator(func_to_decorate: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func_to_decorate)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return func_to_decorate(*args, **kwargs)
            except Exception as e:
                logger.error(f"Database error in {func_to_decorate.__name__}: {str(e)}")
                logger.error(traceback.format_exc())
                
                if raise_error:
                    raise DatabaseError(
                        message=error_message,
                        details={"original_error": str(e)}
                    )
                else:
                    if fallback_value is not None:
                        return fallback_value
                    # 型チェックを満たすためにcastを使用
                    return cast(T, None)
        
        return wrapper
    
    # funcが指定されている場合は直接デコレータを適用
    if func is not None:
        return decorator(func)
    
    # funcが指定されていない場合はデコレータを返す
    return decorator
