## MODIFIED Requirements

### Requirement: Notificação Discord após análise completa
O sistema SHALL enviar uma notificação no Discord após a persistência bem-sucedida de um relatório com status `COMPLETO`. A mesma função `send_discord_notification` SHALL ser reutilizada para notificar o resultado da correção, recebendo o resumo adequado ao contexto (análise ou correção). A mensagem SHALL conter: ID do relatório, resumo e link funcional para o relatório na interface web.

#### Scenario: Relatório completo com Discord configurado
- **WHEN** um relatório é finalizado com status `COMPLETO` e as variáveis `DISCORD_BOT_TOKEN` e `DISCORD_CHANNEL_ID` estão configuradas
- **THEN** o sistema envia mensagem no canal Discord com ID do relatório, resumo e link `{APP_BASE_URL}/reports/{id}`

#### Scenario: Correção concluída com sucesso
- **WHEN** a correção é finalizada com status `CORRIGIDO`
- **THEN** o sistema envia notificação Discord reutilizando `send_discord_notification` com resumo do resultado da correção

#### Scenario: Correção com falha
- **WHEN** a correção é finalizada com status `FALHA_CORRECAO`
- **THEN** o sistema envia notificação Discord reutilizando `send_discord_notification` com resumo da falha
