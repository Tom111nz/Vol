import pymysql
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ------------------------
# PARAMETERS
# ------------------------
DB_CONFIG = dict(
    host="localhost",
    user="root",
    password="Bright1",
    db="Vol_Test",
    port=3306,
    autocommit=False,
    cursorclass=pymysql.cursors.DictCursor,
)

YEARS = [2025, 2026]
MONTH_ABBR = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

# Delta targets in percent terms (e.g., 10 means 0.10)
DELTA_PCTS = [0.1, 0.5, 1, 2, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50]

# Loop both puts and calls
OPTION_TYPES = ["p", "c"]

USE_LOG_RETURNS = False
OUTPUT_CSV = "vix_contract_delta_correlations_puts_calls.csv"

# NEW: per-day picked strikes output
STRIKES_OUTPUT_CSV = "vix_target_delta_strikes_by_day.csv"

# accumulator for picked strikes
picked_strikes_rows = []


# ------------------------
# Helpers
# ------------------------
def make_contract_suffixes(years):
    """Return list like ['(Jan 25)', '(Feb 25)', ...] across given years."""
    suffixes = []
    for y in years:
        yy = str(y)[-2:]
        for m in MONTH_ABBR:
            suffixes.append(f"({m} {yy})")
    return suffixes


def compute_returns(series: pd.Series, log: bool) -> pd.Series:
    if log:
        series = series.where(series > 0)
        return np.log(series).diff()
    return series.pct_change()


def load_data_for_contract(contract_suffix: str) -> pd.DataFrame:
    """Load all option rows + futures close for a single contract suffix."""
    con = pymysql.connect(**DB_CONFIG)

    query = """
        SELECT
            vc.quote_date AS QuoteDate,
            vc.futurescontract AS FuturesContract,
            vf.Settle AS VixFutureSettle,
            vc.VixCalculated,
            st.strike,
            st.option_type,
            og.bid_1545 AS Theo_Bid,
            og.delta_1545 AS Delta
        FROM vixcalculated vc
        LEFT JOIN vixfutures vf
            ON vf.tradedate = vc.quote_date
           AND vf.contract = vc.futurescontract
        LEFT JOIN optiongreeks og
            ON og.optionexpiryId = vc.optionexpiryID
        LEFT JOIN strike st
            ON st.id = og.strikeiD
        WHERE vc.futurescontract LIKE %s
          ##AND vf.Settle IS NOT NULL
          ##AND vf.Settle <> 0.0
        ORDER BY vc.quote_date;
    """

    with con.cursor() as cur:
        cur.execute(query, (f"% {contract_suffix}",))
        rows = cur.fetchall()

    con.close()

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df["QuoteDate"] = pd.to_datetime(df["QuoteDate"])
    return df


def pick_closest_delta_per_day(
    df: pd.DataFrame,
    option_type: str,
    target_delta: float
) -> pd.DataFrame:
    """For each QuoteDate, pick option row closest to target_delta."""
    opts = df[df["option_type"].str.lower() == option_type.lower()].copy()
    if opts.empty:
        return opts

    opts["delta_dist"] = (opts["Delta"] - target_delta).abs()

    picked = (
        opts.loc[opts.groupby("QuoteDate")["delta_dist"].idxmin()]
           .sort_values("QuoteDate")
    )
    return picked


def target_delta_for_type(delta_pct: float, option_type: str) -> float:
    """
    Calls are positive delta, puts are negative delta.
    delta_pct is in percent units, e.g. 10 -> 0.10
    """
    base = delta_pct / 100.0
    return base if option_type.lower() == "c" else -base


def analyze_contract(
    df: pd.DataFrame,
    contract_suffix: str,
    delta_pcts: list[float],
    option_type: str
) -> pd.DataFrame:
    """Return correlations for all deltas for this contract and option type."""
    if df.empty:
        return pd.DataFrame()

    vix_daily = (
        df.groupby("QuoteDate", as_index=False)["VixFutureSettle"]
          .first()
          .sort_values("QuoteDate")
    )

    out_rows = []

    for d in delta_pcts:
        target_delta = target_delta_for_type(d, option_type)

        picked = pick_closest_delta_per_day(df, option_type, target_delta)
        if picked.empty:
            continue

        # ------------------------
        # NEW: capture per-day picked strike info
        # ------------------------
        for _, r in picked.iterrows():
            picked_strikes_rows.append({
                "ContractSuffix": contract_suffix,
                "OptionType": option_type.lower(),
                "DeltaPct": d,
                "TargetDelta": target_delta,
                "QuoteDate": r["QuoteDate"],
                "Strike": r["strike"],
                "ActualDelta": r["Delta"],
                "Theo_Bid": r["Theo_Bid"],
                "FuturesContract": r["FuturesContract"],
                "VixFutureSettle": r["VixFutureSettle"],
                "VixCalculated": r["VixCalculated"],
            })

        merged = pd.merge(
            vix_daily,
            picked[["QuoteDate", "Theo_Bid"]],
            on="QuoteDate",
            how="inner"
        ).sort_values("QuoteDate")

        merged["vix_ret"] = compute_returns(
            merged["VixFutureSettle"], USE_LOG_RETURNS
        )
        merged["opt_ret"] = compute_returns(
            merged["Theo_Bid"], USE_LOG_RETURNS
        )

        valid = merged["vix_ret"].notna() & merged["opt_ret"].notna()
        n = int(valid.sum())

        corr = (
            np.nan
            if n < 5
            else merged.loc[valid, "vix_ret"]
                 .corr(merged.loc[valid, "opt_ret"])
        )

        out_rows.append({
            "ContractSuffix": contract_suffix,
            "OptionType": option_type.lower(),
            "DeltaPct": d,
            "TargetDelta": target_delta,
            "N": n,
            "Corr": corr,
            "StartDate": merged["QuoteDate"].min(),
            "EndDate": merged["QuoteDate"].max(),
        })

    return pd.DataFrame(out_rows)


# ------------------------
# Run: contracts x deltas x option type
# ------------------------
contract_suffixes = make_contract_suffixes(YEARS)

all_results = []

for suffix in contract_suffixes:
    df = load_data_for_contract(suffix)
    print(f"{suffix}: records loaded = {len(df)}")

    for opt_type in OPTION_TYPES:
        res = analyze_contract(df, suffix, DELTA_PCTS, opt_type)
        if not res.empty:
            all_results.append(res)

results = pd.concat(all_results, ignore_index=True) if all_results else pd.DataFrame()

print("\nDone. Total rows in results:", len(results))
print(results.head())

# Save combined puts+calls CSV
if not results.empty:
    results.to_csv(OUTPUT_CSV, index=False)
    print("Saved:", OUTPUT_CSV)

# ------------------------
# NEW: Save per-day target-delta strike selections
# ------------------------
if picked_strikes_rows:
    strikes_df = pd.DataFrame(picked_strikes_rows)
    strikes_df.sort_values(
        ["ContractSuffix", "OptionType", "DeltaPct", "QuoteDate"],
        inplace=True
    )
    strikes_df.to_csv(STRIKES_OUTPUT_CSV, index=False)
    print("Saved:", STRIKES_OUTPUT_CSV)

# ------------------------
# Optional: Heatmaps (Puts and Calls)
# ------------------------
if not results.empty:
    results["ContractDate"] = pd.to_datetime(
        results["ContractSuffix"]
            .str.extract(r"\((\w+ \d{2})\)")[0],
        format="%b %y"
    )

    contract_order = (
        results[["ContractSuffix", "ContractDate"]]
        .drop_duplicates()
        .sort_values("ContractDate")["ContractSuffix"]
        .tolist()
    )

    fig, axes = plt.subplots(1, 2, figsize=(16, 8), constrained_layout=True)

    for ax, opt_type, title in zip(
        axes, ["p", "c"], ["Puts", "Calls"]
    ):
        sub = results[results["OptionType"] == opt_type].copy()
        if sub.empty:
            ax.set_title(f"{title} (no data)")
            ax.axis("off")
            continue

        pivot = sub.pivot(
            index="ContractSuffix",
            columns="DeltaPct",
            values="Corr"
        ).reindex(contract_order)

        im = ax.imshow(
            pivot.values,
            aspect="auto",
            interpolation="nearest"
        )
        ax.set_title(f"Correlation Heatmap ({title})")
        ax.set_xlabel("Delta Target (%)")
        ax.set_ylabel("Contract Suffix")
        ax.set_yticks(range(len(pivot.index)))
        ax.set_yticklabels(pivot.index)
        ax.set_xticks(range(len(pivot.columns)))
        ax.set_xticklabels(pivot.columns)

        fig.colorbar(
            im,
            ax=ax,
            fraction=0.046,
            pad=0.04,
            label="Return Correlation"
        )

    plt.show()