# -*- coding: utf-8 -*-

from . import config
from . import core
from . import services
from . import models
from . import components
from . import wizard


def post_init_hook(env):
    """Post-installation hook to register components"""
    import logging
    _logger = logging.getLogger(__name__)
    
    try:
        # Build component registry for SAP integration
        from odoo.addons.component.builder import ComponentBuilder
        builder = ComponentBuilder(env)
        
        # Components are automatically built when module is loaded
        # This is just to ensure they are properly initialized
        _logger.info("SAP Integration module: Components initialized successfully!")
        
    except Exception as e:
        _logger.warning(f"Could not initialize components: {str(e)}")
        # This is not critical - components will be loaded automatically


