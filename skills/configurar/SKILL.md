---
name: configurar
description: "Use para configurar o mktOS Mídia pela primeira vez ou reconfigurar um workspace existente — onboarding guiado passo a passo, conexão de MCPs, criação de estrutura no Google Drive/ClickUp e cadastro do primeiro cliente."
---

# /mktos:configurar

## Propósito

Ponto de entrada do sistema para novos usuários e hub de reconfiguração para usuários existentes. No primeiro uso, guia o profissional através de 7 etapas para ter o plugin 100% operacional em menos de 10 minutos — workspace criado, MCPs conectados, primeiro cliente cadastrado. Em usos subsequentes, exibe o status atual e oferece acesso rápido ao que precisa ser ajustado.

## Processo

1. **Detecte o estado do workspace**: Verifique se `./data/workspace.json` existe.

   - **Existe → Modo Reconfiguração**: Leia o arquivo e exiba o status atual:

     > **Workspace:** {nome} ({tipo})
     > **Email admin:** {email}
     > **Moeda padrão:** {moeda}
     > **Clientes cadastrados:** {N}
     > **Integrações ativas:** {lista}
     >
     > O que você quer reconfigurar?
     > 1. Adicionar ou trocar cliente ativo (`/mktos:conta`)
     > 2. Reconectar ou testar MCPs
     > 3. Atualizar dados do workspace
     > 4. Recomeçar onboarding do zero

     Aguarde a escolha e execute a ação correspondente. Para opções 1–3, execute o sub-fluxo específico abaixo. Para opção 4, prossiga com o onboarding completo ignorando o arquivo existente.

   - **Não existe → Modo Onboarding**: Prossiga com as etapas abaixo.

---

### Onboarding Completo (primeira vez)

2. **Etapa 1 — Dados do workspace**:

   Apresente e aguarde resposta para cada campo:
   > "Vamos configurar seu workspace do mktOS Mídia. Algumas perguntas rápidas:"
   > - **Nome do workspace** (ex: "Minha Agência", "João Silva Mídia"):
   > - **Email do administrador**:
   > - **Moeda padrão**: BRL (Real) / USD (Dólar) / EUR (Euro)?

   Armazene as respostas — serão usadas para criar `workspace.json` na etapa 7.

3. **Etapa 2 — Perfil de uso**:

   > "Qual é o seu perfil de trabalho?"
   >
   > 1. 🏢 **Empresa** — Gerencio mídia para a minha própria empresa. Uma conta, foco operacional.
   > 2. 🧑‍💻 **Freela** — Atendo alguns clientes de forma autônoma. Poucos clientes, pouca burocracia.
   > 3. 🦸 **Eu-gência** — Sou solo mas opero como agência. Múltiplos clientes, processos estruturados.
   > 4. 🏭 **Agência** — Equipe, múltiplos clientes, SOPs, relatórios recorrentes.

   Armazene o perfil — determina as etapas e sugestões de estrutura seguintes.

4. **Etapa 3 — Estrutura sugerida**:

   Exiba a estrutura de organização recomendada para o perfil escolhido:

   **Empresa:**
   ```
   Google Drive/
   └── Mídia/
       ├── Google Ads/
       │   └── [Nome da Empresa]/
       └── Meta Ads/
           └── [Nome da Empresa]/
   ```

   **Freela:**
   ```
   Google Drive/
   └── Clientes/
       └── [Cliente]/
           ├── Google Ads/
           └── Meta Ads/
   ```

   **Eu-gência / Agência:**
   ```
   Google Drive/
   └── Clientes/
       ├── [Cliente A]/
       │   ├── Google Ads/
       │   ├── Meta Ads/
       │   └── Relatórios/
       └── [Cliente B]/
   SOPs/
   Templates/
   ```

   Pergunte: "Quer que eu crie essa estrutura no seu Google Drive agora?"

5. **Etapa 4 — Google Drive** (se confirmado):

   Use MCP `google-drive-designlab` para criar as pastas da estrutura sugerida. Apresente os links das pastas criadas ao concluir. Se o MCP não estiver conectado, avise e pule para a próxima etapa — a pasta pode ser criada manualmente depois.

6. **Etapa 5 — Ferramenta de tarefas**:

   > "Qual ferramenta você usa para gestão de tarefas?"
   > 1. **ClickUp** — Criar lista "mktOS - Operacional" no workspace conectado
   > 2. **Trello** — Criar quadro "mktOS Operacional" com listas: A fazer / Em andamento / Concluído
   > 3. **Nenhuma** — Pular esta etapa

   Se ClickUp: use MCP `clickup-midify` para criar a lista. Se Trello: use MCP `trello` para criar o quadro. Se nenhuma: pule.

7. **Etapa 6 — Conexão de MCPs**:

   Execute `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/setup-mktos.py" --action check-deps` para verificar dependências Python.

   Em seguida, verifique quais MCPs estão respondendo tentando uma operação de leitura simples em cada um. Apresente o status:

   | MCP | Status | Ação |
   |-----|--------|------|
   | google-ads | 🟢 Conectado / 🔴 Offline | — / Ver instruções |
   | meta-marketing | 🟢 / 🔴 | — / Ver instruções |
   | google-calendar-guroo | 🟢 / 🔴 | — / Ver instruções |
   | clickup-midify | 🟢 / 🔴 | — / Ver instruções |
   | gmail-guroo | 🟢 / 🔴 | — / Ver instruções |
   | google-drive-designlab | 🟢 / 🔴 | — / Ver instruções |

   Para qualquer MCP offline, instrua: "Para ativar o `{mcp}`, acesse **Configurações → Extensões → Plugins** no Claude Code e insira sua chave de API. Consulte `docs/README.md` para instruções detalhadas por integração."

   Mínimo necessário para operar: `google-ads` OU `meta-marketing` (pelo menos um de mídia paga).

8. **Etapa 7 — Primeiro cliente**:

   > "Agora vamos cadastrar seu primeiro cliente (ou a sua própria empresa, se for o caso)."
   > - **Nome completo** (ex: "Empresa Ltda"):
   > - **Slug** — identificador curto, sem espaços ou acentos (ex: "rede-daltro"):
   > - **Google Ads ID** (opcional, pode preencher depois):
   > - **Meta Ad Account ID** (opcional, pode preencher depois):
   > - **Orçamento mensal de mídia** (em {moeda}):
   > - **Canais ativos**: Google Ads / Meta / TikTok / LinkedIn (selecione os que usa)
   > - **Vertical / Setor** (ex: educação, varejo, saúde, b2b):

   Execute:
   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/gerenciar-contas.py" \
     --action adicionar \
     --slug "{slug}" \
     --nome "{nome}"
   ```
   Em seguida, troque para esta conta:
   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/gerenciar-contas.py" \
     --action trocar \
     --slug "{slug}"
   ```
   Salve os dados adicionais (Google Ads ID, Meta ID, orçamento, canais, vertical) diretamente em `./data/clientes/{slug}/perfil.json`.

9. **Criar `workspace.json`**: Execute via `setup-mktos.py`:
   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/setup-mktos.py" --action init
   ```
   Em seguida, atualize o arquivo com os dados coletados nas etapas anteriores (nome, tipo, email, moeda, integrações ativas).

10. **Exibir resumo de conclusão**:

    > ✅ **mktOS Mídia configurado com sucesso!**
    >
    > **Workspace:** {nome} · **Tipo:** {tipo} · **Cliente ativo:** {slug}
    >
    > **Próximos comandos para começar:**

    Adapte a lista ao perfil escolhido:

    **Empresa / Freela:**
    ```
    /mktos:plano       → Criar plano de mídia
    /mktos:keywords    → Pesquisar palavras-chave
    /mktos:relatorio   → Ver performance atual
    ```

    **Eu-gência / Agência:**
    ```
    /mktos:conta       → Gerenciar clientes
    /mktos:plano       → Criar plano de mídia
    /mktos:relatorio   → Relatório para cliente
    /mktos:saude       → Dashboard de criativos
    ```

    > 💡 Para adicionar mais clientes: `/mktos:conta adicionar`
    > 📚 Documentação completa: `docs/README.md`

## Agentes Usados

Nenhum agente especializado — este é um fluxo de configuração conduzido diretamente.

## Notas de Segurança

- **Nunca solicite ou armazene senhas, tokens de API ou credenciais** no `workspace.json` ou em qualquer arquivo criado por esta skill. Credenciais ficam exclusivamente nos arquivos de configuração dos MCPs (`.mcp.json`).
- O `workspace.json` contém apenas metadados do workspace — nome, tipo, email, preferências.
- Aprovação obrigatória antes de qualquer criação de pasta no Google Drive ou lista no ClickUp.
