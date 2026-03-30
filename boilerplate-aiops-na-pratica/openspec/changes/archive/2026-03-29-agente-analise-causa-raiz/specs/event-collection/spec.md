## MODIFIED Requirements

### Requirement: EventHandler placeholder
O sistema SHALL implementar uma classe `EventHandler` com método **async** que recebe a lista de eventos no contrato de saída e um `async_sessionmaker` injetado no construtor. O `EventCollector` SHALL chamar o handler com `await`. A implementação inicial do PRD 001 (log no stdout) SHALL ser substituída pelo pipeline de análise do PRD 002.

#### Scenario: Handler é chamado de forma assíncrona
- **WHEN** o EventCollector possui eventos para entregar ao handler
- **THEN** o EventCollector SHALL chamar `await self._handler.handle(events)`

#### Scenario: Handler recebe sessionmaker no construtor
- **WHEN** o EventHandler é instanciado
- **THEN** o construtor SHALL receber `async_sessionmaker` como parâmetro para acesso ao banco de dados
