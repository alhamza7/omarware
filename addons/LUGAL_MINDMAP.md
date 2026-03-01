# Lugal Suite — Complete Module MindMap

> Generated: 2026-02-23 | Odoo 19 | Modules: lugal_auth · lugal_crm · lugal_supply

---

```mermaid
mindmap
  root((🏛️ LUGAL SUITE))

    %%──────────────────────────────────────────
    %% MODULE 1: lugal_auth
    %%──────────────────────────────────────────
    🔐 lugal_auth
      depends: base only
      🗄️ Models
        lugal.jwt.service
          generate_access_token
          generate_refresh_token
          verify_access_token
            blacklist check
            legacy nbs_archive fallback
          verify_refresh_token
          authenticate_user
          refresh_access_token
          revoke_token
        lugal.jwt.blacklist
          jti revocation list
          is_revoked
          revoke
          cron: purge expired
        lugal.auth.rate.limit
          per username+IP counter
          is_locked
          record_failure
          record_success
          cron: purge stale
      🌐 Endpoints
        POST /lugal/auth/login
          rate limited
          returns access + refresh token
        POST /lugal/auth/refresh
          renew access token
        POST /lugal/auth/logout
          blacklists current token
      ⚙️ Config ir.config_parameter
        lugal_auth.jwt_secret_key
        lugal_auth.jwt_refresh_secret_key
        lugal_auth.jwt_access_token_expire_minutes
        lugal_auth.jwt_refresh_token_expire_days
        lugal_auth.login_max_attempts
        lugal_auth.login_window_minutes
        lugal_auth.login_lockout_minutes
      🔄 Cron Jobs
        Purge Expired Blacklist — daily
        Purge Stale Rate Limits — every 6h
      📦 Helpers
        controllers/_auth.py
          ensure_jwt_user_id()
          imported by ALL Lugal modules

    %%──────────────────────────────────────────
    %% MODULE 2: lugal_crm
    %%──────────────────────────────────────────
    📋 lugal_crm
      depends: lugal_auth · lugal_supply · mail · product · stock

      %%── MODELS (24) ──
      🗄️ Models 24 total

        👥 Customer Domain
          lugal.crm.branch
            name · code · city · manager_id
            user_ids M2M
          lugal.crm.customer.stage
            name · name_ar · stage_type · sequence
          lugal.crm.tag
            name · name_ar · tag_type · color
          lugal.crm.channel.identity
            channel · external_id → customer
          lugal.crm.customer
            360° Card
            Identity: name · phone 1/2/3 · email · photo
            Address: city · country · shop_location · billing_address
            Pipeline: stage · tags · vip_status
            Finance: LTV · credit_debt · credit_limit
            Docs: attachment_ids → ir.attachment
            Tracking: mail.thread + mail.activity.mixin

        📞 Call Centre
          lugal.crm.call
            direction: inbound/outbound
            duration · recording_url
            script_id · qa_score
            post_call_notes · wrap_up
            pos_order linkage
          lugal.crm.call.script
            title · category · question · answer
          lugal.crm.call.queue
            position · status · agent_id

        💬 Omnichannel
          lugal.crm.omnichannel.message
            channel · direction · content
            sla_deadline · sla_breached
            owner_id · status
          lugal.crm.channel.config
            channel_type · sla_threshold · work_hours
          lugal.crm.message.template
            name · content · language

        📋 Tasks & Tickets
          lugal.crm.task
            title · priority · due_date
            assigned_to · status · follow_up_date
          lugal.crm.ticket
            ticket_number TKT-XXXXX auto
            type · priority · sla_deadline
            assigned_to · status
          lugal.crm.interaction
            type · notes · outcome
            call_id / message_id link

        📊 KPI & Analytics
          lugal.crm.employee.kpi
            calls · messages · frt · ttr
            transfers · missed · score
            _cron_daily_kpi_snapshot

        📚 Knowledge Base
          lugal.crm.kb.article
            title · title_ar · content · content_ar
            category · branch_ids
          lugal.crm.kb.notification
            title · body · target_group · is_read

        🛒 Supply Chain CRM side
          lugal.crm.supply.po
            po_number · vendor_id → lugal.supply.vendor
            container_id → lugal.supply.container
            status · total_amount computed
          lugal.crm.supply.po.line
            product_id · quantity · unit_price
            total_price computed
          lugal.crm.requested.item
            product · quantity · requested_by
            _cron_notify_requested_items

        👔 Workforce
          lugal.crm.shift
            shift_type · start · end · branch_id
          lugal.crm.attendance
            user_id · check_in · check_out

        🔒 Audit & QA
          lugal.crm.audit.log
            immutable · 45 actions
            user · model · record · details
          lugal.crm.qa.review
            review_number QA-XXXXX auto
            review_type: call / message
            scores: greeting · knowledge · solving · professionalism · compliance
            overall score computed
            status: draft → submitted

      %%── CONTROLLERS (15) ──
      🌐 Controllers 15 total · 150 endpoints

        customer_controller 16ep
          /api/crm/customers/*
          list · get · create · update · delete
          360_card · stage_change · tag_assign
          channel_identity · interactions · timeline

        call_controller 10ep
          /api/crm/calls/*
          list · get · create · end_call
          add_recording · update_qa_score
          get_queue · assign_from_queue
          call_scripts · call_script_search

        ticket_controller 11ep
          /api/crm/tickets/*
          list · get · create · update · delete
          assign · escalate · resolve · reopen
          add_note · get_history

        task_controller 8ep
          /api/crm/tasks/*
          list · get · create · update · delete
          assign · my_tasks · overdue

        channel_controller 11ep
          /api/crm/channels/*
          config CRUD · message inbox
          send_message · assign_conversation
          resolve_conversation · transfer
          sla_status · unread_count

        analytics_controller 9ep
          /api/crm/analytics/*
          dashboard_stats
          channel_report
          employee_kpi
          all_employees_kpi 🔒 Supervisor
          supervisor_dashboard 🔒 Supervisor
          branch_report
          ai_vs_human
          export_kpi CSV 🔒 Manager
          audit_log

        knowledge_controller 8ep
          /api/crm/knowledge/*
          articles: list · get · create · update · delete
          notifications: list · mark_read · broadcast

        branch_controller 6ep
          /api/crm/branches/*
          list · get
          create 🔒 Manager
          update 🔒 Supervisor
          user_assign 🔒 Manager
          delete 🔒 Manager

        config_controller 13ep
          /api/crm/config/*
          tags: list · create 🔒 · update 🔒 · delete 🔒
          stages: list · create 🔒 · update 🔒 · delete 🔒
          scripts: list · get · create 🔒 · update 🔒 · delete 🔒

        supply_controller 21ep
          /api/crm/supply/*
          PO: list · get · create · update · delete
          PO lines: add · update · delete
          vendors: list · get · create · update
          containers: list · get · create · update
          clearance_delivered flag
          po_upload_update

        workforce_controller 13ep
          /api/crm/workforce/*
          shifts: list · get · create · update · delete
          attendance: list · check_in · check_out
          templates: list · get · create · update · delete

        price_list_controller 8ep
          /api/crm/products/*
          catalog: list · search · get_by_barcode
          pricelist: get_customer_price
          requested_items: list · create · fulfill

        pos_bridge_controller 7ep
          /api/crm/pos/* optional
          create_invoice · get_products
          customer_orders · last_order
          order_detail · product_stock
          check_availability

        delivery_controller 3ep
          /api/crm/delivery/*
          customer_deliveries
          order_tracking
          update_delivery_status

        qa_controller 6ep
          /api/crm/qa/*
          list 🔒 QA Auditor
          get 🔒 QA Auditor
          create 🔒 QA Auditor
          update 🔒 QA Auditor
          submit 🔒 QA Auditor
          stats 🔒 QA Supervisor

      %%── HELPERS ──
      🛠️ Helper Files
        controllers/_auth.py
          re-export from lugal_auth
        controllers/_audit.py
          crm_audit() shorthand
        controllers/_permissions.py
          require_group()
          is_agent_or_above()
          is_supervisor_or_above()
          is_manager_or_above()
          is_general_manager()
          is_qa_auditor_or_above()
          is_qa_supervisor()
          forbidden()

      %%── SECURITY ──
      🔒 Security
        Security Groups 6
          Agent / موظف
          Supervisor / مشرف → implies Agent
          Manager / مدير → implies Supervisor
          General Manager / المدير العام → implies Manager
          QA Auditor / مدقق
          QA Supervisor / مشرف المدققين → implies QA Auditor
        Access Rules 25
          all 24 models covered

      %%── DATA ──
      ⚙️ Data & Automation
        Sequences
          TKT-XXXXX → lugal.crm.ticket
          QA-XXXXX  → lugal.crm.qa.review
        Cron Jobs 3
          Auto-notify Requested Items — daily
          Flag SLA-breached Messages — every hour
          Daily Employee KPI Snapshot — daily

    %%──────────────────────────────────────────
    %% MODULE 3: lugal_supply
    %%──────────────────────────────────────────
    🚢 lugal_supply
      depends: base · mail
      No controllers — data module only

      🗄️ Models 2
        lugal.supply.vendor
          name · code · country
          whatsapp · wechat · telegram
          contact_person · notes
          mail.thread tracking
        lugal.supply.container
          container_number · bl_number
          vessel · port_loading · port_discharge
          eta · status
          searates_url
          clearance_info_delivered flag
          clearance_info_delivered_at · by
          po_uploaded_by_id
          attachment_ids → ir.attachment
          mail.thread + mail.activity.mixin
          action_mark_clearance_delivered()

      🔒 Security
        Access Rules 2
          lugal.supply.vendor — CRUD
          lugal.supply.container — CRUD

    %%──────────────────────────────────────────
    %% CROSS-MODULE CONNECTIONS
    %%──────────────────────────────────────────
    🔗 Cross-Module Connections

      lugal_auth → lugal_crm
        JWT tokens — centralized
        ensure_jwt_user_id() shared helper
        /lugal/auth/* endpoints used by CRM frontend

      lugal_supply → lugal_crm
        lugal.supply.vendor
          referenced by crm_supply_po.vendor_id
        lugal.supply.container
          referenced by crm_supply_po.container_id
        API served via supply_controller in lugal_crm

      pos_perfume_custom → lugal_crm optional
        guard: _pos_available()
        pos.perfume.order — create invoice from call dialog
        pos.perfume.order.line — invoice lines

      Odoo base → ALL
        res.users — agents, managers, owners
        res.partner — customer ERP link
        res.country — customer address
        ir.attachment — documents, ID cards
        ir.sequence — ticket & QA numbering
        ir.cron — scheduled jobs
        ir.config_parameter — JWT secrets, rate limits

      product → lugal_crm
        product.product — catalog, requested items
        product.pricelist — customer pricing
        uom.uom — units of measure

      stock → lugal_crm
        stock.warehouse — stock per warehouse
        stock.quant — live inventory qty
        used by pos_bridge_controller only
```

---

## Permission Matrix

| Endpoint Category | Agent | Supervisor | Manager | GM | QA Auditor | QA Supervisor |
|-------------------|-------|------------|---------|-----|------------|---------------|
| Read customer data | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Create/update customers | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| Calls, tickets, tasks | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| Branch update | ❌ | ✅ | ✅ | ✅ | ❌ | ❌ |
| Branch create/delete | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ |
| Tags/stages/scripts CRUD | ❌ | ✅ | ✅ | ✅ | ❌ | ❌ |
| All employees KPI | ❌ | ✅ | ✅ | ✅ | ❌ | ❌ |
| Export KPI CSV | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ |
| QA reviews (CRUD) | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| QA stats | ❌ | ✅ | ✅ | ✅ | ❌ | ✅ |

---

## API Endpoint Summary

| Module | Controller | Endpoints | Auth Level |
|--------|------------|-----------|------------|
| lugal_auth | auth_controller | 3 | None (public) |
| lugal_crm | customer_controller | 16 | JWT |
| lugal_crm | call_controller | 10 | JWT |
| lugal_crm | ticket_controller | 11 | JWT |
| lugal_crm | task_controller | 8 | JWT |
| lugal_crm | channel_controller | 11 | JWT |
| lugal_crm | analytics_controller | 9 | JWT + Role |
| lugal_crm | knowledge_controller | 8 | JWT |
| lugal_crm | branch_controller | 6 | JWT + Role |
| lugal_crm | config_controller | 13 | JWT + Role |
| lugal_crm | supply_controller | 21 | JWT |
| lugal_crm | workforce_controller | 13 | JWT |
| lugal_crm | price_list_controller | 8 | JWT |
| lugal_crm | pos_bridge_controller | 7 | JWT (optional) |
| lugal_crm | delivery_controller | 3 | JWT |
| lugal_crm | qa_controller | 6 | JWT + Role |
| **TOTAL** | | **153 endpoints** | |

---

## Data Flow Diagram

```
Frontend App
    │
    ├─► POST /lugal/auth/login ──────────────────► lugal_auth
    │       ← access_token + refresh_token              │
    │                                              rate limiter
    │                                              JWT blacklist
    │
    ├─► POST /api/crm/* ─────────────────────────► lugal_crm
    │   Authorization: Bearer <token>                   │
    │                                         ensure_jwt_user_id()
    │                                                   │
    │                                    ┌──────────────┼──────────────┐
    │                                    │              │              │
    │                              permission      business        crm_audit()
    │                              guard check       logic         log action
    │                                    │              │
    │                                    │     ┌────────┼────────┐
    │                                    │     │        │        │
    │                                    │  lugal_    product   stock
    │                                    │  supply
    │                                    │  (containers,
    │                                    │   vendors)
    │
    ├─► POST /api/crm/pos/* ─────────────────────► pos_perfume_custom
    │   (optional — guard: _pos_available())         (POS invoicing)
    │
    └─► POST /lugal/auth/logout ─────────────────► lugal_auth
            Authorization: Bearer <token>         blacklist token (jti)
```

---

## Module Independence Matrix

| Can work without → | lugal_auth | lugal_crm | lugal_supply | pos_perfume | nbs_archive |
|-------------------|------------|-----------|--------------|-------------|-------------|
| **lugal_auth** | — | ✅ | ✅ | ✅ | ✅ |
| **lugal_supply** | ✅ | ✅ | — | ✅ | ✅ |
| **lugal_crm** | ❌ required | — | ❌ required | ✅ optional | ✅ not needed |
