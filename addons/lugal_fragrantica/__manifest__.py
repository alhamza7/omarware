# -*- coding: utf-8 -*-
{
    'name': 'Fragrantica Integration',
    'version': '1.0.0',
    'category': 'Sales',
    'summary': 'ربط منتجات العطور مع قاعدة بيانات Fragrantica',
    'description': """
        Fragrantica Integration Module
        ==============================
        
        هذا المودول يوفر:
        - ربط المنتجات مع قاعدة بيانات Fragrantica الشاملة
        - عرض معلومات كاملة عن العطور (نوتات، توافقات، وصف)
        - إمكانية البحث في أكثر من 49,000 عطر
        - تعديل وتخصيص المعلومات لكل منتج
        - طلب إضافة عطور جديدة من موقع Fragrantica
        
        المميزات:
        - قاعدة بيانات شاملة لأكثر من 49,000 عطر
        - معلومات تفصيلية: النوتات العطرية، التوافقات، الوصف، الصور
        - بحث متقدم بالعربي والإنجليزي
        - واجهة سهلة الاستخدام
        - قابلية تعديل كل المعلومات
    """,
    'author': 'Lugal Team',
    'website': 'https://www.lugal.com',
    'depends': ['base', 'product', 'sale'],
    'data': [
        # Security
        'security/ir.model.access.csv',
        
        # Views
        'views/fragrantica_perfume_views.xml',
        'views/fragrantica_pending_request_views.xml',
        'views/product_template_views.xml',
        'views/fragrantica_menu.xml',
        
        # Wizards
        'wizards/import_fragrantica_data_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'lugal_fragrantica/static/src/css/fragrantica.css',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}

