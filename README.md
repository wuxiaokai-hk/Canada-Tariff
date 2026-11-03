# Canada–U.S. tariff project

One command takes the project from downloading the data to the final reports:

- the U.S. effective tariff rate on Canadian goods;
- the January 2027 threat scenarios, with probabilities and the Moody's mapping;
- a check of the 2.6% realized rate;
- the impact on each Ontario CMA.

## Quick start

```bash
pip install -r requirements.txt
python run_all.py
```

This rebuilds every report from the data already saved in `data/`. The output goes to `reports/<today>/` and is copied to `reports/latest/`.

## Updating with new data

| What changed | Run |
|---|---|
| New U.S. import data, e.g. a new month on DataWeb | `python run_all.py --download-dataweb` |
| New StatCan tables | `python run_all.py --download-statcan` |
| Everything | `python run_all.py --download` |
| An assumption, e.g. probabilities, tariff rates, base month | Edit `tariff/config.py`, then `python run_all.py` |
| A new White House annex or ban list | Add the HTS codes to `tariff/annex_codes.py`, then `python run_all.py` |

The DataWeb download needs a free API token:
1. Sign in at https://dataweb.usitc.gov and open the **API** tab.
2. Copy the token.
3. Save it once to a private file (Mac/Linux): `echo "PASTE_TOKEN" > ~/.dataweb_token && chmod 600 ~/.dataweb_token`.
   `run_all.py` reads it from there. Alternatively set it for one session: `export DATAWEB_TOKEN="..."`
   (Windows PowerShell: `$env:DATAWEB_TOKEN="..."`). The variable wins if both are set.
   Tokens expire; when DataWeb rejects yours, copy a new one and overwrite the file.

DataWeb limits how fast you can call it, so the download takes about 15–20 minutes. StatCan needs no key.
Each HTS chapter is saved to `data/hts10_chapters/2025_pulled_<date>/chNN.csv` as soon as it arrives, and these files are kept after the run (one folder per download date). If the download stops (Ctrl+C, network error, rate limit), just run the same command again the same day: it reuses the saved chapters and fetches only the missing ones. To force a completely fresh download on the same day, delete that day's folder first.

**Safe updates:** new files are downloaded into `data/_incoming/` and checked first. The checks are:
- the row count;
- the HTS10 total against the monthly totals;
- USMCA rows are present;
- the StatCan geographies.

Only if the checks pass are the old files moved to `data/archive/<date_time>/` and the new ones put in place. `data/MANIFEST.json` records when each source was pulled.

## What you get (`reports/latest/`)

| File | Contents |
|---|---|
| `Canada_US_Tariff_Scenarios_2026.xlsx` | The formula workbook. Every number is a live Excel formula. Tabs: DataWeb data, New HTS codes, Calculated tariff rate, Scenario A/B/C, Scenario probabilities, Verify 2.6%, Inputs, HS6 values, Sources. Yellow cells are assumptions you can change in Excel |
| `Ontario_CMA_Tariff_Results.xlsx` | Ontario CMA results: summary, charts, drivers, industries, sensitivity, scenarios |
| `RESULTS.md` | National results with every calculation written out with its numbers |
| `CMA_RESULTS.md` | CMA results with the industries and HTS lines driving each CMA |
| `tariff_results.xlsx`, `cma_results_detail.xlsx` | All model outputs as plain values, for further analysis |
| `matched_hts_lines.csv`, `all_calculations.csv` | Line-level matches, and every calculation step |
| `RUN_LOG.txt` | Data versions, headline numbers and data-check results for the run |

## Project layout

```
run_all.py              one command: download -> check -> archive -> model -> reports
tariff/config.py        ALL assumptions, each with its source  <- edit here
tariff/annex_codes.py   White House Section 338 HTS lists and import bans
tariff/dataweb.py       USITC DataWeb downloader (HTS10, monthly totals, USMCA split)
tariff/statcan.py       Statistics Canada downloader (98-10-0448 employment by CMA, 16-10-0117 manufacturing revenue)
tariff/pipeline.py      download/check/archive logic and report building
tariff/model.py         national effective rate, scenarios, probabilities, 2.6% verification
tariff/cma.py           HTS10 -> NAICS industry -> Ontario CMA
tariff/workbook.py      writes the formula workbook
tariff/cma_excel.py     writes the CMA workbook
tariff/report.py        writes the Markdown/CSV/values outputs
data/                   current data, MANIFEST.json, archive/ of earlier versions
reports/<date>/         one folder per run; reports/latest/ = most recent
```

## Method

**Realized rate** = calculated duty ÷ customs value (DataWeb).

**Today's rate:**
- Start from the base month's realized rate (`BASE_MONTH` in config).
- Add 50% × (2025 imports on the Section 338 HTS lines, matched exactly at 8 or 10 digits) ÷ total imports.
- The statutory version starts from the Bank of Canada's 5.0% instead.

**Scenarios** (cumulative), each adding value × affected share × (new rate − current rate):
- A: vehicles (HS 8703/8704/8701) to 50% on non-U.S. content.
- B: plus parts (HS 8708) losing the USMCA exemption.
- C: plus steel derivatives (HS 73) to 50%.

**Probabilities:** P(any January increase) × a conditional split across A/B/C.

**CMAs:**
- Each HTS10 line's tariff change gives an export response of ((1+t1)/(1+t0))^-σ − 1, with σ = 2. Banned lines lose 100%.
- Lines are assigned to NAICS 4-digit industries, then split across CMAs by 2021 Census employment shares.
- Jobs at risk = employment × export intensity × export loss.

## Limits

- **Static trade weights:** based on 2025 trade, before anyone adjusts.
- **CMAs are estimated:** StatCan does not publish exports by CMA and product, so they are estimated from employment.
- **Census quirks:** the 2021 Census counts workers where they live. GM Oshawa reopened after the Census.
- **January 2027 threat:** posted on August 24, 2026, but not proclaimed as of the latest update.
- **Downloaders:** the DataWeb downloader follows the request format the DataWeb site uses. The StatCan downloader was checked offline against the real table structure. Both have run only partly against the live sites, so check `RUN_LOG.txt` after your first download.
