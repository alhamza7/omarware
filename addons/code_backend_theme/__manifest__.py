# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Swaraj R (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
{
    "name": "Code Backend Theme",
    "version": "19.0.1.0.0",
    "category": "Themes/Backend",
    "summary": "Code Backend Theme is an attractive theme for backend",
    "description": """Minimalist and elegant theme for Odoo backend""",
    "author": "Cybrosys Techno Solutions",
    "company": "Cybrosys Techno Solutions",
    "maintainer": "Cybrosys Techno Solutions",
    "website": "https://www.cybrosys.com",
    "depends": ["web", "mail"],
    "data": [
        "views/layout_templates.xml",
        "views/base_menus.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "code_backend_theme/static/src/scss/theme_accent.scss",
            "code_backend_theme/static/src/scss/navigation_bar.scss",
            "code_backend_theme/static/src/scss/datetimepicker.scss",
            "code_backend_theme/static/src/scss/theme.scss",
            "code_backend_theme/static/src/scss/sidebar.scss",
            "code_backend_theme/static/src/js/fields/colors.js",
            "code_backend_theme/static/src/js/web_navbar_appmenu/webNavbarAppMenu.js",
        ],
    },
    "images": [
        "static/description/banner.jpg",
        "static/description/theme_screenshot.jpg",
    ],
    "license": "LGPL-3",
    "installable": True,
    "auto_install": False,
    "application": False,
    # Hooks disabled - causing compatibility issues with Odoo 19
    # "pre_init_hook": "test_pre_init_hook",
    # "post_init_hook": "test_post_init_hook",
}
