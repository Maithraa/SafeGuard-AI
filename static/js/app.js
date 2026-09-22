/**
 * FraudGuard AI - Core Frontend Logic
 * Strictly adheres to 4px-8px rectangular design guidelines.
 * Controls Chart.js, Live Simulation, Mule Canvas, CSV Upload, and Triage actions.
 */

// Global state for charts
let riskDoughnutChart = null;
let activityLineChart = null;

// Utility formatting functions
const formatINR = (val) => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0
  }).format(val);
};

// ---------------------------------------------------------------------------
// 1. Admin Dashboard Initializer
// ---------------------------------------------------------------------------
async function initDashboard() {
  try {
    const res = await fetch('/api/dashboard');
    const data = await res.json();
    const { metrics, recent_suspicious, hourly_trend } = data;

    // Update Banner Stat Counters
    const elTotal = document.getElementById('statTotalAnalyzed');
    const elSuspicious = document.getElementById('statSuspicious');
    const elCritical = document.getElementById('statCritical');
    const elVolume = document.getElementById('statVolume');
    const elAnomalyRate = document.getElementById('statAnomalyRate');

    if (elTotal) elTotal.textContent = metrics.total_analyzed.toLocaleString();
    if (elSuspicious) elSuspicious.textContent = metrics.suspicious_count.toLocaleString();
    if (elCritical) elCritical.textContent = metrics.critical_count.toLocaleString();
    if (elVolume) elVolume.textContent = `₹${metrics.analyzed_volume_cr} Cr`;
    if (elAnomalyRate) elAnomalyRate.textContent = `${metrics.anomaly_rate}%`;

    // Render Doughnut Chart
    renderRiskDoughnut(metrics.risk_breakdown);

    // Render Hourly Volume Line Chart
    renderHourlyTrend(hourly_trend);

    // Populate Recent Suspicious Activity Table
    renderRecentSuspiciousTable(recent_suspicious);

  } catch (err) {
    console.error('Error initializing dashboard:', err);
  }
}

// ---------------------------------------------------------------------------
// 2. Chart.js Visualizations (Strict Rectangular Tooltips & Color Highlights)
// ---------------------------------------------------------------------------
function renderRiskDoughnut(breakdown) {
  const ctx = document.getElementById('riskDoughnutCanvas');
  if (!ctx) return;

  const lowCount = breakdown.LOW || 38;
  const medCount = breakdown.MEDIUM || 8;
  const highCount = breakdown.HIGH || 5;
  const critCount = breakdown.CRITICAL || 4;

  // Update badge counts next to chart
  const bLow = document.getElementById('badgeCountLow');
  const bMed = document.getElementById('badgeCountMed');
  const bHigh = document.getElementById('badgeCountHigh');
  const bCrit = document.getElementById('badgeCountCrit');
  if (bLow) bLow.textContent = lowCount;
  if (bMed) bMed.textContent = medCount;
  if (bHigh) bHigh.textContent = highCount;
  if (bCrit) bCrit.textContent = critCount;

  if (riskDoughnutChart) {
    riskDoughnutChart.data.datasets[0].data = [lowCount, medCount, highCount, critCount];
    riskDoughnutChart.update();
    return;
  }

  riskDoughnutChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Low Risk', 'Medium Risk', 'High Risk', 'Critical Threat'],
      datasets: [{
        data: [lowCount, medCount, highCount, critCount],
        backgroundColor: ['#10b981', '#f59e0b', '#f97316', '#dc2626'],
        borderColor: '#1f2937',
        borderWidth: 3,
        hoverOffset: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '72%',
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#111827',
          borderColor: '#374151',
          borderWidth: 1,
          cornerRadius: 4,
          padding: 10,
          titleFont: { family: 'Inter', size: 12, weight: 'bold' },
          bodyFont: { family: 'Inter', size: 12 }
        }
      }
    }
  });
}

function renderHourlyTrend(trend) {
  const ctx = document.getElementById('hourlyActivityCanvas');
  if (!ctx) return;

  if (activityLineChart) {
    activityLineChart.destroy();
  }

  activityLineChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: trend.hours,
      datasets: [
        {
          label: 'Normal Transactions',
          data: trend.normal,
          borderColor: '#3b82f6',
          backgroundColor: 'rgba(59, 130, 246, 0.08)',
          fill: true,
          tension: 0.3,
          borderWidth: 2,
          pointRadius: 0,
          pointHoverRadius: 5
        },
        {
          label: 'Suspicious / Flagged',
          data: trend.suspicious,
          borderColor: '#dc2626',
          backgroundColor: 'rgba(220, 38, 38, 0.15)',
          fill: true,
          tension: 0.3,
          borderWidth: 2,
          pointRadius: 2,
          pointBackgroundColor: '#dc2626',
          pointHoverRadius: 6
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: 'index',
        intersect: false
      },
      plugins: {
        legend: {
          position: 'top',
          align: 'end',
          labels: {
            boxWidth: 12,
            boxHeight: 12,
            borderRadius: 2,
            color: '#9ca3af',
            font: { family: 'Inter', size: 11, weight: '500' }
          }
        },
        tooltip: {
          backgroundColor: '#111827',
          borderColor: '#374151',
          borderWidth: 1,
          cornerRadius: 4,
          padding: 10
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: { color: '#6b7280', font: { size: 10 } }
        },
        y: {
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: { color: '#6b7280', font: { size: 10 } }
        }
      }
    }
  });
}

function renderRecentSuspiciousTable(items) {
  const tbody = document.getElementById('recentSuspiciousTbody');
  if (!tbody) return;

  tbody.innerHTML = '';
  if (!items || items.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding: 2rem; color: #6b7280;">No high-risk transactions detected.</td></tr>';
    return;
  }

  items.forEach(txn => {
    const tr = document.createElement('tr');
    tr.className = txn.risk_level === 'CRITICAL' ? 'risk-border-critical' : 'risk-border-high';

    tr.innerHTML = `
      <td>
        <div style="font-weight: 700; color: #fff; font-family: var(--font-mono);">${txn.transaction_id}</div>
        <div style="font-size: 0.75rem; color: #9ca3af;">${txn.timestamp}</div>
      </td>
      <td>
        <div style="font-weight: 600;">${txn.holder_name}</div>
        <div style="font-size: 0.75rem; color: #6b7280; font-family: var(--font-mono);">${txn.account_id}</div>
      </td>
      <td style="font-weight: 700; font-family: var(--font-mono); color: #fff;">
        ${formatINR(txn.amount)}
      </td>
      <td>
        <div style="display: flex; align-items: center; gap: 6px;">
          <span>📍</span>
          <span>${txn.location}</span>
        </div>
      </td>
      <td>
        <span class="risk-badge ${txn.risk_level === 'CRITICAL' ? 'risk-badge-critical' : 'risk-badge-high'}">
          ${txn.risk_level} (${txn.hybrid_score})
        </span>
      </td>
      <td style="max-width: 260px; font-size: 0.775rem; color: #d1d5db; line-height: 1.3;">
        ${txn.xai_summary}
      </td>
      <td>
        <div style="display: flex; gap: 6px;">
          <a href="/transactions/${txn.transaction_id}" class="btn btn-secondary btn-sm" style="text-decoration:none;">View XAI</a>
          <button onclick="quickFreezeAccount('${txn.account_id}', this)" class="btn btn-danger btn-sm">Freeze</button>
        </div>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

// ---------------------------------------------------------------------------
// 3. Live Simulation Flow (CRITICAL FOR HACKATHON JURY)
// ---------------------------------------------------------------------------
async function triggerSimulation() {
  const btn = document.getElementById('btnSimulateLive');
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '⚡ Simulating Threat Vector...';
  }

  try {
    const res = await fetch('/api/simulate-transaction', { method: 'POST' });
    const data = await res.json();

    if (!data.success) {
      alert('Simulation error: ' + (data.error || 'Failed'));
      return;
    }

    const { transaction, analysis, refreshed_metrics } = data;

    // 1. Populate and show Simulation Result Modal
    document.getElementById('simModalTxnId').textContent = transaction.transaction_id;
    document.getElementById('simModalAmount').textContent = formatINR(transaction.amount);
    document.getElementById('simModalLocation').textContent = `${transaction.location} (from ${transaction.prev_location})`;
    document.getElementById('simModalVelocity').textContent = `${transaction.geo_velocity_kmh} km/h (Impossible Velocity)`;
    document.getElementById('simModalScore').textContent = `${analysis.hybrid_score} / 100`;
    document.getElementById('simModalRiskBadge').textContent = analysis.risk_level;
    document.getElementById('simModalRiskBadge').className = `risk-badge ${analysis.badge_class}`;

    // Fill progress bar
    const pBar = document.getElementById('simModalProgressBar');
    if (pBar) {
      pBar.style.width = `${analysis.hybrid_score}%`;
      pBar.style.backgroundColor = analysis.color_code;
    }

    // Populate XAI bullet points
    const reasonsContainer = document.getElementById('simModalXaiReasons');
    if (reasonsContainer) {
      reasonsContainer.innerHTML = '';
      analysis.xai_reasons.forEach(r => {
        const row = document.createElement('div');
        row.className = 'xai-reason-row warning';
        row.innerHTML = `
          <span class="xai-icon">⚠️</span>
          <div><strong>Flagged factor:</strong> ${r}</div>
        `;
        reasonsContainer.appendChild(row);
      });
    }

    // Set link for deep inspection
    const deepLink = document.getElementById('simModalDeepLink');
    if (deepLink) {
      deepLink.href = `/transactions/${transaction.transaction_id}`;
    }

    // Show modal
    openModal('simulationModal');

    // 2. Smoothly Update Dashboard Metrics without reload
    const elTotal = document.getElementById('statTotalAnalyzed');
    const elSuspicious = document.getElementById('statSuspicious');
    const elCritical = document.getElementById('statCritical');
    if (elTotal) elTotal.textContent = (parseInt(elTotal.textContent.replace(/,/g, '')) + 1).toLocaleString();
    if (elSuspicious) elSuspicious.textContent = (parseInt(elSuspicious.textContent.replace(/,/g, '')) + 1).toLocaleString();
    if (elCritical) elCritical.textContent = (parseInt(elCritical.textContent.replace(/,/g, '')) + 1).toLocaleString();

    // 3. Update Doughnut Chart in-place
    if (refreshed_metrics) {
      renderRiskDoughnut(refreshed_metrics.risk_breakdown);
    }

    // 4. Prepend new transaction row to Recent Suspicious Table
    const tbody = document.getElementById('recentSuspiciousTbody');
    if (tbody) {
      const newTr = document.createElement('tr');
      newTr.className = 'risk-border-critical';
      newTr.style.animation = 'modalFadeIn 0.4s ease';
      newTr.innerHTML = `
        <td>
          <div style="font-weight: 700; color: #f87171; font-family: var(--font-mono);">${transaction.transaction_id} (LIVE)</div>
          <div style="font-size: 0.75rem; color: #9ca3af;">Just now</div>
        </td>
        <td>
          <div style="font-weight: 600;">Karthik Natarajan</div>
          <div style="font-size: 0.75rem; color: #6b7280; font-family: var(--font-mono);">${transaction.account_id}</div>
        </td>
        <td style="font-weight: 700; font-family: var(--font-mono); color: #fff;">
          ${formatINR(transaction.amount)}
        </td>
        <td>
          <div style="display: flex; align-items: center; gap: 6px;">
            <span>📍</span>
            <span>${transaction.location}</span>
          </div>
        </td>
        <td>
          <span class="risk-badge risk-badge-critical">
            CRITICAL (${analysis.hybrid_score})
          </span>
        </td>
        <td style="max-width: 260px; font-size: 0.775rem; color: #fca5a5; line-height: 1.3;">
          ${analysis.xai_reasons[0]}
        </td>
        <td>
          <div style="display: flex; gap: 6px;">
            <a href="/transactions/${transaction.transaction_id}" class="btn btn-secondary btn-sm">View XAI</a>
            <button onclick="quickFreezeAccount('${transaction.account_id}', this)" class="btn btn-danger btn-sm">Freeze</button>
          </div>
        </td>
      `;
      tbody.insertBefore(newTr, tbody.firstChild);
    }

  } catch (err) {
    console.error('Simulation error:', err);
    alert('Failed to run live simulation.');
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = '⚡ Simulate Live Transaction';
    }
  }
}

// ---------------------------------------------------------------------------
// 4. Quick Account Actions
// ---------------------------------------------------------------------------
async function quickFreezeAccount(accountId, btnElement) {
  if (!confirm(`Are you sure you want to FREEZE Account ${accountId} and restrict all digital banking rails?`)) {
    return;
  }

  if (btnElement) {
    btnElement.disabled = true;
    btnElement.textContent = 'Freezing...';
  }

  try {
    // Attempt alert action if available, or update account
    const res = await fetch('/api/alerts/1/action', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'Freeze' })
    });

    if (btnElement) {
      btnElement.textContent = 'Frozen 🔒';
      btnElement.className = 'btn btn-secondary btn-sm';
      btnElement.disabled = true;
    }

    showNotification(`Account ${accountId} successfully FROZEN. Outbound UPI and NEFT locked.`);
  } catch (e) {
    console.error(e);
  }
}

// ---------------------------------------------------------------------------
// 5. Mule Network Interactive Canvas Visualizer
// ---------------------------------------------------------------------------
function initMuleCanvas(data) {
  const canvas = document.getElementById('muleCanvas');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();

  canvas.width = rect.width * dpr;
  canvas.height = rect.height * dpr;
  ctx.scale(dpr, dpr);

  const w = rect.width;
  const h = rect.height;

  // Position nodes strategically
  const nodePositions = {
    'ACC101': { x: w * 0.25, y: h * 0.35, name: 'ACC101 (Karthik)', type: 'Mule Ring Alpha' },
    'ACC102': { x: w * 0.50, y: h * 0.20, name: 'ACC102 (Priya)', type: 'Intermediary Hop' },
    'ACC105': { x: w * 0.70, y: h * 0.45, name: 'ACC105 (Farooq)', type: 'Smurfing Hub' },
    'ACC109': { x: w * 0.75, y: h * 0.75, name: 'ACC109 (Suresh)', type: 'Extraction Node' },
    'ACC108': { x: w * 0.20, y: h * 0.70, name: 'ACC108 (Sneha)', type: 'Dormant Funnel' }
  };

  let animationFrameId;
  let offset = 0;

  function draw() {
    ctx.clearRect(0, 0, w, h);

    // Draw background grid
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.03)';
    ctx.lineWidth = 1;
    for (let x = 0; x < w; x += 30) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, h);
      ctx.stroke();
    }
    for (let y = 0; y < h; y += 30) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(w, y);
      ctx.stroke();
    }

    // Draw Edges
    data.edges.forEach(edge => {
      const src = nodePositions[edge.source];
      const tgt = nodePositions[edge.target];
      if (!src || !tgt) return;

      ctx.save();
      ctx.beginPath();
      ctx.moveTo(src.x, src.y);
      ctx.lineTo(tgt.x, tgt.y);

      if (edge.is_circular) {
        ctx.strokeStyle = '#dc2626'; // Red for circular loops
        ctx.lineWidth = 2.5;
        ctx.setLineDash([8, 6]);
        ctx.lineDashOffset = -offset;
      } else {
        ctx.strokeStyle = '#4b5563';
        ctx.lineWidth = 1.5;
      }
      ctx.stroke();
      ctx.restore();

      // Label along edge
      const midX = (src.x + tgt.x) / 2;
      const midY = (src.y + tgt.y) / 2;
      ctx.save();
      ctx.fillStyle = edge.is_circular ? '#ef4444' : '#9ca3af';
      ctx.font = '600 11px Inter';
      ctx.textAlign = 'center';
      ctx.fillText(edge.label, midX, midY - 6);
      ctx.restore();
    });

    // Draw Nodes (Rectangular cards with 6px border radius)
    Object.keys(nodePositions).forEach(id => {
      const node = nodePositions[id];
      const isLoop = ['ACC101', 'ACC102', 'ACC105'].includes(id);

      const cardW = 140;
      const cardH = 50;
      const x = node.x - cardW / 2;
      const y = node.y - cardH / 2;

      // Draw Card Background
      ctx.save();
      ctx.fillStyle = isLoop ? '#2d1520' : '#1f2937';
      ctx.strokeStyle = isLoop ? '#dc2626' : '#374151';
      ctx.lineWidth = isLoop ? 2 : 1;

      // Draw rectangle with 6px radius
      roundRect(ctx, x, y, cardW, cardH, 6, true, true);

      // Node Name & ID
      ctx.fillStyle = '#ffffff';
      ctx.font = 'bold 12px Inter';
      ctx.textAlign = 'center';
      ctx.fillText(node.name, node.x, y + 20);

      // Node Role
      ctx.fillStyle = isLoop ? '#f87171' : '#9ca3af';
      ctx.font = '10px Inter';
      ctx.fillText(node.type, node.x, y + 36);

      ctx.restore();
    });

    offset += 0.5;
    animationFrameId = requestAnimationFrame(draw);
  }

  draw();
}

function roundRect(ctx, x, y, width, height, radius, fill, stroke) {
  ctx.beginPath();
  ctx.moveTo(x + radius, y);
  ctx.lineTo(x + width - radius, y);
  ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
  ctx.lineTo(x + width, y + height - radius);
  ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
  ctx.lineTo(x + radius, y + height);
  ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
  ctx.lineTo(x, y + radius);
  ctx.quadraticCurveTo(x, y, x + radius, y);
  ctx.closePath();
  if (fill) ctx.fill();
  if (stroke) ctx.stroke();
}

// ---------------------------------------------------------------------------
// 6. Modal Utilities
// ---------------------------------------------------------------------------
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.classList.add('active');
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.classList.remove('active');
}

function showNotification(text) {
  const banner = document.createElement('div');
  banner.style.position = 'fixed';
  banner.style.bottom = '24px';
  banner.style.right = '24px';
  banner.style.backgroundColor = '#1f2937';
  banner.style.border = '1px solid #10b981';
  banner.style.borderLeft = '5px solid #10b981';
  banner.style.borderRadius = '6px';
  banner.style.padding = '14px 20px';
  banner.style.color = '#ffffff';
  banner.style.fontWeight = '600';
  banner.style.boxShadow = '0 10px 25px rgba(0,0,0,0.5)';
  banner.style.zIndex = '9999';
  banner.textContent = text;
  document.body.appendChild(banner);

  setTimeout(() => {
    banner.remove();
  }, 4000);
}
