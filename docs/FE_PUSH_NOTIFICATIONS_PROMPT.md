# FE Prompt — Web Push Notifications (Background / Tab-Closed Delivery)

## Goal
Receive chat and email notifications **even when the browser tab is closed or the
app is in the background**.  Uses the standard **Web Push API** + a **Service Worker**.

---

## Step 1 — Generate VAPID Keys (One-Time, Admin)

On the Odoo server, run once in a Python shell (or a custom server action):

```python
from py_vapid import Vapid
v = Vapid()
v.generate_keys()
print("Private:", v.private_key.private_bytes(
    encoding=__import__('cryptography.hazmat.primitives.serialization', fromlist=['Encoding']).Encoding.PEM,
    format=__import__('cryptography.hazmat.primitives.serialization', fromlist=['PrivateFormat']).PrivateFormat.TraditionalOpenSSL,
    encryption_algorithm=__import__('cryptography.hazmat.primitives.serialization', fromlist=['NoEncryption']).NoEncryption()
).decode())
print("Public:", v.public_key.public_bytes(
    encoding=__import__('cryptography.hazmat.primitives.serialization', fromlist=['Encoding']).Encoding.PEM,
    format=__import__('cryptography.hazmat.primitives.serialization', fromlist=['PublicFormat']).PublicFormat.SubjectPublicKeyInfo
).decode())
```

Or faster — install `pywebpush` and use:
```bash
pip install pywebpush
python -c "from pywebpush import Vapid; v = Vapid(); v.generate_keys(); print(v.private_key); print(v.public_key)"
```

Save the keys in `ir.config_parameter`:
- `lugal.push.vapid.private_key` → PEM private key string
- `lugal.push.vapid.public_key`  → Base64url-encoded public key (the **applicationServerKey**)
- `lugal.push.vapid.email`        → `mailto:admin@yourdomain.com`

---

## Step 2 — Create the Service Worker file

Create `public/sw.js` at the root of your Vite project (it must be served at `/sw.js`):

```javascript
// public/sw.js
// Service Worker for Web Push Notifications

self.addEventListener('push', (event) => {
  let data = {};
  try {
    data = event.data ? event.data.json() : {};
  } catch (e) {
    data = { title: 'New Notification', body: event.data ? event.data.text() : '' };
  }

  const title = data.title || 'Lugal';
  const options = {
    body: data.body || '',
    icon: '/favicon.ico',
    badge: '/favicon.ico',
    tag: data.data?.type === 'chat'
      ? `chat-${data.data?.conversation_id}`
      : `email-${data.data?.message_id}`,
    renotify: true,
    data: data.data || {},
  };

  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const notifData = event.notification.data || {};
  const url = notifData.url || '/';

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((windowClients) => {
      // If the app is already open in a tab, focus it and navigate
      for (const client of windowClients) {
        if (client.url.includes(self.location.origin) && 'focus' in client) {
          client.focus();
          client.postMessage({ type: 'NAVIGATE', url });
          return;
        }
      }
      // Otherwise open a new tab
      if (clients.openWindow) {
        return clients.openWindow(url);
      }
    })
  );
});
```

---

## Step 3 — Register the Service Worker on App Start

In your main app entry (e.g. `src/app/App.tsx` or `src/main.tsx`), add:

```typescript
// src/shared/push/usePushNotifications.ts
import { useEffect } from 'react';
import { apiClient } from '@/shared/api/apiClient'; // your JSON-RPC client

function urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

export async function registerPushNotifications(accessToken: string): Promise<void> {
  if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
    console.log('[Push] Web Push not supported in this browser');
    return;
  }

  try {
    // 1. Register the service worker
    const registration = await navigator.serviceWorker.register('/sw.js', { scope: '/' });
    console.log('[Push] Service Worker registered:', registration.scope);

    // 2. Fetch VAPID public key from backend
    const vapidRes = await fetch('/api/crm/push/vapid-public-key', {
      headers: { Authorization: `Bearer ${accessToken}` },
    });
    const { public_key: vapidPublicKey } = await vapidRes.json();
    if (!vapidPublicKey) {
      console.warn('[Push] No VAPID public key configured on backend');
      return;
    }

    // 3. Request notification permission
    const permission = await Notification.requestPermission();
    if (permission !== 'granted') {
      console.log('[Push] Notification permission denied');
      return;
    }

    // 4. Subscribe to push
    const subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(vapidPublicKey),
    });

    const subJson = subscription.toJSON();
    const keys = subJson.keys as { auth: string; p256dh: string };

    // 5. Send subscription to backend
    await apiClient.call('/api/crm/push/subscribe', {
      endpoint: subJson.endpoint,
      auth: keys.auth,
      p256dh: keys.p256dh,
      user_agent: navigator.userAgent,
    });

    console.log('[Push] Push subscription registered with backend');
  } catch (err) {
    console.warn('[Push] Push registration failed:', err);
  }
}
```

Call this after the user logs in (where you call `fetchWsConfig`):

```typescript
// In your auth/login flow, after successful login:
import { registerPushNotifications } from '@/shared/push/usePushNotifications';

// After login and access_token is available:
await registerPushNotifications(accessToken);
```

---

## Step 4 — Handle Navigation from SW `postMessage`

In your `App.tsx` (or `RealtimeProvider.tsx`), listen for the SW's `NAVIGATE` message:

```typescript
useEffect(() => {
  if (!('serviceWorker' in navigator)) return;

  const handler = (event: MessageEvent) => {
    if (event.data?.type === 'NAVIGATE' && event.data?.url) {
      // Use React Router navigate
      navigate(event.data.url);
    }
  };

  navigator.serviceWorker.addEventListener('message', handler);
  return () => navigator.serviceWorker.removeEventListener('message', handler);
}, [navigate]);
```

---

## Step 5 — Suppress push notification if app is in focus

The Service Worker shows a notification even when the app tab is open and focused.
To suppress it when the user is already viewing the chat, add this to `sw.js`:

```javascript
// In sw.js — inside the 'push' handler, before showNotification:
self.addEventListener('push', (event) => {
  // ... parse data ...

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((windowClients) => {
      // If any tab has the app open and is focused, don't show the notification
      const appOpen = windowClients.some(
        (client) => client.visibilityState === 'visible' && client.url.includes(self.location.origin)
      );
      if (appOpen) return; // The in-app WebSocket notification handles it

      return self.registration.showNotification(title, options);
    })
  );
});
```

---

## Step 6 — Unsubscribe on Logout

When the user logs out, unsubscribe from push:

```typescript
// In your logout handler:
async function unregisterPush(accessToken: string) {
  if (!('serviceWorker' in navigator)) return;
  try {
    const reg = await navigator.serviceWorker.ready;
    const sub = await reg.pushManager.getSubscription();
    if (sub) {
      await apiClient.call('/api/crm/push/unsubscribe', { endpoint: sub.endpoint });
      await sub.unsubscribe();
    }
  } catch (err) {
    console.warn('[Push] Unsubscribe failed:', err);
  }
}
```

---

## Vite Config — Serve sw.js Correctly

Make sure Vite doesn't cache-bust the service worker file. In `vite.config.ts`:

```typescript
// In defineConfig:
build: {
  rollupOptions: {
    input: {
      main: 'index.html',
      sw: 'public/sw.js',  // keep sw.js as-is in public/
    },
  },
},
```

Actually, since `public/sw.js` is in the `public/` folder, Vite copies it to `dist/` as-is with no hashing. No extra config needed.

---

## Backend APIs Added

| Method | URL | Description |
|---|---|---|
| `GET` | `/api/crm/push/vapid-public-key` | Returns VAPID public key (no auth needed) |
| `POST` | `/api/crm/push/subscribe` | Register browser push subscription |
| `POST` | `/api/crm/push/unsubscribe` | Deactivate a push subscription |

---

## When Push Notifications Fire

| Event | Title | Body |
|---|---|---|
| New chat message | Sender's name | First 80 chars of message |
| New email | From name or email address | Email subject |

Notifications include `data.url` so clicking them opens the correct chat/email.

---

## Notes

- The Service Worker must be served from the **same origin** as the app (not a subdomain).
- HTTPS is required for Web Push — works with your existing `basicSsl()` Vite setup.
- If the user **denies** notification permission, push silently skips — no errors.
- Subscriptions auto-expire if the user clears browser data; re-login re-registers.
- Install `pywebpush` on the server: `pip install pywebpush` (once, in Odoo's venv).
