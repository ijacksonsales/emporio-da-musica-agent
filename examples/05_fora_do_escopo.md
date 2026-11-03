# Fora do escopo: acessórios, categoria vazia e informações da loja

**O que este cenário testa:** A loja não vende acessórios e não tem instrumentos de sopro no catálogo. O agente redireciona com educação e depois responde endereço e horário via política.

*Gerado automaticamente por `scripts/run_scenarios.py` em 2026-11-02 22:51 com `gemini-3.5-flash-lite`, data de referência 25/03/2026.*

---

**Cliente:** Olá, sou o Diego! Vocês vendem encordoamento e amplificador pra guitarra?

**Lia:** Oi, Diego! Boas-vindas à Empório da Música! Eu sou a Lia.

Nós trabalhamos exclusivamente com instrumentos musicais, então não vendemos encordoamento nem amplificadores por aqui, infelizmente. Te sugiro dar uma olhada em lojas especializadas em acessórios!

Se precisar de alguma guitarra ou outro instrumento, é só me falar. Precisa de mais alguma coisa por enquanto?

**Cliente:** Entendi. E saxofone alto, vocês têm?


> 🔧 Ferramentas: `search_products({"category": "sopros_metais"})`

**Lia:** Diego, no momento nós não temos saxofones altos disponíveis no catálogo. 

Quer dar uma olhada em alguma outra categoria, como violões, guitarras ou teclados?

**Cliente:** Beleza. Qual o endereço da loja e até que horas abre no sábado?


> 🔧 Ferramentas: `get_store_policy({"topic": "about_contact"})`, `get_store_policy({"topic": "hours"})`

**Lia:** Diego, nossa loja fica na Rua 14 de Maio, 3200, Centro, em Campo Grande - MS. 

No sábado, abrimos das 09:00 às 13:00! 

Precisa de mais alguma coisa?
