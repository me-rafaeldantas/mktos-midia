#!/usr/bin/env python3
"""
instalar-plugin.py — Registra o mktOS Mídia no Claude Code.

Uso:
  python3 ~/mktOS-midia/scripts/instalar-plugin.py

O que faz:
  1. Detecta o caminho do repositório automaticamente
  2. Lê ~/.claude/settings.json (ou cria se não existir)
  3. Injeta o registro do plugin sem sobrescrever outras configurações
  4. Instrui o próximo passo: reiniciar o VS Code e rodar /mktos:configurar
"""

import json
import sys
from pathlib import Path

CLAUDE_DIR = Path.home() / ".claude"
SETTINGS_FILE = CLAUDE_DIR / "settings.json"

# O script fica em scripts/ — o repo está um nível acima
REPO_ROOT = Path(__file__).parent.parent.resolve()
MARKETPLACE_KEY = "mktos-midia"
PLUGIN_KEY = "mktOS Mídia@mktos-midia"


def ler_settings() -> dict:
    if not SETTINGS_FILE.exists():
        return {}
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"\n✗ {SETTINGS_FILE} contém JSON inválido.")
        print("  Corrija o arquivo manualmente antes de continuar.")
        sys.exit(1)


def salvar_settings(dados: dict):
    CLAUDE_DIR.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
        f.write("\n")


def main():
    print(f"\nmktOS Mídia — Instalação do Plugin")
    print("─" * 40)
    print(f"Repositório: {REPO_ROOT}")

    # Confirma que está rodando a partir do repositório correto
    if not (REPO_ROOT / ".claude-plugin" / "plugin.json").exists():
        print("\n✗ Repositório mktOS-midia não encontrado.")
        print(f"  Esperado em: {REPO_ROOT}")
        print("  Clone o repositório e tente novamente.")
        sys.exit(1)

    settings = ler_settings()

    # Verifica se já está instalado
    ja_registrado = (
        MARKETPLACE_KEY in settings.get("extraKnownMarketplaces", {})
        and PLUGIN_KEY in settings.get("enabledPlugins", {})
    )

    if ja_registrado:
        caminho_atual = (
            settings["extraKnownMarketplaces"][MARKETPLACE_KEY]
            .get("source", {})
            .get("path", "")
        )
        if caminho_atual == str(REPO_ROOT):
            print("\n✓ Plugin já está instalado e configurado corretamente.")
            print("\nPróximo passo: execute /mktos:configurar no Claude Code.")
            return

        # Instalado, mas apontando para outro caminho
        print(f"\n⚠  Plugin já registrado com caminho diferente:")
        print(f"   Atual:  {caminho_atual}")
        print(f"   Novo:   {REPO_ROOT}")
        resposta = input("\n   Atualizar para o novo caminho? [s/N] ").strip().lower()
        if resposta not in ("s", "sim", "y", "yes"):
            print("\nInstalação cancelada.")
            sys.exit(0)

    # Injeta extraKnownMarketplaces
    settings.setdefault("extraKnownMarketplaces", {})[MARKETPLACE_KEY] = {
        "source": {
            "source": "directory",
            "path": str(REPO_ROOT),
        }
    }

    # Injeta enabledPlugins
    settings.setdefault("enabledPlugins", {})[PLUGIN_KEY] = True

    salvar_settings(settings)
    print(f"\n✓ Plugin registrado no Claude Code ({SETTINGS_FILE})")

    # Registrar no Antigravity
    registrar_antigravity()

    print("\nPróximos passos:")
    print("  1. Reinicie o VS Code / Antigravity")
    print("  2. Rode a configuração inicial no Claude Code com: /mktos:configurar")
    print("     (ou use o mktOS Mídia diretamente no chat do Antigravity)")
    print()


def registrar_antigravity():
    gemini_plugins_dir = Path.home() / ".gemini" / "config" / "plugins"
    gemini_plugin_target = gemini_plugins_dir / "mktos-midia"
    
    print(f"\nRegistrando no Antigravity...")
    try:
        gemini_plugins_dir.mkdir(parents=True, exist_ok=True)
        
        # Se o link ou pasta já existe
        if gemini_plugin_target.exists() or gemini_plugin_target.is_symlink():
            is_link = gemini_plugin_target.is_symlink()
            link_target = os.readlink(gemini_plugin_target) if is_link else ""
            
            if is_link and link_target == str(REPO_ROOT):
                print(f"✓ Plugin já registrado no Antigravity via link simbólico.")
                return
            
            # Se for link diferente ou pasta
            print(f"⚠  Já existe um registro do plugin no Antigravity:")
            print(f"   Destino: {gemini_plugin_target}")
            resposta = input("   Deseja recriar o link simbólico para este repositório? [s/N] ").strip().lower()
            if resposta not in ("s", "sim", "y", "yes"):
                print("   Registro no Antigravity pulado.")
                return
            
            # Remove link/pasta antiga
            if is_link or gemini_plugin_target.is_file():
                gemini_plugin_target.unlink()
            elif gemini_plugin_target.is_dir():
                import shutil
                shutil.rmtree(gemini_plugin_target)
        
        # Cria o link simbólico
        gemini_plugin_target.symlink_to(REPO_ROOT, target_is_directory=True)
        print(f"✓ Link simbólico criado em: {gemini_plugin_target} -> {REPO_ROOT}")
    except Exception as e:
        print(f"✗ Erro ao registrar no Antigravity: {e}")


if __name__ == "__main__":
    main()
