#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
セーリング戦略分析システム - FastAPI バックエンド
"""

import os
import re
import json
from datetime import datetime
from fastapi import FastAPI, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from dotenv import load_dotenv

# 環境変数のロード
load_dotenv()

# エンコーディングミドルウェア
class EncodingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["Content-Type"] = "application/json; charset=utf-8"
        return response

# 日本語処理ミドルウェア
class JapaneseProcessingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        if response.headers.get("content-type") == "application/json":
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
            
            try:
                # レスポンスのデコードと再エンコード
                body_str = body.decode("utf-8")
                response = Response(
                    content=body_str,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type="application/json",
                )
                response.headers["Content-Type"] = "application/json; charset=utf-8"
            except Exception as e:
                print(f"エンコーディングエラー: {e}")
                pass
                
        return response

# アプリケーションの作成
app = FastAPI(
    title="セーリング戦略分析システム API",
    description="セーリング競技のGPSデータを分析し、戦略を評価するためのAPI",
    version="0.1.0"
)

# ミドルウェアの追加
app.add_middleware(EncodingMiddleware)
app.add_middleware(JapaneseProcessingMiddleware)

# APIルーターのインポートと設定のインポート
from app.api.router import api_router
from app.core.config import settings

# デバッグログ出力
print(f"CORS origins: {settings.CORS_ORIGINS}")

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルートパス
@app.get("/")
async def root():
    return {"message": "セーリング戦略分析システムAPIへようこそ"}

# ヘルスチェックエンドポイント
@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "version": settings.API_VERSION,
        "environment": settings.APP_ENV
    }

# APIルーターの登録
app.include_router(api_router, prefix=settings.API_V1_STR)

# アプリケーション起動時の処理
@app.on_event("startup")
async def startup_event():
    print("アプリケーションを起動しています...")
    # データベース接続などの初期化処理をここに追加

# アプリケーション終了時の処理
@app.on_event("shutdown")
async def shutdown_event():
    print("アプリケーションをシャットダウンしています...")
    # リソースのクリーンアップ処理をここに追加

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
