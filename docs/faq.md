# Perguntas Frequentes (FAQ) — mktOS Mídia 🚀

Este documento reúne respostas para as dúvidas mais comuns sobre o funcionamento, instalação, segurança e gestão de contexto do plugin **mktOS Mídia** rodando tanto no **Claude Code** quanto no **Antigravity (Gemini)**.

---

## 🎯 1. Gestão de Contas e Contexto

### Como o Gemini/Antigravity lida com a troca de contas de clientes e isolamento de dados?
No Claude Code, você usava comandos de barra rígidos (como `/mktos:conta trocar {slug}`). No Gemini (Antigravity), você pode fazer isso de forma natural em português:
* *Exemplo:* *"Mude o cliente ativo para a Loja Alpha"* ou *"Troque para o contexto da Clínica Beta"*.

**Como funciona sob o capô:**
1. A IA detecta a sua intenção e lê as diretrizes em [conta/SKILL.md](file:///Users/dantas/mktOS-midia/skills/conta/SKILL.md).
2. Ela dispara silenciosamente o script local [gerenciar-contas.py](file:///Users/dantas/mktOS-midia/scripts/gerenciar-contas.py) passando a ação correspondente.
3. O script grava a informação da conta ativa no arquivo local `./data/clientes/_conta-ativa.json`.
4. Todas as outras Skills (como relatórios, planos de mídia e pacing) lêem este arquivo de estado antes de rodar, isolando todas as leituras e escritas apenas na subpasta daquele cliente específico (`./data/clientes/{slug}/`).

---

## 🛠️ 2. Desenvolvimento e Ciclo de Vida do Plugin

### O Antigravity usa o código que estou editando no meu diretório ou ele baixa o repositório do GitHub?
Ele utiliza **diretamente o seu diretório local de desenvolvimento**. Ele não baixa o repositório do GitHub toda vez e nem move os arquivos para pastas ocultas.

**Como funciona:**
Durante a instalação (`./install.sh`), o script cria um **Link Simbólico (symlink)** em `~/.gemini/config/plugins/mktos-midia` apontando diretamente para a pasta onde você clonou o código. Qualquer modificação que você fizer em um arquivo markdown de Skill ou script Python é consumida pela IA **imediatamente** na sua próxima mensagem do chat.

---

## 🛡️ 3. Segurança e Armazenamento

### Desinstalar o plugin apaga o meu conteúdo (dados dos clientes)?
**Não. Seus dados e workspaces continuam intactos.** A desinstalação apenas remove os vínculos de leitura lógica das IAs:
* **No Claude**: Remove a referência de caminhos dentro de `~/.claude/settings.json`.
* **No Gemini**: Exclui o link simbólico (o "atalho") em `~/.gemini/config/plugins/mktos-midia` (um comando `rm` sobre link simbólico não toca na pasta física original).

A pasta física do projeto e todo o conteúdo de `./data/` permanecem preservados em sua máquina local. A única forma de perder o seu conteúdo é se você deletar manualmente o diretório do repositório (`/Users/dantas/mktOS-midia`) do seu disco rígido.

### Por que minhas chaves de API não subiram para o GitHub? Como configuro em uma nova máquina?
Para evitar vazamentos de segurança acidentais, o arquivo `.mcp.json` (que armazena suas chaves de API) e a pasta `./data/` estão listados no arquivo [.gitignore](file:///Users/dantas/mktOS-midia/.gitignore). 

Ao clonar o projeto em uma nova máquina, você deve:
1. Executar `./install.sh` para recriar o ambiente virtual local.
2. Rodar o assistente interativo:
   ```bash
   .venv/bin/python3 scripts/configurar-mcp.py
   ```
3. O assistente usará o template limpo [.mcp.json.template](file:///Users/dantas/mktOS-midia/.mcp.json.template) para gerar o seu arquivo local seguro com suas novas credenciais.

---

## 📋 4. Instalação e Onboarding

### O comportamento na primeira instalação é similar ao Claude Code? O Gemini fará perguntas sobre minhas preferências?
**Sim, o comportamento é idêntico e segue o mesmo fluxo.**
Como o Gemini consome a Skill [configurar/SKILL.md](file:///Users/dantas/mktOS-midia/skills/configurar/SKILL.md) nativamente, basta você iniciar o chat no Antigravity dizendo algo como *"Quero configurar o mktOS"* ou *"Iniciar setup"*. A IA conduzirá uma entrevista conversacional de 7 etapas idêntica à do Claude Code, coletando suas preferências e acionando os scripts locais para estruturar o seu workspace local.
