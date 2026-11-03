# U.S. effective tariff rate on Canadian goods: current rate and January 2027 scenarios

Computed in Python from USITC DataWeb HTS10 data (U.S. imports from Canada, 2025) and the White House Section 338 annexes.

## Headline results

| Outcome | Realized rate | Statutory rate | Probability |
|---|---|---|---|
| Today (Section 338 in force) | 5.47% | 7.65% | 70% (no January increase) |
| Scenario A: Cars and trucks to 50%; CUSMA parts stay exempt | 6.49% | 9.68% | 12% |
| Scenario B: A + auto parts to 50% (CUSMA parts exemption removed) | 7.76% | 11.09% | 12% |
| Scenario C: B + steel derivatives to 50% (full Aug 24 threat) | 8.00% | 11.33% | 6% |
| **Probability-weighted** | **6.02%** | **8.53%** | |

Realized = duties actually collected / import value (what Census, USAFacts and RBC measure). Statutory = headline rates applied to all trade (what the Bank of Canada and Global Trade Alert use).

## Moody's mapping

| moodys | percentile | outcome | rate_realized | rate_statutory |
|---|---|---|---|---|
| S1 | 10.00% | No January increase | 5.47% | 7.65% |
| Baseline | 50.00% | No January increase | 5.47% | 7.65% |
| S2 | 75.00% | Scenario A: Cars and trucks to 50%; CUSMA parts stay exempt | 6.49% | 9.68% |
| S3 | 90.00% | Scenario B: A + auto parts to 50% (CUSMA parts exemption removed) | 7.76% | 11.09% |
| S4 | 96.00% | Scenario C: B + steel derivatives to 50% (full Aug 24 threat) | 8.00% | 11.33% |


## Does the 2.6% hold up?

Yes. DataWeb 2025: US$9.99bn duty / US$382.04bn imports = **2.61%**. Every source using duties collected / import value agrees within 0.05pp; sources near 5-9% use statutory rates.

| source | period | measure | their | ours | verdict |
|---|---|---|---|---|---|
| USAFacts (from Census) | 2025 | Duties collected / import value | 2.6% | 2.61% | Agrees |
| USAFacts (from Census) | 2026-07 | Duties collected / import value | 2.8% | 2.82% | Agrees |
| RBC Economics | 2026-07 | Effective rate on imports from Canada | 2.8% | 2.82% | Agrees |
| RBC Economics | 2026-08 | Effective rate on imports from Canada | 3.2% | 3.18% | Agrees |
| USAFacts (from Census) | Jan-Jul 2026 | Duties collected / import value | 3.1% | 3.05% | Agrees |
| USAFacts (from Census) | 2024 | Duties collected / import value | 0.1% |  | Context only |
| UN Comtrade | 2025 | Total U.S. imports from Canada (US$) | US$382.41bn | US$382.04bn | Agrees |
| Wharton Budget Model | 2026-07 | USMCA claim share, Canada + Mexico | 80.2% | 75.08% | Consistent (Canada only vs Canada + Mexico) |
| Bank of Canada MPR | 2026-07 | Statutory average U.S. tariff on Canada | 5.0% | 2.82% | Different concept (statutory) |
| Global Trade Alert | Before Jan 2027 | Statutory, trade-weighted, incl. Section 338 | 8.5% | 7.65% | Close (statutory vs statutory) |
| Wharton Budget Model | 2026-07 | Overall U.S. effective rate, all partners | 6.7% |  | Context only |


## Every calculation, with the numbers plugged in

### 1. DataWeb 2025

| Step | Result | Formula | Worked numbers |
|---|---|---|---|
| U.S. imports from Canada (customs value) | US$382.04bn | `sum(customs_value over all HTS10)` | 20,131 HTS10 lines = US$382.04bn |
| Calculated duty | US$9.99bn | `sum(calc_duty)` | US$9.99bn |
| Dutiable value | US$55.69bn | `sum(dutiable_value)` | US$55.69bn |
| Realized effective rate, 2025 | 2.61% | `calc_duty / customs_value` | US$9.99bn / US$382.04bn = 2.61% |
| Check: 12 monthly totals = annual HTS10 total | 1.000 | `sum(monthly 2025 value) / sum(HTS10 value)` | US$382.04bn / US$382.04bn = 1.0000 |
| USMCA (CUSMA) claim share, all goods | 75.08% | `USMCA value / all value` | US$286.85bn / US$382.04bn = 75.1% |
| USMCA claim share, HS 8708 auto parts | 80.80% | `USMCA value / all value (8708)` | US$8.70bn / US$10.76bn = 80.8% |
| USMCA claim share, HS 8703 cars | 98.98% | `USMCA value / all value (8703)` | US$24.85bn / US$25.11bn = 99.0% |

### 2. New HTS codes

| Step | Result | Formula | Worked numbers |
|---|---|---|---|
| Lines under the 50% tariff now / banned lines | 659 | `count of annex lines` | 659 tariffed lines, 68 banned lines; 76 lines had no 2025 imports |
| Value under Section 338 now (net of carve-outs) | US$20.26bn | `sum(sign x value), sign = +1 listed, -1 carve-out` | July-annex lines US$19.28bn + Sep 15 additions US$1.85bn - carve-outs = US$20.26bn |
| Check: exact coverage / official US$20bn | 1.013 | `coverage / 20e9` | US$20.26bn / US$20.00bn = 1.013 |
| Value of banned lines (from Sep 29) | US$0.97bn | `sum(value of banned lines)` | US$0.97bn vs CRS about US$0.97bn (ratio 1.000) |
| Value of lines removed on Sep 15 | US$0.88bn | `sum(value of removed lines)` | US$0.88bn |
| Realized duty already paid on tariffed lines, 2025 | 2.51% | `sum(sign x duty) / coverage` | US$0.51bn / US$20.26bn = 2.51% |

### 3. Calculated tariff rate

| Step | Result | Formula | Worked numbers |
|---|---|---|---|
| Realized base rate (2026-07, before Section 338) | 2.82% | `duty / value in base month` | US$0.95bn / US$33.49bn = 2.82% |
| Covered share of all imports | 5.30% | `coverage / total imports` | US$20.26bn / US$382.04bn = 5.30% |
| Section 338 increment | 2.65% | `covered share x 50%` | 5.30% x 50% = 2.65% |
| CURRENT RATE, realized | 5.47% | `base_realized + 50% x coverage / total` | 2.82% + 50% x US$20.26bn / US$382.04bn = 5.47% |
| CURRENT RATE, statutory | 7.65% | `base_statutory + 50% x coverage / total` | 5.00% + 50% x US$20.26bn / US$382.04bn = 7.65% |
| Check: August 2026 realized vs 10/31 of the month under Section 338 | 3.18% | `realized Aug rate vs base + increment x 10/31` | realized 3.18% vs implied 3.68% (gap = front-loading / trade shifts) |
| Reconciliation: earlier HS6-based statutory estimate | 8.48% | `base_statutory + 50% x HS6 value / total` | 5.00% + 50% x US$26.59bn / US$382.04bn = 8.48% (HS6 codes include unlisted 8-digit lines) |

### 4. Scenario A

| Step | Result | Formula | Worked numbers |
|---|---|---|---|
| Added duty from this scenario's components | US$3.88bn | `sum(value x share x (after - now))` | US$31.06bn x 50% x (50% - 25%) = US$3.88bn |
| Increment over the previous scenario (realized) | 1.02% | `added duty / total imports` | US$3.88bn / US$382.04bn = 1.02% |
| AVERAGE RATE, SCENARIO A (realized) | 6.49% | `current + cumulative increments` | 5.47% + 1.02% = 6.49% |
| AVERAGE RATE, SCENARIO A (statutory) | 9.68% | `current + cumulative increments` | 7.65% + 2.03% = 9.68% |

### 4. Scenario B

| Step | Result | Formula | Worked numbers |
|---|---|---|---|
| Added duty from this scenario's components | US$4.86bn | `sum(value x share x (after - now))` | US$4.35bn + US$0.52bn = US$4.86bn |
| Increment over the previous scenario (realized) | 1.27% | `added duty / total imports` | US$4.86bn / US$382.04bn = 1.27% |
| AVERAGE RATE, SCENARIO B (realized) | 7.76% | `current + cumulative increments` | 5.47% + 2.29% = 7.76% |
| AVERAGE RATE, SCENARIO B (statutory) | 11.09% | `current + cumulative increments` | 7.65% + 3.44% = 11.09% |

### 4. Scenario C

| Step | Result | Formula | Worked numbers |
|---|---|---|---|
| Added duty from this scenario's components | US$0.90bn | `sum(value x share x (after - now))` | US$3.59bn x 100% x (50% - 25%) = US$0.90bn |
| Increment over the previous scenario (realized) | 0.23% | `added duty / total imports` | US$0.90bn / US$382.04bn = 0.23% |
| AVERAGE RATE, SCENARIO C (realized) | 8.00% | `current + cumulative increments` | 5.47% + 2.52% = 8.00% |
| AVERAGE RATE, SCENARIO C (statutory) | 11.33% | `current + cumulative increments` | 7.65% + 3.68% = 11.33% |

### 5. Probabilities

| Step | Result | Formula | Worked numbers |
|---|---|---|---|
| P(any Jan 2027 increase in force by end-Q1 2027) | 30.00% | `input` | Split given an increase: A 40%, B 40%, C 20% |
| PROBABILITY-WEIGHTED RATE (realized) | 6.02% | `sum(probability x rate)` | 70% x 5.47% + 12% x 6.49% + 12% x 7.76% + 6% x 8.00% = 6.02% |
| PROBABILITY-WEIGHTED RATE (statutory) | 8.53% | `sum(probability x rate)` | 70% x 7.65% + 12% x 9.68% + 12% x 11.09% + 6% x 11.33% = 8.53% |

## Scenario components

| scenario | component | worked_realized | worked_statutory |
|---|---|---|---|
| A | Cars, trucks, tractors (8703/8704/8701), non-U.S. content | US$31.06bn x 50% x (50% - 25%) = US$3.88bn | US$31.06bn x 25% = US$7.76bn |
| B | Auto parts under CUSMA (exempt today) | US$10.76bn x 81% x (50% - 0%) = US$4.35bn | US$10.76bn x 50% = US$5.38bn |
| B | Auto parts not under CUSMA | US$10.76bn x 19% x (50% - 25%) = US$0.52bn | US$10.76bn x 0% = US$0.00bn |
| C | Steel derivatives (HS ch. 73 proxy) | US$3.59bn x 100% x (50% - 25%) = US$0.90bn | US$3.59bn x 25% = US$0.90bn |


## Probability evidence

| source | finding | reading | how_used |
|---|---|---|---|
| Kalshi (Oct 12, 2026) | Canada accepts a U.S. trade deal before Jan 1, 2027 | 30% | 70% no-deal is an upper bound on increase odds, not an estimate of them |
| Kalshi (Oct 12, 2026) | ...before Dec 1, 2026 | 10% | Talks not expected to conclude quickly |
| Polymarket (Oct 12, 2026) | U.S.-Canada agreement to lower tariffs by Dec 31, 2026 | 62% | Markets lean toward de-escalation |
| Polymarket (Oct 12, 2026) | Trump announces a Canada tariff increase by Oct 31, 2026 | 73% | Announcements likely; implementation is a separate, lower-probability event |
| Treasury & Risk / Bloomberg (Jan 27, 2026) | Share of Trump tariff threats carried out | 25% | Base rate; central 30% sits slightly above because Section 232 only needs a rate change |
| Global Automakers of Canada (Sep 2026) | Doubt the CUSMA parts exemption will be extended |  | Why B gets equal weight with A |
| No proclamation (as of Oct 13, 2026) | Threat exists only as an Aug 24 post |  | Keeps C at the smallest conditional share |


## Sensitivity (realized rates)

| P_any_increase | US_content_share | rate_A | rate_B | rate_C | prob_weighted |
|---|---|---|---|---|---|
| 20.00% | 30.00% | 6.90% | 8.17% | 8.40% | 5.92% |
| 20.00% | 50.00% | 6.49% | 7.76% | 8.00% | 5.84% |
| 20.00% | 60.00% | 6.29% | 7.56% | 7.80% | 5.80% |
| 30.00% | 30.00% | 6.90% | 8.17% | 8.40% | 6.14% |
| 30.00% | 50.00% | 6.49% | 7.76% | 8.00% | 6.02% |
| 30.00% | 60.00% | 6.29% | 7.56% | 7.80% | 5.96% |
| 40.00% | 30.00% | 6.90% | 8.17% | 8.40% | 6.37% |
| 40.00% | 50.00% | 6.49% | 7.76% | 8.00% | 6.20% |
| 40.00% | 60.00% | 6.29% | 7.56% | 7.80% | 6.12% |


## Caveats

- Static 2025 trade weights: actual duties fall as tariffed and banned trade shrinks.
- The January 2027 increases exist only as an August 24, 2026 social-media post; no proclamation had been issued as of October 13, 2026.
- Steel derivatives use HS chapter 73 as a proxy and an assumed 25% current effective Section 232 rate.
- U.S. content of Canadian-built vehicles (50%) is an assumption; see the sensitivity table.
