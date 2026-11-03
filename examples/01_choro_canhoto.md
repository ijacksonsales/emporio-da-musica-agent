# Recomendação não óbvia: violão para choro, canhoto, com orçamento

**O que este cenário testa:** Pergunta incomum. O agente precisa inferir que choro pede violão de 7 cordas de nylon, filtrar por orçamento e situação (o 113 é descontinuado), calcular PIX e parcelas, e admitir que o catálogo não informa versão para canhoto. Abertura: o cliente não se apresenta, então a Lia dá boas-vindas e pergunta o nome antes.

*Gerado automaticamente por `scripts/run_scenarios.py` em 2026-11-02 22:49 com `gemini-3.5-flash-lite`, data de referência 25/03/2026.*

---

**Cliente:** Oi! Sou canhoto e quero começar a tocar choro. Tenho uns R$ 1.500, qual violão você me indica? Dá pra parcelar?

**Lia:** Oi! Boas-vindas à Empório da Música! 🎸 Eu sou a Lia, assistente virtual da loja. Já te ajudo com a indicação do violão para choro! Antes, como posso te chamar?

**Cliente:** Me chamo Rafael.


> 🔧 Ferramentas: `search_products({"query": "7 cordas", "string_type": "nylon", "category": "violoes", "max_price": 1500})`

**Lia:** Rafael, para começar no choro, o instrumento clássico é o violão de 7 cordas com cordas de nylon. Encontrei duas opções excelentes no nosso catálogo que cabem no seu orçamento:

1. **Giannini GWNE-7 7 Cordas Nylon Natural**
   - Preço: R$ 1.149,00
   - No PIX: R$ 1.091,55
   - Parcelamento: até 11x sem juros

2. **Rozini RV-174 7 Cordas Nylon Natural**
   - Preço: R$ 1.299,00
   - No PIX: R$ 1.234,05
   - Parcelamento: até 12x sem juros

Sobre serem para canhotos, o nosso catálogo não especifica se esses modelos possuem versão para canhoto. Se quiser, posso registrar uma solicitação para a nossa equipe confirmar essa disponibilidade com os fabricantes para você! 

Precisa de ajuda com mais alguma coisa?

**Cliente:** Legal! E se eu pagar no PIX, quanto fica o mais em conta?


> 🔧 Ferramentas: `get_product_details({"product": "Giannini GWNE-7 7 Cordas Nylon Natural"})`

**Lia:** Rafael, o modelo mais em conta é o **Giannini GWNE-7 7 Cordas Nylon Natural**. Pagando no PIX, o valor dele fica por **R$ 1.091,55**. 

Quer que eu peça para a nossa equipe confirmar se ele tem versão para canhoto para você?
