---
name: materiais
description: "Use quando o usuário precisar gerar um brief de produção criativa com specs técnicas de assets por plataforma — dimensões, safe zone, peso, codec, nomenclatura de arquivo e checklist de entrega para o designer."
argument-hint: "[plataformas] [objetivo]"
---

# /mktos:materiais

## Propósito

Gerar um brief de produção criativa completo para campanhas de mídia paga. Produz specs técnicas precisas por plataforma e formato, hierarquiza os assets por prioridade de produção, define diretrizes de copy por posição, gera a nomenclatura de arquivo correta e cria a tarefa de revisão no ClickUp para rastreabilidade do processo de produção.

## Entrada Necessária

O usuário deve fornecer (ou será solicitado):

- **Plataformas da campanha**: Google Ads, Meta, YouTube, LinkedIn, TikTok — ou "todas as plataformas ativas do cliente"
- **Objetivo da campanha**: awareness, consideração ou conversão — determina quais formatos priorizar
- **Formatos desejados** (opcional): feed, stories, reels, carrossel, display, bumper, skippable — se omitido, determinado pelo objetivo
- **Número de variantes**: quantas versões criativas por formato (padrão: 2)
- **Destino de entrega dos assets**: ClickUp, Google Drive, Figma, Canva ou entrega manual

## Processo

1. **Carregue contexto da conta**: Leia `./data/clientes/_conta-ativa.json` para obter o slug ativo, depois carregue `./data/clientes/{slug}/perfil.json`. Identifique `canais_ativos`, `vertical` e `brand_voice` para aplicar na direção criativa. Se nenhuma conta existir, pergunte: "Configurar uma conta primeiro (`/mktos:configurar`)?"

2. **Identifique plataformas da campanha atual**: Use os `canais_ativos` do perfil como padrão. Se o usuário informou plataformas específicas, use-as como override. Confirme a lista final antes de prosseguir.

3. **Determine formatos prioritários pelo objetivo**:
   - **Awareness**: feed estático 1:1, stories 9:16, bumper YouTube 6s
   - **Consideração**: feed 4:5, carrossel, reels/stories com CTA, skippable YouTube
   - **Conversão**: feed 1:1 com CTA direto, stories com swipe-up, display 300×250 + 728×90

4. **Execute `gerador-specs.py`** com as plataformas e formatos definidos:
   ```
   python3 "scripts/gerador-specs.py" \
     --platforms {plataformas} \
     --formats {formatos} \
     --variants {n_variantes} \
     --output-format json
   ```
   Use o output como fonte de verdade para todas as specs do brief. Nunca estime dimensões ou pesos — sempre use o script.

5. **Defina hierarquia de produção**:
   - **Obrigatório**: formats com `prioridade: obrigatorio` no output do script — sem estes, a campanha não pode ser lançada
   - **Recomendado**: formats com `prioridade: recomendado` — impactam coverage e performance
   - **Opcional**: formats com `prioridade: opcional` — produzir se houver capacidade

6. **Gere spec técnica completa por formato**: Para cada formato obrigatório e recomendado, estruture:
   - Dimensões: largura × altura em px
   - Ratio: ex. 1:1, 9:16, 1.91:1
   - Peso máximo: em MB ou KB
   - Safe zone: área segura em px (quando aplicável)
   - Regra de overlay de texto
   - Codec e extensão aceita (para vídeo)
   - Nomenclatura de arquivo: `{slug}-{plataforma}-{formato}-v{n}.{ext}`

7. **Gere diretrizes de copy por posição**: Para cada formato, especifique os limites de caracteres e instruções por campo:
   - **Google RSA**: headline 1-15 (máx 30 chars cada), descrição 1-4 (máx 90 chars cada), display URL
   - **Meta feed**: headline (máx 40 chars), primary text (máx 125 chars recomendado), CTA (botão nativo)
   - **Meta stories/reels**: texto overlay (máx 20% da área), CTA overlay ou sticker
   - **YouTube bumper (6s)**: mensagem única, logo nos primeiros 2s, CTA verbal nos últimos 2s
   - **YouTube skippable**: hook nos primeiros 5s (antes do skip), mensagem completa até 30s, CTA final
   - **TikTok in-feed**: caption (máx 100 chars), hook visual nos primeiros 3s, CTA nativo

8. **Defina checklist de entrega**:
   - Formato de exportação: JPG/PNG (imagem), MP4 H.264 (vídeo), HTML5 (display animado)
   - Nomenclatura de arquivo aplicada (listar cada arquivo esperado com nome exato)
   - Destino de entrega: pasta específica no Google Drive ou tarefa no ClickUp
   - Prazo de entrega: perguntar ao usuário se não informado

9. **Crie tarefa no ClickUp** com aprovação obrigatória antes de executar:
   Apresente o resumo da tarefa a criar: título, lista de assets, prazo. Aguarde confirmação do usuário. Após aprovação, use MCP `clickup-midify` para criar a tarefa com:
   - Título: `[Criativo] Brief {nome-cliente} — {N} assets {plataformas}`
   - Descrição: lista completa de assets com specs resumidas
   - Status inicial: "A produzir"

10. **Se Canva ou Figma conectados, pergunte**: "Quer que eu crie os frames com as dimensões corretas no Canva/Figma?" Se confirmado, use o MCP correspondente para criar frames com as dimensões exatas de cada formato obrigatório.

## Saída

Um brief de produção criativa completo contendo:

- **Tabela de specs por formato**: plataforma, formato, dimensões, ratio, peso máximo, safe zone, overlay de texto, codec e extensão
- **Hierarquia de produção**: assets ordenados por prioridade (obrigatório → recomendado → opcional) com justificativa
- **Diretrizes de copy por formato**: limites de caracteres por posição, instruções de CTA, regras de overlay
- **Lista de arquivos a entregar**: cada arquivo com nome exato seguindo nomenclatura `{slug}-{plataforma}-{formato}-v{n}.{ext}`
- **Checklist de entrega**: format de exportação, destino, prazo
- **Link da tarefa no ClickUp**: tarefa criada com lista de assets para acompanhamento de produção

## Agentes Usados

- **diretor-criativo** — Interpretação do objetivo, seleção de formatos prioritários, specs via `gerador-specs.py`, diretrizes de copy por posição, criação de frames no Canva/Figma, geração de nomenclatura

## Integração Work Log

Após gerar o brief, registre automaticamente usando `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/log-tarefas.py" --action log` com `source_skill: materiais` e `category: Criativo`. Em seguida, ofereça registrar também as tarefas de produção individuais:

> "Quer registrar cada asset como tarefa separada no work-log?"

Se confirmado, registre um item por asset obrigatório:

- **[Criativo] Produzir {plataforma} {formato} — {N} variantes** — `priority: high` para obrigatórios
- **[Criativo] Revisar e aprovar assets de {plataforma}** — `priority: normal`

Use `account_slug` da conta ativa.
