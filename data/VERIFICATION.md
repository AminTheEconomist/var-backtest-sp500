# S&P 500 daily close — verification report

Built by `data/verify_data.py` on 2026-09-16. Tolerance: 1 cent.

| Source | Days | First | Last |
|---|---|---|---|
| yahoo | 10,256 | 1985-01-02 | 2025-09-16 |
| fred | 2,512 | 2016-09-19 | 2026-09-16 |
| wsj | 10,507 | 1985-01-02 | 2026-09-16 |

## Pairwise agreement on overlapping days

| Pair | Overlapping days | Days differing > 1 cent | Largest difference |
|---|---|---|---|
| fred vs wsj | 2,512 | 0 | 0.00 |
| fred vs yahoo | 2,261 | 7 | 5.29 |
| wsj vs yahoo | 10,256 | 69 | 5.29 |

## Result

- Days in the final series: **10,507**, 1985-01-02 to 2026-09-16
- `agree_2`: 8,184
- `agree_3`: 2,254
- `majority_2of3`: 7
- `wsj_tiebreak`: 62
- Largest disagreement in relative terms: 1987-05-07, 0.18%

## Every day where the sources did not all agree

- 1986-03-12 (wsj_tiebreak): yahoo=232.54, wsj=232.51
- 1986-06-20 (wsj_tiebreak): yahoo=247.58, wsj=247.96
- 1987-05-07 (wsj_tiebreak): yahoo=294.71, wsj=294.17
- 1988-04-13 (wsj_tiebreak): yahoo=271.58, wsj=271.55
- 1988-04-25 (wsj_tiebreak): yahoo=262.51, wsj=262.46
- 1988-12-08 (wsj_tiebreak): yahoo=276.59, wsj=276.57
- 1989-06-13 (wsj_tiebreak): yahoo=323.91, wsj=323.41
- 1992-02-21 (wsj_tiebreak): yahoo=411.43, wsj=411.46
- 1992-04-20 (wsj_tiebreak): yahoo=410.18, wsj=410.16
- 1993-07-09 (wsj_tiebreak): yahoo=448.11, wsj=448.13
- 1994-09-07 (wsj_tiebreak): yahoo=470.99, wsj=470.96
- 1994-09-30 (wsj_tiebreak): yahoo=462.71, wsj=462.69
- 1994-10-13 (wsj_tiebreak): yahoo=467.79, wsj=467.77
- 1994-11-16 (wsj_tiebreak): yahoo=465.62, wsj=465.6
- 1995-02-21 (wsj_tiebreak): yahoo=482.72, wsj=482.74
- 1996-09-30 (wsj_tiebreak): yahoo=687.33, wsj=687.31
- 1996-12-09 (wsj_tiebreak): yahoo=749.76, wsj=749.81
- 1996-12-12 (wsj_tiebreak): yahoo=729.3, wsj=729.33
- 1997-02-25 (wsj_tiebreak): yahoo=812.03, wsj=812.1
- 1997-05-05 (wsj_tiebreak): yahoo=830.29, wsj=830.24
- 1997-06-12 (wsj_tiebreak): yahoo=883.46, wsj=883.48
- 1997-07-31 (wsj_tiebreak): yahoo=954.31, wsj=954.29
- 1997-10-16 (wsj_tiebreak): yahoo=955.25, wsj=955.23
- 1998-03-30 (wsj_tiebreak): yahoo=1093.6, wsj=1093.55
- 2000-11-29 (wsj_tiebreak): yahoo=1341.93, wsj=1341.91
- 2000-12-22 (wsj_tiebreak): yahoo=1305.95, wsj=1305.97
- 2001-01-12 (wsj_tiebreak): yahoo=1318.55, wsj=1318.32
- 2001-06-29 (wsj_tiebreak): yahoo=1224.38, wsj=1224.42
- 2001-08-29 (wsj_tiebreak): yahoo=1148.56, wsj=1148.6
- 2002-07-16 (wsj_tiebreak): yahoo=900.94, wsj=901.05
- 2002-08-19 (wsj_tiebreak): yahoo=950.7, wsj=950.72
- 2003-07-16 (wsj_tiebreak): yahoo=994.09, wsj=994.0
- 2003-11-12 (wsj_tiebreak): yahoo=1058.53, wsj=1058.56
- 2004-11-02 (wsj_tiebreak): yahoo=1130.56, wsj=1130.54
- 2004-12-17 (wsj_tiebreak): yahoo=1194.2, wsj=1194.22
- 2005-04-26 (wsj_tiebreak): yahoo=1151.83, wsj=1151.74
- 2005-06-01 (wsj_tiebreak): yahoo=1202.22, wsj=1202.27
- 2005-08-23 (wsj_tiebreak): yahoo=1217.59, wsj=1217.57
- 2005-08-25 (wsj_tiebreak): yahoo=1212.37, wsj=1212.39
- 2006-03-10 (wsj_tiebreak): yahoo=1281.42, wsj=1281.58
- 2006-03-31 (wsj_tiebreak): yahoo=1294.87, wsj=1294.83
- 2006-04-10 (wsj_tiebreak): yahoo=1296.62, wsj=1296.6
- 2006-04-18 (wsj_tiebreak): yahoo=1307.28, wsj=1307.65
- 2006-05-03 (wsj_tiebreak): yahoo=1308.12, wsj=1307.85
- 2006-05-30 (wsj_tiebreak): yahoo=1259.87, wsj=1259.84
- 2006-06-12 (wsj_tiebreak): yahoo=1237.44, wsj=1236.4
- 2006-07-11 (wsj_tiebreak): yahoo=1272.43, wsj=1272.52
- 2006-08-02 (wsj_tiebreak): yahoo=1277.41, wsj=1278.55
- 2006-08-30 (wsj_tiebreak): yahoo=1305.37, wsj=1304.27
- 2006-09-12 (wsj_tiebreak): yahoo=1313.0, wsj=1313.11
- 2006-09-15 (wsj_tiebreak): yahoo=1319.66, wsj=1319.87
- 2006-09-19 (wsj_tiebreak): yahoo=1317.64, wsj=1318.31
- 2006-09-28 (wsj_tiebreak): yahoo=1338.88, wsj=1339.15
- 2006-10-04 (wsj_tiebreak): yahoo=1350.2, wsj=1350.22
- 2006-10-18 (wsj_tiebreak): yahoo=1365.8, wsj=1365.96
- 2006-11-27 (wsj_tiebreak): yahoo=1381.96, wsj=1381.9
- 2007-04-16 (wsj_tiebreak): yahoo=1468.33, wsj=1468.47
- 2007-12-27 (wsj_tiebreak): yahoo=1476.27, wsj=1476.37
- 2008-09-26 (wsj_tiebreak): yahoo=1213.27, wsj=1213.01
- 2008-09-29 (wsj_tiebreak): yahoo=1106.42, wsj=1106.39
- 2010-05-05 (wsj_tiebreak): yahoo=1165.87, wsj=1165.9
- 2012-08-01 (wsj_tiebreak): yahoo=1375.32, wsj=1375.14
- 2018-11-29 (majority_2of3): yahoo=2737.8, fred=2737.76, wsj=2737.76
- 2019-08-12 (majority_2of3): yahoo=2882.7, fred=2883.75, wsj=2883.75
- 2020-05-11 (majority_2of3): yahoo=2930.19, fred=2930.32, wsj=2930.32
- 2020-10-02 (majority_2of3): yahoo=3348.42, fred=3348.44, wsj=3348.44
- 2020-10-05 (majority_2of3): yahoo=3408.6, fred=3408.63, wsj=3408.63
- 2020-10-06 (majority_2of3): yahoo=3360.97, fred=3360.95, wsj=3360.95
- 2021-08-11 (majority_2of3): yahoo=4442.41, fred=4447.7, wsj=4447.7

## Spot checks

- 1987-10-16: yahoo=282.7, fred=None, wsj=282.7
- 1987-10-19: yahoo=224.84, fred=None, wsj=224.84
- 2008-09-29: yahoo=1106.42, fred=None, wsj=1106.39
- 2008-10-15: yahoo=907.84, fred=None, wsj=907.84
- 2020-03-16: yahoo=2386.13, fred=2386.13, wsj=2386.13
- 2025-09-16: yahoo=6606.76, fred=6606.76, wsj=6606.76
- 2026-09-16: yahoo=None, fred=7551.81, wsj=7551.81
