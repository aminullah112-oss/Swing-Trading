// Trade desk (homepage): market context + analysed trade plans for today's signals.
const SETUP_LABELS = {
    'PULLBACK_EMA20': '📉 Pullback to EMA20', 'PULLBACK_EMA50': '📉 Pullback to EMA50',
    'BREAKOUT_CONT': '🚀 Breakout continuation', 'COMPRESSION': '🔲 Compression', 'TRENDING': '📈 Trending',
};
const ICON = {ok: '✅', warn: '⚠️', block: '⛔'};
const MANUAL_CHECKS = [
    'Results / earnings date inside the next 5 sessions? (skip it or size down)',
    'F&O ban, ASM/GSM list or circuit-limit status',
    'Corporate action before entry: ex-dividend, split, bonus, rights',
    'Recent news, block/bulk deals or regulatory issues',
    'Sector overlap with positions you already hold (avoid several names from one sector)',
    'Your own chart read: is there a clean base, or heavy supply just overhead?',
];

let desk = {data: null, rd: null, showFiltered: false};

function sparkSVG(sp, trigger, stop) {
    if (!sp || !sp.close || sp.close.length < 5) return '';
    const W = 300, H = 110, P = 6;
    const vals = [...sp.close, ...sp.ema20, ...sp.ema50, trigger, stop];
    const lo = Math.min(...vals), hi = Math.max(...vals), n = sp.close.length;
    const x = i => P + i * (W - 2 * P) / (n - 1);
    const y = v => H - P - (v - lo) * (H - 2 * P) / ((hi - lo) || 1);
    const line = (arr, color, w, dash = '') =>
        `<polyline fill="none" stroke="${color}" stroke-width="${w}" ${dash ? `stroke-dasharray="${dash}"` : ''} points="${arr.map((v, i) => x(i).toFixed(1) + ',' + y(v).toFixed(1)).join(' ')}"/>`;
    const hline = (v, color, label) =>
        `<line x1="${P}" x2="${W - P}" y1="${y(v).toFixed(1)}" y2="${y(v).toFixed(1)}" stroke="${color}" stroke-width="1" stroke-dasharray="4 3"/>` +
        `<text x="${W - P - 2}" y="${(y(v) - 3).toFixed(1)}" fill="${color}" font-size="9" text-anchor="end">${label}</text>`;
    return `<svg viewBox="0 0 ${W} ${H}" class="spark" role="img" aria-label="60-day price chart with EMA20, EMA50, buy level and stop">` +
        line(sp.ema50, '#6c8cff', 1.4) + line(sp.ema20, '#ffd740', 1.2) + line(sp.close, '#e8e8e8', 1.8) +
        hline(trigger, '#69f0ae', 'buy') + hline(stop, '#ff5252', 'stop') + `</svg>`;
}

// Size at the live risk the readiness policy allows; otherwise at the scanner's reference (paper) risk.
function plan(s, cfg, liveRisk) {
    const rps = s.trigger - s.stop_loss;
    if (liveRisk > 0 && rps > 0) {
        let sh = Math.floor(cfg.capital * liveRisk / 100 / rps);
        sh = Math.min(sh, Math.floor(cfg.capital * cfg.max_pos_pct / 100 / s.trigger));
        return {shares: sh, invested: sh * s.trigger, risk: sh * rps, label: `live size (≤${liveRisk}% risk)`, live: true};
    }
    const p = s.position || {};
    return {shares: p.shares ?? 0, invested: p.invested ?? 0, risk: p.risk_amount ?? 0,
            label: `reference size (${cfg.risk_pct}% risk, paper)`, live: false};
}

function card(s, cfg, liveRisk) {
    const pl = plan(s, cfg, liveRisk);
    const warns = s.checks.filter(c => c.status !== 'ok');
    const checks = s.checks.map(c => `<li class="chk-${esc(c.status)}">${ICON[c.status] || ''} ${esc(c.text)}</li>`).join('');
    const manual = MANUAL_CHECKS.map(t => `<li>☐ ${esc(t)}</li>`).join('');
    return `
    <article class="plan-card">
        <header class="plan-head">
            <div><strong class="plan-sym">${esc(s.symbol)}</strong><div class="setup-label">${esc(SETUP_LABELS[s.setup_type] || s.setup_type)}</div></div>
            <div class="plan-px">${inr2(s.price)}<div class="setup-label">signal-day close</div></div>
        </header>
        ${sparkSVG(s.spark, s.trigger, s.stop_loss)}
        <div class="plan-grid">
            <div><label>Buy above</label><b class="t1-cell">${inr2(s.trigger)}</b><small>valid for the session after ${esc(s.signal_date)} only</small></div>
            <div><label>Stop-loss</label><b class="stop-cell">${inr2(s.stop_loss)}</b><small>−${esc(s.stop_pct.toFixed(1))}% from entry</small></div>
            <div><label>Shares</label><b>${esc(pl.shares)}</b><small>${esc(pl.label)}</small></div>
            <div><label>Risk</label><b class="risk-cell">${inr0(pl.risk)}</b><small>${inr0(pl.invested)} invested</small></div>
        </div>
        <div class="plan-note">Exit: close below EMA50 (<b>${inr2(s.ema_50)}</b>) → sell next open · max 120 sessions · stop stays fixed.</div>
        <ul class="checks">${checks}</ul>
        <details><summary>Manual pre-trade checklist (not automated)</summary><ul class="checks manual">${manual}</ul></details>
        <footer class="plan-foot">
            <span title="Close of the session the signal was generated on">signal: ${esc(s.signal_date)}</span><span>RSI ${esc(s.rsi.toFixed(0))}</span><span>Vol ${esc(s.vol_ratio.toFixed(1))}x</span>
            <span>${esc(s.from_52w_high.toFixed(1))}% from 52w high</span><span>ATR ${esc(s.atr_pct.toFixed(1))}%</span>
            ${s.in_stockedge ? '<span title="StockEdge flag has never been backtested">SE ✓</span>' : ''}
            <a class="back-link" href="sizer.html?entry=${encodeURIComponent(s.trigger)}&stop=${encodeURIComponent(s.stop_loss)}">🧮 resize</a>
        </footer>
        ${warns.length ? `<div class="warn-count">${warns.length} caution${warns.length > 1 ? 's' : ''} above</div>` : ''}
    </article>`;
}

function marketCards(m) {
    if (!m) return '';
    const n = m.nifty;
    const items = [
        ['Nifty 50', n ? esc(n.close.toLocaleString('en-IN')) : '—', n ? esc(n.trend) : 'Index data unavailable'],
        ['vs EMA200', n ? signed(n.vs_ema200_pct, 1) + '%' : '—', n ? `EMA50 ${n.ema50.toLocaleString('en-IN')} · EMA200 ${n.ema200.toLocaleString('en-IN')}` : ''],
        ['20-day change', n ? signed(n.change_20d_pct, 1) + '%' : '—', n ? `${n.drawdown_pct}% from 52-week high` : ''],
        ['Universe in Stage 2', m.breadth_stage2_pct + '%', 'share of scanned stocks in an uptrend structure'],
    ];
    return items.map(([l, v, sub]) => `<div class="mkt-card"><div class="card-label">${esc(l)}</div><div class="mkt-val">${v}</div><div class="mkt-sub">${sub}</div></div>`).join('');
}

function renderDataNotes(data) {
    const lag = document.getElementById('lag-bar');
    const behind = data.sessions_behind || 0;
    lag.hidden = !behind;
    if (behind) {
        lag.innerHTML = `⚠ DATA LAG — market data ends ${esc(data.data_cutoff)}, but the last completed session should be ${esc(data.expected_session)} ` +
            `(${esc(behind)} session${behind > 1 ? 's' : ''} behind). If that was a trading day, the buy levels below refer to a session that has already traded: ` +
            `check the live price before placing anything. If it was an exchange holiday, ignore this.`;
    }
    const miss = data.missing_symbols || [];
    const note = document.getElementById('missing-note');
    note.hidden = !miss.length;
    if (miss.length) {
        note.innerHTML = `<strong>Not scanned (no usable data):</strong> ${miss.map(esc).join(', ')} — these ${miss.length} stocks cannot signal until their data returns. ` +
            `Often a renamed, merged or delisted ticker; check the symbol list in screener.py.`;
    }
}

function render() {
    const {data, rd} = desk;
    const cfg = data.risk_config;
    const liveRisk = rd ? (rd.policy.live_risk_pct_allowed || 0) : 0;
    const stocks = data.stocks || [];
    const ok = stocks.filter(s => s.execution_ok), out = stocks.filter(s => !s.execution_ok);
    renderDataNotes(data);
    setText('count-signals', stocks.length);
    setText('count-tradeable', ok.length);
    setText('count-scanned', data.total_scanned || '—');
    document.getElementById('market-row').innerHTML = marketCards(data.market);
    document.getElementById('capital-note').innerHTML =
        `<strong>Capital:</strong> ${esc(inr0(cfg.capital))} &nbsp;|&nbsp; <strong>Reference risk/trade:</strong> ${esc(cfg.risk_pct)}% &nbsp;|&nbsp; ` +
        `<strong>Max position:</strong> ${esc(cfg.max_pos_pct)}% &nbsp;|&nbsp; <strong>Open-risk cap:</strong> ${esc(cfg.max_open_risk_pct)}% ` +
        `(about ${Math.max(1, Math.floor(cfg.max_open_risk_pct / cfg.risk_pct))} positions at once). Gaps can push real losses past the stop.`;

    const grid = document.getElementById('plans');
    grid.innerHTML = ok.length ? ok.map(s => card(s, cfg, liveRisk)).join('') :
        `<div class="empty-note">📊 No tradeable signals today.<br><small>${stocks.length ? 'Every signal failed an execution check (see below).' : 'No stock met the entry conditions. That is normal: the system trades selectively.'}</small></div>`;

    const f = document.getElementById('filtered');
    f.hidden = !out.length;
    document.getElementById('filtered-count').textContent = out.length;
    document.getElementById('filtered-body').innerHTML = out.map(s => `
        <tr class="stock-row"><td><strong>${esc(s.symbol)}</strong></td><td>${inr2(s.trigger)}</td><td>${inr2(s.stop_loss)}</td>
        <td>${esc(s.checks.filter(c => c.status === 'block').map(c => c.text).join(' · '))}</td></tr>`).join('');
}

async function init() {
    const [data, rd, hl] = await Promise.all([getJSON('results.json'), getJSON('readiness.json'), getJSON('health.json')]);
    renderFreshness(data);
    renderLiveGate(rd, hl);
    const grid = document.getElementById('plans');
    if (!data) { grid.innerHTML = '<div class="empty-note">No scan data yet. Run the Daily Stock Screen workflow.</div>'; return; }
    if (!data.strategy || !data.market) {
        grid.innerHTML = '<div class="empty-note">results.json is from an older scanner version. Run the Daily Stock Screen workflow to refresh it.</div>';
        return;
    }
    setText('scan-time', data.scan_date + ' ' + data.scan_time);
    desk = {data, rd};
    render();
}
document.addEventListener('DOMContentLoaded', init);
setInterval(init, 5 * 60 * 1000);
document.addEventListener('visibilitychange', () => { if (!document.hidden) init(); });
