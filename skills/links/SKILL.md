---
name: links
description: "Use quando o usuário precisar gerar URLs com parâmetros UTM para uma campanha — por canal, por adset, com validação GA4 channel group e planilha organizada por plataforma pronta para uso."
argument-hint: "[URL base] [nome da campanha]"
---

# /mktos:links

## Propósito

Gerar todas as URLs rastreadas de uma campanha em minutos. Produz UTMs corretos por canal seguindo os GA4 channel groups padrão, valida cada URL gerada, alerta sobre conflitos de parâmetros de plataforma (gclid, fbclid) e entrega uma planilha organizada por plataforma e adset pronta para colar no Google Ads Editor ou no Meta Ads Manager. URLs com UTMs errados são dados sujos no GA4 — e dados sujos levam a decisões erradas.

## Entrada Necessária

O usuário deve fornecer (ou será solicitado):

- **URL(s) base**: a landing page da campanha — uma única URL ou lista por canal (ex: URL diferente para Google vs. Meta)
- **Nome da campanha**: usado em `utm_campaign` — deve seguir a convenção de nomenclatura da conta
- **Canais da campanha**: quais plataformas serão usadas (Google Search, Google Display, Meta, TikTok, LinkedIn, YouTube)
- **Adsets ou grupos de anúncio** (opcional): se houver segmentação por público ou grupo, gerar URL por adset com `utm_content`
- **Termos de busca** (opcional, Google Search): para `utm_term` nas keywords principais

## Processo

1. **Carregue contexto da conta**: Leia `./data/clientes/_conta-ativa.json` para obter o slug ativo, depois carregue `./data/clientes/{slug}/perfil.json`. Use `canais_ativos` e `slug` do perfil. Se nenhuma conta existir, pergunte: "Configurar uma conta primeiro (`/mktos:configurar`)?"

2. **Colete os parâmetros da campanha**: Confirme com o usuário:
   - URL(s) base da campanha
   - Nome da campanha (será sanitizado: lowercase, underscores, sem acentos, ≤ 50 chars)
   - Canais a cobrir (use `canais_ativos` do perfil como sugestão padrão)
   - Adsets ou grupos de anúncio, se houver segmentação

3. **Verifique a convenção UTM de campanhas anteriores**: Execute:
   ```
   python3 "scripts/rastreador-campanhas.py" \
     --brand {slug} \
     --action get-insights \
     --type benchmark
   ```
   Se houver histórico de UTMs, use o mesmo padrão de `utm_source` e `utm_medium` já adotado pela conta. Sinalize ao usuário se o nome da campanha informada difere do padrão histórico.

4. **Valide cada URL base**: Para cada URL, confirme que o domínio é válido e acessível. Se a URL retornar erro ou redirect chain (3 ou mais redirects), alerte o usuário antes de gerar os UTMs — UTM em URL com redirect pode perder o parâmetro dependendo da configuração do servidor.

5. **Gere os UTMs por canal** via `gerador-utm.py` seguindo os GA4 channel groups padrão:

   | Canal | utm_source | utm_medium | GA4 Channel |
   |-------|-----------|-----------|-------------|
   | Google Search | google | cpc | Paid Search |
   | Google Display | google | display | Display |
   | Google PMax | google | cpc | Paid Search |
   | YouTube | youtube | video | Video |
   | Meta (Feed/Stories) | facebook | paid_social | Paid Social |
   | Instagram (separado) | instagram | paid_social | Paid Social |
   | TikTok | tiktok | paid_social | Paid Social |
   | LinkedIn | linkedin | paid_social | Paid Social |

   Para cada canal:
   ```
   python3 "scripts/gerador-utm.py" \
     --base-url "{url_base}" \
     --source {source} \
     --medium {medium} \
     --campaign "{utm_campaign}" \
     --content "{adset_ou_grupo}"
   ```
   Para `utm_content`: use o nome do adset ou grupo de anúncio sanitizado. Para `utm_term` (Google Search): informe a keyword principal do grupo.

6. **Verifique conflitos de parâmetros de plataforma**:
   - **Google Ads com auto-tagging ativado**: o `gclid` é adicionado automaticamente. Se o cliente usa auto-tagging, UTMs manuais no Google são desnecessários — a importação GA4→Google Ads já cuida do rastreamento. Alerte: "Se auto-tagging está ativo no Google Ads, UTMs manuais no Google podem criar dados duplicados. Confirme com o cliente qual método usar."
   - **Meta Ads**: o `fbclid` é adicionado automaticamente pelo Meta — nunca inclua manualmente. UTMs manuais no Meta coexistem com `fbclid` sem problema.
   - **ValueTrack parameters**: Se o cliente usa `{gclid}` ou `{lpurl}` no Google Ads, não adicione `utm_source=google` manualmente na URL do anúncio — o sistema sobrescreve.

7. **Rode `auditoria-rastreamento.py` em batch** em todas as URLs geradas:
   ```
   python3 "scripts/auditoria-rastreamento.py" \
     --action audit-utms \
     --urls '[{lista_de_urls_com_plataforma}]'
   ```
   Corrija automaticamente qualquer `quality_score < 100`. Apresente ao usuário apenas os issues que exigirem decisão humana (ex: conflito de auto-tagging). Não entregue URL com erros sem avisar.

8. **Gere a planilha de URLs**: Organize as URLs por plataforma e adset em formato tabular:

   ```
   Plataforma       | Adset / Grupo        | URL Final (copiar no anúncio)         | GA4 Channel
   Google Search    | Marca - Exato        | https://site.com?utm_source=google…   | Paid Search
   Google Search    | Concorrentes         | https://site.com?utm_source=google…   | Paid Search
   Meta             | Público Frio 25-40   | https://site.com?utm_source=facebook… | Paid Social
   Meta             | Retargeting 30d      | https://site.com?utm_source=facebook… | Paid Social
   ```

   Se o usuário tiver adsets com URLs diferentes, separe em blocos por URL base.

9. **Salve o mapeamento UTM→campanha** via `rastreador-campanhas.py`:
   ```
   python3 "scripts/rastreador-campanhas.py" \
     --brand {slug} \
     --action save-campaign \
     --data '{"name": "{nome_campanha}", "utm_campaign": "{utm_campaign}", "channels": [{canais}], "urls": [{urls_geradas}], "created_at": "{data}"}'
   ```

## Saída

Entrega completa de URLs da campanha:

- **Tabela de URLs por plataforma e adset**: URL final com UTMs completos, canal GA4 esperado e `quality_score` — pronta para colar no editor de cada plataforma
- **Alertas de conflito**: auto-tagging Google, redirect chains, `utm_campaign` > 50 chars, parâmetros de plataforma que não devem ser duplicados
- **Resumo da auditoria UTM**: total de URLs geradas, quality score médio, número de issues resolvidos automaticamente
- **Convenção de nomenclatura adotada**: `utm_source`, `utm_medium` e padrão de `utm_content` usados — para referência futura e consistência

## Agentes Usados

- **gestor-trafego** — Definição de `utm_source` e `utm_medium` corretos por plataforma, orientação sobre auto-tagging vs. UTM manual por plataforma, alerta sobre conflitos de parâmetros ValueTrack

## Integração Work Log

Após entregar as URLs, registre automaticamente usando `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/log-tarefas.py" --action log` com `source_skill: links` e `category: Ads`:

- **[Ads] URLs UTM geradas — {nome_campanha} — {N} canais** — `priority: normal`

Em seguida, pergunte:

> "Quer que eu também valide a nomenclatura das campanhas nas plataformas (`/mktos:rastreamento`)?"

Use `account_slug` da conta ativa.
