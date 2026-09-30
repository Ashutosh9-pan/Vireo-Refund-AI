# Vireo Refund AI — Business Memo

## Executive summary

The Vireo Refund AI dashboard reconciles the supplied support-ticket export into a canonical ticket view and combines refund analytics with a grounded AI assistant.

The key data-quality issue is that the export contains duplicate/migration records and data originating from both the current helpdesk and legacy Freshdesk system. The project therefore separates raw export rows from canonical ticket-level analysis.

## Data reconciliation findings

The tested dashboard view contains:

- **12,238** raw ticket rows.
- **11,600** unique ticket IDs.
- **638** duplicate export rows.

The canonical refund analysis contains:

- **2,340** refund tickets.
- **₹6,709,932** canonical refund value.
- Average refund of approximately **₹2,867**.
- Refund rate of approximately **20.2%**.
- Average CSAT of approximately **3.49/5**.

## Refund concentration

`GW-OTHER` is the largest refund reason by refund value in the tested all-filter dashboard view, with **₹2,907,036**, representing approximately **43.3%** of canonical refund value.

The highest monthly refund value in the same view is **November 2025**, at approximately **₹575,984**.

## Operational interpretation

The reconciliation workflow is important because raw exported rows are not equivalent to unique canonical tickets. The supplied support policy also documents a system transition between the legacy Freshdesk tool and the current helpdesk, including a legacy monetary-unit difference.

The internal email thread reinforces that Finance saw a much larger export total than the helpdesk report and that migration re-imports can create duplicate appearances. The project therefore treats reconciliation as a required data-preparation step before reporting refund totals.

## Policy considerations

The supplied support policy states that for a dead-on-arrival product within seven days of delivery, the customer chooses either a full refund or a replacement. It also states that a customer should not receive both a refund and a replacement for the same order.

The policy defines refund reason codes including `GW-OTHER`, `DOA-REPL`, `LOST-TRANSIT`, `DUP-PAYMENT`, `CANCEL`, `PRICE-ADJ`, `RETURN-QC-OK`, and `WTY-BUYBACK`.

## AI assistant

Ask Vireo uses a source-aware RAG pipeline:

1. Detect query intent.
2. Retrieve relevant Vireo sources.
3. Build a bounded context.
4. Generate a grounded answer with Gemini.
5. Display the retrieved sources.

The assistant has been tested on policy questions, reconciliation questions, aggregate analytics, exact-ticket lookup, missing ticket IDs and out-of-scope questions.

## Recommendation for continued use

Treat the canonical dataset as the reporting layer, retain the raw export for audit/reconciliation purposes, and use Ask Vireo as a grounded support-analysis interface rather than as an unrestricted general-purpose chatbot.
