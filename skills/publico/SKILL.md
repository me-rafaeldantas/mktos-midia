---
name: publico
description: "Use quando o usuário precisar definir públicos-alvo para campanhas pagas — personas de comprador, segmentos comportamentais, critérios de lookalike, pools de retargeting e targeting acionável por plataforma (Meta, Google, LinkedIn)."
argument-hint: "[segmento ou vertical]"
---

# /mktos:publico

## Propósito

Construir personas de público-alvo e traduzi-las em critérios de targeting diretamente acionáveis nas plataformas de mídia paga. O output não é um documento genérico de "público-alvo" — é uma especificação técnica de configuração de audiências no Meta Ads, Google Ads e LinkedIn Ads. Conhecer o público é a base de toda decisão de targeting, bid strategy e criativo.

## Entrada Necessária

O usuário deve fornecer (ou será solicitado):

- **Produto ou serviço anunciado**: o que está sendo vendido e qual problema resolve
- **Dados de clientes existentes** (se disponível): métricas de CRM, listas de clientes, dados de conversão histórica, audiências salvas nas plataformas
- **Canais de veiculação**: Meta, Google, LinkedIn — cada plataforma tem capacidades de targeting distintas
- **Objetivo da campanha**: aquisição de novos clientes, retargeting de visitantes, reativação de clientes, geração de leads
- **Geo e idioma**: região(ões) de targeting

## Processo

1. **Carregue contexto da conta**: Leia `./data/clientes/_conta-ativa.json` para obter o slug ativo, depois carregue `./data/clientes/{slug}/perfil.json`. Aplique `vertical`, `canais_ativos` e qualquer dado de público já salvo. Verifique `./data/sops/`. Se nenhuma conta existir, pergunte: "Configurar uma conta primeiro (`/mktos:configurar`)?"

2. **Levante dados disponíveis**: Pergunte ao usuário sobre fontes de dados existentes:
   - Listas de clientes para upload (customer match)?
   - Pixel Meta e/ou tag Google instalados? Se sim, há audiences salvas nas plataformas?
   - Dados de conversão histórica para identificar perfil de quem converte?
   - Pesquisa de clientes, entrevistas ou feedback disponível?
   Se não houver dados, construa personas hipótese baseadas na vertical e no produto — marque claramente como "hipótese a validar".

3. **Construa 2 a 4 personas de comprador**: Para cada persona, defina:
   - **Perfil demográfico**: faixa etária, gênero (se relevante), localização, renda estimada, nível educacional
   - **Perfil comportamental**: como pesquisa e compra, quais canais usa, frequência de compra, dispositivo predominante
   - **Motivação de compra**: principal benefício buscado, problema que resolve, urgência
   - **Objeções típicas**: por que posterga ou não compra — preço, credibilidade, necessidade não urgente
   - **Momento de busca**: o que desencadeia a busca pelo produto (gatilho situacional)
   - **Tamanho estimado do segmento**: pequeno (<50k), médio (50k–500k), grande (>500k) — impacta bid strategy

4. **Defina segmentos de retargeting**: Mapeie os pools de audiência com base na jornada do cliente:
   - **Visitantes do site**: todos os visitantes dos últimos 30/60/90/180 dias — segmentar por página visitada se possível
   - **Engajamento com conteúdo**: quem assistiu X% de vídeo, interagiu com posts, abriu formulário sem completar
   - **Abandonadores de carrinho/formulário**: alta intenção, não converteu — prioridade máxima para retargeting
   - **Clientes recentes**: compraram nos últimos 90/180 dias — candidatos para upsell ou cross-sell
   - **Clientes antigos inativos**: compraram há mais de 6 meses — reativação

5. **Defina critérios de lookalike**: Para cada persona ou pool de retargeting relevante, especifique o seed ideal para lookalike:
   - Fonte: lista de clientes (customer match), converters via pixel, engajamento de perfil, vídeo viewers
   - Tamanho recomendado: 1%–3% para campanhas de conversão, 5%–10% para reach/awareness
   - Sobreposição a excluir: exclua clientes existentes do lookalike de aquisição

6. **Gere targeting acionável por plataforma**:

   **Meta Ads**:
   - Interesses detalhados: lista de interesses específicos do Gerenciador de Anúncios para cada persona (ex: "Educação técnica", "Cursos profissionalizantes", "SENAI")
   - Comportamentos: comportamentos de compra relevantes, uso de dispositivo, status de viajante
   - Dados demográficos: faixa etária, localização, idioma
   - Exclusões: interesses ou comportamentos que indicam público errado
   - Tipo de audiência recomendado: Advantage+ Audience, interesse manual ou lookalike

   **Google Ads**:
   - Segmentos de intenção personalizada: keywords que o público pesquisa (alimentado pela pesquisa do `/mktos:keywords`)
   - Segmentos de afinidade: categorias de interesse de longo prazo compatíveis com a persona
   - Segmentos in-market: categorias de compra ativa relevantes (ex: "Serviços educacionais > Ensino técnico")
   - Remarketing: listas de visitantes do site por page path ou evento de conversão
   - Customer Match: se lista de clientes disponível — upload para seed de lookalike e exclusão
   - Demographics: faixa etária, gênero, renda familiar (disponível em alguns mercados)

   **LinkedIn Ads** (se `linkedin` em `canais_ativos`):
   - Cargo/função: títulos de trabalho relevantes
   - Setor de atuação: indústrias do público-alvo
   - Tamanho da empresa: se relevante para o produto
   - Nível de senioridade: decisor, influenciador, usuário final
   - Habilidades: competências que indicam o perfil

7. **Estime o tamanho de cada audiência**: Para os segmentos principais, forneça estimativa de alcance potencial nas plataformas e classifique a estratégia de bid recomendada:
   - Audiência menor (<50k): usar CPA target alto, evitar broad — foco em conversão
   - Audiência média (50k–500k): CPA target, testar lookalike 1%–3%
   - Audiência grande (>500k): pode usar estratégias de volume (maximizar conversões, target ROAS)

8. **Defina estratégia de exclusão**: Para cada campanha de aquisição, especifique quem excluir:
   - Clientes já ativos (customer match ou pixel event "purchase")
   - Funcionários e parceiros (se relevante)
   - Faixas etárias incompatíveis com o produto
   - Geos fora do raio de atendimento

## Saída

Um guia de audiências por campanha contendo:

- **Personas de comprador**: 2–4 personas com perfil completo (demográfico, comportamental, motivações, objeções, tamanho estimado)
- **Mapa de segmentos de retargeting**: pools por estágio da jornada com critério de inclusão, janela de tempo e mensagem recomendada
- **Especificação de lookalike**: seed ideal, tamanho recomendado e exclusões para cada público similar
- **Configuração de targeting por plataforma**: para cada persona, critérios prontos para copiar e configurar no Meta Ads Manager, Google Ads e LinkedIn Campaign Manager
- **Prioridade de audiências**: ranking de qual audiência testar primeiro por probabilidade de conversão × volume disponível
- **Plano de validação**: como confirmar ou refutar as hipóteses de persona em 30–60 dias de campanha — métricas-chave a monitorar (CPL, taxa de conversão, ROAS por segmento)

## Agentes Usados

- **gestor-trafego** — Tradução de personas em critérios de targeting por plataforma, estratégias de bid por tamanho de audiência, recomendações de tipo de campanha por objetivo, specs de customer match e lookalike por plataforma

## Integração Work Log

Após entregar o guia de audiências, pergunte ao usuário:

> "Quer registrar as audiências definidas no work-log para rastreamento?"

Se confirmado, registre usando `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/log-tarefas.py" --action log` com `source_skill: publico` e `category: Ads`:

- **[Ads] Definir públicos — {N} personas — Meta e Google** — `priority: normal`
- **[Ads] Configurar retargeting — {N} pools de audiência** — `priority: high` se o cliente tiver pixel ativo
- **[Ads] Subir customer match — lista de clientes** — `priority: high` se lista de clientes disponível

Use `account_slug` da conta ativa.
