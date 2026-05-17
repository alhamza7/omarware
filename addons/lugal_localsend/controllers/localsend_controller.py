# -*- coding: utf-8 -*-
import logging

from odoo import fields, http
from odoo.http import request

from odoo.addons.lugal_auth.controllers._auth import ensure_jwt_user_id

_logger = logging.getLogger(__name__)

_DEFAULT_PORT = 53317


def _is_localsend_manager(env):
    return env.user.has_group("lugal_localsend.group_lugal_localsend_manager")


def _caller_ip():
    """Return the real client IP, honouring X-Forwarded-For if behind a proxy."""
    xff = request.httprequest.headers.get("X-Forwarded-For") or ""
    if xff:
        return xff.split(",")[0].strip()
    return request.httprequest.remote_addr or ""


def _looks_like_ip(value):
    if not value or " " in value or len(value) > 45:
        return False
    return ("." in value) or (":" in value)


def _effective_lan_ip(**kwargs):
    """Prefer LAN IP from the client (LocalSend / desktop wrapper); else HTTP IP."""
    for key in ("lan_ip", "local_ip", "network_ip", "ip_address"):
        raw = (kwargs.get(key) or "").strip()
        if raw and _looks_like_ip(raw):
            return raw
    return _caller_ip()


def _resolve_sender_device(env, user_id):
    return env["lugal.localsend.device"].sudo().search(
        [("user_id", "=", user_id), ("active", "=", True)],
        order="is_online desc, last_seen desc, id desc",
        limit=1,
    )


def _resolve_receiver_device(env, target_user_id, target_device_id=None):
    Device = env["lugal.localsend.device"].sudo()
    if target_device_id:
        d = Device.browse(int(target_device_id)).exists()
        if not d or not d.user_id or d.user_id.id != int(target_user_id):
            return Device.browse(), "target_device_id does not match target_user_id"
        return d, None
    rows = Device.search(
        [("user_id", "=", int(target_user_id)), ("active", "=", True)],
        order="is_online desc, last_seen desc, id desc",
        limit=1,
    )
    if not rows:
        return Device.browse(), "Target user has no registered device."
    return rows, None


def _serialize_device(device):
    return {
        "id": device.id,
        "name": device.name or "",
        "device_uid": device.device_uid or "",
        "ip_address": device.ip_address or "",
        "port": int(device.port or _DEFAULT_PORT),
        "protocol": device.protocol or "http",
        "require_pin": bool(device.require_pin),
        "owner_user_id": device.user_id.id if device.user_id else None,
        "owner_name": device.user_id.name if device.user_id else "",
        "is_online": bool(device.is_online),
        "last_seen": device.last_seen.isoformat() if device.last_seen else "",
    }


def _device_connection(device):
    """Return the P2P connection info the frontend needs to start a direct transfer."""
    ip = device.ip_address or ""
    port = int(device.port or _DEFAULT_PORT)
    proto = device.protocol or "http"
    return {
        "device": _serialize_device(device),
        "localsend_url": "%s://%s:%s" % (proto, ip, port),
        "prepare_upload_url": "%s://%s:%s/api/localsend/v2/prepare-upload" % (proto, ip, port),
        "upload_url": "%s://%s:%s/api/localsend/v2/upload" % (proto, ip, port),
    }


class LocalSendCrmController(http.Controller):

    # ------------------------------------------------------------------
    # Register / heartbeat
    # ------------------------------------------------------------------

    @http.route(
        "/api/crm/localsend/devices/register",
        type="jsonrpc",
        auth="none",
        csrf=False,
        methods=["POST"],
    )
    def localsend_device_register(self, **kwargs):
        """Register this user's machine (store its LAN IP + port for discovery).

        Auth is JWT only.  IP is taken from ``lan_ip`` / ``ip_address`` when
        the client sends the real LAN address; otherwise falls back to the HTTP
        connection IP.
        """
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {"success": False, "error": "Unauthorized", "data": None}

            ip = _effective_lan_ip(**kwargs)
            if not ip:
                return {"success": False, "error": "Could not determine device IP", "data": None}

            port = int(kwargs.get("port") or _DEFAULT_PORT)
            protocol = (kwargs.get("protocol") or "http").strip().lower()
            device_name = (kwargs.get("device_name") or "").strip()
            device_uid = (kwargs.get("device_uid") or "").strip() or False

            user = request.env["res.users"].sudo().browse(uid)
            if not device_name:
                device_name = "%s's Device" % (user.name or "User")

            Device = request.env["lugal.localsend.device"].sudo()
            existing = Device.search([("user_id", "=", uid), ("ip_address", "=", ip)], limit=1)

            now = fields.Datetime.now()
            if existing:
                existing.write({
                    "name": device_name,
                    "port": port,
                    "protocol": protocol,
                    "is_online": True,
                    "last_seen": now,
                    "require_pin": False,
                    "pin_code": False,
                    **({"device_uid": device_uid} if device_uid else {}),
                })
                rec = existing
            else:
                any_device = Device.search([("user_id", "=", uid)], limit=1)
                if any_device:
                    any_device.write({
                        "name": device_name,
                        "ip_address": ip,
                        "port": port,
                        "protocol": protocol,
                        "is_online": True,
                        "last_seen": now,
                        "require_pin": False,
                        "pin_code": False,
                        **({"device_uid": device_uid} if device_uid else {}),
                    })
                    rec = any_device
                else:
                    rec = Device.create({
                        "name": device_name,
                        "ip_address": ip,
                        "port": port,
                        "protocol": protocol,
                        "user_id": uid,
                        "is_online": True,
                        "last_seen": now,
                        "require_pin": False,
                        "pin_code": False,
                        **({"device_uid": device_uid} if device_uid else {}),
                    })

            return {"success": True, "data": _serialize_device(rec)}
        except Exception as exc:
            _logger.exception("localsend_device_register failed")
            return {"success": False, "error": str(exc), "data": None}

    @http.route(
        "/api/crm/localsend/devices/heartbeat",
        type="jsonrpc",
        auth="none",
        csrf=False,
        methods=["POST"],
    )
    def localsend_device_heartbeat(self, **kwargs):
        """Lightweight keep-alive. Call every ~30 s to stay marked as online."""
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {"success": False, "error": "Unauthorized", "data": None}

            ip = _effective_lan_ip(**kwargs)
            device = _resolve_sender_device(request.env, uid)
            if device:
                vals = {"is_online": True, "last_seen": fields.Datetime.now()}
                if ip and device.ip_address != ip:
                    vals["ip_address"] = ip
                device.write(vals)
                return {"success": True, "data": _serialize_device(device)}
            return {"success": False, "error": "No device registered for this user", "data": None}
        except Exception as exc:
            _logger.exception("localsend_device_heartbeat failed")
            return {"success": False, "error": str(exc), "data": None}

    # ------------------------------------------------------------------
    # Device discovery
    # ------------------------------------------------------------------

    @http.route(
        "/api/crm/localsend/devices/list",
        type="jsonrpc",
        auth="none",
        csrf=False,
        methods=["POST"],
    )
    def localsend_devices_list(self, **kwargs):
        """List registered devices.

        Optional filters:
        - ``owner_only`` — only current user's devices
        - ``online_only`` — only devices currently marked as online
        """
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {"success": False, "error": "Unauthorized", "data": None}

            domain = [("active", "=", True)]
            if kwargs.get("owner_only") in (True, "true", "1", 1):
                domain.append(("user_id", "=", uid))
            if kwargs.get("online_only") in (True, "true", "1", 1):
                domain.append(("is_online", "=", True))

            rows = request.env["lugal.localsend.device"].sudo().search(domain, order="name asc")
            return {
                "success": True,
                "data": {"total": len(rows), "items": [_serialize_device(r) for r in rows]},
            }
        except Exception as exc:
            _logger.exception("localsend_devices_list failed")
            return {"success": False, "error": str(exc), "data": None}

    @http.route(
        "/api/crm/localsend/resolve",
        type="jsonrpc",
        auth="none",
        csrf=False,
        methods=["POST"],
    )
    def localsend_resolve(self, **kwargs):
        """Return connection info for a target user's device.

        The frontend uses ``localsend_url`` / ``prepare_upload_url`` / ``upload_url``
        to initiate the LocalSend v2 protocol **directly** from the browser to the
        target device — the Odoo server is NOT involved in the actual file transfer.

        Required: ``target_user_id``
        Optional: ``target_device_id`` (when the user has multiple devices)
        """
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {"success": False, "error": "Unauthorized", "data": None}

            target_user_id = int(kwargs.get("target_user_id") or 0)
            if not target_user_id:
                return {"success": False, "error": "target_user_id is required", "data": None}

            tid = int(kwargs.get("target_device_id") or 0) or None
            target_device, err = _resolve_receiver_device(request.env, target_user_id, tid)
            if not target_device:
                return {"success": False, "error": err or "Target device not found or offline", "data": None}

            sender_device = _resolve_sender_device(request.env, uid)

            return {
                "success": True,
                "data": {
                    **_device_connection(target_device),
                    "sender_device": _serialize_device(sender_device) if sender_device else None,
                },
            }
        except Exception as exc:
            _logger.exception("localsend_resolve failed")
            return {"success": False, "error": str(exc), "data": None}

    # ------------------------------------------------------------------
    # Manual device management (manager use / backward compat)
    # ------------------------------------------------------------------

    @http.route(
        "/api/crm/localsend/devices/create",
        type="jsonrpc",
        auth="none",
        csrf=False,
        methods=["POST"],
    )
    def localsend_device_create(self, **kwargs):
        """Manual device creation (manager use / backward compatibility)."""
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {"success": False, "error": "Unauthorized", "data": None}

            name = (kwargs.get("name") or "").strip()
            ip_address = (kwargs.get("ip_address") or "").strip()
            if not name or not ip_address:
                return {"success": False, "error": "name and ip_address are required", "data": None}

            owner_uid = int(kwargs.get("user_id") or uid)
            if owner_uid != uid and not _is_localsend_manager(request.env):
                return {
                    "success": False,
                    "error": "Forbidden: only managers can assign devices to other users",
                    "data": None,
                }

            vals = {
                "name": name,
                "device_uid": (kwargs.get("device_uid") or "").strip() or False,
                "protocol": (kwargs.get("protocol") or "http").strip().lower(),
                "ip_address": ip_address,
                "port": int(kwargs.get("port") or _DEFAULT_PORT),
                "user_id": owner_uid,
                "is_online": bool(kwargs.get("is_online", False)),
                "require_pin": bool(kwargs.get("require_pin", False)),
                "pin_code": (kwargs.get("pin_code") or "").strip() or False,
                "note": kwargs.get("note") or "",
            }
            rec = request.env["lugal.localsend.device"].sudo().create(vals)
            return {"success": True, "data": _serialize_device(rec)}
        except Exception as exc:
            _logger.exception("localsend_device_create failed")
            return {"success": False, "error": str(exc), "data": None}

    # ------------------------------------------------------------------
    # Transfers
    # ------------------------------------------------------------------

    def _serialize_transfer(self, t):
        return {
            "id":                   t.id,
            "name":                 t.name or "",
            "status":               t.status,
            "source_user_id":       t.source_user_id.id if t.source_user_id else None,
            "source_user_name":     t.source_user_id.name if t.source_user_id else "",
            "target_user_id":       t.target_user_id.id if t.target_user_id else None,
            "target_user_name":     t.target_user_id.name if t.target_user_id else "",
            "source_device_id":     t.source_device_id.id if t.source_device_id else None,
            "source_device_name":   t.source_device_id.name if t.source_device_id else "",
            "target_device_id":     t.target_device_id.id if t.target_device_id else None,
            "target_device_name":   t.target_device_id.name if t.target_device_id else "",
            "attachment_id":        t.attachment_id.id if t.attachment_id else None,
            "file_name":            t.attachment_id.name if t.attachment_id else "",
            "file_size":            t.file_size or 0,
            "mime_type":            t.mime_type or "",
            "error_message":        t.error_message or "",
            "localsend_session_id": t.localsend_session_id or "",
            "started_at":           t.started_at.isoformat() if t.started_at else None,
            "finished_at":          t.finished_at.isoformat() if t.finished_at else None,
            "created_at":           t.create_date.isoformat() if t.create_date else None,
        }

    @http.route(
        "/api/crm/localsend/transfers/create",
        type="jsonrpc",
        auth="none",
        csrf=False,
        methods=["POST"],
    )
    def localsend_transfer_create(self, **kwargs):
        """Create a LocalSend transfer record and optionally trigger sending immediately.

        Required params:
          target_user_id   — recipient user ID
          attachment_id    — ir.attachment ID of the file to send

        Optional params:
          target_device_id — specific device ID for the recipient (auto-resolved if omitted)
          name             — human-readable label for the transfer
          send_now         — true/false (default true) — trigger the send immediately
        """
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {"success": False, "error": "Unauthorized", "data": None}

            target_user_id = int(kwargs.get("target_user_id") or 0)
            attachment_id  = int(kwargs.get("attachment_id")  or 0)
            if not target_user_id:
                return {"success": False, "error": "target_user_id is required", "data": None}
            if not attachment_id:
                return {"success": False, "error": "attachment_id is required", "data": None}

            env = request.env

            # Resolve sender device
            sender_device = _resolve_sender_device(env, uid)
            if not sender_device:
                return {"success": False, "error": "Sender has no registered device. Call /devices/register first.", "data": None}

            # Resolve target device
            tid = int(kwargs.get("target_device_id") or 0) or None
            target_device, err = _resolve_receiver_device(env, target_user_id, tid)
            if not target_device:
                return {"success": False, "error": err or "Target device not found", "data": None}

            # Verify attachment belongs to caller (or caller is manager)
            att = env["ir.attachment"].sudo().browse(attachment_id).exists()
            if not att:
                return {"success": False, "error": "Attachment not found", "data": None}

            transfer_name = (kwargs.get("name") or "").strip() or (att.name or "File Transfer")

            transfer = env["lugal.localsend.transfer"].sudo().create({
                "name":             transfer_name,
                "source_user_id":   uid,
                "target_user_id":   target_user_id,
                "source_device_id": sender_device.id,
                "target_device_id": target_device.id,
                "attachment_id":    attachment_id,
                "status":           "draft",
            })

            send_now = str(kwargs.get("send_now", "true")).lower() not in ("false", "0", "no")
            if send_now:
                try:
                    transfer._send_via_localsend()
                except Exception as send_exc:
                    # Transfer record is already updated to failed by _send_via_localsend
                    _logger.warning("localsend_transfer_create: send failed: %s", send_exc)
                    return {
                        "success": False,
                        "error": str(send_exc),
                        "data": self._serialize_transfer(transfer),
                    }

            return {"success": True, "data": self._serialize_transfer(transfer)}
        except Exception as exc:
            _logger.exception("localsend_transfer_create failed")
            return {"success": False, "error": str(exc), "data": None}

    @http.route(
        "/api/crm/localsend/transfers/list",
        type="jsonrpc",
        auth="none",
        csrf=False,
        methods=["POST"],
    )
    def localsend_transfers_list(self, **kwargs):
        """List transfers for the current user (sent and received).

        Optional params:
          direction  — 'sent' | 'received' | 'all' (default 'all')
          status     — filter by status (draft/queued/sending/sent/failed/cancelled)
          limit      — max records (default 50)
          offset     — skip N records (default 0)
        """
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {"success": False, "error": "Unauthorized", "data": None}

            direction = (kwargs.get("direction") or "all").strip().lower()
            status    = (kwargs.get("status")    or "").strip()
            limit     = max(1, int(kwargs.get("limit")  or 50))
            offset    = max(0, int(kwargs.get("offset") or 0))

            if direction == "sent":
                domain = [("source_user_id", "=", uid)]
            elif direction == "received":
                domain = [("target_user_id", "=", uid)]
            else:
                domain = ["|", ("source_user_id", "=", uid), ("target_user_id", "=", uid)]

            if status:
                domain.append(("status", "=", status))

            Transfer = request.env["lugal.localsend.transfer"].sudo()
            total = Transfer.search_count(domain)
            rows  = Transfer.search(domain, limit=limit, offset=offset, order="create_date desc")

            return {
                "success": True,
                "data": {
                    "total":  total,
                    "limit":  limit,
                    "offset": offset,
                    "items":  [self._serialize_transfer(t) for t in rows],
                },
            }
        except Exception as exc:
            _logger.exception("localsend_transfers_list failed")
            return {"success": False, "error": str(exc), "data": None}

    @http.route(
        "/api/crm/localsend/transfers/<int:transfer_id>/send",
        type="jsonrpc",
        auth="none",
        csrf=False,
        methods=["POST"],
    )
    def localsend_transfer_send(self, transfer_id, **kwargs):
        """Trigger (or re-trigger) the actual LocalSend file push for an existing transfer."""
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {"success": False, "error": "Unauthorized", "data": None}

            t = request.env["lugal.localsend.transfer"].sudo().browse(transfer_id).exists()
            if not t:
                return {"success": False, "error": "Transfer not found", "data": None}
            if t.source_user_id.id != uid and not _is_localsend_manager(request.env):
                return {"success": False, "error": "Forbidden", "data": None}

            try:
                t._send_via_localsend()
            except Exception as send_exc:
                return {"success": False, "error": str(send_exc), "data": self._serialize_transfer(t)}

            return {"success": True, "data": self._serialize_transfer(t)}
        except Exception as exc:
            _logger.exception("localsend_transfer_send failed")
            return {"success": False, "error": str(exc), "data": None}

    @http.route(
        "/api/crm/localsend/transfers/<int:transfer_id>/cancel",
        type="jsonrpc",
        auth="none",
        csrf=False,
        methods=["POST"],
    )
    def localsend_transfer_cancel(self, transfer_id, **kwargs):
        """Cancel a pending/queued transfer."""
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {"success": False, "error": "Unauthorized", "data": None}

            t = request.env["lugal.localsend.transfer"].sudo().browse(transfer_id).exists()
            if not t:
                return {"success": False, "error": "Transfer not found", "data": None}
            if t.source_user_id.id != uid and not _is_localsend_manager(request.env):
                return {"success": False, "error": "Forbidden", "data": None}
            if t.status in ("sent", "cancelled"):
                return {"success": False, "error": f"Cannot cancel a transfer with status '{t.status}'", "data": None}

            t.action_cancel()
            return {"success": True, "data": self._serialize_transfer(t)}
        except Exception as exc:
            _logger.exception("localsend_transfer_cancel failed")
            return {"success": False, "error": str(exc), "data": None}
