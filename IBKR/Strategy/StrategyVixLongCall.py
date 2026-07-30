from dataclasses import dataclass
from datetime import timedelta

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
    option_type: str = "C"

    contracts: int = 2
    multiplier: int = 100

    first_target_multiple: float = 50.0
    second_target_multiple: float = 100.0
    third_target_multiple: float = 150.0

    spx_inital_multiple: float = 50.0

    first_target_fraction: float = 0.50
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
                func.date(OptionExpiry.quote_date) == trade_date,

                OptionExpiry.root.in_(
                    ["VIX", "VIXW"]
                ),
                OptionExpiry.rootOriginal.in_(
                    ["VIX", "VIXW"]
                ),

                OptionExpiry.expiration >=
                target_expiry,

                Strike.option_type ==
                self.params.option_type,

                Strike.strike ==
                self.params.strike,
            )
            .order_by(
                OptionExpiry.expiration
            )
        )

        return self.session.execute(stmt).first()

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

        entry_price = greeks.ask_1545

        spx_history = self.get_spx_history(
            entry_date,
            option_expiry.expiration,
        )

        spx_dict = {}

        for d, close in spx_history:
            spx_dict[d] = close

        initial_spx = spx_dict.get(entry_date)

        spx_position_value = (
                entry_price
                * self.params.contracts
                * self.params.multiplier
                * self.params.spx_inital_multiple
        )

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

        first_tranche = original_contracts / 4.0
        second_tranche = original_contracts / 4.0
        third_tranche = original_contracts / 4.0

        history = self.get_daily_history(
            entry_date,
            option_expiry.expiration,
            strike.strike,
            strike.option_type,
            option_expiry.rootOriginal,
            option_expiry.root,)

        rows = []

        for quote_date, bid_price in history:

            bid_price = bid_price or 0.0

            spx_close = spx_dict.get(
                quote_date.date()
            )

            if spx_close is not None and initial_spx is not None:
                spx_return = (
                        spx_close / initial_spx
                )

                spx_position_current = (
                        spx_position_value
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

                realized_pnl += (
                    bid_price - entry_price
                ) * (
                    contracts_to_sell
                    * self.params.multiplier
                )

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

                realized_pnl += (
                    bid_price - entry_price
                ) * (
                    contracts_to_sell
                    * self.params.multiplier
                )

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

                realized_pnl += (
                                        bid_price - entry_price
                                ) * (
                                        contracts_to_sell
                                        * self.params.multiplier
                                )

                remaining_contracts -= contracts_to_sell

                target3_hit = True

            # -----------------------------
            # Expiry Exit
            # -----------------------------

            if (
                quote_date.date()
                >= option_expiry.expiration.date()
                and remaining_contracts > 0
            ):
                realized_pnl += (
                    bid_price - entry_price
                ) * (
                    remaining_contracts
                    * self.params.multiplier
                )

                remaining_contracts = 0

            unrealized_value = (
                bid_price
                * remaining_contracts
                * self.params.multiplier
            )

            equity = (
                realized_pnl
                + unrealized_value
            )

            rows.append(
                {
                    "entry_date": entry_date,
                    "quote_date": quote_date,

                    "expiration":
                        option_expiry.expiration,

                    "strike":
                        strike.strike,

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

                    "spx_plus_realized_pnl":
                        spx_position_current + realized_pnl,

                }
            )

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
                continue

            option_expiry, greeks, strike = trade

            print(
                f"Processing Trade | "
                f"Entry={entry_date} | "
                f"Expiry={option_expiry.expiration.date()} | "
                f"Strike={strike.strike} | "
                f"Type={strike.option_type} | "
                f"Ask1545={greeks.ask_1545}"
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

    params = StrategyParameters(
        dte_target=42,
        strike=60.0,
        option_type="C",
        contracts=4,
        multiplier=100,
        first_target_multiple=10,
        second_target_multiple=40,
        third_target_multiple=100,
        first_target_fraction=0.50,
        spx_inital_multiple=50.0,
    )

    with Session(engine) as session:

        strategy = VixCallStrategy(
            session=session,
            params=params,
        )

        results = strategy.run(
            start_date="2008-01-01",
            end_date="2008-12-31",
        )

        print(results.head())
        print(results.tail())

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
                    "entry_price": first_row["entry_price"],
                    "contracts": params.contracts,
                    "first_spx_position": first_row["spx_position"],
                    "last_spx_position": last_row["spx_position"],
                    "first_spx_plus_realized_pnl":
                        first_row["spx_plus_realized_pnl"],
                    "last_spx_plus_realized_pnl":
                        last_row["spx_plus_realized_pnl"],
                    "SPX return": last_row["spx_position"] / first_row["spx_position"] - 1,
                    "Strategy return": last_row["spx_plus_realized_pnl"] / first_row["spx_plus_realized_pnl"] - 1,
                    "Strategy_gain_dollar": last_row["spx_plus_realized_pnl"] - last_row["spx_position"],
                    "Strategy_gain_percentage_portfolio": (last_row["spx_plus_realized_pnl"] - last_row["spx_position"]) / first_row["spx_plus_realized_pnl"],
                }
            )

        summary_df = pd.DataFrame(summary_rows)

        with pd.ExcelWriter(
                excel_file,
                engine="openpyxl"
        ) as writer:

            summary_df.to_excel(
                writer,
                sheet_name="Summary",
                index=False,
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