from pathlib import Path
import sys

import pandas as pd


# Add src/ to Python path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


from data_loader import build_canonical_tickets
from rag_engine import detect_query_intent, retrieve_documents


def test_canonical_tickets_returns_one_row_per_ticket():
    data = pd.DataFrame(
        [
            {
                "ticket_id": "TK-1",
                "source_system": "legacy_fd",
                "refund_amount_inr": 90000,
            },
            {
                "ticket_id": "TK-1",
                "source_system": "helpdesk",
                "refund_amount_inr": 900,
            },
            {
                "ticket_id": "TK-2",
                "source_system": "helpdesk",
                "refund_amount_inr": 1200,
            },
        ]
    )

    result = build_canonical_tickets(data)

    assert len(result) == 2
    assert result["ticket_id"].nunique() == 2


def test_canonical_tickets_prefers_helpdesk_record():
    data = pd.DataFrame(
        [
            {
                "ticket_id": "TK-1",
                "source_system": "legacy_fd",
                "refund_amount_inr": 90000,
            },
            {
                "ticket_id": "TK-1",
                "source_system": "helpdesk",
                "refund_amount_inr": 900,
            },
        ]
    )

    result = build_canonical_tickets(data)

    row = result.iloc[0]

    assert row["source_system"] == "helpdesk"
    assert row["refund_amount_inr"] == 900


def test_policy_query_intent():
    assert (
        detect_query_intent(
            "What is the refund policy for a DOA product?"
        )
        == "policy"
    )


def test_reconciliation_query_intent():
    assert (
        detect_query_intent(
            "Why does the refund export require reconciliation?"
        )
        == "reconciliation"
    )


def test_analytics_query_intent():
    assert (
        detect_query_intent(
            "What is the largest refund reason and its refund value?"
        )
        == "analytics"
    )


def test_reason_query_intent():
    assert (
        detect_query_intent(
            "What are the main reasons for refunds?"
        )
        == "reason"
    )


def test_ticket_query_intent():
    assert (
        detect_query_intent(
            "Tell me the details of ticket TK-240003."
        )
        == "ticket"
    )


def test_existing_ticket_is_retrieved_exactly():
    results = retrieve_documents(
        "Tell me the details of ticket TK-240003.",
        top_k=3,
    )

    assert len(results) >= 1

    first = results[0]

    assert first["type"] == "ticket"
    assert first["id"] == "TK-240003"
    assert first["source"] == "tickets.csv"


def test_unknown_ticket_returns_no_result():
    results = retrieve_documents(
        "Tell me the details of ticket TK-999999.",
        top_k=3,
    )

    assert results == []


def test_analytics_query_does_not_return_random_tickets():
    results = retrieve_documents(
        "What is the largest refund reason and its refund value?",
        top_k=5,
    )

    assert len(results) >= 1

    assert all(
        document["type"] == "analytics"
        for document in results
    )