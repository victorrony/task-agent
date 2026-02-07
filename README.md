# FinanceAgent Pro (v3.1) - Engenharia de Assistência Financeira 🚀

O **FinanceAgent Pro** é um sistema agêntico de nível industrial para gestão financeira, focado na realidade de **Cabo Verde (CVE)** e mercados globais. Diferente de um chatbot comum, este sistema utiliza um **ciclo de vida determinístico** para garantir segurança e precisão na execução de tarefas.

---

## ⚙️ Ciclo de Vida da Tarefa (Lifecycle)
Para garantir rigor financeiro, cada pedido do utilizador passa pelas seguintes fases:

1.  **Ingestão & Contexto**: Receção do input e isolamento do `ContextVar` do utilizador.
2.  **Diagnóstico Silencioso (Health Check)**: O `FinancialAdvisor` avalia a saúde financeira (Reserva, Dívidas) sem o utilizador pedir.
3.  **Classificação & Planeamento**: O LLM decide quais **Skills** são necessárias.
4.  **Validação de Regras (Guardrails)**: Verificação de Hard Limits (ex: bloquear despesas acima do limite).
5.  **Execução via Skills**: Chamada de funções atómicas com inputs validados.
6.  **Persistência Camadada**: Gravação do estado nas camadas de memória apropriadas.
7.  **Resposta Sintetizada**: Resposta final com base nos factos gerados.

---

## 🛠️ Contratos de Skills (Exemplos)
Cada capacidade do agente é governada por um contrato de execução:

| Skill | Input (Schema) | Output (Schema) | Nível de Risco |
| :--- | :--- | :--- | :--- |
| `add_transaction` | `{amount, type, category}` | `{new_balance, status}` | **ALTO** (Altera Saldo) |
| `get_stock_quote`| `{symbol}` | `{price, change_pct}` | **BAIXO** (Consulta) |
| `manage_goals` | `{action, goal_name}` | `{progress, remaining}`| **MÉDIO** (Estratégico) |

---

## 🧠 Arquitetura de Memória (Camadas)
O sistema não possui apenas um "histórico", mas sim uma estrutura de memória particionada:

- **L1: Contexto Operacional (Short-term)**: Histórico imediato da conversa atual.
- **L2: Perfil & Preferências (Static)**: Dados do utilizador (Idade, Perfil de Risco, CVE context).
- **L3: Factos Financeiros (Hard Data)**: Histórico de transações e saldos reais no SQLite.
- **L4: Log de Decisões (Audit)**: Registo de porquê o agente escolheu a Tool X ou Y.

---

## 📈 Prova de Execução (Exemplo Real)

**Input:** `"Regista 2000 CVE em combustível"`

**Processamento Interno:**
- **Diagnóstico:** Reserva de emergência em 4 meses (ALERTA: < 6).
- **Regra:** Categoria 'Transporte' tem limite de 10.000/mês. Gasto atual: 8.000.
- **Decisão:** Executa `add_transaction`.

**Output:**
> ✅ Transação de 2.000 CVE registada.
> ⚠️ **Nota do Consultor:** Já atingiste o teu limite de 10.000 CVE para Transportes este mês. 
> Além disso, lembra-te que a tua prioridade atual é reforçar a reserva (estás a 66% da meta).

---

## 📂 Estrutura Técnica

```text
task-agent/
├── agent/
│   ├── task_agent.py     # Orquestrador do Ciclo de Vida
│   ├── logic.py          # Motor de Regras e Diagnóstico
│   ├── memory.py         # Gestor de Memória Camadada
│   ├── db.py             # Persistência Enterprise (SQLite)
│   └── tools/            # Implementação Atómica de Skills
└── ui/                   # Interface de Observabilidade (Dashboard)
```

---

## � Limitações e Compliance
- **Não Executor**: O sistema não possui acesso a APIS bancárias reais; simula operações para fins de gestão.
- **Aconselhamento**: As sugestões são puramente algorítmicas e educacionais, não constituindo aconselhamento financeiro legal.
- **Dados**: Depende da precisão dos dados inseridos manualmente pelo utilizador.

---

## 📜 Licença e Próximos Passos
- [ ] Implementação de **Modo Auditor** (Explicação de decisão).
- [ ] Logs estruturados para observabilidade.
- [ ] Dashboard de tracking de decisões.
