// Paper-trading page: ledger, forward results, readiness scorecard and health.
const REASON_LABELS = {
    stop: 'Stop', gap_stop: 'Gap through stop', ema50: 'Closed < EMA50', ema20: 'Closed < EMA20',
    time: '120-day limit', trail: 'Trail', gap_trail: 'Gap through trail',
};
const GATE_STATUS = {pass: '✅ pass', fail: '❌ fail', insufficient: '⏳ not enough data', manual: '🖐 not attested'};

function renderLedger(led) {
    if (!led) return;
    const sum = led.summary || {};
    setText('count-open', sum.open ?? 0);
    setText('label-open', 'Paper: open' + (sum.pending ? ` (+${sum.pending} pending)` : ''));
    setText('count-closed', sum.closed ?? 0);
    setText('count-signals', sum.signals ?? 0);
    setText('avg-r', signed(sum.avg_r_incl_open));
    const ci = sum.avg_r_ci95 ? ` · 95% CI ${sum.avg_r_ci95[0]}..${sum.avg_r_ci95[1]} (naive)` : '';
    setText('ledger-meta', `since ${led.started || '—'} · ${sum.closed ?? 0} closed, win rate ` +
        `${sum.win_rate != null ? Math.round(sum.win_rate * 100) + '%' : '—'}, closed-only avg ${signed(sum.avg_r)}R, ` +
        `incl. open ${signed(sum.avg_r_incl_open)}R (${sum.total_r_incl_open ?? 0}R total)${ci}` +
        (led.last_update_ok === false ? ' · ⚠ last price update failed' : ''));

    const oc = sum.outcomes;
    if (oc) {
        const pct = v => v == null ? '—' : Math.round(v * 100) + '%';
        setText('outcome-meta', `triggered ${pct(oc.trigger_rate)} · closed win rate ${pct(oc.closed_win_rate)} · entered in profit ${pct(oc.entered_in_profit_rate)}` +
            (oc.legacy_excluded ? ` · ${oc.legacy_excluded} legacy excluded` : ''));
        document.getElementById('outcome-body').innerHTML = Object.values(oc.classes).map(c =>
            `<tr class="stock-row"><td>${esc(c.label)}</td><td>${esc(c.n)}</td><td>${c.avg_r != null ? signed(c.avg_r) : '—'}</td></tr>`).join('');
    }

    const order = {open: 0, pending: 1, closed: 2, expired: 3, void: 4};
    const rows = (led.signals || []).slice().sort((a, b) =>
        (order[a.status] - order[b.status]) || String(b.signal_date).localeCompare(String(a.signal_date))).slice(0, 80);
    if (!rows.length) return;
    document.getElementById('ledger-body').innerHTML = rows.map(r => {
        const rVal = r.status === 'closed' ? r.r : r.unrealized_r;
        const rCell = rVal != null
            ? `<span style="color:${rVal >= 0 ? '#00c853' : '#ff5252'}">${signed(rVal)}${r.status === 'open' ? ' (mtm)' : ''}</span>` : '—';
        const exit = r.status === 'closed'
            ? `${inr2(r.exit)}<div class="setup-label">${esc(REASON_LABELS[r.exit_reason] || r.exit_reason)} · ${esc(r.exit_date)}</div>`
            : r.status === 'open' ? `${inr2(r.mark_price)}${r.exit_signal ? '<div class="setup-label">EMA50 exit signalled — exits next open</div>' : ''}` : '—';
        return `
        <tr class="stock-row${r.status === 'expired' ? ' over-budget' : ''}">
            <td>${esc(r.status)}</td><td><strong>${esc(r.symbol)}</strong></td>
            <td>${esc(r.signal_date)}<div class="setup-label">buy &gt; ${inr2(r.trigger)}</div></td>
            <td>${r.entry ? inr2(r.entry) + `<div class="setup-label">${esc(r.entry_date)}</div>` : '—'}</td>
            <td>${exit}</td><td>${rCell}</td><td>${r.days_held ?? '—'}</td><td>${esc(r.shares)}</td>
            <td>${r.pnl_inr != null ? inr0(r.pnl_inr) : '—'}</td><td>${r.taken ? '✅' : (r.entry ? '—' : '')}</td>
        </tr>`;
    }).join('');
}

function renderReadiness(rd, hl) {
    renderLiveGate(rd, hl);
    if (!rd) return;
    const p = rd.policy;
    setText('readiness-meta', `${p.score}/10 · generated ${String(rd.generated).slice(0, 16).replace('T', ' ')} UTC`);
    const fmt = v => v == null ? '' : (typeof v === 'object' ? JSON.stringify(v) : String(v));
    document.getElementById('readiness-body').innerHTML = rd.gates.map(g => `
        <tr class="stock-row">
            <td>${esc(g.id)} ${esc(g.label)}${g.critical ? ' <strong>(critical)</strong>' : ''}</td>
            <td>${esc(g.earned)}/${esc(g.points)}</td><td>${esc(GATE_STATUS[g.status] || g.status)}</td>
            <td>${esc([fmt(g.value), g.detail].filter(Boolean).join(' — '))}</td>
        </tr>`).join('');
    if (hl) {
        const bad = hl.checks.filter(c => c.level !== 'ok');
        document.getElementById('health-note').innerHTML = `<strong>Health: ${esc(hl.status)}</strong>` +
            (bad.length ? ' — ' + bad.map(c => `${esc(c.id)}: ${esc(c.msg)}`).join(' · ') : ' — all checks passing');
    }
}

async function init() {
    const [res, led, rd, hl] = await Promise.all([getJSON('results.json'), getJSON('ledger.json'), getJSON('readiness.json'), getJSON('health.json')]);
    renderFreshness(res);
    renderLedger(led);
    renderReadiness(rd, hl);
}
document.addEventListener('DOMContentLoaded', init);
setInterval(init, 5 * 60 * 1000);
document.addEventListener('visibilitychange', () => { if (!document.hidden) init(); });
