#!/bin/bash
set -e
source "$(dirname "$0")/scripts/env.sh"

require_venv || { pause_before_close; exit 1; }

echo "📂 项目: $ROOT"
echo "▶  一次性 xlsx 名单查询（不修改主脚本）"
echo

"$PYTHON" "$ROOT/scripts/run-xlsx-once.py"
EXIT=$?

echo
if [[ $EXIT -eq 0 ]]; then
    echo "✅ 执行完成"
else
    echo "❌ 退出码: $EXIT"
fi
pause_before_close
exit $EXIT
