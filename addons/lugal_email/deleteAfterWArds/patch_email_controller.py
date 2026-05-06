#!/usr/bin/env python3
"""
Build the patched email_controller.py.
Reads the original from stdin or a provided path,
applies two surgical fixes to folder_delete, writes output.

Fix 1: Change write({'is_deleted': True}) → write({'folder': 'inbox'})
         for messages in deleted folders during folder_delete

Fix 2: Add rule-cleanup + message-restore block + updated return
         at end of folder_delete
"""

import sys

# ── Fix 1: restore messages to inbox instead of marking deleted ──────────────
OLD_1 = """                            try:
                                request.env['lugal.email.message'].sudo().search([
                                    ('account_id', '=', account_id),
                                    ('folder',     '=', folder_path),
                                    ('is_deleted', '=', False),
                                ]).write({'is_deleted': True})
                                request.env.cr.commit()
                            except Exception:
                                pass"""

NEW_1 = """                            try:
                                # Restore messages to inbox instead of marking deleted.
                                # Messages only get is_deleted when the user explicitly
                                # deletes them — not when a folder container is removed.
                                orphaned = request.env['lugal.email.message'].sudo().search([
                                    ('account_id', '=', account_id),
                                    ('folder',     '=', folder_path),
                                    ('is_deleted', '=', False),
                                ])
                                if orphaned:
                                    orphaned.write({'folder': 'inbox'})
                                request.env.cr.commit()
                            except Exception:
                                pass"""

# ── Fix 2: add rule-delete + restore block + updated return ──────────────────
OLD_2 = """            return _json_response({'success': True, 'data': {
                'deleted_path':  path,
                'deleted_paths': deleted_paths,
            }})
        except Exception as exc:
            return _json_response({'success': False, 'error': _format_imap_error(exc)}, 500)

    # ── Move to custom folder ──────────────────────────────────────────────────"""

NEW_2 = """            # ── Cleanup: delete rules + restore messages when folder deleted ──
            # Rules pointing at a deleted folder silently drop future emails.
            # Delete them now and fire async IMAP to put orphaned messages back.
            rules_deleted = 0
            msgs_restored = 0
            if deleted_paths:
                deleted_set = set(p.lower() for p in deleted_paths)

                # 1. Delete rules whose move_folder destination is now gone
                Rule = request.env['lugal.email.rule'].sudo()
                rules_to_del = Rule.browse()
                for rule in Rule.search([('account_id', '=', account_id)]):
                    try:
                        actions = json.loads(rule.actions_json or '[]')
                        for act in actions:
                            if act.get('action') == 'move_folder':
                                if (act.get('value') or '').lower() in deleted_set:
                                    rules_to_del |= rule
                                    break
                    except Exception:
                        pass
                if rules_to_del:
                    rules_deleted = len(rules_to_del)
                    _logger.info(
                        'folder_delete: removing %d rule(s) targeting deleted path(s): %s',
                        rules_deleted, [r.id for r in rules_to_del],
                    )
                    rules_to_del.unlink()

                # 2. Any messages still under deleted paths → restore to inbox
                Msg = request.env['lugal.email.message'].sudo()
                still_orphaned = Msg.search([
                    ('account_id', '=', account_id),
                    ('folder',     'in', deleted_paths),
                    ('is_deleted', '=', False),
                ])
                if still_orphaned:
                    msgs_restored = len(still_orphaned)
                    to_imap = [(m.imap_uid, m.folder) for m in still_orphaned if m.imap_uid]
                    still_orphaned.write({'folder': 'inbox'})

                    # Async IMAP: physically move messages back to INBOX on server
                    import collections as _col, threading as _thr
                    _db  = request.env.cr.dbname
                    _aid = account_id
                    by_src = _col.defaultdict(list)
                    for uid, src in to_imap:
                        by_src[src].append(uid)

                    def _bg(_by_src=by_src, _db=_db, _aid=_aid):
                        try:
                            from odoo.modules.registry import Registry as _Reg
                            import odoo as _odoo
                            with _Reg(_db).cursor() as _cr:
                                _env = _odoo.api.Environment(_cr, _odoo.SUPERUSER_ID, {})
                                _acc = _env['lugal.email.account'].browse(_aid)
                                with _acc._imap_session() as _conn:
                                    for _src, _uids in _by_src.items():
                                        try:
                                            _conn.select(_src, readonly=False)
                                            _uid_set = ','.join(str(u) for u in _uids)
                                            _t, _ = _conn.uid('move', _uid_set, 'INBOX')
                                            if _t != 'OK':
                                                _conn.uid('copy', _uid_set, 'INBOX')
                                                _conn.uid('store', _uid_set, '+FLAGS', '(\\\\Deleted)')
                                                _conn.expunge()
                                            _logger.info(
                                                'folder_delete restore: %d msgs %s→INBOX', len(_uids), _src)
                                        except Exception as _me:
                                            _logger.warning('folder_delete restore %s: %s', _src, _me)
                        except Exception as _e:
                            _logger.warning('folder_delete restore thread: %s', _e)

                    if to_imap:
                        _thr.Thread(target=_bg, daemon=True,
                                    name=f'imap-restore-{_aid}').start()

                try:
                    request.env.cr.commit()
                except Exception:
                    pass

            return _json_response({'success': True, 'data': {
                'deleted_path':  path,
                'deleted_paths': deleted_paths,
                'rules_deleted': rules_deleted,
                'msgs_restored': msgs_restored,
            }})
        except Exception as exc:
            return _json_response({'success': False, 'error': _format_imap_error(exc)}, 500)

    # ── Move to custom folder ──────────────────────────────────────────────────"""


def patch(src: str) -> str:
    assert OLD_1 in src, "Fix 1 target not found — indentation may have changed"
    assert OLD_2 in src, "Fix 2 target not found — check surrounding context"
    src = src.replace(OLD_1, NEW_1, 1)
    src = src.replace(OLD_2, NEW_2, 1)
    return src


if __name__ == '__main__':
    in_path  = sys.argv[1] if len(sys.argv) > 1 else '-'
    out_path = sys.argv[2] if len(sys.argv) > 2 else '-'
    src = open(in_path).read() if in_path != '-' else sys.stdin.read()
    result = patch(src)
    if out_path != '-':
        open(out_path, 'w').write(result)
        print(f"Written: {out_path} ({result.count(chr(10))+1} lines)")
    else:
        sys.stdout.write(result)
