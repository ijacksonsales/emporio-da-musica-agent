# Devolução por arrependimento fora do prazo

**O que este cenário testa:** Pedido 7 entregue (previsão) em 17/02/2026. Arrependimento vale 7 dias após o recebimento, então está fora do prazo; a garantia legal de 90 dias ainda vale para defeito de fabricação.

*Gerado automaticamente por `scripts/run_scenarios.py` em 2026-11-02 22:06 com `gemini-3.5-flash-lite`, data de referência 25/03/2026.*

---

**Cliente:** Me arrependi da minha compra, posso devolver meu pedido?


> 🔧 Ferramentas: `get_store_policy({"topic": "returns"})`

**Lia:** Pode sim! Para compras feitas pela internet, você tem o direito de arrependimento e pode solicitar a devolução em até **7 dias corridos após o recebimento** do produto, sem precisar justificar.

Para que dê tudo certo, o instrumento precisa estar na embalagem original, sem sinais de uso, acompanhado de todos os acessórios e manuais. O frete de devolução fica por nossa conta e o reembolso é feito na mesma forma de pagamento original.

Você tem o número do pedido em mãos? Se puder me passar o número junto com o seu e-mail ou telefone cadastrado, eu já localizo os dados para darmos início ao processo para você!

**Cliente:** Pedido 7, meu telefone é (67) 99789-0123


> 🔧 Ferramentas: `get_store_policy({"topic": "returns"})`, `get_order_status({"email_or_phone": "(67) 99789-0123", "order_id": "7"})`

**Lia:** Letícia, verifiquei aqui os dados do seu pedido (número 7, do ukulele Shelby SU-21S). 

Como ele foi entregue em 17/02/2026, o prazo de 7 dias corridos para devolução por arrependimento (que era até 24/02/2026) acabou expirando. 

Se o motivo for algum problema ou defeito no instrumento, me avisa para verificarmos as opções de garantia, tá bom? Como a loja está fechada agora (nossos atendentes voltam amanhã às 09:00), caso prefira, posso registrar o seu caso para a nossa equipe humana entrar em contato e analisar se há alguma exceção que possamos abrir para você. Quer que eu abra esse chamado?

**Cliente:** E se o ukulele apresentar algum defeito?


> 🔧 Ferramentas: `get_store_policy({"topic": "warranty"})`

**Lia:** Se o ukulele apresentar algum defeito de fabricação, você conta com a garantia legal de 90 dias a partir da data de recebimento do produto. A maioria dos fabricantes também oferece uma garantia própria estendida (que costuma variar de 6 meses a 2 anos, conforme o certificado que acompanha o instrumento).

A garantia cobre eventuais defeitos de fabricação, mas vale lembrar que ela não abrange desgaste natural (como trastes ou cordas), danos por mau uso, quedas ou exposição a condições extremas, tá?

Se você notar qualquer probleminha com o seu ukulele, é só nos avisar! Como a loja já está fechada hoje, nossa equipe volta amanhã às 09:00 e pode te orientar certinho sobre como proceder com a assistência. Precisa de mais alguma informação por enquanto?
