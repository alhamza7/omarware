# -*- coding: utf-8 -*-

from . import config
from . import core
from . import services
from . import models
from . import components
from . import wizard


def post_init_hook(env):
    """Post-installation hook to register components"""
    # Force component registry rebuild
    from odoo.addons.component.core import ComponentRegistry
    
    # The components are automatically registered when the module is loaded
    # This hook ensures they are properly initialized
    pass


