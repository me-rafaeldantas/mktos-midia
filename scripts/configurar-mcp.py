#!/usr/bin/env python3
"""
configurar-mcp.py — Assistente de configuração interativo para servidores MCP.

Coleta credenciais e chaves de API e as grava no .mcp.json local (Claude Code)
e no mcp_config.json global do Antigravity/Gemini.
"""

import json
import os
import sys
from pathlib import Path
import stat

# Caminhos dos arquivos de configuração
REPO_ROOT = Path(__file__).parent.parent.resolve()
LOCAL_MCP_FILE = REPO_ROOT / ".mcp.json"
GEMINI_MCP_DIR = Path.home() / ".gemini" / "antigravity-ide"
GEMINI_MCP_FILE = GEMINI_MCP_DIR / "mcp_config.json"


def ler_json(caminho: Path) -> dict:
    if not caminho.exists():
        return {}
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def salvar_json(caminho: Path, dados: dict):
    # Garante que os diretórios pais existem
    caminho.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Grava os dados
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
            f.write("\n")
        
        # Restringe permissões de leitura/escrita para o usuário dono (chmod 600)
        os.chmod(caminho, stat.S_IRUSR | stat.S_IWUSR)
        print(f"✓ Configuração gravada e protegida (chmod 600) em: {caminho}")
    except Exception as e:
        print(f"✗ Erro ao salvar {caminho}: {e}")


def obter_input(prompt: str, padrao: str = "") -> str:
    sufixo = f" [{padrao}]" if padrao else ""
    escolha = input(f"{prompt}{sufixo}: ").strip()
    return escolha if escolha else padrao


def obter_input_obrigatorio(prompt: str, padrao: str = "") -> str:
    while True:
        valor = obter_input(prompt, padrao)
        if valor:
            return valor
        print("✗ Este campo é obrigatório. Insira um valor válido.")


def main():
    print("\n==============================================")
    print("      mktOS Mídia — Assistente de MCPs        ")
    print("==============================================\n")
    print("Este assistente irá guiar você na configuração das chaves de API")
    print("para integrar com Google Ads, Meta, Drive, ClickUp, Slack, etc.")
    print("A configuração será replicada no Claude Code e no Antigravity.\n")
    
    # Carrega dados atuais
    local_data = ler_json(LOCAL_MCP_FILE)
    gemini_data = ler_json(GEMINI_MCP_FILE)
    
    # Mescla as configurações existentes
    mcp_servers = local_data.get("mcpServers", {})
    if not mcp_servers:
        mcp_servers = gemini_data.get("mcpServers", {})

    # Se ainda estiver vazio, cria estrutura padrão básica
    if not mcp_servers:
        mcp_servers = {
            "google-ads": {
                "command": "uvx",
                "args": ["mcp-google-ads"],
                "env": {}
            },
            "meta-marketing": {
                "command": "uvx",
                "args": ["meta-ads-mcp"],
                "env": {}
            },
            "google-drive-designlab": {
                "command": "npx",
                "args": ["-y", "mcp-google-drive"],
                "env": {}
            },
            "gmail-guroo": {
                "command": "npx",
                "args": ["-y", "@gongrzhe/server-gmail-autoauth-mcp"]
            },
            "google-calendar-guroo": {
                "command": "npx",
                "args": ["-y", "@cocal/google-calendar-mcp"],
                "env": {}
            },
            "clickup-midify": {
                "command": "npx",
                "args": ["-y", "@taazkareem/clickup-mcp-server"],
                "env": {}
            },
            "trello": {
                "command": "npx",
                "args": ["-y", "trello-mcp"],
                "env": {}
            }
        }

    # 1. Google Ads
    print("--- [1/7] Google Ads MCP ---")
    ativo = obter_input("Configurar Google Ads? (s/n)", "s").lower() == "s"
    if ativo:
        ads_conf = mcp_servers.setdefault("google-ads", {"command": "uvx", "args": ["mcp-google-ads"], "env": {}})
        ads_env = ads_conf.setdefault("env", {})
        
        ads_env["GOOGLE_ADS_DEVELOPER_TOKEN"] = obter_input_obrigatorio(
            "Developer Token do Google Ads", ads_env.get("GOOGLE_ADS_DEVELOPER_TOKEN", "")
        )
        ads_env["GOOGLE_ADS_LOGIN_CUSTOMER_ID"] = obter_input_obrigatorio(
            "Login Customer ID (MCC principal sem traços)", ads_env.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID", "")
        )
        ads_env["GOOGLE_ADS_AUTH_TYPE"] = "oauth"
        ads_env["GOOGLE_ADS_CREDENTIALS_PATH"] = obter_input_obrigatorio(
            "Caminho absoluto para credenciais OAuth JSON", 
            ads_env.get("GOOGLE_ADS_CREDENTIALS_PATH", str(Path.home() / "mktOS" / "credentials" / "google-ads-oauth.json"))
        )
    else:
        # Se usuário pulou mas já existia, mantém o que está lá ou cria vazio
        pass
    print()

    # 2. Meta Ads
    print("--- [2/7] Meta Ads (Facebook/Instagram) MCP ---")
    ativo = obter_input("Configurar Meta Ads? (s/n)", "s").lower() == "s"
    if ativo:
        meta_conf = mcp_servers.setdefault("meta-marketing", {"command": "uvx", "args": ["meta-ads-mcp"], "env": {}})
        meta_env = meta_conf.setdefault("env", {})
        
        meta_env["META_ACCESS_TOKEN"] = obter_input_obrigatorio(
            "Meta Access Token (System User Token)", meta_env.get("META_ACCESS_TOKEN", "")
        )
        meta_env["META_APP_ID"] = obter_input_obrigatorio(
            "Meta App ID", meta_env.get("META_APP_ID", "")
        )
        meta_env["META_APP_SECRET"] = obter_input_obrigatorio(
            "Meta App Secret", meta_env.get("META_APP_SECRET", "")
        )
    print()

    # 3. Google Drive
    print("--- [3/7] Google Drive MCP ---")
    ativo = obter_input("Configurar Google Drive? (s/n)", "n").lower() == "s"
    if ativo:
        drive_conf = mcp_servers.setdefault("google-drive-designlab", {"command": "npx", "args": ["-y", "mcp-google-drive"], "env": {}})
        drive_env = drive_conf.setdefault("env", {})
        
        drive_env["GOOGLE_APPLICATION_CREDENTIALS"] = obter_input_obrigatorio(
            "Caminho do arquivo JSON de credenciais da Service Account",
            drive_env.get("GOOGLE_APPLICATION_CREDENTIALS", "")
        )
    print()

    # 4. ClickUp
    print("--- [4/7] ClickUp MCP ---")
    ativo = obter_input("Configurar ClickUp? (s/n)", "n").lower() == "s"
    if ativo:
        clickup_conf = mcp_servers.setdefault("clickup-midify", {"command": "npx", "args": ["-y", "@taazkareem/clickup-mcp-server"], "env": {}})
        clickup_env = clickup_conf.setdefault("env", {})
        
        clickup_env["CLICKUP_API_KEY"] = obter_input_obrigatorio(
            "ClickUp API Key (Personal Token)", clickup_env.get("CLICKUP_API_KEY", "")
        )
        clickup_env["CLICKUP_TEAM_ID"] = obter_input_obrigatorio(
            "ClickUp Workspace ID (Team ID)", clickup_env.get("CLICKUP_TEAM_ID", "")
        )
    print()

    # 5. Trello
    print("--- [5/7] Trello MCP ---")
    ativo = obter_input("Configurar Trello? (s/n)", "n").lower() == "s"
    if ativo:
        trello_conf = mcp_servers.setdefault("trello", {"command": "npx", "args": ["-y", "trello-mcp"], "env": {}})
        trello_env = trello_conf.setdefault("env", {})
        
        trello_env["TRELLO_API_KEY"] = obter_input_obrigatorio(
            "Trello API Key", trello_env.get("TRELLO_API_KEY", "")
        )
        trello_env["TRELLO_TOKEN"] = obter_input_obrigatorio(
            "Trello Token", trello_env.get("TRELLO_TOKEN", "")
        )
    print()

    # 6. Google Calendar
    print("--- [6/7] Google Calendar MCP ---")
    ativo = obter_input("Configurar Google Calendar? (s/n)", "n").lower() == "s"
    if ativo:
        cal_conf = mcp_servers.setdefault("google-calendar-guroo", {"command": "npx", "args": ["-y", "@cocal/google-calendar-mcp"], "env": {}})
        cal_env = cal_conf.setdefault("env", {})
        
        cal_env["GOOGLE_OAUTH_CREDENTIALS"] = obter_input_obrigatorio(
            "Caminho do arquivo OAuth JSON do Google Calendar",
            cal_env.get("GOOGLE_OAUTH_CREDENTIALS", "")
        )
    print()

    # 7. Outras Integrações (Gmail, etc.)
    print("--- [7/7] Outras Ferramentas (Gmail Autoauth) ---")
    ativo = obter_input("Configurar Gmail? (s/n)", "s").lower() == "s"
    if ativo:
        mcp_servers["gmail-guroo"] = {
            "command": "npx",
            "args": ["-y", "@gongrzhe/server-gmail-autoauth-mcp"]
        }
    print()

    # Salva o arquivo de configuração
    dados_finais = {
        "_instrucoes": "Gerenciado automaticamente via scripts/configurar-mcp.py",
        "mcpServers": mcp_servers
    }

    print("Gravando configurações...")
    
    # 1. Salva localmente para o Claude Code
    salvar_json(LOCAL_MCP_FILE, dados_finais)
    
    # 2. Salva globalmente para o Antigravity
    salvar_json(GEMINI_MCP_FILE, dados_finais)

    print("\n==============================================")
    print("     Configuração de MCP Concluída com Sucesso! ")
    print("==============================================")
    print("Dica: Reinicie o Claude Code e o Antigravity para aplicar as alterações.\n")


if __name__ == "__main__":
    main()
