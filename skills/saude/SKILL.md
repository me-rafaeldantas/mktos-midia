---
name: saude
description: "Use quando o usuário quiser um dashboard de saúde criativa — previsão de fadiga em anúncios ativos, recomendações de refresh, plano de teste A/B para criativos em desgaste e gestão do ciclo de vida criativo."
---

# /mktos:saude

## Propósito

Monitorar a saúde criativa de todas as campanhas ativas. Pontua cada criativo por risco de fadiga, prevê quando o desgaste vai impactar performance, gera briefs de refresh com sugestões específicas de mudança e cria planos de teste A/B para validar os novos criativos. Fadiga criativa é uma das formas mais silenciosas de desperdiçar verba em mídia paga — um anúncio que funcionou bem e ficou em ar tempo demais sangra budget enquanto CTR cai, CPM sobe e engajamento desaparece. Este comando detecta o problema antes que custe caro.

## Entrada Necessária

Flexível — a skill adapta o fluxo ao contexto disponível:

- **Com contexto** (usuário já vem de uma análise, menciona criativos ou traz dados): executa direto a partir da informação fornecida
- **Sem contexto** (comando executado vazio): apresenta menu de entrada e adapta o fluxo à opção escolhida

## Processo

1. **Carregue contexto da conta**: Leia `./data/clientes/_conta-ativa.json` para obter o slug ativo, depois carregue `./data/clientes/{slug}/perfil.json`. Aplique benchmarks históricos de performance criativa e restrições de capacidade de produção. Verifique SOPs em `./data/sops/`. Se nenhuma conta existir, pergunte: "Configurar uma conta primeiro (`/mktos:configurar`)?"

2. **Detecte o modo de entrada**: Se o usuário trouxe dados ou contexto de criativos → vá direto ao passo 4. Se o comando foi executado sem contexto, apresente o menu:

   > **O que você quer analisar?**
   >
   > 1. 🔍 **Verificar Saúde da Conta** — análise automática de todos os criativos ativos nos últimos 7 dias, com destaque para tendências dos últimos 3 dias
   > 2. 🎯 **Analisar um criativo específico** — informe o nome ou ID do anúncio e o canal
   > 3. 🔁 **Planejar refresh de campanha** — identifique quais criativos precisam ser renovados e gere briefs
   > 4. 📊 **Ver criativos em risco** — apenas os anúncios com sinal de fadiga iminente, sem análise completa

   Aguarde a escolha do usuário antes de prosseguir. Aceite também respostas em linguagem natural ("quero ver o que está fadigando no Meta").

3. **Execute o fluxo por modo**:

   ### Modo 1 — Verificar Saúde da Conta (proativo, sem input do usuário)

   Puxe os dados automaticamente das plataformas ativas:

   **Google Ads** — Execute GAQL para os top anúncios por gasto nos últimos 7 e 3 dias:
   ```sql
   SELECT
     ad_group_ad.ad.id,
     ad_group_ad.ad.name,
     campaign.name,
     metrics.cost_micros,
     metrics.impressions,
     metrics.clicks,
     metrics.ctr,
     metrics.average_cpc
   FROM ad_group_ad
   WHERE segments.date DURING LAST_7_DAYS
     AND ad_group_ad.status = 'ENABLED'
   ORDER BY metrics.cost_micros DESC
   LIMIT 10
   ```
   Repita com `LAST_3_DAYS` para o mesmo conjunto de anúncios — a diferença entre as janelas revela se a performance está acelerando ou desacelerando.

   **Meta Ads** — Use MCP `meta-marketing` com `get_ads` filtrando `status=ACTIVE`, métricas: `spend`, `impressions`, `ctr`, `cpm`, `frequency`, `reach` para os períodos de 7 dias e 3 dias.

   Identifique a **ação de conversão principal** da conta: use `kpis` do `perfil.json` (campo `conversao_principal` ou `objetivo_principal`). Se não configurado, pergunte: "Qual é o resultado que mais importa agora — lead, compra, clique, visualização?" — e use esse foco para priorizar quais criativos merecem atenção.

   Com os dados coletados, calcule para cada criativo:
   - **CTR 7D vs CTR 3D**: queda > 15% nos últimos 3 dias vs. 7 dias = sinal de fadiga acelerando
   - **CPM 7D vs CPM 3D**: alta > 10% nos últimos 3 dias = leilão ficando mais caro para este criativo
   - **Frequência** (Meta): acima de 3.5 em 7 dias = saturação de audiência
   - **Dias em veiculação**: referência por canal (Meta > 21 dias sem refresh = risco; Google Search > 45 dias)

   Siga direto para o passo 4 com os dados coletados.

   ### Modo 2 — Analisar criativo específico

   Pergunte: nome ou ID do criativo, canal e período de análise. Se o usuário informar o ID, puxe os dados via MCP. Siga para o passo 4.

   ### Modo 3 — Planejar refresh de campanha

   Puxe criativos ativos com `health_score < 60` (Fadigando ou pior) via Modo 1, mas exiba apenas esses. Pule diretamente para o passo 5 (briefs de refresh) sem gerar relatório completo de saúde.

   ### Modo 4 — Ver criativos em risco

   Execute Modo 1, mas exiba apenas os criativos com CTR 3D < CTR 7D × 0.85 ou frequência > 3.5. Relatório resumido, sem planos de A/B.

4. **Pontue a saúde de cada criativo**: Execute `indicador-fadiga.py` com os dados de performance de cada criativo (vindos do MCP no Modo 1, ou fornecidos pelo usuário nos demais modos):
   ```
   python3 "scripts/indicador-fadiga.py" \
     --action score-health \
     --creative-id {id} \
     --data '{"impressions":50000,"frequency":4.2,"ctr_current":0.018,"ctr_baseline":0.025,"cpm_current":12.5,"cpm_baseline":9.0,"engagement_rate_current":0.03,"engagement_rate_baseline":0.05,"days_running":28,"audience_size":200000}'
   ```
   O modelo avalia 5 sinais de fadiga ponderados:
   - Razão CTR atual ÷ baseline (peso 30%)
   - Razão CPM atual ÷ baseline (peso 25%)
   - Razão engajamento atual ÷ baseline (peso 20%)
   - Saturação de frequência ou impressões (peso 15%)
   - Dias em veiculação relativo às normas do canal (peso 10%)

   Cada criativo recebe um score de saúde de 0–100 e classificação de estágio:
   - **Novo** (80–100): performance estável, sem sinais de fadiga
   - **Maduro** (60–79): performance sustentada, monitorar
   - **Fadigando** (40–59): sinais iniciais de desgaste — planejar refresh
   - **Fadigado** (20–39): queda significativa — executar refresh urgente
   - **Esgotado** (0–19): performance colapsada — pausar imediatamente

5. **Preveja a linha do tempo de fadiga**: Para cada criativo ainda não em estágio Fadigado ou Esgotado, projete os dias estimados até a fadiga com base na trajetória atual de declínio. Fatores: tamanho do público (menor = fatiga mais rápido), taxa de frequência, dinâmicas do canal e efeitos de sazonalidade. Entregue estimativa de "dias restantes" com intervalo de confiança.

6. **Gere briefs de refresh para criativos em desgaste**: Para cada criativo nos estágios Fadigando, Fadigado ou Esgotado, produza um brief específico:
   - **O que manter**: elementos que impulsionaram a performance inicial — hook, proposta de valor, prova social, CTA que ainda ressoa
   - **O que mudar**: elementos que contribuem para a fadiga — tratamento visual, ângulo do headline, esquema de cores, formato, abertura do vídeo
   - **O que testar**: novos ângulos ou abordagens com base em tendências competitivas e posicionamento da marca

7. **Crie plano de teste A/B para cada criativo que precisar de refresh**: Para cada brief de refresh, gere:
   - Controle (criativo atual) e variante(s) com as mudanças recomendadas
   - Hipótese: por que a variante deve superar o controle
   - Métrica primária de avaliação (CTR, CPC, taxa de conversão)
   - Tamanho mínimo de amostra para significância estatística
   - Duração estimada do teste
   - Critério de declaração de vencedor

8. **Priorize por gasto e impacto**: Classifique todos os criativos que precisam de atenção pela combinação de gasto diário (maior gasto = maior desperdício se fadigado) e severidade da fadiga (mais fadigado = mais urgência). Calcule o desperdício estimado de gasto — custo incremental de manter um criativo fadigado versus um novo no baseline de performance.

## Saída

Um relatório de saúde criativa contendo:

- **Dashboard de saúde criativa**: todos os criativos ativos pontuados e classificados — mostrando nome ou ID, canal, score de saúde (0–100), estágio de fadiga, métricas-chave vs. baseline (razão CTR, razão CPM, razão engajamento), frequência, dias em veiculação e gasto diário
- **Previsões de fadiga**: para cada criativo não esgotado, dias estimados até a performance cair abaixo dos thresholds aceitáveis — com intervalo de confiança e principal driver da fadiga projetada
- **Lista de prioridade de refresh**: criativos classificados por urgência — combinando severidade de fadiga com nível de gasto, com desperdício diário estimado por criativo fadigado
- **Briefs de refresh por criativo**: recomendações específicas e acionáveis para cada criativo fadigando ou fadigado — o que manter, o que mudar, o que testar
- **Planos de teste A/B**: controle e variante, hipótese, métrica primária, tamanho de amostra, duração e critério de sucesso
- **Linha do tempo do ciclo de vida criativo**: quando cada criativo foi lançado, estágio atual e datas de transição projetadas — para planejamento proativo de produção
- **Recuperação de performance estimada**: melhoria projetada em CTR, CPM e engajamento se criativos fadigados forem refreshados

## Agentes Usados

- **diretor-criativo** — Geração de briefs de refresh (o que manter/mudar/testar), design de variantes de teste A/B e direção criativa alinhada à voz da marca e restrições de produção
- **monitor-performance** — Detecção de sinais de fadiga a partir de tendências de métricas, cálculo do score de saúde com `indicador-fadiga.py`, projeção de linha do tempo de fadiga e classificação de estágio do ciclo de vida
- **gestor-trafego** — Análise de performance por canal com benchmarking ajustado para fadiga, cálculo de desperdício de gasto para priorização de refresh e calibração de thresholds de fadiga por plataforma

## Integração Work Log

Após apresentar o relatório, pergunte ao usuário **somente se houver criativos em estágio Fadigando ou pior**:

> "Encontrei [N] criativos em fadiga que precisam de ação. Quer registrar os refreshes no work-log?"

Se confirmado, registre usando `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/log-tarefas.py" --action log` com `source_skill: saude`:

- **[Criativo] Refresh urgente — [nome do criativo] em [canal]** — `priority: high` para Fadigado ou Esgotado
- **[Criativo] Planejar refresh — [nome do criativo] em [canal]** — `priority: normal` para Fadigando
- **[Criativo] Configurar teste A/B — [criativo A] vs [criativo B]** — `priority: normal`
- **[Ads] Pausar criativo esgotado — [nome] em [canal]** — `priority: high` para estágio Esgotado

Use `category: Criativo` para briefs de refresh e `category: Ads` para pausas de campanha. Use `account_slug` da conta ativa.
