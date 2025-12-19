import { Paper, BottomNavigation, BottomNavigationAction } from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Description as DocumentsIcon,
  Folder as FolderIcon,
  Search as SearchIcon,
  Edit as EditIcon,
  AssignmentTurnedIn as SignatureIcon,
  Notifications as NotificationsIcon,
  AdminPanelSettings as AdminIcon,
} from '@mui/icons-material';
import { useLocation, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuthStore } from '../../stores/authStore';

export default function BottomNav() {
  const { t } = useTranslation();
  const location = useLocation();
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const isAdmin = !!user?.is_admin;

  const items = [
    { path: '/dashboard', label: t('nav.dashboard'), icon: <DashboardIcon /> },
    { path: '/documents', label: t('nav.documents'), icon: <DocumentsIcon /> },
    { path: '/folders', label: t('nav.folders'), icon: <FolderIcon /> },
    { path: '/search', label: t('nav.search'), icon: <SearchIcon /> },
    { path: '/edit-requests', label: t('nav.editRequests'), icon: <EditIcon /> },
    { path: '/signatures', label: t('nav.signatures'), icon: <SignatureIcon /> },
    { path: '/notifications', label: t('nav.notifications'), icon: <NotificationsIcon /> },
    ...(isAdmin ? [{ path: '/admin/permissions', label: t('nav.permissions'), icon: <AdminIcon /> }] : []),
  ];

  const current =
    items.find((i) => location.pathname === i.path || location.pathname.startsWith(i.path + '/'))?.path ||
    '/dashboard';

  return (
    <Paper
      elevation={0}
      sx={{
        position: 'fixed',
        left: 16,
        right: 16,
        bottom: 14,
        zIndex: (t) => t.zIndex.appBar + 1,
        borderRadius: 999,
        border: '1px solid rgba(0,0,0,0.10)',
        backdropFilter: 'blur(12px)',
        background: 'rgba(255,255,255,0.94)',
        overflow: 'hidden',
        boxShadow: '0 18px 55px rgba(0,0,0,0.12)',
      }}
    >
      <BottomNavigation
        value={current}
        onChange={(_, value) => navigate(value)}
        showLabels={false}
        sx={{
          height: 64,
          px: 1,
          '& .MuiBottomNavigationAction-root': {
            minWidth: 0,
            px: 1.3,
            color: 'text.secondary',
            borderRadius: 999,
          },
          '& .Mui-selected': {
            color: 'text.primary',
          },
          '& .MuiBottomNavigationAction-label': {
            fontSize: 11,
            fontWeight: 700,
          },
          '& .MuiBottomNavigationAction-root.Mui-selected': {
            background: 'rgba(0,0,0,0.06)',
          },
        }}
      >
        {items.map((i) => (
          <BottomNavigationAction key={i.path} value={i.path} icon={i.icon} label={i.label} />
        ))}
      </BottomNavigation>
    </Paper>
  );
}


