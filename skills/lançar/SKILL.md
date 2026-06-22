---
name: lançar
description: "Use quando o usuário quiser criar e lançar uma campanha de publicidade paga no Google Ads ou Meta, incluindo direcionamento de público, salvaguardas de orçamento e setup de monitoramento de performance."
argument-hint: "[plataforma]"
---

# /mktos:lançar

## Propósito

Cria e lança uma campanha de publicidade paga na plataforma de anúncio especificada com estrutura adequada de campanha, direcionamento de público, estratégia de lance, controles de orçamento e verificações de conformidade. Inclui salvaguardas de orçamento obrigatórias que requerem re-confirmação explícita quando gasto excede limites do cliente, e configura monitoramento pós-lançamento para detectar problemas de performance inicial antes que orçamento seja desperdiçado.

## Entrada Necessária

O usuário deve fornecer (ou será solicitado):

- **Plataforma de anúncio**: Onde lançar — Google Ads ou Meta Ads — deve ter servidor MCP correspondente conectado em `.mcp.json`
- **Objetivo da campanha**: Meta primária — awareness (alcance/impressões), consideração (tráfego/engajamento) ou conversão (leads/vendas/ROAS alvo)
- **Orçamento**: Orçamento diário ou vitalício com qualquer limite máximo de CPC ou CPA
- **Datas da campanha**: Data de início, data de fim e qualquer preferência de dayparting
- **Direcionamento de público**: Demográficos, interesses, comportamentos, públicos customizados, lookalikes e retargeting — com direcionamento geográfico e de idioma
- **Criativo de anúncio**: Headlines (múltiplas variantes), descrições, assets de imagem ou vídeo, URLs de destino e extensões aplicáveis
- **Estratégia de lance**: CPC manual, maximizar conversões, CPA alvo, ROAS alvo ou maximizar cliques — com bid cap quando aplicável
- **Rastreamento de conversão**: Quais eventos de conversão otimizar, status do pixel, janela de atribuição
- **Direcionamento negativo**: Palavras-chave negativas (Busca), exclusões de placement (Display) ou exclusões de público
- **Convenção de nomenclatura**: Formato customizado ou padrão para consistência de relatório
- **Parâmetros UTM**: Para todas as URLs de destino (source, medium, campaign, content)

## Processo

1. **Carregue contexto da conta**: Leia `./data/clientes/_conta-ativa.json` para obter o slug ativo, depois carregue `./data/clientes/{slug}/perfil.json`. Aplique regras de conformidade (`skills/context-engine/regras-conformidade.md`). Verifique SOPs em `./data/sops/`. Se nenhuma conta existir, pergunte: "Configurar uma conta primeiro (`/mktos:configurar`)?" — ou prossiga com padrões.
2. **Verifique orçamento contra limites da conta**: Verifique o orçamento da campanha contra `orcamento_mensal` em `perfil.json`. Se o orçamento configurado exceder o limite definido, interrompa e requeira re-confirmação explícita do usuário com o valor exato exibido. Este safeguard não pode ser contornado.
3. **Busque assets no ClickUp/Trello**: Antes de configurar os anúncios, pergunte ao usuário se há tarefa no ClickUp ou Trello com o criativo aprovado. Se informado, busque via MCP os arquivos anexados à tarefa. Confirme quais assets estão disponíveis antes de prosseguir.
4. **Verifique conexão da plataforma**: Confirme que o servidor MCP da plataforma alvo está configurado em `.mcp.json` e que o pixel de rastreamento está ativo. Se não configurado, instrua usar `/mktos:conectar` para setup.
5. **Construa estrutura de campanha**: Projete a hierarquia de campanha — nível de campanha (objetivo, orçamento, cronograma), nível de ad group/ad set (público, placement, lance) e nível de anúncio (criativo). Aplique convenções de nomenclatura do perfil para relatório limpo.
6. **Configure direcionamento de público**: Configure parâmetros de direcionamento por especificações de plataforma — consulte `skills/context-engine/specs-plataformas.md` para mapeamentos de campo, formatos de upload de público customizado e features específicas de plataforma.
7. **Conduza revisão de conformidade**: Verifique todo criativo contra requisitos específicos da indústria — disclaimers obrigatórios, categorias de conteúdo proibido e políticas de publicidade de plataforma. Sinalize qualquer criativo que precise de modificação antes do lançamento.
8. **Avalie qualidade do criativo**: Avalie — limites de caractere, relevância de keyword, specs de imagem/vídeo (dimensões, tamanho, sobreposição de texto no Meta), relevância da landing page e correspondência mensagem anúncio → página de destino.
9. **Configure estratégia de lance e controles de orçamento**: Configure estratégia de lance com guardrails — bid caps ou valores de CPA/ROAS alvo, pacing de orçamento, frequency caps, controles de placement e ajustes de dispositivo.
10. **Aplique direcionamento negativo**: Configure keywords negativas para Busca, exclusões de placement para Display/Vídeo e exclusões de público para evitar sobreposição e gasto desperdiçado.
11. **Crie registro de aprovação**: Execute `gerenciador-aprovacao.py` com nível de risco alto, ou crítico se orçamento diário exceder R$ 1.000. Gere resumo com alcance projetado, custo estimado, direcionamento, preview de criativo, verificação de orçamento e status de conformidade.
12. **Apresente resumo detalhado e aguarde aprovação**: Exiba a configuração completa da campanha — plataforma, objetivo, orçamento com status de safeguard, estimativas de tamanho de público, preview de criativo, estratégia de lance, alcance projetado e checklist de conformidade. **Aguarde aprovação explícita do usuário antes de qualquer ação MCP de escrita.**
13. **Execute criação de campanha via MCP**: Após aprovação confirmada, crie a campanha via MCP da plataforma. Configure status da campanha como **PAUSED por padrão** — ativar requer instrução explícita separada.
14. **Verifique status da campanha**: Após criação, consulte a API para confirmar que a campanha existe com configurações corretas, está no status PAUSED e não tem violações de política ou reprovações de anúncio.
15. **Atualize ClickUp após lançamento**: Via MCP `clickup-midify`, atualize o status da tarefa correspondente para "Campanha criada — [ID da campanha]". Se o usuário informou a tarefa no passo 3, use o ID fornecido; caso contrário, pergunte se deseja atualizar alguma tarefa.
16. **Configure cronograma de monitoramento**: Defina cadência pós-lançamento — verificar em 4h, 24h, 48h e 7 dias. Configure limites de alerta para CPC, CPM, CTR, taxa de conversão, CPA e pacing diário.
17. **Registre execução**: Execute `rastreador-execucao.py` para registrar o lançamento com timestamp, plataforma, ID da campanha, orçamento, direcionamento, assets criativos, estratégia de lance e cronograma de monitoramento.

## Saída

Uma confirmação de lançamento estruturada contendo:

- **ID de campanha e URL da plataforma**: Link direto para a campanha no gerenciador de anúncios para revisão e gerenciamento
- **Estrutura de campanha**: Nome da campanha, ad groups/ad sets e anúncios com direcionamento, criativos e estratégia de lance
- **Configuração de orçamento**: Orçamento diário ou vitalício, estratégia de lance, pacing, frequency caps e confirmação que está dentro dos limites da conta
- **Resumo de direcionamento de público**: Tamanho estimado por ad group, parâmetros de direcionamento e listas de exclusão aplicadas
- **Status de criativo**: Aprovação por políticas de plataforma, quality scores e eventuais problemas de política sinalizados
- **Performance projetada**: Alcance estimado, impressões, cliques, conversões, CPC, CPM e custo por resultado
- **Checklist de conformidade**: Pass/fail para políticas de publicidade, regulações da indústria e disclaimers obrigatórios
- **Cronograma de monitoramento**: Cadência de verificação pós-lançamento com limites de alerta e protocolo de escalação
- **Confirmação de atualização ClickUp**: Tarefa atualizada com ID da campanha criada
- **Entrada de log de execução**: Registro com timestamp do lançamento para trilha de auditoria

## Agentes Usados

- **gestor-trafego** — Design de estrutura de campanha, configuração de direcionamento, estratégia de lance, avaliação de qualidade de criativo, busca de assets no ClickUp/Trello e modelagem de projeção de performance
- **coordenador** — Safeguard de orçamento com re-confirmação obrigatória, fluxo de aprovação, execução via API, verificação de status, atualização do ClickUp, confirmação por email, setup de monitoramento e logging de execução

## Integração Work Log

Após confirmar o lançamento, registre automaticamente (sem perguntar — campanha criada é fato) usando `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/log-tarefas.py" --action log` com `source_skill: lançar` e `status: done` na criação. Em seguida, pergunte:

> "Quer registrar as tarefas de monitoramento pós-lançamento no work-log?"

Se confirmado, registre com `status: queued`:

- **[Ads] Verificar performance +4h — [nome da campanha] em [plataforma]** — `priority: high`
- **[Ads] Verificar performance +24h — [nome da campanha] em [plataforma]** — `priority: high`
- **[Ads] Verificar performance +48h — [nome da campanha] em [plataforma]** — `priority: normal`
- **[Ads] Revisão completa 7 dias — [nome da campanha] em [plataforma]** — `priority: normal`
- **[Ads] Refresh criativo em [data estimada]** — se rotação criativa foi definida no setup

O lançamento em si deve ser registrado com `category: Ads` e comentário inicial contendo: plataforma, ID da campanha, objetivo, orçamento diário e URL do dashboard na plataforma.
