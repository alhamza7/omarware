import { useEffect, useMemo, useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
} from '@mui/material';
import { useTranslation } from 'react-i18next';
import { useSignatureStore } from '../../stores/signatureStore';
import toast from 'react-hot-toast';

export default function SignatureRequestsPage() {
  const { t } = useTranslation();
  const { requests, fetchRequests, approve, reject, isLoading, error } = useSignatureStore();
  const [tab, setTab] = useState<'all' | 'pending'>('pending');
  const [rejectOpen, setRejectOpen] = useState(false);
  const [rejectReason, setRejectReason] = useState('');
  const [selectedId, setSelectedId] = useState<number | null>(null);

  useEffect(() => {
    fetchRequests(tab === 'pending' ? { state: 'pending' } : {});
  }, [tab, fetchRequests]);

  const rows = useMemo(() => requests || [], [requests]);

  const onApprove = async (id: number) => {
    try {
      const resp = await approve(id);
      toast.success(`تمت الموافقة. token: ${resp.sign_token}`);
      fetchRequests(tab === 'pending' ? { state: 'pending' } : {});
    } catch (e: any) {
      toast.error(e?.message || 'فشل الموافقة');
    }
  };

  const openReject = (id: number) => {
    setSelectedId(id);
    setRejectReason('');
    setRejectOpen(true);
  };

  const onReject = async () => {
    if (!selectedId) return;
    try {
      await reject(selectedId, rejectReason);
      toast.success('تم الرفض');
      setRejectOpen(false);
      fetchRequests(tab === 'pending' ? { state: 'pending' } : {});
    } catch (e: any) {
      toast.error(e?.message || 'فشل الرفض');
    }
  };

  return (
    <Box>
      <Typography variant="h4" sx={{ fontWeight: 900, mb: 2 }}>
        طلبات التوقيع
      </Typography>

      <Paper sx={{ p: 2, mb: 2, border: '1px solid rgba(0,0,0,0.08)' }}>
        <Tabs value={tab} onChange={(_, v) => setTab(v)} textColor="primary" indicatorColor="primary">
          <Tab value="pending" label="قيد الانتظار" />
          <Tab value="all" label="الكل" />
        </Tabs>
      </Paper>

      {error ? (
        <Paper sx={{ p: 2, border: '1px solid rgba(220,38,38,0.25)' }}>
          <Typography color="error">{error}</Typography>
        </Paper>
      ) : (
        <Paper sx={{ overflow: 'hidden', border: '1px solid rgba(0,0,0,0.08)' }}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>المستند</TableCell>
                <TableCell>الطالب</TableCell>
                <TableCell>الموقّع</TableCell>
                <TableCell>الحالة</TableCell>
                <TableCell>{t('common.actions')}</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {rows.map((r) => (
                <TableRow key={r.id} hover>
                  <TableCell>{r.document_title}</TableCell>
                  <TableCell>{r.requester_name}</TableCell>
                  <TableCell>{r.signer_name}</TableCell>
                  <TableCell>{r.state}</TableCell>
                  <TableCell>
                    <Button size="small" onClick={() => onApprove(r.id)} disabled={isLoading || r.state !== 'pending'}>
                      موافقة
                    </Button>
                    <Button size="small" color="error" onClick={() => openReject(r.id)} disabled={isLoading || r.state !== 'pending'}>
                      رفض
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
              {rows.length === 0 && (
                <TableRow>
                  <TableCell colSpan={5} align="center">
                    <Typography color="text.secondary">{t('common.noData')}</Typography>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </Paper>
      )}

      <Dialog open={rejectOpen} onClose={() => setRejectOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>رفض طلب توقيع</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            multiline
            rows={3}
            label="سبب الرفض (اختياري)"
            value={rejectReason}
            onChange={(e) => setRejectReason(e.target.value)}
            sx={{ mt: 1 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRejectOpen(false)}>{t('common.cancel')}</Button>
          <Button onClick={onReject} color="error" variant="contained">
            رفض
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}












