# -*- coding: utf-8 -*-
"""
Supply Stories API  (WhatsApp-style status/stories)

Routes
------
  POST /api/crm/supply/stories/feed        — fetch active stories feed
  POST /api/crm/supply/stories/create      — post a new story (text / media)
  POST /api/crm/supply/stories/<id>/view   — record that current user viewed it
  POST /api/crm/supply/stories/<id>/delete — soft-expire (author only)
  POST /api/crm/supply/stories/upload      — upload media for a story (multipart)

All routes use JSON-RPC 2.0 envelope with JWT Bearer auth,
except /upload which is multipart HTTP.
"""

import base64
import datetime as _dt
import json
import logging
import mimetypes
import uuid
from datetime import timezone, timedelta

from odoo import http
from odoo.http import request, Response

from ._auth import ensure_jwt_user_id
from ._error import crm_error
from .upload_controller import _build_attachment_url

_RIYADH_TZ = timezone(timedelta(hours=3))


def _to_riyadh_iso(dt):
    """Convert a naive-UTC Odoo datetime to ISO 8601 with +03:00 (Riyadh) offset.
    Odoo returns False (not None) for unset Datetime fields, so we guard for both."""
    if not dt:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(_RIYADH_TZ).isoformat(timespec='seconds')

_logger = logging.getLogger(__name__)

# Stories expire after 24 h by default
STORY_TTL_HOURS = 24

# Allowed MIME types for story media (images: any image/*; video/audio: explicit lists)
STORY_VIDEO_MIMES = frozenset({
    'video/mp4', 'video/webm', 'video/quicktime',
})
STORY_AUDIO_MIMES = frozenset({
    'audio/mpeg', 'audio/mp4', 'audio/ogg', 'audio/webm',
    'audio/wav', 'audio/x-wav', 'audio/aac', 'audio/x-m4a',
})


def _story_upload_mime_allowed(mime: str) -> bool:
    if not mime:
        return False
    if mime.startswith('image/'):
        return True
    if mime in STORY_VIDEO_MIMES:
        return True
    if mime in STORY_AUDIO_MIMES:
        return True
    return False

STORY_MAX_MB        = 1024   # 1 GB — video/audio stories
STORY_MAX_IMAGE_MB  = 1024   # 1 GB — image stories


def _now_utc():
    return _dt.datetime.utcnow().replace(microsecond=0)


def _serialize_story(story, viewer_uid):
    """Return dict representation of a story record — field names match FE CrmSupplyStory type."""
    att = story.attachment_id
    media_url = None
    att_id = None
    if att and att.exists():
        token = att.access_token or ''
        media_url = f'/web/content/{att.id}?access_token={token}'
        att_id = att.id

    # Build attachments array — FE expects an array even for single-attachment stories
    # Field names match CrmSupplyMessageAttachment: name (not filename), file_url, file_type, etc.
    attachments = []
    if att_id and media_url:
        mime = att.mimetype or ''
        if mime.startswith('video'):
            file_type = 'video'
        elif mime.startswith('image'):
            file_type = 'image'
        elif mime.startswith('audio'):
            file_type = 'audio'
        else:
            file_type = 'file'
        attachments = [{
            'id':        att_id,
            'name':      att.name or 'file',
            'url':       media_url,
            'file_url':  media_url,
            'mimetype':  mime,
            'file_type': file_type,
            'size_bytes': int(att.file_size or 0),
        }]

    is_viewed = viewer_uid in story.viewer_ids.ids
    author = story.author_id

    return {
        # FE-expected primary fields
        'id':               story.id,
        'user_id':          author.id if author else None,
        'user_name':        author.name if author else '',
        'content':          story.content or '',
        'attachments':      attachments,
        'expires_at':       _to_riyadh_iso(story.expires_at) or '',
        'created_at':       _to_riyadh_iso(story.create_date) or '',
        'is_viewed':        is_viewed,
        'viewed_at':        None,
        'viewer_count':     len(story.viewer_ids),
        # Extra fields (kept for backward compat and FE convenience)
        'kind':             story.kind,
        'caption':          story.caption or '',
        'bg_color':         story.bg_color or '#128C7E',
        'font_size':        int(story.font_size or 18),
        'media_url':        media_url,
        'attachment_id':    att_id,
        'duration_seconds': float(story.duration_seconds or 0),
        'author_avatar':    f'/web/image/res.users/{author.id}/avatar_128' if author else None,
        'is_mine':          author.id == viewer_uid if author else False,
        'viewer_ids':       story.viewer_ids.ids,
    }


def _active_domain():
    """Domain that filters out expired stories."""
    return [
        '|',
        ('expires_at', '=', False),
        ('expires_at', '>', _dt.datetime.utcnow()),
    ]


class SupplyStoriesController(http.Controller):

    # -------------------------------------------------------------------------
    # POST /api/crm/supply/stories/feed
    # -------------------------------------------------------------------------

    @http.route('/api/crm/supply/stories/feed',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def stories_feed(self, **kwargs):
        """
        Return active stories grouped by author.

        Optional params:
          include_mine (bool, default true)  — include the caller's own stories
          limit        (int,  default 100)   — max stories to return

        Response:
          {
            "success": true,
            "data": {
              "stories": [<story>],        // flat list, sorted newest first per author
              "by_author": {               // grouped: { "2": [story, ...], ... }
                "<author_id>": [<story>]
              },
              "total": <int>
            }
          }
        """
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}

            if 'lugal.supply.story' not in request.env:
                return {'success': False, 'error': 'Stories are not available (module not loaded)'}

            include_mine = kwargs.get('include_mine', True)
            if isinstance(include_mine, str):
                include_mine = include_mine.lower() not in ('false', '0', 'no')
            try:
                limit = int(kwargs.get('limit', 100) or 100)
            except (TypeError, ValueError):
                limit = 100
            limit = min(max(limit, 1), 500)

            Story = request.env['lugal.supply.story'].sudo()
            domain = _active_domain()
            if not include_mine:
                domain.append(('author_id', '!=', uid))

            stories = Story.search(domain, order='create_date asc', limit=limit)
            serialized = [_serialize_story(s, uid) for s in stories]

            # Build author-bucket list (FE CrmSupplyStoryAuthorBucket format)
            bucket_map = {}   # user_id -> bucket dict
            for s in serialized:
                author_id = s['user_id']
                if author_id not in bucket_map:
                    bucket_map[author_id] = {
                        'user_id':              author_id,
                        'user_name':            s['user_name'],
                        'stories':              [],
                        'has_unviewed':         False,
                        'last_viewed_story_id': None,
                    }
                bucket = bucket_map[author_id]
                bucket['stories'].append(s)
                if not s['is_viewed'] and s['user_id'] != uid:
                    bucket['has_unviewed'] = True
                if s['is_viewed']:
                    bucket['last_viewed_story_id'] = s['id']

            # Sort: own bucket first, then others by most-recent story timestamp (desc)
            items = list(bucket_map.values())
            # Step 1: sort by latest story timestamp descending (ISO strings sort lexicographically)
            items.sort(key=lambda b: b['stories'][-1]['created_at'] if b['stories'] else '', reverse=True)
            # Step 2: stable sort to put own bucket first
            items.sort(key=lambda b: 0 if b['user_id'] == uid else 1)

            return {
                'success': True,
                'data': {
                    'items':        items,
                    'total_stories': len(serialized),
                    # Keep legacy fields for any old clients
                    'stories':      serialized,
                    'total':        len(serialized),
                },
            }
        except Exception as e:
            return crm_error(e, 'stories_feed')

    # -------------------------------------------------------------------------
    # POST /api/crm/supply/stories/create
    # -------------------------------------------------------------------------

    @http.route('/api/crm/supply/stories/create',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def stories_create(self, kind='text', content=None, caption=None,
                       bg_color=None, font_size=None,
                       attachment_id=None, attachment_ids=None,
                       duration_seconds=None,
                       ttl_hours=None, **kwargs):
        """
        Post a new story.

        Body params:
          kind             (str)  'text'|'image'|'video'|'audio' — auto-detected from mime
          content          (str)  Text for text stories / caption for media
          caption          (str)  Optional caption on media stories
          bg_color         (str)  CSS colour for text stories (default '#128C7E')
          font_size        (int)  Font size for text stories (default 18)
          attachment_id    (int)  ID from /stories/upload (singular form)
          attachment_ids   (list) [int, ...] array form accepted — first element is used
          duration_seconds (float) Length of audio/video in seconds
          ttl_hours        (int)  Override expiry window (default 24, max 48)

        Response:
          { "success": true, "data": <story> }
        """
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}

            if 'lugal.supply.story' not in request.env:
                return {'success': False, 'error': 'Stories are not available (module not loaded)'}

            # Accept attachment_ids (array) as an alias for attachment_id (singular)
            if not attachment_id and attachment_ids:
                ids_list = attachment_ids if isinstance(attachment_ids, list) else [attachment_ids]
                if ids_list:
                    attachment_id = ids_list[0]

            # Validate and load attachment
            att = None
            if attachment_id:
                Att = request.env['ir.attachment'].sudo()
                att = Att.browse(int(attachment_id)).exists()
                if not att:
                    return {'success': False, 'error': 'Attachment not found'}

            # Auto-detect kind from attachment mime type when client omits it or sends 'text'
            kind = (kind or 'text').strip().lower()
            if att and kind == 'text':
                mime = att.mimetype or ''
                if mime.startswith('video'):
                    kind = 'video'
                elif mime.startswith('image'):
                    kind = 'image'
                elif mime.startswith('audio'):
                    kind = 'audio'

            if kind not in ('text', 'image', 'video', 'audio'):
                kind = 'text'

            if kind == 'text' and not (content or '').strip() and not att:
                return {'success': False, 'error': 'content or attachment required for story'}

            ttl = max(1, min(int(ttl_hours or STORY_TTL_HOURS), 48))
            expires_at = _dt.datetime.utcnow() + _dt.timedelta(hours=ttl)

            Story = request.env['lugal.supply.story'].sudo()
            vals = {
                'author_id':        uid,
                'kind':             kind,
                'content':          (content or '').strip() or None,
                'caption':          (caption or '').strip() or None,
                'bg_color':         (bg_color or '#128C7E').strip(),
                'font_size':        int(font_size or 18),
                'expires_at':       expires_at,
                'duration_seconds': float(duration_seconds or 0),
            }
            if att:
                vals['attachment_id'] = att.id

            story = Story.create(vals)

            # Broadcast to all supply users via bus
            try:
                request.env['bus.bus'].sudo()._sendone(
                    'supply_stories',
                    'supply.story.new',
                    _serialize_story(story, uid),
                )
            except Exception as bus_exc:
                _logger.debug('stories bus error: %s', bus_exc)

            return {'success': True, 'data': _serialize_story(story, uid)}
        except Exception as e:
            return crm_error(e, 'stories_create')

    # -------------------------------------------------------------------------
    # POST /api/crm/supply/stories/<id>/view
    # -------------------------------------------------------------------------

    @http.route('/api/crm/supply/stories/<int:story_id>/view',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def stories_view(self, story_id, **kwargs):
        """
        Record that the current user has viewed story <id>.
        Idempotent — calling multiple times is safe.

        Response:
          { "success": true, "data": {
              "story_id": <id>, "viewed_at": <iso>, "viewer_count": <int>, "story": <story>
          } }
        """
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}

            Story = request.env['lugal.supply.story'].sudo()
            story = Story.browse(story_id).exists()
            if not story:
                return {'success': False, 'error': 'Story not found'}

            viewed_at_iso = None
            # Authors don't count as viewers of their own story
            if story.author_id.id != uid and uid not in story.viewer_ids.ids:
                story.write({'viewer_ids': [(4, uid)]})
                now = _dt.datetime.now(_RIYADH_TZ)
                viewed_at_iso = now.isoformat(timespec='seconds')

                # Persist the view receipt with timestamp
                ViewReceipt = request.env['lugal.supply.story.view.receipt'].sudo()
                existing = ViewReceipt.search([('story_id', '=', story.id), ('user_id', '=', uid)], limit=1)
                if not existing:
                    ViewReceipt.create({'story_id': story.id, 'user_id': uid, 'viewed_at': now})

                # Notify the author
                try:
                    viewer = request.env['res.users'].sudo().browse(uid)
                    request.env['bus.bus'].sudo()._sendone(
                        f'supply_user.{story.author_id.id}',
                        'supply.story.viewed',
                        {
                            'story_id':    story.id,
                            'viewer_id':   uid,
                            'viewer_name': viewer.name if viewer.exists() else '',
                            'viewer_count': len(story.viewer_ids),
                        },
                    )
                except Exception as bus_exc:
                    _logger.debug('story view bus error: %s', bus_exc)

            return {
                'success': True,
                'data': {
                    'story_id':     story.id,
                    'viewed_at':    viewed_at_iso,
                    'viewer_count': len(story.viewer_ids),
                    'story':        _serialize_story(story, uid),
                },
            }
        except Exception as e:
            return crm_error(e, 'stories_view')

    # -------------------------------------------------------------------------
    # POST /api/crm/supply/stories/<id>/viewers
    # -------------------------------------------------------------------------

    @http.route('/api/crm/supply/stories/<int:story_id>/viewers',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def stories_viewers(self, story_id, **kwargs):
        """
        Return the list of users who viewed story <id>.
        Only the story author may call this.

        Response:
          { "success": true, "data": {
              "story_id": <id>, "viewer_count": <int>,
              "items": [{ "user_id": <int>, "user_name": <str>, "viewed_at": <iso|null> }]
          } }
        """
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}

            Story = request.env['lugal.supply.story'].sudo()
            story = Story.browse(story_id).exists()
            if not story:
                return {'success': False, 'error': 'Story not found'}

            viewers = story.viewer_ids
            # Build a map of user_id → viewed_at from view receipts
            ViewReceipt = request.env['lugal.supply.story.view.receipt'].sudo()
            receipts = ViewReceipt.search([('story_id', '=', story.id)])
            receipt_map = {r.user_id.id: r.viewed_at for r in receipts}

            items = []
            for v in viewers:
                viewed_at = receipt_map.get(v.id)
                items.append({
                    'user_id':   v.id,
                    'user_name': v.name or '',
                    'viewed_at': _to_riyadh_iso(viewed_at),
                })

            return {
                'success': True,
                'data': {
                    'story_id':     story.id,
                    'viewer_count': len(viewers),
                    'items':        items,
                },
            }
        except Exception as e:
            return crm_error(e, 'stories_viewers')

    # -------------------------------------------------------------------------
    # POST /api/crm/supply/stories/<id>/delete
    # -------------------------------------------------------------------------

    @http.route('/api/crm/supply/stories/<int:story_id>/delete',
                type='jsonrpc', auth='none', csrf=False, methods=['POST'])
    def stories_delete(self, story_id, **kwargs):
        """
        Expire a story immediately (author only).

        Response:
          { "success": true }
        """
        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return {'success': False, 'error': 'Unauthorized'}

            Story = request.env['lugal.supply.story'].sudo()
            story = Story.browse(story_id).exists()
            if not story:
                return {'success': False, 'error': 'Story not found'}
            if story.author_id.id != uid:
                return {'success': False, 'error': 'Forbidden'}

            # Expire immediately instead of hard-delete
            story.write({'expires_at': _dt.datetime.utcnow()})

            try:
                request.env['bus.bus'].sudo()._sendone(
                    'supply_stories',
                    'supply.story.deleted',
                    {'story_id': story.id, 'author_id': uid},
                )
            except Exception as bus_exc:
                _logger.debug('story delete bus error: %s', bus_exc)

            return {'success': True}
        except Exception as e:
            return crm_error(e, 'stories_delete')

    # -------------------------------------------------------------------------
    # POST /api/crm/supply/stories/upload  (multipart/form-data)
    # -------------------------------------------------------------------------

    @http.route('/api/crm/supply/stories/upload',
                type='http', auth='none', csrf=False,
                methods=['POST', 'OPTIONS'], cors='*')
    def stories_upload(self, **kwargs):
        """
        Upload media for a story before calling /stories/create.

        Form fields:
          file             — binary file (image, video, or audio)
          kind             — optional hint: 'image'|'video'|'audio'
          duration_seconds — for audio/video

        Response:
          {
            "success": true,
            "data": {
              "attachment_id": <int>,
              "url": "<str>",
              "kind": "image"|"video"|"audio",
              "mimetype": "<str>",
              "size": <bytes>,
              "duration_seconds": <float>
            }
          }
        """
        def _json(payload, status=200):
            return Response(
                json.dumps(payload), status=status,
                headers=[('Content-Type', 'application/json')],
            )

        if request.httprequest.method == 'OPTIONS':
            return Response(status=204, headers=[
                ('Access-Control-Allow-Origin', '*'),
                ('Access-Control-Allow-Methods', 'POST, OPTIONS'),
                ('Access-Control-Allow-Headers', 'Authorization, Content-Type'),
            ])

        try:
            uid = ensure_jwt_user_id()
            if not uid:
                return _json({'success': False, 'error': 'Unauthorized'}, 401)

            files = (
                request.httprequest.files.getlist('files[]')
                or request.httprequest.files.getlist('files')
                or request.httprequest.files.getlist('file')
            )
            if not files:
                return _json({'success': False, 'error': 'No file provided'}, 400)

            f = files[0]  # stories: single file per upload
            data = f.read()
            mime = f.mimetype or mimetypes.guess_type(f.filename or '')[0] or ''

            if not _story_upload_mime_allowed(mime):
                return _json({'success': False, 'error': f'Unsupported type: {mime}'}, 400)

            # Size limits
            is_image = mime.startswith('image/')
            max_bytes = (STORY_MAX_IMAGE_MB if is_image else STORY_MAX_MB) * 1024 * 1024
            if len(data) > max_bytes:
                limit = STORY_MAX_IMAGE_MB if is_image else STORY_MAX_MB
                return _json({'success': False, 'error': f'File exceeds {limit} MB'}, 400)

            # Determine kind
            kind_hint = (kwargs.get('kind') or request.httprequest.form.get('kind') or '').lower()
            if kind_hint in ('image', 'video', 'audio'):
                kind = kind_hint
            elif mime.startswith('image/'):
                kind = 'image'
            elif mime in STORY_VIDEO_MIMES:
                kind = 'video'
            else:
                kind = 'audio'

            try:
                duration = float(
                    kwargs.get('duration_seconds')
                    or request.httprequest.form.get('duration_seconds')
                    or 0
                )
            except (ValueError, TypeError):
                duration = 0.0

            # Enforce 60-second cap for video/audio stories
            STORY_MAX_DURATION_S = 60.0
            if kind in ('video', 'audio') and duration > STORY_MAX_DURATION_S:
                return _json(
                    {'success': False,
                     'error': f'Video/audio stories may not exceed {int(STORY_MAX_DURATION_S)} seconds. '
                              f'Received: {duration:.1f}s'},
                    400,
                )

            token = uuid.uuid4().hex
            Att = request.env['ir.attachment'].sudo()
            att = Att.create({
                'name':         f.filename or f'story_{kind}',
                'mimetype':     mime,
                'datas':        base64.b64encode(data).decode('utf-8'),
                'type':         'binary',
                'res_model':    'lugal.supply.story',
                'res_id':       False,
                'access_token': token,
            })
            att.flush_recordset(['access_token'])

            url = _build_attachment_url(att)

            return _json({
                'success': True,
                'data': {
                    'attachment_id':    att.id,
                    'url':              url,
                    'kind':             kind,
                    'mimetype':         mime,
                    'size':             len(data),
                    'duration_seconds': duration,
                },
            })
        except Exception as e:
            _logger.exception('stories_upload')
            try:
                request.env.cr.rollback()
            except Exception:
                pass
            return _json({'success': False, 'error': str(e)}, 500)
# TODO: remove - cherry-pick marker
