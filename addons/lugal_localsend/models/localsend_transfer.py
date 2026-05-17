# -*- coding: utf-8 -*-
import base64
import json
import logging
import mimetypes
import ssl
import uuid
from urllib import error, parse, request as urlrequest

from odoo import fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


def _localsend_ssl_context():
    """LocalSend often uses HTTPS with a LAN self-signed certificate."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def _localsend_urlopen(request_obj, timeout, protocol):
    if (protocol or "http") == "https":
        return urlrequest.urlopen(request_obj, timeout=timeout, context=_localsend_ssl_context())
    return urlrequest.urlopen(request_obj, timeout=timeout)


class LugalLocalSendTransfer(models.Model):
    _name = "lugal.localsend.transfer"
    _description = "LocalSend Transfer Session"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    name = fields.Char(required=True, tracking=True, default="New Transfer")
    source_user_id = fields.Many2one(
        "res.users",
        string="Sender",
        required=True,
        default=lambda self: self.env.user,
        tracking=True,
    )
    target_user_id = fields.Many2one("res.users", string="Receiver", tracking=True)
    source_device_id = fields.Many2one(
        "lugal.localsend.device",
        string="Source Device",
        required=True,
        tracking=True,
    )
    target_device_id = fields.Many2one(
        "lugal.localsend.device",
        string="Target Device",
        required=True,
        tracking=True,
    )
    attachment_id = fields.Many2one("ir.attachment", string="Attachment", required=True)
    file_size = fields.Integer(related="attachment_id.file_size", store=True)
    mime_type = fields.Char(related="attachment_id.mimetype", store=True)
    status = fields.Selection(
        [
            ("draft",     "Draft"),
            ("queued",    "Queued – Awaiting Receiver"),
            ("sending",   "Sending via LocalSend"),
            ("sent",      "Sent via LocalSend"),
            ("available", "Available for Download"),
            ("downloaded","Downloaded"),
            ("failed",    "Failed"),
            ("cancelled", "Cancelled"),
        ],
        default="draft",
        required=True,
        tracking=True,
    )
    started_at = fields.Datetime(tracking=True)
    finished_at = fields.Datetime(tracking=True)
    error_message = fields.Text()
    localsend_session_id = fields.Char(readonly=True)

    def action_queue(self):
        self.write({"status": "queued"})

    def action_send_now(self):
        for rec in self:
            rec._send_via_localsend()
        return True

    def action_mark_sent(self):
        self.write({"status": "sent", "finished_at": fields.Datetime.now()})

    def action_mark_failed(self):
        self.write({"status": "failed", "finished_at": fields.Datetime.now()})

    def action_cancel(self):
        self.write({"status": "cancelled", "finished_at": fields.Datetime.now()})

    # ──────────────────────────────────────────────────────────────────────────
    # Download URL helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _download_url(self):
        """
        Return the Odoo download URL for this transfer's attachment.
        The browser can download the file directly via this URL without
        requiring LocalSend to be installed.
        """
        if not self.attachment_id:
            return ""
        return "/web/content/%d?download=true" % self.attachment_id.id

    def _preview_url(self):
        """Inline view URL (no download=true, good for images/PDFs in-browser)."""
        if not self.attachment_id:
            return ""
        return "/web/content/%d" % self.attachment_id.id

    # ──────────────────────────────────────────────────────────────────────────
    # Bus notifications
    # ──────────────────────────────────────────────────────────────────────────

    def _notify_via_bus(self, event_type: str, extra: dict = None):
        """
        Push a real-time notification to both sender and receiver.

        FE subscription channel:  localsend_user.<uid>
        Events emitted:
          localsend.transfer.available  — file ready to download from Odoo
          localsend.transfer.sent       — file delivered via LocalSend
          localsend.transfer.failed     — unrecoverable failure
          localsend.transfer.queued     — queued for retry when LocalSend opens
          localsend.transfer.downloaded — receiver confirmed download
          localsend.transfer.cancelled  — transfer cancelled

        Every payload always includes download_url so the FE can provide a
        fallback download button even when LocalSend is unavailable.
        """
        payload = {
            "transfer_id":    self.id,
            "name":           self.name or "",
            "status":         self.status,
            "source_user_id": self.source_user_id.id if self.source_user_id else None,
            "source_user_name": self.source_user_id.name if self.source_user_id else "",
            "target_user_id": self.target_user_id.id if self.target_user_id else None,
            "target_user_name": self.target_user_id.name if self.target_user_id else "",
            "file_name":      self.attachment_id.name if self.attachment_id else "",
            "file_size":      self.file_size or 0,
            "mime_type":      self.mime_type or "",
            "download_url":   self._download_url(),
            "preview_url":    self._preview_url(),
            "error_message":  self.error_message or "",
            **(extra or {}),
        }
        Bus = self.env["bus.bus"].sudo()
        for uid in {self.source_user_id.id, self.target_user_id.id} - {False, None}:
            try:
                Bus._sendone("localsend_user.%d" % uid, event_type, payload)
            except Exception as exc:
                _logger.debug("localsend bus notify failed uid=%s: %s", uid, exc)

    # ──────────────────────────────────────────────────────────────────────────
    # Connectivity check
    # ──────────────────────────────────────────────────────────────────────────

    def _preflight_device_check(self, device, timeout=5):
        """
        Quick TCP-level reachability probe before the full LocalSend handshake.
        Returns (ok: bool, error_msg: str | None).
        """
        import socket
        ip   = device.ip_address or ""
        port = int(device.port or 53317)
        if not ip:
            return False, "Device has no IP address stored."
        try:
            with socket.create_connection((ip, port), timeout=timeout):
                pass
            return True, None
        except ConnectionRefusedError:
            return False, (
                "LocalSend app is not running on %s (%s:%s). "
                "The file is available for download from the app."
                % (device.name or "device", ip, port)
            )
        except OSError as exc:
            return False, (
                "Cannot reach %s (%s:%s): %s"
                % (device.name or "device", ip, port, exc)
            )

    # ──────────────────────────────────────────────────────────────────────────
    # Send via LocalSend (optional fast-path)
    # ──────────────────────────────────────────────────────────────────────────

    def _send_via_localsend(self):
        """
        Attempt to push the file directly to the target device via LocalSend v2.

        If LocalSend is not reachable the transfer is set to 'queued' (NOT failed)
        and a bus notification is sent with a download_url so the receiver can
        still get the file from the browser.  The transfer will be retried
        automatically when the target device next calls /devices/heartbeat.
        """
        self.ensure_one()
        if not self.attachment_id or not self.target_device_id:
            raise UserError("Attachment and target device are required.")
        if not self.attachment_id.datas:
            raise UserError("Attachment has no binary data.")

        # Pre-flight: if target device is not reachable, fall back gracefully.
        reachable, preflight_err = self._preflight_device_check(self.target_device_id)
        if not reachable:
            self.write({
                "status": "queued",       # NOT failed — file still downloadable
                "error_message": preflight_err,
            })
            # Notify receiver: file is available for download + queued for retry
            self._notify_via_bus(
                "localsend.transfer.available",
                {
                    "delivery_method": "download",
                    "message": (
                        "%s sent you '%s'. Download it now or it will be "
                        "delivered automatically when LocalSend is opened."
                    ) % (
                        self.source_user_id.name or "Someone",
                        self.attachment_id.name or "a file",
                    ),
                },
            )
            # No exception raised — this is a graceful fallback, not an error.
            return

        self.write({"status": "sending", "started_at": fields.Datetime.now(), "error_message": False})

        file_id = uuid.uuid4().hex
        file_name = self.attachment_id.name or "upload.bin"
        mime = self.attachment_id.mimetype or mimetypes.guess_type(file_name)[0] or "application/octet-stream"
        binary_data = base64.b64decode(self.attachment_id.datas)
        file_size = len(binary_data)

        info = {
            "alias": self.source_device_id.name or self.source_user_id.name or "Odoo",
            "version": "2.1",
            "deviceModel": "Odoo",
            "deviceType": "server",
            "fingerprint": self.source_device_id.device_uid or "odoo-localsend-bridge",
            "port": int(self.source_device_id.port or 53317),
            "protocol": self.source_device_id.protocol or "http",
            "download": False,
        }
        prepare_payload = {
            "info": info,
            "files": {
                file_id: {
                    "id": file_id,
                    "fileName": file_name,
                    "size": file_size,
                    "fileType": mime,
                    "sha256": None,
                    "preview": None,
                }
            },
        }

        target_proto = self.target_device_id.protocol or "http"
        target_ip    = self.target_device_id.ip_address
        target_port  = self.target_device_id.port or 53317
        base_url = "%s://%s:%s/api/localsend/v2" % (target_proto, target_ip, target_port)
        pin = (self.target_device_id.pin_code or "").strip() if self.target_device_id.require_pin else ""
        prepare_url = base_url + "/prepare-upload"
        if pin:
            prepare_url += "?" + parse.urlencode({"pin": pin})

        try:
            prepare_req = urlrequest.Request(
                prepare_url,
                data=json.dumps(prepare_payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with _localsend_urlopen(prepare_req, 30, target_proto) as resp:
                if resp.status == 204:
                    raise UserError(
                        "LocalSend returned 204 — receiver declined or finished."
                    )
                prepare_resp_raw = resp.read().decode("utf-8") or "{}"
            prepare_resp = json.loads(prepare_resp_raw)
            session_id = prepare_resp.get("sessionId")
            file_token = (prepare_resp.get("files") or {}).get(file_id)
            if not session_id or not file_token:
                raise UserError("LocalSend prepare-upload did not return sessionId/token.")

            upload_query = parse.urlencode(
                {"sessionId": session_id, "fileId": file_id, "token": file_token}
            )
            upload_req = urlrequest.Request(
                base_url + "/upload?" + upload_query,
                data=binary_data,
                headers={"Content-Type": mime},
                method="POST",
            )
            with _localsend_urlopen(upload_req, 120, target_proto):
                pass

            self.write({
                "status": "sent",
                "localsend_session_id": session_id,
                "finished_at": fields.Datetime.now(),
                "error_message": False,
            })
            self._notify_via_bus(
                "localsend.transfer.sent",
                {"delivery_method": "localsend"},
            )
        except error.HTTPError as exc:
            body = ""
            try:
                body = exc.read().decode("utf-8")
            except Exception:
                body = ""
            msg = "LocalSend HTTP %s at %s — %s" % (exc.code, prepare_url, body or exc.reason)
            _logger.warning("localsend transfer %s failed: %s", self.id, msg)
            self.write({"status": "queued", "error_message": msg})
            self._notify_via_bus(
                "localsend.transfer.available",
                {"delivery_method": "download", "error_message": msg},
            )
        except UserError:
            raise
        except Exception as exc:
            msg = "LocalSend push to %s (%s:%s) failed: %s" % (
                self.target_device_id.name or "device", target_ip, target_port, exc
            )
            _logger.exception("localsend transfer %s failed", self.id)
            self.write({"status": "queued", "error_message": msg})
            self._notify_via_bus(
                "localsend.transfer.available",
                {"delivery_method": "download", "error_message": msg},
            )
