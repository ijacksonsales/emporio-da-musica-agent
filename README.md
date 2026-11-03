# Empório da Música — Customer Service Agent

Prototype of a text-message customer service agent for **Empório da Música**, a fictional musical
instrument store in Campo Grande/MS. Built for the Artefact AI Engineer technical challenge.

The agent, **Lia**, talks to customers in Brazilian Portuguese and answers questions about
products, prices, stock, promotions, orders and store policies. It decides on its own when to
query the store data and when to read the policy manual, handles out-of-scope requests and
hands complex cases to the human team.

| | |
|---|---|
| **Approach** | Hybrid: typed function calling over the CSV data + on-demand policy retrieval by topic |
| **Model** | Google Gemini `gemini-3.5-flash-lite` (free tier) via the official `google-genai` SDK, behind a provider interface |
| **Interface** | Streamlit chat UI with streaming replies |
| **Memory** | SQLite, 7-day retention, only user/assistant text |
| **Tests** | 104 deterministic tests (pricing, tools, identity checks, grounding guard, memory, security) + live scenario and red-team scripts |

**Documentation**

| Document | Content |
|---|---|
| [`docs/DECISION_LOG.md`](docs/DECISION_LOG.md) | Every decision: who made it, how the AI assistant contributed, alternatives and impact |
| [`docs/DATA_AUDIT.md`](docs/DATA_AUDIT.md) | Table relationships and every inconsistency found in the data and the manual |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Request flow, modules and tools |
| [`docs/SECURITY.md`](docs/SECURITY.md) | Attack surface, controls and tests |
| [`docs/RED_TEAM_RESULTS.md`](docs/RED_TEAM_RESULTS.md) | Live attacks against the agent and its answers |
| [`examples/`](examples/) | Five real conversations with the agent |

---

## 1. How to run

### Requirements

- Python 3.11+
- A Gemini API key (free): <https://aistudio.google.com/apikey>

### Setup

```bash
git clone <this repository>
cd <repository folder>

python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -e ".[dev]"

cp .env.example .env        # Windows: copy .env.example .env
# edit .env and set GEMINI_API_KEY
```

### Configuration (`.env`)

| Variable | Default | Meaning |
|---|---|---|
| `GEMINI_API_KEY` | — | Your Gemini API key (required) |
| `LLM_PROVIDER` | `gemini` | Provider implementation |
| `LLM_MODEL` | `gemini-3.5-flash-lite` | Any Gemini model with function calling |
| `REFERENCE_DATE` | `2026-03-25` | The agent's "today" (see [Assumptions](#5-assumptions)) |
| `HISTORY_TTL_DAYS` | `7` | Conversation retention |
| `DB_PATH` | `var/conversations.sqlite3` | SQLite file for history and handoffs |

### Commands

```bash
streamlit run app/streamlit_app.py    # chat UI at http://localhost:8501
pytest                                # deterministic tests, no API calls
python scripts/run_scenarios.py       # regenerate examples/ with the live model
python scripts/red_team.py            # attack the live agent, writes docs/RED_TEAM_RESULTS.md
python scripts/build_pdf.py           # build the submission PDF from the docs
```

In the UI, the sidebar toggle **"Mostrar ferramentas usadas"** shows which tools the agent called
and what they returned. The session id lives in the URL (`?session=...`): reopening the same URL
within 7 days continues the conversation.

---

## 2. Technical decisions

The full reasoning, including alternatives and impact, is in the
[Decision Log](docs/DECISION_LOG.md). Summary:

### Agent approach: hybrid (D01, D08, D15)

The store has two very different kinds of knowledge:

- **Structured, exact data** (prices, stock, orders, promotions): exposed through **typed tools**
  (`search_products`, `get_product_details`, `get_order_status`). Typed parameters limit what the
  model can do, are easy to test and remove any SQL surface over store data. A free-form SQL agent
  could return "almost right" rows or dump data.
- **Prose policies** (the manual): served on demand by `get_store_policy(topic)`.
- **Actions**: `escalate_to_human` registers complaints with a protocol number (manual §7.3).

The function-calling loop is written by hand on top of the Google SDK (no LangChain): the project
is small, every step is visible and the provider interface keeps it swappable.

### Retrieval: policy by topic, no vector store (D02, D03, D17)

The manual is ~8 pages. Instead of loading it into every prompt, it is split into 8 topic
sections returned only when needed, so **token cost is proportional to the question, not to the
manual**. A vector store would be more a point of failure than a solution at this size: a fixed
topic enum is deterministic and testable. The sections were transcribed once and reviewed against
the PDF, because automatic extraction broke words and tables apart.

The risk of this choice is the model answering from general knowledge without calling the tool.
It is mitigated by an explicit rule in the prompt ("never answer about hours, payment, returns...
without `get_store_policy`") and verified in the example runs.

### LLM: Gemini 3.5 Flash-Lite (D04)

Free tier (500 requests/day, 15/minute on my project), so anyone can run it at no cost, with good
native function calling. The provider layer (`llm/base.py`) means another model only needs one new
module.

### Prompt strategy (D18, D19, D21)

**Behavior in the prompt, knowledge through tools.** The system prompt (English, replies in
Portuguese) only holds what applies to every message: persona and tone (manual §7.1), grounding
rules, recommendation guidelines, scope, LGPD rules, handoff and security. The reference date and
current time are injected each turn so the agent knows whether the store is open.

**Opening (D21).** On the first message Lia welcomes the customer and asks their name before
answering (unless they already said it; if they decline, she moves on). The code tells the prompt
when the history is empty, and the instruction sits at the end of the prompt with a fixed,
gender-neutral template: small models follow the most recent, most concrete instruction best.

The prompt was **iterated against real runs** (D19, D21): live runs exposed generic
recommendations, a false "out of stock" claim, a promised handoff never registered, a gendered
greeting and a "só um instante" that never came back. Each was fixed and re-verified.

### Price math and grounding in code (D09, D23, D24)

Promotions, the non-cumulative PIX discount and the tiered installment minimums are computed with
`Decimal` in `pricing.py` and returned ready to the model. LLMs make arithmetic mistakes, and the
manual itself warns that wrong prices can be misleading advertising.

Prompt rules were not enough: in one run the model **invented two products with prices** without
calling any tool. So a **grounding guard** now runs in code: text produced before any data tool in
a turn is held back; if it quotes a price, or promises to check something and stops, it is never
shown — the model is told to use the tools, and if it insists the customer gets a fallback message.
Text after a data tool streams live.

### Streaming UI (D20)

Replies stream from Gemini through the agent loop to the UI (`st.write_stream`), paced word by
word. The non-streaming API just consumes the same stream, and the stored reply is exactly the
text the customer saw.

### Data treatment (D07, `docs/DATA_AUDIT.md`)

The data was audited before writing code. It contains planted inconsistencies, each handled
explicitly, for example:

- Products 135–144 have descriptions of different instruments (e.g. "Music Man Bass 1X"
  described as a Fender Jazz Bass). The loader detects this automatically (brand and string/key
  count checks) and hides those descriptions: name + specs are the source of truth.
- Orders 3 and 20 have totals that don't match their items: flagged; the agent escalates if the
  customer questions the amount.
- Discontinued / coming-soon / zero-stock products are never offered; alternatives are suggested.
- Only `is_active = 1` promotions exist for the agent; expired ones are never promised.
- Customers 11 and 43 share an e-mail, so orders are verified against the customer of that order,
  never by e-mail alone.
- The manual contradicts itself (two phone numbers, accented e-mail, installment minimums);
  the resolution of each conflict is documented.

### Conversation memory (D06)

SQLite keyed by session id, 7-day TTL from the last activity. Only user and assistant text is
stored; raw tool results are discarded, which keeps the history sent to the model small
(otherwise the token savings of D02 would disappear after a few turns) and avoids keeping order
data. The TTL doubles as data minimization (LGPD).

### Security (D10, D13, `docs/SECURITY.md`)

Order lookups need the order number **and** the e-mail/phone of that order's customer; failures
look identical whether the order exists or not; 3 failures — or a security escalation by the
agent — lock lookups for the conversation. Tools never return personal data, not even the
customer's name (D22). SQLite queries are parameterized. Tests attack all of this with SQL
injection payloads, path traversal and enumeration, and the red-team script attacks the live model
(8/8 checks passed, every transcript reviewed by hand; two earlier runs found real gaps, fixed in
D24).

---

## 3. Example conversations

Generated with the real model by `scripts/run_scenarios.py` and reviewed by hand (not edited):

| File | Scenario | What it shows |
|---|---|---|
| [`01_choro_canhoto.md`](examples/01_choro_canhoto.md) | Left-handed beginner wants to play choro with R$ 1,500 | Name asked first; domain reasoning (choro → 7-string nylon), budget filter, PIX/installments, honesty about missing data |
| [`02_promocao_ativa_e_vencida.md`](examples/02_promocao_ativa_e_vencida.md) | Price of a product on sale, then an expired Easter discount | Customer introduces herself (answered right away); original price + % + final price, PIX not cumulative, refusing an expired promotion |
| [`03_pedido_atrasado.md`](examples/03_pedido_atrasado.md) | "My order hasn't arrived" | Identity check, delay detection, complaint registered with protocol |
| [`04_arrependimento_fora_do_prazo.md`](examples/04_arrependimento_fora_do_prazo.md) | "I regret my purchase, can I return it?" | Customer declines to give a name (respected); order dates + return policy; regret window expired, warranty still valid |
| [`05_fora_do_escopo.md`](examples/05_fora_do_escopo.md) | Strings and amplifier, then a saxophone, then address/hours | Accessories redirected, empty category, store info from policy |

---

## 4. Project structure

```
├── app/streamlit_app.py           # chat UI
├── data/raw/                      # original challenge data (CSV names without the sheet prefix)
├── docs/                          # decision log, data audit, architecture, security, red team
├── examples/                      # example conversations
├── scripts/                       # scenario runner, red team, PDF builder
├── src/emporio_agent/
│   ├── agent.py                   # function-calling loop
│   ├── config.py                  # settings
│   ├── data/loader.py             # CSV loading + data-quality flags
│   ├── llm/                       # provider interface + Gemini
│   ├── memory.py                  # SQLite history with TTL
│   ├── policies/sections/*.md     # policy manual by topic
│   ├── pricing.py                 # promotion / PIX / installments
│   ├── prompts/system_prompt.md
│   ├── runtime.py                 # wiring
│   └── tools/                     # catalog, orders, policies, handoff, registry
└── tests/                         # 104 tests
```

---

## 5. Assumptions

The challenge asks to assume reasonable interpretations and document them:

| Assumption | Why |
|---|---|
| "Today" is **2026-03-25** (configurable) | The data ends on 2026-03-22. With the real date (Nov/2026) every return window would be expired and pending orders would be 8 months old. |
| Receipt date = `estimated_delivery` for delivered orders | There is no actual delivery date; needed for the 7-day regret and 90-day warranty windows. |
| All orders are online purchases | The regret right applies to online purchases, and orders have no channel field. |
| Installment minimums follow manual §3.1 (≤3x R$50, 4–6x R$80, 7–12x R$100) | More specific than the summary table, which says R$100 for everything. |
| Store phone (67) 3341-4444, WhatsApp (67) 3321-4500, e-mail without accent | Each number is what its section states; accented domains are error-prone. |
| Price filters use the final price (promotion applied) | That is what the customer pays. |
| Customer data in the CSV is the registered contact used for verification | No other identity source exists. |

---

## 6. Known limitations and what I would do with more time

| Limitation | With more time |
|---|---|
| Free-tier quota (15 requests/minute) can interrupt bursts of use; the client retries with backoff | Paid tier or a fallback model through the provider layer |
| LLM behavior varies between runs; examples and red team are evidence, not guarantees. `gemini-3.5-flash-lite` is cheap but follows long prompts less reliably | An automated evaluation suite (LLM-as-judge + assertions on tool calls) in CI, run on every prompt change; compare against a larger model |
| The grounding guard only catches prices and unkept promises; an invented product name *without* a price, or a policy answered from memory, would pass | Check product names in the reply against the catalog; require a policy tool call when policy keywords appear |
| Failed-verification counter is in memory (resets on restart) | Persist it in SQLite/Redis with expiry |
| Handoffs are only stored in SQLite | Integrate with the team's helpdesk/WhatsApp Business inbox |
| Policy sections were transcribed by hand | Ingestion pipeline with review step when the manual changes; embeddings only if the manual grows a lot |
| Freight cost for other cities is not calculated (needs ZIP code, weight, size) | Integrate the Correios/Jadlog quote APIs |
| Catalog has no left-handed / variant information | Add product variants to the data model |
| No real customer authentication; anyone with order number + contact sees the order | One-time code sent to the registered phone/e-mail |
| Streamlit is a demo channel | WhatsApp Business API webhook using the same `Runtime.chat` |
| No observability beyond the tool panel | Structured logs/traces of each turn (tool calls, latency, tokens) |

---

## 7. Use of AI coding assistants

I used **Claude** (Anthropic) throughout the project, in two ways:

1. **Claude.ai chat**, before writing code: reading the challenge rules, auditing the data and
   discussing the architecture.
2. **Claude Code** (CLI agent), during implementation: it wrote code, tests and docs in my local
   repository under my direction, ran the tests and the live scripts, and made the commits.

### My workflow

- **Plan before acting.** Nothing was executed before a written plan (structure, tools, commits,
  security tests, scenarios) was reviewed and approved by me.
- **Decisions are mine; the assistant proposes and challenges.** The [Decision Log](docs/DECISION_LOG.md)
  records, for each decision, whether it came from me or was a suggestion I accepted, and what the
  assistant contributed. Examples:
  - *Mine:* hybrid approach confirmed, Gemini, simple UI, 7-day memory, mapping the tables first,
    serving the policy through a tool instead of the system prompt (to save tokens), adding
    security tests, adding an unusual test question, the model choice after checking my quotas,
    English deliverables and co-authored commits. After testing the UI myself I also asked for
    streaming replies, found the broken "R$" rendering, and required the agent to welcome
    customers and ask their name before answering.
  - *Suggested by Claude and accepted by me:* typed tools instead of text-to-SQL, price math in
    code, identity verification, no vector store, configurable reference date, hand-written agent
    loop.
  - *Refined by Claude after my decision:* when I chose the policy tool to save tokens, it pointed
    out that tool schemas also cost tokens, that the new risk was the model skipping the tool, and
    that storing tool results in the history would cancel the savings — which shaped the prompt
    rules and the memory design.
- **Incremental, honest history.** Each step was committed separately with Claude as
  `Co-Authored-By`, so the history shows the real order of work, including fixes.
- **Verification over trust.** Tests caught two of the assistant's own mistakes (the catalog has
  65 products, not 64; "Kalani" was matched as the brand "Kala"). Every live run was reviewed by
  hand, and that review — not the automatic checks — found the most important problems: generic
  recommendations, a promised handoff never registered, a gendered greeting, a customer called by
  a name they had declined to give, and invented products with prices. The last two led to fixes
  in code (D22, D23) rather than more prompt text. All transcripts in the repository are real,
  unedited outputs.

---

## Author

Jackson Sales — AI Engineer candidate, Artefact (2026).
