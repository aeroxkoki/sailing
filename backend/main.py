"""
セーリング戦略分析システム - FastAPI バックエンド
"""

import os
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# 環境変数のロード
load_dotenv()

# アプリケーションの作成
app = FastAPI(
    title="セーリング戦略分析システム API",
    description="セーリング競技のGPSデータを分析し、戦略を評価するためのAPI",
    version="0.1.0"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルートパス
@app.get("/")
async def root():
    return {"message": "セーリング戦略分析システムAPIへようこそ"}

# ヘルスチェック
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# APIルーターのインポートと登録
from app.api.router import api_router
from app.core.config import settings

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
