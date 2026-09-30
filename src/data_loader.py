from pathlib import Path
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


def load_data() -> dict[str, pd.DataFrame]:
    """Load all structured Vireo support datasets."""
    data = {
        "tickets": pd.read_csv(DATA_DIR / "tickets.csv"),
        "agents": pd.read_csv(DATA_DIR / "agents.csv"),
        "customers": pd.read_csv(DATA_DIR / "customers.csv"),
        "orders": pd.read_csv(DATA_DIR / "orders.csv"),
        "products": pd.read_csv(DATA_DIR / "products.csv"),
    }

    tickets = data["tickets"]

    date_columns = [
        "created_at",
        "first_response_at",
        "resolved_at",
    ]

    for column in date_columns:
        tickets[column] = pd.to_datetime(
            tickets[column],
            errors="coerce",
        )

    for column in ["refund_amount_inr", "csat_score", "transfers"]:
        tickets[column] = pd.to_numeric(
            tickets[column],
            errors="coerce",
        )

    data["tickets"] = tickets

    return data


def build_canonical_tickets(tickets: pd.DataFrame) -> pd.DataFrame:
    """
    Create one canonical row per ticket.

    Migration duplicates can exist in both systems.
    Preference:
      1. helpdesk row when available
      2. otherwise legacy_fd row

    Legacy refund amounts are converted from the legacy
    native unit to rupees using the policy's 100x correction
    discovered during reconciliation.
    """
    canonical_rows = []

    for ticket_id, group in tickets.groupby("ticket_id", sort=False):
        helpdesk = group[group["source_system"].eq("helpdesk")]

        if not helpdesk.empty:
            row = helpdesk.iloc[0].copy()
        else:
            row = group.iloc[0].copy()

        refund = row["refund_amount_inr"]

        if pd.notna(refund) and row["source_system"] == "legacy_fd":
            row["refund_amount_inr"] = refund / 100.0

        canonical_rows.append(row)

    return pd.DataFrame(canonical_rows).reset_index(drop=True)


if __name__ == "__main__":
    datasets = load_data()
    canonical = build_canonical_tickets(datasets["tickets"])

    print("Loaded datasets:")
    for name, df in datasets.items():
        print(f"{name}: {df.shape}")

    print(f"\nRaw ticket rows: {len(datasets['tickets']):,}")
    print(f"Unique ticket IDs: {datasets['tickets']['ticket_id'].nunique():,}")
    print(f"Canonical ticket rows: {len(canonical):,}")

    refund_rows = canonical[
        canonical["refund_amount_inr"].notna()
    ]

    print(f"Canonical refund tickets: {len(refund_rows):,}")
    print(
        "Canonical refund amount: "
        f"₹{refund_rows['refund_amount_inr'].sum():,.2f}"
    )