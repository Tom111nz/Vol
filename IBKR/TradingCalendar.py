from zoneinfo import ZoneInfo

import pandas as pd
from datetime import datetime
from pandas.tseries.holiday import (
    AbstractHolidayCalendar, Holiday, nearest_workday,
    USMartinLutherKingJr, USPresidentsDay, GoodFriday,
    USMemorialDay, USLaborDay, USThanksgivingDay
)
from pandas.tseries.offsets import CustomBusinessDay


class USTradingCalendar(AbstractHolidayCalendar):
    rules = [
        # New Year's Day
        Holiday('NewYearsDay', month=1, day=1, observance=nearest_workday),

        # Martin Luther King Jr. Day
        USMartinLutherKingJr,

        # Presidents Day
        USPresidentsDay,

        # Good Friday (VERY important: market closed, not a federal holiday)
        GoodFriday,

        # Memorial Day
        USMemorialDay,

        # Independence Day
        Holiday('IndependenceDay', month=7, day=4, observance=nearest_workday),

        # Labor Day
        USLaborDay,

        # Thanksgiving
        USThanksgivingDay,

        # Christmas
        Holiday('Christmas', month=12, day=25, observance=nearest_workday),
    ]


def getMarketDateInFuture(daysInFuture: int, tz: str = "America/New_York"):
    us_trading_bd = CustomBusinessDay(calendar=USTradingCalendar())
    start = pd.Timestamp(datetime.now(ZoneInfo(tz)).date())  # normalize to date in US timezone
    result = start + daysInFuture * us_trading_bd
    return result.date()