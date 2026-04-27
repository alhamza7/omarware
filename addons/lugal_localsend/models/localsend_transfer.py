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
            ("draft", "Draft"),
            ("queued", "Queued"),
            ("sending", "Sending"),
            ("sent", "Sent"),
            ("failed", "Failed"),
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

    def _send_via_localsend(self):
        self.ensure_one()
        if not self.attachment_id or not self.target_device_id:
            raise UserError("Attachment and target device are required.")
        if not self.attachment_id.datas:
            raise UserError("Attachment has no binary data.")

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
        base_url = "%s://%s:%s/api/localsend/v2" % (
            target_proto,
            self.target_device_id.ip_address,
            self.target_device_id.port or 53317,
        )
        # PIN is disabled for direct transfers — require_pin is always False
        # for auto-registered devices.  Manual devices that still have require_pin
        # set will use the stored pin_code.
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
                        "LocalSend returned 204 (no transfer / finished). "
                        "Check receiver accepts files and PIN if enabled."
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

            self.write(
                {
                    "status": "sent",
                    "localsend_session_id": session_id,
                    "finished_at": fields.Datetime.now(),
                    "error_message": False,
                }
            )
        except error.HTTPError as exc:
            body = ""
            try:
                body = exc.read().decode("utf-8")
            except Exception:
                body = ""
            msg = "LocalSend HTTP error %s %s" % (exc.code, body or exc.reason)
            _logger.warning("localsend transfer %s failed: %s", self.id, msg)
            self.write({"status": "failed", "finished_at": fields.Datetime.now(), "error_message": msg})
            raise UserError(msg)
        except Exception as exc:
            msg = "LocalSend transfer failed: %s" % exc
            _logger.exception("localsend transfer %s failed", self.id)
            self.write({"status": "failed", "finished_at": fields.Datetime.now(), "error_message": msg})
            raise UserError(msg)
