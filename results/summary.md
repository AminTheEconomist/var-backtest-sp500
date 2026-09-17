# VaR backtest — S&P 500

- Forecast days: **10,255** (1986-01-02 to 2026-09-16)
- One-day VaR at 99%, rolling 250-day window, no look-ahead
- Expected breaches at 1%: **102.6**

| Model | Breaches | Breach rate | Kupiec p-value | Clustering p-value |
|---|---|---|---|---|
| historical | 167 | 1.63% | 0.0000 | 0.0000 |
| parametric | 224 | 2.18% | 0.0000 | 0.0000 |
| monte_carlo | 154 | 1.50% | 0.0000 | 0.0000 |

## Worst years (historical-simulation breaches)

| Year | Trading days | Historical | Parametric | Monte Carlo (t) |
|---|---|---|---|---|
| 2008 | 253 | 13 (red) | 21 (red) | 13 (red) |
| 2007 | 251 | 10 (red) | 15 (red) | 12 (red) |
| 2022 | 251 | 10 (red) | 15 (red) | 10 (red) |
| 1986 | 253 | 9 (yellow) | 8 (yellow) | 6 (yellow) |
| 2020 | 253 | 8 (yellow) | 13 (red) | 12 (red) |
| 1996 | 254 | 7 (yellow) | 10 (red) | 6 (yellow) |
| 1997 | 253 | 7 (yellow) | 7 (yellow) | 5 (yellow) |
| 1994 | 252 | 7 (yellow) | 9 (yellow) | 8 (yellow) |

## Black Monday, 19 October 1987

- Actual one-day loss: **20.47%** ($204,669 on $1,000,000)
- historical VaR that morning: 2.67% ($26,728); the loss was **7.7x** the forecast
- parametric VaR that morning: 2.45% ($24,521); the loss was **8.3x** the forecast
- monte_carlo VaR that morning: 2.74% ($27,422); the loss was **7.5x** the forecast
- In standard deviations of the prior 250 days: **19.4**
