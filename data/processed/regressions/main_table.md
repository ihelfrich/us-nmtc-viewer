# Main regression results — Helfrich (2026), NMTC working paper

_Outcome variable: `leverage_win` (project-level total cost / QLICI, winsorized [1, 20])._  
_All specifications include the rural indicator $R_i = 1$ if non-metro._  
_M0–M4 are OLS; M4-Q is quantile regression at the median; M5 is OLS with the rural × QALICB-type interaction._  
_M3 standard errors are HC1; M4–M5 standard errors are clustered at the CDE level._  
_Stars: \*\*\* p<0.01, \*\* p<0.05, \* p<0.10._

| | M0 | M1 | M2 | M3 | M4 | M4-Q | M5 |
|---|---:|---:|---:|---:|---:|---:|---:|
| **rural** ($\hat\beta$) | -0.262*** | -0.249*** | -0.186*** | -0.172** | -0.047 | -0.001 | 0.091 |
| _(standard error)_ | (0.060) | (0.061) | (0.061) | (0.067) | (0.101) | (0.008) | (0.621) |
| year FE | — | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| QALICB-type FE | — | — | ✓ | ✓ | ✓ | ✓ | ✓ |
| state FE | — | — | — | ✓ | — | — | — |
| CDE FE | — | — | — | — | ✓ | ✓ | ✓ |
| $R^2$ | 0.002 | 0.015 | 0.022 | 0.039 | 0.131 | nan | 0.132 |
| N | 8,024 | 8,024 | 8,024 | 8,024 | 8,024 | 8,024 | 8,024 |

### M5 — rural × QALICB-type interaction (full breakdown)

| term | $\hat\beta$ | (SE) | p |
|---|---:|---:|---:|
| `rural` | 0.091 | (0.621) | 0.883 |
| `rural:C(qalicb_type)[T.NRE]` | -0.085 | (0.647) | 0.895 |
| `rural:C(qalicb_type)[T.RE]` | -0.397 | (0.648) | 0.540 |
| `rural:C(qalicb_type)[T.SPE]` | -0.046 | (0.642) | 0.943 |
