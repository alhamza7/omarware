# Remote Access — NBS Project Server

## Connection Details

| Field    | Value                      |
|----------|----------------------------|
| Host     | `ssh.noralnibras.com`      |
| Username | `dev_niral`                |
| Password | `niral_dev`                |
| Port     | `22` (via Cloudflare Tunnel) |

---

## Step 1 — Install cloudflared

> Required on your local machine to route through the Cloudflare Tunnel.

### Windows
Download and install from:
https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/

Or via winget:
```powershell
winget install Cloudflare.cloudflared
```

### Mac
```bash
brew install cloudflare/cloudflare/cloudflared
```

### Linux (Ubuntu/Debian)
```bash
curl -L https://pkg.cloudflare.com/cloudflared-stable-linux-amd64.deb -o cloudflared.deb
sudo dpkg -i cloudflared.deb
```

---

## Step 2 — Add SSH Config Entry

Add the following block to your SSH config file:

- **Windows**: `C:\Users\YourName\.ssh\config`
- **Mac/Linux**: `~/.ssh/config`

```
Host nbs-server
    HostName ssh.noralnibras.com
    User dev_niral
    ProxyCommand cloudflared access ssh --hostname ssh.noralnibras.com
    ServerAliveInterval 30
    ServerAliveCountMax 3
```

---

## Step 3 — Connect via Cursor (Remote SSH)

1. Open **Cursor**
2. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
3. Type: `Remote-SSH: Connect to Host`
4. Select **`nbs-server`** from the list
5. Enter password when prompted: **`niral_dev`**
6. Open folder: `/home/capo7amzah/Documents/NBS-PROJECT`

---

## Step 4 — Connect via Terminal (optional)

```bash
ssh nbs-server
# Password: niral_dev
```

Or without the config file:

```bash
ssh -o "ProxyCommand=cloudflared access ssh --hostname ssh.noralnibras.com" dev_niral@ssh.noralnibras.com
# Password: niral_dev
```

---

## Available Services

| Service | URL |
|---------|-----|
| Odoo API (Backend) | https://app.noralnibras.com |
| Odoo Admin Panel  | https://app.noralnibras.com/web |

---

## Project Location on Server

```
/home/capo7amzah/Documents/NBS-PROJECT/
├── Lugal-ai/          ← Odoo backend (Python)
└── NBS-CRM/           ← Frontend (Vite/React)
```

---

## Notes

- The tunnel runs 24/7 as a system service and restarts automatically.
- If the connection drops, wait 5 seconds and reconnect — cloudflared reconnects automatically.
- Do **not** run `sudo` commands without coordination with the main admin.
