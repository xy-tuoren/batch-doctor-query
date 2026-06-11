#!/bin/bash
set -e
source "$(dirname "$0")/scripts/env.sh"

require_venv || { pause_before_close; exit 1; }

echo "📂 项目: $ROOT"
echo "▶  批量查询（代理 + 查询上限自动换 IP）"
echo "   代理: http://127.0.0.1:7897（Clash mixed-port，以你本机设置为准）"
echo "   Clash API: unix:///tmp/verge/verge-mihomo.sock"
echo "   Clash 组: 批量查询轮换"
echo

"$PYTHON" "$ROOT/batch-doctor-query.py" \
  --proxy http://127.0.0.1:7897 \
  --clash-api unix:///tmp/verge/verge-mihomo.sock \
  --clash-group "批量查询轮换"
EXIT=$?

echo
if [[ $EXIT -eq 0 ]]; then
    echo "✅ 执行完成"
else
    echo "❌ 退出码: $EXIT"
fi
pause_before_close
exit $EXIT
