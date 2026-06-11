#!/bin/bash
set -e
source "$(dirname "$0")/scripts/env.sh"

require_venv || { pause_before_close; exit 1; }

echo "📂 项目: $ROOT"
echo "▶  验证码测试（无头，5 轮，不点查询）"
echo "   使用 name.json 中第一个姓名"
echo

"$PYTHON" "$ROOT/batch-doctor-query.py" --test-captcha --captcha-rounds 5
EXIT=$?

echo
if [[ $EXIT -eq 0 ]]; then
    echo "✅ 执行完成"
else
    echo "❌ 退出码: $EXIT"
fi
pause_before_close
exit $EXIT
