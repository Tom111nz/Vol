
import QuantLib as ql
from dataclasses import dataclass
import math
from IBKR.Constant import *
from IBKR.RequestMarketData import *
from IBKR.Connect import connect

@dataclass
class Black76Inputs:
    forward: float
    strike: float
    volatility: float
    expiry: float
    risk_free_rate: float
    is_call: bool = True

def black76_greeks(params: Black76Inputs):

    payoff = ql.PlainVanillaPayoff(
        ql.Option.Call if params.is_call else ql.Option.Put,
        params.strike
    )

    calc = ql.BlackCalculator(
        payoff,
        params.forward,
        params.volatility * math.sqrt(params.expiry),
        math.exp(-params.risk_free_rate * params.expiry)
    )

    return {
        "price": calc.value(),
        "delta": calc.deltaForward(),
        "gamma": calc.gammaForward(),
        "vega": calc.vega(params.expiry),
        "theta": calc.theta(params.forward, params.expiry),
        "thetaPerDay": calc.thetaPerDay(params.forward, params.expiry),
        "rho": calc.rho(params.expiry),
        "vanna": calc.vanna(params.forward, params.expiry),
        "volga": calc.volga(params.expiry),
        "impliedVol": params.volatility,
    }


def forward_from_put_call_parity(
    call_price: float,
    put_price: float,
    strike: float,
    risk_free_rate: float,
    expiry: float,
) -> float:
    return strike + (call_price - put_price) * math.exp(risk_free_rate * expiry)


expiryTargetBusinessDaysAhead = 3 # this is based on CBOE dates (not NZ dates), so 0 is 0DTE expiry option
strike = 7530
riskFreeRate = 0.04
## request some IBKR greeks compare them to QuantLib
## IBKR
reqMarketDataType = 1 # (1=live,2=frozen,3=delayed,4=delayed-frozen)
ib = connect(reqMarketDataType)
spxSpot = getSpxSpot(ib, False)
#chain_spxw = getSpxOptions(ib)
optionType = P
optionTypeBlack76 = (optionType == C)
dateXDaysAhead = getMarketDateInFuture(expiryTargetBusinessDaysAhead)  # remembering we are a day in front of CBOE
optionPut = buildOption(dateXDaysAhead, strike, optionType, SPXW)
#qualified = ib.qualifyContracts(optionPut)
put_bid, put_ask, put_delta, put_gamma, put_vega, put_theta, put_impliedVol, put_optPrice, put_undPrice, put_ttm, put_expiryDateTime  = requestBidAskandGreeks(ib, optionPut)
#optionCall = buildOption(dateXDaysAhead, strike, P if optionType == C else C, SPXW)
#qualified = ib.qualifyContracts(optionCall)
#call_bid, call_ask, call_delta, call_gamma, call_vega, call_theta, call_impliedVol, call_optPrice, call_undPrice, call_ttm, call_expiryDateTime  = requestBidAskandGreeks(ib, optionCall)
forward = spxSpot#forward_from_put_call_parity(call_bid, put_bid, strike, riskFreeRate, put_ttm)
print(f"Forward: {forward}")
## quantlib
trade = Black76Inputs(
    forward=forward,
    strike=strike,
    volatility=put_impliedVol,
    expiry=put_ttm,
    risk_free_rate=riskFreeRate,
    is_call=optionTypeBlack76
)

result = black76_greeks(trade)
for greek, value in result.items():
    print(f"{greek}: {value:.6f}")

print("IBKR")
variables = {
    "put_bid": put_bid,
    "put_ask": put_ask,
    "put_delta": put_delta,
    "put_gamma": put_gamma,
    "put_vega": put_vega,
    "put_theta": put_theta,
    "put_impliedVol": put_impliedVol,
    "put_optPrice": put_optPrice,
    "put_undPrice": put_undPrice,
    "put_ttm": put_ttm,
    "put_expiryDateTime": put_expiryDateTime,
}

for name, value in variables.items():
    print(f"{name} = {value}")