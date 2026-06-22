---
name: keywords
description: "Use quando o usuário precisar de pesquisa de palavras-chave — sugestões por seed ou URL, agrupamento por tema/intenção, ranking de oportunidade, separação Search vs. Display e lista de negativos para importação no Google Ads."
argument-hint: "[seed-keywords ou URL]"
---

# /mktos:keywords

## Propósito

Realizar pesquisa completa de palavras-chave para campanhas de Google Ads. Busca sugestões via Keyword Planner, agrupa por tema e intenção de busca, pontua por oportunidade (volume × CPC × competição) e entrega listas formatadas de keywords positivas e negativas prontas para importação. Pesquisa de keywords bem feita é a diferença entre uma campanha que encontra o público certo e uma que queima budget em tráfego irrelevante.

## Entrada Necessária

O usuário deve fornecer (ou será solicitado):

- **Seed keywords ou URL de referência**: palavras-chave semente (ex: "escola técnica, cursos técnicos") ou URL do site/landing page do cliente — a API sugere keywords com base no conteúdo da página
- **Idioma**: pt (padrão), en, es — define o idioma das sugestões
- **Geo**: região de targeting — Brasil (padrão), estado ou cidade específica
- **Objetivo da campanha** (opcional): define se separar para Search ou Display

## Processo

1. **Carregue contexto da conta**: Leia `./data/clientes/_conta-ativa.json` para obter o slug ativo, depois carregue `./data/clientes/{slug}/perfil.json`. Use `vertical`, `canais_ativos` e `google_ads_id` do perfil. Se nenhuma conta existir, pergunte: "Configurar uma conta primeiro (`/mktos:configurar`)?"

2. **Colete parâmetros de pesquisa**: Pergunte ao usuário:
   - "Keywords semente ou URL de referência?"
   - "Geo: Brasil ou região específica? (ex: estado RJ, cidade São Paulo)"
   - "Idioma: pt (padrão) ou outro?"
   Se o usuário informar o cliente e já houver `vertical` no perfil, use-o como contexto para seed keywords adicionais.

3. **Execute a pesquisa em cascata** — tente cada nível em sequência, avançando ao próximo apenas se o anterior falhar:

   **Nível 1 — API Google Ads (automático)**
   ```
   python3 "scripts/planejador-keywords.py" \
     --account {google_ads_id} \
     --action suggest \
     --seed-keywords "{keywords}" \
     --language {lang} \
     --geo {geo_code}
   ```
   Para URL como referência: use `--url "{url}"` no lugar de `--seed-keywords`.
   Se `"status": "ok"` → siga para o passo 4. Fim da cascata.

   ---

   **Nível 2 — CSV exportado do Keyword Planner** (se API retornar `"status": "fallback"`)

   Apresente ao usuário as instruções de exportação:
   > "Não consegui acessar o Keyword Planner via API. Para continuar com dados reais do Google:
   > 1. Acesse **Google Ads → Ferramentas → Planejador de palavras-chave**
   > 2. Selecione **Encontre novas palavras-chave** e busque por: `{seed_keywords}`
   > 3. Na tabela de resultados, clique em **↓ Baixar ideias de palavras-chave** (ícone no topo da tabela)
   > 4. Salve o arquivo CSV e informe o caminho aqui"

   Quando o usuário fornecer o caminho:
   ```
   python3 "scripts/planejador-keywords.py" \
     --action import-csv \
     --file "{caminho_do_arquivo}"
   ```
   Se `"status": "ok"` → siga para o passo 4. Anote `(fonte: CSV)` no cabeçalho do relatório. Fim da cascata.

   ---

   **Nível 3 — WebSearch estimado** (se o usuário não puder ou não quiser trazer o CSV)

   Avise antes de prosseguir:
   > "Sem acesso ao CSV, vou buscar estimativas em fontes públicas. Os dados serão marcados como **estimados** — use para identificar temas e intenções, não para planejar lances ou orçamento."

   Use WebSearch para buscar volume e CPC aproximados para cada seed keyword (fontes: Google Trends para tendência relativa, Ubersuggest plano gratuito, dados públicos SEMrush). Monte o mesmo JSON de saída com os campos padrão e `"data_source": "websearch_estimated"`.

   Adicione o seguinte aviso no topo do relatório final:
   > ⚠️ **Dados estimados** — origem: WebSearch. Use para orientação temática, não para definir lances ou orçamento. Valide com o Keyword Planner quando possível.

4. **Agrupe keywords por tema e intenção de busca**:
   - **Comercial**: termos com intenção de compra direta — preço, contratar, serviço, valor (ex: "curso técnico preço", "matricular escola técnica")
   - **Informacional**: termos buscando aprender ou comparar — como, o que é, diferença, melhor (ex: "como fazer curso técnico", "quanto tempo dura")
   - **Navegacional**: termos que buscam uma marca ou site específico (ex: "escola técnica [nome]")
   - **Transacional**: termos prontos para agir — cadastrar, inscrever, solicitar, agendar (ex: "inscrição curso técnico 2026", "agendar visita escola")

5. **Pontue por oportunidade**: Para cada keyword, calcule um score de oportunidade baseado em:
   - Volume mensal (`avg_monthly_searches`) — maior = melhor
   - CPC (`high_top_of_page_bid_micros`) — reflete valor comercial
   - Competição invertida (`competition_index`) — menor competição = maior oportunidade
   - Fórmula: `score = (volume / 1000) × (cpc_brl × 0.5) × ((100 - competition_index) / 100)`
   Classifique como: Alta oportunidade (score > 10), Média (3–10), Baixa (< 3).

6. **Separe para Search vs. Display**:
   - **Search**: keywords de alta intenção (comercial + transacional), volume médio/alto, CPC justificado — usar como keywords exatas ou de frase
   - **Display**: keywords temáticas e informacionais, broad match — usar para targeting contextual de Display e PMax
   Identifique variações de cauda longa (3+ palavras) com competição LOW ou MEDIUM — geralmente melhor custo-eficiência para Search.

7. **Identifique cauda longa de menor competição**: filtre keywords com 3+ palavras e `competition` LOW ou MEDIUM. Estas são candidatas prioritárias para grupos de anúncio específicos com Quality Score alto.

8. **Gere lista de keywords negativas sugeridas**: Analise o conjunto de keywords e identifique termos que indicam intenção errada ou público não relevante:
   - Termos de emprego se o cliente não recruta (ex: "vagas", "emprego", "salário")
   - Termos competitivos de outras verticais
   - Termos geográficos fora do targeting do cliente
   - Modificadores de pesquisa gratuita quando o produto é pago ("grátis", "gratuito", "de graça")

9. **Salve lista de keywords no contexto do cliente** via `rastreador-campanhas.py`:
   ```
   python3 "scripts/rastreador-campanhas.py" \
     --brand {slug} \
     --action save-insight \
     --data '{"type": "keyword-research", "date": "{data}", "seed": "{seed}", "top_keywords": [{top_10}], "negatives": [{negatives}]}'
   ```

## Saída

Um relatório de pesquisa de keywords estruturado em:

- **Resumo**: total de keywords encontradas, distribuição por intenção, geo e idioma da pesquisa
- **Tabela por grupo temático**: para cada grupo — keyword, volume mensal, CPC mínimo (R$), CPC máximo (R$), competição (LOW/MEDIUM/HIGH), score de oportunidade, recomendação (Search/Display/Cauda Longa)
- **Top 20 keywords de oportunidade**: ranking das melhores palavras-chave para a campanha por score, com tipo de match recomendado (exato/frase/ampla modificada)
- **Cauda longa prioritária**: lista separada de keywords 3+ palavras com menor competição — candidatas para grupos específicos
- **Lista de negativos sugeridos**: keywords a bloquear com justificativa por categoria (intenção errada, fora do geo, pesquisa informacional para campanha de conversão)
- **Pronta para importação**: colunas formatadas para upload direto no Google Ads Editor ou interface da plataforma

## Agentes Usados

- **gestor-trafego** — Interpretação da intenção de busca por vertical, seleção de tipo de match por estágio de funil, separação Search vs. Display, benchmarks de CPC esperado por nicho e recomendações de estrutura de grupos de anúncio

## Integração Work Log

Após entregar o relatório, pergunte ao usuário:

> "Quer registrar esta pesquisa de keywords no work-log?"

Se confirmado, registre usando `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/log-tarefas.py" --action log` com `source_skill: keywords` e `category: Ads`:

- **[Ads] Pesquisa de keywords — {seed ou domínio} — {N} keywords mapeadas** — `priority: normal`
- **[Ads] Configurar grupos de anúncio — {N} grupos temáticos identificados** — `priority: normal` (se o usuário quiser avançar para estruturação de campanha)

Use `account_slug` da conta ativa.
