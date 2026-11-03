"""All calculations. Each step returns its numbers and a 'worked' string showing the formula with values plugged in."""
import os

import pandas as pd

from . import config as C
from . import annex_codes as A


def bn(x):
    return f"US${x / 1e9:,.2f}bn"


def pct(x, d=2):
    return f"{x * 100:.{d}f}%"


# ---------------------------------------------------------------- data
def load_data(data_dir):
    h = pd.read_csv(os.path.join(data_dir, "dataweb_canada_hts10_2025.csv"), dtype={"hts10": str})
    h["hts10"] = h["hts10"].str.zfill(10)
    h["hts8"] = h["hts10"].str[:8]
    h["hs6"] = h["hts10"].str[:6]
    h["hs4"] = h["hts10"].str[:4]
    h["ch"] = h["hts10"].str[:2]
    m = pd.read_csv(os.path.join(data_dir, "dataweb_monthly_totals.csv"))
    p = pd.read_csv(os.path.join(data_dir, "dataweb_program_split_2025.csv"), dtype={"hs4": str})
    hs6 = pd.read_csv(os.path.join(data_dir, "comtrade_hs6_2025.csv"), dtype={"hs6": str})
    return h, m, p, hs6


# ---------------------------------------------------------------- annex lines
def annex_table():
    """Every HTS line in the Section 338 annexes and the Sep 29 bans, with status."""
    jul = {}
    for c in A.ANNEX_JUL_DAIRY: jul[c] = "Dairy"
    for c in A.ANNEX_JUL_ALCOHOL: jul[c] = "Alcoholic beverages"
    for c in A.ANNEX_JUL_MOTOR: jul[c] = "Motor vehicles list"
    sep = {}
    for c in A.SEP_ADD_MOTOR: sep[c] = "Added (motor vehicles list)"
    for c in A.SEP_ADD_ALCOHOL: sep[c] = "Added (alcohol list)"
    for c in A.SEP_REMOVE_MOTOR + A.SEP_REMOVE_ALCOHOL:
        sep[c] = "Removed" if len(c.replace(".", "")) == 8 else "Carved out at 10 digits"
    bans = set(A.BAN_DAIRY + A.BAN_ALCOHOL + A.BAN_MOTOR)
    rows = []
    for c in sorted(set(jul) | set(sep) | bans, key=lambda x: x.replace(".", "")):
        d = c.replace(".", "")
        s = sep.get(c, "")
        listed = (c in jul or s.startswith("Added")) and not s.startswith(("Removed", "Carved"))
        sign = 1 if listed else (-1 if s.startswith("Carved") else 0)
        rows.append({"hts_line": c, "digits": d, "n_digits": len(d), "july_annex": jul.get(c, ""),
                     "sep_change": s, "under_50pct_now": listed, "banned": c in bans, "sign": sign})
    return pd.DataFrame(rows)


def match_lines(annex, h):
    """Exact match: 8-digit lines sum all HTS10 rows under them; 10-digit lines match one row."""
    by8 = h.groupby("hts8")[["customs_value", "calc_duty"]].sum()
    by10 = h.set_index("hts10")[["customs_value", "calc_duty"]]
    vals, duties = [], []
    for d in annex["digits"]:
        src = by8 if len(d) == 8 else by10
        if d in src.index:
            vals.append(float(src.loc[d, "customs_value"])); duties.append(float(src.loc[d, "calc_duty"]))
        else:
            vals.append(0.0); duties.append(0.0)
    annex = annex.copy()
    annex["value_2025"] = vals
    annex["duty_2025"] = duties
    annex["realized_rate_2025"] = (annex["duty_2025"] / annex["value_2025"]).where(annex["value_2025"] > 0, 0)
    annex["matched"] = annex["value_2025"] > 0
    return annex


# ---------------------------------------------------------------- model
def run(data_dir):
    h, monthly, prog, hs6 = load_data(data_dir)
    R = {"steps": [], "tables": {}}

    def step(section, name, value, formula, worked, fmt="pct"):
        R["steps"].append({"section": section, "step": name, "value": value, "formula": formula, "worked": worked, "fmt": fmt})
        return value

    # 1. DataWeb totals and the 2.6%
    tot = h["customs_value"].sum(); duty = h["calc_duty"].sum(); dutiable = h["dutiable_value"].sum()
    step("1. DataWeb 2025", "U.S. imports from Canada (customs value)", tot, "sum(customs_value over all HTS10)", f"{len(h):,} HTS10 lines = {bn(tot)}", "usd")
    step("1. DataWeb 2025", "Calculated duty", duty, "sum(calc_duty)", bn(duty), "usd")
    step("1. DataWeb 2025", "Dutiable value", dutiable, "sum(dutiable_value)", bn(dutiable), "usd")
    rate25 = step("1. DataWeb 2025", "Realized effective rate, 2025", duty / tot, "calc_duty / customs_value",
                  f"{bn(duty)} / {bn(tot)} = {pct(duty / tot)}")

    monthly = monthly.copy()
    monthly["rate"] = monthly["calc_duty"] / monthly["customs_value"]
    mm = monthly.set_index("month")
    ytd = monthly[monthly["month"].between("2026-01", "2026-07")]
    rate_ytd = ytd["calc_duty"].sum() / ytd["customs_value"].sum()
    R["tables"]["monthly"] = monthly
    chk = monthly[monthly["month"].str.startswith("2025")][["customs_value", "calc_duty"]].sum()
    step("1. DataWeb 2025", "Check: 12 monthly totals = annual HTS10 total", chk["customs_value"] / tot,
         "sum(monthly 2025 value) / sum(HTS10 value)", f"{bn(chk['customs_value'])} / {bn(tot)} = {chk['customs_value'] / tot:.4f}", "ratio")

    ps = prog[prog["hs4"] == "ALL"].groupby("program")["customs_value"].sum()
    usmca_all = ps.get("USMCA", 0) / ps.sum()
    p8708 = prog[prog["hs4"] == "8708"].set_index("program")["customs_value"]
    usmca_8708 = p8708.get("USMCA", 0) / p8708.sum()
    p8703 = prog[prog["hs4"] == "8703"].set_index("program")["customs_value"]
    usmca_8703 = p8703.get("USMCA", 0) / p8703.sum()
    step("1. DataWeb 2025", "USMCA (CUSMA) claim share, all goods", usmca_all, "USMCA value / all value",
         f"{bn(ps.get('USMCA', 0))} / {bn(ps.sum())} = {pct(usmca_all, 1)}")
    step("1. DataWeb 2025", "USMCA claim share, HS 8708 auto parts", usmca_8708, "USMCA value / all value (8708)",
         f"{bn(p8708.get('USMCA', 0))} / {bn(p8708.sum())} = {pct(usmca_8708, 1)}")
    step("1. DataWeb 2025", "USMCA claim share, HS 8703 cars", usmca_8703, "USMCA value / all value (8703)",
         f"{bn(p8703.get('USMCA', 0))} / {bn(p8703.sum())} = {pct(usmca_8703, 1)}")

    # 2. New HTS codes, exact match
    annex = match_lines(annex_table(), h)
    R["tables"]["annex"] = annex
    cov = (annex["sign"] * annex["value_2025"]).sum()
    cov_duty = (annex["sign"] * annex["duty_2025"]).sum()
    banned = annex.loc[annex["banned"], "value_2025"].sum()
    jul_v = annex.loc[annex["under_50pct_now"] & (annex["july_annex"] != ""), "value_2025"].sum()
    add_v = annex.loc[annex["sep_change"].str.startswith("Added"), "value_2025"].sum()
    rem_v = annex.loc[annex["sep_change"] == "Removed", "value_2025"].sum()
    n_listed = int(annex["under_50pct_now"].sum()); n_ban = int(annex["banned"].sum())
    unmatched = annex[(annex["sign"] != 0) | annex["banned"]]
    step("2. New HTS codes", "Lines under the 50% tariff now / banned lines", n_listed, "count of annex lines",
         f"{n_listed} tariffed lines, {n_ban} banned lines; {int((~unmatched['matched']).sum())} lines had no 2025 imports", "int")
    step("2. New HTS codes", "Value under Section 338 now (net of carve-outs)", cov, "sum(sign x value), sign = +1 listed, -1 carve-out",
         f"July-annex lines {bn(jul_v)} + Sep 15 additions {bn(add_v)} - carve-outs = {bn(cov)}", "usd")
    step("2. New HTS codes", "Check: exact coverage / official US$20bn", cov / C.OFFICIAL_COVERAGE_USD, "coverage / 20e9",
         f"{bn(cov)} / {bn(C.OFFICIAL_COVERAGE_USD)} = {cov / C.OFFICIAL_COVERAGE_USD:.3f}", "ratio")
    step("2. New HTS codes", "Value of banned lines (from Sep 29)", banned, "sum(value of banned lines)",
         f"{bn(banned)} vs CRS about {bn(C.OFFICIAL_BANNED_USD)} (ratio {banned / C.OFFICIAL_BANNED_USD:.3f})", "usd")
    step("2. New HTS codes", "Value of lines removed on Sep 15", rem_v, "sum(value of removed lines)", bn(rem_v), "usd")
    step("2. New HTS codes", "Realized duty already paid on tariffed lines, 2025", cov_duty / cov if cov else 0,
         "sum(sign x duty) / coverage", f"{bn(cov_duty)} / {bn(cov)} = {pct(cov_duty / cov)}")

    # 3. Calculated tariff rate today
    base_r = float(mm.loc[C.BASE_MONTH, "rate"])
    share = cov / tot
    inc338 = share * C.SECTION_338_RATE
    cur_r = base_r + inc338
    cur_s = C.STATUTORY_BASE_RATE + inc338
    step("3. Calculated tariff rate", f"Realized base rate ({C.BASE_MONTH}, before Section 338)", base_r,
         "duty / value in base month",
         f"{bn(mm.loc[C.BASE_MONTH, 'calc_duty'])} / {bn(mm.loc[C.BASE_MONTH, 'customs_value'])} = {pct(base_r)}")
    step("3. Calculated tariff rate", "Covered share of all imports", share, "coverage / total imports",
         f"{bn(cov)} / {bn(tot)} = {pct(share)}")
    step("3. Calculated tariff rate", "Section 338 increment", inc338, "covered share x 50%",
         f"{pct(share)} x {pct(C.SECTION_338_RATE, 0)} = {pct(inc338)}")
    step("3. Calculated tariff rate", "CURRENT RATE, realized", cur_r, "base_realized + 50% x coverage / total",
         f"{pct(base_r)} + {pct(C.SECTION_338_RATE, 0)} x {bn(cov)} / {bn(tot)} = {pct(cur_r)}")
    step("3. Calculated tariff rate", "CURRENT RATE, statutory", cur_s, "base_statutory + 50% x coverage / total",
         f"{pct(C.STATUTORY_BASE_RATE)} + {pct(C.SECTION_338_RATE, 0)} x {bn(cov)} / {bn(tot)} = {pct(cur_s)}")
    aug = float(mm.loc["2026-08", "rate"]) if "2026-08" in mm.index else None
    if aug is not None:
        step("3. Calculated tariff rate", "Check: August 2026 realized vs 10/31 of the month under Section 338", aug,
             "realized Aug rate vs base + increment x 10/31",
             f"realized {pct(aug)} vs implied {pct(base_r + inc338 * 10 / 31)} (gap = front-loading / trade shifts)")
    # reconciliation with the earlier HS6-based 8.48%
    listed6 = set(annex.loc[annex["under_50pct_now"], "digits"].str[:6])
    hs6v = hs6[hs6["hs6"].isin(listed6)]["customs_value"].sum()
    old = C.STATUTORY_BASE_RATE + C.SECTION_338_RATE * hs6v / tot
    step("3. Calculated tariff rate", "Reconciliation: earlier HS6-based statutory estimate", old,
         "base_statutory + 50% x HS6 value / total",
         f"{pct(C.STATUTORY_BASE_RATE)} + 50% x {bn(hs6v)} / {bn(tot)} = {pct(old)} (HS6 codes include unlisted 8-digit lines)")

    # 4. Scenarios
    v_veh = h[h["hs4"].isin(C.VEHICLE_HS4)]["customs_value"].sum()
    v_parts = h[h["hs4"].isin(C.PARTS_HS4)]["customs_value"].sum()
    v_steel = h[h["ch"].isin(C.STEEL_DERIVATIVE_CHAPTERS)]["customs_value"].sum()
    comps = {
        "A": [("Cars, trucks, tractors (8703/8704/8701), non-U.S. content", v_veh, 1 - C.US_CONTENT_SHARE,
               C.CURRENT_232_VEHICLES, C.THREAT_RATE, C.THREAT_RATE - C.CURRENT_232_VEHICLES)],
        "B": [("Auto parts under CUSMA (exempt today)", v_parts, usmca_8708, 0.0, C.THREAT_RATE, C.THREAT_RATE),
              ("Auto parts not under CUSMA", v_parts, 1 - usmca_8708, C.CURRENT_232_NONCUSMA_PARTS, C.THREAT_RATE, 0.0)],
        "C": [("Steel derivatives (HS ch. 73 proxy)", v_steel, 1.0, C.CURRENT_232_STEEL_DERIV, C.THREAT_RATE,
               C.THREAT_RATE - C.CURRENT_232_STEEL_DERIV)],
    }
    desc = {"A": "Cars and trucks to 50%; CUSMA parts stay exempt",
            "B": "A + auto parts to 50% (CUSMA parts exemption removed)",
            "C": "B + steel derivatives to 50% (full Aug 24 threat)"}
    comp_rows, scen = [], {}
    cum_r = cum_s = 0.0
    for k in ("A", "B", "C"):
        add_r = add_s = 0.0
        for (lab, val, sh, now, after, stat_mult) in comps[k]:
            d_r = val * sh * (after - now)
            d_s = val * stat_mult
            add_r += d_r; add_s += d_s
            comp_rows.append({"scenario": k, "component": lab, "value_2025": val, "affected_share": sh, "rate_now": now,
                              "rate_after": after, "added_duty_realized": d_r, "added_duty_statutory": d_s,
                              "worked_realized": f"{bn(val)} x {pct(sh, 0)} x ({pct(after, 0)} - {pct(now, 0)}) = {bn(d_r)}",
                              "worked_statutory": f"{bn(val)} x {pct(stat_mult, 0)} = {bn(d_s)}"})
        inc_r, inc_s = add_r / tot, add_s / tot
        cum_r += inc_r; cum_s += inc_s
        scen[k] = {"desc": desc[k], "inc_r": inc_r, "inc_s": inc_s, "rate_r": cur_r + cum_r, "rate_s": cur_s + cum_s,
                   "add_r": add_r, "add_s": add_s}
        step(f"4. Scenario {k}", f"Added duty from this scenario's components", add_r, "sum(value x share x (after - now))",
             (lambda rs: rs[0]["worked_realized"] if len(rs) == 1 else
              " + ".join(r["worked_realized"].split(" = ")[1] for r in rs) + f" = {bn(add_r)}")([r for r in comp_rows if r["scenario"] == k]), "usd")
        step(f"4. Scenario {k}", "Increment over the previous scenario (realized)", inc_r, "added duty / total imports",
             f"{bn(add_r)} / {bn(tot)} = {pct(inc_r)}")
        step(f"4. Scenario {k}", f"AVERAGE RATE, SCENARIO {k} (realized)", scen[k]["rate_r"], "current + cumulative increments",
             f"{pct(cur_r)} + {pct(cum_r)} = {pct(scen[k]['rate_r'])}")
        step(f"4. Scenario {k}", f"AVERAGE RATE, SCENARIO {k} (statutory)", scen[k]["rate_s"], "current + cumulative increments",
             f"{pct(cur_s)} + {pct(cum_s)} = {pct(scen[k]['rate_s'])}")
    R["tables"]["scenario_components"] = pd.DataFrame(comp_rows)

    # 5. Probabilities
    p = {"None": 1 - C.P_ANY_INCREASE}
    for k in ("A", "B", "C"):
        p[k] = C.P_ANY_INCREASE * C.CONDITIONAL_SPLIT[k]
    outcomes = [("No January increase", "None", cur_r, cur_s)] + [(f"Scenario {k}: {scen[k]['desc']}", k, scen[k]["rate_r"], scen[k]["rate_s"]) for k in ("A", "B", "C")]
    prob = pd.DataFrame([{"outcome": o, "key": k, "probability": p[k], "rate_realized": rr, "rate_statutory": rs} for o, k, rr, rs in outcomes])
    prob["cumulative"] = prob["probability"].cumsum()
    R["tables"]["probabilities"] = prob
    w_r = (prob["probability"] * prob["rate_realized"]).sum()
    w_s = (prob["probability"] * prob["rate_statutory"]).sum()
    step("5. Probabilities", "P(any Jan 2027 increase in force by end-Q1 2027)", C.P_ANY_INCREASE, "input",
         "Split given an increase: " + ", ".join(f"{k} {pct(v, 0)}" for k, v in C.CONDITIONAL_SPLIT.items()))
    step("5. Probabilities", "PROBABILITY-WEIGHTED RATE (realized)", w_r, "sum(probability x rate)",
         " + ".join(f"{pct(a, 0)} x {pct(b)}" for a, b in zip(prob["probability"], prob["rate_realized"])) + f" = {pct(w_r)}")
    step("5. Probabilities", "PROBABILITY-WEIGHTED RATE (statutory)", w_s, "sum(probability x rate)",
         " + ".join(f"{pct(a, 0)} x {pct(b)}" for a, b in zip(prob["probability"], prob["rate_statutory"])) + f" = {pct(w_s)}")
    mp = []
    for name, pc in sorted(C.MOODYS_PERCENTILES.items(), key=lambda x: x[1]):
        row = prob[prob["cumulative"] >= pc - 1e-12].iloc[0]
        mp.append({"moodys": name, "percentile": pc, "outcome": row["outcome"], "rate_realized": row["rate_realized"], "rate_statutory": row["rate_statutory"]})
    R["tables"]["moodys_mapping"] = pd.DataFrame(mp)
    R["tables"]["evidence"] = pd.DataFrame(C.PROBABILITY_EVIDENCE, columns=["source", "finding", "reading", "how_used"])

    # 6. Verification of the 2.6%
    ours = {"rate_2025": rate25, "rate_2026-07": float(mm.loc["2026-07", "rate"]), "rate_2026-08": aug,
            "rate_2026ytd_jul": rate_ytd, "total_value": tot, "usmca_share_all": usmca_all, "current_statutory": cur_s}
    ver = []
    for (src, per, meas, theirs, key, comparable) in C.EXTERNAL_CHECKS:
        o = ours.get(key) if key else None
        if o is None:
            verdict, gap = "Context only", None
        elif key == "total_value":
            gap = o / theirs - 1; verdict = "Agrees" if abs(gap) < 0.005 else "Differs"
        elif comparable:
            gap = (o - theirs) * 100; verdict = "Agrees" if abs(gap) <= 0.06 else "Differs"
        else:
            gap = (o - theirs) * 100
            verdict = ("Close (statutory vs statutory)" if key == "current_statutory" and abs(gap) <= 1
                       else "Consistent (Canada only vs Canada + Mexico)" if key == "usmca_share_all"
                       else "Different concept (statutory)")
        ver.append({"source": src, "period": per, "measure": meas, "their_figure": theirs, "our_figure": o, "gap": gap, "verdict": verdict})
    R["tables"]["verification"] = pd.DataFrame(ver)

    # 7. Sensitivity
    sens = []
    for pinc in (0.20, 0.30, 0.40):
        for usc in (0.30, 0.50, 0.60):
            a_inc = v_veh * (1 - usc) * (C.THREAT_RATE - C.CURRENT_232_VEHICLES) / tot
            ra = cur_r + a_inc
            rb = ra + scen["B"]["inc_r"]
            rc = rb + scen["C"]["inc_r"]
            pr = [1 - pinc] + [pinc * C.CONDITIONAL_SPLIT[k] for k in "ABC"]
            sens.append({"P_any_increase": pinc, "US_content_share": usc, "rate_A": ra, "rate_B": rb, "rate_C": rc,
                         "prob_weighted": pr[0] * cur_r + pr[1] * ra + pr[2] * rb + pr[3] * rc})
    R["tables"]["sensitivity"] = pd.DataFrame(sens)

    R["summary"] = {"total": tot, "duty": duty, "rate25": rate25, "coverage": cov, "banned": banned, "base_r": base_r,
                    "cur_r": cur_r, "cur_s": cur_s, "scen": scen, "w_r": w_r, "w_s": w_s, "prob": p,
                    "v_veh": v_veh, "v_parts": v_parts, "v_steel": v_steel, "usmca_8708": usmca_8708, "old_hs6": old}
    R["tables"]["steps"] = pd.DataFrame(R["steps"])
    return R
