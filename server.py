#!/usr/bin/env python3
"""
Lightweight HTTP + Lead Capture & Visit/Click Analytics Server
for Southern NH & Northern MA Septic Directory
Serves static files from /workspace/septic-directory/site
Handles:
  - POST /api/quote   -> saves homeowner quote requests to data/leads.json & data/leads.csv
  - POST /api/sponsor -> saves hauler featured-spot sponsorship inquiries to data/sponsors.json
  - POST /api/track   -> logs pageviews, town visits, calculator runs, and hauler clicks to data/analytics.json
  - GET  /api/stats   -> returns aggregated analytics + lead counts
  - GET  /api/health  -> returns health status, lead count, and visit count
"""

import csv
import datetime
import http.server
import json
import os
import socketserver
import uuid
from zoneinfo import ZoneInfo

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SITE_DIR = os.path.join(BASE_DIR, "site")
DATA_DIR = os.path.join(BASE_DIR, "data")
PROVIDERS_JSON = os.path.join(DATA_DIR, "providers.json")
LEADS_JSON = os.path.join(DATA_DIR, "leads.json")
LEADS_CSV = os.path.join(DATA_DIR, "leads.csv")
SPONSORS_JSON = os.path.join(DATA_DIR, "sponsors.json")
ANALYTICS_JSON = os.path.join(DATA_DIR, "analytics.json")
PORT = int(os.environ.get("SEPTIC_PORT", "8088"))


def default_analytics():
    return {
        "total_views": 0,
        "unique_visitors": 0,
        "visitor_ids": [],
        "calc_runs": 0,
        "quote_submits": 0,
        "sponsor_inquiries": 0,
        "pages": {},
        "towns": {},
        "providers": {},
        "recent_events": [],
        "updated_at": ""
    }


def load_analytics():
    if os.path.exists(ANALYTICS_JSON):
        try:
            with open(ANALYTICS_JSON, "r", encoding="utf-8") as f:
                data = json.load(f)
                base = default_analytics()
                base.update(data)
                return base
        except Exception:
            pass
    return default_analytics()


def save_analytics(data):
    os.makedirs(DATA_DIR, exist_ok=True)
    now_et = datetime.datetime.now(ZoneInfo("America/New_York"))
    data["updated_at"] = now_et.strftime("%Y-%m-%d %I:%M:%S %p EDT")
    if len(data.get("visitor_ids", [])) > 2000:
        data["visitor_ids"] = data["visitor_ids"][-2000:]
    if len(data.get("recent_events", [])) > 100:
        data["recent_events"] = data["recent_events"][-100:]
    with open(ANALYTICS_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def record_event(payload):
    data = load_analytics()
    now_et = datetime.datetime.now(ZoneInfo("America/New_York"))
    ts = now_et.strftime("%Y-%m-%d %I:%M:%S %p EDT")

    ev_type = str(payload.get("type", "pageview")).strip()
    page = str(payload.get("page", "/")).strip() or "/"
    town = str(payload.get("town", "")).strip()
    visitor_id = str(payload.get("visitor_id", "")).strip()
    provider_id = str(payload.get("provider_id", "")).strip()
    provider_name = str(payload.get("provider_name", "")).strip()
    action = str(payload.get("action", "")).strip()

    if visitor_id and visitor_id not in data["visitor_ids"]:
        data["visitor_ids"].append(visitor_id)
        data["unique_visitors"] = len(data["visitor_ids"])

    if ev_type == "pageview":
        data["total_views"] = int(data.get("total_views", 0)) + 1
        data["pages"][page] = int(data["pages"].get(page, 0)) + 1
        if town:
            data["towns"][town] = int(data["towns"].get(town, 0)) + 1
    elif ev_type == "calc":
        data["calc_runs"] = int(data.get("calc_runs", 0)) + 1
    elif ev_type == "quote":
        data["quote_submits"] = int(data.get("quote_submits", 0)) + 1
        if town:
            data["towns"][town] = int(data["towns"].get(town, 0)) + 1
    elif ev_type == "sponsor":
        data["sponsor_inquiries"] = int(data.get("sponsor_inquiries", 0)) + 1
    elif ev_type == "provider_click":
        key = provider_id or provider_name or "unknown"
        entry = data["providers"].get(key, {"name": provider_name or key, "phone": 0, "web": 0, "total": 0})
        if provider_name:
            entry["name"] = provider_name
        if action == "phone":
            entry["phone"] = int(entry.get("phone", 0)) + 1
        else:
            entry["web"] = int(entry.get("web", 0)) + 1
        entry["total"] = int(entry.get("phone", 0)) + int(entry.get("web", 0))
        data["providers"][key] = entry

    data["recent_events"].append({
        "timestamp_et": ts,
        "type": ev_type,
        "page": page,
        "town": town,
        "provider_id": provider_id,
        "provider_name": provider_name,
        "action": action
    })

    save_analytics(data)
    return data


def load_providers():
    try:
        with open(PROVIDERS_JSON, "r", encoding="utf-8") as f:
            return json.load(f).get("providers", [])
    except Exception:
        return []


def match_providers_for_lead(town_raw, service_raw):
    providers = load_providers()
    town_name = (town_raw or "").split(",")[0].strip()
    matches = []
    for p in providers:
        if not town_name or town_name in p.get("towns_served", []):
            matches.append(p)
    if not matches:
        matches = providers[:3]
    if "Emergency" in (service_raw or ""):
        matches.sort(key=lambda x: (not x.get("emergency_24_7", False), not x.get("featured", False)))
    else:
        matches.sort(key=lambda x: (not x.get("featured", False),))
    top = []
    for m in matches[:3]:
        top.append({
            "id": m.get("id"),
            "name": m.get("name"),
            "phone": m.get("phone"),
            "est_1000_gal": m.get("est_1000_gal"),
            "hq": f"{m.get('hq_town')}, {m.get('hq_state')}"
        })
    return top


def save_lead(payload):
    os.makedirs(DATA_DIR, exist_ok=True)
    now_et = datetime.datetime.now(ZoneInfo("America/New_York"))
    lead_id = f"LEAD-{now_et.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:4].upper()}"
    town = str(payload.get("town", "Danville, NH")).strip()
    service = str(payload.get("service", "Routine Pumping")).strip()
    matched = match_providers_for_lead(town, service)

    record = {
        "lead_id": lead_id,
        "timestamp_et": now_et.strftime("%Y-%m-%d %I:%M:%S %p EDT"),
        "name": str(payload.get("name", "")).strip(),
        "phone": str(payload.get("phone", "")).strip(),
        "email": str(payload.get("email", "")).strip(),
        "town": town,
        "service": service,
        "notes": str(payload.get("notes", "")).strip(),
        "source_page": str(payload.get("source_page", "/")).strip(),
        "matched_providers": [m["name"] for m in matched],
        "status": "new"
    }

    leads = []
    if os.path.exists(LEADS_JSON):
        try:
            with open(LEADS_JSON, "r", encoding="utf-8") as f:
                leads = json.load(f)
        except Exception:
            leads = []
    leads.append(record)
    with open(LEADS_JSON, "w", encoding="utf-8") as f:
        json.dump(leads, f, indent=2)

    write_header = not os.path.exists(LEADS_CSV)
    with open(LEADS_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(["lead_id", "timestamp_et", "name", "phone", "email", "town", "service", "source_page", "matched_providers", "status"])
        writer.writerow([
            record["lead_id"],
            record["timestamp_et"],
            record["name"],
            record["phone"],
            record["email"],
            record["town"],
            record["service"],
            record["source_page"],
            "; ".join(record["matched_providers"]),
            record["status"],
        ])

    record_event({
        "type": "quote",
        "page": record["source_page"],
        "town": town.split(",")[0].strip()
    })

    return record, matched


def save_sponsor_inquiry(payload):
    os.makedirs(DATA_DIR, exist_ok=True)
    now_et = datetime.datetime.now(ZoneInfo("America/New_York"))
    inq_id = f"SPON-{now_et.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:4].upper()}"
    record = {
        "inquiry_id": inq_id,
        "timestamp_et": now_et.strftime("%Y-%m-%d %I:%M:%S %p EDT"),
        "company": str(payload.get("company", "")).strip(),
        "contact": str(payload.get("contact", "")).strip(),
        "phone": str(payload.get("phone", "")).strip(),
        "email": str(payload.get("email", "")).strip(),
        "towns": str(payload.get("towns", "")).strip(),
        "plan": str(payload.get("plan", "$99/mo Exclusive Featured Town Hauler")).strip(),
        "status": "new"
    }
    sponsors = []
    if os.path.exists(SPONSORS_JSON):
        try:
            with open(SPONSORS_JSON, "r", encoding="utf-8") as f:
                sponsors = json.load(f)
        except Exception:
            sponsors = []
    sponsors.append(record)
    with open(SPONSORS_JSON, "w", encoding="utf-8") as f:
        json.dump(sponsors, f, indent=2)

    record_event({"type": "sponsor", "page": "/stats.html"})
    return record


class SepticDirectoryHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=SITE_DIR, **kwargs)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def _send_json(self, status_code, obj):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith("/api/health"):
            leads_count = 0
            if os.path.exists(LEADS_JSON):
                try:
                    with open(LEADS_JSON, "r", encoding="utf-8") as f:
                        leads_count = len(json.load(f))
                except Exception:
                    pass
            analytics = load_analytics()
            self._send_json(200, {
                "ok": True,
                "service": "septic-directory",
                "leads_captured": leads_count,
                "total_views": analytics.get("total_views", 0),
                "unique_visitors": analytics.get("unique_visitors", 0)
            })
            return

        if self.path.startswith("/api/stats"):
            leads = []
            if os.path.exists(LEADS_JSON):
                try:
                    with open(LEADS_JSON, "r", encoding="utf-8") as f:
                        leads = json.load(f)
                except Exception:
                    pass
            analytics = load_analytics()
            resp = dict(analytics)
            resp["ok"] = True
            resp["leads_captured"] = len(leads)
            resp.pop("visitor_ids", None)
            self._send_json(200, resp)
            return

        return super().do_GET()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
        try:
            payload = json.loads(raw)
        except Exception:
            payload = {}

        if self.path.startswith("/api/track"):
            data = record_event(payload)
            self._send_json(200, {
                "ok": True,
                "total_views": data.get("total_views", 0),
                "unique_visitors": data.get("unique_visitors", 0),
                "calc_runs": data.get("calc_runs", 0),
                "quote_submits": data.get("quote_submits", 0)
            })
            return

        if self.path.startswith("/api/sponsor"):
            if not payload.get("company") or not payload.get("phone"):
                self._send_json(400, {"ok": False, "error": "Company name and phone are required."})
                return
            record = save_sponsor_inquiry(payload)
            self._send_json(200, {
                "ok": True,
                "inquiry_id": record["inquiry_id"],
                "timestamp_et": record["timestamp_et"],
                "message": f"Sponsorship inquiry #{record['inquiry_id']} received for {record['company']}."
            })
            return

        if self.path.startswith("/api/quote"):
            if not payload.get("name") or not payload.get("phone"):
                self._send_json(400, {"ok": False, "error": "Name and phone number are required."})
                return

            record, matched = save_lead(payload)
            resp = {
                "ok": True,
                "lead_id": record["lead_id"],
                "timestamp_et": record["timestamp_et"],
                "town": record["town"],
                "service": record["service"],
                "matched_providers": matched,
                "message": f"Quote request #{record['lead_id']} logged for {record['town']} ({record['service']})."
            }
            self._send_json(200, resp)
            return

        self.send_response(404)
        self.end_headers()


class ReusableTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True


if __name__ == "__main__":
    with ReusableTCPServer(("127.0.0.1", PORT), SepticDirectoryHandler) as httpd:
        print(f"[septic-directory] Serving {SITE_DIR} and /api/{{quote,track,stats,sponsor}} on http://127.0.0.1:{PORT}", flush=True)
        httpd.serve_forever()
