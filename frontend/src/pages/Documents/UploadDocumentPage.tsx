import { useEffect, useMemo, useState } from 'react';
import {
  Box,
  Button,
  Grid,
  MenuItem,
  Paper,
  TextField,
  Typography,
} from '@mui/material';
import { useTranslation } from 'react-i18next';
import { useLocation, useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { adminApi } from '../../api/admin.api';
import { documentsApi } from '../../api/documents.api';
import apiClient from '../../api/client';

function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () => reject(new Error('Failed to read file'));
    reader.onload = () => {
      const result = String(reader.result || '');
      // result is like: data:application/pdf;base64,XXXXX
      const comma = result.indexOf(',');
      resolve(comma >= 0 ? result.slice(comma + 1) : result);
    };
    reader.readAsDataURL(file);
  });
}

export default function UploadDocumentPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();

  const [departments, setDepartments] = useState<Array<{ id: number; name: string; code: string }>>([]);
  const [docTypes, setDocTypes] = useState<Array<{ id: number; name: string; code: string; department_id: number }>>(
    []
  );
  const [folders, setFolders] = useState<Array<{ id: number; name: string; code: string }>>([]);
  const [loading, setLoading] = useState(false);

  // Upload kind (main/sub/attachment)
  const [uploadKind, setUploadKind] = useState<'main' | 'sub' | 'attachment'>('main');
  const [targetDocumentId, setTargetDocumentId] = useState<number | ''>(''); // for attachment

  // Auto-create folder (only for main)
  const [createNewFolder, setCreateNewFolder] = useState(false);
  const [newFolderName, setNewFolderName] = useState('');
  const [newFolderCode, setNewFolderCode] = useState('');
  const [newFolderDescription, setNewFolderDescription] = useState('');

  // Form fields
  const [departmentId, setDepartmentId] = useState<number | ''>('');
  const [documentTypeId, setDocumentTypeId] = useState<number | ''>('');
  const [title, setTitle] = useState('');
  const [folderId, setFolderId] = useState<number | ''>('');
  const [confidentiality, setConfidentiality] = useState<'public' | 'internal' | 'confidential' | 'strict'>(
    'internal'
  );
  const [poNumber, setPoNumber] = useState('');
  const [blNumber, setBlNumber] = useState('');
  const [containerNumber, setContainerNumber] = useState('');
  const [invoiceNumber, setInvoiceNumber] = useState('');
  const [envoyNumber, setEnvoyNumber] = useState('');
  const [file, setFile] = useState<File | null>(null);

  useEffect(() => {
    (async () => {
      const depts = await adminApi.getDepartments();
      setDepartments(depts.data);
    })();
  }, []);

  useEffect(() => {
    // Prefill from query params (folder direct upload / attachment flow)
    const sp = new URLSearchParams(location.search || '');
    const qKind = (sp.get('upload_kind') || '').toLowerCase();
    const qFolderId = sp.get('folder_id');
    const qDeptId = sp.get('department_id');
    const qTargetDocId = sp.get('target_document_id');

    if (qKind === 'main' || qKind === 'sub' || qKind === 'attachment') {
      setUploadKind(qKind as any);
    }
    if (qFolderId) {
      const n = Number(qFolderId);
      if (!Number.isNaN(n)) setFolderId(n);
    }
    if (qDeptId) {
      const n = Number(qDeptId);
      if (!Number.isNaN(n)) setDepartmentId(n);
    }
    if (qTargetDocId) {
      const n = Number(qTargetDocId);
      if (!Number.isNaN(n)) setTargetDocumentId(n);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    (async () => {
      if (!departmentId) {
        setDocTypes([]);
        setDocumentTypeId('');
        setFolders([]);
        setFolderId('');
        return;
      }
      const types = await adminApi.getDocumentTypes(Number(departmentId));
      setDocTypes(types.data as any);
      setDocumentTypeId('');

      // Load folders for this department (optional)
      try {
        const resp = await apiClient.post('/api/folders', {
          jsonrpc: '2.0',
          method: 'call',
          params: { department_id: Number(departmentId) },
        });
        const result = resp.data.result || resp.data;
        setFolders(result.data || []);
      } catch {
        setFolders([]);
      }
    })();
  }, [departmentId]);

  const canSubmit = useMemo(() => {
    if (loading) return false;
    if (!file) return false;
    if (title.trim().length === 0) return false;

    if (uploadKind === 'attachment') {
      return !!targetDocumentId;
    }

    // main / sub => document upload
    if (!departmentId || !documentTypeId) return false;
    if (uploadKind === 'main' && createNewFolder) {
      return newFolderName.trim().length > 0 && newFolderCode.trim().length > 0 && !!departmentId;
    }
    return true;
  }, [
    loading,
    file,
    title,
    uploadKind,
    targetDocumentId,
    departmentId,
    documentTypeId,
    createNewFolder,
    newFolderName,
    newFolderCode,
  ]);

  const onSubmit = async () => {
    if (!canSubmit || !file) return;
    setLoading(true);
    try {
      const fileData = await fileToBase64(file);

      if (uploadKind === 'attachment') {
        const resp = await apiClient.post(`/api/documents/${Number(targetDocumentId)}/add-attachment`, {
          jsonrpc: '2.0',
          method: 'call',
          params: {
            name: title.trim(),
            description: null,
            file_data: fileData,
            file_name: file.name,
            attachment_type: 'supporting',
          },
        });
        const result = resp.data.result || resp.data;
        if (!result.success) throw new Error(result.error || 'Upload attachment failed');
        toast.success('تم إضافة المرفق بنجاح');
        navigate(`/documents/${Number(targetDocumentId)}`);
        return;
      }

      let finalFolderId: number | '' = folderId;
      if (uploadKind === 'main' && createNewFolder) {
        const folderResp = await apiClient.post('/api/folders/create', {
          jsonrpc: '2.0',
          method: 'call',
          params: {
            name: newFolderName.trim(),
            code: newFolderCode.trim(),
            department_id: Number(departmentId),
            folder_type: 'other',
            description: newFolderDescription.trim() || null,
            document_ids: [],
          },
        });
        const folderResult = folderResp.data.result || folderResp.data;
        if (!folderResult.success) throw new Error(folderResult.error || 'Failed to create folder');
        finalFolderId = Number(folderResult.data.id);
      }

      const resp = await documentsApi.uploadDocument({
        department_id: Number(departmentId),
        document_type_id: Number(documentTypeId),
        title: title.trim(),
        file_data: fileData,
        file_name: file.name,
        confidentiality_level: confidentiality,
        folder_ids: finalFolderId ? [Number(finalFolderId)] : [],
        upload_kind: uploadKind,
        // Send searchable numbers as direct params (backend expects them outside custom_fields)
        po_number: poNumber || undefined,
        bl_number: blNumber || undefined,
        container_number: containerNumber || undefined,
        invoice_number: invoiceNumber || undefined,
        envoy_number: envoyNumber || undefined,
      } as any);

      if (!resp.success) throw new Error(resp.error || 'Upload failed');

      toast.success(`تم رفع المستند بنجاح! الباركود: ${resp.data.barcode}`);
      navigate(`/documents/${resp.data.id}`);
    } catch (e: any) {
      const errMsg = e?.response?.data?.error || e?.message || 'فشل رفع المستند';
      console.error('Upload error:', e);
      console.error('Error details:', e?.response?.data);
      toast.error(errMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 2, flexWrap: 'wrap', mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 900, color: 'text.primary' }}>
          {t('documents.uploadNew')}
        </Typography>
        <Button variant="outlined" onClick={() => navigate('/documents')}>{t('common.cancel')}</Button>
      </Box>

      <Paper elevation={2} sx={{ p: 4, mt: 2, borderRadius: 3, background: '#fff', border: '1px solid rgba(0,0,0,0.06)' }}>
        <Typography variant="h6" sx={{ mb: 3, fontWeight: 700, color: '#333' }}>
          معلومات المستند الأساسية
        </Typography>
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <TextField
              select
              fullWidth
              label="نوع الرفع"
              value={uploadKind}
              onChange={(e) => setUploadKind(e.target.value as any)}
            >
              <MenuItem value="main">مستند رئيسي</MenuItem>
              <MenuItem value="sub">مستند فرعي</MenuItem>
              <MenuItem value="attachment">مرفق</MenuItem>
            </TextField>
          </Grid>

          {uploadKind === 'attachment' && (
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="معرّف المستند (document_id) لإضافة المرفق *"
                value={targetDocumentId}
                onChange={(e) => setTargetDocumentId(e.target.value ? Number(e.target.value) : '')}
                required
              />
            </Grid>
          )}

          {uploadKind !== 'attachment' && (
            <>
              <Grid item xs={12} md={6}>
                <TextField
                  select
                  fullWidth
                  label="📁 القسم *"
                  value={departmentId}
                  onChange={(e) => setDepartmentId(e.target.value ? Number(e.target.value) : '')}
                  required
                  variant="outlined"
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      '&:hover fieldset': { borderColor: '#111111' },
                      '&.Mui-focused fieldset': { borderColor: '#111111' },
                    },
                  }}
                >
                  <MenuItem value="">اختر القسم</MenuItem>
                  {departments.map((d) => (
                    <MenuItem key={d.id} value={d.id}>
                      {d.name} ({d.code})
                    </MenuItem>
                  ))}
                </TextField>
              </Grid>

              <Grid item xs={12} md={6}>
                <TextField
                  select
                  fullWidth
                  label="📄 نوع المستند *"
                  value={documentTypeId}
                  onChange={(e) => setDocumentTypeId(e.target.value ? Number(e.target.value) : '')}
                  disabled={!departmentId}
                  required
                  variant="outlined"
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      '&:hover fieldset': { borderColor: '#111111' },
                      '&.Mui-focused fieldset': { borderColor: '#111111' },
                    },
                  }}
                >
                  <MenuItem value="">اختر نوع المستند</MenuItem>
                  {(docTypes || []).map((dt: any) => (
                    <MenuItem key={dt.id} value={dt.id}>
                      {dt.name} ({dt.code})
                    </MenuItem>
                  ))}
                </TextField>
              </Grid>
            </>
          )}

          <Grid item xs={12}>
            <TextField
              fullWidth
              label="📝 عنوان المستند *"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
              placeholder="أدخل عنواناً واضحاً للمستند"
              variant="outlined"
              sx={{ 
                '& .MuiOutlinedInput-root': {
                  '&:hover fieldset': { borderColor: '#111111' },
                  '&.Mui-focused fieldset': { borderColor: '#111111' }
                }
              }}
            />
          </Grid>

          {uploadKind !== 'attachment' && (
          <Grid item xs={12} md={6}>
            <TextField
              select
              fullWidth
              label="📁 ربط بإضبارة (اختياري)"
              value={folderId}
              onChange={(e) => setFolderId(e.target.value ? Number(e.target.value) : '')}
              disabled={!departmentId}
            >
              <MenuItem value="">(بدون) — لا تربط بإضبارة</MenuItem>
              {folders.map((f) => (
                <MenuItem key={f.id} value={f.id}>
                  {f.name} — {f.code}
                </MenuItem>
              ))}
            </TextField>
          </Grid>
          )}

          {uploadKind === 'main' && (
            <Grid item xs={12} md={6}>
              <TextField
                select
                fullWidth
                label="إنشاء إضبارة جديدة تلقائيًا؟"
                value={createNewFolder ? 'yes' : 'no'}
                onChange={(e) => setCreateNewFolder(e.target.value === 'yes')}
                disabled={!departmentId}
              >
                <MenuItem value="no">لا</MenuItem>
                <MenuItem value="yes">نعم</MenuItem>
              </TextField>
            </Grid>
          )}

          {uploadKind === 'main' && createNewFolder && (
            <>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="اسم الإضبارة الجديدة *"
                  value={newFolderName}
                  onChange={(e) => setNewFolderName(e.target.value)}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="كود الإضبارة الجديدة *"
                  value={newFolderCode}
                  onChange={(e) => setNewFolderCode(e.target.value)}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="وصف الإضبارة"
                  value={newFolderDescription}
                  onChange={(e) => setNewFolderDescription(e.target.value)}
                />
              </Grid>
            </>
          )}

          {uploadKind === 'sub' && (
            <Grid item xs={12}>
              <Paper sx={{ p: 2, border: '1px solid rgba(0,0,0,0.08)', background: 'rgba(0,0,0,0.02)' }}>
                <Typography sx={{ fontWeight: 800, mb: 0.5 }}>مستند فرعي</Typography>
                <Typography color="text.secondary">
                  في نظام الإضبارة: المستندات الثانوية هي أي ملفات إضافية داخل نفس الإضبارة. لا نستخدم parent_document_id.
                </Typography>
              </Paper>
            </Grid>
          )}

          <Grid item xs={12} md={6}>
            <TextField
              select
              fullWidth
              label="🔐 مستوى السرية"
              value={confidentiality}
              onChange={(e) => setConfidentiality(e.target.value as any)}
              variant="outlined"
              sx={{ 
                '& .MuiOutlinedInput-root': {
                  '&:hover fieldset': { borderColor: '#111111' },
                  '&.Mui-focused fieldset': { borderColor: '#111111' }
                }
              }}
            >
              <MenuItem value="public">🌍 عام (Public)</MenuItem>
              <MenuItem value="internal">🏢 داخلي (Internal)</MenuItem>
              <MenuItem value="confidential">🔒 سري (Confidential)</MenuItem>
              <MenuItem value="strict">🔐 سري للغاية (Strict)</MenuItem>
            </TextField>
          </Grid>

          <Grid item xs={12} md={6}>
            <Button 
              variant="outlined" 
              component="label" 
              fullWidth 
              sx={{ 
                py: 1.8,
                borderWidth: 2,
                borderStyle: 'dashed',
                borderColor: '#111111',
                color: '#111111',
                fontWeight: 700,
                '&:hover': {
                  borderWidth: 2,
                  borderColor: '#000000',
                  background: 'rgba(0,0,0,0.03)'
                }
              }}
            >
              {file ? `✅ ${file.name}` : '📎 اختر ملف للرفع *'}
              <input
                type="file"
                hidden
                onChange={(e) => setFile(e.target.files?.[0] || null)}
              />
            </Button>
          </Grid>

          {/* Advanced searchable numbers */}
          <Grid item xs={12}>
            <Typography variant="h6" sx={{ mt: 2, mb: 1, fontWeight: 800, color: 'text.primary' }}>
              🔍 أرقام قابلة للبحث (اختياري)
            </Typography>
          </Grid>
          <Grid item xs={12} md={4}>
            <TextField 
              fullWidth 
              label="رقم PO (أمر الشراء)" 
              value={poNumber} 
              onChange={(e) => setPoNumber(e.target.value)}
              placeholder="PO-2024-001"
              variant="outlined"
            />
          </Grid>
          <Grid item xs={12} md={4}>
            <TextField 
              fullWidth 
              label="رقم BL (بوليصة الشحن)" 
              value={blNumber} 
              onChange={(e) => setBlNumber(e.target.value)}
              placeholder="BL-2024-001"
              variant="outlined"
            />
          </Grid>
          <Grid item xs={12} md={4}>
            <TextField 
              fullWidth 
              label="رقم الحاوية" 
              value={containerNumber} 
              onChange={(e) => setContainerNumber(e.target.value)}
              placeholder="CONT-2024-001"
              variant="outlined"
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <TextField 
              fullWidth 
              label="رقم الفاتورة" 
              value={invoiceNumber} 
              onChange={(e) => setInvoiceNumber(e.target.value)}
              placeholder="INV-2024-001"
              variant="outlined"
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <TextField 
              fullWidth 
              label="رقم المبعوث" 
              value={envoyNumber} 
              onChange={(e) => setEnvoyNumber(e.target.value)}
              placeholder="ENV-2024-001"
              variant="outlined"
            />
          </Grid>

          <Grid item xs={12}>
            <Button 
              variant="contained" 
              fullWidth 
              disabled={!canSubmit} 
              onClick={onSubmit}
              sx={{ 
                py: 1.8, 
                fontSize: '1.1rem', 
                fontWeight: 700,
                '&:hover': {
                  transform: 'translateY(-2px)',
                  boxShadow: '0 16px 52px rgba(0,0,0,0.14)'
                },
                transition: 'all 0.3s'
              }}
            >
              {loading ? 'جاري الرفع...' : 'رفع المستند'}
            </Button>
          </Grid>
        </Grid>
      </Paper>
    </Box>
  );
}


