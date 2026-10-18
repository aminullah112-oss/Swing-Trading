# Benchmarks and pre-registered redesign tests

All series use the **same stock list and dates**, so survivorship flatters each equally. Absolute numbers are optimistic; comparisons are the point. Calmar = CAGR / |max drawdown|; Sharpe uses rf = 0. The strategy rows are a risk-sized portfolio (at most about three positions at 0.5% risk), so they are partly in cash: compare Calmar and Sharpe, not raw CAGR.

## Design period (before 2023-01-01)

| Series | CAGR | Max DD | Calmar | Sharpe |
|---|---|---|---|---|
| Live strategy (baseline) | 1.9% | -13.4% | 0.14 | 0.31 |
| H1 momentum-30 replica | 22.4% | -37.4% | 0.6 | 1.08 |
| Equal-weight universe | 21.6% | -37.9% | 0.57 | 1.2 |
| Nifty 50 | 12.9% | -38.4% | 0.34 | 0.78 |

## Hold-out (from 2023-01-01)

| Series | CAGR | Max DD | Calmar | Sharpe |
|---|---|---|---|---|
| Live strategy (baseline) | 7.2% | -14.8% | 0.49 | 0.88 |
| H1 momentum-30 replica | 24.1% | -23.0% | 1.05 | 1.36 |
| Equal-weight universe | 17.6% | -20.7% | 0.85 | 1.2 |
| Nifty 50 | 6.7% | -15.8% | 0.43 | 0.59 |

## Pre-registered hypotheses

Improvement needs (a) a higher Calmar than the baseline in both periods and (b) a hold-out daily-return difference whose month-clustered interval (Bonferroni, 2 hypotheses) excludes zero.

| Variant | Design CAGR / DD / Calmar | Hold-out CAGR / DD / Calmar | (a) Calmar up in both | Hold-out return diff vs baseline, %/day (CI) | (b) CI > 0 | Improves? |
|---|---|---|---|---|---|---|
| Baseline (live variant) | 1.9% / -13.4% / 0.14 | 7.2% / -14.8% / 0.49 | — | — | — | — |
| H2: admit by momentum rank | 4.2% / -17.1% / 0.25 | 6.1% / -15.5% / 0.4 | ❌ | -0.0486..+0.0353 | ❌ | ❌ |
| H3: half risk when Nifty < EMA200 | 2.8% / -12.6% / 0.22 | 3.6% / -12.6% / 0.28 | ❌ | -0.0412..+0.0123 | ❌ | ❌ |

**Does the live strategy beat the momentum-30 replica in the hold-out (by Calmar)?** No. Daily-return difference (strategy minus replica): -0.1245..-0.0023 %/day (month-clustered 95% CI).

## Calendar-year returns (%)

| Series | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Live strategy (baseline) |  | -0.5 | -0.6 | 4.8 | 10.1 | 0.7 | -3.2 | 24.6 | 8.3 | -0.3 | -1.1 |
| H1 momentum-30 replica |  |  | 0.6 | 11.6 | 29.7 | 72.6 | 3.7 | 62.4 | 38.3 | 9.5 | -8.1 |
| Equal-weight universe | -5.5 | 48.9 | -2.7 | 10.8 | 36.0 | 51.8 | 7.2 | 47.8 | 22.4 | 6.4 | -4.2 |
| Nifty 50 | -3.9 | 28.6 | 3.2 | 12.0 | 14.9 | 24.1 | 4.3 | 20.0 | 8.8 | 10.5 | -11.4 |

_Three hypotheses were tested, so a single "improves both" is weak evidence. Neither H2 nor H3 changes the live scanner; a winner would be a candidate for the forward test. Momentum replica: equal weight, top 30, March/September rebalance, 25 bps per side. First rebalance: 2018-04-02._