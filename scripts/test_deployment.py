#!/usr/bin/env python3
"""
デプロイ後のテストスクリプト

APIエンドポイントとフロントエンドのヘルスチェックを実行
"""

import argparse
import json
import sys
import time
from urllib.parse import urljoin
import requests

def check_api_health(base_url: str, verbose: bool = False) -> bool:
    """APIのヘルスチェックを実行"""
    health_url = urljoin(base_url, "/health")
    
    try:
        if verbose:
            print(f"ヘルスチェックエンドポイントにアクセス中: {health_url}")
            
        response = requests.get(health_url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if verbose:
                print(f"ヘルスチェック成功: {json.dumps(data, ensure_ascii=False, indent=2)}")
            return True
        else:
            if verbose:
                print(f"ヘルスチェック失敗: ステータスコード {response.status_code}")
            return False
    except Exception as e:
        if verbose:
            print(f"ヘルスチェックエラー: {e}")
        return False

def check_frontend(url: str, verbose: bool = False) -> bool:
    """フロントエンドのアクセスチェックを実行"""
    try:
        if verbose:
            print(f"フロントエンドにアクセス中: {url}")
            
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            if verbose:
                print(f"フロントエンドアクセス成功: ステータスコード {response.status_code}")
            return True
        else:
            if verbose:
                print(f"フロントエンドアクセス失敗: ステータスコード {response.status_code}")
            return False
    except Exception as e:
        if verbose:
            print(f"フロントエンドアクセスエラー: {e}")
        return False

def test_api_endpoints(base_url: str, verbose: bool = False) -> dict:
    """主要なAPIエンドポイントをテスト"""
    results = {}
    
    # テスト対象のエンドポイント
    endpoints = [
        {"path": "/api/v1/health", "method": "GET", "expected_status": 200},
        {"path": "/api/v1/projects", "method": "GET", "expected_status": 200},
        {"path": "/api/v1/wind-estimation/status", "method": "GET", "expected_status": 200},
        {"path": "/api/v1/strategy-detection/status", "method": "GET", "expected_status": 200},
    ]
    
    for endpoint in endpoints:
        path = endpoint["path"]
        method = endpoint["method"]
        expected_status = endpoint["expected_status"]
        
        url = urljoin(base_url, path)
        
        try:
            if verbose:
                print(f"{method} リクエスト送信中: {url}")
                
            if method == "GET":
                response = requests.get(url, timeout=10)
            elif method == "POST":
                response = requests.post(url, json={}, timeout=10)
            else:
                if verbose:
                    print(f"未対応のHTTPメソッド: {method}")
                continue
                
            success = response.status_code == expected_status
            
            results[path] = {
                "success": success,
                "status_code": response.status_code,
                "expected_status": expected_status,
            }
            
            if verbose:
                status = "成功" if success else "失敗"
                print(f"エンドポイント {path} テスト{status}: "
                      f"ステータスコード {response.status_code} (期待値: {expected_status})")
                
        except Exception as e:
            results[path] = {
                "success": False,
                "error": str(e),
            }
            
            if verbose:
                print(f"エンドポイント {path} テストエラー: {e}")
    
    return results

def main():
    """メイン実行関数"""
    parser = argparse.ArgumentParser(description="デプロイ後のテストスクリプト")
    parser.add_argument("--api-url", 
                        default="https://sailing-strategy-api.onrender.com",
                        help="バックエンドAPIのベースURL")
    parser.add_argument("--frontend-url", 
                        default="https://sailing-strategy-analyzer.vercel.app",
                        help="フロントエンドのURL")
    parser.add_argument("--verbose", "-v", 
                        action="store_true",
                        help="詳細な出力を表示")
    
    args = parser.parse_args()
    
    print("セーリング戦略分析システム デプロイテスト")
    print("=" * 50)
    
    # APIヘルスチェック
    print("\nAPIヘルスチェック...")
    api_health = check_api_health(args.api_url, args.verbose)
    print(f"APIヘルスチェック: {'成功' if api_health else '失敗'}")
    
    # APIエンドポイントテスト（ヘルスチェックが成功した場合のみ）
    if api_health:
        print("\nAPIエンドポイントテスト...")
        api_results = test_api_endpoints(args.api_url, args.verbose)
        
        success_count = sum(1 for result in api_results.values() if result.get("success", False))
        total_count = len(api_results)
        
        print(f"APIエンドポイントテスト: {success_count}/{total_count} 成功")
    
    # フロントエンドアクセスチェック
    print("\nフロントエンドアクセスチェック...")
    frontend_health = check_frontend(args.frontend_url, args.verbose)
    print(f"フロントエンドアクセス: {'成功' if frontend_health else '失敗'}")
    
    # 総合結果
    print("\n総合結果:")
    overall_success = api_health and (api_health is False or success_count == total_count) and frontend_health
    print(f"テスト全体: {'成功' if overall_success else '失敗'}")
    
    # 終了コード
    sys.exit(0 if overall_success else 1)

if __name__ == "__main__":
    main()
