# Fluxo de Mídia Paga — mktOS Mídia

Diagrama, mapeamento de comandos e integrações do loop core de tráfego pago.

---

## Diagrama do Fluxo Completo

```
┌─────────────────────────────────────────────────────────────────────┐
│                        LOOP CORE DE MÍDIA                           │
└─────────────────────────────────────────────────────────────────────┘

  CONTEXTO          PLANEJAMENTO        EXECUÇÃO         OTIMIZAÇÃO
  ─────────         ────────────        ─────────        ──────────

  /mktos:conta   ──▶  /mktos:plano     ──▶  /mktos:lançar ──▶  /mktos:pacing
  /mktos:conta        (plano de          (campanha         (dashboard de
   status           mídia paga)         PAUSADA)          orçamento)
                                                              │
                         ▲                                    │
                         │                                    ▼
                         └──────────────────────────  /mktos:orçamento
                                                       (realocação
                                                        otimizada)


  CRIATIVO (Sprint 7)     AUDIENCE (Sprint 8)     RASTREAMENTO (Sprint 9)
  ────────────────────    ───────────────────     ──────────────────────
  /mktos:materiais          /mktos:keywords           /mktos:rastreamento
  /mktos:criativo           /mktos:publico            /mktos:links
  /mktos:saude


  RELATÓRIO (Sprint 10)   ONBOARDING (Sprint 11)  AVANÇADO (Sprint 12)
  ─────────────────────   ──────────────────────  ────────────────────
  /mktos:relatorio          /mktos:configurar         /mktos:retargeting
                          /mktos:conectar           /mktos:negativos
```

---

## Mapeamento: Etapa → Comando → Agente → Script

### 1. Gestão de Conta

| Etapa | Comando | Agente | Script |
|---|---|---|---|
| Listar clientes | `/mktos:conta listar` | — | `gerenciar-contas.py --action listar` |
| Trocar cliente ativo | `/mktos:conta trocar {slug}` | — | `gerenciar-contas.py --action trocar` |
| Adicionar cliente | `/mktos:conta adicionar` | — | `gerenciar-contas.py --action adicionar` |
| Ver status do cliente | `/mktos:conta status` | — | `gerenciar-contas.py --action status` |

### 2. Planejamento de Mídia

| Etapa | Comando | Agente | Scripts |
|---|---|---|---|
| Criar plano de mídia | `/mktos:plano` | `media-buyer` | `rastreador-campanhas.py`, `log-tarefas.py` |
| Verificar datas de voo | (interno ao plano) | `media-buyer` | MCP `google-calendar-guroo` |
| Registrar tarefas do plano | (interno ao plano) | — | `log-tarefas.py --action log` |

### 3. Lançamento de Campanha

| Etapa | Comando | Agente | Scripts |
|---|---|---|---|
| Lançar campanha | `/mktos:lançar` | `media-buyer` + `execution-coordinator` | `gerenciador-aprovacao.py`, `rastreador-execucao.py`, `rastreador-campanhas.py` |
| Buscar assets | (interno ao lançar) | `media-buyer` | MCP `clickup-midify` ou `trello` |
| Criar campanha PAUSADA | (interno ao lançar) | `execution-coordinator` | MCP `google-ads` ou `meta-marketing` |
| Atualizar tarefa ClickUp | (interno ao lançar) | `execution-coordinator` | MCP `clickup-midify` |
| Enviar confirmação | (interno ao lançar) | `execution-coordinator` | MCP `gmail-guroo` |
| Gerar UTMs | (interno ao lançar) | `media-buyer` | `gerador-utm.py` |

### 4. Monitoramento de Pacing

| Etapa | Comando | Agente | Scripts |
|---|---|---|---|
| Dashboard de orçamento | `/mktos:pacing` | `monitor-performance` + `media-buyer` | `controlador-pacing.py`, `monitor-performance.py` |
| Puxar dados das plataformas | (interno ao pacing) | `monitor-performance` | MCP `google-ads`, `meta-marketing` |
| Alerta crítico por email | (interno ao pacing) | `monitor-performance` | MCP `gmail-guroo` |
| Salvar snapshot | (interno ao pacing) | `monitor-performance` | `monitor-performance.py --action save-snapshot` |

### 5. Otimização de Orçamento

| Etapa | Comando | Agente | Scripts |
|---|---|---|---|
| Otimizar alocação | `/mktos:orçamento` | `analytics-analyst` + `media-buyer` | `otimizador-orcamento.py`, `calculadora-roi.py` |
| Calcular eficiência por canal | (interno ao orçamento) | `analytics-analyst` | `otimizador-orcamento.py` |
| Projetar melhoria de ROI | (interno ao orçamento) | `analytics-analyst` | `previsao-receita.py` |
| Registrar realocações no work-log | (interno ao orçamento) | — | `log-tarefas.py --action log` |

---

## Integrações por Etapa do Fluxo

| Integração MCP | Usado em |
|---|---|
| `google-ads` | `/mktos:lançar`, `/mktos:pacing`, `/mktos:orçamento` |
| `meta-marketing` | `/mktos:lançar`, `/mktos:pacing`, `/mktos:orçamento` |
| `clickup-midify` | `/mktos:lançar` (busca assets + update pós-lançamento) |
| `trello` | `/mktos:lançar` (alternativa ao ClickUp para assets) |
| `google-calendar-guroo` | `/mktos:plano` (verificação de datas de voo) |
| `gmail-guroo` | `/mktos:lançar` (confirmação), `/mktos:pacing` (alertas críticos) |
| `slack` | Todos (alertas opcionais de performance) |
| `google-drive-designlab` | Futuramente `/mktos:materiais` (acesso a assets) |
| `canva` | Futuramente `/mktos:criativo` (geração de criativos) |

---

## Fluxo de Aprovação Obrigatória

Toda operação de escrita em plataforma externa passa pelo fluxo:

```
Agente prepara ação
        │
        ▼
gerenciador-aprovacao.py ──▶ Cria registro de aprovação com risco
        │
        ▼
Apresenta Resumo de Execução ao usuário
        │
        ▼
Aguarda aprovação explícita ("sim" / "pode lançar" / "confirmo")
        │
        ▼
Executa via MCP (campanha sempre em status PAUSED)
        │
        ▼
rastreador-execucao.py ──▶ Registra resultado com timestamp
        │
        ▼
Atualiza ClickUp + Envia email de confirmação
```

Nenhuma etapa pode ser pulada. O hook `PreToolUse mcp_.*` bloqueia qualquer chamada de escrita que não tenha aprovação explícita na conversa atual.

---

## Ciclo de Vida de uma Campanha

```
PLANO          LANÇAMENTO     MONITORAMENTO    OTIMIZAÇÃO
  │                │               │               │
  ▼                ▼               ▼               ▼
/mktos:plano    /mktos:lançar     /mktos:pacing     /mktos:orçamento
  │                │               │               │
  │                ▼               │               │
  │          status: PAUSED         │               │
  │          (revisar na            │               │
  │           plataforma)           │               │
  │                │               │               │
  │          ativar manualmente     │               │
  │          (fora do plugin)       │               │
  │                │               │               │
  └────────────────┴───────────────┴───────────────┘
                        log-tarefas.py
                  (trilha de auditoria contínua)
```

---

## Scripts do Loop Core

| Script | Função | Usado em |
|---|---|---|
| `gerenciar-contas.py` | CRUD de clientes e conta ativa | `/mktos:conta` |
| `gerenciador-aprovacao.py` | Ciclo de aprovação pré-execução | `/mktos:lançar` |
| `rastreador-execucao.py` | Trilha de auditoria de execuções | `/mktos:lançar` |
| `rastreador-campanhas.py` | Histórico de campanhas e insights | `/mktos:plano`, `/mktos:lançar`, `/mktos:orçamento` |
| `controlador-pacing.py` | Cálculo de pacing de orçamento | `/mktos:pacing` |
| `otimizador-orcamento.py` | Otimização de alocação por canal | `/mktos:orçamento`, `/mktos:pacing` |
| `monitor-performance.py` | Snapshots e detecção de anomalias | `/mktos:pacing` |
| `calculadora-roi.py` | Cálculo de ROI por canal | `/mktos:orçamento` |
| `previsao-receita.py` | Projeção de receita | `/mktos:orçamento` |
| `gerador-utm.py` | Geração e validação de UTMs | `/mktos:lançar` |
| `log-tarefas.py` | Log de tarefas e atividades | Todos |
