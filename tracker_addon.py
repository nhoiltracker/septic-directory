#!/usr/bin/env python3
"""
Visit & Hauler-Click Tracker + Live Analytics Dashboard (stats.html)
+ FAQ JSON-LD + Sponsor Claim Modal for Southern NH & Northern MA Septic Directory.
Zero personal names or personal emails anywhere.
"""
import json
import os
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SITE_DIR = os.path.join(BASE_DIR, "site")
TOWNS_DIR = os.path.join(SITE_DIR, "towns")
DATA_PATH = os.path.join(BASE_DIR, "data", "providers.json")

TRACKER_SNIPPET = """
<!-- Visit & Hauler-Click Tracker + Live Analytics Bar -->
<style>
  .tracker-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    background: rgba(16, 185, 129, 0.16);
    border: 1px solid rgba(110, 231, 183, 0.4);
    color: #ecfdf5;
    padding: 0.22rem 0.65rem;
    border-radius: 999px;
    font-size: 0.76rem;
    font-weight: 700;
    text-decoration: none;
  }
  .tracker-pill:hover { background: rgba(16, 185, 129, 0.28); text-decoration: none; }
  .faq-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.85rem; margin-top: 0.75rem; }
  .faq-item { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 0.85rem 1rem; }
  .faq-item h4 { font-size: 0.92rem; color: #0f172a; margin-bottom: 0.3rem; }
  .faq-item p { font-size: 0.84rem; color: #475569; margin: 0; }
  @media (max-width: 820px) { .faq-grid { grid-template-columns: 1fr; } }
</style>
<script>
(function() {
  const STORAGE_KEY = 'septic_dir_analytics_v1';
  const VISITOR_KEY = 'septic_dir_visitor_id';
  const SESSION_KEY = 'septic_dir_session_counted';
  const CounterNS = 'nhmasepticdirectory2026';

  function getVisitorId() {
    try {
      let vid = localStorage.getItem(VISITOR_KEY);
      if (!vid) {
        vid = 'v_' + Math.random().toString(36).slice(2, 10) + '_' + Date.now().toString(36);
        localStorage.setItem(VISITOR_KEY, vid);
      }
      return vid;
    } catch (e) { return 'v_anon'; }
  }

  function loadStats() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) return JSON.parse(raw);
    } catch (e) {}
    return {
      total_views: 0,
      unique_visitors: 1,
      calc_runs: 0,
      quote_submits: 0,
      pages: {},
      towns: {},
      providers: {},
      events: []
    };
  }

  function saveStats(st) {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(st)); } catch (e) {}
  }

  function currentPageSlug() {
    const p = window.location.pathname || '/';
    if (p.indexOf('/towns/') !== -1) {
      return p.split('/towns/')[1].replace('.html', '') || 'town';
    }
    if (p.indexOf('stats.html') !== -1) return 'stats';
    return 'home';
  }

  function recordEvent(type, detail) {
    const st = loadStats();
    const slug = currentPageSlug();
    if (type === 'pageview') {
      st.total_views = (st.total_views || 0) + 1;
      st.pages[slug] = (st.pages[slug] || 0) + 1;
      if (slug !== 'home' && slug !== 'stats') {
        st.towns[slug] = (st.towns[slug] || 0) + 1;
      }
    } else if (type === 'calc') {
      st.calc_runs = (st.calc_runs || 0) + 1;
    } else if (type === 'quote') {
      st.quote_submits = (st.quote_submits || 0) + 1;
    } else if (type === 'provider_click' && detail && detail.provider) {
      const pName = detail.provider;
      if (!st.providers[pName]) st.providers[pName] = { calls: 0, websites: 0, total: 0 };
      if (detail.kind === 'call') st.providers[pName].calls += 1;
      else st.providers[pName].websites += 1;
      st.providers[pName].total += 1;
    }
    st.events = st.events || [];
    st.events.unshift({
      ts: new Date().toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'}),
      date: new Date().toLocaleDateString(),
      type: type,
      page: slug,
      detail: detail || {}
    });
    if (st.events.length > 40) st.events = st.events.slice(0, 40);
    saveStats(st);

    // Also post to local /api/track when reachable
    fetch('/api/track', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        event_type: type,
        page: window.location.pathname || '/',
        town: (detail && detail.town) || slug,
        provider_id: (detail && detail.provider_id) || '',
        provider_name: (detail && detail.provider) || '',
        visitor_id: getVisitorId()
      })
    }).catch(function() {});

    // Sync global visit counter via CounterAPI
    if (type === 'pageview') {
      fetch('https://api.counterapi.dev/v1/' + CounterNS + '/pageviews/up')
        .then(function(r) { return r.json(); })
        .then(function(d) {
          if (d && typeof d.count === 'number') {
            try { localStorage.setItem('septic_global_views', String(d.count)); } catch (e) {}
            updateLiveBadges(d.count, st);
          }
        })
        .catch(function() {
          updateLiveBadges(null, st);
        });
    } else {
      updateLiveBadges(null, st);
    }
  }

  function updateLiveBadges(remoteCount, st) {
    const storedGlobal = parseInt(localStorage.getItem('septic_global_views') || '0', 10);
    const views = Math.max(remoteCount || 0, storedGlobal, st.total_views || 1);
    document.querySelectorAll('[data-live-views]').forEach(function(el) {
      el.textContent = views.toLocaleString() + ' Live Visits';
    });
  }

  window.septicTracker = { recordEvent: recordEvent, loadStats: loadStats };

  document.addEventListener('DOMContentLoaded', function() {
    recordEvent('pageview', { path: window.location.pathname });

    // Attach click tracking to all phone & website links
    document.querySelectorAll('a.phone-link, a.btn-quote, .featured-banner a').forEach(function(a) {
      a.addEventListener('click', function() {
        const row = a.closest('tr');
        let provName = 'Bodwell\\'s Septic Service, LLC';
        if (row) {
          const nameEl = row.querySelector('.provider-name');
          if (nameEl) provName = nameEl.textContent.replace('Featured Hauler', '').trim();
        }
        const isCall = (a.getAttribute('href') || '').indexOf('tel:') === 0;
        recordEvent('provider_click', {
          provider: provName,
          kind: isCall ? 'call' : 'website',
          href: a.getAttribute('href') || ''
        });
      });
    });

    // Hook calculator changes
    ['calcPeople', 'calcTank', 'calcDisposal', 'calcLid'].forEach(function(id) {
      const el = document.getElementById(id);
      if (el) {
        el.addEventListener('change', function() {
          recordEvent('calc', { tank: (document.getElementById('calcTank') || {}).value });
        });
      }
    });

    // Hook quote form submit
    document.querySelectorAll('form.quote-form').forEach(function(f) {
      f.addEventListener('submit', function() {
        const townInput = f.querySelector('[name="town"]');
        const svcInput = f.querySelector('[name="service"]');
        recordEvent('quote', {
          town: townInput ? townInput.value : '',
          service: svcInput ? svcInput.value : ''
        });
      });
    });
  });
})();
</script>
"""

FAQ_SECTION_HTML = """
    <section class="section-card" id="septic-faq">
      <h3>❓ Frequently Asked Questions: NH &amp; Northern MA Septic Pumping &amp; Inspections</h3>
      <div class="faq-grid">
        <div class="faq-item">
          <h4>How much does it cost to pump a 1,000-gallon septic tank in Southern NH?</h4>
          <p>In Danville, Derry, Salem, Hampstead, Kingston, and Exeter NH, routine 1,000-gallon septic pumping averages <strong>$350 to $450</strong> (1,500-gallon tanks run $440–$535). C.B. LaFrance publishes a flat $420 rate up to 1,000–1,500 gallons.</p>
        </div>
        <div class="faq-item">
          <h4>Is a septic inspection required when selling a home in NH vs. Massachusetts?</h4>
          <p>In <strong>Massachusetts (Haverhill, Amesbury, Methuen)</strong>, a certified <strong>Title 5 inspection ($500–$850)</strong> is required by law under 310 CMR 15.000 within 2 years of closing. In <strong>New Hampshire</strong>, home buyers order a standard <strong>NH Real Estate Septic Evaluation ($375–$550)</strong>, and waterfront properties require an NHDES Site Assessment under RSA 485-A:39.</p>
        </div>
        <div class="faq-item">
          <h4>How often should a septic tank be pumped in Rockingham County?</h4>
          <p>NHDES and the EPA recommend pumping a 1,000-gallon tank serving 3–4 people <strong>every 2.5 to 3 years</strong>. Homes using a kitchen garbage disposal should pump every 1.5–2 years because ground food waste increases tank solids by up to 50%.</p>
        </div>
        <div class="faq-item">
          <h4>How can I avoid paying the $50–$125 buried lid digging fee?</h4>
          <p>Uncover your concrete septic tank access covers before the pumper truck arrives, or ask your hauler to install a flush PVC surface riser ($350–$600 one-time retrofit) so your lids never have to be dug up again.</p>
        </div>
      </div>
    </section>
"""

FAQ_JSON_LD = """
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "How much does it cost to pump a 1,000-gallon septic tank in Southern NH?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "In Danville, Derry, Salem, Hampstead, Kingston, and Exeter NH, routine 1,000-gallon septic pumping averages $350 to $450, while 1,500-gallon tanks average $440 to $535."
      }
    },
    {
      "@type": "Question",
      "name": "Is a septic inspection required when selling a home in NH vs. Massachusetts?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "In Massachusetts (Haverhill, Amesbury, Methuen), a state-certified Title 5 inspection ($500-$850) is mandatory under 310 CMR 15.000 within 2 years of a home sale. In New Hampshire, buyers typically order an NH Real Estate Septic Evaluation ($375-$550), and waterfront homes require an NHDES Site Assessment under NH RSA 485-A:39."
      }
    },
    {
      "@type": "Question",
      "name": "How often should a residential septic tank be pumped?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "For a standard 3-bedroom home with a 1,000-gallon septic tank and 3 to 4 occupants, NHDES and EPA guidelines recommend pumping every 2.5 to 3 years."
      }
    }
  ]
}
</script>
"""


def build_stats_page(data, css):
    towns = data["towns"]
    providers = data["providers"]
    town_rows = "\n".join([
        f'<tr><td><a href="towns/{t["slug"]}.html"><strong>{t["name"]}, {t["state"]}</strong> ({t["zip"]})</a></td><td>{t["provider_count"]} Pros</td><td id="town-stat-{t["slug"]}">0</td></tr>'
        for t in towns
    ])
    prov_rows = "\n".join([
        f'<tr data-prov-name="{p["name"]}"><td><strong>{p["name"]}</strong> ({p["hq_town"]}, {p["hq_state"]})</td><td class="p-calls">0</td><td class="p-webs">0</td><td class="p-total" style="font-weight:800;color:#047857;">0</td></tr>'
        for p in providers[:12]
    ])

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Live Visit &amp; Hauler Click Tracker — Southern NH &amp; Northern MA Septic Directory</title>
  <meta name="description" content="Live visitor analytics, town page traffic, calculator usage, and septic hauler call/website click tracking for the Southern NH &amp; Northern MA Septic Directory." />
  <style>{css}</style>
</head>
<body>
  <div class="topbar">
    <div class="topbar-inner">
      <div><a href="index.html" style="color:#6ee7b7;font-weight:700;">&larr; Back to Main Septic Directory</a></div>
      <div><span class="live-dot"></span><strong>Live Directory Visit &amp; Lead Tracker</strong> &middot; <span data-live-views>Live Visits</span></div>
    </div>
  </div>

  <header class="hero" style="padding:1.8rem 0 2.2rem;">
    <div class="container">
      <div class="badge-pill">📊 Real-Time Directory Traffic &amp; Sponsor Lead Attribution</div>
      <h1>Live Visit, Town Traffic &amp; Hauler Click Tracker</h1>
      <p class="hero-sub">
        Track homeowner visits across all 16 Rockingham County NH &amp; Northern MA town pages, pumping calculator runs, quote requests, and outbound phone/website clicks to each licensed septic company.
      </p>
    </div>
  </header>

  <section class="container kpi-strip" style="margin-top:-1.4rem;">
    <div class="kpi-card pumping">
      <div class="kpi-label">Total Directory Visits</div>
      <div class="kpi-value" id="statTotalViews">1</div>
      <div class="kpi-meta">Synced across live session &amp; global counter</div>
    </div>
    <div class="kpi-card nh-insp">
      <div class="kpi-label">Hauler Call &amp; Website Clicks</div>
      <div class="kpi-value" id="statProviderClicks">0</div>
      <div class="kpi-meta">Direct outbound homeowner leads to haulers</div>
    </div>
    <div class="kpi-card title5">
      <div class="kpi-label">Pumping Calculator Runs</div>
      <div class="kpi-value" id="statCalcRuns">0</div>
      <div class="kpi-meta">Interactive cost &amp; schedule estimates</div>
    </div>
    <div class="kpi-card emerg">
      <div class="kpi-label">Homeowner Quote Requests</div>
      <div class="kpi-value" id="statQuoteSubmits">0</div>
      <div class="kpi-meta">Routed via <a href="mailto:603septicpros@mail.grokbot.com">603septicpros@mail.grokbot.com</a></div>
    </div>
  </section>

  <main class="container">
    <div class="two-col">
      <div class="table-card" style="margin-bottom:0;">
        <div class="table-header">
          <h2>📞 Hauler Call &amp; Website Click Leaderboard</h2>
          <span style="font-size:0.78rem;color:#64748b;">Proof of leads for $99/mo Featured Sponsors</span>
        </div>
        <div class="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Septic Company</th>
                <th>Phone Clicks</th>
                <th>Website Clicks</th>
                <th>Total Leads</th>
              </tr>
            </thead>
            <tbody id="provStatTbody">
              {prov_rows}
            </tbody>
          </table>
        </div>
      </div>

      <div class="table-card" style="margin-bottom:0;">
        <div class="table-header">
          <h2>🏘️ Visits by Town Page (16 Towns)</h2>
          <span style="font-size:0.78rem;color:#64748b;">Rockingham County NH &amp; Essex County MA</span>
        </div>
        <div class="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Town Page</th>
                <th>Listed Haulers</th>
                <th>Tracked Views</th>
              </tr>
            </thead>
            <tbody>
              {town_rows}
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <div class="section-card">
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:0.5rem;margin-bottom:0.65rem;">
        <h3 style="margin:0;">🕒 Recent Tracked Visitor &amp; Lead Activity</h3>
        <button class="btn-quote" onclick="refreshStatsDashboard()" style="cursor:pointer;">🔄 Refresh Live Counts</button>
      </div>
      <div id="recentEventsBox" style="font-size:0.84rem;color:#334155;display:grid;gap:0.4rem;">
        <div>Loading live visitor events...</div>
      </div>
    </div>
  </main>

  <footer>
    <div class="container" style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:1rem;">
      <div>
        <strong style="color:#fff;">Southern NH &amp; Northern MA Septic Directory — Analytics</strong><br />
        Sponsor &amp; Partner Inquiries: <a href="mailto:603septicpros@mail.grokbot.com" style="color:#6ee7b7;">603septicpros@mail.grokbot.com</a>
      </div>
      <div>
        <a href="index.html" style="color:#6ee7b7;font-weight:700;">&larr; Return to Main Directory</a>
      </div>
    </div>
  </footer>
  {TRACKER_SNIPPET}
  <script>
    function refreshStatsDashboard() {{
      const st = (window.septicTracker && window.septicTracker.loadStats()) || {{}};
      const globalViews = parseInt(localStorage.getItem('septic_global_views') || '0', 10);
      const totalViews = Math.max(globalViews, st.total_views || 1);
      document.getElementById('statTotalViews').textContent = totalViews.toLocaleString();
      document.getElementById('statCalcRuns').textContent = (st.calc_runs || 0).toLocaleString();

      let quotesCount = st.quote_submits || 0;
      try {{
        const savedLeads = JSON.parse(localStorage.getItem('septic_directory_leads') || '[]');
        quotesCount = Math.max(quotesCount, savedLeads.length);
      }} catch (e) {{}}
      document.getElementById('statQuoteSubmits').textContent = quotesCount.toLocaleString();

      let totalProvClicks = 0;
      const provMap = st.providers || {{}};
      document.querySelectorAll('#provStatTbody tr').forEach(function(row) {{
        const name = row.getAttribute('data-prov-name');
        const rec = provMap[name] || {{ calls: 0, websites: 0, total: 0 }};
        row.querySelector('.p-calls').textContent = rec.calls || 0;
        row.querySelector('.p-webs').textContent = rec.websites || 0;
        row.querySelector('.p-total').textContent = rec.total || 0;
        totalProvClicks += (rec.total || 0);
      }});
      document.getElementById('statProviderClicks').textContent = totalProvClicks.toLocaleString();

      const townMap = st.towns || {{}};
      Object.keys(townMap).forEach(function(slug) {{
        const cell = document.getElementById('town-stat-' + slug);
        if (cell) cell.textContent = townMap[slug];
      }});

      const evBox = document.getElementById('recentEventsBox');
      const evs = st.events || [];
      if (evs.length === 0) {{
        evBox.innerHTML = '<div>No recent events recorded in this browser yet. Browse a town page or click a hauler to test!</div>';
      }} else {{
        evBox.innerHTML = evs.slice(0, 12).map(function(e) {{
          return '<div style="padding:0.45rem 0.7rem;background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;">' +
            '<strong>' + e.ts + '</strong> &middot; <span style="color:#047857;font-weight:700;">' + e.type.toUpperCase() + '</span> &middot; Page: <code>' + e.page + '</code> ' +
            (e.detail && e.detail.provider ? ('&rarr; <strong>' + e.detail.provider + '</strong> (' + e.detail.kind + ')') : '') +
          '</div>';
        }}).join('');
      }}

      // Also merge from local server /api/stats if running
      fetch('/api/stats').then(function(r) {{ return r.json(); }}).then(function(srv) {{
        if (srv && srv.total_views) {{
          document.getElementById('statTotalViews').textContent = Math.max(totalViews, srv.total_views).toLocaleString();
        }}
      }}).catch(function() {{}});
    }}
    document.addEventListener('DOMContentLoaded', function() {{
      setTimeout(refreshStatsDashboard, 150);
    }});
  </script>
</body>
</html>
"""
    out = os.path.join(SITE_DIR, "stats.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[OK] Generated {out}")


def inject_into_site():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Extract SHARED_CSS from index.html
    idx_path = os.path.join(SITE_DIR, "index.html")
    with open(idx_path, "r", encoding="utf-8") as f:
        idx_html = f.read()

    m = re.search(r"<style>(.*?)</style>", idx_html, re.S)
    css = m.group(1) if m else ""

    build_stats_page(data, css)

    # Inject live visit badge, FAQ section, sponsor email (603septicpros@mail.grokbot.com), FAQ JSON-LD, and tracker into index.html
    if "stats.html" not in idx_html:
        idx_html = idx_html.replace(
            'Browse 16 Local Towns &darr;</a>',
            'Browse 16 Local Towns &darr;</a> &middot; <a class="tracker-pill" href="stats.html">📊 <span data-live-views>Live Visits</span> &amp; Click Stats</a>'
        )
        idx_html = idx_html.replace(
            '<span style="text-align:center;color:#d1fae5;font-size:0.82rem;">Verified NHDES &amp; MassDEP Directory</span>',
            '<a style="text-align:center;color:#d1fae5;font-size:0.82rem;text-decoration:underline;" href="mailto:603septicpros@mail.grokbot.com?subject=Featured%20Hauler%20Spot%20($99/mo)">Email 603septicpros@mail.grokbot.com</a> &middot; <a style="text-align:center;color:#6ee7b7;font-size:0.8rem;" href="stats.html">View Live Traffic &amp; Call Clicks &rarr;</a>'
        )
        idx_html = idx_html.replace(
            '<section class="hauler-cta">',
            FAQ_SECTION_HTML + '\n    <section class="hauler-cta">'
        )
        idx_html = idx_html.replace("</head>", FAQ_JSON_LD + "\n</head>")
        idx_html = idx_html.replace("</body>", TRACKER_SNIPPET + "\n</body>")
        with open(idx_path, "w", encoding="utf-8") as f:
            f.write(idx_html)
        print("[OK] Injected Visit Tracker, FAQ Schema & Sponsor links into site/index.html")

    # Inject tracker and stats link into all 16 town pages
    for fname in sorted(os.listdir(TOWNS_DIR)):
        if not fname.endswith(".html"):
            continue
        p = os.path.join(TOWNS_DIR, fname)
        with open(p, "r", encoding="utf-8") as f:
            th = f.read()
        if "stats.html" not in th:
            th = th.replace(
                '</div>\n    </div>\n  </div>',
                ' &middot; <a class="tracker-pill" href="../stats.html">📊 <span data-live-views>Live Visits</span></a></div>\n    </div>\n  </div>',
                1
            )
            th = th.replace("</body>", TRACKER_SNIPPET + "\n</body>")
            with open(p, "w", encoding="utf-8") as f:
                f.write(th)
    print("[OK] Injected Visit Tracker into all 16 town pages")


if __name__ == "__main__":
    inject_into_site()
