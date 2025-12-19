import { useEffect, useState } from 'react';
import {
  Box,
  Typography,
  Button,
  Paper,
  TextField,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
} from '@mui/material';
import { Add as AddIcon, Search as SearchIcon, Visibility as ViewIcon } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useDocumentStore } from '../../stores/documentStore';
import { format } from 'date-fns';

export default function DocumentsPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { documents, isLoading, fetchDocuments } = useDocumentStore();
  const [q, setQ] = useState('');

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'success';
      case 'archived':
        return 'default';
      default:
        return 'info';
    }
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">{t('documents.title')}</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => navigate('/documents/upload')}
        >
          {t('documents.upload')}
        </Button>
      </Box>

      <Paper sx={{ p: 2, mb: 2, border: '1px solid rgba(0,0,0,0.08)' }}>
        <TextField
          fullWidth
          placeholder="ابحث عن أي شيء (عنوان، باركود، PO/BL/فاتورة، OCR...)"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && q.trim()) navigate(`/search?q=${encodeURIComponent(q.trim())}`);
          }}
          InputProps={{
            startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
          }}
        />
      </Paper>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>{t('documents.name')}</TableCell>
              <TableCell>{t('documents.barcode')}</TableCell>
              <TableCell>{t('documents.type')}</TableCell>
              <TableCell>{t('documents.department')}</TableCell>
              <TableCell>{t('documents.uploadDate')}</TableCell>
              <TableCell>{t('documents.status')}</TableCell>
              <TableCell>{t('common.actions')}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={7} align="center">
                  {t('common.loading')}
                </TableCell>
              </TableRow>
            ) : !documents || documents.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} align="center">
                  {t('documents.noDocuments')}
                </TableCell>
              </TableRow>
            ) : (
              documents.map((doc) => (
                <TableRow key={doc.id} hover>
                  <TableCell>{(doc as any).name || doc.title || '-'}</TableCell>
                  <TableCell>{doc.barcode || '-'}</TableCell>
                  <TableCell>{(doc as any).document_type?.name || (doc as any).document_type_name || '-'}</TableCell>
                  <TableCell>{(doc as any).department?.name || (doc as any).department_name || '-'}</TableCell>
                  <TableCell>
                    {doc.upload_date ? format(new Date(doc.upload_date), 'yyyy-MM-dd') : '-'}
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={doc.status || '-'}
                      color={getStatusColor(doc.status || '')}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <IconButton
                      size="small"
                      onClick={() => navigate(`/documents/${doc.id}`)}
                    >
                      <ViewIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}

