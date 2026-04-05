@echo off
python odoo-bin shell -d lugal --no-http --shell-interface=python -c "from update_with_shell import update_products_from_sap; update_products_from_sap()"
pause

