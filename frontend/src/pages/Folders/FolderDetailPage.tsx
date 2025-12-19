import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  MenuItem,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material';
import { useTranslation } from 'react-i18next';
import apiClient from '../../api/client';
import toast from 'react-hot-toast';
import { signaturesApi } from '../../api/signatures.api';
import { editRequestsApi } from '../../api/editRequests.api';

type Folder = {
  id: number;
  name: string;
  code: string;
  description?: string;
  main_document_id?: number | null;
  department_id?: number | null;
  department_name?: string | null;
};

type FolderDoc = {
  id: number;
  title: string;
  barcode: string;
  document_type_name: string;
  upload_date: string;
  status: string;
  parent_document_id?: number | null;
  parent_title?: string | null;
};

type AttachmentRow = {
  id: number;
  name: string;
  description?: string | null;
  file_name: string;
  file_size?: number | null;
  file_type?: string | null;
  uploader_name?: string | null;
  upload_date?: string | null;
  attachment_type?: string | null;
};

type FolderWorkflowInfo = {
  folder_id: number;
  workflow_id?: number | null;
  workflow_name?: string | null;
  state_id?: number | null;
  state_name?: string | null;
  allowed_transitions?: Array<{
    id: number;
    name: string;
    to_state_id: number;
    to_state_name: string;
    requires_request?: boolean;
  }>;
};

export default function FolderDetailPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();

  const [folder, setFolder] = useState<Folder | null>(null);
  const [docs, setDocs] = useState<FolderDoc[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [attachmentsDocId, setAttachmentsDocId] = useState<number | ''>('');
  const [attachments, setAttachments] = useState<AttachmentRow[]>([]);

  const [workflowInfo, setWorkflowInfo] = useState<FolderWorkflowInfo | null>(null);
  const [workflowError, setWorkflowError] = useState<string | null>(null);

  const [transitionOpen, setTransitionOpen] = useState(false);
  const [transitionTarget, setTransitionTarget] = useState<{ id: number; label: string } | null>(null);
  const [transitionMessage, setTransitionMessage] = useState('');

  const [managers, setManagers] = useState<Array<{ id: number; name: string; login?: string }>>([]);
  const [signatureOpen, setSignatureOpen] = useState(false);
  const [signatureSignerId, setSignatureSignerId] = useState<number | ''>('');
  const [signatureMessage, setSignatureMessage] = useState('');

  const [editOpen, setEditOpen] = useState(false);
  const [editReason, setEditReason] = useState('');

  const load = async () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      const resp = await apiClient.post(`/api/folders/${id}/documents`, {
        jsonrpc: '2.0',
        method: 'call',
        params: {},
      });
      const result = resp.data.result || resp.data;
      setFolder(result.folder || null);
      setDocs(result.data || []);

      // Default attachments/doc actions to folder "main document":
      // By product spec: main document is the FIRST uploaded document inside the folder.
      const sorted = [...(result.data || [])].sort((a: FolderDoc, b: FolderDoc) => {
        const ta = a.upload_date ? new Date(a.upload_date).getTime() : Number.POSITIVE_INFINITY;
        const tb = b.upload_date ? new Date(b.upload_date).getTime() : Number.POSITIVE_INFINITY;
        return ta - tb;
      });
      const nextDocId = (sorted[0]?.id as number | undefined) || null;
      if (nextDocId) {
        setAttachmentsDocId((prev) => (prev === '' ? nextDocId : prev));
      }
    } catch (e: any) {
      setError(e?.message || 'Failed to load folder');
    } finally {
      setLoading(false);
    }
  };

  const loadWorkflow = async (folderId: number) => {
    setWorkflowError(null);
    try {
      const resp = await apiClient.post(`/api/folders/${folderId}/workflow`, {
        jsonrpc: '2.0',
        method: 'call',
        params: {},
      });
      const result = resp.data.result || resp.data;
      if (!result.success) {
        setWorkflowInfo(null);
        setWorkflowError(result.error || 'Failed to load workflow');
        return;
      }
      setWorkflowInfo(result.data as FolderWorkflowInfo);
    } catch (e: any) {
      setWorkflowInfo(null);
      setWorkflowError(e?.message || 'Failed to load workflow');
    }
  };

  const applyTransition = async (transitionId: number, message?: string) => {
    if (!id) return;
    setWorkflowError(null);
    try {
      const resp = await apiClient.post(`/api/folders/${id}/workflow/transition`, {
        jsonrpc: '2.0',
        method: 'call',
        params: { transition_id: transitionId, message: message || undefined },
      });
      const result = resp.data.result || resp.data;
      if (!result.success) throw new Error(result.error || 'Transition failed');
      await loadWorkflow(Number(id));
    } catch (e: any) {
      setWorkflowError(e?.message || 'Transition failed');
    }
  };

  const openTransition = (transitionId: number, label: string) => {
    setTransitionTarget({ id: transitionId, label });
    setTransitionMessage('');
    setTransitionOpen(true);
  };

  const submitTransition = async () => {
    if (!transitionTarget) return;
    await applyTransition(transitionTarget.id, transitionMessage.trim() || undefined);
    setTransitionOpen(false);
    setTransitionTarget(null);
  };

  const loadAttachments = async (documentId: number) => {
    try {
      const resp = await apiClient.post(`/api/documents/${documentId}/attachments`, {
        jsonrpc: '2.0',
        method: 'call',
        params: {},
      });
      const result = resp.data.result || resp.data;
      setAttachments((result.data || []) as AttachmentRow[]);
    } catch {
      setAttachments([]);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  useEffect(() => {
    if (!id) return;
    loadWorkflow(Number(id));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  useEffect(() => {
    if (attachmentsDocId === '') return;
    loadAttachments(Number(attachmentsDocId));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [attachmentsDocId]);

  useEffect(() => {
    // Fetch managers list for signature requester dialog
    (async () => {
      try {
        const resp = await apiClient.post('/api/users/managers', { department_id: undefined });
        setManagers((resp.data?.data || resp.data?.result?.data || []) as any);
      } catch {
        setManagers([]);
      }
    })();
  }, []);

  const docsSorted = useMemo(() => {
    return [...docs].sort((a, b) => {
      const ta = a.upload_date ? new Date(a.upload_date).getTime() : Number.POSITIVE_INFINITY;
      const tb = b.upload_date ? new Date(b.upload_date).getTime() : Number.POSITIVE_INFINITY;
      return ta - tb;
    });
  }, [docs]);

  const mainDoc = docsSorted[0] || null;
  const subDocs = docsSorted.slice(1);

  const openSignature = () => {
    if (!mainDoc) return;
    setSignatureSignerId('');
    setSignatureMessage('');
    setSignatureOpen(true);
  };

  const submitSignature = async () => {
    if (!mainDoc) return;
    if (!signatureSignerId) {
      toast.error('اختر الموقّع');
      return;
    }
    try {
      const res = await signaturesApi.create({
        document_id: mainDoc.id,
        signer_id: Number(signatureSignerId),
        message: signatureMessage || undefined,
      });
      if (!res.success) throw new Error(res.error || 'فشل إنشاء طلب التوقيع');
      toast.success('تم إنشاء طلب توقيع');
      setSignatureOpen(false);
      navigate('/signatures');
    } catch (e: any) {
      toast.error(e?.message || 'فشل إنشاء طلب التوقيع');
    }
  };

  const openEditRequest = () => {
    if (!mainDoc) return;
    setEditReason('');
    setEditOpen(true);
  };

  const submitEditRequest = async () => {
    if (!mainDoc) return;
    if (!editReason.trim()) {
      toast.error('اكتب سبب طلب التعديل');
      return;
    }
    try {
      const res = await editRequestsApi.createEditRequest(mainDoc.id, editReason.trim());
      if (!res.success) throw new Error('فشل إنشاء طلب التعديل');
      toast.success('تم إنشاء طلب تعديل');
      setEditOpen(false);
      navigate('/edit-requests');
    } catch (e: any) {
      toast.error(e?.message || 'فشل إنشاء طلب التعديل');
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 900 }}>
            {folder?.name || t('nav.folders')}
          </Typography>
          <Typography color="text.secondary" sx={{ mt: 0.5 }}>
            {folder?.code ? `${folder.code}` : ''} {loading ? `• ${t('common.loading')}` : ''}
          </Typography>
        </Box>

        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          <Button
            variant="contained"
            onClick={() => {
              if (!id) return;
              const kind = docs.length === 0 ? 'main' : 'sub';
              const qs = new URLSearchParams();
              qs.set('upload_kind', kind);
              qs.set('folder_id', String(id));
              if (folder?.department_id) qs.set('department_id', String(folder.department_id));
              navigate(`/documents/upload?${qs.toString()}`);
            }}
            sx={{ borderRadius: 999 }}
          >
            رفع داخل الإضبارة
          </Button>
          <Button onClick={() => navigate('/folders')}>{t('common.back')}</Button>
        </Box>
      </Box>

      {error && (
        <Paper sx={{ p: 2, mt: 2, border: '1px solid rgba(211,47,47,0.2)', background: 'rgba(211,47,47,0.04)' }}>
          <Typography color="error">{error}</Typography>
        </Paper>
      )}

      <Paper sx={{ mt: 2, overflow: 'hidden' }}>
        <Box
          sx={{
            px: 3,
            py: 2,
            background: '#111111',
            color: 'white',
          }}
        >
          <Typography sx={{ fontWeight: 900 }}>{t('documents.title')}</Typography>
        </Box>

        {docs.length === 0 ? (
          <Box sx={{ p: 3 }}>
            <Typography color="text.secondary">{t('common.noData')}</Typography>
          </Box>
        ) : (
          <>
            {/* Main document: first uploaded inside folder */}
            <Box sx={{ p: 3 }}>
              <Typography sx={{ fontWeight: 900, mb: 1.5 }}>📌 المستند الرئيسي (أول ملف رُفع)</Typography>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>{t('documents.barcode')}</TableCell>
                    <TableCell>{t('documents.name')}</TableCell>
                    <TableCell>{t('documents.type')}</TableCell>
                    <TableCell>{t('documents.uploadDate')}</TableCell>
                    <TableCell>{t('documents.status')}</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {(mainDoc ? [mainDoc] : []).map((d) => (
                    <TableRow key={d.id} hover>
                      <TableCell sx={{ fontWeight: 800 }}>{d.barcode}</TableCell>
                      <TableCell sx={{ cursor: 'pointer' }} onClick={() => navigate(`/documents/${d.id}`)}>{d.title}</TableCell>
                      <TableCell>{d.document_type_name}</TableCell>
                      <TableCell>{d.upload_date ? new Date(d.upload_date).toLocaleString() : '-'}</TableCell>
                      <TableCell>{d.status}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Box>

            {/* Sub documents: all other docs in folder */}
            <Box sx={{ px: 3, pb: 3 }}>
              <Typography sx={{ fontWeight: 900, mb: 1.5 }}>🧩 المستندات الثانوية (ضمن نفس الإضبارة)</Typography>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>{t('documents.barcode')}</TableCell>
                    <TableCell>{t('documents.name')}</TableCell>
                    <TableCell>{t('documents.type')}</TableCell>
                    <TableCell>{t('documents.uploadDate')}</TableCell>
                    <TableCell>{t('documents.status')}</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {subDocs.map((d) => (
                    <TableRow key={d.id} hover>
                      <TableCell sx={{ fontWeight: 800 }}>{d.barcode}</TableCell>
                      <TableCell sx={{ cursor: 'pointer' }} onClick={() => navigate(`/documents/${d.id}`)}>{d.title}</TableCell>
                      <TableCell>{d.document_type_name}</TableCell>
                      <TableCell>{d.upload_date ? new Date(d.upload_date).toLocaleString() : '-'}</TableCell>
                      <TableCell>{d.status}</TableCell>
                    </TableRow>
                  ))}
                  {subDocs.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={5} align="center">
                        <Typography color="text.secondary">{t('common.noData')}</Typography>
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </Box>
          </>
        )}
      </Paper>

      {/* Attachments */}
      <Paper sx={{ mt: 2, overflow: 'hidden' }}>
        <Box sx={{ px: 3, py: 2, background: '#111111', color: 'white', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
          <Typography sx={{ fontWeight: 900 }}>📎 المرفقات</Typography>
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', flexWrap: 'wrap' }}>
            <TextField
              select
              size="small"
              label="المستند"
              value={attachmentsDocId}
              onChange={(e) => setAttachmentsDocId(e.target.value ? Number(e.target.value) : '')}
              sx={{ minWidth: 260, bgcolor: 'white', borderRadius: 1 }}
            >
              {docs.map((d) => (
                <MenuItem key={d.id} value={d.id}>
                  {d.title} — {d.barcode}
                </MenuItem>
              ))}
            </TextField>
            <Button
              variant="outlined"
              color="inherit"
              onClick={() => {
                const qs = new URLSearchParams();
                qs.set('upload_kind', 'attachment');
                if (attachmentsDocId !== '') qs.set('target_document_id', String(attachmentsDocId));
                navigate(`/documents/upload?${qs.toString()}`);
              }}
              sx={{ borderColor: 'rgba(255,255,255,0.4)', color: 'white' }}
            >
              إضافة مرفق
            </Button>
          </Box>
        </Box>

        {attachments.length === 0 ? (
          <Box sx={{ p: 3 }}>
            <Typography color="text.secondary">{t('common.noData')}</Typography>
          </Box>
        ) : (
          <Box sx={{ p: 3 }}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>الاسم</TableCell>
                  <TableCell>الوصف</TableCell>
                  <TableCell>الرافع</TableCell>
                  <TableCell>التاريخ</TableCell>
                  <TableCell align="right">إجراءات</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {attachments.map((a) => (
                  <TableRow key={a.id} hover>
                    <TableCell sx={{ fontWeight: 800 }}>{a.name || a.file_name}</TableCell>
                    <TableCell>{a.description || '-'}</TableCell>
                    <TableCell>{a.uploader_name || '-'}</TableCell>
                    <TableCell>{a.upload_date ? new Date(a.upload_date).toLocaleString() : '-'}</TableCell>
                    <TableCell align="right">
                      <Button
                        size="small"
                        variant="outlined"
                        onClick={() => window.open(`/api/documents/${Number(attachmentsDocId)}/attachments/${a.id}/download`, '_blank')}
                      >
                        تحميل
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Box>
        )}
      </Paper>

      {/* Diagram (simple) */}
      <Paper sx={{ mt: 2, p: 3 }}>
        <Typography sx={{ fontWeight: 900, mb: 1.5 }}>🗺️ مخطط الإضبارة</Typography>
        <Typography color="text.secondary" sx={{ mb: 2 }}>
          عرض مُلخّص: المستند الرئيسي هو أول ملف رُفع داخل الإضبارة، وبعده المستندات الثانوية حسب ترتيب الرفع.
        </Typography>
        {!mainDoc ? (
          <Typography color="text.secondary">{t('common.noData')}</Typography>
        ) : (
          <Box>
            <Typography sx={{ fontWeight: 900 }}>MAIN: {mainDoc.title}</Typography>
            <Typography sx={{ fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace', color: 'text.secondary', mt: 0.5 }}>
              {mainDoc.barcode}
            </Typography>
            <Box sx={{ mt: 1.5, pl: 2, borderLeft: '2px solid rgba(0,0,0,0.2)' }}>
              {subDocs.length === 0 ? (
                <Typography color="text.secondary">لا توجد مستندات ثانوية بعد.</Typography>
              ) : (
                subDocs.map((d) => (
                  <Typography key={d.id} sx={{ color: 'text.secondary', mb: 0.6 }}>
                    └─ SUB: {d.title}
                  </Typography>
                ))
              )}
            </Box>
          </Box>
        )}
      </Paper>

      {/* Workflow actions */}
      <Paper sx={{ mt: 2, overflow: 'hidden' }}>
        <Box sx={{ px: 3, py: 2, background: '#111111', color: 'white' }}>
          <Typography sx={{ fontWeight: 900 }}>⚙️ الإجراءات المتاحة (Workflow)</Typography>
          <Typography sx={{ opacity: 0.85, mt: 0.5, fontSize: 13 }}>
            {workflowInfo?.workflow_name ? `سير العمل: ${workflowInfo.workflow_name}` : 'لا يوجد سير عمل مرتبط بالإضبارة'}
            {workflowInfo?.state_name ? ` • الحالة الحالية: ${workflowInfo.state_name}` : ''}
          </Typography>
        </Box>

        <Box sx={{ p: 3 }}>
          {workflowError && (
            <Paper sx={{ p: 2, mb: 2, border: '1px solid rgba(211,47,47,0.2)', background: 'rgba(211,47,47,0.04)' }}>
              <Typography color="error">{workflowError}</Typography>
            </Paper>
          )}

          {!workflowInfo?.workflow_id ? (
            <Typography color="text.secondary">
              لا يوجد Workflow مُعيّن لهذه الإضبارة بعد. (التعيين يتم عبر API: <code>/api/folders/&lt;id&gt;/workflow/set</code>)
            </Typography>
          ) : (workflowInfo.allowed_transitions || []).length === 0 ? (
            <Typography color="text.secondary">لا توجد انتقالات مسموحة لك في هذه الحالة.</Typography>
          ) : (
            <Box>
              {(workflowInfo.allowed_transitions || []).some((tr) => tr.requires_request) && (
                <Paper sx={{ p: 2, mb: 2, border: '1px solid rgba(0,0,0,0.10)', background: 'rgba(0,0,0,0.02)' }}>
                  <Typography sx={{ fontWeight: 800, mb: 1 }}>إجراءات مرتبطة بالحالة</Typography>
                  <Typography color="text.secondary" sx={{ mb: 1.5 }}>
                    بعض الانتقالات تتطلب إنشاء طلب (توقيع/تعديل). سيتم تطبيق الطلب على المستند الرئيسي للإضبارة.
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    <Button variant="outlined" onClick={openSignature} disabled={!mainDoc}>
                      طلب توقيع
                    </Button>
                    <Button variant="outlined" onClick={openEditRequest} disabled={!mainDoc}>
                      طلب تعديل
                    </Button>
                  </Box>
                </Paper>
              )}

              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {(workflowInfo.allowed_transitions || []).map((tr) => (
                  <Button
                    key={tr.id}
                    variant="contained"
                    onClick={() => openTransition(tr.id, `${tr.name} → ${tr.to_state_name}`)}
                    sx={{ borderRadius: 999 }}
                  >
                    {tr.name} → {tr.to_state_name}
                    {tr.requires_request ? ' (يتطلب طلب)' : ''}
                  </Button>
                ))}
              </Box>
            </Box>
          )}
        </Box>
      </Paper>

      {/* Transition message dialog */}
      <Dialog open={transitionOpen} onClose={() => setTransitionOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>تغيير حالة الإضبارة</DialogTitle>
        <DialogContent>
          <Typography color="text.secondary" sx={{ mb: 2 }}>
            {transitionTarget?.label || ''}
          </Typography>
          <TextField
            fullWidth
            multiline
            rows={3}
            label="رسالة/ملاحظة للحالة الجديدة (اختياري)"
            value={transitionMessage}
            onChange={(e) => setTransitionMessage(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTransitionOpen(false)}>إلغاء</Button>
          <Button variant="contained" onClick={submitTransition} disabled={!transitionTarget}>
            تطبيق
          </Button>
        </DialogActions>
      </Dialog>

      {/* Signature request dialog (for main document) */}
      <Dialog open={signatureOpen} onClose={() => setSignatureOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>طلب توقيع على المستند الرئيسي</DialogTitle>
        <DialogContent>
          <Typography color="text.secondary" sx={{ mb: 2 }}>
            {mainDoc ? `${mainDoc.title} — ${mainDoc.barcode}` : 'لا يوجد مستند رئيسي'}
          </Typography>
          <TextField
            select
            fullWidth
            label="الموقّع *"
            value={signatureSignerId}
            onChange={(e) => setSignatureSignerId(e.target.value ? Number(e.target.value) : '')}
          >
            <MenuItem value="">اختر الموقّع</MenuItem>
            {managers.map((m) => (
              <MenuItem key={m.id} value={m.id}>
                {m.name}
              </MenuItem>
            ))}
          </TextField>
          <TextField
            fullWidth
            multiline
            rows={3}
            label="رسالة (اختياري)"
            value={signatureMessage}
            onChange={(e) => setSignatureMessage(e.target.value)}
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSignatureOpen(false)}>إلغاء</Button>
          <Button variant="contained" onClick={submitSignature} disabled={!mainDoc}>
            إنشاء
          </Button>
        </DialogActions>
      </Dialog>

      {/* Edit request dialog (for main document) */}
      <Dialog open={editOpen} onClose={() => setEditOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>طلب تعديل على المستند الرئيسي</DialogTitle>
        <DialogContent>
          <Typography color="text.secondary" sx={{ mb: 2 }}>
            {mainDoc ? `${mainDoc.title} — ${mainDoc.barcode}` : 'لا يوجد مستند رئيسي'}
          </Typography>
          <TextField
            fullWidth
            multiline
            rows={4}
            label="سبب طلب التعديل *"
            value={editReason}
            onChange={(e) => setEditReason(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditOpen(false)}>إلغاء</Button>
          <Button variant="contained" onClick={submitEditRequest} disabled={!mainDoc}>
            إنشاء
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}


