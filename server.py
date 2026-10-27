#!/usr/bin/env python3
"""
Lightweight HTTP + Lead Capture Server for Southern NH & Northern MA Septic Directory
Serves static files from /workspace/septic-directory/site
Handles:
  - POST /api/quote  -> saves homeowner quote requests to data/leads.json & data/leads.csv
  - GET  /api/health -> returns health status and lead count
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
PORT = int(os.environ.get("SEPTIC_PORT", "8088"))


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
    # Prioritize featured, then emergency if emergency requested
    if "Emergency" in (service_raw or ""):
        matches.sort(key=lambda x: (not x.get("emergency_24_7", False), not x.get("featured", False)))
    else:
        matches.sort(key=lambda x: (not x.get("featured", False),))
    top = []
    for m in matches[:3]:
        top.append({
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
        "town": town,
        "service": service,
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
            writer.writerow(["lead_id", "timestamp_et", "name", "phone", "town", "service", "source_page", "matched_providers", "status"])
        writer.writerow([
            record["lead_id"],
            record["timestamp_et"],
            record["name"],
            record["phone"],
            record["town"],
            record["service"],
            record["source_page"],
            "; ".join(record["matched_providers"]),
            record["status"],
        ])

    return record, matched


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

    def do_GET(self):
        if self.path.startswith("/api/health"):
            leads_count = 0
            if os.path.exists(LEADS_JSON):
                try:
                    with open(LEADS_JSON, "r", encoding="utf-8") as f:
                        leads_count = len(json.load(f))
                except Exception:
                    pass
            body = json.dumps({"ok": True, "service": "septic-directory", "leads_captured": leads_count}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        return super().do_GET()

    def do_POST(self):
        if self.path.startswith("/api/quote"):
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
            try:
                payload = json.loads(raw)
            except Exception:
                payload = {}

            if not payload.get("name") or not payload.get("phone"):
                body = json.dumps({"ok": False, "error": "Name and phone number are required."}).encode("utf-8")
                self.send_response(400)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
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
            body = json.dumps(resp).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        self.send_response(404)
        self.end_headers()


class ReusableTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True


if __name__ == "__main__":
    with ReusableTCPServer(("127.0.0.1", PORT), SepticDirectoryHandler) as httpd:
        print(f"[septic-directory] Serving {SITE_DIR} and /api/quote on http://127.0.0.1:{PORT}", flush=True)
        httpd.serve_forever()
