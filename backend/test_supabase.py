# -*- coding: utf-8 -*-
"""
Supabaseクライアント初期化のテスト
"""

import pkg_resources
import importlib.metadata

def get_package_version(package_name):
    """パッケージのバージョンを取得する"""
    try:
        return importlib.metadata.version(package_name)
    except importlib.metadata.PackageNotFoundError:
        try:
            return pkg_resources.get_distribution(package_name).version
        except pkg_resources.DistributionNotFound:
            return "Not installed"

# Supabase関連のパッケージのバージョンを取得する
supabase_version = get_package_version("supabase")
gotrue_version = get_package_version("gotrue")
postgrest_version = get_package_version("postgrest")
realtime_version = get_package_version("realtime")
storage3_version = get_package_version("storage3")

print("Supabase関連パッケージのバージョン情報:")
print(f"- supabase: {supabase_version}")
print(f"- gotrue: {gotrue_version}")
print(f"- postgrest: {postgrest_version}")
print(f"- realtime: {realtime_version}")
print(f"- storage3: {storage3_version}")

# Supabaseクライアントのインポートと初期化をテスト
print("\nSupabaseクライアントの初期化テスト:")
try:
    from supabase import create_client, Client
    
    # テスト用のダミー値
    dummy_url = "https://example.supabase.co"
    dummy_key = "dummy_key"
    
    # create_clientの実装を確認
    print("create_client関数のヘルプ:")
    import inspect
    create_client_sig = inspect.signature(create_client)
    print(f"パラメータ: {create_client_sig}")
    
    # クライアントの初期化を試みる（実際の接続はしない）
    print("\n基本的なパラメータでの初期化テスト:")
    try:
        # 単純な初期化（接続しない）
        create_client(dummy_url, dummy_key)
        print("✅ 基本的なパラメータでの初期化は成功しました")
    except Exception as e:
        print(f"❌ 基本的なパラメータでの初期化に失敗しました: {e}")
    
    # クライアントクラスの確認
    print("\nクライアントクラスの確認:")
    client_init_sig = inspect.signature(Client.__init__)
    print(f"Client.__init__パラメータ: {client_init_sig}")
    
    # 内部で使用されるクラスの確認
    # Supabaseの実装によって異なる可能性がある
    print("\n内部クラスの確認:")
    try:
        from supabase._sync.client import SyncClient
        sync_client_init_sig = inspect.signature(SyncClient.__init__)
        print(f"SyncClient.__init__パラメータ: {sync_client_init_sig}")
    except (ImportError, AttributeError) as e:
        print(f"SyncClientの確認に失敗しました: {e}")
    
except ImportError as e:
    print(f"❌ Supabaseクライアントのインポートに失敗しました: {e}")
except Exception as e:
    print(f"❌ 予期しないエラーが発生しました: {e}")

print("\nテスト完了")
