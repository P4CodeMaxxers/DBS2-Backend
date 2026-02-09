#!/usr/bin/env python3
"""
DBS2 Multiplayer WebSocket Server
Follows the teacher's WebSocket article: broadcast chat room for DBS2 game.
Players in the basement can send messages that all connected clients see.

Usage: python dbs2_websocket_server.py
Runs on ws://localhost:8765 (dev) or ws://0.0.0.0:8765 (prod)
"""
import asyncio
import json
import os
from websockets.exceptions import ConnectionClosedOK, ConnectionClosedError

try:
    import websockets
except ImportError:
    print("Install websockets: pip install websockets")
    raise

# Track all connected clients for broadcast
connected = set()
# Message history so new clients see past messages (bigger apps use a database)
message_history = []
MAX_HISTORY = 50  # Keep last N messages


async def broadcast_handler(websocket):
    """Handle a connected client: welcome, replay history, then broadcast incoming messages."""
    connected.add(websocket)
    remote = websocket.remote_address
    print(f"[DBS2 WS] Client connected: {remote}, total: {len(connected)}")

    # Send welcome message
    await websocket.send(json.dumps({
        "type": "system",
        "message": "Welcome to DBS2 Multiplayer Chat! Type to talk with other players in the basement.",
    }))

    # Replay past messages so new client is up to speed
    for msg in message_history[-MAX_HISTORY:]:
        try:
            await websocket.send(msg)
        except Exception:
            break

    try:
        async for raw in websocket:
            try:
                # Accept JSON { "name": "...", "text": "..." } or plain string
                if isinstance(raw, str) and raw.strip().startswith("{"):
                    data = json.loads(raw)
                    name = data.get("name", "Anonymous")
                    text = data.get("text", str(data))
                else:
                    name = "Anonymous"
                    text = str(raw)

                if not text.strip():
                    continue

                # Build broadcast message
                msg = json.dumps({
                    "type": "chat",
                    "name": name[:32],
                    "text": text[:500],
                })
                message_history.append(msg)
                if len(message_history) > MAX_HISTORY:
                    message_history.pop(0)

                print(f"[DBS2 WS] Broadcast from {name}: {text[:50]}...")

                # Broadcast to all connected clients
                to_remove = set()
                for client in connected:
                    try:
                        await client.send(msg)
                    except (ConnectionClosedOK, ConnectionClosedError):
                        to_remove.add(client)
                for dead in to_remove:
                    connected.discard(dead)
            except json.JSONDecodeError:
                # Plain text fallback
                msg = json.dumps({"type": "chat", "name": "Anonymous", "text": str(raw)[:500]})
                message_history.append(msg)
                if len(message_history) > MAX_HISTORY:
                    message_history.pop(0)
                for client in connected:
                    try:
                        await client.send(msg)
                    except (ConnectionClosedOK, ConnectionClosedError):
                        pass
    finally:
        connected.discard(websocket)
        print(f"[DBS2 WS] Client disconnected: {remote}, total: {len(connected)}")


async def main():
    host = os.environ.get("WS_HOST", "0.0.0.0")
    port = int(os.environ.get("WS_PORT", "8765"))
    async with websockets.serve(
        broadcast_handler,
        host,
        port,
        ping_interval=10,
        ping_timeout=5,
    ):
        print(f"[DBS2 WS] Server listening on ws://{host}:{port}")
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
