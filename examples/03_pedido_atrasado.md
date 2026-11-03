# Pedido atrasado: verificação de identidade e reclamação

**O que este cenário testa:** Pedido 8 enviado com previsão 28/02/2026 e ainda não entregue em 25/03/2026. O agente pede número e contato, verifica, detecta o atraso e registra a reclamação para a equipe (retorno em 24h úteis).

*Gerado automaticamente por `scripts/run_scenarios.py` em 2026-11-02 22:12 com `gemini-3.5-flash-lite`, data de referência 25/03/2026.*

---

**Cliente:** Oi, meu pedido não chegou até hoje e já passou muito da data prevista!

**Lia:** Olá! Poxa, sinto muito por esse atraso e pelo transtorno. Quero te ajudar a verificar o que aconteceu com a entrega. 

Para eu consultar o status do seu pedido, por favor, me informe o **número do pedido** e o seu **e-mail ou telefone cadastrado**.

**Cliente:** É o pedido 8, meu e-mail é anacarol.ferreira@coldmail.com


> 🔧 Ferramentas: `get_order_status({"order_id": "8", "email_or_phone": "anacarol.ferreira@coldmail.com"})`, `escalate_to_human({"summary": "Pedido 8 de Ana (Kala KA-C Concert Mogno) está com 25 dias de atraso na entrega (previsão era 28/02/2026). Cliente entrou em contato reclamando da demora.", "reason": "problema_pedido", "order_id": "8"})`

**Lia:** Ana, verifiquei aqui que o seu pedido número 8 (com o ukulele Kala KA-C Concert Mogno) realmente consta como atrasado desde o final de fevereiro. Peço desculpas sinceras por esse transtorno!

Já registrei o seu caso com a nossa equipe para verificarmos o que aconteceu com a transportadora. O seu número de protocolo é **EMP-000001**, e retornaremos com uma posição em **até 24 horas úteis**. 

Se precisar de mais alguma coisa enquanto isso, é só me chamar!
