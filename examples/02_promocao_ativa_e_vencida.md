# Preço com promoção ativa, PIX não cumulativo e promoção vencida

**O que este cenário testa:** Produto 90 tem 18% ativo: mostrar preço original, % e final, sem somar o PIX. Produto 93 teve promoção de Páscoa, hoje inativa: não prometer o desconto. Abertura: a cliente já se apresenta, então a Lia responde direto.

*Gerado automaticamente por `scripts/run_scenarios.py` em 2026-11-02 22:50 com `gemini-3.5-flash-lite`, data de referência 25/03/2026.*

---

**Cliente:** Boa tarde! Aqui é a Marina. Quanto tá o violão Crafter HT-100? Se eu pagar no PIX ganho mais desconto?


> 🔧 Ferramentas: `get_product_details({"product": "Crafter HT-100"})`, `get_store_policy({"topic": "payment"})`

**Lia:** Oi, Marina! Boas-vindas à Empório da Música! Eu sou a Lia. 

O violão Crafter HT-100 Folk Aço Natural está com uma promoção ativa de 18% de desconto! Ele sai de R$ 2.399,00 por **R$ 1.967,18**, valor que você também pode parcelar em até 12x sem juros de R$ 163,93 no cartão de crédito.

Sobre o pagamento no PIX, como ele já está com o preço promocional, o desconto adicional de PIX não é cumulativo, ou seja, o valor no PIX é o mesmo R$ 1.967,18 da promoção. 

Temos 3 unidades dele disponíveis em estoque por aqui. Posso te ajudar com mais alguma coisa, Marina?

**Cliente:** E o Martin D-28? Vi um anúncio de Páscoa com 15% off nele.


> 🔧 Ferramentas: `get_product_details({"product": "Martin D-28"})`, `get_store_policy({"topic": "promotions"})`

**Lia:** Marina, entendo perfeitamente a dúvida sobre o anúncio, mas o Martin D-28 está com o preço de tabela normal por aqui, custando R$ 11.499,00 (que você pode parcelar em até 12x sem juros de R$ 958,25 ou por R$ 10.924,05 no PIX). 

Nossas campanhas e descontos promocionais seguem rigorosamente o que está ativo no sistema no momento da compra, e no momento não temos nenhuma campanha de Páscoa vigente por aqui. As promoções oficiais da loja acontecem em datas específicas (como Black Friday, Aniversário da Loja em agosto, Semana do Músico em novembro, entre outras).

Posso te ajudar com mais alguma informação sobre o Martin D-28 ou outro instrumento, Marina?
