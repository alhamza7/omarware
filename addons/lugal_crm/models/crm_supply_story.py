# -*- coding: utf-8 -*-

import logging
from odoo import models, fields

_logger = logging.getLogger(__name__)


class LugalSupplyStory(models.Model):
    """
    WhatsApp-style ephemeral status/story for supply team members.

    A story expires automatically after `expires_hours` (default 24 h).
    Viewers are tracked in viewer_ids so the author can see who watched.

    Supported kinds:
      text  — plain text with optional background colour
      image — uploaded image (ir.attachment)
      video — uploaded video (ir.attachment, max 30 s recommended)
      audio — voice / audio clip (ir.attachment)
    """
    _name        = 'lugal.supply.story'
    _description = 'Supply Story'
    _order       = 'create_date desc, id desc'

    author_id = fields.Many2one(
        'res.users', string='Author',
        required=True, ondelete='cascade', index=True,
    )

    kind = fields.Selection([
        ('text',  'Text'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('audio', 'Audio / Voice'),
    ], string='Kind', required=True, default='text')

    # ── Text story fields ────────────────────────────────────────────────────
    content    = fields.Text(string='Text Content')
    bg_color   = fields.Char(
        string='Background Colour',
        default='#128C7E',
        help='CSS colour string for text stories (e.g. "#128C7E").',
    )
    font_size  = fields.Integer(string='Font Size', default=18)

    # ── Media story fields ───────────────────────────────────────────────────
    attachment_id = fields.Many2one(
        'ir.attachment', string='Media Attachment',
        ondelete='set null',
    )
    media_url     = fields.Char(
        string='Media URL',
        compute='_compute_media_url', store=False,
    )
    duration_seconds = fields.Float(
        string='Duration (s)', default=0.0,
        help='Length of audio/video in seconds.',
    )

    # ── Caption (optional on media stories) ─────────────────────────────────
    caption = fields.Text(string='Caption')

    # ── Expiry ───────────────────────────────────────────────────────────────
    expires_at = fields.Datetime(
        string='Expires At', index=True,
        help='Story auto-disappears after this datetime (default +24 h).',
    )

    is_expired = fields.Boolean(
        string='Expired', compute='_compute_is_expired', store=False,
    )

    # ── View tracking ────────────────────────────────────────────────────────
    viewer_ids = fields.Many2many(
        'res.users',
        'lugal_supply_story_viewer_rel',
        'story_id', 'user_id',
        string='Viewers',
    )
    view_count = fields.Integer(
        string='View Count',
        compute='_compute_view_count', store=False,
    )

    def _compute_media_url(self):
        for story in self:
            if story.attachment_id:
                token = story.attachment_id.access_token or ''
                story.media_url = (
                    f'/web/content/{story.attachment_id.id}'
                    f'?access_token={token}'
                )
            else:
                story.media_url = False

    def _compute_is_expired(self):
        from odoo.fields import Datetime as OdooDatetime
        import datetime as _dt
        now = _dt.datetime.utcnow()
        for story in self:
            if story.expires_at:
                story.is_expired = story.expires_at < now
            else:
                story.is_expired = False

    def _compute_view_count(self):
        for story in self:
            story.view_count = len(story.viewer_ids)


class LugalSupplyStoryViewReceipt(models.Model):
    """Stores exactly when each user viewed a story (for WhatsApp-style 'seen' with timestamp)."""
    _name        = 'lugal.supply.story.view.receipt'
    _description = 'Story View Receipt'
    _order       = 'viewed_at desc'
    _rec_name    = 'story_id'

    story_id  = fields.Many2one('lugal.supply.story', required=True, ondelete='cascade', index=True)
    user_id   = fields.Many2one('res.users',          required=True, ondelete='cascade', index=True)
    viewed_at = fields.Datetime(string='Viewed At', required=True)

    _sql_constraints = [
        ('unique_story_user', 'UNIQUE(story_id, user_id)', 'A user can only have one view receipt per story'),
    ]
# TODO: remove - cherry-pick marker
