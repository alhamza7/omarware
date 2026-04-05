// ============================================================
// Vendors — CRUD Management Panel
// ============================================================
import { useState, useEffect, useCallback } from 'react';
import {
  Plus, Search, RefreshCw, Trash2, Loader2, X,
  ChevronLeft, ChevronRight, Building2, Pencil, Check, Phone, Mail,
} from 'lucide-react';
import { Button } from '../../../components/ui/button';
import { Input }  from '../../../components/ui/input';
import supplyApi  from '../../../services/supplyApi';
import type { Vendor, VendorCreateInput } from '../../../types/supply';

// ─────────────────────────────────────────────────────────────
// Vendor Form (shared between Create and Edit)
// ─────────────────────────────────────────────────────────────
function VendorForm({
  initial, title, onSave, onClose,
}: {
  initial?: Partial<VendorCreateInput>;
  title:    string;
  onSave:   (vals: VendorCreateInput) => Promise<{ success: boolean; error?: string }>;
  onClose:  () => void;
}) {
  const [vals, setVals] = useState<VendorCreateInput>({
    name:          initial?.name          ?? '',
    name_ar:       initial?.name_ar       ?? '',
    contact_type:  initial?.contact_type  ?? 'vendor',
    division:      initial?.division      ?? '',
    contact_name:  initial?.contact_name  ?? '',
    phone:         initial?.phone         ?? '',
    email:         initial?.email         ?? '',
    website:       initial?.website       ?? '',
    whatsapp:      initial?.whatsapp      ?? '',
    telegram:      initial?.telegram      ?? '',
    city:          initial?.city          ?? '',
    address:       initial?.address       ?? '',
    payment_terms: initial?.payment_terms ?? '',
    notes:         initial?.notes         ?? '',
  });
  const [busy,  setBusy]  = useState(false);
  const [error, setError] = useState('');

  const set = (k: keyof VendorCreateInput, v: string) =>
    setVals(p => ({ ...p, [k]: v }));

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!vals.name.trim()) return setError('Vendor name is required');
    setBusy(true); setError('');
    const res = await onSave(vals);
    if (!res.success) setError(res.error ?? 'Failed to save vendor');
    setBusy(false);
  };

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] flex flex-col">
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <h2 className="text-base font-bold text-gray-900 flex items-center gap-2">
            <Building2 className="w-4 h-4 text-emerald-600" /> {title}
          </h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X className="w-5 h-5" /></button>
        </div>

        <form onSubmit={submit} className="flex flex-col flex-1 overflow-hidden">
          <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div className="col-span-2">
                <label className="text-sm font-medium text-gray-700 block mb-1">Vendor Name *</label>
                <Input value={vals.name} onChange={e => set('name', e.target.value)} placeholder="Company name" required />
              </div>
              <div className="col-span-2">
                <label className="text-sm font-medium text-gray-700 block mb-1">Name (Arabic)</label>
                <Input value={vals.name_ar} onChange={e => set('name_ar', e.target.value)} placeholder="اسم الشركة" dir="rtl" />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 block mb-1">Type</label>
                <select
                  className="w-full h-9 rounded-md border border-input bg-background px-3 py-1 text-sm"
                  value={vals.contact_type}
                  onChange={e => set('contact_type', e.target.value as 'customer' | 'vendor' | 'both')}
                >
                  <option value="vendor">Vendor</option>
                  <option value="customer">Customer</option>
                  <option value="both">Both</option>
                </select>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 block mb-1">Division</label>
                <select
                  className="w-full h-9 rounded-md border border-input bg-background px-3 py-1 text-sm"
                  value={vals.division}
                  onChange={e => set('division', e.target.value)}
                >
                  <option value="">— Any —</option>
                  <option value="europe">Europe</option>
                  <option value="china">China</option>
                </select>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 block mb-1">Contact Person</label>
                <Input value={vals.contact_name} onChange={e => set('contact_name', e.target.value)} placeholder="Name" />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 block mb-1">Phone</label>
                <Input value={vals.phone} onChange={e => set('phone', e.target.value)} placeholder="+39..." />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 block mb-1">Email</label>
                <Input type="email" value={vals.email} onChange={e => set('email', e.target.value)} placeholder="info@..." />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 block mb-1">WhatsApp</label>
                <Input value={vals.whatsapp} onChange={e => set('whatsapp', e.target.value)} placeholder="+..." />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 block mb-1">Telegram</label>
                <Input value={vals.telegram} onChange={e => set('telegram', e.target.value)} placeholder="@handle" />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 block mb-1">City</label>
                <Input value={vals.city} onChange={e => set('city', e.target.value)} placeholder="Milan" />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 block mb-1">Website</label>
                <Input value={vals.website} onChange={e => set('website', e.target.value)} placeholder="https://..." />
              </div>
              <div className="col-span-2">
                <label className="text-sm font-medium text-gray-700 block mb-1">Address</label>
                <Input value={vals.address} onChange={e => set('address', e.target.value)} placeholder="Full address" />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 block mb-1">Payment Terms</label>
                <Input value={vals.payment_terms} onChange={e => set('payment_terms', e.target.value)} placeholder="Net 30" />
              </div>
              <div className="col-span-2">
                <label className="text-sm font-medium text-gray-700 block mb-1">Notes</label>
                <textarea
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm min-h-[60px] resize-none focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  value={vals.notes} onChange={e => set('notes', e.target.value)} placeholder="Any notes..."
                />
              </div>
            </div>
            {error && <p className="text-sm text-red-600 bg-red-50 px-3 py-2 rounded-lg">{error}</p>}
          </div>

          <div className="flex justify-end gap-3 px-6 py-4 border-t bg-gray-50">
            <Button type="button" variant="outline" onClick={onClose}>Cancel</Button>
            <Button type="submit" disabled={busy} className="bg-emerald-600 hover:bg-emerald-700">
              {busy ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Check className="w-4 h-4 mr-2" />}
              Save Vendor
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// Main Vendor Container
// ─────────────────────────────────────────────────────────────
export function VendorContainer() {
  const [vendors,      setVendors]      = useState<Vendor[]>([]);
  const [total,        setTotal]        = useState(0);
  const [page,         setPage]         = useState(1);
  const PER_PAGE = 30;
  const [search,       setSearch]       = useState('');
  const [searchDraft,  setSearchDraft]  = useState('');
  const [loading,      setLoading]      = useState(false);
  const [error,        setError]        = useState<string | null>(null);
  const [showCreate,   setShowCreate]   = useState(false);
  const [editVendor,   setEditVendor]   = useState<Vendor | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Vendor | null>(null);
  const [deleteBusy,   setDeleteBusy]   = useState(false);

  const load = useCallback(async () => {
    setLoading(true); setError(null);
    const res = await supplyApi.vendorList(search, page, PER_PAGE);
    if (res?.success) { setVendors(res.data?.items ?? []); setTotal(res.data?.total ?? 0); }
    else setError(res?.error ?? 'Failed to load vendors');
    setLoading(false);
  }, [search, page]);

  useEffect(() => { load(); }, [load]);

  const doCreate = async (vals: VendorCreateInput) => {
    const res = await supplyApi.vendorCreate(vals);
    if (res?.success) { setVendors(v => [res.data, ...v]); setTotal(t => t + 1); setShowCreate(false); }
    return { success: res?.success ?? false, error: res?.error };
  };

  const doEdit = async (vals: VendorCreateInput) => {
    if (!editVendor) return { success: false };
    const res = await supplyApi.vendorUpdate(editVendor.id, vals);
    if (res?.success) { setVendors(v => v.map(x => x.id === editVendor.id ? res.data : x)); setEditVendor(null); }
    return { success: res?.success ?? false, error: res?.error };
  };

  const doDelete = async () => {
    if (!deleteTarget) return;
    setDeleteBusy(true);
    const res = await supplyApi.vendorDelete(deleteTarget.id);
    if (res?.success) { setVendors(v => v.filter(x => x.id !== deleteTarget.id)); setTotal(t => t - 1); setDeleteTarget(null); }
    setDeleteBusy(false);
  };

  const totalPages  = Math.ceil(total / PER_PAGE);

  const CONTACT_TYPE_COLORS: Record<string, string> = {
    vendor:   'bg-emerald-100 text-emerald-700',
    customer: 'bg-blue-100 text-blue-700',
    both:     'bg-purple-100 text-purple-700',
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top Bar */}
      <div className="bg-white border-b px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-emerald-600 rounded-lg flex items-center justify-center">
            <Building2 className="w-4 h-4 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-900">Vendors & Contacts</h1>
            <p className="text-xs text-gray-500">{total} contacts total</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={load} className="p-2 text-gray-400 hover:text-gray-700 rounded-lg hover:bg-gray-100 transition">
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <Button onClick={() => setShowCreate(true)} className="gap-2 bg-emerald-600 hover:bg-emerald-700">
            <Plus className="w-4 h-4" /> New Vendor
          </Button>
        </div>
      </div>

      {/* Search */}
      <div className="bg-white border-b px-6 py-3 flex items-center gap-3">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <Input
            className="pl-9 h-8 text-sm" placeholder="Search by name, phone, email..."
            value={searchDraft}
            onChange={e => setSearchDraft(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter') { setSearch(searchDraft); setPage(1); } }}
          />
        </div>
        {search && (
          <button onClick={() => { setSearch(''); setSearchDraft(''); setPage(1); }}
            className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-800 px-2 py-1 rounded-lg hover:bg-gray-100 transition">
            <X className="w-3 h-3" /> Clear
          </button>
        )}
      </div>

      {/* List */}
      <div className="px-6 py-4">
        {error ? (
          <div className="text-center py-16">
            <p className="text-red-600 mb-3">{error}</p>
            <Button variant="outline" onClick={load}>Retry</Button>
          </div>
        ) : loading ? (
          <div className="text-center py-16"><Loader2 className="w-8 h-8 animate-spin text-emerald-600 mx-auto" /></div>
        ) : vendors.length === 0 ? (
          <div className="text-center py-16">
            <Building2 className="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500 mb-4">No vendors found</p>
            <Button onClick={() => setShowCreate(true)} className="gap-2 bg-emerald-600 hover:bg-emerald-700">
              <Plus className="w-4 h-4" /> Add First Vendor
            </Button>
          </div>
        ) : (
          <div className="bg-white rounded-xl border overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b text-left">
                  <th className="px-4 py-3 font-semibold text-gray-600">Vendor</th>
                  <th className="px-4 py-3 font-semibold text-gray-600">Contact</th>
                  <th className="px-4 py-3 font-semibold text-gray-600">Division</th>
                  <th className="px-4 py-3 font-semibold text-gray-600">Type</th>
                  <th className="px-4 py-3 font-semibold text-gray-600">Location</th>
                  <th className="px-4 py-3 font-semibold text-gray-600 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {vendors.map(v => (
                  <tr key={v.id} className="hover:bg-gray-50 transition">
                    <td className="px-4 py-3">
                      <p className="font-semibold text-gray-900">{v.name}</p>
                      {v.name_ar && <p className="text-xs text-gray-500 font-normal" dir="rtl">{v.name_ar}</p>}
                      {v.contact_name && <p className="text-xs text-gray-400">{v.contact_name}</p>}
                    </td>
                    <td className="px-4 py-3">
                      {v.phone && (
                        <p className="flex items-center gap-1 text-xs text-gray-700">
                          <Phone className="w-3 h-3 text-gray-400" /> {v.phone}
                        </p>
                      )}
                      {v.email && (
                        <p className="flex items-center gap-1 text-xs text-gray-500">
                          <Mail className="w-3 h-3 text-gray-400" /> {v.email}
                        </p>
                      )}
                      {v.whatsapp && <p className="text-xs text-green-600">WA: {v.whatsapp}</p>}
                    </td>
                    <td className="px-4 py-3">
                      {v.division ? (
                        <span className="capitalize text-gray-700 text-xs">{v.division}</span>
                      ) : <span className="text-gray-400 text-xs">—</span>}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${CONTACT_TYPE_COLORS[v.contact_type] ?? 'bg-gray-100 text-gray-700'}`}>
                        {v.contact_type}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-600">
                      {[v.city, v.country_name].filter(Boolean).join(', ') || '—'}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-end gap-1">
                        <button onClick={() => setEditVendor(v)}
                          className="p-1.5 rounded-lg text-gray-400 hover:text-emerald-600 hover:bg-emerald-50 transition" title="Edit">
                          <Pencil className="w-4 h-4" />
                        </button>
                        <button onClick={() => setDeleteTarget(v)}
                          className="p-1.5 rounded-lg text-gray-400 hover:text-red-600 hover:bg-red-50 transition" title="Delete">
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {totalPages > 1 && (
              <div className="flex items-center justify-between px-4 py-3 border-t bg-gray-50">
                <p className="text-sm text-gray-500">Page {page} of {totalPages} · {total} total</p>
                <div className="flex gap-1">
                  <button disabled={page <= 1} onClick={() => setPage(p => p - 1)}
                    className="p-1.5 rounded-lg text-gray-500 hover:bg-gray-200 disabled:opacity-30 transition">
                    <ChevronLeft className="w-4 h-4" />
                  </button>
                  <button disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}
                    className="p-1.5 rounded-lg text-gray-500 hover:bg-gray-200 disabled:opacity-30 transition">
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Create */}
      {showCreate && (
        <VendorForm
          title="New Vendor"
          onSave={doCreate}
          onClose={() => setShowCreate(false)}
        />
      )}

      {/* Edit */}
      {editVendor && (
        <VendorForm
          title={`Edit: ${editVendor.name}`}
          initial={editVendor as unknown as Partial<VendorCreateInput>}
          onSave={doEdit}
          onClose={() => setEditVendor(null)}
        />
      )}

      {/* Delete Confirm */}
      {deleteTarget && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl p-6 max-w-sm w-full">
            <h3 className="text-base font-bold text-gray-900 mb-2">Delete Vendor</h3>
            <p className="text-sm text-gray-600 mb-4">
              Are you sure you want to delete <strong>{deleteTarget.name}</strong>? This cannot be undone.
            </p>
            <div className="flex justify-end gap-3">
              <Button variant="outline" onClick={() => setDeleteTarget(null)}>Cancel</Button>
              <Button variant="destructive" onClick={doDelete} disabled={deleteBusy}>
                {deleteBusy ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Trash2 className="w-4 h-4 mr-2" />} Delete
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
