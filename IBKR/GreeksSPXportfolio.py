from IBKR.GreeksSPX import *
spot = 7515.9
strike1 = 6800
strike2 = 6880
position1 = {
    "quantity": 0,
    "spot": spot,
    "strike": strike1,
    "time_to_expiry": 30 / 360,
    "volatility": 0.20,
    "risk_free_rate": 0.043,
    "dividend_yield": 0.01,
    "option_type": "put"
}
position2 = {
    "quantity": 1,
    "spot": spot,
    "strike": strike2,
    "time_to_expiry": 37 / 360,
    "volatility": 0.144,
    "risk_free_rate": 0.043,
    "dividend_yield": 0.01,
    "option_type": "put"
}
positions = [position1, position2]
result = portfolio_delta(positions)
print(result["delta_index"])
print(result["delta_notional"])
result = portfolio_vega(positions)
print(result["vega_index"])
print(result["vega_notional"])
result = portfolio_theta(positions)
print(result["theta_annual_index"])
print(result["theta_daily_index"])
pricer = price(spot, strike2, 37 / 360, 0.22192, 0.05, 0.015, 'put')
print(pricer)
forward = forward_price(spot, 37 / 360, 0.043, 0.01)
print(forward)
