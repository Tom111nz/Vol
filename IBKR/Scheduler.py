import atexit
import os
import sys
import time
import signal
import logging
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta, time as dtime
from zoneinfo import ZoneInfo
from Constant import BUY
from IBKR import LoadOptions

# Only allow one instance to run at a time
import errno
import atexit

LOCK_FILE = "scheduler.lock"

if os.path.exists(LOCK_FILE):
    try:
        with open(LOCK_FILE, "r") as f:
            pid = int(f.read())

        os.kill(pid, 0)

        print("Already running. Exiting.")
        sys.exit(1)

    except OSError as e:
        if e.errno == errno.ESRCH:
            print("Stale lock detected. Removing.")
            os.remove(LOCK_FILE)
        else:
            print("Cannot verify existing process. Exiting for safety.")
            sys.exit(1)

# ✅ Create the lock file
with open(LOCK_FILE, "w") as f:
    f.write(str(os.getpid()))

# ✅ Ensure lock is removed on exit
def cleanup_lock():
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)

atexit.register(cleanup_lock)

# ------------------------
# TIMEZONES
# ------------------------
ET = ZoneInfo("America/New_York")  # DST-aware IANA tz [1](https://docs.python.org/3/library/zoneinfo.html)

# ------------------------
# LOGGING
# ------------------------
def setup_logger(log_path="scheduler.log", level=logging.INFO):
    logger = logging.getLogger("ETScheduler")
    logger.setLevel(level)

    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    # Avoid duplicate handlers if reloaded
    if not logger.handlers:
        fh = logging.FileHandler(log_path)
        fh.setFormatter(fmt)
        logger.addHandler(fh)

        ch = logging.StreamHandler()
        ch.setFormatter(fmt)
        logger.addHandler(ch)

    return logger

logger = setup_logger()

# ------------------------
# SCHEDULER DATA TYPES
# ------------------------
@dataclass(frozen=True)
class DailyTriggerET:
    """
    Run once per ET calendar day within [time, time+window).
    """
    name: str
    at: dtime                      # ET time-of-day
    window: timedelta = timedelta(minutes=2)

# Example triggers (add as many as you like)
TRIGGERS = [
    #DailyTriggerET("market_open_tasks", dtime(9, 30), timedelta(minutes=3)),
    #DailyTriggerET("midday_check",      dtime(12, 0), timedelta(minutes=2)),
    DailyTriggerET("pre_close_tasks",   dtime(15, 45), timedelta(minutes=3)),
]

# Track last-run per trigger by ET date
last_run_by_trigger: dict[str, datetime.date] = {}

# ------------------------
# GRACEFUL SHUTDOWN
# ------------------------
shutdown_event = threading.Event()

def _request_shutdown(signum, frame):
    # Keep handler minimal; set a flag and let the main loop exit. [2](https://docs.python.org/3/library/signal.html)
    logger.info(f"Shutdown requested (signal={signum}). Exiting loop gracefully...")
    shutdown_event.set()

def install_signal_handlers():
    # SIGTERM may not be sent in all Windows cases, but SIGINT (Ctrl+C) is common.
    signal.signal(signal.SIGINT, _request_shutdown)
    try:
        signal.signal(signal.SIGTERM, _request_shutdown)
    except Exception:
        # Some environments may not support SIGTERM; safe to ignore.
        pass

# ------------------------
# TIME HELPERS
# ------------------------
def now_et() -> datetime:
    return datetime.now(ET)

def is_weekday_et(dt: datetime) -> bool:
    return dt.weekday() < 1 # 0 is a Monday

def trigger_window(dt: datetime, trig: DailyTriggerET) -> tuple[datetime, datetime]:
    """
    Compute the window [start, end) in ET for today's date.
    """
    start = dt.replace(hour=trig.at.hour, minute=trig.at.minute, second=0, microsecond=0)
    end = start + trig.window
    return start, end

def should_fire(dt: datetime, trig: DailyTriggerET) -> bool:
    """
    True if within trigger window and not run yet today (ET date).
    """
    start, end = trigger_window(dt, trig)
    if not (start <= dt < end):
        return False
    last_date = last_run_by_trigger.get(trig.name)
    return last_date != dt.date()

def mark_fired(dt: datetime, trig: DailyTriggerET):
    last_run_by_trigger[trig.name] = dt.date()

# ------------------------
# YOUR JOBS (replace these with your IBKR logic)
# ------------------------
def run_trigger(trig: DailyTriggerET):
    """
    Dispatch per-trigger work. Wrap each trigger in its own try/except so one failure
    doesn't kill the scheduler.
    """
    logger.info(f"[{trig.name}] Starting job...")
    try:
        # ---- PUT YOUR REAL WORK HERE ----
        reqMarketDataType = 1
        expiryTargetBusinessDaysAhead = [1]  # this is based on CBOE dates (not NZ dates), so 0 is 0DTE expiry option
        percentageChangeTargetForOptionStrike = [-0.07]
        ## SPX circuit breaks are at 7%, 13% and 20% (close for remainder of day) from previous day's close
        optionType = ['P']
        buySell = [BUY]
        totalQuantity = [1]
        if reqMarketDataType != 1:
            isSubmitOrder = False
        else:
            isSubmitOrder = True
        isLimitOrder = True
        LoadOptions.trade(
            reqMarketDataType, expiryTargetBusinessDaysAhead, percentageChangeTargetForOptionStrike,
            optionType, buySell, totalQuantity, isSubmitOrder, isLimitOrder
        )
        # e.g. connect IBKR, load chain, request bid/ask, write results, etc.
        time.sleep(1)

        logger.info(f"[{trig.name}] Completed successfully.")
    except Exception as e:
        logger.exception(f"[{trig.name}] Failed: {e}")

# ------------------------
# MAIN LOOP
# ------------------------
def scheduler_loop(poll_seconds: float = 1.0, heartbeat_seconds: int = 60):
    install_signal_handlers()
    logger.info("ET scheduler started (multiple triggers + graceful shutdown).")

    last_heartbeat = time.time()

    while not shutdown_event.is_set():
        dt = now_et()

        # optional heartbeat log
        if time.time() - last_heartbeat >= heartbeat_seconds:
            logger.info(f"Heartbeat: ET now {dt.isoformat(timespec='seconds')}")
            last_heartbeat = time.time()

        # Skip weekends (ET). If you want Sunday night GTH etc, adjust logic.
        if is_weekday_et(dt):
            for trig in TRIGGERS:
                if should_fire(dt, trig):
                    logger.info(f"Trigger matched: {trig.name} at ET {dt.isoformat(timespec='seconds')}")
                    run_trigger(trig)
                    mark_fired(dt, trig)

                    # Small sleep to avoid re-triggering in the same second/window
                    time.sleep(1.0)

        time.sleep(poll_seconds)

    # Cleanup section
    logger.info("Scheduler exiting: performing cleanup...")
    # Add any cleanup here (close files, disconnect IB, flush buffers, etc.)
    logger.info("Shutdown complete.")

if __name__ == "__main__":
    scheduler_loop()