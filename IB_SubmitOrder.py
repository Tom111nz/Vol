import logging
import csv
import os
from datetime import datetime
import IB_Connection
# ib_async (maintained replacement for ib_insync-style API)
from ib_async import IB, Contract, Order

# -----------------------
# Logging Setup (same as yours)
# -----------------------
logging.basicConfig(
    filename="spx_main.log",
    level=logging.INFO,
    format="%(asctime)s - %(message)s"
)
logging.info("=== Script started ===")

CSV_FILE = "spx_fills.csv"
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "order_id", "price", "quantity", "time"])

# -----------------------
# Your contract + order builders (same details)
# -----------------------
def build_spx_option(strike, expiration):
    c = Contract()
    c.symbol = "SPX"
    c.secType = "OPT"
    c.exchange = "CBOE"
    c.currency = "USD"
    c.lastTradeDateOrContractMonth = expiration #"20240520"  # <-- your original detail (likely expired now)
    c.strike = int(strike)
    c.right = "P"
    c.multiplier = "100"
    return c

def build_limit_buy(price):
    o = Order()
    o.action = "BUY"
    o.orderType = "LMT"
    o.totalQuantity = 1
    o.lmtPrice = float(price)
    return o

# -----------------------
# Main
# -----------------------
def main():
    ib = IB()

    # Connect (same host/port/clientId as your script)
    ib.connect("127.0.0.1", 7497, clientId=1)
    logging.info("Connected to TWS/IB Gateway")
    strike, expiration, bid, ask = IB_Connection.lowest_put_strike_delta_ge_target_for_xbd_expiry(ib)
    # Build and QUALIFY contract (important in ib_async/ib_insync style)
    contract = build_spx_option(strike, expiration)

    try:
        # Qualify ensures conId / fully qualified fields are populated
        ib.qualifyContracts(contract)
        logging.info(
            f"Contract qualified: conId={getattr(contract, 'conId', None)}, "
            f"{contract.symbol} {contract.lastTradeDateOrContractMonth} "
            f"{contract.right} {contract.strike}"
        )
    except Exception as e:
        logging.exception(f"Contract qualification failed: {e}")
        ib.disconnect()
        return

    order = build_limit_buy(ask)

    # Place order
    trade = ib.placeOrder(contract, order)
    logging.info(
        f"Submitted order: orderId={trade.order.orderId}, "
        f"type={trade.order.orderType}, action={trade.order.action}, "
        f"qty={trade.order.totalQuantity}, lmtPrice={trade.order.lmtPrice}"
    )

    # -----------------------
    # Fill logging: write to CSV on fills
    # -----------------------
    def on_fill(trade_, fill_):
        """
        fill_.execution has the same core data you used before:
        orderId, price, shares, time
        """
        try:
            with open(CSV_FILE, "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    datetime.now().isoformat(),
                    fill_.execution.orderId,
                    fill_.execution.price,
                    fill_.execution.shares,
                    fill_.execution.time
                ])
            logging.info(
                f"FILL: orderId={fill_.execution.orderId} "
                f"price={fill_.execution.price} shares={fill_.execution.shares} "
                f"time={fill_.execution.time}"
            )
        except Exception as e:
            logging.exception(f"Failed writing fill to CSV: {e}")

    # Subscribe handler to this trade's fills
    trade.fillEvent += on_fill

    # Also log status changes (similar to your orderStatus logging)
    def on_status(trade_):
        st = trade_.orderStatus
        logging.info(
            f"OrderStatus: ID={trade_.order.orderId}, Status={st.status}, "
            f"Filled={st.filled}, Remaining={st.remaining}, "
            f"AvgFillPrice={st.avgFillPrice}, LastFillPrice={st.lastFillPrice}"
        )

    trade.statusEvent += on_status

    # Wait (non-blocking sleep so the event loop can process messages)
    # ib_async follows the same "don't block the loop" guidance as the ib_insync model. [2](https://ib-api-reloaded.github.io/ib_async/api.html)
    ib.sleep(10)

    logging.info("Disconnecting")
    ib.disconnect()

if __name__ == "__main__":
    main()