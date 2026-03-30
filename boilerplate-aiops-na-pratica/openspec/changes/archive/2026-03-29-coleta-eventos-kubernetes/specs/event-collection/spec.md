## ADDED Requirements

### Requirement: Coleta periódica de eventos Warning
O sistema SHALL executar um loop assíncrono que coleta eventos do tipo Warning de todos os namespaces do cluster Kubernetes em intervalos regulares. O intervalo SHALL ser configurável via variável de ambiente `EVENT_COLLECTION_INTERVAL_MINUTES` (padrão: 3 minutos).

#### Scenario: Coleta no intervalo padrão
- **WHEN** a aplicação inicia sem a variável `EVENT_COLLECTION_INTERVAL_MINUTES` definida
- **THEN** o loop de coleta SHALL executar a cada 3 minutos

#### Scenario: Coleta com intervalo customizado
- **WHEN** a variável `EVENT_COLLECTION_INTERVAL_MINUTES` está definida com valor "5"
- **THEN** o loop de coleta SHALL executar a cada 5 minutos

#### Scenario: Variável de ambiente inválida
- **WHEN** a variável `EVENT_COLLECTION_INTERVAL_MINUTES` contém valor não-numérico, negativo ou zero
- **THEN** o sistema SHALL usar o padrão de 3 minutos e registrar warning no log

### Requirement: Filtro por tipo Warning
O sistema SHALL coletar apenas eventos com `type=Warning`. Eventos do tipo Normal SHALL ser ignorados.

#### Scenario: Cluster com eventos Warning e Normal
- **WHEN** o cluster possui eventos Warning e Normal no intervalo
- **THEN** apenas os eventos Warning SHALL ser retornados pela coleta

### Requirement: Filtro temporal por intervalo do loop
O sistema SHALL coletar apenas eventos ocorridos dentro do intervalo do loop atual. O campo `event_time` SHALL ser usado como timestamp primário. Se `event_time` for nulo, SHALL usar `deprecated_last_timestamp` como fallback. Eventos sem nenhum dos dois campos SHALL ser descartados com warning no log.

#### Scenario: Evento com eventTime dentro do intervalo
- **WHEN** um evento Warning possui `event_time` dentro do intervalo do loop
- **THEN** o evento SHALL ser incluído na coleta

#### Scenario: Evento com eventTime fora do intervalo
- **WHEN** um evento Warning possui `event_time` anterior ao intervalo do loop
- **THEN** o evento SHALL ser excluído da coleta

#### Scenario: Evento sem eventTime com deprecatedLastTimestamp
- **WHEN** um evento Warning possui `event_time` nulo mas `deprecated_last_timestamp` dentro do intervalo
- **THEN** o evento SHALL ser incluído na coleta usando `deprecated_last_timestamp` como timestamp

#### Scenario: Evento sem nenhum timestamp
- **WHEN** um evento Warning possui `event_time` e `deprecated_last_timestamp` ambos nulos
- **THEN** o evento SHALL ser descartado e um warning SHALL ser registrado no log

### Requirement: Transformação para contrato de saída
Os eventos coletados SHALL ser transformados para o seguinte contrato antes de serem entregues ao handler:

```python
{
    "uid": str,           # metadata.uid
    "type": str,          # tipo do evento ("Warning")
    "reason": str,        # reason do evento
    "message": str,       # mensagem descritiva
    "namespace": str,     # namespace do evento
    "involved_object": {
        "kind": str,      # tipo do recurso
        "name": str,      # nome do recurso
        "namespace": str  # namespace do recurso
    },
    "timestamp": str      # ISO 8601 — eventTime ou fallback
}
```

#### Scenario: Transformação de evento CrashLoopBackOff
- **WHEN** um evento Warning de CrashLoopBackOff é coletado
- **THEN** o evento SHALL ser transformado para o contrato com todos os campos preenchidos, incluindo `involved_object` com kind, name e namespace do Pod afetado

### Requirement: Entrega em batch ao EventHandler
Os eventos coletados em um ciclo SHALL ser agrupados e entregues como lista única ao `EventHandler`. Se nenhum evento Warning for encontrado no intervalo, o handler SHALL NOT ser chamado.

#### Scenario: Múltiplos eventos no mesmo ciclo
- **WHEN** 5 eventos Warning ocorrem dentro do intervalo
- **THEN** os 5 eventos SHALL ser entregues como batch único ao EventHandler

#### Scenario: Nenhum evento no intervalo
- **WHEN** nenhum evento Warning ocorre dentro do intervalo
- **THEN** o EventHandler SHALL NOT ser chamado e o sistema aguarda o próximo ciclo

### Requirement: EventHandler placeholder
O sistema SHALL implementar uma classe `EventHandler` com método que recebe a lista de eventos no contrato de saída. A implementação inicial SHALL imprimir os eventos no stdout. Esta classe SHALL ser substituída pela implementação real no PRD 002.

#### Scenario: Handler imprime eventos
- **WHEN** o EventHandler recebe uma lista de eventos
- **THEN** os eventos SHALL ser impressos no stdout

### Requirement: Resiliência a falhas de conectividade
O sistema SHALL tratar erros de conexão com o cluster sem interromper o loop de coleta. Erros SHALL ser registrados no log e a coleta SHALL ser tentada novamente no próximo ciclo.

#### Scenario: Cluster inacessível
- **WHEN** o cluster Kubernetes está inacessível durante a coleta
- **THEN** o erro SHALL ser registrado no log e o loop SHALL continuar aguardando o próximo ciclo

#### Scenario: Permissão RBAC insuficiente
- **WHEN** o ServiceAccount não possui permissão para listar eventos
- **THEN** o erro SHALL ser registrado no log indicando a permissão necessária e o loop SHALL continuar

### Requirement: Autenticação com cluster Kubernetes
O sistema SHALL autenticar com o cluster usando `load_incluster_config()` (produção). Se falhar, SHALL tentar `load_kube_config()` como fallback (desenvolvimento local).

#### Scenario: Execução dentro do cluster
- **WHEN** a aplicação roda dentro de um Pod Kubernetes
- **THEN** SHALL usar `load_incluster_config()` para autenticação via ServiceAccount

#### Scenario: Execução local em desenvolvimento
- **WHEN** a aplicação roda fora do cluster (desenvolvimento)
- **THEN** SHALL usar `load_kube_config()` com o kubeconfig local
