#!/bin/bash
set -e
source "$(dirname "$0")/scripts/env.sh"

require_venv || { pause_before_close; exit 1; }

echo "📂 项目: $ROOT"
echo "▶  批量查询（无头）"
echo

"$PYTHON" "$ROOT/batch-doctor-query.py"
EXIT=$?

echo
if [[ $EXIT -eq 0 ]]; then
    echo "✅ 执行完成"
else
    echo "❌ 退出码: $EXIT"
fi
pause_before_close
exit $EXIT
