"""Build the formula workbook Canada_US_Tariff_Scenarios_2026.xlsx from the files in data/.

Called by run_all.py; can also be run alone:  python -m tariff.workbook data output.xlsx
Every number in the workbook is a live Excel formula; assumptions come from tariff/config.py.
"""
import calendar
import csv
import json
import os
import sys

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Side, Border
from openpyxl.utils import get_column_letter

from . import config as C
from .annex_codes import *  # noqa: F401,F403


def _month_label(m):
    y, mm = m.split("-")
    return f"{calendar.month_name[int(mm)]} {y}"


def context(data_dir):
    """Numbers the workbook needs that come from the downloaded data files (no typing by hand)."""
    m = pd.read_csv(os.path.join(data_dir, "dataweb_monthly_totals.csv")).sort_values("month")
    m = m[m["customs_value"] > 0]
    mm = m.set_index("month")
    base = C.BASE_MONTH if C.BASE_MONTH in mm.index else m["month"].iloc[-1]
    latest = m["month"].iloc[-1]
    y = m[m["month"].str.startswith("2025")]
    h = pd.read_csv(os.path.join(data_dir, "dataweb_canada_hts10_2025.csv"), dtype={"hts10": str})
    p = pd.read_csv(os.path.join(data_dir, "dataweb_program_split_2025.csv"), dtype={"hs4": str})
    def share(hs4):
        s = p[p["hs4"] == hs4].groupby("program")["customs_value"].sum()
        return float(s.get("USMCA", 0) / s.sum()) if s.sum() else 0.0
    ytd = m[m["month"].between(f"{latest[:4]}-01", base)] if base[:4] == latest[:4] else m.iloc[0:0]
    manifest = os.path.join(data_dir, "MANIFEST.json")
    pulled = json.load(open(manifest)).get("dataweb_pulled", "see MANIFEST") if os.path.exists(manifest) else "October 12, 2026"
    # share of the latest month with Section 338 in force (338 started Aug 22, 2026)
    start = pd.Timestamp(C.SECTION_338_START)
    lm = pd.Period(latest, "M")
    days = lm.days_in_month
    frac = 0.0 if lm.end_time < start else (1.0 if lm.start_time >= start else (days - start.day + 1) / days)
    return {
        "pulled": pulled, "base": base, "latest": latest,
        "base_label": _month_label(base), "latest_label": _month_label(latest),
        "base_val": float(mm.loc[base, "customs_value"]), "base_duty": float(mm.loc[base, "calc_duty"]),
        "latest_val": float(mm.loc[latest, "customs_value"]), "latest_duty": float(mm.loc[latest, "calc_duty"]),
        "y_val": float(h["customs_value"].sum()), "y_duty": float(h["calc_duty"].sum()), "y_dutiable": float(h["dutiable_value"].sum()),
        "y_monthly_val": float(y["customs_value"].sum()),
        "ytd_rate": float(ytd["calc_duty"].sum() / ytd["customs_value"].sum()) if len(ytd) else None,
        "usmca_all": share("ALL"), "usmca_8703": share("8703"), "usmca_8708": share("8708"),
        "frac338": round(frac, 3),
    }


def verify_rows(X, CUR_S):
    """Rows for the 'Verify 2.6%' tab, from config.EXTERNAL_CHECKS."""
    ours = {"rate_2025": "='DataWeb data'!E5", f"rate_{X['base']}": "='DataWeb data'!E6", f"rate_{X['latest']}": "='DataWeb data'!E7",
            "total_value": "='DataWeb data'!B5", "usmca_share_all": "='DataWeb data'!B11", "current_statutory": "=" + CUR_S,
            "rate_2026ytd_jul": X["ytd_rate"]}
    rows = [("This workbook (DataWeb)", "2025", "Calculated duty / customs value", "='DataWeb data'!E5", "='DataWeb data'!E5", "DataWeb HTS10 total")]
    for (src, per, meas, theirs, key, comparable) in C.EXTERNAL_CHECKS:
        name = "UN Comtrade cross-check" if src.startswith("UN Comtrade") else src
        rows.append((name, per, meas, float(theirs), ours.get(key) if key else None, "" if comparable else "Different concept or context"))
    return rows


def build(data_dir, out_path):
    X = context(data_dir)
    v = {r["hs6"]: int(float(r["customs_value"])) for r in csv.DictReader(open(os.path.join(data_dir, "comtrade_hs6_2025.csv")))}
    CSV = os.path.join(data_dir, "dataweb_canada_hts10_2025.csv")
    OUT = out_path
    AR = "Arial"
    F = Font(name=AR, size=10); FB = Font(name=AR, size=10, bold=True)
    FH = Font(name=AR, size=10, bold=True, color="FFFFFF"); FBLUE = Font(name=AR, size=10, color="0000FF")
    FGREEN = Font(name=AR, size=10, color="008000"); FT = Font(name=AR, size=14, bold=True)
    FI = Font(name=AR, size=9, italic=True, color="595959")
    HFILL = PatternFill("solid", fgColor="1F3864"); YFILL = PatternFill("solid", fgColor="FFFF00")
    KFILL = PatternFill("solid", fgColor="DDEBF7")
    USD = '$#,##0;($#,##0);"-"'; PCT = '0.0%;(0.0%);"-"'; PCT2 = '0.00%;(0.00%);"-"'; BN = '$#,##0.00,,,"bn";($#,##0.00,,,"bn");"-"'
    WRAP = Alignment(wrap_text=True, vertical="top")

    wb = Workbook()

    def header(ws, row, cols, widths=None, freeze=True):
        for i, c in enumerate(cols, 1):
            cell = ws.cell(row=row, column=i, value=c); cell.font = FH; cell.fill = HFILL
            cell.alignment = Alignment(wrap_text=True, vertical="center")
        if widths:
            for i, w in enumerate(widths, 1):
                ws.column_dimensions[get_column_letter(i)].width = w
        if freeze:
            ws.freeze_panes = ws.cell(row=row + 1, column=1)

    def put(ws, r, c, val, font=F, fmt=None, fill=None, wrap=False):
        cell = ws.cell(row=r, column=c, value=val); cell.font = font
        if fmt: cell.number_format = fmt
        if fill: cell.fill = fill
        if wrap: cell.alignment = WRAP
        return cell

    def title(ws, t, sub=None):
        put(ws, 1, 1, t, FT)
        if sub: put(ws, 2, 1, sub, FI)

    # ======================= Read me =======================
    RM = wb.active; RM.title = "Read me"
    RM.column_dimensions["A"].width = 125
    readme = [
        ("Canada-U.S. tariffs: effective U.S. tariff rate on Canadian goods, and January 2027 threat scenarios", FT),
        ("As of October 13, 2026. Data: USITC DataWeb (U.S. imports for consumption from Canada, HTS10, 2025 and monthly 2026), White House Section 338 annexes, UN Comtrade.", FI),
        ("", F),
        ("Tabs", FB),
        ("1. DataWeb data: U.S. imports from Canada from USITC DataWeb. Annual 2025 total, monthly 2026, CUSMA (USMCA) claim shares, and line-level HTS10 detail (customs value, calculated duty, dutiable value).", F),
        ("2. New HTS codes: every HTS line in the Section 338 annexes (July 20 and September 8, 2026 proclamations) and the September 29 import bans, with status and matched 2025 import values.", F),
        ("3. Calculated tariff rate: the current trade-weighted effective rate = realized pre-Section-338 rate (DataWeb) + Section 338 increment on covered HTS lines.", F),
        ("4-6. Scenario A, B, C: the average (trade-weighted) effective rate if the January 1, 2027 threats are implemented. Each scenario adds to the one before.", F),
        ("     A = cars, trucks and tractors to 50% (CUSMA parts stay exempt). B = A + auto parts to 50% (CUSMA parts exemption removed). C = B + steel derivatives to 50% (the full August 24 threat).", F),
        ("7. Scenario probabilities: probability of each outcome by end-Q1 2027, the evidence behind it, the probability-weighted rate, and how A/B/C map to Moody's S3 and S4.", F),
        ("8. Verify 2.6%: the 2025 realized rate of 2.61% checked against USAFacts, RBC, Wharton, Bank of Canada, Global Trade Alert and monthly DataWeb figures.", F),
        ("9. HS6 values: 2025 import values by 6-digit HS code (UN Comtrade), used as a fallback when line-level HTS10 data is not loaded.", F),
        ("10. Sources.", F),
        ("", F),
        ("Two ways to measure the rate", FB),
        ("Realized (central): calculated duties / customs value, as Census/DataWeb record them. Captures CUSMA-exempt trade (75% of 2025 value) and is what USAFacts and RBC publish. This is the basis for the scenario rates.", F),
        ("Statutory (upper bound): applies headline rates to full trade values, as the Bank of Canada (5.0%) and Global Trade Alert (8.5%) do. Shown alongside for comparison with Moody's and other published assumptions.", F),
        ("", F),
        ("Conventions", FB),
        ("Every number is a live Excel formula. On 'Calculated tariff rate' and the Scenario tabs, extra columns print each formula as text and show the same calculation with the numbers plugged in (e.g. 5.00% + 50% x US$xx.xxbn / US$382.04bn).", F),
        ("Yellow cells with blue text are inputs; change them and every rate recalculates. Black = formula. Green = link to another tab.", F),
        ("Rates are static (2025 trade weights). Actual duties collected will be lower once tariffed and banned trade shrinks.", F),
        ("The January 2027 increases were announced by social-media post on August 24, 2026. No proclamation had been issued as of October 13, 2026.", F),
    ]
    for i, (t, f) in enumerate(readme, 1):
        c = put(RM, i, 1, t, f); c.alignment = Alignment(wrap_text=True)

    # ======================= DataWeb data =======================
    DW = wb.create_sheet("DataWeb data")
    title(DW, "USITC DataWeb: U.S. imports for consumption from Canada (country code 1220)",
          f"Source: dataweb.usitc.gov, Import / HTS, measures CONS_CUSTOMS_VALUE, CONS_CALC_DUTY, CONS_CUSTOMS_VALUE_SUB_DUTY. Pulled {X['pulled']}; data available through {X['latest_label']}.")
    for col, w in zip("ABCDEFGHI", [34, 20, 20, 20, 12, 3, 14, 10, 14]):
        DW.column_dimensions[col].width = w
    header(DW, 4, ["A. Totals", "Customs value (US$)", "Calculated duty (US$)", "Dutiable value (US$)", "Realized rate"], freeze=False)
    totals = [
        ("2025 (calendar year)", X["y_val"], X["y_duty"], X["y_dutiable"]),
        (f"{X['base_label']} (base month, before Section 338)", X["base_val"], X["base_duty"], None),
        (f"{X['latest_label']} (latest month available)", X["latest_val"], X["latest_duty"], None),
    ]
    for i, (lab, val, duty, dv) in enumerate(totals, 5):
        put(DW, i, 1, lab)
        put(DW, i, 2, val, FBLUE, USD); put(DW, i, 3, duty, FBLUE, USD)
        if dv: put(DW, i, 4, dv, FBLUE, USD)
        put(DW, i, 5, f"=C{i}/B{i}", F, PCT2)
    put(DW, 8, 1, "Rows 6-7: DataWeb monthly totals (data/dataweb_monthly_totals.csv). The base month is set in tariff/config.py (BASE_MONTH).", FI)

    header(DW, 10, ["B. CUSMA (USMCA) claim share, 2025", "Share of customs value entered under CUSMA", "", "", ""], freeze=False)
    cus = [("All goods", X["usmca_all"]), ("Passenger vehicles, HS 8703", X["usmca_8703"]), ("Auto parts, HS 8708", X["usmca_8708"])]
    for i, (lab, s) in enumerate(cus, 11):
        put(DW, i, 1, lab); put(DW, i, 2, s, FBLUE, PCT)
    put(DW, 14, 1, "From DataWeb 'Break Out CSC' (special program indicator S/S+). CUSMA-claimed goods pay no Section 301/IEEPA-type surcharge; they can still owe Section 232 or Section 338 duty.", FI)

    DROW = 17
    header(DW, DROW - 1, ["C. HTS10 detail, 2025", "Customs value (US$)", "Calculated duty (US$)", "Dutiable value (US$)", "Realized rate", "", "HTS8 (helper)", "Chapter (helper)", "HS4 (helper)"], freeze=False)
    DW.freeze_panes = "A17"
    n10 = 0
    if CSV and os.path.exists(CSV):
        with open(CSV) as fh:
            rd = csv.DictReader(fh)
            rows = sorted(rd, key=lambda r: r['hts10'])
        for k, r0 in enumerate(rows):
            r = DROW + k
            code = r0['hts10'].strip().zfill(10)
            DW.cell(row=r, column=1, value=code).font = F
            DW.cell(row=r, column=2, value=float(r0['customs_value'] or 0)).number_format = USD
            DW.cell(row=r, column=3, value=float(r0['calc_duty'] or 0)).number_format = USD
            DW.cell(row=r, column=4, value=float(r0['dutiable_value'] or 0)).number_format = USD
            c = DW.cell(row=r, column=5, value=f"=IF(B{r}>0,C{r}/B{r},0)"); c.number_format = PCT2
            DW.cell(row=r, column=7, value=f"=LEFT(A{r},8)")
            DW.cell(row=r, column=8, value=f"=LEFT(A{r},2)")
            DW.cell(row=r, column=9, value=f"=LEFT(A{r},4)")
        n10 = len(rows)
    else:
        put(DW, DROW, 1, "HTS10 rows not yet loaded. Paste dataweb_canada_hts10_2025.csv (columns hts10, customs_value, calc_duty, dutiable_value) into A17:D, with HTS10 as text; columns G-H fill themselves when copied down. Every other tab switches to exact HTS matching automatically.", FI)
        DW.cell(row=DROW, column=1).alignment = Alignment(wrap_text=False)
    LAST = max(DROW + n10 - 1, DROW + 25000)
    put(DW, 4, 7, "HTS10 lines loaded", FB); put(DW, 5, 7, f"=COUNT(B{DROW}:B{LAST})", F)
    put(DW, 4, 8, "Sum check", FB); put(DW, 5, 8, f"=IF(G5>0,SUM(B{DROW}:B{LAST})/B5,0)", F, '0.000')
    put(DW, 6, 7, "Exact HTS matching on?", FB); put(DW, 7, 7, '=IF(G5>1000,"Yes","No - HS6 fallback")', FB)
    DWV = f"'DataWeb data'!$B${DROW}:$B${LAST}"; DWD = f"'DataWeb data'!$C${DROW}:$C${LAST}"
    DWA = f"'DataWeb data'!$A${DROW}:$A${LAST}"; DW8 = f"'DataWeb data'!$G${DROW}:$G${LAST}"
    EXACT = "'DataWeb data'!$G$5>1000"
    DWH = f"'DataWeb data'!$H${DROW}:$H${LAST}"; DW4 = f"'DataWeb data'!$I${DROW}:$I${LAST}"
    if n10:
        for col in "BCD":
            c = DW[f"{col}5"]; c.value = f"=SUM({col}{DROW}:{col}{LAST})"; c.font = F
        DW["A8"].value = f"Row 5 = SUM of the {n10:,} HTS10 rows below. Rows 6-7 from DataWeb monthly totals. H5 checks the HTS10 sum against the sum of the 12 monthly 2025 totals ({X['y_monthly_val']:,.0f})."
        DW["H5"].value = f"=IF(G5>0,SUM(B{DROW}:B{LAST})/{X['y_monthly_val']},0)"
    def dwsum(hs4s, fallback):
        s4 = "+".join(f'SUMIFS({DWV},{DW4},"{h}")' for h in hs4s)
        return f"=IF({EXACT},{s4},{fallback})"

    # ======================= Inputs (shared) =======================
    IN = wb.create_sheet("Inputs")
    IN.column_dimensions["A"].width = 64; IN.column_dimensions["B"].width = 18; IN.column_dimensions["C"].width = 95
    title(IN, "Shared inputs (yellow = change me)")
    header(IN, 3, ["Input", "Value", "Source / note"])
    inputs = [
        ("tot", "U.S. imports from Canada, 2025, customs value (US$)", "='DataWeb data'!B5", USD, "Link: DataWeb tab", True),
        ("duty", "Calculated duty on imports from Canada, 2025 (US$)", "='DataWeb data'!C5", USD, "Link: DataWeb tab", True),
        ("base", f"Realized pre-Section-338 base rate ({X['base_label']})", "='DataWeb data'!E6", PCT2, "Link: DataWeb tab (base month set in config.BASE_MONTH).", True),
        ("boc", "Statutory base rate before Section 338 (Bank of Canada)", C.STATUTORY_BASE_RATE, PCT, "Bank of Canada, MPR July 2026, tariff assumptions", False),
        ("r338", "Section 338 tariff rate", C.SECTION_338_RATE, PCT, "Proclamations of July 20, 2026; in force Aug 22, 2026; no CUSMA exemption", False),
        ("off", "Officially cited value under Section 338 (US$)", C.OFFICIAL_COVERAGE_USD, USD, "U.S. tariffs on about US$20bn of Canadian goods (CRS R49349; Al Jazeera Aug 22, 2026)", False),
        ("offban", "Officially cited value of banned goods (US$)", C.OFFICIAL_BANNED_USD, USD, "CRS R49349: about US$967 million", False),
        ("thr", "Threatened rate from Jan 1, 2027 (vehicles, trucks, parts, steel derivatives)", C.THREAT_RATE, PCT, "Presidential social-media post, Aug 24, 2026; no proclamation yet", False),
        ("c232", "Current Section 232 rate on Canadian vehicles (non-U.S. content)", C.CURRENT_232_VEHICLES, PCT, "Trade Commissioner Service, U.S. tariff measures (Sep 28, 2026)", False),
        ("usc", "U.S. content share of Canadian-built vehicles", C.US_CONTENT_SHARE, PCT, "ASSUMPTION. 25% Section 232 applies to non-U.S. content. Test 30%-60%.", False),
        ("v8703", "Imports of passenger vehicles, HS 8703 (US$)", dwsum(["8703"], 25120838880), USD, "DataWeb HTS10 sum (falls back to UN Comtrade 2025: US$25.12bn)", True),
        ("v8704", "Imports of trucks, HS 8704 (US$)", dwsum(["8704"], 5630053152), USD, "DataWeb HTS10 sum (fallback UN Comtrade US$5.63bn)", True),
        ("v8701", "Imports of tractors incl. road tractors, HS 8701 (US$)", dwsum(["8701"], 320582518), USD, "DataWeb HTS10 sum (fallback UN Comtrade US$0.32bn)", True),
        ("v8708", "Imports of auto parts, HS 8708 (US$)", dwsum(["8708"], 10790609727), USD, "DataWeb HTS10 sum (fallback UN Comtrade US$10.79bn)", True),
        ("cus8708", "CUSMA claim share, HS 8708", "='DataWeb data'!B13", PCT, "Link: DataWeb tab. CUSMA parts are currently exempt from Section 232.", False),
        ("cpart", "Section 232 rate now on non-CUSMA parts", C.CURRENT_232_NONCUSMA_PARTS, PCT, "Section 232 autos and parts proclamation", False),
        ("vsteel", "Imports of steel derivative products, Canada (US$)", f'=IF({EXACT},SUMIFS({DWV},{DWH},"73"),6.5e9)', USD, "Proxy: DataWeb sum of HS chapter 73 (articles of iron or steel); fallback estimate US$6.5bn. CRS IN12519: Canada steel US$4.54bn, aluminum US$7.53bn (excl. derivatives).", True),
        ("csteel", "Current effective Section 232 rate on Canadian steel derivatives", C.CURRENT_232_STEEL_DERIV, PCT, "ESTIMATE. CUSMA-qualifying: 25% on non-U.S. content, floor 15%; non-qualifying Annex I-A at 50% (CRS IN12519, Sep 2026).", False),
    ]
    IR = {}
    for i, (key, lab, val, fmt, src, link) in enumerate(inputs, 4):
        put(IN, i, 1, lab)
        c = put(IN, i, 2, val, FGREEN if link else FBLUE, fmt, None if link else YFILL)
        put(IN, i, 3, src, F, wrap=True)
        IR[key] = f"Inputs!$B${i}"

    # ======================= New HTS codes =======================
    L = wb.create_sheet("New HTS codes", 2)
    title(L, "HTS lines under the new, higher U.S. tariffs on Canada (Section 338) and the September 29 import bans",
          "Annex lines transcribed from White House proclamation annexes. Exact values: SUMIFS of DataWeb HTS10 rows on the 8- or 10-digit line. HS6 value is the containing 6-digit code (fallback only).")
    cols = ["HTS line", "Digits", "HS6", "July 20 annex", "Sep 15 change", "Under 50% tariff now", "Banned from Sep 29",
            "Sector", "Sign in coverage", "2025 value, exact (US$)", "2025 duty paid, exact (US$)", "Realized rate 2025", "HS6 value (US$)"]
    header(L, 4, cols, [14, 7, 9, 18, 26, 12, 11, 34, 10, 18, 18, 11, 17])

    SECTORS = [((1, 21), "Food, dairy, plants and agri-products"), ((22, 22), "Beverages and alcohol"),
               ((23, 38), "Minerals and chemicals"), ((39, 40), "Plastics and rubber"), ((41, 43), "Leather, hides and fur"),
               ((44, 46), "Wood products"), ((47, 49), "Pulp, paper and printed matter"), ((50, 67), "Textiles, apparel and footwear"),
               ((68, 71), "Stone, glass and jewellery"), ((72, 83), "Base metals and metal products"),
               ((84, 85), "Machinery and electrical equipment"), ((86, 89), "Vehicles, motorcycles and boats"),
               ((90, 92), "Instruments"), ((93, 93), "Arms"), ((94, 94), "Furniture, bedding and lighting"),
               ((95, 96), "Toys and sporting goods"), ((97, 99), "Art, antiques, special")]
    def sector(code):
        ch = int(code[:2])
        for (a, b), n in SECTORS:
            if a <= ch <= b: return n
        return "Other"

    src_jul = {}
    for c in ANNEX_JUL_DAIRY: src_jul[c] = "Dairy"
    for c in ANNEX_JUL_ALCOHOL: src_jul[c] = "Alcoholic beverages"
    for c in ANNEX_JUL_MOTOR: src_jul[c] = "Motor vehicles list"
    sep = {}
    for c in SEP_ADD_MOTOR: sep[c] = "Added (motor vehicles list)"
    for c in SEP_ADD_ALCOHOL: sep[c] = "Added (alcohol list)"
    full_remove = set()
    for c in SEP_REMOVE_MOTOR + SEP_REMOVE_ALCOHOL:
        if len(c.replace(".", "")) == 8:
            sep[c] = "Removed"; full_remove.add(c)
        else:
            sep[c] = "Carved out at 10 digits"
    bans = set(BAN_DAIRY + BAN_ALCOHOL + BAN_MOTOR)
    allcodes = sorted(set(src_jul) | set(sep) | bans, key=lambda x: x.replace(".", ""))
    R0 = 5
    for k, c in enumerate(allcodes):
        r = R0 + k
        d = c.replace(".", ""); h = d[:6]
        listed = ((c in src_jul) or sep.get(c, "").startswith("Added")) and c not in full_remove and not sep.get(c, "").startswith("Carved")
        carve = sep.get(c, "").startswith("Carved")
        sign = 1 if listed else (-1 if carve else 0)
        vals = [c, len(d), h, src_jul.get(c, ""), sep.get(c, ""), "Yes" if listed else "No", "Yes" if c in bans else "No", sector(h), sign]
        for j, x in enumerate(vals, 1):
            L.cell(row=r, column=j, value=x).font = F
        L.cell(row=r, column=9).number_format = '0;-0;0'
        crit = f'"{d}"'
        rng = DW8 if len(d) == 8 else DWA
        c1 = L.cell(row=r, column=10, value=f"=SUMIFS({DWV},{rng},{crit})"); c1.font = FGREEN; c1.number_format = USD
        c2 = L.cell(row=r, column=11, value=f"=SUMIFS({DWD},{rng},{crit})"); c2.font = FGREEN; c2.number_format = USD
        c3 = L.cell(row=r, column=12, value=f"=IF(J{r}>0,K{r}/J{r},0)"); c3.number_format = PCT2
        c4 = L.cell(row=r, column=13, value=f"=IFERROR(INDEX('HS6 values'!$C:$C,MATCH(C{r},'HS6 values'!$A:$A,0)),0)"); c4.font = FGREEN; c4.number_format = USD
    RL = R0 + len(allcodes) - 1
    put(L, 3, 1, f"{len(allcodes)} lines. Coverage = sum of value x sign (+1 listed, -1 10-digit carve-out inside a listed 8-digit line).", FI)
    # summary block to right
    L.column_dimensions["O"].width = 46; L.column_dimensions["P"].width = 18; L.column_dimensions["Q"].width = 18
    header(L, 4, [], freeze=False)
    for j, t in enumerate(["Summary (exact HTS match)", "Customs value (US$)", "Duty paid 2025 (US$)"], 15):
        c = L.cell(row=4, column=j, value=t); c.font = FH; c.fill = HFILL
    summ = [
        ("Lines under 50% tariff now (net of carve-outs)", f"=SUMPRODUCT(I{R0}:I{RL},J{R0}:J{RL})", f"=SUMPRODUCT(I{R0}:I{RL},K{R0}:K{RL})"),
        ("of which July 20 annex lines", f'=SUMIFS(J{R0}:J{RL},F{R0}:F{RL},"Yes",D{R0}:D{RL},"?*")', f'=SUMIFS(K{R0}:K{RL},F{R0}:F{RL},"Yes",D{R0}:D{RL},"?*")'),
        ("of which September 15 additions", f'=SUMIFS(J{R0}:J{RL},E{R0}:E{RL},"Added*")', f'=SUMIFS(K{R0}:K{RL},E{R0}:E{RL},"Added*")'),
        ("Banned lines (from Sep 29)", f'=SUMIFS(J{R0}:J{RL},G{R0}:G{RL},"Yes")', f'=SUMIFS(K{R0}:K{RL},G{R0}:G{RL},"Yes")'),
        ("Lines removed on Sep 15", f'=SUMIFS(J{R0}:J{RL},E{R0}:E{RL},"Removed")', f'=SUMIFS(K{R0}:K{RL},E{R0}:E{RL},"Removed")'),
    ]
    for i, (lab, f1, f2) in enumerate(summ, 5):
        put(L, i, 15, lab); put(L, i, 16, f1, F, USD); put(L, i, 17, f2, F, USD)
    put(L, 10, 15, "Lines under tariff now", FB); put(L, 10, 16, f'=COUNTIF(F{R0}:F{RL},"Yes")')
    put(L, 11, 15, "Banned lines", FB); put(L, 11, 16, f'=COUNTIF(G{R0}:G{RL},"Yes")')
    LCOV = "'New HTS codes'!$P$5"; LBAN = "'New HTS codes'!$P$8"; LJUL = "'New HTS codes'!$P$6"

    # ======================= HS6 values =======================
    H = wb.create_sheet("HS6 values")
    header(H, 1, ["HS6", "Sector", "U.S. imports from Canada 2025 (US$)", "Listed lines now", "Listed in July annexes", "Banned lines",
                  "Value under tariff now (US$)", "Value under July lists (US$)", "Value banned (US$)"], [9, 34, 20, 11, 12, 10, 20, 20, 18])
    hs_sorted = sorted(v)
    for r, h in enumerate(hs_sorted, 2):
        put(H, r, 1, h); put(H, r, 2, sector(h)); put(H, r, 3, v[h], FBLUE, USD)
        put(H, r, 4, f"=COUNTIFS('New HTS codes'!$C:$C,A{r},'New HTS codes'!$F:$F,\"Yes\")")
        put(H, r, 5, f"=COUNTIFS('New HTS codes'!$C:$C,A{r},'New HTS codes'!$D:$D,\"?*\")")
        put(H, r, 6, f"=COUNTIFS('New HTS codes'!$C:$C,A{r},'New HTS codes'!$G:$G,\"Yes\")")
        for col, s in ((7, "D"), (8, "E"), (9, "F")):
            put(H, r, col, f"=IF({s}{r}>0,C{r},0)", F, USD)
    NH = len(hs_sorted) + 1; HT = NH + 2
    put(H, HT, 1, "Total", FB)
    for col in (3, 7, 8, 9):
        Lc = get_column_letter(col); put(H, HT, col, f"=SUM({Lc}2:{Lc}{NH})", FB, USD)
    put(H, HT + 1, 1, "Source: UN Comtrade public API, U.S.-reported imports from Canada, 2025. HS6 values overstate coverage because a 6-digit code can hold unlisted 8-digit lines; the Calculated tariff rate tab calibrates for this.", FI)

    # ======================= Calculated tariff rate =======================
    E = wb.create_sheet("Calculated tariff rate", 3)
    title(E, "Current trade-weighted effective U.S. tariff rate on Canadian goods (measures in force, October 2026)")
    for col, w in zip("ABCD", [66, 18, 18, 80]): E.column_dimensions[col].width = w
    header(E, 3, ["Step", "Realized (central)", "Statutory (upper)", "Logic"])
    exact = EXACT
    rows = [
        ("U.S. imports from Canada, 2025 (US$)", f"={IR['tot']}", f"={IR['tot']}", "DataWeb customs value", USD),                       # 4
        ("Base rate before Section 338", f"={IR['base']}", f"={IR['boc']}", f"Realized: DataWeb {X['base_label']}. Statutory: Bank of Canada.", PCT2),  # 5
        ("Current-list value, exact HTS match (US$)", f"={LCOV}", f"={LCOV}", "New HTS codes tab; zero until HTS10 rows are loaded", USD),  # 6
        ("Current-list value, HS6 match (US$)", f"='HS6 values'!G{HT}", f"='HS6 values'!G{HT}", "HS6 values tab", USD),  # 7
        ("Calibration factor (official US$20bn / July-list HS6 value)", f"={IR['off']}/'HS6 values'!H{HT}", "=1", "HS6 fallback only; statutory keeps full HS6 value", '0.000'),  # 8
        ("Covered value used (US$)", f"=IF({exact},B6,B7*B8)", f"=IF({exact},C6,C7*C8)", "Exact HTS value when loaded, else calibrated HS6", USD),  # 9
        ("Share of all imports from Canada", "=B9/B4", "=C9/C4", "", PCT2),  # 10
        ("Section 338 increment (pp)", f"=B10*{IR['r338']}", f"=C10*{IR['r338']}", "50% x covered share (static weights)", PCT2),  # 11
        ("CALCULATED CURRENT RATE", "=B5+B11", "=C5+C11", "Feeds the scenario tabs as the starting point", PCT2),  # 12
        ("", None, None, "", None),
        ("Checks", None, None, "", None),
        (f"Realized rate, {X['latest_label']} (latest month)", "='DataWeb data'!E7", None, "Should move toward the calculated rate as Section 338 takes full effect", PCT2),  # 15
        (f"Implied rate if Section 338 applied {X['frac338']:.2f} of {X['latest_label']}", f"=B5+B11*{X['frac338']}", None, "Compare with the row above", PCT2),  # 16
        ("Global Trade Alert, rate in force before Jan 2027 (statutory)", None, C.GTA_BENCHMARKS["current"], "Global Trade Alert, Aug 25, 2026", PCT),  # 17
        ("Bank of Canada 5.0% + ATB estimate of Section 338 (+2.5pp)", None, C.ATB_STATUTORY_ESTIMATE, "ATB Financial, Aug 2026", PCT),  # 18
        ("Banned value, exact HTS (US$)", f"={LBAN}", None, "Compare CRS: about US$967 million", USD),  # 19
        ("Earlier HS6-basis statutory estimate (the previous 8.48%)", None, f"=C5+{IR['r338']}*C7/C4", "Same formula with the HS6 value (US$26.59bn) instead of exact HTS (US$20.26bn). HS6 codes include unlisted 8-digit lines, so this overstated coverage.", PCT2),
        ("Exact HTS coverage vs official US$20bn", f"=B6/{IR['off']}", None, "Exact match lands within about 1% of the officially cited coverage", '0.000'),
    ]
    for col, w in zip("DEFGH", [44, 44, 52, 52, 60]): E.column_dimensions[col].width = w
    header(E, 3, ["Step", "Realized (central)", "Statutory (upper)", "Excel formula in column B", "Excel formula in column C",
                  "Worked numbers, realized (live)", "Worked numbers, statutory (live)", "Logic"])
    DWC6 = "'DataWeb data'!C6"; DWB6 = "'DataWeb data'!B6"; HSH = f"'HS6 values'!H{HT}"
    def wk(col, r):
        """Live worked-number strings for each step; col = 'B' or 'C'."""
        bn = lambda ref: f'TEXT({ref}/1e9,"$#,##0.00")&"bn"'
        pc = lambda ref: f'TEXT({ref},"0.00%")'
        m = {
            4: f'="Total 2025 = "&{bn(col+"4")}',
            5: (f'="{X["base_label"]} duty "&{bn(DWC6)}&" / imports "&{bn(DWB6)}&" = "&{pc("B5")}' if col == "B"
                else f'="Bank of Canada statutory base = "&{pc("C5")}'),
            6: f'="Sum of value x sign over listed HTS lines = "&{bn(col+"6")}',
            7: f'="Sum of HS6 codes holding a listed line = "&{bn(col+"7")}',
            8: (f'="US$20bn official / "&{bn(HSH)}&" = "&TEXT(B8,"0.000")' if col == "B" else '="1 (no calibration)"'),
            9: f'=IF({EXACT},"Exact HTS = "&{bn(col+"6")},{bn(col+"7")}&" x "&TEXT({col}8,"0.000")&" = "&{bn(col+"9")})',
            10: f'={bn(col+"9")}&" / "&{bn(col+"4")}&" = "&{pc(col+"10")}',
            11: f'={pc(col+"10")}&" x "&TEXT({IR["r338"]},"0%")&" = "&{pc(col+"11")}',
            12: f'={pc(col+"5")}&" + "&{pc(col+"11")}&" = "&{pc(col+"12")}',
            13: f'={pc(col+"5")}&" + "&TEXT({IR["r338"]},"0%")&" x "&{bn(col+"9")}&" / "&{bn(col+"4")}&" = "&{pc(col+"13")}',
        }
        return m.get(r)
    FCODE = Font(name="Courier New", size=9, color="404040")
    def ftxt(ws, r, c, s):
        cell = ws.cell(row=r, column=c); cell.value = s; cell.data_type = 's'; cell.font = FCODE
        return cell
    rows.insert(9, ("One-line formula (same result as row 12)", f"=B5+{IR['r338']}*B9/B4", f"=C5+{IR['r338']}*C9/C4",
                    "Base + 50% x covered value / total imports", PCT2))
    for i, (lab, b, c_, note, fmt) in enumerate(rows, 4):
        bold = lab.isupper() or lab == "Checks"
        put(E, i, 1, lab, FB if bold else F)
        for col, fx in ((2, b), (3, c_)):
            if fx is not None:
                cell = put(E, i, col, fx, FBLUE if isinstance(fx, float) else F, fmt)
                if isinstance(fx, float): cell.fill = YFILL
                if bold: cell.font = FB; cell.fill = KFILL
        if isinstance(b, str): ftxt(E, i, 4, b)
        if isinstance(c_, str): ftxt(E, i, 5, c_)
        if i <= 13:
            if b is not None and wk("B", i): put(E, i, 6, wk("B", i))
            if c_ is not None and wk("C", i): put(E, i, 7, wk("C", i))
        put(E, i, 8, note)
    put(E, 21, 7, f'=TEXT(C5,"0.00%")&" + "&TEXT({IR["r338"]},"0%")&" x "&TEXT(C7/1e9,"$#,##0.00")&"bn / "&TEXT(C4/1e9,"$#,##0.00")&"bn = "&TEXT(C21,"0.00%")')
    put(E, 22, 6, f'=TEXT(B6/1e9,"$#,##0.00")&"bn / US$20bn = "&TEXT(B22,"0.000")')
    put(E, 2, 1, "Columns D-E show the formula behind each number; columns F-G show the same calculation with the live numbers plugged in.", FI)
    CUR_R = "'Calculated tariff rate'!$B$12"; CUR_S = "'Calculated tariff rate'!$C$12"

    # ======================= Scenario tabs =======================
    def scen_sheet(name, letter, desc, comps, prev, gta, prob_ref):
        S = wb.create_sheet(name)
        title(S, f"Scenario {letter}: {desc}", "Average (trade-weighted) effective U.S. tariff rate on Canadian goods if this happens. Static 2025 weights. Columns I-L show each formula and the live numbers behind it.")
        for col, w in zip("ABCDEFGHIJKL", [52, 18, 12, 12, 12, 18, 18, 46, 34, 60, 30, 46]): S.column_dimensions[col].width = w
        header(S, 4, ["Component", "2025 value (US$)", "Affected share", "Rate now", "Rate after", "Added duty, realized (US$)", "Added duty, statutory (US$)", "Basis",
                      "Excel formula, realized (col F)", "Worked numbers, realized (live)", "Excel formula, statutory (col G)", "Worked numbers, statutory (live)"])
        bn = lambda ref: f'TEXT({ref}/1e9,"$#,##0.00")&"bn"'
        pc = lambda ref: f'TEXT({ref},"0.00%")'
        p0 = lambda ref: f'TEXT({ref},"0%")'
        def show(r, fF, wF, fG, wG):
            if fF: ftxt(S, r, 9, fF)
            if wF: put(S, r, 10, wF)
            if fG: ftxt(S, r, 11, fG)
            if wG: put(S, r, 12, wG)
        r = 5
        for (lab, val, share, now, after, stat_share, note) in comps:
            put(S, r, 1, lab); put(S, r, 2, val, FGREEN, USD); put(S, r, 3, share, F, PCT)
            put(S, r, 4, now, FGREEN, PCT); put(S, r, 5, after, FGREEN, PCT)
            fF = f"=B{r}*C{r}*(E{r}-D{r})"; fG = f"=B{r}*{stat_share}"
            put(S, r, 6, fF, F, USD); put(S, r, 7, fG, F, USD)
            put(S, r, 8, note, F, wrap=True)
            wF = f'={bn("B"+str(r))}&" x "&{p0("C"+str(r))}&" x ("&{p0("E"+str(r))}&" - "&{p0("D"+str(r))}&") = "&{bn("F"+str(r))}'
            wG = f'={bn("B"+str(r))}&" x "&TEXT({stat_share},"0%")&" = "&{bn("G"+str(r))}'
            show(r, fF + "   [value x affected share x (rate after - rate now)]", wF, fG, wG)
            r += 1
        last = r - 1
        r += 1
        put(S, r, 1, "Added duty, this scenario's components", FB); put(S, r, 6, f"=SUM(F5:F{last})", FB, USD); put(S, r, 7, f"=SUM(G5:G{last})", FB, USD); add_r = r
        show(r, f"=SUM(F5:F{last})", f'="Sum = "&{bn("F"+str(r))}', f"=SUM(G5:G{last})", f'="Sum = "&{bn("G"+str(r))}')
        r += 1
        put(S, r, 1, "Increment from these components (pp)", FB); put(S, r, 6, f"=F{add_r}/{IR['tot']}", FB, PCT2); put(S, r, 7, f"=G{add_r}/{IR['tot']}", FB, PCT2); inc_r = r
        show(r, f"=F{add_r}/{IR['tot']}", f'={bn("F"+str(add_r))}&" / "&{bn(IR["tot"])}&" = "&{pc("F"+str(r))}',
             f"=G{add_r}/{IR['tot']}", f'={bn("G"+str(add_r))}&" / "&{bn(IR["tot"])}&" = "&{pc("G"+str(r))}')
        r += 2
        header(S, r, ["Rate build-up", "", "", "", "", "Realized (central)", "Statutory (upper)", "", "Excel formula, realized", "Worked numbers, realized", "Excel formula, statutory", "Worked numbers, statutory"], freeze=False); r += 1
        put(S, r, 1, "Calculated current rate"); put(S, r, 6, f"={CUR_R}", FGREEN, PCT2); put(S, r, 7, f"={CUR_S}", FGREEN, PCT2); start = r
        show(r, f"={CUR_R}", f'="Today (Calculated tariff rate tab) = "&{pc("F"+str(r))}', f"={CUR_S}", f'="Today (Calculated tariff rate tab) = "&{pc("G"+str(r))}'); r += 1
        if prev:
            put(S, r, 1, f"Plus earlier scenario components ({prev[0]})"); put(S, r, 6, f"='{prev[0]}'!F{prev[1]}", FGREEN, PCT2); put(S, r, 7, f"='{prev[0]}'!G{prev[1]}", FGREEN, PCT2)
            show(r, f"='{prev[0]}'!F{prev[1]}", f'="From {prev[0]} = "&{pc("F"+str(r))}', f"='{prev[0]}'!G{prev[1]}", f'="From {prev[0]} = "&{pc("G"+str(r))}'); r += 1
        put(S, r, 1, "Plus this scenario's components"); put(S, r, 6, f"=F{inc_r}", F, PCT2); put(S, r, 7, f"=G{inc_r}", F, PCT2)
        show(r, f"=F{inc_r}", None, f"=G{inc_r}", None); r += 1
        put(S, r, 1, "Total increment over today (pp)", FB); put(S, r, 6, f"=SUM(F{start+1}:F{r-1})", FB, PCT2); put(S, r, 7, f"=SUM(G{start+1}:G{r-1})", FB, PCT2); tot_inc = r
        show(r, f"=SUM(F{start+1}:F{r-1})", None, f"=SUM(G{start+1}:G{r-1})", None); r += 1
        put(S, r, 1, f"AVERAGE TARIFF RATE, SCENARIO {letter}", FB)
        for col in (6, 7):
            c = put(S, r, col, f"={get_column_letter(col)}{start}+{get_column_letter(col)}{tot_inc}", FB, PCT2); c.fill = KFILL
        show(r, f"=F{start}+F{tot_inc}", f'={pc("F"+str(start))}&" + "&{pc("F"+str(tot_inc))}&" = "&{pc("F"+str(r))}',
             f"=G{start}+G{tot_inc}", f'={pc("G"+str(start))}&" + "&{pc("G"+str(tot_inc))}&" = "&{pc("G"+str(r))}')
        rate_r = r; r += 2
        put(S, r, 1, "Probability (Scenario probabilities tab)"); put(S, r, 6, f"={prob_ref}", FGREEN, PCT); prob_r = r; r += 1
        put(S, r, 1, "External benchmark: Global Trade Alert (statutory)"); put(S, r, 7, gta, FBLUE, PCT) if gta is not None else put(S, r, 7, "n/a"); r += 1
        return S, tot_inc, rate_r

    vehicles = f"({IR['v8703']}+{IR['v8704']}+{IR['v8701']})"
    compA = [("Cars, trucks and tractors (HS 8703, 8704, 8701), non-U.S. content", f"={vehicles}", f"=1-{IR['usc']}", f"={IR['c232']}", f"={IR['thr']}",
              f"({IR['thr']}-{IR['c232']})", "Section 232 auto rate 25% -> 50% on non-U.S. content. Statutory: +25pp on full value.")]
    compB = [("Auto parts entered under CUSMA (now exempt)", f"={IR['v8708']}", f"={IR['cus8708']}", "=0", f"={IR['thr']}", f"{IR['thr']}", "Exemption removed; 50% on CUSMA parts. Statutory: 50% on full HS 8708 value."),
             ("Auto parts not entered under CUSMA (25% now)", f"={IR['v8708']}", f"=1-{IR['cus8708']}", f"={IR['cpart']}", f"={IR['thr']}", "0", "25% -> 50%. Already in statutory row above.")]
    compC = [("Steel derivative products", f"={IR['vsteel']}", "=1", f"={IR['csteel']}", f"={IR['thr']}", f"({IR['thr']}-{IR['csteel']})", "Effective 232 rate ~25% -> 50%. Value is an estimate (Inputs tab).")]

    SA, A_inc, A_rate = scen_sheet("Scenario A", "A", "cars and trucks to 50%, CUSMA parts stay exempt", compA, None, C.GTA_BENCHMARKS["A"], "'Scenario probabilities'!$C$6")
    SB, B_inc, B_rate = scen_sheet("Scenario B", "B", "Scenario A + auto parts to 50% (CUSMA parts exemption removed)", compB, ("Scenario A", A_inc), C.GTA_BENCHMARKS["B"], "'Scenario probabilities'!$C$7")
    SC, C_inc, C_rate = scen_sheet("Scenario C", "C", "Scenario B + steel derivatives to 50% (full August 24 threat)", compC, ("Scenario B", B_inc), None, "'Scenario probabilities'!$C$8")

    # ======================= Scenario probabilities =======================
    P = wb.create_sheet("Scenario probabilities")
    title(P, "Probability of each scenario being in force by end of Q1 2027", "Judgmental, anchored on prediction markets, the follow-through record on tariff threats, and industry signals. Yellow cells drive everything.")
    for col, w in zip("ABCDEFGH", [44, 16, 14, 16, 16, 16, 16, 70]): P.column_dimensions[col].width = w
    header(P, 4, ["Outcome", "Conditional on an increase", "Probability", "Rate, realized", "Rate, statutory", "Cumulative probability", "Percentile band", "What it means"], freeze=False)
    put(P, 5, 1, "No January increase (status quo or deal)")
    put(P, 5, 3, "=1-B12", F, PCT); put(P, 5, 4, f"={CUR_R}", FGREEN, PCT2); put(P, 5, 5, f"={CUR_S}", FGREEN, PCT2)
    put(P, 5, 8, "Threat not implemented, delayed past Q1, or traded away in a deal. Today's rate holds (or falls with a deal).", F, wrap=True)
    scen = [("Scenario A: vehicles to 50%", C.CONDITIONAL_SPLIT["A"], A_rate, "Most likely form if implemented: vehicles only, parts exemption extended (the post named parts, but the CUSMA parts exemption has been extended before)."),
            ("Scenario B: + parts to 50%", C.CONDITIONAL_SPLIT["B"], B_rate, "Parts exemption lapses. Global Automakers of Canada publicly doubt the exemption will be extended."),
            ("Scenario C: + steel derivatives to 50%", C.CONDITIONAL_SPLIT["C"], C_rate, "Full threat as posted on Aug 24.")]
    for i, (lab, cond, rr, note) in enumerate(scen, 6):
        put(P, i, 1, lab); put(P, i, 2, cond, FBLUE, PCT, YFILL); put(P, i, 3, f"=$B$12*B{i}", F, PCT)
        sh = ["Scenario A", "Scenario B", "Scenario C"][i - 6]
        put(P, i, 4, f"='{sh}'!F{rr}", FGREEN, PCT2); put(P, i, 5, f"='{sh}'!G{rr}", FGREEN, PCT2); put(P, i, 8, note, F, wrap=True)
    for i in range(5, 9):
        put(P, i, 6, f"=SUM($C$5:C{i})", F, PCT)
        put(P, i, 7, f'=TEXT(F{i}-C{i},"0%")&" - "&TEXT(F{i},"0%")')
    put(P, 9, 1, "Check: probabilities sum to 100%", FI); put(P, 9, 3, "=SUM(C5:C8)", F, PCT); put(P, 9, 2, "=SUM(B6:B8)", F, PCT)
    put(P, 10, 1, "PROBABILITY-WEIGHTED RATE", FB)
    for col in ("D", "E"):
        c = put(P, 10, " DE".index(col) + 3, f"=SUMPRODUCT($C$5:$C$8,{col}5:{col}8)", FB, PCT2); c.fill = KFILL
    P.column_dimensions["I"].width = 60
    for k, (col, lab) in enumerate((("D", "Realized"), ("E", "Statutory"))):
        parts = '&" + "&'.join(f'TEXT(C{j},"0%")&" x "&TEXT({col}{j},"0.00%")' for j in range(5, 9))
        put(P, 10 + k, 8, f'="{lab}: "&' + parts + f'&" = "&TEXT({col}10,"0.00%")', F)
    ftxt(P, 10, 9, "=SUMPRODUCT($C$5:$C$8,D5:D8)   [sum of probability x rate]")
    put(P, 12, 1, "P(any January 2027 increase in force by end-Q1 2027)", FB); put(P, 12, 2, C.P_ANY_INCREASE, FBLUE, PCT, YFILL)
    put(P, 12, 8, "Central 30%. Range 20%-40% (see evidence). Test sensitivity here.", F, wrap=True)

    put(P, 14, 1, "Mapping to Moody's scenarios (from the cumulative distribution)", FB)
    header(P, 15, ["Moody's scenario", "Percentile", "Outcome at that percentile", "Rate, realized", "Rate, statutory", "", "", "Reading"], freeze=False)
    mp = sorted([(k, v) for k, v in C.MOODYS_PERCENTILES.items() if k != "S1"], key=lambda x: x[1])
    for i, (nm, pc) in enumerate(mp, 16):
        put(P, i, 1, nm); put(P, i, 2, pc, F, '0%')
        put(P, i, 3, f"=INDEX($A$5:$A$8,MATCH(TRUE,INDEX($F$5:$F$8>=B{i},0),0))")
        put(P, i, 4, f"=INDEX($D$5:$D$8,MATCH(TRUE,INDEX($F$5:$F$8>=B{i},0),0))", F, PCT2)
        put(P, i, 5, f"=INDEX($E$5:$E$8,MATCH(TRUE,INDEX($F$5:$F$8>=B{i},0),0))", F, PCT2)
    put(P, 19, 8, "With central inputs: Baseline = today's rate; S3 (90th) lands on Scenario B; S4 (96th) on Scenario C.", F, wrap=True)

    put(P, 21, 1, "Evidence", FB)
    header(P, 22, ["Source (date accessed)", "Market / finding", "Reading", "", "", "", "", "How it is used"], freeze=False)
    ev = list(C.PROBABILITY_EVIDENCE)
    for i, (s, m, rd, use) in enumerate(ev, 23):
        put(P, i, 1, s, F, wrap=True); put(P, i, 2, m, F, wrap=True)
        if rd is not None: put(P, i, 3, rd, FBLUE, PCT)
        put(P, i, 8, use, F, wrap=True)
    P.column_dimensions["B"].width = 40

    # ======================= Verify 2.6% =======================
    V = wb.create_sheet("Verify 2.6%")
    title(V, "Does the 2.6% realized rate on Canadian goods (2025) agree with other sources?",
          "Verdict: yes. Every source that uses duties collected / import value gets 2.6% for 2025, and the 2026 monthly figures match to within 0.05pp. Sources near 5-9% use statutory rates, a different concept.")
    for col, w in zip("ABCDEFGH", [38, 18, 30, 12, 12, 12, 16, 70]): V.column_dimensions[col].width = w
    header(V, 4, ["Source", "Period", "Measure", "Their figure", "Our figure", "Gap (pp)", "Agrees?", "Comment"])
    ver = verify_rows(X, CUR_S)
    for i, (s, per, meas, theirs, ours, cm) in enumerate(ver, 5):
        put(V, i, 1, s); put(V, i, 2, per); put(V, i, 3, meas, F, wrap=True)
        fmt = BN if s.startswith("UN Comtrade") else PCT2
        put(V, i, 4, theirs, FBLUE if isinstance(theirs, float) else FGREEN, fmt)
        if ours is not None:
            put(V, i, 5, ours, FBLUE if isinstance(ours, float) else FGREEN, fmt)
            if s.startswith("UN Comtrade"):
                put(V, i, 6, f"=E{i}/D{i}-1", F, PCT2); put(V, i, 7, f'=IF(ABS(F{i})<0.005,"Yes","No")')
            elif s.startswith("Global Trade"):
                put(V, i, 6, f"=(E{i}-D{i})*100", F, '0.00'); put(V, i, 7, f'=IF(ABS(F{i})<=1,"Close (within 1pp, statutory vs statutory)","No")')
            elif s.startswith(("Bank of Canada", "Wharton Budget Model")) and "USMCA" not in meas:
                put(V, i, 6, f"=(E{i}-D{i})*100", F, '0.00'); put(V, i, 7, "Different concept")
            elif "USMCA" in meas:
                put(V, i, 6, f"=(E{i}-D{i})*100", F, '0.0'); put(V, i, 7, "Consistent")
            else:
                put(V, i, 6, f"=(E{i}-D{i})*100", F, '0.00'); put(V, i, 7, f'=IF(ABS(F{i})<=0.06,"Yes","No")')
        else:
            put(V, i, 7, "Context")
        put(V, i, 8, cm, F, wrap=True)
    nv = 5 + len(ver) + 1
    put(V, nv, 1, "Why realized (2.6%-3.2%) and statutory (5%-8.5%) differ", FB)
    why = ["1. About 75% of 2025 imports from Canada entered under CUSMA and paid no surcharge; statutory measures apply headline rates to all trade.",
           "2. Energy (about a quarter of imports) carries low or no duty, pulling the realized average down.",
           "3. Section 232 on CUSMA vehicles applies only to non-U.S. content, so duty paid per dollar of vehicle is about half the headline rate.",
           "4. Trade shifts away from tariffed goods (lower weight on high-duty lines) after tariffs take effect.",
           "Implication for Moody's: calibrate scenario tariff inputs on the realized basis if the model's tariff variable is 'duties collected / imports'; use the statutory column if it represents headline rates."]
    for k, t in enumerate(why, nv + 1):
        c = put(V, k, 1, t); c.alignment = Alignment(wrap_text=False)

    # ======================= Sources =======================
    SR = wb.create_sheet("Sources")
    SR.column_dimensions["A"].width = 64; SR.column_dimensions["B"].width = 110
    header(SR, 1, ["Source", "Link"])
    srcs = [
        ("USITC DataWeb, U.S. imports for consumption from Canada (HTS10, 2025; monthly 2026)", "https://dataweb.usitc.gov/"),
        ("White House, Annex I to Proclamation 11047 (dairy), July 2026", "https://www.whitehouse.gov/wp-content/uploads/2026/07/ANNEX-I-1.pdf"),
        ("White House, Annex I to Proclamation 11046 (alcoholic beverages), July 2026", "https://www.whitehouse.gov/wp-content/uploads/2026/07/ANNEX-I-2.pdf"),
        ("White House, Annex I to Proclamation 11048 (motor vehicles list), July 2026", "https://www.whitehouse.gov/wp-content/uploads/2026/07/ANNEX-I-3.pdf"),
        ("White House, scope modification, motor vehicles list, Sep 2026", "https://www.whitehouse.gov/wp-content/uploads/2026/09/ANNEX-I-AUTO.pdf"),
        ("White House, scope modification, alcohol list, Sep 2026", "https://www.whitehouse.gov/wp-content/uploads/2026/09/Alcohol-Scope-Modification-Annex-I.pdf"),
        ("White House, import exclusion, dairy, Sep 2026", "https://www.whitehouse.gov/wp-content/uploads/2026/09/ANNEX-I-DAIRY.pdf"),
        ("White House, import exclusion, alcohol, Sep 2026", "https://www.whitehouse.gov/wp-content/uploads/2026/09/ANNEX-I-ALCOHOL.pdf"),
        ("White House, import exclusion, motor vehicles, Sep 2026", "https://www.whitehouse.gov/wp-content/uploads/2026/09/ANNEX-I-MOTOR-VEHICLES.pdf"),
        ("UN Comtrade public API (U.S. imports from Canada, 2025)", "https://comtradeapi.un.org/public/v1/preview/C/A/HS?reporterCode=842&partnerCode=124&period=2025&flowCode=M"),
        ("USAFacts, average U.S. tariff rate on Canada", "https://usafacts.org/answers/what-is-the-average-us-tariff-rate-overall/countries/canada/"),
        ("RBC, What we know and don't about Section 338 tariffs", "https://www.rbc.com/en/economics/canadian-analysis/featured-analysis/insights/next-chapter-of-u-s-canada-trade-war-what-we-know-and-dont-about-section-338-tariffs/"),
        ("RBC, Canadian exports surged ahead of new U.S. tariffs in August", "https://www.rbc.com/en/economics/canadian-analysis/data-flashes/canadian-exports-surged-ahead-of-new-u-s-tariffs-in-august/"),
        ("RBC, Most Canadian exports to the U.S. remained duty-free in June", "https://www.rbc.com/en/economics/canadian-analysis/featured-analysis/insights/most-canadian-exports-to-the-u-s-remained-duty-free-in-june/"),
        ("Wharton Budget Model, effective tariff rates, Sep 9, 2026", "https://budgetmodel.wharton.upenn.edu/p/2026-09-09-effective-tariff-rates-and-revenues-updated-september-9-2026/"),
        ("Bank of Canada, MPR July 2026, tariff assumptions", "https://www.bankofcanada.ca/publications/mpr/mpr-2026-07-15/tariff-assumptions/"),
        ("Global Trade Alert, Canada: Section 232 at 50% scenarios, Aug 25, 2026", "https://globaltradealert.org/blog/canada-s232-50pct-scenarios"),
        ("Congressional Research Service, R49349, Sep 14, 2026", "https://www.everycrsreport.com/reports/R49349.html"),
        ("Congressional Research Service, IN12519, Section 232 tariffs on steel and aluminum, Sep 17, 2026", "https://www.everycrsreport.com/files/2026-09-17_IN12519_8d8b2b79a208aac182ae6214a1cc7846896bee4e.html"),
        ("Kalshi, Canada accepts a U.S. trade deal", "https://kalshi.com/markets/kxcanusdeal/canada-accepts-a-us-trade-deal/kxcanusdeal-26"),
        ("Polymarket, U.S.-Canada trade war markets", "https://polymarket.com/predictions/us-canada-trade-war"),
        ("Treasury & Risk, Trump carries out one in four tariff threats, Jan 27, 2026", "https://www.treasuryandrisk.com/amp/2026/01/27/trump-carries-out-one-in-four-tariff-threats/"),
        ("Trade Commissioner Service, U.S. tariff measures, Sep 28, 2026", "https://www.tradecommissioner.gc.ca/en/market-industry-info/search-country-region/country/canada-united-states-export/us-tariffs/supporting-exporters-through-tariff-challenges.html"),
    ]
    for i, (a, b) in enumerate(srcs, 2):
        put(SR, i, 1, a); put(SR, i, 2, b)

    order = ["Read me", "DataWeb data", "New HTS codes", "Calculated tariff rate", "Scenario A", "Scenario B", "Scenario C",
             "Scenario probabilities", "Verify 2.6%", "Inputs", "HS6 values", "Sources"]
    wb._sheets = [wb[n] for n in order]
    wb.calculation.fullCalcOnLoad = True   # Excel recalculates every formula on open
    wb.save(OUT)
    print("saved", OUT, "hts10 rows", n10, "annex lines", len(allcodes))


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "data", sys.argv[2] if len(sys.argv) > 2 else "Canada_US_Tariff_Scenarios_2026.xlsx")
