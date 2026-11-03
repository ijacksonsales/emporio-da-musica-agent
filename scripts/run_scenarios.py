"""Run the example conversations against the live agent and save them to examples/.

Framing (titles, goals, what to look for) is in English; the conversation itself is in
Brazilian Portuguese, the language the agent uses with customers. Each customer message
carries an English gloss so reviewers can follow without reading Portuguese.

Usage: python scripts/run_scenarios.py [scenario_id ...]
"""

from __future__ import annotations

import sys
from datetime import datetime

from _common import ROOT, fresh_runtime, run_conversation, transcript

SCENARIOS = [
    {
        "id": "01_choro_canhoto",
        "title": "Non-obvious recommendation: a left-handed beginner who wants to play choro",
        "goal": (
            "An unusual question. The agent must infer that choro calls for a 7-string nylon "
            "guitar, filter by budget and status (product 113 is discontinued), compute PIX and "
            "installments, and admit that the catalog has no left-handed information. Opening: "
            "the customer does not introduce himself, so Lia welcomes him and asks his name first."
        ),
        "look_for": [
            "Lia asks for the name before answering, then recommends only real catalog products.",
            "Giannini GWNE-7 (R$ 1,149) and Rozini RV-174 (R$ 1,299) are the two 7-string nylon guitars within budget.",
            "PIX = list price − 5%; installments follow the tiered minimums (11x for R$ 1,149, because 12x would be below R$ 100).",
            "No claim that left-handed models are out of stock: the catalog simply doesn't say.",
        ],
        "messages": [
            ("Oi! Sou canhoto e quero começar a tocar choro. Tenho uns R$ 1.500, qual violão você me indica? Dá pra parcelar?",
             "Hi! I'm left-handed and want to start playing choro. I have about R$ 1,500, which guitar do you recommend? Can I pay in installments?"),
            ("Me chamo Rafael.", "My name is Rafael."),
            ("Legal! E se eu pagar no PIX, quanto fica o mais em conta?",
             "Nice! And if I pay with PIX, how much is the cheapest one?"),
        ],
    },
    {
        "id": "02_promocao_ativa_e_vencida",
        "title": "Active promotion, non-cumulative PIX discount and an expired promotion",
        "goal": (
            "Product 90 has an active 18% promotion: show original price, % and final price, "
            "without adding the PIX discount on top. Product 93 had an Easter promotion that is "
            "no longer active: the agent must not promise it. Opening: the customer introduces "
            "herself, so Lia answers right away."
        ),
        "look_for": [
            "R$ 2,399 → R$ 1,967.18 with 18% off; PIX price equals the promotional price (not cumulative).",
            "The expired Easter discount is refused transparently and the current price is shown.",
        ],
        "messages": [
            ("Boa tarde! Aqui é a Marina. Quanto tá o violão Crafter HT-100? Se eu pagar no PIX ganho mais desconto?",
             "Good afternoon! This is Marina. How much is the Crafter HT-100 guitar? Do I get an extra discount with PIX?"),
            ("E o Martin D-28? Vi um anúncio de Páscoa com 15% off nele.",
             "And the Martin D-28? I saw an Easter ad with 15% off on it."),
        ],
    },
    {
        "id": "03_pedido_atrasado",
        "title": "Delayed order: identity verification and complaint handoff",
        "goal": (
            "Order 8 was shipped with an estimated delivery of 2026-02-28 and has not arrived by "
            "the reference date (2026-03-25). The agent asks for the order number and contact, "
            "verifies them, detects the delay and registers a complaint for the team "
            "(reply within 24 business hours, manual §7.3)."
        ),
        "look_for": [
            "The order is only looked up after the customer gives order number + registered e-mail.",
            "The 25-day delay is detected by the tool, not guessed.",
            "A real handoff is registered and the protocol number is given to the customer.",
        ],
        "messages": [
            ("Oi, meu pedido não chegou até hoje e já passou muito da data prevista!",
             "Hi, my order still hasn't arrived and it's way past the expected date!"),
            ("Sou a Ana. É o pedido 8, meu e-mail é anacarol.ferreira@coldmail.com",
             "I'm Ana. It's order 8, my e-mail is anacarol.ferreira@coldmail.com"),
        ],
    },
    {
        "id": "04_arrependimento_fora_do_prazo",
        "title": "Return request outside the 7-day regret window",
        "goal": (
            "Order 7 was delivered (estimated) on 2026-02-17. The regret right lasts 7 days from "
            "receipt, so it has expired; the 30-day defect exchange has also expired, but the "
            "90-day legal warranty is still valid. Opening: the customer prefers not to give her "
            "name, and Lia continues without insisting."
        ),
        "look_for": [
            "Lia respects the customer's choice and never uses a name (the tool doesn't return one, D22).",
            "Deadlines come from the order data (regret window closed on 2026-02-24).",
            "For defects, the agent points to the 90-day legal warranty from receipt, which is still valid (until 2026-05-18).",
        ],
        "messages": [
            ("Me arrependi da minha compra, posso devolver meu pedido?",
             "I regret my purchase, can I return my order?"),
            ("Prefiro não dizer meu nome. É o pedido 7, meu telefone é (67) 99789-0123",
             "I'd rather not give my name. It's order 7, my phone is (67) 99789-0123"),
            ("E se o ukulele apresentar algum defeito?", "And what if the ukulele has a defect?"),
        ],
    },
    {
        "id": "05_fora_do_escopo",
        "title": "Out of scope: accessories, an empty category and store information",
        "goal": (
            "The store does not sell accessories and has no wind instruments in the catalog. The "
            "agent redirects politely, checks the catalog before saying there are no saxophones, "
            "and answers address and hours from the policy tool."
        ),
        "look_for": [
            "Accessories (strings, amplifier) are declined per manual §1/§7.1, suggesting an accessories store.",
            "The empty category is confirmed with a catalog search, not assumed.",
            "The address comes from get_store_policy; Saturday hours (09:00–13:00) are part of the system prompt, so no tool is required for them.",
        ],
        "messages": [
            ("Olá, sou o Diego! Vocês vendem encordoamento e amplificador pra guitarra?",
             "Hi, I'm Diego! Do you sell guitar strings and amplifiers?"),
            ("Entendi. E saxofone alto, vocês têm?", "Got it. And do you have an alto saxophone?"),
            ("Beleza. Qual o endereço da loja e até que horas abre no sábado?",
             "OK. What's the store address and until what time is it open on Saturday?"),
        ],
    },
]


def main(selected: list[str]) -> None:
    runtime = fresh_runtime("scenarios.sqlite3")
    out_dir = ROOT / "examples"
    out_dir.mkdir(exist_ok=True)
    for scenario in SCENARIOS:
        if selected and scenario["id"] not in selected:
            continue
        print(f"Running {scenario['id']}...")
        messages = [pt for pt, _ in scenario["messages"]]
        glosses = [en for _, en in scenario["messages"]]
        turns = run_conversation(runtime, messages)
        look_for = "\n".join(f"- {item}" for item in scenario["look_for"])
        content = (
            f"# {scenario['title']}\n\n"
            f"**What this scenario tests:** {scenario['goal']}\n\n"
            f"**What to look for:**\n\n{look_for}\n\n"
            f"*Generated by `scripts/run_scenarios.py` on {datetime.now():%Y-%m-%d %H:%M} with "
            f"`{runtime.settings.llm_model}` (reference date {runtime.settings.reference_date}). "
            "Real, unedited output, reviewed by hand. The conversation is in Brazilian Portuguese, "
            "the language the agent speaks with customers; customer messages include an English "
            "gloss.*\n\n---\n\n"
            f"{transcript(turns, glosses)}"
        )
        (out_dir / f"{scenario['id']}.md").write_text(content, encoding="utf-8", newline="\n")
    print("Done.")


if __name__ == "__main__":
    main(sys.argv[1:])
