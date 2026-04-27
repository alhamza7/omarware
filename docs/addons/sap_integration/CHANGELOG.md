# Changelog

All notable changes to SAP Integration module will be documented in this file.

## [2.0.0] - 2024 - OCA Connector Integration

### 🎉 Major Update: Full OCA Connector Framework Integration

This is a **major rewrite** of the SAP Integration module to use the industry-standard OCA Connector Framework.

### Added

#### Binding Models (New Architecture)
- `sap.res.partner` - SAP Business Partners binding with _inherits pattern
- `sap.product.product` - SAP Items binding with _inherits pattern  
- `sap.sale.order` - SAP Orders binding with _inherits pattern
- `sap.account.move` - SAP Invoices binding with _inherits pattern

#### Components (OCA Connector Architecture)
- **Adapters** (`components/adapter.py`)
  - `SapPartnerAdapter` - Business Partners CRUD operations
  - `SapProductAdapter` - Items CRUD operations
  - `SapSaleOrderAdapter` - Orders CRUD operations
  - `SapInvoiceAdapter` - Invoices CRUD operations

- **Binders** (`components/binder.py`)
  - Link Odoo IDs with SAP external IDs
  - `to_internal()` - Get Odoo record from SAP ID
  - `to_external()` - Get SAP ID from Odoo record
  - `bind()` - Create the binding

- **Mappers** (`components/mapper.py`)
  - Import mappers: SAP → Odoo data transformation
  - Export mappers: Odoo → SAP data transformation
  - Declarative @mapping decorators
  - Partner, Product, and Sale Order mappers

- **Importers** (`components/importer.py`)
  - `SapImporter` - Base importer with hooks
  - `SapBatchImporter` - Batch import support
  - Specific importers for each entity
  - Support for @job decorators (when queue_job installed)

- **Exporters** (`components/exporter.py`)
  - `SapExporter` - Base exporter with hooks
  - Dependency export support
  - Specific exporters for each entity

- **Listeners** (`components/listener.py`)
  - Event-based synchronization
  - Auto-bind on record creation
  - Auto-export on record update
  - `@skip_if` conditional execution

#### Documentation
- `README.md` - Complete documentation (2000+ lines)
- `QUICKSTART.md` - Quick start guide
- `MIGRATION_TO_OCA.md` - Migration guide from v1.0 to v2.0
- `CHANGELOG.md` - This file

### Changed

#### Core Models
- `sap.backend` - Now inherits from `connector.backend`
- Added `_backend_type = 'sap'`
- Full integration with OCA Component system

#### Dependencies
- Added `connector` - OCA Connector Framework
- Added `component` - Component architecture
- Added `component_event` - Event system
- Prepared for `queue_job` (optional but recommended)

#### Architecture
- From custom sync models to OCA Binding models
- From monolithic methods to Component-based architecture
- From manual sync to Event-driven synchronization
- From direct API calls to Adapter pattern

### Security
- Added access rules for new binding models
- Updated `ir.model.access.csv` with 4 new entries

### Improved

#### Code Organization
- Separation of concerns (Adapter, Binder, Mapper, Importer, Exporter)
- Declarative mappings with decorators
- WorkContext pattern for component access
- Better error handling and logging

#### Performance (when queue_job installed)
- Background job processing
- Asynchronous synchronization
- Job retry mechanism
- Priority and channel support

#### Maintainability
- Components are reusable
- Easy to extend and override
- Better test coverage potential
- Industry-standard patterns

### Backward Compatibility

⚠️ **Breaking Changes**:
- Old sync models (`sap.customer.sync`, etc.) are **deprecated**
- New binding models (`sap.res.partner`, etc.) should be used
- API methods changed (use `import_batch()` instead of direct methods)

**Migration Path**:
```python
# Old way (still works but deprecated)
sync = env['sap.customer.sync'].create({...})
sync.sync_from_sap()

# New way (recommended)
binding = env['sap.res.partner'].import_record(backend, external_id)
```

### Technical Details

#### File Changes
- **New files**: 9 (6 components + 3 docs)
- **Modified files**: 5
- **Total lines added**: ~3500
- **No files deleted**: All old models preserved for compatibility

#### Code Statistics
- Components: ~1500 lines
- Binding Models: ~300 lines
- Documentation: ~3000 lines
- Total: ~4800 lines added

### Requirements

#### Mandatory
- Odoo 17.0
- `connector` module (included)
- `component` module (included)
- `component_event` module (included)

#### Optional (Recommended)
- `queue_job` module for background processing
  ```bash
  pip install odoo-addon-queue-job==17.0.*
  ```

### Installation

1. Update module list
2. Install/Upgrade SAP Integration
3. (Optional) Install queue_job
4. Configure SAP Backend
5. Test connection
6. Start importing data

### Known Issues

- `queue_job` not installed by default (synchronization is blocking)
- Event listeners need explicit context activation
- Some SAP endpoints may need custom mappers

### Future Roadmap

- [ ] Add queue_job to dependencies when available
- [ ] Create wizards for bulk operations
- [ ] Add sync dashboard with statistics
- [ ] Implement incremental sync (delta sync)
- [ ] Add webhook support for real-time sync
- [ ] Support for more SAP entities
- [ ] Conflict resolution strategies

---

## [1.0.0] - Previous Version

### Features (Original)
- Basic SAP Service Layer integration
- Customer synchronization
- Product synchronization
- Order synchronization
- Invoice synchronization
- Manual sync models

### Architecture (Original)
- Custom sync models
- Direct API communication
- Manual data mapping
- No component architecture
- No event system

---

## Migration Guide

See `MIGRATION_TO_OCA.md` for detailed migration instructions.

## Quick Start

See `QUICKSTART.md` for quick setup and usage examples.

## Full Documentation

See `README.md` for complete documentation.

---

**Contributors**: Your Company  
**Based on**: OCA Connector Framework by Camptocamp & OCA  
**License**: LGPL-3

