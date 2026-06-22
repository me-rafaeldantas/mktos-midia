---
name: conta
description: "Use para gerenciar contas do workspace: listar clientes, trocar o contexto ativo, adicionar novo cliente ou verificar o status da conta atual. Trigger: /mktos:conta, /mktos:conta listar, /mktos:conta trocar, /mktos:conta adicionar, /mktos:conta status, trocar cliente, ver conta ativa, qual cliente está ativo, adicionar novo cliente."
argument-hint: "[listar | trocar {slug} | adicionar | status]"
---

# /mktos:conta

## Propósito

Gerenciar o workspace e as sub-contas do mktOS Mídia. Permite listar clientes cadastrados, trocar o cliente ativo (contexto de todos os próximos comandos), adicionar um novo cliente e verificar os dados da conta atualmente ativa.

## Verificação Inicial (todos os sub-comandos)

Antes de qualquer sub-ação, verificar se `./data/workspace.json` existe:
- Se **não existe**: informar que o workspace não está configurado e orientar: "Execute `/mktos:configurar` para criar o workspace e configurar o primeiro cliente."
- Se **existe**: prosseguir com a sub-ação solicitada.

## Sub-ações

### `/mktos:conta listar`

**Propósito:** Listar todos os clientes cadastrados no workspace com status resumido.

**Processo:**
1. Executar `python3 scripts/gerenciar-contas.py --action listar`
2. Exibir tabela com: Nome, Slug, Google Ads ID, Meta Ad Account, Campanhas registradas
3. Destacar qual cliente está ativo no momento com indicador visual (★ ou **[ATIVO]**)
4. Se não houver clientes: orientar a usar `/mktos:conta adicionar`

**Output esperado:**
```
Clientes no workspace Minha Agência:

★ Cliente Alpha              cliente-alpha     Google Ads: 1234567890   Meta: act_111111   3 campanhas
  Cliente Beta                cliente-beta      Google Ads: não config.  Meta: não config.  0 campanhas

Total: 2 clientes  |  Ativo: Cliente Alpha
```

---

### `/mktos:conta trocar {slug}`

**Propósito:** Trocar o cliente ativo — todos os próximos comandos `/mktos:` operarão neste cliente.

**Processo:**
1. Verificar se o slug fornecido existe em `./data/clientes/`
2. Se não existe: listar os slugs disponíveis e sugerir o correto
3. Executar `python3 scripts/gerenciar-contas.py --action trocar --slug {slug}`
4. Confirmar a troca com resumo do novo cliente ativo

**Output esperado:**
```
Contexto alterado ✓

Cliente ativo: Cliente Alpha
Slug: cliente-alpha
Google Ads ID: 1234567890
Meta Ad Account: act_111111111
Campanhas registradas: 3
Integrações disponíveis: google-ads, meta-marketing, clickup-midify

Todos os próximos comandos /mktos: operarão com os dados de Cliente Alpha.
```

---

### `/mktos:conta adicionar`

**Propósito:** Cadastrar um novo cliente no workspace com coleta interativa de dados.

**Processo:**
1. Verificar que workspace está configurado
2. Perguntar interativamente:
   - Nome completo do cliente: ex. "Clínica Exemplo" ou "Loja Exemplo Ltda"
   - Slug (sugerir automaticamente a partir do nome, ex: "clinica-exemplo"): confirmar ou editar
   - Google Ads ID (opcional — pode ser configurado depois)
   - Meta Ad Account ID (opcional — pode ser configurado depois, formato act_XXXXXX)
   - Moeda principal do cliente (padrão: BRL)
3. Executar: `python3 scripts/gerenciar-contas.py --action adicionar --slug {slug} --nome "{nome}" [--google-ads-id {id}] [--meta-account {id}]`
4. Perguntar se deseja já trocar para o novo cliente: se sim, executar `--action trocar`
5. Orientar próximos passos: "Configure os KPIs e orçamento do cliente em `/mktos:configurar` ou prossiga com `/mktos:plano`"

**Output esperado:**
```
Cliente adicionado ✓

Clínica Exemplo
Slug: clinica-exemplo
Diretórios criados:
  ./data/clientes/clinica-exemplo/campanhas/
  ./data/clientes/clinica-exemplo/criativos/
  ./data/clientes/clinica-exemplo/performance/

Deseja trocar para este cliente agora? (s/n)
```

---

### `/mktos:conta status`

**Propósito:** Exibir todos os dados do cliente ativo — visão rápida antes de iniciar qualquer operação.

**Processo:**
1. Executar `python3 scripts/gerenciar-contas.py --action status`
2. Se nenhuma conta ativa: orientar `/mktos:conta trocar {slug}`
3. Exibir painel completo do cliente ativo

**Output esperado:**
```
Conta Ativa: Cliente Alpha (cliente-alpha)
Trocado em: 11/06/2026 às 10:00

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Plataformas
  Google Ads ID:    1234567890
  Meta Ad Account:  act_111111111
  Canais ativos:    google-search, meta-feed, meta-stories
  Moeda:            BRL

KPIs Configurados
  ROAS alvo:        4.0x
  CPA alvo:         R$ 80,00
  Orçamento mensal: R$ 10.000,00

Campanhas registradas: 2
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Workspace: Minha Agência (agência)
Integrações disponíveis: google-ads, meta-marketing, clickup-midify, gmail-guroo, google-calendar-guroo, trello
```

## Agentes Usados

Nenhum agente especialista é invocado neste skill — é uma operação de gestão de contexto executada diretamente pelo coordenador.

## Integração Work Log

Não registrar no work log — troca de conta é uma operação de navegação, não uma atividade de campanha.
