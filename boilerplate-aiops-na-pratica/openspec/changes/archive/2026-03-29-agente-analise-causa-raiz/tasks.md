## 1. Setup do Alembic e Modelo de Dados

- [x] 1.1 Configurar Alembic com suporte a engine async (alembic init, ajustar env.py com run_async, configurar alembic.ini com DATABASE_URL)
- [x] 1.2 Criar modelo SQLAlchemy `Report` em `models/report.py` (id UUID, markdown TEXT, status VARCHAR, event_uids TEXT[], created_at, updated_at)
- [x] 1.3 Criar migration Alembic para tabela `reports` com GIN index em `event_uids`

## 2. Adaptação do EventHandler e EventCollector

- [x] 2.1 Modificar `EventHandler` para async: construtor recebe `async_sessionmaker`, método `handle` passa a ser `async def`
- [x] 2.2 Modificar `EventCollector` para chamar `await self._handler.handle(events)` no lugar de `self._handler.handle(events)`
- [x] 2.3 Atualizar `main.py` para injetar `sessionmaker` no construtor do `EventHandler`

## 3. Deduplicação de Eventos

- [x] 3.1 Implementar método de consulta no banco que verifica quais event_uids já estão vinculados a relatórios ativos (status NOT IN CORRIGIDO)
- [x] 3.2 Implementar lógica de filtragem no `EventHandler.handle()` que remove eventos duplicados antes de disparar análise
- [x] 3.3 Tratar indisponibilidade do banco na deduplicação (log de erro, não disparar análise, aguardar próximo ciclo)

## 4. Agente de Análise de Causa Raiz

- [x] 4.1 Criar `agents/root_cause_agent.py` com função que configura o `MultiServerMCPClient` (transport http, URL configurável via MCP_KUBERNETES_URL) e carrega as tools
- [x] 4.2 Implementar criação do agente com `create_agent`, `ChatAnthropic` (Claude Sonnet), `ToolCallLimitMiddleware` (run_limit configurável via AGENT_MAX_ITERATIONS) e system_prompt de investigação
- [x] 4.3 Implementar parsing da variável `AGENT_MAX_ITERATIONS` com fallback para 25 e warning no log para valores inválidos
- [x] 4.4 Implementar invocação do agente com a lista de eventos e captura do relatório Markdown gerado

## 5. Pipeline Completo no EventHandler

- [x] 5.1 Implementar criação do relatório com status EM_ANALISE no banco antes de disparar análise (protege contra race condition)
- [x] 5.2 Implementar execução da análise em background via `asyncio.create_task` com try/except que atualiza relatório para INCOMPLETO em caso de falha
- [x] 5.3 Implementar atualização do relatório no banco com markdown gerado e status COMPLETO ou INCOMPLETO (quando agente atinge limite de iterações)
- [x] 5.4 Atualizar `collector/__init__.py` para exportar as novas classes/dependências

## 6. Variáveis de Ambiente e Documentação

- [x] 6.1 Adicionar `AGENT_MAX_ITERATIONS` e `MCP_KUBERNETES_URL` ao CLAUDE.md na seção de variáveis de ambiente
- [x] 6.2 Adicionar serviço MCP Server Kubernetes (Flux159) ao docker-compose com health check e porta exposta
