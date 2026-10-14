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
        return {shares: sh, invested: sh * s.trigger, risk: sh * rps, live: true,
                label: sh === 0 ? `0: one share risks more than the ${liveRisk}% live limit` : `live size (≤${liveRisk}% risk)`};
    }
    const p = s.position || {};
    return {shares: p.shares ?? 0, invested: p.invested ?? 0, risk: p.risk_amount ?? 0,
            label: `reference size (${cfg.risk_pct}% risk, paper)`, live: false};
}

const BASIS = {rule: 'C0 rule (backtested)', reference: 'reference level', empirical: 'past C0 trades', untested: 'untested idea'};
function planBlock(s) {
    const p = s.plan;
    if (!p) return '';
    const tag = b => `<span class="setup-label">${esc(BASIS[b] || b)}</span>`;
    const lv = p.profit_review_levels.levels.map(l => `${l.r}R ${inr2(l.price)} (+${l.gain_pct}%)`).join(' · ');
    const d = p.expected_duration;
    const dur = d.available === false ? esc(d.note)
        : `Winners usually ran <b>${esc(d.winners_median_days)}</b> sessions (middle half ${esc(d.winners_range_days[0])}-${esc(d.winners_range_days[1])}); ` +
          `stopped-out trades ended after ~${esc(d.losers_median_days)}. Typical winner +${esc(d.typical_winner_r)}R (${inr2(d.typical_winner_price)}), ` +
          `strong +${esc(d.strong_winner_r)}R. Win rate ${Math.round(d.win_rate * 100)}% <small>(${esc(d.from)})</small>`;
    const sell = p.sell_trigger, add = p.add_more;
    return `<details class="trade-plan" open><summary>Trade plan from daily data</summary><ul class="checks">
        <li>🎯 <b>Profit review levels</b> ${tag('reference')}: ${lv}. <small>${esc(p.profit_review_levels.note)}</small></li>
        <li>⛔ <b>Stop</b> ${tag('rule')}: ${inr2(p.stop.price)}. <small>${esc(p.stop.note)}</small></li>
        <li>⏱ <b>How long</b> ${tag('empirical')}: ${dur}. <small>${esc(d.note || '')}</small></li>
        <li>🔔 <b>Sell trigger</b> ${tag('rule')}: ${esc(sell.condition)}. EMA50 now ${inr2(sell.ema50_now)}${sell.ema50_in_about_a_week ? `, about ${inr2(sell.ema50_in_about_a_week)} in a week` : ''}; ${esc(sell.time_exit)}.
            Watch: ${sell.warning_signs.map(esc).join('; ')}.</li>
        <li>➕ <b>Add more</b> ${tag('untested')} <i>${esc(add.default)}</i>: only if ${add.conditions.map(esc).join('; ')}. Up to ${esc(add.max_extra_shares)} extra shares (₹${esc(add.risk_of_add_inr)} risk).
            <small>${esc(add.note)}. Never: ${esc(add.never_add)}.</small></li></ul></details>`;
}

const TIER = {preferred: ['⭐ Preferred', 'meets every selection condition'], standard: ['Standard', 'a C0 signal that misses one or more selection conditions'], avoid: ['⛔ Avoid', 'known event risk']};
function selectionBlock(s) {
    const x = s.selection;
    if (!x) return '';
    const t = TIER[x.tier] || [x.tier, ''];
    const conds = Object.entries(x.conditions).map(([k, v]) => `<li class="chk-${v ? 'ok' : 'warn'}">${v ? '✅' : '⚠️'} ${esc(k)}</li>`).join('');
    const ev = x.events.reasons.map(r => `<li class="chk-block">⛔ ${esc(r)}</li>`).join('') +
        x.events.unverified.map(r => `<li class="chk-warn">❔ ${esc(r)}</li>`).join('');
    return `<details class="selection"><summary><b>${esc(t[0])}</b> · RS rank ${x.rs_rank_pct != null ? esc(x.rs_rank_pct) + 'th pct' : 'n/a'} · ${esc(x.sector)} · Nifty ${esc(x.regime)}</summary>
        <ul class="checks">${conds}${ev}${x.size_notes.map(n => `<li class="chk-warn">📉 ${esc(n)}</li>`).join('')}</ul>
        <div class="setup-label">${esc(t[1])}. Hypothesis, not proven: C0 trades every signal; the tiers are tested in PREREG_v2. Rank order was tested for admission and did not help.</div></details>`;
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
        ${selectionBlock(s)}
        ${planBlock(s)}
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
    const dq = data.data_quality;
    const untrusted = !!dq && dq.status !== 'TRUSTED';
    lag.hidden = !untrusted;
    if (untrusted) {
        const cc = dq.crosscheck || {};
        lag.innerHTML = `⚠ NO ENTRIES TODAY — the market data is not confirmed. Latest official data is ${esc(data.data_cutoff)}, but the session to trade is ${esc(dq.expected_session)}. ` +
            `Why: ${dq.reasons.map(esc).join('; ')}. ` +
            `Yahoo normally publishes official daily bars overnight; the 08:30 IST scan usually has them. ` +
            `NSE cross-check: ${esc(cc.status || 'not run')}${cc.filled && cc.filled.length ? ` (${cc.filled.length} bars filled from NSE)` : ''}. ` +
            `Nothing below is an entry instruction.`;
    }
    const pbar = document.getElementById('prov-bar');
    if (pbar) {
        const n = (data.preview || []).length;
        pbar.hidden = !(untrusted && n);
        if (n) pbar.innerHTML = `ℹ WATCHLIST ONLY — ${esc(n)} stocks would qualify on provisional 5-minute data for ${esc(data.provisional && data.provisional.date)}. ` +
            `They are shown below as a watchlist to prepare for the next trusted scan. They are not entries, and the plan may change when the official bar arrives.`;
    }
    const miss = data.missing_symbols || [];
    const note = document.getElementById('missing-note');
    note.hidden = !miss.length;
    if (miss.length) {
        note.innerHTML = `<strong>Not scanned (no usable data):</strong> ${miss.map(esc).join(', ')} — these ${miss.length} stocks cannot signal until their data returns. ` +
            `Often a renamed, merged or delisted ticker; see SYMBOL_ALIASES in screener.py.`;
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
        `<div class="empty-note">📊 No tradeable signals right now.<br><small>${(data.data_quality && data.data_quality.status !== 'TRUSTED') ? 'The data is not confirmed, so no entries are allowed. Any provisional candidates are listed under Watchlist below.' : (stocks.length ? 'Every signal failed an execution check (see below).' : 'No stock met the entry conditions. That is normal: the system trades selectively.')}</small></div>`;

    const wl = document.getElementById('watchlist');
    if (wl) {
        const pv = data.preview || [];
        wl.hidden = !pv.length;
        document.getElementById('watchlist-count').textContent = pv.length;
        document.getElementById('watchlist-body').innerHTML = pv.map(s => `
            <tr class="stock-row"><td><strong>${esc(s.symbol)}</strong></td><td>${esc(SETUP_LABELS[s.setup_type] || s.setup_type)}</td>
            <td>${inr2(s.price)}</td><td>${inr2(s.trigger)}</td><td>${inr2(s.stop_loss)}</td><td>${esc(s.rsi.toFixed(0))}</td><td>${esc(s.from_52w_high.toFixed(1))}%</td></tr>`).join('');
    }

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
