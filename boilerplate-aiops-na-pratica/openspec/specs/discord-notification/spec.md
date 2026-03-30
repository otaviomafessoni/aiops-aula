## ADDED Requirements

### Requirement: Notificação Discord após análise completa
O sistema SHALL enviar uma notificação no Discord após a persistência bem-sucedida de um relatório com status `COMPLETO`. A mensagem SHALL conter: ID do relatório, resumo da causa raiz e link funcional para o relatório na interface web. A mensagem SHALL ser em texto simples (sem embed). Relatórios com status `INCOMPLETO` não SHALL gerar notificação.

#### Scenario: Relatório completo com Discord configurado
- **WHEN** um relatório é finalizado com status `COMPLETO` e as variáveis `DISCORD_BOT_TOKEN` e `DISCORD_CHANNEL_ID` estão configuradas
- **THEN** o sistema envia mensagem no canal Discord com ID do relatório, resumo e link `{APP_BASE_URL}/reports/{id}`

#### Scenario: Relatório incompleto
- **WHEN** um relatório é finalizado com status `INCOMPLETO`
- **THEN** o sistema não envia notificação Discord

### Requirement: Configuração via variáveis de ambiente
O sistema SHALL usar as variáveis de ambiente `DISCORD_BOT_TOKEN`, `DISCORD_CHANNEL_ID` e `APP_BASE_URL` para configuração do bot Discord. `APP_BASE_URL` SHALL ter valor padrão `http://localhost:8000`.

#### Scenario: Todas as variáveis configuradas
- **WHEN** `DISCORD_BOT_TOKEN`, `DISCORD_CHANNEL_ID` e `APP_BASE_URL` estão definidas
- **THEN** o sistema utiliza os valores configurados para envio de notificações

#### Scenario: Variáveis Discord não configuradas
- **WHEN** `DISCORD_BOT_TOKEN` ou `DISCORD_CHANNEL_ID` não estão definidas e ocorre tentativa de envio
- **THEN** o sistema loga `WARNING` e não envia a notificação

### Requirement: Retry com backoff exponencial
O sistema SHALL implementar retry com backoff exponencial para envio de notificações Discord: 3 tentativas com intervalos de 1s, 2s e 4s. Após esgotar as tentativas, o sistema SHALL logar o erro e continuar normalmente sem bloquear o fluxo de análise.

#### Scenario: Discord API temporariamente indisponível
- **WHEN** o envio da notificação falha nas primeiras tentativas mas funciona na terceira
- **THEN** o sistema retenta com backoff exponencial e envia a notificação com sucesso

#### Scenario: Discord API totalmente indisponível
- **WHEN** o envio da notificação falha em todas as 3 tentativas
- **THEN** o sistema loga o erro e continua normalmente sem bloquear o fluxo

### Requirement: Resiliência a falhas de token pós-startup
O sistema SHALL continuar tentando enviar notificações mesmo se o token Discord for invalidado após o startup. Cada falha SHALL ser logada silenciosamente sem desabilitar o mecanismo de notificação.

#### Scenario: Token invalidado após startup
- **WHEN** o token Discord é invalidado depois que a aplicação iniciou
- **THEN** o sistema falha silenciosamente a cada tentativa de envio e loga o erro
