# -*- coding: utf-8 -*-
"""
Force update pos_perfume_custom module and clear assets
"""
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import odoo
from odoo import api
from odoo.modules.registry import Registry

def force_update():
    """Force update and clear assets"""
    
    odoo.tools.config.parse_config(['--config=odoo.conf'])
    db_name = 'lugal'
    
    print(f"\n{'='*60}")
    print(f"Force updating pos_perfume_custom module")
    print(f"{'='*60}\n")
    
    registry = Registry(db_name)
    
    with registry.cursor() as cr:
        env = api.Environment(cr, odoo.SUPERUSER_ID, {})
        
        try:
            # Clear assets
            print("1. Clearing assets cache...")
            # Clear asset bundles
            assets = env['ir.attachment'].search([
                '|',
                ('name', 'like', 'web.assets_%'),
                ('url', 'like', '/web/assets/%')
            ])
            if assets:
                assets.unlink()
                print(f"   ✅ Cleared {len(assets)} asset files")
            else:
                print("   ℹ️ No assets to clear")
            
            # Clear registry cache
            registry.clear_cache()
            print("   ✅ Registry cache cleared")
            
            # Update module
            print("\n2. Updating pos_perfume_custom module...")
            module = env['ir.module.module'].search([
                ('name', '=', 'pos_perfume_custom')
            ], limit=1)
            
            if module:
                print(f"   Found module: {module.name} (state: {module.state})")
                module.button_immediate_upgrade()
                print("   ✅ Module upgraded")
            
            cr.commit()
            
            print(f"\n{'='*60}")
            print("✅ Update complete!")
            print("{'='*60}\n")
            print("Now:")
            print("1. Start Odoo normally")
            print("2. Clear browser cache (Ctrl+Shift+Del)")
            print("3. Refresh page (Ctrl+F5)")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            cr.rollback()
            return False

if __name__ == '__main__':
    try:
        success = force_update()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

