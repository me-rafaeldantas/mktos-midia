---
name: criativo
description: "Use quando o usuário precisar de variações de copy de anúncio específicas por plataforma — headlines RSA, primary text Meta, copy LinkedIn, scripts TikTok — com pontuação de qualidade e plano de teste A/B."
argument-hint: "[plataforma]"
---

# /mktos:criativo

## Propósito

Gerar variações de copy de anúncio de alta performance adaptadas para cada plataforma e formato. Cada variação é pontuada por qualidade e compliance, com recomendações de estratégia de teste A/B. Nenhuma variante sai sem pontuação — o usuário sempre sabe qual escolher primeiro e por quê.

## Entrada Necessária

O usuário deve fornecer (ou será solicitado):

- **Produto ou serviço**: O que está sendo anunciado
- **Plataforma(s)**: Google Ads, Meta, LinkedIn, TikTok
- **Formato do anúncio**: RSA, imagem única, carrossel, script de vídeo, stories, etc.
- **Objetivo da campanha**: Awareness, tráfego, leads, conversões
- **Público-alvo**: Para quem os anúncios são direcionados
- **Oferta ou CTA principal**: Promoção, proposta de valor ou ação desejada
- **URL da landing page** (opcional): Para verificar alinhamento de mensagem

## Processo

1. **Carregue contexto da conta**: Leia `./data/clientes/_conta-ativa.json` para obter o slug ativo, depois carregue `./data/clientes/{slug}/perfil.json`. Aplique voz da marca (`brand_voice`), vertical e regras de conformidade (`skills/context-engine/regras-conformidade.md`). Verifique SOPs em `./data/sops/`. Se nenhuma conta existir, pergunte: "Configurar uma conta primeiro (`/mktos:configurar`)?" — ou prossiga com padrões.

2. **Identifique restrições específicas da plataforma**: limites de caracteres, requisitos de formato, restrições de política. Consulte `skills/context-engine/specs-plataformas.md` e `skills/context-engine/regras-conformidade.md`. Para categorias especiais (saúde, crédito, imóveis, política), aplique verificações adicionais.

3. **Gere 3 a 5 variações de copy por plataforma**, cada uma com ângulo distinto:
   - **Benefício racional**: o que o produto entrega objetivamente
   - **Urgência**: tempo limitado, escassez, prazo
   - **Prova social**: resultados de outros clientes, números, depoimentos
   - **Curiosidade**: pergunta ou afirmação que instiga o clique
   - **Direto/CTA forte**: oferta clara sem rodeios

4. **Pontue cada variação com `analisador-headlines.py`** (para headlines) e `avaliador-conteudo.py` (para copy completo):
   ```
   python3 "scripts/analisador-headlines.py" --headline "Seu headline aqui"
   python3 "scripts/avaliador-conteudo.py" --text "copy completo" --type ad --keyword "palavra-chave"
   ```
   Inclua a pontuação (0–100) e o principal fator que elevou ou reduziu o score em cada variante.

5. **Sinalize possíveis violações de política**: alegações proibidas, linguagem restrita, categorias de anúncio especial que exigem declaração ou aprovação prévia na plataforma.

6. **Recomende agrupamentos de teste A/B**: qual variável testar primeiro (ângulo de copy, CTA, formato de headline), orçamento mínimo para significância estatística, duração estimada do teste.

7. **Se URL de landing page fornecida**: verifique alinhamento de mensagem — o headline do anúncio deve espelhar a promessa principal da página. Sinalize desalinhamentos que prejudicam o Quality Score (Google) ou relevance score (Meta).

## Saída

Por plataforma, um conjunto de variações de copy contendo:

- **Headlines, descrições e CTAs** formatados às specs da plataforma (limites de caracteres respeitados)
- **Pontuação de qualidade** (0–100) com principal fator positivo e negativo por variação
- **Checklist de compliance** com problemas sinalizados e sugestão de correção
- **Recomendação de teste A/B**: quais variações testar primeiro, hipótese por teste e critério de vencedor
- **Avaliação de alinhamento com landing page** (se URL fornecida)
- **Direção criativa visual**: notas de direção para o asset de imagem ou vídeo que acompanha cada variante

## Agentes Usados

- **diretor-criativo** — Geração de copy, desenvolvimento de ângulos, pontuação com `analisador-headlines.py` e `avaliador-conteudo.py`, verificação de specs de plataforma, direção visual e design de variantes para teste A/B
- **gestor-trafego** — Specs de plataforma, compliance de política, estratégia de teste e benchmarks de performance esperada por formato

## Integração Work Log

Após entregar as variações, pergunte ao usuário:

> "Quer registrar as variantes aprovadas no work-log para acompanhamento de produção?"

Se confirmado, registre usando `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/log-tarefas.py" --action log` com `source_skill: criativo` e `category: Criativo`:

- **[Criativo] Produzir assets para {N} variantes aprovadas — {plataforma}** — `priority: high`
- **[Criativo] Configurar teste A/B — {variante A} vs {variante B}** — `priority: normal`

Use `account_slug` da conta ativa.
