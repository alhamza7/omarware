#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix email folder rules for Anees (and optionally all users).

Run via:
  ./venv/bin/python odoo-bin shell -c odoo_local.conf -d <db> \
      --shell-interface=python < scripts/fix_email_folder_rules.py

What it does:
  1. Finds the target user's email accounts.
  2. Lists all their active rules (with conditions + actions).
  3. Retroactively applies every move-rule to ALL inbound messages
     (inbox + any wrong custom folder) for their accounts.
  4. Prints a summary of what was moved.
"""

import json

TARGET_LOGIN = 'anees'   # change to None to run for ALL users

print("=" * 70)
print("EMAIL FOLDER RULES – RETROACTIVE FIX")
print("=" * 70)

# ── 1. Find user(s) ─────────────────────────────────────────────────────────
User = env['res.users'].sudo()
if TARGET_LOGIN:
    users = User.search([('login', '=', TARGET_LOGIN)])
    if not users:
        print(f"ERROR: user '{TARGET_LOGIN}' not found")
        raise SystemExit(1)
else:
    users = User.search([('share', '=', False), ('active', '=', True)])

print(f"\nTarget users: {[u.login for u in users]}")

Rule = env['lugal.email.rule'].sudo()
Msg  = env['lugal.email.message'].sudo()
Acc  = env['lugal.email.account'].sudo()

LOGICAL = {'inbox', 'sent', 'drafts', 'trash', 'archive', 'spam'}

total_moved = 0

for user in users:
    uid = user.id
    accounts = Acc.search([('user_id', '=', uid), ('is_active', '=', True)])
    if not accounts:
        print(f"\n[{user.login}]  no active email accounts – skipping")
        continue

    print(f"\n{'─'*60}")
    print(f"User: {user.login} (id={uid})")
    print(f"Accounts: {[(a.id, a.email_address) for a in accounts]}")

    # ── 2. List rules ──────────────────────────────────────────────────────
    rules = Rule.search([
        ('user_id', '=', uid),
        ('is_active', '=', True),
    ], order='sequence asc, id asc')

    print(f"Active rules: {len(rules)}")
    for r in rules:
        try:
            conds   = json.loads(r.conditions_json or '[]')
            actions = json.loads(r.actions_json   or '[]')
        except Exception:
            conds, actions = [], []
        move_dests = [a.get('value') for a in actions if a.get('action') == 'move_folder']
        print(f"  Rule {r.id}: '{r.name}'")
        print(f"    conditions : {conds}")
        print(f"    actions    : {actions}")
        print(f"    move_dests : {move_dests}")
        if r.account_id:
            print(f"    account_id : {r.account_id.id} ({r.account_id.email_address})")

    # ── 3. Apply rules retroactively ──────────────────────────────────────
    # We process ALL inbound messages (not just inbox) so that messages
    # already landed in the wrong custom folder also get re-sorted.
    domain = [
        ('account_id', 'in', accounts.ids),
        ('folder', 'not in', ['sent', 'drafts', 'trash', 'spam']),
        ('is_deleted', '=', False),
    ]
    move_rules = rules.filtered(lambda r: any(
        a.get('action') == 'move_folder' and (a.get('value') or '').strip()
        for a in (json.loads(r.actions_json or '[]') if r.actions_json else [])
    ))

    if not move_rules:
        print("  No active move-folder rules – nothing to apply.")
        continue

    print(f"\n  Applying {len(move_rules)} move rule(s) to inbound messages …")

    msgs = Msg.search(domain, order='date desc, id desc', limit=10000)
    print(f"  Candidate messages: {len(msgs)}")

    user_moved = 0
    for msg in msgs:
        msg_vals = {
            'from_address':    msg.from_address or '',
            'to_addresses':    msg.to_addresses or '',
            'cc_addresses':    msg.cc_addresses or '',
            'bcc_addresses':   msg.bcc_addresses or '',
            'subject':         msg.subject or '',
            'body_text':       msg.body_text or '',
            'has_attachments': False,
            'is_important':    msg.is_important,
            'is_read':         msg.is_read,
            'is_starred':      msg.is_starred,
            'folder':          msg.folder or '',
            'account_id':      msg.account_id.id,
        }
        # Check attachments
        att_count = env['ir.attachment'].sudo().search_count([
            ('res_model', '=', 'lugal.email.message'),
            ('res_id',    '=', msg.id),
        ])
        msg_vals['has_attachments'] = bool(att_count)

        for rule in move_rules:
            try:
                if not rule._matches(msg_vals):
                    continue

                # Get destination folder(s) from rule
                actions = json.loads(rule.actions_json or '[]')
                dest = next(
                    (a.get('value', '').strip() for a in actions
                     if a.get('action') == 'move_folder' and a.get('value', '').strip()),
                    None,
                )
                if not dest:
                    continue

                # Skip if already in the correct folder branch
                cur = (msg.folder or '').strip()
                if cur == dest or cur.startswith(dest + '.') or cur.startswith(dest + '/'):
                    if rule.stop_processing:
                        break
                    continue

                before = msg.folder
                rule._apply_actions(msg)
                msg.invalidate_recordset()
                after  = msg.folder
                if after != before:
                    user_moved += 1
                    print(f"    Moved msg {msg.id} ({msg.subject[:40]!r}) "
                          f"{before!r} → {after!r}")
                if rule.stop_processing:
                    break
            except Exception as exc:
                print(f"    ERROR applying rule {rule.id} to msg {msg.id}: {exc}")

    print(f"\n  Moved {user_moved} messages for {user.login}")
    total_moved += user_moved

    # Refresh unread counts for all affected accounts
    for acc in accounts:
        unread = Msg.search_count([
            ('account_id', '=', acc.id),
            ('folder', 'not in', ['sent', 'drafts', 'trash', 'spam']),
            ('is_read', '=', False),
            ('is_deleted', '=', False),
        ])
        acc.write({'unread_count': unread})
        print(f"  Refreshed unread_count for {acc.email_address}: {unread}")

env.cr.commit()
print(f"\n{'='*70}")
print(f"DONE – total messages moved: {total_moved}")
print(f"{'='*70}")
