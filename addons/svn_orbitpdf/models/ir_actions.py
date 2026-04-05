# -*- coding: utf-8 -*-
# Copyright 2025 Sveltware Solutions

import io
import plutoprint

from odoo import models, fields
from odoo.tools.safe_eval import safe_eval, time

from collections import OrderedDict
from PIL import Image


class IrActionReport(models.AbstractModel):
    _inherit = 'ir.actions.report'

    u_pdf_engine = fields.Selection(
        [
            ('default', 'Default'),
            ('pluto', 'PlutoPrint'),
        ],
        string='Render Engine',
        default='default',
        required=True,
    )

    def _pluto_paperformat(self, pf):
        """
        Convert Odoo PaperFormat into PlutoPrint-compatible @page CSS.
        """
        size_css = ''
        margin_css = ''

        if pf.format and pf.format != 'custom':
            orientation = 'landscape' if pf.orientation == 'Landscape' else 'portrait'
            size_css = f'size: {pf.format} {orientation};'
        else:
            size_css = f'size: {pf.print_page_width}mm {pf.print_page_height}mm;'

        margin_css = f'margin: {pf.margin_top}mm {pf.margin_right}mm {pf.margin_bottom}mm {pf.margin_left}mm;'

        return f"""
            @page {{
                {size_css}
                {margin_css}
            }}
        """.strip()

    def _render_qweb_pdf_prepare_streams(self, report_ref, data, res_ids=None):
        # If not Pluto, fall back to normal Odoo behavior
        report_sudo = self._get_report(report_ref)
        if report_sudo.u_pdf_engine != 'pluto':
            return super()._render_qweb_pdf_prepare_streams(report_ref, data, res_ids)

        # ---------------------------------------------------------------------
        # Copy of Odoo logic (unchanged)
        # ---------------------------------------------------------------------
        if not data:
            data = {}
        data.setdefault('report_type', 'pdf')

        has_duplicated_ids = res_ids and len(res_ids) != len(set(res_ids))

        # No records OR duplicated IDs return empty PDF
        if has_duplicated_ids or not res_ids:
            return {False: {'stream': io.BytesIO(), 'attachment': None}}

        collected_streams = OrderedDict()

        # Attachment retrieval (Odoo's original logic)
        if res_ids:
            records = self.env[report_sudo.model].browse(res_ids)
            for record in records:
                res_id = record.id
                if res_id in collected_streams:
                    continue

                stream = None
                attachment = None
                if not has_duplicated_ids and report_sudo.attachment and not self.env.context.get('report_pdf_no_attachment'):
                    attachment = report_sudo.retrieve_attachment(record)

                    # Extract the stream from the attachment.
                    if attachment and report_sudo.attachment_use:
                        stream = io.BytesIO(attachment.raw)

                        # Ensure the stream can be saved in Image.
                        if attachment.mimetype.startswith('image'):
                            img = Image.open(stream)
                            new_stream = io.BytesIO()
                            img.convert('RGB').save(new_stream, format='pdf')
                            stream.close()
                            stream = new_stream

                collected_streams[res_id] = {'stream': stream, 'attachment': attachment}
                if res_title := report_sudo.print_report_name:
                    collected_streams[res_id]['title'] = safe_eval(res_title, {'object': record, 'time': time})

        # Determine which records require PDF generation
        res_ids_wo_stream = [res_id for res_id, stream_data in collected_streams.items() if not stream_data['stream']]

        page_style = self._pluto_paperformat(report_sudo.paperformat_id)

        for res_id in res_ids_wo_stream:
            book = plutoprint.Book()
            html = self._render_qweb_html(report_ref, [res_id], data=data)[0]
            book.load_data(html, user_style=page_style)

            if pdf_title := collected_streams[res_id].get('title'):
                book.set_metadata(plutoprint.PDF_METADATA_TITLE, pdf_title)

            pdf_stream = io.BytesIO()
            book.write_to_pdf_stream(pdf_stream)
            collected_streams[res_id]['stream'] = pdf_stream

        return collected_streams
