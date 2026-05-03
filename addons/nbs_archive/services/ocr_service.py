# -*- coding: utf-8 -*-
"""
OCR service stub — full implementation is in models/nbs_ocr_service.py.

This file is intentionally empty so that the Google Vision implementation
in models/nbs_ocr_service.py is not overridden at load time.
(addons/__init__.py loads `services` AFTER `models`, so any methods defined
here would shadow the models/ version.  Keeping this file as a pass-through
prevents that.)
"""
