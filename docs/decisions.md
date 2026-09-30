# Vireo Refund AI — Technical Decisions

## 1. Canonical ticket grain

**Decision:** Use one canonical record per `ticket_id` for refund analysis.

**Reason:** The supplied export contains duplicate/migration rows. Counting every exported row as a separate ticket would inflate ticket and refund metrics.

**Implementation:** `build_canonical_tickets()` builds the canonical dataset and prefers the current helpdesk record when the same ticket appears in both systems.

## 2. Legacy monetary normalization

**Decision:** Normalize legacy-only refund amounts before calculating canonical refund metrics.

**Reason:** The supplied policy states that the legacy tool stored monetary values in its own native unit while the current helpdesk stores rupees. The canonical data loader applies the project reconciliation normalization for legacy-only records.

**Important distinction:** The written policy supports the existence of different monetary units; the exact normalization used by the project is a data-reconciliation finding/implementation decision rather than a policy statement.

## 3. RAG instead of direct Gemini prompting

**Decision:** Use retrieval-augmented generation rather than sending the user question directly to Gemini.

**Reason:** The assistant needs to answer from Vireo-specific sources and avoid unsupported answers.

## 4. TF-IDF retrieval

**Decision:** Use TF-IDF vectors with cosine similarity.

**Reason:** It is lightweight, local, deterministic and sufficient for the supplied dataset without introducing an external vector database.

## 5. Source-aware retrieval

**Decision:** Retrieval is filtered by query intent.

**Rules:**

- Ticket ID present → retrieve the exact canonical ticket.
- Policy/rule query → policy/knowledge sources.
- Reconciliation query → data summary, email thread and policy.
- Refund-reason query → data summary, policy and knowledge.
- Analytics query → data summary.
- General query → normal TF-IDF retrieval.

**Reason:** This prevents unrelated tickets from being surfaced for policy and aggregate analytics questions.

## 6. Deterministic analytical summary

**Decision:** Create a `data_summary` document from canonical data before retrieval.

**Reason:** Aggregate questions such as largest refund reason, total refund value and monthly refund values should use deterministic calculations rather than asking the language model to calculate from thousands of ticket records.

## 7. Grounded Gemini prompt

**Decision:** Gemini receives only the retrieved Vireo context.

**Rules:**

- Do not invent facts.
- Policy questions prioritize `support-policy.pdf`.
- Reconciliation answers distinguish data findings from written policy and email discussion.
- Exact ticket questions use the exact retrieved ticket.
- Analytics answers use calculated summary values.

## 8. Gemini automatic function calling

**Decision:** Disable automatic function calling in the Gemini generation configuration.

**Reason:** The application does not use Gemini tools/functions and therefore does not need automatic function-calling behavior.

## 9. Source traceability

**Decision:** Add a deterministic retrieved-source footer to each AI response.

**Reason:** Users reviewing an answer should be able to see which project source types were retrieved.

## 10. Out-of-scope and missing-record behavior

**Decision:** Return a clear source-availability message when no relevant record is retrieved.

**Reason:** The assistant should not fabricate ticket information or answer unrelated questions as though they came from the Vireo data.

## 11. AI provider

**Decision:** Use Google Gemini through the `google-genai` Python SDK.

**Reason:** Gemini is the configured provider for this project. OpenAI is not required for the current implementation.
