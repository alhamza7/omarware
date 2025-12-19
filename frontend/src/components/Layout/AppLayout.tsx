import { Outlet } from 'react-router-dom';
import { Box, AppBar, Toolbar, Typography, IconButton, Badge } from '@mui/material';
import { Notifications as NotificationsIcon, Logout as LogoutIcon } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuthStore } from '../../stores/authStore';
import { useNotificationStore } from '../../stores/notificationStore';
import BottomNav from './BottomNav';
import BackgroundFX from './BackgroundFX';

export default function AppLayout() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const logout = useAuthStore((state) => state.logout);
  const unreadCount = useNotificationStore((state) => state.unreadCount);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <Box
      sx={{
        display: 'flex',
        minHeight: '100vh',
        background: '#ffffff',
        position: 'relative',
      }}
    >
      <BackgroundFX />

      {/* App Bar */}
      <AppBar
        position="fixed"
        elevation={0}
        sx={{
          zIndex: (theme) => theme.zIndex.drawer + 1,
          background: 'rgba(255,255,255,0.85)',
          color: 'text.primary',
          backdropFilter: 'blur(10px)',
          borderBottom: '1px solid rgba(0,0,0,0.06)',
        }}
      >
        <Toolbar>
          <Typography
            variant="h6"
            noWrap
            component="div"
            sx={{
              flexGrow: 1,
              fontWeight: 900,
              color: 'text.primary',
              letterSpacing: 0.3,
            }}
          >
            {t('app.name')}
          </Typography>

          <IconButton color="inherit" onClick={() => navigate('/notifications')}>
            <Badge badgeContent={unreadCount} color="error">
              <NotificationsIcon />
            </Badge>
          </IconButton>

          <IconButton color="inherit" onClick={handleLogout}>
            <LogoutIcon />
          </IconButton>
        </Toolbar>
      </AppBar>

      {/* Main Content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: { xs: 2, md: 3 },
          mt: 9,
          position: 'relative',
          zIndex: 1,
        }}
      >
        <Box
          sx={{
            maxWidth: 1400,
            mx: 'auto',
            background: 'rgba(255,255,255,0.90)',
            borderRadius: 4,
            boxShadow: '0 12px 40px rgba(0,0,0,0.08)',
            p: { xs: 2, md: 3 },
            pb: { xs: 12, md: 12 }, // space for bottom nav
            border: '1px solid rgba(0,0,0,0.06)',
          }}
        >
          <Outlet />
        </Box>
      </Box>

      {/* Bottom navigation (all screens) */}
      <BottomNav />
    </Box>
  );
}


