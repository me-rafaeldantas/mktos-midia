---
name: pacing
description: "Use quando o usuário quiser rastreamento de orçamento em tempo real entre plataformas de anúncios com análise de pacing, alertas de overspend e recomendações de realocação."
---

# /mktos:pacing

## Propósito

Rastreia orçamento de publicidade em tempo real entre todas as plataformas de anúncios conectadas. Analisa pacing de gasto contra metas, projeta totais do final do período, sinaliza riscos de overspend e ineficiências de underspend, calcula taxas de queimada diária e recomenda realocações de orçamento para maximizar ROI dentro da janela de orçamento restante.

## Entrada Necessária

O usuário deve fornecer (ou será solicitado):

- **Período de orçamento**: Este mês, este trimestre ou intervalo de datas customizado (ex: "1º jun – 30 jun").
  Determina o denominador de pacing e horizonte de projeção
- **Plataformas a incluir**: Todas as plataformas conectadas ou específicas (ex: "Google Ads e Meta apenas").
  Padrão é todas as MCPs de anúncio configuradas
- **Metas de orçamento por plataforma** (opcional): Metas específicas de gasto por plataforma para o período.
  Se omitido, metas são puxadas de `perfil.json` campo `orcamento_mensal` e qualquer alocação de plataforma salva
- **Orçamento total** (opcional): Limite de orçamento geral para o período.
  Se omitido, puxado de `perfil.json`
- **Limites de alerta** (opcional): Limites customizados para overpace (padrão: >110% do pacing esperado) e
  underspend (padrão: <70% do pacing esperado)
- **Incluir métricas de eficiência** (opcional): Se deve puxar dados de CPA, ROAS e conversões junto com gasto.
  Padrão é sim

## Processo

1. **Carregue contexto da conta**: Leia `./data/clientes/_conta-ativa.json` para obter o slug ativo, depois carregue `./data/clientes/{slug}/perfil.json`. Verifique SOPs em `./data/sops/`. Se nenhuma conta existir, pergunte: "Configurar uma conta primeiro (`/mktos:configurar`)?" — ou prossiga com padrões.
2. **Extraia metas de orçamento**: Puxe `orcamento_mensal` de `perfil.json` e qualquer alocação por plataforma salva de execuções anteriores do `/mktos:orçamento` ou `/mktos:plano`. Se o usuário forneceu metas explícitas, use-as como overrides. Calcule a taxa de gasto diário alvo para cada plataforma (orçamento ÷ dias no período).
3. **Puxe dados de gasto das plataformas via MCP**: Consulte cada plataforma conectada (google-ads, meta-marketing) para gasto do período atual — gasto total até agora, detalhamento diário, distribuição por campanha e métricas de custo (CPC, CPM, CPA).
4. **Calcule pacing por plataforma**: Execute `scripts/controlador-pacing.py` com dados de gasto e metas de orçamento para computar: dias decorridos/restantes, percentual de pacing esperado vs. real, razão de pacing (real ÷ esperado), taxa de queimada diária (média de 7 dias) e tendência (aceleração/estável/desaceleração).
5. **Projete gasto do final do período**: Extrapole a taxa de queimada atual até o final do período para cada plataforma — produza projeções de melhor caso (menor gasto diário recente), esperado (média de 7 dias) e pior caso (maior gasto diário recente).
6. **Compare com metas de orçamento**: Para cada plataforma, calcule a lacuna entre gasto projetado e meta — expresse como valor em R$ e variância percentual.
7. **Sinalize problemas de pacing**: Gere alertas —
   - 🔴 Overpace crítico (>120%): ação imediata — reduza lances, pause baixos desempenhos, defina caps diários
   - 🟡 Aviso de overpace (110–120%): ajustes proativos esta semana
   - 🟡 Aviso de underspend (<70%): aumente lances ou expanda targeting ou realoque
   - 🔵 Info de underspend (70–85%): monitore
8. **Envie alerta por Gmail para alertas críticos**: Se houver alertas 🔴 (overpace >120% ou underspend com risco de não gastar ≥20% do orçamento), envie email de alerta via `gmail-guroo` contendo: plataforma afetada, pacing atual vs. esperado, valor em R$ de overspend/underspend projetado e ação recomendada. Solicite confirmação antes de enviar.
9. **Puxe métricas de eficiência**: Para cada plataforma, recupere CPA, ROAS, volume de conversão e custo por conversão para que decisões de realocação sejam informadas por desempenho — não apenas por pacing.
10. **Recomende realocações**: Execute `scripts/otimizador-orcamento.py` com dados de eficiência para sugerir movimentações específicas de plataformas com underspend ou baixa eficiência para aquelas com alto desempenho e espaço para escalar.
11. **Salve snapshot de orçamento**: Persista o snapshot de pacing atual via `scripts/monitor-performance.py --brand {slug} --action save-snapshot` para rastreamento histórico e comparação em futuras execuções.

## Saída

Um dashboard de orçamento estruturado contendo:

- **Resumo de orçamento**: Orçamento total do período, gasto até agora, total restante, percentual de pacing geral, dias decorridos, dias restantes, total projetado e status de saúde geral (no caminho / overpacing / underpacing)
- **Tabela de gasto por plataforma**: Nome da plataforma, meta, gasto real, percentual de pacing, taxa de queimada diária (média de 7 dias), gasto projetado, variância da meta (R$ e %) e flag de status (🟢/🟡/🔴)
- **Alertas de overspend/underspend**: Lista ordenada por prioridade com severidade, plataforma, pacing atual, variância projetada e ação corretiva recomendada específica
- **Recomendações de realocação**: Movimentações específicas em R$ entre plataformas com rationale — ex: "Mova R$ 2.000 do Meta (pacing 62%, CPA R$ 85) para Google Ads (pacing 98%, CPA R$ 22, espaço para escalar)"
- **Contexto de eficiência**: CPA, ROAS, volume de conversão e tendência de custo por plataforma para que decisões de orçamento considerem qualidade de performance, não apenas pacing
- **Detalhamento de taxa de queimada diária**: Gasto diário atual vs. alvo por plataforma, com direção de tendência de 7 dias
- **Cenários de projeção**: Projeções de melhor caso, esperado e pior caso por plataforma e em agregado
- **Resumo executivo**: 2–3 sentenças — saúde total do orçamento, maior risco ou oportunidade e a ação única mais importante agora

## Agentes Usados

- **monitor-performance** — Agregação de dados de gasto das plataformas, cálculos de pacing, modelagem de projeção, persistência de snapshot, alertas críticos via Gmail e análise de tendências históricas
- **gestor-trafego** — Estratégia de otimização de orçamento, recomendações de realocação, táticas específicas de plataforma (estratégias de lance, caps diários, expansão de público) e expertise em dinâmica de leilão

## Integração Work Log

Após apresentar o dashboard de pacing, pergunte ao usuário **somente se houver alertas amarelos ou vermelhos**:

> "Encontrei [N] problemas de pacing que precisam de ação. Quer registrar as correções no work-log?"

Se confirmado, extraia e registre cada ação corretiva usando `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/log-tarefas.py" --action log` com `source_skill: pacing`. Tipos de tarefa a extrair:

- **[Ads] Corrigir overpacing em [plataforma] — reduzir cap diário** — para alertas vermelhos de overspend
- **[Ads] Corrigir underpacing em [plataforma] — aumentar cap diário** — para alertas de underspend com risco de não gastar o budget
- **[Ads] Realizar realocação emergencial de R$ [valor] de [origem] para [destino]** — quando recomendação de realocação imediata for gerada
- **[Analytics] Revisar snapshot de pacing de [plataforma]** — quando dados estiverem inconsistentes ou com lag

Use `priority: high` para alertas vermelhos (overspend >15% ou underspend projetado >20%). Se o dashboard não apresentar alertas, não ofereça logging — não há tarefas acionáveis.
