let riskCfg = null;

const SETUP_LABELS = {
    'PULLBACK_EMA20': '📉 Pullback EMA20',
    'PULLBACK_EMA50': '📉 Pullback EMA50',
    'BREAKOUT_CONT':  '🚀 Breakout',
    'COMPRESSION':    '🔲 Compression',
    'TRENDING':       '📈 Trending',
};
const REASON_LABELS = {
    stop: 'Stop', gap_stop: 'Gap through stop', ema50: 'Closed < EMA50', ema20: 'Closed < EMA20',
    time: '120-day limit', trail: 'Trail', gap_trail: 'Gap through trail',
};

const esc = v => String(v ?? '').replace(/[&<>"']/g,
    c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const inr0 = n => '₹' + Number(n).toLocaleString('en-IN', {maximumFractionDigits: 0});
const inr2 = n => '₹' + Number(n).toLocaleString('en-IN', {minimumFractionDigits: 2, maximumFractionDigits: 2});
const setText = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };

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
        `<strong>Risk/trade:</strong> ${esc(cfg.risk_pct)}% &nbsp;|&nbsp; ` +
        `<strong>Max position:</strong> ${esc(cfg.max_pos_pct)}% &nbsp;|&nbsp; ` +
        `<strong>Max open risk:</strong> ${esc(cfg.max_open_risk_pct)}% &nbsp;|&nbsp; ` +
        `Shares are sized from the buy-stop price to the stop. Gaps can push real losses past the stop. ` +
        `Daily-updated screener, not real-time.`;
}

async function loadResults() {
    try {
        const res = await fetch('results.json?t=' + Date.now());
        if (!res.ok) { showEmpty('No scan data yet. Trigger the workflow from the GitHub Actions tab.'); return; }
        const data = await res.json();
        riskCfg = data.risk_config || null;
        renderStatus(data);
        if (!data.strategy) {   // written by the pre-v4 scanner (tiers/score); its fields don't match this page
            showEmpty('results.json is from the previous scanner version. Run the Daily Stock Screen workflow to refresh it.');
            return;
        }
        renderRiskNote(riskCfg);
        setText('count-signals', data.summary?.signals ?? (data.stocks || []).length);
        setText('count-scanned', data.total_scanned || '—');
        if (data.scan_date && data.scan_time) setText('scan-time', data.scan_date + ' ' + data.scan_time);
        renderTable(data.stocks || []);
    } catch (e) {
        console.error(e);
        showEmpty('Error loading results: ' + e.message);
    }
}

function renderTable(stocks) {
    const tbody = document.getElementById('tbody');
    if (!stocks.length) {
        tbody.innerHTML = `
            <tr><td colspan="11" class="loading-cell">
                📊 No signals in the latest scan.<br>
                <small>No stock met the entry conditions today — this is normal and correct behavior.</small>
            </td></tr>`;
        return;
    }
    tbody.innerHTML = stocks.map(s => {
        const p = s.position;
        const dim = p && !p.within_risk_budget ? ' over-budget' : '';
        const setup = SETUP_LABELS[s.setup_type] || s.setup_type || '—';
        const tip = p?.note || (p && !p.within_risk_budget ? 'Exceeds open-risk budget' : '');
        return `
        <tr class="stock-row${dim}" title="${esc(tip)}">
            <td class="symbol-cell"><strong>${esc(s.symbol)}</strong><div class="setup-label">${esc(setup)}</div></td>
            <td class="price-cell">${inr2(s.price)}</td>
            <td class="t1-cell"><strong>${inr2(s.trigger)}</strong></td>
            <td class="stop-cell">${inr2(s.stop_loss)}</td>
            <td class="shares-cell">${p ? esc(p.shares) : '—'}${p ? ` <a class="back-link" title="Open in position sizer" href="sizer.html?entry=${encodeURIComponent(s.trigger)}&stop=${encodeURIComponent(s.stop_loss)}">🧮</a>` : ''}</td>
            <td>${p ? inr0(p.invested) : '—'}</td>
            <td class="risk-cell">${p ? inr0(p.risk_amount) : '—'}</td>
            <td>${inr2(s.ema_50)}</td>
            <td>${s.rsi?.toFixed(1)}</td>
            <td>${Math.max(s.vol_ratio || 0, s.vol_5d_ratio || 0).toFixed(1)}x</td>
            <td>${s.in_stockedge ? '✅' : '—'}</td>
        </tr>`;
    }).join('');
}

function showEmpty(msg) {
    document.getElementById('tbody').innerHTML =
        `<tr><td colspan="11" class="loading-cell">${esc(msg)}</td></tr>`;
}

// ---------- paper-trade ledger ----------
async function loadLedger() {
    try {
        const res = await fetch('ledger.json?t=' + Date.now());
        if (!res.ok) return;
        renderLedger(await res.json());
    } catch (e) { console.error(e); }
}

function renderLedger(led) {
    const sum = led.summary || {};
    setText('count-open', sum.open ?? 0);
    setText('label-open', 'Paper: open' + (sum.pending ? ` (+${sum.pending} pending)` : ''));
    setText('count-closed', sum.closed ?? 0);
    const sg = v => v == null ? '—' : (v > 0 ? '+' : '') + v.toFixed(2);
    setText('avg-r', sg(sum.avg_r_incl_open));
    const ci = sum.avg_r_ci95 ? ` · 95% CI ${sum.avg_r_ci95[0]}..${sum.avg_r_ci95[1]} (naive)` : '';
    setText('ledger-meta', `since ${led.started || '—'} · ${sum.closed ?? 0} closed, win rate ` +
        `${sum.win_rate != null ? Math.round(sum.win_rate * 100) + '%' : '—'}, closed-only avg ${sg(sum.avg_r)}R, ` +
        `incl. open ${sg(sum.avg_r_incl_open)}R (${sum.total_r_incl_open ?? 0}R total)${ci}` +
        (led.last_update_ok === false ? ' · ⚠ last price update failed' : ''));

    const order = {open: 0, pending: 1, closed: 2, expired: 3};
    const rows = (led.signals || []).slice().sort((a, b) =>
        (order[a.status] - order[b.status]) || String(b.signal_date).localeCompare(String(a.signal_date))).slice(0, 60);
    const body = document.getElementById('ledger-body');
    if (!rows.length) return;
    body.innerHTML = rows.map(r => {
        const rVal = r.status === 'closed' ? r.r : r.unrealized_r;
        const rCell = rVal != null ? `<span style="color:${rVal >= 0 ? '#00c853' : '#ff5252'}">${rVal > 0 ? '+' : ''}${Number(rVal).toFixed(2)}${r.status === 'open' ? ' (mtm)' : ''}</span>` : '—';
        const exit = r.status === 'closed'
            ? `${inr2(r.exit)}<div class="setup-label">${esc(REASON_LABELS[r.exit_reason] || r.exit_reason)} · ${esc(r.exit_date)}</div>`
            : r.status === 'open' ? `${inr2(r.mark_price)}${r.exit_signal ? '<div class="setup-label">EMA50 exit signalled — exits next open</div>' : ''}` : '—';
        return `
        <tr class="stock-row${r.status === 'expired' ? ' over-budget' : ''}">
            <td>${esc(r.status)}</td>
            <td><strong>${esc(r.symbol)}</strong></td>
            <td>${esc(r.signal_date)}<div class="setup-label">buy &gt; ${inr2(r.trigger)}</div></td>
            <td>${r.entry ? inr2(r.entry) + `<div class="setup-label">${esc(r.entry_date)}</div>` : '—'}</td>
            <td>${exit}</td>
            <td>${rCell}</td>
            <td>${r.days_held ?? '—'}</td>
            <td>${esc(r.shares)}</td>
            <td>${r.pnl_inr != null ? inr0(r.pnl_inr) : '—'}</td>
            <td>${r.taken ? '✅' : (r.entry ? '—' : '')}</td>
        </tr>`;
    }).join('');
}

function init() { loadResults(); loadLedger(); }
document.addEventListener('DOMContentLoaded', init);
setInterval(init, 5 * 60 * 1000);
document.addEventListener('visibilitychange', () => { if (!document.hidden) init(); });
