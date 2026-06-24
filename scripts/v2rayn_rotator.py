"""v2rayN 订阅节点轮换：从 guiNDB 读取节点，用 xray 全局代理启动/切换。"""

from __future__ import annotations

import json
import os
import re
import socket
import sqlite3
import subprocess
import time
import urllib.request
from pathlib import Path

V2RAYN_HOME = Path.home() / "Library/Application Support/v2rayN"
GUI_CONFIG = V2RAYN_HOME / "guiConfigs/guiNConfig.json"
GUI_DB = V2RAYN_HOME / "guiConfigs/guiNDB.db"
XRAY_BIN = V2RAYN_HOME / "bin/xray/xray"
RUNTIME_CONFIG = V2RAYN_HOME / "binConfigs/config.json"
DEFAULT_PORT = 10808
DEFAULT_NODE_FILTER = "CF官方优选%"
VLESS_CONFIG_TYPE = 5


def _node_sort_key(remarks: str) -> tuple[int, str]:
    m = re.search(r"优选(\d+)$", remarks or "")
    return (int(m.group(1)) if m else 9999, remarks or "")


def _port_listening(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def _vless_uuid(profile: dict) -> str:
    """v2rayN 数据库里 VLESS 的 UUID 存在 Password 列。"""
    return (profile.get("Password") or profile.get("Id") or "").strip()


def build_global_xray_config(profile: dict, port: int = DEFAULT_PORT) -> dict:
    """根据 ProfileItem 行生成全局走 proxy 的 xray 配置。"""
    uuid = _vless_uuid(profile)
    if not uuid:
        raise ValueError(f"节点 {profile.get('Remarks')} 缺少 VLESS UUID")
    outbound = {
        "tag": "proxy",
        "protocol": "vless",
        "settings": {
            "vnext": [{
                "address": profile["Address"],
                "port": int(profile["Port"]),
                "users": [{
                    "id": uuid,
                    "email": "t@t.tt",
                    "security": profile.get("Security") or "auto",
                    "encryption": "none",
                }],
            }],
        },
        "mux": {"enabled": False, "concurrency": -1},
    }
    network = profile.get("Network") or "tcp"
    stream: dict = {"network": network}
    if profile.get("StreamSecurity"):
        stream["security"] = profile["StreamSecurity"]
        tls: dict = {}
        if profile.get("Sni"):
            tls["serverName"] = profile["Sni"]
        if profile.get("Fingerprint"):
            tls["fingerprint"] = profile["Fingerprint"]
        if str(profile.get("AllowInsecure")).lower() == "true":
            tls["allowInsecure"] = True
        if tls:
            stream["tlsSettings"] = tls
    if network == "ws":
        stream["wsSettings"] = {
            "path": profile.get("Path") or "/",
            "host": profile.get("RequestHost") or profile.get("Sni") or "",
            "headers": {},
        }
    outbound["streamSettings"] = stream

    return {
        "log": {"loglevel": "warning"},
        "inbounds": [{
            "tag": "mixed",
            "port": port,
            "listen": "127.0.0.1",
            "protocol": "mixed",
            "sniffing": {
                "enabled": True,
                "destOverride": ["http", "tls"],
                "routeOnly": False,
            },
            "settings": {
                "auth": "noauth",
                "udp": True,
                "allowTransparent": False,
            },
        }],
        "outbounds": [
            outbound,
            {"tag": "direct", "protocol": "freedom"},
            {"tag": "block", "protocol": "blackhole"},
        ],
        "routing": {
            "domainStrategy": "AsIs",
            "rules": [{
                "type": "field",
                "network": "tcp,udp",
                "outboundTag": "proxy",
            }],
        },
    }


class V2rayNRotator:
    """受限时轮换 v2rayN 订阅内 CF官方优选 等节点。"""

    def __init__(
        self,
        node_filter: str = DEFAULT_NODE_FILTER,
        port: int = DEFAULT_PORT,
        log_fn=None,
    ):
        self.node_filter = node_filter
        self.port = port
        self._log = log_fn or (lambda msg: print(msg, flush=True))
        self._nodes: list[dict] = []
        self._index = -1
        self._load_nodes()
        if not XRAY_BIN.is_file():
            raise FileNotFoundError(f"未找到 xray: {XRAY_BIN}")
        self._ensure_global_mode_in_gui()
        if self._nodes:
            self._apply_node(self._nodes[self._index if self._index >= 0 else 0])

    @property
    def node_count(self) -> int:
        return len(self._nodes)

    def _load_nodes(self):
        if not GUI_DB.is_file():
            raise FileNotFoundError(f"未找到 v2rayN 数据库: {GUI_DB}")

        conn = sqlite3.connect(GUI_DB)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT IndexId, Remarks, Address, Port, Network, Path,
                   StreamSecurity, Sni, Fingerprint, Id, Password, Security,
                   RequestHost, AllowInsecure, ConfigType
            FROM ProfileItem
            WHERE Remarks LIKE ?
              AND ConfigType = ?
              AND COALESCE(Password, Id, '') != ''
            """,
            (self.node_filter, VLESS_CONFIG_TYPE),
        ).fetchall()
        conn.close()

        self._nodes = sorted([dict(r) for r in rows], key=lambda r: _node_sort_key(r["Remarks"]))
        if not self._nodes:
            raise RuntimeError(f"订阅内没有匹配「{self.node_filter}」的 VLESS 节点")

        current_id = None
        if GUI_CONFIG.is_file():
            try:
                with GUI_CONFIG.open(encoding="utf-8") as f:
                    current_id = json.load(f).get("IndexId")
            except (json.JSONDecodeError, OSError):
                pass
        if current_id:
            for i, n in enumerate(self._nodes):
                if n["IndexId"] == current_id:
                    self._index = i
                    break

    def _ensure_global_mode_in_gui(self):
        if not GUI_CONFIG.is_file():
            return
        try:
            with GUI_CONFIG.open(encoding="utf-8") as f:
                cfg = json.load(f)
            cfg.setdefault("ClashUIItem", {})["RuleMode"] = 1
            with GUI_CONFIG.open("w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2, ensure_ascii=False)
                f.write("\n")
        except (json.JSONDecodeError, OSError):
            pass

    def current_node(self) -> str | None:
        if self._index < 0 or self._index >= len(self._nodes):
            return None
        return self._nodes[self._index]["Remarks"]

    def _write_gui_index(self, index_id: str):
        if not GUI_CONFIG.is_file():
            return
        try:
            with GUI_CONFIG.open(encoding="utf-8") as f:
                cfg = json.load(f)
            cfg["IndexId"] = index_id
            cfg.setdefault("ClashUIItem", {})["RuleMode"] = 1
            with GUI_CONFIG.open("w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2, ensure_ascii=False)
                f.write("\n")
        except (json.JSONDecodeError, OSError):
            pass

    def _wait_port(self, timeout: float = 20) -> bool:
        deadline = time.time() + timeout
        while time.time() < deadline:
            if _port_listening(self.port):
                return True
            time.sleep(0.3)
        return False

    def _restart_xray(self):
        subprocess.run(["pkill", "-x", "v2rayN"], check=False)
        subprocess.run(["pkill", "-x", "xray"], check=False)
        time.sleep(0.6)
        subprocess.Popen(
            [str(XRAY_BIN), "run", "-c", str(RUNTIME_CONFIG)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        if not self._wait_port():
            raise RuntimeError(f"xray 未在 {self.port} 端口启动")

    def _apply_node(self, profile: dict):
        RUNTIME_CONFIG.parent.mkdir(parents=True, exist_ok=True)
        with RUNTIME_CONFIG.open("w", encoding="utf-8") as f:
            json.dump(build_global_xray_config(profile, self.port), f, indent=2)
            f.write("\n")
        self._write_gui_index(profile["IndexId"])
        self._restart_xray()
        time.sleep(1.0)

    def rotate(self) -> str | None:
        if not self._nodes:
            self._log(f"  ⚠ v2rayN 没有可轮换节点（{self.node_filter}）")
            return None
        self._index = (self._index + 1) % len(self._nodes)
        profile = self._nodes[self._index]
        try:
            self._apply_node(profile)
        except (OSError, subprocess.SubprocessError, RuntimeError) as e:
            self._log(f"  ⚠ v2rayN 切换节点失败: {e}")
            return None
        name = profile["Remarks"]
        self._log(f"  🌐 v2rayN 已切换节点 → {name}")
        return name


def warmup_v2rayn_proxy(
    node_filter: str = DEFAULT_NODE_FILTER,
    port: int = DEFAULT_PORT,
) -> str:
    """启动 xray 并返回代理 URL（供 start-v2rayn-proxy.sh 调用）。"""
    rotator = V2rayNRotator(node_filter=node_filter, port=port)
    proxy_url = f"socks5://127.0.0.1:{port}"
    ip = ""
    try:
        proxy_handler = urllib.request.ProxyHandler({
            "http": proxy_url,
            "https": proxy_url,
        })
        opener = urllib.request.build_opener(proxy_handler)
        with opener.open("https://api.ipify.org", timeout=12) as resp:
            ip = resp.read().decode().strip()
    except OSError:
        ip = ""
    node = rotator.current_node() or "?"
    print(f"✓ v2rayN 节点: {node}（{rotator.node_count} 个可轮换）")
    if ip:
        print(f"✓ 代理出口 IP: {ip}")
    print(f"PROXY_URL={proxy_url}")
    return proxy_url

