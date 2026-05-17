#!/usr/bin/env python3
"""
patch_recipient_read_at.py

Fixes the bug where `recipient_read_at` on a sender's sent-folder message is
NEVER populated, even when an internal Lugal recipient marks the email as read.

Root cause
----------
1. `_propagate_read_to_sent_copies` in email_controller.py only writes
   `is_read` and `read_at` to the sender's sent copy. It never writes
   `recipient_read_at`. So the field stays null forever.

2. The same function filters its search on `is_read=False`. If the sent row
   already had `is_read=True` set by an unrelated path (IMAP \Seen sync,
   manual mark, etc.), the search returns empty and nothing is stamped —
   even though the recipient just genuinely read the email.

3. `crm_notifications_controller.py` `mark_read` for email writes
   `is_read=True` but never calls `_propagate_read_to_sent_copies`. So when
   the recipient hits "Mark all read" or dismisses the notification, the
   sender's sent copy never receives the recipient_read_at timestamp.

Fixes applied
-------------
- email_controller.py: rewrite `_propagate_read_to_sent_copies` to gate on
  `recipient_read_at IS NULL` instead of `is_read=False`, and to write
  `recipient_read_at` alongside `is_read`/`read_at`.

- crm_notifications_controller.py: import the propagation helper and call
  it inside `mark_read` for every email message that transitioned from
  unread to read in this request.

Usage
-----
    python3 patch_recipient_read_at.py \
        /home/lugalai/Lugal-ai/addons/lugal_email/controllers/email_controller.py \
        /home/lugalai/Lugal-ai/addons/lugal_crm/controllers/crm_notifications_controller.py

The script creates a .bak.<timestamp> backup next to each file and refuses
to write if the result fails AST parsing.
"""

import sys
import os
import ast
import shutil
from datetime import datetime


# ──────────────────────────────────────────────────────────────────────────
# email_controller.py — replace _propagate_read_to_sent_copies
# ──────────────────────────────────────────────────────────────────────────

EMAIL_CTRL_OLD = """def _propagate_read_to_sent_copies(env, message_id, read_at):
    \"\"\"
    When a recipient marks an inbox message as read, find the matching sent-folder
    copy (same RFC 2822 Message-ID) in any Lugal account and mark it read too.

    This is what drives is_read/read_at on *sent* messages — they track whether the
    recipient has read the message, not whether the sender opened their own copy.
    \"\"\"
    if not message_id:
        return
    try:
        sent_copies = env['lugal.email.message'].sudo().search([
            ('message_id', '=', message_id),
            ('is_read', '=', False),
            ('is_deleted', '=', False),
        ])
        sent_copies = sent_copies.filtered(lambda msg: _is_sent_folder(msg.folder))
        if sent_copies:
            sent_copies.with_context(lugal_recipient_read=True).write({
                'is_read': True,
                'read_at': read_at,
            })
            _logger.info(
                '_propagate_read_to_sent_copies: marked %d sent copy(s) read '
                'for message_id=%s', len(sent_copies), message_id,
            )
    except Exception as exc:
        _logger.warning(
            '_propagate_read_to_sent_copies failed message_id=%s: %s', message_id, exc,
        )"""

EMAIL_CTRL_NEW = """def _propagate_read_to_sent_copies(env, message_id, read_at):
    \"\"\"
    When a recipient marks an inbox message as read, find the matching sent-folder
    copy (same RFC 2822 Message-ID) in any Lugal account and stamp:

      - recipient_read_at  → exposed in the sent-folder API as the moment the
                             recipient actually opened the email
      - is_read = True     → clears the sender's sent-folder unread badge
      - read_at            → kept in sync for backward compatibility

    The search gate is `recipient_read_at IS NULL` (not `is_read=False`) so
    that we still stamp recipient_read_at even when is_read was set to True
    earlier by an unrelated path (IMAP \\\\Seen sync, manual mark, etc.).
    Without this, the sender's API always returned recipient_read_at=null
    even after the recipient genuinely read the message.
    \"\"\"
    if not message_id or not read_at:
        return
    try:
        sent_copies = env['lugal.email.message'].sudo().search([
            ('message_id', '=', message_id),
            ('is_deleted', '=', False),
            ('recipient_read_at', '=', False),
        ])
        sent_copies = sent_copies.filtered(lambda msg: _is_sent_folder(msg.folder))
        if sent_copies:
            sent_copies.with_context(lugal_recipient_read=True).write({
                'is_read': True,
                'read_at': read_at,
                'recipient_read_at': read_at,
            })
            _logger.info(
                '_propagate_read_to_sent_copies: stamped recipient_read_at on '
                '%d sent copy(s) for message_id=%s at %s',
                len(sent_copies), message_id, read_at,
            )
    except Exception as exc:
        _logger.warning(
            '_propagate_read_to_sent_copies failed message_id=%s: %s', message_id, exc,
        )"""


# ──────────────────────────────────────────────────────────────────────────
# crm_notifications_controller.py — add import + wire propagation in mark_read
# ──────────────────────────────────────────────────────────────────────────

NOTIF_CTRL_IMPORT_OLD = """from ._auth import ensure_jwt_user_id
from ._error import crm_error"""

NOTIF_CTRL_IMPORT_NEW = """from ._auth import ensure_jwt_user_id
from ._error import crm_error

# Used to stamp recipient_read_at on the sender's sent-folder copy when this
# user marks an email (or all emails) as read via the notifications endpoint.
from odoo.addons.lugal_email.controllers.email_controller import (
    _propagate_read_to_sent_copies,
)"""


NOTIF_CTRL_BLOCK_OLD = """                if msgs:
                    msgs.write({'is_read': True})
                    email_marked = len(msgs)
                    for acc in Acc.browse(acc_ids):
                        unread_count = EmailMsg.search_count([
                            ('account_id', '=', acc.id),
                            ('folder', 'not in', ['sent', 'drafts', 'trash', 'spam']),
                            ('is_read', '=', False),
                            ('is_deleted', '=', False),
                        ])
                        acc.write({'unread_count': unread_count})"""

NOTIF_CTRL_BLOCK_NEW = """                if msgs:
                    # Capture state BEFORE write so we know which rows actually
                    # transitioned unread → read on THIS call, and remember each
                    # one's RFC-2822 Message-ID for sent-copy propagation.
                    from odoo import fields as _odoo_fields
                    _newly_read = [
                        (m.id, m.message_id, m.read_at)
                        for m in msgs
                        if not m.is_read and m.message_id
                    ]
                    msgs.write({'is_read': True})
                    email_marked = len(msgs)
                    # Propagate the recipient-read timestamp to the senders'
                    # sent copies so /api/lugal/email/sync?folder=sent shows
                    # recipient_read_at correctly.
                    _now = _odoo_fields.Datetime.now()
                    for _mid, _msg_rfc_id, _prior_read_at in _newly_read:
                        try:
                            _propagate_read_to_sent_copies(
                                request.env,
                                _msg_rfc_id,
                                _prior_read_at or _now,
                            )
                        except Exception as _prop_exc:
                            _logger.warning(
                                'mark_read: recipient_read_at propagation failed '
                                'msg=%s: %s', _mid, _prop_exc,
                            )
                    for acc in Acc.browse(acc_ids):
                        unread_count = EmailMsg.search_count([
                            ('account_id', '=', acc.id),
                            ('folder', 'not in', ['sent', 'drafts', 'trash', 'spam']),
                            ('is_read', '=', False),
                            ('is_deleted', '=', False),
                        ])
                        acc.write({'unread_count': unread_count})"""


# ──────────────────────────────────────────────────────────────────────────
# Patcher
# ──────────────────────────────────────────────────────────────────────────

def patch_file(path, replacements, label):
    print(f"\n[{label}] {path}")
    if not os.path.exists(path):
        print(f"  ERROR: file not found")
        return False

    with open(path, 'r', encoding='utf-8') as f:
        src = f.read()
    original = src

    for old, new, anchor_name in replacements:
        if old not in src:
            # Idempotency: if the NEW text is already in place, treat as success.
            if new in src:
                print(f"  SKIP   anchor '{anchor_name}' (already patched)")
                continue
            print(f"  ABORT  cannot find anchor '{anchor_name}'.")
            print(f"         File may have been hand-edited. Inspect manually.")
            return False
        src = src.replace(old, new, 1)
        print(f"  OK     anchor '{anchor_name}'")

    if src == original:
        print(f"  NO CHANGES (everything already applied)")
        return True

    try:
        ast.parse(src)
    except SyntaxError as e:
        print(f"  SYNTAX ERROR after patch: {e}")
        return False

    backup = f"{path}.bak.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(path, backup)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(src)
    print(f"  WRITTEN  {len(src):,} bytes (backup: {os.path.basename(backup)})")
    return True


def main():
    if len(sys.argv) != 3:
        print("Usage:")
        print("  python3 patch_recipient_read_at.py "
              "<email_controller.py> <crm_notifications_controller.py>")
        sys.exit(2)

    email_ctrl_path = sys.argv[1]
    notif_ctrl_path = sys.argv[2]

    ok = True
    ok &= patch_file(
        email_ctrl_path,
        [(EMAIL_CTRL_OLD, EMAIL_CTRL_NEW, '_propagate_read_to_sent_copies')],
        'email_controller.py',
    )
    ok &= patch_file(
        notif_ctrl_path,
        [
            (NOTIF_CTRL_IMPORT_OLD, NOTIF_CTRL_IMPORT_NEW, 'imports'),
            (NOTIF_CTRL_BLOCK_OLD,  NOTIF_CTRL_BLOCK_NEW,  'mark_read email block'),
        ],
        'crm_notifications_controller.py',
    )

    print()
    if ok:
        print("All patches applied successfully.")
        sys.exit(0)
    else:
        print("One or more patches failed. Review output above.")
        sys.exit(1)


if __name__ == '__main__':
    main()
