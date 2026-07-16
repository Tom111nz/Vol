# GreeksSPX.py
from typing import Any

import numpy as np
from numpy import dtype, ndarray

from scipy.stats import norm
from scipy.optimize import brentq

SPX_MULTIPLIER = 100.0

EPSILON = 1e-12


# ============================================================
# Validation
# ============================================================

def _validate_option_type(option_type):
    option_type = option_type.lower()

    if option_type not in ("call", "put"):
        raise ValueError(
            "option_type must be 'call' or 'put'"
        )

    return option_type


def _validate_inputs(
    spot,
    strike,
    time_to_expiry,
    volatility
):
    if spot <= 0:
        raise ValueError("spot must be > 0")

    if strike <= 0:
        raise ValueError("strike must be > 0")

    if time_to_expiry < 0:
        raise ValueError(
            "time_to_expiry must be >= 0"
        )

    if volatility < 0:
        raise ValueError(
            "volatility must be >= 0"
        )


def _make_notional(raw):
    return raw * SPX_MULTIPLIER


# ============================================================
# Forward
# ============================================================

def forward_price(
    spot,
    risk_free_rate,
    dividend_yield,
    time_to_expiry,
):
    return (
        spot
        * np.exp(
            (risk_free_rate - dividend_yield)
            * time_to_expiry
        )
    )


# ============================================================
# d1 d2
# ============================================================

def d1(
    spot,
    strike,
    time_to_expiry,
    volatility,
    risk_free_rate,
    dividend_yield,
):

    _validate_inputs(
        spot,
        strike,
        time_to_expiry,
        volatility
    )

    F = forward_price(
        spot,
        risk_free_rate,
        dividend_yield,
        time_to_expiry,
    )

    if (
        time_to_expiry <= EPSILON
        or volatility <= EPSILON
    ):
        if F > strike:
            return np.inf
        elif F < strike:
            return -np.inf
        return 0.0

    return (
        np.log(F / strike)
        + 0.5 * volatility**2
        * time_to_expiry
    ) / (
        volatility
        * np.sqrt(time_to_expiry)
    )


def d2(
    spot,
    strike,
    time_to_expiry,
    volatility,
    risk_free_rate,
    dividend_yield,
):
    return (
        d1(
            spot,
            strike,
            time_to_expiry,
            volatility,
            risk_free_rate,
            dividend_yield,
        )
        - volatility
        * np.sqrt(time_to_expiry)
    )


# ============================================================
# Black 76 Price
# ============================================================

def price(
        spot: object,
        strike: object,
        time_to_expiry: object,
        volatility: object,
        risk_free_rate: object,
        dividend_yield: object,
        option_type: object,
) -> ndarray[tuple[Any, ...], dtype[Any]] | Any:

    option_type = _validate_option_type(
        option_type
    )

    F = forward_price(
        spot,
        risk_free_rate,
        dividend_yield,
        time_to_expiry,
    )

    df = np.exp(
        -risk_free_rate
        * time_to_expiry
    )

    if (
        volatility <= EPSILON
        or time_to_expiry <= EPSILON
    ):
        intrinsic = (
            max(F - strike, 0.0)
            if option_type == "call"
            else max(strike - F, 0.0)
        )

        return df * intrinsic

    d_1 = d1(
        spot,
        strike,
        time_to_expiry,
        volatility,
        risk_free_rate,
        dividend_yield,
    )

    d_2 = d_1 - volatility * np.sqrt(
        time_to_expiry
    )

    if option_type == "call":
        return df * (
            F * norm.cdf(d_1)
            - strike * norm.cdf(d_2)
        )

    return df * (
        strike * norm.cdf(-d_2)
        - F * norm.cdf(-d_1)
    )


# ============================================================
# Delta
# dV/dS
# ============================================================

def delta(
    spot,
    strike,
    time_to_expiry,
    volatility,
    risk_free_rate,
    dividend_yield,
    option_type,
):

    option_type = _validate_option_type(
        option_type
    )

    d_1 = d1(
        spot,
        strike,
        time_to_expiry,
        volatility,
        risk_free_rate,
        dividend_yield,
    )

    dq = np.exp(
        -dividend_yield
        * time_to_expiry
    )

    if option_type == "call":
        raw = dq * norm.cdf(d_1)
    else:
        raw = dq * (
            norm.cdf(d_1) - 1.0
        )

    return {
        "delta_index": raw,
        "delta_notional": _make_notional(raw),
    }


# ============================================================
# Gamma
# d2V/dS2
# ============================================================

def gamma(
    spot,
    strike,
    time_to_expiry,
    volatility,
    risk_free_rate,
    dividend_yield,
):

    if (
        volatility <= EPSILON
        or time_to_expiry <= EPSILON
    ):
        raw = 0.0

    else:

        d_1 = d1(
            spot,
            strike,
            time_to_expiry,
            volatility,
            risk_free_rate,
            dividend_yield,
        )

        raw = (
            np.exp(
                -dividend_yield
                * time_to_expiry
            )
            * norm.pdf(d_1)
            / (
                spot
                * volatility
                * np.sqrt(time_to_expiry)
            )
        )

    return {
        "gamma_index": raw,
        "gamma_notional": _make_notional(raw),
    }


# ============================================================
# Vega
# dV/dVol
# ============================================================

def vega(
    spot,
    strike,
    time_to_expiry,
    volatility,
    risk_free_rate,
    dividend_yield,
):

    F = forward_price(
        spot,
        risk_free_rate,
        dividend_yield,
        time_to_expiry,
    )

    d_1 = d1(
        spot,
        strike,
        time_to_expiry,
        volatility,
        risk_free_rate,
        dividend_yield,
    )

    raw = (
        np.exp(
            -risk_free_rate
            * time_to_expiry
        )
        * F
        * norm.pdf(d_1)
        * np.sqrt(time_to_expiry)
    )

    return {
        "vega_index": raw,
        "vega_notional": _make_notional(raw),
    }


# ============================================================
# Volga (Vomma)
# Vega*d1*d2/vol
# ============================================================

def volga(
    spot,
    strike,
    time_to_expiry,
    volatility,
    risk_free_rate,
    dividend_yield,
):

    if volatility <= EPSILON:
        raw = 0.0

    else:

        d_1 = d1(
            spot,
            strike,
            time_to_expiry,
            volatility,
            risk_free_rate,
            dividend_yield,
        )

        d_2 = d2(
            spot,
            strike,
            time_to_expiry,
            volatility,
            risk_free_rate,
            dividend_yield,
        )

        raw = (
            vega(
                spot,
                strike,
                time_to_expiry,
                volatility,
                risk_free_rate,
                dividend_yield,
            )["vega_index"]
            * d_1
            * d_2
            / volatility
        )

    return {
        "volga_index": raw,
        "volga_notional": _make_notional(raw),
    }


# ============================================================
# Vanna
# dDelta/dVol
# ============================================================

def vanna(
    spot,
    strike,
    time_to_expiry,
    volatility,
    risk_free_rate,
    dividend_yield,
):

    d_1 = d1(
        spot,
        strike,
        time_to_expiry,
        volatility,
        risk_free_rate,
        dividend_yield,
    )

    d_2 = d2(
        spot,
        strike,
        time_to_expiry,
        volatility,
        risk_free_rate,
        dividend_yield,
    )

    raw = (
        -np.exp(
            -dividend_yield
            * time_to_expiry
        )
        * norm.pdf(d_1)
        * d_2
        / volatility
    )

    return {
        "vanna_index": raw,
        "vanna_notional": _make_notional(raw),
    }


# ============================================================
# Rho
# dV/dr
# ============================================================

def rho(
    spot,
    strike,
    time_to_expiry,
    volatility,
    risk_free_rate,
    dividend_yield,
    option_type,
):

    raw = (
        -time_to_expiry
        * price(
            spot,
            strike,
            time_to_expiry,
            volatility,
            risk_free_rate,
            dividend_yield,
            option_type,
        )
    )

    return {
        "rho_index": raw,
        "rho_notional": _make_notional(raw),
    }


# ============================================================
# Theta
# ============================================================

def theta(
    spot,
    strike,
    time_to_expiry,
    volatility,
    risk_free_rate,
    dividend_yield,
    option_type,
):

    px = price(
        spot,
        strike,
        time_to_expiry,
        volatility,
        risk_free_rate,
        dividend_yield,
        option_type,
    )

    vg = vega(
        spot,
        strike,
        time_to_expiry,
        volatility,
        risk_free_rate,
        dividend_yield,
    )["vega_index"]

    annual = (
        -(vg * volatility)
        / (
            2.0
            * np.sqrt(
                max(
                    time_to_expiry,
                    EPSILON
                )
            )
        )
        - risk_free_rate * px
    )

    daily = annual / 365.0

    return {
        "theta_annual_index": annual,
        "theta_daily_index": daily,
        "theta_annual_notional":
            _make_notional(annual),
        "theta_daily_notional":
            _make_notional(daily),
    }


# ============================================================
# Dual Delta
# dV/dK
# ============================================================

def dual_delta(
    spot,
    strike,
    time_to_expiry,
    volatility,
    risk_free_rate,
    dividend_yield,
    option_type,
):

    option_type = _validate_option_type(
        option_type
    )

    d_2 = d2(
        spot,
        strike,
        time_to_expiry,
        volatility,
        risk_free_rate,
        dividend_yield,
    )

    df = np.exp(
        -risk_free_rate
        * time_to_expiry
    )

    raw = (
        -df * norm.cdf(d_2)
        if option_type == "call"
        else df * norm.cdf(-d_2)
    )

    return {
        "dual_delta_index": raw,
        "dual_delta_notional":
            _make_notional(raw),
    }


# ============================================================
# Dual Gamma
# d2V/dK2
# ============================================================

def dual_gamma(
    spot,
    strike,
    time_to_expiry,
    volatility,
    risk_free_rate,
    dividend_yield,
):

    d_2 = d2(
        spot,
        strike,
        time_to_expiry,
        volatility,
        risk_free_rate,
        dividend_yield,
    )

    raw = (
        np.exp(
            -risk_free_rate
            * time_to_expiry
        )
        * norm.pdf(d_2)
        / (
            strike
            * volatility
            * np.sqrt(time_to_expiry)
        )
    )

    return {
        "dual_gamma_index": raw,
        "dual_gamma_notional":
            _make_notional(raw),
    }


# ============================================================
# Probability ITM
# ============================================================

def probability_itm(
    spot,
    strike,
    time_to_expiry,
    volatility,
    risk_free_rate,
    dividend_yield,
    option_type,
):

    d_2 = d2(
        spot,
        strike,
        time_to_expiry,
        volatility,
        risk_free_rate,
        dividend_yield
    )

    if option_type.lower() == "call":
        return norm.cdf(d_2)

    return norm.cdf(-d_2)


# ============================================================
# Expected Move
# ============================================================

def expected_move(
    spot,
    volatility,
    time_to_expiry
):
    return (
        spot
        * volatility
        * np.sqrt(time_to_expiry)
    )


# ============================================================
# Implied Volatility
# ============================================================

def implied_volatility(
    market_price,
    spot,
    strike,
    time_to_expiry,
    risk_free_rate,
    dividend_yield,
    option_type
):

    def objective(vol):

        return (
            price(
                spot,
                strike,
                time_to_expiry,
                vol,
                risk_free_rate,
                dividend_yield,
                option_type
            )
            - market_price
        )

    try:

        return brentq(
            objective,
            1e-6,
            5.0,
            maxiter=500
        )

    except Exception:
        return np.nan

# ============================================================
# Charm
# d(Delta) / d(Time)
# ============================================================

def charm(
    spot,
    strike,
    time_to_expiry,
    volatility,
    risk_free_rate,
    dividend_yield,
    option_type,
):

    option_type = _validate_option_type(
        option_type
    )

    if (
        time_to_expiry <= EPSILON
        or volatility <= EPSILON
    ):
        raw = 0.0

    else:

        d_1 = d1(
            spot,
            strike,
            time_to_expiry,
            volatility,
            risk_free_rate,
            dividend_yield,
        )

        d_2 = d2(
            spot,
            strike,
            time_to_expiry,
            volatility,
            risk_free_rate,
            dividend_yield,
        )

        phi = norm.pdf(d_1)

        raw = (
            np.exp(
                -dividend_yield
                * time_to_expiry
            )
            * phi
            * (
                (
                    2.0
                    * (risk_free_rate - dividend_yield)
                    * time_to_expiry
                    - d_2
                    * volatility
                    * np.sqrt(time_to_expiry)
                )
                /
                (
                    2.0
                    * time_to_expiry
                    * volatility
                    * np.sqrt(time_to_expiry)
                )
            )
            -
            dividend_yield
            *
            (
                np.exp(
                    -dividend_yield
                    * time_to_expiry
                )
                * norm.cdf(d_1)
            )
        )

        if option_type == "put":
            raw += (
                dividend_yield
                * np.exp(
                    -dividend_yield
                    * time_to_expiry
                )
            )

    return {
        "charm_index": raw,
        "charm_notional":
            _make_notional(raw),
    }


# ============================================================
# Veta
# d(Vega) / d(Time)
# ============================================================

def veta(
    spot,
    strike,
    time_to_expiry,
    volatility,
    risk_free_rate,
    dividend_yield,
):

    if (
        time_to_expiry <= EPSILON
        or volatility <= EPSILON
    ):
        raw = 0.0

    else:

        F = forward_price(
            spot,
            risk_free_rate,
            dividend_yield,
            time_to_expiry,
        )

        d_1 = d1(
            spot,
            strike,
            time_to_expiry,
            volatility,
            risk_free_rate,
            dividend_yield,
        )

        d_2 = d2(
            spot,
            strike,
            time_to_expiry,
            volatility,
            risk_free_rate,
            dividend_yield,
        )

        raw = (
            np.exp(
                -risk_free_rate
                * time_to_expiry
            )
            * F
            * norm.pdf(d_1)
            * np.sqrt(time_to_expiry)
            *
            (
                dividend_yield
                +
                (
                    (risk_free_rate - dividend_yield)
                    * d_1
                )
                /
                (
                    volatility
                    * np.sqrt(time_to_expiry)
                )
                -
                (
                    1.0
                    + d_1 * d_2
                )
                /
                (
                    2.0
                    * time_to_expiry
                )
            )
        )

    return {
        "veta_index": raw,
        "veta_notional":
            _make_notional(raw),
    }


# ============================================================
# Speed
# d(Gamma) / d(Spot)
# ============================================================

def speed(
    spot,
    strike,
    time_to_expiry,
    volatility,
    risk_free_rate,
    dividend_yield,
):

    if (
        time_to_expiry <= EPSILON
        or volatility <= EPSILON
    ):
        raw = 0.0

    else:

        gam = gamma(
            spot,
            strike,
            time_to_expiry,
            volatility,
            risk_free_rate,
            dividend_yield,
        )["gamma_index"]

        d_1 = d1(
            spot,
            strike,
            time_to_expiry,
            volatility,
            risk_free_rate,
            dividend_yield,
        )

        raw = (
            -gam
            / spot
            *
            (
                1.0
                +
                d_1
                /
                (
                    volatility
                    * np.sqrt(time_to_expiry)
                )
            )
        )

    return {
        "speed_index": raw,
        "speed_notional":
            _make_notional(raw),
    }


# ============================================================
# Zomma
# d(Gamma) / d(Volatility)
# ============================================================

def zomma(
    spot,
    strike,
    time_to_expiry,
    volatility,
    risk_free_rate,
    dividend_yield,
):

    if (
        volatility <= EPSILON
        or time_to_expiry <= EPSILON
    ):
        raw = 0.0

    else:

        gam = gamma(
            spot,
            strike,
            time_to_expiry,
            volatility,
            risk_free_rate,
            dividend_yield,
        )["gamma_index"]

        d_1 = d1(
            spot,
            strike,
            time_to_expiry,
            volatility,
            risk_free_rate,
            dividend_yield,
        )

        d_2 = d2(
            spot,
            strike,
            time_to_expiry,
            volatility,
            risk_free_rate,
            dividend_yield,
        )

        raw = (
            gam
            *
            (
                d_1
                * d_2
                - 1.0
            )
            / volatility
        )

    return {
        "zomma_index": raw,
        "zomma_notional":
            _make_notional(raw),
    }


# ============================================================
# Color
# d(Gamma) / d(Time)
# ============================================================

def color(
    spot,
    strike,
    time_to_expiry,
    volatility,
    risk_free_rate,
    dividend_yield,
):

    if (
        volatility <= EPSILON
        or time_to_expiry <= EPSILON
    ):
        raw = 0.0

    else:

        gam = gamma(
            spot,
            strike,
            time_to_expiry,
            volatility,
            risk_free_rate,
            dividend_yield,
        )["gamma_index"]

        d_1 = d1(
            spot,
            strike,
            time_to_expiry,
            volatility,
            risk_free_rate,
            dividend_yield,
        )

        d_2 = d2(
            spot,
            strike,
            time_to_expiry,
            volatility,
            risk_free_rate,
            dividend_yield,
        )

        raw = (
            -gam
            *
            (
                dividend_yield
                +
                (
                    2.0
                    * (risk_free_rate - dividend_yield)
                    * time_to_expiry
                    - d_2
                    * volatility
                    * np.sqrt(time_to_expiry)
                )
                /
                (
                    2.0
                    * time_to_expiry
                )
                *
                d_1
                /
                (
                    volatility
                    * np.sqrt(time_to_expiry)
                )
                +
                1.0
                /
                (
                    2.0
                    * time_to_expiry
                )
            )
        )

    return {
        "color_index": raw,
        "color_notional":
            _make_notional(raw),
    }


# ============================================================
# Ultima
# d(Volga) / d(Volatility)
# ============================================================

def ultima(
    spot,
    strike,
    time_to_expiry,
    volatility,
    risk_free_rate,
    dividend_yield,
):

    if (
        volatility <= EPSILON
        or time_to_expiry <= EPSILON
    ):
        raw = 0.0

    else:

        volga_value = volga(
            spot,
            strike,
            time_to_expiry,
            volatility,
            risk_free_rate,
            dividend_yield,
        )["volga_index"]

        d_1 = d1(
            spot,
            strike,
            time_to_expiry,
            volatility,
            risk_free_rate,
            dividend_yield,
        )

        d_2 = d2(
            spot,
            strike,
            time_to_expiry,
            volatility,
            risk_free_rate,
            dividend_yield,
        )

        raw = (
            volga_value
            / volatility
            *
            (
                d_1 * d_2
                -
                (
                    d_1 / d_2
                )
                -
                (
                    d_2 / d_1
                )
                - 1.0
            )
        )

    return {
        "ultima_index": raw,
        "ultima_notional":
            _make_notional(raw),
    }

# ============================================================
# Portfolio Helpers
# ============================================================

position = {
    "quantity": 10,

    "spot": 6000.0,
    "strike": 6100.0,

    "time_to_expiry": 30 / 365,
    "volatility": 0.20,

    "risk_free_rate": 0.05,
    "dividend_yield": 0.015,

    "option_type": "call"
}


def _require_quantity(position):

    if "quantity" not in position:
        raise KeyError(
            "position missing quantity"
        )

    return float(position["quantity"])


def _aggregate_two_field_greek(
    positions,
    greek_function,
    index_key,
    notional_key,
):

    total_index = 0.0
    total_notional = 0.0

    for position in positions:

        quantity = _require_quantity(
            position
        )

        greek = greek_function(
            spot=position["spot"],
            strike=position["strike"],
            time_to_expiry=position[
                "time_to_expiry"
            ],
            volatility=position[
                "volatility"
            ],
            risk_free_rate=position[
                "risk_free_rate"
            ],
            dividend_yield=position[
                "dividend_yield"
            ],
            option_type=position[
                "option_type"
            ]
            if "option_type"
            in position
            else "call",
        )

        total_index += (
            quantity
            * greek[index_key]
        )

        total_notional += (
            quantity
            * greek[notional_key]
        )

    return {
        index_key: total_index,
        notional_key: total_notional,
    }


# ============================================================
# Portfolio Delta
# ============================================================

def portfolio_delta(positions):

    return _aggregate_two_field_greek(
        positions,
        delta,
        "delta_index",
        "delta_notional",
    )


# ============================================================
# Portfolio Gamma
# ============================================================

def portfolio_gamma(positions):

    total_index = 0.0
    total_notional = 0.0

    for position in positions:

        quantity = _require_quantity(
            position
        )

        greek = gamma(
            spot=position["spot"],
            strike=position["strike"],
            time_to_expiry=position[
                "time_to_expiry"
            ],
            volatility=position[
                "volatility"
            ],
            risk_free_rate=position[
                "risk_free_rate"
            ],
            dividend_yield=position[
                "dividend_yield"
            ],
        )

        total_index += (
            quantity
            * greek["gamma_index"]
        )

        total_notional += (
            quantity
            * greek["gamma_notional"]
        )

    return {
        "gamma_index": total_index,
        "gamma_notional": total_notional,
    }


# ============================================================
# Portfolio Vega
# ============================================================

def portfolio_vega(positions):

    total_index = 0.0
    total_notional = 0.0

    for position in positions:

        quantity = _require_quantity(
            position
        )

        greek = vega(
            spot=position["spot"],
            strike=position["strike"],
            time_to_expiry=position[
                "time_to_expiry"
            ],
            volatility=position[
                "volatility"
            ],
            risk_free_rate=position[
                "risk_free_rate"
            ],
            dividend_yield=position[
                "dividend_yield"
            ],
        )

        total_index += (
            quantity
            * greek["vega_index"]
        )

        total_notional += (
            quantity
            * greek["vega_notional"]
        )

    return {
        "vega_index": total_index,
        "vega_notional": total_notional,
    }


# ============================================================
# Portfolio Vanna
# ============================================================

def portfolio_vanna(positions):

    total_index = 0.0
    total_notional = 0.0

    for position in positions:

        quantity = _require_quantity(
            position
        )

        greek = vanna(
            spot=position["spot"],
            strike=position["strike"],
            time_to_expiry=position[
                "time_to_expiry"
            ],
            volatility=position[
                "volatility"
            ],
            risk_free_rate=position[
                "risk_free_rate"
            ],
            dividend_yield=position[
                "dividend_yield"
            ],
        )

        total_index += (
            quantity
            * greek["vanna_index"]
        )

        total_notional += (
            quantity
            * greek["vanna_notional"]
        )

    return {
        "vanna_index": total_index,
        "vanna_notional": total_notional,
    }


# ============================================================
# Portfolio Volga
# ============================================================

def portfolio_volga(positions):

    total_index = 0.0
    total_notional = 0.0

    for position in positions:

        quantity = _require_quantity(
            position
        )

        greek = volga(
            spot=position["spot"],
            strike=position["strike"],
            time_to_expiry=position[
                "time_to_expiry"
            ],
            volatility=position[
                "volatility"
            ],
            risk_free_rate=position[
                "risk_free_rate"
            ],
            dividend_yield=position[
                "dividend_yield"
            ],
        )

        total_index += (
            quantity
            * greek["volga_index"]
        )

        total_notional += (
            quantity
            * greek["volga_notional"]
        )

    return {
        "volga_index": total_index,
        "volga_notional": total_notional,
    }


# ============================================================
# Portfolio Theta
# ============================================================

def portfolio_theta(positions):

    annual_index = 0.0
    daily_index = 0.0

    annual_notional = 0.0
    daily_notional = 0.0

    for position in positions:

        quantity = _require_quantity(
            position
        )

        greek = theta(
            spot=position["spot"],
            strike=position["strike"],
            time_to_expiry=position[
                "time_to_expiry"
            ],
            volatility=position[
                "volatility"
            ],
            risk_free_rate=position[
                "risk_free_rate"
            ],
            dividend_yield=position[
                "dividend_yield"
            ],
            option_type=position[
                "option_type"
            ],
        )

        annual_index += (
            quantity
            * greek[
                "theta_annual_index"
            ]
        )

        daily_index += (
            quantity
            * greek[
                "theta_daily_index"
            ]
        )

        annual_notional += (
            quantity
            * greek[
                "theta_annual_notional"
            ]
        )

        daily_notional += (
            quantity
            * greek[
                "theta_daily_notional"
            ]
        )

    return {
        "theta_annual_index":
            annual_index,

        "theta_daily_index":
            daily_index,

        "theta_annual_notional":
            annual_notional,

        "theta_daily_notional":
            daily_notional,
    }