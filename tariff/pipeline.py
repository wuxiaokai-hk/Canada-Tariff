"""Download -> check -> archive -> model -> reports. Used by run_all.py."""
import datetime as dt
import glob
import json
import os
import shutil

import pandas as pd

from . import cma, cma_excel, model, report, workbook

DATA_FILES = {
    "dataweb": ["dataweb_canada_hts10_2025.csv", "dataweb_monthly_totals.csv", "dataweb_program_split_2025.csv"],
    "statcan": ["statcan_cma_employment_naics4_2021.csv", "statcan_mfg_sales_naics.csv"],
}


# ---------------------------------------------------------------- checks
def check_dataweb(d):
    """Return a list of problems with the DataWeb files in folder d (empty list = OK)."""
    p = []
    h = pd.read_csv(os.path.join(d, "dataweb_canada_hts10_2025.csv"), dtype={"hts10": str})
    m = pd.read_csv(os.path.join(d, "dataweb_monthly_totals.csv"))
    s = pd.read_csv(os.path.join(d, "dataweb_program_split_2025.csv"), dtype={"hs4": str})
    if len(h) < 15000:
        p.append(f"HTS10 file has only {len(h):,} lines (expected about 20,000)")
    y = m[m["month"].str.startswith("2025")]["customs_value"].sum()
    if y and abs(h["customs_value"].sum() / y - 1) > 0.005:
        p.append(f"HTS10 total {h['customs_value'].sum():,.0f} differs from 2025 monthly total {y:,.0f} by more than 0.5%")
    if not {"USMCA"} <= set(s["program"]):
        p.append("program split has no USMCA rows")
    return p


def check_statcan(d):
    p = []
    e = pd.read_csv(os.path.join(d, "statcan_cma_employment_naics4_2021.csv"), dtype={"naics4": str})
    if e["geo"].nunique() < 18:
        p.append(f"employment file has {e['geo'].nunique()} geographies (expected 18: Canada, Ontario, 16 CMAs)")
    tot = e[e["naics4"] == "TOTAL"].set_index("geo")["employed"]
    if "Canada" not in tot or tot["Canada"] < 1e7:
        p.append("Canada total employment missing or too small")
    s = pd.read_csv(os.path.join(d, "statcan_mfg_sales_naics.csv"), dtype={"naics": str})
    if s["sales_cad"].notna().sum() < 50:
        p.append("manufacturing sales file has fewer than 50 industries with data")
    return p


# ---------------------------------------------------------------- download with archive
def download(data_dir, dataweb_token=None, statcan=False):
    """Download into data/_incoming, check, archive the current files, then move the new ones in."""
    inc = os.path.join(data_dir, "_incoming")
    shutil.rmtree(inc, ignore_errors=True)
    os.makedirs(inc)
    chapters = os.path.join(data_dir, "hts10_chapters")   # per-chapter saves, kept permanently; lets a stopped run resume
    groups = []
    if dataweb_token:
        from . import dataweb
        dataweb.download_all(dataweb_token, inc, progress_dir=chapters)
        groups.append("dataweb")
    if statcan:
        from . import statcan as sc
        sc.download_all(inc)
        groups.append("statcan")
    problems = []
    if "dataweb" in groups:
        problems += check_dataweb(inc)
    if "statcan" in groups:
        problems += check_statcan(inc)
    if problems:
        raise RuntimeError("Downloaded data failed checks; data/ left unchanged. New files are in data/_incoming:\n  - " + "\n  - ".join(problems))
    stamp = dt.datetime.now().strftime("%Y-%m-%d_%H%M")
    arch = os.path.join(data_dir, "archive", stamp)
    os.makedirs(arch, exist_ok=True)
    man = read_manifest(data_dir)
    for g in groups:
        for f in DATA_FILES[g]:
            if os.path.exists(os.path.join(data_dir, f)):
                shutil.copy2(os.path.join(data_dir, f), os.path.join(arch, f))
            shutil.move(os.path.join(inc, f), os.path.join(data_dir, f))
        man[f"{g}_pulled"] = dt.date.today().strftime("%B %d, %Y")
    if os.path.exists(os.path.join(data_dir, "MANIFEST.json")):
        shutil.copy2(os.path.join(data_dir, "MANIFEST.json"), os.path.join(arch, "MANIFEST.json"))
    write_manifest(data_dir, man)
    shutil.rmtree(inc, ignore_errors=True)
    print(f"New data in place; previous files archived in {arch}")


def read_manifest(data_dir):
    f = os.path.join(data_dir, "MANIFEST.json")
    return json.load(open(f)) if os.path.exists(f) else {}


def write_manifest(data_dir, man=None):
    man = man or read_manifest(data_dir)
    h = pd.read_csv(os.path.join(data_dir, "dataweb_canada_hts10_2025.csv"), dtype={"hts10": str})
    m = pd.read_csv(os.path.join(data_dir, "dataweb_monthly_totals.csv"))
    man.update({"hts10_lines": len(h), "hts10_customs_value": float(h["customs_value"].sum()),
                "hts10_calc_duty": float(h["calc_duty"].sum()), "latest_month": str(m["month"].max()),
                "updated": dt.datetime.now().isoformat(timespec="seconds")})
    json.dump(man, open(os.path.join(data_dir, "MANIFEST.json"), "w"), indent=2)
    return man


# ---------------------------------------------------------------- reports
def build_reports(data_dir, reports_dir):
    problems = check_dataweb(data_dir) + check_statcan(data_dir)
    for p in problems:
        print("WARNING:", p)
    run = os.path.join(reports_dir, dt.date.today().isoformat())
    os.makedirs(run, exist_ok=True)

    R = model.run(data_dir)
    report.write_all(R, run)
    report.print_summary(R)

    h, _, _, _ = model.load_data(data_dir)
    u = R["summary"]["usmca_8708"]
    CR = cma.run(h, data_dir, u)
    sens = []
    for s in (1.0, 2.0, 4.0):
        o = cma.run(h, data_dir, u, sigma=s)["cma"]
        sens.append(o[["geo", "export_loss_pct_today", "export_loss_pct_C"] + [c for c in o.columns if c.startswith("mfg_jobs_at_risk")]].assign(sigma=s))
    names = pd.read_csv(os.path.join(data_dir, "naics2017_names.csv"), dtype=str).set_index("code")["desc"].to_dict()
    report.write_cma_markdown(CR, R, os.path.join(run, "CMA_RESULTS.md"), names)
    report.write_cma_excel(CR, os.path.join(run, "cma_results_detail.xlsx"), pd.concat(sens))

    workbook.build(data_dir, os.path.join(run, "Canada_US_Tariff_Scenarios_2026.xlsx"))
    cma_excel.build(data_dir, os.path.join(run, "Ontario_CMA_Tariff_Results.xlsx"))

    man = read_manifest(data_dir)
    S = R["summary"]
    log = [f"Run {dt.datetime.now():%Y-%m-%d %H:%M}",
           f"DataWeb data pulled: {man.get('dataweb_pulled', 'n/a')}; latest month {man.get('latest_month', 'n/a')}; {man.get('hts10_lines', 'n/a')} HTS10 lines",
           f"StatCan data pulled: {man.get('statcan_pulled', 'n/a')}",
           f"2025 realized rate {S['rate25']:.2%}; today {S['cur_r']:.2%} realized / {S['cur_s']:.2%} statutory",
           *[f"Scenario {k}: {S['scen'][k]['rate_r']:.2%} / {S['scen'][k]['rate_s']:.2%} (p = {S['prob'][k]:.0%})" for k in "ABC"],
           f"Probability-weighted: {S['w_r']:.2%} / {S['w_s']:.2%}",
           "Data checks: " + ("all passed" if not problems else "; ".join(problems))]
    open(os.path.join(run, "RUN_LOG.txt"), "w").write("\n".join(log) + "\n")

    latest = os.path.join(reports_dir, "latest")
    shutil.rmtree(latest, ignore_errors=True)
    shutil.copytree(run, latest)
    print(f"\nReports written to {run} (also copied to {latest}):")
    for f in sorted(glob.glob(os.path.join(run, "*"))):
        print("  ", os.path.basename(f))
    return run
