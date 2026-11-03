"""Download U.S. imports from Canada from USITC DataWeb.

DataWeb's API needs a personal token:
  1. Sign in at https://dataweb.usitc.gov (free account).
  2. Open the "API" tab and copy your token.
  3. Set it before running:  export DATAWEB_TOKEN="paste-token-here"
     (Windows PowerShell: $env:DATAWEB_TOKEN="paste-token-here")

Without a token, run_all.py uses the cached CSVs in data/ (pulled October 12, 2026).
"""
import copy
import csv
import os
import time

import requests

API = "https://datawebws.usitc.gov/dataweb/api/v2/report2/runReport"
CANADA = "1220"
PAUSE = 9          # seconds between calls; DataWeb returns HTTP 429 if called faster
RETRY_429 = 60     # seconds to wait after a 429


def _base_query(measures, years, granularity, timeline="Annual"):
    """Query body in the same shape the DataWeb web app sends."""
    return {
        "savedQueryName": "", "savedQueryDesc": "", "isOwner": True, "runMonthly": False,
        "reportOptions": {"tradeType": "Import", "classificationSystem": "HTS"},
        "searchOptions": {
            "MiscGroup": {
                "districtGroups": {"userGroups": []},
                "importPrograms": {"aggregation": None, "importPrograms": [], "programsSelectType": "all"},
                "extImportPrograms": {"aggregation": "Aggregate CSC", "extImportPrograms": [],
                                      "extImportProgramsExpanded": [], "programsSelectType": "all"},
                "provisionCodes": {"aggregation": "Aggregate RPCODE", "provisionCodesSelectType": "all",
                                   "rateProvisionCodes": [], "rateProvisionCodesExpanded": []},
            },
            "commodities": {
                "aggregation": "Aggregate Commodities", "codeDisplayFormat": "YES",
                "commodities": [], "commoditiesExpanded": [], "commoditiesManual": "",
                "commodityGroups": {"systemGroups": [], "userGroups": []},
                "commoditySelectType": "all", "granularity": str(granularity),
                "groupGranularity": None, "searchGranularity": None,
            },
            "componentSettings": {
                "dataToReport": measures, "scale": "1", "timeframeSelectType": "fullYears",
                "years": years, "startDate": None, "endDate": None, "startMonth": None, "endMonth": None,
                "yearsTimeline": timeline,
            },
            "countries": {
                "aggregation": "Aggregate Countries", "countries": [CANADA],
                # name must match DataWeb's country list exactly, or it rejects the query ("Incorrect country information")
                "countriesExpanded": [{"name": "Canada - CA - CAN", "value": CANADA}], "countriesSelectType": "list",
                "countryGroups": {"systemGroups": [], "userGroups": []},
            },
        },
        "sortingAndDataFormat": {
            "DataSort": {"columnOrder": [], "fullColumnOrder": [], "sortOrder": []},
            "reportCustomizations": {"exportCombineTables": False, "showAllSubtotal": True, "subtotalRecords": "",
                                     "totalRecords": "20000", "exportRawData": True},
        },
    }


def _break_out(q, codes):
    q = copy.deepcopy(q)
    c = q["searchOptions"]["commodities"]
    c["aggregation"] = "Break Out Commodities"
    if codes:
        c["commoditySelectType"] = "list"
        c["commodities"] = list(codes)
    return q


def _post(session, q, token):
    headers = {"Content-Type": "application/json; charset=utf-8", "Authorization": "Bearer " + token}
    for attempt in range(8):
        r = session.post(API, json=q, headers=headers, timeout=180)
        if r.status_code == 200:
            time.sleep(PAUSE)
            j = r.json()
            errors = (j.get("dto") or {}).get("errors")
            if errors:   # DataWeb reports invalid queries with HTTP 200 and no tables
                raise RuntimeError("DataWeb rejected the query: " + "; ".join(map(str, errors)))
            return j
        if r.status_code == 429:
            print(f"    rate-limited, waiting {RETRY_429}s")
            time.sleep(RETRY_429)
            continue
        if r.status_code in (401, 403):
            raise RuntimeError("DataWeb rejected the token (HTTP %s). Copy a fresh token from the API tab." % r.status_code)
        print(f"    HTTP {r.status_code}, retrying")
        time.sleep(15)
    raise RuntimeError("DataWeb did not answer after 8 attempts")


def _num(x):
    try:
        return float(str(x).replace(",", ""))
    except ValueError:
        return 0.0


def _rows(table):
    """Each row as a list of cell values."""
    return [[e.get("value") for e in r["rowEntries"]] for r in table["row_groups"][0]["rowsNew"]]


HTS10_HEADER = ["hts10", "customs_value", "calc_duty", "dutiable_value"]


def _write_rows(path, rows):
    """Write a CSV via a temp file, so a crash never leaves a half-written file behind."""
    tmp = path + ".tmp"
    with open(tmp, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(HTS10_HEADER)
        w.writerows(rows)
    os.replace(tmp, path)


def download_hts10(token, year="2025", out_csv="data/dataweb_canada_hts10_2025.csv", progress_dir=None):
    """HTS10 customs value, calculated duty and dutiable value, one request per HS chapter (row cap is 20,000).

    Each chapter is saved to progress_dir/<year>_pulled_<date>/chNN.csv as soon as it arrives, and kept
    after the run. If the run stops, the next run on the same day reuses the saved chapters and downloads
    only the missing ones. To force a fresh same-day download, delete that day's folder.
    """
    measures = ["CONS_CUSTOMS_VALUE", "CONS_CALC_DUTY", "CONS_CUSTOMS_VALUE_SUB_DUTY"]
    base = _base_query(measures, [year], 10)
    if progress_dir is None:
        progress_dir = os.path.join(os.path.dirname(out_csv), "hts10_chapters")
    progress_dir = os.path.join(progress_dir, f"{year}_pulled_{time.strftime('%Y-%m-%d')}")
    os.makedirs(progress_dir, exist_ok=True)
    data = {}
    s = None
    for ch in range(1, 100):
        ch = f"{ch:02d}"
        if ch == "77":          # chapter reserved in the HTS
            continue
        saved = os.path.join(progress_dir, f"ch{ch}.csv")
        if os.path.exists(saved):
            with open(saved, newline="") as f:
                for r in list(csv.reader(f))[1:]:
                    data[r[0]] = [float(x) for x in r[1:]]
            print(f"  chapter {ch}: {len(data):,} lines so far (saved earlier)")
            continue
        s = s or requests.Session()
        j = _post(s, _break_out(base, [ch]), token)
        tables = j["dto"]["tables"]        # one table per measure, in the order requested
        chapter = {}
        for ti, tb in enumerate(tables):
            for v in _rows(tb):
                # codes may come back formatted, e.g. "0101.21.00.10" or "0101210010 - description"
                code = "".join(c for c in str(v[0]).split(" ")[0] if c.isdigit())
                if len(code) != 10:
                    continue
                chapter.setdefault(code, [0.0, 0.0, 0.0])[ti] = _num(v[-1])
        if not chapter:
            sample = _rows(tables[0])[:3] if tables else "no tables in response"
            print(f"    no HTS10 codes parsed for chapter {ch}; first rows: {sample}")
        _write_rows(saved, [[c] + [int(x) for x in chapter[c]] for c in sorted(chapter)])
        data.update(chapter)
        print(f"  chapter {ch}: {len(data):,} lines so far")
    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    _write_rows(out_csv, [[c] + [int(x) for x in data[c]] for c in sorted(data)])
    return out_csv


def download_monthly(token, years=("2025", "2026"), out_csv="data/dataweb_monthly_totals.csv"):
    """Monthly totals of customs value and calculated duty, all goods."""
    q = _base_query(["CONS_CUSTOMS_VALUE", "CONS_CALC_DUTY"], list(years), 2, timeline="Monthly")
    j = _post(requests.Session(), q, token)
    tables = j["dto"]["tables"]
    out = {}
    for ti, tb in enumerate(tables):
        for v in _rows(tb):
            yr = str(v[0])
            for m, x in enumerate(v[1:13], 1):
                out.setdefault(f"{yr}-{m:02d}", [0.0, 0.0])[ti] = _num(x)
    with open(out_csv, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["month", "customs_value", "calc_duty"])
        for k in sorted(out):
            if out[k][0] > 0:
                w.writerow([k, int(out[k][0]), int(out[k][1])])
    return out_csv


def download_program_split(token, year="2025", out_csv="data/dataweb_program_split_2025.csv"):
    """Value and duty by special program (USMCA vs none), all goods and HS 8703/8704/8708."""
    measures = ["CONS_CUSTOMS_VALUE", "CONS_CALC_DUTY"]
    rows = []
    s = requests.Session()
    for codes, gran in ((None, 2), (["8703", "8704", "8708"], 4)):
        q = _base_query(measures, [year], gran)
        if codes:
            q = _break_out(q, codes)
        q["searchOptions"]["MiscGroup"]["importPrograms"]["aggregation"] = "Break Out CSC"
        q["searchOptions"]["MiscGroup"]["extImportPrograms"]["aggregation"] = "Break Out CSC"
        j = _post(s, q, token)
        acc = {}
        for ti, tb in enumerate(j["dto"]["tables"]):
            for v in _rows(tb):
                txt = " ".join(str(x) for x in v)
                prog = "USMCA" if "USMCA" in txt else ("NONE" if "No special" in txt else "OTHER")
                hs4 = str(v[0]) if (codes and str(v[0]).isdigit()) else "ALL"
                acc.setdefault((hs4, prog), [0.0, 0.0])[ti] += _num(v[-1])
        rows += [(k[0], k[1], int(a), int(b)) for k, (a, b) in acc.items()]
    with open(out_csv, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["hs4", "program", "customs_value", "calc_duty"])
        w.writerows(sorted(rows))
    return out_csv


def download_all(token, data_dir="data", progress_dir=None):
    print("Downloading from USITC DataWeb (about 15-20 minutes because of the rate limit)...")
    download_hts10(token, out_csv=os.path.join(data_dir, "dataweb_canada_hts10_2025.csv"), progress_dir=progress_dir)
    download_monthly(token, out_csv=os.path.join(data_dir, "dataweb_monthly_totals.csv"))
    download_program_split(token, out_csv=os.path.join(data_dir, "dataweb_program_split_2025.csv"))
    print("Download complete.")
