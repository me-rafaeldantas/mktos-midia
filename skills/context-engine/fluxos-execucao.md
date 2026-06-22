# Fluxos de Execução — Procedimentos Operacionais Padrão

Toda execução de marketing segue fluxos de trabalho padronizados para garantir consistência, qualidade e conformidade. Cada fluxo é um procedimento numerado passo a passo que os agentes seguem durante a execução. Pular etapas não é permitido — se uma etapa não se aplicar, registre-a como "N/A" com uma justificativa.

---

## 1. Fluxo de Publicação de Blog

Usar para: posts de blog, artigos, guias, listicles, conteúdo how-to, thought leadership.

### Preparação de Conteúdo

1. **Verificação de formato** — Confirme que o conteúdo está no formato do CMS de destino (HTML para WordPress, rich text para Webflow). Remova elementos não suportados.
2. **Validação de contagem de palavras** — Confirme que a contagem de palavras atende ao brief de conteúdo. Mínimos por tipo:
   - Post de blog padrão: 800-1.500 palavras
   - Pillar page: 2.000-4.000 palavras
   - Post de notícia/atualização: 400-800 palavras
3. **Pontuação de legibilidade** — Execute análise de legibilidade. Meta de nível Flesch-Kincaid por público:
   - B2C geral: Nível 6-8 (Flesch score 60-70)
   - B2B profissional: Nível 10-12 (Flesch score 40-55)
   - Técnico/desenvolvedor: Nível 12-14 (Flesch score 30-45)
4. **Verificação de voz da marca** — Pontue o conteúdo contra o perfil de voz da marca. Pontuação mínima: 70/100.

### Otimização SEO

5. **Posicionamento da palavra-chave principal** — Verifique se a palavra-chave principal aparece em:
   - Título da página (dentro dos primeiros 60 caracteres)
   - Heading H1 (exatamente uma vez)
   - Primeiras 100 palavras do texto
   - Pelo menos um subtítulo H2
   - Slug da URL
6. **Meta description** — Escreva ou verifique a meta description: 150-160 caracteres, inclui a palavra-chave principal, contém uma proposta de valor clara ou CTA.
7. **Alt text** — Toda imagem tem alt text descritivo. Inclua a palavra-chave principal em pelo menos um alt de imagem (naturalmente, sem forçar).
8. **Links internos** — Mínimo de 3 links internos para conteúdo relevante existente. Pelo menos 1 link nas primeiras 300 palavras. Anchor text descritivo (não "clique aqui").
9. **Links externos** — Inclua 1-3 fontes externas de autoridade quando relevante. Configure `target="_blank" rel="noopener"`.
10. **Schema markup** — Aplique o schema JSON-LD apropriado (`BlogPosting`, `Article` ou `HowTo`).

### Publicação

11. **Atribuição de categoria e tag** — Atribua exatamente 1 categoria primária e 2-5 tags relevantes. Use a taxonomia existente; crie novos termos apenas quando não houver correspondência.
12. **Imagem destacada** — Faça upload da imagem destacada conforme as specs da plataforma (WordPress: mínimo 1200x628 px). Verifique se ela é exibida corretamente no preview de compartilhamento social.
13. **Agendar ou publicar** — Se agendar, confirme que a data/hora de publicação está alinhada com o calendário de conteúdo. Se publicar imediatamente, confirme com o usuário.
14. **Verificar URL ao vivo** — Após a publicação, confirme que a URL ao vivo responde com HTTP 200. Verifique se a página renderiza corretamente (sem imagens quebradas, sem problemas de layout).
15. **Registrar execução** — Registre no rastreador de campanhas: URL, data de publicação, palavra-chave principal, contagem de palavras, pontuação de legibilidade, pontuação SEO.
16. **Monitorar primeiras 24h** — Verifique pageviews, bounce rate e tempo médio na página após 24 horas. Alerte se os pageviews estiverem abaixo de 50% da média do blog da marca.

---

## 2. Fluxo de Campanha de E-mail

Usar para: e-mails de marketing, newsletters, sequências de drip, disparos promocionais, convites para eventos.

### Seleção de Lista

1. **Identificação de segmento** — Selecione o segmento-alvo com base no brief da campanha. Documente nome do segmento, tamanho e critérios de seleção.
2. **Verificação do tamanho da lista** — Confirme a contagem de destinatários. Alerte se a contagem desviar mais de 20% do tamanho esperado.
3. **Verificação de consentimento** — Verifique se todos os destinatários têm consentimento de marketing válido conforme a regulamentação aplicável:
   - Regiões GDPR: Consentimento opt-in registrado
   - Regiões CAN-SPAM: Nenhum opt-out registrado
   - Regiões CASL: Consentimento expresso ou implícito válido (verificar validade)
4. **Verificação de supressão** — Cruze com a lista de supressão (descadastros, bounces, reclamações). Remova qualquer correspondência.

### Construção do Template

5. **Linha de assunto** — Escreva a linha de assunto: 30-50 caracteres para segurança mobile. Pontue contra a rubrica de avaliação de e-mail (mínimo 70/100).
6. **Texto de preview** — Escreva o preheader: 40-90 caracteres. Deve complementar (não repetir) a linha de assunto.
7. **Estrutura do corpo** — Construa o corpo do e-mail: hierarquia clara (headline, corpo, CTA), coluna única para mobile-first, CSS inline para compatibilidade.
8. **Posicionamento do CTA** — Botão CTA primário acima da dobra. Repita o CTA no final do e-mail. Botão com mínimo de 44x44 px de área de toque.
9. **Mapeamento de personalização** — Mapeie merge tags para campos de dados. Teste se todas as merge tags resolvem corretamente. Defina valores de fallback para campos vazios.
10. **Link de descadastro** — Confirme que um mecanismo de descadastro funcional está presente e visível. Cabeçalho de descadastro com um clique incluído.

### Garantia de Qualidade

11. **Verificação de spam score** — Execute o conteúdo pela análise de spam. Meta de pontuação SpamAssassin abaixo de 5,0. Marque palavras gatilho (grátis, garantia, aja agora, tempo limitado).
12. **Envio de teste** — Envie para lista de seed interna (mínimo 3 endereços entre Gmail, Outlook, Apple Mail).
13. **Revisão de renderização** — Verifique renderização em desktop e mobile. Verifique compatibilidade com modo escuro. Confirme que imagens carregam e que o alt text é exibido quando imagens estão bloqueadas.

### Envio

14. **Gate de aprovação** — Obtenha aprovação explícita do usuário autorizado antes de enviar.
15. **Agendar ou enviar** — Defina o horário de envio com base na saída do analisador de horário de postagem ou no melhor horário estabelecido pela marca. Respeite o horário de silêncio (sem envios entre 21h-8h no fuso horário local do destinatário).
16. **Monitorar entrega** — Acompanhe nas primeiras 2 horas:
    - Entregabilidade: Meta > 95%
    - Taxa de bounce: Alerte se > 3%
    - Taxa de descadastro: Alerte se > 0,5%
    - Reclamações de spam: Alerte se > 0,1%
17. **Registro de desempenho** — Registre: data de envio, tamanho da lista, linha de assunto, taxa de abertura, taxa de clique, taxa de conversão, receita atribuída.

---

## 3. Fluxo de Campanha de Anúncios

Usar para: Google Ads, Meta Ads, LinkedIn Ads, TikTok Ads, Pinterest Ads, Amazon Ads.

### Estrutura da Campanha

1. **Hierarquia da campanha** — Configure: Campanha (objetivo, orçamento, cronograma) → Grupo de Anúncios/Ad Set (segmentação, lance) → Anúncio (criativo, copy, CTA, URL de destino).
2. **Convenção de nomenclatura** — Aplique a nomenclatura padrão: `{Marca}_{Objetivo}_{Público}_{Plataforma}_{Data}`. Exemplo: `Acme_Leads_Retargeting_Meta_2026-02`.

### Configuração de Público

3. **Definição de segmentação** — Configure o público: dados demográficos, interesses, comportamentos, localizações geográficas. Documente todos os parâmetros de segmentação.
4. **Exclusões** — Defina públicos de exclusão: clientes existentes (se prospectando), conversores recentes, tráfego interno, funcionários de concorrentes (se possível).
5. **Públicos semelhantes/lookalike** — Se usar, especifique o público-fonte (mínimo 1.000 contatos para Meta, 300 para LinkedIn) e percentual de similaridade (1-3% para precisão, 5-10% para alcance).

### Criativo

6. **Upload de criativo** — Prepare os assets conforme as specs da plataforma (consulte `platform-specs.md` e `platform-publishing-specs.md`). Mínimo de 3 variações de criativo para teste A/B.
7. **Copy do anúncio** — Escreva copy respeitando os limites de caracteres da plataforma. Pontue contra a rubrica criativa de anúncios (mínimo 70/100 para lançar).
8. **Landing page** — Verifique se a URL de destino carrega em menos de 3 segundos, corresponde à mensagem do anúncio (message match) e tem rastreamento de conversão funcionando.

### Orçamento e Lances

9. **Seleção de estratégia de lance** — Escolha a estratégia alinhada ao objetivo da campanha:
   - Awareness: Maximizar alcance / CPM alvo
   - Tráfego: Maximizar cliques / CPC alvo
   - Conversões: Maximizar conversões / CPA alvo / ROAS alvo
10. **Orçamento diário** — Defina o orçamento diário dentro do `budget_range` da marca. Nunca exceda o orçamento diário máximo da marca sem reconfirmação explícita do usuário.
11. **Pacing de orçamento** — Configure distribuição diária uniforme, salvo se o brief especificar o contrário (ex: dayparting, entrega acelerada).

### Conformidade e Lançamento

12. **Revisão de conformidade** — Verifique contra as políticas de anúncios da plataforma (consulte `compliance-rules.md` Seção 4). Verifique os disclaimers obrigatórios para setores regulamentados. Confirme a designação de Categoria Especial de Anúncio se aplicável (moradia, crédito, emprego).
13. **Rastreamento de conversão** — Verifique se o pixel/tag dispara corretamente na página de conversão. Teste com um clique antes do lançamento.
14. **Lançamento** — Ative a campanha. Confirme que o status mostra "Ativo" ou "Em execução" (não "Limitado" ou "Erro").

### Otimização

15. **Verificação em 48 horas** — Revise: impressões, CTR, CPC. Pause criativos com baixo desempenho (CTR abaixo de 50% da média do grupo de anúncios). Confirme que o orçamento está pacing corretamente.
16. **Otimização em 7 dias** — Revise: CPA, ROAS, taxa de conversão. Ajuste lances, realoque orçamento de grupos de anúncios com baixo desempenho. Adicione palavras negativas (campanhas de pesquisa).
17. **Revisão em 14 dias** — Revisão completa de desempenho: verificação de fadiga criativa (frequência > 3,0), saturação de público, eficiência do orçamento. Renove criativos se o CTR tiver caído > 20% desde o lançamento.
18. **Registro de desempenho** — Registre: impressões, cliques, CTR, CPC, conversões, CPA, ROAS, gasto. Compare com benchmarks do setor de `industry-profiles.md`.

---

## 4. Fluxo de Agendamento Social

Usar para: posts orgânicos de mídia social em todas as plataformas.

1. **Formato de conteúdo** — Prepare o conteúdo conforme as especificações da plataforma (consulte `platform-specs.md`). Respeite os limites de caracteres, tamanhos de imagem e limites de duração de vídeo por plataforma.
2. **Formatação por plataforma** — Adapte o conteúdo para a cultura de cada plataforma:
   - LinkedIn: Tom profissional, insights do setor, parágrafos com quebras de linha
   - Instagram: Visual em primeiro lugar, legenda com quebras de linha, emojis adequados à voz da marca
   - Twitter/X: Conciso, conversacional, formato de thread para conteúdo longo
   - TikTok: Vídeo nativo, consideração de áudio em tendência, tom casual
3. **Pesquisa de hashtags** — Selecione 3-5 hashtags por post. Mix: 1-2 de alto alcance (100K+ posts), 2-3 de nicho/específicas do setor (1K-100K posts). Exceções por plataforma: Twitter/X (1-2 máx), LinkedIn (3-5), Instagram (5-10).
4. **Melhor horário de postagem** — Use a saída do analisador de horário de postagem ou os melhores horários estabelecidos pela marca. Consulte as recomendações gerais de `platform-specs.md`.
5. **Assets visuais** — Verifique se todas as imagens/vídeos atendem aos requisitos de dimensão e tamanho de arquivo da plataforma. Verifique as zonas de texto seguras para conteúdo de Stories/Reels.
6. **Agendamento** — Coloque o post na fila na ferramenta de agendamento ou no agendador nativo da plataforma. Confirme se o horário agendado está correto (atenção ao fuso horário).
7. **Monitoramento de engajamento** — Verifique o engajamento em 2 horas e 24 horas após a postagem. Responda a comentários dentro das diretrizes da marca.
8. **Relatório de desempenho** — Em 24 horas e 7 dias, registre: impressões, alcance, taxa de engajamento, salvamentos, compartilhamentos, cliques em link (se aplicável). Compare com a média móvel de 30 dias da marca.

---

## 5. Fluxo de Operações de CRM

Usar para: importações de contatos, criação de leads, atualizações de dados, gerenciamento de listas, operações de pipeline.

1. **Validação de dados** — Verifique todos os registros quanto aos campos obrigatórios. Valide formatos:
   - E-mail: Compatível com RFC 5322, domínio tem registro MX
   - Telefone: Formato E.164 (internacional), remova caracteres não numéricos
   - URL: Deve incluir protocolo (https://)
   - País/Estado: Códigos ISO 3166
2. **Verificação de deduplicação** — Execute a deduplicação usando hierarquia de correspondência:
   - Primário: Endereço de e-mail (correspondência exata)
   - Secundário: Número de telefone (normalizado)
   - Terciário: Nome da empresa + nome do contato (correspondência difusa, > 85% de similaridade)
3. **Mapeamento de campos** — Mapeie os campos de origem para os campos nativos do CRM. Documente quaisquer campos não mapeados. Crie campos personalizados apenas com aprovação explícita.
4. **Snapshot pré-importação** — Faça um backup dos registros afetados antes de qualquer operação em lote. Armazene o caminho do snapshot no log de execução.
5. **Importar/criar** — Execute a importação. Para operações em lote (> 100 registros): use endpoints de API em batch, implemente rate limiting conforme as specs do fornecedor do CRM.
6. **Verificação** — Confirme: contagem de registros corresponde ao esperado, sem truncamento de dados, todos os campos obrigatórios preenchidos. Verifique aleatoriamente 5 registros para precisão.
7. **Vinculação de campanha** — Associe os contatos importados à campanha/lista relevante no CRM.
8. **Entrada no log de sincronização** — Registre: tipo de operação, contagem de registros, origem, data, operador, quaisquer erros ou avisos.

---

## 6. Fluxo de Entrega de Relatório

Usar para: relatórios de pulso semanais, revisões mensais, QBRs, relatórios de desempenho ad-hoc.

1. **Extração de dados** — Consulte todas as fontes de analytics conectadas (Google Analytics, Search Console, plataformas de anúncios, plataformas de e-mail, CRM) via servidores MCP. Normalize os intervalos de datas para o período do relatório.
2. **Agregação** — Combine dados de múltiplas fontes. Normalize: moeda (converta para a moeda principal da marca), formatos de data (ISO 8601), definições de métricas (ex: definição de "conversões" consistente entre plataformas).
3. **Cálculo de KPIs** — Para cada KPI, calcule:
   - Valor do período atual
   - vs. meta (% de atingimento)
   - vs. período anterior (% de variação, seta de direção)
   - vs. benchmark do setor (acima/abaixo, percentil se disponível)
4. **Detecção de anomalias** — Marque qualquer métrica que mudou > 25% período a período. Marque qualquer KPI abaixo de 80% da meta. Marque qualquer métrica que desvie > 2 desvios padrão da média dos últimos 90 dias.
5. **Seleção de formato** — Escolha o formato de entrega por tipo de relatório:
   - Pulso semanal: Blocks do Slack ou e-mail curto
   - Revisão mensal: Google Slides ou e-mail HTML com gráficos
   - QBR: Deck de apresentação em Google Slides
   - Ad-hoc: Google Sheets ou mensagem direta
6. **Voz da marca/agência** — Aplique a voz adequada:
   - Relatórios internos: Pode usar abreviações, referenciar múltiplos clientes (modo agência)
   - Relatórios para o cliente: Profissional, terceira pessoa, linguagem adequada à marca
7. **Enviar** — Entregue o relatório pelo canal configurado. Inclua um resumo executivo de 2-3 frases no início.
8. **Confirmar recebimento** — Registre o timestamp de entrega. Para entrega por e-mail, verifique se não houve bounce. Para Slack, verifique se a mensagem foi postada com sucesso.

---

## 7. Fluxo de SMS/WhatsApp

Usar para: SMS promocional, SMS transacional com elementos de marketing, mensagens de marketing no WhatsApp.

### Conformidade (Etapa Obrigatória Inicial)

1. **Verificação de consentimento** — Verifique o consentimento opt-in para cada destinatário:
   - EUA (TCPA): Consentimento escrito expresso para SMS de marketing. Consentimento expresso prévio para SMS informacional.
   - UE (GDPR): Consentimento opt-in explícito.
   - Canadá (CASL): Consentimento expresso com prova documentada.
   - Todos: O consentimento deve ser específico para o canal SMS/WhatsApp (consentimento de e-mail não se transfere).
2. **Horário de silêncio** — Aplique janelas de envio: sem mensagens entre 21h e 8h no fuso horário local do destinatário. Coreia do Sul: sem mensagens entre 21h-8h (lei). EUA: varia por estado, 8h-21h é o mais seguro.
3. **Mecanismo de opt-out** — Toda mensagem deve incluir instruções de opt-out:
   - SMS: "Reply STOP to unsubscribe" (exato ou equivalente)
   - WhatsApp: Link de descadastro ou palavra-chave de resposta

### Preparação de Mensagem

4. **Formatação de mensagem** — Respeite os limites de caracteres:
   - SMS (codificação GSM-7): 160 caracteres por segmento. Unicode: 70 caracteres por segmento.
   - WhatsApp: 1.024 caracteres. Suporta mídia rica (imagens até 5 MB, vídeo até 16 MB, documentos até 100 MB).
5. **Verificação de ID do remetente** — Confirme que o número/ID de envio está registrado e verificado:
   - SMS: Número gratuito, short code ou 10DLC (EUA). ID de remetente alfanumérico (internacional, onde suportado).
   - WhatsApp: Número verificado da WhatsApp Business API com nome de exibição aprovado.
6. **Aprovação de template (WhatsApp)** — Mensagens de marketing no WhatsApp exigem templates pré-aprovados. Envie o template para aprovação da Meta (prazo de 24-48h). Mensagens de sessão (dentro de 24h da mensagem do usuário) não exigem templates.

### Envio e Monitoramento

7. **Envio de teste** — Envie primeiro para números de teste internos. Verifique entrega e renderização.
8. **Enviar** — Execute o envio. Monitore a taxa de entrega em tempo real.
9. **Rastreamento de entrega** — Monitore: taxa de entrega (meta > 95%), taxa de resposta, taxa de opt-out (alerte se > 1% por envio). Registre números não entregáveis para limpeza de lista.
10. **Rastreamento de custo** — Registre o custo por mensagem. Os custos de SMS variam por país e operadora. O WhatsApp cobra por conversa (janela de 24h). Alerte se o custo da campanha exceder o orçamento em > 10%.

---

## 8. Fluxo de Operações de Memória

Usar para: armazenar insights de marketing, aprendizados de campanha, conteúdo para a memória da marca, atualizações da base de conhecimento.

1. **Extração de conteúdo** — Remova artefatos de formatação. Extraia pontos-chave, métricas e insights acionáveis. Preserve a atribuição de origem (nome da campanha, data, canal).
2. **Marcação de metadados** — Aplique metadados estruturados:
   - `content_type`: insight | campaign_data | performance_snapshot | content_piece | voice_sample
   - `tags`: Array de tags de tópico relevantes (ex: ["email", "subject-lines", "open-rate"])
   - `source`: Campanha ou análise de origem
   - `date`: Timestamp ISO 8601
   - `confidence`: high | medium | low (para insights)
3. **Deduplicação** — Gere hash do conteúdo. Verifique contra entradas existentes. Se duplicado detectado, atualize os metadados da entrada existente (timestamp, confidence) em vez de criar uma nova entrada.
4. **Armazenamento** — Escreva no local apropriado em `./data/clientes/{slug}/`:
   - Insights: `insights.json` (buffer rotativo, máx 200 entradas, as mais antigas são descartadas)
   - Campanhas: `campaigns/{id}.json`
   - Performance: `performance/{campaign}-{date}.json`
   - Conteúdo: `content-library/`
5. **Atualização do índice** — Atualize os arquivos de índice relevantes (`_index.json` para campanhas). Garanta que a nova entrada seja pesquisável por tags e data.
6. **Verificação** — Releia a entrada armazenada. Confirme que o conteúdo corresponde ao que foi escrito. Confirme que a pesquisa/lookup retorna a entrada.
7. **Estado de sincronização** — Atualize o timestamp de última modificação em `_conta-ativa.json`. Registre a operação de memória no log de execução.

---

## Checklist Pré-Execução

Tabela de referência rápida dos verificadores obrigatórios por tipo de execução. Todos os checks devem ser aprovados antes de prosseguir com a execução.

| Verificação | Blog | E-mail | Anúncios | Social | CRM | Relatório | SMS/WA | Memória |
|---|---|---|---|---|---|---|---|---|
| Contexto da marca carregado | Sim | Sim | Sim | Sim | Sim | Sim | Sim | Sim |
| Regras de conformidade aplicadas | Sim | Sim | Sim | Sim | Sim | Não | Sim | Não |
| Conteúdo pontuado (rubrica) | Sim | Sim | Sim | Sim | Não | Não | Não | Não |
| Specs da plataforma verificadas | Sim | Sim | Sim | Sim | Não | Não | Sim | Não |
| Consentimento/opt-in verificado | Não | Sim | Não | Não | Não | Não | Sim | Não |
| Orçamento dentro do limite | Não | Não | Sim | Não | Não | Não | Sim | Não |
| Envio de teste/preview | Não | Sim | Não | Não | Não | Não | Sim | Não |
| Gate de aprovação | Médio | Médio | Alto | Médio | Alto | Baixo | Alto | Baixo |
| Backup/snapshot realizado | Não | Não | Não | Não | Sim | Não | Não | Não |
| Rastreamento verificado | Sim | Sim | Sim | Não | Não | Não | Sim | Não |
| Entrada no log de desempenho | Sim | Sim | Sim | Sim | Sim | Sim | Sim | Sim |
