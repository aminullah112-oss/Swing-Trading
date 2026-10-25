# Benchmarks and pre-registered redesign tests

All series use the **same stock list and dates**, so survivorship flatters each equally. Absolute numbers are optimistic; comparisons are the point. Calmar = CAGR / |max drawdown|; Sharpe uses rf = 0. The strategy rows are a risk-sized portfolio (at most about three positions at 0.5% risk), so they are partly in cash: compare Calmar and Sharpe, not raw CAGR.

## Design period (before 2023-01-01)

| Series | CAGR | Max DD | Calmar | Sharpe |
|---|---|---|---|---|
| Live strategy (baseline) | 2.1% | -14.4% | 0.15 | 0.33 |
| H1 momentum-30 replica | 22.6% | -37.4% | 0.6 | 1.08 |
| Equal-weight universe | 21.3% | -38.0% | 0.56 | 1.18 |
| Nifty 50 | 12.6% | -38.4% | 0.33 | 0.76 |

## Hold-out (from 2023-01-01)

| Series | CAGR | Max DD | Calmar | Sharpe |
|---|---|---|---|---|
| Live strategy (baseline) | 6.0% | -15.7% | 0.38 | 0.72 |
| H1 momentum-30 replica | 22.7% | -23.0% | 0.99 | 1.3 |
| Equal-weight universe | 16.2% | -20.7% | 0.78 | 1.12 |
| Nifty 50 | 6.0% | -15.8% | 0.38 | 0.53 |

## Pre-registered hypotheses

Improvement needs (a) a higher Calmar than the baseline in both periods and (b) a hold-out daily-return difference whose month-clustered interval (Bonferroni, 2 hypotheses) excludes zero.

| Variant | Design CAGR / DD / Calmar | Hold-out CAGR / DD / Calmar | (a) Calmar up in both | Hold-out return diff vs baseline, %/day (CI) | (b) CI > 0 | Improves? |
|---|---|---|---|---|---|---|
| Baseline (live variant) | 2.1% / -14.4% / 0.15 | 6.0% / -15.7% / 0.38 | — | — | — | — |
| H2: admit by momentum rank | 2.8% / -17.5% / 0.16 | 6.1% / -15.5% / 0.39 | ✅ | -0.0396..+0.0342 | ❌ | ❌ |
| H3: half risk when Nifty < EMA200 | 2.2% / -13.7% / 0.16 | 3.6% / -11.5% / 0.32 | ❌ | -0.0322..+0.0136 | ❌ | ❌ |

**Does the live strategy beat the momentum-30 replica in the hold-out (by Calmar)?** No. Daily-return difference (strategy minus replica): -0.1282..+0.0013 %/day (month-clustered 95% CI).

## Calendar-year returns (%)

| Series | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Live strategy (baseline) |  | 0.1 | 7.9 | 0.9 | 2.0 | 1.0 | 0.1 | 24.6 | 10.5 | 1.3 | -7.6 |
| H1 momentum-30 replica |  |  | 0.6 | 11.6 | 29.7 | 73.1 | 4.2 | 62.4 | 38.3 | 9.5 | -11.5 |
| Equal-weight universe | -7.5 | 49.1 | -2.7 | 10.7 | 35.9 | 52.1 | 7.2 | 47.7 | 22.2 | 6.7 | -8.1 |
| Nifty 50 | -6.0 | 28.6 | 3.2 | 12.0 | 14.9 | 24.1 | 4.3 | 20.0 | 8.8 | 10.5 | -13.5 |

_Three hypotheses were tested, so a single "improves both" is weak evidence. Neither H2 nor H3 changes the live scanner; a winner would be a candidate for the forward test. Momentum replica: equal weight, top 30, March/September rebalance, 25 bps per side. First rebalance: 2018-04-02._