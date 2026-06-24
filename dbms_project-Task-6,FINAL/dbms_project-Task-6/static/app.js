/* ─────────────────────────────────────────────────────────
   MediCore — Emergency Hospital Management System
   Frontend SPA Logic
───────────────────────────────────────────────────────── */

// ── State ───────────────────────────────────────────────
// ── State ───────────────────────────────────────────────
const API = '';  // same-origin
let currentDischargeId = null;
let allBedsData = [];

// ── Auth Init & Logout ────────────────────────────────────
async function authInit() {
  const token = localStorage.getItem('ehrbms_token');
  const user = localStorage.getItem('ehrbms_user');
  if (!token) {
    if (window.location.pathname !== '/login') {
      window.location.href = '/login';
    }
    return;
  }
  try {
    const res = await fetch(`/api/me?token=${token}&_t=${Date.now()}`);
    if (!res.ok) throw new Error('Invalid session');
    const userObj = await res.json();
    const uSpan = document.getElementById('current-user');
    const lBtn = document.getElementById('logout-btn');
    if (uSpan) {
      const isDoc = (userObj.role && userObj.role.toLowerCase() === 'doctor');
      uSpan.textContent = userObj.username + (isDoc ? ' (Doctor)' : ' (Admin)');
    }
    if (lBtn) lBtn.style.display = 'inline-block';
    
    if (userObj.role && userObj.role.toLowerCase() === 'doctor') {
      document.body.classList.add('role-doctor');
      // Physically remove irrelevant sidebar links (keep inventory — read-only for doctors)
      const removeIds = [
        'nav-doctors', 'nav-beds',
        'nav-report-doctor-patients', 'nav-report-daily', 'nav-report-shortage'
      ];
      removeIds.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.remove();
      });
      // Remove 'Reports & Analytics' section header
      document.querySelectorAll('.nav-section-label').forEach(el => el.remove());

      if (!document.getElementById('role-style')) {
        const style = document.createElement('style');
        style.id = 'role-style';
        style.innerHTML = `
          /* Hide add/admit buttons for doctors */
          .role-doctor #page-patients .page-actions,
          .role-doctor #page-admissions .page-actions,
          .role-doctor #page-inventory .page-actions { display: none !important; }

          /* Hide Fatigued Doctors and Available Doctors stat cards by ID */
          .role-doctor #stat-card-doctors,
          .role-doctor #stat-card-fatigued { display: none !important; }

          /* Hide only the + Stock button in inventory table; keep - Use visible */
          .role-doctor #inventory-table [data-inv-action="add"] { display: none !important; }
        `;
        document.head.appendChild(style);
      }
    } else {
      document.body.classList.add('role-admin');
      // Admins can STOCK inventory but NOT use items
      if (!document.getElementById('role-admin-style')) {
        const style = document.createElement('style');
        style.id = 'role-admin-style';
        style.innerHTML = `
          /* Admin: hide the - Use button, keep + Stock visible */
          .role-admin #inventory-table [data-inv-action="use"] { display: none !important; }
        `;
        document.head.appendChild(style);
      }
    }

  } catch (err) {
    logout();
  }
}

async function logout() {
  const token = localStorage.getItem('ehrbms_token');
  if (token) {
    try {
      await fetch('/api/logout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token })
      });
    } catch (e) {}
  }
  localStorage.removeItem('ehrbms_token');
  localStorage.removeItem('ehrbms_user');
  window.location.href = '/login';
}

authInit();

// ── Clock ────────────────────────────────────────────────
function updateClock() {
  const el = document.getElementById('current-time');
  if (el) {
    const now = new Date();
    el.textContent = now.toLocaleString('en-IN', {
      weekday: 'short', day: '2-digit', month: 'short',
      hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true
    });
  }
}
setInterval(updateClock, 1000);
updateClock();

// ── Navigation ────────────────────────────────────────────
const PAGE_META = {
  dashboard:  { title: 'Dashboard',   sub: 'Overview / Live Stats' },
  patients:   { title: 'Patients',    sub: 'Manage / Add Patients' },
  admissions: { title: 'Admissions',  sub: 'Manage / Admit & Discharge' },
  doctors:    { title: 'Doctors',     sub: 'Medical Staff / Availability' },
  beds:       { title: 'Bed Monitor', sub: 'Real-time Bed Status' },
  inventory:  { title: 'Inventory',   sub: 'Resource Stock / Alerts' },
  hospitals:  { title: 'Hospitals',   sub: 'Registered Hospitals' },
};

function navigateTo(page) {
  // Update nav
  document.querySelectorAll('.nav-item').forEach(el => {
    el.classList.toggle('active', el.dataset.page === page);
  });
  // Show page
  document.querySelectorAll('.page').forEach(el => {
    el.classList.toggle('active', el.id === `page-${page}`);
  });
  // Update header
  const meta = PAGE_META[page] || { title: page, sub: '' };
  
  const titleMap = {
    'dashboard': 'Dashboard',
    'patients': 'Patient Management',
    'admissions': 'Admissions',
    'doctors': 'Medical Staff',
    'beds': 'Bed Monitor',
    'inventory': 'Inventory Management',
    'hospitals': 'Hospitals',
    'report-doctor-patients': 'Report-Doctor-Patients',
    'report-daily': 'Daily Statistics',
    'report-shortage': 'Resource Shortage'
  };
  document.getElementById('page-title').textContent = titleMap[page] || page;
  document.getElementById('breadcrumb').textContent  = meta.sub;

  // Load data
  loadPage(page);
}

document.querySelectorAll('.nav-item').forEach(el => {
  el.addEventListener('click', () => navigateTo(el.dataset.page));
});

// ── Page Loader ───────────────────────────────────────────
function loadPage(page) {
  switch (page) {
    case 'dashboard':              loadDashboard();  break;
    case 'patients':               loadPatients();   break;
    case 'admissions':             loadAdmissions(); break;
    case 'doctors':                loadDoctors();    break;
    case 'beds':                   loadBeds();       break;
    case 'inventory':              loadInventory();  break;
    case 'hospitals':              loadHospitals();  break;
    case 'report-doctor-patients': loadReportDoctorPatients(); break;
    case 'report-daily':           loadReportDaily(); break;
    case 'report-shortage':        loadReportShortage(); break;
  }
}

// ── API Helper ────────────────────────────────────────────
async function apiFetch(url, opts = {}) {
  try {
    if (!opts.headers) opts.headers = {};
    const token = localStorage.getItem('ehrbms_token');
    if (token) {
      opts.headers['Authorization'] = `Bearer ${token}`; // Backend currently uses query or body for logout
    }

    const res = await fetch(API + url, opts);
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Server error');
    return data;
  } catch (err) {
    showToast('❌ ' + err.message, 'error');
    throw err;
  }
}

// ── Toast ─────────────────────────────────────────────────
function showToast(msg, type = 'info') {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.className = `toast ${type} show`;
  setTimeout(() => t.classList.remove('show'), 3500);
}

// ── Modal ─────────────────────────────────────────────────
function openModal(id) {
  const el = document.getElementById(id);
  if (el) el.classList.add('open');
}

function closeModal(id) {
  const el = document.getElementById(id);
  if (el) el.classList.remove('open');
}

// Close on overlay click
document.querySelectorAll('.modal-overlay').forEach(overlay => {
  overlay.addEventListener('click', e => {
    if (e.target === overlay) closeModal(overlay.id);
  });
});

// ── DASHBOARD ────────────────────────────────────────────
async function loadDashboard() {
  try {
    const d = await apiFetch('/api/dashboard');
    animateNumber('stat-patients',   d.total_patients);
    animateNumber('stat-admissions', d.active_admissions);
    animateNumber('stat-beds',       d.available_beds);
    animateNumber('stat-doctors',    d.available_doctors);
    animateNumber('stat-fatigued',   d.fatigued_doctors);
    animateNumber('stat-critical',   d.critical_patients);
    animateNumber('stat-lowstock',   d.low_stock_items);
  } catch {}

  try {
    const admissions = await apiFetch('/api/admissions');
    const active = admissions.filter(a => a.status === 'Active');
    const wrap = document.getElementById('dashboard-admissions-table');
    if (!active.length) {
      wrap.innerHTML = emptyState('🏥', 'No active admissions');
      return;
    }
    wrap.innerHTML = buildTable(
      ['Patient', 'Emergency', 'Doctor', 'Specialization', 'Bed', 'Ward', 'Date'],
      active.map(a => [
        `<strong>${a.patient_name}</strong><br><small style="color:var(--text-muted)">Age ${a.patient_age}</small>`,
        levelBadge(a.emergency_level),
        a.doctor_name,
        `<span style="color:var(--text-muted)">${a.specialization}</span>`,
        `<span class="badge badge-info">Bed ${a.bed_id}</span>`,
        a.ward_type,
        fmtDate(a.admission_date)
      ])
    );
  } catch {}
}

function animateNumber(id, target) {
  const el = document.getElementById(id);
  if (!el) return;
  let start = 0;
  const step = Math.max(1, Math.ceil(target / 20));
  const timer = setInterval(() => {
    start = Math.min(start + step, target);
    el.textContent = start;
    if (start >= target) clearInterval(timer);
  }, 40);
}

// ── PATIENTS ─────────────────────────────────────────────
async function loadPatients() {
  const wrap = document.getElementById('patients-table');
  wrap.innerHTML = '<div class="loading-spinner"></div>';
  try {
    const data = await apiFetch('/api/patients');
    if (!data.length) { wrap.innerHTML = emptyState('🧑‍⚕️', 'No patients found'); return; }
    wrap.innerHTML = `<div class="grid-cards-wrapper">` + data.map(p => `
      <div class="grid-card">
        <div class="card-top">
          <div class="card-avatar-wrap">
            <img src="https://ui-avatars.com/api/?name=${encodeURIComponent(p.name)}&background=random" class="card-avatar" />
            <div class="card-status-dot" style="background:${p.current_status === 'Admitted' ? 'var(--accent-green)' : 'var(--border)'}"></div>
          </div>
          <div class="card-top-right">${levelBadge(p.emergency_level)}</div>
        </div>
        <div class="card-name">${p.name}</div>
        <div class="card-sub">${p.age} yrs &bull; ${p.gender}</div>
        <div class="card-bottom">
          <div style="font-weight:600; color:var(--text-muted)">Visited &mdash; 0</div>
          ${p.current_status !== 'Admitted'
            ? `<button class="btn btn-sm btn-outline" style="border:none; color:var(--accent-blue)" tabindex="0" title="Quick Admit" onclick="quickAdmit(${p.patient_id}, '${p.name}')">Admit ➔</button>`
            : '<span style="color:var(--accent-green)">Admitted</span>'}
        </div>
      </div>
    `).join('') + `</div>`;
  } catch {}
}

function quickAdmit(patientId, name) {
  navigateTo('admissions');
  setTimeout(() => openAdmitModal(), 300);
}

// ── ADMISSIONS ────────────────────────────────────────────
async function loadAdmissions() {
  const wrap = document.getElementById('admissions-table');
  wrap.innerHTML = '<div class="loading-spinner"></div>';
  try {
    const data = await apiFetch('/api/admissions');
    if (!data.length) { wrap.innerHTML = emptyState('🏥', 'No admissions yet'); return; }
    
    wrap.innerHTML = `<div class="grid-cards-wrapper">` + data.map(a => `
      <div class="grid-card">
        <div class="card-top">
          <img src="https://ui-avatars.com/api/?name=${encodeURIComponent(a.patient_name)}&background=random" class="card-avatar" />
          <div class="card-top-right" style="background:#e0f2fe; padding:0.2rem 0.6rem; border-radius:12px; color:var(--accent-blue)">
            ${new Date(a.admission_date).toLocaleTimeString('en-US', {hour: '2-digit', minute:'2-digit'})}
          </div>
        </div>
        <div class="card-name">${a.patient_name}</div>
        <div class="card-sub">${a.emergency_level} &nbsp;&bull;&nbsp; Bed #${a.bed_id}</div>
        <div class="card-bottom">
          <div>Visited - ${Math.floor(Math.random()*4)}</div>
          ${a.status === 'Active'
            ? `<button class="btn btn-sm" style="background:transparent; color:var(--accent-blue); font-weight:600; cursor:pointer; border:none" onclick="openDischarge(${a.admission_id}, '${a.patient_name}', '${a.doctor_name}', ${a.bed_id})" style="background:#ef4444; color:white; border:none; padding:6px 18px; border-radius:100px; font-weight:600; cursor:pointer;">Discharge</button>`
            : `<small style="color:var(--text-muted)">${statusBadge(a.status)}</small>`}
        </div>
      </div>
    `).join('') + `</div>`;
  } catch {}
}

async function openAdmitModal() {
  // Pre-populate admission ID
  const allAdm = await apiFetch('/api/admissions');
  let maxId = 600;
  allAdm.forEach(a => { if (a.admission_id > maxId) maxId = a.admission_id; });
  document.getElementById('admit-id').value = maxId + 1;
  document.getElementById('admit-date').value = todayStr();

  // Load unadmitted patients
  const patients = await apiFetch('/api/unadmitted-patients');
  const pSel = document.getElementById('admit-patient-id');
  pSel.innerHTML = patients.length
    ? patients.map(p => `<option value="${p.patient_id}">${p.name} (${p.emergency_level})</option>`).join('')
    : '<option value="">No available patients</option>';

  // Load available doctors
  const doctors = await apiFetch('/api/available-doctors');
  const dSel = document.getElementById('admit-doctor-id');
  dSel.innerHTML = doctors.length
    ? doctors.map(d => `<option value="${d.doctor_id}">${d.name} — ${d.specialization}</option>`).join('')
    : '<option value="">No available doctors</option>';

  // Load available beds
  const beds = await apiFetch('/api/available-beds');
  const bSel = document.getElementById('admit-bed-id');
  bSel.innerHTML = beds.length
    ? beds.map(b => `<option value="${b.bed_id}">Bed ${b.bed_id} — ${b.bed_type} | ${b.ward_type} | ${b.hospital_name}</option>`).join('')
    : '<option value="">No available beds</option>';

  openModal('modal-admit-patient');
}

async function submitAdmitPatient(e) {
  e.preventDefault();
  const body = {
    admission_id: parseInt(document.getElementById('admit-id').value),
    patient_id:   parseInt(document.getElementById('admit-patient-id').value),
    doctor_id:    parseInt(document.getElementById('admit-doctor-id').value),
    bed_id:       parseInt(document.getElementById('admit-bed-id').value),
    admission_date: document.getElementById('admit-date').value
  };
  try {
    const res = await apiFetch('/api/admissions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    showToast('✅ Patient admitted! Bed & Doctor updated by SQL trigger.', 'success');
    closeModal('modal-admit-patient');
    loadAdmissions();
  } catch {}
}

function openDischarge(admId, patName, docName, bedId) {
  currentDischargeId = admId;
  document.getElementById('discharge-info').innerHTML = `
    <strong>Patient:</strong> ${patName}<br>
    <strong>Doctor:</strong> ${docName}<br>
    <strong>Bed:</strong> ${bedId}
  `;
  document.getElementById('discharge-date').value = todayStr();
  openModal('modal-discharge');
}

async function submitDischarge() {
  if (!currentDischargeId) return;
  const date = document.getElementById('discharge-date').value;
  if (!date) { showToast('Please enter discharge date', 'error'); return; }
  try {
    await apiFetch(`/api/admissions/${currentDischargeId}/discharge`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ discharge_date: date })
    });
    showToast('✅ Patient discharged! Bed freed & Doctor available — via SQL trigger.', 'success');
    closeModal('modal-discharge');
    loadAdmissions();
  } catch {}
}

// ── DOCTORS ───────────────────────────────────────────────
async function loadDoctors() {
  const wrap = document.getElementById('doctors-table');
  wrap.innerHTML = '<div class="loading-spinner"></div>';
  try {
    const data = await apiFetch('/api/doctors');
    if (!data.length) { wrap.innerHTML = emptyState('👨‍⚕️', 'No doctors found'); return; }
    
    wrap.innerHTML = `<div class="grid-cards-wrapper">` + data.map(d => `
      <div class="grid-card">
        <div class="card-top">
          <div class="card-avatar-wrap">
            <img src="https://ui-avatars.com/api/?name=${encodeURIComponent(d.name)}&background=random" class="card-avatar" />
            <div class="card-status-dot" style="background:${d.availability_status==='Available'?'var(--accent-green)':(d.availability_status==='Fatigued'?'var(--accent-red)':'var(--accent-orange)')}"></div>
          </div>
          <div class="card-top-right"></div>
        </div>
        <div class="card-name">${d.name}</div>
        <div class="card-sub">
          ${d.specialization}<br>
          <small style="font-size:0.6rem; color:var(--accent-yellow)">MBBS, FCPS, FICS (USA)</small>
          ${d.availability_status === 'Fatigued' && d.fatigued_until ? `
            <div style="margin-top:0.5rem; color:var(--accent-red); font-size:0.75rem; font-weight:700">
              🕒 Fatigued until ${new Date(d.fatigued_until).toLocaleTimeString('en-US', {hour:'2-digit', minute:'2-digit'})}
            </div>` : ''}
        </div>
        <div class="card-bottom">
           <div style="flex:1">
             <select class="search-input" style="width:100%; border:none; padding:0; height:20px; font-weight:600; color:var(--text-primary); cursor:pointer; font-size:0.8rem; outline:none; appearance:none; background:transparent" onchange="updateDoctorStatus(${d.doctor_id}, this.value)">
               <option ${d.availability_status==='Available'?'selected':''}>Available</option>
               <option ${d.availability_status==='Busy'?'selected':''}>Busy</option>
               <option ${d.availability_status==='On Leave'?'selected':''}>On Leave</option>
               <option ${d.availability_status==='Fatigued'?'selected':''}>Fatigued</option>
             </select>
           </div>
           <div style="text-align:right">Sun - Fri<br><strong>10:00 am to 1:00 pm</strong></div>
        </div>
      </div>
    `).join('') + `</div>`;
  } catch {}
}

async function updateDoctorStatus(id, status) {
  try {
    await apiFetch(`/api/doctors/${id}/status`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ availability_status: status })
    });
    showToast(`✅ Doctor status updated to "${status}"`, 'success');
  } catch {}
}

// ── BEDS ──────────────────────────────────────────────────
async function loadBeds() {
  const wrap = document.getElementById('beds-table');
  wrap.innerHTML = '<div class="loading-spinner"></div>';
  try {
    allBedsData = await apiFetch('/api/beds');
    renderBedsTable(allBedsData);
  } catch {}
}

function renderBedsTable(data) {
  const wrap = document.getElementById('beds-table');
  if (!data.length) { wrap.innerHTML = emptyState('🛏️', 'No beds found'); return; }
  wrap.innerHTML = buildTable(
    ['Bed ID', 'Type', 'Status', 'Ward', 'Ward Type', 'Action'],
    data.map(b => [
      `<strong>#${b.bed_id}</strong>`,
      b.bed_type,
      bedStatusBadge(b.status),
      `Ward ${b.ward_id}`,
      b.ward_type,
      b.status !== 'Occupied'
        ? `<button class="btn-discharge" style="background:var(--accent-red);" onclick="deleteBed(${b.bed_id})">🗑 Remove</button>`
        : `<span class="badge badge-muted" title="Discharge patient first">Occupied</span>`
    ])
  );
}

function filterBeds(status, btn) {
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  const filtered = status === 'all' ? allBedsData : allBedsData.filter(b => b.status === status);
  renderBedsTable(filtered);
}

// ── ADD / REMOVE BED ──────────────────────────────────────
async function openAddBedModal() {
  // Auto-suggest next bed ID
  const allBeds = await apiFetch('/api/beds');
  let maxId = 100;
  allBeds.forEach(b => { if (b.bed_id > maxId) maxId = b.bed_id; });
  document.getElementById('new-bed-id').value = maxId + 1;
  document.getElementById('new-bed-type').value = '';

  // Populate wards dropdown
  const wards = await apiFetch('/api/wards');
  const wSel = document.getElementById('new-bed-ward');
  wSel.innerHTML = wards.length
    ? wards.map(w => `<option value="${w.ward_id}">Ward ${w.ward_id} — ${w.ward_type}</option>`).join('')
    : '<option value="">No wards available</option>';

  // Reset & open
  document.getElementById('form-add-bed').reset();
  document.getElementById('new-bed-id').value = maxId + 1;
  openModal('modal-add-bed');
}

async function submitAddBed(e) {
  e.preventDefault();
  const body = {
    bed_id:   parseInt(document.getElementById('new-bed-id').value),
    ward_id:  parseInt(document.getElementById('new-bed-ward').value),
    bed_type: document.getElementById('new-bed-type').value,
  };
  try {
    await apiFetch('/api/beds', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    showToast(`✅ Bed #${body.bed_id} (${body.bed_type}) added successfully!`, 'success');
    closeModal('modal-add-bed');
    loadBeds();
  } catch {}
}

async function deleteBed(bedId) {
  if (!confirm(`Remove Bed #${bedId}? This cannot be undone.`)) return;
  try {
    await apiFetch(`/api/beds/${bedId}`, { method: 'DELETE' });
    showToast(`🗑 Bed #${bedId} removed successfully.`, 'success');
    loadBeds();
  } catch {}
}

// ── INVENTORY ─────────────────────────────────────────────
async function loadInventory() {
  const wrap = document.getElementById('inventory-table');
  wrap.innerHTML = '<div class="loading-spinner"></div>';
  try {
    const data = await apiFetch('/api/inventory');
    const lowCount = data.filter(i => i.low_stock).length;
    const badge = document.getElementById('low-stock-badge');
    if (lowCount > 0) {
      badge.textContent = `⚠️ ${lowCount} Low Stock Item${lowCount > 1 ? 's' : ''}`;
      badge.style.display = 'inline-flex';
    } else {
      badge.style.display = 'none';
    }

    if (!data.length) { wrap.innerHTML = emptyState('📦', 'No inventory found'); return; }
    wrap.innerHTML = buildTable(
      ['Resource', 'Quantity', 'Threshold', 'Stock Level', 'Alert', 'Actions'],
      data.map(i => {
        const pct = Math.min(i.stock_percent || 0, 100);
        const fillClass = pct >= 80 ? 'fill-ok' : pct >= 40 ? 'fill-warn' : 'fill-low';
        return [
          `<strong>${i.resource_name}</strong>`,
          `<strong style="color:${i.low_stock ? '#f87171' : '#4ade80'}">${i.quantity}</strong>`,
          i.threshold_level,
          `<div class="stock-bar-wrap">
             <div class="stock-bar">
               <div class="stock-bar-fill ${fillClass}" style="width:${pct}%"></div>
             </div>
             <span class="stock-pct">${pct}%</span>
           </div>`,
          i.low_stock
            ? '<span class="badge badge-danger">⚠️ Low Stock</span>'
            : '<span class="badge badge-success">✅ OK</span>',
          `<div style="display:flex;gap:0.5rem">
             <button class="btn btn-sm btn-outline" data-inv-action="add" style="color:var(--accent-green)" onclick="openUpdateStockModal(${i.inventory_id}, '${i.resource_name.replace(/'/g, "\\'")}', 'add')">＋ Stock</button>
             <button class="btn btn-sm btn-outline" data-inv-action="use" style="color:var(--accent-red)" onclick="openUpdateStockModal(${i.inventory_id}, '${i.resource_name.replace(/'/g, "\\'")}', 'use')">－ Use</button>
           </div>`
        ];
      })
    );
  } catch {}
}

async function openUpdateStockModal(invId, resName, action) {
  document.getElementById('stock-inv-id').value = invId;
  document.getElementById('stock-action').value = action;
  
  const title = document.getElementById('update-stock-title');
  const label = document.getElementById('stock-action-label');
  const btn = document.getElementById('stock-submit-btn');
  
  if (action === 'add') {
    title.innerHTML = `📦 Add Stock: ${resName}`;
    label.textContent = "Add";
    btn.textContent = "Add to Stock";
    btn.className = "btn btn-primary";
  } else {
    title.innerHTML = `📦 Use Stock: ${resName}`;
    label.textContent = "Use";
    btn.textContent = "Consume Stock";
    btn.className = "btn btn-danger";
  }
  
  document.getElementById('stock-amount').value = '';
  openModal('modal-update-stock');
}

async function submitUpdateStock(e) {
  e.preventDefault();
  const invId = document.getElementById('stock-inv-id').value;
  const action = document.getElementById('stock-action').value;
  const amount = parseInt(document.getElementById('stock-amount').value);
  
  try {
    await apiFetch(`/api/inventory/${invId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action, amount })
    });
    showToast(action === 'add' ? `✅ Stock added successfully.` : `✅ Stock consumed successfully.`, 'success');
    closeModal('modal-update-stock');
    loadInventory();
  } catch {}
}

async function openNewItemModal() {
  document.getElementById('form-new-item').reset();
  const hSel = document.getElementById('new-item-hospital');
  hSel.innerHTML = '<option value="">-- Loading hospitals --</option>';
  openModal('modal-new-item');
  
  try {
    const hosps = await apiFetch('/api/hospitals');
    hSel.innerHTML = hosps.length 
      ? hosps.map(h => `<option value="${h.hospital_id}">${h.name} (${h.location})</option>`).join('')
      : '<option value="">No hospitals available</option>';
  } catch {}
}

async function submitNewItem(e) {
  e.preventDefault();
  const body = {
    resource_name: document.getElementById('new-item-name').value.trim(),
    hospital_id: parseInt(document.getElementById('new-item-hospital').value),
    quantity: parseInt(document.getElementById('new-item-quantity').value),
    threshold_level: parseInt(document.getElementById('new-item-threshold').value)
  };
  
  try {
    await apiFetch('/api/inventory', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    showToast(`✅ Added ${body.resource_name} tracking successfully!`, 'success');
    closeModal('modal-new-item');
    loadInventory();
  } catch {}
}

// ── HOSPITALS ─────────────────────────────────────────────
async function loadHospitals() {
  const grid = document.getElementById('hospitals-cards');
  if (!grid) return;
  
  grid.innerHTML = '<div class="loading-spinner"></div>';
  try {
    const data = await apiFetch('/api/hospitals');
    if (!data.length) {
      grid.innerHTML = '<div class="empty-state">No hospitals registered</div>';
      return;
    }
    
    grid.className = 'grid-cards-wrapper';
    
    grid.innerHTML = data.map(h => `
      <div class="grid-card">
        <div class="card-top">
          <div class="card-avatar-wrap">
            <div style="width:60px; height:60px; background:var(--bg-card-hover); border-radius:16px; display:flex; align-items:center; justify-content:center; font-size:1.8rem; box-shadow:0 4px 10px rgba(0,0,0,0.05)">🏥</div>
          </div>
          <div class="card-top-right" style="font-size:0.8rem">ID #${h.hospital_id}</div>
        </div>
        
        <div class="card-name">${h.name}</div>
        <div class="card-sub" style="margin-bottom:1.5rem">
          <span style="color:var(--text-secondary)">📍 ${h.location}</span><br>
          <small>📞 ${h.contact_no}</small>
        </div>
        
        <div class="card-bottom" style="border-top: 1px dashed var(--border); padding-top: 1rem; margin-top: auto;">
          <div>Wards<br><strong>${h.total_wards || '?'}</strong></div>
          <div>Total Beds<br><strong>${h.total_beds}</strong></div>
          <div>Available<br><strong style="color:var(--accent-teal)">${h.available_beds || 0}</strong></div>
        </div>
      </div>
    `).join('');
  } catch (err) {
    grid.innerHTML = '<div class="error-msg">Failed to load hospitals</div>';
  }
}
// ── REPORT: DOCTOR-PATIENTS ─────────────────────────────
async function loadReportDoctorPatients() {
  const wrap = document.getElementById('dp-table');
  if (!wrap) return;
  wrap.innerHTML = '<div class="loading-spinner"></div>';
  try {
    const data = await apiFetch('/api/reports/doctor-patients');
    if (!data.length) { wrap.innerHTML = emptyState('🔗', 'No active doctor assignments found.'); return; }
    
    wrap.innerHTML = buildTable(
      ['Doctor', 'Current Patient', 'Emergency', 'Admission Date'],
      data.map(r => [
        `<strong>${r.doctor_name}</strong><br><small style="color:var(--text-muted)">${r.specialization}</small>`,
        `<strong>${r.patient_name}</strong><br><small style="color:var(--text-muted)">Age ${r.age} | ID #${r.patient_id}</small>`,
        levelBadge(r.emergency_level),
        fmtDate(r.admission_date)
      ])
    );
  } catch {}
}


// ── REPORT: DAILY STATS ─────────────────────────────────
async function loadReportDaily() {
  const wrap = document.getElementById('daily-table');
  wrap.innerHTML = '<div class="loading-spinner"></div>';
  try {
    const data = await apiFetch('/api/reports/daily-stats');
    if (!data.length) { wrap.innerHTML = emptyState('📅', 'No historic data'); return; }

    wrap.innerHTML = buildTable(
      ['Date', 'New Admissions', 'Patient Discharges', 'Net Change'],
      data.map(r => {
        const net = r.admissions - r.discharges;
        const netStr = net > 0 ? `<span style="color:var(--accent-red)">+${net}</span>` :
                       net < 0 ? `<span style="color:var(--accent-green)">${net}</span>` : '0';
        return [
          `<strong>${fmtDate(r.day)}</strong>`,
          `<span style="color:var(--text-primary)">${r.admissions}</span>`,
          `<span style="color:var(--text-muted)">${r.discharges}</span>`,
          netStr
        ];
      })
    );
  } catch {}
}

// ── REPORT: RESOURCE SHORTAGE ───────────────────────────
async function loadReportShortage() {
  const wrap = document.getElementById('shortage-table');
  wrap.innerHTML = '<div class="loading-spinner"></div>';
  try {
    const data = await apiFetch('/api/reports/resource-shortage');
    if (!data.length) { wrap.innerHTML = emptyState('✅', 'All resources are above threshold levels.'); return; }

    wrap.innerHTML = buildTable(
      ['Resource', 'Current Qty', 'Min Threshold', 'Shortage', 'Stock Level'],
      data.map(r => {
         const pct = Math.max(0, r.stock_pct);
         return [
          `<strong>${r.resource_name}</strong>`,
          `<span style="color:var(--accent-red); font-weight:700">${r.quantity}</span>`,
          r.threshold_level,
          `<span class="badge badge-danger">-${r.shortage_amount} units</span>`,
          `<div class="stock-bar-wrap">
             <div class="stock-bar">
               <div class="stock-bar-fill fill-low" style="width:${pct}%"></div>
             </div>
             <span class="stock-pct">${pct}%</span>
           </div>`
        ];
      })
    );
  } catch {}
}

// ── FORMS ─────────────────────────────────────────────────
async function submitAddPatient(e) {
  e.preventDefault();
  const body = {
    patient_id:      parseInt(document.getElementById('new-patient-id').value),
    name:            document.getElementById('new-patient-name').value.trim(),
    age:             parseInt(document.getElementById('new-patient-age').value),
    gender:          document.getElementById('new-patient-gender').value,
    emergency_level: document.getElementById('new-patient-emergency').value,
  };
  try {
    await apiFetch('/api/patients', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    showToast(`✅ Patient "${body.name}" added successfully!`, 'success');
    closeModal('modal-add-patient');
    document.getElementById('form-add-patient').reset();
    loadPatients();
  } catch {}
}

// ── TABLE BUILDER ─────────────────────────────────────────
function buildTable(headers, rows) {
  const ths = headers.map(h => `<th>${h}</th>`).join('');
  const trs = rows.map(r =>
    `<tr>${r.map(c => `<td>${c ?? '—'}</td>`).join('')}</tr>`
  ).join('');
  return `<table><thead><tr>${ths}</tr></thead><tbody>${trs}</tbody></table>`;
}

// ── TABLE FILTER ──────────────────────────────────────────
function filterTable(tableId, query) {
  const wrap = document.getElementById(tableId);
  if (!wrap) return;
  const q = query.toLowerCase();
  
  // Try rows first (for legacy tables if any are left)
  const rows = wrap.querySelectorAll('tbody tr');
  if (rows.length > 0) {
    rows.forEach(row => {
      row.style.display = row.textContent.toLowerCase().includes(q) ? '' : 'none';
    });
    return;
  }
  
  // Try grid cards
  const cards = wrap.querySelectorAll('.grid-card');
  cards.forEach(card => {
    card.style.display = card.textContent.toLowerCase().includes(q) ? 'flex' : 'none';
  });
}

// ── BADGE HELPERS ─────────────────────────────────────────
function levelBadge(level) {
  const map = {
    Critical: 'badge-danger',
    High:     'badge-warning',
    Medium:   'badge-info',
    Low:      'badge-success'
  };
  return `<span class="badge ${map[level] || 'badge-muted'}">${level || '—'}</span>`;
}

function statusBadge(status) {
  const map = {
    Active:      'badge-success',
    Discharged:  'badge-muted',
    Transferred: 'badge-warning'
  };
  return `<span class="badge ${map[status] || 'badge-muted'}">${status}</span>`;
}

function bedStatusBadge(status) {
  const map = {
    Available:   'badge-success',
    Occupied:    'badge-danger',
    Maintenance: 'badge-warning'
  };
  return `<span class="badge ${map[status] || 'badge-muted'}">${status}</span>`;
}

function docStatusBadge(status) {
  const map = {
    Available: 'badge-success',
    Busy:      'badge-danger',
    'On Leave':'badge-warning',
    Fatigued:  'badge-danger'
  };
  return `<span class="badge ${map[status] || 'badge-muted'}">${status}</span>`;
}

function emptyState(icon, msg) {
  return `<div class="empty-state">
    <div class="empty-state-icon">${icon}</div>
    <p>${msg}</p>
  </div>`;
}

// ── UTILS ─────────────────────────────────────────────────
function fmtDate(dateStr) {
  if (!dateStr) return '—';
  const d = new Date(dateStr);
  return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
}

function todayStr() {
  return new Date().toISOString().split('T')[0];
}

// ── INIT ──────────────────────────────────────────────────
loadDashboard();

// Admit patient button from admissions page
document.addEventListener('click', e => {
  const btn = e.target.closest('[onclick="openModal(\'modal-admit-patient\')"]');
  if (btn) { openAdmitModal(); }
});

// Override the static onclick on the Admit Patient button
document.querySelectorAll('[onclick="openModal(\'modal-admit-patient\')"]').forEach(btn => {
  btn.onclick = (e) => { e.preventDefault(); openAdmitModal(); };
});





// --- NOTIFICATIONS & ALERTS ---
let notifInterval = null;

async function fetchNotifications() {
  try {
    const data = await apiFetch('/api/notifications?unread_only=true');
    updateNotifUI(data);
  } catch (err) {
    console.warn("Notification fetch failed (expected if DB not ready)");
  }
}

function updateNotifUI(notifs) {
  const countEl = document.getElementById('notif-count');
  const listEl = document.getElementById('notif-list');
  if (!countEl || !listEl) return;
  
  if (notifs && notifs.length > 0) {
    countEl.innerText = notifs.length;
    countEl.style.display = 'block';
    
    listEl.innerHTML = notifs.map(n => `
      <div class="notif-item" id="notif-${n.notification_id}">
        <div class="notif-msg">${n.message}</div>
        <div class="notif-time" style="font-size:10px; opacity:0.6">${new Date(n.created_at).toLocaleTimeString()}</div>
        <div class="btn-dismiss" onclick="dismissNotif(${n.notification_id})">Dismiss</div>
      </div>
    `).join('');
  } else {
    countEl.style.display = 'none';
    listEl.innerHTML = '<div class="notif-empty">No active alerts</div>';
  }
}

async function dismissNotif(id) {
  try {
    await apiFetch(`/api/notifications/${id}/read`, { method: 'POST' });
    fetchNotifications(); 
  } catch (err) {
    console.error("Dismiss failed");
  }
}

function toggleNotifs() {
  const dropdown = document.getElementById('notif-dropdown');
  if (!dropdown) return;
  dropdown.classList.toggle('open');
  if (dropdown.classList.contains('open')) {
    fetchNotifications();
  }
}

// Start polling for notifications
document.addEventListener('DOMContentLoaded', () => {
  setTimeout(() => {
    fetchNotifications();
    setInterval(fetchNotifications, 15000); // Check every 15s
  }, 2000);
});

// Close dropdown when clicking outside
window.addEventListener('click', (e) => {
  const dropdown = document.getElementById('notif-dropdown');
  if (dropdown && !e.target.closest('.notification-center')) {
    dropdown.classList.remove('open');
  }
});
