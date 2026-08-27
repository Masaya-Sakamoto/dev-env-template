#!/bin/bash
set -euo pipefail

# スクリプトの配置ディレクトリからプロジェクトルートに移動
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

echo "=========================================="
echo "🧪 インフラ統合テスト (Runtime直接検証)"
echo "=========================================="
echo ""

# 1. 依存イメージのビルド (base -> builder)
echo "📦 Step 1: Base および Builder イメージをビルド中..."
docker compose build base
docker compose build builder

# 2. ランタイムイメージのビルド (テスト対象)
echo "📦 Step 2: Runtime イメージをビルド中..."
docker compose build runtime

# 3. テストの実行
echo "🧪 Step 3: Runtime イメージ上で Sionna-RT ユニットテストを実行中..."
docker compose --profile test run --rm test

echo ""
echo "=========================================="
echo "✅ インフラ統合テストが正常に完了しました！"
echo "=========================================="
