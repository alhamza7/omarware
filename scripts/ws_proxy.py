#!/usr/bin/env python3
"""
Lugal WebSocket Reverse Proxy
==============================
Listens on PROXY_PORT and routes:
  • /websocket  →  GEVENT_PORT (8076)  — WebSocket upgrade
  • everything  →  ODOO_PORT   (8075)  — normal HTTP

Run:
    python3 scripts/ws_proxy.py

Service is registered as a systemd user unit (lugal-proxy.service).

Keep-alive strategy
-------------------
Odoo's bus/websocket.py has a hardcoded CONNECTION_TIMEOUT = 60 s.
After 45 s of silence it sends a PING; if no PONG arrives within 15 s it
closes the connection with code 4002 (KEEP_ALIVE_TIMEOUT).

When a browser tab goes to the background, browsers throttle JS/WS callbacks
so the round-trip  Odoo→proxy→browser→proxy→Odoo  can easily exceed 15 s,
causing Odoo to tear down the connection (user sees no notifications until
they hard-reload).

Fix: the proxy answers Odoo's PINGs immediately (proxy-side PONG), so Odoo
never times out regardless of what the browser is doing.  A separate
coroutine sends periodic PINGs to the browser so that leg of the tunnel also
stays alive even during long periods of user inactivity.
"""

import asyncio
import aiohttp
from aiohttp import web, ClientSession, ClientTimeout, WSMsgType
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("ws_proxy")

# Client-facing ports. 8069 preserves the historical backend URL used by FE;
# 3003 is kept for older proxy-based clients/tools.
PROXY_PORTS = (8069, 3003)
ODOO_HOST   = "http://127.0.0.1:8075"
GEVENT_HOST = "http://127.0.0.1:8076"

# Send a PING to the browser every N seconds to keep the browser-side
# connection alive.  Must be shorter than any browser/OS idle timeout
# (typically 60–120 s).  30 s is a safe margin.
BROWSER_PING_INTERVAL = 30

SKIP_HEADERS = {"host", "content-length", "transfer-encoding", "connection",
                "keep-alive", "te", "trailers", "upgrade"}


async def proxy_websocket(request: web.Request) -> web.WebSocketResponse:
    """Upgrade to WebSocket and bridge to gevent worker on 8072."""
    # autoping=True: aiohttp automatically replies to any PING the browser
    # sends with a PONG.  We still send our own periodic pings to the browser.
    ws_server = web.WebSocketResponse(autoping=True)
    await ws_server.prepare(request)

    qs = "?" + request.query_string if request.query_string else ""
    target = GEVENT_HOST.replace("http://", "ws://") + request.path + qs

    upstream_headers = {k: v for k, v in request.headers.items()
                        if k.lower() not in {"host", "sec-websocket-key",
                                             "sec-websocket-extensions"}}
    upstream_headers["Host"] = "127.0.0.1:8076"
    try:
        origin_port = int((request.host or '').rsplit(':', 1)[-1])
    except Exception:
        origin_port = PROXY_PORTS[0]
    upstream_headers["Origin"] = f"http://127.0.0.1:{origin_port}"

    log.info("WS  %s → %s", request.path + qs, target)

    # timeout=None: never let aiohttp kill a long-lived idle WebSocket
    # connection at the session level.
    _no_timeout = ClientTimeout(total=None, connect=30)
    try:
        async with ClientSession(timeout=_no_timeout) as session:
            # autoping=True: aiohttp automatically PONGs Odoo's PINGs
            # immediately, so Odoo's 15-second PONG-wait never fires.
            async with session.ws_connect(
                target,
                headers=upstream_headers,
                autoclose=False,
                autoping=True,          # ← key fix: proxy PONGs Odoo instantly
                heartbeat=30,           # ← also send keep-alive PINGs upstream
            ) as ws_client:

                async def forward_to_client():
                    """Forward data/control frames from Odoo → browser."""
                    async for msg in ws_client:
                        if msg.type == WSMsgType.TEXT:
                            await ws_server.send_str(msg.data)
                        elif msg.type == WSMsgType.BINARY:
                            await ws_server.send_bytes(msg.data)
                        elif msg.type in (WSMsgType.PING, WSMsgType.PONG):
                            # autoping=True already handled these on ws_client;
                            # nothing to forward — swallow silently.
                            pass
                        elif msg.type == WSMsgType.CLOSE:
                            # Forward the close code + reason so the browser
                            # receives it (e.g. 4001 = session expired → FE
                            # calls _ensureSession and reconnects cleanly).
                            log.info(
                                "WS upstream CLOSE code=%s → forwarding to browser",
                                ws_client.close_code,
                            )
                            await ws_server.close(
                                code=ws_client.close_code or 1000,
                                message=(ws_client.close_message or b''),
                            )
                            break
                        elif msg.type == WSMsgType.ERROR:
                            log.warning("WS upstream error: %s", ws_client.exception())
                            break

                async def forward_to_server():
                    """Forward data/control frames from browser → Odoo."""
                    async for msg in ws_server:
                        if msg.type == WSMsgType.TEXT:
                            await ws_client.send_str(msg.data)
                        elif msg.type == WSMsgType.BINARY:
                            await ws_client.send_bytes(msg.data)
                        elif msg.type in (WSMsgType.PING, WSMsgType.PONG):
                            # autoping=True on ws_server already handled these;
                            # swallow so we don't double-reply upstream.
                            pass
                        elif msg.type == WSMsgType.CLOSE:
                            log.info(
                                "WS browser CLOSE code=%s → forwarding upstream",
                                ws_server.close_code,
                            )
                            await ws_client.close(
                                code=ws_server.close_code or 1000,
                                message=(ws_server.close_message or b''),
                            )
                            break
                        elif msg.type == WSMsgType.ERROR:
                            log.warning("WS browser error: %s", ws_server.exception())
                            break

                async def browser_keepalive():
                    """Periodically ping the browser to prevent idle disconnects.

                    Browsers (especially background tabs) do not send frames on
                    their own, so without this the proxy→browser leg silently
                    dies after the OS/browser idle timeout (~60–120 s).
                    """
                    while not ws_server.closed:
                        await asyncio.sleep(BROWSER_PING_INTERVAL)
                        if ws_server.closed:
                            break
                        try:
                            await ws_server.ping()
                        except Exception:
                            break

                await asyncio.gather(
                    forward_to_client(),
                    forward_to_server(),
                    browser_keepalive(),
                    return_exceptions=True,
                )
    except Exception as exc:
        log.warning("WS proxy error: %s", exc)
    finally:
        if not ws_server.closed:
            await ws_server.close()

    return ws_server


async def proxy_http(request: web.Request) -> web.StreamResponse:
    """Forward all other HTTP requests to Odoo on 8069."""
    qs = "?" + request.query_string if request.query_string else ""
    target = ODOO_HOST + request.path + qs

    headers = {k: v for k, v in request.headers.items()
               if k.lower() not in SKIP_HEADERS}
    original_host = request.headers.get("Host", "")
    headers["Host"] = "127.0.0.1:8075"
    headers["X-Forwarded-For"] = request.remote
    headers["X-Forwarded-Proto"] = "http"
    headers["X-Forwarded-Host"] = original_host  # original client-facing host:port

    body = await request.read()

    async with ClientSession() as session:
        async with session.request(
            request.method, target,
            headers=headers, data=body,
            allow_redirects=False,
        ) as resp:
            response_headers = {k: v for k, v in resp.headers.items()
                                 if k.lower() not in {"transfer-encoding", "content-encoding"}}
            response = web.StreamResponse(status=resp.status, headers=response_headers)
            await response.prepare(request)
            async for chunk in resp.content.iter_chunked(65536):
                await response.write(chunk)
            await response.write_eof()
            return response


async def router(request: web.Request):
    upgrade = request.headers.get("Upgrade", "").lower()
    if upgrade == "websocket":
        return await proxy_websocket(request)
    return await proxy_http(request)


def main():
    # Allow up to 1 GB request bodies to support large email attachment uploads.
    _1GB = 1 * 1024 * 1024 * 1024
    app = web.Application(client_max_size=_1GB)
    app.router.add_route("*", "/{path_info:.*}", router)

    log.info("Lugal Proxy starting on ports %s (max body: 1 GB)", PROXY_PORTS)
    log.info("  HTTP  → %s", ODOO_HOST)
    log.info("  WS    → %s", GEVENT_HOST.replace("http://", "ws://"))

    async def _run():
        runner = web.AppRunner(app, access_log=None)
        await runner.setup()
        sites = []
        for port in PROXY_PORTS:
            site = web.TCPSite(runner, host="0.0.0.0", port=port)
            await site.start()
            sites.append(site)
            log.info("  Listening on :%d", port)
        while True:
            await asyncio.sleep(3600)

    asyncio.run(_run())


if __name__ == "__main__":
    main()
