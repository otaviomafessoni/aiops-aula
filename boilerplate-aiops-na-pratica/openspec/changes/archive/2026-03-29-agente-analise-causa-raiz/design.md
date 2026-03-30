## Context

A aplicação coleta eventos Warning do Kubernetes periodicamente (PRD 001) via `EventCollector` → `EventHandler`. Hoje o handler apenas loga os eventos. Este design transforma o handler no ponto de entrada do pipeline de análise: filtragem de duplicados, criação de relatório, invocação do agente e persistência do resultado.

Estado atual relevante:
- `EventHandler.handle()` é síncrono e sem acesso ao banco
- `EventCollector` chama `handler.handle(events)` sem await
- Não há modelos SQLAlchemy nem Alembic configurado
- Módulo `agents/` está vazio
- Dependências LangChain e langchain-mcp-adapters já estão no `pyproject.toml`

## Goals / Non-Goals

**Goals:**
- Transformar o EventHandler em ponto de entrada async do pipeline de análise
- Implementar deduplicação de eventos por `metadata.uid` contra relatórios existentes
- Criar agente ReAct que investiga causa raiz via MCP Server Kubernetes
- Persistir relatórios estruturados no PostgreSQL com ciclo de status
- Executar análise em background sem bloquear coleta

**Non-Goals:**
- Interface de visualização dos relatórios (PRD 003)
- Notificação no Discord (PRD 003)
- Execução automática de correções (PRD 004)
- Histórico de eventos brutos no banco
- Deduplicação avançada por `involvedObject` + `reason` (v2)

## Decisions

### 1. EventHandler async com sessionmaker injetado no construtor

O handler precisa consultar e escrever no banco. Injetar `async_sessionmaker` no construtor dá autonomia ao handler para gerenciar suas próprias sessões, inclusive em tasks background.

**Alternativa descartada:** Passar session por chamada — amarraria o ciclo de vida da sessão ao caller, complicando execução em background.

**Impacto:** `EventCollector` passa a chamar `await self._handler.handle(events)`. Mudança de uma linha no PRD 001.

### 2. Análise em background via asyncio.create_task

O fluxo do handler:
1. Filtra eventos duplicados (consulta banco)
2. Cria relatório com status EM_ANALISE (protege contra race condition)
3. Dispara `asyncio.create_task(self._analyze(report_id, events))` → retorna imediato

O relatório EM_ANALISE já existe no banco antes da análise começar, então ciclos subsequentes de coleta identificam os eventos como "em tratamento".

**Alternativa descartada:** Execução sequencial — bloquearia coleta por 5-10 minutos durante análise.

### 3. Agente com create_agent + ToolCallLimitMiddleware

API atual do LangChain:
```
create_agent(model, tools, system_prompt=..., middleware=[...])
```

- `ChatAnthropic(model="claude-sonnet-4-6")` como LLM
- `ToolCallLimitMiddleware(run_limit=N, exit_behavior='continue')` para limitar iterações
- `run_limit` configurável via `AGENT_MAX_ITERATIONS` (padrão: 25)
- Com `exit_behavior='continue'`, ao atingir o limite o agente para de chamar tools mas gera uma resposta final indicando que a investigação foi inconclusiva e requer análise manual
- Relatório salvo com status INCOMPLETO neste caso

**Alternativa descartada:** `create_react_agent` do LangGraph — depreciado no LangGraph v1.

### 4. MCP via MultiServerMCPClient (HTTP)

O MCP Server Kubernetes (Flux159) roda como container no `docker-compose` do projeto (assim como o PostgreSQL). A conexão é feita via HTTP usando `langchain-mcp-adapters`:
```
MultiServerMCPClient({
    "kubernetes": {
        "transport": "http",
        "url": "http://mcp-kubernetes:3000/mcp",
    }
})
```

A URL do MCP Server SHALL ser configurável via variável de ambiente `MCP_KUBERNETES_URL`.

O client é criado por invocação do agente (não compartilhado entre análises).

**Alternativa descartada:** stdio via `npx` — requer Node.js instalado na aplicação e é projetado para uso local. HTTP via docker-compose é mais adequado para ambiente de servidor e alinhado com a infraestrutura existente.

### 5. Modelo Report com TEXT[] e GIN index

```
reports:
  - id: UUID (PK)
  - markdown: TEXT
  - status: VARCHAR (enum)
  - event_uids: TEXT[] (GIN index)
  - created_at: TIMESTAMP WITH TIME ZONE
  - updated_at: TIMESTAMP WITH TIME ZONE
```

Status possíveis: EM_ANALISE, COMPLETO, INCOMPLETO, CORRIGINDO, CORRIGIDO, FALHA_CORRECAO

Consulta de deduplicação: `SELECT id FROM reports WHERE event_uids && ARRAY[:uids] AND status NOT IN ('CORRIGIDO')`

O operador `&&` (overlap) com GIN index é performático para arrays.

### 6. Alembic com async engine

Configurar Alembic apontando para o `Base.metadata` de `database.py`. Usar `run_async` no `env.py` para suportar o engine asyncpg. Primeira migration cria a tabela `reports`.

### 7. Estrutura de módulos

```
src/my_agent_app/
├── agents/
│   ├── __init__.py
│   └── root_cause_agent.py    # create_agent + prompt + invocação
├── collector/
│   ├── __init__.py
│   ├── event_collector.py     # mudança: await handler.handle()
│   └── event_handler.py       # reescrita: async, dedup, background
├── models/
│   ├── __init__.py
│   └── report.py              # modelo SQLAlchemy Report
└── ...
```

## Risks / Trade-offs

| Risco | Mitigação |
|-------|-----------|
| Qualidade da análise do LLM varia — causa raiz pode ser incorreta | Relatórios ficam disponíveis para revisão humana. Prompt estruturado com regras de investigação |
| Custo de API escala com volume de eventos e investigações longas | `ToolCallLimitMiddleware` limita chamadas. Deduplicação evita reprocessamento |
| MCP Server Kubernetes indisponível durante análise | Relatório atualizado para INCOMPLETO. Eventos reprocessados no próximo ciclo |
| Tasks em background podem falhar silenciosamente | Logging estruturado em cada etapa. Try/except no wrapper da task com atualização do status para INCOMPLETO |
| MCP Server como container no docker-compose adiciona dependência de infraestrutura | Alinhado com padrão existente (PostgreSQL já roda no compose). Health check no container garante disponibilidade |
| EventAggregator do K8s cria UIDs diferentes para o mesmo problema lógico | Risco aceito na v1. Deduplicação por `metadata.uid` é suficiente para a maioria dos casos |
