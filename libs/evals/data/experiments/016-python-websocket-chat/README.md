# Experiment: python-websocket-chat

**Format:** text/x-python | **Size:** medium | **Edits:** 3

**Expected sections:** models, connection-manager, handlers, app

## Protocol cost (the only difference from base)

| Prompt | Chars | ~Tokens |
|---|---|---|
| Base system | 94 | 23 |
| GAP init system | 230 | 57 |
| GAP maintain system | 383 | 95 |
| **Protocol overhead** | | **~129 tokens** |

## Turns

| Turn | Edit |
|---|---|
| 0 | (creation) |
| 1 | Add a new 'ReactionMessage' model with fields: message_id, user_id, emoji, an... |
| 2 | Rewrite the broadcast method in ConnectionManager to support broadcasting onl... |
| 3 | Add a new handler for 'pin_message' that allows users to pin a message in a r... |