## 1. Setup

- [x] 1.1 Adicionar dependência `kubernetes>=31.0.0` no `pyproject.toml` e rodar `uv sync`
- [x] 1.2 Adicionar `EVENT_COLLECTION_INTERVAL_MINUTES` na documentação do CLAUDE.md (tabela de variáveis de ambiente)

## 2. EventHandler

- [x] 2.1 Criar `src/my_agent_app/collector/event_handler.py` com classe `EventHandler` e método `handle(events: list[dict])` que imprime os eventos no stdout

## 3. EventCollector

- [x] 3.1 Criar `src/my_agent_app/collector/event_collector.py` com classe `EventCollector` que recebe `EventHandler` e o intervalo de coleta
- [x] 3.2 Implementar autenticação com cluster (`load_incluster_config` com fallback para `load_kube_config`)
- [x] 3.3 Implementar método de coleta usando `EventsV1Api.list_event_for_all_namespaces()` via `asyncio.to_thread()` com `field_selector="type=Warning"`
- [x] 3.4 Implementar filtro temporal (eventos dentro do intervalo) com lógica de fallback `event_time` → `deprecated_last_timestamp`
- [x] 3.5 Implementar transformação dos eventos do SDK para o contrato de saída (dict padronizado)
- [x] 3.6 Implementar loop assíncrono (`run`) com tratamento de erros (ApiException, ConnectionError) sem interromper o loop

## 4. Integração no FastAPI

- [x] 4.1 Implementar leitura da env var `EVENT_COLLECTION_INTERVAL_MINUTES` com validação (fallback para 3 se inválido)
- [x] 4.2 Alterar `main.py` lifespan para criar `EventCollector` e iniciar task com `asyncio.create_task()`
- [x] 4.3 Cancelar a task do collector no shutdown (após o `yield` do lifespan)
- [x] 4.4 Atualizar `collector/__init__.py` com exports do módulo

## 5. Documentação

- [x] 5.1 Corrigir referência no PRD 001 de `src/aiops_k8s/` para `src/my_agent_app/`
