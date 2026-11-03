# Decision Log

This log records every relevant decision made while building the agent: who made it, how the
AI coding assistant (Claude, via claude.ai and Claude Code) contributed, which alternatives were
considered, and what impact the decision has on the project. New entries are added in the same
commit that implements them, so the Git history shows when each decision was taken.

**Attribution legend**

- **Jackson** — decision proposed and made by me.
- **Claude → Jackson** — suggested by the assistant, reviewed and accepted (or adjusted) by me.
- **Jackson + Claude** — I set the direction, the assistant refined the details.

---

## D01 — Hybrid agent architecture

| | |
|---|---|
| **Decided by** | Claude → Jackson |
| **Decision** | Use function calling over the structured data (CSV tables) and on-demand retrieval for the policy manual, instead of a single technique for everything. |
| **Alternatives** | Pure RAG over everything; SQL agent (text-to-SQL); ReAct with free-form tools. |
| **Claude's contribution** | Proposed the split after reading the challenge: CSVs are exact, structured data (prices, stock, order status), while the manual is prose. Each kind of data gets the retrieval method that fits it. |
| **Rationale** | Prices and stock must be exact — semantic search over tables can return "close enough" rows. Policies are text and need to be read, not queried. |
| **Impact** | ✅ Exact answers for prices, stock and orders; fewer hallucinations. ⚠️ Two retrieval paths to maintain. |
| **Status** | Accepted |

## D02 — Policy manual served through a tool, not loaded into the system prompt

| | |
|---|---|
| **Decided by** | **Jackson** |
| **Decision** | Expose the manual through `get_store_policy(topic)` and load only the relevant section when needed. |
| **Alternatives** | Put the whole manual (~8 pages) in the system prompt (Claude initially presented both options as defensible). |
| **Claude's contribution** | After my decision, pointed out three nuances that complete the argument: (1) tool schemas are also sent on every request, but they cost a few hundred tokens vs. a few thousand for the manual; (2) the new risk is the model *not calling* the tool and answering from generic knowledge — mitigated by an explicit rule in the prompt and by tests; (3) what applies to every message (persona, tone, scope) stays in the prompt. Resulting rule: **behavior in the prompt, knowledge on demand through tools.** |
| **Rationale** | Token cost and context usage proportional to the question, not to the size of the manual. |
| **Impact** | ✅ Lower cost per message, scales if the manual grows. ⚠️ Model may skip the tool → mitigated by prompt rule + scenario tests. |
| **Status** | Accepted |

## D03 — No vector store / embeddings; topic enum mapped to manual sections

| | |
|---|---|
| **Decided by** | Claude → Jackson |
| **Decision** | Split the manual by section and index it by a fixed `topic` enum (hours, payment, returns, shipping, promotions, warranty, privacy, about/contact). |
| **Alternatives** | Embeddings + vector DB; keyword search. |
| **Claude's contribution** | Measured the manual (~8 pages, 10 sections) and argued that a vector store would be more a point of failure than a solution at this size. Proposed the enum design. Section 7 (WhatsApp service guidelines) describes *how to behave*, so it becomes system prompt instructions instead of a topic. |
| **Rationale** | Deterministic, no extra infrastructure, trivially testable. |
| **Impact** | ✅ Zero retrieval errors for known topics, no extra dependency. ⚠️ Does not scale to hundreds of pages — would revisit with embeddings (listed in limitations). |
| **Status** | Accepted |

## D04 — Gemini as the LLM, behind a provider abstraction

| | |
|---|---|
| **Decided by** | **Jackson** (Gemini) + Claude (abstraction layer) |
| **Decision** | Use Google Gemini through the official `google-genai` SDK, wrapped by a small provider interface so the model can be swapped by configuration. |
| **Alternatives** | Paid APIs (OpenAI, Anthropic); local models (Ollama). |
| **Claude's contribution** | Suggested the abstraction layer and documenting the free-tier rate limit as a known limitation. |
| **Rationale** | Free tier → zero cost for me and for the evaluators running the project; good native function-calling support. |
| **Impact** | ✅ Easy for anyone to run. ⚠️ Free-tier quotas/rate limits can interrupt long sessions → documented. |
| **Status** | Accepted |

## D05 — Simple web UI with Streamlit

| | |
|---|---|
| **Decided by** | **Jackson** (simple UI) + Claude (Streamlit) |
| **Decision** | Chat interface in Streamlit. |
| **Alternatives** | CLI, notebook, REST API, Gradio. |
| **Claude's contribution** | Suggested Streamlit or Gradio as the fastest path; Streamlit chosen for its native chat components. |
| **Impact** | ✅ Fast to build and demo. ⚠️ Not a production channel (the real channel would be WhatsApp). |
| **Status** | Accepted |

## D06 — Conversation history persisted for 7 days

| | |
|---|---|
| **Decided by** | **Jackson** (7-day retention) + Claude (storage details) |
| **Decision** | SQLite store keyed by `session_id`, with a 7-day TTL. Only user and assistant messages are stored — raw tool results are discarded. |
| **Alternatives** | No persistence; in-memory only; storing the full transcript including tool outputs. |
| **Claude's contribution** | Proposed SQLite + TTL, and pointed out that re-sending stored tool results every turn would cancel the token savings from D02 — so tool outputs are not persisted. Also framed the TTL as data minimization (LGPD). |
| **Rationale** | A customer can come back within the week and continue the conversation; data is not kept longer than needed. |
| **Impact** | ✅ Continuity, bounded storage, token savings end to end, privacy argument. ⚠️ Agent re-queries tools for facts from earlier turns (acceptable: data may have changed anyway). |
| **Status** | Accepted |

## D07 — Map table relationships and audit the data before coding

| | |
|---|---|
| **Decided by** | **Jackson** (map the tables) + Claude (audit execution) |
| **Decision** | Before writing code, map how the tables connect and audit the data for inconsistencies. |
| **Claude's contribution** | Read every CSV and the manual end to end, drew the relationship map and listed the inconsistencies (see `docs/DATA_AUDIT.md`). |
| **Impact** | ✅ Revealed several planted traps (wrong descriptions, totals that don't add up, expired promotions, duplicated e-mails, contradictions in the manual) that drive data cleaning and the example conversations. |
| **Status** | Done |

## D08 — Typed tools instead of free-form text-to-SQL

| | |
|---|---|
| **Decided by** | Claude → Jackson |
| **Decision** | A small set of typed tools (`search_products`, `get_product_details`, `get_order_status`, `get_store_policy`, `escalate_to_human`). |
| **Alternatives** | Let the model write SQL/pandas queries. |
| **Rationale** | Typed parameters limit what the model can do (no arbitrary queries, no data dumps), are easy to unit test and remove the SQL injection surface on store data. |
| **Impact** | ✅ Safer and testable. ⚠️ Questions outside the tools' parameters need new tools. |
| **Status** | Accepted |

## D09 — All price math in Python, never in the LLM

| | |
|---|---|
| **Decided by** | Claude → Jackson |
| **Decision** | Active promotion, original price + discount %, PIX 5% discount (only when no promotion applies — rules are not cumulative) and installment limits are computed in code and returned ready by the tools. |
| **Rationale** | LLMs make arithmetic mistakes; the manual warns that wrong prices can be considered misleading advertising. |
| **Impact** | ✅ Correct, auditable prices. |
| **Status** | Accepted |

## D10 — Identity check before showing an order (LGPD)

| | |
|---|---|
| **Decided by** | Claude → Jackson |
| **Decision** | An order is only shown if the customer provides the order number **and** the e-mail or phone registered for that order's customer. |
| **Rationale** | The manual has an LGPD section; order data is personal data. Identifying by e-mail alone would be ambiguous (customers 11 and 43 share the same e-mail). |
| **Impact** | ✅ Privacy by design. ⚠️ One extra step for the customer. |
| **Status** | Accepted |

## D11 — Configurable reference date

| | |
|---|---|
| **Decided by** | Claude proposed it; **Jackson** chose the value |
| **Decision** | `REFERENCE_DATE` setting, default **2026-03-25** (the last order is from 2026-03-22). |
| **Alternatives** | Use the real current date (November 2026). |
| **Claude's contribution** | Showed that with the real date every return window is expired and orders 9–16 would be "pending" for 8 months, which makes the data incoherent. |
| **Impact** | ✅ Reproducible deadlines (7-day regret, 30-day defect exchange) and coherent scenarios. ⚠️ Must be explained in the README. |
| **Status** | Accepted |

## D12 — Working method: English deliverables, incremental co-authored commits, plan first

| | |
|---|---|
| **Decided by** | **Jackson** |
| **Decision** | Code, docs, commits and this log in English; the agent itself talks to customers in Brazilian Portuguese. Commits are small and incremental, with Claude credited as co-author (`Co-Authored-By`). Every phase is planned and approved before execution. |
| **Rationale** | The challenge explicitly asks to see the real workflow with coding assistants; co-authorship makes it visible in the history. |
| **Impact** | ✅ Transparent, honest history. |
| **Status** | Accepted |

## D13 — Security testing (injection and data-leak attacks)

| | |
|---|---|
| **Decided by** | **Jackson** |
| **Decision** | Add automated tests for SQL injection, malicious tool arguments, PII leakage and order-ID enumeration, plus a red-team script that attacks the live agent with prompt-injection attempts. |
| **Claude's contribution** | Noted that store data lives in pandas (no SQL), so SQL injection only applies to the conversation store — which still gets tested with parameterized queries. Designed the attack list and the "3 failed verifications → handoff" rule. |
| **Impact** | ✅ Demonstrates the agent resists common attacks; results documented in `docs/SECURITY.md`. |
| **Status** | Accepted |

## D14 — An unusual test question where the agent can stand out

| | |
|---|---|
| **Decided by** | **Jackson** (idea) + Claude (scenario) |
| **Decision** | Include a non-obvious scenario: *"Sou canhoto, quero começar a tocar choro e tenho uns R$1.500..."*. The agent must infer a 7-string nylon guitar, filter by budget and status, compute payment options and be honest that the catalog has no left-handed information. |
| **Impact** | ✅ Shows domain reasoning, tool composition and honesty in a single conversation. |
| **Status** | Accepted |

## D15 — Official `google-genai` SDK with a hand-written agent loop (no LangChain)

| | |
|---|---|
| **Decided by** | Claude → Jackson |
| **Decision** | Implement the function-calling loop directly with the Google SDK. |
| **Alternatives** | LangChain / LangGraph. |
| **Rationale** | Fewer dependencies, every step of the loop is visible and easy to explain; the project is small enough not to need an orchestration framework. |
| **Impact** | ✅ Transparency and control. ⚠️ Features like tracing must be built manually if needed. |
| **Status** | Accepted |

## D16 — Submission format

| | |
|---|---|
| **Decided by** | **Jackson** (following the recruiter's form) |
| **Decision** | Submit through the Google Form: a PDF generated from the README and documentation, named `Jackson Sales - AI Engineer – Full-Stack para Aplicações com IA Generativa - Vaga afirmativa para pessoas negras.pdf`, plus the public GitHub link. |
| **Impact** | A script builds the PDF from the Markdown docs, so the PDF and the repository never diverge. |
| **Status** | Accepted |
