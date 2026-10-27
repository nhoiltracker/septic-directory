#!/usr/bin/env python3
"""
Deploy /workspace/septic-directory/site to a free live public subdomain (.csb.app)
over standard HTTPS (port 443) with zero credentials required.
"""

import json
import os
import urllib.request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SITE_DIR = os.path.join(BASE_DIR, "site")
LIVE_URL_PATH = os.path.join(BASE_DIR, "data", "live_url.txt")


def collect_files():
    files = {
        "sandbox.config.json": {
            "content": json.dumps({"template": "static"}, indent=2)
        },
        "package.json": {
            "content": json.dumps({
                "name": "southern-nh-northern-ma-septic-directory",
                "version": "1.0.0",
                "description": "Southern NH & Northern MA Septic Pumping, Inspection & Title 5 Directory",
                "main": "index.html"
            }, indent=2)
        }
    }
    for root, _, filenames in os.walk(SITE_DIR):
        for fname in filenames:
            full_path = os.path.join(root, fname)
            rel_path = os.path.relpath(full_path, SITE_DIR).replace("\\", "/")
            with open(full_path, "r", encoding="utf-8") as f:
                files[rel_path] = {"content": f.read()}
    return files


def deploy():
    files = collect_files()
    payload = json.dumps({"files": files}).encode("utf-8")
    req = urllib.request.Request(
        "https://codesandbox.io/api/v1/sandboxes/define?json=1",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "SepticDirectoryDeployer/1.0"
        },
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    sandbox_id = data["sandbox_id"]
    live_url = f"https://{sandbox_id}.csb.app"
    with open(LIVE_URL_PATH, "w", encoding="utf-8") as f:
        f.write(live_url + "\n")
    print(f"[OK] Deployed {len(files)} files to {live_url}")
    return live_url


if __name__ == "__main__":
    deploy()
