let allStocks = [];
let activeFilter = 'ALL';

const DECISION_LABELS = {
    'HIGH_CONVICTION': '🟢 HIGH CONVICTION',
    'GO':              '🟩 GO',
    'WATCH_CLOSELY':   '🟡 WATCH CLOSELY',
    'WATCH':           '🟨 WATCH',
    'NO_GO':           '🔴 NO-GO',
};

async function loadResults() {
    try {
        const res  = await fetch('results.json?t=' + Date.now());
        if (!res.ok) { showEmpty('No scan data yet. Run workflow manually from GitHub Actions.'); return; }
        const data = await res.json();

        allStocks = data.stocks || [];

        // Summary counts
        document.getElementById('count-hc').textContent      = data.summary?.high_conviction || 0;
        document.getElementById('count-go').textContent      = data.summary?.go              || 0;
        document.getElementById('count-wc').textContent      = data.summary?.watch_closely   || 0;
        document.getElementById('count-w').textContent       = data.summary?.watch           || 0;
        document.getElementById('count-scanned').textContent = data.total_scanned            || '—';

        if (data.scan_date && data.scan_time) {
            document.getElementById('scan-time').textContent = data.scan_date + ' ' + data.scan_time;
        }

        renderTable(activeFilter);

    } catch(e) {
        console.error(e);
        showEmpty('Error loading results. Check console.');
    }
}

function renderTable(filter) {
    const tbody = document.getElementById('tbody');
    const stocks = filter === 'ALL' ? allStocks : allStocks.filter(s => s.decision === filter);

    if (stocks.length === 0) {
        tbody.innerHTML = `<tr><td colspan="14" class="loading-cell">No stocks match this filter today.</td></tr>`;
        return;
    }

    tbody.innerHTML = stocks.map(s => {
        const p   = s.position;
        const scoreColor = s.score >= 75 ? '#00c853' : s.score >= 50 ? '#ffd740' : '#ff5252';

        return `
        <tr>
            <td><span class="badge badge-${s.decision}">${DECISION_LABELS[s.decision] || s.decision}</span></td>
            <td style="font-weight:700;color:#fff;font-size:1em">${s.symbol}</td>
            <td>
                <div class="score-wrap">
                    <div class="score-bar"><div class="score-fill" style="width:${s.score}%;background:${scoreColor}"></div></div>
                    <span class="score-num" style="color:${scoreColor}">${s.score}</span>
                </div>
            </td>
            <td>${s.in_stockedge ? '<span class="se-yes">✅ YES</span>' : '<span class="se-no">—</span>'}</td>
            <td class="price-cell">₹${s.price?.toFixed(2)}</td>
            <td class="rsi-cell" style="color:${s.rsi>=55&&s.rsi<=65?'#69f0ae':s.rsi>65?'#ffd740':'#aaa'}">${s.rsi?.toFixed(1)}</td>
            <td class="vol-cell">${s.vol_ratio?.toFixed(1)}x</td>
            <td class="dist-cell">${s.ema_dist_pct?.toFixed(1)}%</td>
            <td class="stop-cell">${p ? '₹'+p.stop_loss : '—'}</td>
            <td class="t1-cell">${p ? '₹'+p.target_1 : '—'}</td>
            <td class="t2-cell">${p ? '₹'+p.target_2 : '—'}</td>
            <td class="shares-cell">${p ? p.shares : '—'}</td>
            <td class="risk-cell">${p ? '₹'+p.risk_amount?.toLocaleString('en-IN') : '—'}</td>
            <td class="reasons">${(s.reasons||[]).join(' · ')}</td>
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
        `<tr><td colspan="14" class="loading-cell">${msg}</td></tr>`;
}

// Load on start, refresh every 5 min
document.addEventListener('DOMContentLoaded', loadResults);
setInterval(loadResults, 5 * 60 * 1000);
document.addEventListener('visibilitychange', () => { if (!document.hidden) loadResults(); });
