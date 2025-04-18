#!/bin/bash

# ディレクトリ構造を作成するスクリプト
cd /Users/koki_air/Documents/GitHub/sailing-strategy-analyzer/backend

# API関連のディレクトリとファイル
mkdir -p app/api/endpoints
touch app/api/__init__.py
touch app/api/router.py
touch app/api/endpoints/__init__.py
touch app/api/endpoints/wind_estimation.py
touch app/api/endpoints/strategy_detection.py
touch app/api/endpoints/data_import.py
touch app/api/endpoints/projects.py
touch app/api/endpoints/sessions.py
touch app/api/endpoints/users.py

# Core関連のディレクトリとファイル
mkdir -p app/core
touch app/core/__init__.py
touch app/core/config.py
touch app/core/security.py
touch app/core/dependencies.py

# DB関連のディレクトリとファイル
mkdir -p app/db/repositories
touch app/db/__init__.py
touch app/db/database.py
touch app/db/repositories/__init__.py
touch app/db/repositories/base_repository.py

# Models関連のディレクトリとファイル
mkdir -p app/models/domain
mkdir -p app/models/schemas
touch app/models/__init__.py
touch app/models/domain/__init__.py
touch app/models/domain/project.py
touch app/models/domain/session.py
touch app/models/domain/wind_data.py
touch app/models/domain/strategy_point.py
touch app/models/schemas/__init__.py
touch app/models/schemas/project.py
touch app/models/schemas/session.py
touch app/models/schemas/wind_data.py
touch app/models/schemas/strategy_point.py

# Services関連のディレクトリとファイル
mkdir -p app/services
touch app/services/__init__.py
touch app/services/wind_estimation_service.py
touch app/services/strategy_detection_service.py
touch app/services/data_import_service.py
touch app/services/project_service.py

# Utils関連のディレクトリとファイル
mkdir -p app/utils
touch app/utils/__init__.py
touch app/utils/gps_utils.py
touch app/utils/validation.py

# Tests関連のディレクトリとファイル
mkdir -p tests/api
mkdir -p tests/services
touch tests/__init__.py
touch tests/conftest.py
touch tests/api/__init__.py
touch tests/api/test_endpoints.py
touch tests/services/__init__.py
touch tests/services/test_services.py

# Alembic関連のディレクトリとファイル
mkdir -p alembic/versions
touch alembic/env.py

echo "Directory structure created successfully."
