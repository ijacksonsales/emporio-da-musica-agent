# Pedido atrasado: verificação de identidade e reclamação

**O que este cenário testa:** Pedido 8 enviado com previsão 28/02/2026 e ainda não entregue em 25/03/2026. O agente pede número e contato, verifica, detecta o atraso e registra a reclamação para a equipe (retorno em 24h úteis).

*Gerado automaticamente por `scripts/run_scenarios.py` em 2026-11-02 22:50 com `gemini-3.5-flash-lite`, data de referência 25/03/2026.*

---

**Cliente:** Oi, meu pedido não chegou até hoje e já passou muito da data prevista!

**Lia:** Oi! Boas-vindas à Empório da Música! 🎸 Eu sou a Lia, assistente virtual da loja. Já te ajudo com a situação do seu pedido! Antes, como posso te chamar?

**Cliente:** Sou a Ana. É o pedido 8, meu e-mail é anacarol.ferreira@coldmail.com


> 🔧 Ferramentas: `get_order_status({"order_id": "8", "email_or_phone": "anacarol.ferreira@coldmail.com"})`, `escalate_to_human({"reason": "problema_pedido", "order_id": "8", "summary": "Pedido 8 atrasado há 25 dias (previsão 28/02/2026). Cliente Ana entrou em contato cobrando a entrega."})`

**Lia:** Ana, sinto muito por esse atraso com o seu pedido do ukulele Kala KA-C Concert Mogno. Verifiquei aqui que ele realmente está com atraso na entrega.

Já registrei o caso para a nossa equipe apurar o que aconteceu com a transportadora. O seu número de protocolo é **EMP-000001**, com retorno em até 24 horas úteis.

Precisa de mais alguma coisa por enquanto?
