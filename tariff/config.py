"""Assumptions. Change values here and re-run run_all.py. Every number has its source next to it."""

# ---------- Tariff measures ----------
SECTION_338_RATE = 0.50          # Proclamations of July 20, 2026; in force Aug 22, 2026; no CUSMA exemption
STATUTORY_BASE_RATE = 0.050      # Bank of Canada, MPR July 2026, tariff assumptions (statutory average before Section 338)
SECTION_338_START = "2026-08-22"   # Section 338 tariffs in force from this date
BASE_MONTH = "2026-07"           # last full month before Section 338: realized base rate is taken from this month

OFFICIAL_COVERAGE_USD = 20e9     # "US$20bn" of Canadian goods under Section 338 (CRS R49349; Al Jazeera, Aug 22, 2026)
OFFICIAL_BANNED_USD = 967e6      # CRS R49349: about US$967 million of 2025 imports on the exclusion lists

# ---------- January 1, 2027 threat (social-media post, Aug 24, 2026; no proclamation as of Oct 2026) ----------
THREAT_RATE = 0.50               # cars, trucks, parts and steel derivatives to 50%
CURRENT_232_VEHICLES = 0.25      # Section 232 on non-U.S. content of CUSMA vehicles (Trade Commissioner Service, Sep 28, 2026)
US_CONTENT_SHARE = 0.50          # ASSUMPTION: U.S. content of Canadian-built vehicles (exempt from the 232 auto tariff). Test 0.30-0.60
CURRENT_232_NONCUSMA_PARTS = 0.25  # Section 232 on non-CUSMA auto parts; CUSMA parts are exempt today
CURRENT_232_STEEL_DERIV = 0.25   # ESTIMATE: CUSMA goods pay 25% on non-U.S. content with a 15% floor; non-CUSMA Annex I-A pays 50% (CRS IN12519)
STEEL_DERIVATIVE_CHAPTERS = ["73"]  # proxy for steel derivative products: HS chapter 73, articles of iron or steel

VEHICLE_HS4 = ["8703", "8704", "8701"]   # passenger vehicles, trucks, tractors (incl. road tractors)
PARTS_HS4 = ["8708"]

# ---------- Scenario probabilities (by end-Q1 2027) ----------
P_ANY_INCREASE = 0.30            # central; test 0.20-0.40
CONDITIONAL_SPLIT = {            # given that some increase happens
    "A": 0.40,                   # vehicles only; CUSMA parts exemption extended
    "B": 0.40,                   # vehicles + parts
    "C": 0.20,                   # vehicles + parts + steel derivatives (full threat)
}
MOODYS_PERCENTILES = {"Baseline": 0.50, "S1": 0.10, "S2": 0.75, "S3": 0.90, "S4": 0.96}

PROBABILITY_EVIDENCE = [
    ("Kalshi (Oct 12, 2026)", "Canada accepts a U.S. trade deal before Jan 1, 2027", 0.30,
     "70% no-deal is an upper bound on increase odds, not an estimate of them"),
    ("Kalshi (Oct 12, 2026)", "...before Dec 1, 2026", 0.10, "Talks not expected to conclude quickly"),
    ("Polymarket (Oct 12, 2026)", "U.S.-Canada agreement to lower tariffs by Dec 31, 2026", 0.62,
     "Markets lean toward de-escalation"),
    ("Polymarket (Oct 12, 2026)", "Trump announces a Canada tariff increase by Oct 31, 2026", 0.73,
     "Announcements likely; implementation is a separate, lower-probability event"),
    ("Treasury & Risk / Bloomberg (Jan 27, 2026)", "Share of Trump tariff threats carried out", 0.25,
     "Base rate; central 30% sits slightly above because Section 232 only needs a rate change"),
    ("Global Automakers of Canada (Sep 2026)", "Doubt the CUSMA parts exemption will be extended", None,
     "Why B gets equal weight with A"),
    ("No proclamation (as of Oct 13, 2026)", "Threat exists only as an Aug 24 post", None,
     "Keeps C at the smallest conditional share"),
]

# ---------- External estimates used to verify the 2.6% ----------
# (source, period, measure, value, our comparable key or None, comparable?)
EXTERNAL_CHECKS = [
    ("USAFacts (from Census)", "2025", "Duties collected / import value", 0.026, "rate_2025", True),
    ("USAFacts (from Census)", "2026-07", "Duties collected / import value", 0.028, "rate_2026-07", True),
    ("RBC Economics", "2026-07", "Effective rate on imports from Canada", 0.028, "rate_2026-07", True),
    ("RBC Economics", "2026-08", "Effective rate on imports from Canada", 0.032, "rate_2026-08", True),
    ("USAFacts (from Census)", "Jan-Jul 2026", "Duties collected / import value", 0.031, "rate_2026ytd_jul", True),
    ("USAFacts (from Census)", "2024", "Duties collected / import value", 0.001, None, False),
    ("UN Comtrade", "2025", "Total U.S. imports from Canada (US$)", 382413150648, "total_value", True),
    ("Wharton Budget Model", "2026-07", "USMCA claim share, Canada + Mexico", 0.802, "usmca_share_all", False),
    ("Bank of Canada MPR", "2026-07", "Statutory average U.S. tariff on Canada", 0.050, "rate_2026-07", False),
    ("Global Trade Alert", "Before Jan 2027", "Statutory, trade-weighted, incl. Section 338", 0.085, "current_statutory", False),
    ("Wharton Budget Model", "2026-07", "Overall U.S. effective rate, all partners", 0.067, None, False),
]
ATB_STATUTORY_ESTIMATE = 0.075   # Bank of Canada 5.0% + ATB Financial estimate of Section 338 (+2.5pp), Aug 2026
GTA_BENCHMARKS = {"current": 0.085, "A": 0.110, "B": 0.157}   # Global Trade Alert, Aug 25, 2026 (statutory)

# ---------- CMA analysis ----------
TRADE_ELASTICITY = 2.0   # sigma: % fall in exports per 1% rise in the tariff-inclusive price. Short-run estimates ~1-2,
                         # long-run ~2-4 (e.g. Boehm, Levchenko & Pandalai-Nayar 2023; Fontagne et al. 2022). Test 1-4.
USDCAD_2025 = 1.40       # approx. 2025 average Canadian dollars per U.S. dollar (Bank of Canada annual average); converts exports for export intensity
