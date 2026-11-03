"""How the tariff changes hit each Ontario CMA's exports, built up from HTS10 lines.

Chain:  HTS10 line (DataWeb value, duty, tariff change)  ->  NAICS 4-digit industry (HS6-NAICS concordance)
        ->  CMA (CMA share of national employment in that industry, 2021 Census)

For CMA c and industry i:   exports_ci = US imports from Canada_i x (employment_ci / employment_i,Canada)
Export response of a line:  dX/X = ((1 + t0 + dt) / (1 + t0)) ^ (-sigma) - 1     (banned lines: -100%)
Jobs at risk (manufacturing): employment_ci x export intensity_i x (dX/X)_i, export intensity = US exports / national sales
"""
import os

import numpy as np
import pandas as pd

from . import config as C
from . import annex_codes as A


def _line_flags(h):
    """Section 338 and ban status for every HTS10 row (8-digit lines cover their 10-digit children)."""
    def split(codes):
        d = [c.replace(".", "") for c in codes]
        return {x for x in d if len(x) == 8}, {x for x in d if len(x) == 10}
    full_remove = {c for c in A.SEP_REMOVE_MOTOR + A.SEP_REMOVE_ALCOHOL if len(c.replace(".", "")) == 8}
    carve = {c.replace(".", "") for c in A.SEP_REMOVE_MOTOR + A.SEP_REMOVE_ALCOHOL if len(c.replace(".", "")) == 10}
    listed = (set(A.ANNEX_JUL_DAIRY + A.ANNEX_JUL_ALCOHOL + A.ANNEX_JUL_MOTOR) | set(A.SEP_ADD_MOTOR + A.SEP_ADD_ALCOHOL)) - full_remove
    l8, l10 = split(listed)
    b8, b10 = split(A.BAN_DAIRY + A.BAN_ALCOHOL + A.BAN_MOTOR)
    s338 = (h["hts8"].isin(l8) | h["hts10"].isin(l10)) & ~h["hts10"].isin(carve)
    banned = h["hts8"].isin(b8) | h["hts10"].isin(b10)
    return s338, banned


def line_shocks(h, usmca_8708, sigma):
    """Tariff change and export response per HTS10 line, cumulative: Today -> A -> B -> C."""
    h = h.copy()
    h["t0"] = (h["calc_duty"] / h["customs_value"]).where(h["customs_value"] > 0, 0.0)
    h["s338"], h["banned"] = _line_flags(h)
    d_today = np.where(h["s338"], C.SECTION_338_RATE, 0.0)
    d_a = np.where(h["hs4"].isin(C.VEHICLE_HS4), (C.THREAT_RATE - C.CURRENT_232_VEHICLES) * (1 - C.US_CONTENT_SHARE), 0.0)
    d_b = np.where(h["hs4"].isin(C.PARTS_HS4), usmca_8708 * C.THREAT_RATE + (1 - usmca_8708) * (C.THREAT_RATE - C.CURRENT_232_NONCUSMA_PARTS), 0.0)
    d_c = np.where(h["ch"].isin(C.STEEL_DERIVATIVE_CHAPTERS), C.THREAT_RATE - C.CURRENT_232_STEEL_DERIV, 0.0)
    cum = {"today": d_today, "A": d_today + d_a, "B": d_today + d_a + d_b, "C": d_today + d_a + d_b + d_c}
    for k, d in cum.items():
        h[f"dt_{k}"] = d
        h[f"rate_{k}"] = h["t0"] + d
        resp = ((1 + h["t0"] + d) / (1 + h["t0"])) ** (-sigma) - 1
        h[f"resp_{k}"] = np.where(h["banned"], -1.0, resp)
        h[f"loss_{k}"] = h["customs_value"] * h[f"resp_{k}"]          # negative = exports lost (US$)
        h[f"addduty_{k}"] = h["customs_value"] * d
    return h


# HS4 headings whose industry is unambiguous; overrides the many-to-many HS6-NAICS mapping
NAICS_OVERRIDES = {"8703": "3361", "8704": "3361", "8702": "3361", "8707": "3362", "8708": "3363", "8706": "3363"}


def census_group(n4):
    """Map NAICS 4-digit codes to the 2021 Census industry groups (farms are combined as 1110, farm support as 1150)."""
    if n4[:3] in ("111", "112") and n4 not in ("1114", "1125"):
        return "1110"
    if n4 in ("1151", "1152"):
        return "1150"
    return n4


def to_naics(h, conc):
    """Split each HTS10 line across the NAICS 4-digit industries its HS6 maps to.

    Weights: share of the HS6's NAICS 6-digit matches falling in each 4-digit industry, ignoring the
    non-industry 9xxx codes when a real industry exists; vehicle headings use NAICS_OVERRIDES."""
    c = conc.copy()
    c["naics4"] = c["naics4"].map(census_group)
    real = ~c["naics4"].str.startswith("9")
    has_real = real.groupby(c["hs6"]).transform("any")
    c = c[real | ~has_real]
    c = c.groupby(["hs6", "naics4"]).size().rename("n").reset_index()
    c["w"] = c["n"] / c.groupby("hs6")["n"].transform("sum")
    over = pd.DataFrame([(h6, NAICS_OVERRIDES[h6[:4]], 1.0) for h6 in c["hs6"].unique() if h6[:4] in NAICS_OVERRIDES],
                        columns=["hs6", "naics4", "w"])
    c = pd.concat([c[~c["hs6"].str[:4].isin(NAICS_OVERRIDES)][["hs6", "naics4", "w"]], over])
    m = h.merge(c[["hs6", "naics4", "w"]], on="hs6", how="left")
    m["naics4"] = m["naics4"].fillna("9999")                            # ch. 98/99 special provisions: no industry
    m["w"] = m["w"].fillna(1.0)
    return m


def run(h, data_dir, usmca_8708, sigma=None, fx=None):
    sigma = C.TRADE_ELASTICITY if sigma is None else sigma
    fx = C.USDCAD_2025 if fx is None else fx
    conc = pd.read_csv(os.path.join(data_dir, "hs6_naics_concordance.csv"), dtype=str)
    emp = pd.read_csv(os.path.join(data_dir, "statcan_cma_employment_naics4_2021.csv"), dtype={"naics4": str})
    emp["employed"] = pd.to_numeric(emp["employed"], errors="coerce").fillna(0)
    sales_path = os.path.join(data_dir, "statcan_mfg_sales_naics.csv")
    sales = pd.read_csv(sales_path, dtype={"naics": str}) if os.path.exists(sales_path) else None

    L = line_shocks(h, usmca_8708, sigma)
    M = to_naics(L, conc)
    val_cols = ["customs_value", "calc_duty"] + [f"{p}_{k}" for p in ("loss", "addduty") for k in ("today", "A", "B", "C")]
    for col in val_cols:
        M[col] = M[col] * M["w"]
    for k in ("today", "A", "B", "C"):
        M[f"rv_{k}"] = M["customs_value"] * M[f"rate_{k}"]           # for value-weighted average rates
    ind = M.groupby("naics4")[val_cols + [f"rv_{k}" for k in ("today", "A", "B", "C")]].sum()

    # employment shares
    E = emp.pivot_table(index="naics4", columns="geo", values="employed", aggfunc="sum")
    cmas = [g for g in E.columns if g not in ("Canada", "Ontario")]
    E["Ontario, outside CMAs"] = (E["Ontario"] - E[cmas].sum(axis=1)).clip(lower=0)
    geos = cmas + ["Ontario, outside CMAs", "Ontario"]
    share = E[geos].div(E["Canada"], axis=0).replace([np.inf, -np.inf], 0).fillna(0)
    totals = emp[emp["naics4"] == "TOTAL"].set_index("geo")["employed"]
    totals["Ontario, outside CMAs"] = totals["Ontario"] - totals[cmas].sum()

    # export intensity (manufacturing): US exports (C$) / national sales (C$)
    inten = pd.Series(dtype=float)
    if sales is not None:
        s = sales.dropna(subset=["sales_cad"]).set_index("naics")["sales_cad"]
        inten = (ind["customs_value"] * fx / s.reindex(ind.index)).clip(upper=1.0)
    ind["export_intensity"] = inten.reindex(ind.index)

    rows, drivers = [], []
    goods = [i for i in ind.index if i != "9999"]
    for g in geos:
        sh = share[g].reindex(goods).fillna(0)
        I = ind.loc[goods].mul(sh, axis=0)
        x = I["customs_value"].sum()
        r = {"geo": g, "employment_total": totals.get(g, np.nan),
             "goods_employment": E.loc[[i for i in goods if i in E.index], g].sum(),
             "exports_to_us": x, "rate_2025": I["calc_duty"].sum() / x if x else 0}
        for k in ("today", "A", "B", "C"):
            r[f"rate_{k}"] = I[f"rv_{k}"].sum() / x if x else 0
            r[f"added_duty_{k}"] = I[f"addduty_{k}"].sum()
            r[f"export_loss_{k}"] = -I[f"loss_{k}"].sum()
            r[f"export_loss_pct_{k}"] = r[f"export_loss_{k}"] / x if x else 0
            if sales is not None:
                emp_i = E.loc[[i for i in goods if i in E.index], g]
                resp_i = (ind.loc[emp_i.index, f"loss_{k}"] / ind.loc[emp_i.index, "customs_value"]).fillna(0)
                jobs = -(emp_i * ind.loc[emp_i.index, "export_intensity"].fillna(0) * resp_i).sum()
                r[f"mfg_jobs_at_risk_{k}"] = jobs
                r[f"jobs_at_risk_pct_emp_{k}"] = jobs / r["employment_total"] if r["employment_total"] else np.nan
        r["exports_per_worker"] = x / r["employment_total"] if r["employment_total"] else np.nan
        rows.append(r)
        # top industries and HTS lines behind the CMA's losses (scenario C, cumulative)
        top_i = (-I["loss_C"]).sort_values(ascending=False).head(5)
        for n, v in top_i.items():
            drivers.append({"geo": g, "level": "NAICS4", "code": n, "export_loss_C": v, "share_of_cma_loss": v / r["export_loss_C"] if r["export_loss_C"] else 0})
        Ml = M[M["naics4"].isin(goods)].copy()
        Ml["alloc"] = Ml["naics4"].map(sh).fillna(0)
        Ml["loss_alloc"] = -Ml["loss_C"] * Ml["alloc"]
        top_l = Ml.groupby("hts10")["loss_alloc"].sum().sort_values(ascending=False).head(10)
        for n, v in top_l.items():
            drivers.append({"geo": g, "level": "HTS10", "code": n, "export_loss_C": v, "share_of_cma_loss": v / r["export_loss_C"] if r["export_loss_C"] else 0})
    out = pd.DataFrame(rows)
    out["rank_loss_pct_C"] = out["export_loss_pct_C"].rank(ascending=False).astype(int)
    ind = ind.reset_index()
    ind["avg_rate_2025"] = ind["calc_duty"] / ind["customs_value"]
    for k in ("today", "A", "B", "C"):
        ind[f"rate_{k}"] = ind[f"rv_{k}"] / ind["customs_value"]
        ind[f"export_loss_pct_{k}"] = -ind[f"loss_{k}"] / ind["customs_value"]
    ind["ontario_emp_share_of_canada"] = ind["naics4"].map(share["Ontario"]).fillna(0)
    return {"cma": out, "drivers": pd.DataFrame(drivers), "industry": ind, "lines": L, "sigma": sigma}
