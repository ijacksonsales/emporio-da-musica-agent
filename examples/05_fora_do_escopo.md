# Fora do escopo: acessórios, categoria vazia e informações da loja

**O que este cenário testa:** A loja não vende acessórios e não tem instrumentos de sopro no catálogo. O agente redireciona com educação e depois responde endereço e horário via política.

*Gerado automaticamente por `scripts/run_scenarios.py` em 2026-11-02 22:06 com `gemini-3.5-flash-lite`, data de referência 25/03/2026.*

---

**Cliente:** Vocês vendem encordoamento e amplificador pra guitarra?

**Lia:** Olá! Tudo bem?

A Empório da Música trabalha exclusivamente com **instrumentos musicais**. Por isso, não vendemos acessórios como encordoamentos ou amplificadores. 

Nesse caso, recomendo dar uma olhada em lojas especializadas em acessórios para instrumentos. 

Mas se estiver procurando uma guitarra nova, temos várias opções incríveis por aqui! Posso te ajudar com alguma?

**Cliente:** Entendi. E saxofone alto, vocês têm?


> 🔧 Ferramentas: `search_products({"category": "sopros_metais"})`

**Lia:** No momento, nós não temos saxofones disponíveis no catálogo da Empório da Música. Nossa linha de sopros está temporariamente sem produtos. 

Se quiser dar uma olhada em outras categorias, temos ótimas opções de violões, guitarras, teclados, pianos e baterias! Posso te mostrar alguma delas?

**Cliente:** Beleza. Qual o endereço da loja e até que horas abre no sábado?


> 🔧 Ferramentas: `get_store_policy({"topic": "about_contact"})`, `get_store_policy({"topic": "hours"})`

**Lia:** Nossa loja fica na **Rua 14 de Maio, 3200, Centro, Campo Grande - MS**.

Aos sábados, funcionamos das **09:00 às 13:00**.

Posso te ajudar com mais alguma informação ou com a busca por algum instrumento?
