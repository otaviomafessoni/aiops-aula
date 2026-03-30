## Context

A aplicação FastAPI em `src/my_agent_app/` é o boilerplate do agente AIOps. O módulo `collector/` existe mas está vazio. O `main.py` usa o padrão lifespan do FastAPI para gerenciar o ciclo de vida. Não há dependência do Kubernetes SDK ainda — precisa ser adicionada ao `pyproject.toml`.

A coleta de eventos é a primeira etapa do pipeline: coleta → análise (PRD 002) → correção (PRD 004). O handler é placeholder nesta fase.

## Goals / Non-Goals

**Goals:**
- Coletar eventos Warning de todos os namespaces do cluster Kubernetes em intervalos configuráveis
- Entregar eventos transformados (contrato padronizado) a um handler extensível
- Rodar como task assíncrona sem bloquear o event loop do FastAPI
- Tratar falhas (cluster inacessível, RBAC) com resiliência — sem interromper o loop

**Non-Goals:**
- Persistir eventos no banco de dados
- Deduplicar eventos (responsabilidade do PRD 002)
- Coletar eventos do tipo Normal
- Suportar multi-cluster
- Implementar paginação de eventos

## Decisions

### 1. SDK síncrono + asyncio.to_thread()

**Escolha**: Usar `kubernetes` (SDK síncrono) com `asyncio.to_thread()` para não bloquear o event loop.

**Alternativa considerada**: `kubernetes_asyncio` (client assíncrono nativo).

**Rationale**: Evita adicionar outra dependência. O `to_thread()` é suficiente para uma chamada de API por ciclo. A lib `kubernetes` é a oficial e mais estável.

### 2. EventsV1Api (events.k8s.io/v1)

**Escolha**: Usar `EventsV1Api.list_event_for_all_namespaces()` com `field_selector="type=Warning"`.

**Alternativa considerada**: `CoreV1Api.list_event_for_all_namespaces()` (API legada v1).

**Rationale**: A API `events.k8s.io/v1` é a versão atual e possui o campo `event_time` nativo. A CoreV1Api usa o modelo legado com campos deprecated.

### 3. Filtro temporal: eventTime com fallback

**Escolha**: Usar `event_time` do objeto retornado. Se nulo, usar `deprecated_last_timestamp`. Se ambos nulos, descartar o evento.

**Rationale**: Controllers legados não populam `event_time`. O fallback garante compatibilidade sem perder eventos válidos.

### 4. Task assíncrona no lifespan

**Escolha**: Criar `asyncio.create_task()` no lifespan do FastAPI. Cancelar a task no shutdown.

**Alternativa considerada**: BackgroundTasks do FastAPI, APScheduler.

**Rationale**: Mais simples, sem dependência extra. O loop é único e contínuo — não precisa de scheduler.

### 5. Autenticação com cluster

**Escolha**: Usar `kubernetes.config.load_incluster_config()` com fallback para `load_kube_config()` (desenvolvimento local).

**Rationale**: Em produção roda dentro do cluster (ServiceAccount). Em dev, usa o kubeconfig local. O fallback é padrão da comunidade.

### 6. Estrutura de arquivos

```
src/my_agent_app/collector/
├── __init__.py
├── event_collector.py   # EventCollector: loop + coleta + transformação
└── event_handler.py     # EventHandler: placeholder (print)
```

O `EventCollector` recebe um `EventHandler` por injeção, facilitando a substituição no PRD 002.

## Risks / Trade-offs

| Risco | Mitigação |
|-------|-----------|
| Volume alto de eventos pode aumentar latência da chamada ao API server | Sem limite por ciclo (decisão do PRD). Monitorar em produção. Se necessário, adicionar paginação futuramente |
| SDK síncrono bloqueia uma thread do pool | Uma thread por ciclo a cada N minutos — impacto desprezível |
| Cluster inacessível no startup impede primeira coleta | Log de erro + retry no próximo ciclo. Não impede o FastAPI de subir |
| Drift de clock entre app e API server pode causar perda de eventos | Usar margem de 10s no filtro temporal (buscar eventos um pouco antes do intervalo) |
