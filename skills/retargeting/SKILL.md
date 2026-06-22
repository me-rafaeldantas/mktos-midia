---
name: retargeting
description: "Use quando o usuário precisar criar ou revisar uma estratégia de retargeting/remarketing — segmentação de público por estágio de funil, sequência de criativos, controle de frequência, retargeting dinâmico e alocação de orçamento por segmento."
argument-hint: "[conta ou campanha]"
---

# /mktos:retargeting

## Propósito

Desenhar uma estratégia completa de retargeting cross-platform com segmentação de audiência por estágio de funil e comportamento, sequência criativa, gestão de frequência e alocação de orçamento. Entrega um playbook de retargeting pronto para implementação nas plataformas de anúncios ativas.

## Entrada Necessária

O usuário deve fornecer (ou será solicitado):

- **Volume de tráfego**: visitantes únicos e pageviews mensais (estimativa serve)
- **Estágios do funil de conversão**: etapas principais da jornada (visita, visualização de produto, carrinho, checkout, compra — ou equivalente em captação de leads)
- **Plataformas ativas**: Google Ads, Meta, LinkedIn, TikTok, programático, etc.
- **Orçamento de retargeting**: budget mensal disponível ou alocado para remarketing
- **Catálogo de produtos**: se existe feed de produtos e em quais plataformas está configurado (para retargeting dinâmico)
- **Ciclo médio de compra**: tempo típico da primeira visita até a conversão (dias, semanas, meses)
- **Setup atual**: campanhas de retargeting existentes, status de pixel/tag, definições de audiência em uso e performance atual
- **Status de rastreamento**: quais pixels/tags estão instalados e disparando corretamente (Meta Pixel, Google Tag, LinkedIn Insight Tag, TikTok Pixel, etc.)

## Processo

1. **Carregue contexto da conta**: Leia `./data/clientes/_conta-ativa.json` para obter o slug ativo, depois carregue `./data/clientes/{slug}/perfil.json`. Aplique benchmarks históricos de performance criativa e restrições de capacidade de produção. Verifique SOPs em `./data/sops/`. Se nenhuma conta existir, pergunte: "Configurar uma conta primeiro (`/mktos:configurar`)?"

2. **Verifique histórico de campanhas**: Execute `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/rastreador-campanhas.py" --slug {slug} --action list-campaigns` para revisar campanhas de retargeting existentes e identificar o que já foi testado.

3. **Audite a infraestrutura de rastreamento**: Verifique o status de instalação de pixels e tags nas plataformas ativas. Identifique lacunas de rastreamento que impediriam a construção de audiências ou atribuição de conversões antes de desenhar a estratégia. Considere executar `/mktos:rastreamento` para uma auditoria completa se o status for desconhecido.

4. **Defina os segmentos de audiência de retargeting**: Crie segmentos baseados em:
   - **Estágio de funil**: visitantes (awareness), visualizadores de produto (consideração), abandonadores de carrinho, compradores recentes, clientes inativos
   - **Sinais comportamentais**: páginas visitadas, tempo no site, frequência de visitas, conteúdo consumido
   - **Janelas de recência**: 1–3 dias, 4–7 dias, 8–14 dias, 15–30 dias, 31–90 dias
   
   Estime o tamanho de cada segmento com base no volume de tráfego informado.

5. **Desenhe a sequência criativa por segmento**: Mapeie uma sequência de mensagens para cada segmento que avance o usuário em direção à conversão:
   - **Awareness**: mensagem educativa e proposta de valor
   - **Consideração**: prova social e diferenciação
   - **Abandono de carrinho**: urgência e incentivo
   - **Compradores recentes**: upsell e cross-sell
   - **Clientes inativos**: oferta de reengajamento

6. **Defina caps de frequência por plataforma**: Estabeleça limites de impressões por usuário por dia e por semana em cada plataforma. Equilibre visibilidade com fadiga criativa — referência: 3–5 impressões/dia em display, 1–2/dia em feed social, máximo 15–20 por semana no total de todas as veiculações.

7. **Planeje a coordenação cross-platform**: Orquestre o retargeting entre plataformas para que o usuário vivencie uma jornada coerente, sem mensagens redundantes. Atribua papéis primário e secundário por plataforma (ex: Meta para retargeting de awareness, Google Display para mid-funil, Search Remarketing para alta intenção, LinkedIn para decisores B2B).

8. **Desenhe listas de exclusão**: Defina:
   - Janelas de exclusão de conversores (excluir compradores por 7–30 dias pós-conversão)
   - Exclusões entre segmentos (evitar que o mesmo usuário veja anúncios de awareness e abandono de carrinho simultaneamente)
   - Regras de audiência negativa para evitar desperdício e fadiga de marca

9. **Aloque orçamento por segmento**: Distribua o budget de retargeting entre os segmentos com base em tamanho da audiência, proximidade da conversão e ROAS esperado. Segmentos de fundo de funil (abandono de carrinho) tipicamente recebem maior gasto por usuário, mesmo com audiências menores.

10. **Configure o retargeting dinâmico**: Se há catálogo de produtos disponível, especifique o setup de anúncios dinâmicos — requisitos de feed, design de template, lógica de recomendação de produtos (itens visualizados, produtos complementares, mais vendidos) e criativos de fallback para usuários sem dados em nível de produto.

11. **Defina KPIs e gatilhos de otimização**: Estabeleça métricas de sucesso por segmento e plataforma (ROAS, CPA, conversões view-through, frequência, CTR). Defina gatilhos de otimização — quando renovar criativo, ajustar lances, realocar orçamento ou expandir/contrair janelas de audiência.

12. **Crie a estrutura de UTM para rastreamento**: Construa uma convenção de nomenclatura UTM que permita rastreamento granular do retargeting por segmento, plataforma, variante criativa e estágio de funil. Execute `/mktos:links` para geração completa se necessário.

## Saída

Um documento de estratégia de retargeting contendo:

- **Definição dos segmentos de audiência**: tamanho estimado, janelas de recência e critérios comportamentais por segmento
- **Brief criativo por segmento**: temas de mensagem, formatos de anúncio e lógica de sequenciamento
- **Recomendações de cap de frequência**: limite por plataforma com justificativa
- **Plano de coordenação cross-platform**: qual plataforma serve qual papel no funil
- **Definição de listas de exclusão**: janelas de supressão de conversores e regras entre segmentos
- **Tabela de alocação de orçamento**: por segmento e plataforma com targets de ROAS
- **Guia de setup do retargeting dinâmico**: requisitos de feed e lógica de recomendação de produtos
- **Framework de KPIs**: targets por segmento, gatilhos de otimização e cadência de revisão
- **Estrutura de UTM**: convenção de nomenclatura para rastreamento de campanhas de retargeting
- **Roadmap de otimização 30/60/90 dias**: marcos e critérios de escala
- **Considerações de privacidade e conformidade**: consentimento de cookies, restrições de audiência LGPD/GDPR, limitações de privacidade por plataforma
- **Checklist de infraestrutura de rastreamento**: requisitos de verificação de pixel/tag por plataforma

## Integração Work Log

Após apresentar a estratégia, pergunte:

> "Quer registrar os próximos passos de implementação no work-log?"

Se confirmado, registre usando `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/log-tarefas.py" --action log` com `source_skill: retargeting` e `category: Ads`:

- **[Ads] Implementar segmentos de retargeting — [N segmentos] — [nome da conta]** → `priority: high`
- **[Ads] Configurar retargeting dinâmico — [plataforma]** → `priority: normal` (se catálogo disponível)
- **[Ads] Revisar performance de retargeting em 14 dias** → `priority: normal`

## Agentes Usados

- **gestor-trafego** — Segmentação de audiência, setup de retargeting por plataforma, gestão de frequência, alocação de orçamento, estratégia de lances, configuração de retargeting dinâmico e estrutura de campanha
- **marketing-strategist** — Estratégia de sequência criativa, coordenação cross-platform, arquitetura de mensagem por estágio de funil e roadmap de otimização

## Skills Relacionadas

- `/mktos:publico` — Pesquisa de personas e públicos-alvo (insumo para definição de segmentos)
- `/mktos:rastreamento` — Auditoria de pixels e tags (pré-requisito para construção de audiências)
- `/mktos:saude` — Monitoramento de fadiga de criativos ativos de retargeting
- `/mktos:links` — Geração de UTMs para rastreamento de campanhas de retargeting
