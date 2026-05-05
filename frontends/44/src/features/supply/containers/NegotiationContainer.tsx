// ============================================================
// Negotiations — list + comments (mail.thread via API)
// ============================================================
import { useState, useEffect, useCallback } from 'react';
import {
  MessageSquare, X, Search, RefreshCw, Loader2, Eye, Send, Trash2, Handshake,
} from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '../../../components/ui/button';
import { Input } from '../../../components/ui/input';
import supplyApi from '../../../services/supplyApi';
import { LoginForm } from './PoContainer';
import { useSupplyStore } from '../store/supplyStore';
import type { Negotiation, Comment, NegotiationCommentRow } from '../../../types/supply';

function mapNegCommentRow(row: NegotiationCommentRow): Comment {
  return {
    id:            row.id,
    body:          row.body,
    body_html:     '',
    is_note:       false,
    author_id:     row.author_id,
    author_name:   row.author_name,
    author_avatar: null,
    message_type:  'comment',
    subtype:       '',
    created_at:    row.date,
  };
}

function NegotiationDetailSheet({
  negotiation: initial,
  onClose,
}: {
  negotiation: Negotiation;
  onClose: () => void;
}) {
  const [n, setN] = useState<Negotiation>(initial);
  const [comments, setComments] = useState<Comment[]>([]);
  const [newComment, setNewComment] = useState('');
  const [busy, setBusy] = useState<string | null>(null);

  useEffect(() => { setN(initial); }, [initial]);

  const loadComments = useCallback(async () => {
    const r = await supplyApi.negotiationCommentList(n.id, 1, 100);
    if (r?.success) {
      setComments((r.data?.items ?? []).map(mapNegCommentRow));
    } else if (r?.error) {
      toast.error(r.error);
    }
  }, [n.id]);

  useEffect(() => { loadComments(); }, [loadComments]);

  const refreshNegotiation = async () => {
    const r = await supplyApi.negotiationGet(n.id);
    if (r?.success) setN(r.data);
  };

  const submitComment = async () => {
    if (!newComment.trim()) return;
    setBusy('comment');
    const r = await supplyApi.negotiationCommentAdd(n.id, newComment.trim());
    if (r?.success) {
      setNewComment('');
      await loadComments();
      await refreshNegotiation();
    } else if (r?.error) {
      toast.error(r.error);
    }
    setBusy(null);
  };

  const deleteComment = async (msgId: number) => {
    setBusy(`del-${msgId}`);
    const r = await supplyApi.negotiationCommentDelete(n.id, msgId);
    if (r?.success) {
      setComments(c => c.filter(x => x.id !== msgId));
    } else if (r?.error) {
      toast.error(r.error);
    }
    setBusy(null);
  };

  const stateLabel = n.status ?? n.state ?? '';

  return (
    <div className="fixed inset-0 bg-black/40 z-40 flex justify-end">
      <div className="bg-white w-full max-w-2xl h-full flex flex-col shadow-2xl">
        <div className="flex items-center justify-between px-6 py-4 border-b bg-gray-50">
          <div>
            <h2 className="text-lg font-bold text-gray-900">{n.name || n.negotiation_code || `Negotiation #${n.id}`}</h2>
            <div className="flex flex-wrap gap-2 mt-1 text-xs text-gray-600">
              {n.vendor_name && <span>Vendor: <strong className="text-gray-800">{n.vendor_name}</strong></span>}
              {n.item_name && <span>· Item: {n.item_name}</span>}
              {stateLabel && (
                <span className="ml-1 px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-800 capitalize">{stateLabel}</span>
              )}
            </div>
          </div>
          <button type="button" onClick={onClose} className="text-gray-400 hover:text-gray-700 transition">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="px-6 py-2 border-b flex items-center gap-2 bg-white">
          <MessageSquare className="w-4 h-4 text-indigo-600" />
          <span className="text-sm font-semibold text-gray-800">Comments</span>
          <button
            type="button"
            onClick={() => { loadComments(); refreshNegotiation(); }}
            className="ml-auto p-1.5 rounded-lg text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition"
            title="Refresh"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="flex-1 flex flex-col min-h-0">
          <div className="flex-1 px-6 py-4 space-y-3 overflow-y-auto">
            {comments.length === 0 && (
              <p className="text-center text-sm text-gray-400 py-8">No comments yet.</p>
            )}
            {comments.map(c => (
              <div key={c.id} className="p-3 rounded-xl text-sm bg-gray-50">
                <div className="flex items-center justify-between mb-1">
                  <span className="font-medium text-gray-800">{c.author_name || '—'}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-400">
                      {c.created_at ? new Date(c.created_at).toLocaleString() : ''}
                    </span>
                    <button
                      type="button"
                      onClick={() => deleteComment(c.id)}
                      disabled={busy === `del-${c.id}`}
                      className="text-gray-300 hover:text-red-500 disabled:opacity-40 transition"
                      title="Delete comment"
                    >
                      {busy === `del-${c.id}` ? <Loader2 className="w-3 h-3 animate-spin" /> : <Trash2 className="w-3 h-3" />}
                    </button>
                  </div>
                </div>
                <p className="text-gray-700 whitespace-pre-wrap">{c.body}</p>
              </div>
            ))}
          </div>

          <div className="px-6 py-3 border-t space-y-2 bg-white shrink-0">
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
      </div>
    </div>
  );
}

export function NegotiationContainer() {
  const store = useSupplyStore();
  const [showLogin, setShowLogin] = useState(!store.token);
  const [items, setItems] = useState<Negotiation[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const perPage = 20;
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchDraft, setSearchDraft] = useState('');
  const [search, setSearch] = useState('');
  const [detail, setDetail] = useState<Negotiation | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    const r = await supplyApi.negotiationList({ page, per_page: perPage, search: search || undefined });
    if (r?.success) {
      setItems(r.data?.items ?? []);
      setTotal(r.data?.total ?? 0);
    } else {
      if (r?.error?.toLowerCase().includes('unauthorized')) setShowLogin(true);
      else setError(r?.error ?? 'Failed to load negotiations');
    }
    setLoading(false);
  }, [page, search]);

  useEffect(() => {
    if (!showLogin) load();
  }, [showLogin, load]);

  if (showLogin) return <LoginForm onLogin={() => setShowLogin(false)} />;

  const totalPages = Math.max(1, Math.ceil(total / perPage));

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white border-b px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
            <Handshake className="w-4 h-4 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-900">Negotiations</h1>
            <p className="text-xs text-gray-500">{total} records</p>
          </div>
        </div>
        <button type="button" onClick={load} className="p-2 text-gray-400 hover:text-gray-700 rounded-lg hover:bg-gray-100 transition">
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      <div className="bg-white border-b px-6 py-3 flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <Input
            className="pl-9 h-8 text-sm"
            placeholder="Search by code or item..."
            value={searchDraft}
            onChange={e => setSearchDraft(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && (setSearch(searchDraft.trim()), setPage(1))}
          />
        </div>
        <Button type="button" size="sm" variant="secondary" onClick={() => { setSearch(searchDraft.trim()); setPage(1); }}>
          Search
        </Button>
        {search && (
          <button
            type="button"
            onClick={() => { setSearch(''); setSearchDraft(''); setPage(1); }}
            className="text-xs text-gray-500 hover:text-gray-800"
          >
            Clear
          </button>
        )}
      </div>

      <div className="px-6 py-4">
        {error ? (
          <div className="text-center py-16">
            <p className="text-red-600 mb-3">{error}</p>
            <Button variant="outline" onClick={load}>Retry</Button>
          </div>
        ) : loading ? (
          <div className="text-center py-16"><Loader2 className="w-8 h-8 animate-spin text-indigo-600 mx-auto" /></div>
        ) : items.length === 0 ? (
          <div className="text-center py-16 text-gray-500">No negotiations found.</div>
        ) : (
          <div className="bg-white rounded-xl border overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b text-left">
                  <th className="px-4 py-3 font-semibold text-gray-600">Reference</th>
                  <th className="px-4 py-3 font-semibold text-gray-600">Vendor</th>
                  <th className="px-4 py-3 font-semibold text-gray-600">Item</th>
                  <th className="px-4 py-3 font-semibold text-gray-600">State</th>
                  <th className="px-4 py-3 font-semibold text-gray-600 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {items.map(row => (
                  <tr key={row.id} className="hover:bg-gray-50 cursor-pointer transition" onClick={() => setDetail(row)}>
                    <td className="px-4 py-3 font-semibold text-indigo-700">{row.name || row.negotiation_code || `#${row.id}`}</td>
                    <td className="px-4 py-3 max-w-[160px] truncate">{row.vendor_name || '—'}</td>
                    <td className="px-4 py-3 max-w-[200px] truncate">{row.item_name || '—'}</td>
                    <td className="px-4 py-3 capitalize text-gray-700">{row.status ?? row.state ?? '—'}</td>
                    <td className="px-4 py-3 text-right" onClick={e => e.stopPropagation()}>
                      <button
                        type="button"
                        onClick={() => setDetail(row)}
                        className="p-1.5 rounded-lg text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 transition"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {totalPages > 1 && (
              <div className="flex items-center justify-between px-4 py-3 border-t bg-gray-50">
                <p className="text-sm text-gray-500">Page {page} of {totalPages}</p>
                <div className="flex gap-1">
                  <button
                    type="button"
                    disabled={page <= 1}
                    onClick={() => setPage(p => p - 1)}
                    className="p-1.5 rounded-lg text-gray-500 hover:bg-gray-200 disabled:opacity-30"
                  >
                    ←
                  </button>
                  <button
                    type="button"
                    disabled={page >= totalPages}
                    onClick={() => setPage(p => p + 1)}
                    className="p-1.5 rounded-lg text-gray-500 hover:bg-gray-200 disabled:opacity-30"
                  >
                    →
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {detail && (
        <NegotiationDetailSheet negotiation={detail} onClose={() => setDetail(null)} />
      )}
    </div>
  );
}
