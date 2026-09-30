# 💳 Vireo Refund AI

Vireo Refund AI is a Streamlit-based refund intelligence dashboard and grounded AI assistant built for analyzing Vireo Audio support-ticket data.

It combines deterministic analytics, source-aware retrieval, and Google Gemini to answer refund, support, reconciliation, and ticket-level questions from the supplied data pack.

---

## 📸 Project Screenshots

### Dashboard overview

Shows the main KPI layer, interactive filters, and refund analytics by reason and channel.

![Vireo Refund AI dashboard](docs/screenshots/dashboard-overview.png)

### Analytics + AI assistant

Shows the Business Snapshot and an analytics question answered from the calculated data summary.

![Vireo Refund AI analytics assistant](docs/screenshots/analytics-ai-response.png)

### RAG knowledge response

Shows a grounded refund-reason response with retrieved policy and knowledge sources.

![Vireo Refund AI RAG response](docs/screenshots/rag-knowledge-response.png)

### Exact ticket retrieval

Shows the AI assistant retrieving the exact canonical record for `TK-240003` and displaying its source.

![Vireo Refund AI ticket retrieval](docs/screenshots/ticket-retrieval.png)

### Unknown ticket handling

Shows the assistant returning a source-availability message for an unknown ticket instead of fabricating ticket details.

![Vireo Refund AI unknown ticket handling](docs/screenshots/unknown-ticket-handling.png)

---

## 🚀 What the project does

- Analyzes support tickets, refunds, CSAT, channels, teams, priorities and agents.
- Uses one canonical ticket record per `ticket_id` for refund analysis.
- Reconciles migrated helpdesk/Freshdesk records and legacy monetary fields.
- Provides ticket-level refund exploration.
- Provides an AI assistant, **Ask Vireo**, using retrieval-augmented generation (RAG) with Gemini.
- Grounds answers in the available policy, internal email thread, knowledge files, analytical summary and canonical ticket records.
- Displays retrieved sources with AI responses.
- Handles unknown or unsupported requests without inventing unsupported Vireo data.

---

## 📊 Dashboard features

### KPI overview

The dashboard reports:

- Ticket volume
- Refund-ticket volume
- Refund amount
- Average refund
- Refund rate
- Average CSAT

### Refund analysis

Refund activity can be analyzed by:

- Reason code
- Channel
- Month
- Team
- Agent

### Interactive filters

The dashboard supports filtering by:

- Channel
- Team
- Status
- Priority

### Ticket explorer

Refund tickets can be searched by:

- Ticket ID
- Customer ID
- Order ID

### Data reconciliation

The dashboard exposes raw ticket rows, unique ticket IDs, duplicate export rows and source-system counts so migrated data can be reconciled before financial analysis.

---

## 🤖 Ask Vireo — RAG architecture

```text
                    User Question
                          |
                          v
                    Intent Detection
                          |
                          v
                 Source-aware Retrieval
                          |
          +---------------+----------------+
          |               |                |
          v               v                v
   support-policy   email-thread     knowledge/*.md/txt
          |               |                |
          +---------------+----------------+
                          |
             +------------+------------+
             |                         |
             v                         v
       data_summary             canonical tickets
             |
             +------------+------------+
                          |
                          v
                 TF-IDF + Cosine Similarity
                          |
                          v
                  Retrieved Context
                          |
                          v
                      Gemini
                          |
                          v
              Grounded Answer + Sources
```

The retrieval layer is intentionally source-aware:

- **Policy questions** use `support-policy.pdf` and supporting knowledge documents.
- **Exact ticket questions** retrieve the requested canonical ticket record only.
- **Reconciliation questions** use the analytical summary and internal email thread, with policy context where useful.
- **Analytics questions** use the deterministic `data_summary` document.
- **Refund-reason questions** combine analytical findings with policy reason-code meanings.

This design keeps calculations deterministic while using Gemini for natural-language synthesis.

---

## 🗂️ Data sources

The project uses the supplied Vireo support data pack:

- `data/tickets.csv` — support-ticket export.
- `data/agents.csv` — agent roster/assignments.
- `data/customers.csv` — customer records.
- `data/orders.csv` — order records.
- `data/products.csv` — product catalog.
- `data/support-policy.pdf` — customer-support operating policy v3.2.
- `data/email-thread.txt` — internal discussion about the refund reconciliation task.
- `knowledge/` — project knowledge files used by the RAG layer.

The ticket export covers support activity from January 2025 through June 2026, with timestamps supplied by the source data in IST.

---

## 🔍 Data reconciliation approach

The canonical ticket dataset contains one record per `ticket_id`.

When the same ticket appears in both migrated/legacy and current helpdesk data, the current helpdesk record is preferred.

The legacy system stores monetary fields in its native unit while the current helpdesk stores rupees. Legacy-only monetary values are normalized by the canonical data loader before refund analysis.

Duplicate migration/re-import rows are not counted as separate canonical tickets.

---

## 📈 Current verified dashboard findings

Using the tested all-filter dashboard view:

| Metric | Value |
|---|---:|
| Raw ticket rows | 12,238 |
| Unique/canonical ticket IDs | 11,600 |
| Duplicate export rows | 638 |
| Refund tickets | 2,340 |
| Canonical refund amount | ₹6,709,932 |
| Average refund | ~₹2,867 |
| Refund rate | ~20.2% |
| Average CSAT | ~3.49/5 |
| Largest refund reason by value | `GW-OTHER` — ₹2,907,036 |
| Highest monthly refund value | `2025-11` — ₹575,984 |

These values depend on the canonical reconciliation logic and the current all-filter dashboard view.

---

## 🧪 Testing

The project has an automated pytest suite covering the core retrieval and reconciliation behavior.

Latest verified result:

```text
10 passed
```

The tested scenarios include:

- Canonical ticket creation.
- Preference for the helpdesk record when both source systems contain the same ticket.
- Policy intent detection.
- Reconciliation intent detection.
- Analytics intent detection.
- Refund-reason intent detection.
- Exact ticket intent detection.
- Exact retrieval of `TK-240003`.
- Unknown ticket handling for `TK-999999`.
- Analytics retrieval restricted to the analytical summary rather than random ticket records.

---

## 🛠️ Technology stack

- Python
- Pandas
- Scikit-learn
- PyPDF
- Plotly
- Streamlit
- Google Gemini API (`google-genai`)
- python-dotenv
- Pytest

---

## 📁 Project structure

```text
Vireo-Refund-AI/
├── data/
│   ├── agents.csv
│   ├── customers.csv
│   ├── email-thread.txt
│   ├── orders.csv
│   ├── products.csv
│   ├── support-policy.pdf
│   └── tickets.csv
├── docs/
│   ├── screenshots/
│   │   ├── dashboard-overview.png
│   │   ├── analytics-ai-response.png
│   │   ├── rag-knowledge-response.png
│   │   ├── ticket-retrieval.png
│   │   └── unknown-ticket-handling.png
│   ├── decisions.md
│   └── memo.md
├── knowledge/
│   └── refund_guide.md
├── outputs/
├── src/
│   ├── analysis.py
│   ├── app.py
│   ├── data_loader.py
│   ├── refund_analyzer.py
│   └── rag_engine.py
├── tests/
│   └── test_refund_analyzer.py
├── .env
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

---

## ⚙️ Local setup

### 1. Create and activate the virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 3. Configure Gemini

Create `.env` in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key
```

Do **not** commit `.env` or expose the API key publicly.

### 4. Run the dashboard

```powershell
python -m streamlit run src\app.py
```

Open the local Streamlit URL shown in the terminal, normally:

```text
http://localhost:8501
```

### 5. Run the automated tests

```powershell
python -m pytest -v
```

### 6. Optional RAG smoke test

```powershell
python src\rag_engine.py
```

This command runs retrieval/Gemini smoke tests and exits when complete. The RAG module does not need to remain running separately from Streamlit.

---

## 💬 Example Ask Vireo questions

```text
What is the refund policy for a dead-on-arrival product within 7 days?
```

```text
Why does the refund export require reconciliation?
```

```text
What is the largest refund reason and its refund value?
```

```text
Tell me the details of ticket TK-240003.
```

```text
Tell me the details of ticket TK-999999.
```

---

## 🛡️ Grounding and safety behavior

Ask Vireo is designed to minimize unsupported claims:

- Exact ticket requests are constrained to the requested record.
- Analytics questions use deterministic summary values.
- Policy questions are grounded in the written support policy.
- Retrieved sources are displayed with AI answers.
- Unknown ticket IDs return a source-availability message instead of fabricated ticket details.
- Out-of-scope questions are not answered from unrelated ticket data.

---

## 🔐 Configuration and secrets

The project uses `.env` for the Gemini API key at runtime.

The repository should keep:

```text
.env
.venv/
.pytest_cache/
__pycache__/
```

out of version control through `.gitignore`.

Use `.env.example` as the safe configuration template.

---

## 📝 Project notes

The project uses Gemini rather than OpenAI for generation. The runtime client is loaded from the `GEMINI_API_KEY` environment variable.

The dashboard calculations remain deterministic and are performed with Pandas, while Gemini is used to turn retrieved Vireo context into a natural-language response.

---

## 📌 Status

**Functional and locally verified.**

Dashboard, filters, source-aware RAG retrieval, Gemini responses, ticket retrieval, unknown-ticket handling and automated tests have been exercised successfully during development.
