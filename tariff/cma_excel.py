"""Formatted Excel workbook of the Ontario CMA results (Ontario_CMA_Tariff_Results.xlsx)."""
import os

import pandas as pd
from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.formatting.rule import DataBarRule, ColorScaleRule
from openpyxl.styles import Alignment, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from . import cma, model


def build(data_dir, out_path):
    D = data_dir
    OUT = out_path
    R = model.run(D)
    h, _, _, _ = model.load_data(D)
    U = R["summary"]["usmca_8708"]
    CR = cma.run(h, D, U)
    SENS = {s: cma.run(h, D, U, sigma=s)["cma"].set_index("geo") for s in (1.0, 2.0, 4.0)}
    names = pd.read_csv(os.path.join(D, "naics2017_names.csv"), dtype=str).set_index("code")["desc"].to_dict()

    AR = "Arial"
    F = Font(name=AR, size=10); FB = Font(name=AR, size=10, bold=True); FT = Font(name=AR, size=14, bold=True)
    FH = Font(name=AR, size=10, bold=True, color="FFFFFF"); FI = Font(name=AR, size=9, italic=True, color="595959")
    FBLUE = Font(name=AR, size=10, color="0000FF"); FGREEN = Font(name=AR, size=10, color="008000")
    HF = PatternFill("solid", fgColor="1F3864"); SUB = PatternFill("solid", fgColor="D9E1F2")
    YF = PatternFill("solid", fgColor="FFFF00"); TOT = PatternFill("solid", fgColor="F2F2F2")
    thin = Side(style="thin", color="BFBFBF")
    USD = '$#,##0.00,,,"bn";($#,##0.00,,,"bn");"-"'; USDM = '$#,##0,,"m";($#,##0,,"m");"-"'
    PCT1 = '0.0%;(0.0%);"-"'; PCT2 = '0.00%;(0.00%);"-"'; INT = '#,##0;(#,##0);"-"'

    wb = Workbook()


    def hdr(ws, row, cols, start=1, fill=HF, font=FH, height=30):
        for i, c in enumerate(cols, start):
            x = ws.cell(row=row, column=i, value=c); x.font = font; x.fill = fill
            x.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
        ws.row_dimensions[row].height = height


    def put(ws, r, c, v, font=F, fmt=None, fill=None):
        x = ws.cell(row=r, column=c, value=v); x.font = font
        if fmt: x.number_format = fmt
        if fill: x.fill = fill
        return x


    def widths(ws, ws_w):
        for i, w in enumerate(ws_w, 1):
            ws.column_dimensions[get_column_letter(i)].width = w


    # ------------------------------------------------------------------ Read me
    RM = wb.active; RM.title = "Read me"; RM.column_dimensions["A"].width = 130
    lines = [
        ("How U.S. tariffs hit exports from each Ontario CMA", FT),
        ("Built up from 20,131 HTS10 product lines of U.S. imports from Canada (USITC DataWeb, 2025). Prepared October 15, 2026.", FI),
        ("", F),
        ("Tabs", FB),
        ("1. CMA summary: for each CMA, exports to the U.S., the average tariff rate on them, the export loss and manufacturing jobs at risk, today and in Scenarios A, B, C, plus the probability-weighted outcome.", F),
        ("2. Charts: export loss and tariff rate by CMA.", F),
        ("3. Drivers: the industries and HTS product lines behind each CMA's loss.", F),
        ("4. Industries: tariff rate and export loss for each NAICS 4-digit industry, with Ontario's share of its jobs.", F),
        ("5. Sensitivity: export loss and jobs at risk with a weaker (1) or stronger (4) export response.", F),
        ("6. Scenarios: what Today, A, B and C mean, and their probabilities (yellow cells feed the probability-weighted columns).", F),
        ("", F),
        ("Scenarios (cumulative)", FB),
        ("Today: Section 338 50% tariffs and the September 29 import bans, on top of 2025 duties.", F),
        ("A: Today + cars, trucks and tractors to 50% (25pp more on non-U.S. content). CUSMA parts stay exempt.", F),
        ("B: A + auto parts to 50% (CUSMA parts exemption removed).", F),
        ("C: B + steel derivatives to 50% (the full August 24 threat).", F),
        ("", F),
        ("Method", FB),
        ("1. Each HTS10 line gets its 2025 realized tariff (duty / value) plus the new tariff in each scenario.", F),
        ("2. Export response per line = ((1 + new rate) / (1 + 2025 rate)) ^ (-elasticity) - 1, elasticity 2. Banned lines lose 100%.", F),
        ("3. Lines are assigned to NAICS 4-digit industries (HS6-NAICS concordance; vehicles and parts assigned directly).", F),
        ("4. Each industry's exports are split across CMAs by the CMA's share of Canadian employment in that industry (2021 Census, table 98-10-0448).", F),
        ("5. Jobs at risk = CMA employment in the industry x export intensity (U.S. exports / Canadian manufacturing revenue, table 16-10-0117) x export loss.", F),
        ("", F),
        ("Reading the numbers", FB),
        ("Tariff rate = average duty on the CMA's exports to the U.S. 'Export loss %' = drop in those exports, before any rerouting or price cuts.", F),
        ("These are estimates: StatCan does not publish exports by CMA and product. Employment-based allocation assumes exports per worker are the same everywhere in Canada within an industry.", F),
        ("Census counts workers where they live (Barrie includes Honda Alliston commuters). GM Oshawa reopened after the 2021 Census, so Oshawa is understated.", F),
        ("Static, first-round effects only: no supply-chain or household-spending multipliers. Farming, forestry and mining jobs at risk are not estimated.", F),
        ("", F),
        ("Conventions: blue = typed input, black = formula, green = link to another tab, yellow fill = assumption you can change.", FI),
    ]
    for i, (t, f) in enumerate(lines, 1):
        put(RM, i, 1, t, f).alignment = Alignment(wrap_text=True)

    # ------------------------------------------------------------------ Scenarios (inputs for weighting)
    SC = wb.create_sheet("Scenarios")
    widths(SC, [16, 70, 14, 18, 18])
    put(SC, 1, 1, "Scenarios and probabilities", FT)
    hdr(SC, 3, ["Scenario", "What happens", "Probability", "National rate, realized", "National rate, statutory"])
    summ = R["summary"]; sc = summ["scen"]
    rows = [("Today", "Section 338 at 50% + Sep 29 bans (no January increase)", summ["prob"]["None"], summ["cur_r"], summ["cur_s"]),
            ("A", "Cars, trucks, tractors to 50%; CUSMA parts stay exempt", summ["prob"]["A"], sc["A"]["rate_r"], sc["A"]["rate_s"]),
            ("B", "A + auto parts to 50% (CUSMA parts exemption removed)", summ["prob"]["B"], sc["B"]["rate_r"], sc["B"]["rate_s"]),
            ("C", "B + steel derivatives to 50% (full Aug 24 threat)", summ["prob"]["C"], sc["C"]["rate_r"], sc["C"]["rate_s"])]
    for i, (k, d, p, rr, rs) in enumerate(rows, 4):
        put(SC, i, 1, k, FB); put(SC, i, 2, d)
        put(SC, i, 3, p, FBLUE, PCT1, YF); put(SC, i, 4, rr, FBLUE, PCT2); put(SC, i, 5, rs, FBLUE, PCT2)
    put(SC, 8, 2, "Check: probabilities sum to 100%", FI); put(SC, 8, 3, "=SUM(C4:C7)", FB, PCT1)
    put(SC, 10, 1, "Probabilities are by end-Q1 2027: P(any January increase) 30% x conditional split A 40% / B 40% / C 20%. "
                "Evidence: Kalshi (30% chance of a deal before Jan 1), Polymarket (62% agreement to lower tariffs by Dec 31), "
                "Treasury & Risk/Bloomberg (one in four tariff threats carried out). National rates from the national model (RESULTS.md).", FI)
    SC.merge_cells("A10:E12"); SC["A10"].alignment = Alignment(wrap_text=True, vertical="top")
    P = {"today": "Scenarios!$C$4", "A": "Scenarios!$C$5", "B": "Scenarios!$C$6", "C": "Scenarios!$C$7"}

    # ------------------------------------------------------------------ CMA summary
    S = wb.create_sheet("CMA summary", 1)
    df = CR["cma"].copy()
    cmas = df[~df["geo"].isin(["Ontario", "Ontario, outside CMAs"])].sort_values("export_loss_pct_C", ascending=False)
    order = list(cmas["geo"]) + ["Ontario, outside CMAs", "Ontario"]
    df = df.set_index("geo").loc[order].reset_index()
    put(S, 1, 1, "Ontario CMAs: tariff rate, export loss and jobs at risk", FT)
    put(S, 2, 1, "Ranked by export loss in Scenario C. Exports are 2025 U.S. imports allocated to each CMA. Scenarios are cumulative; see 'Scenarios' tab.", FI)
    groups = [("", 1, 4), ("Average tariff rate on exports to U.S.", 5, 9), ("Export loss, % of exports", 10, 13),
              ("Export loss, US$", 14, 17), ("Manufacturing jobs at risk", 18, 21), ("Prob.-weighted", 22, 24), ("", 25, 25)]
    for t, a, b in groups:
        if t:
            S.merge_cells(start_row=4, start_column=a, end_row=4, end_column=b)
            x = S.cell(row=4, column=a, value=t); x.font = FB; x.fill = SUB; x.alignment = Alignment(horizontal="center")
    cols = ["CMA", "Employed (2021)", "Goods-sector employed", "Exports to U.S. 2025",
            "2025", "Today", "A", "B", "C",
            "Today", "A", "B", "C",
            "Today", "A", "B", "C",
            "Today", "A", "B", "C",
            "Export loss %", "Export loss US$", "Jobs at risk",
            "Jobs at risk C, % of employed"]
    hdr(S, 5, cols)
    r0 = 6
    for i, (_, x) in enumerate(df.iterrows()):
        r = r0 + i
        tot = x["geo"] in ("Ontario",)
        fill = TOT if x["geo"] in ("Ontario", "Ontario, outside CMAs") else None
        put(S, r, 1, x["geo"], FB if tot else F, None, fill)
        put(S, r, 2, x["employment_total"], FBLUE, INT, fill)
        put(S, r, 3, x["goods_employment"], FBLUE, INT, fill)
        put(S, r, 4, x["exports_to_us"], FBLUE, USD, fill)
        for j, k in enumerate(["rate_2025", "rate_today", "rate_A", "rate_B", "rate_C"]):
            put(S, r, 5 + j, x[k], FBLUE, PCT1, fill)
        for j, k in enumerate(["today", "A", "B", "C"]):
            put(S, r, 10 + j, x[f"export_loss_pct_{k}"], FBLUE, PCT1, fill)
            L = get_column_letter(10 + j)
            put(S, r, 14 + j, f"=$D{r}*{L}{r}", F, USDM, fill)                       # US$ loss = exports x loss %
            put(S, r, 18 + j, x[f"mfg_jobs_at_risk_{k}"], FBLUE, INT, fill)
        put(S, r, 22, f"={P['today']}*J{r}+{P['A']}*K{r}+{P['B']}*L{r}+{P['C']}*M{r}", F, PCT1, fill)
        put(S, r, 23, f"=$D{r}*V{r}", F, USDM, fill)
        put(S, r, 24, f"={P['today']}*R{r}+{P['A']}*S{r}+{P['B']}*T{r}+{P['C']}*U{r}", F, INT, fill)
        put(S, r, 25, f"=IF(B{r}>0,U{r}/B{r},0)", F, PCT2, fill)
    rl = r0 + len(df) - 1
    ncma = len(cmas)
    put(S, rl + 2, 1, "Check: 16 CMAs + rest of Ontario = Ontario (exports)", FI)
    put(S, rl + 2, 4, f"=SUM(D{r0}:D{r0 + ncma})-D{rl}", F, USDM)
    put(S, rl + 3, 1, "Blue numbers are model outputs from the Python project (tariff/cma.py, run on HTS10 data); black cells are formulas.", FI)
    S.freeze_panes = "B6"
    widths(S, [30, 12, 12, 13] + [8] * 9 + [10] * 4 + [9] * 4 + [11, 12, 11, 12])
    S.conditional_formatting.add(f"M{r0}:M{r0 + ncma - 1}", DataBarRule(start_type="num", start_value=0, end_type="max", color="C00000"))
    S.conditional_formatting.add(f"I{r0}:I{r0 + ncma - 1}", ColorScaleRule(start_type="min", start_color="FFFFFF", end_type="max", end_color="F4B183"))
    S.conditional_formatting.add(f"Y{r0}:Y{r0 + ncma - 1}", DataBarRule(start_type="num", start_value=0, end_type="max", color="7F7F7F"))

    # ------------------------------------------------------------------ Charts
    CH = wb.create_sheet("Charts", 2)
    put(CH, 1, 1, "Charts (data linked to 'CMA summary')", FT)
    hdr(CH, 3, ["CMA", "Export loss today", "Export loss C", "Tariff today", "Tariff C"])
    for i in range(ncma):
        r = 4 + i; src = r0 + i
        put(CH, r, 1, f"='CMA summary'!A{src}", FGREEN)
        for j, col in enumerate(["J", "M", "F", "I"]):
            put(CH, r, 2 + j, f"='CMA summary'!{col}{src}", FGREEN, PCT1)
    widths(CH, [30, 12, 12, 12, 12])
    last = 3 + ncma
    for title, c1, c2, anchor, ytitle in (("Export loss, % of exports: today vs C", 2, 3, "G3", "% of exports to U.S."),
                                          ("Tariff rate on exports: today vs C", 4, 5, "G26", "Tariff rate")):
        ch = BarChart(); ch.type = "bar"; ch.style = 10; ch.title = title; ch.y_axis.title = ytitle
        ch.add_data(Reference(CH, min_col=c1, max_col=c2, min_row=3, max_row=last), titles_from_data=True)
        ch.set_categories(Reference(CH, min_col=1, min_row=4, max_row=last))
        ch.y_axis.numFmt = "0%"; ch.height = 11; ch.width = 22; ch.x_axis.scaling.orientation = "maxMin"
        CH.add_chart(ch, anchor)

    # ------------------------------------------------------------------ Drivers
    DR = wb.create_sheet("Drivers")
    put(DR, 1, 1, "What drives each CMA's export loss (Scenario C, cumulative)", FT)
    hdr(DR, 3, ["CMA", "Type", "Code", "Description", "Export loss, US$", "Share of CMA's loss"])
    d = CR["drivers"]
    r = 4
    for g in order:
        sub = pd.concat([d[(d["geo"] == g) & (d["level"] == "NAICS4")].head(5), d[(d["geo"] == g) & (d["level"] == "HTS10")].head(5)])
        for _, x in sub.iterrows():
            desc = names.get(x["code"], "") if x["level"] == "NAICS4" else f"HTS {x['code'][:4]}.{x['code'][4:6]}.{x['code'][6:]} ({names.get(cma.NAICS_OVERRIDES.get(x['code'][:4], ''), '')})".replace(" ()", "")
            put(DR, r, 1, g); put(DR, r, 2, "Industry (NAICS)" if x["level"] == "NAICS4" else "Product line (HTS10)")
            put(DR, r, 3, x["code"]); put(DR, r, 4, desc)
            put(DR, r, 5, x["export_loss_C"], FBLUE, USDM); put(DR, r, 6, x["share_of_cma_loss"], FBLUE, PCT1)
            r += 1
        r += 1
    widths(DR, [30, 20, 12, 70, 16, 14]); DR.freeze_panes = "A4"

    # ------------------------------------------------------------------ Industries
    IN = wb.create_sheet("Industries")
    put(IN, 1, 1, "NAICS 4-digit industries: tariff rate and export loss (all Canada, U.S. imports 2025)", FT)
    hdr(IN, 3, ["NAICS", "Industry", "U.S. imports 2025", "Rate 2025", "Rate today", "Rate A", "Rate B", "Rate C",
                "Export loss today", "Export loss C", "Export loss C, US$", "Ontario share of Canadian jobs"])
    ind = CR["industry"]
    ind = ind[(ind["naics4"] != "9999") & (ind["customs_value"] > 0)].sort_values("loss_C").copy()
    for i, (_, x) in enumerate(ind.iterrows(), 4):
        put(IN, i, 1, x["naics4"]); put(IN, i, 2, names.get(x["naics4"], ""))
        put(IN, i, 3, x["customs_value"], FBLUE, USD)
        for j, k in enumerate(["avg_rate_2025", "rate_today", "rate_A", "rate_B", "rate_C", "export_loss_pct_today", "export_loss_pct_C"]):
            put(IN, i, 4 + j, x[k], FBLUE, PCT1)
        put(IN, i, 11, f"=C{i}*J{i}", F, USDM)
        put(IN, i, 12, min(x["ontario_emp_share_of_canada"], 1.0), FBLUE, PCT1)
    widths(IN, [8, 60, 13, 9, 9, 9, 9, 9, 11, 11, 13, 13]); IN.freeze_panes = "C4"
    IN.conditional_formatting.add(f"J4:J{3 + len(ind)}", DataBarRule(start_type="num", start_value=0, end_type="max", color="C00000"))

    # ------------------------------------------------------------------ Sensitivity
    SE = wb.create_sheet("Sensitivity")
    put(SE, 1, 1, "Sensitivity to the export response (elasticity): Scenario C", FT)
    put(SE, 2, 1, "Elasticity = % drop in exports per 1% rise in the tariff-inclusive price. 1 = short run, 2 = central, 4 = long run.", FI)
    for t, a, b in (("Export loss C, % of exports", 2, 4), ("Manufacturing jobs at risk, C", 5, 7)):
        SE.merge_cells(start_row=4, start_column=a, end_row=4, end_column=b)
        x = SE.cell(row=4, column=a, value=t); x.font = FB; x.fill = SUB; x.alignment = Alignment(horizontal="center")
    hdr(SE, 5, ["CMA", "Elasticity 1", "Elasticity 2", "Elasticity 4", "Elasticity 1", "Elasticity 2", "Elasticity 4"])
    for i, g in enumerate(order, 6):
        put(SE, i, 1, g, FB if g == "Ontario" else F)
        for j, s in enumerate((1.0, 2.0, 4.0)):
            put(SE, i, 2 + j, SENS[s].loc[g, "export_loss_pct_C"], FBLUE, PCT1)
            put(SE, i, 5 + j, SENS[s].loc[g, "mfg_jobs_at_risk_C"], FBLUE, INT)
    widths(SE, [30, 12, 12, 12, 12, 12, 12]); SE.freeze_panes = "B6"

    # ------------------------------------------------------------------ Sources
    SO = wb.create_sheet("Sources")
    widths(SO, [60, 110])
    hdr(SO, 1, ["Source", "Link / note"])
    src = [("USITC DataWeb: U.S. imports for consumption from Canada, HTS10, 2025", "https://dataweb.usitc.gov/"),
           ("White House Section 338 annexes (July 20, Sep 15) and Sep 29 import exclusions", "https://www.whitehouse.gov/ (annex PDFs listed in the Python project)"),
           ("Statistics Canada, table 98-10-0448-01 (2021 Census, industry groups by CMA)", "https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=9810044801"),
           ("Statistics Canada, table 16-10-0117-01 (manufacturing revenue by NAICS, 2024)", "https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1610011701"),
           ("HS6-NAICS concordance (Pierce & Schott), via the 'concordance' R package", "https://github.com/insongkim/concordance"),
           ("Trade elasticity range", "Boehm, Levchenko & Pandalai-Nayar (2023); Fontagne et al. (2022)"),
           ("Scenario probabilities", "Kalshi, Polymarket (Oct 12, 2026); Treasury & Risk / Bloomberg (Jan 27, 2026)")]
    for i, (a, b) in enumerate(src, 2):
        put(SO, i, 1, a); put(SO, i, 2, b)

    for ws in wb.worksheets:
        ws.sheet_view.showGridLines = ws.title in ("Drivers", "Industries", "Sources")
    wb.calculation.fullCalcOnLoad = True   # Excel recalculates every formula on open
    wb.save(OUT)
    return OUT
