# mktOS Mídia 🚀
> **Sistema operacional de mídia paga especializado para Antigravity (Gemini) e Claude Code.**

O **mktOS Mídia** é um plugin de inteligência artificial voltado para a rotina diária de tráfego pago. Ele apoia o ciclo completo de performance — planejamento de canais, briefs criativos, análise de fadiga, rastreamento UTM, auditoria de tags e geração de relatórios cross-platform — rodando scripts locais integrados às APIs do Google Ads e Meta Ads via MCP.

---

## 📋 Pré-requisitos

Antes de iniciar a instalação, certifique-se de ter:
- Um terminal configurado no **macOS** ou **Linux**.
- **Python 3.8** ou superior instalado (`python3 --version`).
- O **Claude Code** instalado e/ou o **Antigravity IDE** ativo.

---

## 🛠️ Instalação Passo a Passo (Plug-and-Play)

Para instalar o plugin pela primeira vez e configurar suas integrações de forma isolada, siga as etapas abaixo:

### Passo 1: Clone o repositório
Abra o seu terminal e clone o projeto em uma pasta local de sua escolha (recomendado: diretório root de seu usuário):
```bash
git clone https://github.com/rafaeldantas/mktos-midia.git ~/mktOS-midia
cd ~/mktOS-midia
```

### Passo 2: Execute o Instalador Automático
Rode o script de instalação rápida. Ele criará um ambiente virtual isolado, instalará as dependências de análise de copy e registrará o plugin nos dois runtimes (Claude Code e Antigravity):
```bash
./install.sh
```

**O que o instalador faz automaticamente:**
1. Valida se a sua versão do Python é compatível (>= 3.8).
2. Cria o ambiente virtual (`.venv`) na raiz do repositório para evitar poluição global de pacotes.
3. Instala as dependências de Processamento de Linguagem Natural (`nltk`, `textstat`) e análise.
4. Vincula o plugin ao Claude Code no arquivo `~/.claude/settings.json`.
5. Cria um link simbólico direto para o Antigravity em `~/.gemini/config/plugins/mktos-midia`.

---

## 🔑 Configurando Integrações MCP (Model Context Protocol)

O instalador perguntará no final se você deseja configurar as integrações de rede de anúncios e ferramentas. O assistente de configuração interativa de MCPs pode ser executado a qualquer momento:

```bash
.venv/bin/python3 scripts/configurar-mcp.py
```

O assistente solicitará (opcionalmente) suas credenciais e gravará de forma segura com permissão restrita (`chmod 600`) nos seguintes destinos:
- **Claude Code**: Gravado no arquivo `.mcp.json` na raiz deste repositório.
- **Antigravity**: Gravado no arquivo global `~/.gemini/antigravity-ide/mcp_config.json`.

*Nota: Você não é obrigado a configurar nenhum MCP para usar o plugin. Se optar por pular, o assistente configurará fallbacks locais e importação de relatórios via arquivo CSV.*

---

## 🎯 Como Utilizar o Plugin

### 1. No Antigravity (Gemini)
Como o Antigravity carrega as Skills do plugin nativamente no contexto da IA, você **não precisa de comandos com barra**. Apenas converse em português no chat:

- *"Crie um plano de mídia para o meu cliente"* (Ativa a Skill `plano`)
- *"Analise o pacing de gastos do cliente Daltro"* (Ativa a Skill `pacing`)
- *"Gere o relatório consolidado deste mês"* (Ativa a Skill `relatorio`)

O Gemini lerá as diretrizes dos SOPs (`skills/`) e executará de forma transparente os scripts Python locais usando o ambiente virtual configurado.

### 2. No Claude Code (Anthropic)
No Claude Code, as ações são disparadas pelos comandos com prefixo `/mktos:`.

1. **Inicialize seu Workspace e cadastre seu primeiro cliente:**
   ```
   /mktos:configurar
   ```
2. **Confirme que está operando no cliente correto:**
   ```
   /mktos:conta status
   ```
3. **Comandos de Execução Comuns:**
   - `/mktos:plano` - Cria um plano de mídia estruturado.
   - `/mktos:criativo` - Produz copies de anúncios baseados em IA e análises locais.
   - `/mktos:lançar` - Lança campanhas no Google Ads ou Meta Ads (criadas **sempre em modo pausado** por segurança).
   - `/mktos:relatorio` - Consolida dados em um relatório executivo para o cliente.

---

## 📂 Organização de Arquivos e Memória

Os dados sensíveis dos seus clientes (orçamentos, históricos de campanhas e análises) ficam salvos localmente na sua máquina e **nunca** sobem para o repositório Git:
- **Localização dos perfis de clientes**: `./data/clientes/{slug-do-cliente}/`
- **Registro geral de tarefas**: `./data/work-log/tasks.jsonl`

---

## 🛡️ Segurança e Aprovações
- **Zero Escrita Direta Sem Confirmação**: O mktOS Mídia nunca publica, altera orçamentos ou cria tarefas sem que você aprove explicitamente digitando "sim" ou "confirmo" no chat.
- **Hardcoded Paused**: Toda campanha criada através de integrações diretas do plugin nasce obrigatoriamente pausada (`PAUSED`). Você tem total controle de quando ativá-la nos painéis oficiais.
