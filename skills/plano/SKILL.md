---
name: plano
description: "Use quando o usuário precisar criar um plano de mídia paga, calendário de compra de mídia, plano de voo de publicidade, alocação de orçamento entre canais, calendário de rotação criativa ou estratégia holística de publicidade paga em múltiplas plataformas."
argument-hint: "[--orçamento=valor --canais=lista]"
---

# /mktos:plano

## Propósito

Gerar um plano de mídia paga holístico que coordena orçamento, canais, públicos, criativos e timing em todas as plataformas publicitárias. Equilibra objetivos de alcance e eficiência com restrições de execução prática para produzir um plano pronto para implementação com targets de pacing claro e protocolos de contingência.

## Entrada Necessária

O usuário deve fornecer (ou será solicitado):

- **Datas da campanha**: Data de início, data de término, períodos de blackout ou janelas obrigatórias de voo
- **Orçamento total de mídia paga**: Orçamento agregado para o período da campanha com qualquer piso ou limite específico do canal
- **Canais disponíveis**: Plataformas em consideração — Google Ads, Meta Ads, LinkedIn Ads, TikTok Ads, display programático, etc.
- **Objetivos da campanha**: Objetivos primários e secundários — conscientização (alcance/impressões), consideração (tráfego/engajamento), conversão (leads/vendas/ROAS)
- **Públicos-alvo com segmentos**: Definições de público incluindo dados demográficos, interesses, comportamentos, públicos customizados, lookalikes e pools de retargeting
- **Ativos criativos disponíveis**: Formatos e tamanhos de anúncios existentes, durações de vídeo, variantes estáticas e cronograma de produção criativa para novos ativos
- **Direcionamento geográfico**: Mercados, regiões ou cidades para direcionar com qualquer ponderação de orçamento específica por geo
- **Desempenho histórico por canal**: Dados de campanha passada — CPC, CPM, CPA, ROAS — por canal e segmento de público
- **Fatores de sazonalidade**: Flutuações de demanda, feriados, períodos promocionais ou eventos que afetam custos ou desempenho

## Processo

1. **Carregue contexto da conta**: Leia `./data/clientes/_conta-ativa.json` para obter o slug ativo, depois carregue `./data/clientes/{slug}/perfil.json`. Aplique regras de conformidade para mercados-alvo (`skills/context-engine/regras-conformidade.md`) e contexto da indústria. Verifique SOPs em `./data/sops/`. Se nenhuma conta existir, pergunte: "Configurar uma conta primeiro (`/mktos:configurar`)?" — ou prossiga com padrões.
2. **Verifique disponibilidade de datas no calendário**: Use `google-calendar-guroo` para verificar conflitos nas datas de início e fim propostas para a campanha. Se houver conflitos (eventos do cliente, reuniões, férias), alerte e sugira datas alternativas antes de avançar com o plano.
3. **Avalie ajuste canal-objetivo**: Avalie cada canal disponível contra objetivos da campanha usando capacidade de alcance, precisão de direcionamento, benchmarks de custo, suporte a formato criativo e confiabilidade de medição.
4. **Aloque orçamento entre canais**: Distribua orçamento usando alocação ponderada por eficiência — fatore desempenho histórico, curvas de retorno decrescente, limites de gasto efetivo mínimo e importância estratégica por canal.
5. **Projete cronograma de voo**: Estruture timing da campanha como contínuo, pulsado ou voando com base em objetivos, sazonalidade e orçamento — defina níveis de gasto semanal e períodos de heavy-up.
6. **Construa matriz de direcionamento de público**: Mapeie cada segmento de público para seus canais ideais com parâmetros de direcionamento, alcance esperado, frequência estimada e gerenciamento de sobreposição entre plataformas.
7. **Planeje rotação criativa**: Agende variantes criativas entre canais com frequência de rotação, limites de fadiga (caps de frequência), janelas de teste A/B e datas de refresh para novos ativos.
8. **Defina framework de medição**: Estabeleça KPIs por canal, requisitos de rastreamento (pixels, UTMs), modelo de atribuição e cadência de relatório.
9. **Reserve contingência**: Reserve 10–15% do orçamento como contingência para escalabilidade oportunista, realocação por underperformance ou oportunidades emergentes — defina critérios de trigger para uso.
10. **Crie checklists de configuração de plataforma**: Construa checklists de setup específicos de canal cobrindo estrutura de conta, convenções de nomenclatura, implementação de rastreamento e specs criativos.
11. **Modele projeções de alcance e frequência**: Projete alcance total, frequência média e frequência efetiva por canal e em agregado — sinalize riscos de saturação ou underspend.
12. **Compile calendário unificado de plano de mídia**: Reúna todos os componentes em uma visualização única mostrando pacing de orçamento, rotação criativa, ativação de público e marcos de medição semana a semana.

## Saída

Um plano de mídia paga estruturado contendo:

- **Tabela de alocação de canal**: Valor de orçamento, percentual e rationale estratégica para cada canal com guardrails de gasto mínimo e máximo
- **Cronograma de voo com ondas de orçamento semanal**: Plano semana a semana com fases de ramp-up, estado estável, heavy-up e wind-down por canal
- **Matriz de direcionamento de público**: Mapeamento segmento × canal × criativo com parâmetros de direcionamento, alcance esperado e caps de frequência
- **Calendário de rotação criativa**: Cronograma de ativos por canal com datas de rotação, limites de fadiga e marcos de refresh
- **Projeções de alcance e frequência**: Alcance projetado, frequência média e efetiva por canal e em agregado com faixas de confiança
- **Framework de medição**: KPIs por canal, requisitos de rastreamento, modelo de atribuição e cadência de relatório
- **Checklists de configuração de plataforma**: Checklists de implementação específicos de canal cobrindo estrutura, convenções de nomenclatura, rastreamento e specs criativos
- **Plano de orçamento de contingência**: Valor de reserva, critérios de trigger e framework de decisão de realocação
- **Targets de pacing diário/semanal**: Benchmarks de gasto e desempenho para monitoramento em voo com limites de variância aceitável
- **Mapa de sinergia entre canais**: Fluxos de retargeting, caminhos de mensagem sequencial e lógica de progressão de público da conscientização à conversão

## Agentes Usados

- **gestor-trafego** — Alocação de canal, pacing de orçamento, dinâmica de leilão, configuração de plataforma, modelagem de alcance/frequência, planejamento de rotação criativa e verificação de calendário

## Integração Work Log

Após apresentar o plano de mídia, pergunte ao usuário:

> "Quer registrar as tarefas de implementação deste plano no work-log para acompanhamento?"

Se confirmado, extraia e registre cada tarefa usando `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/log-tarefas.py" --action log` com `source_skill: plano`. Tipos de tarefa a extrair deste output:

- **[Ads] Configurar conta/campanha em [plataforma]** — para cada canal incluído no plano
- **[Ads] Configurar públicos e direcionamento em [plataforma]** — por canal
- **[Ads] Subir criativos em [plataforma]** — para cada lote criativo no calendário de rotação
- **[Ads] Configurar rastreamento e UTMs** — pixels, importações de conversão, parâmetros UTM
- **[Ads] Configurar monitoramento de pacing** — alertas de orçamento e dashboards
- **[Strategy] Revisar resultados em [data]** — checkpoints de otimização definidos no plano

Use `category: Ads` para todas as tarefas de configuração de campanha e plataforma. Use a conta ativa como `account_slug`.
