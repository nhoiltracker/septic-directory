#!/usr/bin/env python3
"""
Deploy /workspace/septic-directory/site to GitHub Pages
(https://nhoiltracker.github.io/septic-directory/)
"""
import os
import shutil
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SITE_DIR = os.path.join(BASE_DIR, "site")
DOCS_DIR = os.path.join(BASE_DIR, "docs")
LIVE_URL = "https://nhoiltracker.github.io/septic-directory"

def deploy():
    if os.path.exists(DOCS_DIR):
        shutil.rmtree(DOCS_DIR)
    shutil.copytree(SITE_DIR, DOCS_DIR)
    with open(os.path.join(DOCS_DIR, ".nojekyll"), "w") as f:
        f.write("")
    with open(os.path.join(BASE_DIR, "data", "live_url.txt"), "w") as f:
        f.write(LIVE_URL + "\n")
    subprocess.run(["git", "add", "-A"], cwd=BASE_DIR, check=False)
    subprocess.run(["git", "commit", "-m", "Update Septic Directory live site"], cwd=BASE_DIR, check=False)
    subprocess.run(["git", "push", "origin", "main"], cwd=BASE_DIR, check=False)
    print(f"[OK] Deployed to {LIVE_URL}/")

if __name__ == "__main__":
    deploy()
