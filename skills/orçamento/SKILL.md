---
name: orçamento
description: "Use quando o usuário precisar otimizar alocação de orçamento de mídia paga, realocar gasto entre canais com base em performance, criar um plano de orçamento orientado por dados ou justificar mudanças de orçamento com projeções de ROI."
argument-hint: "[orçamento-total]"
---

# /mktos:orçamento

## Propósito

Otimização de orçamento de mídia paga orientada por dados entre canais usando dados de performance e benchmarks da indústria. Analisa eficiência de gasto atual, modela retornos decrescentes por canal e produz alocação otimizada com melhoria de ROI projetada e cronograma de realocação faseada.

## Entrada Necessária

O usuário deve fornecer (ou será solicitado):

- **Orçamento atual por canal**: Como o gasto está distribuído hoje (ex: Google Ads, Meta Ads, LinkedIn, TikTok)
- **Dados de performance por canal**: Métricas-chave — gasto, receita ou conversões, CPA, ROAS e volume de conversão durante o período de medição
- **Orçamento total disponível**: Orçamento geral de mídia paga para o período de otimização (mensal, trimestral ou anual)
- **Objetivos de negócio**: Objetivo primário — maximizar receita, minimizar CPA, atingir alvo específico de leads/ROAS, equilibrar crescimento com eficiência
- **Restrições**: Gasto mínimo por canal, mandatos da liderança, considerações sazonais, compromissos contratuais ou minimums de plataforma
- **Período de medição**: Janela que os dados de performance cobrem (últimos 30, 60, 90 dias ou intervalo customizado)
- **Modelo de atribuição**: Como conversões são atualmente atribuídas (último-clique, primeiro-clique, linear, orientado por dados ou desconhecido)
- **Fatores de sazonalidade**: Picos próximos, períodos promocionais ou eventos que afetam performance do canal
- **Contexto histórico**: Se dados refletem um período típico ou foram influenciados por eventos únicos (lançamento de produto, momento viral, interrupção)

## Processo

1. **Carregue contexto da conta**: Leia `./data/clientes/_conta-ativa.json` para obter o slug ativo, depois carregue `./data/clientes/{slug}/perfil.json`. Verifique SOPs em `./data/sops/`. Se nenhuma conta existir, pergunte: "Configurar uma conta primeiro (`/mktos:configurar`)?" — ou prossiga com padrões.
2. **Execute `otimizador-orcamento.py`**: Execute `scripts/otimizador-orcamento.py` com os dados de canal fornecidos para calcular métricas de eficiência baseline e gerar cenários de otimização.
3. **Calcule métricas de eficiência por canal**: Calcule ROAS, CPA, custo por lead, receita por real gasto, margem de contribuição e custo marginal de aquisição para cada canal.
4. **Classifique canais por eficiência marginal**: Ordene canais por retorno incremental por real adicional gasto, considerando níveis de saturação atuais e tendências históricas de performance.
5. **Aplique modelo de retornos decrescentes**: Modele como a eficiência de cada canal degrada conforme o gasto aumenta — identifique o ponto de inflexão e ceiling de saturação para cada canal.
6. **Gere alocação otimizada**: Redistribua orçamento para maximizar o objetivo declarado respeitando todas as restrições e limites mínimos de gasto viável.
7. **Compare atual vs. otimizado**: Construa comparação lado a lado mostrando mudanças de gasto, mudanças de métricas projetadas e melhoria líquida em todos os KPIs.
8. **Projete melhoria de ROI**: Estime receita total, volume de conversão, ganhos de ROAS e CPA da realocação com intervalos de confiança.
9. **Considere limites de gasto viável mínimo**: Garanta que nenhum canal caia abaixo do gasto mínimo necessário para gerar dados significativos, manter competitividade de leilão ou cumprir obrigações contratuais.
10. **Inclua orçamento de teste**: Reserve 10–15% do orçamento total para experimentação — novos canais, testes criativos, expansão de público ou plataformas emergentes.
11. **Sinalize ressalvas de atribuição**: Note onde limitações do modelo de atribuição podem distorcer cálculos de eficiência e recomende ajustes.
12. **Crie cronograma de realocação**: Faseie mudanças de orçamento ao longo de 4–8 semanas para evitar disrupção de performance — ramp-up e ramp-down graduais com checkpoints semanais e triggers de rollback.

## Saída

Um plano de otimização de orçamento estruturado contendo:

- **Tabela de alocação atual vs. otimizada**: Orçamentos lado a lado por canal com valores em R$, percentual do total e mudança do atual
- **Melhoria de ROI projetada**: Ganhos esperados em receita, conversões, ROAS e CPA com faixas de confiança
- **Classificação de eficiência de canal**: Canais ordenados por retorno marginal com curvas de retornos decrescentes e indicadores de saturação
- **Recomendações de realocação**: Mudanças específicas em R$ com rationale clara para cada aumento, diminuição ou manutenção
- **Comparação de cenários**: Projeções de melhor caso, esperado e conservador para a alocação otimizada
- **Cronograma de implementação**: Realocação faseada com checkpoints semanais, triggers de performance e critérios de rollback
- **Avaliação de risco**: Desvantagens potenciais de cada mudança, avisos de gasto viável mínimo, pontos cegos de atribuição e estratégias de mitigação
- **Plano de orçamento de teste**: Experimentos recomendados com orçamento alocado, hipóteses, critérios de sucesso e abordagem de mensuração
- **Notas de atribuição**: Ressalvas sobre como o modelo atual pode sobre- ou subcreditar canais específicos
- **Resumo executivo**: Visão geral de uma página com descobertas principais e ações recomendadas para apresentação a stakeholders

## Agentes Usados

- **analista-dados** — Análise de dados de performance, cálculos de eficiência, modelagem de retornos decrescentes, projeções de ROI e avaliação de atribuição
- **gestor-trafego** — Estratégia de orçamento por canal, expertise em limites de gasto, sequenciamento de realocação, benchmarks específicos de plataforma e dinâmica de leilão

## Integração Work Log

Após apresentar o plano de otimização, pergunte ao usuário:

> "Quer registrar as ações de realocação deste plano no work-log para acompanhamento?"

Se confirmado, extraia e registre cada ação usando `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/log-tarefas.py" --action log` com `source_skill: orçamento`. Tipos de tarefa a extrair:

- **[Ads] Aumentar budget de [canal] em R$ X** — para cada canal com recomendação de scale-up
- **[Ads] Reduzir budget de [canal] em R$ X** — para cada canal com recomendação de corte
- **[Ads] Pausar [canal/campanha]** — quando canal estiver abaixo do gasto viável mínimo
- **[Analytics] Revisar atribuição de [canal]** — quando modelo de atribuição foi sinalizado como limitante
- **[Ads] Executar realocação — Semana [N]** — um item por checkpoint do cronograma faseado
- **[Analytics] Validar resultado da realocação** — para checkpoints de rollback no cronograma

Use `category: Ads` para movimentações de orçamento e `category: Analytics` para revisões de dados. Use `priority: high` para recomendações com variância >15% do atual.
