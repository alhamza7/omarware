import { useEffect, useState } from 'react';
import {
  Grid,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  Button,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Chip,
} from '@mui/material';
import {
  Description as DocumentsIcon,
  CloudUpload as UploadIcon,
  HourglassEmpty as PendingIcon,
  Notifications as NotificationsIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { useAuthStore } from '../stores/authStore';
import { adminApi } from '../api/admin.api';
import { documentsApi, Document } from '../api/documents.api';
import { useNavigate } from 'react-router-dom';

export default function Dashboard() {
  const { t } = useTranslation();
  const user = useAuthStore((state) => state.user);
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    total_documents: 0,
    my_documents: 0,
    pending_ocr: 0,
    pending_approvals: 0,
    unread_notifications: 0,
  });
  const [loading, setLoading] = useState(true);
  const [recentDocs, setRecentDocs] = useState<Document[]>([]);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const response = await adminApi.getDashboardStats();
      setStats({
        total_documents: response.stats?.total_documents ?? 0,
        my_documents: response.stats?.my_documents ?? 0,
        pending_ocr: 0,
        pending_approvals: response.stats?.pending_approvals ?? 0,
        unread_notifications: response.stats?.unread_notifications ?? 0,
      });
      const docsResp = await documentsApi.getDocuments({ page: 1, per_page: 6 });
      setRecentDocs(docsResp.data || []);
    } catch (error) {
      console.error('Failed to load stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const statCards = [
    {
      title: t('dashboard.stats.totalDocuments'),
      value: stats.total_documents,
      icon: <DocumentsIcon fontSize="large" />,
      gradient: '#111111',
    },
    {
      title: t('dashboard.stats.myDocuments'),
      value: stats.my_documents,
      icon: <UploadIcon fontSize="large" />,
      gradient: '#111111',
    },
    {
      title: t('dashboard.stats.pendingApprovals'),
      value: stats.pending_approvals,
      icon: <PendingIcon fontSize="large" />,
      gradient: '#111111',
    },
    {
      title: t('dashboard.stats.unreadNotifications'),
      value: stats.unread_notifications,
      icon: <NotificationsIcon fontSize="large" />,
      gradient: '#111111',
    },
  ];

  return (
    <Box>
      <Box
        sx={{
          display: 'flex',
          alignItems: { xs: 'flex-start', md: 'center' },
          justifyContent: 'space-between',
          gap: 2,
          flexWrap: 'wrap',
          mb: 4,
        }}
      >
        <Box>
          <Typography variant="h3" sx={{ fontWeight: 900, mb: 0.5, color: 'text.primary' }}>
            {t('dashboard.welcome', { name: user?.name || '' })}
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ fontWeight: 600 }}>
            مرحباً بك في نظام الأرشفة الإلكترونية
          </Typography>
        </Box>

        <Button 
          variant="contained" 
          onClick={() => navigate('/documents/upload')}
          size="large"
          sx={{
            px: 4,
            py: 1.5,
            fontSize: '1.1rem',
            boxShadow: '0 12px 40px rgba(0,0,0,0.12)',
          }}
        >
          {t('documents.uploadNew')}
        </Button>
      </Box>

      <Grid container spacing={3}>
        {statCards.map((stat, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <Card 
              elevation={0}
              sx={{ 
                borderRadius: 4,
                overflow: 'hidden',
                border: '1px solid rgba(0,0,0,0.06)',
                transition: 'all 0.3s',
                '&:hover': {
                  transform: 'translateY(-8px)',
                  border: '1px solid rgba(0,0,0,0.14)',
                }
              }}
            >
              <CardContent sx={{ p: 0 }}>
                <Box
                  sx={{
                    borderRadius: 0,
                    p: 3,
                    color: 'white',
                    background: stat.gradient,
                    position: 'relative',
                    overflow: 'hidden',
                  }}
                >
                  <Box sx={{ position: 'relative', zIndex: 1 }}>
                    <Box sx={{ opacity: 0.95, mb: 2 }}>{stat.icon}</Box>
                    <Typography variant="h3" sx={{ fontWeight: 900, mb: 0.5 }}>
                      {loading ? '...' : (stat.value || 0).toLocaleString()}
                    </Typography>
                    <Typography sx={{ opacity: 0.95, fontWeight: 600 }}>
                      {stat.title}
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Grid container spacing={3} sx={{ mt: 2 }}>
        <Grid item xs={12}>
          <Paper 
            elevation={0}
            sx={{ 
              p: 0, 
              overflow: 'hidden',
              borderRadius: 4,
              border: '1px solid rgba(0,0,0,0.06)',
            }}
          >
            <Box
              sx={{
                px: 3,
                py: 2.5,
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                gap: 2,
                background: '#111111',
                color: 'white',
              }}
            >
              <Typography variant="h5" sx={{ fontWeight: 900 }}>
                📋 {t('dashboard.recentDocuments')}
              </Typography>
              <Button 
                variant="contained" 
                color="inherit" 
                onClick={() => navigate('/documents')} 
                sx={{ 
                  color: '#111111',
                  background: '#ffffff',
                  fontWeight: 700,
                  px: 3,
                  '&:hover': {
                    background: 'rgba(255,255,255,0.95)',
                  }
                }}
              >
                عرض الكل →
              </Button>
            </Box>

            {recentDocs.length === 0 ? (
              <Box sx={{ p: 6, textAlign: 'center' }}>
                <Typography variant="h6" color="text.secondary" sx={{ mb: 1 }}>
                  لا توجد مستندات حتى الآن
                </Typography>
                <Button variant="outlined" onClick={() => navigate('/documents/upload')}>
                  رفع أول مستند
                </Button>
              </Box>
            ) : (
              <Table>
                <TableHead>
                  <TableRow sx={{ background: 'rgba(0,0,0,0.02)' }}>
                    <TableCell sx={{ fontWeight: 800, color: '#2d3748' }}>{t('documents.barcode')}</TableCell>
                    <TableCell sx={{ fontWeight: 800, color: '#2d3748' }}>{t('documents.name')}</TableCell>
                    <TableCell sx={{ fontWeight: 800, color: '#2d3748' }}>{t('documents.department')}</TableCell>
                    <TableCell sx={{ fontWeight: 800, color: '#2d3748' }}>{t('documents.type')}</TableCell>
                    <TableCell sx={{ fontWeight: 800, color: '#2d3748' }}>{t('documents.uploadDate')}</TableCell>
                    <TableCell sx={{ fontWeight: 800, color: '#2d3748' }}>{t('documents.status')}</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {recentDocs.map((d) => (
                    <TableRow
                      key={d.id}
                      hover
                      sx={{ 
                        cursor: 'pointer',
                        transition: 'all 0.2s',
                        '&:hover': {
                          background: 'rgba(0,0,0,0.03)',
                        }
                      }}
                      onClick={() => navigate(`/documents/${d.id}`)}
                    >
                      <TableCell sx={{ fontWeight: 800, color: '#111111' }}>{d.barcode || '-'}</TableCell>
                      <TableCell sx={{ fontWeight: 600 }}>{d.title || '-'}</TableCell>
                      <TableCell>{d.department_name || '-'}</TableCell>
                      <TableCell>{d.document_type_name || '-'}</TableCell>
                      <TableCell sx={{ color: 'text.secondary' }}>
                        {d.upload_date ? new Date(d.upload_date).toLocaleDateString('ar-SA') : '-'}
                      </TableCell>
                      <TableCell>
                        <Chip
                          size="small"
                          label={d.status === 'active' ? 'نشط' : (d.status || 'غير معروف')}
                          sx={{
                            background: '#111111',
                            color: 'white',
                            fontWeight: 700,
                            borderRadius: 2,
                          }}
                        />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}


