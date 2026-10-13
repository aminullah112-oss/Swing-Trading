let allStocks = [];
let activeFilter = 'ALL';
let riskCfg = null;

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

const esc = v => String(v ?? '').replace(/[&<>"']/g,
    c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const inr0 = n => '₹' + Number(n).toLocaleString('en-IN', {maximumFractionDigits: 0});

// Fresh <= 4 calendar days since the last market bar (covers weekends and a holiday); else Stale.
function renderStatus(data) {
    const bar = document.getElementById('status-bar');
    if (!data.data_cutoff) {
        bar.className = 'status-bar status-stale';
        bar.textContent = '⚠ STALE — results.json has no data-cutoff date (written by an older scanner version).';
        return;
    }
    const ageDays = (Date.now() - new Date(data.data_cutoff + 'T00:00:00+05:30')) / 864e5;
    const fresh   = ageDays <= 4;
    bar.className = 'status-bar ' + (fresh ? 'status-fresh' : 'status-stale');
    bar.textContent = (fresh ? '● FRESH' : '⚠ STALE') +
        ` — market data through ${data.data_cutoff} · scanned ${data.scan_date} ${data.scan_time}` +
        ` · ${data.symbols_processed}/${data.total_scanned} symbols · scan ${data.scan_id}`;
}

function renderRiskNote(cfg) {
    if (!cfg) return;
    document.getElementById('capital-note').innerHTML =
        `<strong>Capital:</strong> ${esc(inr0(cfg.capital))} &nbsp;|&nbsp; ` +
        `<strong>Risk/trade:</strong> HC ${esc(cfg.risk_pct_hc)}% · GO ${esc(cfg.risk_pct_go)}% &nbsp;|&nbsp; ` +
        `<strong>Max position:</strong> ${esc(cfg.max_pos_pct)}% &nbsp;|&nbsp; ` +
        `<strong>Max open risk:</strong> ${esc(cfg.max_open_risk_pct)}% &nbsp;|&nbsp; ` +
        `<strong>Stop:</strong> max(1.5×ATR, 3%) &nbsp;|&nbsp; ` +
        `<strong>Exit:</strong> close below EMA20 (daily). ` +
        `Gaps can push real losses past the stop. Daily-updated screener, not real-time.`;
}

async function loadResults() {
    try {
        const res  = await fetch('results.json?t=' + Date.now());
        if (!res.ok) {
            showEmpty('No scan data yet. Trigger workflow from GitHub Actions tab.');
            return;
        }
        const data = await res.json();
        allStocks  = data.stocks || [];
        riskCfg    = data.risk_config || null;
        renderStatus(data);
        renderRiskNote(data.risk_config);

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
        <tr class="stock-row${p && !p.within_risk_budget ? ' over-budget' : ''}" data-decision="${esc(s.decision)}">
            <td><span class="badge badge-${esc(s.decision)}">${esc(DECISION_LABELS[s.decision] || s.decision)}</span></td>
            <td class="symbol-cell">
                <strong>${esc(s.symbol)}</strong>
                <div class="setup-label">${esc(setupLabel)}</div>
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
            <td class="shares-cell" title="${esc(p?.note || (p && !p.within_risk_budget ? 'Exceeds open-risk budget' : ''))}">${p ? (p.shares || '0') : '—'}${p ? ` <a class="back-link" title="Open in position sizer" href="sizer.html?entry=${encodeURIComponent(s.price)}&stop=${encodeURIComponent(p.stop_loss)}">🧮</a>` : ''}</td>
            <td class="risk-cell">${p ? '₹' + p.risk_amount?.toLocaleString('en-IN') : '—'}</td>
            <td class="reasons">${esc((s.reasons||[]).slice(0,3).join(' · '))}</td>
        </tr>`;
    }).join('');
}

function filterDecision(btn, decision) {
    activeFilter = decision;
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    btn.classList.add('active');
    renderTable(decision);
}

function showEmpty(msg) {
    document.getElementById('tbody').innerHTML =
        `<tr><td colspan="15" class="loading-cell">${esc(msg)}</td></tr>`;
}

document.addEventListener('DOMContentLoaded', loadResults);
setInterval(loadResults, 5 * 60 * 1000);
document.addEventListener('visibilitychange', () => {
    if (!document.hidden) loadResults();
});
