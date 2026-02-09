#!/bin/bash
# Run DBS2 WebSocket multiplayer chat server
# Usage: ./run_websocket.sh  or  python dbs2_websocket_server.py
cd "$(dirname "$0")"
pip install -q websockets 2>/dev/null || true
python3 dbs2_websocket_server.py
