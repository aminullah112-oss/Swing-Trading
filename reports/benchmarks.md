# Benchmarks and pre-registered redesign tests

All series use the **same stock list and dates**, so survivorship flatters each equally. Absolute numbers are optimistic; comparisons are the point. Calmar = CAGR / |max drawdown|; Sharpe uses rf = 0. The strategy rows are a risk-sized portfolio (at most about three positions at 0.5% risk), so they are partly in cash: compare Calmar and Sharpe, not raw CAGR.

## Design period (before 2023-01-01)

| Series | CAGR | Max DD | Calmar | Sharpe |
|---|---|---|---|---|
| Live strategy (baseline) | 1.9% | -16.2% | 0.12 | 0.3 |
| H1 momentum-30 replica | 22.6% | -37.4% | 0.6 | 1.08 |
| Equal-weight universe | 24.0% | -38.0% | 0.63 | 1.31 |
| Nifty 50 | 14.5% | -38.4% | 0.38 | 0.85 |

## Hold-out (from 2023-01-01)

| Series | CAGR | Max DD | Calmar | Sharpe |
|---|---|---|---|---|
| Live strategy (baseline) | 7.1% | -14.8% | 0.48 | 0.84 |
| H1 momentum-30 replica | 25.2% | -23.0% | 1.1 | 1.42 |
| Equal-weight universe | 18.7% | -20.7% | 0.9 | 1.27 |
| Nifty 50 | 9.6% | -15.8% | 0.61 | 0.79 |

## Pre-registered hypotheses

Improvement needs (a) a higher Calmar than the baseline in both periods and (b) a hold-out daily-return difference whose month-clustered interval (Bonferroni, 2 hypotheses) excludes zero.

| Variant | Design CAGR / DD / Calmar | Hold-out CAGR / DD / Calmar | (a) Calmar up in both | Hold-out return diff vs baseline, %/day (CI) | (b) CI > 0 | Improves? |
|---|---|---|---|---|---|---|
| Baseline (live variant) | 1.9% / -16.2% / 0.12 | 7.1% / -14.8% / 0.48 | — | — | — | — |
| H2: admit by momentum rank | 1.5% / -20.9% / 0.07 | 6.8% / -10.9% / 0.62 | ❌ | -0.0383..+0.0314 | ❌ | ❌ |
| H3: half risk when Nifty < EMA200 | 1.5% / -12.2% / 0.12 | 4.7% / -7.9% / 0.59 | ❌ | -0.0378..+0.0190 | ❌ | ❌ |

**Does the live strategy beat the momentum-30 replica in the hold-out (by Calmar)?** No. Daily-return difference (strategy minus replica): -0.1338..-0.0009 %/day (month-clustered 95% CI).

## Calendar-year returns (%)

| Series | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Live strategy (baseline) |  | 2.0 | 3.4 | -0.6 | 1.7 | 1.7 | 2.5 | 25.2 | 9.1 | -0.2 | -2.1 |
| H1 momentum-30 replica |  |  | 0.6 | 11.6 | 29.7 | 73.1 | 4.2 | 62.4 | 38.3 | 9.5 | -2.6 |
| Equal-weight universe | 4.2 | 49.1 | -2.7 | 10.7 | 35.9 | 52.1 | 7.2 | 47.7 | 22.2 | 6.7 | 1.1 |
| Nifty 50 | 3.2 | 28.6 | 3.2 | 12.0 | 14.9 | 24.1 | 4.3 | 20.0 | 8.8 | 10.5 | -1.3 |

_Three hypotheses were tested, so a single "improves both" is weak evidence. Neither H2 nor H3 changes the live scanner; a winner would be a candidate for the forward test. Momentum replica: equal weight, top 30, March/September rebalance, 25 bps per side. First rebalance: 2018-04-02._