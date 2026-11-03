# Fora do escopo: acessórios, categoria vazia e informações da loja

**O que este cenário testa:** A loja não vende acessórios e não tem instrumentos de sopro no catálogo. O agente redireciona com educação e depois responde endereço e horário via política.

*Gerado automaticamente por `scripts/run_scenarios.py` em 2026-11-02 22:13 com `gemini-3.5-flash-lite`, data de referência 25/03/2026.*

---

**Cliente:** Vocês vendem encordoamento e amplificador pra guitarra?

**Lia:** Olá! Tudo bem?

Aqui no Empório da Música nós trabalhamos **apenas com instrumentos musicais**. Infelizmente não vendemos acessórios como encordoamentos, cabos, palhetas, amplificadores ou pedais. Para esses itens, o ideal é procurar uma loja especializada em acessórios!

Precisa de ajuda com alguma guitarra, violão ou outro instrumento?

**Cliente:** Entendi. E saxofone alto, vocês têm?


> 🔧 Ferramentas: `search_products({"category": "sopros_metais"})`

**Lia:** No momento nós não temos saxofones disponíveis no nosso catálogo. 

Quer dar uma olhada em outros instrumentos, como violões, guitarras ou teclados? Temos várias opções legais por aqui!

**Cliente:** Beleza. Qual o endereço da loja e até que horas abre no sábado?


> 🔧 Ferramentas: `get_store_policy({"topic": "about_contact"})`, `get_store_policy({"topic": "hours"})`

**Lia:** Nossa loja física fica na Rua 14 de Maio, 3200, Centro, aqui em Campo Grande/MS. 

Aos sábados, abrimos das **09:00 às 13:00**.

Precisa de ajuda com mais alguma coisa?
