from datetime import datetime
import csv
from pathlib import Path

def log(msg: str):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

import csv
from pathlib import Path

import csv
from pathlib import Path

def append_fill_row(fill, csv_file="fills.csv"):
    file_exists = Path(csv_file).exists()
    exec_id = fill.execution.execId

    with open(csv_file, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow([
                "execId",
                "time",
                "symbol",
                "expiry",
                "strike",
                "right",
                "action",
                "qty",
                "price",
                "commission",
                "exchange",
                "orderId"
            ])

        c = fill.contract
        e = fill.execution
        commission = fill.commissionReport.commission if fill.commissionReport else None

        writer.writerow([
            exec_id,
            e.time,
            c.symbol,
            getattr(c, "lastTradeDateOrContractMonth", ""),
            getattr(c, "strike", ""),
            getattr(c, "right", ""),
            e.side,
            e.shares,
            e.price,
            commission,
            e.exchange,
            e.orderId
        ])

def update_commission(exec_id, commission, csv_file="fills.csv"):
    path = Path(csv_file)
    if not path.exists():
        return

    rows = []
    with open(csv_file, "r", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            if row.get("execId") == exec_id:
                row["commission"] = str(commission)
            rows.append(row)

    with open(csv_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)