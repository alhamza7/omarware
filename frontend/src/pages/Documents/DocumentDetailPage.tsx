import { useEffect, useMemo, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Chip,
  Button,
  Table,
  TableBody,
  TableCell,
  TableRow,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
} from '@mui/material';
import { ArrowBack as BackIcon, Download as DownloadIcon } from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { useDocumentStore } from '../../stores/documentStore';
import { useAuthStore } from '../../stores/authStore';
import { usersApi } from '../../api/users.api';
import { useSignatureStore } from '../../stores/signatureStore';
import { fileToBase64 } from '../../utils/file';
import { format } from 'date-fns';
import toast from 'react-hot-toast';

export default function DocumentDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { currentDocument, isLoading, fetchDocument, downloadVersion } = useDocumentStore();
  const user = useAuthStore((s) => s.user);
  const canRequestSignature = !!user && (!user.is_manager || user.is_admin);
  const { requests, fetchRequests, createRequest, uploadSigned } = useSignatureStore();

  const [openRequestSign, setOpenRequestSign] = useState(false);
  const [managers, setManagers] = useState<Array<{ id: number; name: string; login: string }>>([]);
  const [selectedSignerId, setSelectedSignerId] = useState<number | ''>('');
  const [signMessage, setSignMessage] = useState('');

  const [openUploadSigned, setOpenUploadSigned] = useState(false);
  const [selectedApprovedReqId, setSelectedApprovedReqId] = useState<number | null>(null);
  const [signToken, setSignToken] = useState('');
  const [signedFile, setSignedFile] = useState<File | null>(null);

  const docId = useMemo(() => {
    if (!id) return null;
    const num = parseInt(id, 10);
    return Number.isFinite(num) ? num : null;
  }, [id]);

  const signatureRows = useMemo(() => {
    const all = requests || [];
    if (!docId) return [];
    return all.filter((r: any) => r.document_id === docId);
  }, [requests, docId]);
  const approvedRequests = useMemo(() => signatureRows.filter((r: any) => r.state === 'approved'), [signatureRows]);

  useEffect(() => {
    if (docId) {
      fetchDocument(docId);
      fetchRequests({ document_id: docId });
    }
  }, [docId, fetchDocument, fetchRequests]);

  useEffect(() => {
    // Load managers for signer selection
    (async () => {
      try {
        const departmentId = (currentDocument as any)?.department_id;
        const resp = await usersApi.getManagers(departmentId);
        setManagers(resp.data || []);
      } catch {
        setManagers([]);
      }
    })();
  }, [(currentDocument as any)?.department_id]);

  const handleDownload = async (versionId: number, fileName: string) => {
    if (currentDocument) {
      await downloadVersion(currentDocument.id, versionId, fileName);
    }
  };

  const title = (currentDocument as any)?.name || (currentDocument as any)?.title || '-';
  const documentTypeName =
    (currentDocument as any)?.document_type?.name || (currentDocument as any)?.document_type_name || '-';
  const departmentName =
    (currentDocument as any)?.department?.name || (currentDocument as any)?.department_name || '-';
  const uploaderName =
    (currentDocument as any)?.uploader?.name || (currentDocument as any)?.uploader_name || '-';
  const tagsRaw = Array.isArray((currentDocument as any)?.tags) ? (currentDocument as any).tags : [];
  const tags = tagsRaw.filter(Boolean);
  const versions = Array.isArray((currentDocument as any)?.versions) ? (currentDocument as any).versions : [];
  const ocr = (currentDocument as any)?.ocr || {};
  const fileName: string = (currentDocument as any)?.file_name || '';
  const fileExt = (fileName.split('.').pop() || '').toLowerCase();
  const isOcrSupported = ['pdf', 'jpg', 'jpeg', 'png', 'tiff'].includes(fileExt);
  const ocrStatus = (currentDocument as any)?.ocr_status || ocr?.ocr_status || 'pending';

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (!currentDocument) {
    return (
      <Box>
        <Typography>{t('errors.notFound')}</Typography>
      </Box>
    );
  }

  const onCreateSignatureRequest = async () => {
    if (!currentDocument?.id || !selectedSignerId) return;
    try {
      await createRequest({
        document_id: currentDocument.id,
        signer_id: Number(selectedSignerId),
        message: signMessage || undefined,
      });
      toast.success('تم إرسال طلب التوقيع');
      setOpenRequestSign(false);
      setSelectedSignerId('');
      setSignMessage('');
      fetchRequests({ document_id: currentDocument.id });
    } catch (e: any) {
      toast.error(e?.message || 'فشل إرسال طلب التوقيع');
    }
  };

  const onUploadSigned = async () => {
    if (!selectedApprovedReqId || !signedFile || !signToken.trim()) return;
    try {
      const fileData = await fileToBase64(signedFile);
      await uploadSigned(selectedApprovedReqId, {
        file_data: fileData,
        file_name: signedFile.name,
        sign_token: signToken.trim(),
        notes: 'Signed version upload',
      });
      toast.success('تم رفع النسخة الموقّعة بنجاح');
      setOpenUploadSigned(false);
      setSelectedApprovedReqId(null);
      setSignToken('');
      setSignedFile(null);
      fetchDocument((currentDocument as any).id);
      fetchRequests({ document_id: (currentDocument as any).id });
    } catch (e: any) {
      toast.error(e?.message || 'فشل رفع النسخة الموقعة');
    }
  };

  return (
    <Box>
      <Box display="flex" alignItems="center" mb={3}>
        <Button startIcon={<BackIcon />} onClick={() => navigate('/documents')}>
          {t('common.back')}
        </Button>
      </Box>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          {title}
        </Typography>

        <Grid container spacing={2} sx={{ mt: 2 }}>
          <Grid item xs={12} md={6}>
            <Table size="small">
              <TableBody>
                <TableRow>
                  <TableCell><strong>{t('documents.barcode')}</strong></TableCell>
                  <TableCell>{(currentDocument as any).barcode || '-'}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell><strong>{t('documents.type')}</strong></TableCell>
                  <TableCell>{documentTypeName}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell><strong>{t('documents.department')}</strong></TableCell>
                  <TableCell>{departmentName}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell><strong>{t('documents.uploader')}</strong></TableCell>
                  <TableCell>{uploaderName}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell><strong>{t('documents.uploadDate')}</strong></TableCell>
                  <TableCell>
                    {(currentDocument as any).upload_date
                      ? format(new Date((currentDocument as any).upload_date), 'yyyy-MM-dd HH:mm')
                      : '-'}
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </Grid>

          <Grid item xs={12} md={6}>
            <Table size="small">
              <TableBody>
                <TableRow>
                  <TableCell><strong>{t('documents.status')}</strong></TableCell>
                  <TableCell>
                    <Chip label={(currentDocument as any).status || '-'} color="success" size="small" />
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell><strong>{t('documents.confidentiality')}</strong></TableCell>
                  <TableCell>{(currentDocument as any).confidentiality_level || '-'}</TableCell>
                </TableRow>
                {!!ocrStatus && (
                  <TableRow>
                    <TableCell><strong>{t('documents.ocrStatus')}</strong></TableCell>
                    <TableCell>
                      <Chip
                        label={ocrStatus}
                        size="small"
                        color={
                          ocrStatus === 'completed'
                            ? 'success'
                            : ocrStatus === 'failed'
                              ? 'error'
                              : ocrStatus === 'processing'
                                ? 'info'
                                : 'warning'
                        }
                      />
                    </TableCell>
                  </TableRow>
                )}
                {tags.length > 0 && (
                  <TableRow>
                    <TableCell><strong>{t('documents.tags')}</strong></TableCell>
                    <TableCell>
                      {tags.map((tag: any, idx: number) => {
                        const key = (tag && (tag.id ?? tag.name)) ?? `tag-${idx}`;
                        const label = (tag && tag.name) ?? (typeof tag === 'string' ? tag : String(tag ?? ''));
                        return <Chip key={key} label={label} size="small" sx={{ mr: 0.5 }} />;
                      })}
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </Grid>
        </Grid>
      </Paper>

      {/* OCR Preview */}
      {isOcrSupported ? (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Box display="flex" justifyContent="space-between" alignItems="center" gap={2} flexWrap="wrap">
            <Typography variant="h6" sx={{ fontWeight: 900 }}>
              OCR
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {ocr.current_version_ocr_date ? format(new Date(ocr.current_version_ocr_date), 'yyyy-MM-dd HH:mm') : ''}
              {typeof ocr.extracted_text_length === 'number' ? ` • ${ocr.extracted_text_length} chars` : ''}
            </Typography>
          </Box>

          <Box
            sx={{
              mt: 2,
              p: 2,
              border: '1px solid rgba(0,0,0,0.08)',
              borderRadius: 2,
              background: 'rgba(0,0,0,0.02)',
              whiteSpace: 'pre-wrap',
              fontFamily: 'monospace',
              fontSize: 13,
              lineHeight: 1.6,
              maxHeight: 320,
              overflow: 'auto',
            }}
          >
            {ocr.extracted_text_preview || (ocrStatus === 'processing' ? 'OCR قيد المعالجة...' : 'لا يوجد نص مستخرج بعد.')}
          </Box>
        </Paper>
      ) : (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" sx={{ fontWeight: 900 }}>
            OCR
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            OCR يعمل تلقائيًا فقط لملفات PDF والصور. هذا الملف ({fileName || '-'}) غير مدعوم لـ OCR.
          </Typography>
        </Paper>
      )}

      {/* Signature Requests (employee-only action) */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" gap={2} flexWrap="wrap">
          <Typography variant="h6" sx={{ fontWeight: 900 }}>
            طلبات التوقيع
          </Typography>
          <Box display="flex" gap={1} flexWrap="wrap">
            {canRequestSignature && (
              <Button variant="outlined" onClick={() => setOpenRequestSign(true)}>
                طلب توقيع
              </Button>
            )}
            {canRequestSignature && approvedRequests.length > 0 && (
              <Button variant="contained" onClick={() => { setSelectedApprovedReqId(approvedRequests[0].id); setOpenUploadSigned(true); }}>
                رفع النسخة الموقّعة
              </Button>
            )}
          </Box>
        </Box>

        <Box sx={{ mt: 2, border: '1px solid rgba(0,0,0,0.08)', borderRadius: 2, overflow: 'hidden' }}>
          <Table size="small">
            <TableBody>
              {signatureRows.map((r: any) => (
                <TableRow key={r.id}>
                  <TableCell sx={{ fontWeight: 800 }}>{r.state}</TableCell>
                  <TableCell>{r.signer_name}</TableCell>
                  <TableCell color="text.secondary">{r.request_date ? format(new Date(r.request_date), 'yyyy-MM-dd HH:mm') : '-'}</TableCell>
                </TableRow>
              ))}
              {signatureRows.length === 0 && (
                <TableRow>
                  <TableCell colSpan={3} align="center">
                    <Typography color="text.secondary">{t('common.noData')}</Typography>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </Box>
      </Paper>

      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          {t('documents.versionHistory')}
        </Typography>

        <Table>
          <TableBody>
            {versions.map((version: any) => (
              <TableRow key={version.id}>
                <TableCell>v{version.version_number}</TableCell>
                <TableCell>{version.file_name}</TableCell>
                <TableCell>{version.uploaded_by || version.uploader?.name || '-'}</TableCell>
                <TableCell>
                  {version.upload_date ? format(new Date(version.upload_date), 'yyyy-MM-dd HH:mm') : '-'}
                </TableCell>
                <TableCell>
                  <Button
                    size="small"
                    startIcon={<DownloadIcon />}
                    onClick={() => handleDownload(version.id, version.file_name)}
                  >
                    {t('documents.download')}
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>

      {/* Create Signature Request Dialog */}
      <Dialog open={openRequestSign} onClose={() => setOpenRequestSign(false)} fullWidth maxWidth="sm">
        <DialogTitle>طلب توقيع</DialogTitle>
        <DialogContent>
          <TextField
            select
            fullWidth
            label="اختر المشرف/المدير"
            value={selectedSignerId}
            onChange={(e) => setSelectedSignerId(e.target.value ? Number(e.target.value) : '')}
            sx={{ mt: 1 }}
          >
            <MenuItem value="">اختر</MenuItem>
            {managers.map((m) => (
              <MenuItem key={m.id} value={m.id}>
                {m.name} ({m.login})
              </MenuItem>
            ))}
          </TextField>

          <TextField
            fullWidth
            multiline
            rows={3}
            label="ملاحظة (اختياري)"
            value={signMessage}
            onChange={(e) => setSignMessage(e.target.value)}
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenRequestSign(false)}>{t('common.cancel')}</Button>
          <Button variant="contained" onClick={onCreateSignatureRequest} disabled={!selectedSignerId}>
            إرسال
          </Button>
        </DialogActions>
      </Dialog>

      {/* Upload Signed Dialog */}
      <Dialog open={openUploadSigned} onClose={() => setOpenUploadSigned(false)} fullWidth maxWidth="sm">
        <DialogTitle>رفع النسخة الموقّعة</DialogTitle>
        <DialogContent>
          <TextField
            select
            fullWidth
            label="اختر الطلب المعتمد"
            value={selectedApprovedReqId || ''}
            onChange={(e) => setSelectedApprovedReqId(e.target.value ? Number(e.target.value) : null)}
            sx={{ mt: 1 }}
          >
            <MenuItem value="">اختر</MenuItem>
            {approvedRequests.map((r: any) => (
              <MenuItem key={r.id} value={r.id}>
                #{r.id} • {r.signer_name}
              </MenuItem>
            ))}
          </TextField>

          <TextField
            fullWidth
            label="Sign Token"
            value={signToken}
            onChange={(e) => setSignToken(e.target.value)}
            sx={{ mt: 2 }}
          />

          <Button variant="outlined" component="label" sx={{ mt: 2 }}>
            {signedFile ? signedFile.name : 'اختر الملف الموقّع'}
            <input type="file" hidden onChange={(e) => setSignedFile(e.target.files?.[0] || null)} />
          </Button>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenUploadSigned(false)}>{t('common.cancel')}</Button>
          <Button variant="contained" onClick={onUploadSigned} disabled={!selectedApprovedReqId || !signedFile || !signToken.trim()}>
            رفع
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

