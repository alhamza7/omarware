import { useEffect, useMemo, useState } from 'react';
import {
  Box,
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Grid,
  Paper,
  TextField,
  Typography,
} from '@mui/material';
import { styled } from '@mui/material/styles';
import LocalShippingRoundedIcon from '@mui/icons-material/LocalShippingRounded';
import WorkRoundedIcon from '@mui/icons-material/WorkRounded';
import ApartmentRoundedIcon from '@mui/icons-material/ApartmentRounded';
import DescriptionRoundedIcon from '@mui/icons-material/DescriptionRounded';
import FolderOpenRoundedIcon from '@mui/icons-material/FolderOpenRounded';
import { useTranslation } from 'react-i18next';
import { adminApi } from '../../api/admin.api';
import apiClient from '../../api/client';
import { useNavigate } from 'react-router-dom';

type Folder = {
  id: number;
  name: string;
  code: string;
  folder_type: string;
  department_id: number;
  department_name: string;
  description?: string | null;
  document_count: number;
  owner_name?: string;
  create_date?: string | null;
  state: string;
};

const FolderCard = styled(Paper)(() => ({
  position: 'relative',
  overflow: 'hidden',
  borderRadius: 20,
  padding: 30,
  cursor: 'pointer',
  color: '#111111',
  background: '#ffffff',
  border: '1px solid rgba(0,0,0,0.10)',
  boxShadow: '0 10px 35px rgba(0,0,0,0.08)',
  transition: 'transform 0.3s, box-shadow 0.3s',
  '&:hover': {
    transform: 'translateY(-10px)',
    boxShadow: '0 18px 55px rgba(0,0,0,0.12)',
  },
}));

export default function FoldersPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [folders, setFolders] = useState<Folder[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [q, setQ] = useState('');

  const [createOpen, setCreateOpen] = useState(false);
  const [name, setName] = useState('');
  const [code, setCode] = useState('');
  const [departmentId, setDepartmentId] = useState<number | ''>('');

  const [departments, setDepartments] = useState<Array<{ id: number; name: string; code: string }>>([]);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [foldersResp, deptsResp] = await Promise.all([
        apiClient.post('/api/folders', { jsonrpc: '2.0', method: 'call', params: { state: 'active' } }),
        adminApi.getDepartments(),
      ]);
      setFolders((foldersResp.data.result?.data || foldersResp.data.data || []) as Folder[]);
      setDepartments(deptsResp.data);
    } catch (e: any) {
      setError(e?.message || 'Failed to load folders');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const canCreate = useMemo(() => name.trim() && code.trim() && departmentId !== '', [name, code, departmentId]);

  const getFolderVisual = (folderType: string) => {
    const ft = (folderType || '').toLowerCase();
    if (ft === 'official') {
      return {
        label: 'مستند رسمي',
        icon: <DescriptionRoundedIcon sx={{ fontSize: 44, color: '#111111' }} />,
      };
    }
    if (ft === 'invoice') {
      return {
        label: 'فاتورة',
        icon: <DescriptionRoundedIcon sx={{ fontSize: 44, color: '#111111' }} />,
      };
    }
    if (ft === 'shipment') {
      return {
        label: 'شحنة',
        icon: <LocalShippingRoundedIcon sx={{ fontSize: 44, color: '#111111' }} />,
      };
    }
    if (ft === 'project') {
      return {
        label: 'مشروع',
        icon: <WorkRoundedIcon sx={{ fontSize: 44, color: '#111111' }} />,
      };
    }
    if (ft === 'client') {
      return {
        label: 'عميل',
        icon: <ApartmentRoundedIcon sx={{ fontSize: 44, color: '#111111' }} />,
      };
    }
    if (ft === 'contract') {
      return {
        label: 'عقد',
        icon: <DescriptionRoundedIcon sx={{ fontSize: 44, color: '#111111' }} />,
      };
    }
    return {
      label: 'إضبارة',
      icon: <FolderOpenRoundedIcon sx={{ fontSize: 44, color: '#111111' }} />,
    };
  };

  const formatDate = (iso?: string | null) => {
    if (!iso) return '-';
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return '-';
    return new Intl.DateTimeFormat('ar-SA', { year: 'numeric', month: 'short', day: '2-digit' }).format(d);
  };

  const createFolder = async () => {
    if (!canCreate) return;
    setLoading(true);
    setError(null);
    try {
      await apiClient.post('/api/folders/create', {
        jsonrpc: '2.0',
        method: 'call',
        params: {
          name,
          code,
          department_id: departmentId,
          folder_type: 'other',
          description: null,
          document_ids: [],
        },
      });
      setCreateOpen(false);
      setName('');
      setCode('');
      setDepartmentId('');
      await load();
    } catch (e: any) {
      setError(e?.response?.data?.error || e?.message || 'Failed to create folder');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Paper elevation={0} sx={{ p: { xs: 2.5, md: 3 }, borderRadius: 4, border: '1px solid rgba(0,0,0,0.08)', background: '#fff' }}>
        <Box>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 2, flexWrap: 'wrap' }}>
            <Box>
              <Typography variant="h4" sx={{ fontWeight: 900 }}>
                {t('nav.folders')}
              </Typography>
              <Typography color="text.secondary" sx={{ mt: 0.5 }}>
                {loading ? t('common.loading') : `${folders.length} ${t('common.entries')}`}
              </Typography>
            </Box>

            <Button variant="contained" onClick={() => setCreateOpen(true)} sx={{ borderRadius: 999, px: 3, py: 1.2 }}>
              {t('common.add')}
            </Button>
          </Box>
        </Box>
      </Paper>

      {error && (
        <Paper sx={{ p: 2, mt: 2, border: '1px solid rgba(211,47,47,0.2)', background: 'rgba(211,47,47,0.04)' }}>
          <Typography color="error">{error}</Typography>
        </Paper>
      )}

      <Paper sx={{ p: 2, mt: 2, border: '1px solid rgba(0,0,0,0.08)' }}>
        <TextField
          fullWidth
          placeholder="ابحث عن أي شيء (اسم إضبارة، كود، مستندات داخلها...)"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && q.trim()) navigate(`/search?q=${encodeURIComponent(q.trim())}`);
          }}
        />
      </Paper>

      <Grid container spacing={2} sx={{ mt: 1 }}>
        {folders.map((f) => (
          <Grid item xs={12} md={6} lg={4} key={f.id}>
            {(() => {
              const v = getFolderVisual(f.folder_type);
              return (
                <FolderCard onClick={() => navigate(`/folders/${f.id}`)} elevation={0}>
                  <Box sx={{ position: 'relative', zIndex: 1 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                      <Box>{v.icon}</Box>
                      <Box
                        sx={{
                          background: '#111111',
                          px: 2,
                          py: 0.6,
                          borderRadius: 999,
                          fontSize: 13,
                          fontWeight: 800,
                          color: 'white',
                        }}
                      >
                        {v.label}
                      </Box>
                    </Box>

                    <Typography sx={{ fontSize: 24, fontWeight: 800, mb: 1 }}>{f.name}</Typography>
                    <Typography
                      sx={{
                        fontSize: 14,
                        opacity: 0.9,
                        fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace',
                        mb: 1.5,
                      }}
                    >
                      {f.code}
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 1.2 }}>
                      <Chip
                        size="small"
                        label={f.department_name}
                        sx={{
                          bgcolor: 'rgba(0,0,0,0.06)',
                          color: '#111111',
                          fontWeight: 800,
                          border: '1px solid rgba(0,0,0,0.08)',
                        }}
                      />
                      <Chip
                        size="small"
                        label={formatDate(f.create_date)}
                        sx={{
                          bgcolor: 'rgba(0,0,0,0.04)',
                          color: '#111111',
                          fontWeight: 800,
                          border: '1px solid rgba(0,0,0,0.06)',
                        }}
                      />
                    </Box>

                    {f.description ? (
                      <Typography sx={{ fontSize: 14, opacity: 0.92, mb: 2, lineHeight: 1.6 }}>
                        {f.description}
                      </Typography>
                    ) : (
                      <Typography sx={{ fontSize: 14, opacity: 0.6, mb: 2, lineHeight: 1.6 }}>
                        لا يوجد وصف
                      </Typography>
                    )}

                    <Box sx={{ display: 'flex', gap: 2, pt: 2, borderTop: '1px solid rgba(0,0,0,0.08)', flexWrap: 'wrap' }}>
                      <Typography sx={{ fontSize: 14, display: 'flex', gap: 0.8, alignItems: 'center' }}>
                        📄 {f.document_count}
                      </Typography>
                      <Typography sx={{ fontSize: 14, display: 'flex', gap: 0.8, alignItems: 'center' }}>
                        👤 {f.owner_name || '-'}
                      </Typography>
                      <Typography sx={{ fontSize: 14, display: 'flex', gap: 0.8, alignItems: 'center' }}>
                        ✅ {f.state || '-'}
                      </Typography>
                    </Box>
                  </Box>
                </FolderCard>
              );
            })()}
          </Grid>
        ))}
      </Grid>

      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle sx={{ fontWeight: 900 }}>{t('nav.folders')}</DialogTitle>
        <DialogContent sx={{ pt: 1 }}>
          <TextField
            fullWidth
            label="Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            sx={{ mt: 1.5 }}
          />
          <TextField
            fullWidth
            label="Code"
            value={code}
            onChange={(e) => setCode(e.target.value)}
            sx={{ mt: 1.5 }}
          />
          <TextField
            select
            fullWidth
            label="Department"
            SelectProps={{ native: true }}
            value={departmentId}
            onChange={(e) => setDepartmentId(e.target.value ? Number(e.target.value) : '')}
            sx={{ mt: 1.5 }}
          >
            <option value="" />
            {departments.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
          </TextField>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateOpen(false)}>{t('common.cancel')}</Button>
          <Button variant="contained" onClick={createFolder} disabled={!canCreate || loading}>
            {t('common.save')}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}


