#!/bin/bash
set -e
source "$(dirname "$0")/scripts/env.sh"

echo "📂 项目: $ROOT"
echo "▶  创建/更新虚拟环境并安装依赖"
echo

if [[ ! -d "$ROOT/.venv" ]]; then
    echo "创建 .venv …"
    python3 -m venv "$ROOT/.venv"
fi

"$PYTHON" -m pip install --upgrade pip -q
"$PYTHON" -m pip install -r "$ROOT/requirements.txt"
"$PYTHON" -m playwright install chromium

echo
echo "✅ 环境就绪: $ROOT/.venv"
"$PYTHON" --version
echo
echo "   查询-无头.command      批量查询（后台）"
echo "   查询-有头.command      批量查询（显示浏览器）"
echo "   查询-代理轮换.command  代理查询，上限自动换 IP"
echo "   验证码测试.command     仅测验证码（无头）"
pause_before_close
