#!/usr/bin/env python3
"""
Smoke-test all /api/crm/* routes registered in lugal_crm controllers.
Uses a fresh JWT for base.user_admin (same as Odoo shell would mint).
Does not modify the database or application code.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ODOO_BIN = ROOT / "odoo-bin"
ODOO_CONF = ROOT / "odoo.conf"
DB = "nbs_lugalai"
BASE = "http://127.0.0.1:8069"
CONTROLLERS = ROOT / "addons" / "lugal_crm" / "controllers"


def mint_jwt() -> str:
    code = """
admin = env.ref('base.user_admin')
t = env['lugal.jwt.service'].sudo().generate_access_token(admin.id)
print(t.decode() if isinstance(t, bytes) else str(t))
"""
    p = subprocess.run(
        [sys.executable, str(ODOO_BIN), "shell", "-c", str(ODOO_CONF), "-d", DB],
        input=code,
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )
    if p.returncode != 0:
        print(p.stderr, file=sys.stderr)
        sys.exit(p.returncode)
    lines = [ln.strip() for ln in p.stdout.splitlines() if ln.strip()]
    if not lines:
        sys.exit("No JWT from shell")
    return lines[-1]


def collect_routes() -> list[tuple[str, str]]:
    """Return list of (path, type) e.g. ('/api/crm/foo', 'jsonrpc')."""
    route_re = re.compile(
        r"@http\.route\(\s*'(/api/crm[^']+)'\s*,\s*type='(jsonrpc|http)'"
    )
    found: dict[str, str] = {}
    for py in sorted(CONTROLLERS.glob("*.py")):
        if py.name.startswith("_"):
            continue
        text = py.read_text(encoding="utf-8", errors="replace")
        for m in route_re.finditer(text):
            path, rtype = m.group(1), m.group(2)
            found[path] = rtype
    return sorted(found.items(), key=lambda x: x[0])


def materialize_path(path: str) -> str:
    return re.sub(r"<int:\w+>", "1", path)


def call_jsonrpc(token: str, path: str) -> tuple[int, object]:
    url = BASE + path
    body = json.dumps(
        {"jsonrpc": "2.0", "method": "call", "params": {}, "id": 1}
    ).encode()
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-Odoo-Database": DB,
            "Authorization": f"Bearer {token}",
        },
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
        code = resp.status
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return code, {"_raw": raw[:500]}
    return code, data


def call_http_form(token: str, path: str) -> tuple[int, str]:
    url = BASE + path
    body = b"branch_id=&period_start=&period_end="
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Odoo-Database": DB,
            "Authorization": f"Bearer {token}",
        },
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
        return resp.status, raw[:200]


def main() -> None:
    token = mint_jwt()
    routes = collect_routes()
    ok = 0
    fail = 0
    rows: list[str] = []

    for path, rtype in routes:
        mp = materialize_path(path)
        try:
            if rtype == "jsonrpc":
                code, data = call_jsonrpc(token, mp)
                if code != 200:
                    fail += 1
                    rows.append(f"FAIL {mp} HTTP {code} {str(data)[:120]}")
                    continue
                if not isinstance(data, dict):
                    fail += 1
                    rows.append(f"FAIL {mp} non-dict body")
                    continue
                if "error" in data and data["error"]:
                    err = data["error"]
                    msg = ""
                    if isinstance(err, dict):
                        d = err.get("data") or {}
                        msg = str(d.get("message") or err.get("message") or "")
                    else:
                        msg = str(err)
                    if "missing" in msg and "required positional argument" in msg:
                        rows.append(f"NEED_PARAMS {mp} ({msg[:70]}…)")
                        ok += 1
                        continue
                    fail += 1
                    rows.append(f"FAIL {mp} jsonrpc error {err}")
                    continue
                res = data.get("result")
                if isinstance(res, dict) and res.get("success") is False:
                    # Endpoint reachable; business validation / missing id is acceptable for smoke
                    err = (res.get("error") or "")[:80]
                    rows.append(f"REACH {mp} success=False err={err!r}")
                    ok += 1
                else:
                    rows.append(f"OK   {mp}")
                    ok += 1
            else:
                code, snippet = call_http_form(token, mp)
                if code == 200:
                    rows.append(f"OK   {mp} http CSV len={len(snippet)}")
                    ok += 1
                elif code in (401, 403):
                    rows.append(f"REACH {mp} HTTP {code} (auth/role gate)")
                    ok += 1
                else:
                    fail += 1
                    rows.append(f"FAIL {mp} HTTP {code} {snippet[:80]}")
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")[:200]
            if e.code in (401, 403):
                rows.append(f"REACH {mp} HTTP {e.code}")
                ok += 1
            elif e.code == 400 and ("No file" in body or "files provided" in body):
                rows.append(f"NEED_PARAMS {mp} HTTP 400 (multipart upload required)")
                ok += 1
            else:
                fail += 1
                rows.append(f"FAIL {mp} HTTPError {e.code} {body}")
        except Exception as ex:
            fail += 1
            rows.append(f"FAIL {mp} {type(ex).__name__}: {ex}")

    print(f"Routes tested: {len(routes)}  OK/reachable: {ok}  Hard fail: {fail}\n")
    for line in rows:
        print(line)


if __name__ == "__main__":
    main()
