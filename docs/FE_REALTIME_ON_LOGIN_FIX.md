# FE Fix — WebSocket Must Connect on Login, Not on Page Navigate

## The Problem

The WebSocket connection and email notifications only work **after the user
navigates to the email or messaging page**. This is because `RealtimeProvider`
(or `BusClient`) is mounted **inside a specific route/page** instead of at the
**app root**.

The backend is fully ready. All channels, all events, all session cookies are
set up correctly. The fix is **100% on the FE side** — one structural change.

---

## Root Cause

The component tree today looks something like this:

```
<App>
  <Routes>
    <Route path="/dashboard"  element={<DashboardPage />} />
    <Route path="/email"      element={
      <RealtimeProvider>        ← ❌ WRONG — only mounts when user is on /email
        <EmailPage />
      </RealtimeProvider>
    } />
    <Route path="/messages"   element={
      <RealtimeProvider>        ← ❌ WRONG — duplicate, mounts again
        <MessagesPage />
      </RealtimeProvider>
    } />
  </Routes>
</App>
```

The user must navigate to `/email` or `/messages` before the WebSocket opens.
Notifications, email badges, and message counts are all broken until then.

---

## The Fix — Move RealtimeProvider to App Root

### Step 1 — Find where RealtimeProvider is currently used

Search your codebase for all usages:

```bash
grep -r "RealtimeProvider\|BusClient\|useRealtime" src/ --include="*.tsx" -l
```

Remove every instance that wraps a specific page or route.

---

### Step 2 — Add it once at the App root

**`src/app/providers/AppProviders.tsx`**

```tsx
import { RealtimeProvider } from '@/features/realtime/RealtimeProvider';
// (adjust the import path to match your project)

export function AppProviders({ children }: { children: React.ReactNode }) {
  return (
    <ReduxProvider>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider>
          <RealtimeProvider>    {/* ← ADD HERE — wraps everything */}
            {children}
          </RealtimeProvider>
        </ThemeProvider>
      </QueryClientProvider>
    </ReduxProvider>
  );
}
```

If your app does not have `AppProviders`, add `RealtimeProvider` directly in
`App.tsx` or `main.tsx` — wherever the root layout is rendered.

---

### Step 3 — Guard on access token, not on component location

Inside `RealtimeProvider.tsx`, the `useEffect` that opens the WebSocket **must
depend on the access token**, not on component mount:

```tsx
// RealtimeProvider.tsx

const accessToken = useSelector(selectAccessToken);
// or: const accessToken = localStorage.getItem('tokenForCrm');

useEffect(() => {
  // Only connect when the user is actually logged in
  if (!accessToken) return;

  let ws: WebSocket | null = null;
  let destroyed = false;

  async function connect() {
    // The login endpoint now sends Set-Cookie automatically.
    // Call ws/session as a safety fallback (in case the cookie expired).
    try {
      await fetch('/api/crm/ws/session', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
          'X-Odoo-Database': import.meta.env.VITE_API_DB,
        },
        body: '{}',
        credentials: 'include',
      });
    } catch {
      // Non-fatal — proceed anyway; existing cookie may still be valid
    }

    if (destroyed) return;

    const proto = location.protocol === 'https:' ? 'wss' : 'ws';
    ws = new WebSocket(`${proto}://${location.host}/websocket`);

    ws.onopen = () => {
      ws!.send(JSON.stringify({
        event_name: 'subscribe',
        data: { channels: [], last: 0 },
      }));
    };

    ws.onmessage = handleBusEvent;   // your existing handler

    ws.onclose = (e) => {
      if (destroyed || e.code === 1000) return;
      // Reconnect with backoff
      setTimeout(connect, 3000);
    };
  }

  connect();

  return () => {
    destroyed = true;
    ws?.close(1000, 'provider_unmount');
  };

}, [accessToken]);   // ← key: re-runs on login/logout
```

**Key points:**
- When `accessToken` is `null` (not logged in) → effect returns immediately, no connection
- When `accessToken` is set (after login) → connection opens immediately
- When `accessToken` is cleared (after logout) → cleanup closes the connection

---

### Step 4 — Update the login flow

After a successful login response, ensure the token is stored in Redux/localStorage
**before** React re-renders (so the `useEffect` above fires immediately):

```ts
// In your auth slice / login mutation handler:

const loginResult = await login({ username, password });

if (loginResult.success) {
  const { access_token, refresh_token, ws_session_id } = loginResult.data;

  // 1. Store tokens
  localStorage.setItem('tokenForCrm', access_token);
  localStorage.setItem('posRefreshToken', refresh_token);
  dispatch(setTokens({ accessToken: access_token, refreshToken: refresh_token }));

  // 2. (Fallback) Set cookie manually if browser blocked Set-Cookie
  if (ws_session_id && !document.cookie.includes('session_id=')) {
    document.cookie = `session_id=${ws_session_id}; path=/; SameSite=Lax; Max-Age=86400`;
  }

  // 3. Navigate — RealtimeProvider detects the token and opens WS automatically
  navigate('/dashboard');
}
```

> **Note:** As of today the login endpoint (`POST /lugal/auth/login`) already
> sends `Set-Cookie: session_id=...` in the response AND returns `ws_session_id`
> in the response body. The FE just needs to store the tokens and navigate.

---

### Step 5 — Handle logout correctly

When the user logs out, clear the token from Redux/localStorage first, then
close the WebSocket. `RealtimeProvider` detects `accessToken = null` and the
cleanup function in `useEffect` closes the socket automatically:

```ts
// logout handler
dispatch(clearTokens());                    // clears accessToken in Redux
localStorage.removeItem('tokenForCrm');
localStorage.removeItem('posRefreshToken');
// No need to manually close WS — RealtimeProvider useEffect cleanup does it
navigate('/login');
```

---

## What events arrive on the WebSocket (no page navigation needed)

After the fix, these events arrive the moment they happen — regardless of which
page the user is on:

| Event type | Channel | Meaning |
|---|---|---|
| `crm.email.message.new` | `supply_user.<uid>` | New email in inbox |
| `supply.chat.message.new` | `supply_chat.<id>` | New CRM chat message |
| `supply.chat.typing.start` | `supply_chat.<id>` | Someone is typing |
| `supply.story.new` | `supply_stories` | New story posted |
| `supply.story.viewed` | `supply_user.<uid>` | Story view count update |

Use these events to update **badges, counters, and notification indicators**
in the header/sidebar even when the user is on the dashboard or any other page.

---

## Email badge update on new email event

Inside your `handleBusEvent` function, add this case:

```ts
if (type === 'crm.email.message.new') {
  // Increment the email unread badge in your UI store
  dispatch(incrementEmailUnread());

  // Invalidate the notifications query to refresh the badge count from API
  queryClient.invalidateQueries({ queryKey: ['crm', 'email', 'notifications'] });
  queryClient.invalidateQueries({ queryKey: ['email', 'mailbox', 'inbox'] });

  // Show a toast notification
  toast.info(`New email from ${payload.from_name || payload.from_address}`, {
    description: payload.subject,
    duration: 5000,
  });
}
```

---

## Quick checklist

- [ ] `RealtimeProvider` is rendered at the **app root** (in `AppProviders` or `App.tsx`)
- [ ] `RealtimeProvider` is **not** inside any specific route or page component
- [ ] The `useEffect` in `RealtimeProvider` depends on `accessToken` (not just on mount)
- [ ] On login: token is stored **before** navigation so the effect fires immediately
- [ ] On logout: token is cleared so the effect cleanup closes the WebSocket
- [ ] `crm.email.message.new` handler updates the email badge in the header
- [ ] No call to `POST /api/crm/ws/session` is needed before opening the WebSocket
  (the login endpoint sets the cookie automatically — it's a safety-only call now)
