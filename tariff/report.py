"""Write the results: a readable report (RESULTS.md), an Excel workbook of values, and CSVs."""
import os

import pandas as pd

from .model import bn, pct


def _fmt(v, f):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    return {"pct": pct(v), "usd": bn(v), "ratio": f"{v:.3f}", "int": f"{int(v):,}"}.get(f, str(v))


def _md_table(df, cols, fmts):
    head = "| " + " | ".join(cols) + " |\n|" + "---|" * len(cols) + "\n"
    body = ""
    for _, r in df.iterrows():
        body += "| " + " | ".join(_fmt(r[c], fmts.get(c, "str")) if fmts.get(c) else str(r[c]) for c in cols) + " |\n"
    return head + body


def write_markdown(R, path):
    S = R["summary"]; T = R["tables"]; sc = S["scen"]
    L = []
    L.append("# U.S. effective tariff rate on Canadian goods: current rate and January 2027 scenarios\n")
    L.append("Computed in Python from USITC DataWeb HTS10 data (U.S. imports from Canada, 2025) and the White House Section 338 annexes.\n")
    L.append("## Headline results\n")
    L.append("| Outcome | Realized rate | Statutory rate | Probability |\n|---|---|---|---|")
    L.append(f"| Today (Section 338 in force) | {pct(S['cur_r'])} | {pct(S['cur_s'])} | {pct(S['prob']['None'], 0)} (no January increase) |")
    for k in "ABC":
        L.append(f"| Scenario {k}: {sc[k]['desc']} | {pct(sc[k]['rate_r'])} | {pct(sc[k]['rate_s'])} | {pct(S['prob'][k], 0)} |")
    L.append(f"| **Probability-weighted** | **{pct(S['w_r'])}** | **{pct(S['w_s'])}** | |\n")
    L.append("Realized = duties actually collected / import value (what Census, USAFacts and RBC measure). "
             "Statutory = headline rates applied to all trade (what the Bank of Canada and Global Trade Alert use).\n")

    L.append("## Moody's mapping\n")
    L.append(_md_table(T["moodys_mapping"], ["moodys", "percentile", "outcome", "rate_realized", "rate_statutory"],
                       {"percentile": "pct", "rate_realized": "pct", "rate_statutory": "pct"}))

    L.append("\n## Does the 2.6% hold up?\n")
    L.append(f"Yes. DataWeb 2025: {bn(S['duty'])} duty / {bn(S['total'])} imports = **{pct(S['rate25'])}**. "
             "Every source using duties collected / import value agrees within 0.05pp; sources near 5-9% use statutory rates.\n")
    v = T["verification"].copy()
    v["their"] = [bn(x) if x > 1e6 else pct(x, 1) for x in v["their_figure"]]
    v["ours"] = ["" if pd.isna(o) or o is None else (bn(o) if o > 1e6 else pct(o)) for o in v["our_figure"]]
    L.append(_md_table(v, ["source", "period", "measure", "their", "ours", "verdict"], {}))

    L.append("\n## Every calculation, with the numbers plugged in\n")
    for sec, g in T["steps"].groupby("section", sort=False):
        L.append(f"### {sec}\n")
        L.append("| Step | Result | Formula | Worked numbers |\n|---|---|---|---|")
        for _, r in g.iterrows():
            L.append(f"| {r['step']} | {_fmt(r['value'], r['fmt'])} | `{r['formula']}` | {r['worked']} |")
        L.append("")

    L.append("## Scenario components\n")
    L.append(_md_table(T["scenario_components"], ["scenario", "component", "worked_realized", "worked_statutory"], {}))

    L.append("\n## Probability evidence\n")
    ev = T["evidence"].copy(); ev["reading"] = [pct(x, 0) if pd.notna(x) else "" for x in ev["reading"]]
    L.append(_md_table(ev, ["source", "finding", "reading", "how_used"], {}))

    L.append("\n## Sensitivity (realized rates)\n")
    L.append(_md_table(T["sensitivity"], ["P_any_increase", "US_content_share", "rate_A", "rate_B", "rate_C", "prob_weighted"],
                       {c: "pct" for c in ["P_any_increase", "US_content_share", "rate_A", "rate_B", "rate_C", "prob_weighted"]}))

    L.append("\n## Caveats\n")
    L.append("- Static 2025 trade weights: actual duties fall as tariffed and banned trade shrinks.")
    L.append("- The January 2027 increases exist only as an August 24, 2026 social-media post; no proclamation had been issued as of October 13, 2026.")
    L.append("- Steel derivatives use HS chapter 73 as a proxy and an assumed 25% current effective Section 232 rate.")
    L.append("- U.S. content of Canadian-built vehicles (50%) is an assumption; see the sensitivity table.")
    with open(path, "w") as f:
        f.write("\n".join(L) + "\n")


def write_excel(R, path):
    T = R["tables"]
    with pd.ExcelWriter(path, engine="openpyxl") as xw:
        S = R["summary"]; sc = S["scen"]
        summ = pd.DataFrame([{"outcome": "Today (Section 338 in force)", "rate_realized": S["cur_r"], "rate_statutory": S["cur_s"], "probability": S["prob"]["None"]}] +
                            [{"outcome": f"Scenario {k}: {sc[k]['desc']}", "rate_realized": sc[k]["rate_r"], "rate_statutory": sc[k]["rate_s"], "probability": S["prob"][k]} for k in "ABC"] +
                            [{"outcome": "Probability-weighted", "rate_realized": S["w_r"], "rate_statutory": S["w_s"], "probability": 1.0}])
        sheets = [("Summary", summ), ("All calculations", T["steps"]), ("DataWeb monthly", T["monthly"]),
                  ("New HTS codes", T["annex"]), ("Scenario components", T["scenario_components"]),
                  ("Probabilities", T["probabilities"]), ("Moodys mapping", T["moodys_mapping"]),
                  ("Evidence", T["evidence"]), ("Verify 2.6%", T["verification"]), ("Sensitivity", T["sensitivity"])]
        for name, df in sheets:
            df.to_excel(xw, sheet_name=name, index=False)
            ws = xw.sheets[name]
            for i, col in enumerate(df.columns, 1):
                w = max(len(str(col)), *(len(str(x)) for x in df[col].head(200))) if len(df) else len(str(col))
                ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = min(max(10, w + 2), 70)
                low = str(col).lower()
                fmt = ("0.00%" if any(s in low for s in ("rate", "share", "prob", "cumulative", "percentile")) and "worked" not in low
                       else '#,##0' if any(s in low for s in ("value", "duty", "added")) and "worked" not in low else None)
                if fmt:
                    for c in ws.iter_cols(min_col=i, max_col=i, min_row=2):
                        for cell in c:
                            if isinstance(cell.value, (int, float)):
                                cell.number_format = fmt
            ws.freeze_panes = "A2"


def write_all(R, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    write_markdown(R, os.path.join(out_dir, "RESULTS.md"))
    write_excel(R, os.path.join(out_dir, "tariff_results.xlsx"))
    R["tables"]["annex"].to_csv(os.path.join(out_dir, "matched_hts_lines.csv"), index=False)
    R["tables"]["steps"].to_csv(os.path.join(out_dir, "all_calculations.csv"), index=False)


def print_summary(R):
    S = R["summary"]; sc = S["scen"]
    print("\nU.S. effective tariff rate on Canadian goods")
    print("-" * 78)
    print(f"{'Outcome':<52}{'Realized':>9}{'Statutory':>10}{'Prob':>7}")
    print(f"{'Today (Section 338 in force)':<52}{pct(S['cur_r']):>9}{pct(S['cur_s']):>10}{pct(S['prob']['None'], 0):>7}")
    for k in "ABC":
        print(f"{('Scenario ' + k + ': ' + sc[k]['desc'])[:51]:<52}{pct(sc[k]['rate_r']):>9}{pct(sc[k]['rate_s']):>10}{pct(S['prob'][k], 0):>7}")
    print(f"{'Probability-weighted':<52}{pct(S['w_r']):>9}{pct(S['w_s']):>10}")
    print("-" * 78)
    print(f"2025 realized rate: {bn(S['duty'])} / {bn(S['total'])} = {pct(S['rate25'])}")
    print(f"Section 338 coverage (exact HTS): {bn(S['coverage'])}; banned: {bn(S['banned'])}")
    for _, r in R["tables"]["moodys_mapping"].iterrows():
        print(f"  Moody's {r['moodys']:<9}({pct(r['percentile'], 0):>4}) -> {r['outcome'][:40]:<40} {pct(r['rate_realized'])} / {pct(r['rate_statutory'])}")


# ---------------------------------------------------------------- CMA results
CMA_COLS = [("geo", "CMA"), ("exports_to_us", "Exports to U.S. 2025"), ("rate_2025", "Rate 2025"), ("rate_today", "Rate today"),
            ("rate_A", "Rate A"), ("rate_B", "Rate B"), ("rate_C", "Rate C"),
            ("export_loss_pct_today", "Export loss today"), ("export_loss_pct_C", "Export loss C"),
            ("mfg_jobs_at_risk_today", "Mfg jobs at risk today"), ("mfg_jobs_at_risk_C", "Mfg jobs at risk C"),
            ("jobs_at_risk_pct_emp_C", "Jobs at risk C, % of employment")]


def _cfmt(col, v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    if col == "geo":
        return str(v)
    if col.startswith(("rate", "export_loss_pct", "jobs_at_risk_pct")):
        return pct(v, 2 if "pct_emp" in col else 1)
    if col.startswith("mfg_jobs"):
        return f"{v:,.0f}"
    return bn(v)


def write_cma_markdown(CR, R, path, naics_names):
    cm = CR["cma"].sort_values("export_loss_pct_C", ascending=False)
    cols = [c for c in CMA_COLS if c[0] in cm.columns]
    L = ["# How the tariffs hit exports from each Ontario CMA (built from HTS10 lines)\n"]
    L.append("Method: each HTS10 line's tariff change -> the NAICS industry that makes it (HS6-NAICS concordance) -> each CMA's share of "
             "national employment in that industry (2021 Census). Export response uses a trade elasticity of "
             f"{CR['sigma']} on the tariff-inclusive price; banned lines lose 100%. Scenarios are cumulative (A includes today, B includes A, ...).\n")
    L.append("## CMA results, ranked by export loss in Scenario C\n")
    L.append("| " + " | ".join(c[1] for c in cols) + " |\n|" + "---|" * len(cols))
    for _, r in cm.iterrows():
        L.append("| " + " | ".join(_cfmt(c, r[c]) for c, _ in cols) + " |")
    L.append("\nRates are value-weighted realized tariff rates on each CMA's exports to the U.S. (2025 realized duty + new tariffs). "
             "Export loss is % of the CMA's 2025 exports to the U.S. Jobs at risk = employment x export intensity x export loss, manufacturing only.\n")
    L.append("## What drives each CMA's loss (Scenario C)\n")
    d = CR["drivers"]
    for g in cm["geo"]:
        di = d[(d["geo"] == g) & (d["level"] == "NAICS4")].head(3)
        dl = d[(d["geo"] == g) & (d["level"] == "HTS10")].head(3)
        inds = "; ".join(f"{c} {naics_names.get(c, '')} ({pct(s, 0)})" for c, s in zip(di["code"], di["share_of_cma_loss"]))
        lines = "; ".join(f"{c} ({pct(s, 0)})" for c, s in zip(dl["code"], dl["share_of_cma_loss"]))
        L.append(f"- **{g}**: industries {inds}. Top HTS lines: {lines}.")
    L.append("\n## Industries (NAICS 4-digit) hit hardest\n")
    ind = CR["industry"].sort_values("loss_C").head(15)
    L.append("| NAICS | Industry | U.S. imports 2025 | Rate 2025 | Rate today | Rate C | Export loss C | Ontario share of Canadian jobs |\n|---|---|---|---|---|---|---|---|")
    for _, r in ind.iterrows():
        L.append(f"| {r['naics4']} | {naics_names.get(r['naics4'], '')} | {bn(r['customs_value'])} | {pct(r['avg_rate_2025'])} | {pct(r['rate_today'])} | "
                 f"{pct(r['rate_C'])} | {pct(r['export_loss_pct_C'], 1)} | {pct(r['ontario_emp_share_of_canada'], 0)} |")
    L.append("\n## Caveats\n")
    L.append("- Exports are allocated to CMAs by employment share within each industry: assumes exports per worker in an industry are the same everywhere in Canada.")
    L.append("- 2021 Census employment (latest industry-by-CMA data, table 98-10-0448), counted where workers live, not where they work: "
             "e.g. Barrie picks up Honda Alliston commuters. GM Oshawa reopened in late 2021, after the Census, so Oshawa's auto share is understated.")
    L.append("- 2025 trade weights; static, first-round effects only (no supply-chain or household-income multipliers).")
    L.append("- Export intensity uses 2024 manufacturing revenue (table 16-10-0117); jobs at risk are not computed for farming, forestry and mining.")
    L.append("- HS6 codes mapping to several NAICS industries are split equally. HTS chapters 98-99 (special provisions, about 5.5% of value) have no industry and are left out.")
    L.append(f"- Elasticity {CR['sigma']} is a mid-range short-to-medium-run value; losses scale roughly in proportion to it (see sensitivity in cma_results.xlsx).")
    with open(path, "w") as f:
        f.write("\n".join(L) + "\n")


def write_cma_excel(CR, path, sens=None):
    with pd.ExcelWriter(path, engine="openpyxl") as xw:
        tabs = [("CMA results", CR["cma"]), ("Drivers", CR["drivers"]), ("Industries", CR["industry"])]
        if sens is not None:
            tabs.append(("Elasticity sensitivity", sens))
        for name, df in tabs:
            df.to_excel(xw, sheet_name=name, index=False)
            ws = xw.sheets[name]
            for i, col in enumerate(df.columns, 1):
                ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = max(12, min(40, len(str(col)) + 2))
                low = str(col).lower()
                fmt = "0.00%" if low.startswith(("rate", "export_loss_pct", "jobs_at_risk_pct", "share", "ontario_emp", "avg_rate", "export_intensity")) \
                    else "#,##0" if any(s in low for s in ("value", "duty", "loss", "exports", "jobs", "employment", "rv_")) else None
                if fmt:
                    for c in ws.iter_cols(min_col=i, max_col=i, min_row=2):
                        for cell in c:
                            if isinstance(cell.value, (int, float)):
                                cell.number_format = fmt
            ws.freeze_panes = "B2"
