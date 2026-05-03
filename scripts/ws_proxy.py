#!/usr/bin/env python3
"""
Lugal WebSocket Reverse Proxy
==============================
Listens on PROXY_PORT and routes:
  • /websocket  →  GEVENT_PORT (8072)  — WebSocket upgrade
  • everything  →  ODOO_PORT   (8069)  — normal HTTP

Run:
    python3 scripts/ws_proxy.py

Service is registered as a systemd user unit (lugal-proxy.service).
"""

import asyncio
import aiohttp
from aiohttp import web, ClientSession, WSMsgType
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("ws_proxy")

PROXY_PORT  = 3003
ODOO_HOST   = "http://127.0.0.1:8069"
GEVENT_HOST = "http://127.0.0.1:8072"

SKIP_HEADERS = {"host", "content-length", "transfer-encoding", "connection",
                "keep-alive", "te", "trailers", "upgrade"}


async def proxy_websocket(request: web.Request) -> web.WebSocketResponse:
    """Upgrade to WebSocket and bridge to gevent worker on 8072."""
    ws_server = web.WebSocketResponse(autoping=False)
    await ws_server.prepare(request)

    qs = "?" + request.query_string if request.query_string else ""
    target = GEVENT_HOST.replace("http://", "ws://") + request.path + qs

    upstream_headers = {k: v for k, v in request.headers.items()
                        if k.lower() not in {"host", "sec-websocket-key",
                                             "sec-websocket-extensions"}}
    upstream_headers["Host"] = "127.0.0.1:8072"
    upstream_headers["Origin"] = f"http://127.0.0.1:{PROXY_PORT}"

    log.info("WS  %s → %s", request.path + qs, target)

    try:
        async with ClientSession() as session:
            async with session.ws_connect(target, headers=upstream_headers,
                                          autoclose=False, autoping=False) as ws_client:

                async def forward_to_client():
                    """Forward frames from gevent (upstream) → browser (downstream)."""
                    async for msg in ws_client:
                        if msg.type == WSMsgType.TEXT:
                            await ws_server.send_str(msg.data)
                        elif msg.type == WSMsgType.BINARY:
                            await ws_server.send_bytes(msg.data)
                        elif msg.type == WSMsgType.PING:
                            await ws_server.ping(msg.data)
                        elif msg.type == WSMsgType.PONG:
                            await ws_server.pong(msg.data)
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
                    """Forward frames from browser (downstream) → gevent (upstream)."""
                    async for msg in ws_server:
                        if msg.type == WSMsgType.TEXT:
                            await ws_client.send_str(msg.data)
                        elif msg.type == WSMsgType.BINARY:
                            await ws_client.send_bytes(msg.data)
                        elif msg.type == WSMsgType.PING:
                            await ws_client.ping(msg.data)
                        elif msg.type == WSMsgType.PONG:
                            await ws_client.pong(msg.data)
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

                await asyncio.gather(
                    forward_to_client(),
                    forward_to_server(),
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
    headers["Host"] = "127.0.0.1:8069"
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

    log.info("Lugal Proxy starting on :%d (max body: 1 GB)", PROXY_PORT)
    log.info("  HTTP  → %s", ODOO_HOST)
    log.info("  WS    → %s", GEVENT_HOST.replace("http://", "ws://"))

    web.run_app(app, host="0.0.0.0", port=PROXY_PORT, access_log=None)


if __name__ == "__main__":
    main()
