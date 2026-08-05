/**
 * Fintech Analytics 2.0 - Dashboard Core
 */

const apiBase = '/api';
const summaryGrid = document.getElementById('summary-grid');
const statusContainer = document.getElementById('status-container');
const uploadResult = document.getElementById('upload-result');
const uploadOverlay = document.getElementById('upload-overlay');
const overlayTitle = document.getElementById('overlay-title');

// Shared Plotly Layout Constants
const PLOTLY_DARK_LAYOUT = {
  margin: { l: 40, r: 20, t: 20, b: 40 },
  paper_bgcolor: 'rgba(0,0,0,0)',
  plot_bgcolor: 'rgba(0,0,0,0)',
  font: { color: '#94a3b8', family: 'Inter, sans-serif' },
  xaxis: {
    fixedrange: true,
    gridcolor: '#1e293b',
    zerolinecolor: '#1e293b',
    tickfont: { size: 10 }
  },
  yaxis: {
    fixedrange: true,
    gridcolor: '#1e293b',
    zerolinecolor: '#1e293b',
    tickfont: { size: 10 }
  },
  showlegend: false
};

function setStatus(message, type = 'error') {
  const colorClass = type === 'success' ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' : 'bg-rose-500/10 border-rose-500/20 text-rose-400';
  statusContainer.innerHTML = `
    <div class="mb-6 p-4 rounded-2xl border ${colorClass} flex items-center gap-3 animate-in fade-in slide-in-from-top-4 duration-300">
      <svg class="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
      <span class="text-sm font-medium">${message}</span>
    </div>
  `;
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
  return '৳' + value.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
}

async function fetchJson(path) {
  const response = await fetch(`${apiBase}${path}`);
  if (!response.ok) {
    const payload = await response.text();
    throw new Error(`${response.status} ${response.statusText}: ${payload}`);
  }
  return response.json();
}

function renderSummary(summary) {
  summaryGrid.innerHTML = '';
  const cards = [
    { label: 'Total Volume', value: summary.total_transactions.toLocaleString(), icon: '📊' },
    { label: 'Gross Revenue', value: formatCurrency(summary.total_revenue), icon: '💰', color: 'text-brand-500' },
    { label: 'Failed Ops', value: summary.failed_transaction_count.toLocaleString(), icon: '⚠️', color: 'text-rose-400' },
    { label: 'Fraud Flags', value: summary.suspicious_transaction_count.toLocaleString(), icon: '🚨', color: 'text-amber-400' },
    { label: 'Primary Channel', value: summary.most_used_payment_method || '—', icon: '💳' },
  ];

  cards.forEach((c) => {
    const card = document.createElement('div');
    card.className = 'kpi-card';
    card.innerHTML = `
      <div class="flex items-center justify-between mb-3">
        <span class="text-[10px] font-bold text-slate-500 uppercase tracking-widest">${c.label}</span>
        <span class="text-lg">${c.icon}</span>
      </div>
      <div class="text-2xl font-extrabold ${c.color || 'text-white'} truncate">${c.value}</div>
    `;
    summaryGrid.appendChild(card);
  });
}

function renderRevenueChart(summary) {
  const days = summary.daily_summary.map((row) => row.day).reverse();
  const revenue = summary.daily_summary.map((row) => row.total_revenue).reverse();

  Plotly.newPlot('revenue-chart', [
    {
      x: days,
      y: revenue,
      type: 'scatter',
      mode: 'lines+markers',
      marker: { color: '#0ea5e9', size: 6 },
      line: { shape: 'spline', smoothing: 1.2, width: 3, color: '#0ea5e9' },
      fill: 'tozeroy',
      fillcolor: 'rgba(14, 165, 233, 0.05)'
    },
  ], PLOTLY_DARK_LAYOUT, { responsive: true, displayModeBar: false });
}

function renderFailedChart(summary) {
  const days = summary.daily_summary.map((row) => row.day).reverse();
  const failed = summary.daily_summary.map((row) => row.failed_count).reverse();

  Plotly.newPlot('failed-chart', [
    {
      x: days,
      y: failed,
      type: 'bar',
      marker: {
        color: '#f43f5e',
        line: { color: '#f43f5e', width: 0 }
      },
    },
  ], PLOTLY_DARK_LAYOUT, { responsive: true, displayModeBar: false });
}

function renderTopUsers(users) {
  const container = document.getElementById('top-users-chart');
  if (!users.length) {
    container.innerHTML = '<div class="flex items-center justify-center h-full text-slate-500 text-sm italic">No data available</div>';
    return;
  }

  const labels = users.map((row) => row.user_id);
  const values = users.map((row) => row.total_spent);

  Plotly.newPlot('top-users-chart', [
    {
      x: values,
      y: labels,
      type: 'bar',
      orientation: 'h',
      marker: {
        color: '#6366f1',
        line: { color: '#6366f1', width: 0 }
      },
    },
  ], {
    ...PLOTLY_DARK_LAYOUT,
    margin: { l: 80, r: 20, t: 10, b: 40 },
  }, { responsive: true, displayModeBar: false });
}

function renderMerchantPerformance(list) {
  const container = document.getElementById('merchant-table');
  if (!list.length) {
    container.innerHTML = '<div class="p-8 text-center text-slate-500 text-sm italic">No merchant data discovered</div>';
    return;
  }

  container.innerHTML = `
    <table class="w-full">
      <thead>
        <tr class="bg-slate-900/50">
          <th class="table-header">Merchant ID</th>
          <th class="table-header text-right">Revenue</th>
          <th class="table-header text-center">Txns</th>
          <th class="table-header text-right">Success</th>
        </tr>
      </thead>
      <tbody>
        ${list
          .map(
            (row) =>
              `<tr>
                <td class="table-cell font-medium text-slate-300">${row.merchant_id}</td>
                <td class="table-cell text-right font-bold text-emerald-400">${formatCurrency(row.total_revenue)}</td>
                <td class="table-cell text-center text-slate-400">${row.transaction_count}</td>
                <td class="table-cell text-right">
                  <div class="flex flex-col items-end gap-1">
                    <span class="text-xs font-bold text-slate-200">${row.success_rate.toFixed(1)}%</span>
                    <div class="w-16 h-1 bg-slate-800 rounded-full overflow-hidden">
                      <div class="h-full bg-brand-500" style="width: ${row.success_rate}%"></div>
                    </div>
                  </div>
                </td>
              </tr>`
          )
          .join('')}
      </tbody>
    </table>
  `;
}

function renderChannelPerformance(list) {
  const container = document.getElementById('channel-table');
  if (!list.length) {
    container.innerHTML = '<div class="p-8 text-center text-slate-500 text-sm italic">No channel data discovered</div>';
    return;
  }

  container.innerHTML = `
    <table class="w-full">
      <thead>
        <tr class="bg-slate-900/50">
          <th class="table-header">Channel</th>
          <th class="table-header text-right">Revenue</th>
          <th class="table-header text-center">Txns</th>
          <th class="table-header text-right">Success</th>
        </tr>
      </thead>
      <tbody>
        ${list
          .map(
            (row) =>
              `<tr>
                <td class="table-cell font-medium text-slate-300">${row.payment_method}</td>
                <td class="table-cell text-right font-bold text-brand-500">${formatCurrency(row.total_revenue)}</td>
                <td class="table-cell text-center text-slate-400">${row.transaction_count}</td>
                <td class="table-cell text-right">
                  <div class="flex flex-col items-end gap-1">
                    <span class="text-xs font-bold text-slate-200">${row.success_rate.toFixed(1)}%</span>
                    <div class="w-16 h-1 bg-slate-800 rounded-full overflow-hidden">
                      <div class="h-full bg-indigo-500" style="width: ${row.success_rate}%"></div>
                    </div>
                  </div>
                </td>
              </tr>`
          )
          .join('')}
      </tbody>
    </table>
  `;
}

function renderSuspicious(list) {
  const container = document.getElementById('suspicious-table');
  if (!list.length) {
    container.innerHTML = '<div class="p-12 text-center"><div class="text-4xl mb-4">🛡️</div><div class="text-slate-500 text-sm font-medium">No suspicious activity detected in the current audit period</div></div>';
    return;
  }

  container.innerHTML = `
    <table class="w-full">
      <thead class="bg-slate-900/50">
        <tr>
          <th class="table-header">Txn ID</th>
          <th class="table-header">Actor</th>
          <th class="table-header">Merchant</th>
          <th class="table-header text-right">Amount</th>
          <th class="table-header text-center">Status</th>
          <th class="table-header">Violation Reason</th>
        </tr>
      </thead>
      <tbody>
        ${list
          .slice(0, 15)
          .map((row) => {
            const statusClass = row.transaction_status === 'FAILED' ? 'bg-rose-500/20 text-rose-400' : 'bg-emerald-500/20 text-emerald-400';
            return `
              <tr class="hover:bg-slate-800/30 transition-colors">
                <td class="table-cell font-mono text-xs text-brand-500">${row.transaction_id}</td>
                <td class="table-cell font-medium">${row.user_id}</td>
                <td class="table-cell text-slate-400">${row.merchant_id}</td>
                <td class="table-cell text-right font-bold">${formatCurrency(row.amount)}</td>
                <td class="table-cell text-center">
                  <span class="status-pill ${statusClass}">${row.transaction_status}</span>
                </td>
                <td class="table-cell text-xs text-amber-400/80 leading-relaxed max-w-xs">${row.suspicious_reason || 'Manual Flag'}</td>
              </tr>
            `;
          })
          .join('')}
      </tbody>
    </table>
  `;
}

async function loadDashboard() {
  try {
    clearStatus();
    const [summary, topUsers, merchants, channels, suspicious] = await Promise.all([
      fetchJson('/analytics/summary'),
      fetchJson('/analytics/top-users?limit=10'),
      fetchJson('/analytics/merchant-performance'),
      fetchJson('/analytics/channel-performance'),
      fetchJson('/transactions/suspicious?limit=50'),
    ]);

    renderSummary(summary);
    renderRevenueChart(summary);
    renderFailedChart(summary);
    renderTopUsers(topUsers);
    renderMerchantPerformance(merchants);
    renderChannelPerformance(channels);
    renderSuspicious(suspicious);
  } catch (error) {
    setStatus(`Dashboard Sync Error: ${error.message}`);
  }
}

async function uploadCsv(file) {
  const form = new FormData();
  form.append('file', file, file.name);

  const response = await fetch(`${apiBase}/upload/csv`, {
    method: 'POST',
    body: form,
  });

  if (!response.ok) {
    const payload = await response.json();
    throw new Error(payload.detail || `${response.status} ${response.statusText}`);
  }

  return response.json();
}

const uploadForm = document.getElementById('upload-form');
uploadForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  clearStatus();

  const fileInput = document.getElementById('transaction-file');
  if (!fileInput.files.length) {
    setStatus('Please select a CSV file for ingestion.');
    return;
  }

  const file = fileInput.files[0];
  const submitBtn = event.target.querySelector('button');
  const originalBtnText = submitBtn.textContent;

  submitBtn.disabled = true;
  submitBtn.textContent = 'Processing...';

  try {
    const result = await uploadCsv(file);
    showOverlay('Ingestion Successful', JSON.stringify(result, null, 2));
    setStatus('Pipeline execution completed successfully.', 'success');
    await loadDashboard();
  } catch (error) {
    showOverlay('Ingestion Failed', error.message);
    setStatus(`Pipeline Error: ${error.message}`);
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = originalBtnText;
    fileInput.value = '';
  }
});

window.addEventListener('load', loadDashboard);
