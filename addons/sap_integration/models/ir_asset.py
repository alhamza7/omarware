# -*- coding: utf-8 -*-
"""
Patch for ir.asset to handle None manifest gracefully
This fixes the TypeError when queue_job or other modules have missing manifests
"""

from odoo import models
from odoo.modules import Manifest
from odoo.addons.base.models.ir_asset import DEFAULT_SEQUENCE


class IrAsset(models.Model):
    """Patch ir.asset to handle None manifest"""
    _inherit = 'ir.asset'

    def _fill_asset_paths(self, bundle, asset_paths, seen, addons, installed, **assets_params):
        """
        Override to handle None manifest gracefully
        """
        if bundle in seen:
            raise Exception("Circular assets bundle declaration: %s" % " > ".join(seen + [bundle]))

        # this index is used for prepending: files are inserted at the beginning
        # of the CURRENT bundle.
        bundle_start_index = len(asset_paths.list)

        assets = self._get_related_assets([('bundle', '=', bundle)], **assets_params).filtered('active')
        # 1. Process the first sequence of 'ir.asset' records
        for asset in assets.filtered(lambda a: a.sequence < DEFAULT_SEQUENCE):
            self._process_path(bundle, asset.directive, asset.target, asset.path, asset_paths, seen, addons, installed, bundle_start_index, **assets_params)

        # 2. Process all addons' manifests.
        for addon in addons:
            manifest = Manifest.for_addon(addon, display_warning=False)
            if manifest is not None:
                # Only process if manifest exists and has assets
                assets_dict = manifest.get('assets', {})
                if isinstance(assets_dict, dict):
                    for command in assets_dict.get(bundle, ()):
                        directive, target, path_def = self._process_command(command)
                        self._process_path(bundle, directive, target, path_def, asset_paths, seen, addons, installed, bundle_start_index, **assets_params)

        # 3. Process the rest of 'ir.asset' records
        for asset in assets.filtered(lambda a: a.sequence >= DEFAULT_SEQUENCE):
            self._process_path(bundle, asset.directive, asset.target, asset.path, asset_paths, seen, addons, installed, bundle_start_index, **assets_params)

