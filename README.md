# Write Ahead Log

A small Flask service demonstrating a Write-Ahead Log (WAL).

Every state mutation is appended to an ordered log before being applied to the in-memory state. The state can then be rebuilt by replaying the log.

## Run

```bash
pip install -r requirements.txt
python app.py
```

## API

- `POST /api/write` — append a state change
- `GET /api/state` — current state
- `GET /api/log` — inspect the append-only log
- `POST /api/replay` — rebuild state from the log
- `GET /api/stats` — log statistics
- `GET /health` — health check

Example:

```json
{
  "key": "status",
  "value": "online"
}
```

## Concepts

Write-Ahead Logging, append-only logs, ordered operations, replay, state reconstruction, crash-recovery concepts, durability patterns.
