// ============================================================
// Containers — Full Management Panel
// ============================================================
import { useState, useEffect, useCallback, useRef } from 'react';
import {
  Plus, Search, RefreshCw, Trash2, Eye, ChevronLeft, ChevronRight,
  Loader2, X, Ship, Anchor, Package2, FileText, MessageSquare,
  Paperclip, Upload, Send, AlertTriangle, User, Check, Pencil,
} from 'lucide-react';
import { Button } from '../../../components/ui/button';
import { Input }  from '../../../components/ui/input';
import supplyApi  from '../../../services/supplyApi';
import type {
  Container, ContainerStatus, ContainerCreateInput, ContainerListFilter,
  Attachment, Comment, Penalty, PenaltyInput, PenaltyType,
} from '../../../types/supply';

// ─────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────
const CONTAINER_STATUS_META: Record<ContainerStatus, { label: string; color: string; icon: React.ReactNode }> = {
  waiting:   { label: 'Waiting',   color: 'bg-gray-100 text-gray-700',   icon: <Package2 className="w-3 h-3" /> },
  active:    { label: 'Active',    color: 'bg-blue-100 text-blue-700',   icon: <Ship className="w-3 h-3" /> },
  at_port:   { label: 'At Port',   color: 'bg-amber-100 text-amber-700', icon: <Anchor className="w-3 h-3" /> },
  completed: { label: 'Completed', color: 'bg-green-100 text-green-700', icon: <Check className="w-3 h-3" /> },
};

function ContainerStatusBadge({ status }: { status: ContainerStatus }) {
  const meta = CONTAINER_STATUS_META[status] ?? { label: status, color: 'bg-gray-100 text-gray-700', icon: null };
  return (
    <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${meta.color}`}>
      {meta.icon} {meta.label}
    </span>
  );
}

const PENALTY_LABELS: Record<PenaltyType, string> = {
  storage:   'Storage Fee',
  damage:    'Damage',
  late:      'Late Fee',
  customs:   'Customs',
  demurrage: 'Demurrage',
  other:     'Other',
};

// ─────────────────────────────────────────────────────────────
// Create Container Modal
// ─────────────────────────────────────────────────────────────
function CreateContainerModal({ onClose, onCreated }: {
  onClose:   () => void;
  onCreated: (c: Container) => void;
}) {
  const [vals, setVals] = useState<ContainerCreateInput>({
    name: '', container_number: '', bl_number: '',
    origin_location: '', destination_port: '', division: '',
    tracking_url: '', notes: '',
  });
  const [busy,  setBusy]  = useState(false);
  const [error, setError] = useState('');

  const set = (k: keyof ContainerCreateInput, v: string | number) =>
    setVals(p => ({ ...p, [k]: v }));

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!vals.name.trim()) return setError('Container name is required');
    setBusy(true); setError('');
    const res = await supplyApi.containerCreate(vals);
    if (res?.success) {
      onCreated(res.data);
    } else {
      setError(res?.error ?? 'Failed to create container');
    }
    setBusy(false);
  };

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] flex flex-col">
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <h2 className="text-base font-bold text-gray-900 flex items-center gap-2">
            <Plus className="w-4 h-4 text-blue-600" /> New Container
          </h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X className="w-5 h-5" /></button>
        </div>
        <form onSubmit={submit} className="flex flex-col flex-1 overflow-hidden">
          <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div className="col-span-2">
                <label className="text-sm font-medium text-gray-700 block mb-1">Container Name *</label>
                <Input value={vals.name} onChange={e => set('name', e.target.value)} placeholder="CONT-2026-001" required />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 block mb-1">Container #</label>
                <Input value={vals.container_number} onChange={e => set('container_number', e.target.value)} placeholder="TCKU1234567" />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 block mb-1">B/L Number</label>
                <Input value={vals.bl_number} onChange={e => set('bl_number', e.target.value)} placeholder="BL-2026-001" />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 block mb-1">Origin</label>
                <Input value={vals.origin_location} onChange={e => set('origin_location', e.target.value)} placeholder="Shanghai, CN" />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 block mb-1">Destination Port</label>
                <Input value={vals.destination_port} onChange={e => set('destination_port', e.target.value)} placeholder="Jeddah, SA" />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 block mb-1">Departure Date</label>
                <Input type="date" value={vals.departure_date ?? ''} onChange={e => set('departure_date', e.target.value)} />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 block mb-1">ETA</label>
                <Input type="date" value={vals.eta ?? ''} onChange={e => set('eta', e.target.value)} />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 block mb-1">Division</label>
                <select className="w-full h-9 rounded-md border border-input bg-background px-3 py-1 text-sm"
                  value={vals.division} onChange={e => set('division', e.target.value)}>
                  <option value="">— Any —</option>
                  <option value="europe">Europe</option>
                  <option value="china">China</option>
                </select>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 block mb-1">Tracking URL</label>
                <Input value={vals.tracking_url} onChange={e => set('tracking_url', e.target.value)} placeholder="https://..." />
              </div>
              <div className="col-span-2">
                <label className="text-sm font-medium text-gray-700 block mb-1">Notes</label>
                <textarea
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm min-h-[60px] resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={vals.notes} onChange={e => set('notes', e.target.value)} placeholder="Any notes..."
                />
              </div>
            </div>
            {error && <p className="text-sm text-red-600 bg-red-50 px-3 py-2 rounded-lg">{error}</p>}
          </div>
          <div className="flex justify-end gap-3 px-6 py-4 border-t bg-gray-50">
            <Button type="button" variant="outline" onClick={onClose}>Cancel</Button>
            <Button type="submit" disabled={busy}>
              {busy ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Plus className="w-4 h-4 mr-2" />}
              Create Container
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// Container Detail Sheet
// ─────────────────────────────────────────────────────────────
function ContainerDetailSheet({ container: initial, onClose, onUpdated }: {
  container: Container;
  onClose:   () => void;
  onUpdated: (c: Container) => void;
}) {
  type Tab = 'info' | 'attachments' | 'penalties' | 'comments';
  const [c,           setC]           = useState<Container>(initial);
  const [tab,         setTab]         = useState<Tab>('info');
  const [busy,        setBusy]        = useState<string | null>(null);
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [comments,    setComments]    = useState<Comment[]>([]);
  const [penalties,   setPenalties]   = useState<Penalty[]>([]);
  const [totalPenAmt, setTotalPenAmt] = useState(0);
  const [newComment,  setNewComment]  = useState('');
  const [isNote,      setIsNote]      = useState(false);
  // Penalty form
  const [penType,     setPenType]     = useState<PenaltyType>('storage');
  const [penAmount,   setPenAmount]   = useState('');
  const [penReason,   setPenReason]   = useState('');
  const [penDate,     setPenDate]     = useState('');
  const [showPenForm, setShowPenForm] = useState(false);
  // Driver form
  const [showDriverForm, setShowDriverForm] = useState(false);
  const [driverName,     setDriverName]     = useState(c.driver_name);
  const [driverPhone,    setDriverPhone]    = useState(c.driver_phone);
  const [showReminderForm, setShowReminderForm] = useState(false);
  const [reminderDate,     setReminderDate]     = useState(c.reminder_date?.slice(0, 16) ?? '');
  const [reminderNote,     setReminderNote]     = useState(c.reminder_note ?? '');
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => { setC(initial); }, [initial]);

  useEffect(() => {
    if (tab === 'attachments') supplyApi.containerAttachList(c.id).then(r => { if (r?.success) setAttachments(r.data?.attachments ?? []); });
    if (tab === 'comments')    supplyApi.containerCommentList(c.id).then(r => { if (r?.success) setComments(r.data?.items ?? []); });
    if (tab === 'penalties')   supplyApi.containerPenaltiesList(c.id).then(r => { if (r?.success) { setPenalties(r.data?.items ?? []); setTotalPenAmt(r.data?.total_amount ?? 0); } });
  }, [tab, c.id]);

  const reload = useCallback(async () => {
    const res = await supplyApi.containerGet(c.id);
    if (res?.success) { setC(res.data); onUpdated(res.data); }
  }, [c.id, onUpdated]);

  const markArrived = async () => {
    setBusy('arrived');
    const res = await supplyApi.containerMarkArrived(c.id);
    if (res?.success) { setC(res.data); onUpdated(res.data); }
    setBusy(null);
  };

  const markClearance = async () => {
    setBusy('clearance');
    const res = await supplyApi.containerClearanceDelivered(c.id);
    if (res?.success) { setC(res.data); onUpdated(res.data); }
    setBusy(null);
  };

  const assignDriver = async () => {
    if (!driverName.trim()) return;
    setBusy('driver');
    const res = await supplyApi.containerAssignDriver(c.id, { driver_name: driverName.trim(), driver_phone: driverPhone.trim() });
    if (res?.success) { setC(res.data); onUpdated(res.data); setShowDriverForm(false); }
    setBusy(null);
  };

  const saveReminder = async () => {
    setBusy('reminder');
    const res = await supplyApi.containerSetReminder(c.id, {
      reminder_date: reminderDate || undefined,
      reminder_note: reminderNote || undefined,
    });
    if (res?.success) { setC(res.data); onUpdated(res.data); setShowReminderForm(false); }
    setBusy(null);
  };

  const clearReminder = async () => {
    setBusy('clear-reminder');
    const res = await supplyApi.containerSetReminder(c.id, { clear_reminder: true });
    if (res?.success) { setC(res.data); onUpdated(res.data); setReminderDate(''); setReminderNote(''); }
    setBusy(null);
  };

  const unassignDriver = async () => {
    setBusy('unassign');
    const res = await supplyApi.containerUnassignDriver(c.id);
    if (res?.success) { setC(res.data); onUpdated(res.data); }
    setBusy(null);
  };

  const submitPenalty = async () => {
    const amt = parseFloat(penAmount);
    if (!amt || amt <= 0) return;
    setBusy('penalty');
    const input: PenaltyInput = { penalty_type: penType, amount: amt };
    if (penReason) input.reason = penReason;
    if (penDate)   input.penalty_date = penDate;
    const res = await supplyApi.containerAddPenalty(c.id, input);
    if (res?.success) {
      setPenalties(p => [...p, res.data]);
      setTotalPenAmt(t => t + amt);
      setPenAmount(''); setPenReason(''); setPenDate('');
      setShowPenForm(false);
    }
    setBusy(null);
  };

  const deletePenalty = async (penId: number, amt: number) => {
    setBusy(`pen-del-${penId}`);
    const res = await supplyApi.containerPenaltyDelete(c.id, penId);
    if (res?.success) { setPenalties(p => p.filter(x => x.id !== penId)); setTotalPenAmt(t => t - amt); }
    setBusy(null);
  };

  const submitComment = async () => {
    if (!newComment.trim()) return;
    setBusy('comment');
    const res = await supplyApi.containerCommentAdd(c.id, newComment.trim(), isNote);
    if (res?.success) { setComments(p => [...p, res.data]); setNewComment(''); }
    setBusy(null);
  };

  const deleteComment = async (msgId: number) => {
    setBusy(`cdel-${msgId}`);
    const res = await supplyApi.containerCommentDelete(c.id, msgId);
    if (res?.success) setComments(p => p.filter(x => x.id !== msgId));
    setBusy(null);
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files ?? []);
    if (!files.length) return;
    setBusy('upload');
    const res = await supplyApi.containerAttachUploadMultiple(c.id, files);
    if (res?.success) { const newAtts = res.data?.attachments ?? []; setAttachments(a => [...newAtts, ...a]); }
    setBusy(null);
    if (fileRef.current) fileRef.current.value = '';
  };

  const deleteAttachment = async (attId: number) => {
    setBusy(`att-${attId}`);
    const res = await supplyApi.containerAttachDelete(c.id, attId);
    if (res?.success) setAttachments(a => a.filter(x => x.id !== attId));
    setBusy(null);
  };

  return (
    <div className="fixed inset-0 bg-black/40 z-40 flex justify-end">
      <div className="bg-white w-full max-w-2xl h-full flex flex-col shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b bg-gray-50">
          <div>
            <h2 className="text-lg font-bold text-gray-900">{c.name}</h2>
            <div className="flex items-center gap-2 mt-0.5 flex-wrap">
              <ContainerStatusBadge status={c.status as ContainerStatus} />
              {c.container_number && <span className="text-xs text-gray-500 font-mono">{c.container_number}</span>}
              {c.bl_number && <span className="text-xs text-gray-500">BL: {c.bl_number}</span>}
              {c.division && <span className="text-xs text-gray-400 capitalize">· {c.division}</span>}
            </div>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-700 transition"><X className="w-5 h-5" /></button>
        </div>

        {/* Action bar */}
        <div className="flex gap-2 px-6 py-3 border-b bg-white flex-wrap">
          {c.status === 'active' && (
            <button onClick={markArrived} disabled={!!busy}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-amber-500 text-white hover:bg-amber-600 disabled:opacity-50 transition">
              {busy === 'arrived' ? <Loader2 className="w-3 h-3 animate-spin" /> : <Anchor className="w-3 h-3" />} Mark Arrived
            </button>
          )}
          {!c.clearance_info_delivered && (
            <button onClick={markClearance} disabled={!!busy}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-green-600 text-white hover:bg-green-700 disabled:opacity-50 transition">
              {busy === 'clearance' ? <Loader2 className="w-3 h-3 animate-spin" /> : <Check className="w-3 h-3" />} Clearance Delivered
            </button>
          )}
          {c.driver_id ? (
            <button onClick={unassignDriver} disabled={!!busy}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-red-100 text-red-700 hover:bg-red-200 disabled:opacity-50 transition">
              {busy === 'unassign' ? <Loader2 className="w-3 h-3 animate-spin" /> : <User className="w-3 h-3" />} Unassign Driver
            </button>
          ) : (
            <button onClick={() => setShowDriverForm(v => !v)}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-blue-100 text-blue-700 hover:bg-blue-200 transition">
              <User className="w-3 h-3" /> Assign Driver
            </button>
          )}
          <button onClick={reload}
            className="ml-auto p-1.5 rounded-lg text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition" title="Refresh">
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Driver form */}
        {showDriverForm && !c.driver_id && (
          <div className="px-6 py-3 bg-blue-50 border-b flex items-end gap-2 flex-wrap">
            <div className="flex-1 min-w-[140px]">
              <label className="text-xs text-gray-600 mb-1 block">Driver Name</label>
              <Input value={driverName} onChange={e => setDriverName(e.target.value)} placeholder="Full name" className="h-8 text-sm" />
            </div>
            <div className="flex-1 min-w-[120px]">
              <label className="text-xs text-gray-600 mb-1 block">Phone</label>
              <Input value={driverPhone} onChange={e => setDriverPhone(e.target.value)} placeholder="+966…" className="h-8 text-sm" />
            </div>
            <Button size="sm" onClick={assignDriver} disabled={busy === 'driver'}>
              {busy === 'driver' ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : <Check className="w-3 h-3 mr-1" />} Assign
            </Button>
            <Button size="sm" variant="outline" onClick={() => setShowDriverForm(false)}>Cancel</Button>
          </div>
        )}

        {/* Tabs */}
        <div className="flex border-b px-6">
          {(['info', 'attachments', 'penalties', 'comments'] as Tab[]).map(t => (
            <button key={t} onClick={() => setTab(t)}
              className={`px-4 py-2.5 text-sm font-medium border-b-2 transition capitalize ${
                tab === t ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}>
              {t === 'info'        && <span className="flex items-center gap-1.5"><Ship className="w-3.5 h-3.5" />Info</span>}
              {t === 'attachments' && <span className="flex items-center gap-1.5"><Paperclip className="w-3.5 h-3.5" />Files ({c.attachment_count})</span>}
              {t === 'penalties'   && <span className="flex items-center gap-1.5"><AlertTriangle className="w-3.5 h-3.5" />Penalties ({penalties.length})</span>}
              {t === 'comments'    && <span className="flex items-center gap-1.5"><MessageSquare className="w-3.5 h-3.5" />Comments</span>}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div className="flex-1 overflow-y-auto">

          {/* Info Tab */}
          {tab === 'info' && (
            <div className="px-6 py-4 space-y-4">
              <div className="grid grid-cols-2 gap-3">
                {[
                  ['Origin', c.origin_location],
                  ['Destination Port', c.destination_port],
                  ['Departure', c.departure_date],
                  ['ETA', c.eta],
                  ['Arrived At', c.arrived_at],
                  ['Clearance Company', c.clearance_company_name],
                  ['Clearance Delivered', c.clearance_info_delivered ? `Yes — ${c.clearance_info_delivered_at?.slice(0, 10) ?? ''}` : 'No'],
                  ['Total Weight (kg)', c.total_weight_kg ? String(c.total_weight_kg) : '—'],
                  ['Total CBM', c.total_cbm ? String(c.total_cbm) : '—'],
                ].filter(([, v]) => v).map(([label, value]) => (
                  <div key={label as string} className="bg-gray-50 rounded-lg px-3 py-2">
                    <p className="text-xs text-gray-500">{label as string}</p>
                    <p className="text-sm font-medium text-gray-800 mt-0.5">{value as string}</p>
                  </div>
                ))}
              </div>

              {c.driver_id && (
                <div className="bg-blue-50 rounded-xl p-3 border border-blue-100">
                  <p className="text-xs font-semibold text-blue-700 mb-1 flex items-center gap-1"><User className="w-3 h-3" /> Assigned Driver</p>
                  <p className="text-sm font-medium text-gray-900">{c.driver_name}</p>
                  {c.driver_phone && <p className="text-xs text-gray-600">{c.driver_phone}</p>}
                  {c.driver_assigned_at && <p className="text-xs text-gray-400 mt-1">Assigned {new Date(c.driver_assigned_at).toLocaleString()}</p>}
                </div>
              )}

              {c.tracking_url && (
                <a href={c.tracking_url} target="_blank" rel="noreferrer"
                  className="flex items-center gap-2 text-sm text-blue-600 hover:underline">
                  <Ship className="w-4 h-4" /> Track Container
                </a>
              )}

              {/* Reminder section */}
              {c.reminder_date ? (
                <div className="bg-purple-50 rounded-xl p-3 border border-purple-100">
                  <div className="flex items-center justify-between mb-1">
                    <p className="text-xs font-semibold text-purple-700 flex items-center gap-1">
                      🔔 Reminder
                    </p>
                    <div className="flex gap-1">
                      <button onClick={() => setShowReminderForm(v => !v)}
                        className="text-xs text-purple-500 hover:text-purple-700 px-2 py-0.5 rounded transition">Edit</button>
                      <button onClick={clearReminder} disabled={busy === 'clear-reminder'}
                        className="text-xs text-red-400 hover:text-red-600 px-2 py-0.5 rounded transition disabled:opacity-50">
                        {busy === 'clear-reminder' ? <Loader2 className="w-3 h-3 animate-spin inline" /> : 'Clear'}
                      </button>
                    </div>
                  </div>
                  <p className="text-sm font-medium text-gray-800">{new Date(c.reminder_date).toLocaleString()}</p>
                  {c.reminder_note && <p className="text-xs text-gray-600 mt-0.5">{c.reminder_note}</p>}
                </div>
              ) : (
                <button onClick={() => setShowReminderForm(v => !v)}
                  className="flex items-center gap-2 text-sm text-purple-600 hover:text-purple-800 transition">
                  🔔 Set Reminder
                </button>
              )}

              {showReminderForm && (
                <div className="bg-purple-50 rounded-xl p-3 border border-purple-100 space-y-2">
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="text-xs text-gray-600 mb-1 block">Reminder Date/Time</label>
                      <Input type="datetime-local" value={reminderDate} onChange={e => setReminderDate(e.target.value)} className="h-8 text-sm" />
                    </div>
                    <div>
                      <label className="text-xs text-gray-600 mb-1 block">Note</label>
                      <Input value={reminderNote} onChange={e => setReminderNote(e.target.value)} placeholder="Optional note" className="h-8 text-sm" />
                    </div>
                  </div>
                  <div className="flex justify-end gap-2">
                    <Button type="button" variant="outline" size="sm" onClick={() => setShowReminderForm(false)}>Cancel</Button>
                    <Button type="button" size="sm" onClick={saveReminder} disabled={busy === 'reminder'}>
                      {busy === 'reminder' ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : null} Save Reminder
                    </Button>
                  </div>
                </div>
              )}

              {c.notes && (
                <div className="bg-amber-50 rounded-lg px-3 py-2 border border-amber-100">
                  <p className="text-xs text-amber-600 font-medium mb-0.5">Notes</p>
                  <p className="text-sm text-gray-700 whitespace-pre-wrap">{c.notes}</p>
                </div>
              )}
            </div>
          )}

          {/* Attachments Tab */}
          {tab === 'attachments' && (
            <div className="px-6 py-4 space-y-3">
              <div>
                <input ref={fileRef} type="file" multiple className="hidden" onChange={handleFileUpload} />
                <button onClick={() => fileRef.current?.click()} disabled={busy === 'upload'}
                  className="w-full flex items-center justify-center gap-2 py-2.5 border-2 border-dashed border-gray-200 rounded-xl text-sm text-gray-500 hover:border-blue-400 hover:text-blue-600 transition disabled:opacity-50">
                  {busy === 'upload' ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
                  {busy === 'upload' ? 'Uploading...' : 'Click to upload files'}
                </button>
                <p className="text-xs text-gray-400 text-center mt-1">PDF, Images, Office files — multiple allowed</p>
              </div>
              {attachments.length === 0 && <p className="text-center text-sm text-gray-400 py-4">No attachments.</p>}
              {attachments.map(a => (
                <div key={a.id} className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl">
                  <FileText className="w-8 h-8 text-blue-500 shrink-0" />
                  <div className="flex-1 min-w-0">
                    <a href={a.file_url || a.url} target="_blank" rel="noreferrer" className="text-sm font-medium text-blue-600 hover:underline truncate block">{a.name}</a>
                    <p className="text-xs text-gray-400">{a.mimetype} · {a.uploaded_by_name}</p>
                  </div>
                  <button onClick={() => deleteAttachment(a.id)} disabled={busy === `att-${a.id}`}
                    className="text-red-400 hover:text-red-600 disabled:opacity-40">
                    {busy === `att-${a.id}` ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* Penalties Tab */}
          {tab === 'penalties' && (
            <div className="px-6 py-4 space-y-3">
              {penalties.length > 0 && (
                <div className="flex items-center justify-between bg-red-50 rounded-lg px-4 py-2 border border-red-100">
                  <span className="text-sm font-medium text-red-700">Total Penalties</span>
                  <span className="text-sm font-bold text-red-900">{totalPenAmt.toLocaleString('en-US', { minimumFractionDigits: 2 })}</span>
                </div>
              )}

              {!showPenForm && (
                <button onClick={() => setShowPenForm(true)}
                  className="w-full flex items-center justify-center gap-2 py-2.5 border-2 border-dashed border-gray-200 rounded-xl text-sm text-gray-500 hover:border-red-400 hover:text-red-600 transition">
                  <Plus className="w-4 h-4" /> Add Penalty
                </button>
              )}

              {showPenForm && (
                <div className="border rounded-xl p-4 bg-red-50 space-y-3">
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="text-xs text-gray-600 mb-1 block">Type</label>
                      <select
                        className="w-full h-8 rounded-md border border-input bg-background px-2 text-sm"
                        value={penType}
                        onChange={e => setPenType(e.target.value as PenaltyType)}
                      >
                        {(Object.keys(PENALTY_LABELS) as PenaltyType[]).map(k => (
                          <option key={k} value={k}>{PENALTY_LABELS[k]}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="text-xs text-gray-600 mb-1 block">Amount *</label>
                      <Input type="number" min="0" step="0.01" placeholder="0.00" value={penAmount} onChange={e => setPenAmount(e.target.value)} className="h-8 text-sm" />
                    </div>
                    <div>
                      <label className="text-xs text-gray-600 mb-1 block">Date</label>
                      <Input type="date" value={penDate} onChange={e => setPenDate(e.target.value)} className="h-8 text-sm" />
                    </div>
                    <div>
                      <label className="text-xs text-gray-600 mb-1 block">Reason</label>
                      <Input placeholder="Optional reason" value={penReason} onChange={e => setPenReason(e.target.value)} className="h-8 text-sm" />
                    </div>
                  </div>
                  <div className="flex justify-end gap-2">
                    <Button type="button" variant="outline" size="sm" onClick={() => setShowPenForm(false)}>Cancel</Button>
                    <Button type="button" size="sm" onClick={submitPenalty} disabled={busy === 'penalty'}>
                      {busy === 'penalty' ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : null} Add Penalty
                    </Button>
                  </div>
                </div>
              )}

              {penalties.length === 0 && !showPenForm && (
                <p className="text-center text-sm text-gray-400 py-4">No penalties recorded.</p>
              )}
              {penalties.map(pen => (
                <div key={pen.id} className="flex items-start gap-3 p-3 bg-gray-50 rounded-xl">
                  <AlertTriangle className="w-5 h-5 text-red-400 mt-0.5 shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-gray-900">{PENALTY_LABELS[pen.penalty_type] ?? pen.penalty_type}</span>
                      <span className="text-sm font-bold text-red-700">{pen.amount.toLocaleString('en-US', { minimumFractionDigits: 2 })} {pen.currency_name}</span>
                    </div>
                    {pen.reason && <p className="text-xs text-gray-500 mt-0.5">{pen.reason}</p>}
                    <p className="text-xs text-gray-400">{pen.penalty_date || pen.created_at?.slice(0, 10)} · {pen.created_by_name}</p>
                  </div>
                  <button onClick={() => deletePenalty(pen.id, pen.amount)} disabled={busy === `pen-del-${pen.id}`}
                    className="text-red-400 hover:text-red-600 disabled:opacity-40 shrink-0">
                    {busy === `pen-del-${pen.id}` ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* Comments Tab */}
          {tab === 'comments' && (
            <div className="flex flex-col h-full">
              <div className="flex-1 px-6 py-4 space-y-3 overflow-y-auto">
                {comments.length === 0 && <p className="text-center text-sm text-gray-400 py-8">No comments yet.</p>}
                {comments.map(comment => (
                  <div key={comment.id} className={`p-3 rounded-xl text-sm ${comment.is_note ? 'bg-amber-50 border border-amber-100' : 'bg-gray-50'}`}>
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-gray-800">{comment.author_name}</span>
                        {comment.is_note && <span className="text-xs bg-amber-200 text-amber-800 px-1.5 py-0.5 rounded">Note</span>}
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-gray-400">{new Date(comment.created_at).toLocaleString()}</span>
                        <button onClick={() => deleteComment(comment.id)} disabled={busy === `cdel-${comment.id}`}
                          className="text-gray-300 hover:text-red-500 disabled:opacity-40 transition">
                          {busy === `cdel-${comment.id}` ? <Loader2 className="w-3 h-3 animate-spin" /> : <Trash2 className="w-3 h-3" />}
                        </button>
                      </div>
                    </div>
                    <p className="text-gray-700 whitespace-pre-wrap">{comment.body}</p>
                  </div>
                ))}
              </div>
              <div className="px-6 py-3 border-t space-y-2 bg-white">
                <label className="flex items-center gap-1.5 text-xs text-gray-600 cursor-pointer">
                  <input type="checkbox" checked={isNote} onChange={e => setIsNote(e.target.checked)} className="rounded" />
                  Internal Note
                </label>
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
        </div>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// Main Container Panel
// ─────────────────────────────────────────────────────────────
export function ContainerContainer() {
  const [containers,   setContainers]   = useState<Container[]>([]);
  const [total,        setTotal]        = useState(0);
  const [filter,       setFilterState]  = useState<ContainerListFilter>({ page: 1, per_page: 20 });
  const [loading,      setLoading]      = useState(false);
  const [error,        setError]        = useState<string | null>(null);
  const [showCreate,   setShowCreate]   = useState(false);
  const [detail,       setDetail]       = useState<Container | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Container | null>(null);
  const [searchDraft,  setSearchDraft]  = useState('');
  const [deleteBusy,   setDeleteBusy]   = useState(false);

  const setFilter = (f: Partial<ContainerListFilter>) =>
    setFilterState(prev => ({ ...prev, ...f }));

  const load = useCallback(async () => {
    setLoading(true); setError(null);
    const res = await supplyApi.containerList(filter);
    if (res?.success) { setContainers(res.data?.items ?? []); setTotal(res.data?.total ?? 0); }
    else { setError(res?.error ?? 'Failed to load containers'); }
    setLoading(false);
  }, [filter]);

  useEffect(() => { load(); }, [load]);

  const doDelete = async () => {
    if (!deleteTarget) return;
    setDeleteBusy(true);
    const res = await supplyApi.containerDelete(deleteTarget.id);
    if (res?.success) { setContainers(c => c.filter(x => x.id !== deleteTarget.id)); setTotal(t => t - 1); setDeleteTarget(null); }
    setDeleteBusy(false);
  };

  const totalPages  = Math.ceil(total / (filter.per_page ?? 20));
  const currentPage = filter.page ?? 1;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top Bar */}
      <div className="bg-white border-b px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-amber-500 rounded-lg flex items-center justify-center">
            <Ship className="w-4 h-4 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-900">Containers</h1>
            <p className="text-xs text-gray-500">{total} containers total</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={load} className="p-2 text-gray-400 hover:text-gray-700 rounded-lg hover:bg-gray-100 transition">
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <Button onClick={() => setShowCreate(true)} className="gap-2 bg-amber-500 hover:bg-amber-600">
            <Plus className="w-4 h-4" /> New Container
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white border-b px-6 py-3 flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <Input
            className="pl-9 h-8 text-sm" placeholder="Search containers..."
            value={searchDraft}
            onChange={e => setSearchDraft(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && setFilter({ search: searchDraft, page: 1 })}
          />
        </div>
        <select className="h-8 rounded-md border border-input bg-background px-3 py-0 text-sm"
          value={filter.status ?? ''}
          onChange={e => setFilter({ status: e.target.value as ContainerStatus | '', page: 1 })}>
          <option value="">All Statuses</option>
          <option value="waiting">Waiting</option>
          <option value="active">Active</option>
          <option value="at_port">At Port</option>
          <option value="completed">Completed</option>
        </select>
        <select className="h-8 rounded-md border border-input bg-background px-3 py-0 text-sm"
          value={filter.division ?? ''}
          onChange={e => setFilter({ division: e.target.value, page: 1 })}>
          <option value="">All Divisions</option>
          <option value="europe">Europe</option>
          <option value="china">China</option>
        </select>
        {(filter.status || filter.search || filter.division) && (
          <button onClick={() => { setFilter({ status: '', search: '', division: '', page: 1 }); setSearchDraft(''); }}
            className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-800 px-2 py-1 rounded-lg hover:bg-gray-100 transition">
            <X className="w-3 h-3" /> Clear
          </button>
        )}
      </div>

      {/* Table */}
      <div className="px-6 py-4">
        {error ? (
          <div className="text-center py-16">
            <p className="text-red-600 mb-3">{error}</p>
            <Button variant="outline" onClick={load}>Retry</Button>
          </div>
        ) : loading ? (
          <div className="text-center py-16"><Loader2 className="w-8 h-8 animate-spin text-amber-500 mx-auto" /></div>
        ) : containers.length === 0 ? (
          <div className="text-center py-16">
            <Ship className="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500 mb-4">No containers found</p>
            <Button onClick={() => setShowCreate(true)} className="gap-2 bg-amber-500 hover:bg-amber-600">
              <Plus className="w-4 h-4" /> Create First Container
            </Button>
          </div>
        ) : (
          <div className="bg-white rounded-xl border overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b text-left">
                  <th className="px-4 py-3 font-semibold text-gray-600">Container</th>
                  <th className="px-4 py-3 font-semibold text-gray-600">Route</th>
                  <th className="px-4 py-3 font-semibold text-gray-600">Status</th>
                  <th className="px-4 py-3 font-semibold text-gray-600">ETA</th>
                  <th className="px-4 py-3 font-semibold text-gray-600">Driver</th>
                  <th className="px-4 py-3 font-semibold text-gray-600 text-center">Files</th>
                  <th className="px-4 py-3 font-semibold text-gray-600 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {containers.map(cont => (
                  <tr key={cont.id} className="hover:bg-gray-50 transition cursor-pointer" onClick={() => setDetail(cont)}>
                    <td className="px-4 py-3">
                      <p className="font-semibold text-amber-700">{cont.name}</p>
                      {cont.container_number && <p className="text-xs text-gray-500 font-mono">{cont.container_number}</p>}
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-600">
                      {cont.origin_location && <p>{cont.origin_location}</p>}
                      {cont.destination_port && <p>→ {cont.destination_port}</p>}
                    </td>
                    <td className="px-4 py-3">
                      <ContainerStatusBadge status={cont.status as ContainerStatus} />
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-600">
                      {cont.eta ? new Date(cont.eta).toLocaleDateString() : '—'}
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-600">
                      {cont.driver_name ? (
                        <span className="flex items-center gap-1"><User className="w-3 h-3 text-blue-400" />{cont.driver_name}</span>
                      ) : <span className="text-gray-400">—</span>}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className="inline-block bg-gray-100 text-gray-700 rounded-full px-2 py-0.5 text-xs font-medium">{cont.attachment_count}</span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-end gap-1" onClick={e => e.stopPropagation()}>
                        <button onClick={() => setDetail(cont)}
                          className="p-1.5 rounded-lg text-gray-400 hover:text-amber-600 hover:bg-amber-50 transition">
                          <Eye className="w-4 h-4" />
                        </button>
                        <button onClick={() => setDeleteTarget(cont)}
                          className="p-1.5 rounded-lg text-gray-400 hover:text-red-600 hover:bg-red-50 transition">
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
                <p className="text-sm text-gray-500">Page {currentPage} of {totalPages} · {total} total</p>
                <div className="flex gap-1">
                  <button disabled={currentPage <= 1} onClick={() => setFilter({ page: currentPage - 1 })}
                    className="p-1.5 rounded-lg text-gray-500 hover:bg-gray-200 disabled:opacity-30 transition">
                    <ChevronLeft className="w-4 h-4" />
                  </button>
                  <button disabled={currentPage >= totalPages} onClick={() => setFilter({ page: currentPage + 1 })}
                    className="p-1.5 rounded-lg text-gray-500 hover:bg-gray-200 disabled:opacity-30 transition">
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Modals */}
      {showCreate && (
        <CreateContainerModal
          onClose={() => setShowCreate(false)}
          onCreated={(cont) => { setContainers(c => [cont, ...c]); setTotal(t => t + 1); setShowCreate(false); setDetail(cont); }}
        />
      )}

      {detail && (
        <ContainerDetailSheet
          container={detail}
          onClose={() => setDetail(null)}
          onUpdated={(c) => { setContainers(prev => prev.map(x => x.id === c.id ? c : x)); setDetail(c); }}
        />
      )}

      {deleteTarget && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl p-6 max-w-sm w-full">
            <h3 className="text-base font-bold text-gray-900 mb-2">Delete Container</h3>
            <p className="text-sm text-gray-600 mb-4">Are you sure you want to delete <strong>{deleteTarget.name}</strong>? This cannot be undone.</p>
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
