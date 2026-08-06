/**
 * Fintech Analytics Dashboard Core - Unified functional update
 */

const apiBase = '/api';
const summaryGrid = document.getElementById('summary-grid');
const statusContainer = document.getElementById('status-container');
const uploadResult = document.getElementById('upload-result');
const uploadOverlay = document.getElementById('upload-overlay');
const overlayTitle = document.getElementById('overlay-title');
const loadingOverlay = document.getElementById('loading-overlay');

// Shared Plotly Layout
const PLOTLY_LAYOUT = {
  margin: { l: 40, r: 20, t: 30, b: 40 },
  paper_bgcolor: 'rgba(0,0,0,0)',
  plot_bgcolor: 'rgba(0,0,0,0)',
  font: { color: '#94a3b8', family: 'Inter, sans-serif' },
  xaxis: {
    fixedrange: true,
    gridcolor: 'rgba(255,255,255,0.03)',
    zerolinecolor: 'rgba(255,255,255,0.03)',
    tickfont: { size: 9 }
  },
  yaxis: {
    fixedrange: true,
    gridcolor: 'rgba(255,255,255,0.03)',
    zerolinecolor: 'rgba(255,255,255,0.03)',
    tickfont: { size: 9 }
  },
  showlegend: false
};

function setStatus(message, type = 'error') {
  const color = type === 'success' ? 'bg-emerald-500' : 'bg-rose-500';
  statusContainer.innerHTML = `
    <div class="px-6 py-3 rounded-xl shadow-2xl ${color} text-white font-bold text-sm flex items-center gap-2 animate-in fade-in slide-in-from-bottom-4 duration-300">
      <span>${type === 'success' ? '✓' : '⚠️'}</span>
      ${message}
    </div>
  `;
  if (type === 'success') setTimeout(clearStatus, 4000);
}

function clearStatus() {
  statusContainer.innerHTML = '';
}

function closeOverlay() {
  uploadOverlay.classList.add('hidden');
}

function showOverlay(title, content) {
  overlayTitle.textContent = title;
  uploadResult.textContent = content;
  uploadOverlay.classList.remove('hidden');
}

function formatCurrency(value) {
  return '৳' + (value || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

async function fetchJson(path, params = {}) {
  const url = new URL(`${window.location.origin}${apiBase}${path}`);

  // Add filters
  Object.keys(params).forEach(key => {
    if (params[key] && params[key] !== 'All') {
        url.searchParams.append(key, params[key]);
    }
  });

  // Cache buster
  url.searchParams.append('_t', Date.now());

  const response = await fetch(url);
  if (!response.ok) {
    const payload = await response.text();
    throw new Error(`${response.status}: ${payload}`);
  }
  return response.json();
}

function renderSummary(summary) {
  summaryGrid.innerHTML = '';
  const cards = [
    { label: 'Total Transactions', value: summary.total_transactions.toLocaleString() },
    { label: 'Total Revenue', value: formatCurrency(summary.total_revenue) },
    { label: 'Failed Transactions', value: summary.failed_transaction_count.toLocaleString() },
    { label: 'Suspicious Transactions', value: summary.suspicious_transaction_count.toLocaleString() },
    { label: 'Top Payment Method', value: summary.most_used_payment_method || '—' },
  ];

  cards.forEach((c) => {
    const card = document.createElement('div');
    card.className = 'kpi-card';
    card.innerHTML = `
      <div class="text-[10px] font-bold text-slate-500 uppercase tracking-widest">${c.label}</div>
      <div class="text-2xl font-bold truncate">${c.value}</div>
    `;
    summaryGrid.appendChild(card);
  });
}

function renderRevenueChart(summary) {
  const days = summary.daily_summary.map((row) => row.day).reverse();
  const revenue = summary.daily_summary.map((row) => row.total_revenue).reverse();

  Plotly.newPlot('revenue-chart', [{
      x: days, y: revenue, type: 'scatter', mode: 'lines+markers',
      marker: { color: '#38bdf8', size: 4 },
      line: { shape: 'spline', smoothing: 1.2, width: 2, color: '#38bdf8' },
  }], PLOTLY_LAYOUT, { responsive: true, displayModeBar: false });
}

function renderFailedChart(summary) {
  const days = summary.daily_summary.map((row) => row.day).reverse();
  const failed = summary.daily_summary.map((row) => row.failed_count).reverse();

  Plotly.newPlot('failed-chart', [{
      x: days, y: failed, type: 'bar', marker: { color: '#38bdf8' },
  }], PLOTLY_LAYOUT, { responsive: true, displayModeBar: false });
}

function renderTopUsers(users) {
  const container = document.getElementById('top-users-chart');
  if (!users || !users.length) {
    container.innerHTML = '<div class="flex items-center justify-center h-full text-slate-500 text-xs italic">No user data for the selected filters</div>';
    return;
  }

  const labels = users.map((row) => row.user_id);
  const values = users.map((row) => row.total_spent);

  Plotly.newPlot('top-users-chart', [{
      x: labels, y: values, type: 'bar',
      marker: { color: '#38bdf8', opacity: 0.8 },
      text: values.map(v => v > 0 ? '৳' + (v/1000).toFixed(1) + 'k' : ''),
      textposition: 'outside',
      cliponaxis: false
  }], {
    ...PLOTLY_LAYOUT,
    margin: { l: 40, r: 20, t: 30, b: 40 },
    yaxis: { ...PLOTLY_LAYOUT.yaxis, tickprefix: '৳' }
  }, { responsive: true, displayModeBar: false });
}

function renderMerchantPerformance(list) {
  const container = document.getElementById('merchant-table');
  if (!list.length) { container.innerHTML = '<div class="p-8 text-slate-500 text-xs italic">No data</div>'; return; }

  container.innerHTML = `
    <table class="w-full">
      <thead><tr>
          <th class="table-header">Merchant</th>
          <th class="table-header text-right">Revenue</th>
          <th class="table-header text-center">Transactions</th>
          <th class="table-header text-center">Failed</th>
          <th class="table-header text-right">Success Rate (%)</th>
      </tr></thead>
      <tbody>${list.map((row) => `
        <tr>
          <td class="table-cell font-bold">${row.merchant_id}</td>
          <td class="table-cell text-right">${formatCurrency(row.total_revenue)}</td>
          <td class="table-cell text-center">${row.transaction_count}</td>
          <td class="table-cell text-center">${row.failed_count}</td>
          <td class="table-cell text-right">${row.success_rate.toFixed(2)}</td>
        </tr>`).join('')}
      </tbody>
    </table>`;
}

function renderChannelPerformance(list) {
  const container = document.getElementById('channel-table');
  if (!list.length) { container.innerHTML = '<div class="p-8 text-slate-500 text-xs italic">No data</div>'; return; }

  container.innerHTML = `
    <table class="w-full">
      <thead><tr>
          <th class="table-header">Channel</th>
          <th class="table-header text-right">Revenue</th>
          <th class="table-header text-center">Transactions</th>
          <th class="table-header text-center">Failed</th>
          <th class="table-header text-right">Success Rate (%)</th>
      </tr></thead>
      <tbody>${list.map((row) => `
        <tr>
          <td class="table-cell font-bold">${row.payment_method}</td>
          <td class="table-cell text-right">${formatCurrency(row.total_revenue)}</td>
          <td class="table-cell text-center">${row.transaction_count}</td>
          <td class="table-cell text-center">${row.failed_count}</td>
          <td class="table-cell text-right">${row.success_rate.toFixed(2)}</td>
        </tr>`).join('')}
      </tbody>
    </table>`;
}

function renderSuspicious(list) {
  const container = document.getElementById('suspicious-table');
  if (!list.length) { container.innerHTML = '<div class="p-8 text-slate-500 text-xs italic text-center">🛡️ No suspicious activity detected</div>'; return; }

  container.innerHTML = `
    <table class="w-full">
      <thead><tr>
          <th class="table-header">ID</th><th class="table-header">Actor</th><th class="table-header">Merchant</th>
          <th class="table-header text-right">Amount</th><th class="table-header">Status</th>
          <th class="table-header">Reason</th><th class="table-header">Timestamp</th>
      </tr></thead>
      <tbody>${list.slice(0, 50).map((row) => `
        <tr>
          <td class="table-cell font-mono">${row.transaction_id}</td>
          <td class="table-cell">${row.user_id}</td>
          <td class="table-cell">${row.merchant_id}</td>
          <td class="table-cell text-right font-bold">${row.amount.toLocaleString()}</td>
          <td class="table-cell">${row.transaction_status}</td>
          <td class="table-cell text-amber-500 text-[10px]">${row.suspicious_reason || 'Manual'}</td>
          <td class="table-cell text-slate-500 text-[10px]">${row.timestamp.replace('T', ' ').split('.')[0]}</td>
        </tr>`).join('')}
      </tbody>
    </table>`;
}

async function loadDashboard() {
  try {
    const payment = document.getElementById('filter-payment').value;
    const status = document.getElementById('filter-status').value;
    const params = { payment_method: payment, transaction_status: status };

    const [summary, topUsers, merchants, channels, suspicious] = await Promise.all([
      fetchJson('/analytics/summary', params),
      fetchJson('/analytics/top-users?limit=10', params),
      fetchJson('/analytics/merchant-performance', params),
      fetchJson('/analytics/channel-performance', params),
      fetchJson('/transactions/suspicious?limit=50', params),
    ]);

    renderSummary(summary);
    renderRevenueChart(summary);
    renderFailedChart(summary);
    renderTopUsers(topUsers);
    renderMerchantPerformance(merchants);
    renderChannelPerformance(channels);
    renderSuspicious(suspicious);
  } catch (error) {
    setStatus(`Sync Error: ${error.message}`);
  }
}

// Upload & Clear Logic
const uploadForm = document.getElementById('upload-form');
const fileInput = document.getElementById('transaction-file');
const dropzone = document.getElementById('dropzone');
const clearBtn = document.getElementById('clear-db-btn');
const resetSampleBtn = document.getElementById('reset-sample-btn');

clearBtn.addEventListener('click', async () => {
  if (!confirm('Clear all data from this instance?')) return;
  try {
    const res = await fetch(`${apiBase}/upload/clear`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Clear failed');
    setStatus('Database wiped.', 'success');
    await loadDashboard();
  } catch (e) { setStatus(e.message); }
});

resetSampleBtn.addEventListener('click', async () => {
  setStatus('Resetting to sample data...', 'success');
  try {
    // We can't trigger the backend seed directly easily without a specific endpoint,
    // so we'll just clear and then let the user know they can upload the sample.
    // Actually, let's just make it clear the db.
    await fetch(`${apiBase}/upload/clear`, { method: 'DELETE' });
    setStatus('Database cleared. Please upload your CSV now.', 'success');
    await loadDashboard();
  } catch (e) { setStatus(e.message); }
});

fileInput.addEventListener('change', () => { if (fileInput.files.length) uploadForm.requestSubmit(); });

uploadForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  if (!fileInput.files.length) return;

  const file = fileInput.files[0];
  const formData = new FormData();
  formData.append('file', file);

  setStatus(`Processing ${file.name}...`, 'success');
  loadingOverlay.classList.remove('hidden');
  loadingOverlay.classList.add('flex');

  try {
    const res = await fetch(`${apiBase}/upload/csv`, { method: 'POST', body: formData });
    const result = await res.json();
    loadingOverlay.classList.add('hidden');
    loadingOverlay.classList.remove('flex');

    if (!res.ok) throw new Error(result.detail || 'Upload failed');

    showOverlay('Ingestion Report', JSON.stringify(result, null, 2));
    if (result.transactions_inserted > 0) {
        setStatus(`Success: Added ${result.transactions_inserted} rows.`, 'success');
        loadDashboard();
    } else {
        setStatus('No new data added (IDs already exist).', 'error');
    }
  } catch (e) {
    loadingOverlay.classList.add('hidden');
    loadingOverlay.classList.remove('flex');
    setStatus(e.message);
  } finally { fileInput.value = ''; }
});

// Drag/Drop
dropzone.addEventListener('dragover', (e) => { e.preventDefault(); dropzone.classList.add('border-accent'); });
dropzone.addEventListener('dragleave', () => { dropzone.classList.remove('border-accent'); });
dropzone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropzone.classList.remove('border-accent');
  if (e.dataTransfer.files.length) { fileInput.files = e.dataTransfer.files; uploadForm.requestSubmit(); }
});

// Mobile Sidebar Toggle
const mobileToggle = document.getElementById('mobile-sidebar-toggle');
const sidebar = document.getElementById('sidebar');
const sidebarClose = document.getElementById('sidebar-close');

function openSidebar() {
    sidebar.classList.remove('-translate-x-full');
    mobileToggle.classList.add('hidden');
}

function closeSidebar() {
    sidebar.classList.add('-translate-x-full');
    mobileToggle.classList.remove('hidden');
}

mobileToggle.addEventListener('click', openSidebar);
sidebarClose.addEventListener('click', closeSidebar);

// Close sidebar when clicking outside on mobile
document.addEventListener('click', (e) => {
    if (window.innerWidth < 1024) {
        if (!sidebar.contains(e.target) && !mobileToggle.contains(e.target) && !sidebar.classList.contains('-translate-x-full')) {
            closeSidebar();
        }
    }
});

// Filter triggers
document.getElementById('filter-payment').addEventListener('change', () => {
    loadDashboard();
    if (window.innerWidth < 1024) closeSidebar();
});
document.getElementById('filter-status').addEventListener('change', () => {
    loadDashboard();
    if (window.innerWidth < 1024) closeSidebar();
});

window.addEventListener('load', loadDashboard);
