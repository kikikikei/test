# step4_sync.py
# Real-time vs Batch synchronization demo (no external libs)

from datetime import datetime
import json, re, pathlib

# ---------- Survivorship & helpers ----------
PRIORITY = {"CRM": 2, "eCommerce": 1, "Support": 1}  # tie-breaker if timestamps equal

def to_dt(x: str) -> datetime:
    # Accepts ISO8601; supports "Z"
    if x.endswith("Z"):
        x = x[:-1] + "+00:00"
    return datetime.fromisoformat(x)

def norm_email(e: str) -> str:
    return e.strip().lower()

def norm_phone(p: str) -> str:
    # keep leading + and digits; collapse cruft
    s = re.sub(r"[^\d+]", "", p)
    return "+" + re.sub(r"^\+*", "", s) if s.startswith("+") else s

def put(golden: dict, meta: dict, field: str, value, ts: datetime, src: str):
    """Apply survivorship: newer timestamp wins; on tie, higher source priority wins."""
    if value in (None, "", []):
        return
    m = meta.get(field)
    if (
        m is None
        or ts > m["ts"]
        or (ts == m["ts"] and PRIORITY.get(src, 0) > PRIORITY.get(m["src"], 0))
    ):
        golden[field] = value
        meta[field] = {"ts": ts, "src": src}

def merge(golden: dict, meta: dict, rec: dict):
    rec = rec.copy()
    if rec.get("email"):
        rec["email"] = norm_email(rec["email"])
    if rec.get("phone"):
        rec["phone"] = norm_phone(rec["phone"])

    ts  = to_dt(rec.get("updated_at", "1970-01-01T00:00:00+00:00"))
    src = rec.get("source", "unknown")

    # identity + common fields
    put(golden, meta, "customer_id", rec.get("customer_id") or rec.get("id"), ts, src)
    put(golden, meta, "email",       rec.get("email"), ts, src)
    for f in ["first_name", "last_name", "phone"]:
        if f in rec: put(golden, meta, f, rec[f], ts, src)

    # sub-objects
    for sub in ["address", "loyalty"]:
        if isinstance(rec.get(sub), dict):
            golden.setdefault(sub, {}); meta.setdefault(sub, {})
            for k, v in rec[sub].items():
                put(golden[sub], meta[sub], k, v, ts, src)

    golden["_last_updated"] = max(
        golden.get("_last_updated", to_dt("1970-01-01T00:00:00+00:00")), ts
    )
    return golden, meta

def key_for(rec: dict) -> str:
    return f"email:{norm_email(rec['email'])}" if rec.get("email") else f"id:{rec.get('customer_id') or rec.get('id')}"

# ---------- Real-time: apply events immediately ----------
store, store_meta = {}, {}

def upsert_event(evt: dict):
    k = key_for(evt)
    g = store.setdefault(k, {})
    m = store_meta.setdefault(k, {})
    merge(g, m, evt)

realtime_events = [
    # Support fixes phone
    {"source": "Support", "updated_at": "2025-09-20T13:10:00Z",
     "email": "ava.lopez@example.com", "phone": "(415) 555-9999"},
    # CRM updates address street
    {"source": "CRM", "updated_at": "2025-09-20T13:15:00Z",
     "customer_id": "C123", "email": "Ava.Lopez@example.com",
     "address": {"street": "15 Market St"}},
]

for ev in realtime_events:
    upsert_event(ev)

print("After REAL-TIME events (in-memory):")
print(json.dumps(store, indent=2, ensure_ascii=False, default=str))


# ---------- Batch: write file now, process later ----------
batch = [
    # Later loyalty update for Ava
    {"source": "eCommerce", "updated_at": "2025-09-20T14:00:00Z",
     "email": "ava.lopez@example.com", "loyalty": {"points": 4400}},
    # New customer (created in batch)
    {"source": "CRM", "updated_at": "2025-09-20T14:05:00Z",
     "customer_id": "C124", "first_name": "Brianna", "last_name": "Lee",
     "email": "b.lee@example.com"},
    # Another new customer
    {"source": "Support", "updated_at": "2025-09-20T14:10:00Z",
     "email": "c.garcia@example.com", "first_name": "Carlos",
     "last_name": "Garcia", "phone": "+1-212-555-0188"},
]

out = pathlib.Path("batch_updates.jsonl")
with out.open("w", encoding="utf-8") as f:
    for rec in batch:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

# “Later”: process the file
with out.open("r", encoding="utf-8") as f:
    for line in f:
        upsert_event(json.loads(line))

print("\nAfter BATCH processing (file → applied):")
print(json.dumps(store, indent=2, ensure_ascii=False, default=str))



