// Sentinel Dashboard — pure Canvas 2D, zero dependencies
const API = '';
const COLORS = {
  critical: '#f85149', high: '#d29922', medium: '#e3b341',
  low: '#3fb950', info: '#58a6ff',
  blue: '#58a6ff', green: '#3fb950', purple: '#bc8cff',
  cyan: '#39c5cf', orange: '#db6d28', pink: '#f778ba',
};
const SEVERITY_ORDER = ['critical', 'high', 'medium', 'low', 'info'];

let state = { stats: null, issues: [], files: [], duplicates: [], techDebt: null };

// ── Tab switching ──────────────────────────────────────────────────
document.querySelectorAll('.tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    tab.classList.add('active');
    document.getElementById(tab.dataset.tab).classList.add('active');
    renderTab(tab.dataset.tab);
  });
});

document.getElementById('refreshBtn').addEventListener('click', loadAll);

// ── Data loading ────────────────────────────────────────────────────
async function fetchJSON(url) {
  const r = await fetch(API + url);
  return r.json();
}

async function loadAll() {
  try {
    const [stats, issues, files, duplicates, techDebt] = await Promise.all([
      fetchJSON('/api/stats'),
      fetchJSON('/api/issues?limit=500'),
      fetchJSON('/api/files'),
      fetchJSON('/api/duplicates'),
      fetchJSON('/api/tech-debt'),
    ]);
    state = { stats, issues, files, duplicates, techDebt };
    renderTab('overview');
  } catch (e) {
    console.error('Load failed:', e);
  }
}

function renderTab(tab) {
  switch (tab) {
    case 'overview': renderOverview(); break;
    case 'issues': renderIssues(); break;
    case 'files': renderFiles(); break;
    case 'security': renderSecurity(); break;
    case 'complexity': renderComplexity(); break;
    case 'duplicates': renderDuplicates(); break;
    case 'techdebt': renderTechDebt(); break;
  }
}

// ── Overview ────────────────────────────────────────────────────────
function renderOverview() {
  if (!state.stats) return;
  const s = state.stats;
  const grid = document.getElementById('statsGrid');
  const cards = [
    { label: 'Quality Score', value: s.quality_score, cls: s.quality_score >= 80 ? 'good' : s.quality_score >= 60 ? 'medium' : 'critical' },
    { label: 'Grade', value: s.grade, cls: 'info' },
    { label: 'Risk Level', value: s.risk_level.toUpperCase(), cls: s.risk_level },
    { label: 'Total Issues', value: s.total_issues, cls: s.total_issues > 0 ? 'high' : 'good' },
    { label: 'Files Scanned', value: s.files_scanned, cls: 'info' },
    { label: 'Files w/ Issues', value: s.files_with_issues, cls: 'medium' },
    { label: 'Tech Debt', value: s.tech_debt, cls: 'high' },
    { label: 'Issues/KLOC', value: s.issues_per_kloc, cls: 'low' },
  ];
  grid.innerHTML = cards.map(c =>
    `<div class="stat-card"><div class="label">${c.label}</div><div class="value ${c.cls}">${c.value}</div></div>`
  ).join('');

  drawSeverityChart();
  drawCategoryChart();
  drawTopFilesChart();
}

// ── Canvas helpers ──────────────────────────────────────────────────
function setupCanvas(id) {
  const canvas = document.getElementById(id);
  const ctx = canvas.getContext('2d');
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  canvas.width = rect.width * dpr;
  canvas.height = rect.height * dpr;
  ctx.scale(dpr, dpr);
  return { ctx, w: rect.width, h: rect.height };
}

function drawBarChart(canvasId, data, options = {}) {
  const { ctx, w, h } = setupCanvas(canvasId);
  ctx.clearRect(0, 0, w, h);
  const pad = { top: 20, right: 20, bottom: 50, left: 60 };
  const cw = w - pad.left - pad.right;
  const ch = h - pad.top - pad.bottom;
  const maxVal = Math.max(...data.map(d => d.value), 1);

  // Grid
  ctx.strokeStyle = '#21262d';
  ctx.lineWidth = 1;
  for (let i = 0; i <= 4; i++) {
    const y = pad.top + (ch / 4) * i;
    ctx.beginPath(); ctx.moveTo(pad.left, y); ctx.lineTo(w - pad.right, y); ctx.stroke();
    ctx.fillStyle = '#8b949e';
    ctx.font = '11px sans-serif';
    ctx.textAlign = 'right';
    ctx.fillText(Math.round(maxVal - (maxVal / 4) * i), pad.left - 8, y + 4);
  }

  // Bars
  const barW = Math.min(40, (cw / data.length) * 0.6);
  const gap = cw / data.length;
  data.forEach((d, i) => {
    const x = pad.left + gap * i + (gap - barW) / 2;
    const barH = (d.value / maxVal) * ch;
    const y = pad.top + ch - barH;
    ctx.fillStyle = d.color || COLORS.blue;
    ctx.beginPath();
    ctx.roundRect(x, y, barW, barH, [3, 3, 0, 0]);
    ctx.fill();
    // Label
    ctx.fillStyle = '#8b949e';
    ctx.font = '10px sans-serif';
    ctx.textAlign = 'center';
    ctx.save();
    ctx.translate(x + barW / 2, h - pad.bottom + 12);
    ctx.rotate(-0.4);
    ctx.fillText(d.label.length > 14 ? d.label.slice(0, 12) + '..' : d.label, 0, 0);
    ctx.restore();
    // Value
    if (d.value > 0) {
      ctx.fillStyle = '#c9d1d9';
      ctx.font = 'bold 11px sans-serif';
      ctx.fillText(d.value, x + barW / 2, y - 5);
    }
  });
}

function drawHorizontalBarChart(canvasId, data, options = {}) {
  const { ctx, w, h } = setupCanvas(canvasId);
  ctx.clearRect(0, 0, w, h);
  const pad = { top: 10, right: 40, bottom: 20, left: 200 };
  const cw = w - pad.left - pad.right;
  const ch = h - pad.top - pad.bottom;
  const maxVal = Math.max(...data.map(d => d.value), 1);
  const rowH = Math.min(30, ch / data.length);

  data.forEach((d, i) => {
    const y = pad.top + rowH * i + 4;
    const barW = (d.value / maxVal) * cw;
    // Label
    ctx.fillStyle = '#c9d1d9';
    ctx.font = '11px monospace';
    ctx.textAlign = 'right';
    ctx.fillText(d.label.length > 28 ? '...' + d.label.slice(-26) : d.label, pad.left - 8, y + rowH / 2 + 4);
    // Bar
    ctx.fillStyle = d.color || COLORS.blue;
    ctx.beginPath();
    ctx.roundRect(pad.left, y, Math.max(barW, 2), rowH - 8, [0, 3, 3, 0]);
    ctx.fill();
    // Value
    if (d.value > 0) {
      ctx.fillStyle = '#c9d1d9';
      ctx.font = 'bold 11px sans-serif';
      ctx.textAlign = 'left';
      ctx.fillText(d.value, pad.left + barW + 6, y + rowH / 2 + 4);
    }
  });
}

function drawDonutChart(canvasId, data) {
  const { ctx, w, h } = setupCanvas(canvasId);
  ctx.clearRect(0, 0, w, h);
  const cx = w / 2, cy = h / 2;
  const radius = Math.min(w, h) / 2 - 30;
  const innerR = radius * 0.55;
  const total = data.reduce((s, d) => s + d.value, 0) || 1;
  let start = -Math.PI / 2;

  data.forEach(d => {
    if (d.value === 0) return;
    const angle = (d.value / total) * Math.PI * 2;
    ctx.beginPath();
    ctx.arc(cx, cy, radius, start, start + angle);
    ctx.arc(cx, cy, innerR, start + angle, start, true);
    ctx.closePath();
    ctx.fillStyle = d.color;
    ctx.fill();
    // Label
    if (d.value > total * 0.05) {
      const mid = start + angle / 2;
      const lx = cx + Math.cos(mid) * (radius + innerR) / 2;
      const ly = cy + Math.sin(mid) * (radius + innerR) / 2;
      ctx.fillStyle = '#fff';
      ctx.font = 'bold 12px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(d.value, lx, ly + 4);
    }
    start += angle;
  });

  // Center text
  ctx.fillStyle = '#c9d1d9';
  ctx.font = 'bold 22px sans-serif';
  ctx.textAlign = 'center';
  ctx.fillText(total, cx, cy - 2);
  ctx.fillStyle = '#8b949e';
  ctx.font = '11px sans-serif';
  ctx.fillText('total', cx, cy + 16);
}

// ── Specific charts ──────────────────────────────────────────────────
function drawSeverityChart() {
  const data = SEVERITY_ORDER.map(s => ({
    label: s.toUpperCase(),
    value: state.issues.filter(i => i.severity === s).length,
    color: COLORS[s],
  }));
  drawDonutChart('severityChart', data);
}

function drawCategoryChart() {
  const cats = {};
  state.issues.forEach(i => { cats[i.category] = (cats[i.category] || 0) + 1; });
  const data = Object.entries(cats).sort((a, b) => b[1] - a[1]).map(([k, v], i) => ({
    label: k, value: v, color: Object.values(COLORS)[i % 12],
  }));
  drawBarChart('categoryChart', data);
}

function drawTopFilesChart() {
  const top = state.files.slice(0, 10).filter(f => f.issue_count > 0);
  const data = top.map(f => ({
    label: f.path.split('/').pop() || f.path,
    value: f.issue_count,
    color: f.issue_count > 5 ? COLORS.red : f.issue_count > 2 ? COLORS.orange : COLORS.yellow,
  }));
  if (data.length === 0) {
    const { ctx, w, h } = setupCanvas('topFilesChart');
    ctx.clearRect(0, 0, w, h);
    ctx.fillStyle = '#8b949e';
    ctx.font = '14px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('No files with issues — great job!', w / 2, h / 2);
    return;
  }
  drawHorizontalBarChart('topFilesChart', data);
}

// ── Issues tab ───────────────────────────────────────────────────────
function renderIssues() {
  const tbody = document.querySelector('#issuesTable tbody');
  const sevFilter = document.getElementById('severityFilter').value;
  const search = document.getElementById('issueSearch').value.toLowerCase();

  let filtered = state.issues;
  if (sevFilter) filtered = filtered.filter(i => i.severity === sevFilter);
  if (search) filtered = filtered.filter(i =>
    i.message.toLowerCase().includes(search) ||
    i.file.toLowerCase().includes(search) ||
    i.rule_id.toLowerCase().includes(search)
  );

  document.getElementById('issueCount').textContent = `${filtered.length} issues`;

  tbody.innerHTML = filtered.slice(0, 300).map(i => `
    <tr>
      <td><span class="badge ${i.severity}">${i.severity.toUpperCase()}</span></td>
      <td><code>${i.rule_id}</code></td>
      <td><code>${i.file}</code></td>
      <td>${i.line}</td>
      <td>${i.message}</td>
    </tr>
  `).join('');
}

document.getElementById('severityFilter').addEventListener('change', renderIssues);
document.getElementById('issueSearch').addEventListener('input', renderIssues);

// ── Files tab ────────────────────────────────────────────────────────
function renderFiles() {
  // Table
  const tbody = document.querySelector('#filesTable tbody');
  tbody.innerHTML = state.files.map(f => `
    <tr>
      <td><code>${f.path}</code></td>
      <td>${f.language}</td>
      <td>${f.lines}</td>
      <td>${f.code_lines}</td>
      <td>${f.functions}</td>
      <td style="color:${f.max_complexity > 10 ? COLORS.red : f.max_complexity > 5 ? COLORS.orange : COLORS.green}">${f.max_complexity}</td>
      <td><span class="badge ${f.issue_count > 5 ? 'critical' : f.issue_count > 2 ? 'high' : f.issue_count > 0 ? 'medium' : 'low'}">${f.issue_count}</span></td>
    </tr>
  `).join('');

  // Bubble chart
  drawFileBubbles();
}

function drawFileBubbles() {
  const { ctx, w, h } = setupCanvas('fileBubblesChart');
  ctx.clearRect(0, 0, w, h);
  const files = state.files.filter(f => f.issue_count > 0).slice(0, 30);
  if (files.length === 0) {
    ctx.fillStyle = '#8b949e';
    ctx.font = '14px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('No files with issues!', w / 2, h / 2);
    return;
  }

  // Simple circle packing
  const bubbles = files.map((f, i) => ({
    x: w / 2 + (Math.random() - 0.5) * w * 0.6,
    y: h / 2 + (Math.random() - 0.5) * h * 0.6,
    r: Math.max(8, Math.sqrt(f.issue_count) * 12),
    file: f,
    color: f.issue_count > 5 ? COLORS.red : f.issue_count > 2 ? COLORS.orange : f.issue_count > 1 ? COLORS.yellow : COLORS.blue,
  }));

  // Collision resolution
  for (let iter = 0; iter < 80; iter++) {
    for (let i = 0; i < bubbles.length; i++) {
      for (let j = i + 1; j < bubbles.length; j++) {
        const a = bubbles[i], b = bubbles[j];
        const dx = b.x - a.x, dy = b.y - a.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const minDist = a.r + b.r + 2;
        if (dist < minDist) {
          const push = (minDist - dist) / 2;
          const nx = dx / dist, ny = dy / dist;
          a.x -= nx * push; a.y -= ny * push;
          b.x += nx * push; b.y += ny * push;
        }
      }
    }
  }

  // Keep in bounds
  bubbles.forEach(b => {
    b.x = Math.max(b.r + 5, Math.min(w - b.r - 5, b.x));
    b.y = Math.max(b.r + 5, Math.min(h - b.r - 5, b.y));
  });

  // Draw
  bubbles.forEach(b => {
    ctx.beginPath();
    ctx.arc(b.x, b.y, b.r, 0, Math.PI * 2);
    ctx.fillStyle = b.color + '40';
    ctx.fill();
    ctx.strokeStyle = b.color;
    ctx.lineWidth = 2;
    ctx.stroke();
    // Label
    const name = b.file.path.split('/').pop();
    ctx.fillStyle = '#c9d1d9';
    ctx.font = `${Math.min(11, b.r / 2.5)}px sans-serif`;
    ctx.textAlign = 'center';
    if (b.r > 15) ctx.fillText(name.slice(0, 12), b.x, b.y - 2);
    ctx.font = `bold ${Math.min(14, b.r / 2)}px sans-serif`;
    ctx.fillText(b.file.issue_count, b.x, b.y + 12);
  });
}

// ── Security tab ─────────────────────────────────────────────────────
function renderSecurity() {
  const secIssues = state.issues.filter(i => i.category === 'security');
  const statsGrid = document.getElementById('securityStats');
  const crit = secIssues.filter(i => i.severity === 'critical').length;
  const high = secIssues.filter(i => i.severity === 'high').length;
  statsGrid.innerHTML = `
    <div class="stat-card"><div class="label">Security Issues</div><div class="value ${crit > 0 ? 'critical' : high > 0 ? 'high' : 'good'}">${secIssues.length}</div></div>
    <div class="stat-card"><div class="label">Critical</div><div class="value critical">${crit}</div></div>
    <div class="stat-card"><div class="label">High</div><div class="value high">${high}</div></div>
    <div class="stat-card"><div class="label">Affected Files</div><div class="value info">${new Set(secIssues.map(i => i.file)).size}</div></div>
  `;

  // Rules chart
  const rules = {};
  secIssues.forEach(i => { rules[i.rule_id + ' ' + i.rule_name] = (rules[i.rule_id + ' ' + i.rule_name] || 0) + 1; });
  const data = Object.entries(rules).sort((a, b) => b[1] - a[1]).map(([k, v]) => ({
    label: k, value: v, color: COLORS.red,
  }));
  if (data.length > 0) {
    drawHorizontalBarChart('securityRulesChart', data);
  }

  // Table
  const tbody = document.querySelector('#securityTable tbody');
  tbody.innerHTML = secIssues.slice(0, 100).map(i => `
    <tr>
      <td><span class="badge ${i.severity}">${i.severity.toUpperCase()}</span></td>
      <td><code>${i.rule_id}</code></td>
      <td><code>${i.file}</code></td>
      <td>${i.line}</td>
      <td>${i.message}</td>
      <td style="color:#8b949e;font-size:0.75rem">${i.suggestion || ''}</td>
    </tr>
  `).join('');
}

// ── Complexity tab ───────────────────────────────────────────────────
function renderComplexity() {
  const complexFiles = state.files.filter(f => f.max_complexity > 0);
  const highComplex = state.files.filter(f => f.max_complexity > 10);
  const totalFuncs = state.files.reduce((s, f) => s + f.functions, 0);

  document.getElementById('complexityStats').innerHTML = `
    <div class="stat-card"><div class="label">Total Functions</div><div class="value info">${totalFuncs}</div></div>
    <div class="stat-card"><div class="label">Files w/ Complexity</div><div class="value medium">${complexFiles.length}</div></div>
    <div class="stat-card"><div class="label">High Complexity (>10)</div><div class="value ${highComplex.length > 0 ? 'critical' : 'good'}">${highComplex.length}</div></div>
    <div class="stat-card"><div class="label">Max Complexity</div><div class="value ${state.files.length && Math.max(...state.files.map(f => f.max_complexity)) > 10 ? 'critical' : 'low'}">${state.files.length ? Math.max(...state.files.map(f => f.max_complexity)) : 0}</div></div>
  `;

  // Distribution
  const dist = { '1-5': 0, '6-10': 0, '11-20': 0, '20+': 0 };
  state.files.forEach(f => {
    if (f.max_complexity > 0) {
      if (f.max_complexity <= 5) dist['1-5']++;
      else if (f.max_complexity <= 10) dist['6-10']++;
      else if (f.max_complexity <= 20) dist['11-20']++;
      else dist['20+']++;
    }
  });
  drawBarChart('complexityDistChart', Object.entries(dist).map(([k, v]) => ({
    label: k, value: v, color: v > 0 ? COLORS.orange : COLORS.green,
  })));

  // Lines vs Functions scatter
  drawScatterChart('linesFuncsChart', state.files.filter(f => f.code_lines > 0).slice(0, 50));

  // Table
  const tbody = document.querySelector('#complexityTable tbody');
  tbody.innerHTML = state.files.filter(f => f.max_complexity > 0)
    .sort((a, b) => b.max_complexity - a.max_complexity).slice(0, 50).map(f => `
    <tr>
      <td><code>${f.path}</code></td>
      <td>${f.functions}</td>
      <td style="color:${f.max_complexity > 10 ? COLORS.red : f.max_complexity > 5 ? COLORS.orange : COLORS.green}">${f.max_complexity}</td>
      <td>${f.avg_complexity}</td>
      <td>${f.code_lines}</td>
    </tr>
  `).join('');
}

function drawScatterChart(canvasId, data) {
  const { ctx, w, h } = setupCanvas(canvasId);
  ctx.clearRect(0, 0, w, h);
  const pad = { top: 20, right: 20, bottom: 40, left: 50 };
  const cw = w - pad.left - pad.right;
  const ch = h - pad.top - pad.bottom;
  const maxX = Math.max(...data.map(d => d.code_lines), 1);
  const maxY = Math.max(...data.map(d => d.functions), 1);

  ctx.strokeStyle = '#21262d';
  for (let i = 0; i <= 4; i++) {
    const y = pad.top + (ch / 4) * i;
    ctx.beginPath(); ctx.moveTo(pad.left, y); ctx.lineTo(w - pad.right, y); ctx.stroke();
  }

  data.forEach(d => {
    const x = pad.left + (d.code_lines / maxX) * cw;
    const y = pad.top + ch - (d.functions / maxY) * ch;
    const r = Math.max(3, Math.sqrt(d.issue_count) * 3);
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.fillStyle = (d.max_complexity > 10 ? COLORS.red : d.issue_count > 0 ? COLORS.orange : COLORS.blue) + '80';
    ctx.fill();
  });

  ctx.fillStyle = '#8b949e';
  ctx.font = '10px sans-serif';
  ctx.textAlign = 'center';
  ctx.fillText('Code Lines', w / 2, h - 8);
  ctx.save();
  ctx.translate(12, h / 2);
  ctx.rotate(-Math.PI / 2);
  ctx.fillText('Functions', 0, 0);
  ctx.restore();
}

// ── Duplicates tab ───────────────────────────────────────────────────
function renderDuplicates() {
  const totalLines = state.duplicates.reduce((s, d) => s + d.line_count * d.occurrences.length, 0);
  document.getElementById('dupStats').innerHTML = `
    <div class="stat-card"><div class="label">Duplicate Blocks</div><div class="value medium">${state.duplicates.length}</div></div>
    <div class="stat-card"><div class="label">Duplicated Lines</div><div class="value high">${totalLines}</div></div>
    <div class="stat-card"><div class="label">Affected Files</div><div class="value info">${new Set(state.duplicates.flatMap(d => d.occurrences.map(o => o[0]))).size}</div></div>
  `;

  const list = document.getElementById('dupList');
  list.innerHTML = state.duplicates.slice(0, 15).map((d, i) => `
    <div class="dup-item">
      <h4>#${i + 1} — ${d.line_count} lines, ${d.occurrences.length} occurrences</h4>
      <div class="occurrences">
        ${d.occurrences.map(o => `<span class="occ">${o[0]}:${o[1]}</span>`).join('')}
      </div>
      <pre>${d.lines.slice(0, 6).join('\n')}${d.lines.length > 6 ? '\n...' : ''}</pre>
    </div>
  `).join('') || '<p style="color:#3fb950">No duplicate code found!</p>';
}

// ── Tech Debt tab ────────────────────────────────────────────────────
function renderTechDebt() {
  const d = state.techDebt;
  if (!d) return;

  document.getElementById('debtHero').innerHTML = `
    <div><div class="big-number ${d.quality_score >= 80 ? 'value good' : d.quality_score >= 60 ? 'value medium' : 'value critical'}" style="color:${d.quality_score >= 80 ? COLORS.green : d.quality_score >= 60 ? COLORS.yellow : COLORS.red}">${d.quality_score}</div><div class="big-label">Quality Score / 100</div></div>
    <div><div class="big-number" style="color:${COLORS.blue}">${d.grade}</div><div class="big-label">Grade</div></div>
    <div><div class="big-number" style="color:${d.risk_level === 'critical' ? COLORS.red : d.risk_level === 'high' ? COLORS.orange : d.risk_level === 'medium' ? COLORS.yellow : COLORS.green}">${d.risk_level.toUpperCase()}</div><div class="big-label">Risk Level</div></div>
    <div><div class="big-number" style="color:${COLORS.purple}">${d.formatted}</div><div class="big-label">Estimated Tech Debt</div></div>
    <div><div class="big-number" style="color:${COLORS.cyan}">${d.issues_per_kloc}</div><div class="big-label">Issues per KLOC</div></div>
  `;

  // Debt by severity
  const sevData = SEVERITY_ORDER.map(s => ({
    label: s.toUpperCase(),
    value: d.debt_by_severity[s] || 0,
    color: COLORS[s],
  })).filter(d => d.value > 0);
  drawBarChart('debtSeverityChart', sevData);

  // Quality breakdown
  const bd = d.breakdown;
  drawHorizontalBarChart('qualityBreakdownChart', [
    { label: 'Security Issues', value: bd.security_issues, color: COLORS.red },
    { label: 'Bug Issues', value: bd.bug_issues, color: COLORS.orange },
    { label: 'Complexity Issues', value: bd.complexity_issues, color: COLORS.yellow },
    { label: 'Style Issues', value: bd.style_issues, color: COLORS.blue },
    { label: 'Duplicate Blocks', value: bd.duplicate_blocks, color: COLORS.purple },
  ].filter(d => d.value > 0));

  // Density chart
  const densityData = state.files.filter(f => f.code_lines > 10)
    .map(f => ({
      label: f.path.split('/').pop(),
      value: Math.round((f.issue_count / f.code_lines) * 1000),
      color: (f.issue_count / f.code_lines) * 1000 > 20 ? COLORS.red : (f.issue_count / f.code_lines) * 1000 > 10 ? COLORS.orange : COLORS.green,
    }))
    .sort((a, b) => b.value - a.value).slice(0, 15);
  drawHorizontalBarChart('densityChart', densityData);
}

// ── Init ──────────────────────────────────────────────────────────────
loadAll();
