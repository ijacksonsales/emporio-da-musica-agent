# Devolução por arrependimento fora do prazo

**O que este cenário testa:** Pedido 7 entregue (previsão) em 17/02/2026. Arrependimento vale 7 dias após o recebimento, então está fora do prazo; a garantia legal de 90 dias ainda vale para defeito de fabricação.

*Gerado automaticamente por `scripts/run_scenarios.py` em 2026-11-02 22:13 com `gemini-3.5-flash-lite`, data de referência 25/03/2026.*

---

**Cliente:** Me arrependi da minha compra, posso devolver meu pedido?


> 🔧 Ferramentas: `get_store_policy({"topic": "returns"})`

**Lia:** Com certeza! Conforme o Código de Defesa do Consumidor, você tem até **7 dias corridos após o recebimento** do pedido para solicitar a devolução por arrependimento. 

Para que tudo ocorra bem, o instrumento precisa estar na embalagem original, sem sinais de uso, acompanhado de todos os acessórios e manuais. Ah, e o frete de devolução fica por nossa conta, e o reembolso é feito na mesma forma de pagamento em até 10 dias úteis após o recebimento de volta aqui na loja.

Para darmos início ao processo, você pode me informar o **número do seu pedido** junto com o seu **e-mail ou telefone cadastrado**? Assim consigo verificar os prazos direitinho para você!

**Cliente:** Pedido 7, meu telefone é (67) 99789-0123


> 🔧 Ferramentas: `get_order_status({"order_id": "7", "email_or_phone": "(67) 99789-0123"})`, `get_store_policy({"topic": "returns"})`

**Lia:** Oi, Letícia! Verifiquei os dados do seu pedido (número 7, do ukulele Shelby SU-21S).

O prazo legal de 7 dias corridos após o recebimento para a devolução por arrependimento era até o dia 24/02/2026, pois o pedido foi entregue em 17/02/2026. Como esse prazo já passou, infelizmente não consigo seguir com a devolução por arrependimento direto pelo sistema.

Se você estiver enfrentando algum problema com o instrumento (como defeito de fabricação), me avisa que posso te orientar sobre a garantia ou registrar o caso com a nossa equipe, tá bom? Precisa de mais alguma ajuda?

**Cliente:** E se o ukulele apresentar algum defeito?


> 🔧 Ferramentas: `get_store_policy({"topic": "warranty"})`

**Lia:** Se o ukulele apresentar algum defeito de fabricação, não se preocupe! 

Todos os nossos instrumentos contam com a **garantia legal de 90 dias** a partir da data de recebimento, além da garantia do fabricante (que costuma variar de 6 meses a 2 anos, conforme o certificado que acompanha o produto). 

A garantia cobre eventuais defeitos de fabricação, mas vale lembrar que ela não se aplica a desgaste natural (como cordas e trastes), danos por mau uso, quedas ou modificações por terceiros, tá bom?

Se você notar qualquer probleminha com o instrumento, é só me avisar por aqui que eu posso te orientar e registrar o caso com a nossa equipe para verificarmos o reparo ou troca! Precisa de mais alguma ajuda?
