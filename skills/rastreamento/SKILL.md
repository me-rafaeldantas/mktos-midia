---
name: rastreamento
description: "Use quando o usuário precisar auditar a infraestrutura de rastreamento de uma conta — status de pixel Meta, ações de conversão Google Ads, eventos GA4, gaps de tracking, modelo de atribuição e checklist de implementação."
---

# /mktos:rastreamento

## Propósito

Auditar toda a infraestrutura de rastreamento de uma conta de mídia paga. Verifica pixel Meta, ações de conversão Google Ads, eventos GA4 e GTM em sequência, identifica o que está medindo errado ou não está medindo, mapeia divergências de atribuição entre plataformas e gera um checklist priorizado de correções. Rastreamento quebrado é budget invisível — sem tracking correto, não é possível otimizar lances nem provar resultado para o cliente.

## Entrada Necessária

O usuário deve fornecer (ou será solicitado):

- **Plataformas ativas**: quais estão rodando campanhas (Meta, Google, TikTok, LinkedIn)
- **ID da propriedade GA4** (se disponível): para cruzar eventos de conversão
- **Domínio do site**: para verificar se o pixel/tag está instalado corretamente
- **Conversões que importam**: quais eventos o cliente considera como resultado — lead, compra, ligação, visita à loja

## Processo

1. **Carregue contexto da conta**: Leia `./data/clientes/_conta-ativa.json` para obter o slug ativo, depois carregue `./data/clientes/{slug}/perfil.json`. Use `canais_ativos`, `google_ads_id`, `meta_ad_account` e `vertical` do perfil. Se nenhuma conta existir, pergunte: "Configurar uma conta primeiro (`/mktos:configurar`)?"

2. **Audite o Meta Pixel** (se Meta em `canais_ativos`): Via MCP `meta-marketing`:
   - Liste os pixels vinculados à conta: `get_account_info` para confirmar pixel IDs
   - Verifique se o pixel está ativo e recebendo eventos recentes
   - Identifique quais eventos estão disparando: `PageView`, `Lead`, `Purchase`, `InitiateCheckout`, `ViewContent`
   - Verifique se há Conversions API (CAPI) configurada — sem CAPI, dados iOS 14+ são parciais
   - Sinalize: pixel sem disparos nos últimos 7 dias (🔴), pixel ativo mas sem eventos de conversão (🟡), pixel + CAPI configurados (🟢)

3. **Audite as ações de conversão do Google Ads** (se Google em `canais_ativos`): Execute GAQL via MCP `google-ads`:
   ```sql
   SELECT
     conversion_action.name,
     conversion_action.status,
     conversion_action.type,
     conversion_action.counting_type,
     conversion_action.attribution_model_settings.attribution_model,
     conversion_action.view_through_lookback_window_days,
     conversion_action.click_through_lookback_window_days
   FROM conversion_action
   WHERE conversion_action.status != 'REMOVED'
   ```
   Para cada ação de conversão:
   - Status `ENABLED` e `Gravando` (receiving_conversions > 0 nos últimos 30 dias) → 🟢
   - Status `ENABLED` mas sem conversões recentes → 🟡 (tag instalada mas não disparando)
   - Status `HIDDEN` ou sem tag instalada → 🔴
   - Verifique se pelo menos uma ação está marcada como "conversão primária" (usada nos lances)

4. **Audite o GA4** em cascata — sem MCP disponível, guie o usuário para exportar os dados relevantes:

   **Nível 1 — Conversões importadas via Google Ads** (automático, sem input do usuário):
   Execute GAQL via MCP `google-ads` para identificar conversões que vieram do GA4:
   ```sql
   SELECT conversion_action.name, conversion_action.type
   FROM conversion_action
   WHERE conversion_action.type = 'GOOGLE_ANALYTICS_4_GOAL'
      OR conversion_action.type = 'GOOGLE_ANALYTICS_4_PURCHASE'
   ```
   Se houver resultados: GA4 já está alimentando o Google Ads — registre quais conversões e avance.

   **Nível 2 — Lista de Key Events colada pelo usuário** (se nenhuma conversão GA4 aparecer no nível 1):
   Solicite ao usuário:
   > "Preciso verificar seus Key Events no GA4. Acesse:
   > **GA4 → Administrador → Eventos** (coluna esquerda, ícone de engrenagem)
   > Na tabela de eventos, os marcados como 'Key event' têm um toggle azul na coluna direita.
   > Cole aqui a lista de nomes dos eventos marcados como Key Event."

   Com a lista recebida, verifique:
   - Há pelo menos um Key Event correspondente às conversões declaradas pelo usuário? → 🟢
   - Há Key Events cadastrados mas sem correspondência no Google Ads (não importados)? → 🟡 gap de importação
   - Nenhum Key Event cadastrado? → 🔴 GA4 não está medindo conversões

   Verifique também dupla contagem: se os Key Events do GA4 estão importados no Google Ads **e** há uma tag direta do Google Ads no site para o mesmo evento, a conversão está sendo contada duas vezes.

   **Nível 3 — Sem acesso ao GA4** (se o usuário não tiver acesso):
   Registre como "GA4: não auditado — sem acesso" no relatório e avance. Sinalize como gap de processo: quem gerencia mídia deve ter acesso de leitor ao GA4 no mínimo.

5. **Verifique GTM** em cascata — aplique o mesmo padrão guiado:

   Primeiro pergunte: "O site usa Google Tag Manager?" Se não → pule este step.

   **Nível 1 — Tags identificáveis pelo contexto** (automático):
   Com base nas ações de conversão do Google Ads (step 3) e no pixel Meta (step 2), infira se as tags provavelmente passam por GTM:
   - Conversion action com tipo `WEBPAGE` = tag instalada diretamente no site (GTM ou hardcode)
   - Se o pixel Meta está ativo mas sem CAPI = provavelmente GTM sem server-side

   **Nível 2 — Export do container GTM** (se o usuário tiver acesso):
   Solicite ao usuário:
   > "Para auditar o GTM, acesse:
   > **GTM → Administrador → Exportar container → versão mais recente → JSON**
   > Cole aqui apenas a seção `tags` do arquivo exportado (array de objetos com `name` e `type`)."

   Com o array de tags recebido, analise:
   - Quantas tags de conversão do Google Ads existem? Se mais de uma para o mesmo evento → risco de dupla contagem 🔴
   - Pixel Meta e evento de conversão Meta em tags separadas sem `firing condition` de exclusão mútua → 🟡
   - Tags sem trigger definido → 🔴 (tag morta, nunca dispara)
   - Container com versão não publicada (usuário menciona "rascunho não publicado") → 🔴 mudanças não estão ao vivo

   **Nível 3 — Sem acesso ao GTM**:
   Registre como "GTM: não auditado — sem acesso" e avance. Sinalize como gap de processo.

6. **Identifique gaps de rastreamento**: Com base nas conversões informadas pelo usuário, verifique o que está faltando:
   - Conversão declarada sem ação de conversão correspondente → gap crítico 🔴
   - Funil com evento de início mas sem evento de conclusão (ex: `InitiateCheckout` sem `Purchase`) → gap médio 🟡
   - Sem rastreamento de ligação telefônica (se site tem número de telefone) → oportunidade 🔵
   - Sem rastreamento de formulário (se site tem formulário de contato) → gap crítico 🔴

7. **Mapeie divergências de janela de atribuição**: Compare as janelas configuradas entre plataformas:
   - Meta: padrão 7 dias clique + 1 dia view
   - Google Ads: padrão 30 dias clique (Search), 3 dias view (Display/Video)
   - GA4: sessão de último clique por padrão
   Se há divergência significativa (ex: Meta 7 dias vs. Google 30 dias): alerte que os relatórios de cada plataforma vão mostrar números diferentes para o mesmo período — não é erro, é atribuição distinta.

8. **Recomende modelo de atribuição** com base no volume de conversões do cliente:
   - **< 30 conversões/mês**: Último clique — não há volume suficiente para modelos baseados em dados
   - **30–150 conversões/mês**: Baseado em posição ou linear — distribui crédito sem depender de ML
   - **> 150 conversões/mês**: Baseado em dados (Data-Driven) — Google usa ML para distribuição real
   Verifique qual modelo está configurado atualmente. Se for último clique com > 150 conversões/mês, recomende migrar para Data-Driven.

9. **Gere checklist de gaps priorizados**: Liste cada gap encontrado com:
   - **Severidade**: Crítico (impede otimização de lances) / Médio (dados incompletos) / Oportunidade (melhoria)
   - **Plataforma afetada**
   - **O que falta**: descrição técnica do gap
   - **Como corrigir**: instruções específicas de implementação (GTM, código direto, importação GA4)
   - **Impacto se não corrigir**: em linguagem de negócio (ex: "O Google Ads não consegue otimizar lances para leads — CPA vai subir")

10. **Crie ações de conversão faltantes no Google Ads** (com aprovação obrigatória): Se houver gaps de ação de conversão no Google Ads, apresente ao usuário o resumo de cada ação a criar. Aguarde confirmação antes de executar. Após aprovação, use MCP `google-ads` para criar cada ação via GAQL ou ferramenta disponível.

11. **Gere instruções para Meta Custom Conversions** (se houver gap de pixel): Se o pixel Meta não tem eventos de conversão configurados corretamente, gere o passo a passo específico:
    - URL de evento ou regra de correspondência de URL
    - Nome do evento padrão a usar (`Lead`, `Purchase`, etc.)
    - Instruções de configuração via Events Manager

12. **Documente a infraestrutura auditada** via `rastreador-campanhas.py`:
    ```
    python3 "scripts/rastreador-campanhas.py" \
      --brand {slug} \
      --action save-insight \
      --data '{"type": "tracking-audit", "date": "{data}", "google_conversions": {n}, "meta_pixel_status": "{status}", "gaps": [{gaps}], "attribution_model": "{modelo}"}'
    ```

## Saída

Um relatório de auditoria de rastreamento contendo:

- **Status por plataforma** (semáforo 🟢🟡🔴): Meta Pixel, Google Ads Conversions, GA4, GTM — com resumo de O que funciona / O que está incompleto / O que está quebrado
- **Mapa de gaps**: cada gap identificado com severidade, plataforma, descrição técnica e impacto no negócio
- **Checklist de implementação**: ações ordenadas por prioridade, com instruções passo a passo específicas
- **Análise de atribuição**: janelas configuradas por plataforma, divergências identificadas, modelo atual vs. recomendado
- **Aviso de dupla contagem** (se detectado): quais conversões estão sendo contadas mais de uma vez e como corrigir
- **Próximos passos**: lista das 3 correções de maior impacto, na ordem certa para executar

## Agentes Usados

- **gestor-trafego** — Interpretação de ações de conversão por objetivo de campanha, impacto de gaps de tracking em estratégias de lance (tCPA, tROAS, Maximizar Conversões), recomendação de modelo de atribuição por volume

## Integração Work Log

Após apresentar o relatório, pergunte ao usuário **somente se houver gaps críticos ou médios**:

> "Encontrei [N] gaps de rastreamento. Quer registrar as correções no work-log?"

Se confirmado, registre usando `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/log-tarefas.py" --action log` com `source_skill: rastreamento` e `category: Ads`:

- **[Ads] Instalar tag de conversão — {nome} em {plataforma}** — `priority: high` para gaps críticos
- **[Ads] Corrigir dupla contagem — {plataforma}** — `priority: high`
- **[Ads] Migrar modelo de atribuição para Data-Driven** — `priority: normal`
- **[Ads] Configurar CAPI Meta** — `priority: normal` se pixel ativo mas sem CAPI

Use `account_slug` da conta ativa.
