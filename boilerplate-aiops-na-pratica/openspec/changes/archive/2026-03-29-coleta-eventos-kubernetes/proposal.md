## Why

A descoberta de eventos problemáticos no cluster Kubernetes é manual — o operador precisa executar `kubectl get events` ou consultar dashboards. Sem coleta automática, problemas passam despercebidos e o tempo de detecção pode chegar a horas. Este change implementa o PRD 001, criando a base do pipeline de observabilidade que alimentará o agente de análise (PRD 002).

## What Changes

- Adicionar loop assíncrono no FastAPI que coleta eventos Warning do cluster Kubernetes periodicamente
- Usar Python SDK Kubernetes (`kubernetes`) com `EventsV1Api.list_event_for_all_namespaces()` via `asyncio.to_thread()`
- Filtrar apenas eventos Warning ocorridos dentro do intervalo do loop (baseado em `eventTime` com fallback para `deprecatedLastTimestamp`)
- Transformar eventos do SDK para contrato de saída padronizado (dict com uid, type, reason, message, namespace, involved_object, timestamp)
- Criar classe `EventHandler` placeholder que imprime eventos no stdout (implementação real no PRD 002)
- Intervalo configurável via variável de ambiente `EVENT_COLLECTION_INTERVAL_MINUTES` (padrão: 3 minutos)
- Tratamento de erros (cluster inacessível, RBAC insuficiente) sem interromper o loop

## Capabilities

### New Capabilities

- `event-collection`: Coleta periódica de eventos Warning do cluster Kubernetes com filtro temporal, transformação para contrato de saída e entrega a um handler

### Modified Capabilities

_Nenhuma — este é o primeiro change do projeto._

## Impact

- **Código**: Novo módulo em `src/my_agent_app/collector/` (event_collector.py, event_handler.py). Alteração em `main.py` para iniciar/parar a task no lifespan
- **Dependências**: Adicionar `kubernetes>=31.0.0` no `pyproject.toml`
- **Variáveis de ambiente**: Nova env var `EVENT_COLLECTION_INTERVAL_MINUTES`
- **Infraestrutura**: Requer acesso ao cluster Kubernetes com ClusterRole de leitura em events
