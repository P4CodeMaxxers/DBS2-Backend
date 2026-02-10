# DBS2 WebSocket Chat – Deployed Server

The DBS2 chat box uses a **separate WebSocket server** (not Flask). It must be running on the same machine as the backend for chat to work on the live site.

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
