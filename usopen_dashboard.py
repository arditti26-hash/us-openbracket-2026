#!/usr/bin/env python3
"""US Open 2026 Group Bracket Dashboard — scrapes served.bracket.tennis"""

import json, re, urllib.request, os, time
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timedelta
try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None

def _now_et():
    if ZoneInfo:
        return datetime.now(ZoneInfo('America/New_York'))
    return datetime.utcnow() - timedelta(hours=4)

PORT = int(os.environ.get('PORT', 8768))

# ── Edit your group members here ─────────────────────────────────────────────
MEMBERS = [
    'willarditti',
    'jackthesnack21',
    # add more served.bracket.tennis usernames here
]

COLORS = {
    0: {'primary': '#1a3a6e', 'bg': 'rgba(26,58,110,0.10)',   'border': 'rgba(26,58,110,0.22)'},
    1: {'primary': '#c8a020', 'bg': 'rgba(200,160,32,0.12)',  'border': 'rgba(200,160,32,0.28)'},
    2: {'primary': '#1a3a6e', 'bg': 'rgba(26,58,110,0.10)',   'border': 'rgba(26,58,110,0.22)'},
    3: {'primary': '#c8a020', 'bg': 'rgba(200,160,32,0.12)',  'border': 'rgba(200,160,32,0.28)'},
    4: {'primary': '#1a3a6e', 'bg': 'rgba(26,58,110,0.10)',   'border': 'rgba(26,58,110,0.22)'},
    5: {'primary': '#c8a020', 'bg': 'rgba(200,160,32,0.12)',  'border': 'rgba(200,160,32,0.28)'},
}

TOURNAMENT_SLUG = 'us-open-2026'
GROUP_SLUG      = 'serving-hot-takes'

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>US Open 2026</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,600;0,700;1,400&family=Playfair+Display:wght@700;900&display=swap" rel="stylesheet">
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --green:   #1a3a6e;
  --green2:  #1e4a8a;
  --green3:  #12285a;
  --purple:  #c8a020;
  --gold:    #c8a020;
  --cream:   #f0f4fa;
  --cream2:  #e4ecf7;
  --berry:   #c0392b;
  --bg:      #f5f2eb;
  --card:    #ffffff;
  --text:    #1a1a1a;
  --muted:   #6b6b6b;
  --border:  #ddd8cc;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
  background: var(--bg);
  background-image: repeating-linear-gradient(
    180deg,
    rgba(0, 80, 40, 0.022) 0px, rgba(0, 80, 40, 0.022) 24px,
    transparent 24px, transparent 48px
  );
  color: var(--text);
  min-height: 100vh;
}

/* ── TOP NAV BAR ── */
.topbar {
  background: var(--green3);
  color: #fff;
  padding: 0 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 48px;
  border-bottom: 3px solid var(--purple);
  position: sticky; top: 0; z-index: 20;
  gap: 8px;
}
.topbar-left { display: flex; align-items: center; gap: 6px; font-size: 0.75rem; font-family: sans-serif; opacity: 0.85; min-width: 0; }
.topbar-left span:last-child { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.topbar-flag { font-size: 1rem; flex-shrink: 0; }
.topbar-right { display: flex; align-items: center; gap: 6px; flex-shrink: 0; }
.live-badge {
  display: flex; align-items: center; gap: 6px;
  background: rgba(201,169,75,0.15); border: 1px solid rgba(201,169,75,0.4);
  padding: 4px 12px; border-radius: 100px;
  font-size: 11px; font-weight: 700; color: var(--gold); letter-spacing: 1px;
  font-family: sans-serif;
}
.live-dot { width: 6px; height: 6px; background: var(--gold); border-radius: 50%; animation: blink 1.5s ease-in-out infinite; }
@keyframes blink { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.4;transform:scale(0.7)} }

/* ── HERO HEADER ── */
.hero {
  background: linear-gradient(160deg, var(--green3) 0%, var(--green) 55%, var(--green2) 100%);
  color: #fff;
  text-align: center;
  padding: 22px 20px 20px;
  border-bottom: 4px solid var(--gold);
  position: relative;
  overflow: hidden;
}
.hero::before {
  content: '';
  position: absolute; inset: 0;
  background:
    repeating-linear-gradient(
      180deg,
      rgba(255,255,255,0.03) 0px, rgba(255,255,255,0.03) 18px,
      rgba(0,0,0,0.04) 18px, rgba(0,0,0,0.04) 36px
    ),
    radial-gradient(ellipse at 15% 50%, rgba(201,169,75,0.07) 0%, transparent 55%),
    radial-gradient(ellipse at 85% 50%, rgba(75,0,110,0.10) 0%, transparent 55%);
  pointer-events: none;
}
.hero-inner { position: relative; display: flex; align-items: center; justify-content: center; gap: 16px; flex-wrap: wrap; }
.hero-trophy { font-size: 2rem; filter: drop-shadow(0 2px 6px rgba(0,0,0,0.35)); flex-shrink: 0; }
.hero-text { text-align: left; }
.hero-title {
  font-family: 'Playfair Display', 'EB Garamond', Georgia, serif;
  font-size: 1.9rem; font-weight: 900; letter-spacing: 0.02em;
  line-height: 1.1; text-shadow: 0 2px 10px rgba(0,0,0,0.3);
}
.hero-title span { color: var(--gold); }
.hero-subtitle {
  font-family: 'EB Garamond', Georgia, serif;
  font-size: 0.88rem; font-style: italic; opacity: 0.72;
  letter-spacing: 0.06em; margin-top: 2px;
}
.hero-pills { display: flex; align-items: center; justify-content: center; gap: 8px; flex-wrap: wrap; margin-top: 14px; }
.hero-pill {
  background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.22);
  border-radius: 100px; padding: 4px 12px;
  font-size: 0.73rem; font-family: sans-serif; letter-spacing: 0.03em;
}
.hero-pill.gold { background: rgba(201,169,75,0.18); border-color: rgba(201,169,75,0.45); color: var(--gold); }

/* ── GRASS / STRAWBERRIES & CREAM ACCENT STRIP ── */
.sc-banner {
  background: linear-gradient(90deg, var(--cream) 0%, var(--cream2) 50%, var(--cream) 100%);
  border-bottom: 1px solid #e0d5b0;
  padding: 7px 12px;
  display: flex; align-items: center; justify-content: center; gap: 10px; flex-wrap: wrap;
  font-family: 'EB Garamond', Georgia, serif;
  font-size: 0.82rem; color: #5a3e1b; letter-spacing: 0.05em;
  text-align: center;
}
.sc-grass {
  display: flex; gap: 3px; align-items: flex-end;
}
.sc-grass span {
  display: inline-block; width: 3px; border-radius: 2px 2px 0 0;
  background: var(--green2); opacity: 0.7;
}
.sc-grass span:nth-child(1) { height: 10px; }
.sc-grass span:nth-child(2) { height: 14px; }
.sc-grass span:nth-child(3) { height: 9px; }
.sc-grass span:nth-child(4) { height: 13px; }
.sc-grass span:nth-child(5) { height: 11px; }
.sc-banner .berry { color: var(--berry); font-size: 1rem; }

/* ── MAIN ── */
.wrap { max-width: 880px; margin: 0 auto; padding: 28px 20px 60px; }

/* ── STATUS BAR ── */
.status-bar {
  display: flex; align-items: center; gap: 8px;
  font-size: 0.78rem; font-family: sans-serif; color: var(--muted);
  margin-bottom: 24px;
}
.sdot { width: 7px; height: 7px; border-radius: 50%; background: var(--gold); flex-shrink: 0; }

/* ── LEADERBOARD CARD ── */
.card {
  background: var(--card); border: 1px solid var(--border);
  border-radius: 14px; overflow: hidden; margin-bottom: 24px;
  box-shadow: 0 1px 6px rgba(0,0,0,0.07);
}
.card-header {
  padding: 16px 20px 13px; border-bottom: 1px solid var(--border);
  display: flex; align-items: center; justify-content: space-between;
}
.card-title {
  font-family: 'Playfair Display', 'EB Garamond', Georgia, serif;
  font-size: 1.1rem; font-weight: 700; color: var(--green);
}
.card-sub { font-size: 0.74rem; font-family: sans-serif; color: var(--muted); margin-top: 3px; }

/* ── TABLE ── */
.lb-table { width: 100%; border-collapse: collapse; font-family: sans-serif; table-layout: fixed; }
.lb-table th {
  text-align: center; padding: 8px 4px;
  font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.04em;
  color: var(--muted); border-bottom: 2px solid var(--border);
  background: var(--bg); white-space: nowrap; overflow: hidden;
}
.lb-table th:nth-child(1) { width: 28px; text-align: center; }
.lb-table th:nth-child(2) { width: 26%; text-align: left; }
.lb-table th:nth-child(3), .lb-table th:nth-child(4),
.lb-table th:nth-child(5), .lb-table th:nth-child(6) { width: 18.5%; }
.lb-table td {
  padding: 10px 4px; border-bottom: 1px solid var(--border);
  font-size: 0.82rem; vertical-align: middle; text-align: center;
  overflow: hidden;
}
.lb-table td:nth-child(1) { text-align: center; }
.lb-table td:nth-child(2) { text-align: left; overflow: hidden; }
.lb-table tr:last-child td { border-bottom: none; }
.lb-table tr:hover td { background: #f9f6ef; }

.rank-cell { color: var(--muted); font-size: 0.82rem; }
.rank-cell.gold { color: var(--gold); font-size: 1rem; }

/* ── PLAYER ROW STYLING ── */
.player-name {
  font-weight: 700; font-size: 0.95rem;
}
.name-link { text-decoration: none; }
.name-link:hover { text-decoration: underline; }

.score-pill {
  display: inline-block; padding: 3px 7px; border-radius: 14px;
  font-size: 0.78rem; font-weight: 700;
}
.pill-atp      { background: #e8f4ee; color: #1a6b3c; }
.pill-wta      { background: #f3e8f4; color: #6b1a6b; }
.pill-combined { background: #fff3dc; color: #7a5a00; }
.pill-none     { background: #f0f0f0; color: #aaa; }

.bar-wrap { margin-top: 5px; height: 3px; background: #e8e4dc; border-radius: 2px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 2px; transition: width 0.8s ease; }

/* ── SCORING RULES ── */
.rules-grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(110px, 1fr));
  gap: 10px; padding: 16px;
}
.rule-item {
  background: var(--bg); border-radius: 9px; padding: 11px 12px;
  text-align: center; border: 1px solid var(--border);
}
.rule-round { font-size: 0.68rem; font-family: sans-serif; color: var(--muted); text-transform: uppercase; letter-spacing: 0.04em; }
.rule-pts { font-size: 1.4rem; font-weight: 700; color: var(--green); font-family: 'EB Garamond', Georgia, serif; }
.rule-note { font-size: 0.66rem; font-family: sans-serif; color: var(--muted); margin-top: 2px; }
.rules-bonuses { padding: 0 16px 16px; display: flex; flex-wrap: wrap; gap: 8px; }
.bonus-tag {
  background: #fff8e6; border: 1px solid #e8d89a; border-radius: 7px;
  padding: 5px 11px; font-size: 0.77rem; font-family: sans-serif; color: #7a5a00;
}

/* ── EMPTY / ERROR ── */
.info-block {
  text-align: center; padding: 52px 20px; font-family: sans-serif; color: var(--muted);
}
.info-block .icon { font-size: 2.5rem; margin-bottom: 10px; }
.info-block h2 { font-size: 1.1rem; color: var(--green); margin-bottom: 6px; }
.info-block p { font-size: 0.88rem; line-height: 1.55; max-width: 360px; margin: 0 auto; }

.footer {
  text-align: center; font-family: sans-serif; font-size: 0.75rem;
  color: var(--muted); margin-top: 16px;
}

/* ── SETTINGS MODAL ── */
    #modal-overlay {
      display: none; position: fixed; inset: 0;
      background: rgba(0,0,0,0.45); z-index: 100;
      align-items: center; justify-content: center;
    }
    #modal-overlay.open { display: flex; }
    #modal {
      background: #fff; border-radius: 14px; width: 420px; max-width: 95vw;
      box-shadow: 0 8px 40px rgba(0,0,0,0.2); overflow: hidden;
    }
    .modal-header {
      background: var(--green); color: #fff; padding: 16px 20px;
      display: flex; align-items: center; justify-content: space-between;
    }
    .modal-header h2 { font-size: 1rem; font-family: sans-serif; }
    #modal-close { background: none; border: none; color: #fff; font-size: 1.4rem; cursor: pointer; line-height: 1; }
    .modal-body { padding: 20px; }
    .modal-body label { font-size: 0.8rem; font-family: sans-serif; color: var(--muted); display: block; margin-bottom: 6px; }
    .input-row { display: flex; gap: 8px; margin-bottom: 14px; }
    #username-input {
      flex: 1; border: 1px solid var(--border); border-radius: 7px;
      padding: 8px 12px; font-size: 0.9rem; font-family: sans-serif; outline: none;
    }
    #username-input:focus { border-color: var(--green); }
    #add-btn {
      background: var(--green); color: #fff; border: none; border-radius: 7px;
      padding: 8px 16px; cursor: pointer; font-size: 0.9rem; font-family: sans-serif;
    }
    #members-list { list-style: none; margin-bottom: 16px; max-height: 200px; overflow-y: auto; }
    #members-list li {
      display: flex; align-items: center; justify-content: space-between;
      padding: 8px 10px; border-radius: 7px; font-family: sans-serif; font-size: 0.88rem;
    }
    #members-list li:nth-child(odd) { background: var(--bg); }
    .remove-btn { background: none; border: none; color: #ef4444; cursor: pointer; font-size: 1rem; padding: 0 4px; }
    .modal-footer { border-top: 1px solid var(--border); padding: 14px 20px; display: flex; gap: 8px; flex-wrap: wrap; }
    #copy-btn, #save-btn {
      flex: 1; padding: 9px; border-radius: 8px; cursor: pointer;
      font-family: sans-serif; font-size: 0.88rem; border: none;
    }
    #copy-btn { background: var(--bg); border: 1px solid var(--border); color: var(--text); }
    #save-btn { background: var(--green); color: #fff; font-weight: 600; }
    .modal-hint { font-size: 0.72rem; font-family: sans-serif; color: var(--muted); width: 100%; text-align: center; }

    /* ── RESPONSIVE ── */
@media (max-width: 560px) {
  header { height: auto; padding: 12px 14px; flex-wrap: wrap; gap: 10px; }
}
</style>
</head>
<body>

<!-- TOP NAV -->
<div class="topbar">
  <div class="topbar-left">
    <span class="topbar-flag">🇬🇧</span>
    <span style="display:inline-flex;flex-direction:column;width:22px;height:14px;border-radius:2px;overflow:hidden;flex-shrink:0;box-shadow:0 1px 3px rgba(0,0,0,0.4);">
      <span style="flex:1;background:#1a3a6e;"></span>
      <span style="flex:1;background:#c8a020;"></span>
      <span style="flex:1;background:#1a3a6e;"></span>
      <span style="flex:1;background:#c8a020;"></span>
      <span style="flex:1;background:#1a3a6e;"></span>
    </span>
    <span>US Open 2026</span>
  </div>
  <div class="topbar-right">
    <div class="live-badge"><div class="live-dot"></div>LIVE</div>
    <button onclick="location.reload()" style="background:rgba(255,255,255,0.15);border:1px solid rgba(255,255,255,0.3);color:#fff;border-radius:6px;padding:5px 10px;cursor:pointer;font-size:0.75rem;font-family:sans-serif;white-space:nowrap;">↻ Refresh</button>
    <button onclick="copyInviteLink()" id="invite-btn" style="background:rgba(255,255,255,0.15);border:1px solid rgba(255,255,255,0.3);color:#fff;border-radius:6px;padding:5px 10px;cursor:pointer;font-size:0.75rem;font-family:sans-serif;white-space:nowrap;">🔗 Share</button>
    <button onclick="openModal()" style="background:rgba(255,255,255,0.15);border:1px solid rgba(255,255,255,0.3);color:#fff;border-radius:6px;padding:5px 10px;cursor:pointer;font-size:0.75rem;font-family:sans-serif;white-space:nowrap;">⚙ Group</button>
  </div>
</div>

<!-- HERO -->
<div class="hero">
  <div class="hero-inner">
    <div class="hero-trophy"><img src="https://upload.wikimedia.org/wikipedia/en/thumb/7/7e/US_Open_tennis_2022_logo.svg/250px-US_Open_tennis_2022_logo.svg.png" alt="US Open" style="height:60px;width:auto;filter:drop-shadow(0 2px 6px rgba(0,0,0,0.35));"></div>
    <div class="hero-text">
      <div class="hero-title">US Open <span>2026</span></div>
      <div class="hero-subtitle">The US Open · Flushing Meadows, New York</div>
    </div>
  </div>
  <div class="hero-pills">
    <span class="hero-pill">🎾 Men's &amp; Women's Draw</span>
    <span class="hero-pill gold">🏅 served.bracket.tennis</span>
  </div>
</div>

<!-- GRASS / S&C STRIP -->
<div class="sc-banner">
  <div class="sc-grass"><span></span><span></span><span></span><span></span><span></span></div>
  <span>🍈</span>
  <span>Page &amp; Will's US Open Challenge</span>
  <span>🍈</span>
  <div class="sc-grass"><span></span><span></span><span></span><span></span><span></span></div>
</div>

<!-- SETTINGS MODAL -->
<div id="modal-overlay" onclick="closeModalOutside(event)">
  <div id="modal">
    <div class="modal-header">
      <h2>⚙ Manage Group Members</h2>
      <button id="modal-close" onclick="closeModal()">✕</button>
    </div>
    <div class="modal-body">
      <label>Add a served.bracket.tennis username</label>
      <div class="input-row">
        <input id="username-input" type="text" placeholder="e.g. jackthesnack21"
          onkeydown="if(event.key==='Enter') addMember()" />
        <button id="add-btn" onclick="addMember()">Add</button>
      </div>
      <label>Group members (<span id="member-count">0</span>)</label>
      <ul id="members-list"></ul>
    </div>
    <div class="modal-footer">
      <button id="invite-btn" onclick="copyInviteLink()" style="width:100%;padding:10px;border-radius:8px;cursor:pointer;font-family:sans-serif;font-size:0.9rem;font-weight:600;border:none;background:#4b006e;color:#fff;margin-bottom:8px;">📋 Copy Invite Link</button>
      <button id="save-btn" onclick="saveAndClose()">Save &amp; Refresh</button>
      <div class="modal-hint">Share the invite link — anyone who opens it sees the full group</div>
    </div>
  </div>
</div>

<div class="wrap">
  <div class="status-bar">
    <div class="sdot"></div>
    <span id="status-text">Loading…</span>
  </div>

  <div class="card">
    <div class="card-header">
      <div>
        <div class="card-title">Combined Standings</div>
        <div class="card-sub">ATP + WTA · served.bracket.tennis</div>
      </div>
    </div>
    <div style="overflow-x:auto;-webkit-overflow-scrolling:touch;">
    <table class="lb-table" style="min-width:520px;width:100%;table-layout:fixed;">
      <thead>
        <tr>
          <th>#</th>
          <th>Player</th>
          <th>Combined</th>
          <th>Mens</th>
          <th>Womens</th>
          <th>Max Pts</th>
          <th>Global</th>
        </tr>
      </thead>
      <tbody id="lb-body">
        <tr><td colspan="7" style="padding:32px;text-align:center;color:#aaa;font-family:sans-serif">Loading…</td></tr>
      </tbody>
    </table>
    </div>
  </div>

  <!-- AI DAILY SUMMARY -->
  <div class="card" style="margin-bottom:24px;">
    <div class="card-header">
      <div>
        <div class="card-title">🎙 Today at the US Open</div>
        <div class="card-sub" id="summary-updated">Refreshes hourly</div>
      </div>
      <button onclick="loadSummary(true)" style="background:var(--bg);border:1px solid var(--border);color:var(--muted);border-radius:6px;padding:5px 12px;cursor:pointer;font-size:0.75rem;font-family:sans-serif;">↻ Refresh</button>
    </div>
    <div id="summary-body" style="padding:14px 20px;font-family:'EB Garamond',Georgia,serif;font-size:0.97rem;line-height:1.6;color:#2a2a2a;">
      <span style="color:#aaa;font-family:sans-serif;font-size:0.85rem;">Loading today's recap…</span>
    </div>
  </div>

  <script>
  (function(){
    window.loadSummary = function(bust) {
      var url = bust ? '/api/summary?bust=' + Date.now() : '/api/summary';
      fetch(url)
        .then(function(r){ return r.json(); })
        .then(function(data){
          var el = document.getElementById('summary-body');
          var upd = document.getElementById('summary-updated');
          if (data.error === 'no_key') {
            el.innerHTML = '<span style="color:#aaa;font-family:sans-serif;font-size:0.82rem;">Add <code style="background:#f0f0f0;padding:1px 5px;border-radius:3px;">ANTHROPIC_API_KEY</code> to Render environment variables to enable AI recaps.</span>';
          } else if (data.error) {
            el.innerHTML = '<span style="color:#aaa;font-family:sans-serif;font-size:0.82rem;">Recap unavailable — ' + data.error + '</span>';
          } else if (data.summary) {
            var text = data.summary;
            var html = text
              .replace(/WOMEN'S:/g, '<strong style="font-family:sans-serif;font-size:0.7rem;text-transform:uppercase;letter-spacing:0.08em;color:#6b1a6b;">Women\'s</strong><br>')
              .replace(/MEN'S:/g,   '<strong style="font-family:sans-serif;font-size:0.7rem;text-transform:uppercase;letter-spacing:0.08em;color:#00512e;margin-top:8px;display:block;">Men\'s</strong><br>');
            el.innerHTML = html;
            if (data.updated) upd.textContent = 'Updated · ' + data.updated;
          }
        })
        .catch(function(){});
    }
    window.loadSummary(false);
    setInterval(function(){ window.loadSummary(false); }, 60 * 60 * 1000);
  })();
  </script>

  <!-- LIVE BRACKET VISUALIZATION -->
  <div class="card" id="bracket-card" style="margin-bottom:24px;overflow:hidden;">
    <div class="card-header" style="margin-bottom:0;">
      <div>
        <div class="card-title">🎾 Live Bracket</div>
        <div class="card-sub">Real-time draw · served.bracket.tennis</div>
      </div>
      <div style="display:flex;gap:8px;align-items:center;">
        <button id="btn-atp" onclick="switchBracketTour('atp')"
          style="padding:6px 16px;border-radius:100px;border:2px solid #00512e;background:#00512e;color:#fff;font-size:0.78rem;font-weight:700;cursor:pointer;font-family:sans-serif;letter-spacing:0.5px;">
          Men's
        </button>
        <button id="btn-wta" onclick="switchBracketTour('wta')"
          style="padding:6px 16px;border-radius:100px;border:2px solid #ddd8cc;background:#fff;color:#4b006e;font-size:0.78rem;font-weight:700;cursor:pointer;font-family:sans-serif;letter-spacing:0.5px;">
          Women's
        </button>
        <a id="bracket-ext-link" href="https://served.bracket.tennis/tournaments/__SLUG__/atp/bracket"
           target="_blank" rel="noopener"
           style="padding:6px 12px;border-radius:100px;border:1px solid #ddd8cc;background:#f9f7f4;color:#6b6b6b;font-size:0.72rem;font-family:sans-serif;text-decoration:none;white-space:nowrap;">
          Full ↗
        </a>
      </div>
    </div>

    <!-- Single scrollable container: labels + bracket scroll together -->
    <div id="bracket-scroll" style="overflow-x:auto;overflow-y:auto;max-height:520px;background:#fafaf8;-webkit-overflow-scrolling:touch;">
      <div id="bracket-round-labels" style="display:flex;position:sticky;top:0;z-index:5;background:#f0ede6;border-bottom:1px solid #e8e4d8;">
      </div>
      <div id="bracket-body">
        <div style="padding:40px;text-align:center;color:#aaa;font-size:0.85rem;font-family:sans-serif;">Loading bracket…</div>
      </div>
    </div>
  </div>

  <script>
  (function(){
    var _bTour = 'atp';
    var _bCache = {};

    window.switchBracketTour = function(tour) {
      _bTour = tour;
      document.getElementById('btn-atp').style.background = tour === 'atp' ? '#00512e' : '#fff';
      document.getElementById('btn-atp').style.color = tour === 'atp' ? '#fff' : '#00512e';
      document.getElementById('btn-atp').style.borderColor = tour === 'atp' ? '#00512e' : '#ddd8cc';
      document.getElementById('btn-wta').style.background = tour === 'wta' ? '#4b006e' : '#fff';
      document.getElementById('btn-wta').style.color = tour === 'wta' ? '#fff' : '#4b006e';
      document.getElementById('btn-wta').style.borderColor = tour === 'wta' ? '#4b006e' : '#ddd8cc';
      document.getElementById('bracket-ext-link').href =
        'https://served.bracket.tennis/tournaments/__SLUG__/' + tour + '/bracket';
      loadBracket(tour);
    };

    function loadBracket(tour, bustCache) {
      var body = document.getElementById('bracket-body');
      var labelsEl = document.getElementById('bracket-round-labels');
      if (_bCache[tour] && !bustCache) { renderBracket(_bCache[tour], body, labelsEl); return; }
      var membersParam = (window._currentMembers && window._currentMembers.length)
        ? '&members=' + encodeURIComponent(window._currentMembers.join(',')) : '';
      fetch('/api/bracket?tour=' + tour + membersParam)
        .then(function(r){ return r.json(); })
        .then(function(data){
          _bCache[tour] = data;
          renderBracket(data, body, labelsEl);
        })
        .catch(function(e){
          if (!_bCache[tour])
            body.innerHTML = '<div style="padding:40px;text-align:center;color:#c0392b;font-size:0.85rem;font-family:sans-serif;">Could not load bracket.</div>';
        });
    }

    // Re-poll every 45 s to pick up live score/status changes
    setInterval(function(){ loadBracket(_bTour, true); }, 45000);

    var ROUND_LABELS = ['','R1','R2','R3','R4','QF','SF','F'];
    var ROUND_COLORS = {
      1:'#00512e', 2:'#006b3c', 3:'#007a45', 4:'#3a7d2e',
      5:'#7d5a00', 6:'#a0006b', 7:'#4b006e'
    };
    var COL_W = 162;  // px per round column (wider for flag + name)
    var ROW_H = 22;   // px per player row
    var TOTAL_H = 3200; // px — 64 R1 slots × 50px

    // ITF 3-letter → ISO 2-letter
    var ISO2 = {
      'USA':'US','GBR':'GB','ESP':'ES','FRA':'FR','GER':'DE','AUS':'AU',
      'ITA':'IT','SRB':'RS','RUS':'RU','ARG':'AR','CAN':'CA','CHN':'CN',
      'JPN':'JP','BEL':'BE','NED':'NL','SUI':'CH','DEN':'DK','NOR':'NO',
      'SWE':'SE','CZE':'CZ','POL':'PL','HUN':'HU','GRE':'GR','CRO':'HR',
      'BUL':'BG','ROU':'RO','UKR':'UA','KAZ':'KZ','BRA':'BR','CHI':'CL',
      'COL':'CO','MEX':'MX','RSA':'ZA','EGY':'EG','TUN':'TN','MAR':'MA',
      'KOR':'KR','TPE':'TW','IND':'IN','THA':'TH','MAS':'MY','SGP':'SG',
      'NZL':'NZ','AUT':'AT','SVK':'SK','SLO':'SI','FIN':'FI','POR':'PT',
      'MDA':'MD','LTU':'LT','LAT':'LV','EST':'EE','GEO':'GE','ARM':'AM',
      'AZE':'AZ','UZB':'UZ','BAH':'BS','ECU':'EC','PER':'PE','URU':'UY',
      'TUR':'TR','ISR':'IL','QAT':'QA','UAE':'AE','KUW':'KW','BLR':'BY',
      'CYP':'CY','LUX':'LU','MON':'MC','BIH':'BA','MKD':'MK','ALB':'AL',
      'PAK':'PK','VIE':'VN','PHI':'PH','INA':'ID','SRI':'LK','NEP':'NP',
      'CHI':'CL','PAR':'PY','VEN':'VE','BOL':'BO','DOM':'DO','PUR':'PR',
    };

    function countryFlag(code) {
      if (!code) return '';
      var c2 = ISO2[code] || (code.length === 2 ? code : null);
      if (!c2) return '';
      var o = 127397; // 0x1F1E6 - 65
      try {
        return String.fromCodePoint(c2.charCodeAt(0) + o, c2.charCodeAt(1) + o);
      } catch(e) { return ''; }
    }

    function lastName(name) {
      if (!name) return 'TBD';
      var parts = name.trim().split(' ');
      return parts[parts.length - 1];
    }

    function formatSetScore(score) {
      return (typeof score === 'string' && score.length) ? score : null;
    }

    function renderBracket(data, container, labelsEl) {
      var matches = data.matches || [];
      if (!matches.length) {
        container.innerHTML = '<div style="padding:40px;text-align:center;color:#aaa;font-size:0.85rem;font-family:sans-serif;">No bracket data yet.</div>';
        labelsEl.innerHTML = '';
        return;
      }

      // Build live-player lookup from ESPN overlay
      var liveSet = {};
      (data.live_players || []).forEach(function(n){ liveSet[n] = true; });
      var espnScores = data.espn_scores || {};

      // Group by round, sort by pos
      var rounds = {};
      var maxRound = 0;
      matches.forEach(function(m) {
        if (!rounds[m.round]) rounds[m.round] = [];
        rounds[m.round].push(m);
        if (m.round > maxRound) maxRound = m.round;
      });
      for (var r in rounds) rounds[r].sort(function(a,b){ return a.pos - b.pos; });

      // Build round labels bar (synced scroll with bracket body)
      labelsEl.innerHTML = '';
      labelsEl.style.display = 'flex';
      labelsEl.style.minWidth = (maxRound * (COL_W + 1)) + 'px';
      for (var rn = 1; rn <= maxRound; rn++) {
        var lbl = document.createElement('div');
        lbl.style.cssText = 'width:' + COL_W + 'px;flex-shrink:0;text-align:center;padding:5px 0 6px;font-size:0.7rem;font-weight:700;letter-spacing:1px;font-family:sans-serif;color:' + (ROUND_COLORS[rn] || '#333') + ';border-right:1px solid #e8e4d8;';
        lbl.textContent = ROUND_LABELS[rn] || ('R' + rn);
        labelsEl.appendChild(lbl);
      }

      // Build bracket
      var wrap = document.createElement('div');
      wrap.style.cssText = 'display:flex;height:' + TOTAL_H + 'px;';

      for (var rv = 1; rv <= maxRound; rv++) {
        var rMatches = rounds[rv] || [];
        var col = document.createElement('div');
        col.style.cssText = 'display:flex;flex-direction:column;width:' + COL_W + 'px;flex-shrink:0;border-right:1px solid #e8e4d8;';

        rMatches.forEach(function(m) {
          var isLive = !!m.is_live;
          var isComplete = !!m.winner;

          var slot = document.createElement('div');
          slot.style.cssText = 'flex:1;display:flex;align-items:center;padding:0 3px;';

          var card = document.createElement('div');
          card.style.cssText = 'width:100%;border-radius:4px;overflow:hidden;'
            + 'box-shadow:' + (isLive ? '0 0 0 2px #c0392b' : '0 1px 3px rgba(0,0,0,0.08)') + ';';

          [
            { name: m.p1, rank: m.p1_rank, country: m.p1_country },
            { name: m.p2, rank: m.p2_rank, country: m.p2_country }
          ].forEach(function(p, pi) {
            var isWinner = isComplete && m.winner === p.name;
            var isLoser  = isComplete && m.winner !== p.name && !!p.name;
            var isTbd    = !p.name;
            var playerLive = p.name && liveSet[p.name];

            var row = document.createElement('div');
            row.style.cssText = [
              'height:' + ROW_H + 'px',
              'line-height:' + ROW_H + 'px',
              'padding:0 5px',
              'font-size:10.5px',
              'overflow:hidden',
              'white-space:nowrap',
              'text-overflow:ellipsis',
              'font-family:sans-serif',
              'display:flex',
              'align-items:center',
              'justify-content:space-between',
              'border:1px solid ' + (isWinner ? '#9ecfad' : isLive ? '#e8a0a0' : '#e0dbd0'),
              pi === 0 ? 'border-bottom:1px solid ' + (isLive ? '#e8a0a0' : '#e8e4d8') : '',
              'background:' + (isWinner ? '#d4f0dc' : isLive ? '#fff5f5' : isTbd ? '#f5f4f0' : '#fff'),
              'color:' + (isWinner ? '#00512e' : isLoser ? '#999' : isTbd ? '#ccc' : '#1a1a1a'),
              'font-weight:' + (isWinner ? '600' : '400'),
            ].join(';');

            var flag = p.country ? countryFlag(p.country) : '';
            var seed = (p.rank && p.rank <= 32) ? '[' + p.rank + ']' : '';
            var nameSpan = document.createElement('span');
            nameSpan.style.cssText = 'overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1;';
            nameSpan.textContent = (flag ? flag + ' ' : '') + (seed ? seed + ' ' : '') + lastName(p.name);
            row.appendChild(nameSpan);

            // LIVE dot on first row only
            if (isLive && pi === 0) {
              var dot = document.createElement('span');
              dot.style.cssText = 'flex-shrink:0;width:6px;height:6px;border-radius:50%;background:#c0392b;margin-left:4px;animation:blink 1.5s ease-in-out infinite;display:inline-block;';
              row.appendChild(dot);
            }

            card.appendChild(row);
          });

          var scoreStr = (isComplete || isLive) ? formatSetScore(m.score) : null;

          if (scoreStr) {
            var scoreRow = document.createElement('div');
            scoreRow.style.cssText = 'padding:2px 6px 3px;font-size:9.5px;font-family:sans-serif;'
              + 'color:' + (isLive ? '#c0392b' : '#888') + ';'
              + 'background:' + (isLive ? '#fff0f0' : '#f7f5f0') + ';'
              + 'border:1px solid ' + (isLive ? '#e8a0a0' : '#e0dbd0') + ';border-top:none;'
              + 'letter-spacing:0.5px;';
            scoreRow.textContent = isLive ? '● ' + scoreStr : scoreStr;
            card.appendChild(scoreRow);
          }

          slot.appendChild(card);
          col.appendChild(slot);
        });

        wrap.appendChild(col);
      }

      container.innerHTML = '';
      container.appendChild(wrap);
    }

    // Load ATP bracket on page load (after a short delay so scores load first)
    setTimeout(function(){ loadBracket('atp'); }, 800);
  })();
  </script>

  <!-- DRAFTKINGS ODDS -->
  <div class="card" style="margin-bottom:24px;">
    <div class="card-header" style="margin-bottom:0;">
      <div>
        <div class="card-title">📊 US Open Odds</div>
        <div class="card-sub">Outright winner · DraftKings · updated September 2</div>
      </div>
      <div style="display:flex;gap:8px;align-items:center;">
        <button id="odds-btn-atp" onclick="switchOddsTour('atp')"
          style="padding:6px 16px;border-radius:100px;border:2px solid #00512e;background:#00512e;color:#fff;font-size:0.78rem;font-weight:700;cursor:pointer;font-family:sans-serif;letter-spacing:0.5px;">
          Men's
        </button>
        <button id="odds-btn-wta" onclick="switchOddsTour('wta')"
          style="padding:6px 16px;border-radius:100px;border:2px solid #ddd8cc;background:#fff;color:#4b006e;font-size:0.78rem;font-weight:700;cursor:pointer;font-family:sans-serif;letter-spacing:0.5px;">
          Women's
        </button>
      </div>
    </div>
    <div id="odds-body" style="padding:16px 0 4px;">
      <div style="text-align:center;color:#aaa;font-size:0.85rem;font-family:sans-serif;padding:20px;">Loading odds…</div>
    </div>
    <div style="padding:8px 20px 14px;font-size:0.7rem;font-family:sans-serif;color:#aaa;text-align:right;">
      Odds via DraftKings · must be 21+ · gambling problem? call 1-800-522-4700
    </div>
  </div>

  <script>
  (function(){
    var _oddsTour = 'atp';
    var _oddsData = null;

    window.switchOddsTour = function(tour) {
      _oddsTour = tour;
      document.getElementById('odds-btn-atp').style.cssText =
        'padding:6px 16px;border-radius:100px;border:2px solid ' + (tour==='atp'?'#00512e':'#ddd8cc') +
        ';background:' + (tour==='atp'?'#00512e':'#fff') +
        ';color:' + (tour==='atp'?'#fff':'#00512e') +
        ';font-size:0.78rem;font-weight:700;cursor:pointer;font-family:sans-serif;letter-spacing:0.5px;';
      document.getElementById('odds-btn-wta').style.cssText =
        'padding:6px 16px;border-radius:100px;border:2px solid ' + (tour==='wta'?'#4b006e':'#ddd8cc') +
        ';background:' + (tour==='wta'?'#4b006e':'#fff') +
        ';color:' + (tour==='wta'?'#fff':'#4b006e') +
        ';font-size:0.78rem;font-weight:700;cursor:pointer;font-family:sans-serif;letter-spacing:0.5px;';
      if (_oddsData) renderOdds(_oddsData);
    };

    function renderOdds(data) {
      var el = document.getElementById('odds-body');
      var list = (data[_oddsTour] || []);

      if (data.error === 'no_key') {
        el.innerHTML = '<div style="padding:20px 24px;font-family:sans-serif;font-size:0.82rem;color:#555;line-height:1.6;">'
          + '<strong style="color:#00512e;">Set up live odds in 2 steps:</strong><br>'
          + '1. Get a free API key at <strong>the-odds-api.com</strong> (500 free requests/month)<br>'
          + '2. Add <code style="background:#f0f0f0;padding:1px 5px;border-radius:3px;">ODDS_API_KEY=your_key</code> as an environment variable on Render'
          + '</div>';
        return;
      }
      if (data.error && !list.length) {
        el.innerHTML = '<div style="text-align:center;color:#aaa;font-size:0.82rem;font-family:sans-serif;padding:20px 16px;">'
          + 'Odds unavailable — ' + data.error + '</div>';
        return;
      }
      if (!list.length) {
        el.innerHTML = '<div style="text-align:center;color:#aaa;font-size:0.82rem;font-family:sans-serif;padding:20px;">No ' + (_oddsTour==='atp'?"Men's":"Women's") + ' odds available yet.</div>';
        return;
      }

      var rows = list.map(function(item, i) {
        var odds = item[0], name = item[1];
        var pos = odds && odds[0] === '+';
        var fav = odds && odds[0] === '-';
        var oddsColor = pos ? '#00512e' : fav ? '#c0392b' : '#333';
        var oddsBg    = pos ? 'rgba(0,81,46,0.07)' : fav ? 'rgba(192,57,43,0.07)' : '#f9f7f4';
        return '<div style="display:flex;align-items:center;padding:9px 20px;border-bottom:1px solid #f0ece0;gap:12px;">'
          + '<div style="width:22px;text-align:center;font-size:0.75rem;font-weight:700;color:#aaa;font-family:sans-serif;flex-shrink:0;">' + (i+1) + '</div>'
          + '<div style="flex:1;font-size:0.88rem;font-family:\'EB Garamond\',Georgia,serif;color:#1a1a1a;">' + name + '</div>'
          + '<div style="font-size:0.9rem;font-weight:700;font-family:sans-serif;color:' + oddsColor + ';background:' + oddsBg + ';padding:3px 10px;border-radius:100px;letter-spacing:0.3px;flex-shrink:0;">' + odds + '</div>'
          + '</div>';
      }).join('');

      el.innerHTML = rows;
    }

    function loadOdds() {
      fetch('/api/odds')
        .then(function(r){ return r.json(); })
        .then(function(data){
          _oddsData = data;
          renderOdds(data);
        })
        .catch(function(){
          document.getElementById('odds-body').innerHTML =
            '<div style="text-align:center;color:#aaa;font-size:0.82rem;font-family:sans-serif;padding:20px;">Could not reach DraftKings.</div>';
        });
    }

    loadOdds();
    setInterval(loadOdds, 5 * 60 * 1000);
  })();
  </script>

  <!-- SCORING RULES -->
  <div class="card">
    <div class="card-header">
      <div>
        <div class="card-title">🏆 Scoring Rules</div>
        <div class="card-sub">Points per correct pick · served.bracket.tennis · The Championships 2026</div>
      </div>
    </div>
    <div class="rules-grid">
      <div class="rule-item"><div class="rule-round">Round 1</div><div class="rule-pts">10</div><div class="rule-note">64 matches</div></div>
      <div class="rule-item"><div class="rule-round">Round 2</div><div class="rule-pts">20</div><div class="rule-note">32 matches</div></div>
      <div class="rule-item"><div class="rule-round">Round 3</div><div class="rule-pts">30</div><div class="rule-note">16 matches</div></div>
      <div class="rule-item"><div class="rule-round">Round 4</div><div class="rule-pts">40</div><div class="rule-note">8 matches</div></div>
      <div class="rule-item"><div class="rule-round">Quarters</div><div class="rule-pts">60</div><div class="rule-note">4 matches</div></div>
      <div class="rule-item"><div class="rule-round">Semis</div><div class="rule-pts">80</div><div class="rule-note">2 matches</div></div>
      <div class="rule-item"><div class="rule-round">Final</div><div class="rule-pts">100</div><div class="rule-note">1 match</div></div>
    </div>
    <div class="rules-bonuses">
      <div class="bonus-tag">🎾 Points apply to both Men's &amp; Women's draws</div>
      <div class="bonus-tag">🏆 Unseeded upset: correct pick = double points</div>
      <div class="bonus-tag">📊 Seed gap bonus: +1 pt per seed difference on correct upset pick</div>
      <div class="bonus-tag">🔢 Tiebreaker: closest guess to total games in men's final</div>
    </div>
  </div>

  <div class="footer" id="footer"></div>
</div>

<script>
const COLORS = __COLORS_JSON__;
const SLUG   = '__SLUG__';
let allData = null;
let members = [];

// ── MEMBER STORAGE ────────────────────────────────────────────────────────────
function loadMembers() {
  // Check ?m= query param first — survives iMessage/SMS link sharing unlike #hash
  const params = new URLSearchParams(location.search);
  const fromParam = params.get('m');
  if (fromParam) {
    const fromUrl = fromParam.split(',').map(s => s.trim()).filter(Boolean);
    if (fromUrl.length > 0) {
      localStorage.setItem('wim_members', JSON.stringify(fromUrl));
      return fromUrl;
    }
  }
  // Fall back to localStorage (returning visitor)
  try { return JSON.parse(localStorage.getItem('wim_members') || '[]'); }
  catch(e) { return []; }
}

function saveMembers() {
  localStorage.setItem('wim_members', JSON.stringify(members));
  const param = members.map(encodeURIComponent).join(',');
  const newUrl = location.origin + location.pathname + '?m=' + param;
  history.replaceState(null, '', newUrl);
}

// ── DATA FETCH ────────────────────────────────────────────────────────────────
async function loadData() {
  if (members.length === 0) {
    showEmpty();
    return;
  }
  document.getElementById('status-text').textContent = 'Fetching scores…';
  try {
    const params = encodeURIComponent(members.join(','));
    window._currentMembers = members;
    const res = await fetch('/api/data?members=' + params);
    if (!res.ok) throw new Error('HTTP ' + res.status);
    allData = await res.json();
    render();
    document.getElementById('footer').innerHTML = '🍈 &nbsp;US Open 2026 · Flushing Meadows · New York · Scores from served.bracket.tennis · Updated: ' + allData.updated;
  } catch(e) {
    document.getElementById('status-text').textContent = 'Error loading data — ' + e.message;
  }
}

// ── RENDER ────────────────────────────────────────────────────────────────────
function render() {
  if (!allData) return;
  const players = allData.players;

  const sorted = [...players].sort((a, b) => (b.combined ?? -1) - (a.combined ?? -1));
  const maxScore = sorted.reduce((m, p) => Math.max(m, p.combined ?? 0), 1);
  const tbody = document.getElementById('lb-body');

  tbody.innerHTML = sorted.map((p, i) => {
    const rank  = i + 1;
    const c     = COLORS[String(i % 2)] || COLORS['0'];
    const pct   = p.combined != null ? Math.round((p.combined / maxScore) * 100) : 0;
    const bracketUrl = `https://served.bracket.tennis/tournaments/${SLUG}/combined/brackets/${encodeURIComponent(p.username)}`;
    const atpPill  = p.atp  != null ? `<span class="score-pill pill-atp">${p.atp.toLocaleString()}</span>`  : `<span class="score-pill pill-none">–</span>`;
    const wtaPill  = p.wta  != null ? `<span class="score-pill pill-wta">${p.wta.toLocaleString()}</span>`  : `<span class="score-pill pill-none">–</span>`;
    const combPill = p.combined != null ? `<span class="score-pill pill-combined">${p.combined.toLocaleString()}</span>` : `<span class="score-pill pill-none">–</span>`;
    const maxPill  = p.max_combined != null
      ? `<span style="font-size:0.78rem;color:#7d5a00;font-family:sans-serif;font-weight:600;">▲ ${p.max_combined.toLocaleString()}</span>`
      : `<span class="score-pill pill-none">–</span>`;
    const globalPill = p.global_rank != null
      ? `<span style="font-size:0.78rem;color:#4b006e;font-family:sans-serif;font-weight:700;">#${p.global_rank.toLocaleString()}</span>`
      : `<span class="score-pill pill-none">–</span>`;
    return `<tr>
      <td class="rank-cell ${rank<=3?'gold':''}">${rank<=3?['🥇','🥈','🥉'][rank-1]:rank}</td>
      <td style="overflow:hidden;">
        <div class="player-name" style="white-space:nowrap;"><a class="name-link" href="${bracketUrl}" target="_blank" rel="noopener" style="color:${c.primary}">${esc(p.username)}</a></div>
        <div class="bar-wrap"><div class="bar-fill" style="width:${pct}%;background:${c.primary}"></div></div>
      </td>
      <td style="text-align:center;">${combPill}</td><td style="text-align:center;">${atpPill}</td><td style="text-align:center;">${wtaPill}</td><td style="text-align:center;">${maxPill}</td><td style="text-align:center;">${globalPill}</td>
    </tr>`;
  }).join('');

  document.getElementById('status-text').textContent = `Live · last updated ${allData.updated}`;
}

// ── EMPTY STATE ───────────────────────────────────────────────────────────────
function showEmpty() {
  document.getElementById('lb-body').innerHTML = `<tr><td colspan="6" style="padding:48px;text-align:center;font-family:sans-serif;color:#aaa;">
    <div style="font-size:2rem;margin-bottom:10px">👥</div>
    <div style="font-size:1rem;color:#006b3c;font-weight:600;margin-bottom:6px">Set up your group</div>
    <div style="font-size:0.85rem;margin-bottom:16px">Click <strong>⚙ Group</strong> in the header to add your served.bracket.tennis usernames.</div>
  </td></tr>`;
  document.getElementById('status-text').textContent = 'No group members added yet';
}

// ── MODAL ─────────────────────────────────────────────────────────────────────
function openModal() {
  renderMembersList();
  document.getElementById('modal-overlay').classList.add('open');
  setTimeout(() => document.getElementById('username-input').focus(), 100);
}
function closeModal() { document.getElementById('modal-overlay').classList.remove('open'); }
function closeModalOutside(e) { if (e.target === document.getElementById('modal-overlay')) closeModal(); }

function addMember() {
  const input = document.getElementById('username-input');
  const val = input.value.trim();
  if (!val) return;
  if (!members.find(m => m.toLowerCase() === val.toLowerCase())) members.push(val);
  input.value = '';
  renderMembersList();
}

function removeMember(idx) { members.splice(idx, 1); renderMembersList(); }

function renderMembersList() {
  const ul = document.getElementById('members-list');
  ul.innerHTML = '';
  document.getElementById('member-count').textContent = members.length;
  members.forEach((m, i) => {
    const li = document.createElement('li');
    li.innerHTML = `<span>${esc(m)}</span><button class="remove-btn" onclick="removeMember(${i})">✕</button>`;
    ul.appendChild(li);
  });
}

function saveAndClose() {
  saveMembers();
  closeModal();
  loadData();
}

async function copyInviteLink() {
  saveMembers();
  const link = location.origin + location.pathname + '?m=' + members.map(encodeURIComponent).join(',');
  try {
    await navigator.clipboard.writeText(link);
    const btn = document.getElementById('invite-btn');
    btn.textContent = '✓ Copied!';
    setTimeout(() => btn.textContent = '📋 Copy Invite Link', 2000);
  } catch(e) { prompt('Copy this link:', link); }
}

// ── UTILS ─────────────────────────────────────────────────────────────────────
function esc(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// ── INIT ──────────────────────────────────────────────────────────────────────
members = loadMembers();
renderMembersList();
loadData();
setInterval(loadData, 5 * 60 * 1000);
</script>
</body>
</html>"""


# ── HTML template injection ────────────────────────────────────────────────────

def build_html():
    colors_for_js = {str(k): v for k, v in COLORS.items()}
    html = HTML.replace('__COLORS_JSON__', json.dumps(colors_for_js))
    html = html.replace('__SLUG__', TOURNAMENT_SLUG)
    return html


# ── Scoring engine — served.bracket.tennis turbo-stream decoder ──────────────

ROUND_POINTS = {1: 10, 2: 20, 3: 30, 4: 40, 5: 60, 6: 80, 7: 100}


def _fetch_bracket_html(username, tour):
    url = f'https://served.bracket.tennis/tournaments/{TOURNAMENT_SLUG}/{tour}/brackets/{username}'
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'text/html',
    })
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.read().decode('utf-8', errors='replace')


def _parse_flat_array(html):
    """Extract and parse the React Router turbo-stream flat array from the page script."""
    scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.S)
    big = max(scripts, key=len) if scripts else ''
    m = re.search(r'streamController\.enqueue\("(.*?)"\)', big, re.S)
    if not m:
        return None
    encoded = m.group(1)
    # Decode the JavaScript string: \\ → \, \" → "  then strip stray literal newlines
    arr_str = (encoded
               .replace('\\\\', '\x00BS\x00')
               .replace('\\"', '"')               .replace('\x00BS\x00', '\\')               .replace('\n', '')               .replace('\r', ''))
    if arr_str.endswith('\\n'):
        arr_str = arr_str[:-2]
    try:
        return json.loads(arr_str)
    except Exception:
        return None


def _ts_val(flat, ref):
    """Resolve a turbo-stream integer reference to its value."""
    if not isinstance(ref, int) or ref < 0 or ref >= len(flat):
        return None
    item = flat[ref]
    if isinstance(item, dict):
        return _ts_obj(flat, item)
    return item


def _ts_obj(flat, obj):
    """Decode a turbo-stream object {"_N":M, ...} into a plain Python dict."""
    result = {}
    for k, v in obj.items():
        key_idx = int(k[1:])
        key = flat[key_idx] if 0 <= key_idx < len(flat) else None
        val = _ts_val(flat, v) if isinstance(v, int) else v
        if key is not None:
            result[key] = val
    return result


def _parse_match_scores(scores_str, p1_name, p2_name, winner_name, is_live):
    """
    Parse served.bracket.tennis scores string into a display string.
    Format: '[[p1_g, p1_tb, p1_g2, p1_tb2, ...], [p2_g, p2_tb, ...]]'
    Each pair is (games_won, tiebreak_score) per set.
    Returns e.g. '6-3  6-4  7-6(3)' or '*4-6  6-3  *6-6' when live.
    """
    if not scores_str:
        return None
    try:
        arr = json.loads(scores_str)
        if not isinstance(arr, list) or len(arr) < 2:
            return None
        p1_arr, p2_arr = arr[0], arr[1]
        n = min(len(p1_arr), len(p2_arr)) // 2
        if n == 0:
            return None

        # Show from winner's perspective; if no winner yet show from p1's view
        flip = (winner_name and winner_name == p2_name)

        parts = []
        for i in range(n):
            idx  = i * 2
            g1   = p1_arr[idx];   tb1 = p1_arr[idx+1] if idx+1 < len(p1_arr) else None
            g2   = p2_arr[idx];   tb2 = p2_arr[idx+1] if idx+1 < len(p2_arr) else None
            if g1 is None or g2 is None:
                continue
            if g1 == 0 and g2 == 0:
                continue  # skip empty/abandoned set entries
            wg, lg, wtb, ltb = (g2, g1, tb2, tb1) if flip else (g1, g2, tb1, tb2)

            last_set = (i == n - 1)
            if is_live and last_set:
                # In-progress set: just show games, no tiebreak detail
                parts.append(f'*{wg}-{lg}')
            elif ltb is not None:
                parts.append(f'{wg}-{lg}({int(ltb)})')
            else:
                parts.append(f'{wg}-{lg}')

        return '  '.join(parts) if parts else None
    except Exception:
        return None


def _extract_bracket_data(flat):
    """
    Decode the flat turbo-stream array to produce:
      r1_draw:       {slot(1-128): (player_name, ranking)}
      match_results: {(round, pos): {winner, wr, lr}}

    R1 match at position k maps to draw slots 2k-1 (top) and 2k (bottom).
    Seeding proxy: ATP/WTA ranking (top 32 are seeded at the US Open).
    """
    matches_refs = None
    for i, item in enumerate(flat):
        if (item == 'matches'
                and i + 1 < len(flat)
                and isinstance(flat[i + 1], list)
                and len(flat[i + 1]) > 50):
            matches_refs = flat[i + 1]
            break
    if not matches_refs:
        return {}, {}, []

    r1_draw = {}
    match_results = {}
    all_matches = []

    for ref in matches_refs:
        raw = flat[ref]
        if not isinstance(raw, dict):
            continue
        m = _ts_obj(flat, raw)
        rnd = m.get('roundNumber')
        pos = m.get('position')
        if not rnd or not pos:
            continue

        p1 = m.get('player1') or {}
        p2 = m.get('player2') or {}
        winner = m.get('winner') or {}

        if rnd == 1:
            s1 = (pos - 1) * 2 + 1
            s2 = (pos - 1) * 2 + 2
            if p1.get('name'):
                r1_draw[s1] = (p1['name'], p1.get('ranking') or 999)
            if p2.get('name'):
                r1_draw[s2] = (p2['name'], p2.get('ranking') or 999)

        if winner.get('name'):
            wname = winner['name']
            lname = p2.get('name') if p1.get('name') == wname else p1.get('name')
            r1 = p1.get('ranking') or 999
            r2 = p2.get('ranking') or 999
            wr = r1 if p1.get('name') == wname else r2
            lr = r2 if p1.get('name') == wname else r1
            match_results[(rnd, pos)] = {'winner': wname, 'loser': lname, 'wr': wr, 'lr': lr}

        def _ctry(pobj):
            c = pobj.get('country')
            if isinstance(c, dict):
                return (c.get('code') or c.get('abbreviation') or '').upper()
            return (c or '').upper()

        p1_name     = p1.get('name') or None
        p2_name     = p2.get('name') or None
        winner_name = winner.get('name') or None
        has_started = bool(m.get('has_started'))
        is_live     = has_started and not winner_name and (p1_name or p2_name)

        # scores field: '[[p1_g,p1_tb,p1_g2,p1_tb2,...],[p2_g,p2_tb,...]]'
        score = _parse_match_scores(
            m.get('scores'), p1_name, p2_name, winner_name, bool(is_live)
        )

        all_matches.append({
            'round': rnd,
            'pos': pos,
            'p1': p1_name,
            'p2': p2_name,
            'p1_rank': p1.get('ranking') or 999,
            'p2_rank': p2.get('ranking') or 999,
            'p1_country': _ctry(p1),
            'p2_country': _ctry(p2),
            'winner': winner_name,
            'score': score,
            'is_live': bool(is_live),
        })

    return r1_draw, match_results, all_matches


def _extract_picks(html):
    """
    Extract user picks from bracket page HTML.
    Returns {(round, match_pos): draw_slot} or {}.
    Picks are embedded as {"_v":2,"1:1":slot,...}.
    """
    scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.S)
    big = max(scripts, key=len) if scripts else ''
    m = re.search(r'picks\\",\\"(\{.*?\})\\"'  , big)
    if not m:
        return {}
    raw = m.group(1).replace('\\\\\\"'  , '"')
    try:
        data = json.loads(raw)
    except Exception:
        return {}
    picks = {}
    for key, val in data.items():
        if ':' in str(key):
            parts = key.split(':')
            try:
                picks[(int(parts[0]), int(parts[1]))] = int(val)
            except (ValueError, TypeError):
                pass
    return picks


def _calculate_score(picks, r1_draw, match_results):
    """
    Calculate a user's total bracket score.

    picks:         {(round, match_pos): draw_slot}
    r1_draw:       {draw_slot: (player_name, ranking)}
    match_results: {(round, match_pos): {winner, wr, lr}}

    Points per correct pick:
      base:           ROUND_POINTS[round]
      unseeded upset: x2  (winner_rank > 32, loser_rank <= 32)
      seeded upset:   +gap  (both seeded, winner_rank > loser_rank)
    """
    total = 0
    for (rnd, mpos), slot in picks.items():
        if not (1 <= rnd <= 7):
            continue
        result = match_results.get((rnd, mpos))
        if not result:
            continue
        if slot not in r1_draw:
            continue
        player_name, _ = r1_draw[slot]
        if result['winner'] != player_name:
            continue

        base = ROUND_POINTS[rnd]
        wr, lr = result['wr'], result['lr']
        winner_seeded = wr <= 32
        loser_seeded  = lr <= 32

        if not winner_seeded and loser_seeded:
            pts = base * 2
        elif winner_seeded and loser_seeded and wr > lr:
            pts = base + (wr - lr)
        else:
            pts = base

        total += pts
    return total


def _calculate_max_score(picks, r1_draw, match_results):
    """Max possible score = current correct picks + base points for future picks
    where the picked player hasn't been eliminated yet."""
    current = _calculate_score(picks, r1_draw, match_results)
    eliminated = {r['loser'] for r in match_results.values() if r.get('loser')}
    future = 0
    for (rnd, mpos), slot in picks.items():
        if not (1 <= rnd <= 7):
            continue
        if match_results.get((rnd, mpos)):
            continue  # completed match already in current score
        if slot not in r1_draw:
            continue
        player_name, _ = r1_draw[slot]
        if player_name not in eliminated:
            future += ROUND_POINTS[rnd]
    return current + future


# ── ESPN live-match overlay ───────────────────────────────────────────────────

_espn_live_cache    = {}   # tour -> {'live': set_of_names, 'scores': {name: score_str}}
_espn_live_cache_ts = {}

def _espn_parse_events(data, live, scores):
    """
    Parse ESPN scoreboard JSON, populating:
      live   — set of full names currently playing
      scores — {full_name: score_str, last_name: score_str} for completed/live matches
    """
    for event in data.get('events', []):
        for comp in event.get('competitions', []):
            stype     = (comp.get('status') or {}).get('type') or {}
            state     = stype.get('name', '')
            completed = stype.get('completed', False)

            competitors = comp.get('competitors', [])

            # Collect names + per-player linescores
            players = []
            for c in competitors:
                name = (c.get('athlete') or {}).get('fullName', '') or \
                       (c.get('athlete') or {}).get('displayName', '')
                ls   = c.get('linescores') or []
                players.append({'name': name, 'ls': ls})

            names = [p['name'] for p in players if p['name']]

            if state == 'STATUS_IN_PROGRESS' and not completed:
                for name in names:
                    live.add(name)

            # --- Build set-score string ---
            score_str = None

            # Format 1: competition-level linescores with displayValue ("6-3")
            comp_ls = comp.get('linescores') or []
            if comp_ls:
                parts = [s.get('displayValue', '') for s in comp_ls if s.get('displayValue')]
                if parts:
                    score_str = '  '.join(parts)

            # Format 2: per-competitor linescores (zip games per set)
            if not score_str and len(players) == 2:
                ls0 = [l.get('value') for l in players[0]['ls'] if l.get('value') is not None]
                ls1 = [l.get('value') for l in players[1]['ls'] if l.get('value') is not None]
                if ls0 and ls1 and len(ls0) == len(ls1):
                    score_str = '  '.join(f'{int(a)}-{int(b)}' for a, b in zip(ls0, ls1))

            if score_str and names:
                for name in names:
                    scores[name] = score_str
                    last = name.strip().split()[-1] if name.strip() else ''
                    if last:
                        scores[last] = score_str


def _fetch_espn_live(tour):
    """
    Returns {'live': {player_name, ...}, 'scores': {name: score_str}}
    Fetches today + past 5 days so recently-completed match scores are included.
    Cached 45 seconds.
    """
    now = time.time()
    if tour in _espn_live_cache and now - _espn_live_cache_ts.get(tour, 0) < 45:
        return _espn_live_cache[tour]

    slug  = 'atp' if tour == 'atp' else 'wta'
    live  = set()
    scores = {}

    today = datetime.now()
    for delta in range(6):  # today + 5 previous days
        date_str = (today - timedelta(days=delta)).strftime('%Y%m%d')
        # Try multiple ESPN endpoints — Grand Slams may not appear under atp/wta slug
        endpoints = [
            f'https://site.api.espn.com/apis/site/v2/sports/tennis/{slug}/scoreboard?dates={date_str}',
            f'https://site.api.espn.com/apis/site/v2/sports/tennis/scoreboard?dates={date_str}',
        ]
        for url in endpoints:
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=8) as r:
                    data = json.loads(r.read().decode())
                _espn_parse_events(data, live, scores)
            except Exception:
                continue

    result = {'live': live, 'scores': scores}
    _espn_live_cache[tour]    = result
    _espn_live_cache_ts[tour] = now
    return result


# ── US Open daily schedule (all times already ET) ───────────────────────────
_WIMBLEDON_SCHEDULE = """
US Open 2026 daily schedule (all times Eastern / ET — the tournament is in New York):
- Outside courts (Courts 4–17): play begins at 11:00 AM ET
- Arthur Ashe Stadium: day session first match at 12:00 PM ET; evening session at 7:00 PM ET
- Louis Armstrong Stadium: day session first match at 12:00 PM ET; evening session at 7:00 PM ET
- Grandstand: day session first match at 11:00 AM ET

High-profile matches (top seeds, QF/SF/Final) are on Arthur Ashe or Louis Armstrong starting at 12:00 PM ET day session or 7:00 PM ET evening session.
Outside-court matches for lower seeds typically begin at 11:00 AM ET.
All times are already ET — no conversion needed.
"""

# ── US Open odds (DraftKings · sourced 2026-08-24) ───────────────────────────
# Update these manually from DraftKings when odds change

_STATIC_ODDS = {
    'atp': [
        ('+145',  'Carlos Alcaraz'),
        ('+360',  'Alexander Zverev'),
        ('+1000', 'Taylor Fritz'),
        ('+1200', 'Ben Shelton'),
        ('+1400', 'Rafael Jodar'),
        ('+1700', 'Daniil Medvedev'),
        ('+2500', 'Felix Auger-Aliassime'),
        ('+3500', 'Frances Tiafoe'),
        ('+3500', 'Jakub Mensik'),
        ('+4000', 'Lorenzo Musetti'),
    ],
    'wta': [
        ('+330',  'Aryna Sabalenka'),
        ('+425',  'Coco Gauff'),
        ('+500',  'Iga Swiatek'),
        ('+900',  'Jessica Pegula'),
        ('+1400', 'Naomi Osaka'),
        ('+1700', 'Elena Rybakina'),
        ('+1800', 'Mirra Andreeva'),
        ('+1800', 'Marta Kostyuk'),
        ('+1800', 'Amanda Anisimova'),
        ('+2200', 'Alexandra Eala'),
    ],
}


# ── AI daily summary ─────────────────────────────────────────────────────────

ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
ODDS_UPDATE_TOKEN = os.environ.get('ODDS_UPDATE_TOKEN', '')

# Live odds override — populated by /api/update-odds, falls back to _STATIC_ODDS
_live_odds = {}
_live_odds_updated = ''

_summary_cache    = {}
_summary_cache_ts = 0


def _fetch_news_text(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            html = r.read().decode('utf-8', errors='replace')
        text = re.sub(r'<[^>]+>', ' ', html)
        text = re.sub(r'\s+', ' ', text).strip()
        return text[:3000]
    except Exception:
        return ''


def _fetch_usopen_news():
    """Try multiple sources for US Open headlines."""
    for url in [
        'https://www.bbc.com/sport/tennis/us-open',
        'https://www.bbc.co.uk/sport/tennis',
        'https://www.espn.com/tennis/',
    ]:
        text = _fetch_news_text(url)
        if text:
            return text
    return ''


def _fetch_today_espn_scores():
    """Fetch today's completed US Open match results from ESPN groupings structure."""
    lines = []
    today_et   = _now_et()
    today_date = today_et.strftime('%Y-%m-%d')
    today_str  = today_et.strftime('%Y%m%d')
    seen = set()

    for slug in ('atp', 'wta'):
        url = f'https://site.api.espn.com/apis/site/v2/sports/tennis/{slug}/scoreboard?dates={today_str}'
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read().decode())
            for event in data.get('events', []):
                for grouping in event.get('groupings', []):
                    for comp in grouping.get('competitions', []):
                        # Filter to today's matches only
                        comp_date = comp.get('date', '')[:10]
                        if comp_date != today_date:
                            continue
                        if not comp.get('status', {}).get('type', {}).get('completed'):
                            continue
                        # Result is in notes[0].text e.g. "Sinner (ITA) bt Kecmanovic (SRB) 4-6 6-3..."
                        note = ''
                        for n in comp.get('notes', []):
                            if n.get('type') == 'event':
                                note = n.get('text', '')
                                break
                        if note and note not in seen:
                            seen.add(note)
                            lines.append(note)
        except Exception:
            continue
    return lines


def _build_results_text():
    """Build completed results and upcoming matches from bracket data, split by tour."""
    atp_done, wta_done = [], []
    atp_upcoming, wta_upcoming = [], []
    round_names = {1:'R1',2:'R2',3:'R3',4:'R4',5:'QF',6:'SF',7:'Final'}
    for tour, done_bucket, upcoming_bucket in [('atp', atp_done, atp_upcoming), ('wta', wta_done, wta_upcoming)]:
        try:
            _, results, all_matches = _get_tournament_data(tour, MEMBERS)
            score_lookup = {}
            for m in all_matches:
                if m.get('winner') and m.get('score'):
                    score_lookup[(m['round'], m['pos'])] = m['score']
            for (rnd, pos), r in sorted(results.items()):
                rname  = round_names.get(rnd, f'R{rnd}')
                winner = r.get('winner', '?')
                loser  = r.get('loser', '?')
                score  = score_lookup.get((rnd, pos), '')
                line   = f"{rname}: {winner} def. {loser}"
                if score:
                    line += f" ({score})"
                done_bucket.append(line)
            completed_keys = set(results.keys())
            for m in all_matches:
                key = (m['round'], m['pos'])
                if key in completed_keys:
                    continue
                if m.get('is_live'):
                    continue
                p1, p2 = m.get('p1'), m.get('p2')
                if p1 and p2:
                    rname = round_names.get(m['round'], f"R{m['round']}")
                    upcoming_bucket.append(f"{rname}: {p1} vs {p2}")
        except Exception:
            pass

    # Today's results direct from ESPN (most reliable date-filtered source)
    today_lines = _fetch_today_espn_scores()
    today_section = "Today's completed matches (ESPN):\n" + '\n'.join(today_lines[:20]) if today_lines else "Today's completed matches: none confirmed yet via ESPN"

    atp_ahead = "Men's upcoming (bracket):\n" + '\n'.join(atp_upcoming[:15]) if atp_upcoming else "Men's upcoming: none scheduled yet"
    wta_ahead = "Women's upcoming (bracket):\n" + '\n'.join(wta_upcoming[:15]) if wta_upcoming else "Women's upcoming: none scheduled yet"

    return today_section + '\n\n' + wta_ahead + '\n\n' + atp_ahead


def _fetch_ai_summary():
    """
    Call Claude Haiku to write a short US Open daily wrap.
    Cached 1 hour. Returns {'summary': str, 'updated': str, 'error': str|None}
    """
    global _summary_cache, _summary_cache_ts
    now = time.time()
    # Invalidate cache if it's from a previous calendar day (ET) or older than 30 min
    cache_date = datetime.fromtimestamp(_summary_cache_ts, tz=ZoneInfo('America/New_York')).strftime('%Y-%m-%d') if (_summary_cache_ts and ZoneInfo) else (datetime.utcfromtimestamp(_summary_cache_ts) - timedelta(hours=4)).strftime('%Y-%m-%d') if _summary_cache_ts else ''
    today_date = _now_et().strftime('%Y-%m-%d')
    if _summary_cache and now - _summary_cache_ts < 1800 and cache_date == today_date:
        return _summary_cache

    if not ANTHROPIC_API_KEY:
        result = {'summary': '', 'updated': '', 'error': 'no_key'}
        _summary_cache = result
        _summary_cache_ts = now
        return result

    results_text = _build_results_text()
    news_text    = _fetch_usopen_news()
    today        = _now_et().strftime('%B %d, %Y')

    now_et      = _now_et()
    hour_et     = now_et.hour
    today_date  = now_et.strftime('%B %d, %Y')
    tomorrow_et = now_et + timedelta(days=1)
    tomorrow_date = tomorrow_et.strftime('%B %d, %Y')

    if hour_et < 18:
        lookahead_label = "upcoming"
        day_context = (
            f"It is currently {now_et.strftime('%I:%M %p ET')} on {today_date}. "
            "For the looking-ahead sentences: pick the two most compelling upcoming matches from the data. "
            "If the news context explicitly confirms a match is today, say 'today' and include the ET time. "
            "If you are not certain, just say 'in their upcoming match' — never guess a day or time. "
            "Always write the looking-ahead sentences regardless — never refuse or ask for more info."
        )
    else:
        lookahead_label = "upcoming"
        day_context = (
            f"It is currently {now_et.strftime('%I:%M %p ET')} on {today_date} — past 6 PM ET so today's play is done. "
            "For the looking-ahead sentences: pick the two most compelling upcoming matches from the data. "
            "If the news context explicitly confirms a match is tomorrow, say 'tomorrow' and include the ET time. "
            "If you are not certain, just say 'in their upcoming match' — never guess a day or time. "
            "Never say 'tonight'. Always write the looking-ahead sentences regardless — never refuse or ask for more info."
        )

    prompt = (
        f"You are a tennis writer covering the US Open {today}. Current time: {now_et.strftime('%I:%M %p ET')}.\n"
        f"Write an ultra-concise daily update in this exact format — no intro, no extra text, no blank lines between sentences:\n\n"
        f"WOMEN'S: [sentence 1: recap today's most notable Women's result with score] [sentence 2: one more Women's result or storyline] [sentence 3: most compelling Women's match {lookahead_label} — name players, stakes, ET time if confirmed] [sentence 4: one more Women's match {lookahead_label} to watch with ET time if confirmed]\n"
        f"MEN'S: [sentence 1: recap today's most notable Men's result with score] [sentence 2: one more Men's result or storyline] [sentence 3: most compelling Men's match {lookahead_label} — name players, stakes, ET time if confirmed] [sentence 4: one more Men's match {lookahead_label} to watch with ET time if confirmed]\n\n"
        f"Rules:\n"
        f"- Every sentence must be SHORT (under 20 words).\n"
        f"- Tone: engaging and specific, but measured. Avoid hyperbolic words like demolished, crushed, steamrolled, bagel, brutal, dominant, stunning.\n"
        f"- Only use facts from the data below. Never fabricate.\n"
        f"- CRITICAL: For the recap sentences, ONLY reference matches listed under \"Today's completed matches\" in the data. Do NOT recap matches from previous days.\n"
        f"- {day_context}\n"
        f"- If you include a match time, show ET only. Format: '12:00 PM ET'.\n"
        f"- CRITICAL: Always produce the full update — never refuse or ask for more information. If day/time is uncertain, say 'in their upcoming match' instead of guessing.\n\n"
        f"US Open schedule (ET times):\n{_WIMBLEDON_SCHEDULE}\n\n"
        f"Data:\n{results_text}\n\n"
        f"News context:\n{news_text[:2500]}"
    )

    try:
        payload = json.dumps({
            'model': 'claude-haiku-4-5-20251001',
            'max_tokens': 450,
            'messages': [{'role': 'user', 'content': prompt}],
        }).encode()
        req = urllib.request.Request(
            'https://api.anthropic.com/v1/messages',
            data=payload,
            headers={
                'x-api-key': ANTHROPIC_API_KEY,
                'anthropic-version': '2023-06-01',
                'content-type': 'application/json',
            },
            method='POST',
        )
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read().decode())
        summary = data['content'][0]['text'].strip()
        result  = {'summary': summary, 'updated': _now_et().strftime('%b %d · %I:%M %p ET'), 'error': None}
    except Exception as e:
        result = {'summary': '', 'updated': '', 'error': str(e)}

    _summary_cache    = result
    _summary_cache_ts = now
    return result


def _fetch_dk_odds():
    # Use live odds pushed by scheduled agent if available
    if _live_odds.get('atp') or _live_odds.get('wta'):
        return {'atp': _live_odds.get('atp', []), 'wta': _live_odds.get('wta', []), 'error': None, 'updated': _live_odds_updated}
    # Fall back to hardcoded odds
    return {'atp': _STATIC_ODDS['atp'], 'wta': _STATIC_ODDS['wta'], 'error': None}


# ── Global leaderboard rank ───────────────────────────────────────────────────

_global_rank_cache    = {}
_global_rank_cache_ts = 0


def _fetch_global_ranks():
    """
    Scrape served.bracket.tennis global combined leaderboard.
    Returns {username_lower: rank} cached 10 minutes.
    """
    global _global_rank_cache, _global_rank_cache_ts
    now = time.time()
    if _global_rank_cache and now - _global_rank_cache_ts < 600:
        return _global_rank_cache
    try:
        url = f'https://served.bracket.tennis/tournaments/{TOURNAMENT_SLUG}/leaderboard'
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'text/html',
        })
        with urllib.request.urlopen(req, timeout=15) as r:
            html = r.read().decode('utf-8', errors='replace')
        flat = _parse_flat_array(html)
        ranks = {}
        if flat:
            # Find leaderboard entries: look for username strings near rank numbers
            for i, item in enumerate(flat):
                if isinstance(item, str) and item == 'rank':
                    # Look nearby for username and rank value
                    pass
            # Fallback: regex scrape usernames in order from HTML
            entries = re.findall(r'/tournaments/[^/]+/combined/brackets/([^"\'<>\s/]+)', html)
            seen = []
            for e in entries:
                if e not in seen:
                    seen.append(e)
            for idx, username in enumerate(seen):
                ranks[username.lower()] = idx + 1
        _global_rank_cache = ranks
        _global_rank_cache_ts = now
    except Exception:
        pass
    return _global_rank_cache


# ── Group score scraper — pulls exact scores from served.bracket.tennis ───────

_group_scores_cache    = {}
_group_scores_cache_ts = 0.0


def _fetch_tour_score(username, tour):
    """
    Fetch a user's ATP or WTA bracket page and return their score as an int,
    or None on failure.  The page renders the score as e.g. "380 pts".
    """
    try:
        url = f'https://served.bracket.tennis/tournaments/{TOURNAMENT_SLUG}/{tour}/brackets/{username}'
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'text/html',
        })
        with urllib.request.urlopen(req, timeout=15) as r:
            html = r.read().decode('utf-8', errors='replace')
        m = re.search(r'(\d+)\s*pts', html, re.I)
        if m:
            return int(m.group(1))
    except Exception:
        pass
    return None


def _scrape_group_scores():
    """
    Fetch each member's ATP and WTA bracket pages from served.bracket.tennis,
    extract the rendered score ("NNN pts"), and return:
      {username_lower: {'atp': int|None, 'wta': int|None, 'combined': int|None}}
    Cached 5 minutes.
    """
    global _group_scores_cache, _group_scores_cache_ts
    now = time.time()
    if _group_scores_cache and now - _group_scores_cache_ts < 300:
        return _group_scores_cache

    out = {}
    for member in MEMBERS:
        atp = _fetch_tour_score(member, 'atp')
        wta = _fetch_tour_score(member, 'wta')
        combined = None
        if atp is not None and wta is not None:
            combined = atp + wta
        elif atp is not None:
            combined = atp
        elif wta is not None:
            combined = wta
        out[member.lower()] = {'atp': atp, 'wta': wta, 'combined': combined}

    if out:
        _group_scores_cache    = out
        _group_scores_cache_ts = now

    return _group_scores_cache


# Tournament data cache: shared draw+results across all users per request
_tourney_cache    = {}
_tourney_cache_ts = {}


def _get_tournament_data(tour, members):
    """
    Return (r1_draw, match_results) for the given tour, cached 3 minutes.
    Fetches the first available member's bracket page to decode the draw.
    """
    now = time.time()
    if tour in _tourney_cache and now - _tourney_cache_ts.get(tour, 0) < 180:
        return _tourney_cache[tour]

    for username in members:
        try:
            html = _fetch_bracket_html(username, tour)
            flat = _parse_flat_array(html)
            if flat:
                r1_draw, match_results, all_matches = _extract_bracket_data(flat)
                if r1_draw:
                    _tourney_cache[tour] = (r1_draw, match_results, all_matches)
                    _tourney_cache_ts[tour] = now
                    return r1_draw, match_results, all_matches
        except Exception:
            continue

    return {}, {}, []


def get_data(members=None):
    if members is None:
        members = MEMBERS
    if not members:
        return {'players': [], 'updated': _now_et().strftime('%b %d, %Y · %I:%M:%S %p ET')}

    # Pull scores directly from served.bracket.tennis (exact, no local re-calculation)
    group_scores = _scrape_group_scores()

    players = []
    for i, member in enumerate(members):
        s = group_scores.get(member.lower(), {})
        atp_score    = s.get('atp')
        wta_score    = s.get('wta')
        combined     = s.get('combined')

        # Derive combined if only one tour score is available
        if combined is None:
            if atp_score is not None and wta_score is not None:
                combined = atp_score + wta_score
            elif atp_score is not None:
                combined = atp_score
            elif wta_score is not None:
                combined = wta_score

        players.append({
            'username':     member,
            'atp':          atp_score,
            'wta':          wta_score,
            'combined':     combined,
            'max_combined': None,
            'color_idx':    i % len(COLORS),
        })

    players.sort(key=lambda p: (-(p['combined'] or -1), -(p['atp'] or -1)))

    global_ranks = _fetch_global_ranks()
    for p in players:
        p['global_rank'] = global_ranks.get(p['username'].lower())

    return {
        'players': players,
        'updated': _now_et().strftime('%b %d, %Y · %I:%M:%S %p ET'),
    }


# ── HTTP Server ───────────────────────────────────────────────────────────────

BUILT_HTML = build_html().encode('utf-8')

class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def send_body(self, body: bytes, content_type: str, status: int = 200):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Connection', 'close')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith('/api/data'):
            try:
                members = None
                if '?' in self.path:
                    qs = self.path.split('?', 1)[1]
                    for part in qs.split('&'):
                        if part.startswith('members='):
                            val = urllib.request.unquote(part[8:])
                            members = [m.strip() for m in val.split(',') if m.strip()]
                data = get_data(members)
                body = json.dumps(data).encode()
                self.send_body(body, 'application/json')
            except Exception as e:
                self.send_body(str(e).encode(), 'text/plain', 500)
        elif self.path.startswith('/api/bracket'):
            try:
                tour = 'atp'
                members = None
                if '?' in self.path:
                    qs = self.path.split('?', 1)[1]
                    for part in qs.split('&'):
                        if part.startswith('tour='):
                            tour = part[5:].lower()
                        elif part.startswith('members='):
                            val = urllib.request.unquote(part[8:])
                            members = [m.strip() for m in val.split(',') if m.strip()]
                members = members or MEMBERS
                _, _, all_matches = _get_tournament_data(tour, members)
                espn = _fetch_espn_live(tour)
                body = json.dumps({
                    'tour': tour,
                    'matches': all_matches,
                    'live_players': list(espn['live']),
                    'espn_scores': espn['scores'],
                }).encode()
                self.send_body(body, 'application/json')
            except Exception as e:
                self.send_body(str(e).encode(), 'text/plain', 500)
        elif self.path.startswith('/api/summary'):
            try:
                if 'bust=' in self.path:
                    global _summary_cache, _summary_cache_ts
                    _summary_cache = {}
                    _summary_cache_ts = 0
                body = json.dumps(_fetch_ai_summary()).encode()
                self.send_body(body, 'application/json')
            except Exception as e:
                self.send_body(json.dumps({'summary':'','updated':'','error':str(e)}).encode(), 'application/json')
        elif self.path.startswith('/api/odds/sports'):
            # Debug: show all tennis sports The Odds API returns for this key
            try:
                if not ODDS_API_KEY:
                    body = json.dumps({'error': 'no key'}).encode()
                else:
                    sports = _odds_api_get(f'/sports?apiKey={ODDS_API_KEY}&all=true')
                    tennis = [s for s in sports if 'tennis' in (s.get('key','') + s.get('title','')).lower()]
                    body = json.dumps(tennis, indent=2).encode()
                self.send_body(body, 'application/json')
            except Exception as e:
                self.send_body(json.dumps({'error': str(e)}).encode(), 'application/json')
        elif self.path.startswith('/api/odds'):
            try:
                body = json.dumps(_fetch_dk_odds()).encode()
                self.send_body(body, 'application/json')
            except Exception as e:
                self.send_body(json.dumps({'atp':[],'wta':[],'error':str(e)}).encode(), 'application/json')
        else:
            self.send_body(BUILT_HTML, 'text/html; charset=utf-8')

    def do_POST(self):
        global _live_odds, _live_odds_updated
        if self.path == '/api/update-odds':
            try:
                length = int(self.headers.get('Content-Length', 0))
                body   = json.loads(self.rfile.read(length).decode())
                token  = self.headers.get('X-Update-Token', '')
                if ODDS_UPDATE_TOKEN and token != ODDS_UPDATE_TOKEN:
                    self.send_response(401)
                    self.end_headers()
                    return
                mens   = [(item['odds_american'], item['player']) for item in body.get('mens', [])[:10]]
                womens = [(item['odds_american'], item['player']) for item in body.get('womens', [])[:10]]
                if mens or womens:
                    _live_odds = {'atp': mens, 'wta': womens}
                    _live_odds_updated = body.get('updated', _now_et().strftime('%B %d, %Y'))
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'ok': True}).encode())
            except Exception as e:
                self.send_response(500)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, fmt, *args):
        pass  # suppress server log noise


if __name__ == '__main__':
    print(f'🎾 US Open 2026 Bracket Dashboard')
    print(f'   Running at http://localhost:{PORT}')
    print(f'   Tracking {len(MEMBERS)} players: {", ".join(MEMBERS)}')
    print(f'   Refreshes every 5 minutes from served.bracket.tennis')
    print(f'   Press Ctrl+C to stop\n')
    HTTPServer(('0.0.0.0', PORT), Handler).serve_forever()
