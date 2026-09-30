from __future__ import annotations

import os
import re
from functools import lru_cache
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from google import genai
from google.genai import types


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE)


# ============================================================
# GEMINI
# ============================================================

GEMINI_MODEL = "gemini-3.5-flash-lite"


@lru_cache(maxsize=1)
def get_client():
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is missing. "
            "Please add it to the .env file."
        )

    return genai.Client(api_key=api_key)


# ============================================================
# TEXT HELPERS
# ============================================================

def clean_text(value) -> str:
    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass

    text = str(value)

    text = text.replace(
        "\x00",
        " ",
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


# ============================================================
# FILE LOADERS
# ============================================================

def load_text_file(
    path: Path,
) -> str:

    try:
        return path.read_text(
            encoding="utf-8",
            errors="ignore",
        )

    except Exception:
        return ""


def load_pdf_text(
    path: Path,
) -> str:

    if not path.exists():
        return ""

    try:
        reader = PdfReader(
            str(path)
        )

        pages = []

        for page in reader.pages:
            text = (
                page.extract_text()
                or ""
            )

            if text.strip():
                pages.append(
                    text
                )

        return "\n\n".join(
            pages
        )

    except Exception:
        return ""


# ============================================================
# REFERENCE DOCUMENTS
# ============================================================

@lru_cache(maxsize=1)
def load_reference_documents() -> list[dict]:

    documents = []

    # --------------------------------------------------------
    # POLICY
    # --------------------------------------------------------

    policy_path = (
        DATA_DIR
        / "support-policy.pdf"
    )

    policy_text = load_pdf_text(
        policy_path
    )

    if policy_text:

        documents.append(
            {
                "source": "support-policy.pdf",
                "type": "policy",
                "id": "support-policy",
                "content": policy_text,
            }
        )

    # --------------------------------------------------------
    # EMAIL THREAD
    # --------------------------------------------------------

    email_path = (
        DATA_DIR
        / "email-thread.txt"
    )

    email_text = load_text_file(
        email_path
    )

    if email_text:

        documents.append(
            {
                "source": "email-thread.txt",
                "type": "email",
                "id": "email-thread",
                "content": email_text,
            }
        )

    # --------------------------------------------------------
    # KNOWLEDGE FILES
    # --------------------------------------------------------

    if KNOWLEDGE_DIR.exists():

        for path in sorted(
            KNOWLEDGE_DIR.glob("*")
        ):

            if path.suffix.lower() not in {
                ".txt",
                ".md",
            }:
                continue

            text = load_text_file(
                path
            )

            if not text:
                continue

            documents.append(
                {
                    "source": path.name,
                    "type": "knowledge",
                    "id": path.stem,
                    "content": text,
                }
            )

    return documents


# ============================================================
# TICKET DOCUMENT
# ============================================================

def build_ticket_document(
    row: pd.Series,
    customer: pd.Series | None = None,
    order: pd.Series | None = None,
    product: pd.Series | None = None,
) -> str:

    customer = (
        customer
        if customer is not None
        else {}
    )

    order = (
        order
        if order is not None
        else {}
    )

    product = (
        product
        if product is not None
        else {}
    )

    parts = [
        f"Ticket ID: "
        f"{clean_text(row.get('ticket_id'))}",

        f"Created At: "
        f"{clean_text(row.get('created_at'))}",

        f"Status: "
        f"{clean_text(row.get('status'))}",

        f"Channel: "
        f"{clean_text(row.get('channel'))}",

        f"Customer ID: "
        f"{clean_text(row.get('customer_id'))}",

        f"Order ID: "
        f"{clean_text(row.get('order_id'))}",

        f"Product SKU: "
        f"{clean_text(row.get('product_sku'))}",

        f"Category: "
        f"{clean_text(row.get('category'))}",

        f"Priority: "
        f"{clean_text(row.get('priority'))}",

        f"Assigned Team: "
        f"{clean_text(row.get('assigned_team'))}",

        f"Agent ID: "
        f"{clean_text(row.get('agent_id'))}",

        f"Transfers: "
        f"{clean_text(row.get('transfers'))}",

        f"CSAT Score: "
        f"{clean_text(row.get('csat_score'))}",

        f"Refund Amount INR: "
        f"{clean_text(row.get('refund_amount_inr'))}",

        f"Refund Reason Code: "
        f"{clean_text(row.get('refund_reason_code'))}",

        f"Replacement Issued: "
        f"{clean_text(row.get('replacement_issued'))}",

        f"Customer Message: "
        f"{clean_text(row.get('customer_message'))}",

        f"Agent Notes: "
        f"{clean_text(row.get('agent_notes'))}",

        f"Source System: "
        f"{clean_text(row.get('source_system'))}",
    ]

    # --------------------------------------------------------
    # CUSTOMER
    # --------------------------------------------------------

    if isinstance(
        customer,
        pd.Series,
    ):

        parts.extend(
            [

                f"Customer Name: "
                f"{clean_text(customer.get('name'))}",

                f"Customer City: "
                f"{clean_text(customer.get('city'))}",

                f"Customer State: "
                f"{clean_text(customer.get('state'))}",

                f"Care Plus: "
                f"{clean_text(customer.get('care_plus'))}",
            ]
        )

    # --------------------------------------------------------
    # ORDER
    # --------------------------------------------------------

    if isinstance(
        order,
        pd.Series,
    ):

        parts.extend(
            [

                f"Order Date: "
                f"{clean_text(order.get('order_date'))}",

                f"Order Channel: "
                f"{clean_text(order.get('channel'))}",

                f"Order Quantity: "
                f"{clean_text(order.get('qty'))}",

                f"Order Value INR: "
                f"{clean_text(order.get('order_value_inr'))}",

                f"Lot Code: "
                f"{clean_text(order.get('lot_code'))}",
            ]
        )

    # --------------------------------------------------------
    # PRODUCT
    # --------------------------------------------------------

    if isinstance(
        product,
        pd.Series,
    ):

        parts.extend(
            [

                f"Product Name: "
                f"{clean_text(product.get('product_name'))}",

                f"Product Family: "
                f"{clean_text(product.get('family'))}",

                f"Unit Cost INR: "
                f"{clean_text(product.get('unit_cost_inr'))}",

                f"Retail Price INR: "
                f"{clean_text(product.get('retail_price_inr'))}",

                f"Warranty Months: "
                f"{clean_text(product.get('warranty_months'))}",
            ]
        )

    return "\n".join(
        parts
    )


# ============================================================
# BUSINESS SUMMARY
# ============================================================

def build_business_summary(
    raw_tickets: pd.DataFrame,
    canonical: pd.DataFrame,
) -> str:

    # --------------------------------------------------------
    # DATA COUNTS
    # --------------------------------------------------------

    raw_rows = len(
        raw_tickets
    )

    unique_ticket_ids = (
        raw_tickets[
            "ticket_id"
        ].nunique()
    )

    duplicate_rows = (
        raw_rows
        - unique_ticket_ids
    )

    # --------------------------------------------------------
    # REFUND DATA
    # --------------------------------------------------------

    refund_amount_numeric = pd.to_numeric(
        canonical[
            "refund_amount_inr"
        ],
        errors="coerce",
    ).fillna(0)

    refund_tickets = canonical[
        refund_amount_numeric > 0
    ].copy()

    refund_count = len(
        refund_tickets
    )

    refund_amount = float(
        pd.to_numeric(
            refund_tickets[
                "refund_amount_inr"
            ],
            errors="coerce",
        )
        .fillna(0)
        .sum()
    )

    avg_refund = (
        refund_amount
        / refund_count
        if refund_count
        else 0
    )

    # --------------------------------------------------------
    # CSAT
    # --------------------------------------------------------

    csat = pd.to_numeric(
        canonical[
            "csat_score"
        ],
        errors="coerce",
    ).dropna()

    avg_csat = (
        float(csat.mean())
        if not csat.empty
        else 0
    )

    # --------------------------------------------------------
    # REFUND REASONS
    # --------------------------------------------------------

    reason_summary = (
        refund_tickets
        .groupby(
            "refund_reason_code",
            dropna=False,
        )[
            "refund_amount_inr"
        ]
        .sum()
        .sort_values(
            ascending=False
        )
    )

    reason_lines = []

    for reason, amount in (
        reason_summary.items()
    ):

        reason_name = (
            clean_text(reason)
            if clean_text(reason)
            else "Unknown"
        )

        reason_lines.append(
            f"- {reason_name}: "
            f"₹{float(amount):,.2f}"
        )

    # --------------------------------------------------------
    # REFUND + REPLACEMENT
    # --------------------------------------------------------

    replacement_refund_overlap = 0

    if (
        "replacement_issued"
        in refund_tickets.columns
    ):

        replacement_mask = (
            refund_tickets[
                "replacement_issued"
            ]
            .astype(str)
            .str.upper()
            .eq("Y")
        )

        replacement_refund_overlap = int(
            replacement_mask.sum()
        )

    # --------------------------------------------------------
    # SOURCE SYSTEM
    # --------------------------------------------------------

    source_summary = (
        raw_tickets[
            "source_system"
        ]
        .fillna("Unknown")
        .value_counts()
        .to_dict()
    )

    source_lines = [
        f"- {clean_text(source)}: "
        f"{count:,}"
        for source, count
        in source_summary.items()
    ]

    # --------------------------------------------------------
    # MONTHLY REFUND VALUES
    # --------------------------------------------------------

    monthly_lines = []

    if (
        "created_at"
        in refund_tickets.columns
    ):

        temp = refund_tickets.copy()

        temp["month"] = (
            pd.to_datetime(
                temp[
                    "created_at"
                ],
                errors="coerce",
            )
            .dt.to_period("M")
        )

        monthly_data = (
            temp
            .dropna(
                subset=["month"]
            )
            .groupby(
                "month"
            )[
                "refund_amount_inr"
            ]
            .sum()
            .sort_values(
                ascending=False
            )
        )

        for month, amount in (
            monthly_data.head(12).items()
        ):

            monthly_lines.append(
                f"- {month}: "
                f"₹{float(amount):,.2f}"
            )

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    summary = f"""
VIREO REFUND AI DATA SUMMARY

RAW DATA
Raw ticket rows: {raw_rows:,}
Unique ticket IDs: {unique_ticket_ids:,}
Duplicate export rows: {duplicate_rows:,}

CANONICAL DATA
Canonical ticket rows: {len(canonical):,}

REFUND METRICS
Canonical refund tickets: {refund_count:,}
Canonical refund amount: ₹{refund_amount:,.2f}
Average canonical refund: ₹{avg_refund:,.2f}
Average CSAT: {avg_csat:.2f}/5

REFUND TOTALS BY REASON CODE
{chr(10).join(reason_lines)}

TOP MONTHLY REFUND VALUES
{chr(10).join(monthly_lines)}

REFUND + REPLACEMENT FLAG
Refund tickets with replacement_issued = Y:
{replacement_refund_overlap:,}

RAW TICKET SOURCE SYSTEMS
{chr(10).join(source_lines)}

DATA RECONCILIATION NOTE

The canonical dataset prefers the helpdesk record when
the same ticket appears in both systems.

Legacy-only refund amounts are normalized by the
canonical data loader because the legacy system's
monetary field is stored in its native unit, while
the current helpdesk stores rupees.

Do not treat duplicated migration or re-import rows
as separate customer tickets when calculating
canonical refund totals.
""".strip()

    return summary


# ============================================================
# RAG DOCUMENT STORE
# ============================================================

@lru_cache(maxsize=1)
def load_rag_documents() -> list[dict]:

    documents = []

    # --------------------------------------------------------
    # REFERENCE FILES
    # --------------------------------------------------------

    documents.extend(
        load_reference_documents()
    )

    # --------------------------------------------------------
    # DATA
    # --------------------------------------------------------

    from data_loader import (
        load_data,
        build_canonical_tickets,
    )

    data = load_data()

    raw_tickets = data[
        "tickets"
    ]

    canonical = (
        build_canonical_tickets(
            raw_tickets
        )
    )

    customers = data[
        "customers"
    ].copy()

    orders = data[
        "orders"
    ].copy()

    products = data[
        "products"
    ].copy()

    # --------------------------------------------------------
    # LOOKUPS
    # --------------------------------------------------------

    customer_lookup = {}

    if (
        "customer_id"
        in customers.columns
    ):

        customer_lookup = (
            customers
            .drop_duplicates(
                "customer_id"
            )
            .set_index(
                "customer_id"
            )
            .to_dict(
                "index"
            )
        )

    order_lookup = {}

    if (
        "order_id"
        in orders.columns
    ):

        order_lookup = (
            orders
            .drop_duplicates(
                "order_id"
            )
            .set_index(
                "order_id"
            )
            .to_dict(
                "index"
            )
        )

    product_lookup = {}

    if (
        "sku"
        in products.columns
    ):

        product_lookup = (
            products
            .drop_duplicates(
                "sku"
            )
            .set_index(
                "sku"
            )
            .to_dict(
                "index"
            )
        )

    # --------------------------------------------------------
    # ANALYTICS SUMMARY
    # --------------------------------------------------------

    documents.append(
        {
            "source": "data_summary",
            "type": "analytics",
            "id": "business-summary",
            "content": build_business_summary(
                raw_tickets,
                canonical,
            ),
        }
    )

    # --------------------------------------------------------
    # TICKETS
    # --------------------------------------------------------

    for _, row in (
        canonical.iterrows()
    ):

        ticket_id = clean_text(
            row.get(
                "ticket_id"
            )
        )

        customer_id = clean_text(
            row.get(
                "customer_id"
            )
        )

        order_id = clean_text(
            row.get(
                "order_id"
            )
        )

        sku = clean_text(
            row.get(
                "product_sku"
            )
        )

        customer = (
            customer_lookup.get(
                customer_id
            )
        )

        order = (
            order_lookup.get(
                order_id
            )
        )

        product = (
            product_lookup.get(
                sku
            )
        )

        ticket_text = build_ticket_document(
            row,
            (
                pd.Series(customer)
                if customer
                else None
            ),
            (
                pd.Series(order)
                if order
                else None
            ),
            (
                pd.Series(product)
                if product
                else None
            ),
        )

        documents.append(
            {
                "source": "tickets.csv",
                "type": "ticket",
                "id": ticket_id,
                "content": ticket_text,
            }
        )

    return documents


# ============================================================
# TF-IDF INDEX
# ============================================================

@lru_cache(maxsize=1)
def build_rag_index():

    documents = (
        load_rag_documents()
    )

    corpus = [
        document[
            "content"
        ]
        for document in documents
    ]

    vectorizer = TfidfVectorizer(
        lowercase=True,
        stop_words="english",
        ngram_range=(
            1,
            2,
        ),
        max_features=50000,
    )

    matrix = (
        vectorizer.fit_transform(
            corpus
        )
    )

    return (
        documents,
        vectorizer,
        matrix,
    )


# ============================================================
# QUERY INTENT
# ============================================================

def detect_query_intent(
    query: str,
) -> str:

    q = query.lower().strip()

    # --------------------------------------------------------
    # EXACT TICKET
    # --------------------------------------------------------

    if re.search(
        r"\btk-\d+\b",
        q,
    ):
        return "ticket"

    # --------------------------------------------------------
    # RECONCILIATION
    # --------------------------------------------------------

    reconciliation_words = [
        "reconciliation",
        "reconcile",
        "mismatch",
        "overstate",
        "overstated",
        "overstatement",
        "duplicate",
        "duplicates",
        "migration",
        "migrated",
        "legacy",
        "freshdesk",
        "export",
        "crore",
        "lakh",
        "wrong amount",
        "wrong total",
        "refund export",
    ]

    if any(
        word in q
        for word in reconciliation_words
    ):
        return "reconciliation"

    # --------------------------------------------------------
    # ANALYTICS
    # --------------------------------------------------------
    #
    # IMPORTANT:
    # Calculated-value questions must be classified as analytics
    # before generic refund-reason matching.
    #
    # This explicit rule protects the key dashboard question:
    # "What is the largest refund reason and its refund value?"
    # from being classified as a reason-code lookup.
    # --------------------------------------------------------

    largest_refund_value_patterns = [
        "largest refund reason",
        "highest refund reason",
        "biggest refund reason",
        "largest refund value",
        "highest refund value",
    ]

    if any(
        phrase in q
        for phrase in largest_refund_value_patterns
    ):
        return "analytics"

    analytics_words = [
        "how much",
        "how many",
        "total",
        "amount",
        "highest",
        "lowest",
        "largest",
        "smallest",
        "average",
        "avg",
        "rate",
        "trend",
        "monthly",
        "by channel",
        "by team",
        "by agent",
        "csat",
        "refund value",
        "refund volume",
        "refund count",
        "refund amount",
    ]

    if any(
        word in q
        for word in analytics_words
    ):
        return "analytics"

    # --------------------------------------------------------
    # REFUND REASONS
    # --------------------------------------------------------

    reason_patterns = [
        "reason for refund",
        "reasons for refund",
        "reasons for refunds",
        "refund reasons",
        "refund reason",
        "reason code",
        "reason codes",
        "meaning of gw-other",
        "meaning of doa-repl",
        "meaning of lost-transit",
        "meaning of dup-payment",
        "meaning of cancel",
        "meaning of price-adj",
        "meaning of return-qc-ok",
        "meaning of wty-buyback",
    ]

    if any(
        phrase in q
        for phrase in reason_patterns
    ):
        return "reason"

    # --------------------------------------------------------
    # POLICY
    # --------------------------------------------------------

    policy_words = [
        "policy",
        "policies",
        "rule",
        "rules",
        "eligible",
        "eligibility",
        "refund policy",
        "replacement policy",
        "sla",
        "service level",
        "service levels",
        "goodwill",
        "dead-on-arrival",
        "dead on arrival",
        "doa",
        "warranty",
        "team lead",
        "finance",
        "replacement rule",
        "refund rule",
        "how long",
    ]

    if any(
        word in q
        for word in policy_words
    ):
        return "policy"

    # --------------------------------------------------------
    # GENERAL
    # --------------------------------------------------------

    return "general"


# ============================================================
# RETRIEVAL
# ============================================================

def retrieve_documents(
    query: str,
    top_k: int = 7,
) -> list[dict]:

    query = query.strip()

    if not query:
        return []

    documents, vectorizer, matrix = (
        build_rag_index()
    )

    query_vector = (
        vectorizer.transform(
            [query]
        )
    )

    scores = cosine_similarity(
        query_vector,
        matrix,
    )[0]

    intent = detect_query_intent(
        query
    )

    # --------------------------------------------------------
    # EXACT TICKET ID
    # --------------------------------------------------------

    ticket_match = re.search(
        r"\bTK-\d+\b",
        query.upper(),
    )

    requested_ticket = (
        ticket_match.group(0)
        if ticket_match
        else None
    )

    # --------------------------------------------------------
    # SOURCE FILTERING BY INTENT
    # --------------------------------------------------------

    candidate_indexes = []

    for index, document in enumerate(
        documents
    ):

        doc_type = document[
            "type"
        ]

        # ====================================================
        # EXACT TICKET
        # ====================================================

        if intent == "ticket":

            if (
                doc_type == "ticket"
                and requested_ticket
                and document[
                    "id"
                ].upper()
                == requested_ticket
            ):

                candidate_indexes.append(
                    index
                )

            continue

        # ====================================================
        # POLICY
        # ====================================================

        if intent == "policy":

            if doc_type in {
                "policy",
                "knowledge",
            }:

                candidate_indexes.append(
                    index
                )

            continue

        # ====================================================
        # RECONCILIATION
        # ====================================================

        if intent == "reconciliation":

            if doc_type in {
                "analytics",
                "email",
                "policy",
            }:

                candidate_indexes.append(
                    index
                )

            continue

        # ====================================================
        # REFUND REASONS
        # ====================================================

        if intent == "reason":

            if doc_type in {
                "analytics",
                "policy",
                "knowledge",
            }:

                candidate_indexes.append(
                    index
                )

            continue

        # ====================================================
        # ANALYTICS
        # ====================================================

        if intent == "analytics":

            # Strictly use the calculated analytics summary.
            # This prevents random ticket, policy, email, or
            # knowledge documents from being returned for
            # numerical/dashboard questions.

            if (
                doc_type == "analytics"
                and document.get("id") == "business-summary"
            ):

                candidate_indexes.append(
                    index
                )

            continue

        # ====================================================
        # GENERAL
        # ====================================================

        candidate_indexes.append(
            index
        )

    # --------------------------------------------------------
    # RANK
    # --------------------------------------------------------

    # Analytics queries have a single authoritative source.
    # Rank it deterministically rather than relying only on
    # TF-IDF similarity.
    if intent == "analytics" and candidate_indexes:
        ranked_indexes = candidate_indexes.copy()
    else:
        ranked_indexes = sorted(
            candidate_indexes,
            key=lambda index:
                float(scores[index]),
            reverse=True,
        )

    results = []

    # --------------------------------------------------------
    # EXACT TICKET FIRST
    # --------------------------------------------------------

    if requested_ticket:

        for index in ranked_indexes:

            document = documents[
                index
            ]

            if (
                document[
                    "type"
                ] == "ticket"
                and document[
                    "id"
                ].upper()
                == requested_ticket
            ):

                exact_document = (
                    document.copy()
                )

                exact_document[
                    "score"
                ] = 1.0

                results.append(
                    exact_document
                )

                break

    # --------------------------------------------------------
    # OTHER RELEVANT DOCUMENTS
    # --------------------------------------------------------

    for index in ranked_indexes:

        document = documents[
            index
        ]

        # Skip exact ticket
        if requested_ticket:

            if (
                document[
                    "type"
                ] == "ticket"
                and document[
                    "id"
                ].upper()
                == requested_ticket
            ):

                continue

        score = float(
            scores[index]
        )

        if score <= 0:
            continue

        result = (
            document.copy()
        )

        result[
            "score"
        ] = score

        results.append(
            result
        )

        if len(results) >= top_k:
            break

    return results[:top_k]


# ============================================================
# CONTEXT BUILDER
# ============================================================

def build_context(
    retrieved_documents: list[dict],
    max_chars: int = 18000,
) -> str:

    context_parts = []
    current_length = 0

    for index, document in enumerate(
        retrieved_documents,
        start=1,
    ):

        content = document[
            "content"
        ]

        remaining = (
            max_chars
            - current_length
        )

        if remaining <= 0:
            break

        content = content[
            :remaining
        ]

        source = document[
            "source"
        ]

        doc_type = document[
            "type"
        ]

        doc_id = document[
            "id"
        ]

        block = f"""
SOURCE {index}

File: {source}

Type: {doc_type}

ID: {doc_id}

{content}
""".strip()

        context_parts.append(
            block
        )

        current_length += len(
            block
        )

    return (
        "\n\n"
        "=============================="
        "\n\n"
        .join(
            context_parts
        )
    )


# ============================================================
# GEMINI ANSWER
# ============================================================

def generate_answer(
    question: str,
    context: str,
) -> str:

    client = get_client()

    prompt = f"""
You are Vireo AI, an internal refund and
customer-support assistant for Vireo Audio.

Answer the user's question using ONLY the
retrieved Vireo context below.

IMPORTANT RULES:

1. Never invent ticket details, policy rules,
   amounts, dates, customers, products or
   operational facts.

2. If the retrieved context does not contain
   enough information, clearly say that the
   available sources do not provide enough
   information.

3. Distinguish between:
   - written policy
   - actual ticket/data findings
   - internal email discussion
   - calculated analytics summary

4. For policy questions, prioritize
   support-policy.pdf.

5. For reconciliation questions, use
   data_summary and email-thread evidence.

6. For refund-reason questions, use the
   data_summary for actual refund values/counts
   and support-policy.pdf for reason-code meanings.

7. For exact ticket questions, answer only
   from the exact retrieved ticket record.

8. For analytics questions, use the calculated
   data_summary values.

9. Do not treat duplicate export rows as
   separate canonical tickets.

10. Keep the answer professional and concise.

11. Do NOT create a separate Sources section.
    The application adds retrieved sources
    automatically.

USER QUESTION:

{question}

RETRIEVED VIREO CONTEXT:

{context}
""".strip()

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            automatic_function_calling=(
                types.AutomaticFunctionCallingConfig(
                    disable=True
                )
            ),
        ),
    )

    answer = getattr(
        response,
        "text",
        None,
    )

    if not answer:

        return (
            "I could not generate an answer "
            "from the available Vireo sources."
        )

    return answer.strip()


# ============================================================
# PUBLIC FUNCTION
# ============================================================

def ask_refund_ai(
    question: str,
    top_k: int = 7,
) -> str:

    question = question.strip()

    if not question:

        return (
            "Please enter a question."
        )

    # --------------------------------------------------------
    # RETRIEVE
    # --------------------------------------------------------

    retrieved = retrieve_documents(
        question,
        top_k=top_k,
    )

    if not retrieved:

        return (
            "I could not find relevant "
            "information in the available "
            "Vireo sources for this question."
        )

    # --------------------------------------------------------
    # CONTEXT
    # --------------------------------------------------------

    context = build_context(
        retrieved,
        max_chars=18000,
    )

    # --------------------------------------------------------
    # GEMINI
    # --------------------------------------------------------

    answer = generate_answer(
        question,
        context,
    )

    # --------------------------------------------------------
    # SOURCE FOOTER
    # --------------------------------------------------------

    source_items = []
    seen = set()

    for document in retrieved:

        source = document[
            "source"
        ]

        if source in seen:
            continue

        seen.add(
            source
        )

        if document[
            "type"
        ] == "ticket":

            source_items.append(
                f"- {source} "
                f"({document['id']})"
            )

        else:

            source_items.append(
                f"- {source}"
            )

    source_footer = (
        "\n\n---\n"
        "**Retrieved sources**\n"
        + "\n".join(
            source_items
        )
    )

    return (
        answer
        + source_footer
    )


# ============================================================
# TERMINAL TEST
# ============================================================

if __name__ == "__main__":

    print(
        "Vireo Refund AI - Multi-Source RAG"
    )

    print(
        "=" * 45
    )

    # --------------------------------------------------------
    # DOCUMENT COUNT
    # --------------------------------------------------------

    documents = (
        load_rag_documents()
    )

    print(
        f"Total RAG documents: "
        f"{len(documents):,}"
    )

    # --------------------------------------------------------
    # TYPE COUNTS
    # --------------------------------------------------------

    type_counts = {}

    for document in documents:

        doc_type = document[
            "type"
        ]

        type_counts[
            doc_type
        ] = (
            type_counts.get(
                doc_type,
                0
            )
            + 1
        )

    print(
        "\nDocument types:"
    )

    for doc_type, count in (
        type_counts.items()
    ):

        print(
            f"- {doc_type}: "
            f"{count:,}"
        )

    # --------------------------------------------------------
    # POLICY TEST
    # --------------------------------------------------------

    print(
        "\nTesting policy retrieval..."
    )

    policy_question = (
        "What is the refund policy for "
        "a dead-on-arrival product "
        "within 7 days?"
    )

    policy_results = retrieve_documents(
        policy_question,
        top_k=5,
    )

    for index, document in enumerate(
        policy_results,
        start=1,
    ):

        print(
            f"{index}. "
            f"{document['source']} "
            f"[{document['type']}] "
            f"score="
            f"{document['score']:.4f}"
        )

    # --------------------------------------------------------
    # TICKET TEST
    # --------------------------------------------------------

    print(
        "\nTesting ticket retrieval..."
    )

    ticket_question = (
        "Tell me the details of "
        "ticket TK-240003."
    )

    ticket_results = retrieve_documents(
        ticket_question,
        top_k=5,
    )

    for index, document in enumerate(
        ticket_results,
        start=1,
    ):

        print(
            f"{index}. "
            f"{document['source']} "
            f"[{document['type']}] "
            f"ID={document['id']} "
            f"score="
            f"{document['score']:.4f}"
        )

    # --------------------------------------------------------
    # UNKNOWN TICKET TEST
    # --------------------------------------------------------

    print(
        "\nTesting unknown ticket..."
    )

    unknown_ticket_question = (
        "Tell me the details of "
        "ticket TK-999999."
    )

    unknown_ticket_results = (
        retrieve_documents(
            unknown_ticket_question,
            top_k=5,
        )
    )

    if not unknown_ticket_results:

        print(
            "No matching ticket found."
        )

    else:

        for index, document in enumerate(
            unknown_ticket_results,
            start=1,
        ):

            print(
                f"{index}. "
                f"{document['source']} "
                f"[{document['type']}] "
                f"ID={document['id']} "
                f"score="
                f"{document['score']:.4f}"
            )

    # --------------------------------------------------------
    # RECONCILIATION TEST
    # --------------------------------------------------------

    print(
        "\nTesting reconciliation retrieval..."
    )

    reconciliation_question = (
        "Why does the refund "
        "export require reconciliation?"
    )

    reconciliation_results = (
        retrieve_documents(
            reconciliation_question,
            top_k=5,
        )
    )

    for index, document in enumerate(
        reconciliation_results,
        start=1,
    ):

        print(
            f"{index}. "
            f"{document['source']} "
            f"[{document['type']}] "
            f"score="
            f"{document['score']:.4f}"
        )

    # --------------------------------------------------------
    # ANALYTICS TEST
    # --------------------------------------------------------

    print(
        "\nTesting analytics retrieval..."
    )

    analytics_question = (
        "What is the largest refund "
        "reason and its refund value?"
    )

    analytics_intent = detect_query_intent(
        analytics_question
    )

    print(
        f"Detected intent: "
        f"{analytics_intent}"
    )

    analytics_results = retrieve_documents(
        analytics_question,
        top_k=5,
    )

    for index, document in enumerate(
        analytics_results,
        start=1,
    ):

        print(
            f"{index}. "
            f"{document['source']} "
            f"[{document['type']}] "
            f"score="
            f"{document['score']:.4f}"
        )

    # --------------------------------------------------------
    # REASON TEST
    # --------------------------------------------------------

    print(
        "\nTesting refund-reason retrieval..."
    )

    reason_question = (
        "What are the main reasons "
        "for refunds?"
    )

    reason_intent = detect_query_intent(
        reason_question
    )

    print(
        f"Detected intent: "
        f"{reason_intent}"
    )

    reason_results = retrieve_documents(
        reason_question,
        top_k=5,
    )

    for index, document in enumerate(
        reason_results,
        start=1,
    ):

        print(
            f"{index}. "
            f"{document['source']} "
            f"[{document['type']}] "
            f"score="
            f"{document['score']:.4f}"
        )

    # --------------------------------------------------------
    # GEMINI TEST
    # --------------------------------------------------------

    print(
        "\nTesting Gemini...\n"
    )

    try:

        answer = ask_refund_ai(
            policy_question
        )

        print(
            answer
        )

    except Exception as error:

        print(
            "Gemini request failed:"
        )

        print(
            error
        )