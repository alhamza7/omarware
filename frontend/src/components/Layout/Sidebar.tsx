import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Description as DocumentsIcon,
  Search as SearchIcon,
  Edit as EditIcon,
  Folder as FolderIcon,
  Notifications as NotificationsIcon,
  AdminPanelSettings as AdminIcon,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuthStore } from '../../stores/authStore';

interface SidebarProps {
  open: boolean;
}

export default function Sidebar({ open }: SidebarProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const { t } = useTranslation();
  const user = useAuthStore((s) => s.user);
  const isAdmin = !!user?.is_admin;

  const menuItems = [
    { path: '/dashboard', label: t('nav.dashboard'), icon: <DashboardIcon /> },
    { path: '/documents', label: t('nav.documents'), icon: <DocumentsIcon /> },
    { path: '/folders', label: t('nav.folders'), icon: <FolderIcon /> },
    { path: '/search', label: t('nav.search'), icon: <SearchIcon /> },
    { path: '/edit-requests', label: t('nav.editRequests'), icon: <EditIcon /> },
    { path: '/notifications', label: t('nav.notifications'), icon: <NotificationsIcon /> },
    ...(isAdmin ? [{ path: '/admin/permissions', label: t('nav.permissions'), icon: <AdminIcon /> }] : []),
  ];

  return (
    <Drawer
      variant="persistent"
      open={open}
      sx={{
        width: 240,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: 240,
          boxSizing: 'border-box',
          background: 'rgba(255,255,255,0.92)',
          backdropFilter: 'blur(10px)',
          borderRight: '1px solid rgba(0,0,0,0.06)',
        },
      }}
    >
      <Toolbar />
      <List>
        {menuItems.map((item) => (
          <ListItem key={item.path} disablePadding>
            <ListItemButton
              selected={location.pathname === item.path || location.pathname.startsWith(item.path + '/')}
              onClick={() => navigate(item.path)}
              sx={{
                borderRadius: 2,
                mx: 1,
                my: 0.5,
                '&.Mui-selected': {
                  backgroundColor: 'rgba(0,0,0,0.06)',
                  '&:hover': { backgroundColor: 'rgba(0,0,0,0.08)' },
                },
              }}
            >
              <ListItemIcon sx={{ minWidth: 40, color: 'text.secondary' }}>{item.icon}</ListItemIcon>
              <ListItemText primary={item.label} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </Drawer>
  );
}


