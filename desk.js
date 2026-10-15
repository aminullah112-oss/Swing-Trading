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

let desk = {data: null, rd: null, showFiltered: false, ledger: null, picked: null, manual: false};

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

// ---- user preferences (this browser only). Risk can be lowered, never raised above the audited limit in the scan.
const PREF_KEY = 'edge_desk_prefs_v1';
function loadPrefs() {
    try { return Object.assign({capital: '', riskPct: '', tierScale: false}, JSON.parse(localStorage.getItem(PREF_KEY) || '{}')); }
    catch (e) { return {capital: '', riskPct: '', tierScale: false}; }
}
function savePrefs(p) { try { localStorage.setItem(PREF_KEY, JSON.stringify(p)); } catch (e) { /* private mode: keep in memory only */ } }
let prefs = loadPrefs();
const effCapital = cfg => (Number(prefs.capital) > 0 ? Number(prefs.capital) : cfg.capital);
const effRiskPct = (cfg, liveRisk) => liveRisk > 0 ? Math.min(liveRisk, cfg.risk_pct) : PlanMath.effectiveRisk(prefs.riskPct, cfg.risk_pct);
function riskMult(s) {
    const sel = s.selection || {};
    return (prefs.tierScale ? (PlanMath.TIER_MULT[(sel.conviction || {}).level] ?? 1) : 1) * (sel.risk_mult ?? 1);
}

// Size from capital and the risk rule: shares = capital x risk% / (buy-stop - stop), capped at max position % of capital.
function plan(s, cfg, liveRisk) {
    const capital = effCapital(cfg), pct = effRiskPct(cfg, liveRisk), mult = riskMult(s), stopDist = s.trigger - s.stop_loss;
    const sh = PlanMath.sizeShares(capital, pct * mult, s.trigger, stopDist, cfg.max_pos_pct);
    const custom = Number(prefs.capital) > 0 || Number(prefs.riskPct) > 0 || prefs.tierScale;
    const label = sh === 0 ? `0: one share risks more than ${(pct * mult).toFixed(2)}% of ${inr0(capital)}`
        : `${liveRisk > 0 ? 'live' : (custom ? 'your' : 'reference')} size: ${(pct * mult).toFixed(2)}% of ${inr0(capital)}`;
    return {shares: sh, invested: sh * s.trigger, risk: sh * stopDist, label, live: liveRisk > 0};
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

const CONV = {high: ['⭐ High conviction', 'meets all five selection conditions'], medium: ['Medium conviction', 'meets three or four of the five conditions'],
              low: ['Low conviction', 'meets two or fewer of the five conditions'], avoid: ['⛔ Avoid', 'a known event blocks this entry']};
function selectionBlock(s) {
    const x = s.selection;
    if (!x) return '';
    const cv = x.conviction || {level: x.tier === 'preferred' ? 'high' : x.tier, met: 0, of: 5};
    const t = CONV[cv.level] || [cv.level, ''];
    const conds = Object.entries(x.conditions).map(([k, v]) => `<li class="chk-${v ? 'ok' : 'warn'}">${v ? '✅' : '⚠️'} ${esc(k)}</li>`).join('');
    const ev = x.events.reasons.map(r => `<li class="chk-block">⛔ ${esc(r)}</li>`).join('') +
        x.events.unverified.map(r => `<li class="chk-warn">❔ ${esc(r)}</li>`).join('');
    return `<details class="selection"><summary><b>${esc(t[0])}</b> (${esc(cv.met)} of ${esc(cv.of)} conditions) · RS rank ${x.rs_rank_pct != null ? esc(x.rs_rank_pct) + 'th pct' : 'n/a'} · ${esc(x.sector)} · Nifty ${esc(x.regime)}</summary>
        <ul class="checks">${conds}${ev}${x.size_notes.map(n => `<li class="chk-warn">📉 ${esc(n)}</li>`).join('')}</ul>
        <div class="setup-label">${esc(t[1])}. This is a checklist count, <b>not a probability of profit</b>: no test has shown that a higher level wins more often. C0 trades every signal; the levels are tested in PREREG_v2.</div></details>`;
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

function heldFromLedger(led) {
    const open = ((led && led.signals) || []).filter(r => r.status === 'open' && r.evidence_eligible !== false);
    const risk = open.reduce((t, r) => t + (r.shares ? (r.risk_amount || 0) * ((r.filled_shares ?? r.shares) / r.shares) : 0), 0);
    return {symbols: open.map(r => r.symbol), risk};
}

function renderSettings(cfg) {
    const el = document.getElementById('sizing-panel');
    if (!el) return;
    const cap = effCapital(cfg), rp = PlanMath.effectiveRisk(prefs.riskPct, cfg.risk_pct);
    el.innerHTML = `<details class="settings" ${Number(prefs.capital) > 0 || Number(prefs.riskPct) > 0 || prefs.tierScale ? 'open' : ''}>
        <summary><b>Capital and sizing</b>: ${esc(inr0(cap))} · risk ${esc(rp.toFixed(2))}% per trade${prefs.tierScale ? ' · scaled by conviction' : ''}</summary>
        <div class="settings-grid">
            <label>Capital (₹)<input id="pref-capital" type="number" min="0" step="1000" inputmode="numeric" placeholder="${esc(cfg.capital)}" value="${esc(prefs.capital)}"></label>
            <label>Risk per trade (%) <small>max ${esc(cfg.risk_pct)}</small><input id="pref-risk" type="number" min="0.05" max="${esc(cfg.risk_pct)}" step="0.05" inputmode="decimal" placeholder="${esc(cfg.risk_pct)}" value="${esc(prefs.riskPct)}"></label>
            <label class="inline"><input id="pref-tier" type="checkbox" ${prefs.tierScale ? 'checked' : ''}> Size smaller for lower conviction (high 100%, medium 75%, low 50% of the risk budget)</label>
            <button id="pref-reset" type="button">Reset to defaults</button>
        </div>
        <div class="setup-label">Saved in this browser only. Change capital when your cash flow changes; share counts update at once. The risk per trade can be lowered but never raised above ${esc(cfg.risk_pct)}%, and the ${esc(cfg.max_pos_pct)}% position cap and ${esc(cfg.max_open_risk_pct)}% total open-risk cap always apply.</div>
    </details>`;
    const upd = () => {
        prefs = {capital: document.getElementById('pref-capital').value, riskPct: document.getElementById('pref-risk').value, tierScale: document.getElementById('pref-tier').checked};
        savePrefs(prefs); desk.manual = false; render();
    };
    ['pref-capital', 'pref-risk'].forEach(id => document.getElementById(id).addEventListener('change', upd));
    document.getElementById('pref-tier').addEventListener('change', upd);
    document.getElementById('pref-reset').addEventListener('click', () => { prefs = {capital: '', riskPct: '', tierScale: false}; savePrefs(prefs); desk.manual = false; render(); });
}

function renderAlloc(ok, cfg, liveRisk) {
    const el = document.getElementById('alloc-panel');
    if (!el) return;
    if (!ok.length) { el.innerHTML = ''; return; }
    const capital = effCapital(cfg), pct = effRiskPct(cfg, liveRisk), held = heldFromLedger(desk.ledger);
    const cands = ok.map(s => {
        const sel = s.selection || {};
        return {symbol: s.symbol, sector: sel.sector || s.symbol, level: (sel.conviction || {}).level || 'medium', rs: sel.rs_rank_pct, entry: s.trigger,
                stopDist: s.trigger - s.stop_loss, riskMult: riskMult(s)};
    });
    if (!desk.manual || !desk.picked) {
        desk.picked = new Set(PlanMath.autoSelect(cands, {capital, riskPct: pct, maxOpenRiskPct: cfg.max_open_risk_pct, maxPosPct: cfg.max_pos_pct,
            maxPerSector: cfg.max_per_sector || 2, existingRisk: held.risk, held: held.symbols}));
    }
    const rows = PlanMath.rank(cands).map(c => {
        const sh = PlanMath.sizeShares(capital, pct * c.riskMult, c.entry, c.stopDist, cfg.max_pos_pct);
        const on = desk.picked.has(c.symbol), heldNow = held.symbols.includes(c.symbol);
        return {c, sh, on, heldNow, value: sh * c.entry, risk: sh * c.stopDist};
    });
    const chosen = rows.filter(r => r.on && r.sh > 0);
    const totRisk = held.risk + chosen.reduce((t, r) => t + r.risk, 0), totVal = chosen.reduce((t, r) => t + r.value, 0);
    const budget = capital * cfg.max_open_risk_pct / 100;
    const sectors = {}; chosen.forEach(r => { sectors[r.c.sector] = (sectors[r.c.sector] || 0) + 1; });
    const warns = [];
    if (totRisk > budget * 1.0000001) warns.push(`total open risk ${inr0(totRisk)} is above the ${cfg.max_open_risk_pct}% limit (${inr0(budget)})`);
    Object.entries(sectors).forEach(([g, n]) => { if (n > (cfg.max_per_sector || 2)) warns.push(`${n} positions in ${g} (limit ${cfg.max_per_sector || 2})`); });
    chosen.forEach(r => { if (r.value > capital * cfg.max_pos_pct / 100 * 1.0000001) warns.push(`${r.c.symbol} is above the ${cfg.max_pos_pct}% position cap`); });
    el.innerHTML = `<h2 class="section-title">Position plan <span class="muted">concentrate or diversify, within the risk limits</span></h2>
        <div class="table-container"><table><thead><tr><th></th><th>Stock</th><th>Conviction</th><th>Sector</th><th>Shares</th><th>Invested</th><th>Risk</th></tr></thead><tbody>` +
        rows.map(r => `<tr class="stock-row"><td><input type="checkbox" data-sym="${esc(r.c.symbol)}" ${r.on ? 'checked' : ''} ${r.sh < 1 || r.heldNow ? 'disabled' : ''}></td>
            <td><strong>${esc(r.c.symbol)}</strong>${r.heldNow ? ' <small>(already held)</small>' : ''}</td><td>${esc((CONV[r.c.level] || [r.c.level])[0])}</td><td>${esc(r.c.sector)}</td>
            <td>${esc(r.sh)}</td><td>${r.sh ? inr0(r.value) : '—'}</td><td>${r.sh ? inr0(r.risk) : '—'}</td></tr>`).join('') + `</tbody></table></div>
        <div class="capital-note"><b>${esc(chosen.length)} position${chosen.length === 1 ? '' : 's'}</b> · invested ${inr0(totVal)} (${(totVal / capital * 100).toFixed(0)}% of capital, ${inr0(capital - totVal)} left) ·
            total open risk ${inr0(totRisk)} = ${(totRisk / capital * 100).toFixed(2)}% of capital (limit ${esc(cfg.max_open_risk_pct)}%)${held.risk ? ` including ${inr0(held.risk)} already open` : ''}.
            ${warns.length ? `<br><span class="chk-block">⛔ ${warns.map(esc).join('; ')}</span>` : ''}
            <br><small>Boxes are pre-ticked strongest first (conviction, then relative strength) until the risk budget, the sector limit or the stocks run out. Untick or tick to change it.
            Each trade risks the same rupee amount whatever you pick, so putting everything into one stock does not raise the amount at stake on that trade; it removes the protection of other positions,
            and a gap through its stop would hit your whole plan at once. Conviction is a checklist count, not a probability.</small></div>`;
    el.querySelectorAll('input[data-sym]').forEach(cb => cb.addEventListener('change', () => {
        const set = new Set(rows.filter(r => r.on).map(r => r.c.symbol));
        cb.checked ? set.add(cb.dataset.sym) : set.delete(cb.dataset.sym);
        desk.picked = set; desk.manual = true; renderAlloc(ok, cfg, liveRisk);
    }));
}

function render() {
    const {data, rd} = desk;
    const cfg = data.risk_config;
    const liveRisk = rd ? (rd.policy.live_risk_pct_allowed || 0) : 0;
    const stocks = data.stocks || [];
    const level = s => ((s.selection || {}).conviction || {}).level || 'medium';
    const ok = stocks.filter(s => s.execution_ok).sort((a, b) => ({high: 0, medium: 1, low: 2, avoid: 3}[level(a)] - {high: 0, medium: 1, low: 2, avoid: 3}[level(b)]) || (((b.selection || {}).rs_rank_pct ?? -1) - ((a.selection || {}).rs_rank_pct ?? -1))), out = stocks.filter(s => !s.execution_ok);
    renderDataNotes(data);
    renderSettings(cfg);
    renderAlloc(ok, cfg, liveRisk);
    setText('count-signals', stocks.length);
    setText('count-tradeable', ok.length);
    setText('count-scanned', data.total_scanned || '—');
    document.getElementById('market-row').innerHTML = marketCards(data.market);
    document.getElementById('capital-note').innerHTML =
        `<strong>Capital:</strong> ${esc(inr0(effCapital(cfg)))} &nbsp;|&nbsp; <strong>Risk/trade:</strong> ${esc(effRiskPct(cfg, liveRisk).toFixed(2))}% (limit ${esc(cfg.risk_pct)}%) &nbsp;|&nbsp; ` +
        `<strong>Max position:</strong> ${esc(cfg.max_pos_pct)}% &nbsp;|&nbsp; <strong>Open-risk cap:</strong> ${esc(cfg.max_open_risk_pct)}% ` +
        `(about ${Math.max(1, Math.floor(cfg.max_open_risk_pct / effRiskPct(cfg, liveRisk)))} positions at once). Gaps can push real losses past the stop.`;

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
    const [data, rd, hl, led] = await Promise.all([getJSON('results.json'), getJSON('readiness.json'), getJSON('health.json'), getJSON('ledger.json')]);
    renderFreshness(data);
    renderLiveGate(rd, hl);
    const grid = document.getElementById('plans');
    if (!data) { grid.innerHTML = '<div class="empty-note">No scan data yet. Run the Daily Stock Screen workflow.</div>'; return; }
    if (!data.strategy || !data.market) {
        grid.innerHTML = '<div class="empty-note">results.json is from an older scanner version. Run the Daily Stock Screen workflow to refresh it.</div>';
        return;
    }
    setText('scan-time', data.scan_date + ' ' + data.scan_time);
    desk = Object.assign(desk, {data, rd, ledger: led});
    render();
}
document.addEventListener('DOMContentLoaded', init);
setInterval(init, 5 * 60 * 1000);
document.addEventListener('visibilitychange', () => { if (!document.hidden) init(); });
