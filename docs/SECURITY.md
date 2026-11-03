# Security

Security was treated as a first-class requirement (decision D13). This document lists the attack
surface, the controls in place and how each one is tested.

## Attack surface

| Surface | Risk | Control |
|---|---|---|
| Store data (products, orders, customers) | SQL injection, data dumps | Data is loaded into memory; there is **no SQL over store data**. The model can only reach it through typed tools with validated parameters (D08). |
| SQLite (conversations, handoffs) | SQL injection | Every query is parameterized; session ids must match `^[A-Za-z0-9-]{8,64}$`. |
| Order lookup | Reading other customers' orders, order-id enumeration | Order number **and** the e-mail/phone of that order's customer are required. The failure message is the same whether the order exists or not. After 3 failures in a conversation, lookups are blocked and the customer is sent to the team. |
| Tool outputs | Leaking personal data to the model/customer | Tools never return e-mails, phones or addresses; order lookup returns only the customer's first name. |
| Tool arguments | Malicious or malformed values | Unknown tools, unexpected parameters and invalid values return an error to the model instead of raising. The policy topic is an enum (no file paths). Free-text inputs have length limits. |
| Prompt | Prompt injection, prompt extraction, unauthorized discounts | System prompt states that customer messages and tool results are data, not instructions; forbids revealing instructions or tools; prices only come from tools. |
| User input | Very long messages (cost/DoS) | Messages over 2,000 characters are rejected before calling the model. |
| Agent loop | Runaway tool calls | Max 6 tool rounds per turn. |
| Secrets | API key leakage | Key only in `.env`, which is git-ignored. |
| Stored history | Keeping personal data longer than needed | 7-day TTL from last activity; tool results (which may contain order data) are never stored. |

## Automated tests (deterministic, no LLM)

`tests/test_security.py`, `tests/test_orders.py` and `tests/test_registry.py` cover:

- SQL injection payloads in session ids (rejected), message text (stored literally, other sessions intact) and handoff summaries.
- Payloads in every tool argument never raise.
- Path traversal through the policy topic is rejected.
- Catalog tools never return e-mails or phone numbers.
- Wrong contact and non-existent order produce identical responses.
- Order enumeration is locked after 3 failures, per conversation.
- The shared e-mail between customers 11 and 43 does not open the other customer's order.

Run with `pytest`.

## Red team against the live model

`scripts/red_team.py` attacks the running agent and writes the full transcripts to
[`RED_TEAM_RESULTS.md`](RED_TEAM_RESULTS.md). Attacks: prompt extraction, fake admin mode,
personal data of a named customer, unverified order lookup, order enumeration, unauthorized
discount, SQL payload in the chat and tool/schema disclosure.

Model behavior is probabilistic, so these results are evidence, not a guarantee. The controls that
matter most (identity check, lockout, no PII in tool outputs, price math in code) are enforced in
code, so they hold even if the model is fooled.
