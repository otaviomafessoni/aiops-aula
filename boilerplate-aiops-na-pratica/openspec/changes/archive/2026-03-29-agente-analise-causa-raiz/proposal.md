## Why

O PRD 001 implementou a coleta periódica de eventos Warning do Kubernetes, mas os eventos são apenas logados — não há análise automatizada. O diagnóstico de causa raiz é manual, demorado (30min–2h), depende da experiência individual do operador e não produz documentação padronizada. Eventos já em tratamento podem ser reprocessados, desperdiçando tokens de API.

Este change implementa o pipeline completo de análise: filtragem de eventos duplicados, investigação automatizada via agente LangChain + Claude Sonnet conectado ao cluster via MCP, e persistência de relatórios estruturados no PostgreSQL.

## What Changes

- Configurar Alembic para gerenciamento de migrations do banco de dados
- Criar modelo SQLAlchemy `Report` com tabela `reports` (id, markdown, status, event_uids TEXT[] com GIN index, timestamps)
- Implementar lógica de deduplicação por `metadata.uid` dos eventos contra relatórios existentes no banco
- Transformar `EventHandler` de síncrono para **async**, injetando `sessionmaker` no construtor
- Implementar agente de análise com `create_agent` (LangChain) + `ChatAnthropic` (Claude Sonnet) + `ToolCallLimitMiddleware` para limite de iterações
- Conectar agente ao cluster Kubernetes via `MultiServerMCPClient` (langchain-mcp-adapters) + MCP Server Kubernetes (Flux159) via HTTP, rodando como container no docker-compose
- Gerar relatório Markdown estruturado (resumo, severidade, causa raiz, evidências, solução recomendada)
- Persistir relatório no PostgreSQL com fluxo de status: EM_ANALISE → COMPLETO | INCOMPLETO
- Executar análise em background via `asyncio.create_task` para não bloquear o ciclo de coleta

## Capabilities

### New Capabilities
- `event-deduplication`: Filtragem de eventos já vinculados a relatórios ativos por metadata.uid, evitando reprocessamento
- `root-cause-analysis`: Agente ReAct (LangChain + Claude Sonnet + MCP Kubernetes) que investiga causa raiz de eventos Warning automaticamente
- `report-persistence`: Modelo de dados, persistência e ciclo de status de relatórios de diagnóstico no PostgreSQL

### Modified Capabilities
- `event-collection`: EventHandler muda de síncrono para async e passa a receber sessionmaker no construtor

## Impact

- **Código**: `collector/event_handler.py` (reescrita completa), `collector/event_collector.py` (chamada async do handler), `main.py` (injeção de sessionmaker no handler), novo módulo `agents/`, novo módulo `models/`
- **Banco de dados**: Nova tabela `reports` com migration Alembic
- **Dependências**: `langchain`, `langchain-anthropic`, `langchain-mcp-adapters`, `alembic` (já no pyproject.toml)
- **Infraestrutura**: MCP Server Kubernetes (Flux159) adicionado ao docker-compose como novo serviço (acesso via HTTP)
- **Variáveis de ambiente**: Novas `AGENT_MAX_ITERATIONS` (padrão: 25) e `MCP_KUBERNETES_URL`
