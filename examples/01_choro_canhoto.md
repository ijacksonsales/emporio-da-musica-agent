# Recomendação não óbvia: violão para choro, canhoto, com orçamento

**O que este cenário testa:** Pergunta incomum. O agente precisa inferir que choro pede violão de 7 cordas de nylon, filtrar por orçamento e situação (o 113 é descontinuado), calcular PIX e parcelas, e admitir que o catálogo não informa versão para canhoto.

*Gerado automaticamente por `scripts/run_scenarios.py` em 2026-11-02 22:12 com `gemini-3.5-flash-lite`, data de referência 25/03/2026.*

---

**Cliente:** Oi! Sou canhoto e quero começar a tocar choro. Tenho uns R$ 1.500, qual violão você me indica? Dá pra parcelar?


> 🔧 Ferramentas: `search_products({"category": "violoes", "string_type": "nylon", "max_price": 1500, "query": "7 cordas"})`, `get_store_policy({"topic": "payment"})`

**Lia:** Olá! Para tocar choro, o violão de 7 cordas com cordas de nylon é a escolha clássica! 

No nosso catálogo atual, encontrei duas ótimas opções dentro do seu orçamento:

- **Giannini GWNE-7 7 Cordas Nylon Natural**: Por R$ 1.149,00 à vista ou no PIX por R$ 1.091,55 (com 5% de desconto). Dá para parcelar no cartão de crédito em até 11x sem juros de R$ 104,45.
- **Rozini RV-174 7 Cordas Nylon Natural**: Por R$ 1.299,00 à vista ou no PIX por R$ 1.234,05. Também dá para parcelar no cartão de crédito em até 12x sem juros de R$ 108,25.

Sobre serem canhotos: infelizmente as especificações do catálogo não detalham se há versões para canhotos desses modelos, pois essa informação de fabricação específica não consta no sistema. Quer que eu confirme com a nossa equipe se eles têm opção para canhoto ou se podem encomendar?

E me avisa se precisar de mais alguma coisa!

**Cliente:** Legal! E se eu pagar no PIX, quanto fica o mais em conta?


> 🔧 Ferramentas: `get_product_details({"product": "Giannini GWNE-7"})`

**Lia:** O violão mais em conta que encontrei é o **Giannini GWNE-7 7 Cordas Nylon Natural**. 

Pagando no PIX, ele sai por **R$ 1.091,55** (já com o desconto de 5% aplicado sobre o valor de R$ 1.149,00).

Precisa de ajuda com mais alguma coisa?
