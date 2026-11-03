# Pedido atrasado: verificação de identidade e reclamação

**O que este cenário testa:** Pedido 8 enviado com previsão 28/02/2026 e ainda não entregue em 25/03/2026. O agente pede número e contato, verifica, detecta o atraso e registra a reclamação para a equipe (retorno em 24h úteis).

*Gerado automaticamente por `scripts/run_scenarios.py` em 2026-11-02 22:05 com `gemini-3.5-flash-lite`, data de referência 25/03/2026.*

---

**Cliente:** Oi, meu pedido não chegou até hoje e já passou muito da data prevista!

**Lia:** Olá! Poxa, sinto muito por esse atraso e pelo transtorno com a entrega. 

Para que eu possa verificar o que aconteceu com o seu pedido no sistema, você poderia me informar o **número do pedido** e o seu **e-mail ou telefone cadastrado**?

**Cliente:** É o pedido 8, meu e-mail é anacarol.ferreira@coldmail.com


> 🔧 Ferramentas: `get_order_status({"email_or_phone": "anacarol.ferreira@coldmail.com", "order_id": "8"})`, `escalate_to_human({"summary": "Pedido 8 (Kala KA-C Concert Mogno) comprado em 15/02/2026 com previsão para 28/02/2026 está atrasado há 25 dias. Cliente Ana Carolina relatou o atraso.", "order_id": "8", "reason": "problema_pedido"})`

**Lia:** Ana, vejo aqui que o seu pedido realmente está com um atraso significativo na entrega e peço desculpas por isso. 

Já registrei o seu caso com a nossa equipe responsável para investigarmos o ocorrido com a transportadora com urgência. 

O seu número de protocolo é **EMP-000001**, e nossa equipe vai entrar em contato com você em **até 24 horas úteis** com uma posição.

Há mais alguma coisa em que eu possa te ajudar por enquanto?
