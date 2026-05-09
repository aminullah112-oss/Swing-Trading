let allStocks = [];
let activeFilter = 'ALL';

const DECISION_LABELS = {
    'HIGH_CONVICTION': '🟢 HIGH CONVICTION',
    'GO':              '🟩 GO',
    'WATCH_CLOSELY':   '🟡 WATCH CLOSELY',
    'WATCH':           '🟨 WATCH',
};

const SETUP_LABELS = {
    'PULLBACK_EMA20': '📉 Pullback EMA20',
    'PULLBACK_EMA50': '📉 Pullback EMA50',
    'BREAKOUT_CONT':  '🚀 Breakout',
    'COMPRESSION':    '🔲 Compression',
    'TRENDING':       '📈 Trending',
};

async function loadResults() {
    try {
        const res  = await fetch('results.json?t=' + Date.now());
        if (!res.ok) {
            showEmpty('No scan data yet. Trigger workflow from GitHub Actions tab.');
            return;
        }
        const data = await res.json();
        allStocks  = data.stocks || [];

        // Summary
        document.getElementById('count-hc').textContent      = data.summary?.high_conviction || 0;
        document.getElementById('count-go').textContent      = data.summary?.go              || 0;
        document.getElementById('count-wc').textContent      = data.summary?.watch_closely   || 0;
        document.getElementById('count-w').textContent       = data.summary?.watch           || 0;
        document.getElementById('count-scanned').textContent = data.total_scanned            || '—';

        if (data.scan_date && data.scan_time) {
            document.getElementById('scan-time').textContent =
                data.scan_date + ' ' + data.scan_time;
        }

        renderTable(activeFilter);

    } catch(e) {
        console.error(e);
        showEmpty('Error loading results: ' + e.message);
    }
}

function renderTable(filter) {
    const tbody  = document.getElementById('tbody');
    const stocks = filter === 'ALL'
        ? allStocks
        : allStocks.filter(s => s.decision === filter);

    if (!stocks || stocks.length === 0) {
        tbody.innerHTML = `
            <tr><td colspan="15" class="loading-cell">
                📊 No stocks match this filter in the latest scan.<br>
                <small>Market conditions may not meet setup criteria today — this is normal and correct behavior.</small>
            </td></tr>`;
        return;
    }

    tbody.innerHTML = stocks.map(s => {
        const p          = s.position;
        const scoreColor = s.score >= 75 ? '#00c853'
                         : s.score >= 58 ? '#ffd740'
                         : '#ff5252';
        const rsiColor   = s.rsi >= 45 && s.rsi <= 60 ? '#00c853'
                         : s.rsi > 60 && s.rsi <= 68  ? '#ffd740'
                         : '#aaa';
        const seLabel    = s.in_stockedge
            ? '<span class="se-yes">✅</span>'
            : '<span class="se-no">—</span>';
        const setupLabel = SETUP_LABELS[s.setup_type] || s.setup_type || '—';
        const h52w       = s.from_52w_high != null
            ? `<span style="color:${s.from_52w_high > -10 ? '#00c853' : '#aaa'}">${s.from_52w_high?.toFixed(1)}%</span>`
            : '—';

        return `
        <tr class="stock-row" data-decision="${s.decision}">
            <td><span class="badge badge-${s.decision}">${DECISION_LABELS[s.decision] || s.decision}</span></td>
            <td class="symbol-cell">
                <strong>${s.symbol}</strong>
                <div class="setup-label">${setupLabel}</div>
            </td>
            <td>
                <div class="score-wrap">
                    <div class="score-bar">
                        <div class="score-fill" style="width:${s.score}%;background:${scoreColor}"></div>
                    </div>
                    <span class="score-num" style="color:${scoreColor}">${s.score}</span>
                </div>
            </td>
            <td>${seLabel}</td>
            <td class="price-cell">₹${s.price?.toFixed(2)}</td>
            <td style="color:${rsiColor};font-weight:600">${s.rsi?.toFixed(1)}</td>
            <td class="vol-cell">${Math.max(s.vol_ratio||0, s.vol_5d_ratio||0).toFixed(1)}x</td>
            <td class="dist-cell">${s.ema_dist_pct?.toFixed(1)}%</td>
            <td>${h52w}</td>
            <td class="stop-cell">${p ? '₹' + p.stop_loss?.toFixed(2) : '—'}</td>
            <td class="t1-cell">${p ? '₹' + p.target_1?.toFixed(2) : '—'}</td>
            <td class="t2-cell">${p ? '₹' + p.target_2?.toFixed(2) : '—'}</td>
            <td class="shares-cell">${p ? p.shares : '—'}</td>
            <td class="risk-cell">${p ? '₹' + p.risk_amount?.toLocaleString('en-IN') : '—'}</td>
            <td class="reasons">${(s.reasons||[]).slice(0,3).join(' · ')}</td>
        </tr>`;
    }).join('');
}

function filterDecision(decision) {
    activeFilter = decision;
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    event.target.classList.add('active');
    renderTable(decision);
}

function showEmpty(msg) {
    document.getElementById('tbody').innerHTML =
        `<tr><td colspan="15" class="loading-cell">${msg}</td></tr>`;
}

document.addEventListener('DOMContentLoaded', loadResults);
setInterval(loadResults, 5 * 60 * 1000);
document.addEventListener('visibilitychange', () => {
    if (!document.hidden) loadResults();
});
