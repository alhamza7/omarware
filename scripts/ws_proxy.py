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
import json
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
    """Upgrade to WebSocket and bridge to the gevent worker on 8076."""
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
    browser_closed = asyncio.Event()
    browser_to_upstream: asyncio.Queue = asyncio.Queue(maxsize=1000)
    latest_subscribe_frame = None

    async def browser_reader():
        """Read browser frames once and feed whichever upstream connection is alive."""
        nonlocal latest_subscribe_frame
        async for msg in ws_server:
            if msg.type == WSMsgType.TEXT:
                try:
                    payload = json.loads(msg.data)
                    if payload.get("event_name") == "subscribe":
                        latest_subscribe_frame = msg.data
                except Exception:
                    pass
                try:
                    browser_to_upstream.put_nowait((WSMsgType.TEXT, msg.data))
                except asyncio.QueueFull:
                    # If Odoo is unavailable long enough for 1000 client frames
                    # to pile up, the safest behavior is an explicit reconnect.
                    # Silently blocking here would make the tab look connected
                    # while no commands can reach Odoo.
                    log.warning("WS browser queue full; closing browser socket for clean reconnect")
                    await ws_server.close(code=1013, message=b'upstream backlog')
                    break
            elif msg.type == WSMsgType.BINARY:
                try:
                    browser_to_upstream.put_nowait((WSMsgType.BINARY, msg.data))
                except asyncio.QueueFull:
                    log.warning("WS browser binary queue full; closing browser socket for clean reconnect")
                    await ws_server.close(code=1013, message=b'upstream backlog')
                    break
            elif msg.type in (WSMsgType.PING, WSMsgType.PONG):
                # autoping=True on ws_server already handled these.
                pass
            elif msg.type == WSMsgType.CLOSE:
                log.info("WS browser CLOSE code=%s", ws_server.close_code)
                break
            elif msg.type == WSMsgType.ERROR:
                log.warning("WS browser error: %s", ws_server.exception())
                break
        browser_closed.set()

    async def browser_keepalive():
        """Periodically ping the browser to prevent idle disconnects.

        Browsers (especially background tabs) do not send frames on their own,
        so without this the proxy→browser leg silently dies after the
        OS/browser idle timeout (~60–120 s).
        """
        while not ws_server.closed and not browser_closed.is_set():
            await asyncio.sleep(BROWSER_PING_INTERVAL)
            if ws_server.closed or browser_closed.is_set():
                break
            try:
                await ws_server.ping()
            except Exception:
                browser_closed.set()
                break

    browser_reader_task = asyncio.create_task(browser_reader())
    browser_keepalive_task = asyncio.create_task(browser_keepalive())

    try:
        async with ClientSession(timeout=_no_timeout) as session:
            reconnect_delay = 1
            while not ws_server.closed and not browser_closed.is_set():
                try:
                    # autoping=True: aiohttp automatically PONGs Odoo's PINGs
                    # immediately, so Odoo's 15-second PONG-wait never fires.
                    async with session.ws_connect(
                        target,
                        headers=upstream_headers,
                        autoclose=False,
                        autoping=True,          # key fix: proxy PONGs Odoo instantly
                        heartbeat=30,           # also send keep-alive PINGs upstream
                    ) as ws_client:
                        log.info("WS upstream connected → %s", target)
                        reconnect_delay = 1

                        if latest_subscribe_frame:
                            # If Odoo/gevent drops while the browser tab stays
                            # open, replay the last bus subscription on the new
                            # upstream socket. This avoids waiting for logout/login.
                            await ws_client.send_str(latest_subscribe_frame)
                            log.info("WS replayed cached subscribe after upstream reconnect")

                        async def upstream_to_browser():
                            """Forward data/control frames from Odoo → browser."""
                            async for msg in ws_client:
                                if msg.type == WSMsgType.TEXT:
                                    await ws_server.send_str(msg.data)
                                elif msg.type == WSMsgType.BINARY:
                                    await ws_server.send_bytes(msg.data)
                                elif msg.type in (WSMsgType.PING, WSMsgType.PONG):
                                    # autoping=True already handled these on ws_client.
                                    pass
                                elif msg.type == WSMsgType.CLOSE:
                                    log.info("WS upstream CLOSE code=%s", ws_client.close_code)
                                    return ws_client.close_code or 1000
                                elif msg.type == WSMsgType.ERROR:
                                    log.warning("WS upstream error: %s", ws_client.exception())
                                    return ws_client.close_code or 1006
                            return ws_client.close_code or 1006

                        async def upstream_writer():
                            """Forward queued browser frames to the active Odoo socket."""
                            while not browser_closed.is_set() and not ws_client.closed:
                                msg_type, data = await browser_to_upstream.get()
                                if msg_type == WSMsgType.TEXT:
                                    await ws_client.send_str(data)
                                elif msg_type == WSMsgType.BINARY:
                                    await ws_client.send_bytes(data)

                        reader_task = asyncio.create_task(upstream_to_browser())
                        writer_task = asyncio.create_task(upstream_writer())
                        browser_wait_task = asyncio.create_task(browser_closed.wait())
                        done, pending = await asyncio.wait(
                            {reader_task, writer_task, browser_wait_task},
                            return_when=asyncio.FIRST_COMPLETED,
                        )
                        for task in pending:
                            task.cancel()

                        if browser_wait_task in done:
                            await ws_client.close(code=ws_server.close_code or 1000)
                            break

                        close_code = None
                        if reader_task in done and not reader_task.cancelled():
                            close_code = reader_task.result()
                        elif writer_task in done and writer_task.exception():
                            log.warning("WS upstream writer error: %s", writer_task.exception())

                        # 4001 is auth/session-expired: the browser must refresh
                        # its Odoo session bridge with the JWT, so forward it.
                        if close_code == 4001:
                            await ws_server.close(code=4001)
                            break

                        # Any other upstream close is treated as transient. Keep
                        # the browser socket alive and reconnect upstream.
                        log.info(
                            "WS upstream disconnected code=%s; reconnecting in %ss",
                            close_code, reconnect_delay,
                        )
                except Exception as exc:
                    log.warning("WS upstream connect/bridge error: %s", exc)

                if not ws_server.closed and not browser_closed.is_set():
                    await asyncio.sleep(reconnect_delay)
                    reconnect_delay = min(reconnect_delay * 2, 15)
    except Exception as exc:
        log.warning("WS proxy error: %s", exc)
    finally:
        for task in (browser_reader_task, browser_keepalive_task):
            task.cancel()
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
# TODO: remove - cherry-pick marker
