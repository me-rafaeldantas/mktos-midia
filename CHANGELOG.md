# Changelog — mktOS Mídia

Todas as mudanças notáveis neste projeto são documentadas aqui.

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/).

---

## [0.2.0] — 2026-06-22

Nova versão estendendo a compatibilidade do plugin para execução híbrida e nativa tanto no **Claude Code** quanto no **Antigravity (Gemini)**, além de introduzir o fluxo de instalação distribuível e isolamento local de armazenamento.

### Adicionado
- **Suporte Nativo ao Antigravity**: Criação de `plugin.json` e `gemini-extension.json` na raiz do repositório para descoberta automática e suporte nativo das Skills no chat do Gemini (sem comandos de barra).
- **Instalador Plug-and-Play (`install.sh`)**: Script automatizado que valida o ambiente, monta um ambiente virtual Python isolado (`.venv`), instala dependências locais e registra o plugin nos runtimes de ambos os editores.
- **Assistente de MCP Interativo (`scripts/configurar-mcp.py`)**: Wizard em terminal para configuração amigável de tokens de APIs, replicando as credenciais no Claude Code e no Antigravity, e blindando os arquivos de tokens locais com permissão de sistema restrita (`chmod 600`).
- **Armazenamento Interno (`data/`)**: Redirecionamento de toda a escrita/leitura de dados de clientes, logs de tarefas e relatórios para a pasta `./data/` local do repositório, garantindo portabilidade absoluta. A pasta é adicionada ao `.gitignore` para segurança de dados.
- **Migração Automática**: Mecanismo no `setup-mktos.py` que detecta se há dados legados em `~/.claude-marketing/` e realiza a migração transparente dos perfis de clientes existentes para a pasta local `./data/`.
- **Execução Transparente com venv**: Injeção de código de auto-bootstrap no início de todos os scripts Python essenciais, fazendo-os se auto-inicializarem sob o interpretador do `.venv` mesmo se executados globalmente no shell.

### Modificado
- Refatorados 28 arquivos (incluindo markdowns de Skills, Agentes, configurações e scripts Python) para atualizar as referências textuais e operacionais de caminhos absolutos (`~/.claude-marketing/`) para o caminho local do repositório (`./data/`).
- Atualizado e robustecido o script `scripts/instalar-plugin.py` para criar links simbólicos automáticos na pasta de extensões do Antigravity.
- Atualizado o `README.md` principal na raiz do repositório contendo o guia rápido de instalação e nova estrutura local de dados.

---

## [0.1.0] — 2026-06-12

Primeira versão completa do plugin mktOS Mídia. Cobre o ciclo completo de tráfego pago: planejamento → criativo → lançamento → rastreamento → gestão → relatório.

### Skills adicionadas (16)

**Configuração e Clientes**
- `/mktos:configurar` — Onboarding guiado e hub de reconfiguração. Detecta primeiro uso vs. workspace existente. Cria estrutura de pastas, conecta MCPs e registra o primeiro cliente.
- `/mktos:conta` — Gerenciamento de clientes: listar, trocar, adicionar, exibir status. Isolamento total de contexto entre clientes.

**Planejamento e Estratégia**
- `/mktos:plano` — Plano de mídia paga com alocação de orçamento por canal, calendário integrado ao Google Calendar e verificação de conflitos.
- `/mktos:keywords` — Pesquisa de palavras-chave com cascata de fallback: API Google Ads → importação CSV → WebSearch.
- `/mktos:publico` — Mapeamento de personas e públicos-alvo com targeting específico por plataforma, retargeting pools e lookalike.
- `/mktos:retargeting` — Estratégia completa de retargeting: segmentos por estágio de funil, sequência criativa, caps de frequência, retargeting dinâmico, orçamento por segmento.

**Criativo**
- `/mktos:criativo` — Briefing e criação de criativos pagos para Google Ads (RSA), Meta e TikTok com validação de specs.
- `/mktos:materiais` — Geração de assets e especificações técnicas de criativos por plataforma e formato.
- `/mktos:saude` — Dashboard de saúde criativa com fadiga, previsão de desgaste, briefs de refresh e planos de A/B. Menu-driven quando executado sem contexto.

**Lançamento e Execução**
- `/mktos:lançar` — Lançamento de campanhas no Google Ads e Meta com aprovação obrigatória. Toda campanha criada em modo PAUSADO.
- `/mktos:links` — Geração de UTMs estruturadas por plataforma e canal com alertas de conflito (gclid, fbclid, redirects).
- `/mktos:rastreamento` — Auditoria completa de rastreamento: pixels, conversões Google Ads, GA4 key events, GTM, nomenclatura UTM. Score de qualidade 0–100.

**Gestão e Relatórios**
- `/mktos:pacing` — Dashboard de pacing de orçamento com alertas de overspend/underpend e projeção de fim de mês.
- `/mktos:orçamento` — Otimização e realocação de orçamento entre canais baseada em performance (ROAS, CPA, CPL).
- `/mktos:relatorio` — Relatório cross-platform (Google Ads + Meta) com PoP semáforo, análise criativa, benchmarks de setor e recomendações hipótese + impacto.
- `/mktos:negativos` — Análise de relatório de termos de busca, matriz 2×2 relevância/conversão, categorias [NEG], export formatado para Google Ads Editor e aplicação opcional via MCP.

### Agentes adicionados (5)

- `media-buyer` — Planejamento de canais, segmentação, lances, budget, estrutura de campanha
- `analytics-analyst` — Consolidação cross-platform, métricas blended, análise de performance
- `diretor-criativo` — Briefing criativo, sequências de mensagem, variantes A/B
- `monitor-performance` — Monitoramento de KPIs, detecção de anomalias, fadiga criativa
- `execution-coordinator` — Orquestração de publicação com aprovação obrigatória

### Scripts adicionados (23)

| Script | Função |
|---|---|
| `controlador-pacing.py` | Cálculo de pacing diário e projeções de orçamento |
| `gerenciador-aprovacao.py` | Fluxo de aprovação obrigatória para ações de escrita |
| `gerador-specs.py` | Especificações técnicas de assets por plataforma e formato |
| `avaliador-voz.py` | Scoring de aderência ao tom de voz da marca |
| `otimizador-orcamento.py` | Otimização de alocação de orçamento entre canais |
| `rastreador-campanhas.py` | Registro e histórico de campanhas por cliente |
| `avaliador-conteudo.py` | Scoring de qualidade de conteúdo criativo |
| `indicador-fadiga.py` | Score de saúde criativa 0–100 com previsão de fadiga |
| `rastreador-execucao.py` | Log de execuções em plataformas externas |
| `gerenciar-contas.py` | CRUD de contas de clientes no workspace local |
| `publicador-google-ads.py` | Publisher Google Ads com validação RSA, budget guard e PAUSED enforcement |
| `analisador-headlines.py` | Análise de headlines por clareza, benefício e CTR estimado |
| `planejador-keywords.py` | Pesquisa de keywords com cascade API → CSV → WebSearch |
| `relatorio.py` | Geração de relatórios cross-platform com PoP semáforo |
| `publicador-meta.py` | Publisher Meta Ads com validação de specs e aprovação |
| `publicador-meta-whatsapp.py` | Publisher Meta Ads com destino WhatsApp |
| `monitor-performance.py` | Monitoramento de KPIs e detecção de anomalias |
| `previsao-receita.py` | Projeção de receita baseada em funil e performance histórica |
| `calculadora-roi.py` | Cálculo de ROI e análise de atribuição por canal |
| `setup-mktos.py` | Inicialização e verificação do workspace local |
| `auditoria-rastreamento.py` | Auditoria de UTMs, naming convention e parâmetros de rastreamento |
| `gerador-utm.py` | Geração de UTMs com mapeamento GA4 de channel groups |
| `log-tarefas.py` | Registro de tarefas geradas pelas skills no ClickUp/Trello |

### Arquivos de referência (context-engine)

- `industry-profiles.md` — Benchmarks e contexto estratégico por setor
- `platform-specs.md` — Specs técnicos de plataformas (orgânico)
- `platform-publishing-specs.md` — Specs de API para publicação
- `specs-midia.md` — Specs de mídia paga: formatos, limites de cópia, benchmarks e políticas por plataforma
- `compliance-rules.md` — Regras de conformidade por setor e região
- `execution-workflows.md` — Fluxos de execução e aprovação

### Decisões de design

- **Aprovação obrigatória:** qualquer skill que executa ação de escrita em plataforma externa tem passo de confirmação explícita antes da execução.
- **PAUSED enforcement:** toda campanha criada via `publicador-google-ads.py` é gerada com `status = PAUSED`. Não existe caminho para criar campanha ENABLED.
- **Budget guard:** `publicador-google-ads.py` bloqueia criação se o orçamento diário proposto exceder 50% do `orcamento_mensal` registrado no perfil do cliente.
- **Cascata de fallback:** skills que dependem de MCP implementam níveis de fallback para não travar o usuário sem acesso à API.
- **Isolamento de dados:** cada cliente tem pasta e contexto separados em `./data/clientes/{slug}/`. Nenhum dado de cliente é incluído no repositório.
- **Zero dados hardcoded:** o plugin começa do zero em cada instalação. Nenhuma referência a contas reais, IDs ou clientes nos arquivos distribuídos.
