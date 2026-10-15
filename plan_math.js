// Position-sizing and allocation maths for the trade desk. Pure functions, no DOM: tested against risk.py (tests/test_plan_math.py).
// Risk limits come from the scan (risk_config) and can only be tightened here, never raised.
(function (root) {
    function sizeShares(capital, riskPct, entry, stopDist, maxPosPct) {
        if (!(capital > 0 && riskPct > 0 && entry > 0 && stopDist > 0)) return 0;
        let shares = Math.floor(capital * riskPct / 100 / stopDist);
        if (maxPosPct > 0 && shares * entry > capital * maxPosPct / 100) shares = Math.floor(capital * maxPosPct / 100 / entry);
        return Math.max(0, shares);
    }
    const TIER_MULT = {high: 1.0, medium: 0.75, low: 0.5};            // optional, only ever shrinks size
    function effectiveRisk(prefRisk, cfgRisk) {                       // the user's risk % may be lower than the audited limit, never higher
        const p = Number(prefRisk);
        return p > 0 ? Math.min(p, cfgRisk) : cfgRisk;
    }
    const LEVEL_ORDER = {high: 0, medium: 1, low: 2, avoid: 3};
    function rank(cands) {                                            // conviction level, then relative-strength rank
        return cands.slice().sort((a, b) =>
            (LEVEL_ORDER[a.level] - LEVEL_ORDER[b.level]) || ((b.rs ?? -1) - (a.rs ?? -1)) || String(a.symbol).localeCompare(b.symbol));
    }
    // cands: [{symbol, sector, level, rs, entry, stopDist, riskMult}] already filtered to tradeable ones.
    function autoSelect(cands, o) {
        const budget = o.capital * o.maxOpenRiskPct / 100;
        let risk = o.existingRisk || 0;
        const sectors = Object.assign({}, o.sectorCounts || {});
        const out = [];
        for (const c of rank(cands)) {
            if (c.level === 'avoid' || (o.held || []).includes(c.symbol)) continue;
            const sh = sizeShares(o.capital, o.riskPct * (c.riskMult ?? 1), c.entry, c.stopDist, o.maxPosPct);
            const r = sh * c.stopDist;
            if (sh < 1 || risk + r > budget * (1 + 1e-9)) continue;
            if ((sectors[c.sector] || 0) >= o.maxPerSector) continue;
            out.push(c.symbol); risk += r; sectors[c.sector] = (sectors[c.sector] || 0) + 1;
        }
        return out;
    }
    const api = {sizeShares, TIER_MULT, effectiveRisk, rank, autoSelect};
    if (typeof module !== 'undefined' && module.exports) module.exports = api; else root.PlanMath = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
