// Shared helpers for the desk and paper pages.
const esc = v => String(v ?? '').replace(/[&<>"']/g,
    c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const inr0 = n => '₹' + Number(n).toLocaleString('en-IN', {maximumFractionDigits: 0});
const inr2 = n => '₹' + Number(n).toLocaleString('en-IN', {minimumFractionDigits: 2, maximumFractionDigits: 2});
const setText = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };
const signed = (v, d = 2) => v == null ? '—' : (v > 0 ? '+' : '') + Number(v).toFixed(d);

async function getJSON(path) {
    try {
        const res = await fetch(path + '?t=' + Date.now());
        return res.ok ? await res.json() : null;
    } catch (e) { return null; }
}

// Fresh <= 4 calendar days since the last market bar (covers weekends and a holiday); else Stale.
function renderFreshness(data, barId = 'status-bar') {
    const bar = document.getElementById(barId);
    if (!bar) return;
    if (!data || !data.data_cutoff) {
        bar.className = 'status-bar status-stale';
        bar.textContent = '⚠ STALE — no scan data, or written by an older scanner version.';
        return;
    }
    const dq = data.data_quality;
    if (dq && dq.status !== 'TRUSTED') {
        bar.className = 'status-bar status-stale';
        bar.textContent = `⚠ DATA NOT CONFIRMED — latest official data is ${data.data_cutoff} (expected ${dq.expected_session}) · scanned ${data.scan_date} ${data.scan_time} · no entries until it is confirmed`;
        return;
    }
    const ageDays = (Date.now() - new Date(data.data_cutoff + 'T00:00:00+05:30')) / 864e5;
    const fresh = ageDays <= 4;
    bar.className = 'status-bar ' + (fresh ? 'status-fresh' : 'status-stale');
    bar.textContent = (fresh ? '● FRESH' : '⚠ STALE') +
        ` — market data through ${data.data_cutoff} · scanned ${data.scan_date} ${data.scan_time}` +
        ` · ${data.symbols_processed}/${data.total_scanned} symbols · scan ${data.scan_id}`;
}

function renderLiveGate(rd, hl, barId = 'live-bar') {
    const bar = document.getElementById(barId);
    if (!bar) return;
    if (!rd) { bar.className = 'status-bar status-stale'; bar.textContent = 'Readiness not computed yet (run the Daily Stock Screen workflow).'; return; }
    const p = rd.policy, allowed = p.live_risk_pct_allowed > 0;
    bar.className = 'status-bar ' + (allowed ? 'status-fresh' : 'status-stale');
    const micro = allowed && String(p.mode).startsWith('MICRO');
    bar.innerHTML = (allowed ? `LIVE TRADING ALLOWED at up to ${esc(p.live_risk_pct_allowed)}% risk per trade` +
                               (micro ? ' — MICRO-LIVE EXPERIMENT: real money at tiny size to gather fill and forward evidence; no edge has been shown' : '')
                             : 'LIVE TRADING NOT SUPPORTED BY THE EVIDENCE YET — paper only') +
        ` · readiness ${esc(p.score)}/10 (${esc(p.mode)})` + (hl ? ` · health ${esc(hl.status)}` : '') +
        ` · <a class="back-link" href="paper.html">scorecard and paper results →</a>`;
}
