"""Run the example conversations against the live agent and save them to examples/.

Usage: python scripts/run_scenarios.py [scenario_id ...]
"""

from __future__ import annotations

import sys
from datetime import datetime

from _common import ROOT, fresh_runtime, run_conversation, transcript

SCENARIOS = [
    {
        "id": "01_choro_canhoto",
        "title": "Recomendação não óbvia: violão para choro, canhoto, com orçamento",
        "goal": (
            "Pergunta incomum. O agente precisa inferir que choro pede violão de 7 cordas de "
            "nylon, filtrar por orçamento e situação (o 113 é descontinuado), calcular PIX e "
            "parcelas, e admitir que o catálogo não informa versão para canhoto. Abertura: o "
            "cliente não se apresenta, então a Lia dá boas-vindas e pergunta o nome antes."
        ),
        "messages": [
            "Oi! Sou canhoto e quero começar a tocar choro. Tenho uns R$ 1.500, qual violão você me indica? Dá pra parcelar?",
            "Me chamo Rafael.",
            "Legal! E se eu pagar no PIX, quanto fica o mais em conta?",
        ],
    },
    {
        "id": "02_promocao_ativa_e_vencida",
        "title": "Preço com promoção ativa, PIX não cumulativo e promoção vencida",
        "goal": (
            "Produto 90 tem 18% ativo: mostrar preço original, % e final, sem somar o PIX. "
            "Produto 93 teve promoção de Páscoa, hoje inativa: não prometer o desconto. "
            "Abertura: a cliente já se apresenta, então a Lia responde direto."
        ),
        "messages": [
            "Boa tarde! Aqui é a Marina. Quanto tá o violão Crafter HT-100? Se eu pagar no PIX ganho mais desconto?",
            "E o Martin D-28? Vi um anúncio de Páscoa com 15% off nele.",
        ],
    },
    {
        "id": "03_pedido_atrasado",
        "title": "Pedido atrasado: verificação de identidade e reclamação",
        "goal": (
            "Pedido 8 enviado com previsão 28/02/2026 e ainda não entregue em 25/03/2026. "
            "O agente pede número e contato, verifica, detecta o atraso e registra a "
            "reclamação para a equipe (retorno em 24h úteis)."
        ),
        "messages": [
            "Oi, meu pedido não chegou até hoje e já passou muito da data prevista!",
            "Sou a Ana. É o pedido 8, meu e-mail é anacarol.ferreira@coldmail.com",
        ],
    },
    {
        "id": "04_arrependimento_fora_do_prazo",
        "title": "Devolução por arrependimento fora do prazo",
        "goal": (
            "Pedido 7 entregue (previsão) em 17/02/2026. Arrependimento vale 7 dias após o "
            "recebimento, então está fora do prazo; a garantia legal de 90 dias ainda vale "
            "para defeito de fabricação. Abertura: a cliente prefere não dizer o nome e a Lia "
            "segue sem insistir."
        ),
        "messages": [
            "Me arrependi da minha compra, posso devolver meu pedido?",
            "Prefiro não dizer meu nome. É o pedido 7, meu telefone é (67) 99789-0123",
            "E se o ukulele apresentar algum defeito?",
        ],
    },
    {
        "id": "05_fora_do_escopo",
        "title": "Fora do escopo: acessórios, categoria vazia e informações da loja",
        "goal": (
            "A loja não vende acessórios e não tem instrumentos de sopro no catálogo. O agente "
            "redireciona com educação e depois responde endereço e horário via política."
        ),
        "messages": [
            "Olá, sou o Diego! Vocês vendem encordoamento e amplificador pra guitarra?",
            "Entendi. E saxofone alto, vocês têm?",
            "Beleza. Qual o endereço da loja e até que horas abre no sábado?",
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
        turns = run_conversation(runtime, scenario["messages"])
        content = (
            f"# {scenario['title']}\n\n"
            f"**O que este cenário testa:** {scenario['goal']}\n\n"
            f"*Gerado automaticamente por `scripts/run_scenarios.py` em "
            f"{datetime.now():%Y-%m-%d %H:%M} com `{runtime.settings.llm_model}`, "
            f"data de referência {runtime.settings.reference_date:%d/%m/%Y}.*\n\n---\n\n"
            f"{transcript(turns)}"
        )
        (out_dir / f"{scenario['id']}.md").write_text(content, encoding="utf-8", newline="\n")
    print("Done.")


if __name__ == "__main__":
    main(sys.argv[1:])
