# DBS2 WebSocket Chat – Deployed Server

The DBS2 chat box uses a **separate WebSocket server** (not Flask). It must be running on the same machine as the backend for chat to work on the live site.

## 404 on wss://.../dbs2-ws – Checklist

If you see **"WebSocket connection failed: 404"** on the deployed site:

1. **WebSocket process must be running on the server** (port 8765).  
   See options below (run_with_websocket.sh or systemd).

2. **Nginx must proxy `/dbs2-ws` for HTTPS.**  
   The browser uses `wss://` (port 443). Your **HTTPS** server block for `dbs2.opencodingsociety.com` must include the same `location /dbs2-ws { ... }` as in `deploy_flask_nginx`.  
   If you use certbot/Let’s Encrypt, the live config is often in something like `/etc/nginx/sites-enabled/dbs2.opencodingsociety.com` or a snippet under `sites-enabled`. **Add the `/dbs2-ws` block there** (see `deploy/nginx-https-dbs2-ws.snippet`), then run:
   ```bash
   sudo nginx -t && sudo systemctl reload nginx
   ```

3. **Confirm something is listening on 8765** on the server:
   ```bash
   curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" -H "Host: dbs2.opencodingsociety.com" http://localhost:8765/
   ```
   You should get a 426 or 101, not "Connection refused".

## Why it works on localhost but not on the deployed site

- **Local:** You run `python3 socket/dbs2_websocket_server.py` (or `./socket/run_websocket.sh`), so something is listening on port 8765.
- **Deployed:** Only the Flask app is usually started. Nothing listens on 8765, so nginx gets “connection refused” and the frontend sees a 404/connection error.

## Option 1: One command (Flask + WebSocket)

From the backend repo root on the server:

```bash
chmod +x run_with_websocket.sh
./run_with_websocket.sh
```

This starts the WebSocket server in the background on port 8765, then starts Flask. Both run in the same terminal; Ctrl+C stops both.

## Option 2: Two terminals (or tmux/screen)

**Terminal 1 – WebSocket server:**

```bash
cd /path/to/DBS2-Backend
source venv/bin/activate
python3 socket/dbs2_websocket_server.py
```

**Terminal 2 – Flask:**

```bash
cd /path/to/DBS2-Backend
source venv/bin/activate
python main.py
```

## Option 3: systemd (recommended for production)

So the WebSocket server restarts on reboot and runs as a service:

1. Copy and edit the example unit file:
   ```bash
   sudo cp deploy/dbs2-websocket.service.example /etc/systemd/system/dbs2-websocket.service
   sudo nano /etc/systemd/system/dbs2-websocket.service
   ```
   Set `User`, `WorkingDirectory`, and `ExecStart` to your real paths (e.g. `/home/ubuntu/DBS2-Backend` and your venv).

2. Enable and start:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable dbs2-websocket
   sudo systemctl start dbs2-websocket
   sudo systemctl status dbs2-websocket
   ```

3. Keep running Flask (or your WSGI server) as you already do. Nginx is already set up to proxy `https://dbs2.opencodingsociety.com/dbs2-ws` to `http://localhost:8765`.

## Check that it’s working

- On the server: `curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" http://localhost:8765/` should get a 426 or 101 response, not “connection refused”.
- In the browser: open the DBS2 site and the chat widget; it should show “Connected” instead of “Disconnected. Reconnecting…”.
