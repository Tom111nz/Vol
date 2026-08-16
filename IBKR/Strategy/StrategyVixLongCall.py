from dataclasses import dataclass
from datetime import timedelta
from math import floor

import pandas as pd
import pandas_market_calendars as mcal

from sqlalchemy import (
    create_engine,
    select,
    Column,
    Integer,
    Float,
    String,
    DateTime,
    ForeignKey, func,
)

from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Session


# ============================================================
# PARAMETERS
# ============================================================

@dataclass
class StrategyParameters:
    dte_target: int = 42

    strike: float = 60.0
    delta: float = 0.02
    option_type: str = "C"

    contracts: int = 0
    budget: float = 1000.0
    multiplier: int = 100

    first_target_multiple: float = 50.0
    second_target_multiple: float = 100.0
    third_target_multiple: float = 150.0

    spx_initial_multiple: float = 50.0

    first_target_percentage_allocation: float = 0.0
    second_target_percentage_allocation: float = 0.0
    third_target_percentage_allocation: float = 1.0

    def __post_init__(self):
        self.option_type = self.option_type.upper()

# ============================================================
# MODELS
# ============================================================

class Base(DeclarativeBase):
    pass


class OptionExpiry(Base):
    __tablename__ = "optionexpiry"

    ID = Column(Integer, primary_key=True)

    quote_date = Column(DateTime)
    root = Column(String(255))
    expiration = Column(DateTime)
    rootOriginal = Column(String(255))
    calendarTTE = Column(Float)


class Strike(Base):
    __tablename__ = "strike"

    ID = Column(Integer, primary_key=True)

    strike = Column(Float)
    option_type = Column(String(3))


class OptionGreeks(Base):
    __tablename__ = "optiongreeks"

    ID = Column(Integer, primary_key=True)

    OptionExpiryID = Column(
        Integer,
        ForeignKey("optionexpiry.ID")
    )

    StrikeID = Column(
        Integer,
        ForeignKey("strike.ID")
    )

    bid_1545 = Column(Float)
    ask_1545 = Column(Float)
    delta_1545 = Column(Float)

class SpxDaily(Base):
    __tablename__ = "spxdaily"

    TradeDate = Column(DateTime, primary_key=True)

    ClosePrice = Column(Float)

# ============================================================
# STRATEGY
# ============================================================

class VixCallStrategy:

    def __init__(
        self,
        session: Session,
        params: StrategyParameters
    ):
        self.session = session
        self.params = params
        self.calendar = mcal.get_calendar("NYSE")
        self.portfolio_balance = None
        self.spx_balance = None

    # --------------------------------------------------------

    def first_business_days(
        self,
        start_date,
        end_date
    ):
        schedule = self.calendar.schedule(
            start_date=start_date,
            end_date=end_date,
        )

        trading_days = pd.Series(schedule.index)

        df = pd.DataFrame(
            {"date": trading_days.dt.date}
        )

        df["month"] = (
            pd.to_datetime(df["date"])
            .dt.to_period("M")
        )

        return (
            df.groupby("month")
            .first()["date"]
            .tolist()
        )

    # --------------------------------------------------------

    def find_trade_candidate(
            self,
            trade_date,
    ):
        target_expiry = (
                pd.Timestamp(trade_date)
                + timedelta(days=self.params.dte_target)
        )

        stmt = (
            select(
                OptionExpiry,
                OptionGreeks,
                Strike,
            )
            .join(
                OptionGreeks,
                OptionGreeks.OptionExpiryID
                == OptionExpiry.ID
            )
            .join(
                Strike,
                Strike.ID
                == OptionGreeks.StrikeID
            )
            .where(
                func.date(OptionExpiry.quote_date)
                == trade_date,

                OptionExpiry.root.in_(
                    ["VIX", "VIXW"]
                ),

                OptionExpiry.rootOriginal.in_(
                    ["VIX", "VIXW"]
                ),

                OptionExpiry.expiration
                >= target_expiry,

                func.upper(Strike.option_type)
                == self.params.option_type,
            )
            .order_by(
                OptionExpiry.expiration,
                Strike.strike
            )
        )

        #compiled = stmt.compile(
        #    self.session.bind,
        #    compile_kwargs={"literal_binds": True}
        #)

        #print(compiled)

        rows = self.session.execute(stmt).all()

        if not rows:
            return None

        # Use nearest expiry >= target_expiry
        selected_expiry = rows[0][0].expiration

        expiry_rows = [
            r for r in rows
            if r[0].expiration == selected_expiry
        ]

        #for r in expiry_rows:
        #    print(
        #    f"strike={r[2].strike}, "
        #    f"delta={r[1].delta_1545}"
        #    )

        # --------------------------------------------------
        # Delta-based candidate
        # --------------------------------------------------

        delta_row = None

        if self.params.delta != 0:

            eligible = [
                r for r in expiry_rows
                if (
                        r[1].delta_1545 is not None
                        and r[1].delta_1545 <= self.params.delta
                )
            ]

            if eligible:
                delta_row = min(
                    eligible,
                    key=lambda r: r[2].strike
                )

        # --------------------------------------------------
        # Strike-based candidate
        # --------------------------------------------------

        strike_row = None

        if self.params.strike != 0:

            strike_candidates = [
                r for r in expiry_rows
                if r[2].strike >= self.params.strike
            ]

            if strike_candidates:
                strike_row = min(
                    strike_candidates,
                    key=lambda r: r[2].strike
                )

        # --------------------------------------------------
        # Selection logic
        # --------------------------------------------------

        # Both strike and delta specified
        if delta_row is not None and strike_row is not None:
            return min(
                (delta_row, strike_row),
                key=lambda r: r[2].strike
            )

        # Delta only
        if delta_row is not None:
            return delta_row

        # Strike only
        if strike_row is not None:
            return strike_row

        # --------------------------------------------------
        # Fallback
        # --------------------------------------------------

        print("Fallback used to identify strike (max(strike))")

        return max(
            expiry_rows,
            key=lambda r: r[2].strike
        )

    # --------------------------------------------------------

    def get_daily_history(
                self,
                entry_date,
                expiration,
                strike_value,
                option_type,
                root_original,
                root,
        ):
        stmt = (
            select(
                OptionExpiry.quote_date,
                OptionGreeks.bid_1545
            )
            .join(
                OptionGreeks,
                OptionGreeks.OptionExpiryID == OptionExpiry.ID
            )
            .join(
                Strike,
                Strike.ID == OptionGreeks.StrikeID
            )
            .where(
                func.date(OptionExpiry.expiration)
                == expiration.date(),

                Strike.strike == strike_value,

                func.upper(Strike.option_type)
                == option_type,

                func.date(OptionExpiry.quote_date)
                >= entry_date,

                OptionExpiry.rootOriginal == root_original,

                OptionExpiry.root == root,
            )
            .order_by(
                OptionExpiry.quote_date
            )
        )

        return self.session.execute(stmt).all()

    # --------------------------------------------------------

    def process_trade(
        self,
        option_expiry,
        greeks,
        strike,
        entry_date,
    ):
        if greeks.ask_1545 is None:
            return pd.DataFrame()

        ask = greeks.ask_1545
        entry_price = ask or 0.05
        # control for ask_1545 is zero or None, which can happen if the option is illiquid. Use a minimum price of 0.05 to avoid division by zero or negative prices.
        if not ask:
            print(f"ask_1545={ask}, defaulting entry_price to {entry_price}")

        cost_per_contract = (
                entry_price * self.params.multiplier
        )

        self.params.contracts = int(
            self.params.budget // cost_per_contract
        )

        if self.params.contracts < 1:
            return pd.DataFrame()

        spx_history = self.get_spx_history(
            entry_date,
            option_expiry.expiration,
        )

        spx_dict = {}

        for d, close in spx_history:
            spx_dict[d] = close

        initial_spx = spx_dict.get(entry_date)

        initial_portfolio_value = (
                entry_price
                * self.params.contracts
                * self.params.multiplier
                * self.params.spx_initial_multiple
        )

        if self.portfolio_balance is None:
            self.portfolio_balance = initial_portfolio_value

        if self.spx_balance is None:
            self.spx_balance = initial_portfolio_value
        starting_spx_balance = self.spx_balance

        target1_price = (
            entry_price
            * self.params.first_target_multiple
        )

        target2_price = (
            entry_price
            * self.params.second_target_multiple
        )

        target3_price = (
            entry_price
            * self.params.third_target_multiple
        )

        original_contracts = float(
            self.params.contracts
        )

        remaining_contracts = original_contracts

        realized_pnl = 0.0

        target1_hit = False
        target2_hit = False
        target3_hit = False

        first_tranche = floor(original_contracts * self.params.first_target_percentage_allocation)
        second_tranche = floor(original_contracts * self.params.second_target_percentage_allocation)
        third_tranche = floor(original_contracts * self.params.third_target_percentage_allocation)

        history = self.get_daily_history(
            entry_date,
            option_expiry.expiration,
            strike.strike,
            strike.option_type,
            option_expiry.rootOriginal,
            option_expiry.root,)

        last_quote_date = history[-1][0]

        rows = []

        # Initialize before loop
        spx_position_plus_realized_pnl = self.portfolio_balance
        previous_spx_close = None
        spx_position_current = initial_portfolio_value

        for quote_date, bid_price in history:

            bid_price = bid_price or 0.0

            realized_pnl_daily = 0.0
            spx_position_plus_realized_pnl_daily = 0.0

            spx_close = spx_dict.get(
                quote_date.date()
            )

            if spx_close is not None and initial_spx is not None:
                spx_return = (
                        spx_close / initial_spx
                )

                spx_position_current = (
                        starting_spx_balance
                        * spx_return
                )
            # -----------------------------
            # First target
            # -----------------------------

            if (
                not target1_hit
                and bid_price >= target1_price
            ):
                contracts_to_sell = first_tranche

                trade_pnl = (
                    bid_price - entry_price
                ) * (
                    contracts_to_sell
                    * self.params.multiplier
                )

                realized_pnl += trade_pnl
                realized_pnl_daily += trade_pnl

                remaining_contracts -= contracts_to_sell

                target1_hit = True

            # -----------------------------
            # Second target
            # -----------------------------

            if (
                not target2_hit
                and bid_price >= target2_price
            ):
                contracts_to_sell = second_tranche

                trade_pnl = (
                    bid_price - entry_price
                ) * (
                    contracts_to_sell
                    * self.params.multiplier
                )

                realized_pnl += trade_pnl
                realized_pnl_daily += trade_pnl

                remaining_contracts -= contracts_to_sell

                target2_hit = True

            # -----------------------------
            # Third target
            # -----------------------------

            if (
                    not target3_hit
                    and bid_price >= target3_price
            ):
                contracts_to_sell = third_tranche

                trade_pnl = (
                                        bid_price - entry_price
                                ) * (
                                        contracts_to_sell
                                        * self.params.multiplier
                                )

                realized_pnl += trade_pnl
                realized_pnl_daily += trade_pnl

                remaining_contracts -= contracts_to_sell

                target3_hit = True

            # -----------------------------
            # Expiry Exit
            # -----------------------------

            if (
                    (
                    quote_date.date() >= option_expiry.expiration.date()
                    or quote_date == last_quote_date
                    )
                and remaining_contracts > 0
            ):
                trade_pnl = (
                    bid_price - entry_price
                ) * (
                    remaining_contracts
                    * self.params.multiplier
                )
                realized_pnl += trade_pnl
                realized_pnl_daily += trade_pnl

                remaining_contracts = 0

            unrealized_value = (
                (bid_price - entry_price)
                * remaining_contracts
                * self.params.multiplier
            )

            equity = (
                    realized_pnl
                    + unrealized_value
            )

            # --------------------------------------------------
            # SPX position + realized pnl
            # --------------------------------------------------

            if spx_close is not None:

                if previous_spx_close is None:

                    spx_position_plus_realized_pnl_daily = (
                        realized_pnl_daily
                    )

                else:

                    previous_balance = (
                        spx_position_plus_realized_pnl
                    )

                    daily_spx_return = (
                                               spx_close / previous_spx_close
                                       ) - 1.0

                    spx_position_plus_realized_pnl = (
                            previous_balance
                            * (1.0 + daily_spx_return)
                            + realized_pnl_daily
                    )

                    spx_position_plus_realized_pnl_daily = (
                            spx_position_plus_realized_pnl
                            - previous_balance
                    )

                previous_spx_close = spx_close

            rows.append(
                {
                    "entry_date": entry_date,
                    "quote_date": quote_date,

                    "expiration":
                        option_expiry.expiration,

                    "strike":
                        strike.strike,

                    "delta":
                        greeks.delta_1545,

                    "entry_price":
                        entry_price,

                    "bid_price":
                        bid_price,

                    "target1":
                        target1_price,

                    "target2":
                        target2_price,

                    "target3":
                        target3_price,

                    "target1_hit":
                        target1_hit,

                    "target2_hit":
                        target2_hit,

                    "target3_hit":
                        target3_hit,

                    "remaining_contracts":
                        remaining_contracts,

                    "realized_pnl":
                        realized_pnl,

                    "realized_pnl_daily":
                        realized_pnl_daily,

                    "unrealized_value":
                        unrealized_value,

                    "equity":
                        equity,

                    "spx_close":
                        spx_close,

                    "initial_spx":
                        initial_spx,

                    "spx_position":
                        spx_position_current,

                    "spx_plus_equity":
                        spx_position_current + equity,

                    "spx_position_plus_realized_pnl":
                        spx_position_plus_realized_pnl,

                    "spx_position_plus_realized_pnl_daily":
                    spx_position_plus_realized_pnl_daily,

                }
            )

            if rows:
                self.portfolio_balance = (
                    spx_position_plus_realized_pnl
                )
                if spx_position_current is not None:
                    self.spx_balance = spx_position_current

        return pd.DataFrame(rows)

    def get_spx_history(
            self,
            entry_date,
            expiration,
    ):
        stmt = (
            select(
                SpxDaily.TradeDate,
                SpxDaily.ClosePrice
            )
            .where(
                func.date(SpxDaily.TradeDate)
                >= entry_date,

                func.date(SpxDaily.TradeDate)
                <= expiration.date()
            )
            .order_by(
                SpxDaily.TradeDate
            )
        )

        return self.session.execute(stmt).all()

    # --------------------------------------------------------

    def run(
        self,
        start_date,
        end_date,
    ):
        first_days = self.first_business_days(
            start_date,
            end_date,
        )

        results = []

        for entry_date in first_days:

            trade = self.find_trade_candidate(
                entry_date
            )

            if trade is None:
                print(f"No candidate found for {entry_date}")
                continue

            option_expiry, greeks, strike = trade

            print(
                f"Processing Trade | "
                f"Entry={entry_date} | "
                f"Expiry={option_expiry.expiration.date()} | "
                f"Strike={strike.strike} | "
                f"Delta={greeks.delta_1545} | "
                f"Type={strike.option_type} | "
                f"Ask1545={greeks.ask_1545} | "
                f"Budget={self.params.budget}"
            )

            trade_df = self.process_trade(
                option_expiry,
                greeks,
                strike,
                entry_date,
            )

            if not trade_df.empty:
                results.append(trade_df)

        if not results:
            return pd.DataFrame()

        return pd.concat(
            results,
            ignore_index=True,
        )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    DATABASE_URL = ("mysql+pymysql://root:Bright1@localhost:3306/Vol_test")

    engine = create_engine(
        DATABASE_URL,
        future=True,
    )
    ## If strike and delta are set, use minimum of these. If only one is set, use that. Else, use fallback.
    params = StrategyParameters(
        dte_target=42,
        strike=70.0,
        delta=0.01,
        option_type="C",
        contracts=0, # not required to be set, is updated later in code
        budget=1000.0,
        multiplier=100,
        first_target_multiple=10,
        second_target_multiple=40,
        third_target_multiple=100,
        first_target_percentage_allocation = 0.0,
        second_target_percentage_allocation = 0.0,
        third_target_percentage_allocation = 1.0,
        spx_initial_multiple=200.0, # SPX position is this amount times budget
    )

    with Session(engine) as session:

        strategy = VixCallStrategy(
            session=session,
            params=params,
        )

        results = strategy.run(
            start_date="2006-01-01",
            end_date="2026-07-31",
        )

        print(results.head())
        print(results.tail())

        if results.empty:
            raise ValueError(
                "No trades were generated. Check trade selection criteria."
            )

        excel_file = "vix_long_call_strategy.xlsx"

        summary_rows = []

        for expiry, df_expiry in results.groupby("expiration"):
            df_expiry = df_expiry.sort_values("quote_date")

            first_row = df_expiry.iloc[0]
            last_row = df_expiry.iloc[-1]

            summary_rows.append(
                {
                    "expiration": expiry,
                    "first_quote_date": first_row["quote_date"],
                    "last_quote_date": last_row["quote_date"],
                    "strike": first_row["strike"],
                    "delta_1545": first_row["delta"],
                    "entry_price": first_row["entry_price"],
                    "initial_contracts": first_row["remaining_contracts"],
                    "first_spx_position": first_row["spx_position"],
                    "last_spx_position": last_row["spx_position"],
                    "first_spx_plus_equity":
                        first_row["spx_plus_equity"],
                    "last_spx_plus_equity":
                        last_row["spx_plus_equity"],
                    "SPX return": last_row["spx_position"] / first_row["spx_position"] - 1,
                    "Strategy return": last_row["spx_plus_equity"] / first_row["spx_plus_equity"] - 1,
                    "Strategy_gain_dollar": last_row["spx_plus_equity"] - last_row["spx_position"],
                    "Strategy_gain_percentage_portfolio": (last_row["spx_plus_equity"] - last_row["spx_position"]) / first_row["spx_plus_equity"],
                }
            )

        summary_df = pd.DataFrame(summary_rows)

        # Sort by expiry so cumulative returns are in chronological order
        summary_df = summary_df.sort_values("expiration")

        summary_df["SPX_return_cumulative"] = (
            (1 + summary_df["SPX return"])
            .cumprod()
        )

        summary_df["Strategy_return_cumulative"] = (
            (1 + summary_df["Strategy return"])
            .cumprod()
        )

        # ==========================================================
        # SummaryByDate
        # Rows = quote dates
        # Columns = expiries
        # Values = realized_pnl_daily
        # ==========================================================

        summary_by_date = results.copy()

        summary_by_date["quote_date"] = pd.to_datetime(
            summary_by_date["quote_date"]
        ).dt.date

        summary_by_date["expiration"] = pd.to_datetime(
            summary_by_date["expiration"]
        ).dt.date

        summary_by_date = (
            summary_by_date
            .pivot_table(
                index="quote_date",
                columns="expiration",
                values="realized_pnl_daily",
                aggfunc="last",
            )
            .sort_index()
        )

        # Total across all expiries for each date
        summary_by_date["DailyTotal"] = summary_by_date.sum(
            axis=1,
            skipna=True
        )

        # Running cumulative total
        summary_by_date["DailyTotalCumulative"] = (
            summary_by_date["DailyTotal"]
            .cumsum()
        )

        # SPX close for each quote date
        spx_close_by_date = (
            results.copy()
        )

        spx_close_by_date["quote_date"] = pd.to_datetime(
            spx_close_by_date["quote_date"]
        ).dt.date

        spx_close_by_date = (
            spx_close_by_date
            .groupby("quote_date")["spx_close"]
            .last()
        )

        summary_by_date["SPX_Close"] = (
            spx_close_by_date
        )

        initial_portfolio_value = (
                params.spx_initial_multiple
                * params.budget
        )

        first_spx_close = (
            summary_by_date["SPX_Close"]
            .dropna()
            .iloc[0]
        )

        summary_by_date["SPX_Portfolio"] = (
                summary_by_date["SPX_Close"]
                / first_spx_close
                * initial_portfolio_value
        )

        # Daily % change in SPX
        summary_by_date["SPX_Daily_Return"] = (
            summary_by_date["SPX_Close"]
            .pct_change()
            .fillna(0.0)
        )

        # New portfolio with protection calculation
        portfolio_with_protection_new = []

        previous_value = initial_portfolio_value

        for _, row in summary_by_date.iterrows():
            current_value = (
                    row["DailyTotal"]
                    + (1.0 + row["SPX_Daily_Return"]) * previous_value
            )

            portfolio_with_protection_new.append(current_value)

            previous_value = current_value

        summary_by_date["Portfolio_with_protection_new"] = (
            portfolio_with_protection_new
        )

        summary_by_date["Portfolio_with_protection"] = (
                #summary_by_date["SPX_Portfolio"]
                initial_portfolio_value
                + summary_by_date["DailyTotalCumulative"]
        )

        summary_by_date = summary_by_date.reset_index()

        with pd.ExcelWriter(
                excel_file,
                engine="openpyxl"
        ) as writer:

            summary_df.to_excel(
                writer,
                sheet_name="Summary",
                index=False,
            )

            summary_by_date.to_excel(
                writer,
                sheet_name = "SummaryByDate",
                index = False,
            )

            for expiry, df_expiry in results.groupby("expiration"):
                sheet_name = pd.Timestamp(expiry).strftime(
                    "%Y-%m-%d"
                )

                df_expiry.to_excel(
                    writer,
                    sheet_name=sheet_name,
                    index=False,
                )

        print(f"Written {excel_file}")

        print(
            f"Rows written: {len(results):,}"
        )