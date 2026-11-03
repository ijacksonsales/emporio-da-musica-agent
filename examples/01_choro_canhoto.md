# Recomendação não óbvia: violão para choro, canhoto, com orçamento

**O que este cenário testa:** Pergunta incomum. O agente precisa inferir que choro pede violão de 7 cordas de nylon, filtrar por orçamento e situação (o 113 é descontinuado), calcular PIX e parcelas, e admitir que o catálogo não informa versão para canhoto.

*Gerado automaticamente por `scripts/run_scenarios.py` em 2026-11-02 22:07 com `gemini-3.5-flash-lite`, data de referência 25/03/2026.*

---

**Cliente:** Oi! Sou canhoto e quero começar a tocar choro. Tenho uns R$ 1.500, qual violão você me indica? Dá pra parcelar?


> 🔧 Ferramentas: `search_products({"category": "violoes", "string_type": "nylon", "max_price": 1500})`, `get_store_policy({"topic": "payment"})`

**Lia:** Que legal que você quer começar no choro! Para esse estilo, o violão de nylon de 7 cordas é o clássico, pois traz aquele grave encorpado característico do gênero.

Sobre ser canhoto, nosso catálogo não especifica se os modelos são para canhotos na descrição, mas posso confirmar isso diretamente com a nossa equipe para você, se quiser!

No seu orçamento de até R$ 1.500, temos excelentes opções de 7 cordas de nylon dentro do seu limite:

- **Giannini GWNE-7 7 Cordas Nylon Natural**: R$ 1.149,00 (ou R$ 1.091,55 no PIX; e dá para parcelar no cartão em até 11x sem juros de R$ 104,45).
- **Rozini RV-174 7 Cordas Nylon Natural**: R$ 1.299,00 (ou R$ 1.234,05 no PIX; com parcelamento no cartão em até 12x sem juros de R$ 108,25).

Sim, dá para parcelar no cartão sem juros! 

Quer que eu confirme com a equipe se algum desses modelos possui versão para canhoto ou ficou com alguma dúvida sobre eles?

**Cliente:** Legal! E se eu pagar no PIX, quanto fica o mais em conta?


> 🔧 Ferramentas: `search_products({"max_price": 1500, "category": "violoes", "string_type": "nylon", "query": "7 cordas"})`

**Lia:** O violão 7 cordas mais em conta do nosso catálogo é o **Giannini GWNE-7 7 Cordas Nylon Natural**. 

No pagamento à vista via PIX, ele sai por **R$ 1.091,55** (o preço de tabela dele é R$ 1.149,00).

O que acha dele? Quer que eu verifique com a equipe sobre a disponibilidade da versão para canhoto?
