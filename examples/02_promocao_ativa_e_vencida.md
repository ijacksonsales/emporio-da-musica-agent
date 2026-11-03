# Preço com promoção ativa, PIX não cumulativo e promoção vencida

**O que este cenário testa:** Produto 90 tem 18% ativo: mostrar preço original, % e final, sem somar o PIX. Produto 93 teve promoção de Páscoa, hoje inativa: não prometer o desconto.

*Gerado automaticamente por `scripts/run_scenarios.py` em 2026-11-02 22:07 com `gemini-3.5-flash-lite`, data de referência 25/03/2026.*

---

**Cliente:** Boa tarde! Quanto tá o violão Crafter HT-100? Se eu pagar no PIX ganho mais desconto?


> 🔧 Ferramentas: `get_product_details({"product": "Crafter HT-100"})`, `get_store_policy({"topic": "payment"})`

**Lia:** Boa tarde! Tudo bem?

O **Crafter HT-100 Folk Aço Natural** está com um desconto exclusivo de 18% em promoção! O preço de tabela dele é R$ 2.399,00, e com a promoção ele sai por **R$ 1.967,18**, que você pode parcelar em até 12x sem juros de R$ 163,93 no cartão de crédito, ou pagar esse mesmo valor de R$ 1.967,18 no PIX.

Como ele já está com preço promocional ativo, o desconto do PIX não é cumulativo com a promoção, ok? 

Temos 3 unidades dele disponíveis em estoque por aqui. Posso te ajudar com mais alguma informação ou reserva?

**Cliente:** E o Martin D-28? Vi um anúncio de Páscoa com 15% off nele.


> 🔧 Ferramentas: `get_product_details({"product": "Martin D-28"})`, `get_store_policy({"topic": "promotions"})`

**Lia:** Olha, o Martin D-28 Dreadnought Natural é um violão lendário e maravilhoso! 

Sobre o anúncio, as promoções que a gente faz seguem rigorosamente o que está ativo no sistema no momento, e atualmente não temos nenhuma campanha de Páscoa ou desconto promocional para o Martin D-28. Ele está com o preço normal de tabela por **R$ 11.499,00**, que pode ser pago no PIX por **R$ 10.924,05** (com 5% de desconto) ou parcelado em até 12x sem juros de R$ 958,25 no cartão de crédito.

Temos 2 unidades dele em estoque por aqui. Quer que eu te conte mais detalhes sobre ele?
