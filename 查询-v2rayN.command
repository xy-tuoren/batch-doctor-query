#!/bin/bash
set -e
source "$(dirname "$0")/scripts/env.sh"

require_venv || { pause_before_close; exit 1; }

PROXY_URL="socks5://127.0.0.1:10808"

echo "📂 项目: $ROOT"
echo "▶  批量查询（v2rayN 代理 + 受限自动换节点）"
echo "   节点池: CF官方优选*（订阅内 edgetunnel 同类）"
echo "   代理: $PROXY_URL"
echo "   模式: xray 全局（卫健委站点也走代理）"
echo

"$PYTHON" "$ROOT/batch-doctor-query.py" \
  --proxy "$PROXY_URL" \
  --v2rayn-rotate
EXIT=$?

echo
if [[ $EXIT -eq 0 ]]; then
    echo "✅ 执行完成"
else
    echo "❌ 退出码: $EXIT"
fi
pause_before_close
exit $EXIT
