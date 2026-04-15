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

YEARS = [2025] ##, 2026
MONTH_ABBR = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

DELTA_PCTS = [0.1, 0.5, 1, 2, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50]
OPTION_TYPES = ["p", "c"]

USE_LOG_RETURNS = False
OUTPUT_CSV = "vix_contract_delta_correlations_puts_calls.csv"
STRIKES_OUTPUT_CSV = "vix_target_delta_strikes_by_day.csv"

picked_strikes_rows = []

# ------------------------
# Helpers
# ------------------------
def make_contract_suffixes(years):
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


# ------------------------
# SQL template (single expiry)
# ------------------------
QUERY_TEMPLATE = """
SELECT
    vc.quote_date       AS QuoteDate,
    vc.futurescontract AS FuturesContract,
    vf.Settle           AS VixFutureSettle,
    vc.VixCalculated,

    st.strike,
    st.option_type,
    og.bid_1545   AS Theo_Bid,
    og.delta_1545 AS Delta

FROM vixcalculated vc

LEFT JOIN vixfutures vf
    ON vf.tradedate = vc.quote_date
   AND vf.contract  = vc.futurescontract

LEFT JOIN optiongreeks og
    ON og.optionexpiryId = {expiry_col}
   ##AND og.valuetime = '15:45'

LEFT JOIN strike st
    ON st.id = og.strikeiD

WHERE vc.futurescontract LIKE %s

ORDER BY vc.quote_date;
"""


def load_data_for_contract(contract_suffix: str) -> pd.DataFrame:
    con = pymysql.connect(**DB_CONFIG)
    dfs = []

    expiry_variants = [
        ("SPX", "vc.optionexpiryID"),
        ("VIX",  "vc.VixoptionexpiryID"),
    ]

    for option_root, expiry_col in expiry_variants:
        query = QUERY_TEMPLATE.format(expiry_col=expiry_col)

        with con.cursor() as cur:
            cur.execute(query, (f"%{contract_suffix}",))
            rows = cur.fetchall()

        df = pd.DataFrame(rows)
        if not df.empty:
            df["OptionRoot"] = option_root
            dfs.append(df)

    con.close()

    if not dfs:
        return pd.DataFrame()

    df = pd.concat(dfs, ignore_index=True)
    df["QuoteDate"] = pd.to_datetime(df["QuoteDate"])
    return df


def target_delta_for_type(delta_pct: float, option_type: str) -> float:
    base = delta_pct / 100.0
    return base if option_type.lower() == "c" else -base


def pick_closest_delta_per_day(
    df: pd.DataFrame,
    option_type: str,
    target_delta: float
) -> pd.DataFrame:

    opts = df[df["option_type"].str.lower() == option_type.lower()].copy()
    if opts.empty:
        return opts

    opts["delta_dist"] = (opts["Delta"] - target_delta).abs()

    return (
        opts.loc[opts.groupby("QuoteDate")["delta_dist"].idxmin()]
            .sort_values("QuoteDate")
    )


def analyze_contract(
    df: pd.DataFrame,
    contract_suffix: str,
    delta_pcts: list[float],
    option_type: str
) -> pd.DataFrame:

    if df.empty:
        return pd.DataFrame()

    vixFuture_daily = (
        df.groupby("QuoteDate", as_index=False)["VixFutureSettle"]
          .first()
          .sort_values("QuoteDate")
    )

    out_rows = []

    for option_root in ["SPX", "VIX"]:
        sub = df[df["OptionRoot"] == option_root]

        for d in delta_pcts:
            target_delta = target_delta_for_type(d, option_type)
            picked = pick_closest_delta_per_day(sub, option_type, target_delta)
            if picked.empty:
                continue

            for _, r in picked.iterrows():
                picked_strikes_rows.append({
                    "ContractSuffix": contract_suffix,
                    "OptionRoot": option_root,
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
                vixFuture_daily,
                picked[["QuoteDate", "Theo_Bid"]],
                on="QuoteDate",
                how="inner"
            ).sort_values("QuoteDate")

            merged["vix_ret"] = compute_returns(merged["VixFutureSettle"], USE_LOG_RETURNS)
            merged["opt_ret"] = compute_returns(merged["Theo_Bid"], USE_LOG_RETURNS)

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
                "OptionRoot": option_root,
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
# Run
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

if not results.empty:
    results.to_csv(OUTPUT_CSV, index=False)
    print("Saved:", OUTPUT_CSV)

if picked_strikes_rows:
    strikes_df = pd.DataFrame(picked_strikes_rows)
    strikes_df.sort_values(
        ["ContractSuffix", "OptionRoot", "OptionType", "DeltaPct", "QuoteDate"],
        inplace=True
    )
    strikes_df.to_csv(STRIKES_OUTPUT_CSV, index=False)
    print("Saved:", STRIKES_OUTPUT_CSV)


# ------------------------
# Optional heatmaps
# ------------------------
if not results.empty:
    results["ContractDate"] = pd.to_datetime(
        results["ContractSuffix"].str.extract(r"\((\w+ \d{2})\)")[0],
        format="%b %y"
    )

    contract_order = (
        results[["ContractSuffix", "ContractDate"]]
        .drop_duplicates()
        .sort_values("ContractDate")["ContractSuffix"]
        .tolist()
    )

    fig, axes = plt.subplots(1, 2, figsize=(16, 8), constrained_layout=True)

    for ax, opt_type in zip(axes, ["p", "c"]):
        sub = results[(results["OptionType"] == opt_type) & (results["OptionRoot"] == "VIX")]
        pivot = sub.pivot(
            index="ContractSuffix",
            columns="DeltaPct",
            values="Corr"
        ).reindex(contract_order)

        im = ax.imshow(pivot.values, aspect="auto")
        ax.set_title(f"VIX Greeks Correlation ({opt_type.upper()})")
        ax.set_xlabel("Delta (%)")
        ax.set_ylabel("Contract")
        ax.set_yticks(range(len(pivot.index)))
        ax.set_yticklabels(pivot.index)
        ax.set_xticks(range(len(pivot.columns)))
        ax.set_xticklabels(pivot.columns)

        fig.colorbar(im, ax=ax)

    plt.show()
