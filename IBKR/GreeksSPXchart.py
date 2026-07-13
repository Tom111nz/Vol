import numpy as np
import matplotlib.pyplot as plt

from GreeksSPX import delta, charm

# ============================================================
# Parameters
# ============================================================

SPOT = 7500.0
STRIKE = 6800.0

RISK_FREE_RATE = 0.05
DIVIDEND_YIELD = 0.01

VOLATILITIES = [
    0.10,
    0.15,
    0.20,
    0.25,
    0.30,
    0.40
]

days = np.arange(365, 0, -1)

# ============================================================
# Create Figure
# ============================================================

fig, axes = plt.subplots(
    2,
    1,
    figsize=(14, 10),
    sharex=True
)

# ============================================================
# Process Each Volatility
# ============================================================

for vol in VOLATILITIES:

    delta_values = []
    charm_values = []

    for day in days:

        T = day / 365.0

        d = delta(
            spot=SPOT,
            strike=STRIKE,
            time_to_expiry=T,
            volatility=vol,
            risk_free_rate=RISK_FREE_RATE,
            dividend_yield=DIVIDEND_YIELD,
            option_type="put"
        )

        c = charm(
            spot=SPOT,
            strike=STRIKE,
            time_to_expiry=T,
            volatility=vol,
            risk_free_rate=RISK_FREE_RATE,
            dividend_yield=DIVIDEND_YIELD,
            option_type="put"
        )

        delta_values.append(
            d["delta_index"]
        )

        charm_values.append(
            c["charm_index"]
        )

    delta_values = np.array(delta_values)

    gradient_values = np.gradient(
        delta_values,
        days
    )

    daily_charm = np.array(
        charm_values
    ) / 365.0

    # --------------------------------------------------------
    # Delta Chart
    # --------------------------------------------------------

    axes[0].plot(
        days,
        delta_values,
        linewidth=2,
        label=f"Vol={vol:.0%}"
    )

    # --------------------------------------------------------
    # Gradient Chart
    # --------------------------------------------------------

    axes[1].plot(
        days,
        gradient_values,
        linewidth=2,
        label=f"Grad {vol:.0%}"
    )

    #axes[1].plot(
    #    days,
    #    daily_charm,
    #    linestyle="--",
    #    linewidth=1.5
    #)

# ============================================================
# Formatting
# ============================================================

axes[0].set_title(
    "SPX ATM Put Delta Through Time"
)

axes[0].set_ylabel(
    "Delta"
)

axes[0].grid(True, alpha=0.3)

axes[0].legend()

axes[0].invert_xaxis()

# ------------------------------------------------------------

axes[1].set_title(
    "Delta Gradient and Charm Comparison"
)

axes[1].set_xlabel(
    "Days To Expiry"
)

axes[1].set_ylabel(
    "Daily Delta Change"
)

axes[1].axhline(
    0,
    color="black",
    linewidth=1
)

axes[1].grid(True, alpha=0.3)

axes[1].invert_xaxis()

plt.tight_layout()
plt.show()