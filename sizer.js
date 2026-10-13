const $ = id => document.getElementById(id);
const inr = n => '₹' + n.toLocaleString('en-IN', {minimumFractionDigits: 2, maximumFractionDigits: 2});
const num = id => parseFloat($(id).value);

// Same rule as screener.position(): stop distance = max(mult * ATR, 3% of price)
function calcPosition({capital, riskPct, entry, stopDist, maxPosPct, costPct}) {
    let shares   = Math.floor(capital * riskPct / 100 / stopDist);
    let capped   = false;
    const maxVal = capital * maxPosPct / 100;
    if (maxPosPct > 0 && shares * entry > maxVal) {
        shares = Math.floor(maxVal / entry);
        capped = true;
    }
    const value = shares * entry;
    return {
        shares, capped, value,
        pct:   capital ? value / capital * 100 : 0,
        risk:  shares * stopDist,
        costs: value * costPct / 100,
    };
}

function update() {
    const mode    = $('stop-mode').value;
    document.querySelectorAll('[data-mode]').forEach(el => { el.hidden = el.dataset.mode !== mode; });

    const capital = num('capital'), riskPct = num('risk-pct'), entry = num('entry');
    const maxPos  = num('max-pos') || 0, costPct = num('costs') || 0;

    let stopDist, stop;
    if (mode === 'atr') {
        const atr = num('atr'), mult = num('atr-mult');
        stopDist  = Math.max(mult * atr, entry * 0.03);
        stop      = entry - stopDist;
    } else {
        stop      = num('stop');
        stopDist  = entry - stop;
    }

    const table = $('sizer-table'), msg = $('sizer-msg');
    const fail = text => { table.hidden = true; msg.hidden = false; msg.textContent = text; $('o-note').textContent = ''; };

    if (![capital, riskPct, entry].every(v => v > 0) || !isFinite(stopDist)) return fail('Enter capital, entry and stop to size a trade.');
    if (stopDist <= 0)  return fail('Stop must be below entry (long trades only).');
    if (stop <= 0)      return fail('Stop distance is larger than the price.');

    const r = calcPosition({capital, riskPct, entry, stopDist, maxPosPct: maxPos, costPct});
    if (r.shares < 1)   return fail('Zero shares: stop is too wide for this risk budget, or entry exceeds the position cap.');

    msg.hidden = true; table.hidden = false;
    $('o-shares').textContent = r.shares.toLocaleString('en-IN');
    $('o-value').textContent  = inr(r.value);
    $('o-pct').textContent    = r.pct.toFixed(1) + '%';
    $('o-sd').textContent     = inr(stopDist) + ' (' + (stopDist / entry * 100).toFixed(1) + '%)';
    $('o-stop').textContent   = inr(stop);
    $('o-risk').textContent   = inr(r.risk) + ' (' + (r.risk / capital * 100).toFixed(2) + '% of capital)';
    $('o-t1').textContent     = inr(entry + 2 * stopDist);
    $('o-t2').textContent     = inr(entry + 3 * stopDist);
    $('o-costs').textContent  = inr(r.costs);
    $('o-note').textContent   = r.capped
        ? `Capped by the ${maxPos}% max position size; actual risk is below your ${riskPct}% budget.`
        : (r.value > capital ? 'Position value exceeds capital — needs margin/MIS. Lower the cap or widen risk tolerance.' : '');
}

// Prefill from query string: sizer.html?entry=1250&stop=1190&capital=750000&risk=1
const q = new URLSearchParams(location.search);
[['entry','entry'], ['stop','stop'], ['capital','capital'], ['risk','risk-pct']].forEach(([k, id]) => {
    if (q.has(k) && isFinite(parseFloat(q.get(k)))) $(id).value = q.get(k);
});

document.querySelectorAll('#sizer-form input, #sizer-form select').forEach(el => el.addEventListener('input', update));
update();
