#!/bin/bash
# Run Flask backend and DBS2 WebSocket chat server together.
# Use this on the deployed server so chat works: nginx proxies /dbs2-ws to port 8765.

set -e
cd "$(dirname "$0")"

if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Install websockets if missing (for socket server)
pip install -q websockets 2>/dev/null || true

echo "Starting DBS2 WebSocket server on port 8765 (for /dbs2-ws)..."
python3 socket/dbs2_websocket_server.py &
WS_PID=$!
echo "WebSocket server PID: $WS_PID"

cleanup() {
    kill $WS_PID 2>/dev/null || true
    exit 0
}
trap cleanup SIGINT SIGTERM

echo "Starting Flask on port 8403..."
python main.py
