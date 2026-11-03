"""Canada-U.S. tariff project: one command from data download to final reports.

    python run_all.py                     # rebuild every report from the data already in data/
    python run_all.py --download          # download fresh DataWeb + StatCan data first, then rebuild
    python run_all.py --download-dataweb  # only refresh U.S. import data (needs DATAWEB_TOKEN)
    python run_all.py --download-statcan  # only refresh the StatCan tables (no key needed)

Reports go to reports/<today's date>/ and are copied to reports/latest/.
Old data files are kept in data/archive/<date_time>/ whenever new data is downloaded.
Assumptions (tariff rates, probabilities, base month, ...) live in tariff/config.py.
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from tariff import pipeline  # noqa: E402

TOKEN_FILE = os.path.expanduser("~/.dataweb_token")


def _dataweb_token():
    """DATAWEB_TOKEN if set, otherwise the token saved in ~/.dataweb_token."""
    token = os.environ.get("DATAWEB_TOKEN", "").strip()
    if not token and os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE) as f:
            token = f.read().strip()
    return token


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--download", action="store_true", help="refresh DataWeb and StatCan data")
    ap.add_argument("--download-dataweb", action="store_true", help="refresh DataWeb data (needs DATAWEB_TOKEN)")
    ap.add_argument("--download-statcan", action="store_true", help="refresh StatCan data")
    ap.add_argument("--data", default=os.path.join(HERE, "data"))
    ap.add_argument("--reports", default=os.path.join(HERE, "reports"))
    a = ap.parse_args()

    want_dw = a.download or a.download_dataweb
    want_sc = a.download or a.download_statcan
    if want_dw or want_sc:
        token = _dataweb_token() if want_dw else None
        if want_dw and not token:
            sys.exit(f"No DataWeb token. Save it to {TOKEN_FILE} or set DATAWEB_TOKEN "
                     "(sign in at dataweb.usitc.gov > API tab). See README.md.")
        pipeline.download(a.data, dataweb_token=token, statcan=want_sc)

    pipeline.build_reports(a.data, a.reports)


if __name__ == "__main__":
    main()
