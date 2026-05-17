# -*- coding: utf-8 -*-
from . import admin_controller
from . import analytics_controller
from . import branch_controller
from . import bus_compat_controller
from . import call_controller
from . import channel_controller
from . import config_controller
from . import cors_controller
from . import crm_notifications_controller
from . import customer_controller
from . import delivery_controller
from . import knowledge_controller
from . import marquee_controller
from . import pos_bridge_controller
from . import price_list_controller
from . import purchase_products_rest_controller
from . import qa_controller
# supply_controller: base serializers + container attachment/penalty endpoints
from . import supply_controller
# supply_chain_api_controller: vendors, containers, PO CRUD + require_permission guards
from . import supply_chain_api_controller
# supply_extra_api_controller: negotiations, item_requests, clearance, payments, shipments
from . import supply_extra_api_controller
from . import supply_attachment_api
from . import supply_chat_controller
from . import supply_stories_controller
from . import presence_controller
from . import task_controller
from . import ticket_controller
from . import upload_controller
from . import user_controller
from . import workforce_controller
