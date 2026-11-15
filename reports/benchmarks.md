# Benchmarks and pre-registered redesign tests

All series use the **same stock list and dates**, so survivorship flatters each equally. Absolute numbers are optimistic; comparisons are the point. Calmar = CAGR / |max drawdown|; Sharpe uses rf = 0. The strategy rows are a risk-sized portfolio (at most about three positions at 0.5% risk), so they are partly in cash: compare Calmar and Sharpe, not raw CAGR.

## Design period (before 2023-01-01)

| Series | CAGR | Max DD | Calmar | Sharpe |
|---|---|---|---|---|
| Live strategy (baseline) | 2.6% | -11.9% | 0.22 | 0.41 |
| H1 momentum-30 replica | 22.6% | -37.4% | 0.6 | 1.08 |
| Equal-weight universe | 23.5% | -38.0% | 0.62 | 1.29 |
| Nifty 50 | 14.0% | -38.4% | 0.36 | 0.83 |

## Hold-out (from 2023-01-01)

| Series | CAGR | Max DD | Calmar | Sharpe |
|---|---|---|---|---|
| Live strategy (baseline) | 7.5% | -14.8% | 0.51 | 0.88 |
| H1 momentum-30 replica | 25.2% | -23.0% | 1.1 | 1.42 |
| Equal-weight universe | 18.5% | -20.7% | 0.9 | 1.26 |
| Nifty 50 | 8.9% | -15.8% | 0.56 | 0.74 |

## Pre-registered hypotheses

Improvement needs (a) a higher Calmar than the baseline in both periods and (b) a hold-out daily-return difference whose month-clustered interval (Bonferroni, 2 hypotheses) excludes zero.

| Variant | Design CAGR / DD / Calmar | Hold-out CAGR / DD / Calmar | (a) Calmar up in both | Hold-out return diff vs baseline, %/day (CI) | (b) CI > 0 | Improves? |
|---|---|---|---|---|---|---|
| Baseline (live variant) | 2.6% / -11.9% / 0.22 | 7.5% / -14.8% / 0.51 | — | — | — | — |
| H2: admit by momentum rank | 5.6% / -9.8% / 0.57 | 7.2% / -10.9% / 0.66 | ✅ | -0.0385..+0.0318 | ❌ | ❌ |
| H3: half risk when Nifty < EMA200 | 2.1% / -12.4% / 0.17 | 4.5% / -7.9% / 0.57 | ❌ | -0.0381..+0.0160 | ❌ | ❌ |

**Does the live strategy beat the momentum-30 replica in the hold-out (by Calmar)?** No. Daily-return difference (strategy minus replica): -0.1324..+0.0001 %/day (month-clustered 95% CI).

## Calendar-year returns (%)

| Series | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Live strategy (baseline) |  | 1.5 | 1.3 | 5.5 | 5.0 | -2.0 | 3.2 | 20.7 | 3.9 | 0.0 | -1.4 |
| H1 momentum-30 replica |  |  | 0.6 | 11.6 | 29.7 | 73.1 | 4.2 | 62.4 | 38.3 | 9.5 | -3.2 |
| Equal-weight universe | 2.1 | 49.1 | -2.7 | 10.7 | 35.9 | 52.1 | 7.2 | 47.7 | 22.2 | 6.7 | 0.1 |
| Nifty 50 | 1.0 | 28.6 | 3.2 | 12.0 | 14.9 | 24.1 | 4.3 | 20.0 | 8.8 | 10.5 | -3.8 |

_Three hypotheses were tested, so a single "improves both" is weak evidence. Neither H2 nor H3 changes the live scanner; a winner would be a candidate for the forward test. Momentum replica: equal weight, top 30, March/September rebalance, 25 bps per side. First rebalance: 2018-04-02._