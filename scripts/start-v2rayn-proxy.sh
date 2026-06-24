#!/bin/bash
# 启动 v2rayN xray（全局模式），供批量查询使用。
# 轮换逻辑见 scripts/v2rayn_rotator.py

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="${ROOT}/.venv/bin/python"

if [[ ! -x "$PYTHON" ]]; then
    echo "❌ 未找到虚拟环境，请先运行「安装环境.command」"
    exit 1
fi

"$PYTHON" "$ROOT/batch-doctor-query.py" --v2rayn-warmup
