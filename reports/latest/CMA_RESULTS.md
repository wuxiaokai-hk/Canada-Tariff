# How the tariffs hit exports from each Ontario CMA (built from HTS10 lines)

Method: each HTS10 line's tariff change -> the NAICS industry that makes it (HS6-NAICS concordance) -> each CMA's share of national employment in that industry (2021 Census). Export response uses a trade elasticity of 2.0 on the tariff-inclusive price; banned lines lose 100%. Scenarios are cumulative (A includes today, B includes A, ...).

## CMA results, ranked by export loss in Scenario C

| CMA | Exports to U.S. 2025 | Rate 2025 | Rate today | Rate A | Rate B | Rate C | Export loss today | Export loss C | Mfg jobs at risk today | Mfg jobs at risk C | Jobs at risk C, % of employment |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Guelph | US$3.12bn | 5.4% | 8.5% | 11.2% | 22.4% | 22.6% | 3.5% | 20.5% | 369 | 1,552 | 1.88% |
| Windsor | US$7.25bn | 6.8% | 8.7% | 14.2% | 19.8% | 20.0% | 2.2% | 17.2% | 524 | 2,474 | 1.44% |
| Barrie | US$2.87bn | 6.9% | 9.4% | 15.9% | 19.0% | 19.3% | 2.9% | 16.7% | 287 | 906 | 0.89% |
| Kitchener-Cambridge-Waterloo | US$9.51bn | 6.1% | 9.2% | 13.9% | 18.8% | 19.1% | 3.5% | 16.6% | 1,144 | 3,395 | 1.22% |
| Belleville-Quinte West | US$1.01bn | 2.8% | 8.0% | 8.4% | 15.3% | 15.4% | 5.8% | 14.3% | 163 | 379 | 0.81% |
| London | US$5.38bn | 4.6% | 7.1% | 9.7% | 16.0% | 16.2% | 3.0% | 14.3% | 542 | 1,815 | 0.75% |
| Toronto | US$39.60bn | 4.3% | 8.9% | 11.0% | 14.7% | 15.0% | 5.2% | 12.9% | 8,161 | 14,298 | 0.49% |
| Oshawa | US$2.65bn | 5.9% | 9.9% | 13.3% | 15.5% | 15.9% | 4.5% | 12.8% | 429 | 797 | 0.43% |
| Ontario | US$117.60bn | 4.9% | 8.4% | 11.1% | 14.8% | 15.2% | 4.0% | 12.8% | 17,389 | 37,179 | 0.57% |
| Brantford | US$2.35bn | 5.3% | 8.2% | 11.9% | 13.9% | 14.4% | 3.2% | 11.8% | 295 | 631 | 0.97% |
| Ottawa-Gatineau (Ont. part) | US$2.53bn | 3.5% | 11.1% | 12.3% | 12.5% | 12.9% | 8.6% | 11.2% | 892 | 1,005 | 0.18% |
| Hamilton | US$7.45bn | 6.3% | 9.5% | 11.6% | 14.3% | 15.1% | 3.6% | 10.9% | 962 | 2,003 | 0.56% |
| St. Catharines-Niagara | US$3.81bn | 5.4% | 8.4% | 11.5% | 13.0% | 13.5% | 3.6% | 10.8% | 467 | 907 | 0.51% |
| Ontario, outside CMAs | US$26.20bn | 4.4% | 7.1% | 9.5% | 12.5% | 12.9% | 3.1% | 10.6% | 2,819 | 6,577 | 0.62% |
| Peterborough | US$0.62bn | 2.8% | 7.9% | 8.8% | 10.0% | 10.4% | 6.1% | 9.2% | 143 | 186 | 0.34% |
| Kingston | US$1.25bn | 3.9% | 6.3% | 6.5% | 6.9% | 7.0% | 2.7% | 3.7% | 95 | 121 | 0.16% |
| Thunder Bay | US$0.40bn | 1.3% | 3.4% | 3.7% | 3.9% | 4.1% | 2.4% | 3.4% | 28 | 37 | 0.07% |
| Greater Sudbury | US$1.60bn | 1.1% | 2.2% | 2.3% | 2.5% | 2.7% | 1.3% | 1.9% | 70 | 95 | 0.12% |

Rates are value-weighted realized tariff rates on each CMA's exports to the U.S. (2025 realized duty + new tariffs). Export loss is % of the CMA's 2025 exports to the U.S. Jobs at risk = employment x export intensity x export loss, manufacturing only.

## What drives each CMA's loss (Scenario C)

- **Guelph**: industries 3363 Motor Vehicle Parts Manufacturing (62%); 3361 Motor Vehicle Manufacturing (21%); 3353 Electrical Equipment Manufacturing (3%). Top HTS lines: 8708295160 (23%); 8708998180 (10%); 8703230140 (7%).
- **Windsor**: industries 3361 Motor Vehicle Manufacturing (49%); 3363 Motor Vehicle Parts Manufacturing (38%); 3261 Plastics Product Manufacturing (2%). Top HTS lines: 8703230140 (17%); 8708295160 (14%); 8703400020 (7%).
- **Barrie**: industries 3361 Motor Vehicle Manufacturing (60%); 3363 Motor Vehicle Parts Manufacturing (21%); 3261 Plastics Product Manufacturing (3%). Top HTS lines: 8703230140 (21%); 8703400020 (9%); 8708295160 (8%).
- **Kitchener-Cambridge-Waterloo**: industries 3361 Motor Vehicle Manufacturing (44%); 3363 Motor Vehicle Parts Manufacturing (34%); 3169 Other Leather and Allied Product Manufacturing (3%). Top HTS lines: 8703230140 (16%); 8708295160 (13%); 8703400020 (7%).
- **Belleville-Quinte West**: industries 3363 Motor Vehicle Parts Manufacturing (55%); 3222 Converted Paper Product Manufacturing (17%); 3361 Motor Vehicle Manufacturing (5%). Top HTS lines: 8708295160 (21%); 8708998180 (9%); 8708407580 (5%).
- **London**: industries 3363 Motor Vehicle Parts Manufacturing (50%); 3361 Motor Vehicle Manufacturing (28%); 3222 Converted Paper Product Manufacturing (3%). Top HTS lines: 8708295160 (19%); 8703230140 (10%); 8708998180 (8%).
- **Toronto**: industries 3363 Motor Vehicle Parts Manufacturing (32%); 3361 Motor Vehicle Manufacturing (25%); 3261 Plastics Product Manufacturing (4%). Top HTS lines: 8708295160 (12%); 8703230140 (9%); 8708998180 (5%).
- **Oshawa**: industries 3361 Motor Vehicle Manufacturing (42%); 3363 Motor Vehicle Parts Manufacturing (20%); 3222 Converted Paper Product Manufacturing (8%). Top HTS lines: 8703230140 (15%); 8708295160 (7%); 8703400020 (6%).
- **Ontario**: industries 3361 Motor Vehicle Manufacturing (33%); 3363 Motor Vehicle Parts Manufacturing (33%); 3222 Converted Paper Product Manufacturing (3%). Top HTS lines: 8708295160 (12%); 8703230140 (12%); 8708998180 (5%).
- **Brantford**: industries 3361 Motor Vehicle Manufacturing (49%); 3363 Motor Vehicle Parts Manufacturing (20%); 3399 Other Miscellaneous Manufacturing (4%). Top HTS lines: 8703230140 (17%); 8708295160 (7%); 8703400020 (7%).
- **Ottawa-Gatineau (Ont. part)**: industries 3342 Communications Equipment Manufacturing (21%); 3361 Motor Vehicle Manufacturing (18%); 3344 Semiconductor and Other Electronic Component Manufacturing (8%). Top HTS lines: 8517620090 (12%); 8703230140 (6%); 8526100040 (3%).
- **Hamilton**: industries 3361 Motor Vehicle Manufacturing (30%); 3363 Motor Vehicle Parts Manufacturing (28%); 3311 Iron and Steel Mills and Ferroalloy Manufacturing (8%). Top HTS lines: 8708295160 (11%); 8703230140 (11%); 8708998180 (5%).
- **St. Catharines-Niagara**: industries 3361 Motor Vehicle Manufacturing (45%); 3363 Motor Vehicle Parts Manufacturing (15%); 3121 Beverage Manufacturing (7%). Top HTS lines: 8703230140 (16%); 8703400020 (7%); 8703240150 (6%).
- **Ontario, outside CMAs**: industries 3361 Motor Vehicle Manufacturing (35%); 3363 Motor Vehicle Parts Manufacturing (32%); 3222 Converted Paper Product Manufacturing (3%). Top HTS lines: 8703230140 (12%); 8708295160 (12%); 8708998180 (5%).
- **Peterborough**: industries 3363 Motor Vehicle Parts Manufacturing (15%); 3361 Motor Vehicle Manufacturing (15%); 3121 Beverage Manufacturing (10%). Top HTS lines: 8708295160 (6%); 8703230140 (5%); 2208700030 (5%).
- **Kingston**: industries 3252 Resin, Synthetic Rubber, and Artificial Synthetic Fibers and Filaments Manufacturing (14%); 3363 Motor Vehicle Parts Manufacturing (11%); 3361 Motor Vehicle Manufacturing (10%). Top HTS lines: 3907995050 (14%); 8708295160 (4%); 7604291010 (4%).
- **Thunder Bay**: industries 3221 Pulp, Paper, and Paperboard Mills (18%); 3361 Motor Vehicle Manufacturing (14%); 3112 Grain and Oilseed Milling (10%). Top HTS lines: 4810921225 (10%); 1518004000 (7%); 8703230140 (5%).
- **Greater Sudbury**: industries 3363 Motor Vehicle Parts Manufacturing (11%); 3342 Communications Equipment Manufacturing (10%); 3314 Nonferrous Metal (except Aluminum) Production and Processing (9%). Top HTS lines: 7106921000 (9%); 8517620090 (4%); 8708295160 (4%).

## Industries (NAICS 4-digit) hit hardest

| NAICS | Industry | U.S. imports 2025 | Rate 2025 | Rate today | Rate C | Export loss C | Ontario share of Canadian jobs |
|---|---|---|---|---|---|---|---|
| 3361 | Motor Vehicle Manufacturing | US$32.82bn | 9.85% | 9.86% | 21.60% | 18.2% | 83% |
| 3363 | Motor Vehicle Parts Manufacturing | US$14.99bn | 5.81% | 6.52% | 38.98% | 37.1% | 89% |
| 3399 | Other Miscellaneous Manufacturing | US$3.16bn | 2.04% | 29.50% | 31.12% | 32.4% | 39% |
| 3261 | Plastics Product Manufacturing | US$6.01bn | 0.49% | 14.14% | 14.14% | 15.1% | 48% |
| 3222 | Converted Paper Product Manufacturing | US$4.64bn | 0.36% | 17.13% | 17.13% | 18.6% | 52% |
| 3121 | Beverage Manufacturing | US$1.46bn | 0.28% | 29.29% | 29.29% | 57.8% | 39% |
| 3371 | Household and Institutional Furniture and Kitchen Cabinet Manufacturing | US$1.63bn | 1.94% | 32.56% | 32.56% | 33.7% | 32% |
| 3353 | Electrical Equipment Manufacturing | US$4.43bn | 3.57% | 14.55% | 14.55% | 11.9% | 42% |
| 3323 | Architectural and Structural Metals Manufacturing | US$1.47bn | 11.99% | 34.27% | 50.76% | 35.7% | 36% |
| 3339 | Other General Purpose Machinery Manufacturing | US$6.36bn | 3.03% | 10.16% | 10.16% | 7.9% | 49% |
| 3342 | Communications Equipment Manufacturing | US$1.31bn | 4.44% | 37.54% | 37.54% | 35.8% | 54% |
| 3351 | Electric Lighting Equipment Manufacturing | US$0.90bn | 2.79% | 45.44% | 46.50% | 48.3% | 28% |
| 3212 | Veneer, Plywood, and Engineered Wood Product Manufacturing | US$3.18bn | 0.06% | 12.02% | 12.02% | 13.3% | 20% |
| 3344 | Semiconductor and Other Electronic Component Manufacturing | US$2.23bn | 4.42% | 17.30% | 17.76% | 14.6% | 51% |
| 3311 | Iron and Steel Mills and Ferroalloy Manufacturing | US$4.83bn | 21.10% | 21.49% | 26.04% | 6.2% | 69% |

## Caveats

- Exports are allocated to CMAs by employment share within each industry: assumes exports per worker in an industry are the same everywhere in Canada.
- 2021 Census employment (latest industry-by-CMA data, table 98-10-0448), counted where workers live, not where they work: e.g. Barrie picks up Honda Alliston commuters. GM Oshawa reopened in late 2021, after the Census, so Oshawa's auto share is understated.
- 2025 trade weights; static, first-round effects only (no supply-chain or household-income multipliers).
- Export intensity uses 2024 manufacturing revenue (table 16-10-0117); jobs at risk are not computed for farming, forestry and mining.
- HS6 codes mapping to several NAICS industries are split equally. HTS chapters 98-99 (special provisions, about 5.5% of value) have no industry and are left out.
- Elasticity 2.0 is a mid-range short-to-medium-run value; losses scale roughly in proportion to it (see sensitivity in cma_results.xlsx).
