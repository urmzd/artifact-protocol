Create a Python WebSocket chat server using FastAPI.

Include:
- Message models (ChatMessage, SystemMessage, UserJoined, UserLeft)
- ConnectionManager class: connect, disconnect, broadcast, send_to_user, list_rooms
- Message handlers: join room, leave room, send message, typing indicator, message history
- FastAPI app with WebSocket endpoint and REST endpoints for room management
- Basic rate limiting and message validation
