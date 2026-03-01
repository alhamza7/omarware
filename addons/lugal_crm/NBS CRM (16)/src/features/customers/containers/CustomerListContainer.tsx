import { useState } from 'react';
import { RefreshCw } from 'lucide-react';
import { useCustomers } from '../hooks/useCustomers';
import { customerService } from '../services/customerService';
import { CustomerKanban } from '../../../app/components/customer-kanban';
import { CustomerDetailDialog } from '../../../app/components/customer-detail-dialog';
import { CustomerForm } from '../../../app/components/customer-form';
import { Button } from '../../../app/components/ui/button';
import type { Customer, CreateCustomerPayload } from '../types';

interface CustomerListContainerProps {
  view:        'list' | 'kanban';
  showForm:    boolean;
  onCloseForm: () => void;
}

/**
 * Handles all customer list logic: fetching, filtering, pagination, and
 * one-click sync from Odoo res.partner contacts.
 */
export function CustomerListContainer({
  view,
  showForm,
  onCloseForm,
}: CustomerListContainerProps) {
  const [syncLoading, setSyncLoading] = useState(false);
  const [syncMsg,     setSyncMsg]     = useState<string | null>(null);

  const {
    customers,
    selectedCustomer,
    isLoading,
    error,
    setSelected,
    createCustomer,
    changeStage,
    setSearchQuery,
    fetchCustomers,
  } = useCustomers();

  const handleCreate = async (data: CreateCustomerPayload) => {
    await createCustomer(data);
    onCloseForm();
  };

  /** Import Odoo res.partner contacts that are missing from the CRM */
  const handleSyncFromOdoo = async () => {
    setSyncLoading(true);
    setSyncMsg(null);
    const result = await customerService.syncFromOdoo();
    if (result.success && result.data) {
      const { imported, total } = result.data;
      setSyncMsg(imported > 0
        ? `تم استيراد ${imported} عميل جديد. الإجمالي: ${total}`
        : `لا توجد جهات اتصال جديدة للاستيراد. الإجمالي: ${total}`);
      if (imported > 0) fetchCustomers();
    } else {
      setSyncMsg(`خطأ: ${result.error ?? 'فشل الاستيراد'}`);
    }
    setSyncLoading(false);
    setTimeout(() => setSyncMsg(null), 5000);
  };

  /** Map API customer to Kanban format expected by the existing UI component */
  const kanbanCustomers = customers.map((c) => ({
    id:                String(c.id),
    name:              c.name,
    email:             c.email ?? '',
    phone:             c.phone_1,
    address:           c.address ?? '',
    totalPurchases:    c.lifetime_value ?? 0,
    joinDate:          c.member_since ?? '',
    vipStatus:         c.vip_status,
    favoriteFragrance: '',
    /**
     * Priority: vip_status flag → stage_type (canonical key from backend) →
     * stage_name lowercased → fallback 'active'.
     * We default to 'active' (not 'lead') because customers imported from
     * Odoo contacts are already real customers, not new prospects.
     */
    stage:             c.vip_status
      ? 'vip'
      : (c.stage_type || c.stage_name?.toLowerCase() || 'active'),
    lastActivity:      c.last_call_date ?? '',
    channelIdentities: (c.channel_identities ?? []).map((ci) => ({
      channel:  ci.channel,
      handle:   ci.handle,
      verified: ci.verified,
    })),
  }));

  const isEmpty = !isLoading && customers.length === 0;

  return (
    <>
      {/* Sync banner — shown when the list is empty or after sync */}
      {(isEmpty || syncMsg) && (
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 p-4 mb-4 rounded-xl bg-primary/5 border border-primary/20">
          <div className="flex-1 text-sm text-muted-foreground">
            {syncMsg ?? 'لم يتم العثور على عملاء في CRM. هل تريد استيراد جهات الاتصال من أودو؟'}
          </div>
          <Button
            size="sm"
            variant="outline"
            className="shrink-0 gap-2"
            disabled={syncLoading}
            onClick={handleSyncFromOdoo}
          >
            <RefreshCw className={`w-4 h-4 ${syncLoading ? 'animate-spin' : ''}`} />
            {syncLoading ? 'جاري الاستيراد...' : 'استيراد من أودو'}
          </Button>
        </div>
      )}

      {isLoading && (
        <div className="flex items-center justify-center h-40 text-muted-foreground text-sm">
          جاري التحميل...
        </div>
      )}

      {error && (
        <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm">
          {error}
        </div>
      )}

      {showForm && (
        <div className="max-w-4xl">
          <CustomerForm onSubmit={handleCreate} />
        </div>
      )}

      {!isLoading && view === 'kanban' && (
        <CustomerKanban
          customers={kanbanCustomers as never}
          onCustomerClick={(c) => {
            const found = customers.find((cu) => String(cu.id) === c.id);
            if (found) setSelected(found as Customer);
          }}
        />
      )}

      <CustomerDetailDialog
        customer={selectedCustomer as never}
        open={!!selectedCustomer}
        onClose={() => setSelected(null)}
        profileImage=""
      />
    </>
  );
}
