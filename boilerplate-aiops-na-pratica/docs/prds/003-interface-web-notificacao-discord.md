---
prd_number: "003"
status: implementado
priority: alta
created: 2026-03-22
issue:
depends_on: ["002"]
references: []
---

# PRD 003: Interface Web de Relatórios e Notificação via Discord

## 1. Contexto

- **Sistema/produto**: Agente AIOps para Kubernetes — aplicação Python com FastAPI. O PRD 002 gera relatórios de análise de causa raiz e os persiste no PostgreSQL. Stack: Python, FastAPI, Jinja2, PostgreSQL, Discord API.
- **Estado atual**: Os relatórios são gerados e armazenados no banco, mas não há forma de visualizá-los nem de ser notificado quando um novo relatório é criado. O operador precisaria consultar o banco diretamente para acessar os resultados da análise.
- **Problema**: Sem interface de visualização, os relatórios não chegam a quem precisa agir. Sem notificação proativa, a equipe não sabe que um problema foi identificado até que alguém consulte o sistema manualmente — anulando o benefício da automação.

## 2. Solução Proposta

### Visão geral

- Interface web server-side renderizada com Jinja2 pela própria API FastAPI
- Página de listagem com todos os relatórios e seus status
- Página de detalhe com renderização do Markdown completo e botão para acionar correção (PRD 004)
- Bot Discord que envia notificação automática após a geração de cada relatório de análise
- A notificação contém o ID do problema e link direto para o relatório na interface web

### Decisões-chave

1. **Jinja2 para interface web** — Interface server-side renderizada pela própria API FastAPI, sem necessidade de frontend separado (React, Vue, etc.)
2. **Sem autenticação na v1** — Não haverá controle de acesso. Decisão aceita para simplificar a primeira entrega.
3. **Discord como canal de notificação** — Canal já utilizado pela equipe de operações; configuração via variáveis de ambiente (token do bot e ID do canal).

### Fora do escopo

- **Autenticação e autorização** — Não contemplado nesta versão
- **Filtros avançados ou busca na listagem** — Listagem simples sem paginação ou filtro
- **Dashboard com métricas agregadas** — Apenas listagem e detalhe de relatórios
- **Execução da correção** — O botão aciona o agente do PRD 004; a lógica de correção não é responsabilidade deste PRD
- **Notificação de resultado de correção** — Responsabilidade do PRD 004

## 3. Funcionalidades

### US01: Listagem de relatórios

Como engenheiro de plataforma, quero acessar uma página web com a listagem de todos os relatórios de análise, para ter visibilidade do histórico de problemas investigados no cluster.

**Rules:**
- A página exibe todos os relatórios ordenados por data de criação (mais recente primeiro)
- Cada item da lista exibe: ID, data de criação, status e resumo (primeiras linhas da causa raiz)
- Cada item é clicável e leva à página de detalhe
- A página é servida pela própria API FastAPI com template Jinja2

**Edge cases:**
- Nenhum relatório no banco → exibir página com mensagem informativa ("Nenhum relatório encontrado")
- Erro de conexão com o PostgreSQL → exibir página de erro genérica com mensagem amigável

### US02: Visualização detalhada do relatório

Como engenheiro de plataforma, quero visualizar o conteúdo completo de um relatório, para avaliar a causa raiz identificada e os passos de correção recomendados.

**Rules:**
- A página renderiza o conteúdo Markdown completo do relatório em HTML
- Exibe o status atual do relatório
- Inclui botão "Executar correção" que aciona o agente de correção (PRD 004)
- O botão de correção só é exibido para relatórios com status COMPLETO

**Edge cases:**
- Relatório com Markdown malformado → renderizar o que for possível, sem quebrar a página
- Relatório não encontrado (ID inválido) → retornar página 404 com mensagem informativa
- Usuário clica em "Executar correção" com correção já em andamento para o mesmo relatório → botão desabilitado com texto "Correção em andamento..."
- PRD 004 ainda não implementado → botão visível mas desabilitado com alerta informando que a funcionalidade será implementada futuramente

### US03: Notificação no Discord após análise

Como engenheiro DevOps, quero receber notificação no Discord quando um novo relatório de análise for gerado, para tomar conhecimento do problema rapidamente sem monitorar a interface web.

**Rules:**
- A notificação é enviada após a persistência bem-sucedida do relatório no banco
- A mensagem contém: ID do problema, resumo da causa raiz e link funcional para o relatório na interface web
- A configuração do bot Discord (token e canal) é feita via variáveis de ambiente (`DISCORD_BOT_TOKEN`, `DISCORD_CHANNEL_ID`)
- A URL base da interface web é configurável via variável de ambiente (`APP_BASE_URL`)

**Edge cases:**
- Discord API indisponível → retry com backoff exponencial (3 tentativas: 1s → 2s → 4s); após falha, registrar no log e continuar normalmente (a análise não deve ser bloqueada pela notificação)
- Token do bot inválido ou canal inexistente após startup → falhar silenciosamente a cada tentativa de envio e logar o erro
- Link do relatório inacessível (interface web fora do ar) → a notificação é enviada normalmente; o link pode ser acessado quando a interface voltar
- Variáveis de ambiente do Discord não configuradas → logar `WARNING` a cada tentativa de envio e não enviar a notificação

## 4. Critérios de Aceite

### Técnicos

| Critério | Método de verificação |
|----------|----------------------|
| Interface web lista todos os relatórios com status | Teste manual em navegador |
| Página de detalhe renderiza Markdown completo | Teste manual com relatórios de diferentes complexidades |
| Botão de correção aparece apenas para relatórios COMPLETO | Teste manual com relatórios em diferentes status |
| Notificação enviada no Discord com ID e link funcional | Teste manual com bot em canal de teste |
| Notificação não bloqueia o fluxo de análise em caso de falha | Teste simulando Discord indisponível |

### De negócio

| Métrica | Baseline (fonte) | Meta | Prazo | Mín. aceitável | Responsável |
|---------|-------------------|------|-------|-----------------|-------------|
| Tempo entre geração do relatório e conhecimento pela equipe | Indeterminado — equipe descobre manualmente | < 1 minuto (notificação automática) | Na entrega do milestone | < 5 minutos | Time de SRE |

## 5. Milestones

### Milestone 1: Implementar Interface Web

**Objetivo:** Permitir visualização dos relatórios via navegador.

**Funcionalidades:** US01, US02

- [ ] Criar template Jinja2 de listagem de relatórios (US01)
- [ ] Criar rota FastAPI para listagem (`GET /reports`) (US01)
- [ ] Criar template Jinja2 de detalhe do relatório com renderização Markdown (US02)
- [ ] Criar rota FastAPI para detalhe (`GET /reports/{id}`) (US02)
- [ ] Adicionar botão "Executar correção" com controle de estado (US02)
- [ ] Tratar cenários de erro (banco indisponível, relatório não encontrado) (US01, US02)

**Critério de conclusão:**
- Condição: Interface web exibe listagem e detalhe dos relatórios corretamente
- Verificação: Demo em navegador com relatórios reais gerados pelo PRD 002
- Aprovador: Time de SRE

### Milestone 2: Implementar Notificação Discord

**Objetivo:** Equipe é notificada automaticamente quando um relatório é gerado.

**Funcionalidades:** US03

- [ ] Implementar integração com Discord API via bot (US03)
- [ ] Configurar via variáveis de ambiente (token, canal, URL base) (US03)
- [ ] Formatar mensagem com ID, resumo e link (US03)
- [ ] Implementar retry com backoff e fallback silencioso (US03)
- [ ] Tratar ausência de configuração (desabilitar graciosamente) (US03)

**Critério de conclusão:**
- Condição: Após geração de relatório, notificação é enviada no Discord com link funcional
- Verificação: Teste com bot em canal de teste do Discord
- Aprovador: Time de SRE

## 6. Riscos e Dependências

| Risco | Impacto | Mitigação | Status |
|-------|---------|-----------|--------|
| Interface sem autenticação exposta indevidamente | Médio | Restringir acesso via rede (VPN, ingress interno). Documentar que v1 não tem auth | Pendente |
| Discord API muda ou bot é desativado | Baixo | Monitorar logs de falha de notificação. Notificação é best-effort, não bloqueia fluxo | Pendente |

**Dependências:**

| Dependência | Tipo | Status | Impacto se bloqueado |
|-------------|------|--------|----------------------|
| PRD 002 — Relatórios no PostgreSQL | Interna | Em desenvolvimento | Sem relatórios, não há o que exibir ou notificar |
| Jinja2 | Externa | Disponível | Renderização dos templates |
| Biblioteca `markdown` (Python) para renderização Markdown → HTML | Externa | Disponível | Necessária para exibir relatórios formatados |
| Bot Discord (token + canal) | Interna | A configurar | Sem bot, notificações não são enviadas |

## 7. Referências

- [PRD 002 - Agente de Análise](./002-agente-analise-causa-raiz.md) — fornece os relatórios exibidos e notificados
- [PRD 004 - Agente de Correção](./004-agente-correcao-automatica.md) — acionado pelo botão de correção na interface
- [Discord Developer Portal](https://discord.com/developers/docs/intro) — documentação da API do Discord para bots

## 8. Registro de Decisões

- **2026-03-22:** Interface web e notificação Discord no mesmo PRD. Motivo: ambos são canais de entrega da informação ao usuário; faz sentido como unidade de entrega.
- **2026-03-22:** Notificação de resultado de correção fica no PRD 004. Motivo: cada PRD notifica no seu próprio fluxo.
- **2026-03-13:** Jinja2 para interface web. Motivo: server-side renderizada pela própria API, sem frontend separado.
- **2026-03-13:** Sem autenticação na v1. Motivo: simplicidade da primeira entrega.
- **2026-03-13:** Configuração do Discord via variáveis de ambiente. Motivo: simplicidade de deploy.
- **2026-03-29:** Biblioteca `markdown` (Python) escolhida para renderização Markdown → HTML. Motivo: leve, já disponível no projeto, suficiente com extensões `tables` e `fenced_code`.
- **2026-03-29:** Envio Discord via `httpx` (HTTP direto) em vez de `discord.py`. Motivo: notificação unidirecional, sem necessidade de gateway WebSocket.
- **2026-03-29:** Retry Discord: 3 tentativas com backoff exponencial (1s → 2s → 4s).
- **2026-03-29:** Token Discord invalidado pós-startup: falhar silenciosamente e logar erro a cada tentativa.
- **2026-03-29:** Variáveis Discord não configuradas: logar WARNING a cada tentativa de envio.
- **2026-03-29:** Mensagem Discord em texto simples (sem embed).
- **2026-03-29:** `APP_BASE_URL` com valor padrão `http://localhost:8000`.
- **2026-03-29:** Botão "Executar correção" visível mas desabilitado com alerta até PRD 004 ser implementado.
- **2026-03-29:** Correção em andamento: botão desabilitado com texto "Correção em andamento...".
- **2026-03-29:** Entrega sequencial: Milestone 1 (Web) primeiro, depois Milestone 2 (Discord).
