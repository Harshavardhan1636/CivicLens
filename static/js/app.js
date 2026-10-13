/* CivicLens — Frontend Logic */
let issues = [];
let currentCategory = 'all';
let currentDetailId = null;
let map = null;
let markers = [];
let view = 'grid';

const CATS = [
  { id: 'all', label: 'All reports', color: null },
  { id: 'pothole', label: 'Pothole', color: '#b54407' },
  { id: 'garbage', label: 'Garbage', color: '#5b5b5b' },
  { id: 'streetlight', label: 'Streetlight', color: '#8a7300' },
  { id: 'water', label: 'Water', color: '#1d70b8' },
  { id: 'drainage', label: 'Drainage', color: '#158187' },
  { id: 'other', label: 'Other', color: '#505a5f' },
];

const STATUS_CLASS = { 'Open': 'badge-open', 'In-Progress': 'badge-inprogress', 'Resolved': 'badge-resolved' };

function upvoteLabel(n) {
  return `${n} upvote${n === 1 ? '' : 's'}`;
}

function catDot(cat) {
  const c = CATS.find(x => x.id === cat);
  if (!c || !c.color) return '';
  return `<span class="cat-dot" style="background:${c.color}"></span>`;
}

// ── Init ──
document.addEventListener('DOMContentLoaded', () => {
  renderCatPills();
  fetchIssues();
  fetchStats();
  showWelcomeOnce();
});

// First-visit hint: show once, remember dismissal
function showWelcomeOnce() {
  try {
    if (!localStorage.getItem('civiclens_welcomed')) {
      document.getElementById('welcomeBar').hidden = false;
    }
  } catch {
    document.getElementById('welcomeBar').hidden = false;
  }
}
function dismissWelcome() {
  document.getElementById('welcomeBar').hidden = true;
  try { localStorage.setItem('civiclens_welcomed', '1'); } catch {}
}

// Close any open modal with Escape
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    closeReportModal();
    closeDetailModal();
    document.getElementById('aboutModal').classList.remove('open');
  }
});

function renderCatPills() {
  const el = document.getElementById('catPills');
  el.innerHTML = CATS.map(c => `
    <button class="cat-pill ${c.id===currentCategory?'active':''}" onclick="selectCategory('${c.id}')" aria-pressed="${c.id===currentCategory}">
      ${c.color ? `<span class="cat-dot" style="background:${c.color}"></span>` : ''}${c.label}
    </button>
  `).join('');
}

function selectCategory(cat) {
  currentCategory = cat;
  renderCatPills();
  fetchIssues();
}

function setView(v) {
  view = v;
  document.getElementById('btnGrid').classList.toggle('active', v === 'grid');
  document.getElementById('btnMap').classList.toggle('active', v === 'map');
  const grid = document.getElementById('issuesGrid');
  const empty = document.getElementById('emptyState');
  const mapEl = document.getElementById('map');
  if (v === 'map') {
    grid.classList.add('grid-hidden');
    empty.style.display = 'none';
    mapEl.classList.remove('map-hidden');
    initMap();
    renderMapMarkers();
    setTimeout(() => map && map.invalidateSize(), 150);
  } else {
    grid.classList.remove('grid-hidden');
    mapEl.classList.add('map-hidden');
    renderGrid();
  }
}

// ── Fetch ──
async function fetchIssues() {
  const status = document.getElementById('statusFilter').value;
  const search = document.getElementById('searchInput').value.trim();
  const sort = document.getElementById('sortSelect').value;
  const params = new URLSearchParams();
  if (currentCategory !== 'all') params.set('category', currentCategory);
  if (status !== 'all') params.set('status', status);
  if (search) params.set('search', search);
  params.set('sort', sort);
  try {
    const res = await fetch('/api/issues?' + params.toString());
    issues = await res.json();
    if (view === 'grid') renderGrid();
    else renderMapMarkers();
  } catch (e) {
    console.error(e);
    toast('Failed to load issues', 'error');
  }
}

async function fetchStats() {
  try {
    const res = await fetch('/api/stats');
    const s = await res.json();
    document.getElementById('statTotal').textContent = s.total;
    document.getElementById('statOpen').textContent = s.open;
    document.getElementById('statResolved').textContent = s.resolved;
  } catch {}
}

let debounceTimer;
function debouncedFetch() {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(fetchIssues, 350);
}

// ── Render Grid ──
function renderGrid() {
  const grid = document.getElementById('issuesGrid');
  const empty = document.getElementById('emptyState');
  if (!issues.length) {
    grid.innerHTML = '';
    empty.style.display = '';
    return;
  }
  empty.style.display = 'none';
  grid.innerHTML = issues.map(iss => {
    const img = iss.image_path
      ? `<img src="/uploads/${iss.image_path}" alt="" loading="lazy">`
      : `<div class="no-image"><i class="fa-solid fa-image"></i></div>`;
    const statusCls = STATUS_CLASS[iss.status] || 'badge-open';
    return `
    <div class="issue-card" onclick="openDetail('${iss.id}')">
      <div class="card-image">${img}
        <div class="card-badges">
          <span class="badge badge-category">${catDot(iss.category)}${iss.category}</span>
          <span class="badge ${statusCls}">${iss.status}</span>
        </div>
      </div>
      <div class="card-body">
        <div class="card-title">${esc(iss.title)}</div>
        <div class="card-desc">${esc(iss.description)}</div>
        <div class="card-meta">
          <span><i class="fa-solid fa-location-dot"></i> ${esc(iss.address)}</span>
        </div>
      </div>
      <div class="card-footer">
        <button class="upvote-btn" onclick="event.stopPropagation(); upvote('${iss.id}')" title="Upvote — pushes this report higher so it gets fixed sooner">
          <i class="fa-solid fa-arrow-up"></i> ${iss.upvotes}
        </button>
        <span class="card-date"><i class="fa-regular fa-clock"></i> ${timeAgo(iss.created_at)}</span>
      </div>
    </div>`;
  }).join('');
}

// ── Map ──
function initMap() {
  if (map) return;
  map = L.map('map').setView([18.5204, 73.8567], 11);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap', maxZoom: 19
  }).addTo(map);
}

function renderMapMarkers() {
  if (!map) return;
  markers.forEach(m => map.removeLayer(m));
  markers = [];
  if (!issues.length) return;
  const bounds = [];
  issues.forEach(iss => {
    const color = iss.status === 'Resolved' ? '#00703c' : iss.status === 'In-Progress' ? '#1d70b8' : '#b54407';
    const marker = L.circleMarker([iss.latitude, iss.longitude], {
      radius: 9, fillColor: color, color: '#fff', weight: 2, fillOpacity: 0.95
    }).addTo(map);
    marker.bindPopup(`
      <div style="min-width:180px">
        <strong style="font-size:13px">${esc(iss.title)}</strong><br>
        <span style="font-size:11px; color:#505a5f">${iss.category} · ${iss.status} · ${iss.upvotes} upvotes</span><br>
        <span style="font-size:12px; color:#0b0c0c">${esc(iss.address)}</span><br>
        <button onclick="openDetail('${iss.id}')" style="margin-top:6px; background:#00703c; color:#fff; border:none; padding:5px 10px; border-radius:4px; font-size:12px; cursor:pointer">View details</button>
      </div>
    `);
    markers.push(marker);
    bounds.push([iss.latitude, iss.longitude]);
  });
  if (bounds.length) map.fitBounds(bounds, { padding: [30, 30], maxZoom: 14 });
}

// ── Report Modal ──
function openReportModal() {
  document.getElementById('reportModal').classList.add('open');
  document.getElementById('formError').classList.remove('show');
}
function closeReportModal() {
  document.getElementById('reportModal').classList.remove('open');
  document.getElementById('reportForm').reset();
  document.getElementById('formError').classList.remove('show');
  document.getElementById('submitBtn').disabled = false;
  document.getElementById('submitBtn').textContent = 'Submit report';
}

function useMyLocation() {
  if (!navigator.geolocation) return toast('Geolocation not supported', 'error');
  const btn = document.querySelector('.btn-locate');
  btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Locating…';
  navigator.geolocation.getCurrentPosition(pos => {
    document.getElementById('f_lat').value = pos.coords.latitude.toFixed(6);
    document.getElementById('f_lng').value = pos.coords.longitude.toFixed(6);
    btn.innerHTML = '<i class="fa-solid fa-location-crosshairs"></i> Use my location';
    toast('Location captured!', 'success');
  }, err => {
    btn.innerHTML = '<i class="fa-solid fa-location-crosshairs"></i> Use my location';
    toast('Could not get location: ' + err.message, 'error');
  });
}

async function submitReport(e) {
  e.preventDefault();
  const errEl = document.getElementById('formError');
  errEl.classList.remove('show');
  const btn = document.getElementById('submitBtn');
  btn.disabled = true;
  btn.textContent = 'Submitting…';

  const fd = new FormData();
  fd.append('title', document.getElementById('f_title').value.trim());
  fd.append('category', document.getElementById('f_category').value);
  fd.append('description', document.getElementById('f_description').value.trim());
  fd.append('address', document.getElementById('f_address').value.trim());
  fd.append('latitude', document.getElementById('f_lat').value.trim());
  fd.append('longitude', document.getElementById('f_lng').value.trim());
  const fileInput = document.getElementById('f_image');
  if (fileInput.files[0]) fd.append('image', fileInput.files[0]);

  try {
    const res = await fetch('/api/issues', { method: 'POST', body: fd });
    const data = await res.json();
    if (!res.ok) {
      const msg = data.errors ? data.errors.join('<br>') : (data.error || 'Failed to submit');
      errEl.innerHTML = msg;
      errEl.classList.add('show');
      btn.disabled = false;
      btn.textContent = 'Submit report';
      return;
    }
    closeReportModal();
    toast('Issue reported successfully!', 'success');
    fetchIssues();
    fetchStats();
  } catch (err) {
    errEl.textContent = 'Network error. Please try again.';
    errEl.classList.add('show');
    btn.disabled = false;
    btn.textContent = 'Submit report';
  }
}

// ── Detail Modal ──
function openDetail(id) {
  const iss = issues.find(x => x.id === id);
  if (!iss) return;
  currentDetailId = id;
  document.getElementById('d_title').textContent = iss.title;
  document.getElementById('d_meta').textContent = `${iss.category} · ${timeAgo(iss.created_at)} · ${upvoteLabel(iss.upvotes)}`;
  document.getElementById('d_desc').textContent = iss.description;
  document.getElementById('d_address').textContent = iss.address;
  document.getElementById('d_coords').textContent = `${iss.latitude.toFixed(5)}, ${iss.longitude.toFixed(5)}`;
  document.getElementById('d_date').textContent = new Date(iss.created_at).toLocaleString();
  document.getElementById('d_upvotes').textContent = iss.upvotes;

  const badges = document.getElementById('d_badges');
  const sc = STATUS_CLASS[iss.status] || 'badge-open';
  badges.innerHTML = `<span class="badge badge-category">${catDot(iss.category)}${iss.category}</span><span class="badge ${sc}">${iss.status}</span>`;

  const wrap = document.getElementById('d_image_wrap');
  wrap.innerHTML = iss.image_path ? `<img class="detail-image" src="/uploads/${iss.image_path}" alt="">` : '';

  // highlight active status btn
  document.getElementById('btnStatusOpen').className = 'status-btn' + (iss.status === 'Open' ? ' active-open' : '');
  document.getElementById('btnStatusProgress').className = 'status-btn' + (iss.status === 'In-Progress' ? ' active-progress' : '');
  document.getElementById('btnStatusResolved').className = 'status-btn' + (iss.status === 'Resolved' ? ' active-resolved' : '');

  document.getElementById('detailModal').classList.add('open');
}
function closeDetailModal() {
  document.getElementById('detailModal').classList.remove('open');
  currentDetailId = null;
}

async function changeStatus(status) {
  if (!currentDetailId) return;
  try {
    const res = await fetch(`/api/issues/${currentDetailId}/status`, {
      method: 'PATCH', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status })
    });
    if (!res.ok) { const d = await res.json(); return toast(d.error || 'Failed', 'error'); }
    const updated = await res.json();
    const idx = issues.findIndex(x => x.id === currentDetailId);
    if (idx !== -1) issues[idx] = updated;
    openDetail(currentDetailId);
    renderGrid();
    if (view === 'map') renderMapMarkers();
    fetchStats();
    toast(`Status → ${status}`, 'success');
  } catch { toast('Network error', 'error'); }
}

async function upvoteDetail() {
  if (!currentDetailId) return;
  await upvote(currentDetailId);
  const iss = issues.find(x => x.id === currentDetailId);
  if (iss) {
    document.getElementById('d_upvotes').textContent = iss.upvotes;
    document.getElementById('d_meta').textContent = `${iss.category} · ${timeAgo(iss.created_at)} · ${upvoteLabel(iss.upvotes)}`;
  }
}

async function upvote(id) {
  try {
    const res = await fetch(`/api/issues/${id}/upvote`, { method: 'POST' });
    if (!res.ok) return toast('Failed to upvote', 'error');
    const updated = await res.json();
    const idx = issues.findIndex(x => x.id === id);
    if (idx !== -1) issues[idx] = updated;
    renderGrid();
    if (view === 'map') renderMapMarkers();
    toast('Upvoted! Priority increased.', 'success');
  } catch { toast('Network error', 'error'); }
}

async function deleteDetail() {
  if (!currentDetailId || !confirm('Delete this issue permanently?')) return;
  try {
    const res = await fetch(`/api/issues/${currentDetailId}`, { method: 'DELETE' });
    if (!res.ok) return toast('Delete failed', 'error');
    closeDetailModal();
    toast('Issue deleted', 'success');
    fetchIssues();
    fetchStats();
  } catch { toast('Network error', 'error'); }
}

// ── Utils ──
function esc(s) {
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}
function timeAgo(iso) {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  if (days < 7) return `${days}d ago`;
  return new Date(iso).toLocaleDateString();
}
function toast(msg, type='') {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.className = 'toast show ' + type;
  clearTimeout(el._t);
  el._t = setTimeout(() => el.className = 'toast ' + type, 2800);
}
