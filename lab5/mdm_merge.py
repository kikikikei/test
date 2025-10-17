# mdm_merge.py
from datetime import datetime
import json, re

PRIORITY = {"CRM":2, "eCommerce":1, "Support":1}

def to_dt(x):
    if isinstance(x, datetime): return x
    if x.endswith("Z"): x = x[:-1] + "+00:00"
    return datetime.fromisoformat(x)

def norm_email(e): return e.strip().lower()
def norm_phone(p):
    s = re.sub(r"[^\d+]", "", p)
    return "+" + re.sub(r"^\+*", "", s) if s.startswith("+") else s

def put(g, meta, f, v, ts, src):
    if v in (None,"",[]): return
    m = meta.get(f)
    if not m or ts > m["ts"] or (ts == m["ts"] and PRIORITY.get(src,0) > PRIORITY.get(m["src"],0)):
        g[f] = v; meta[f] = {"ts": ts, "src": src}

def merge(g, meta, rec):
    rec = rec.copy()
    if rec.get("email"): rec["email"] = norm_email(rec["email"])
    if rec.get("phone"): rec["phone"] = norm_phone(rec["phone"])
    ts = to_dt(rec.get("updated_at","1970-01-01T00:00:00+00:00"))
    src = rec.get("source","unknown")

    put(g, meta, "customer_id", rec.get("customer_id") or rec.get("id"), ts, src)
    put(g, meta, "email", rec.get("email"), ts, src)
    for f in ["first_name","last_name","phone"]:
        if f in rec: put(g, meta, f, rec[f], ts, src)

    for sub in ["address","loyalty"]:
        if isinstance(rec.get(sub), dict):
            g.setdefault(sub, {}); meta.setdefault(sub, {})
            for k,v in rec[sub].items():
                put(g[sub], meta[sub], k, v, ts, src)

    g["_last_updated"] = max(g.get("_last_updated", to_dt("1970-01-01T00:00:00+00:00")), ts)
    return g, meta












# Demo inputs
A = {"source":"CRM","updated_at":"2025-09-20T11:30:00Z","customer_id":"C123","first_name":"Ava","last_name":"Lopez",
     "email":"Ava.Lopez@example.com","address":{"street":"12 Market Street","city":"San Francisco","state":"CA","postal":"94105","country":"US"}}
B = {"source":"eCommerce","updated_at":"2025-09-20T12:45:00Z",
"customer_id":"123","email":"ava.lopez_new@example.com",
     "phone":"+1 415 555 0134","loyalty":{"tier":"Gold","points":4200},"last_name":"López"}

golden, meta = {}, {}
merge(golden, meta, A)
merge(golden, meta, B)

print(json.dumps(golden, indent=2, ensure_ascii=False, default=str))
