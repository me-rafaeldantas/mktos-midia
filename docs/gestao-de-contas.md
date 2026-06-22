# Gestão de Contas — mktOS Mídia

Como o mktOS Mídia organiza workspace, clientes e isolamento de contexto.

---

## Hierarquia do Workspace

```
Workspace (sua instalação)
└── Clientes (um por empresa anunciante)
    ├── perfil.json          ← dados, KPIs, orçamento, canais ativos
    ├── campanhas/           ← histórico de campanhas criadas
    ├── criativos/           ← assets e criativos aprovados
    └── performance/         ← snapshots históricos de performance
```

O workspace vive em `./data/` na sua máquina. **Nunca dentro do repositório do plugin** — seus dados de clientes ficam locais e privados.

---

## Arquivo _conta-ativa.json

O arquivo `./data/clientes/_conta-ativa.json` registra qual cliente está selecionado no momento:

```json
{
  "slug": "meu-cliente",
  "nome": "Nome da Empresa",
  "atualizado_em": "2026-06-11T10:30:00Z"
}
```

Cada skill e agente lê este arquivo primeiro. Toda análise, plano e execução usa os dados do cliente ativo — nunca mistura dados entre clientes.

---

## Comandos de Conta

### Listar todos os clientes
```
/mktos:conta listar
```
Exibe todos os clientes cadastrados com indicação de qual está ativo.

### Trocar o cliente ativo
```
/mktos:conta trocar meu-cliente
```
Atualiza `_conta-ativa.json` para o slug informado. Todos os comandos seguintes usarão este cliente.

### Adicionar novo cliente
```
/mktos:conta adicionar
```
O assistente vai pedir:
- **Nome completo**: ex. "Nome da Empresa"
- **Slug**: identificador único, apenas letras minúsculas, números e hífens (ex. `meu-cliente`)
- **Google Ads ID** (opcional): Customer ID da conta Google Ads
- **Meta Ad Account ID** (opcional): ID da conta de anúncios do Meta
- **Orçamento mensal**: teto de investimento em R$ para este cliente

### Ver status do cliente ativo
```
/mktos:conta status
```
Exibe: nome, slug, canais ativos, orçamento configurado, número de campanhas registradas e status das integrações MCP.

---

## Isolamento de Contexto

O isolamento é garantido por design — cada skill lê `_conta-ativa.json` antes de qualquer ação. Isso significa:

- `/mktos:pacing` no cliente A mostra só dados de A
- Trocar para o cliente B e rodar `/mktos:pacing` mostra só dados de B
- Nenhum dado de um cliente vaza para outro
- Scripts como `rastreador-campanhas.py` e `monitor-performance.py` usam o `--brand {slug}` para escopar todas as operações de leitura e escrita

**Para verificar o isolamento:**
```
/mktos:conta trocar cliente-a
/mktos:pacing

/mktos:conta trocar cliente-b
/mktos:pacing
```
Os dois dashboards devem mostrar dados completamente independentes.

---

## Estrutura de um Perfil de Cliente

O arquivo `./data/clientes/{slug}/perfil.json` criado pelo comando `/mktos:conta adicionar`:

```json
{
  "slug": "meu-cliente",
  "nome": "Nome da Empresa",
  "tipo": "cliente",
  "google_ads_id": "123-456-7890",
  "meta_ad_account": "act_1234567890",
  "orcamento_mensal": 15000,
  "canais_ativos": ["google_ads", "meta"],
  "modelo_negocio": "",
  "vertical": "educacao",
  "kpis": {
    "cpa_alvo": null,
    "roas_alvo": null,
    "cpl_alvo": null
  },
  "criado_em": "2026-06-11T10:30:00Z",
  "atualizado_em": "2026-06-11T10:30:00Z"
}
```

Você pode editar este arquivo diretamente para adicionar KPIs, ajustar orçamento ou atualizar canais ativos.

---

## Exemplos de Uso por Perfil

### Freela / Gestor Independente
Você gerencia 5 a 15 clientes. Cada cliente tem seu próprio slug. O fluxo diário é:

```
# Manhã — verificar pacing de todos os clientes
/mktos:conta trocar cliente-x && /mktos:pacing
/mktos:conta trocar cliente-y && /mktos:pacing

# Para um cliente específico — otimizar orçamento
/mktos:conta trocar cliente-z
/mktos:orçamento
```

### Agência com Equipe
O workspace compartilhado fica numa pasta comum. Cada gestor usa `/mktos:conta trocar` para alternar entre clientes atribuídos. O work-log registra todas as ações com `account_slug` para rastreabilidade por cliente.

### Empresa (Conta Única)
Geralmente um único cliente no workspace com o slug da empresa. O foco está em profundidade — múltiplas campanhas, criativos e histórico de performance.

### Eu-gência (Freelancer como Agência)
Mistura de clientes de terceiros e projetos próprios. Use slugs descritivos: `agencia-proprio`, `cliente-alpha`, `cliente-beta`. O isolamento garante que dados pessoais não apareçam em relatórios de clientes.

---

## Primeiro Uso — Fluxo Completo

1. **Inicializar workspace** (só na primeira vez):
   ```
   /mktos:configurar
   ```

2. **Adicionar primeiro cliente**:
   ```
   /mktos:conta adicionar
   ```

3. **Confirmar dados**:
   ```
   /mktos:conta status
   ```

4. **Começar a trabalhar**:
   ```
   /mktos:plano
   ```

Pronto. O workspace está configurado e o loop de mídia está disponível para este cliente.

---

## Localização dos Dados

| O que | Onde |
|---|---|
| Workspace raiz | `./data/workspace.json` |
| Cliente ativo | `./data/clientes/_conta-ativa.json` |
| Perfil do cliente | `./data/clientes/{slug}/perfil.json` |
| Campanhas | `./data/clientes/{slug}/campanhas/` |
| Criativos | `./data/clientes/{slug}/criativos/` |
| Performance | `./data/clientes/{slug}/performance/` |
| Work log | `./data/work-log/tasks.jsonl` |
| SOPs customizados | `./data/sops/` |

Todos os dados ficam na sua máquina local. O repositório do plugin não armazena nenhum dado de cliente.
