import { useEffect, useMemo, useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  TextField,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  MenuItem,
  Chip,
  Button,
  CircularProgress,
  Alert,
} from '@mui/material';
import { useTranslation } from 'react-i18next';
import toast from 'react-hot-toast';
import { adminApi, AdminUserRow } from '../../api/admin.api';
import { useAuthStore } from '../../stores/authStore';

export default function PermissionsPage() {
  const { t } = useTranslation();
  const user = useAuthStore((s) => s.user);

  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [departments, setDepartments] = useState<Array<{ id: number; name: string; code: string }>>([]);
  const [rows, setRows] = useState<AdminUserRow[]>([]);

  const isAdmin = !!user?.is_admin;

  const deptById = useMemo(() => {
    const map = new Map<number, { id: number; name: string; code: string }>();
    departments.forEach((d) => map.set(d.id, d));
    return map;
  }, [departments]);

  const load = async () => {
    if (!isAdmin) return;
    setLoading(true);
    setError(null);
    try {
      const [deptsResp, usersResp] = await Promise.all([adminApi.getDepartments(), adminApi.getUsers(search || undefined)]);
      if (!deptsResp.success) throw new Error(deptsResp as any);
      if (!usersResp.success) throw new Error(usersResp.error || 'Failed to load users');
      setDepartments(deptsResp.data || []);
      setRows(usersResp.data || []);
    } catch (e: any) {
      setError(e?.message || 'Failed to load');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const onSave = async (u: AdminUserRow) => {
    try {
      const resp = await adminApi.updateUser(u.id, {
        role: u.role,
        department_ids: u.department_ids,
        manager_department_ids: u.manager_department_ids,
      });
      if (!resp.success) throw new Error(resp.error || 'Update failed');
      toast.success('تم حفظ الصلاحيات');
    } catch (e: any) {
      toast.error(e?.message || 'فشل حفظ الصلاحيات');
    }
  };

  if (!isAdmin) {
    return (
      <Alert severity="error">
        {t('errors.accessDenied') || 'Access denied'}
      </Alert>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 900 }}>
            إدارة الصلاحيات
          </Typography>
          <Typography color="text.secondary" sx={{ mt: 0.5 }}>
            تعديل أدوار المستخدمين + أقسام الوصول
          </Typography>
        </Box>

        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
          <TextField
            size="small"
            placeholder="بحث بالاسم أو اسم المستخدم"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <Button variant="contained" onClick={load} disabled={loading}>
            {loading ? '...' : 'تحديث'}
          </Button>
        </Box>
      </Box>

      <Paper sx={{ mt: 2, p: 2, border: '1px solid rgba(0,0,0,0.06)' }} elevation={0}>
        {error && <Alert severity="error">{error}</Alert>}
        {loading ? (
          <Box display="flex" justifyContent="center" alignItems="center" minHeight={240}>
            <CircularProgress />
          </Box>
        ) : (
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>المستخدم</TableCell>
                <TableCell>الدور</TableCell>
                <TableCell>أقسام الوصول</TableCell>
                <TableCell>أقسام الإدارة</TableCell>
                <TableCell>حفظ</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {rows.map((u, idx) => (
                <TableRow key={u.id} hover>
                  <TableCell>
                    <Typography sx={{ fontWeight: 800 }}>{u.name}</Typography>
                    <Typography variant="body2" color="text.secondary">
                      {u.login} {u.email ? `• ${u.email}` : ''}
                    </Typography>
                  </TableCell>

                  <TableCell>
                    <TextField
                      select
                      size="small"
                      value={u.role}
                      onChange={(e) => {
                        const role = e.target.value as any;
                        setRows((prev) => prev.map((x, i) => (i === idx ? { ...x, role } : x)));
                      }}
                    >
                      <MenuItem value="employee">Employee</MenuItem>
                      <MenuItem value="manager">Supervisor/Manager</MenuItem>
                      <MenuItem value="admin">Admin</MenuItem>
                    </TextField>
                  </TableCell>

                  <TableCell>
                    <TextField
                      select
                      size="small"
                      value={u.department_ids.map(String)}
                      SelectProps={{ multiple: true, renderValue: (selected) => (
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                          {(selected as string[]).map((v) => {
                            const id = Number(v);
                            const d = deptById.get(id);
                            return <Chip key={v} size="small" label={d ? `${d.name} (${d.code})` : v} />;
                          })}
                        </Box>
                      )}}
                      onChange={(e) => {
                        const raw = e.target.value as unknown as string[];
                        const ids = raw.map((v) => Number(v));
                        setRows((prev) => prev.map((x, i) => (i === idx ? { ...x, department_ids: ids } : x)));
                      }}
                      sx={{ minWidth: 240 }}
                    >
                      {departments.map((d) => (
                        <MenuItem key={d.id} value={String(d.id)}>
                          {d.name} ({d.code})
                        </MenuItem>
                      ))}
                    </TextField>
                  </TableCell>

                  <TableCell>
                    <TextField
                      select
                      size="small"
                      value={u.manager_department_ids.map(String)}
                      SelectProps={{ multiple: true, renderValue: (selected) => (
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                          {(selected as string[]).map((v) => {
                            const id = Number(v);
                            const d = deptById.get(id);
                            return <Chip key={v} size="small" label={d ? `${d.name} (${d.code})` : v} />;
                          })}
                        </Box>
                      )}}
                      onChange={(e) => {
                        const raw = e.target.value as unknown as string[];
                        const ids = raw.map((v) => Number(v));
                        setRows((prev) =>
                          prev.map((x, i) => (i === idx ? { ...x, manager_department_ids: ids } : x))
                        );
                      }}
                      sx={{ minWidth: 240 }}
                    >
                      {departments.map((d) => (
                        <MenuItem key={d.id} value={String(d.id)}>
                          {d.name} ({d.code})
                        </MenuItem>
                      ))}
                    </TextField>
                  </TableCell>

                  <TableCell>
                    <Button variant="outlined" size="small" onClick={() => onSave(u)}>
                      حفظ
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Paper>
    </Box>
  );
}


