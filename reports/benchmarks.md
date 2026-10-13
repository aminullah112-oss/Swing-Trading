# Benchmarks and pre-registered redesign tests

All series use the **same stock list and dates**, so survivorship flatters each equally. Absolute numbers are optimistic; comparisons are the point. Calmar = CAGR / |max drawdown|; Sharpe uses rf = 0. The strategy rows are a risk-sized portfolio (at most about three positions at 0.5% risk), so they are partly in cash: compare Calmar and Sharpe, not raw CAGR.

## Design period (before 2023-01-01)

| Series | CAGR | Max DD | Calmar | Sharpe |
|---|---|---|---|---|
| Live strategy (baseline) | 5.7% | -8.5% | 0.67 | 0.85 |
| H1 momentum-30 replica | 22.6% | -37.4% | 0.6 | 1.08 |
| Equal-weight universe | 21.5% | -38.0% | 0.57 | 1.2 |
| Nifty 50 | 12.8% | -38.4% | 0.33 | 0.77 |

## Hold-out (from 2023-01-01)

| Series | CAGR | Max DD | Calmar | Sharpe |
|---|---|---|---|---|
| Live strategy (baseline) | 6.6% | -15.7% | 0.42 | 0.79 |
| H1 momentum-30 replica | 24.1% | -23.0% | 1.05 | 1.36 |
| Equal-weight universe | 17.1% | -20.7% | 0.83 | 1.17 |
| Nifty 50 | 5.8% | -15.8% | 0.36 | 0.52 |

## Pre-registered hypotheses

Improvement needs (a) a higher Calmar than the baseline in both periods and (b) a hold-out daily-return difference whose month-clustered interval (Bonferroni, 2 hypotheses) excludes zero.

| Variant | Design CAGR / DD / Calmar | Hold-out CAGR / DD / Calmar | (a) Calmar up in both | Hold-out return diff vs baseline, %/day (CI) | (b) CI > 0 | Improves? |
|---|---|---|---|---|---|---|
| Baseline (live variant) | 5.7% / -8.5% / 0.67 | 6.6% / -15.7% / 0.42 | — | — | — | — |
| H2: admit by momentum rank | 3.1% / -14.8% / 0.21 | 6.5% / -15.5% / 0.42 | ❌ | -0.0407..+0.0341 | ❌ | ❌ |
| H3: half risk when Nifty < EMA200 | 0.5% / -16.9% / 0.03 | 3.3% / -11.6% / 0.29 | ❌ | -0.0354..+0.0099 | ❌ | ❌ |

**Does the live strategy beat the momentum-30 replica in the hold-out (by Calmar)?** No. Daily-return difference (strategy minus replica): -0.1293..-0.0018 %/day (month-clustered 95% CI).

## Calendar-year returns (%)

| Series | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Live strategy (baseline) |  | 2.9 | 6.0 | 8.6 | 7.0 | 2.2 | 4.3 | 24.6 | 9.1 | 2.0 | -7.0 |
| H1 momentum-30 replica |  |  | 0.6 | 11.6 | 29.7 | 73.1 | 4.2 | 62.4 | 38.3 | 9.5 | -8.1 |
| Equal-weight universe | -5.8 | 49.1 | -2.7 | 10.7 | 35.9 | 52.1 | 7.2 | 47.7 | 22.2 | 6.7 | -5.8 |
| Nifty 50 | -4.5 | 28.6 | 3.2 | 12.0 | 14.9 | 24.1 | 4.3 | 20.0 | 8.8 | 10.5 | -14.4 |

_Three hypotheses were tested, so a single "improves both" is weak evidence. Neither H2 nor H3 changes the live scanner; a winner would be a candidate for the forward test. Momentum replica: equal weight, top 30, March/September rebalance, 25 bps per side. First rebalance: 2018-04-02._