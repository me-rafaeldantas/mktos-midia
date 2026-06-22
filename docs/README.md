# mktOS Mídia 🚀
**Sistema operacional de mídia paga especializado para Antigravity (Gemini) e Claude Code.**

O **mktOS Mídia** é um plugin de inteligência artificial voltado para a rotina diária de tráfego pago. Ele apoia o ciclo completo de performance — planejamento de canais, briefs criativos, análise de fadiga, rastreamento UTM, auditoria de tags e geração de relatórios cross-platform — rodando scripts locais integrados às APIs do Google Ads e Meta Ads via MCP.

---

## 🎯 Principais Diferenciais (Versão 0.2.0)

- **Compatibilidade Dupla**: Funciona nativamente no **Claude Code** (via comandos `/mktos:`) e no **Antigravity IDE / Gemini** (via linguagem natural e Skills/SOPs automáticos).
- **Instalador Inteligente e Isolado**: Script de instalação automática (`./install.sh`) que cria um ambiente Python virtual (`.venv`), instala dependências locais de PLN (nltk, textstat) e registra o plugin em ambas as plataformas.
- **Configurador Interativo de MCP**: Assistente CLI (`scripts/configurar-mcp.py`) para configurar credenciais de forma segura com permissão restrita (`chmod 600`), gravando as credenciais no `.mcp.json` para o Claude Code e em `~/.gemini/antigravity-ide/mcp_config.json` para o Antigravity.
- **Portabilidade & Privacidade (Redirecionamento `./data/`)**: Todo o CRUD de clientes, histórico de campanhas, snapshots de performance e logs de trabalho são salvos na pasta `./data/` dentro do próprio repositório, em vez de pastas globais do sistema. A pasta `./data/` é ignorada no `.gitignore` para total segurança dos dados.
- **Segurança Operacional**: Garantia de zero escrita sem aprovação prévia do usuário e criação de campanhas em modo pausado (`PAUSED`).

---

## 📋 Pré-requisitos

- Terminal configurado no **macOS** ou **Linux**.
- **Python 3.8** ou superior instalado (`python3 --version`).
- O **Claude Code** instalado e/ou o **Antigravity IDE** ativo.

---

## 🛠️ Instalação Passo a Passo

### Passo 1: Clonar o Repositório
Escolha uma pasta local (por exemplo, na raiz do seu usuário):
```bash
git clone https://github.com/rafaeldantas/mktos-midia.git ~/mktOS-midia
cd ~/mktOS-midia
```

### Passo 2: Rodar o Instalador Automático
```bash
./install.sh
```
O script fará:
1. Validação da versão do Python.
2. Criação do `.venv`.
3. Instalação das dependências locais.
4. Registro no Claude Code em `~/.claude/settings.json`.
5. Link simbólico para o Antigravity em `~/.gemini/config/plugins/mktos-midia`.

### Passo 3: Configurar Credenciais
No final do instalador ou rodando o assistente diretamente:
```bash
.venv/bin/python3 scripts/configurar-mcp.py
```
Insira suas chaves (Google Ads, Meta Ads, ClickUp, Gmail, etc.) quando solicitado. Se pular, fallbacks locais e importação de relatórios via arquivos CSV serão ativados.

---

## 📂 Arquitetura de Dados (Portabilidade `./data/`)

Todos os arquivos gerados são mantidos localmente na raiz do repositório no subdiretório `./data/`, assegurando portabilidade e impedindo o vazamento de chaves ou dados de clientes para o Git:
- **Workspace Geral**: `./data/workspace.json`
- **Registro do Cliente Ativo**: `./data/clientes/_conta-ativa.json`
- **Perfil do Cliente**: `./data/clientes/{slug}/perfil.json`
- **Campanhas e Relatórios**: `./data/clientes/{slug}/campanhas/` e `./data/clientes/{slug}/reports/`
- **Work log**: `./data/work-log/tasks.jsonl`

---

## 🎯 Interface de Uso e Comandos

O plugin pode ser operado de duas formas dependendo da plataforma:

### 1. No Claude Code (Comandos com Barra)
Use comandos dedicados na CLI do Claude:
- `/mktos:configurar` - Configuração inicial ou reconfiguração.
- `/mktos:conta listar` - Lista todas as contas de clientes criadas.
- `/mktos:conta trocar {slug}` - Altera o cliente ativo.
- `/mktos:conta status` - Mostra detalhes do cliente atual e status dos MCPs.
- `/mktos:plano` - Cria planos de mídia baseados em verba e público.
- `/mktos:criativo` - Produz copies com análise local de legibilidade e fadiga.
- `/mktos:lançar` - Publica campanhas estruturadas em modo `PAUSED` após aprovação explícita.
- `/mktos:pacing` - Dashboard local de controle de gastos e projeções de estouro.
- `/mktos:relatorio` - Consolida dados para exportação de PDFs e Markdown.

### 2. No Antigravity / Gemini (Linguagem Natural)
Em vez de comandos rígidos, o Gemini lê os arquivos de Skills (`skills/*.md`) e agentes do diretório de plugins e executa-os automaticamente baseado na sua intenção:
- *"Cadastre um novo cliente chamado Loja Alpha"*
- *"Troque para o cliente Loja Alpha"*
- *"Crie um plano de mídia com orçamento de R$10.000 para este mês"*
- *"Como está o pacing de gastos do cliente atual?"*
- *"Analise o texto deste anúncio para fadiga e legibilidade"*

---

## 🛡️ Protocolo de Segurança

Qualquer operação de escrita (ex: criação de campanha via API, disparo de email ou alteração de tarefas no ClickUp) exige confirmação explícita. O assistente listará os detalhes da execução e aguardará você digitar `sim`, `pode executar` ou `confirmar`. Todas as campanhas criadas nascem pausadas.

---

## 📂 Estrutura Completa do Repositório

```
mktOS-midia/
├── .claude-plugin/          # Manifesto do plugin para Claude (plugin.json, marketplace.json)
├── .gitignore               # Configurado para ignorar .venv/ e data/* (exceto .gitkeep)
├── .mcp.json                # Configuração local dos servidores MCP do Claude Code
├── gemini-extension.json    # Manifesto do plugin para Antigravity / Gemini
├── plugin.json              # Manifesto raiz para compatibilidade com loaders genéricos
├── install.sh               # Script interativo de instalação do plugin (macOS/Linux)
├── data/                    # Pasta de dados local, privada e portátil (ignorada no git)
├── scripts/                 # Scripts Python executados sob .venv para análise e automação
├── skills/                  # Skills do plugin (SOPs estruturados em Markdown lidos pela IA)
├── agents/                  # Agentes especialistas com prompts de contexto
├── hooks/                   # Hooks do ciclo de vida do Claude Code (SessionStart, PreToolUse, etc.)
└── docs/                    # Documentação do projeto (este arquivo e guias adicionais)
```
