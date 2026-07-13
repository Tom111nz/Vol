import pytest

from IBKR.GreeksSPX import *

TOL_PRICE = 1e-8
TOL_GREEK = 1e-5


# ============================================================
# Standard Test Contract
# ============================================================

SPOT = 6000.0
STRIKE = 6000.0

T = 0.5

VOL = 0.20

R = 0.05
Q = 0.01


# ============================================================
# Utility finite differences
# ============================================================

def fd_delta(h=0.01):

    p_up = price(
        SPOT + h,
        STRIKE,
        T,
        VOL,
        R,
        Q,
        "call"
    )

    p_dn = price(
        SPOT - h,
        STRIKE,
        T,
        VOL,
        R,
        Q,
        "call"
    )

    return (
        p_up - p_dn
    ) / (2.0 * h)


def fd_gamma(h=1.0):

    p_up = price(
        SPOT + h,
        STRIKE,
        T,
        VOL,
        R,
        Q,
        "call"
    )

    p_mid = price(
        SPOT,
        STRIKE,
        T,
        VOL,
        R,
        Q,
        "call"
    )

    p_dn = price(
        SPOT - h,
        STRIKE,
        T,
        VOL,
        R,
        Q,
        "call"
    )

    return (
        p_up
        - 2.0 * p_mid
        + p_dn
    ) / (h * h)


def fd_vega(h=1e-4):

    p_up = price(
        SPOT,
        STRIKE,
        T,
        VOL + h,
        R,
        Q,
        "call"
    )

    p_dn = price(
        SPOT,
        STRIKE,
        T,
        VOL - h,
        R,
        Q,
        "call"
    )

    return (
        p_up - p_dn
    ) / (2.0 * h)


# ============================================================
# Forward
# ============================================================

def test_forward_price():

    expected = (
        SPOT
        * np.exp((R - Q) * T)
    )

    actual = forward_price(
        SPOT,
        R,
        Q,
        T
    )

    assert np.isclose(
        actual,
        expected
    )


# ============================================================
# d1 d2
# ============================================================

def test_d1_d2_relationship():

    d_1 = d1(
        SPOT,
        STRIKE,
        T,
        VOL,
        R,
        Q
    )

    d_2 = d2(
        SPOT,
        STRIKE,
        T,
        VOL,
        R,
        Q
    )

    expected = (
        VOL
        * np.sqrt(T)
    )

    assert np.isclose(
        d_1 - d_2,
        expected
    )


# ============================================================
# Put Call Parity
# ============================================================

def test_put_call_parity():

    call_price = price(
        SPOT,
        STRIKE,
        T,
        VOL,
        R,
        Q,
        "call"
    )

    put_price = price(
        SPOT,
        STRIKE,
        T,
        VOL,
        R,
        Q,
        "put"
    )

    lhs = call_price - put_price

    rhs = np.exp(
        -R * T
    ) * (
        forward_price(
            SPOT,
            R,
            Q,
            T
        )
        - STRIKE
    )

    assert np.isclose(
        lhs,
        rhs,
        atol=1e-8
    )


# ============================================================
# Delta
# ============================================================

def test_delta_finite_difference():

    analytical = delta(
        SPOT,
        STRIKE,
        T,
        VOL,
        R,
        Q,
        "call"
    )["delta_index"]

    finite_diff = fd_delta()

    assert np.isclose(
        analytical,
        finite_diff,
        rtol=1e-4
    )


# ============================================================
# Gamma
# ============================================================

def test_gamma_finite_difference():

    analytical = gamma(
        SPOT,
        STRIKE,
        T,
        VOL,
        R,
        Q
    )["gamma_index"]

    finite_diff = fd_gamma()

    assert np.isclose(
        analytical,
        finite_diff,
        rtol=1e-3
    )


# ============================================================
# Vega
# ============================================================

def test_vega_finite_difference():

    analytical = vega(
        SPOT,
        STRIKE,
        T,
        VOL,
        R,
        Q
    )["vega_index"]

    finite_diff = fd_vega()

    assert np.isclose(
        analytical,
        finite_diff,
        rtol=1e-4
    )


# ============================================================
# Volga Identity
# ============================================================

def test_volga_identity():

    d_1 = d1(
        SPOT,
        STRIKE,
        T,
        VOL,
        R,
        Q
    )

    d_2 = d2(
        SPOT,
        STRIKE,
        T,
        VOL,
        R,
        Q
    )

    expected = (
        vega(
            SPOT,
            STRIKE,
            T,
            VOL,
            R,
            Q
        )["vega_index"]
        * d_1
        * d_2
        / VOL
    )

    actual = volga(
        SPOT,
        STRIKE,
        T,
        VOL,
        R,
        Q
    )["volga_index"]

    assert np.isclose(
        actual,
        expected
    )


# ============================================================
# Vanna Identity
# ============================================================

def test_vanna_identity():

    d_1 = d1(
        SPOT,
        STRIKE,
        T,
        VOL,
        R,
        Q
    )

    d_2 = d2(
        SPOT,
        STRIKE,
        T,
        VOL,
        R,
        Q
    )

    expected = (
        -np.exp(-Q * T)
        * norm.pdf(d_1)
        * d_2
        / VOL
    )

    actual = vanna(
        SPOT,
        STRIKE,
        T,
        VOL,
        R,
        Q
    )["vanna_index"]

    assert np.isclose(
        actual,
        expected
    )


# ============================================================
# Dual Greeks
# ============================================================

def test_dual_gamma_positive():

    dg = dual_gamma(
        SPOT,
        STRIKE,
        T,
        VOL,
        R,
        Q
    )["dual_gamma_index"]

    assert dg > 0.0


def test_dual_delta_bounds():

    dd = dual_delta(
        SPOT,
        STRIKE,
        T,
        VOL,
        R,
        Q,
        "call"
    )["dual_delta_index"]

    assert -1.0 <= dd <= 0.0


# ============================================================
# Probability ITM
# ============================================================

def test_probability_itm_bounds():

    p = probability_itm(
        SPOT,
        STRIKE,
        T,
        VOL,
        R,
        Q,
        "call"
    )

    assert 0.0 <= p <= 1.0


# ============================================================
# Expected Move
# ============================================================

def test_expected_move():

    expected = (
        SPOT
        * VOL
        * np.sqrt(T)
    )

    actual = expected_move(
        SPOT,
        VOL,
        T
    )

    assert np.isclose(
        actual,
        expected
    )


# ============================================================
# Implied Volatility Inversion
# ============================================================

def test_implied_volatility_roundtrip():

    px = price(
        SPOT,
        STRIKE,
        T,
        VOL,
        R,
        Q,
        "call"
    )

    iv = implied_volatility(
        px,
        SPOT,
        STRIKE,
        T,
        R,
        Q,
        "call"
    )

    assert np.isclose(
        iv,
        VOL,
        atol=1e-6
    )


# ============================================================
# Notional Scaling
# ============================================================

@pytest.mark.parametrize(
    "func,key",
    [
        (delta, "delta"),
        (gamma, "gamma"),
        (vega, "vega"),
        (vanna, "vanna"),
        (volga, "volga"),
    ]
)
def test_notional_scaling(
    func,
    key
):

    result = func(
        SPOT,
        STRIKE,
        T,
        VOL,
        R,
        Q,
        "call"
    ) if key == "delta" else func(
        SPOT,
        STRIKE,
        T,
        VOL,
        R,
        Q
    )

    assert np.isclose(
        result[f"{key}_notional"],
        result[f"{key}_index"]
        * SPX_MULTIPLIER
    )


# ============================================================
# Portfolio Aggregation
# ============================================================

def test_portfolio_delta_aggregation():

    positions = [

        {
            "quantity": 10,
            "spot": SPOT,
            "strike": STRIKE,
            "time_to_expiry": T,
            "volatility": VOL,
            "risk_free_rate": R,
            "dividend_yield": Q,
            "option_type": "call"
        },

        {
            "quantity": -5,
            "spot": SPOT,
            "strike": STRIKE,
            "time_to_expiry": T,
            "volatility": VOL,
            "risk_free_rate": R,
            "dividend_yield": Q,
            "option_type": "call"
        }

    ]

    single_delta = delta(
        SPOT,
        STRIKE,
        T,
        VOL,
        R,
        Q,
        "call"
    )["delta_index"]

    expected = (
        5
        * single_delta
    )

    actual = portfolio_delta(
        positions
    )["delta_index"]

    assert np.isclose(
        actual,
        expected
    )


# ============================================================
# Deep ITM
# ============================================================

def test_deep_itm_delta():

    result = delta(
        7000,
        5000,
        1.0,
        0.20,
        R,
        Q,
        "call"
    )

    assert result[
        "delta_index"
    ] > 0.95


# ============================================================
# Deep OTM
# ============================================================

def test_deep_otm_delta():

    result = delta(
        4000,
        7000,
        1.0,
        0.20,
        R,
        Q,
        "call"
    )

    assert result[
        "delta_index"
    ] < 0.05


# ============================================================
# Near Expiry
# ============================================================

def test_near_expiry():

    px = price(
        SPOT,
        STRIKE,
        1e-6,
        VOL,
        R,
        Q,
        "call"
    )

    assert np.isfinite(px)


# ============================================================
# Zero Volatility
# ============================================================

def test_zero_volatility():

    px = price(
        SPOT,
        STRIKE,
        T,
        0.0,
        R,
        Q,
        "call"
    )

    assert px >= 0.0


# ============================================================
# Invalid Option Type
# ============================================================

def test_invalid_option_type():

    with pytest.raises(
        ValueError
    ):
        price(
            SPOT,
            STRIKE,
            T,
            VOL,
            R,
            Q,
            "banana"
        )
