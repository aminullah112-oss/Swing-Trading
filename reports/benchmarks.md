# Benchmarks and pre-registered redesign tests

All series use the **same stock list and dates**, so survivorship flatters each equally. Absolute numbers are optimistic; comparisons are the point. Calmar = CAGR / |max drawdown|; Sharpe uses rf = 0. The strategy rows are a risk-sized portfolio (at most about three positions at 0.5% risk), so they are partly in cash: compare Calmar and Sharpe, not raw CAGR.

## Design period (before 2023-01-01)

| Series | CAGR | Max DD | Calmar | Sharpe |
|---|---|---|---|---|
| Live strategy (baseline) | 4.2% | -16.1% | 0.26 | 0.63 |
| H1 momentum-30 replica | 22.6% | -37.4% | 0.6 | 1.08 |
| Equal-weight universe | 22.1% | -38.0% | 0.58 | 1.22 |
| Nifty 50 | 13.1% | -38.4% | 0.34 | 0.79 |

## Hold-out (from 2023-01-01)

| Series | CAGR | Max DD | Calmar | Sharpe |
|---|---|---|---|---|
| Live strategy (baseline) | 7.4% | -15.7% | 0.47 | 0.87 |
| H1 momentum-30 replica | 25.1% | -23.0% | 1.09 | 1.41 |
| Equal-weight universe | 18.4% | -20.7% | 0.89 | 1.25 |
| Nifty 50 | 8.8% | -15.8% | 0.56 | 0.74 |

## Pre-registered hypotheses

Improvement needs (a) a higher Calmar than the baseline in both periods and (b) a hold-out daily-return difference whose month-clustered interval (Bonferroni, 2 hypotheses) excludes zero.

| Variant | Design CAGR / DD / Calmar | Hold-out CAGR / DD / Calmar | (a) Calmar up in both | Hold-out return diff vs baseline, %/day (CI) | (b) CI > 0 | Improves? |
|---|---|---|---|---|---|---|
| Baseline (live variant) | 4.2% / -16.1% / 0.26 | 7.4% / -15.7% / 0.47 | — | — | — | — |
| H2: admit by momentum rank | 6.1% / -11.2% / 0.55 | 5.5% / -12.0% / 0.46 | ❌ | -0.0435..+0.0247 | ❌ | ❌ |
| H3: half risk when Nifty < EMA200 | 4.0% / -9.1% / 0.44 | 3.6% / -11.5% / 0.32 | ❌ | -0.0401..+0.0117 | ❌ | ❌ |

**Does the live strategy beat the momentum-30 replica in the hold-out (by Calmar)?** No. Daily-return difference (strategy minus replica): -0.1318..-0.0003 %/day (month-clustered 95% CI).

## Calendar-year returns (%)

| Series | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Live strategy (baseline) |  | 5.0 | 2.0 | 8.1 | 13.2 | 0.4 | -5.4 | 19.6 | 4.0 | 1.3 | -6.1 |
| H1 momentum-30 replica |  |  | 0.6 | 11.6 | 29.7 | 73.1 | 4.2 | 62.4 | 38.3 | 9.5 | -3.9 |
| Equal-weight universe | -4.3 | 49.1 | -2.7 | 10.7 | 35.9 | 52.1 | 7.2 | 47.7 | 22.2 | 6.7 | -0.7 |
| Nifty 50 | -3.7 | 28.6 | 3.2 | 12.0 | 14.9 | 24.1 | 4.3 | 20.0 | 8.8 | 10.5 | -4.2 |

_Three hypotheses were tested, so a single "improves both" is weak evidence. Neither H2 nor H3 changes the live scanner; a winner would be a candidate for the forward test. Momentum replica: equal weight, top 30, March/September rebalance, 25 bps per side. First rebalance: 2018-04-02._