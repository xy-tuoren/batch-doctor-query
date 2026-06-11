#!/usr/bin/env python3
"""一次性：从 xlsx 读取名单，跳过已有截图，调用 batch-doctor-query.py。不修改主脚本。"""

import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCREENSHOTS = os.path.join(ROOT, "screenshots")
MAIN = os.path.join(ROOT, "batch-doctor-query.py")
PYTHON = os.path.join(ROOT, ".venv", "bin", "python")

XLSX = (
    "/Users/xy/Library/Containers/com.tencent.WeWorkMac/Data/Documents/Profiles/"
    "4590F4BED282AC97B23CD34DC195AF8E/Caches/Files/2026-06/"
    "7c0d348e59621ae420180643b8fe6fcf/档案编号-姓名-卫健委图.xlsx"
)
TEMP_JSON = os.path.join(ROOT, "name-xlsx-temp.json")


def load_xlsx(path: str) -> list[dict]:
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with zipfile.ZipFile(path) as zf:
        ss_root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
        strings = []
        for si in ss_root.findall("m:si", ns):
            parts = [x.text or "" for x in si.findall(".//m:t", ns)]
            strings.append("".join(parts))
        sheet = ET.fromstring(zf.read("xl/worksheets/sheet1.xml"))

    def cell_value(cell) -> str:
        t = cell.get("t")
        v = cell.find("m:v", ns)
        if v is None or v.text is None:
            return ""
        val = v.text
        if t == "s":
            val = strings[int(val)]
        return str(val).strip()

    rows = []
    for row in sheet.findall("m:sheetData/m:row", ns):
        vals = [cell_value(c) for c in row.findall("m:c", ns)]
        if any(vals):
            rows.append(vals)
    if not rows:
        return []

    header = rows[0]
    name_idx = header.index("姓名")
    cert_idx = header.index("档案编号")

    doctors = []
    for row in rows[1:]:
        if name_idx >= len(row):
            continue
        name = row[name_idx].strip()
        if not name:
            continue
        cert = row[cert_idx].strip() if cert_idx < len(row) else ""
        doctors.append({"name": name, "certCode": cert or None})
    return doctors


def has_screenshot(name: str, cert: str | None) -> bool:
    if cert and os.path.exists(os.path.join(SCREENSHOTS, f"{name}_{cert}.png")):
        return True
    prefix = f"{name}_"
    try:
        for fname in os.listdir(SCREENSHOTS):
            if fname.startswith(prefix) and fname.endswith(".png"):
                return True
    except FileNotFoundError:
        pass
    return False


def parse_argv() -> tuple[str, list[str]]:
    """仅当首个参数是 .xlsx/.xls 时视为名单路径，其余全部转给主脚本。"""
    args = sys.argv[1:]
    if args and args[0].lower().endswith((".xlsx", ".xls")):
        return args[0], args[1:]
    return XLSX, args


def main():
    xlsx, extra = parse_argv()
    doctors = load_xlsx(xlsx)

    pending = []
    skipped = []
    for d in doctors:
        if has_screenshot(d["name"], d.get("certCode")):
            skipped.append(d)
        else:
            pending.append(d)

    print(f"名单 {len(doctors)} 人，已有截图跳过 {len(skipped)}，待查 {len(pending)}")
    if skipped:
        print("跳过:", ", ".join(d["name"] for d in skipped))
    if not pending:
        print("✅ 无需查询")
        return 0

    with open(TEMP_JSON, "w", encoding="utf-8") as f:
        json.dump(pending, f, ensure_ascii=False, indent=2)
    print(f"临时名单: {TEMP_JSON}")
    print("待查:", ", ".join(d["name"] for d in pending))
    print()

    cmd = [PYTHON, MAIN, "-f", TEMP_JSON, *extra]
    return subprocess.call(cmd)


if __name__ == "__main__":
    sys.exit(main())
