# FinanceAgent Pro (v3.1) - Assistente Financeiro com IA

O **FinanceAgent Pro** e um sistema agentico de nivel industrial para gestao financeira pessoal, focado na realidade de **Cabo Verde (CVE)** e mercados globais. Construido com uma arquitectura separada de backend (FastAPI + LangChain + Google Gemini) e frontend (Next.js 16 + React 19), o sistema utiliza um **ciclo de vida deterministico** com memoria persistente em camadas para garantir seguranca e precisao na execucao de tarefas financeiras.

---

## Stack Tecnologica

| Camada | Tecnologia | Versao |
| :--- | :--- | :--- |
| LLM | Google Gemini (via LangChain) | gemini-2.5-flash |
| Framework de Agente | LangChain + LangChain Google GenAI | >= 0.1.0 |
| Backend API | FastAPI + Uvicorn | Python 3.12 |
| Base de Dados | SQLite3 | Nativo Python |
| Frontend | Next.js + React + TailwindCSS v4 | 16.1.6 / 19.2.3 |
| Graficos | Recharts | 3.7.0 |
| Animacoes | Framer Motion | 12.33.0 |
| Icones | Lucide React | 0.563.0 |
| Notificacoes | react-hot-toast | 2.6.0 |
| Markdown | react-markdown | 10.1.0 |
| APIs Externas | DuckDuckGo Search, Alpha Vantage, CoinGecko, ExchangeRate API | -- |

---

## Arquitectura

O sistema segue uma arquitectura **cliente-servidor** com dois processos independentes:

```
[Frontend Next.js :3000]  <-- REST/JSON -->  [Backend FastAPI :8005]  <-- SQL -->  [SQLite agent_data.db]
                                                      |
                                              [Google Gemini API]
                                              [APIs Financeiras Externas]
```

- **Backend** (porta 8005): API RESTful com FastAPI. Recebe pedidos do frontend, orquestra o agente LangChain, processa ficheiros e devolve respostas estruturadas.
- **Frontend** (porta 3000): Aplicacao Next.js 16 com dashboard interactivo e chat com IA integrado.
- **Base de Dados**: SQLite com persistencia de saldos, transaccoes, metas, preferencias, historico de chat e logs de auditoria.

---

## Ciclo de Vida da Tarefa (Lifecycle)

Para garantir rigor financeiro, cada pedido do utilizador passa pelas seguintes fases:

1. **Ingestao e Contexto**: Recepcao do input e isolamento do `ContextVar` do utilizador.
2. **Diagnostico Silencioso (Health Check)**: O `FinancialAdvisor` avalia a saude financeira (Reserva, Dividas) sem o utilizador pedir.
3. **Classificacao e Planeamento**: O LLM classifica a intencao (ANALISE, REGISTO, SIMULACAO, EDUCACAO) e gera um plano de 1-3 passos.
4. **Validacao de Regras (Guardrails)**: Verificacao de Hard Limits (ex: bloquear exposicao cripto acima do perfil de risco).
5. **Execucao via Tools**: Chamada de ferramentas atomicas com inputs validados (max 5 iteracoes).
6. **Persistencia em Camadas**: Gravacao do estado nas camadas de memoria apropriadas (L1-L4).
7. **Resposta Sintetizada**: Resposta final com base nos factos gerados, com deteccao automatica de accao executada.

---

## Ferramentas do Agente (Tools)

O agente dispoe de **14 ferramentas** organizadas em tres modulos:

### Financas e Portfolio (`finance_tools.py`)

| Ferramenta | Descricao | Nivel de Risco |
| :--- | :--- | :--- |
| `get_account_balance` | Consulta saldo actual da conta | BAIXO |
| `set_account_balance` | Define ou actualiza o saldo da conta | ALTO |
| `add_transaction` | Regista receitas e despesas | ALTO |
| `manage_portfolio` | Gestao de activos no portfolio | MEDIO |
| `suggest_investments` | Sugestoes de investimento com base no perfil e guardrails | MEDIO |
| `set_user_preference` | Define preferencias (idade, perfil de risco, etc.) | BAIXO |
| `get_user_profile` | Consulta perfil e preferencias do utilizador | BAIXO |
| `manage_goals` | Criar, actualizar e acompanhar metas financeiras | MEDIO |

### Integracoes Externas (`integrations.py`)

| Ferramenta | Descricao | Nivel de Risco |
| :--- | :--- | :--- |
| `get_stock_quote` | Cotacao de accoes em tempo real | BAIXO |
| `get_crypto_price` | Preco actual de criptomoedas | BAIXO |
| `get_exchange_rate` | Taxas de cambio entre moedas | BAIXO |

### Utilitarios (`core_tools.py`)

| Ferramenta | Descricao | Nivel de Risco |
| :--- | :--- | :--- |
| `calculate` | Calculadora de expressoes matematicas | BAIXO |
| `web_search` | Pesquisa na internet via DuckDuckGo | BAIXO |
| `get_now` | Data e hora actuais | BAIXO |

---

## Arquitectura de Memoria (Camadas L1-L4)

O sistema nao possui apenas um "historico", mas sim uma estrutura de memoria particionada e persistente:

| Camada | Nome | Tipo | Descricao |
| :--- | :--- | :--- | :--- |
| **L1** | Contexto Operacional | Short-term | Historico imediato da conversa actual (ultimas 10 mensagens) |
| **L2** | Perfil e Preferencias | Static | Dados do utilizador (idade, perfil de risco, contexto CVE) |
| **L3** | Factos Financeiros | Hard Data | Historico de transaccoes, saldos reais, metas no SQLite |
| **L4** | Log de Decisoes | Audit | Registo de intencao, plano de execucao, ferramentas usadas e resultado |

O `MemoryManager` serializa mensagens LangChain completas (incluindo metadados de tool_calls) em JSON no SQLite, permitindo reconstituicao fiel do historico entre sessoes.

---

## Endpoints da API (FastAPI)

O backend expoe os seguintes endpoints na porta **8005**:

| Metodo | Rota | Descricao |
| :--- | :--- | :--- |
| `GET` | `/` | Status do sistema |
| `GET` | `/users` | Lista de utilizadores disponiveis |
| `GET` | `/dashboard/{user_id}` | Estatisticas consolidadas (saldo, lucro, reserva, metas, saude) |
| `POST` | `/chat` | Conversa com o agente (multipart/form-data, suporta ficheiros) |
| `POST` | `/chat/json` | Conversa com o agente (JSON, sem ficheiros) |
| `GET` | `/chat/history/{user_id}` | Historico de mensagens da sessao actual |
| `GET` | `/expenses/categories/{user_id}` | Distribuicao de gastos por categoria (ultimos 90 dias) |
| `GET` | `/transactions/{user_id}` | Historico completo de transaccoes |

### Formatos de ficheiro suportados no upload

O endpoint `/chat` aceita ficheiros ate **10 MB** nos seguintes formatos:

- **Documentos**: PDF, Word (.docx), Excel (.xlsx, .xls), CSV
- **Texto**: TXT, MD, JSON, XML, HTML, LOG, CSS, JS, PY
- **Imagens**: PNG, JPG, JPEG, GIF, WebP, BMP (processadas via visao do Gemini)

---

## Frontend (Next.js)

O frontend e uma aplicacao Next.js 16 com as seguintes funcionalidades:

### Dashboard

- **5 StatCards**: Saldo, Reserva de Emergencia, Lucro Mensal, Saude Financeira, Metas Activas
- **Grafico de linha**: Evolucao do patrimonio ao longo do tempo (Recharts)
- **Grafico donut**: Distribuicao de gastos por categoria (ultimos 90 dias)
- **Progresso de Metas**: Barras de progresso com percentagem e prioridade
- **Lista de Transaccoes**: Ultimas 5 transaccoes com tipo, categoria e valor
- **Ocultacao de valores**: Botao para esconder/mostrar valores sensiveis

### Chat com IA

- Chat em tempo real com o agente via API REST
- **Upload de ficheiros**: PDF, Word, Excel, CSV e imagens directamente no chat
- **Botao de parar geracao**: Cancela a resposta do agente a qualquer momento (AbortController)
- **Renderizacao Markdown**: Respostas formatadas com react-markdown
- **Historico persistente**: Carrega mensagens anteriores da sessao
- **Comandos rapidos**: Botoes pre-definidos (Analisar financas, Simular investimento, Ver metas, Adicionar despesa)
- **Notificacoes toast**: Feedback visual para accoes executadas com sucesso

### Internacionalizacao (i18n)

- Suporte completo para **Portugues** e **Ingles**
- Alternador de idioma no cabecalho
- Ficheiros de traducao em `web/src/locales/pt.json` e `web/src/locales/en.json`

### Multi-utilizador

- Selector de utilizador no cabecalho
- Cada utilizador tem dados, historico e preferencias isolados

---

## Modos do Agente

O sistema suporta quatro modos de operacao, cada um com um prompt de sistema especializado:

| Modo | Ficheiro de Prompt | Descricao |
| :--- | :--- | :--- |
| `assistant` | `system.md` | Modo padrao. Assistente financeiro completo. |
| `analyst` | `analyst.md` | Foco em analise de dados e relatorios. |
| `educator` | `educator.md` | Foco em educacao financeira e explicacoes. |
| `simulator` | `simulator.md` | Foco em simulacoes e projecoes financeiras. |

---

## Estrutura do Projecto

```text
task-agent/
├── api_server.py              # API REST FastAPI (ponto de entrada do backend)
├── main.py                    # Interface de terminal (alternativa)
├── agent_data.db              # Base de dados SQLite (persistencia)
├── requirements.txt           # Dependencias Python
├── .env                       # Variaveis de ambiente (chaves API)
│
├── agent/
│   ├── __init__.py            # Exporta TaskAgent e init_db
│   ├── task_agent.py          # Orquestrador do Ciclo de Vida do Agente
│   ├── logic.py               # Motor de Regras e Diagnostico (FinancialAdvisor)
│   ├── memory.py              # Gestor de Memoria em Camadas (L1-L4)
│   ├── data_service.py        # Servico de dados para o dashboard (cache TTL)
│   ├── db.py                  # Conexao e inicializacao SQLite
│   ├── prompts/
│   │   ├── system.md          # Prompt principal do agente
│   │   ├── analyst.md         # Prompt modo analista
│   │   ├── educator.md        # Prompt modo educador
│   │   └── simulator.md       # Prompt modo simulador
│   └── tools/
│       ├── __init__.py        # Registo central de todas as ferramentas
│       ├── finance_tools.py   # Ferramentas de financas e portfolio
│       ├── integrations.py    # Integracoes com APIs externas (stocks, crypto, forex)
│       ├── core_tools.py      # Utilitarios (calculadora, pesquisa web, data/hora)
│       └── simulations.py     # Ferramentas de simulacao
│
└── web/
    ├── package.json           # Dependencias Node.js
    ├── next.config.ts         # Configuracao Next.js
    └── src/
        ├── app/
        │   ├── layout.tsx     # Layout raiz da aplicacao
        │   ├── page.tsx       # Pagina principal (Dashboard + Chat)
        │   └── globals.css    # Estilos globais (TailwindCSS v4)
        ├── components/
        │   ├── ChatWidget.tsx       # Widget de chat com IA
        │   ├── Dashboard.tsx        # StatCard e LineChart
        │   ├── ExpenseCategories.tsx # Grafico donut de categorias
        │   ├── GoalsProgress.tsx    # Barras de progresso de metas
        │   ├── TransactionsList.tsx # Lista de transaccoes recentes
        │   ├── UserSelector.tsx     # Selector de utilizador
        │   ├── LanguageSwitcher.tsx # Alternador de idioma
        │   └── Skeleton.tsx         # Componentes de loading skeleton
        ├── lib/
        │   ├── api.ts         # Cliente HTTP para a API do backend
        │   └── i18n.tsx       # Sistema de internacionalizacao
        └── locales/
            ├── pt.json        # Traducoes em Portugues
            └── en.json        # Traducoes em Ingles
```

---

## Variaveis de Ambiente

Criar um ficheiro `.env` na raiz do projecto com as seguintes variaveis:

```bash
# Obrigatorio
GOOGLE_API_KEY=<sua-chave-api-google>

# Opcional (default: gemini-2.0-flash)
GEMINI_MODEL=gemini-2.5-flash

# Opcional (para Open Finance)
PLUGGY_CLIENT_ID=<seu-client-id>
PLUGGY_CLIENT_SECRET=<seu-client-secret>
```

O frontend utiliza a variavel `NEXT_PUBLIC_API_URL` (default: `http://localhost:8005`) para se conectar ao backend.

---

## Como Executar

### Pre-requisitos

- Python 3.12+
- Node.js 20+
- npm 10+

### 1. Backend (FastAPI)

```bash
# Criar e activar ambiente virtual
python -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variaveis de ambiente
cp .env.example .env
# Editar .env com a sua GOOGLE_API_KEY

# Executar o servidor API (porta 8005)
./venv/bin/python api_server.py
```

### 2. Frontend (Next.js)

```bash
# Instalar dependencias
cd web && npm install

# Executar em modo de desenvolvimento (porta 3000)
npm run dev
```

### 3. Aceder a Aplicacao

- **Frontend (Dashboard + Chat)**: http://localhost:3000
- **Backend (API)**: http://localhost:8005
- **Documentacao API**: http://localhost:8005/docs (Swagger UI automatico do FastAPI)

---

## Contratos de Skills (Exemplos)

Cada capacidade do agente e governada por um contrato de execucao:

| Skill | Input (Schema) | Output (Schema) | Nivel de Risco |
| :--- | :--- | :--- | :--- |
| `add_transaction` | `{amount, type, category}` | `{new_balance, status}` | **ALTO** (Altera Saldo) |
| `get_stock_quote` | `{symbol}` | `{price, change_pct}` | **BAIXO** (Consulta) |
| `manage_goals` | `{action, goal_name}` | `{progress, remaining}` | **MEDIO** (Estrategico) |
| `suggest_investments` | `{amount}` | `{allocation, guardrails}` | **MEDIO** (Guardrails) |

---

## Prova de Execucao (Exemplo Real)

**Input:** `"Regista 2000 CVE em combustivel"`

**Processamento Interno:**
- **Diagnostico:** Reserva de emergencia em 4 meses (ALERTA: < 6).
- **Regra:** Categoria 'Transporte' tem limite de 10.000/mes. Gasto actual: 8.000.
- **Decisao:** Executa `add_transaction`.

**Output:**
> Transaccao de 2.000 CVE registada.
> **Nota do Consultor:** Ja atingiste o teu limite de 10.000 CVE para Transportes este mes.
> Alem disso, lembra-te que a tua prioridade actual e reforcar a reserva (estas a 66% da meta).

---

## Limitacoes e Compliance

- **Nao Executor**: O sistema nao possui acesso a APIs bancarias reais; simula operacoes para fins de gestao pessoal.
- **Aconselhamento**: As sugestoes sao puramente algoritmicas e educacionais, nao constituindo aconselhamento financeiro legal.
- **Dados**: Depende da precisao dos dados inseridos manualmente pelo utilizador.
- **Limite de Iteracoes**: O agente executa no maximo 5 iteracoes de raciocinio por pedido.
- **Cache**: Dados do dashboard tem TTL de 30 segundos; contexto L2/L3 do agente tem TTL de 5 minutos.

---

## Proximos Passos

- [ ] Implementacao de streaming de respostas (SSE) para feedback em tempo real
- [ ] Integracao com Open Finance via Pluggy SDK
- [ ] Dashboard de tracking de decisoes (logs L4 visiveis na UI)
- [ ] Testes automatizados (unitarios e de integracao)
- [ ] Deploy com Docker Compose (backend + frontend + reverse proxy)

---

## Licenca

Projecto em desenvolvimento activo. Uso interno e educacional.
