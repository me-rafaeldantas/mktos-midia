---
name: negativos
description: "Use quando o usuário quiser analisar o relatório de termos de busca do Google Ads para identificar desperdício de verba, detectar queries irrelevantes e gerar listas de palavras negativas. Focado em campanhas de Fundo de Funil e Meio/Fundo. Entrega resumo textual, arquivo formatado pronto para colar no Google Ads Editor e opção de aplicar via MCP."
argument-hint: "[conta ou campanha]"
---

# /mktos:negativos

## Propósito

Analisar o relatório de termos de busca do Google Ads para identificar termos "sujos" — irrelevantes, fora do portfólio, intenção errada — que estão consumindo verba sem converter. Focado em campanhas de Fundo de Funil (máxima transição Meio/Fundo), onde qualificação é crítica.

Entrega: resumo textual dos padrões encontrados + lista formatada pronta para colar no Google Ads Editor + opção de aplicar diretamente via MCP.

## Entrada Necessária

- **Relatório de termos de busca**: dados colados pelo usuário (tabela ou CSV) ou caminho de arquivo. Colunas esperadas: Termo de Pesquisa, Impressões, Cliques, Custo, Conversões, Valor Conv.
- **Contexto da conta**: carregado automaticamente do perfil ativo. Se não houver conta ativa, perguntar: nome da empresa, produto/serviço, o que NÃO faz parte do portfólio, termos da marca protegidos.
- **Período** (opcional): inferir dos dados se não informado explicitamente.

## Processo

### Etapa 1 — Carregar contexto da conta

Ler `./data/clientes/_conta-ativa.json` para obter o slug ativo. Carregar `./data/clientes/{slug}/perfil.json`. Extrair:
- `nome` — nome da empresa
- `produto` ou descrição do serviço — o que a empresa oferece
- `o_que_nao_fazemos` ou `excluded_products` — **o que a empresa NÃO faz, NÃO vende e NÃO atende**
- `vertical` — setor de atuação
- `regioes` ou `mercados_alvo` — região/público do serviço
- `marcas_proprias` ou variações — marcas próprias que **nunca devem ser negativadas**
- `moeda` — **BRL por padrão**; só usar moeda diferente se o campo `moeda` estiver explicitamente definido no perfil

**Se `o_que_nao_fazemos` estiver ausente ou vazio no perfil**, perguntar explicitamente antes de prosseguir:
> "Para filtrar bem os termos, preciso saber: **o que a [nome da empresa] NÃO faz ou NÃO vende?** Por exemplo: não aluga, não vende peças avulsas, não atende convênio, não cobre determinada região, não oferece parcelamento, etc."

Esta informação é crítica — ela permite negativar termos que parecem relevantes (e até convertem) mas estão fora do objetivo real da conta. Guarde a resposta para usar na classificação da Etapa 4.

Se não houver conta ativa, perguntar ao usuário todos os dados acima antes de prosseguir. Se necessário configurar conta: `/mktos:configurar`.

### Etapa 2 — Carregar negativos existentes (se MCP disponível)

Se `mcp__plugin_mktOS_google-ads` estiver conectado:
- Executar consulta GAQL para listar negativos atuais na conta/campanha:
  ```sql
  SELECT campaign_criterion.keyword.text, campaign_criterion.keyword.match_type
  FROM campaign_criterion
  WHERE campaign_criterion.type = 'KEYWORD' AND campaign_criterion.negative = true
  ```
- Guardar lista para: (a) evitar duplicatas, (b) detectar conflitos com as novas negativas propostas.

Se MCP não disponível: prosseguir sem dados de negativos existentes, avisar o usuário.

### Etapa 3 — Receber e normalizar o relatório de termos

Aceitar os dados do relatório de termos de busca colados pelo usuário ou como caminho de arquivo CSV/TSV. Normalizar colunas esperadas (aceitar variações de nome do Google Ads em PT-BR e EN):

| Esperado | Aceitar variações |
|---|---|
| Termo de Pesquisa | Search term, Termo de pesquisa, Query |
| Grupo de Anúncio | Ad group, Ad Group, Grupo de anúncio |
| Campanha | Campaign |
| Impressões | Impressions, Impr. |
| Cliques | Clicks |
| Custo | Cost, Spend, Gasto |
| Conversões | Conversions, Conv. |
| Valor Conv. | Conv. value, Valor de conversão |

**Detecção de múltiplos grupos de anúncio:** Se a coluna "Grupo de Anúncio" estiver presente e houver mais de um grupo distinto no relatório, registrar os grupos encontrados. Isso ativará a organização por grupo de anúncio na Etapa 8.

Se colunas de custo ou conversões estiverem ausentes: avisar e adaptar a análise (prioridade e custo desperdiçado não estarão disponíveis para esses termos).

### Etapa 4 — Classificar cada termo (matriz 2×2)

Para cada termo no relatório, classificar em uma das quatro categorias:

| | Com Conversão | Sem Conversão |
|---|---|---|
| **Relevante** | **Manter** — não negativar, considerar escalar | **Avaliar** — verificar volume mínimo e período |
| **Irrelevante** | ⚠️ **Analisar com cautela** — pode ter CPL ruim mas conversão real; avaliar antes de negativar | **Negativar** — desperdício ativo (ALTA) ou preventivo (MÉDIA) |

**Definição de "irrelevante" para este contexto (Fundo de Funil):**
- Intenção informacional ou exploratória ("como funciona", "o que é", "review", "vale a pena")
- Produto fora do portfólio declarado
- Serviço ou modalidade que a empresa **declarou não oferecer** (`o_que_nao_fazemos`) — mesmo que esteja convertendo
- Região ou destino não atendido
- Concorrentes (exceto se houver campanha de conquista explícita)
- Intenção de emprego, acadêmica ou DIY
- Genérico demais sem modificador qualificador

> **Regra "O que NÃO fazemos" prevalece sobre conversão:** se um termo converte mas corresponde a algo que a empresa declarou não oferecer (ex: "aluguel" para quem só vende, "convênio" para quem só atende particular), o correto é negativar e sinalizar ao usuário — a conversão pode ser de um lead que vai desqualificar no atendimento, gerando custo operacional. Apresentar esses casos em destaque no resumo.

**Regra inviolável:** Nunca classificar como negativa qualquer termo que contenha variações do nome da marca/produto do cliente (`marcas_proprias` do perfil).

**Limiar estatístico:**
- Antes de classificar "Avaliar" como definitivamente relevante ou irrelevante, verificar volume mínimo de cliques para o período do relatório (30–90 dias = 50+ cliques para contas até R$25k/mês; menos cliques = inconclusivo).

### Etapa 5 — Agrupar em categorias [NEG]

A partir dos termos irrelevantes identificados, criar categorias baseadas nos padrões recorrentes. Nomear no padrão `[NEG] Nome da Categoria`. Categorias típicas (adaptar ao contexto do cliente — criar, fundir ou eliminar conforme necessário):

- `[NEG] Concorrentes` — marcas e nomes de produtos concorrentes
- `[NEG] Produtos fora do portfólio` — o que o cliente não vende
- `[NEG] Fora do escopo declarado` — serviços/modalidades que a empresa declarou não oferecer (`o_que_nao_fazemos`); usar esta categoria separada para destacar negativas que podem ter conversão histórica
- `[NEG] Intenção informacional` — pesquisas sem intenção de compra (como, o que é, review, tutorial, grátis, dicas)
- `[NEG] Inapto para compra imediata` — usuário tem uma barreira objetiva que impede a compra agora (ex: "com problema", "com restrição", "sem entrada", "parcelado sem juros" quando não disponível, "aceita troca")
- `[NEG] Intenção de emprego` — vagas, salário, carreira, estágio
- `[NEG] Outras regiões/destinos` — localizações fora do escopo geográfico do cliente
- `[NEG] Genéricos sem qualificação` — termos amplos que não indicam o produto ou destino
- `[NEG] Varejo / Marketplace` — buscas por lojas físicas, marketplaces ou equipamentos
- `[NEG] DIY / Autoatendimento` — quando o cliente oferece serviço profissional, não tutorial

Criar categorias adicionais específicas ao negócio se padrões distintos forem detectados.

**Critério de nomeação:** as categorias viram listas compartilhadas no Google Ads. Nomes claros facilitam desvincular (ex: se o cliente decidir fazer campanha de conquista, "[NEG] Concorrentes" é fácil de remover).

### Etapa 6 — Definir correspondência e prioridade

Para cada negativa proposta:

**Tipo de correspondência:**
- **Ampla** → quando o objetivo é matar um conceito inteiro independente do contexto. Use para termos cujo significado é sempre irrelevante para este negócio, em qualquer combinação. Ex: `grátis`, `emprego`, `como fazer` — qualquer busca contendo essas palavras é indesejada. É a opção mais agressiva; confirmar com o usuário antes de aplicar.
- **Frase** (default, mais eficiente) → quando a raiz do termo é o problema mas combinações específicas podem ser relevantes. Ex: `"concorrente"` em frase bloqueia "concorrente preço" mas não afeta buscas onde a palavra aparece em outro contexto.
- **Exata** → apenas quando o bloqueio amplo ou de frase poderia capturar termos relevantes. Ex: `[serviço]` exato se "serviço profissional" é relevante mas "serviço grátis" não.

**Regra de seleção:** Ampla para conceitos universalmente irrelevantes → Frase para padrões específicos → Exata para termos ambíguos. Na dúvida, prefira Frase sobre Ampla para preservar alcance.

**Prioridade:**
- **ALTA** → termo com cliques registrados + custo desperdiçado no período, OU padrão com alto volume de impressões irrelevantes. Requer ação imediata.
- **MÉDIA** → preventivo, sem custo registrado ainda mas com risco de ativação futura.

**Custo desperdiçado:** somar o custo de todos os cliques sem conversão do termo no período do relatório.

### Etapa 7 — Verificar conflitos com keywords ativas

Comparar cada negativa proposta com as keywords positivas ativas (se disponível via MCP). Sinalizar antes de prosseguir qualquer caso onde uma negativa proposta poderia bloquear uma keyword ativa com bom desempenho.

Se não houver dados de keywords ativas: advertir o usuário para fazer esta verificação manualmente no Google Ads Editor antes de aplicar.

### Etapa 8 — Gerar outputs

#### a) Resumo textual (3–5 parágrafos)

- Total de termos analisados, total para negativar (ALTA + MÉDIA), custo desperdiçado identificado na moeda da conta
- Principais padrões encontrados e categorias criadas
- Recomendação de nível de aplicação: **conta** (para negativas universais ao negócio) vs **campanha** (para exclusões específicas de um produto ou segmento)
- Alertas de conflito, se houver
- Termos em "Avaliar" que merecem atenção antes de uma próxima rodada

#### b) Lista formatada para Google Ads Editor

Exibir no chat e salvar em `./data/clientes/{slug}/reports/negativos-{YYYY-MM-DD}.txt`.

**Organização da lista — depende do relatório:**

**Relatório com 1 grupo de anúncio (ou sem coluna de grupo):**
Gerar uma lista única organizada por categoria [NEG]. Recomendar nível de aplicação (conta ou campanha) no resumo.

**Relatório com múltiplos grupos de anúncio:**
Separar as negativas em duas seções:

1. **Nível de Conta** — padrões que aparecem em 3+ grupos ou que são universalmente irrelevantes para o negócio. Estas valem para toda a conta.
2. **Por Grupo de Anúncio** — termos irrelevantes específicos de um grupo (produto, segmento ou intenção particular). Entregar um bloco por grupo.

Se o relatório tiver mais de 5 grupos de anúncio distintos, **entregar em fila**: apresentar "Nível de Conta" + primeiro grupo, e perguntar:
> "Aprovado! Posso liberar o próximo grupo ([nome do próximo grupo])?"
Aguardar confirmação antes de continuar. Isso evita output excessivo e permite revisão incremental.

**Formato de saída (comum a todos os casos):**

Correspondência ampla sem aspas: `palavra`
Correspondência de frase entre aspas: `"palavra"`
Correspondência exata entre colchetes: `[palavra]`

Linha em branco entre cada bloco de categoria.

Exemplo com múltiplos grupos:
```
=== NÍVEL DE CONTA ===

[NEG] Intenção informacional (4 palavras)
como funciona
"o que é"
"tutorial"
"review"

[NEG] Intenção de emprego (2 palavras)
emprego
"vaga de"

=== GRUPO: [Nome do Grupo A] ===

[NEG] Produtos fora do portfólio — específico deste grupo (2 palavras)
"produto x"
"serviço y"
```

### Etapa 9 — Oferecer aplicação via MCP

Ao final, perguntar:

> "Quer que eu aplique as negativas ALTA prioridade diretamente na conta via Google Ads, ou prefere revisar a lista primeiro e aplicar manualmente?"

**Aprovação obrigatória antes de qualquer escrita no Google Ads.** Se o usuário confirmar aplicação via MCP:
- Usar `mcp__plugin_mktOS_google-ads__add_negative_keywords` agrupando por lista [NEG]
- Aplicar as negativas ALTA primeiro; perguntar se quer incluir as MÉDIA também
- Confirmar ao usuário: "[N] negativas aplicadas em [N] listas. Custo desperdiçado identificado: {moeda} [X]."

## Regras Críticas

1. **Nunca negativar marcas do cliente** — verificar `marcas_proprias` do perfil.json antes de qualquer operação
2. **"O que NÃO fazemos" supera conversão** — se o termo converte mas está no escopo do que a empresa declarou não oferecer, negativar e destacar no resumo. A conversão pode ser de leads que desqualificam no atendimento.
3. **Conversão prevalece para ambíguos** — fora do escopo de `o_que_nao_fazemos`, 1 conversão com CPL razoável = manter, mesmo que o termo pareça genérico
4. **Hierarquia de correspondência: Frase > Ampla > Exata** — Frase é o default seguro. Ampla para conceitos universalmente indesejados. Exata apenas para termos ambíguos onde bloqueio amplo causaria perda de alcance relevante.
5. **Nomear pensando em gestão futura** — listas com nomes claros são fáceis de desvincular depois (ex: "[NEG] Fora do escopo declarado" pode ser revisada se o portfólio mudar)
6. **Fundo/Meio-Fundo** — esta skill é calibrada para campanhas de intenção de compra; termos informativos que seriam aceitáveis em topo de funil são negativas aqui

## Integração Work Log

Após apresentar os resultados, perguntar:

> "Quer registrar as ações de negativação no work-log para acompanhamento?"

Se confirmado, registrar com `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/log-tarefas.py" --action log` e `source_skill: negativos`, `category: Ads`:

- **[Ads] Aplicar negativas ALTA prioridade — [N palavras] — [nome da conta]** → `priority: high` (se custo desperdiçado > R$50 ou equivalente)
- **[Ads] Aplicar negativas preventivas MÉDIA — [N palavras] — [nome da conta]** → `priority: normal`
- **[Ads] Monitorar impacto das negativas em 7 dias** → `priority: normal`

Se a aplicação via MCP foi executada diretamente nesta sessão: registrar a ação como `status: done`, com comment contendo número de negativas aplicadas, categorias criadas e custo desperdiçado identificado.

## Agentes Usados

- **gestor-trafego** — Classificação de intenção de busca, definição de match type, avaliação de risco de conflito, recomendação de nível de aplicação (conta vs campanha)

## Skills Relacionadas

- `/mktos:keywords` — Pesquisa de palavras-chave (complementar — positivas e negativas andam juntas)
- `/mktos:plano` — Criação de campanhas (inclui setup inicial de negativos)
- `/mktos:relatorio` — Relatório de performance que pode revelar desperdício por categoria de termo
