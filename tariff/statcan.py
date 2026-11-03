"""Download the Statistics Canada tables used for the CMA analysis, through the Web Data Service (WDS). No key needed.

  98-10-0448-01  2021 Census: industry groups (NAICS 2017, 4-digit) by labour force status, CMA
                 -> employed persons by industry in Canada, Ontario and the 16 Ontario CMAs
  16-10-0117-01  Principal statistics for manufacturing industries (revenue from goods manufactured, Canada)
                 -> export intensity of each manufacturing industry

Run:  python -m tariff.statcan data      (writes the two CSVs into data/)
Note: WDS answers a batch of coordinates in arbitrary order, so results are keyed by the coordinate returned.
"""
import csv
import os
import re
import sys
import time

import requests

WDS = "https://www150.statcan.gc.ca/t1/wds/rest"
CENSUS_PID = 98100448
MFG_PID = 16100117
GOODS = re.compile(r"^(11|21|31|32|33)\d{2}$")
ONTARIO_CMA_PATTERN = re.compile(r"\(CMA\), Ont\.$")       # 'Windsor (CMA), Ont.', 'Ottawa - Gatineau (Ontario part) (CMA), Ont.'


def _post(method, body):
    for a in range(5):
        r = requests.post(f"{WDS}/{method}", json=body, timeout=120)
        if r.status_code == 200:
            return r.json()
        time.sleep(5 * (a + 1))
    r.raise_for_status()


def metadata(pid):
    j = _post("getCubeMetadata", [{"productId": pid}])[0]
    if j.get("status") != "SUCCESS":
        raise RuntimeError(f"metadata failed for {pid}: {j}")
    return j["object"]["dimension"]


def get_points(pid, coords, batch=150):
    """coords: list of full 10-position coordinate strings. Returns {coordinate: (value, refPer, scalarFactorCode)}."""
    out = {}
    for i in range(0, len(coords), batch):
        body = [{"productId": pid, "coordinate": c, "latestN": 1} for c in coords[i:i + batch]]
        for x in _post("getDataFromCubePidCoordAndLatestNPeriods", body):
            o = x.get("object") or {}
            if x.get("status") == "SUCCESS" and o.get("vectorDataPoint"):
                dp = o["vectorDataPoint"][-1]
                out[o["coordinate"]] = (dp.get("value"), dp.get("refPer"), dp.get("scalarFactorCode"))
        time.sleep(0.5)
    return out


def _coord(parts):
    return ".".join(str(p) for p in list(parts) + [0] * (10 - len(parts)))


def _clean_geo(name):
    name = re.sub(r"\s*\(CMA\),?\s*Ont\.?$", "", name)
    return name.replace(" (Ontario part)", " (Ont. part)").replace(" - ", "-")


def download_cma_employment(out_csv):
    dims = {d["dimensionPositionId"]: d for d in metadata(CENSUS_PID)}
    geo = dims[1]["member"]
    ind = next(d for d in dims.values() if "Industry" in d["dimensionNameEn"])
    pos_ind = ind["dimensionPositionId"]
    geos = [m for m in geo if m["memberNameEn"] in ("Canada", "Ontario") or ONTARIO_CMA_PATTERN.search(m["memberNameEn"])]
    geos = [m for m in geos if "Ont./Que." not in m["memberNameEn"]]          # keep the Ontario part of Ottawa-Gatineau
    inds = [m for m in ind["member"] if m["memberId"] == 1 or GOODS.match(m["memberNameEn"][:4]) and m["memberNameEn"][4:5] == " "]

    def member(pos, pattern):
        return next(m["memberId"] for m in dims[pos]["member"] if re.search(pattern, m["memberNameEn"]))
    fixed = {}
    for pos, d in dims.items():
        n = d["dimensionNameEn"].lower()
        if pos in (1, pos_ind):
            continue
        fixed[pos] = member(pos, r"^Employed$") if "labour force" in n else member(pos, r"^Count$") if "statistic" in n else member(pos, r"^Total")
    coords, keys = [], []
    for g in geos:
        for m in inds:
            parts = [g["memberId"] if p == 1 else m["memberId"] if p == pos_ind else fixed[p] for p in sorted(dims)]
            coords.append(_coord(parts))
            keys.append((_clean_geo(g["memberNameEn"]), "TOTAL" if m["memberId"] == 1 else m["memberNameEn"][:4], m["memberNameEn"]))
    print(f"  98-10-0448: {len(geos)} geographies x {len(inds)} industries = {len(coords)} cells")
    vals = get_points(CENSUS_PID, coords)
    with open(out_csv, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["geo", "naics4", "industry", "employed", "ref_period"])
        for c, (g, code, name) in zip(coords, keys):
            v = vals.get(c, (0, "2021-01-01", 0))          # cells absent from WDS are zero / suppressed
            w.writerow([g, code, name, v[0] or 0, v[1]])
    return out_csv


def download_manufacturing_sales(out_csv):
    dims = {d["dimensionPositionId"]: d for d in metadata(MFG_PID)}
    canada = next(m["memberId"] for m in dims[1]["member"] if m["memberNameEn"] == "Canada")
    stat = next(m["memberId"] for m in dims[2]["member"] if m["memberNameEn"] == "Revenue from goods manufactured")
    inds = [m for m in dims[3]["member"] if re.fullmatch(r"\d{4}", str(m.get("classificationCode") or ""))]
    coords = [_coord([canada, stat, m["memberId"]]) for m in inds]
    vals = get_points(MFG_PID, coords, batch=100)
    with open(out_csv, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["naics", "industry", "sales_cad", "ref_period"])
        for c, m in zip(coords, inds):
            v, per, sc = vals.get(c, (None, None, 0))
            w.writerow([m["classificationCode"], m["memberNameEn"], "" if v is None else float(v) * 10 ** int(sc or 0), per])
    return out_csv


def download_all(data_dir="data"):
    print("Downloading Statistics Canada tables...")
    download_cma_employment(os.path.join(data_dir, "statcan_cma_employment_naics4_2021.csv"))
    download_manufacturing_sales(os.path.join(data_dir, "statcan_mfg_sales_naics.csv"))
    print("Done.")


if __name__ == "__main__":
    download_all(sys.argv[1] if len(sys.argv) > 1 else "data")
