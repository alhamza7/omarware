# -*- coding: utf-8 -*-

from . import models

def uninstall_hook(cr, registry):
    """Don't delete user templates/data on module uninstall"""
    # By default Odoo deletes all module data on uninstall
    # This hook prevents deletion of user-created templates
    pass

