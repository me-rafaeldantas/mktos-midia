#!/usr/bin/env bash
# install.sh — Instalador automatizado do mktOS Mídia

set -e

# Cores para o output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}"
echo "=============================================="
echo "    mktOS Mídia — Instalador Plug-and-Play    "
echo "=============================================="
echo -e "${NC}"

# 1. Verifica versão do Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 não encontrado. Por favor, instale o Python 3.8+ antes de continuar.${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PYTHON_MAJOR=$(python3 -c 'import sys; print(sys.version_info.major)')
PYTHON_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')

if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]; }; then
    echo -e "${RED}✗ Versão do Python encontrada: $PYTHON_VERSION"
    echo "✗ O mktOS Mídia requer Python 3.8 ou superior.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python $PYTHON_VERSION detectado.${NC}"

# 2. Caminho do repositório
REPO_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
echo -e "${GREEN}✓ Repositório localizado em: $REPO_ROOT${NC}"

# 3. Criação do Ambiente Virtual (venv)
echo -e "\n${YELLOW}--- Criando ambiente virtual Python isolado (.venv) ---${NC}"
if [ ! -d "$REPO_ROOT/.venv" ]; then
    python3 -m venv "$REPO_ROOT/.venv"
    echo -e "${GREEN}✓ Ambiente virtual criado em $REPO_ROOT/.venv${NC}"
else
    echo -e "${GREEN}✓ Ambiente virtual existente detectado.${NC}"
fi

# 4. Instalação de dependências no venv
echo -e "\n${YELLOW}--- Instalando dependências no ambiente virtual ---${NC}"
"$REPO_ROOT/.venv/bin/pip" install --upgrade pip
"$REPO_ROOT/.venv/bin/pip" install -r "$REPO_ROOT/scripts/requirements.txt"
echo -e "${GREEN}✓ Dependências instaladas com sucesso.${NC}"

# 5. Registro do Plugin (Claude Code + Antigravity)
echo -e "\n${YELLOW}--- Registrando o plugin nos editores ---${NC}"
"$REPO_ROOT/.venv/bin/python3" "$REPO_ROOT/scripts/instalar-plugin.py"

# 6. Assistente de configuração MCP
echo -e "\n${YELLOW}--- Configuração dos Servidores MCP ---${NC}"
read -p "Deseja rodar o assistente interativo de configuração de MCP agora? (S/n): " RUN_MCP
RUN_MCP=${RUN_MCP:-S}

if [[ "$RUN_MCP" =~ ^[Ss]$ ]]; then
    "$REPO_ROOT/.venv/bin/python3" "$REPO_ROOT/scripts/configurar-mcp.py"
else
    echo -e "${YELLOW}💡 Você pode rodar a configuração dos MCPs mais tarde executando:"
    echo -e "   $REPO_ROOT/.venv/bin/python3 scripts/configurar-mcp.py${NC}"
fi

echo -e "\n${GREEN}=============================================="
echo "         Instalação Concluída com Sucesso!     "
echo "==============================================${NC}\n"
