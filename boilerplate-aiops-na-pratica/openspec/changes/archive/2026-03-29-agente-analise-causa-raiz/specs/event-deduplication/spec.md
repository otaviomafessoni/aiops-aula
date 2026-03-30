## ADDED Requirements

### Requirement: Filtragem de eventos por metadata.uid contra relatórios existentes
O sistema SHALL consultar o banco de dados antes de disparar análise para verificar se os `metadata.uid` dos eventos já estão vinculados a relatórios existentes. Eventos vinculados a relatórios com status EM_ANALISE, COMPLETO, INCOMPLETO, CORRIGINDO ou FALHA_CORRECAO SHALL ser ignorados. Eventos vinculados a relatórios com status CORRIGIDO SHALL ser reanalisados (problema pode ter reincidido).

#### Scenario: Todos os eventos são novos
- **WHEN** o handler recebe 3 eventos cujos UIDs não existem em nenhum relatório
- **THEN** os 3 eventos SHALL ser encaminhados para análise

#### Scenario: Todos os eventos já estão em tratamento
- **WHEN** o handler recebe 3 eventos cujos UIDs já estão vinculados a relatórios com status EM_ANALISE
- **THEN** nenhum evento SHALL ser encaminhado para análise e o handler SHALL aguardar o próximo ciclo

#### Scenario: Parte dos eventos já está em tratamento
- **WHEN** o handler recebe 5 eventos, sendo 2 vinculados a relatórios ativos e 3 novos
- **THEN** apenas os 3 eventos novos SHALL ser encaminhados para análise

#### Scenario: Evento reaparece após relatório CORRIGIDO
- **WHEN** um evento com UID já vinculado a relatório com status CORRIGIDO é recebido
- **THEN** o evento SHALL ser reanalisado e um novo relatório SHALL ser criado

#### Scenario: Evento vinculado a relatório COMPLETO
- **WHEN** um evento com UID já vinculado a relatório com status COMPLETO é recebido
- **THEN** o evento SHALL ser ignorado

#### Scenario: Evento vinculado a relatório INCOMPLETO
- **WHEN** um evento com UID já vinculado a relatório com status INCOMPLETO é recebido
- **THEN** o evento SHALL ser ignorado

### Requirement: Resiliência na consulta de deduplicação
O sistema SHALL tratar indisponibilidade do banco de dados durante a consulta de deduplicação sem disparar análise. Eventos SHALL ser reprocessados no próximo ciclo.

#### Scenario: Banco indisponível para consulta de deduplicação
- **WHEN** o PostgreSQL está indisponível no momento da consulta de deduplicação
- **THEN** o handler SHALL registrar erro no log, SHALL NOT disparar análise e os eventos SHALL ser reprocessados no próximo ciclo de coleta
