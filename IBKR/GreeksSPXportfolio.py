from IBKR.GreeksSPX import *
spot = 7000
strike1 = 6800
strike2 = 6300
position1 = {
    "quantity": 0,
    "spot": spot,
    "strike": strike1,
    "time_to_expiry": 30 / 365,
    "volatility": 0.20,
    "risk_free_rate": 0.05,
    "dividend_yield": 0.015,
    "option_type": "put"
}
position2 = {
    "quantity": 1,
    "spot": spot,
    "strike": strike2,
    "time_to_expiry": 30 / 365,
    "volatility": 0.15,
    "risk_free_rate": 0.05,
    "dividend_yield": 0.015,
    "option_type": "put"
}
positions = [position1, position2]
result = portfolio_delta(positions)
print(result["delta_index"])
print(result["delta_notional"])
result = portfolio_vega(positions)
print(result["vega_index"])
print(result["vega_notional"])
