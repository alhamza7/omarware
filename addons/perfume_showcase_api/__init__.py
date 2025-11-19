# -*- coding: utf-8 -*-
from . import models
from . import controllers
from . import hooks


def post_init_create_jsonb_compat(env):
    """
    Dummy post-init hook kept for compatibility with previous manifest
    definitions. The actual compatibility wrapper for jsonb_path_query_first
    has already been created directly in the database, so we don't need to
    do anything here.
    """
    # No-op on purpose
    return None
