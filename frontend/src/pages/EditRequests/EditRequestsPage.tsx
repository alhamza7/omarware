import { useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Button,
} from '@mui/material';
import { Check as ApproveIcon, Close as RejectIcon } from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { format } from 'date-fns';
import { editRequestsApi } from '../../api/editRequests.api';
import { useState } from 'react';
import toast from 'react-hot-toast';

export default function EditRequestsPage() {
  const { t } = useTranslation();
  const [requests, setRequests] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadRequests();
  }, []);

  const loadRequests = async () => {
    try {
      const response = await editRequestsApi.getEditRequests();
      setRequests(response.data);
    } catch (error) {
      console.error('Failed to load requests:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (requestId: number) => {
    try {
      await editRequestsApi.approveEditRequest(requestId);
      toast.success(t('editRequests.approveSuccess'));
      loadRequests();
    } catch (error) {
      toast.error(t('errors.generic'));
    }
  };

  const handleReject = async (requestId: number) => {
    try {
      await editRequestsApi.rejectEditRequest(requestId, '');
      toast.success(t('editRequests.rejectSuccess'));
      loadRequests();
    } catch (error) {
      toast.error(t('errors.generic'));
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending':
        return 'warning';
      case 'approved':
        return 'success';
      case 'rejected':
        return 'error';
      case 'completed':
        return 'info';
      default:
        return 'default';
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        {t('editRequests.title')}
      </Typography>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>{t('editRequests.requester')}</TableCell>
              <TableCell>{t('documents.name')}</TableCell>
              <TableCell>{t('editRequests.reason')}</TableCell>
              <TableCell>{t('editRequests.requestDate')}</TableCell>
              <TableCell>{t('editRequests.status')}</TableCell>
              <TableCell>{t('common.actions')}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={6} align="center">
                  {t('common.loading')}
                </TableCell>
              </TableRow>
            ) : requests.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} align="center">
                  {t('common.noData')}
                </TableCell>
              </TableRow>
            ) : (
              requests.map((request) => (
                <TableRow key={request.id} hover>
                  <TableCell>{request.requester.name}</TableCell>
                  <TableCell>{request.document.name}</TableCell>
                  <TableCell>{request.reason}</TableCell>
                  <TableCell>
                    {format(new Date(request.request_date), 'yyyy-MM-dd HH:mm')}
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={t(`editRequests.${request.status}`)}
                      color={getStatusColor(request.status)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    {request.can_approve && request.status === 'pending' && (
                      <Box display="flex" gap={1}>
                        <Button
                          size="small"
                          variant="contained"
                          color="success"
                          startIcon={<ApproveIcon />}
                          onClick={() => handleApprove(request.id)}
                        >
                          {t('editRequests.approve')}
                        </Button>
                        <Button
                          size="small"
                          variant="outlined"
                          color="error"
                          startIcon={<RejectIcon />}
                          onClick={() => handleReject(request.id)}
                        >
                          {t('editRequests.reject')}
                        </Button>
                      </Box>
                    )}
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


