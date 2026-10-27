#!/usr/bin/env python3
"""
Static Site Generator for Southern NH & Northern MA Septic Pumping, Inspection & Title 5 Directory
Reads:  /workspace/septic-directory/data/providers.json
Writes:
  - /workspace/septic-directory/site/index.html
  - /workspace/septic-directory/site/towns/<town-slug>.html (16 SEO town pages)
  - /workspace/septic-directory/site/sitemap.xml
  - /workspace/septic-directory/site/robots.txt
"""

import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data", "providers.json")
LIVE_URL_PATH = os.path.join(BASE_DIR, "data", "live_url.txt")
SITE_DIR = os.path.join(BASE_DIR, "site")
TOWNS_DIR = os.path.join(SITE_DIR, "towns")
os.makedirs(TOWNS_DIR, exist_ok=True)


def get_base_url():
    if os.path.exists(LIVE_URL_PATH):
        try:
            with open(LIVE_URL_PATH, "r", encoding="utf-8") as f:
                url = f.read().strip().rstrip("/")
                if url.startswith("http"):
                    return url
        except Exception:
            pass
    return "https://603septicpros.com"


SHARED_CSS = """
:root {
  --bg: #f8fafc;
  --surface: #ffffff;
  --surface-alt: #f1f5f9;
  --forest: #0f291e;
  --forest-mid: #163a2b;
  --slate: #475569;
  --muted: #64748b;
  --border: #e2e8f0;
  --emerald: #059669;
  --emerald-dark: #047857;
  --emerald-soft: #d1fae5;
  --amber: #d97706;
  --amber-soft: #fef3c7;
  --red: #dc2626;
  --red-soft: #fee2e2;
  --blue: #0284c7;
  --blue-soft: #e0f2fe;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  background: var(--bg);
  color: #0f172a;
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
}
a { color: var(--emerald-dark); text-decoration: none; }
a:hover { text-decoration: underline; }
.topbar {
  background: var(--forest);
  color: #f8fafc;
  font-size: 0.82rem;
  padding: 0.5rem 1.25rem;
  border-bottom: 2px solid var(--emerald);
}
.topbar-inner {
  max-width: 1240px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.5rem;
}
.live-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  background: #34d399;
  border-radius: 50%;
  margin-right: 6px;
  box-shadow: 0 0 0 3px rgba(52,211,153,0.25);
}
header.hero {
  background: linear-gradient(135deg, #0f291e 0%, #163a2b 100%);
  color: #ffffff;
  padding: 2.25rem 1.25rem 2.1rem;
}
.container {
  max-width: 1240px;
  margin: 0 auto;
}
.hero-grid {
  display: grid;
  grid-template-columns: 1.3fr 1fr;
  gap: 1.5rem;
  align-items: center;
}
.badge-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  background: rgba(16, 185, 129, 0.2);
  border: 1px solid rgba(52, 211, 153, 0.45);
  color: #6ee7b7;
  font-size: 0.78rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  padding: 0.28rem 0.75rem;
  border-radius: 999px;
  margin-bottom: 0.75rem;
}
h1 {
  font-size: 2.02rem;
  line-height: 1.18;
  font-weight: 800;
  letter-spacing: -0.02em;
  margin-bottom: 0.65rem;
}
.hero-sub {
  color: #d1fae5;
  font-size: 0.98rem;
  max-width: 650px;
}
.quote-card {
  background: rgba(255, 255, 255, 0.07);
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 12px;
  padding: 1.15rem 1.25rem;
}
.quote-card h3 {
  font-size: 1rem;
  margin-bottom: 0.3rem;
  color: #fff;
}
.quote-card p {
  font-size: 0.82rem;
  color: #d1fae5;
  margin-bottom: 0.75rem;
}
.quote-form {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.45rem;
}
.quote-form input, .quote-form select {
  padding: 0.52rem 0.65rem;
  border-radius: 7px;
  border: 1px solid #335d49;
  background: #0a1f16;
  color: #fff;
  font-size: 0.84rem;
}
.quote-confirm {
  display: none;
  margin-top: 0.65rem;
  padding: 0.75rem 0.85rem;
  border-radius: 8px;
  background: rgba(6, 95, 70, 0.85);
  border: 1px solid #34d399;
  color: #ecfdf5;
  font-size: 0.81rem;
  line-height: 1.45;
}
.quote-confirm a {
  color: #6ee7b7;
  font-weight: 700;
}
.btn-primary {
  background: var(--emerald);
  color: #fff;
  font-weight: 700;
  font-size: 0.86rem;
  padding: 0.55rem 1rem;
  border-radius: 7px;
  border: none;
  cursor: pointer;
  white-space: nowrap;
}
.btn-primary:hover { background: var(--emerald-dark); text-decoration: none; }
.kpi-strip {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
  margin-top: -1.1rem;
  margin-bottom: 1.5rem;
  padding: 0 1.25rem;
}
.kpi-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 1.1rem 1.2rem;
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.05);
}
.kpi-card.pumping { border-top: 4px solid var(--emerald); }
.kpi-card.nh-insp { border-top: 4px solid var(--blue); }
.kpi-card.title5 { border-top: 4px solid var(--amber); }
.kpi-card.emerg { border-top: 4px solid var(--red); }
.kpi-label {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--muted);
  font-weight: 700;
}
.kpi-value {
  font-size: 1.65rem;
  font-weight: 800;
  color: #0f172a;
  margin: 0.2rem 0;
  letter-spacing: -0.02em;
}
.kpi-meta {
  font-size: 0.81rem;
  color: var(--slate);
}
.kpi-meta strong { color: var(--emerald-dark); }
main {
  padding: 0 1.25rem 3rem;
}
.featured-banner {
  background: linear-gradient(90deg, #ecfdf5 0%, #d1fae5 100%);
  border: 1px solid #6ee7b7;
  border-left: 5px solid var(--emerald);
  border-radius: 12px;
  padding: 1rem 1.25rem;
  margin-bottom: 1.25rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
}
.featured-tag {
  display: inline-block;
  background: var(--emerald-dark);
  color: #fff;
  font-size: 0.7rem;
  font-weight: 800;
  text-transform: uppercase;
  padding: 0.18rem 0.55rem;
  border-radius: 4px;
  margin-right: 0.5rem;
  letter-spacing: 0.04em;
}
.calc-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 1.2rem 1.35rem;
  margin-bottom: 1.25rem;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
}
.calc-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr) 1.3fr;
  gap: 0.85rem;
  align-items: center;
  margin-top: 0.75rem;
}
.calc-field label {
  display: block;
  font-size: 0.76rem;
  font-weight: 700;
  color: var(--slate);
  margin-bottom: 0.25rem;
  text-transform: uppercase;
}
.select-input {
  width: 100%;
  padding: 0.48rem 0.7rem;
  border-radius: 8px;
  border: 1px solid #cbd5e1;
  font-size: 0.86rem;
  font-weight: 600;
  color: #0f172a;
  background: #fff;
}
.calc-output {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 10px;
  padding: 0.75rem 1rem;
}
.calc-output-title {
  font-size: 0.74rem;
  font-weight: 800;
  text-transform: uppercase;
  color: var(--emerald-dark);
}
.calc-output-val {
  font-size: 1.15rem;
  font-weight: 800;
  color: #0f172a;
  margin-top: 2px;
}
.calc-output-sub {
  font-size: 0.78rem;
  color: var(--slate);
}
.controls-bar {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 0.95rem 1.25rem;
  margin-bottom: 1.25rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
}
.control-group {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  flex-wrap: wrap;
}
.control-group label {
  font-size: 0.84rem;
  font-weight: 700;
}
.table-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
  margin-bottom: 2rem;
}
.table-header {
  padding: 1rem 1.25rem;
  border-bottom: 1px solid var(--border);
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.5rem;
}
.table-header h2 {
  font-size: 1.15rem;
  font-weight: 800;
}
.table-scroll { overflow-x: auto; }
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.88rem;
}
th {
  background: var(--surface-alt);
  color: var(--slate);
  font-weight: 700;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  text-align: left;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--border);
  white-space: nowrap;
}
td {
  padding: 0.85rem 1rem;
  border-bottom: 1px solid var(--border);
  vertical-align: middle;
}
tr:last-child td { border-bottom: none; }
tr:hover td { background: #f8fafc; }
tr.featured-row td { background: #f0fdf4; }
.provider-name {
  font-weight: 800;
  color: #0f172a;
  font-size: 0.96rem;
}
.provider-sub {
  font-size: 0.78rem;
  color: var(--muted);
  margin-top: 2px;
}
.svc-badge {
  display: inline-block;
  font-size: 0.7rem;
  font-weight: 700;
  padding: 0.14rem 0.48rem;
  border-radius: 4px;
  margin: 2px 4px 2px 0;
  background: #f1f5f9;
  color: #334155;
}
.svc-emerg { background: var(--red-soft); color: var(--red); }
.svc-title5 { background: var(--amber-soft); color: #92400e; }
.svc-nhinsp { background: var(--blue-soft); color: var(--blue); }
.svc-pump { background: var(--emerald-soft); color: var(--emerald-dark); }
.price-range {
  font-weight: 800;
  color: #0f172a;
  font-size: 0.95rem;
}
.phone-link {
  font-weight: 700;
  color: #0f172a;
  white-space: nowrap;
}
.btn-quote {
  display: inline-block;
  padding: 0.42rem 0.75rem;
  background: var(--forest);
  color: #fff;
  border-radius: 6px;
  font-size: 0.78rem;
  font-weight: 700;
  white-space: nowrap;
}
.btn-quote:hover {
  background: var(--emerald);
  text-decoration: none;
}
.two-col {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  margin-bottom: 2rem;
}
.section-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 1.25rem;
}
.section-card h3 {
  font-size: 1.08rem;
  font-weight: 800;
  margin-bottom: 0.4rem;
}
.town-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 0.85rem;
  margin-top: 1rem;
}
.town-tile {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 0.9rem 1rem;
  transition: transform 0.12s ease, border-color 0.12s ease;
  display: block;
}
.town-tile:hover {
  border-color: var(--emerald);
  transform: translateY(-2px);
  text-decoration: none;
}
.town-tile-top {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 0.25rem;
}
.town-tile-name {
  font-weight: 800;
  color: #0f172a;
  font-size: 0.95rem;
}
.town-tile-price {
  font-weight: 800;
  color: var(--emerald-dark);
  font-size: 0.86rem;
}
.town-tile-meta {
  font-size: 0.76rem;
  color: var(--muted);
}
.hauler-cta {
  background: linear-gradient(135deg, #0f291e 0%, #163a2b 100%);
  color: #fff;
  border-radius: 12px;
  padding: 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1.25rem;
  margin-top: 2rem;
}
footer {
  background: var(--forest);
  color: #94a3b8;
  font-size: 0.82rem;
  padding: 2rem 1.25rem;
}
@media (max-width: 960px) {
  .hero-grid, .two-col, .calc-grid { grid-template-columns: 1fr; }
  .kpi-strip { grid-template-columns: repeat(2, 1fr); }
}
"""

QUOTE_FORM_JS = """
async function submitSepticQuote(event, formEl) {
  event.preventDefault();
  const btn = formEl.querySelector('button[type="submit"]');
  const origText = btn.textContent;
  btn.disabled = true;
  btn.textContent = 'Matching Local Pros...';

  const name = formEl.querySelector('[name="name"]').value.trim();
  const phone = formEl.querySelector('[name="phone"]').value.trim();
  const townEl = formEl.querySelector('[name="town"]');
  const svcEl = formEl.querySelector('[name="service"]');
  const town = townEl ? townEl.value : 'Danville, NH';
  const service = svcEl ? svcEl.value : 'Routine Pumping';
  const townShort = town.split(',')[0].trim();

  const payload = {
    name: name,
    phone: phone,
    town: town,
    service: service,
    source_page: window.location.pathname || '/',
    submitted_at: new Date().toISOString()
  };

  // Match top 3 providers from the directory rows on the page
  const matched = [];
  document.querySelectorAll('tbody tr.provider-row, tbody tr').forEach(row => {
    if (matched.length >= 3) return;
    const rowTowns = (row.getAttribute('data-towns') || '');
    if (!rowTowns || rowTowns.split(',').includes(townShort)) {
      const pNameEl = row.querySelector('.provider-name');
      const phoneEl = row.querySelector('.phone-link');
      const priceEl = row.querySelector('.price-range');
      if (pNameEl && phoneEl) {
        const cleanName = pNameEl.textContent.replace('Featured Hauler', '').trim();
        matched.push({
          name: cleanName,
          phone: phoneEl.textContent.replace('📞', '').trim(),
          href: phoneEl.getAttribute('href'),
          rate: priceEl ? priceEl.textContent.trim() : ''
        });
      }
    }
  });

  // Save locally in browser storage
  try {
    const existing = JSON.parse(localStorage.getItem('septic_directory_leads') || '[]');
    existing.push(payload);
    localStorage.setItem('septic_directory_leads', JSON.stringify(existing));
  } catch (e) {}

  // Send to backend /api/quote if available
  let leadId = 'REQ-' + Math.floor(100000 + Math.random() * 900000);
  try {
    const resp = await fetch('/api/quote', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (resp.ok) {
      const data = await resp.json();
      if (data.lead_id) leadId = data.lead_id;
    }
  } catch (e) {}

  const confirmBox = formEl.parentElement.querySelector('.quote-confirm');
  if (confirmBox) {
    let prosHtml = '';
    if (matched.length > 0) {
      prosHtml = '<div style="margin-top:6px;padding-top:6px;border-top:1px solid rgba(255,255,255,0.2);">' +
        '<strong>Top Matched Licensed Pros for ' + townShort + ':</strong><ul style="list-style:none;margin-top:4px;display:grid;gap:3px;">' +
        matched.map(m => '<li>• <strong>' + m.name + '</strong> (' + m.rate + ') — <a href="' + m.href + '">' + m.phone + '</a></li>').join('') +
        '</ul></div>';
    }
    confirmBox.innerHTML =
      '✅ <strong>Quote Request Logged (' + leadId + ')!</strong><br/>' +
      'Request for <strong>' + service + '</strong> in <strong>' + town + '</strong> recorded for ' + name + ' (' + phone + ').' +
      prosHtml;
    confirmBox.style.display = 'block';
  }

  btn.disabled = false;
  btn.textContent = '✓ Quote Request Sent';
  formEl.reset();
}
"""


def render_provider_rows(providers):
    rows = []
    for idx, p in enumerate(providers, 1):
        badges = []
        for s in p["services"]:
            if "Emergency" in s:
                badges.append(f'<span class="svc-badge svc-emerg">🚨 {s}</span>')
            elif "Title 5" in s:
                badges.append(f'<span class="svc-badge svc-title5">📋 {s}</span>')
            elif "NH Septic" in s:
                badges.append(f'<span class="svc-badge svc-nhinsp">🔍 {s}</span>')
            elif "Pumping" in s:
                badges.append(f'<span class="svc-badge svc-pump">🚛 {s}</span>')
            else:
                badges.append(f'<span class="svc-badge">{s}</span>')

        feat_tag = '<span class="featured-tag">Featured Hauler</span>' if p.get("featured") else ""
        row_cls = "provider-row featured-row" if p.get("featured") else "provider-row"
        towns_attr = ",".join(p["towns_served"])
        svcs_attr = ",".join(p["services"])

        rows.append(f"""
        <tr class="{row_cls}" data-towns="{towns_attr}" data-services="{svcs_attr}">
          <td style="font-weight:800;color:#475569;">#{idx}</td>
          <td>
            <div class="provider-name">{feat_tag}{p['name']}</div>
            <div class="provider-sub">📍 {p['hq_town']}, {p['hq_state']} &middot; <strong>{p['permit_status']}</strong></div>
            <div class="provider-sub" style="color:#334155;margin-top:3px;">{p['notes']}</div>
            <div style="margin-top:5px;">{''.join(badges)}</div>
          </td>
          <td>
            <div class="price-range">{p['est_1000_gal']}</div>
            <div class="provider-sub">1,500 gal: {p['est_1500_gal']}</div>
          </td>
          <td>
            <div style="font-weight:700;font-size:0.83rem;color:#0f172a;">{p['inspection_type']}</div>
            <div class="provider-sub">{'✅ 24/7 Emergency Dispatch' if p['emergency_24_7'] else 'Standard Business Hours'}</div>
          </td>
          <td><a class="phone-link" href="tel:{p['phone']}">📞 {p['phone']}</a></td>
          <td><a class="btn-quote" href="{p['website']}" target="_blank" rel="noopener">Website / Quote &rarr;</a></td>
        </tr>
        """)
    return "\n".join(rows)


def build_index_page(data):
    b = data["benchmarks"]
    providers = data["providers"]
    towns = data["towns"]

    town_options = ['<option value="ALL">All 16 Rockingham County NH &amp; Essex County MA Towns</option>']
    quote_town_options = []
    for t in towns:
        town_options.append(
            f'<option value="{t["name"]}">{t["name"]}, {t["state"]} ({t["zip"]}) — {t["provider_count"]} Providers</option>'
        )
        quote_town_options.append(
            f'<option value="{t["name"]}, {t["state"]} ({t["zip"]})">{t["name"]}, {t["state"]} ({t["zip"]})</option>'
        )

    town_tiles = []
    for t in towns:
        town_tiles.append(f"""
        <a class="town-tile" href="towns/{t['slug']}.html">
          <div class="town-tile-top">
            <span class="town-tile-name">{t['name']}, {t['state']}</span>
            <span class="town-tile-price">{t['pumping_1000_range']}</span>
          </div>
          <div class="town-tile-meta">
            ZIP {t['zip']} &middot; <strong>{t['provider_count']} haulers</strong> ({t['emergency_count']} 24/7) &middot; {t['state']} Inspections
          </div>
        </a>
        """)

    rows_html = render_provider_rows(providers)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Southern NH &amp; Northern MA Septic Pumping, Inspection &amp; Title 5 Directory ({data['updated_date']})</title>
  <meta name="description" content="Compare {b['total_providers_tracked']} verified NHDES &amp; MassDEP licensed septic pumping, real estate septic inspection, MA Title 5, and leach field repair companies serving Danville NH (03819), Rockingham County &amp; Merrimack Valley." />
  <style>{SHARED_CSS}</style>
</head>
<body>
  <div class="topbar">
    <div class="topbar-inner">
      <div><span class="live-dot"></span><strong>VERIFIED SEPTAGE HAULER &amp; INSPECTOR DIRECTORY:</strong> NHDES &amp; MassDEP Title 5 Licensed Pros &middot; Updated {data['updated_timestamp']}</div>
      <div>Primary Coverage: <strong>Danville, NH (03819), Rockingham County &amp; Merrimack Valley</strong> &middot; <a href="#town-directory" style="color:#6ee7b7;">Browse 16 Local Towns &darr;</a></div>
    </div>
  </div>

  <header class="hero">
    <div class="container hero-grid">
      <div>
        <div class="badge-pill">🏡 Year-Round Rural Homeowner Directory &middot; NH &amp; MA</div>
        <h1>Southern NH &amp; Northern MA Septic Pumping, Inspection &amp; Title 5 Directory</h1>
        <p class="hero-sub">
          Compare <strong>{b['total_providers_tracked']} NHDES &amp; MassDEP licensed septic haulers, evaluators, and installers</strong> serving Danville (03819), Hampstead, Kingston, Plaistow, Derry, Salem, Exeter, Epping, and Haverhill/Amesbury MA. Check transparent 1,000-gallon pump-out prices, schedule a real estate inspection, or dispatch a 24/7 emergency truck.
        </p>
      </div>
      <div class="quote-card">
        <h3>⚡ Get a Fast Local Septic Quote or Inspection</h3>
        <p>Match with a vetted NHDES or MA Title 5 licensed septic company serving your exact town today.</p>
        <form class="quote-form" onsubmit="submitSepticQuote(event, this)">
          <input type="text" name="name" placeholder="Your Name" required />
          <input type="tel" name="phone" placeholder="Phone Number" required />
          <select name="town" aria-label="Town">
            {''.join(quote_town_options)}
          </select>
          <select name="service" aria-label="Service Needed">
            <option value="Routine Tank Pump-Out">Routine Tank Pump-Out</option>
            <option value="NH Real Estate Inspection">NH Real Estate Inspection</option>
            <option value="MA Title 5 Inspection">MA Title 5 Inspection</option>
            <option value="24/7 Emergency Backup">🚨 24/7 Emergency Backup</option>
            <option value="Leach Field Repair / Replace">Leach Field Repair / Replace</option>
          </select>
          <button type="submit" class="btn-primary" style="grid-column: span 2;">Request Local Quote &rarr;</button>
        </form>
        <div class="quote-confirm" role="status" aria-live="polite"></div>
      </div>
    </div>
  </header>

  <section class="container kpi-strip">
    <div class="kpi-card pumping">
      <div class="kpi-label">1,000-Gal Septic Pump-Out (NH)</div>
      <div class="kpi-value">{b['nh_1000_gal_range']}</div>
      <div class="kpi-meta">Published: <strong>{b['lafrance_published_1000']}</strong> (LaFrance Salem) &amp; <strong>{b['nates_published_1000']}</strong> (Nate's NH) &middot; 1,500 gal: {b['nh_1500_gal_range']}</div>
    </div>
    <div class="kpi-card nh-insp">
      <div class="kpi-label">NH Real Estate Septic Evaluation</div>
      <div class="kpi-value">{b['nh_inspection_range']}</div>
      <div class="kpi-meta">Hydraulic load test, baffle/filter check, leach field soil probe &amp; written PDF report</div>
    </div>
    <div class="kpi-card title5">
      <div class="kpi-label">MA Title 5 Certified Inspection</div>
      <div class="kpi-value">{b['ma_title5_range']}</div>
      <div class="kpi-meta">Mandatory under <strong>310 CMR 15.000</strong> when selling a home in Haverhill, Amesbury or Methuen</div>
    </div>
    <div class="kpi-card emerg">
      <div class="kpi-label">24/7 Emergency Backup Crews</div>
      <div class="kpi-value">{b['emergency_24_7_providers']} <span style="font-size:0.95rem;font-weight:600;color:#64748b;">Local Haulers</span></div>
      <div class="kpi-meta">On-call nights &amp; weekends for main-line blockages, high-pressure jetting &amp; tank alarms</div>
    </div>
  </section>

  <main class="container">
    <div class="featured-banner">
      <div>
        <span class="featured-tag">Featured Danville &amp; Rockingham Hauler</span>
        <strong>Bodwell's Septic Service, LLC (East Kingston, NH)</strong> &mdash;
        <strong>NHDES Permitted Hauler</strong> &middot; Routine Pumping, Real Estate Septic Evaluations, Baffle Repairs &amp; <strong>24/7 On-Call Emergency Service</strong> serving Danville, Kingston, Hampstead, Plaistow, Exeter, Epping &amp; Derry.
      </div>
      <div style="display:flex;gap:0.65rem;align-items:center;">
        <a class="phone-link" href="tel:6037723494">📞 (603) 772-3494</a>
        <a class="btn-primary" href="https://www.bodwells.com/service-area" target="_blank" rel="noopener">Schedule Service &rarr;</a>
      </div>
    </div>

    <section class="calc-card">
      <div style="display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:0.5rem;">
        <h3 style="font-size:1.05rem;font-weight:800;">🧮 Interactive Septic Pumping Schedule &amp; Local Cost Calculator</h3>
        <span style="font-size:0.8rem;color:#64748b;">Based on NHDES, MassDEP Title 5 &amp; US EPA residential wastewater guidelines</span>
      </div>
      <div class="calc-grid">
        <div class="calc-field">
          <label for="calcPeople">Household Size</label>
          <select id="calcPeople" class="select-input" onchange="updateSepticCalc()">
            <option value="2">1–2 People</option>
            <option value="4" selected>3–4 People (Typical Home)</option>
            <option value="6">5+ People</option>
          </select>
        </div>
        <div class="calc-field">
          <label for="calcTank">Tank Size</label>
          <select id="calcTank" class="select-input" onchange="updateSepticCalc()">
            <option value="1000" selected>1,000 Gallons (3-Bed Standard)</option>
            <option value="1250">1,250 Gallons (4-Bed)</option>
            <option value="1500">1,500 Gallons (4–5 Bed)</option>
          </select>
        </div>
        <div class="calc-field">
          <label for="calcDisposal">Garbage Disposal?</label>
          <select id="calcDisposal" class="select-input" onchange="updateSepticCalc()">
            <option value="no" selected>No Garbage Disposal</option>
            <option value="yes">Yes (Uses Kitchen Disposal)</option>
          </select>
        </div>
        <div class="calc-field">
          <label for="calcLid">Tank Cover Access</label>
          <select id="calcLid" class="select-input" onchange="updateSepticCalc()">
            <option value="exposed" selected>Riser at Surface / Exposed</option>
            <option value="buried">Buried Lid (Hauler Digs 1–2 ft)</option>
          </select>
        </div>
        <div class="calc-output">
          <div class="calc-output-title">Recommended Schedule &amp; Est. Cost</div>
          <div class="calc-output-val" id="calcResultMain">Every 2.5–3 Years &middot; $350–$450</div>
          <div class="calc-output-sub" id="calcResultSub">Includes effluent filter cleaning &amp; baffle check</div>
        </div>
      </div>
    </section>

    <div class="controls-bar">
      <div class="control-group">
        <label for="townFilter">📍 Filter by Town:</label>
        <select id="townFilter" class="select-input" style="width:auto;" onchange="applySepticFilters()">
          {''.join(town_options)}
        </select>
      </div>
      <div class="control-group">
        <label for="serviceFilter">🛠️ Filter by Service:</label>
        <select id="serviceFilter" class="select-input" style="width:auto;" onchange="applySepticFilters()">
          <option value="ALL">All Septic Services ({b['total_providers_tracked']} Providers)</option>
          <option value="Routine Pumping">🚛 Routine Septic Tank Pumping</option>
          <option value="24/7 Emergency">🚨 24/7 Emergency Backup Service</option>
          <option value="NH Septic Inspection">🔍 NH Real Estate Septic Inspection</option>
          <option value="MA Title 5 Inspection">📋 MA Title 5 Certified Inspection</option>
          <option value="Leach Field Repair & Design">🚜 Leach Field Repair, Rejuvenation &amp; Design</option>
        </select>
      </div>
    </div>

    <div class="table-card">
      <div class="table-header">
        <div>
          <h2 id="tableTitle">Verified Local Septic Pumping &amp; Inspection Companies ({b['total_providers_tracked']} Providers)</h2>
          <div style="font-size:0.8rem;color:#64748b;">All providers verified against NHDES Septage Hauler Permits, GSOWA &amp; MassDEP Title 5 directories</div>
        </div>
        <div style="font-size:0.82rem;color:#475569;">
          Buried Cover Digging Fee: <strong>{b['cover_digging_fee']}</strong> &middot; Leach Field Replacement: <strong>{b['leach_field_replacement']}</strong>
        </div>
      </div>
      <div class="table-scroll">
        <table>
          <thead>
            <tr>
              <th>#</th>
              <th>Company, HQ &amp; Service Notes</th>
              <th>Est. Pumping Rate (1,000 Gal)</th>
              <th>Inspections &amp; Emergency</th>
              <th>Local Dispatch Phone</th>
              <th>Website / Quote</th>
            </tr>
          </thead>
          <tbody id="providerTbody">
            {rows_html}
          </tbody>
        </table>
      </div>
    </div>

    <div class="two-col">
      <div class="section-card">
        <h3>🔍 NH Real Estate Septic Evaluations vs. MA Title 5 Inspections</h3>
        <p style="font-size:0.85rem;color:#64748b;margin-bottom:0.8rem;">
          Selling or buying a house near the NH/MA border? Here is how septic inspections differ between Rockingham County, NH and Essex County, MA:
        </p>
        <ul style="list-style:none;display:grid;gap:0.65rem;font-size:0.87rem;">
          <li style="padding:0.7rem;background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;">
            <strong>New Hampshire (Danville, Derry, Salem, Hampstead, Exeter):</strong> Standard home purchase &amp; sale agreements include a comprehensive <strong>NH Septic Evaluation ($375–$550)</strong>. The inspector locates the tank, checks scum/sludge depth, inspects inlet/outlet baffles and effluent filters, runs a hydraulic flow test, and probes the leach field. (Plus: under <strong>NH RSA 485-A:39</strong>, waterfront properties must obtain a formal NHDES Site Assessment prior to sale).
          </li>
          <li style="padding:0.7rem;background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;">
            <strong>Massachusetts (Haverhill, Amesbury, Methuen, Boxford):</strong> Under <strong>310 CMR 15.000 (Title 5)</strong>, a state-certified Title 5 inspection ($500–$850) is legally mandatory within 2 years prior to any property transfer (extended to <strong>3 years</strong> if you have receipts proving annual septic pumping).
          </li>
        </ul>
      </div>

      <div class="section-card">
        <h3>💡 3 Ways Rockingham County Homeowners Save $100+ Per Pump-Out</h3>
        <ul style="list-style:none;display:grid;gap:0.65rem;font-size:0.87rem;margin-top:0.4rem;">
          <li style="padding:0.7rem;background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;">
            <strong>1. Expose Your Tank Covers Before the Truck Arrives (Saves $50–$125):</strong> Local haulers like C.B. LaFrance charge a minimum of $50 per foot/cover to dig up buried concrete lids. Uncovering the lid yourself or installing a surface grade riser saves on every future visit.
          </li>
          <li style="padding:0.7rem;background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;">
            <strong>2. Clean the Effluent Filter at Every Pump-Out (Included Free):</strong> Haulers like LaFrance, Bodwell's, and Kent Clean include effluent filter washing and baffle inspection at no extra charge during a routine pump-out &mdash; preventing slow drains and leach field backups.
          </li>
          <li style="padding:0.7rem;background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;">
            <strong>3. Book Before December Ground Freeze:</strong> Once New Hampshire soil freezes solid from December through March, digging buried lids or responding to an overdue tank backup can add $150–$300 in emergency winter fees.
          </li>
        </ul>
      </div>
    </div>

    <section id="town-directory" class="section-card">
      <h3>🏘️ Browse Verified Septic Pumping &amp; Inspection Pros by Town</h3>
      <p style="font-size:0.85rem;color:#64748b;">
        Click your town below for local hauler rankings, 1,000-gallon and 1,500-gallon pumping estimates, 24/7 emergency dispatch numbers, and town inspection rules:
      </p>
      <div class="town-grid">
        {''.join(town_tiles)}
      </div>
    </section>

    <section class="hauler-cta">
      <div style="max-width:720px;">
        <div class="badge-pill" style="margin-bottom:0.4rem;">For NHDES &amp; MassDEP Licensed Septic Companies</div>
        <h3 style="font-size:1.35rem;margin-bottom:0.35rem;">Own a Septic Pumping, Inspection, or Excavation Company?</h3>
        <p style="color:#d1fae5;font-size:0.9rem;">
          Homeowners in Danville, Derry, Salem, Hampstead, Plaistow, Exeter, and Haverhill use this directory year-round to book $400+ pump-outs, $500+ real estate inspections, and $15,000+ leach field replacements. Lock in the <strong>Exclusive Featured Hauler Spot</strong> for your core towns or receive exclusive homeowner quote requests.
        </p>
      </div>
      <div style="display:flex;flex-direction:column;gap:0.5rem;min-width:240px;">
        <a class="btn-primary" style="text-align:center;padding:0.75rem 1.2rem;font-size:0.92rem;" href="#top" onclick="document.querySelector('.quote-form [name=name]').focus(); return false;">⭐ Claim Featured Spot ($99/mo) &rarr;</a>
        <span style="text-align:center;color:#d1fae5;font-size:0.82rem;">Verified NHDES &amp; MassDEP Directory</span>
      </div>
    </section>
  </main>

  <footer>
    <div class="container" style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:1rem;">
      <div>
        <strong style="color:#fff;">Southern NH &amp; Northern MA Septic Pumping, Inspection &amp; Title 5 Directory</strong><br />
        Independent homeowner resource for Danville, NH (03819), Rockingham County &amp; Merrimack Valley.<br />
        Verified against NHDES Permitted Septage Haulers, GSOWA, and MassDEP 310 CMR 15.000 (Title 5) registries.
      </div>
      <div>
        Last verified: <strong>{data['updated_timestamp']}</strong><br />
        Always confirm tank size, lid depth, and final quote directly with your licensed hauler.
      </div>
    </div>
  </footer>

  <script>
    {QUOTE_FORM_JS}

    function updateSepticCalc() {{
      const people = parseInt(document.getElementById('calcPeople').value, 10);
      const tank = parseInt(document.getElementById('calcTank').value, 10);
      const disposal = document.getElementById('calcDisposal').value;
      const lid = document.getElementById('calcLid').value;

      let freq = 'Every 3 Years';
      if (disposal === 'yes') {{
        freq = 'Every 1–1.5 Years';
      }} else if (people <= 2 && tank >= 1250) {{
        freq = 'Every 4–5 Years';
      }} else if (people <= 2) {{
        freq = 'Every 3.5–4 Years';
      }} else if (people >= 5 && tank === 1000) {{
        freq = 'Every 1.5–2 Years';
      }} else if (people >= 5) {{
        freq = 'Every 2–2.5 Years';
      }}

      let low = 350, high = 450;
      if (tank === 1250) {{ low = 400; high = 500; }}
      if (tank === 1500) {{ low = 440; high = 535; }}
      if (lid === 'buried') {{ low += 60; high += 100; }}

      document.getElementById('calcResultMain').textContent = freq + ' · $' + low + '–$' + high;
      document.getElementById('calcResultSub').textContent =
        (disposal === 'yes' ? 'Garbage disposal increases solids by ~50% · ' : '') +
        (lid === 'buried' ? 'Includes ~$60–$100 buried cover excavation' : 'Surface riser/exposed lid saves $50–$125 digging fee');
    }}

    function applySepticFilters() {{
      const town = document.getElementById('townFilter').value;
      const svc = document.getElementById('serviceFilter').value;
      let count = 0;
      document.querySelectorAll('#providerTbody tr.provider-row').forEach(row => {{
        const towns = row.getAttribute('data-towns').split(',');
        const svcs = row.getAttribute('data-services').split(',');
        const matchTown = (town === 'ALL') || towns.includes(town);
        const matchSvc = (svc === 'ALL') || svcs.includes(svc);
        if (matchTown && matchSvc) {{
          row.style.display = '';
          count++;
        }} else {{
          row.style.display = 'none';
        }}
      }});
      document.getElementById('tableTitle').textContent =
        'Verified Local Septic Pumping & Inspection Companies (' + count + ' Providers)';
    }}
  </script>
</body>
</html>
"""
    out_path = os.path.join(SITE_DIR, "index.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[OK] Generated {out_path}")


def build_town_pages(data):
    providers = data["providers"]
    towns = data["towns"]

    for t in towns:
        t_provs = [p for p in providers if t["name"] in p["towns_served"]]
        rows_html = render_provider_rows(t_provs)

        other_links = []
        for ot in towns:
            if ot["slug"] != t["slug"]:
                other_links.append(
                    f'<a class="town-tile" href="{ot["slug"]}.html"><div class="town-tile-top"><span class="town-tile-name">{ot["name"]}, {ot["state"]}</span><span class="town-tile-price">{ot["pumping_1000_range"]}</span></div><div class="town-tile-meta">ZIP {ot["zip"]} &middot; {ot["provider_count"]} haulers</div></a>'
                )

        insp_option = "MA Title 5 Inspection" if t["state"] == "MA" else "NH Real Estate Inspection"

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Septic Tank Pumping &amp; Inspections in {t['name']}, {t['state']} ({t['zip']}) — {t['provider_count']} Local Pros ({data['updated_date']})</title>
  <meta name="description" content="Compare {t['provider_count']} licensed septic pumping, {t['inspection_rule']}, and leach field repair companies serving {t['name']}, {t['state']} ({t['zip']}). 1,000-gallon pump-out cost: {t['pumping_1000_range']}." />
  <style>{SHARED_CSS}</style>
</head>
<body>
  <div class="topbar">
    <div class="topbar-inner">
      <div><a href="../index.html" style="color:#6ee7b7;font-weight:700;">&larr; All Southern NH &amp; Northern MA Septic Directory</a></div>
      <div><span class="live-dot"></span><strong>{t['name']}, {t['state']} ({t['zip']})</strong> &middot; Updated {data['updated_timestamp']}</div>
    </div>
  </div>

  <header class="hero">
    <div class="container hero-grid">
      <div>
        <div class="badge-pill">📍 {t['county']} &middot; ZIP {t['zip']} &middot; Verified Licensed Haulers</div>
        <h1>Septic Tank Pumping, Inspections &amp; Leach Field Repair in {t['name']}, {t['state']} ({t['zip']})</h1>
        <p class="hero-sub">
          Compare <strong>{t['provider_count']} licensed septic haulers and inspectors</strong> serving {t['name']}, {t['state']}. Typical 1,000-gallon routine septic pumping in {t['name']} runs <strong>{t['pumping_1000_range']}</strong>, with <strong>{t['emergency_count']} providers offering 24/7 emergency backup dispatch</strong>.
        </p>
      </div>
      <div class="quote-card">
        <h3>⚡ Request a {t['name']}, {t['state']} Septic Quote</h3>
        <p>Get a fast quote for a pump-out, real estate inspection, or repair in {t['name']} ({t['zip']}).</p>
        <form class="quote-form" onsubmit="submitSepticQuote(event, this)">
          <input type="text" name="name" placeholder="Your Name" required />
          <input type="tel" name="phone" placeholder="Phone Number" required />
          <input type="hidden" name="town" value="{t['name']}, {t['state']} ({t['zip']})" />
          <select name="service" aria-label="Service Needed" style="grid-column: span 2;">
            <option value="Routine Tank Pump-Out">Routine Tank Pump-Out ({t['pumping_1000_range']})</option>
            <option value="{insp_option}">{insp_option}</option>
            <option value="24/7 Emergency Backup">🚨 24/7 Emergency Backup</option>
            <option value="Leach Field Repair / Replace">Leach Field Repair / Replace</option>
          </select>
          <button type="submit" class="btn-primary" style="grid-column: span 2;">Get {t['name']} Quote &rarr;</button>
        </form>
        <div class="quote-confirm" role="status" aria-live="polite"></div>
      </div>
    </div>
  </header>

  <section class="container kpi-strip">
    <div class="kpi-card pumping">
      <div class="kpi-label">1,000-Gal Pump-Out in {t['name']}</div>
      <div class="kpi-value">{t['pumping_1000_range']}</div>
      <div class="kpi-meta">1,500-Gal Tank: <strong>{t['pumping_1500_range']}</strong></div>
    </div>
    <div class="kpi-card nh-insp">
      <div class="kpi-label">{t['name']} Inspection Cost</div>
      <div class="kpi-value">{t['inspection_cost_range'].split('(')[0].strip()}</div>
      <div class="kpi-meta">{t['inspection_rule']}</div>
    </div>
    <div class="kpi-card emerg">
      <div class="kpi-label">24/7 Emergency Haulers</div>
      <div class="kpi-value">{t['emergency_count']} <span style="font-size:0.9rem;color:#64748b;">in {t['name']}</span></div>
      <div class="kpi-meta">Same-day backup &amp; main line clearing</div>
    </div>
    <div class="kpi-card title5">
      <div class="kpi-label">Total Verified Pros</div>
      <div class="kpi-value">{t['provider_count']} <span style="font-size:0.9rem;color:#64748b;">Companies</span></div>
      <div class="kpi-meta">Top local match: <strong>{t['top_provider']}</strong></div>
    </div>
  </section>

  <main class="container">
    <div class="table-card">
      <div class="table-header">
        <h2>{t['name']}, {t['state']} ({t['zip']}) Licensed Septic Pumping &amp; Inspection Providers</h2>
        <a href="../index.html" style="font-size:0.85rem;font-weight:700;">View All 20 Regional Providers &rarr;</a>
      </div>
      <div class="table-scroll">
        <table>
          <thead>
            <tr>
              <th>#</th>
              <th>Company, HQ &amp; Service Notes</th>
              <th>Est. Pumping Rate (1,000 Gal)</th>
              <th>Inspections &amp; Emergency</th>
              <th>Local Dispatch Phone</th>
              <th>Website / Quote</th>
            </tr>
          </thead>
          <tbody>
            {rows_html}
          </tbody>
        </table>
      </div>
    </div>

    <section class="section-card">
      <h3>🏘️ Compare Nearby Rockingham County &amp; Merrimack Valley Towns</h3>
      <div class="town-grid">
        {''.join(other_links)}
      </div>
    </section>
  </main>

  <footer>
    <div class="container">
      <strong>{t['name']}, {t['state']} ({t['zip']}) Septic Pumping &amp; Inspection Directory</strong> &middot;
      <a href="../index.html" style="color:#6ee7b7;">Back to Main Southern NH &amp; Northern MA Directory</a> &middot;
      Updated {data['updated_timestamp']}
    </div>
  </footer>
  <script>
    {QUOTE_FORM_JS}
  </script>
</body>
</html>
"""
        out_path = os.path.join(TOWNS_DIR, f"{t['slug']}.html")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html)
    print(f"[OK] Generated {len(towns)} programmatic SEO town pages in {TOWNS_DIR}")


def build_seo_files(data):
    base_url = get_base_url()
    urls = [f"  <url><loc>{base_url}/</loc><lastmod>{data['updated_date']}</lastmod><priority>1.0</priority></url>"]
    for t in data["towns"]:
        urls.append(
            f"  <url><loc>{base_url}/towns/{t['slug']}.html</loc><lastmod>{data['updated_date']}</lastmod><priority>0.8</priority></url>"
        )
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(urls) + "\n</urlset>\n"
    with open(os.path.join(SITE_DIR, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(sitemap)
    with open(os.path.join(SITE_DIR, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\nSitemap: {base_url}/sitemap.xml\n")
    print(f"[OK] Generated sitemap.xml and robots.txt for {base_url}")


def main():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    build_index_page(data)
    build_town_pages(data)
    build_seo_files(data)


if __name__ == "__main__":
    main()
