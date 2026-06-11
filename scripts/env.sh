#!/bin/bash
# 项目根目录（scripts/ 的上一级）
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || exit 1

PYTHON="$ROOT/.venv/bin/python"

require_venv() {
    if [[ ! -x "$PYTHON" ]]; then
        echo "❌ 未找到虚拟环境: $ROOT/.venv"
        echo "   请先双击「安装环境.command」"
        return 1
    fi
}

pause_before_close() {
    echo
    read -r -p "按回车键关闭窗口…"
}
