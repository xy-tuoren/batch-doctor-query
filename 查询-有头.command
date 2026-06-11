#!/bin/bash
set -e
source "$(dirname "$0")/scripts/env.sh"

require_venv || { pause_before_close; exit 1; }

echo "📂 项目: $ROOT"
echo "▶  批量查询（显示浏览器）"
echo

"$PYTHON" "$ROOT/batch-doctor-query.py" --no-headless
EXIT=$?

echo
if [[ $EXIT -eq 0 ]]; then
    echo "✅ 执行完成"
else
    echo "❌ 退出码: $EXIT"
fi
pause_before_close
exit $EXIT
