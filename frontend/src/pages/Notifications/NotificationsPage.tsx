import { useEffect, useMemo, useState } from 'react';
import {
  Box,
  Button,
  Chip,
  Divider,
  List,
  ListItem,
  ListItemText,
  Paper,
  Typography,
} from '@mui/material';
import { useTranslation } from 'react-i18next';
import { useNotificationStore } from '../../stores/notificationStore';

export default function NotificationsPage() {
  const { t } = useTranslation();
  const {
    notifications,
    unreadCount,
    isLoading,
    error,
    fetchNotifications,
    markAllAsRead,
  } = useNotificationStore();

  const [showUnreadOnly, setShowUnreadOnly] = useState(false);

  useEffect(() => {
    fetchNotifications(showUnreadOnly);
  }, [fetchNotifications, showUnreadOnly]);

  const headerChips = useMemo(
    () => (
      <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', alignItems: 'center' }}>
        <Chip
          label={t('notifications.all')}
          color={!showUnreadOnly ? 'primary' : 'default'}
          variant={!showUnreadOnly ? 'filled' : 'outlined'}
          onClick={() => setShowUnreadOnly(false)}
        />
        <Chip
          label={`${t('notifications.unread')} (${unreadCount})`}
          color={showUnreadOnly ? 'primary' : 'default'}
          variant={showUnreadOnly ? 'filled' : 'outlined'}
          onClick={() => setShowUnreadOnly(true)}
        />
      </Box>
    ),
    [showUnreadOnly, t, unreadCount]
  );

  return (
    <Box>
      <Box
        sx={{
          display: 'flex',
          alignItems: { xs: 'flex-start', md: 'center' },
          justifyContent: 'space-between',
          gap: 2,
          flexWrap: 'wrap',
          mb: 2,
        }}
      >
        <Box>
          <Typography variant="h4">{t('notifications.title')}</Typography>
          <Typography color="text.secondary" sx={{ mt: 0.5 }}>
            {t('common.showing')} {notifications.length} {t('common.entries')}
          </Typography>
        </Box>

        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', alignItems: 'center' }}>
          {headerChips}
          <Button
            variant="contained"
            onClick={() => markAllAsRead()}
            disabled={isLoading || notifications.length === 0}
          >
            {t('notifications.markAllRead')}
          </Button>
        </Box>
      </Box>

      <Paper sx={{ p: 0, overflow: 'hidden' }}>
        {error ? (
          <Box sx={{ p: 3 }}>
            <Typography color="error">{error}</Typography>
          </Box>
        ) : notifications.length === 0 ? (
          <Box sx={{ p: 3 }}>
            <Typography color="text.secondary">{t('notifications.noNotifications')}</Typography>
          </Box>
        ) : (
          <List disablePadding>
            {notifications.map((n, idx) => (
              <Box key={n.id}>
                <ListItem
                  sx={{
                    px: 3,
                    py: 2,
                    backgroundColor: n.is_read ? 'transparent' : 'rgba(102,126,234,0.08)',
                  }}
                >
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', flexWrap: 'wrap' }}>
                        <Typography sx={{ fontWeight: 800 }}>{n.title}</Typography>
                        {!n.is_read && <Chip size="small" color="primary" label={t('notifications.unread')} />}
                      </Box>
                    }
                    secondary={
                      <Box sx={{ mt: 0.75 }}>
                        <Typography color="text.secondary">{n.message}</Typography>
                        {n.created_date && (
                          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                            {new Date(n.created_date).toLocaleString()}
                          </Typography>
                        )}
                      </Box>
                    }
                  />
                </ListItem>
                {idx !== notifications.length - 1 && <Divider />}
              </Box>
            ))}
          </List>
        )}
      </Paper>
    </Box>
  );
}


