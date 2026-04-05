// ============================================================
// Purchase Orders — Full CRUD Container
// ============================================================
import { useState, useEffect, useCallback, useRef } from 'react';
import {
  Plus, Search, RefreshCw, Trash2, Eye, ChevronLeft, ChevronRight,
  CheckCircle2, Truck, Package, XCircle, RotateCcw, Loader2,
  FileText, MessageSquare, Paperclip, X, Send, Upload,
} from 'lucide-react';
import { Button }   from '../../../components/ui/button';
import { Input }    from '../../../components/ui/input';
import { Badge }    from '../../../components/ui/badge';
import { useSupplyStore } from '../store/supplyStore';
import supplyApi          from '../../../services/supplyApi';
import type { Po, PoLine, PoLineInput, PoCreateInput, PoStatus, Vendor, Attachment, Comment } from '../../../types/supply';

// ─────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────
const STATUS_META: Record<PoStatus, { label: string; color: string }> = {
  draft:     { label: 'Draft',     color: 'bg-gray-100 text-gray-700' },
  confirmed: { label: 'Confirmed', color: 'bg-blue-100 text-blue-700' },
  shipped:   { label: 'Shipped',   color: 'bg-amber-100 text-amber-700' },
  received:  { label: 'Received',  color: 'bg-green-100 text-green-700' },
  cancelled: { label: 'Cancelled', color: 'bg-red-100 text-red-700' },
};

function StatusBadge({ status }: { status: PoStatus }) {
  const meta = STATUS_META[status] ?? { label: status, color: 'bg-gray-100 text-gray-700' };
  return <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${meta.color}`}>{meta.label}</span>;
}

function fmt(n: number) { return n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }); }

// ─────────────────────────────────────────────────────────────
// Login Gate
// ─────────────────────────────────────────────────────────────
function LoginForm({ onLogin }: { onLogin: () => void }) {
  const [user, setUser]     = useState('admin');
  const [pass, setPass]     = useState('admin');
  const [err,  setErr]      = useState('');
  const [busy, setBusy]     = useState(false);
  const store = useSupplyStore();

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true); setErr('');
    const res = await supplyApi.login(user, pass);
    if (res?.success && res.data?.access_token) {
      store.setToken(res.data.access_token);
      onLogin();
    } else {
      setErr(res?.error ?? 'Invalid credentials');
    }
    setBusy(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
      <div className="bg-white rounded-2xl shadow-xl p-8 w-full max-w-sm">
        <div className="flex items-center gap-3 mb-8">
          <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center">
            <Package className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-gray-900">Supply Chain</h1>
            <p className="text-xs text-gray-500">Purchase Orders</p>
          </div>
        </div>
        <form onSubmit={submit} className="space-y-4">
          <div>
            <label className="text-sm font-medium text-gray-700 block mb-1">Username</label>
            <Input value={user} onChange={e => setUser(e.target.value)} placeholder="admin" required />
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700 block mb-1">Password</label>
            <Input type="password" value={pass} onChange={e => setPass(e.target.value)} placeholder="••••••••" required />
          </div>
          {err && <p className="text-sm text-red-600 bg-red-50 px-3 py-2 rounded-lg">{err}</p>}
          <Button type="submit" className="w-full" disabled={busy}>
            {busy ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
            Sign In
          </Button>
        </form>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// Create PO Modal
// ─────────────────────────────────────────────────────────────
function CreatePoModal({ onClose, onCreated }: { onClose: () => void; onCreated: (po: Po) => void }) {
  const [name,        setName]        = useState(`PO-${Date.now()}`);
  const [vendorSearch,setVendorSearch]= useState('');
  const [selectedVendor, setSelectedVendor] = useState<Vendor | null>(null);
  const [division,    setDivision]    = useState<'europe' | 'china' | ''>('');
  const [lines,       setLines]       = useState<PoLineInput[]>([
    { product_name: '', item_code: '', uom: '', quantity: 1, unit_price: 0 },
  ]);
  const [vendors,     setVendors]     = useState<Vendor[]>([]);
  const [vLoading,    setVLoading]    = useState(false);
  const [busy,        setBusy]        = useState(false);
  const [error,       setError]       = useState('');

  const searchVendors = useCallback(async (q: string) => {
    setVLoading(true);
    const res = await supplyApi.vendorList(q, 1, 20);
    if (res?.success) setVendors(res.data?.items ?? []);
    setVLoading(false);
  }, []);

  useEffect(() => { searchVendors(''); }, [searchVendors]);

  const addLine = () => setLines(l => [...l, { product_name: '', item_code: '', uom: '', quantity: 1, unit_price: 0 }]);
  const removeLine = (i: number) => setLines(l => l.filter((_, idx) => idx !== i));
  const updateLine = (i: number, k: keyof PoLineInput, v: string | number) =>
    setLines(l => l.map((ln, idx) => idx === i ? { ...ln, [k]: v } : ln));

  const lineTotal = lines.reduce((s, l) => s + (Number(l.quantity) || 0) * (Number(l.unit_price) || 0), 0);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return setError('PO name is required');
    if (!selectedVendor) return setError('Select a vendor');
    const validLines = lines.filter(l => l.product_name || l.item_code);
    if (!validLines.length) return setError('Add at least one product line');

    setBusy(true); setError('');
    const input: PoCreateInput = {
      name: name.trim(),
      vendor_customer_id: selectedVendor.id,
      lines: validLines.map(l => ({
        product_name: l.product_name || undefined,
        item_code:    l.item_code    || undefined,
        uom:          l.uom         || undefined,
        quantity:     Number(l.quantity)   || 1,
        unit_price:   Number(l.unit_price) || 0,
      })),
      ...(division ? { division } : {}),
    };
    const res = await supplyApi.poCreate(input);
    if (res?.success) {
      onCreated(res.data);
    } else {
      setError(res?.error ?? 'Failed to create PO');
    }
    setBusy(false);
  };

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
            <Plus className="w-5 h-5 text-blue-600" /> New Purchase Order
          </h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 transition"><X className="w-5 h-5" /></button>
        </div>

        <form onSubmit={submit} className="flex flex-col flex-1 overflow-hidden">
          <div className="flex-1 overflow-y-auto px-6 py-4 space-y-5">
            {/* PO Name */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-gray-700 block mb-1">PO Reference *</label>
                <Input value={name} onChange={e => setName(e.target.value)} placeholder="PO-2026-001" required />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 block mb-1">Division</label>
                <select
                  className="w-full h-9 rounded-md border border-input bg-background px-3 py-1 text-sm"
                  value={division}
                  onChange={e => setDivision(e.target.value as 'europe' | 'china' | '')}
                >
                  <option value="">— Any —</option>
                  <option value="europe">Europe</option>
                  <option value="china">China</option>
                </select>
              </div>
            </div>

            {/* Vendor Search */}
            <div>
              <label className="text-sm font-medium text-gray-700 block mb-1">Vendor / Contact *</label>
              {selectedVendor ? (
                <div className="flex items-center gap-2 p-2.5 bg-blue-50 rounded-lg border border-blue-200">
                  <div className="flex-1">
                    <p className="text-sm font-medium text-blue-900">{selectedVendor.name}</p>
                    <p className="text-xs text-blue-600">{selectedVendor.phone || selectedVendor.email || 'No contact info'}</p>
                  </div>
                  <button type="button" onClick={() => setSelectedVendor(null)} className="text-blue-400 hover:text-blue-700">
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ) : (
                <div>
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <Input
                      className="pl-9"
                      placeholder="Search vendors..."
                      value={vendorSearch}
                      onChange={e => { setVendorSearch(e.target.value); searchVendors(e.target.value); }}
                    />
                  </div>
                  {vLoading ? (
                    <div className="mt-2 text-center py-4"><Loader2 className="w-4 h-4 animate-spin mx-auto text-gray-400" /></div>
                  ) : vendors.length > 0 ? (
                    <div className="mt-1 border rounded-lg divide-y max-h-40 overflow-y-auto">
                      {vendors.map(v => (
                        <button
                          key={v.id} type="button"
                          className="w-full text-left px-3 py-2 hover:bg-blue-50 transition"
                          onClick={() => { setSelectedVendor(v); setVendorSearch(''); }}
                        >
                          <p className="text-sm font-medium text-gray-900">{v.name}</p>
                          <p className="text-xs text-gray-500">{v.phone || v.email || v.city || 'No info'}</p>
                        </button>
                      ))}
                    </div>
                  ) : null}
                </div>
              )}
            </div>

            {/* Lines */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-medium text-gray-700">Order Lines</label>
                <button type="button" onClick={addLine} className="text-xs text-blue-600 hover:text-blue-800 flex items-center gap-1">
                  <Plus className="w-3 h-3" /> Add Line
                </button>
              </div>
              <div className="space-y-2">
                {lines.map((ln, i) => (
                  <div key={i} className="grid grid-cols-12 gap-2 items-center bg-gray-50 rounded-lg p-2">
                    <div className="col-span-4">
                      <Input
                        placeholder="Product name"
                        value={ln.product_name}
                        onChange={e => updateLine(i, 'product_name', e.target.value)}
                        className="text-sm h-8"
                      />
                    </div>
                    <div className="col-span-2">
                      <Input
                        placeholder="Code"
                        value={ln.item_code}
                        onChange={e => updateLine(i, 'item_code', e.target.value)}
                        className="text-sm h-8"
                      />
                    </div>
                    <div className="col-span-2">
                      <Input
                        placeholder="UoM"
                        value={ln.uom}
                        onChange={e => updateLine(i, 'uom', e.target.value)}
                        className="text-sm h-8"
                      />
                    </div>
                    <div className="col-span-1">
                      <Input
                        type="number" min="0" placeholder="Qty"
                        value={ln.quantity}
                        onChange={e => updateLine(i, 'quantity', parseFloat(e.target.value) || 0)}
                        className="text-sm h-8"
                      />
                    </div>
                    <div className="col-span-2">
                      <Input
                        type="number" min="0" step="0.01" placeholder="Price"
                        value={ln.unit_price}
                        onChange={e => updateLine(i, 'unit_price', parseFloat(e.target.value) || 0)}
                        className="text-sm h-8"
                      />
                    </div>
                    <div className="col-span-1 flex justify-center">
                      {lines.length > 1 && (
                        <button type="button" onClick={() => removeLine(i)} className="text-red-400 hover:text-red-600">
                          <X className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
              <div className="flex justify-end mt-2">
                <span className="text-sm font-semibold text-gray-700">Total: {fmt(lineTotal)}</span>
              </div>
            </div>

            {error && <p className="text-sm text-red-600 bg-red-50 px-3 py-2 rounded-lg">{error}</p>}
          </div>

          {/* Footer */}
          <div className="flex justify-end gap-3 px-6 py-4 border-t bg-gray-50">
            <Button type="button" variant="outline" onClick={onClose}>Cancel</Button>
            <Button type="submit" disabled={busy} className="min-w-[120px]">
              {busy ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Plus className="w-4 h-4 mr-2" />}
              Create PO
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// PO Detail Sheet (right drawer)
// ─────────────────────────────────────────────────────────────
function PoDetailSheet({ po: initialPo, onClose, onUpdated }: {
  po: Po;
  onClose: () => void;
  onUpdated: (po: Po) => void;
}) {
  const [po,       setPo]       = useState<Po>(initialPo);
  const [tab,      setTab]      = useState<'lines' | 'comments' | 'attachments'>('lines');
  const [busy,     setBusy]     = useState<string | null>(null);
  const [comments, setComments] = useState<Comment[]>([]);
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [newComment, setNewComment] = useState('');
  const [isNote,   setIsNote]   = useState(false);
  const [addingLine, setAddingLine] = useState(false);
  const [newLine,  setNewLine]  = useState<PoLineInput>({ product_name: '', item_code: '', uom: '', quantity: 1, unit_price: 0 });
  const fileRef = useRef<HTMLInputElement>(null);

  const reload = useCallback(async () => {
    const res = await supplyApi.poGet(po.id);
    if (res?.success) { setPo(res.data); onUpdated(res.data); }
  }, [po.id, onUpdated]);

  useEffect(() => { setPo(initialPo); }, [initialPo]);

  useEffect(() => {
    if (tab === 'comments')    supplyApi.poCommentList(po.id).then(r => { if (r?.success) setComments(r.data?.items ?? []); });
    if (tab === 'attachments') supplyApi.poAttachList(po.id).then(r => { if (r?.success) setAttachments(r.data?.attachments ?? []); });
  }, [tab, po.id]);

  // Status transitions
  const transition = async (action: string, fn: (id: number) => Promise<{ success: boolean; data: Po; error?: string }>) => {
    setBusy(action);
    const res = await fn(po.id);
    if (res?.success) { setPo(res.data); onUpdated(res.data); }
    setBusy(null);
  };

  // Delete line
  const deleteLine = async (lineId: number) => {
    setBusy(`line-${lineId}`);
    const res = await supplyApi.poLineDelete(po.id, lineId);
    if (res?.success) reload();
    setBusy(null);
  };

  // Add line
  const submitLine = async () => {
    if (!newLine.product_name && !newLine.item_code) return;
    setBusy('add-line');
    await supplyApi.poLineAdd(po.id, { ...newLine, quantity: Number(newLine.quantity), unit_price: Number(newLine.unit_price) });
    setNewLine({ product_name: '', item_code: '', uom: '', quantity: 1, unit_price: 0 });
    setAddingLine(false);
    reload();
    setBusy(null);
  };

  // Add comment
  const submitComment = async () => {
    if (!newComment.trim()) return;
    setBusy('comment');
    const res = await supplyApi.poCommentAdd(po.id, newComment.trim(), isNote);
    if (res?.success) {
      setComments(c => [res.data, ...c]);
      setNewComment('');
    }
    setBusy(null);
  };

  // Upload attachment(s)
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files ?? []);
    if (!files.length) return;
    setBusy('upload');
    const res = await supplyApi.poAttachUploadMultiple(po.id, files);
    if (res?.success) {
      const newAtts = res.data?.attachments ?? [];
      setAttachments(a => [...newAtts, ...a]);
    }
    setBusy(null);
    if (fileRef.current) fileRef.current.value = '';
  };

  // Delete attachment
  const deleteAttachment = async (attId: number) => {
    setBusy(`att-${attId}`);
    await supplyApi.poAttachDelete(po.id, attId);
    setAttachments(a => a.filter(x => x.id !== attId));
    setBusy(null);
  };

  const canConfirm  = po.status === 'draft';
  const canShip     = po.status === 'confirmed';
  const canReceive  = po.status === 'shipped';
  const canCancel   = ['draft', 'confirmed', 'shipped'].includes(po.status);
  const canReopen   = po.status === 'cancelled';

  return (
    <div className="fixed inset-0 bg-black/40 z-40 flex justify-end">
      <div className="bg-white w-full max-w-2xl h-full flex flex-col shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b bg-gray-50">
          <div>
            <h2 className="text-lg font-bold text-gray-900">{po.name}</h2>
            <div className="flex items-center gap-2 mt-0.5">
              <StatusBadge status={po.status} />
              <span className="text-sm text-gray-500">{po.vendor_customer_name || po.vendor_name}</span>
            </div>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-700 transition"><X className="w-5 h-5" /></button>
        </div>

        {/* Status Actions */}
        <div className="flex gap-2 px-6 py-3 border-b bg-white flex-wrap">
          {canConfirm && (
            <button onClick={() => transition('confirm', supplyApi.poConfirm)}
              disabled={!!busy}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 transition">
              {busy === 'confirm' ? <Loader2 className="w-3 h-3 animate-spin" /> : <CheckCircle2 className="w-3 h-3" />}
              Confirm
            </button>
          )}
          {canShip && (
            <button onClick={() => transition('ship', supplyApi.poShip)}
              disabled={!!busy}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-amber-500 text-white hover:bg-amber-600 disabled:opacity-50 transition">
              {busy === 'ship' ? <Loader2 className="w-3 h-3 animate-spin" /> : <Truck className="w-3 h-3" />}
              Mark Shipped
            </button>
          )}
          {canReceive && (
            <button onClick={() => transition('receive', supplyApi.poReceive)}
              disabled={!!busy}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-green-600 text-white hover:bg-green-700 disabled:opacity-50 transition">
              {busy === 'receive' ? <Loader2 className="w-3 h-3 animate-spin" /> : <Package className="w-3 h-3" />}
              Mark Received
            </button>
          )}
          {canCancel && (
            <button onClick={() => transition('cancel', supplyApi.poCancel)}
              disabled={!!busy}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-red-100 text-red-700 hover:bg-red-200 disabled:opacity-50 transition">
              {busy === 'cancel' ? <Loader2 className="w-3 h-3 animate-spin" /> : <XCircle className="w-3 h-3" />}
              Cancel
            </button>
          )}
          {canReopen && (
            <button onClick={() => transition('reopen', supplyApi.poReopen)}
              disabled={!!busy}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-gray-100 text-gray-700 hover:bg-gray-200 disabled:opacity-50 transition">
              {busy === 'reopen' ? <Loader2 className="w-3 h-3 animate-spin" /> : <RotateCcw className="w-3 h-3" />}
              Reopen
            </button>
          )}
          <div className="ml-auto text-sm font-bold text-gray-900">Total: {fmt(po.total_amount)}</div>
        </div>

        {/* Tabs */}
        <div className="flex border-b px-6">
          {(['lines', 'comments', 'attachments'] as const).map(t => (
            <button key={t} onClick={() => setTab(t)}
              className={`px-4 py-2.5 text-sm font-medium border-b-2 transition capitalize ${
                tab === t ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}>
              {t === 'lines'       && <span className="flex items-center gap-1.5"><FileText className="w-3.5 h-3.5" />Lines ({po.line_count})</span>}
              {t === 'comments'    && <span className="flex items-center gap-1.5"><MessageSquare className="w-3.5 h-3.5" />Comments</span>}
              {t === 'attachments' && <span className="flex items-center gap-1.5"><Paperclip className="w-3.5 h-3.5" />Files</span>}
            </button>
          ))}
        </div>

        {/* Tab content */}
        <div className="flex-1 overflow-y-auto">

          {/* Lines Tab */}
          {tab === 'lines' && (
            <div className="px-6 py-4 space-y-3">
              {po.lines.map(line => (
                <div key={line.id} className="flex items-start gap-3 p-3 bg-gray-50 rounded-xl">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">{line.product_name || line.item_code}</p>
                    <div className="flex items-center gap-3 mt-1 text-xs text-gray-500">
                      {line.item_code && <span>#{line.item_code}</span>}
                      {line.uom       && <span>{line.uom}</span>}
                      <span>{line.quantity} × {fmt(line.unit_price)}</span>
                    </div>
                  </div>
                  <div className="text-right shrink-0">
                    <p className="text-sm font-bold text-gray-900">{fmt(line.total_price)}</p>
                    {po.status !== 'received' && (
                      <button
                        onClick={() => deleteLine(line.id)}
                        disabled={busy === `line-${line.id}`}
                        className="mt-1 text-red-400 hover:text-red-600 disabled:opacity-40">
                        {busy === `line-${line.id}` ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Trash2 className="w-3.5 h-3.5" />}
                      </button>
                    )}
                  </div>
                </div>
              ))}

              {/* Add line inline */}
              {po.status !== 'received' && po.status !== 'cancelled' && (
                addingLine ? (
                  <div className="border rounded-xl p-3 space-y-2 bg-blue-50">
                    <div className="grid grid-cols-2 gap-2">
                      <Input placeholder="Product name" value={newLine.product_name} onChange={e => setNewLine(l => ({ ...l, product_name: e.target.value }))} className="text-sm h-8" />
                      <Input placeholder="Item code"    value={newLine.item_code}    onChange={e => setNewLine(l => ({ ...l, item_code: e.target.value }))}    className="text-sm h-8" />
                    </div>
                    <div className="grid grid-cols-3 gap-2">
                      <Input placeholder="UoM"      value={newLine.uom}        onChange={e => setNewLine(l => ({ ...l, uom: e.target.value }))}                     className="text-sm h-8" />
                      <Input type="number" placeholder="Qty"   value={newLine.quantity}   onChange={e => setNewLine(l => ({ ...l, quantity: parseFloat(e.target.value) || 1 }))}    className="text-sm h-8" />
                      <Input type="number" placeholder="Price" value={newLine.unit_price} onChange={e => setNewLine(l => ({ ...l, unit_price: parseFloat(e.target.value) || 0 }))}  className="text-sm h-8" />
                    </div>
                    <div className="flex justify-end gap-2">
                      <Button type="button" variant="outline" size="sm" onClick={() => setAddingLine(false)}>Cancel</Button>
                      <Button type="button" size="sm" onClick={submitLine} disabled={busy === 'add-line'}>
                        {busy === 'add-line' ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : null} Add
                      </Button>
                    </div>
                  </div>
                ) : (
                  <button onClick={() => setAddingLine(true)} className="w-full flex items-center justify-center gap-2 py-2.5 border-2 border-dashed border-gray-200 rounded-xl text-sm text-gray-500 hover:border-blue-400 hover:text-blue-600 transition">
                    <Plus className="w-4 h-4" /> Add Line
                  </button>
                )
              )}
            </div>
          )}

          {/* Comments Tab */}
          {tab === 'comments' && (
            <div className="flex flex-col h-full">
              <div className="flex-1 px-6 py-4 space-y-3 overflow-y-auto">
                {comments.length === 0 && <p className="text-center text-sm text-gray-400 py-8">No comments yet.</p>}
                {comments.map(c => (
                  <div key={c.id} className={`p-3 rounded-xl text-sm ${c.type === 'note' ? 'bg-amber-50 border border-amber-100' : 'bg-gray-50'}`}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-medium text-gray-800">{c.author_name}</span>
                      <div className="flex items-center gap-2">
                        {c.type === 'note' && <span className="text-xs bg-amber-200 text-amber-800 px-1.5 py-0.5 rounded">Note</span>}
                        <span className="text-xs text-gray-400">{new Date(c.created_at).toLocaleString()}</span>
                      </div>
                    </div>
                    <p className="text-gray-700">{c.body}</p>
                  </div>
                ))}
              </div>
              <div className="px-6 py-3 border-t space-y-2 bg-white">
                <div className="flex items-center gap-2">
                  <label className="flex items-center gap-1.5 text-xs text-gray-600 cursor-pointer">
                    <input type="checkbox" checked={isNote} onChange={e => setIsNote(e.target.checked)} className="rounded" />
                    Internal Note
                  </label>
                </div>
                <div className="flex gap-2">
                  <Input
                    placeholder="Write a comment..."
                    value={newComment}
                    onChange={e => setNewComment(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && !e.shiftKey && submitComment()}
                    className="flex-1 text-sm"
                  />
                  <Button size="sm" onClick={submitComment} disabled={!newComment.trim() || busy === 'comment'}>
                    {busy === 'comment' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
                  </Button>
                </div>
              </div>
            </div>
          )}

          {/* Attachments Tab */}
          {tab === 'attachments' && (
            <div className="px-6 py-4 space-y-3">
              {/* Upload button */}
              <div>
                <input ref={fileRef} type="file" multiple className="hidden" onChange={handleFileUpload} />
                <button
                  onClick={() => fileRef.current?.click()}
                  disabled={busy === 'upload'}
                  className="w-full flex items-center justify-center gap-2 py-2.5 border-2 border-dashed border-gray-200 rounded-xl text-sm text-gray-500 hover:border-blue-400 hover:text-blue-600 transition disabled:opacity-50"
                >
                  {busy === 'upload' ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
                  {busy === 'upload' ? 'Uploading...' : 'Click to upload files'}
                </button>
                <p className="text-xs text-gray-400 text-center mt-1">PDF, Images, Office files — max 25 MB each · multiple files allowed</p>
              </div>

              {attachments.length === 0 && <p className="text-center text-sm text-gray-400 py-4">No attachments.</p>}
              {attachments.map(a => (
                <div key={a.id} className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl">
                  <FileText className="w-8 h-8 text-blue-500 shrink-0" />
                  <div className="flex-1 min-w-0">
                    <a href={a.url} target="_blank" rel="noreferrer" className="text-sm font-medium text-blue-600 hover:underline truncate block">{a.name}</a>
                    <p className="text-xs text-gray-400">{a.mimetype} · {a.uploaded_by_name}</p>
                  </div>
                  <button
                    onClick={() => deleteAttachment(a.id)}
                    disabled={busy === `att-${a.id}`}
                    className="text-red-400 hover:text-red-600 disabled:opacity-40">
                    {busy === `att-${a.id}` ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// Delete Confirm
// ─────────────────────────────────────────────────────────────
function DeleteConfirm({ po, onClose, onDeleted }: { po: Po; onClose: () => void; onDeleted: () => void }) {
  const [busy, setBusy] = useState(false);
  const [err,  setErr]  = useState('');

  const confirm = async () => {
    setBusy(true);
    const res = await supplyApi.poDelete(po.id);
    if (res?.success) { onDeleted(); }
    else { setErr(res?.error ?? 'Delete failed'); setBusy(false); }
  };

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl p-6 max-w-sm w-full">
        <h3 className="text-base font-bold text-gray-900 mb-2">Delete Purchase Order</h3>
        <p className="text-sm text-gray-600 mb-1">Are you sure you want to delete <strong>{po.name}</strong>?</p>
        <p className="text-xs text-amber-600 bg-amber-50 px-3 py-2 rounded-lg mb-4">Only draft or cancelled orders can be deleted.</p>
        {err && <p className="text-sm text-red-600 mb-3">{err}</p>}
        <div className="flex justify-end gap-3">
          <Button variant="outline" onClick={onClose}>Cancel</Button>
          <Button variant="destructive" onClick={confirm} disabled={busy}>
            {busy ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Trash2 className="w-4 h-4 mr-2" />}
            Delete
          </Button>
        </div>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// Main PO Container
// ─────────────────────────────────────────────────────────────
export function PoContainer() {
  const store = useSupplyStore();
  const [showLogin,  setShowLogin]  = useState(!store.token);
  const [showCreate, setShowCreate] = useState(false);
  const [detailPo,   setDetailPo]   = useState<Po | null>(null);
  const [deletePo,   setDeletePo]   = useState<Po | null>(null);
  const [searchDraft, setSearchDraft] = useState(store.filter.search ?? '');

  const loadPos = useCallback(async () => {
    store.setLoading(true);
    store.setError(null);
    const res = await supplyApi.poList(store.filter);
    if (res?.success) {
      store.setPOs(res.data?.items ?? [], res.data?.total ?? 0);
    } else {
      if (res?.error?.toLowerCase().includes('unauthorized')) setShowLogin(true);
      else store.setError(res?.error ?? 'Failed to load purchase orders');
    }
    store.setLoading(false);
  }, [store]);

  useEffect(() => { if (!showLogin) loadPos(); }, [showLogin, store.filter, loadPos]);

  if (showLogin) return <LoginForm onLogin={() => setShowLogin(false)} />;

  const totalPages = Math.ceil(store.total / (store.filter.per_page ?? 20));
  const currentPage = store.filter.page ?? 1;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* ── Top Bar ──────────────────────────────────────── */}
      <div className="bg-white border-b px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
            <Package className="w-4 h-4 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-900">Purchase Orders</h1>
            <p className="text-xs text-gray-500">{store.total} orders total</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={loadPos} className="p-2 text-gray-400 hover:text-gray-700 transition rounded-lg hover:bg-gray-100">
            <RefreshCw className={`w-4 h-4 ${store.loading ? 'animate-spin' : ''}`} />
          </button>
          <Button onClick={() => setShowCreate(true)} className="gap-2">
            <Plus className="w-4 h-4" /> New PO
          </Button>
        </div>
      </div>

      {/* ── Filters ───────────────────────────────────────── */}
      <div className="bg-white border-b px-6 py-3 flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <Input
            className="pl-9 h-8 text-sm"
            placeholder="Search by name or vendor..."
            value={searchDraft}
            onChange={e => setSearchDraft(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && store.setFilter({ search: searchDraft, page: 1 })}
          />
        </div>
        <select
          className="h-8 rounded-md border border-input bg-background px-3 py-0 text-sm"
          value={store.filter.status ?? ''}
          onChange={e => store.setFilter({ status: e.target.value as PoStatus | '', page: 1 })}
        >
          <option value="">All Statuses</option>
          <option value="draft">Draft</option>
          <option value="confirmed">Confirmed</option>
          <option value="shipped">Shipped</option>
          <option value="received">Received</option>
          <option value="cancelled">Cancelled</option>
        </select>
        <select
          className="h-8 rounded-md border border-input bg-background px-3 py-0 text-sm"
          value={store.filter.division ?? ''}
          onChange={e => store.setFilter({ division: e.target.value as 'europe' | 'china' | '', page: 1 })}
        >
          <option value="">All Divisions</option>
          <option value="europe">Europe</option>
          <option value="china">China</option>
        </select>
        {(store.filter.status || store.filter.search || store.filter.division) && (
          <button
            onClick={() => { store.setFilter({ status: '', search: '', division: '', page: 1 }); setSearchDraft(''); }}
            className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-800 px-2 py-1 rounded-lg hover:bg-gray-100 transition"
          >
            <X className="w-3 h-3" /> Clear filters
          </button>
        )}
      </div>

      {/* ── Table ─────────────────────────────────────────── */}
      <div className="px-6 py-4">
        {store.error ? (
          <div className="text-center py-16">
            <p className="text-red-600 mb-3">{store.error}</p>
            <Button variant="outline" onClick={loadPos}>Retry</Button>
          </div>
        ) : store.loading ? (
          <div className="text-center py-16"><Loader2 className="w-8 h-8 animate-spin text-blue-600 mx-auto" /></div>
        ) : store.pos.length === 0 ? (
          <div className="text-center py-16">
            <Package className="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500 mb-4">No purchase orders found</p>
            <Button onClick={() => setShowCreate(true)} className="gap-2"><Plus className="w-4 h-4" /> Create First PO</Button>
          </div>
        ) : (
          <div className="bg-white rounded-xl border overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b text-left">
                  <th className="px-4 py-3 font-semibold text-gray-600">PO Reference</th>
                  <th className="px-4 py-3 font-semibold text-gray-600">Vendor</th>
                  <th className="px-4 py-3 font-semibold text-gray-600">Division</th>
                  <th className="px-4 py-3 font-semibold text-gray-600">Status</th>
                  <th className="px-4 py-3 font-semibold text-gray-600 text-right">Total</th>
                  <th className="px-4 py-3 font-semibold text-gray-600 text-center">Lines</th>
                  <th className="px-4 py-3 font-semibold text-gray-600">Created</th>
                  <th className="px-4 py-3 font-semibold text-gray-600 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {store.pos.map(po => (
                  <tr key={po.id} className="hover:bg-gray-50 transition cursor-pointer" onClick={() => setDetailPo(po)}>
                    <td className="px-4 py-3">
                      <span className="font-semibold text-blue-700">{po.name}</span>
                    </td>
                    <td className="px-4 py-3 max-w-[160px]">
                      <p className="font-medium text-gray-900 truncate">{po.vendor_customer_name || po.vendor_name || '—'}</p>
                      {po.vendor_customer_phone && <p className="text-xs text-gray-500">{po.vendor_customer_phone}</p>}
                    </td>
                    <td className="px-4 py-3">
                      {po.division ? <span className="capitalize text-gray-700">{po.division}</span> : <span className="text-gray-400">—</span>}
                    </td>
                    <td className="px-4 py-3"><StatusBadge status={po.status} /></td>
                    <td className="px-4 py-3 text-right font-semibold text-gray-900">{fmt(po.total_amount)}</td>
                    <td className="px-4 py-3 text-center">
                      <span className="inline-block bg-gray-100 text-gray-700 rounded-full px-2 py-0.5 text-xs font-medium">{po.line_count}</span>
                    </td>
                    <td className="px-4 py-3 text-gray-500 text-xs">{new Date(po.created_at).toLocaleDateString()}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-end gap-1" onClick={e => e.stopPropagation()}>
                        <button
                          onClick={() => setDetailPo(po)}
                          className="p-1.5 rounded-lg text-gray-400 hover:text-blue-600 hover:bg-blue-50 transition">
                          <Eye className="w-4 h-4" />
                        </button>
                        {(po.status === 'draft' || po.status === 'cancelled') && (
                          <button
                            onClick={() => setDeletePo(po)}
                            className="p-1.5 rounded-lg text-gray-400 hover:text-red-600 hover:bg-red-50 transition">
                            <Trash2 className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between px-4 py-3 border-t bg-gray-50">
                <p className="text-sm text-gray-500">
                  Page {currentPage} of {totalPages} · {store.total} total
                </p>
                <div className="flex gap-1">
                  <button
                    disabled={currentPage <= 1}
                    onClick={() => store.setFilter({ page: currentPage - 1 })}
                    className="p-1.5 rounded-lg text-gray-500 hover:bg-gray-200 disabled:opacity-30 transition">
                    <ChevronLeft className="w-4 h-4" />
                  </button>
                  <button
                    disabled={currentPage >= totalPages}
                    onClick={() => store.setFilter({ page: currentPage + 1 })}
                    className="p-1.5 rounded-lg text-gray-500 hover:bg-gray-200 disabled:opacity-30 transition">
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* ── Modals ───────────────────────────────────────── */}
      {showCreate && (
        <CreatePoModal
          onClose={() => setShowCreate(false)}
          onCreated={(po) => {
            store.setPOs([po, ...store.pos], store.total + 1);
            setShowCreate(false);
            setDetailPo(po);
          }}
        />
      )}

      {detailPo && (
        <PoDetailSheet
          po={detailPo}
          onClose={() => setDetailPo(null)}
          onUpdated={(po) => { store.updatePoInList(po); setDetailPo(po); }}
        />
      )}

      {deletePo && (
        <DeleteConfirm
          po={deletePo}
          onClose={() => setDeletePo(null)}
          onDeleted={() => { store.removePoFromList(deletePo.id); setDeletePo(null); }}
        />
      )}
    </div>
  );
}
