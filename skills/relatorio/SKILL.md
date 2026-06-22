---
name: relatorio
description: "Use quando o usuário precisar gerar um relatório de performance de mídia paga — dados cross-platform (Google Ads + Meta), ROAS/CPA/CPL, comparativo período-a-período, análise criativa, benchmarks e recomendações para o próximo período."
argument-hint: "[período] [audiência: cliente|interno]"
---

# /mktos:relatorio

## Propósito

Gerar um relatório completo de performance de mídia paga em minutos. Puxa dados de Google Ads e Meta diretamente via MCP, consolida métricas cross-platform, calcula ROAS blended, CPA e CPL, compara com o período anterior e com as metas do cliente, identifica criativos em fadiga e entrega uma narrativa adaptada à audiência — resumo executivo para o cliente, análise de eficiência para a equipe. Relatório bom é o que o cliente entende, não o que você se orgulha de ter construído.

## Entrada Necessária

O usuário deve fornecer (ou será solicitado):

- **Período**: datas de início e fim (ex: "maio 2026" ou "2026-05-01 a 2026-05-31") — padrão: mês anterior completo
- **Audiência**: para o cliente (foco em resultados de negócio) ou uso interno (foco em eficiência e oportunidades)
- **Período anterior** (opcional): para comparativo PoP — se omitido, calcula automaticamente o período equivalente anterior

## Processo

1. **Carregue contexto da conta**: Leia `./data/clientes/_conta-ativa.json` para obter o slug ativo, depois carregue `./data/clientes/{slug}/perfil.json`. Use `canais_ativos`, `kpis`, `orcamento_mensal`, `vertical` e `moeda` do perfil. Se nenhuma conta existir, pergunte: "Configurar uma conta primeiro (`/mktos:configurar`)?"

2. **Defina o período de análise**: Se o usuário não informou, use o mês anterior completo como padrão. Confirme o período com o usuário antes de puxar dados. Calcule automaticamente o período equivalente anterior para PoP (ex: se atual é maio, anterior é abril).

3. **Puxe dados do Google Ads via MCP** (se `google` em `canais_ativos`): Execute GAQL segmentado por campanha:
   ```sql
   SELECT
     campaign.name,
     campaign.status,
     metrics.cost_micros,
     metrics.impressions,
     metrics.clicks,
     metrics.conversions,
     metrics.conversions_value,
     metrics.ctr,
     metrics.average_cpm
   FROM campaign
   WHERE segments.date BETWEEN '{data_inicio}' AND '{data_fim}'
     AND campaign.status = 'ENABLED'
   ```
   Converta `cost_micros` para BRL (divida por 1.000.000). Agrupe por conta para obter totais.

4. **Puxe dados do Meta via MCP** (se `meta` em `canais_ativos`): Use `get_insights` com breakdown por campanha:
   - Métricas: `spend`, `reach`, `impressions`, `link_clicks`, `actions` (leads/purchases), `purchase_roas`
   - Date range: `{data_inicio}` a `{data_fim}`
   - Extraia de `actions`: conta de `lead` para CPL, `purchase` para CPA

5. **Consolide métricas cross-platform**: Execute `relatorio.py` com os dados coletados:
   ```
   python3 "scripts/relatorio.py" \
     --brand {slug} \
     --period "{data_inicio}:{data_fim}" \
     --channels '[{dados_google},{dados_meta}]' \
     --previous-period '[{dados_periodo_anterior}]' \
     --format json \
     --audience {audiencia}
   ```
   O script calcula: ROAS blended, CPA médio, CPL, CTR, CPM e variações PoP com semáforo por métrica.

6. **Analise criativos com maior gasto**: Puxe os top 5 anúncios por gasto via MCP:
   - Google Ads: GAQL com `metrics.cost_micros DESC LIMIT 5` no nível de `ad`
   - Meta: `get_ads` com ordenação por spend

   Para cada criativo, execute:
   ```
   python3 "scripts/indicador-fadiga.py" \
     --action score-health \
     --creative-id {id} \
     --data '{"impressions":{imp},"frequency":{freq},"ctr_current":{ctr},"ctr_baseline":{baseline},"days_running":{dias}}'
   ```
   Sinalize criativos com `health_score < 60` (Fadigando ou pior) no relatório.

7. **Calcule comparativo PoP**: Com os dados do período anterior (puxados via mesmo GAQL/MCP com datas ajustadas), calcule a variação em % para cada métrica principal. Aplique semáforo: 🟢 melhora ≥ 5% / 🟡 estável -5% a +5% / 🔴 queda ≥ 5%. Para métricas de custo (CPA, CPM, CPL), inverta a lógica.

8. **Compare com benchmarks de setor**: Consulte `skills/context-engine/perfis-industria.md` para o `vertical` do cliente. Compare CTR, CPM e CPA atuais com os benchmarks do setor. Sinalize se o cliente está acima ou abaixo da média.

9. **Execute `calculadora-roi.py`** para análise de atribuição e eficiência por canal:
   ```
   python3 "scripts/calculadora-roi.py" \
     --channels '[{canais_com_spend_revenue_conversions}]' \
     --attribution last_touch \
     --period "{periodo}"
   ```
   Use o resultado para identificar o canal mais e menos eficiente em ROI.

10. **Estruture a narrativa por audiência**:

    **Para cliente (`--audience client`)**:
    - Abra com o resultado de negócio mais relevante (leads gerados, ROAS, receita atribuída)
    - Compare com a meta acordada de `kpis` do perfil — atingiu ou ficou abaixo?
    - Explique variações de forma simples: "O custo por lead subiu 12% porque o período inclui feriado nacional, o que reduz o volume de busca"
    - Evite jargão técnico (CPM, CTR, ROAS podem ser explicados em parênteses)
    - Conclua com o que foi bem e o que vai melhorar no próximo período

    **Para equipe interna (`--audience internal`)**:
    - Abra com ranking de canais por eficiência (ROAS e ROI)
    - Destaque criativos em fadiga com custo estimado de manter vs. renovar
    - Identifique gaps de orçamento: canal com ROAS alto mas share de gasto baixo
    - Inclua alertas de rastreamento se houver conversões sem tracking detectadas
    - Conclua com 3-5 hipóteses de otimização para o próximo período

11. **Gere 3 a 5 recomendações priorizadas**: Para cada recomendação, use o formato:
    > **[Ação]** — *Hipótese:* {por que acreditamos que funciona}. *Impacto estimado:* {métrica + magnitude esperada}.

    Exemplos:
    - "Aumentar orçamento de Google Search em 20% — Hipótese: canal opera com ROAS 4.2x e ainda tem margem de escala. Impacto estimado: +15 conversões/mês sem degradação de CPA."
    - "Renovar criativo Meta principal (em fadiga há 28 dias) — Hipótese: CTR caiu 35% do baseline. Impacto estimado: recuperar CTR para baseline reduz CPL em ~20%."

## Saída

Um relatório completo de mídia paga com:

- **Executive summary**: resultado principal do período em linguagem adaptada à audiência
- **Metas vs. realizado**: comparativo contra KPI targets do `perfil.json` com semáforo
- **Tabela por plataforma**: spend, impressões, cliques, CTR, CPM, conversões, ROAS, CPA — com totais consolidados
- **Comparativo PoP**: variação de todas as métricas principais vs. período anterior com semáforo
- **Análise criativa**: status de saúde dos top criativos por gasto, flag de fadiga
- **Benchmarks de setor**: CTR, CPM e CPA do cliente vs. média do setor
- **3 a 5 recomendações priorizadas**: formato hipótese + impacto estimado, ordenadas por impacto

## Agentes Usados

- **monitor-performance** — Coleta de dados via MCP (Google Ads GAQL, Meta insights), detecção de anomalias, análise de saúde criativa com `indicador-fadiga.py`
- **analista-dados** — Consolidação cross-platform, cálculo de métricas blended, comparativo PoP, benchmarking de setor, identificação de oportunidades de realocação de orçamento

## Integração Work Log

Após entregar o relatório, registre automaticamente:

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/log-tarefas.py" --action log
```

Com `source_skill: relatorio` e `category: Ads`:

- **[Ads] Relatório {período} entregue — ROAS {roas}x, {N} conversões** — `priority: normal`

Se houver criativos em fadiga identificados, pergunte:

> "Identificei [N] criativos em fadiga no período. Quer gerar briefs de refresh? (`/mktos:saude`)"

Use `account_slug` da conta ativa.
