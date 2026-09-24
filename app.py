from copy import deepcopy
from threading import RLock
from flask import Flask, jsonify, request

app = Flask(__name__)
LOCK = RLock()


class WriteAheadLog:
    def __init__(self):
        self.log = []
        self.state = {}
        self.next_index = 1

    def append(self, key, value):
        if not isinstance(key, str) or not key.strip():
            raise ValueError("key must be a non-empty string")
        key = key.strip()
        if len(key) > 128:
            raise ValueError("key must be 1-128 characters")

        entry = {
            "index": self.next_index,
            "operation": "set",
            "key": key,
            "value": value,
        }

        # The log is written before the state mutation.
        self.log.append(entry)
        self.next_index += 1
        self.state[key] = value

        return deepcopy(entry)

    def replay(self):
        rebuilt = {}
        for entry in self.log:
            if entry["operation"] == "set":
                rebuilt[entry["key"]] = entry["value"]
        self.state = rebuilt
        return deepcopy(rebuilt)

    def stats(self):
        return {
            "entries": len(self.log),
            "keys": len(self.state),
            "next_index": self.next_index,
            "last_index": self.log[-1]["index"] if self.log else 0,
        }


wal = WriteAheadLog()


@app.get("/health")
def health():
    with LOCK:
        return jsonify({"status": "ok", "entries": len(wal.log)})


@app.post("/api/write")
def write():
    body = request.get_json(silent=True) or {}
    if "value" not in body:
        return jsonify({"error": "value is required"}), 400

    try:
        with LOCK:
            entry = wal.append(body.get("key"), body["value"])
        return jsonify(entry), 201
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@app.get("/api/state")
def state():
    with LOCK:
        return jsonify({
            "state": deepcopy(wal.state),
            "count": len(wal.state),
        })


@app.get("/api/log")
def get_log():
    with LOCK:
        return jsonify({
            "entries": deepcopy(wal.log),
            "count": len(wal.log),
        })


@app.post("/api/replay")
def replay():
    with LOCK:
        rebuilt = wal.replay()
    return jsonify({
        "replayed": True,
        "state": rebuilt,
        "count": len(rebuilt),
    })


@app.get("/api/stats")
def stats():
    with LOCK:
        return jsonify(wal.stats())


if __name__ == "__main__":
    app.run(debug=True)
