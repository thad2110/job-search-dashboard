"""
Build Site Generator
====================
Compiles:
1. data/scraped_jobs.json (raw scraped jobs pool)
2. data/refined_jobs.json (skill-refined jobs categorized per user)
3. data/jobs.json (synced for API and dashboard compatibility)
4. index.html (self-contained, responsive dashboard with dynamic user filtering,
   dynamic KPI stats, dynamic charts, and per-user application tracking)

Run with:
    python build_site.py
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

PROJECT_DIR = Path(__file__).parent
DATA_DIR    = PROJECT_DIR / "data"
USERS_DIR   = PROJECT_DIR / "users"
SCRIPTS_DIR = PROJECT_DIR / "scripts"

DATA_DIR.mkdir(exist_ok=True)
USERS_DIR.mkdir(exist_ok=True)

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from refine_jobs import refine_jobs


def build_dashboard():
    # 1. Run the job refiner against all user profiles in users/*.txt
    print("[build_site] Refining jobs for all users in users/...")
    refined_data = refine_jobs()

    if not refined_data or not refined_data.get("users"):
        print("[build_site] Error: No refined user data generated!")
        sys.exit(1)

    now_ist = refined_data.get("generated_at", datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M IST"))
    default_user_id = refined_data.get("default_user", list(refined_data["users"].keys())[0])
    default_user = refined_data["users"][default_user_id]
    
    # Format refined data as JSON string for embedding
    refined_json_str = json.dumps(refined_data, ensure_ascii=False)

    # 2. Generate HTML Dashboard
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ML & Data Science Job Tracker | Multi-User Live Dashboard</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #f8fafc;
      --card-bg: #ffffff;
      --navy: #0f172a;
      --primary: #1e40af;
      --primary-light: #3b82f6;
      --border: #e2e8f0;
      --text-main: #0f172a;
      --text-muted: #64748b;
      --green: #10b981;
      --green-bg: #ecfdf5;
      --amber: #f59e0b;
      --amber-bg: #fffbeb;
      --rose: #ef4444;
      --rose-bg: #fef2f2;
      --purple: #8b5cf6;
      --purple-bg: #f5f3ff;
      --blue-bg: #eff6ff;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Inter', system-ui, -apple-system, sans-serif;
      background: var(--bg);
      color: var(--text-main);
      line-height: 1.5;
    }}
    header {{
      background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%);
      color: #fff;
      padding: 24px 32px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }}
    .header-content {{
      max-width: 1400px;
      margin: 0 auto;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 16px;
    }}
    header h1 {{
      font-size: 24px;
      font-weight: 700;
      letter-spacing: -0.02em;
      display: flex;
      align-items: center;
      gap: 10px;
    }}
    header p {{
      color: #94a3b8;
      font-size: 13px;
      margin-top: 4px;
    }}
    .refresh-badge {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: rgba(255,255,255,0.1);
      border: 1px solid rgba(255,255,255,0.2);
      border-radius: 999px;
      padding: 6px 14px;
      font-size: 12px;
      color: #e2e8f0;
    }}
    .pulse {{
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #10b981;
      box-shadow: 0 0 8px #10b981;
    }}
    main {{
      max-width: 1400px;
      margin: 0 auto;
      padding: 24px 32px;
    }}
    
    /* Candidate Profile Banner */
    .user-profile-bar {{
      background: #ffffff;
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 18px 24px;
      margin-bottom: 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 18px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.03);
    }}
    .user-info-group {{
      display: flex;
      align-items: center;
      gap: 16px;
      flex-wrap: wrap;
    }}
    .user-avatar {{
      width: 52px;
      height: 52px;
      border-radius: 50%;
      background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
      color: #fff;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      font-size: 18px;
      letter-spacing: 0.05em;
      box-shadow: 0 2px 8px rgba(30,64,175,0.25);
    }}
    .user-details {{
      display: flex;
      flex-direction: column;
      gap: 4px;
    }}
    .user-name-row {{
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
    }}
    .user-dropdown {{
      font-size: 16px;
      font-weight: 700;
      color: var(--navy);
      padding: 6px 12px;
      border-radius: 8px;
      border: 1.5px solid #cbd5e1;
      background: #f8fafc;
      cursor: pointer;
    }}
    .user-dropdown:focus {{
      outline: none;
      border-color: var(--primary-light);
      box-shadow: 0 0 0 2px rgba(59,130,246,0.15);
    }}
    .user-title-tag {{
      font-size: 13px;
      color: var(--text-muted);
      font-weight: 500;
    }}
    .user-skills-wrap {{
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-top: 6px;
    }}
    .skill-pill {{
      background: #eff6ff;
      color: #1e40af;
      border: 1px solid #bfdbfe;
      border-radius: 999px;
      padding: 3px 10px;
      font-size: 11px;
      font-weight: 600;
    }}
    .user-actions {{
      display: flex;
      gap: 10px;
      align-items: center;
      flex-wrap: wrap;
    }}

    /* KPI Grid */
    .kpi-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 14px;
      margin-bottom: 24px;
    }}
    .kpi-card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 16px 20px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.04);
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }}
    .kpi-card .lbl {{
      font-size: 12px;
      font-weight: 600;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}
    .kpi-card .val {{
      font-size: 28px;
      font-weight: 700;
      color: var(--text-main);
      margin-top: 6px;
    }}
    .kpi-card.highlight {{
      border-left: 4px solid var(--primary-light);
    }}
    .kpi-card.applied-kpi {{
      border-left: 4px solid var(--green);
      background: #f0fdf4;
    }}
    .charts-grid {{
      display: grid;
      grid-template-columns: 2fr 1fr 1fr;
      gap: 16px;
      margin-bottom: 24px;
    }}
    @media (max-width: 1024px) {{
      .charts-grid {{ grid-template-columns: 1fr; }}
    }}
    .chart-box {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 18px 20px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }}
    .chart-box h3 {{
      font-size: 14px;
      font-weight: 600;
      color: var(--text-main);
      margin-bottom: 14px;
    }}
    .chart-container {{
      position: relative;
      height: 240px;
    }}
    .table-card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.04);
      overflow: hidden;
    }}
    .filter-bar {{
      padding: 18px 20px;
      border-bottom: 1px solid var(--border);
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      align-items: center;
      background: #fafafa;
    }}
    .search-input {{
      flex: 1;
      min-width: 220px;
      padding: 9px 14px;
      border: 1px solid var(--border);
      border-radius: 8px;
      font-size: 13px;
      background: #fff;
    }}
    .search-input:focus, select:focus {{
      outline: none;
      border-color: var(--primary-light);
      box-shadow: 0 0 0 2px rgba(59,130,246,0.15);
    }}
    select {{
      padding: 9px 12px;
      border: 1px solid var(--border);
      border-radius: 8px;
      font-size: 13px;
      background: #fff;
      color: var(--text-main);
      cursor: pointer;
    }}
    .status-select {{
      font-weight: 600;
      border-color: #cbd5e1;
      background: #f8fafc;
    }}
    .btn-action {{
      padding: 9px 14px;
      background: #fff;
      border: 1px solid var(--border);
      border-radius: 8px;
      font-size: 13px;
      font-weight: 500;
      cursor: pointer;
      color: var(--text-muted);
      transition: all 0.15s;
    }}
    .btn-action:hover {{
      background: #f1f5f9;
      color: var(--text-main);
    }}
    .counter-tag {{
      margin-left: auto;
      font-size: 13px;
      font-weight: 600;
      color: var(--text-muted);
    }}
    .table-container {{
      overflow-x: auto;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      text-align: left;
      font-size: 13px;
      min-width: 1250px;
    }}
    th {{
      background: #f8fafc;
      padding: 12px 14px;
      font-weight: 600;
      color: var(--text-muted);
      border-bottom: 1px solid var(--border);
      white-space: nowrap;
      cursor: pointer;
      user-select: none;
    }}
    th:hover {{
      background: #f1f5f9;
    }}
    td {{
      padding: 12px 14px;
      border-bottom: 1px solid var(--border);
      vertical-align: top;
    }}
    tr:hover td {{
      background: #f8fafc;
    }}
    tr.is-applied td {{
      background: #f0fdf4 !important;
    }}
    tr.is-skipped td {{
      opacity: 0.45;
    }}
    .job-title {{
      font-weight: 600;
      color: var(--navy);
      display: block;
      margin-bottom: 2px;
    }}
    .company-cell {{
      font-weight: 600;
      white-space: nowrap;
    }}
    .badge {{
      display: inline-block;
      padding: 3px 8px;
      border-radius: 6px;
      font-size: 11px;
      font-weight: 600;
      white-space: nowrap;
    }}
    .badge-confirmed {{ background: var(--green-bg); color: #065f46; border: 1px solid rgba(16,185,129,0.2); }}
    .badge-plausible {{ background: var(--amber-bg); color: #92400e; border: 1px solid rgba(245,158,11,0.2); }}
    .badge-na {{ background: var(--blue-bg); color: #1e40af; border: 1px solid rgba(59,130,246,0.2); }}
    .badge-unknown {{ background: #f1f5f9; color: #475569; }}
    .badge-strong {{ background: var(--green-bg); color: #065f46; }}
    .badge-good {{ background: var(--blue-bg); color: #1e40af; }}
    .badge-stretch {{ background: var(--amber-bg); color: #92400e; }}
    
    .badge-skill {{
      background: #f1f5f9;
      color: #334155;
      border: 1px solid #cbd5e1;
      font-size: 10px;
      padding: 2px 6px;
      border-radius: 4px;
      display: inline-block;
      margin-top: 3px;
      margin-right: 3px;
    }}
    .user-fit-note {{
      font-size: 11px;
      color: #0369a1;
      margin-top: 4px;
      font-weight: 500;
      line-height: 1.4;
    }}

    .btn-apply {{
      display: inline-block;
      padding: 6px 12px;
      background: var(--primary);
      color: #fff;
      border-radius: 6px;
      font-weight: 600;
      font-size: 12px;
      text-decoration: none;
      transition: background 0.15s;
      white-space: nowrap;
      text-align: center;
    }}
    .btn-apply:hover {{
      background: #1e3a8a;
    }}
    .btn-referral {{
      display: inline-block;
      padding: 5px 8px;
      background: #f8fafc;
      color: #0f172a;
      border: 1px solid #cbd5e1;
      border-radius: 6px;
      font-weight: 600;
      font-size: 11px;
      cursor: pointer;
      transition: all 0.15s;
      white-space: nowrap;
      text-align: center;
    }}
    .btn-referral:hover {{
      background: #e2e8f0;
      color: #1e40af;
      border-color: #93c5fd;
    }}
    .btn-track {{
      padding: 5px 10px;
      border: 1px solid #cbd5e1;
      border-radius: 6px;
      font-size: 11px;
      font-weight: 600;
      cursor: pointer;
      background: #fff;
      color: var(--text-muted);
      transition: all 0.15s;
      white-space: nowrap;
    }}
    .btn-track:hover {{
      background: #f1f5f9;
      color: var(--text-main);
    }}
    .btn-track.applied {{
      background: var(--green);
      color: #fff;
      border-color: var(--green);
    }}
    .btn-icon {{
      border: none;
      background: transparent;
      cursor: pointer;
      font-size: 14px;
      color: #94a3b8;
      padding: 4px;
      border-radius: 4px;
    }}
    .btn-icon:hover {{
      color: #ef4444;
      background: #fee2e2;
    }}
    .action-group {{
      display: flex;
      align-items: center;
      gap: 6px;
    }}
    .sub-text {{
      font-size: 11px;
      color: var(--text-muted);
      margin-top: 3px;
    }}
    footer {{
      text-align: center;
      padding: 32px;
      color: var(--text-muted);
      font-size: 13px;
    }}
  </style>
</head>
<body>
  <header>
    <div class="header-content">
      <div>
        <h1>🎯 Machine Learning & Data Science Job Tracker</h1>
        <p>Curated verified-open roles matched to candidate skills across India, UK & Australia</p>
      </div>
      <div class="refresh-badge">
        <span class="pulse"></span> Last Updated: {now_ist}
      </div>
    </div>
  </header>

  <main>
    <!-- Dynamic Candidate Profile Banner -->
    <section class="user-profile-bar">
      <div class="user-info-group">
        <div class="user-avatar" id="userAvatar">CM</div>
        <div class="user-details">
          <div class="user-name-row">
            <label for="selUser" style="font-size:12px;font-weight:700;color:var(--text-muted);letter-spacing:0.04em;">CANDIDATE:</label>
            <select id="selUser" class="user-dropdown" aria-label="Select candidate user"></select>
          </div>
          <div class="user-title-tag" id="userTargetRole">Senior Machine Learning Engineer & Applied Scientist</div>
          <div class="user-skills-wrap" id="userSkillsPills"></div>
        </div>
      </div>
      <div class="user-actions">
        <button class="btn-action" id="btnEditContact" title="Update candidate contact information">⚙️ Candidate Info</button>
        <button class="btn-action" id="btnSyncTelegram" style="background:#0284c7;color:#fff;border-color:#0284c7;font-weight:600;" title="Open Telegram with pre-filled /applied command">📲 Sync to Telegram</button>
      </div>
    </section>

    <!-- Dynamic KPI Grid (Changes per candidate) -->
    <section class="kpi-grid">
      <div class="kpi-card highlight">
        <div class="lbl">Total Matched Roles</div>
        <div class="val" id="kpiTotal">0</div>
      </div>
      <div class="kpi-card applied-kpi">
        <div class="lbl">Applied by Candidate</div>
        <div class="val" id="kpiApplied">0</div>
      </div>
      <div class="kpi-card">
        <div class="lbl">India Roles</div>
        <div class="val" id="kpiIndia">0</div>
      </div>
      <div class="kpi-card">
        <div class="lbl">UK & Australia</div>
        <div class="val" id="kpiIntl">0</div>
      </div>
      <div class="kpi-card">
        <div class="lbl">Visa Confirmed</div>
        <div class="val" id="kpiVisa">0</div>
      </div>
      <div class="kpi-card">
        <div class="lbl">Target Companies</div>
        <div class="val" id="kpiCompanies">0</div>
      </div>
    </section>

    <!-- Dynamic Charts Grid (Updates per candidate) -->
    <section class="charts-grid">
      <div class="chart-box">
        <h3>Top Hiring Companies</h3>
        <div class="chart-container"><canvas id="chartCompany"></canvas></div>
      </div>
      <div class="chart-box">
        <h3>Roles by Location</h3>
        <div class="chart-container"><canvas id="chartLocation"></canvas></div>
      </div>
      <div class="chart-box">
        <h3>Visa Sponsorship Status</h3>
        <div class="chart-container"><canvas id="chartVisa"></canvas></div>
      </div>
    </section>

    <!-- Filter & Table Card -->
    <section class="table-card">
      <div class="filter-bar">
        <select id="selUserFilter" class="status-select" title="Switch candidate user"></select>
        <input type="search" id="searchQ" class="search-input" placeholder="🔍 Search company, role title, skills, ID…">
        <select id="selStatus" class="status-select">
          <option value="all">All Roles</option>
          <option value="unapplied" selected>Unapplied Only (Active)</option>
          <option value="applied">Applied Only (Tracker)</option>
          <option value="skipped">Skipped / Hidden</option>
        </select>
        <select id="selCountry"><option value="">All Countries</option></select>
        <select id="selCity"><option value="">All Locations</option></select>
        <select id="selCompany"><option value="">All Companies</option></select>
        <select id="selVisa"><option value="">All Sponsorship</option></select>
        <select id="selExp"><option value="">All Experience Fit</option></select>
        <button class="btn-action" id="btnCopyApplied" title="Copy comma-separated list of applied Job IDs">📋 Copy IDs</button>
        <button class="btn-action" id="btnReset">Reset</button>
        <span class="counter-tag" id="rowCounter">0 roles</span>
      </div>

      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th onclick="sortTable('id')">ID</th>
              <th>Status</th>
              <th onclick="sortTable('company')">Company</th>
              <th onclick="sortTable('title')">Job Title</th>
              <th onclick="sortTable('city')">Location</th>
              <th onclick="sortTable('expCat')">Fit</th>
              <th>Technical & Skill Match</th>
              <th onclick="sortTable('visaCat')">Visa Sponsorship</th>
              <th>Application</th>
            </tr>
          </thead>
          <tbody id="jobsTbody"></tbody>
        </table>
      </div>
    </section>
  </main>

  <footer>
    <p>Curated automatically via ATS feeds &middot; Scraped pool categorized per user skills txt &middot; Amazon subsidiaries strictly excluded</p>
  </footer>

  <!-- Embedded Refined Dataset -->
  <script id="jobs-data" type="application/json">{refined_json_str}</script>

  <script>
    // Load dataset from embedded script tag (with fallback)
    let DATA = JSON.parse(document.getElementById('jobs-data').textContent);

    let state = {{
      user: DATA.default_user || Object.keys(DATA.users)[0],
      search: '',
      status: 'unapplied',
      country: '',
      city: '',
      company: '',
      visa: '',
      exp: '',
      sortKey: 'id',
      sortAsc: true
    }};

    let appliedJobs = new Set();
    let skippedJobs = new Set();

    let chartCompanyInstance = null;
    let chartLocationInstance = null;
    let chartVisaInstance = null;

    // Initialize User Dropdowns
    function initUserDropdowns() {{
      const selUser = document.getElementById('selUser');
      const selUserFilter = document.getElementById('selUserFilter');
      
      selUser.innerHTML = '';
      selUserFilter.innerHTML = '';

      Object.entries(DATA.users || {{}}).forEach(([uid, u]) => {{
        const opt = document.createElement('option');
        opt.value = uid;
        opt.textContent = `${{u.name}} (${{u.stats ? u.stats.total : (u.jobs ? u.jobs.length : 0)}} roles)`;
        selUser.appendChild(opt);

        const opt2 = opt.cloneNode(true);
        selUserFilter.appendChild(opt2);
      }});

      selUser.addEventListener('change', e => switchUser(e.target.value));
      selUserFilter.addEventListener('change', e => switchUser(e.target.value));
    }}

    // Switch active candidate user and re-calculate all stats, charts, and table
    function switchUser(userId) {{
      if (!DATA.users || !DATA.users[userId]) {{
        userId = Object.keys(DATA.users)[0];
      }}
      state.user = userId;
      const user = DATA.users[userId];

      // Sync dropdowns
      document.getElementById('selUser').value = userId;
      document.getElementById('selUserFilter').value = userId;

      // Update Profile Banner
      const initials = (user.name || userId)
        .split(' ')
        .map(n => n[0])
        .join('')
        .substring(0, 2)
        .toUpperCase();
      document.getElementById('userAvatar').textContent = initials;
      document.getElementById('userTargetRole').textContent = `${{user.role || 'Candidate'}} · ${{user.experience || ''}}`;

      // Update skills pills
      const pillsContainer = document.getElementById('userSkillsPills');
      if (pillsContainer) {{
        const topSkills = (user.skills || []).slice(0, 7);
        pillsContainer.innerHTML = topSkills.map(s => `<span class="skill-pill">${{s}}</span>`).join('');
      }}

      // Load per-user tracking from localStorage
      const storedApplied = localStorage.getItem('applied_jobs_' + userId);
      const storedSkipped = localStorage.getItem('skipped_jobs_' + userId);

      if (storedApplied !== null) {{
        appliedJobs = new Set(JSON.parse(storedApplied));
      }} else if (userId === 'chandan') {{
        // Seamless migration for initial chandan user
        appliedJobs = new Set(JSON.parse(localStorage.getItem('applied_jobs') || '[]'));
      }} else {{
        appliedJobs = new Set();
      }}

      if (storedSkipped !== null) {{
        skippedJobs = new Set(JSON.parse(storedSkipped));
      }} else if (userId === 'chandan') {{
        skippedJobs = new Set(JSON.parse(localStorage.getItem('skipped_jobs') || '[]'));
      }} else {{
        skippedJobs = new Set();
      }}

      // Update dropdown filters for this user's jobs
      const userJobs = user.jobs || [];
      updateFilterDropdowns(userJobs);

      // Recalculate stats & update KPI cards
      updateStats(userJobs);

      // Re-render Charts
      renderCharts(userJobs);

      // Re-render Table
      renderTable();
    }}

    function populateDropdown(id, items, defaultLabel) {{
      const el = document.getElementById(id);
      const curVal = el.value;
      el.innerHTML = `<option value="">${{defaultLabel}}</option>`;
      const unique = [...new Set(items.filter(Boolean))].sort();
      unique.forEach(item => {{
        const opt = document.createElement('option');
        opt.value = item;
        opt.textContent = item;
        if (item === curVal) opt.selected = true;
        el.appendChild(opt);
      }});
    }}

    function updateFilterDropdowns(jobs) {{
      populateDropdown('selCountry', jobs.map(j => j.country), 'All Countries');
      populateDropdown('selCity', jobs.map(j => j.city), 'All Locations');
      populateDropdown('selCompany', jobs.map(j => j.company), 'All Companies');
      populateDropdown('selVisa', jobs.map(j => j.visaCat), 'All Sponsorship');
      populateDropdown('selExp', jobs.map(j => j.expCat), 'All Experience Fit');
    }}

    function updateStats(jobs) {{
      const user = DATA.users[state.user] || {{}};
      const currentJobs = jobs || (user.jobs || []);

      document.getElementById('kpiTotal').textContent = currentJobs.length;
      document.getElementById('kpiApplied').textContent = appliedJobs.size;
      document.getElementById('kpiIndia').textContent = currentJobs.filter(j => j.country === 'India').length;
      document.getElementById('kpiIntl').textContent = currentJobs.filter(j => j.country === 'UK' || j.country === 'Australia' || (j.country !== 'India' && j.country)).length;
      document.getElementById('kpiVisa').textContent = currentJobs.filter(j => j.visaCat === 'Confirmed' || (j.visaCat && j.visaCat.includes('Plausible'))).length;
      document.getElementById('kpiCompanies').textContent = new Set(currentJobs.map(j => j.company).filter(Boolean)).size;
    }}

    function renderCharts(jobs) {{
      // 1. Top Hiring Companies Chart
      const compCounts = {{}};
      jobs.forEach(j => {{
        if (j.company) compCounts[j.company] = (compCounts[j.company] || 0) + 1;
      }});
      const topComps = Object.entries(compCounts).sort((a,b) => b[1] - a[1]).slice(0, 10);

      if (chartCompanyInstance) chartCompanyInstance.destroy();
      chartCompanyInstance = new Chart(document.getElementById('chartCompany'), {{
        type: 'bar',
        data: {{
          labels: topComps.map(c => c[0]),
          datasets: [{{
            data: topComps.map(c => c[1]),
            backgroundColor: '#3b82f6',
            borderRadius: 4
          }}]
        }},
        options: {{
          indexAxis: 'y',
          responsive: true,
          maintainAspectRatio: false,
          plugins: {{ legend: {{ display: false }} }},
          scales: {{ x: {{ ticks: {{ stepSize: 1 }} }} }}
        }}
      }});

      // 2. Roles by Location Chart
      const locCounts = {{ 'India': 0, 'UK': 0, 'Australia': 0, 'Global / Other': 0 }};
      jobs.forEach(j => {{
        if (locCounts[j.country] !== undefined) {{
          locCounts[j.country]++;
        }} else {{
          locCounts['Global / Other']++;
        }}
      }});
      const activeLocs = Object.entries(locCounts).filter(([k, v]) => v > 0);

      if (chartLocationInstance) chartLocationInstance.destroy();
      chartLocationInstance = new Chart(document.getElementById('chartLocation'), {{
        type: 'doughnut',
        data: {{
          labels: activeLocs.map(x => x[0]),
          datasets: [{{
            data: activeLocs.map(x => x[1]),
            backgroundColor: ['#10b981', '#3b82f6', '#f59e0b', '#8b5cf6'],
            borderWidth: 0
          }}]
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          plugins: {{ legend: {{ position: 'bottom' }} }}
        }}
      }});

      // 3. Visa Sponsorship Chart
      const visaCounts = {{}};
      jobs.forEach(j => {{
        const k = j.visaCat || 'Unknown';
        visaCounts[k] = (visaCounts[k] || 0) + 1;
      }});

      if (chartVisaInstance) chartVisaInstance.destroy();
      chartVisaInstance = new Chart(document.getElementById('chartVisa'), {{
        type: 'doughnut',
        data: {{
          labels: Object.keys(visaCounts),
          datasets: [{{
            data: Object.values(visaCounts),
            backgroundColor: ['#10b981', '#f59e0b', '#3b82f6', '#94a3b8'],
            borderWidth: 0
          }}]
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          plugins: {{ legend: {{ position: 'bottom' }} }}
        }}
      }});
    }}

    function renderTable() {{
      const user = DATA.users[state.user] || {{}};
      const userJobs = user.jobs || [];
      const tbody = document.getElementById('jobsTbody');

      const filtered = userJobs.filter(j => {{
        const q = state.search.toLowerCase();
        const matchesQ = !q || (j.company + ' ' + j.title + ' ' + j.location + ' ' + j.tech + ' ' + j.id + ' ' + (j.matched_skills || []).join(' ')).toLowerCase().includes(q);
        const matchesCountry = !state.country || j.country === state.country;
        const matchesCity = !state.city || j.city === state.city;
        const matchesCompany = !state.company || j.company === state.company;
        const matchesVisa = !state.visa || j.visaCat === state.visa;
        const matchesExp = !state.exp || j.expCat === state.exp;

        const isApplied = appliedJobs.has(j.id);
        const isSkipped = skippedJobs.has(j.id);

        let matchesStatus = true;
        if (state.status === 'unapplied') {{
          matchesStatus = !isApplied && !isSkipped;
        }} else if (state.status === 'applied') {{
          matchesStatus = isApplied;
        }} else if (state.status === 'skipped') {{
          matchesStatus = isSkipped;
        }}

        return matchesQ && matchesCountry && matchesCity && matchesCompany && matchesVisa && matchesExp && matchesStatus;
      }});

      filtered.sort((a, b) => {{
        let vA = a[state.sortKey] || '';
        let vB = b[state.sortKey] || '';
        if (typeof vA === 'string') vA = vA.toLowerCase();
        if (typeof vB === 'string') vB = vB.toLowerCase();
        return (vA < vB ? -1 : vA > vB ? 1 : 0) * (state.sortAsc ? 1 : -1);
      }});

      document.getElementById('rowCounter').textContent = `${{filtered.length}} of ${{userJobs.length}} roles for ${{user.name || state.user}}`;

      tbody.innerHTML = filtered.map(j => {{
        const isApplied = appliedJobs.has(j.id);
        const isSkipped = skippedJobs.has(j.id);

        const vClass = j.visaCat === 'Confirmed' ? 'badge-confirmed' :
                       (j.visaCat && j.visaCat.includes('Plausible')) ? 'badge-plausible' :
                       (j.visaCat && j.visaCat.includes('N/A')) ? 'badge-na' : 'badge-unknown';

        const eClass = j.expCat === 'Strong' ? 'badge-strong' :
                       j.expCat === 'Stretch' ? 'badge-stretch' : 'badge-good';

        const applyBtn = j.link && j.link.startsWith('http')
          ? `<a href="${{j.link}}" target="_blank" class="btn-apply">Direct Apply ↗</a>`
          : `<span class="sub-text">Unverified</span>`;

        const trackBtn = isApplied
          ? `<button class="btn-track applied" onclick="toggleApplied('${{j.id}}')">Applied ✅</button>`
          : `<button class="btn-track" onclick="toggleApplied('${{j.id}}')">Mark Applied</button>`;

        const skipBtn = isSkipped
          ? `<button class="btn-icon" title="Restore role" onclick="toggleSkipped('${{j.id}}')">↩️</button>`
          : `<button class="btn-icon" title="Not interested / Hide" onclick="toggleSkipped('${{j.id}}')">✕</button>`;

        const rowClass = isApplied ? 'is-applied' : isSkipped ? 'is-skipped' : '';

        const skillBadges = (j.matched_skills && j.matched_skills.length)
          ? j.matched_skills.slice(0, 3).map(s => `<span class="badge-skill">${{s}}</span>`).join('')
          : '';

        const fitNote = j.user_fit_reason ? `<div class="user-fit-note">🎯 ${{j.user_fit_reason}}</div>` : '';

        return `
          <tr class="${{rowClass}}">
            <td><code>${{j.id}}</code></td>
            <td>
              <div class="action-group">
                ${{trackBtn}}
                ${{skipBtn}}
              </div>
            </td>
            <td class="company-cell">${{j.company}}</td>
            <td>
              <span class="job-title">${{j.title}}</span>
              <div class="sub-text">📅 ${{j.posted}}</div>
            </td>
            <td>
              <div>${{j.city}}</div>
              <div class="sub-text">${{j.country}}</div>
            </td>
            <td><span class="badge ${{eClass}}">${{j.expCat}}</span></td>
            <td>
              <div>${{j.tech}}</div>
              ${{fitNote}}
              <div style="margin-top:4px;">${{skillBadges}}</div>
            </td>
            <td><span class="badge ${{vClass}}">${{j.visaCat}}</span></td>
            <td>
              <div style="display:flex;flex-direction:column;gap:5px;">
                ${{applyBtn}}
                <button class="btn-referral" onclick="copyReferral('${{j.id}}')" title="Copy personalized LinkedIn referral message">💬 Referral Note</button>
              </div>
            </td>
          </tr>
        `;
      }}).join('');
    }}

    window.toggleApplied = function(id) {{
      if (appliedJobs.has(id)) {{
        appliedJobs.delete(id);
      }} else {{
        appliedJobs.add(id);
        skippedJobs.delete(id);
      }}
      localStorage.setItem('applied_jobs_' + state.user, JSON.stringify([...appliedJobs]));
      localStorage.setItem('skipped_jobs_' + state.user, JSON.stringify([...skippedJobs]));
      if (state.user === 'chandan') {{
        localStorage.setItem('applied_jobs', JSON.stringify([...appliedJobs]));
        localStorage.setItem('skipped_jobs', JSON.stringify([...skippedJobs]));
      }}
      const user = DATA.users[state.user] || {{}};
      updateStats(user.jobs || []);
      renderTable();
    }};

    window.toggleSkipped = function(id) {{
      if (skippedJobs.has(id)) {{
        skippedJobs.delete(id);
      }} else {{
        skippedJobs.add(id);
        appliedJobs.delete(id);
      }}
      localStorage.setItem('applied_jobs_' + state.user, JSON.stringify([...appliedJobs]));
      localStorage.setItem('skipped_jobs_' + state.user, JSON.stringify([...skippedJobs]));
      if (state.user === 'chandan') {{
        localStorage.setItem('applied_jobs', JSON.stringify([...appliedJobs]));
        localStorage.setItem('skipped_jobs', JSON.stringify([...skippedJobs]));
      }}
      const user = DATA.users[state.user] || {{}};
      updateStats(user.jobs || []);
      renderTable();
    }};

    window.sortTable = function(key) {{
      if (state.sortKey === key) {{
        state.sortAsc = !state.sortAsc;
      }} else {{
        state.sortKey = key;
        state.sortAsc = true;
      }}
      renderTable();
    }};

    window.copyReferral = function(id) {{
      const user = DATA.users[state.user] || {{}};
      const j = (user.jobs || []).find(item => item.id === id);
      if (!j) return;

      const curName = localStorage.getItem('user_name_' + state.user) || user.name || 'Candidate';
      const curPhone = localStorage.getItem('user_phone_' + state.user) || user.phone || '';
      const curEmail = localStorage.getItem('user_email_' + state.user) || user.email || '';

      const msg = `Hi [Name],\\n\\nI hope you're having a great week! I came across the ${{j.title}} opening at ${{j.company}} (${{j.id}}) and felt my background in ${{user.skills_summary || 'Machine Learning & AI'}} is a strong fit.\\n\\nCould you please refer me for this position?\\n- Name: ${{curName}}\\n- Email: ${{curEmail}}\\n- Phone: ${{curPhone}}\\n- Requisition / Link: ${{j.link}}\\n\\nThank you so much for your time and help!\\nBest regards,\\n${{curName}}`;

      navigator.clipboard.writeText(msg).then(() => {{
        alert(`Personalized referral message for ${{j.company}} copied to clipboard!`);
      }});
    }};

    // Event listeners
    document.getElementById('searchQ').addEventListener('input', e => {{
      state.search = e.target.value;
      renderTable();
    }});
    document.getElementById('selStatus').addEventListener('change', e => {{
      state.status = e.target.value;
      renderTable();
    }});
    document.getElementById('selCountry').addEventListener('change', e => {{
      state.country = e.target.value;
      renderTable();
    }});
    document.getElementById('selCity').addEventListener('change', e => {{
      state.city = e.target.value;
      renderTable();
    }});
    document.getElementById('selCompany').addEventListener('change', e => {{
      state.company = e.target.value;
      renderTable();
    }});
    document.getElementById('selVisa').addEventListener('change', e => {{
      state.visa = e.target.value;
      renderTable();
    }});
    document.getElementById('selExp').addEventListener('change', e => {{
      state.exp = e.target.value;
      renderTable();
    }});

    document.getElementById('btnReset').addEventListener('click', () => {{
      state.search = '';
      state.status = 'all';
      state.country = '';
      state.city = '';
      state.company = '';
      state.visa = '';
      state.exp = '';
      state.sortKey = 'id';
      state.sortAsc = true;
      document.getElementById('searchQ').value = '';
      document.getElementById('selStatus').value = 'all';
      document.getElementById('selCountry').value = '';
      document.getElementById('selCity').value = '';
      document.getElementById('selCompany').value = '';
      document.getElementById('selVisa').value = '';
      document.getElementById('selExp').value = '';
      renderTable();
    }});

    document.getElementById('btnCopyApplied').addEventListener('click', () => {{
      const list = [...appliedJobs].join(', ');
      if (!list) {{
        alert('No jobs marked as applied yet for this candidate! Click "Mark Applied" on any row.');
        return;
      }}
      navigator.clipboard.writeText(list).then(() => {{
        alert(`Copied ${{appliedJobs.size}} applied job IDs to clipboard:\\n${{list}}`);
      }});
    }});

    document.getElementById('btnSyncTelegram').addEventListener('click', () => {{
      if (appliedJobs.size === 0) {{
        alert('No jobs marked as applied yet! Click "Mark Applied" on any row first.');
        return;
      }}
      const idList = [...appliedJobs].join(' ');
      const tgUrl = `https://t.me/jobsearch_chan23_bot?text=${{encodeURIComponent('/applied ' + idList)}}`;
      window.open(tgUrl, '_blank');
    }});

    document.getElementById('btnEditContact').addEventListener('click', () => {{
      const user = DATA.users[state.user] || {{}};
      const curName = localStorage.getItem('user_name_' + state.user) || user.name || '';
      const curPhone = localStorage.getItem('user_phone_' + state.user) || user.phone || '';
      const curEmail = localStorage.getItem('user_email_' + state.user) || user.email || '';

      const n = prompt(`Enter Full Name for ${{user.name}}:`, curName);
      if (n !== null && n.trim()) {{
        localStorage.setItem('user_name_' + state.user, n.trim());
        user.name = n.trim();
      }}

      const p = prompt(`Enter Phone Number for ${{user.name}}:`, curPhone);
      if (p !== null && p.trim()) {{
        localStorage.setItem('user_phone_' + state.user, p.trim());
        user.phone = p.trim();
      }}

      const e = prompt(`Enter Email Address for ${{user.name}}:`, curEmail);
      if (e !== null && e.trim()) {{
        localStorage.setItem('user_email_' + state.user, e.trim());
        user.email = e.trim();
      }}

      switchUser(state.user);
      alert('Contact details updated for ' + user.name);
    }});

    // Initialize application
    initUserDropdowns();
    switchUser(state.user);
  </script>
</body>
</html>
"""
    out_html = PROJECT_DIR / "index.html"
    with open(out_html, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[build_site] Generated standalone web dashboard with multi-user filtering at {out_html}")

if __name__ == "__main__":
    build_dashboard()
